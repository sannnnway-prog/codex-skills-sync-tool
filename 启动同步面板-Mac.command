#!/bin/zsh
cd "$(dirname "$0")"
if command -v python3 >/dev/null 2>&1; then
  python3 tools/skill_sync_panel.py
elif command -v python >/dev/null 2>&1; then
  python tools/skill_sync_panel.py
else
  echo "未找到 Python 3。请先安装 Python 3，然后重新双击本文件。"
  echo "下载地址：https://www.python.org/downloads/"
  read "?按回车退出"
fi
