@echo off
setlocal
cd /d "%~dp0"
echo Starting local preview at http://127.0.0.1:8123/index.html
py -m http.server 8123
