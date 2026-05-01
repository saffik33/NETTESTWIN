# NetTest - Installation Guide

## Requirements

- Windows 10/11
- Internet connection (for downloading dependencies)
- Administrator privileges (needed for network commands)

## Install

1. Copy the project folder to any location on the target computer
2. Right-click **`install.bat`** → **Run as administrator**
3. Wait for the installer to complete (~5 minutes)

The installer automatically handles:
- Python 3.13 installation (if not present)
- Node.js LTS installation (if not present)
- All dependencies (pip + npm)
- Frontend build
- Database setup
- Desktop shortcut creation

## Run

Double-click the **NetTest** shortcut on your Desktop, or run **`start.bat`** directly.

The app opens at **http://localhost:8080**

## Stop

Close the server window (Ctrl+C), or run **`stop.bat`**.

## Uninstall

Run **`uninstall.bat`** — it removes all installed dependencies and the desktop shortcut.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Requires administrator privileges" | Right-click → Run as administrator |
| Python/Node not found after install | Close and reopen the terminal, or restart the PC |
| Port 8080 in use | Edit `start.bat` and change `--port 8080` to another port |
| Shortcut not created | Run `start.bat` directly from the project folder |
