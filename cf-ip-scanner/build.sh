#!/bin/bash
set -e

echo "============================================"
echo "  CF 三方 IP - PyInstaller 打包工具"
echo "============================================"
echo

if ! command -v python3 &>/dev/null; then
    echo "[错误] 未找到 Python3"
    exit 1
fi

echo "[1/3] 安装 Python 依赖..."
pip3 install -r requirements.txt

echo
echo "[2/3] PyInstaller 打包为单文件..."
pyinstaller --onefile --name cfipgui --console --hidden-import server --hidden-import web_ui --hidden-import scanner --hidden-import aiohttp main.py

echo
echo "[3/3] 构建完成!"
echo
echo "可执行文件: dist/cfipgui"
echo "运行: ./dist/cfipgui"
echo
