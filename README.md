# yt-dlp 视频下载器（极客碎碎念 Pro 版）

一个基于 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 的 Python 桌面下载器，提供 CustomTkinter 图形界面和命令行入口。普通网站由 yt-dlp 处理；微信视频号分享链接由可选的本地 [wx_channel](https://github.com/nobiyou/wx_channel) 服务处理。本项目不是 yt-dlp 或 wx_channel 的官方发行版。

## 当前功能

- 下载 yt-dlp 支持的单个视频和播放列表，并可指定播放列表范围。
- 提取 MP3、M4A、Opus、FLAC 或 WAV 音频；可选择音质。
- 下载可用字幕，并在 FFmpeg 可用时尝试嵌入视频。
- 通过 GUI 查看进度、速度和日志；也可使用命令行。
- 在 Windows 上通过外部 wx_channel 服务尝试下载微信视频号分享链接。

不同网站的可用格式、字幕和登录要求由网站及 yt-dlp 决定。微信视频号功能属于可选集成，详见下文。

## 环境要求

- Python **3.11 或更新版本**；目前在 Windows 和 Python 3.11.9 上测试。
- [FFmpeg](https://ffmpeg.org/download.html)：合并音视频、提取音频和嵌入字幕时需要。仓库**不包含** FFmpeg。
- 访问目标网站所需的网络环境。部分网站可能要求浏览器登录或 cookies。
- 微信视频号集成仅面向 Windows，需登录微信电脑版并打开一个视频号视频页面。

其他桌面系统尚未做完整 GUI 验收。项目依赖版本见 [requirements.txt](requirements.txt)。

## 安装与启动

```powershell
# Windows PowerShell
 git clone https://github.com/tianming937/yt-dlp-geek-pro.git
 cd yt-dlp-geek-pro
 py -3.11 -m venv .venv
 .\.venv\Scripts\Activate.ps1
 python -m pip install -r requirements.txt
 python main.py --gui
```

在 macOS/Linux 中，将虚拟环境创建命令换为 `python3 -m venv .venv`，激活命令换为 `source .venv/bin/activate`。安装 FFmpeg 后，运行 `ffmpeg -version` 检查是否在 PATH 中。

Windows 也可以双击 `一键启动.bat`；`start.bat` 会检查并安装缺失的 Python 依赖。命令行入口不需要 GUI：

```powershell
python main.py "https://example.com/video"
python main.py "URL" --audio-only --audio-format mp3 --audio-quality 192kbps
python main.py "PLAYLIST_URL" --playlist-items 1-10
python main.py "URL" --subtitles
python main.py "URL" --output "D:\Videos"
python main.py "URL" --info
python main.py --help
```

`--format` 接受 **yt-dlp 格式选择表达式**，例如 `"bv*[height<=720]+ba/b[height<=720]"`；单独写 `720p` 并不一定是有效格式 ID。

## 配置

程序有内置默认设置。要自定义，先把 [config/config.example.json](config/config.example.json) 复制为 `config/config.json`，再编辑副本。后者是本机配置，已被 Git 忽略。可设置下载目录、文件名模板、字幕语言、代理及 cookies 文件路径。不要提交 cookies、账号信息或包含敏感参数的日志。

默认文件保存在项目的 `downloads/` 目录；该目录里的媒体和下载记录不会进入 Git 仓库。GUI 中手动指定的路径会覆盖默认下载路径。

## 微信视频号集成（可选）

本仓库**不分发** `wx_channel.exe`、其证书、设备指纹、下载数据库或本机 `config.yaml`。如需使用：

1. 从 [wx_channel 上游项目](https://github.com/nobiyou/wx_channel/releases)获取与你的 Windows 环境兼容的版本，并自行核实其来源与权限要求。
2. 将可执行文件放到 `tools/wx_channel/wx_channel.exe`，或在本机 `config/config.json` 中设置 `wx_channel_exe`。
3. 配置上游服务使用本机端口 `2025`，并将其下载目录指向本项目的 `downloads/`。本适配器要求服务健康接口报告至少 `5.6.8`；上游 API 变化可能需要适配。
4. 登录微信电脑版，打开任意视频号视频页面，再粘贴 `weixin.qq.com/sph/...` 或 `channels.weixin.qq.com/finder-preview/pages/sph?id=...` 链接。

适配器可能以管理员权限启动该程序；首次运行可能涉及本地代理证书安装。请先阅读上游说明。微信视频号采用服务返回的原视频格式，GUI 的仅音频、画质和字幕选项在此场景不适用。本仓库的自动测试使用模拟接口，不能代替真实微信环境验收。

## 测试

```powershell
python -m unittest discover -s tests -v
```

测试覆盖下载错误传播、代理/cookies 元数据请求、微信链接识别和任务结果判断。当前没有覆盖所有目标网站、GUI 自动化及真实微信环境。

## 已知限制

- 当前 GUI 的“停止”按钮只改变界面状态，不能可靠中断后台下载。请不要把它当作真正的取消操作。
- 普通视频下载会在正式下载前额外获取一次元数据；在网络不稳定时会增加等待。
- 微信视频号依赖独立服务和微信桌面端；上游版本变化可能影响兼容性。
- FFmpeg、微信服务及其运行数据需要用户自行准备，不属于本仓库源码。

欢迎通过 [Issues](https://github.com/tianming937/yt-dlp-geek-pro/issues) 提交可复现的问题。提交时请删除日志中的私人链接、cookies 和账号信息。

## 许可证与致谢

本仓库源码采用 [MIT License](LICENSE)。第三方依赖保留各自许可：[yt-dlp 为 Unlicense](https://github.com/yt-dlp/yt-dlp/blob/master/LICENSE)，[CustomTkinter 为 MIT](https://github.com/TomSchimansky/CustomTkinter/blob/master/LICENSE)，[wx_channel 为 MIT](https://github.com/nobiyou/wx_channel/blob/main/LICENSE)。FFmpeg 的许可取决于所使用的构建，本仓库不分发其二进制文件。
