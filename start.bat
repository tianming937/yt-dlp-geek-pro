@echo off
cd /d "%~dp0"
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ========================================
echo    yt-dlp Video Downloader
echo ========================================
echo.

REM 检查 Python 是否安装
python --version > nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.11+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [信息] 检测到 Python 环境
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [信息] Python 版本: %PYTHON_VERSION%
echo.

python -c "import sys, operator; sys.exit(not operator.ge(sys.version_info[:2], (3, 11)))" > nul 2>&1
if errorlevel 1 (
    echo [错误] 需要 Python 3.11 或更高版本
    echo [当前版本] %PYTHON_VERSION%
    pause
    exit /b 1
)

REM 检查并安装依赖
echo [信息] 检查依赖包...
python -c "import yt_dlp, requests, chardet, customtkinter; assert tuple(map(int, requests.__version__.split('.')[:2])) >= (2, 32); assert int(chardet.__version__.split('.')[0]) < 6" > nul 2>&1
if errorlevel 1 (
    echo [信息] 正在安装或更新依赖...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
    echo [成功] 依赖安装完成
) else (
    echo [信息] 依赖已安装且版本兼容
)
echo.

REM 检查 FFmpeg
echo [信息] 检查 FFmpeg...
if exist "tools\ffmpeg\bin\ffmpeg.exe" (
    echo [信息] 检测到内置 FFmpeg
    set "PATH=%CD%\tools\ffmpeg\bin;%PATH%"
) else (
    ffmpeg -version > nul 2>&1
    if errorlevel 1 (
        echo [警告] 未检测到 FFmpeg
        echo [提示] 运行 tools\download_ffmpeg.bat 下载 FFmpeg
        echo [提示] 或从 https://ffmpeg.org/download.html 手动下载
        echo.
        set /p "continue=是否继续启动？(y/n): "
        if /i not "!continue!"=="y" (
            exit /b 0
        )
    ) else (
        echo [信息] 检测到系统 FFmpeg
    )
)
echo.

REM 创建下载目录
if not exist "downloads" mkdir downloads

REM 启动 GUI
echo [信息] 启动图形界面...
echo.
python main.py --gui

if errorlevel 1 (
    echo.
    echo [错误] 程序运行出错
    pause
)

endlocal
