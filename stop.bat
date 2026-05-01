@echo off
title NetTest - Stop
echo Stopping NetTest...
echo.

:: Strategy 1: Kill uvicorn directly
taskkill /f /im uvicorn.exe >nul 2>&1

:: Strategy 2: Kill python processes listening on port 8000
for /f "tokens=5" %%p in ('netstat -aon 2^>nul ^| findstr ":8080" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%p >nul 2>&1
)

echo [OK] NetTest stopped.
echo.
pause
