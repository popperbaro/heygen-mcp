@echo off
echo === Cai dat HeyGen MCP Server ===
echo.

REM Kiem tra Python
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo Python chua duoc cai dat. Vui long cai dat Python 3.10 tro len.
  echo Tai Python tai: https://www.python.org/downloads/
  pause
  exit /b 1
)

REM Cai dat goi pip
echo Dang cai dat HeyGen MCP Server...
pip install -e . > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo Loi khi cai dat goi. Thu pip khac...
  python -m pip install -e . > nul 2>&1
  if %ERRORLEVEL% NEQ 0 (
    echo Khong the cai dat. Vui long kiem tra lai Python va pip.
    pause
    exit /b 1
  )
)

echo Cai dat thanh cong HeyGen MCP Server!
echo.

REM Tao thu muc logs cho Claude Desktop
echo Dang tao thu muc logs cho Claude Desktop...
mkdir "%APPDATA%\Claude\logs" 2> nul
echo "" > "%APPDATA%\Claude\logs\mcp.log" 2> nul
echo Tao thu muc logs xong.
echo.

REM Huong dan cau hinh
echo === Huong dan tiep theo ===
echo 1. Lay API key tu HeyGen (https://www.heygen.com/)
echo 2. Mo Claude Desktop, vao Settings ^> Developer ^> Edit Config
echo 3. Them cau hinh sau vao file:
echo.
echo {
echo   "mcpServers": {
echo     "HeyGen": {
echo       "command": "python",
echo       "args": ["-m", "heygen_mcp.server"],
echo       "env": {
echo         "HEYGEN_API_KEY": "nhap-api-key-cua-ban-tai-day"
echo       }
echo     }
echo   }
echo }
echo.
echo 4. Luu file, khoi dong lai Claude Desktop
echo 5. Vao menu ^> Help ^> Enable Developer Mode
echo.
echo === Cai dat hoan tat ===
pause 