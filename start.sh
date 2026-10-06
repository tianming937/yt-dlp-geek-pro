#!/bin/bash

cd "$(dirname "$0")" || exit 1

echo "========================================"
echo "   yt-dlp Video Downloader"
echo "========================================"
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python3，请先安装 Python 3.11+"
    exit 1
fi

echo "[信息] 检测到 Python 环境"
echo ""

if ! python3 -c 'import sys; assert sys.version_info >= (3, 11)' &> /dev/null; then
    echo "[错误] 需要 Python 3.11 或更高版本"
    exit 1
fi

# 检查并安装依赖
echo "[信息] 检查依赖包..."
if ! python3 -c "import yt_dlp, requests, chardet, customtkinter" &> /dev/null; then
    echo "[信息] 正在安装项目依赖..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[错误] 依赖安装失败"
        exit 1
    fi
    echo "[成功] 依赖安装完成"
else
    echo "[信息] 依赖已安装"
fi
echo ""

# 检查 FFmpeg
echo "[信息] 检查 FFmpeg..."
if [ -f "tools/ffmpeg/bin/ffmpeg" ]; then
    echo "[信息] 检测到内置 FFmpeg"
    export PATH="$(pwd)/tools/ffmpeg/bin:$PATH"
elif command -v ffmpeg &> /dev/null; then
    echo "[信息] 检测到系统 FFmpeg"
else
    echo "[警告] 未检测到 FFmpeg"
    echo "[提示] 请使用包管理器安装 FFmpeg"
    echo "  - macOS: brew install ffmpeg"
    echo "  - Ubuntu: sudo apt install ffmpeg"
    echo ""
    read -p "是否继续启动？(y/n): " continue
    if [ "$continue" != "y" ]; then
        exit 0
    fi
fi
echo ""

# 创建下载目录
mkdir -p downloads

# 启动 GUI
echo "[信息] 启动图形界面..."
echo ""
python3 main.py --gui
