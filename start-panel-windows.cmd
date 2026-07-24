@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if %errorlevel%==0 (
  python tools\skill_sync_panel.py
  goto :eof
)
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 tools\skill_sync_panel.py
  goto :eof
)
echo Python 3 was not found. Install Python 3, then double-click this file again.
echo Download: https://www.python.org/downloads/
pause
