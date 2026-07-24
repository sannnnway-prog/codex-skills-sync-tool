#!/bin/zsh
cd "$(dirname "$0")"
if command -v python3 >/dev/null 2>&1; then
  python3 tools/skill_sync_panel.py
elif command -v python >/dev/null 2>&1; then
  python tools/skill_sync_panel.py
else
  echo "Python 3 was not found. Install Python 3, then double-click this file again."
  echo "Download: https://www.python.org/downloads/"
  read "?Press Enter to exit"
fi
