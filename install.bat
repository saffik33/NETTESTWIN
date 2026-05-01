@echo off
setlocal EnableDelayedExpansion
title NetTest Installer
color 0A

echo ============================================
echo       NetTest - Network Monitor Installer
echo ============================================
echo.

:: ============================
:: 1. Admin Check
:: ============================
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] This installer requires administrator privileges.
    echo         Right-click install.bat and select "Run as administrator".
    echo.
    pause
    exit /b 1
)

:: ============================
:: 2. Set working directory
:: ============================
cd /d "%~dp0"
echo [INFO] Installing from: "%CD%"
echo.

:: ============================
:: 3. Check/Install Python
:: ============================
echo [STEP 1/9] Checking Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Python not found. Installing via winget...
    winget install Python.Python.3.13 --accept-package-agreements --accept-source-agreements
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to install Python automatically.
        echo         Please install Python 3.12+ from https://python.org
        echo         Make sure to check "Add Python to PATH" during installation.
        pause
        exit /b 1
    )
    echo [INFO] Refreshing PATH...
    set "PATH=%LocalAppData%\Programs\Python\Python313;%LocalAppData%\Programs\Python\Python313\Scripts;%PATH%"
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo [OK] %%v found.
echo.

:: ============================
:: 4. Check/Install Node.js
:: ============================
echo [STEP 2/9] Checking Node.js...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Node.js not found. Installing via winget...
    winget install OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to install Node.js automatically.
        echo         Please install Node.js 18+ from https://nodejs.org
        pause
        exit /b 1
    )
    echo [INFO] Refreshing PATH...
    set "PATH=%ProgramFiles%\nodejs;%PATH%"
)
for /f "tokens=*" %%v in ('node --version 2^>^&1') do echo [OK] Node.js %%v found.
echo.

:: ============================
:: 5. Create Python virtual environment
:: ============================
echo [STEP 3/9] Setting up Python virtual environment...
if exist "backend\venv" (
    echo [INFO] Virtual environment already exists, skipping.
) else (
    python -m venv "backend\venv"
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)
echo [OK] Virtual environment ready.
echo.

:: ============================
:: 6. Install pip dependencies
:: ============================
echo [STEP 4/9] Installing Python dependencies (this may take a few minutes)...
call "backend\venv\Scripts\activate.bat"
python -m pip install --upgrade pip >nul 2>&1
pip install -r "backend\requirements.txt"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python dependencies.
    pause
    exit /b 1
)
echo [OK] Python dependencies installed.
echo.

:: ============================
:: 7. Install npm dependencies
:: ============================
echo [STEP 5/9] Installing frontend dependencies (this may take a few minutes)...
cd /d "%~dp0frontend"
call npm install
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install frontend dependencies.
    pause
    exit /b 1
)
echo [OK] Frontend dependencies installed.
echo.

:: ============================
:: 8. Build frontend
:: ============================
echo [STEP 6/9] Building frontend...
call npm run build
if %errorlevel% neq 0 (
    echo [ERROR] Frontend build failed.
    pause
    exit /b 1
)
echo [OK] Frontend built successfully.
echo.

:: ============================
:: 9. Setup .env
:: ============================
cd /d "%~dp0"
echo [STEP 7/9] Configuring environment...
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo [OK] Created configuration from template.
) else (
    echo [INFO] Configuration already exists, skipping.
)
echo.

:: ============================
:: 10. Run database migrations
:: ============================
echo [STEP 8/9] Setting up database...
cd /d "%~dp0backend"
if not exist "data" mkdir "data"
call "venv\Scripts\activate.bat"
python -m alembic upgrade head
if %errorlevel% neq 0 (
    echo [ERROR] Database setup failed.
    pause
    exit /b 1
)
echo [OK] Database ready.
echo.

:: ============================
:: 11. Create desktop shortcut
:: ============================
cd /d "%~dp0"
echo [STEP 9/9] Creating desktop shortcut...
set "SHORTCUT=%USERPROFILE%\Desktop\NetTest.lnk"
set "TARGET=%~dp0start.bat"

powershell -NoProfile -Command ^
    "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = '%TARGET%'; $s.WorkingDirectory = '%~dp0'; $s.IconLocation = '%SystemRoot%\System32\shell32.dll,14'; $s.Description = 'Launch NetTest Network Monitor'; $s.Save()"

if exist "%SHORTCUT%" (
    echo [OK] Desktop shortcut "NetTest" created.
) else (
    echo [WARN] Could not create desktop shortcut. You can run start.bat manually.
)
echo.

:: ============================
:: Done
:: ============================
echo ============================================
echo.
echo   NetTest installation complete!
echo.
echo   To start: double-click "NetTest" on your
echo   desktop, or run start.bat directly.
echo.
echo ============================================
pause
