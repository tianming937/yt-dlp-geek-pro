#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
yt-dlp 视频下载器 - 命令行入口
Video Downloader - Command Line Entry Point
"""

import sys
import argparse
from pathlib import Path

for stream in (sys.stdout, sys.stderr):
    if stream and hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from scripts.download_video import VideoDownloader
from scripts.utils import (
    print_banner,
    print_system_info,
    check_python_version,
    is_url
)


def main():
    """主函数"""
    # 检查 Python 版本
    if not check_python_version((3, 11)):
        print("错误: 需要 Python 3.11 或更高版本")
        print(f"当前版本: {sys.version}")
        sys.exit(1)

    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='yt-dlp 视频下载器 - 支持 YouTube, Bilibili 等 1000+ 网站',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s "https://www.youtube.com/watch?v=xxxxx"
  %(prog)s "URL" --audio-only
  %(prog)s "URL" --subtitles
  %(prog)s "播放列表URL" --playlist-items 1-10
  %(prog)s "URL" --info
        """
    )

    parser.add_argument(
        'url',
        nargs='?',
        help='视频或播放列表 URL'
    )

    parser.add_argument(
        '--audio-only', '-a',
        action='store_true',
        help='仅下载音频（MP3格式）'
    )

    parser.add_argument(
        '--subtitles', '-s',
        action='store_true',
        help='下载并嵌入字幕'
    )

    parser.add_argument(
        '--format', '-f',
        type=str,
        metavar='FORMAT',
        help='yt-dlp 格式选择表达式（如 "bv*[height<=720]+ba/b[height<=720]"）'
    )

    parser.add_argument(
        '--audio-quality',
        type=str,
        choices=['最佳', '320kbps', '256kbps', '192kbps', '128kbps'],
        help='音频质量（仅在 --audio-only 模式下有效）'
    )

    parser.add_argument(
        '--audio-format',
        type=str,
        choices=['mp3', 'm4a', 'opus', 'flac', 'wav'],
        default='mp3',
        help='音频格式（仅在 --audio-only 模式下有效，默认: mp3）'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        metavar='PATH',
        help='指定输出目录'
    )

    parser.add_argument(
        '--playlist-items', '-p',
        type=str,
        metavar='RANGE',
        help='播放列表范围（如 "1-10", "1,3,5", "1:"）'
    )

    parser.add_argument(
        '--info', '-i',
        action='store_true',
        help='仅显示视频信息（不下载）'
    )

    parser.add_argument(
        '--version', '-v',
        action='store_true',
        help='显示版本信息'
    )

    parser.add_argument(
        '--gui', '-g',
        action='store_true',
        help='启动图形界面'
    )

    args = parser.parse_args()

    # 显示版本信息
    if args.version:
        print_banner()
        print_system_info()
        return

    # 启动 GUI
    if args.gui:
        try:
            from gui.downloader_gui_v3 import main as gui_main
            gui_main()
        except ImportError as e:
            print(f"错误: 无法启动图形界面: {e}")
            print("请先运行: python -m pip install -r requirements.txt")
            sys.exit(1)
        return

    # 如果没有提供 URL，显示帮助
    if not args.url:
        print_banner()
        print()
        parser.print_help()
        print()
        print("提示: 使用 --gui 或 -g 启动图形界面")
        return

    # 验证 URL
    if not is_url(args.url):
        print(f"错误: 无效的 URL: {args.url}")
        sys.exit(1)

    # 创建下载器
    try:
        downloader = VideoDownloader()
    except Exception as e:
        print(f"错误: 初始化下载器失败: {e}")
        sys.exit(1)

    # 仅显示信息
    if args.info:
        print("正在获取视频信息...")
        info = downloader.get_video_info(args.url)

        if info:
            print("\n" + "="*60)
            print(f"标题: {info.get('title', 'N/A')}")
            print(f"上传者: {info.get('uploader', 'N/A')}")
            print(f"时长: {info.get('duration', 'N/A')} 秒")
            print(f"观看次数: {info.get('view_count', 'N/A')}")
            print(f"上传日期: {info.get('upload_date', 'N/A')}")

            # 如果是播放列表
            if info.get('_type') == 'playlist' or 'entries' in info:
                entries = info.get('entries', [])
                count = len(entries) if entries else info.get('playlist_count', 0)
                print(f"播放列表: 是")
                print(f"视频数量: {count}")
            else:
                print(f"播放列表: 否")

            print("="*60)
        else:
            print("获取视频信息失败")
            sys.exit(1)

        return

    # 下载视频
    print_banner()
    print()

    success = downloader.download(
        url=args.url,
        audio_only=args.audio_only,
        subtitles=args.subtitles,
        format_str=args.format,
        output_path=args.output,
        playlist_items=args.playlist_items,
        audio_quality=args.audio_quality,
        audio_format=args.audio_format
    )

    if success:
        print("\n✓ 下载成功!")
        print(f"文件保存在: {args.output or downloader.config.get('download_path', './downloads')}")
    else:
        print("\n✗ 下载失败")
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断下载")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
