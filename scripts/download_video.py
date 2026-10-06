#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
yt-dlp 视频下载核心模块
Video Download Core Module using yt-dlp
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import yt_dlp
except ImportError:
    print("错误: 未安装 yt-dlp，请运行 'pip install yt-dlp'")
    sys.exit(1)

from scripts.wx_channel import WxChannelClient, WxChannelError, is_wechat_channels_url


class VideoDownloader:
    """视频下载器类"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化下载器

        Args:
            config_path: 配置文件路径，默认为 config/config.json
        """
        self.base_dir = Path(__file__).parent.parent
        self.progress_callback: Optional[Callable] = None
        self.log_callback: Optional[Callable] = None
        self.last_error: Optional[str] = None
        self.config_path = config_path or self.base_dir / "config" / "config.json"
        self.config = self._load_config()
        self.ffmpeg_path = self._find_ffmpeg()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "format": "bestvideo+bestaudio/best",
            "output_template": "%(title)s [%(id)s].%(ext)s",
            "playlist_output_template": "%(playlist)s/%(playlist_index)s - %(title)s [%(id)s].%(ext)s",
            "download_path": "./downloads",
            "embed_subtitles": False,
            "subtitle_langs": ["zh-CN", "zh-Hans", "en"],
            "merge_output_format": "mp4",
            "playlist_options": {
                "create_folder": True,
                "download_all": True,
                "start_index": 1,
                "end_index": None
            },
            "proxy": "",
            "cookies_file": "",
            "rate_limit": "",
            "wx_channel_exe": "./tools/wx_channel/wx_channel.exe",
            "wx_channel_api_url": "http://127.0.0.1:2025",
            "wx_channel_download_path": "./downloads",
            "wx_channel_startup_timeout": 120,
            "wx_channel_download_timeout": 1800,
            "wx_channel_poll_interval": 1
        }

        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
        except Exception as e:
            self._log(f"警告: 加载配置文件失败: {e}")

        return default_config

    def _find_ffmpeg(self) -> Optional[str]:
        """查找 FFmpeg 路径"""
        # 检查内置 FFmpeg
        ffmpeg_dir = self.base_dir / "tools" / "ffmpeg"

        if sys.platform == "win32":
            ffmpeg_paths = [
                ffmpeg_dir / "bin" / "ffmpeg.exe",
                ffmpeg_dir / "ffmpeg.exe",
            ]
        else:
            ffmpeg_paths = [
                ffmpeg_dir / "bin" / "ffmpeg",
                ffmpeg_dir / "ffmpeg",
            ]

        for path in ffmpeg_paths:
            if path.exists():
                return str(path.parent)

        # 检查系统 PATH
        import shutil
        if shutil.which("ffmpeg"):
            return None  # 使用系统 FFmpeg

        return None

    def _log(self, message: str):
        """输出日志"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def _progress_hook(self, d: Dict[str, Any]):
        """下载进度回调"""
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            speed = d.get('speed', 0)
            eta = d.get('eta', 0)

            if total > 0:
                percent = (downloaded / total) * 100
            else:
                percent = 0

            if self.progress_callback:
                self.progress_callback({
                    'status': 'downloading',
                    'percent': percent,
                    'downloaded': downloaded,
                    'total': total,
                    'speed': speed,
                    'eta': eta,
                    'filename': d.get('filename', '')
                })
            else:
                speed_str = f"{speed/1024/1024:.1f}MB/s" if speed else "N/A"
                eta_str = f"{eta}s" if eta else "N/A"
                print(f"\r下载中: {percent:.1f}% | 速度: {speed_str} | 剩余: {eta_str}", end='')

        elif d['status'] == 'finished':
            if self.progress_callback:
                self.progress_callback({
                    'status': 'finished',
                    'filename': d.get('filename', '')
                })
            else:
                print(f"\n下载完成: {d.get('filename', '')}")

        elif d['status'] == 'error':
            if self.progress_callback:
                self.progress_callback({
                    'status': 'error',
                    'error': str(d.get('error', 'Unknown error'))
                })

    def _get_wx_channel_client(self) -> WxChannelClient:
        return WxChannelClient(
            base_dir=self.base_dir,
            config=self.config,
            progress_callback=self.progress_callback,
            log_callback=self.log_callback or self._log,
        )

    def _get_ydl_opts(self,
                      audio_only: bool = False,
                      subtitles: bool = False,
                      format_str: Optional[str] = None,
                      output_path: Optional[str] = None,
                      playlist_items: Optional[str] = None,
                      is_playlist: bool = False,
                      audio_quality: Optional[str] = None,
                      audio_format: Optional[str] = None) -> Dict[str, Any]:
        """
        构建 yt-dlp 选项

        Args:
            audio_only: 是否仅下载音频
            subtitles: 是否下载字幕
            format_str: 格式字符串
            output_path: 输出路径
            playlist_items: 播放列表项范围
            is_playlist: 是否为播放列表
            audio_quality: 音频质量 (如 "320", "192", "128" 或 "最佳")
            audio_format: 音频格式 (如 "mp3", "m4a", "opus", "flac", "wav")
        """
        # 确定输出路径
        if output_path:
            download_path = Path(output_path)
        else:
            download_path = self.base_dir / self.config.get('download_path', './downloads')

        download_path.mkdir(parents=True, exist_ok=True)

        # 确定输出模板
        if is_playlist and self.config.get('playlist_options', {}).get('create_folder', True):
            output_template = str(download_path / self.config.get('playlist_output_template',
                                  '%(playlist)s/%(playlist_index)s - %(title)s [%(id)s].%(ext)s'))
        else:
            output_template = str(download_path / self.config.get('output_template',
                                  '%(title)s [%(id)s].%(ext)s'))

        # 基础选项
        opts = {
            'outtmpl': output_template,
            'progress_hooks': [self._progress_hook],
            'ignoreerrors': False,
            'no_warnings': False,
            'quiet': False,
        }

        # FFmpeg 路径
        if self.ffmpeg_path:
            opts['ffmpeg_location'] = self.ffmpeg_path

        # 格式选择
        if audio_only:
            opts['format'] = 'bestaudio/best'

            # 确定音频编码格式
            codec = audio_format if audio_format else 'mp3'

            # 确定音频质量
            if audio_quality:
                # 转换质量选项
                quality_map = {
                    '最佳': '0',  # VBR 最佳质量
                    '320kbps': '320',
                    '256kbps': '256',
                    '192kbps': '192',
                    '128kbps': '128'
                }
                quality = quality_map.get(audio_quality, '192')
            else:
                quality = '192'  # 默认质量

            opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': codec,
                'preferredquality': quality,
            }]
        else:
            if format_str:
                opts['format'] = format_str
            else:
                opts['format'] = self.config.get('format', 'bestvideo+bestaudio/best')

            # 合并格式
            merge_format = self.config.get('merge_output_format', 'mp4')
            if merge_format:
                opts['merge_output_format'] = merge_format

        # 字幕选项
        if subtitles or self.config.get('embed_subtitles', False):
            opts['writesubtitles'] = True
            opts['writeautomaticsub'] = True
            opts['subtitleslangs'] = self.config.get('subtitle_langs', ['zh-CN', 'en'])
            opts['embedsubtitles'] = True
            if 'postprocessors' not in opts:
                opts['postprocessors'] = []
            opts['postprocessors'].append({
                'key': 'FFmpegEmbedSubtitle',
            })

        # 播放列表选项
        if playlist_items:
            opts['playlist_items'] = playlist_items

        # 代理设置
        proxy = self.config.get('proxy', '')
        if proxy:
            opts['proxy'] = proxy

        # Cookies 文件
        cookies_file = self.config.get('cookies_file', '')
        if cookies_file and Path(cookies_file).exists():
            opts['cookiefile'] = cookies_file

        # 速度限制
        rate_limit = self.config.get('rate_limit', '')
        if rate_limit:
            opts['ratelimit'] = rate_limit

        return opts

    def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        获取视频信息（不下载）

        Args:
            url: 视频 URL

        Returns:
            视频信息字典
        """
        self.last_error = None

        if is_wechat_channels_url(url):
            try:
                return self._get_wx_channel_client().get_video_info(url)
            except WxChannelError as e:
                self.last_error = f"获取微信视频信息失败: {e}"
                self._log(self.last_error)
                return None

        opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
        }
        if self.config.get('proxy'):
            opts['proxy'] = self.config['proxy']
        cookies_file = self.config.get('cookies_file', '')
        if cookies_file and Path(cookies_file).exists():
            opts['cookiefile'] = cookies_file

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            self.last_error = f"获取视频信息失败: {e}"
            self._log(self.last_error)
            return None

    def is_playlist(self, url: str) -> bool:
        """
        检查 URL 是否为播放列表

        Args:
            url: URL

        Returns:
            是否为播放列表
        """
        info = self.get_video_info(url)
        if info:
            return info.get('_type') == 'playlist' or 'entries' in info
        return False

    def get_playlist_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        获取播放列表信息

        Args:
            url: 播放列表 URL

        Returns:
            播放列表信息
        """
        info = self.get_video_info(url)
        if info and (info.get('_type') == 'playlist' or 'entries' in info):
            entries = info.get('entries', [])
            return {
                'title': info.get('title', 'Unknown Playlist'),
                'id': info.get('id', ''),
                'uploader': info.get('uploader', ''),
                'count': len(entries) if entries else info.get('playlist_count', 0),
                'entries': entries
            }
        return None

    def download(self,
                 url: str,
                 audio_only: bool = False,
                 subtitles: bool = False,
                 format_str: Optional[str] = None,
                 output_path: Optional[str] = None,
                 playlist_items: Optional[str] = None,
                 audio_quality: Optional[str] = None,
                 audio_format: Optional[str] = None) -> bool:
        """
        下载视频

        Args:
            url: 视频或播放列表 URL
            audio_only: 是否仅下载音频
            subtitles: 是否下载字幕
            format_str: 格式字符串
            output_path: 输出路径
            playlist_items: 播放列表项范围（如 "1-10"）
            audio_quality: 音频质量 (如 "320kbps", "192kbps" 或 "最佳")
            audio_format: 音频格式 (如 "mp3", "m4a", "opus")

        Returns:
            是否成功
        """
        self.last_error = None
        self._log(f"开始下载: {url}")

        if is_wechat_channels_url(url):
            if audio_only or subtitles or format_str:
                self._log("提示: 微信视频号下载使用原视频格式，格式/字幕选项不适用")
            try:
                return self._get_wx_channel_client().download(
                    url, output_path=output_path
                )
            except WxChannelError as e:
                self.last_error = f"微信视频下载失败: {e}"
                self._log(self.last_error)
                return False

        # 预取信息，同时避免同一个失败 URL 被重复请求。
        info = self.get_video_info(url)
        if not info:
            if not self.last_error:
                self.last_error = "获取视频信息失败"
            return False

        is_playlist = info.get('_type') == 'playlist' or 'entries' in info

        if is_playlist:
            entries = info.get('entries', [])
            count = len(entries) if entries else info.get('playlist_count', 0)
            self._log(f"检测到播放列表: {info.get('title', 'Unknown Playlist')}")
            self._log(f"共 {count} 个视频")

        # 构建选项
        opts = self._get_ydl_opts(
            audio_only=audio_only,
            subtitles=subtitles,
            format_str=format_str,
            output_path=output_path,
            playlist_items=playlist_items,
            is_playlist=is_playlist,
            audio_quality=audio_quality,
            audio_format=audio_format
        )

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                result = ydl.download([url])
            if result not in (None, 0):
                raise RuntimeError(f"yt-dlp 退出码 {result}")
            return True
        except Exception as e:
            self.last_error = f"yt-dlp 下载失败: {e}"
            self._log(self.last_error)
            return False

    def download_audio(self, url: str, output_path: Optional[str] = None) -> bool:
        """
        下载音频

        Args:
            url: 视频 URL
            output_path: 输出路径

        Returns:
            是否成功
        """
        return self.download(url, audio_only=True, output_path=output_path)

    def download_with_subtitles(self, url: str, output_path: Optional[str] = None) -> bool:
        """
        下载视频并嵌入字幕

        Args:
            url: 视频 URL
            output_path: 输出路径

        Returns:
            是否成功
        """
        return self.download(url, subtitles=True, output_path=output_path)

    def download_playlist(self,
                          url: str,
                          start: int = 1,
                          end: Optional[int] = None,
                          output_path: Optional[str] = None) -> bool:
        """
        下载播放列表

        Args:
            url: 播放列表 URL
            start: 起始索引
            end: 结束索引
            output_path: 输出路径

        Returns:
            是否成功
        """
        if end:
            playlist_items = f"{start}-{end}"
        else:
            playlist_items = f"{start}:"

        return self.download(url, playlist_items=playlist_items, output_path=output_path)


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='yt-dlp 视频下载器')
    parser.add_argument('url', nargs='?', help='视频或播放列表 URL')
    parser.add_argument('--audio-only', '-a', action='store_true', help='仅下载音频')
    parser.add_argument('--subtitles', '-s', action='store_true', help='下载并嵌入字幕')
    parser.add_argument('--format', '-f', type=str, help='指定格式')
    parser.add_argument('--output', '-o', type=str, help='输出目录')
    parser.add_argument('--playlist-items', '-p', type=str, help='播放列表范围（如 1-10）')
    parser.add_argument('--info', '-i', action='store_true', help='仅显示视频信息')

    args = parser.parse_args()

    if not args.url:
        parser.print_help()
        return

    downloader = VideoDownloader()

    if args.info:
        info = downloader.get_video_info(args.url)
        if info:
            print(json.dumps(info, indent=2, ensure_ascii=False))
        return

    success = downloader.download(
        url=args.url,
        audio_only=args.audio_only,
        subtitles=args.subtitles,
        format_str=args.format,
        output_path=args.output,
        playlist_items=args.playlist_items
    )
    if not success:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
