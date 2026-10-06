#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
yt-dlp 视频下载器 - 图形界面 v3 (CustomTkinter)
专业浅色主题 + 标准字体系统
Video Downloader - GUI Interface v3
"""

import sys
import os
import threading
import queue
from pathlib import Path
from typing import Optional

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import customtkinter as ctk
from tkinter import filedialog, messagebox

try:
    from scripts.download_video import VideoDownloader
    from scripts.utils import format_size, format_time, is_url
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    from download_video import VideoDownloader
    from utils import format_size, format_time, is_url


# 设置 CustomTkinter 主题和颜色
ctk.set_appearance_mode("light")

# 专业浅色配色方案
COLORS = {
    'bg_primary': '#F3F6F5',      # 背景色
    'bg_secondary': '#FFFFFF',    # 内容面板
    'text_primary': '#172A2E',    # 主文字
    'text_secondary': '#637378',  # 次要文字
    'accent_primary': '#167C80',  # 主操作色
    'divider': '#D7E0DF',         # 分隔线
    'success': '#0A7029',         # 成功绿
    'error': '#C41E3A',           # 错误红
    'warning': '#D97706',         # 警告橙
}

# 字体配置
FONTS = {
    'title': ('Microsoft YaHei UI', 20),           # 页标题
    'section': ('Microsoft YaHei UI', 13, 'bold'), # 区块标题
    'body': ('Microsoft YaHei UI', 11),            # 正文
    'small': ('Microsoft YaHei UI', 10),           # 小字
    'number': ('Segoe UI', 11),                    # 数字（速度、时间、百分比）
    'monospace': ('Consolas', 10),                 # 等宽字体（日志）
}


class DownloaderGUI:
    """视频下载器图形界面 v3"""

    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title("yt-dlp下载器 - 极客碎碎念pro版")
        self.root.geometry("1100x830")
        self.root.minsize(900, 730)

        # 应用背景色
        self.root.configure(fg_color=COLORS['bg_primary'])

        # 配置窗口网格
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

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
            self._log("【成功】下载器初始化成功", "success")

            # 检查 FFmpeg
            if self.downloader.ffmpeg_path:
                self._log("【信息】FFmpeg: 已找到", "info")
            else:
                import shutil
                if shutil.which("ffmpeg"):
                    self._log("【信息】FFmpeg: 使用系统安装", "info")
                else:
                    self._log("【警告】未找到 FFmpeg，部分功能可能不可用", "warning")
        except Exception as e:
            self._log(f"【错误】初始化下载器失败: {e}", "error")
            messagebox.showerror("错误", f"初始化下载器失败: {e}")

    def _create_widgets(self):
        """创建界面组件"""
        # 主容器
        main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_container.grid_columnconfigure(0, weight=1)

        # 当前行号
        current_row = 0

        # URL 输入区
        url_frame = self._create_url_section(main_container)
        url_frame.grid(row=current_row, column=0, sticky="ew", pady=(0, 12))
        current_row += 1

        # 控制和进度区
        control_frame = self._create_control_section(main_container)
        control_frame.grid(row=current_row, column=0, sticky="ew", pady=(0, 12))
        current_row += 1

        # 设置区（两列）
        settings_frame = self._create_settings_section(main_container)
        settings_frame.grid(row=current_row, column=0, sticky="ew", pady=(0, 12))
        current_row += 1

        # 保存设置
        path_frame = self._create_path_section(main_container)
        path_frame.grid(row=current_row, column=0, sticky="ew", pady=(0, 8))
        current_row += 1

        # 播放列表
        playlist_frame = self._create_playlist_section(main_container)
        playlist_frame.grid(row=current_row, column=0, sticky="ew", pady=(0, 12))
        current_row += 1

        # 日志区
        log_frame = self._create_log_section(main_container)
        log_frame.grid(row=current_row, column=0, sticky="nsew", pady=(0, 0))
        main_container.grid_rowconfigure(current_row, weight=1)

    def _create_url_section(self, parent):
        """创建 URL 输入区"""
        frame = ctk.CTkFrame(
            parent,
            corner_radius=10,
            fg_color=COLORS['bg_secondary'],
            border_width=1,
            border_color=COLORS['divider']
        )
        frame.grid_columnconfigure(1, weight=1)

        # 标签
        label = ctk.CTkLabel(
            frame,
            text="视频链接",
            font=FONTS['section'],
            text_color=COLORS['text_primary']
        )
        label.grid(row=0, column=0, columnspan=4, sticky="w", padx=20, pady=(16, 12))

        # URL 输入框
        self.url_var = ctk.StringVar()
        self.url_entry = ctk.CTkEntry(
            frame,
            textvariable=self.url_var,
            placeholder_text="https://www.youtube.com/watch?v=...",
            height=40,
            font=FONTS['body'],
            text_color=COLORS['text_primary'],
            fg_color=COLORS['bg_primary'],
            border_color=COLORS['divider'],
            border_width=1
        )
        self.url_entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 16))

        # 粘贴按钮
        paste_btn = ctk.CTkButton(
            frame,
            text="粘贴",
            width=90,
            height=40,
            command=self._paste_url,
            font=FONTS['body'],
            fg_color=COLORS['accent_primary'],
            hover_color="#125B5F",
            text_color="white",
            corner_radius=6
        )
        paste_btn.grid(row=1, column=2, padx=(10, 5), pady=(0, 16))

        # 信息按钮
        info_btn = ctk.CTkButton(
            frame,
            text="获取信息",
            width=90,
            height=40,
            command=self._get_info,
            fg_color="transparent",
            border_width=1,
            border_color=COLORS['accent_primary'],
            text_color=COLORS['accent_primary'],
            hover_color=COLORS['bg_primary'],
            font=FONTS['body'],
            corner_radius=6
        )
        info_btn.grid(row=1, column=3, padx=(5, 20), pady=(0, 16))

        return frame

    def _create_control_section(self, parent):
        """创建控制和进度区"""
        frame = ctk.CTkFrame(
            parent,
            corner_radius=10,
            fg_color=COLORS['bg_secondary'],
            border_width=1,
            border_color=COLORS['divider']
        )
        frame.grid_columnconfigure(0, weight=1)

        # 按钮区
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 16))

        # 开始下载按钮
        self.download_btn = ctk.CTkButton(
            btn_frame,
            text="▶ 开始下载",
            width=140,
            height=44,
            command=self._start_download,
            font=FONTS['section'],
            fg_color=COLORS['accent_primary'],
            hover_color="#125B5F",
            text_color="white",
            corner_radius=6
        )
        self.download_btn.pack(side="left", padx=(0, 12))

        # 暂停按钮
        self.stop_btn = ctk.CTkButton(
            btn_frame,
            text="⏸ 暂停",
            width=100,
            height=44,
            command=self._stop_download,
            fg_color="transparent",
            border_width=1,
            border_color=COLORS['text_secondary'],
            text_color=COLORS['text_secondary'],
            hover_color=COLORS['bg_primary'],
            state="disabled",
            font=FONTS['body'],
            corner_radius=6
        )
        self.stop_btn.pack(side="left", padx=(0, 12))

        # 清空日志按钮
        clear_btn = ctk.CTkButton(
            btn_frame,
            text="清空日志",
            width=100,
            height=44,
            command=self._clear_log,
            fg_color="transparent",
            hover_color=COLORS['bg_primary'],
            text_color=COLORS['text_secondary'],
            font=FONTS['small'],
            corner_radius=6
        )
        clear_btn.pack(side="left")

        # 分隔线
        separator = ctk.CTkFrame(frame, height=1, fg_color=COLORS['divider'])
        separator.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 16))

        # 进度标题
        progress_label = ctk.CTkLabel(
            frame,
            text="下载进度",
            font=FONTS['body'],
            text_color=COLORS['text_secondary']
        )
        progress_label.grid(row=2, column=0, sticky="w", padx=20, pady=(0, 10))

        # 进度条
        self.progress_bar = ctk.CTkProgressBar(
            frame,
            height=8,
            corner_radius=4,
            progress_color=COLORS['accent_primary'],
            fg_color=COLORS['bg_primary']
        )
        self.progress_bar.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 12))
        self.progress_bar.set(0)

        # 文件名
        self.filename_label = ctk.CTkLabel(
            frame,
            text='等待下载...',
            font=FONTS['body'],
            text_color=COLORS['text_primary'],
            anchor="w"
        )
        self.filename_label.grid(row=4, column=0, sticky="w", padx=20, pady=(0, 6))

        # 统计信息
        self.stats_label = ctk.CTkLabel(
            frame,
            text="",
            font=FONTS['number'],
            text_color=COLORS['text_secondary'],
            anchor="w"
        )
        self.stats_label.grid(row=5, column=0, sticky="w", padx=20, pady=(0, 20))

        return frame

    def _create_settings_section(self, parent):
        """创建设置区（两列）"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)

        # 左列：视频设置
        video_frame = self._create_video_settings(frame)
        video_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        # 右列：音频设置
        audio_frame = self._create_audio_settings(frame)
        audio_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        return frame

    def _create_video_settings(self, parent):
        """创建视频设置卡片"""
        frame = ctk.CTkFrame(
            parent,
            corner_radius=10,
            fg_color=COLORS['bg_secondary'],
            border_width=1,
            border_color=COLORS['divider']
        )
        frame.grid_columnconfigure(1, weight=1)

        # 标题
        title = ctk.CTkLabel(
            frame,
            text="视频设置",
            font=FONTS['section'],
            text_color=COLORS['text_primary']
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(16, 14))

        # 清晰度
        ctk.CTkLabel(
            frame,
            text="清晰度",
            font=FONTS['body'],
            text_color=COLORS['text_secondary']
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 12))

        self.format_var = ctk.StringVar(value="最佳质量")
        format_menu = ctk.CTkOptionMenu(
            frame,
            variable=self.format_var,
            values=["最佳质量", "1080p", "720p", "480p"],
            width=200,
            height=32,
            font=FONTS['body'],
            fg_color=COLORS['bg_primary'],
            button_color=COLORS['accent_primary'],
            button_hover_color="#125B5F",
            command=self._on_format_change
        )
        format_menu.grid(row=1, column=1, sticky="ew", padx=16, pady=(0, 12))

        # 格式
        ctk.CTkLabel(
            frame,
            text="格式",
            font=FONTS['body'],
            text_color=COLORS['text_secondary']
        ).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 12))

        self.video_format_var = ctk.StringVar(value="MP4")
        video_format_menu = ctk.CTkOptionMenu(
            frame,
            variable=self.video_format_var,
            values=["MP4", "MKV", "WEBM"],
            width=200,
            height=32,
            font=FONTS['body'],
            fg_color=COLORS['bg_primary'],
            button_color=COLORS['accent_primary'],
            button_hover_color="#125B5F"
        )
        video_format_menu.grid(row=2, column=1, sticky="ew", padx=16, pady=(0, 12))

        # 字幕选项
        checkbox_frame = ctk.CTkFrame(frame, fg_color="transparent")
        checkbox_frame.grid(row=3, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 16))

        self.subtitles_var = ctk.BooleanVar(value=False)
        subtitles_check = ctk.CTkCheckBox(
            checkbox_frame,
            text="下载字幕",
            variable=self.subtitles_var,
            font=FONTS['body'],
            text_color=COLORS['text_primary'],
            fg_color=COLORS['accent_primary'],
            hover_color="#125B5F"
        )
        subtitles_check.pack(side="left", padx=(0, 16))

        self.embed_subs_var = ctk.BooleanVar(value=False)
        embed_check = ctk.CTkCheckBox(
            checkbox_frame,
            text="嵌入字幕",
            variable=self.embed_subs_var,
            font=FONTS['body'],
            text_color=COLORS['text_primary'],
            fg_color=COLORS['accent_primary'],
            hover_color="#125B5F"
        )
        embed_check.pack(side="left")

        return frame

    def _create_audio_settings(self, parent):
        """创建音频设置卡片"""
        frame = ctk.CTkFrame(
            parent,
            corner_radius=10,
            fg_color=COLORS['bg_secondary'],
            border_width=1,
            border_color=COLORS['divider']
        )
        frame.grid_columnconfigure(1, weight=1)

        # 标题
        title = ctk.CTkLabel(
            frame,
            text="音频设置",
            font=FONTS['section'],
            text_color=COLORS['text_primary']
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(16, 14))

        # 音质
        ctk.CTkLabel(
            frame,
            text="音质",
            font=FONTS['body'],
            text_color=COLORS['text_secondary']
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 12))

        self.audio_quality_var = ctk.StringVar(value="最佳")
        self.audio_quality_menu = ctk.CTkOptionMenu(
            frame,
            variable=self.audio_quality_var,
            values=["最佳", "320kbps", "256kbps", "192kbps", "128kbps"],
            width=200,
            height=32,
            font=FONTS['body'],
            fg_color=COLORS['bg_primary'],
            button_color=COLORS['accent_primary'],
            button_hover_color="#125B5F",
            state="disabled"
        )
        self.audio_quality_menu.grid(row=1, column=1, sticky="ew", padx=16, pady=(0, 12))

        # 格式
        ctk.CTkLabel(
            frame,
            text="格式",
            font=FONTS['body'],
            text_color=COLORS['text_secondary']
        ).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 12))

        self.audio_format_var = ctk.StringVar(value="mp3")
        self.audio_format_menu = ctk.CTkOptionMenu(
            frame,
            variable=self.audio_format_var,
            values=["mp3", "m4a", "opus", "flac", "wav"],
            width=200,
            height=32,
            font=FONTS['body'],
            fg_color=COLORS['bg_primary'],
            button_color=COLORS['accent_primary'],
            button_hover_color="#125B5F",
            state="disabled"
        )
        self.audio_format_menu.grid(row=2, column=1, sticky="ew", padx=16, pady=(0, 12))

        # 仅音频选项
        self.audio_only_var = ctk.BooleanVar(value=False)
        audio_only_check = ctk.CTkCheckBox(
            frame,
            text="仅下载音频",
            variable=self.audio_only_var,
            font=FONTS['body'],
            text_color=COLORS['text_primary'],
            fg_color=COLORS['accent_primary'],
            hover_color="#125B5F",
            command=self._on_audio_toggle
        )
        audio_only_check.grid(row=3, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 16))

        return frame

    def _create_path_section(self, parent):
        """创建保存路径设置"""
        frame = ctk.CTkFrame(
            parent,
            corner_radius=10,
            fg_color=COLORS['bg_secondary'],
            border_width=1,
            border_color=COLORS['divider']
        )
        frame.grid_columnconfigure(1, weight=1)

        # 标题
        title = ctk.CTkLabel(
            frame,
            text="保存设置",
            font=FONTS['section'],
            text_color=COLORS['text_primary']
        )
        title.grid(row=0, column=0, columnspan=4, sticky="w", padx=16, pady=(16, 14))

        # 保存位置标签
        ctk.CTkLabel(
            frame,
            text="保存位置",
            font=FONTS['body'],
            text_color=COLORS['text_secondary']
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 16))

        # 路径输入框
        self.output_var = ctk.StringVar(value="./downloads")
        output_entry = ctk.CTkEntry(
            frame,
            textvariable=self.output_var,
            height=32,
            font=FONTS['small'],
            fg_color=COLORS['bg_primary'],
            border_color=COLORS['divider'],
            border_width=1
        )
        output_entry.grid(row=1, column=1, sticky="ew", padx=(10, 10), pady=(0, 16))

        # 浏览按钮
        browse_btn = ctk.CTkButton(
            frame,
            text="浏览",
            width=80,
            height=32,
            command=self._browse_output,
            font=FONTS['small'],
            fg_color=COLORS['accent_primary'],
            hover_color="#125B5F",
            corner_radius=6
        )
        browse_btn.grid(row=1, column=2, padx=(0, 10), pady=(0, 16))

        # 打开文件夹按钮
        open_btn = ctk.CTkButton(
            frame,
            text="打开文件夹",
            width=100,
            height=32,
            command=self._open_download_folder,
            fg_color="transparent",
            hover_color=COLORS['bg_primary'],
            text_color=COLORS['accent_primary'],
            font=FONTS['small'],
            corner_radius=6
        )
        open_btn.grid(row=1, column=3, padx=(0, 16), pady=(0, 16))

        return frame

    def _create_playlist_section(self, parent):
        """创建播放列表设置"""
        frame = ctk.CTkFrame(
            parent,
            corner_radius=10,
            fg_color=COLORS['bg_secondary'],
            border_width=1,
            border_color=COLORS['divider']
        )

        # 标题
        title = ctk.CTkLabel(
            frame,
            text="播放列表选项",
            font=FONTS['section'],
            text_color=COLORS['text_primary']
        )
        title.grid(row=0, column=0, columnspan=6, sticky="w", padx=16, pady=(16, 14))

        # 单选按钮
        self.playlist_mode_var = ctk.StringVar(value="all")

        radio1 = ctk.CTkRadioButton(
            frame,
            text="下载全部",
            variable=self.playlist_mode_var,
            value="all",
            font=FONTS['body'],
            text_color=COLORS['text_primary'],
            fg_color=COLORS['accent_primary'],
            hover_color="#125B5F"
        )
        radio1.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 16))

        radio2 = ctk.CTkRadioButton(
            frame,
            text="指定范围",
            variable=self.playlist_mode_var,
            value="range",
            font=FONTS['body'],
            text_color=COLORS['text_primary'],
            fg_color=COLORS['accent_primary'],
            hover_color="#125B5F"
        )
        radio2.grid(row=1, column=1, sticky="w", padx=(16, 10), pady=(0, 16))

        # 范围输入
        self.playlist_start_var = ctk.StringVar(value="1")
        start_entry = ctk.CTkEntry(
            frame,
            textvariable=self.playlist_start_var,
            width=60,
            height=28,
            font=FONTS['number'],
            fg_color=COLORS['bg_primary'],
            border_color=COLORS['divider'],
            border_width=1
        )
        start_entry.grid(row=1, column=2, padx=(0, 5), pady=(0, 16))

        ctk.CTkLabel(
            frame,
            text="到",
            font=FONTS['body'],
            text_color=COLORS['text_secondary']
        ).grid(row=1, column=3, padx=5, pady=(0, 16))

        self.playlist_end_var = ctk.StringVar(value="10")
        end_entry = ctk.CTkEntry(
            frame,
            textvariable=self.playlist_end_var,
            width=60,
            height=28,
            font=FONTS['number'],
            fg_color=COLORS['bg_primary'],
            border_color=COLORS['divider'],
            border_width=1
        )
        end_entry.grid(row=1, column=4, padx=(5, 0), pady=(0, 16))

        return frame

    def _create_log_section(self, parent):
        """创建日志区"""
        frame = ctk.CTkFrame(
            parent,
            corner_radius=10,
            fg_color=COLORS['bg_secondary'],
            border_width=1,
            border_color=COLORS['divider']
        )
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # 标题栏
        header_frame = ctk.CTkFrame(frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 10))
        header_frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header_frame,
            text="日志",
            font=FONTS['section'],
            text_color=COLORS['text_primary']
        )
        title.pack(side="left")

        # 导出按钮
        export_btn = ctk.CTkButton(
            header_frame,
            text="导出",
            width=70,
            height=26,
            fg_color="transparent",
            hover_color=COLORS['bg_primary'],
            text_color=COLORS['accent_primary'],
            font=FONTS['small'],
            command=self._export_log,
            corner_radius=4
        )
        export_btn.pack(side="right")

        # 日志文本框
        self.log_text = ctk.CTkTextbox(
            frame,
            font=FONTS['monospace'],
            text_color=COLORS['text_primary'],
            fg_color=COLORS['bg_primary'],
            wrap="word",
            border_width=0
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

        return frame

    # ===== 交互逻辑 =====

    def _on_format_change(self, choice):
        """格式选择变化"""
        if choice != "最佳质量":
            self.audio_only_var.set(False)
            self._on_audio_toggle()

    def _on_audio_toggle(self):
        """音频选项切换"""
        if self.audio_only_var.get():
            self.audio_quality_menu.configure(state="normal")
            self.audio_format_menu.configure(state="normal")
        else:
            self.audio_quality_menu.configure(state="disabled")
            self.audio_format_menu.configure(state="disabled")

    def _paste_url(self):
        """从剪贴板粘贴"""
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

    def _get_info(self):
        """获取视频信息"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("警告", "请输入视频链接")
            return

        if not is_url(url):
            messagebox.showwarning("警告", "请输入有效的 URL")
            return

        self._log("【信息】正在获取视频信息...", "info")

        def get_info_thread():
            try:
                info = self.downloader.get_video_info(url)
                if info:
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
        }

        format_str = format_map.get(self.format_var.get())
        audio_only = self.audio_only_var.get()
        subtitles = self.subtitles_var.get()
        output_path = self.output_var.get()

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
        self.download_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.progress_bar.set(0)
        self.filename_label.configure(text="准备下载...")
        self.stats_label.configure(text="")

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
                    self.message_queue.put(('complete', "【成功】下载完成!"))
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
            self._log("【信息】正在停止下载...", "info")
            self.is_downloading = False
            self._update_ui_state()
            self.filename_label.configure(text="已停止")

    def _clear_log(self):
        """清空日志"""
        self.log_text.delete("1.0", "end")

    def _export_log(self):
        """导出日志"""
        from datetime import datetime
        filename = f"download_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt")],
            initialfile=filename
        )
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get("1.0", "end"))
                messagebox.showinfo("成功", f"日志已导出到:\n{filepath}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {e}")

    def _log(self, message: str, log_type: str = "info"):
        """添加日志"""
        self.message_queue.put(('log', {'message': message, 'type': log_type}))

    def _on_progress(self, data: dict):
        """进度回调"""
        self.message_queue.put(('progress', data))

    def _on_log(self, message: str):
        """日志回调"""
        # 根据消息内容判断类型
        if '成功' in message or '完成' in message:
            log_type = 'success'
        elif '警告' in message or 'Warning' in message:
            log_type = 'warning'
        elif '错误' in message or 'Error' in message or '失败' in message:
            log_type = 'error'
        elif '下载' in message:
            log_type = 'download'
        else:
            log_type = 'info'

        # 添加状态前缀
        if '【' not in message:
            prefixes = {
                'success': '【成功】',
                'error': '【错误】',
                'warning': '【警告】',
                'info': '【信息】',
                'download': '【下载】'
            }
            message = prefixes.get(log_type, '') + message

        self._log(message, log_type)

    def _process_messages(self):
        """处理消息队列"""
        try:
            while True:
                msg_type, data = self.message_queue.get_nowait()

                if msg_type == 'log':
                    from datetime import datetime
                    timestamp = datetime.now().strftime('%H:%M:%S')

                    if isinstance(data, dict):
                        message = data.get('message', '')
                        log_type = data.get('type', 'info')
                    else:
                        message = str(data)
                        log_type = 'info'

                    # 插入日志
                    self.log_text.insert("end", f"[{timestamp}] {message}\n")
                    self.log_text.see("end")

                elif msg_type == 'progress':
                    if data['status'] == 'downloading':
                        percent = data.get('percent', 0)
                        self.progress_bar.set(percent / 100)

                        speed = data.get('speed', 0)
                        speed_str = f"{speed/1024/1024:.1f} MB/s" if speed else "N/A"

                        downloaded = data.get('downloaded', 0)
                        total = data.get('total', 0)

                        eta = data.get('eta', 0)
                        eta_str = format_time(eta) if eta else "N/A"

                        filename = data.get('filename', '')
                        if filename:
                            self.filename_label.configure(text=f"正在下载: {Path(filename).name}")

                        if total > 0:
                            self.stats_label.configure(
                                text=f"速度: {speed_str}  |  已下载: {format_size(downloaded)} / {format_size(total)}  |  剩余: {eta_str}"
                            )
                        else:
                            self.stats_label.configure(
                                text=f"速度: {speed_str}  |  已下载: {format_size(downloaded)}  |  剩余: {eta_str}"
                            )

                    elif data['status'] == 'finished':
                        self.filename_label.configure(text="处理中...")
                        self.stats_label.configure(text="正在合并文件...")

                elif msg_type == 'info':
                    messagebox.showinfo("视频信息", data)

                elif msg_type == 'error':
                    self._log(f"【错误】{data}", "error")
                    messagebox.showerror("错误", data)

                elif msg_type == 'complete':
                    self.progress_bar.set(1.0)
                    self.filename_label.configure(text=data)
                    self.stats_label.configure(text="")
                    self._log(data, "success")
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
            self.download_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
        else:
            self.download_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")


def main():
    """主函数"""
    root = ctk.CTk()
    app = DownloaderGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()