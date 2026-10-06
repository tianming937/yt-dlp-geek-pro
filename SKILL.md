---
name: yt-dlp-downloader
description: 视频下载工具，支持 YouTube 和 1000+ 网站。当用户提供视频链接并要求下载时使用此 Skill。支持单个视频下载、播放列表批量下载、字幕下载等功能。
---

# yt-dlp 视频下载器

基于 yt-dlp 的视频下载工具，支持 YouTube、Bilibili、Twitter 等 1000+ 网站。

## 使用场景

当用户执行以下操作时，应使用此 Skill：
- 提供视频链接要求下载
- 要求下载播放列表/频道视频
- 要求提取视频中的音频
- 要求下载视频字幕
- 询问视频信息（标题、时长、格式等）

## 支持的网站

- YouTube（视频、播放列表、频道）
- Bilibili（哔哩哔哩）
- Twitter/X
- TikTok/抖音
- Vimeo
- 以及 1000+ 其他网站

完整列表：https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md

## 调用方式

### 方式一：命令行（推荐）

```bash
# 进入 Skill 目录
cd yt_dlp_bundle

# 基础下载（最佳质量）
python main.py "视频URL"

# 下载播放列表
python main.py "播放列表URL"

# 下载播放列表的指定范围
python main.py "播放列表URL" --playlist-items 1-10

# 仅下载音频
python main.py "视频URL" --audio-only

# 下载并嵌入字幕
python main.py "视频URL" --subtitles

# 查看视频信息（不下载）
python main.py "视频URL" --info
```

### 方式二：GUI 图形界面

```bash
# 进入 Skill 目录
cd yt_dlp_bundle

# 启动图形界面
python gui/downloader_gui.py
```

或者直接运行启动脚本：
- Windows: 双击 `start.bat`
- Linux/Mac: 运行 `bash start.sh`

## 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `URL` | 视频或播放列表链接 | `python main.py "https://..."` |
| `--audio-only` | 仅下载音频 | `python main.py "URL" --audio-only` |
| `--subtitles` | 下载并嵌入字幕 | `python main.py "URL" --subtitles` |
| `--format FORMAT` | 指定格式 | `python main.py "URL" --format "720p"` |
| `--output PATH` | 指定输出目录 | `python main.py "URL" --output "./videos"` |
| `--playlist-items RANGE` | 播放列表范围 | `python main.py "URL" --playlist-items 1-10` |
| `--info` | 仅显示信息 | `python main.py "URL" --info` |

## 输出位置

- 默认下载目录：`yt_dlp_bundle/downloads/`
- 播放列表会创建独立文件夹：`downloads/播放列表名称/`
- 文件命名格式：`视频标题 [视频ID].扩展名`

## 配置文件

配置文件位于 `config/config.json`，可自定义：
- 默认视频质量
- 输出目录
- 字幕语言偏好
- 文件命名模板

## 依赖要求

- Python 3.11+
- FFmpeg（用于合并视频/音频）

运行 `start.bat` 或 `start.sh` 时会检查 Python 依赖。FFmpeg 不包含在仓库中；可自行安装，Windows 也可运行 `tools/download_ffmpeg.bat`。

## 示例对话

**用户**: 帮我下载这个视频 https://www.youtube.com/watch?v=dQw4w9WgXcQ

**AI 操作**:
```bash
cd yt_dlp_bundle
python main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

**用户**: 下载这个播放列表的前5个视频 https://www.youtube.com/playlist?list=xxx

**AI 操作**:
```bash
cd yt_dlp_bundle
python main.py "https://www.youtube.com/playlist?list=xxx" --playlist-items 1-5
```

**用户**: 我只要这个视频的音频

**AI 操作**:
```bash
cd yt_dlp_bundle
python main.py "视频URL" --audio-only
```

## 错误处理

| 错误 | 解决方案 |
|------|----------|
| "FFmpeg not found" | 运行 `tools/download_ffmpeg.bat` 下载 FFmpeg |
| "Video unavailable" | 视频可能被删除或地区限制 |
| "Private video" | 需要登录或视频为私有 |
| 下载速度慢 | 可能是网络问题，考虑使用代理 |

## 相关链接

- yt-dlp 官方仓库：https://github.com/yt-dlp/yt-dlp
- 支持的网站列表：https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md
