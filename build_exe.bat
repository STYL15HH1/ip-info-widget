@echo off
setlocal

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON=py"
) else (
    set "PYTHON=python"
)

cd /d "%~dp0"

for /f "usebackq delims=" %%I in (`%PYTHON% -c "from core.version import APP_VERSION; print(APP_VERSION)"`) do set "APP_VERSION=%%I"
if not defined APP_VERSION set "APP_VERSION=1.5.1"

echo [1/3] Installing build tools...
%PYTHON% -m pip install --upgrade pip
%PYTHON% -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto :error

echo [2/3] Creating a standalone EXE...
for /f "usebackq delims=" %%I in (`%PYTHON% -c "import sys; print(sys.prefix)"`) do set "PYTHON_ROOT=%%I"
%PYTHON% -m PyInstaller --noconfirm --clean --onefile --windowed --name "IPInfoWidget-%APP_VERSION%" --icon "assets\icons\ip-info-widget.ico" --add-data "assets\images;assets\images" --add-data "assets\author;assets\author" --add-data "assets\icons\ip-info-widget.ico;assets\icons" --collect-all winotify --hidden-import _tkinter --add-binary "%PYTHON_ROOT%\DLLs\_tkinter.pyd;." --add-binary "%PYTHON_ROOT%\DLLs\tcl86t.dll;." --add-binary "%PYTHON_ROOT%\DLLs\tk86t.dll;." --add-data "%PYTHON_ROOT%\Lib\tkinter;tkinter" --add-data "%PYTHON_ROOT%\tcl\tcl8.6;_tcl_data" --add-data "%PYTHON_ROOT%\tcl\tk8.6;_tk_data" app.py
if errorlevel 1 goto :error

set "ISCC="
for %%I in (ISCC.exe) do set "ISCC=%%~$PATH:I"
if not defined ISCC if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC goto :inno_missing

echo [3/3] Creating the Windows installer...
"%ISCC%" /DMyAppVersion=%APP_VERSION% installer.iss
if errorlevel 1 goto :error

echo.
echo Done: dist\IPInfoWidget-%APP_VERSION%.exe and installer\IPInfoWidget-Setup-%APP_VERSION%.exe
echo This is the end-user installer. Python is not required.
pause
exit /b 0

:inno_missing
echo.
echo Inno Setup 6 or 7 is required. Install it from https://jrsoftware.org/isdl.php
echo Then run this file again.
pause
exit /b 1

:error
echo.
echo Build failed. Check that Python is installed and available on PATH.
pause
exit /b 1
