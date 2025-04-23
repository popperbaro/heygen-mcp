@echo off
echo === Khoi dong HeyGen MCP Desktop ===
echo.

REM Kiem tra Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo Khong tim thay Python. Vui long cai dat Python 3.10 tro len.
  pause
  exit /b 1
)

REM Kiem tra goi tkinter
python -c "import tkinter" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo Khong tim thay goi tkinter. Tkinter la phan can thiet cho giao dien.
  echo Day thuong la goi mac dinh cua Python, vui long cai dat lai Python voi tkinter.
  pause
  exit /b 1
)

REM Kiem tra goi requests (cho tai video)
python -c "import requests" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo Dang cai dat goi requests cho tai video...
  python -m pip install requests
)

REM Kiem tra va cai dat heygen_mcp
python -c "import heygen_mcp" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo Khong tim thay goi heygen_mcp. Vui long cai dat HeyGen MCP Server truoc.
  echo Ban co the chay script install_heygen_improved.bat hoac install_admin.bat.
  pause
  exit /b 1
)

echo Dang khoi dong HeyGen MCP Desktop...
echo (De tat ung dung, dong cua so nay)
echo.

python heygen_gui.py

echo.
if %ERRORLEVEL% NEQ 0 (
  echo Co loi khi chay ung dung. Vui long kiem tra log.
  pause
)
exit /b 0 