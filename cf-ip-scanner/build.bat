@echo off
chcp 65001 >nul
title CF 三方 IP - 构建工具

echo ============================================
echo   CF 三方 IP - PyInstaller 打包工具
echo ============================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] 安装 Python 依赖...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

echo.
echo [2/3] PyInstaller 打包为单文件 exe...
pyinstaller --onefile --name cfipgui --console main.py
if %errorlevel% neq 0 (
    echo [错误] 打包失败
    pause
    exit /b 1
)

echo.
echo [3/3] 构建完成!
echo.
echo 可执行文件: dist\cfipgui.exe
echo 双击运行即可启动 CF 三方 IP 严选工具。
echo.
pause
