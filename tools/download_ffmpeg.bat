@echo off
cd /d "%~dp0"
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ========================================
echo    FFmpeg 下载工具
echo ========================================
echo.

REM 检查是否已安装
if exist "ffmpeg\bin\ffmpeg.exe" (
    echo [信息] FFmpeg 已存在
    ffmpeg\bin\ffmpeg.exe -version
    echo.
    set /p "reinstall=是否重新下载？(y/n): "
    if /i not "!reinstall!"=="y" (
        echo [信息] 取消下载
        pause
        exit /b 0
    )
)

echo [信息] 准备下载 FFmpeg...
echo.

REM 设置下载 URL（使用 GitHub 镜像）
set "FFMPEG_URL=https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
set "TEMP_ZIP=%TEMP%\ffmpeg.zip"

echo [信息] 下载地址: %FFMPEG_URL%
echo [信息] 临时文件: %TEMP_ZIP%
echo.

REM 检查 PowerShell
powershell -Command "exit" > nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 PowerShell
    echo [提示] 请手动下载 FFmpeg:
    echo   1. 访问: https://ffmpeg.org/download.html
    echo   2. 下载 Windows 版本
    echo   3. 解压到: %CD%\ffmpeg
    pause
    exit /b 1
)

REM 下载 FFmpeg
echo [信息] 正在下载 FFmpeg（约 100MB，请耐心等待）...
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri '%FFMPEG_URL%' -OutFile '%TEMP_ZIP%'}"

if errorlevel 1 (
    echo [错误] 下载失败
    echo [提示] 请检查网络连接或手动下载
    pause
    exit /b 1
)

echo [成功] 下载完成
echo.

REM 解压文件
echo [信息] 正在解压...
if exist "ffmpeg" rmdir /s /q ffmpeg
powershell -Command "& {Expand-Archive -Path '%TEMP_ZIP%' -DestinationPath '%TEMP%\ffmpeg_extract' -Force}"

if errorlevel 1 (
    echo [错误] 解压失败
    del "%TEMP_ZIP%"
    pause
    exit /b 1
)

REM 移动文件到正确位置
for /d %%i in ("%TEMP%\ffmpeg_extract\ffmpeg-*") do (
    move "%%i" "ffmpeg" > nul
)

REM 清理临时文件
del "%TEMP_ZIP%"
rmdir /s /q "%TEMP%\ffmpeg_extract"

echo [成功] FFmpeg 安装完成
echo.

REM 验证安装
if exist "ffmpeg\bin\ffmpeg.exe" (
    echo [信息] FFmpeg 版本信息:
    ffmpeg\bin\ffmpeg.exe -version
    echo.
    echo [成功] FFmpeg 已就绪！
) else (
    echo [错误] 安装验证失败
    echo [提示] 请手动下载并解压到: %CD%\ffmpeg
)

echo.
pause
endlocal
