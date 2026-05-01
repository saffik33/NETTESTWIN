@echo off
title NetTest - Network Monitor
cd /d "%~dp0"

echo ============================================
echo       NetTest - Network Monitor
echo ============================================
echo.

:: Check if frontend is built
if not exist "frontend\dist\index.html" (
    echo [ERROR] Frontend not built. Please run install.bat first.
    pause
    exit /b 1
)

:: Check if venv exists
if not exist "backend\venv\Scripts\activate.bat" (
    echo [ERROR] Python environment not set up. Please run install.bat first.
    pause
    exit /b 1
)

:: Activate virtual environment
call "backend\venv\Scripts\activate.bat"

:: Change to backend directory (needed for relative data/ path)
cd /d "%~dp0backend"

:: Open browser after a short delay
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:8000"

:: Start the server
echo [INFO] Server starting at http://localhost:8000
echo [INFO] A browser window will open automatically.
echo [INFO] Keep this window open. Press Ctrl+C to stop.
echo.
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
