#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具函数模块
Utility Functions Module
"""

import os
import sys
import platform
from pathlib import Path
from typing import Optional


def get_system_info() -> dict:
    """获取系统信息"""
    return {
        'system': platform.system(),
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'machine': platform.machine(),
    }


def check_python_version(min_version: tuple = (3, 11)) -> bool:
    """
    检查 Python 版本

    Args:
        min_version: 最低版本要求

    Returns:
        是否满足要求
    """
    current = sys.version_info[:2]
    return current >= min_version


def check_ffmpeg() -> Optional[str]:
    """
    检查 FFmpeg 是否可用

    Returns:
        FFmpeg 路径，如果不可用则返回 None
    """
    import shutil
    ffmpeg_path = shutil.which('ffmpeg')
    return ffmpeg_path


def format_size(bytes_size: int) -> str:
    """
    格式化文件大小

    Args:
        bytes_size: 字节数

    Returns:
        格式化后的字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


def format_time(seconds: int) -> str:
    """
    格式化时间

    Args:
        seconds: 秒数

    Returns:
        格式化后的字符串
    """
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}分{secs}秒"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}小时{minutes}分"


def sanitize_filename(filename: str) -> str:
    """
    清理文件名中的非法字符

    Args:
        filename: 原始文件名

    Returns:
        清理后的文件名
    """
    # Windows 非法字符
    illegal_chars = '<>:"/\\|?*'
    for char in illegal_chars:
        filename = filename.replace(char, '_')
    return filename


def ensure_dir(path: str) -> Path:
    """
    确保目录存在

    Args:
        path: 目录路径

    Returns:
        Path 对象
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def is_url(text: str) -> bool:
    """
    检查是否为有效 URL

    Args:
        text: 文本

    Returns:
        是否为 URL
    """
    import re
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(text) is not None


def get_video_id_from_url(url: str) -> Optional[str]:
    """
    从 URL 中提取视频 ID

    Args:
        url: 视频 URL

    Returns:
        视频 ID
    """
    import re

    # YouTube
    youtube_patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
    ]

    for pattern in youtube_patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    # Bilibili
    bilibili_patterns = [
        r'bilibili\.com/video/(BV[a-zA-Z0-9]+)',
        r'bilibili\.com/video/(av\d+)',
    ]

    for pattern in bilibili_patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def print_banner():
    """打印欢迎横幅"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║           🎬 yt-dlp 视频下载器                           ║
║           Video Downloader powered by yt-dlp              ║
║                                                           ║
║   支持 YouTube, Bilibili, Twitter 等 1000+ 网站          ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_system_info():
    """打印系统信息"""
    info = get_system_info()
    print(f"系统: {info['system']}")
    print(f"Python: {info['python_version']}")

    ffmpeg = check_ffmpeg()
    if ffmpeg:
        print(f"FFmpeg: ✓ 已安装 ({ffmpeg})")
    else:
        print("FFmpeg: ✗ 未找到")
        print("提示: 运行 tools/download_ffmpeg.bat 下载 FFmpeg")


if __name__ == '__main__':
    # 测试
    print_banner()
    print_system_info()
    print()
    print(f"Python 版本检查: {'✓' if check_python_version() else '✗'}")
    print(f"文件大小格式化: {format_size(1234567890)}")
    print(f"时间格式化: {format_time(3665)}")
