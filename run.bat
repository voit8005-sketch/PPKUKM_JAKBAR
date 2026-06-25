@echo off
echo Starting Sudin PPKUKM Portal...
echo.

REM Install dependencies if needed
echo [1/4] Installing Python dependencies...
pip install -r requirements.txt

REM Create upload dirs
echo [2/4] Creating upload directories...
mkdir static\uploads\news\photos 2>nul
mkdir static\uploads\news\videos 2>nul
mkdir static\uploads\ktp 2>nul
mkdir static\uploads\kegiatan 2>nul

REM Init DB (run SQL if mysql client available, else Flask handles)
echo [3/4] Initializing database...
if exist .env (
    echo Using .env config
) else (
    echo Create .env from .env.example first!
    copy .env.example .env
    echo Edit .env with your DB credentials!
    pause
    exit /b
)

REM Run Flask
echo [4/4] Starting Flask dev server...
echo.
echo Visit: http://localhost:5000
echo Admin login: admin@ppkukm.jakarta / admin123 ^(change after first login^)
echo.
python app.py

pause
