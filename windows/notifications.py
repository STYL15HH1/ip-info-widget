"""Optional Windows toast notifications."""

from __future__ import annotations

import threading

from core.models import IPChange

try:
    from winotify import Notification, audio
except ImportError:
    Notification = None
    audio = None


def send_ip_change_notification(app_name: str, change: IPChange) -> None:
    if Notification is None or audio is None:
        return

    def show() -> None:
        try:
            toast = Notification(
                app_id=app_name,
                title="Public IP changed",
                msg=f"{change.old_ip} → {change.new_ip}\n{change.country}",
                duration="short",
            )
            toast.set_audio(audio.Default, loop=False)
            toast.show()
        except Exception:
            pass

    threading.Thread(target=show, daemon=True).start()
