@echo off
title CF-IP-Scanner Build

echo ============================================
echo   CF-IP-Scanner - PyInstaller Build Tool
echo ============================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install Python 3.8+ first.
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Dependency installation failed
    pause
    exit /b 1
)

echo.
echo [2/3] Building single-file exe...
pyinstaller --onefile --name cfipgui --console --hidden-import server --hidden-import web_ui --hidden-import scanner --hidden-import aiohttp main.py
if %errorlevel% neq 0 (
    echo [ERROR] Build failed
    pause
    exit /b 1
)

echo.
echo [3/3] Build complete!
echo.
echo Output: dist\cfipgui.exe
echo Double-click to run CF-IP-Scanner.
echo.
pause
