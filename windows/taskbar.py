"""Native, dynamic Windows taskbar icon support using owned HICON resources."""

from __future__ import annotations

import ctypes
from ctypes import wintypes

from PIL import Image


WM_SETICON = 0x0080
ICON_SMALL = 0
ICON_BIG = 1
BI_RGB = 0
DIB_RGB_COLORS = 0


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD), ("biWidth", ctypes.c_long), ("biHeight", ctypes.c_long),
        ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", ctypes.c_long), ("biYPelsPerMeter", ctypes.c_long),
        ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", ctypes.c_uint32 * 1)]


class ICONINFO(ctypes.Structure):
    _fields_ = [("fIcon", wintypes.BOOL), ("xHotspot", wintypes.DWORD), ("yHotspot", wintypes.DWORD), ("hbmMask", wintypes.HBITMAP), ("hbmColor", wintypes.HBITMAP)]


class TaskbarIcon:
    """Owns only HICON handles created by this object and releases them on replacement/exit."""

    def __init__(self, root) -> None:
        self.root = root
        self._handle: int | None = None
        self._key: str | None = None
        self.available = hasattr(ctypes, "windll")
        if self.available:
            try:
                self.user32 = ctypes.windll.user32
                self.gdi32 = ctypes.windll.gdi32
                self.user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
                self.user32.SendMessageW.restype = ctypes.c_ssize_t
                self.user32.DestroyIcon.argtypes = [ctypes.c_void_p]
                self.user32.DestroyIcon.restype = wintypes.BOOL
                self.user32.CreateIconIndirect.argtypes = [ctypes.POINTER(ICONINFO)]
                self.user32.CreateIconIndirect.restype = ctypes.c_void_p
                self.gdi32.CreateDIBSection.argtypes = [wintypes.HDC, ctypes.POINTER(BITMAPINFO), wintypes.UINT, ctypes.POINTER(ctypes.c_void_p), wintypes.HANDLE, wintypes.DWORD]
                self.gdi32.CreateDIBSection.restype = ctypes.c_void_p
                self.gdi32.CreateBitmap.restype = ctypes.c_void_p
                self.gdi32.DeleteObject.argtypes = [ctypes.c_void_p]
                self.gdi32.DeleteObject.restype = wintypes.BOOL
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("IPInfoWidget")
            except (AttributeError, OSError):
                self.available = False

    def set_image(self, key: str, image: Image.Image) -> None:
        if not self.available or key == self._key:
            return
        handle = self._create_icon(image)
        if not handle:
            return
        hwnd = self.root.winfo_id()
        self.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, handle)
        self.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, handle)
        self._destroy_current()
        self._handle = handle
        self._key = key

    def clear(self) -> None:
        if not self.available:
            return
        hwnd = self.root.winfo_id()
        self.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, 0)
        self.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, 0)
        self._destroy_current()
        self._key = None

    def _destroy_current(self) -> None:
        if self._handle:
            self.user32.DestroyIcon(self._handle)
            self._handle = None

    def _create_icon(self, image: Image.Image) -> int | None:
        try:
            image = image.convert("RGBA").resize((64, 64), Image.Resampling.LANCZOS)
            width, height = image.size
            info = BITMAPINFO()
            info.bmiHeader = BITMAPINFOHEADER(
                ctypes.sizeof(BITMAPINFOHEADER), width, height, 1, 32, BI_RGB,
                width * height * 4, 0, 0, 0, 0,
            )
            bits = ctypes.c_void_p()
            color = self.gdi32.CreateDIBSection(None, ctypes.byref(info), DIB_RGB_COLORS, ctypes.byref(bits), None, 0)
            if not color or not bits.value:
                return None
            # DIB sections with positive height are bottom-up; HICON expects BGRA pixel data.
            raw = image.tobytes("raw", "BGRA")
            stride = width * 4
            bottom_up = b"".join(raw[offset : offset + stride] for offset in range((height - 1) * stride, -1, -stride))
            ctypes.memmove(bits, bottom_up, len(bottom_up))
            mask = self.gdi32.CreateBitmap(width, height, 1, 1, None)
            icon_info = ICONINFO(True, 0, 0, mask, color)
            handle = self.user32.CreateIconIndirect(ctypes.byref(icon_info))
            self.gdi32.DeleteObject(color)
            self.gdi32.DeleteObject(mask)
            return int(handle) if handle else None
        except (AttributeError, OSError, ValueError):
            return None
