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
echo 未找到 Python。请先安装 Python 3，然后重新双击本文件。
echo 下载地址：https://www.python.org/downloads/
pause
