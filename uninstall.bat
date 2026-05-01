@echo off
setlocal
title NetTest - Uninstall
cd /d "%~dp0"

echo ============================================
echo       NetTest - Uninstaller
echo ============================================
echo.
echo This will remove:
echo   - Python virtual environment (backend\venv)
echo   - Node modules (frontend\node_modules)
echo   - Frontend build (frontend\dist)
echo   - Desktop shortcut
echo.

set /p CONFIRM="Are you sure you want to continue? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo Cancelled.
    pause
    exit /b 0
)

echo.

:: Stop the app if running
echo [1/5] Stopping NetTest if running...
call "%~dp0stop.bat" >nul 2>&1
echo [OK] Done.

echo [2/5] Removing Python virtual environment...
if exist "backend\venv" rmdir /s /q "backend\venv"
echo [OK] Done.

echo [3/5] Removing frontend node_modules...
if exist "frontend\node_modules" rmdir /s /q "frontend\node_modules"
echo [OK] Done.

echo [4/5] Removing frontend build...
if exist "frontend\dist" rmdir /s /q "frontend\dist"
echo [OK] Done.

echo [5/5] Removing desktop shortcut...
powershell -NoProfile -Command "Remove-Item ([Environment]::GetFolderPath('Desktop') + '\NetTest.lnk') -ErrorAction SilentlyContinue"
echo [OK] Done.

echo.
set /p REMOVEDB="Also remove the database (all test history will be lost)? (Y/N): "
if /i "%REMOVEDB%"=="Y" (
    if exist "backend\data\nettest.db" del "backend\data\nettest.db"
    if exist "backend\data\nettest.db-wal" del "backend\data\nettest.db-wal"
    if exist "backend\data\nettest.db-shm" del "backend\data\nettest.db-shm"
    echo [OK] Database removed.
)

echo.
echo ============================================
echo   Uninstall complete.
echo ============================================
echo.
pause
