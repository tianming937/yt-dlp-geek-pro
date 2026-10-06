#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
yt-dlp 视频下载器 - 图形界面
Video Downloader - GUI Interface
"""

import sys
import os
import threading
import queue
from pathlib import Path
from typing import Optional

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

try:
    from scripts.download_video import VideoDownloader
    from scripts.utils import format_size, format_time, is_url
except ImportError:
    # 如果直接运行此文件
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    from download_video import VideoDownloader
    from utils import format_size, format_time, is_url


class DownloaderGUI:
    """视频下载器图形界面"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🎬 yt-dlp 视频下载器")
        self.root.geometry("700x650")
        self.root.minsize(600, 550)

        # 设置图标（如果有的话）
        try:
            self.root.iconbitmap(Path(__file__).parent.parent / "icon.ico")
        except:
            pass

        # 下载器实例
        self.downloader: Optional[VideoDownloader] = None
        self.download_thread: Optional[threading.Thread] = None
        self.is_downloading = False
        self.message_queue = queue.Queue()

        # 创建界面
        self._create_widgets()

        # 初始化下载器
        self._init_downloader()

        # 启动消息处理
        self._process_messages()

    def _init_downloader(self):
        """初始化下载器"""
        try:
            self.downloader = VideoDownloader()
            self.downloader.progress_callback = self._on_progress
            self.downloader.log_callback = self._on_log
            self._log("下载器初始化成功")

            # 检查 FFmpeg
            if self.downloader.ffmpeg_path:
                self._log(f"FFmpeg: 已找到")
            else:
                import shutil
                if shutil.which("ffmpeg"):
                    self._log("FFmpeg: 使用系统安装")
                else:
                    self._log("警告: 未找到 FFmpeg，部分功能可能不可用")
                    self._log("提示: 运行 tools/download_ffmpeg.bat 下载 FFmpeg")
        except Exception as e:
            self._log(f"错误: 初始化下载器失败: {e}")
            messagebox.showerror("错误", f"初始化下载器失败: {e}")

    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ===== URL 输入区域 =====
        url_frame = ttk.LabelFrame(main_frame, text="视频链接", padding="10")
        url_frame.pack(fill=tk.X, pady=(0, 10))

        # URL 输入框
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, font=('', 10))
        url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        # 粘贴按钮
        paste_btn = ttk.Button(url_frame, text="📋 粘贴", width=8, command=self._paste_url)
        paste_btn.pack(side=tk.LEFT, padx=(0, 5))

        # 获取信息按钮
        info_btn = ttk.Button(url_frame, text="ℹ️ 信息", width=8, command=self._get_info)
        info_btn.pack(side=tk.LEFT)

        # ===== 下载选项区域 =====
        options_frame = ttk.LabelFrame(main_frame, text="下载选项", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))

        # 第一行：格式和质量
        row1 = ttk.Frame(options_frame)
        row1.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(row1, text="格式:").pack(side=tk.LEFT)
        self.format_var = tk.StringVar(value="最佳质量")
        format_combo = ttk.Combobox(row1, textvariable=self.format_var, width=15, state="readonly")
        format_combo['values'] = ("最佳质量", "1080p", "720p", "480p")
        format_combo.pack(side=tk.LEFT, padx=(5, 20))
        format_combo.bind('<<ComboboxSelected>>', self._on_format_change)

        # 字幕选项
        self.subtitles_var = tk.BooleanVar(value=False)
        subtitles_check = ttk.Checkbutton(row1, text="下载字幕", variable=self.subtitles_var)
        subtitles_check.pack(side=tk.LEFT, padx=(0, 20))

        # 第一行半：音频下载选项（动态显示）
        row1_5 = ttk.Frame(options_frame)
        row1_5.pack(fill=tk.X, pady=(0, 5))

        self.audio_only_var = tk.BooleanVar(value=False)
        self.audio_check = ttk.Checkbutton(row1_5, text="仅下载音频",
                                           variable=self.audio_only_var,
                                           command=self._on_audio_toggle)
        self.audio_check.pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(row1_5, text="音质:").pack(side=tk.LEFT)
        self.audio_quality_var = tk.StringVar(value="最佳")
        self.audio_quality_combo = ttk.Combobox(row1_5, textvariable=self.audio_quality_var,
                                               width=12, state="readonly")
        self.audio_quality_combo['values'] = ("最佳", "320kbps", "256kbps", "192kbps", "128kbps")
        self.audio_quality_combo.pack(side=tk.LEFT, padx=(5, 20))
        self.audio_quality_combo.config(state=tk.DISABLED)

        ttk.Label(row1_5, text="格式:").pack(side=tk.LEFT)
        self.audio_format_var = tk.StringVar(value="mp3")
        self.audio_format_combo = ttk.Combobox(row1_5, textvariable=self.audio_format_var,
                                              width=8, state="readonly")
        self.audio_format_combo['values'] = ("mp3", "m4a", "opus", "flac", "wav")
        self.audio_format_combo.pack(side=tk.LEFT, padx=(5, 0))
        self.audio_format_combo.config(state=tk.DISABLED)

        # 第二行：输出路径
        row2 = ttk.Frame(options_frame)
        row2.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(row2, text="保存到:").pack(side=tk.LEFT)
        self.output_var = tk.StringVar(value="./downloads")
        output_entry = ttk.Entry(row2, textvariable=self.output_var, width=40)
        output_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        browse_btn = ttk.Button(row2, text="浏览...", command=self._browse_output)
        browse_btn.pack(side=tk.LEFT)

        # 第三行：播放列表选项
        row3 = ttk.Frame(options_frame)
        row3.pack(fill=tk.X)

        ttk.Label(row3, text="播放列表:").pack(side=tk.LEFT)

        self.playlist_mode_var = tk.StringVar(value="all")
        ttk.Radiobutton(row3, text="全部下载", variable=self.playlist_mode_var,
                       value="all").pack(side=tk.LEFT, padx=(5, 10))
        ttk.Radiobutton(row3, text="指定范围:", variable=self.playlist_mode_var,
                       value="range").pack(side=tk.LEFT)

        self.playlist_start_var = tk.StringVar(value="1")
        ttk.Entry(row3, textvariable=self.playlist_start_var, width=5).pack(side=tk.LEFT, padx=2)
        ttk.Label(row3, text="到").pack(side=tk.LEFT)
        self.playlist_end_var = tk.StringVar(value="10")
        ttk.Entry(row3, textvariable=self.playlist_end_var, width=5).pack(side=tk.LEFT, padx=2)

        # ===== 控制按钮区域 =====
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        self.download_btn = ttk.Button(control_frame, text="▶️ 开始下载",
                                       command=self._start_download, style='Accent.TButton')
        self.download_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_btn = ttk.Button(control_frame, text="⏹️ 停止",
                                   command=self._stop_download, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.clear_btn = ttk.Button(control_frame, text="🗑️ 清空日志", command=self._clear_log)
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.open_folder_btn = ttk.Button(control_frame, text="📁 打开目录",
                                          command=self._open_download_folder)
        self.open_folder_btn.pack(side=tk.LEFT)

        # ===== 进度条区域 =====
        progress_frame = ttk.LabelFrame(main_frame, text="下载进度", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                            maximum=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))

        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        status_label.pack(anchor=tk.W)

        # ===== 日志区域 =====
        log_frame = ttk.LabelFrame(main_frame, text="日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)

        # ===== 底部信息 =====
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(footer_frame, text="支持 YouTube, Bilibili, Twitter 等 1000+ 网站",
                 foreground="gray").pack(side=tk.LEFT)
        ttk.Label(footer_frame, text="Powered by yt-dlp",
                 foreground="gray").pack(side=tk.RIGHT)

    def _on_format_change(self, event=None):
        """格式选择变化时的回调"""
        # 如果选择了视频格式，自动取消音频模式
        if self.format_var.get() != "最佳质量":
            self.audio_only_var.set(False)
            self._on_audio_toggle()

    def _on_audio_toggle(self):
        """音频选项切换时的回调"""
        if self.audio_only_var.get():
            # 启用音频选项
            self.audio_quality_combo.config(state="readonly")
            self.audio_format_combo.config(state="readonly")
            # 禁用视频格式选项（可选）
            # self.format_combo.config(state=tk.DISABLED)
        else:
            # 禁用音频选项
            self.audio_quality_combo.config(state=tk.DISABLED)
            self.audio_format_combo.config(state=tk.DISABLED)
            # self.format_combo.config(state="readonly")

    def _paste_url(self):
        """从剪贴板粘贴 URL"""
        try:
            url = self.root.clipboard_get()
            self.url_var.set(url.strip())
        except:
            pass

    def _browse_output(self):
        """浏览输出目录"""
        folder = filedialog.askdirectory(initialdir=self.output_var.get())
        if folder:
            self.output_var.set(folder)

    def _get_info(self):
        """获取视频信息"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("警告", "请输入视频链接")
            return

        if not is_url(url):
            messagebox.showwarning("警告", "请输入有效的 URL")
            return

        self._log("正在获取视频信息...")
        self.status_var.set("正在获取信息...")

        def get_info_thread():
            try:
                info = self.downloader.get_video_info(url)
                if info:
                    # 构建信息文本
                    title = info.get('title', 'N/A')
                    uploader = info.get('uploader', 'N/A')
                    duration = info.get('duration', 0)

                    is_playlist = info.get('_type') == 'playlist' or 'entries' in info

                    msg = f"标题: {title}\n"
                    msg += f"上传者: {uploader}\n"

                    if is_playlist:
                        entries = info.get('entries', [])
                        count = len(entries) if entries else info.get('playlist_count', 0)
                        msg += f"类型: 播放列表\n"
                        msg += f"视频数量: {count}"
                    else:
                        msg += f"时长: {format_time(duration) if duration else 'N/A'}\n"
                        msg += f"类型: 单个视频"

                    self.message_queue.put(('info', msg))
                else:
                    error = self.downloader.last_error or "获取视频信息失败"
                    self.message_queue.put(('error', error))
            except Exception as e:
                self.message_queue.put(('error', f"获取信息失败: {e}"))
            finally:
                self.message_queue.put(('status', "就绪"))

        threading.Thread(target=get_info_thread, daemon=True).start()

    def _start_download(self):
        """开始下载"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("警告", "请输入视频链接")
            return

        if not is_url(url):
            messagebox.showwarning("警告", "请输入有效的 URL")
            return

        if self.is_downloading:
            messagebox.showwarning("警告", "正在下载中，请等待完成")
            return

        # 获取选项
        format_map = {
            "最佳质量": "bestvideo+bestaudio/best",
            "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "仅音频": None  # 使用 audio_only 参数
        }

        format_str = format_map.get(self.format_var.get())
        audio_only = self.audio_only_var.get()  # 使用新的音频选项
        subtitles = self.subtitles_var.get()
        output_path = self.output_var.get()

        # 音频选项
        audio_quality = self.audio_quality_var.get() if audio_only else None
        audio_format = self.audio_format_var.get() if audio_only else None

        # 播放列表选项
        playlist_items = None
        if self.playlist_mode_var.get() == "range":
            start = self.playlist_start_var.get()
            end = self.playlist_end_var.get()
            playlist_items = f"{start}-{end}"

        # 更新界面状态
        self.is_downloading = True
        self.download_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress_var.set(0)
        self.status_var.set("准备下载...")

        # 启动下载线程
        def download_thread():
            try:
                success = self.downloader.download(
                    url=url,
                    audio_only=audio_only,
                    subtitles=subtitles,
                    format_str=format_str,
                    output_path=output_path,
                    playlist_items=playlist_items,
                    audio_quality=audio_quality,
                    audio_format=audio_format
                )

                if success:
                    self.message_queue.put(('complete', "下载完成!"))
                else:
                    error = self.downloader.last_error or "下载失败"
                    self.message_queue.put(('error', error))
            except Exception as e:
                self.message_queue.put(('error', f"下载出错: {e}"))
            finally:
                self.message_queue.put(('done', None))

        self.download_thread = threading.Thread(target=download_thread, daemon=True)
        self.download_thread.start()

    def _stop_download(self):
        """停止下载"""
        if self.is_downloading:
            self._log("正在停止下载...")
            # yt-dlp 没有直接的停止方法，这里只是更新状态
            self.is_downloading = False
            self._update_ui_state()
            self.status_var.set("已停止")

    def _clear_log(self):
        """清空日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _open_download_folder(self):
        """打开下载目录"""
        folder = Path(self.output_var.get())
        if not folder.is_absolute():
            folder = Path(__file__).parent.parent / folder

        folder.mkdir(parents=True, exist_ok=True)

        if sys.platform == 'win32':
            os.startfile(folder)
        elif sys.platform == 'darwin':
            os.system(f'open "{folder}"')
        else:
            os.system(f'xdg-open "{folder}"')

    def _log(self, message: str):
        """添加日志"""
        self.message_queue.put(('log', message))

    def _on_progress(self, data: dict):
        """进度回调"""
        self.message_queue.put(('progress', data))

    def _on_log(self, message: str):
        """日志回调"""
        self.message_queue.put(('log', message))

    def _process_messages(self):
        """处理消息队列"""
        try:
            while True:
                msg_type, data = self.message_queue.get_nowait()

                if msg_type == 'log':
                    self.log_text.config(state=tk.NORMAL)
                    self.log_text.insert(tk.END, f"{data}\n")
                    self.log_text.see(tk.END)
                    self.log_text.config(state=tk.DISABLED)

                elif msg_type == 'progress':
                    if data['status'] == 'downloading':
                        self.progress_var.set(data['percent'])
                        speed = data.get('speed', 0)
                        speed_str = f"{speed/1024/1024:.1f}MB/s" if speed else "N/A"
                        eta = data.get('eta', 0)
                        eta_str = format_time(eta) if eta else "N/A"
                        self.status_var.set(f"下载中: {data['percent']:.1f}% | 速度: {speed_str} | 剩余: {eta_str}")
                    elif data['status'] == 'finished':
                        self.status_var.set("处理中...")

                elif msg_type == 'status':
                    self.status_var.set(data)

                elif msg_type == 'info':
                    messagebox.showinfo("视频信息", data)

                elif msg_type == 'error':
                    self._log(f"错误: {data}")
                    messagebox.showerror("错误", data)

                elif msg_type == 'complete':
                    self.progress_var.set(100)
                    self.status_var.set(data)
                    self._log(data)
                    messagebox.showinfo("完成", data)

                elif msg_type == 'done':
                    self.is_downloading = False
                    self._update_ui_state()

        except queue.Empty:
            pass

        # 继续处理
        self.root.after(100, self._process_messages)

    def _update_ui_state(self):
        """更新界面状态"""
        if self.is_downloading:
            self.download_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
        else:
            self.download_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)


def main():
    """主函数"""
    root = tk.Tk()

    # 设置主题样式
    style = ttk.Style()
    if sys.platform == 'win32':
        style.theme_use('vista')

    app = DownloaderGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
