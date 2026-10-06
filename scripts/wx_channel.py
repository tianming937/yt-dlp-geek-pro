#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Local wx_channel integration for WeChat Channels share links."""

import ctypes
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from urllib.parse import parse_qs, unquote, urlparse

import requests


PUBLIC_FEED_INFO_URL = (
    "https://channels.weixin.qq.com/finder-preview/api/feed/get_feed_info"
)


class WxChannelError(RuntimeError):
    """A user-facing wx_channel integration error."""


def is_wechat_channels_url(url: str) -> bool:
    try:
        parsed = urlparse(url.strip())
    except (TypeError, ValueError):
        return False

    host = parsed.netloc.lower().split(":", 1)[0]
    path = parsed.path.lower()
    if host == "weixin.qq.com" and path.startswith("/sph/"):
        return True
    return (
        host == "channels.weixin.qq.com"
        and path.startswith("/finder-preview/pages/sph")
        and bool(parse_qs(parsed.query).get("id"))
    )


def extract_short_uri(url: str) -> str:
    if not is_wechat_channels_url(url):
        raise WxChannelError("不是受支持的微信视频号分享链接")

    parsed = urlparse(url.strip())
    if parsed.netloc.lower().split(":", 1)[0] == "weixin.qq.com":
        value = parsed.path.split("/sph/", 1)[1].split("/", 1)[0]
    else:
        value = parse_qs(parsed.query).get("id", [""])[0]

    value = unquote(value).strip()
    if not value:
        raise WxChannelError("微信视频号链接缺少 shortUri")
    return value


def _version_tuple(value: str) -> tuple:
    parts = []
    for item in str(value).lstrip("vV").split("."):
        digits = "".join(ch for ch in item if ch.isdigit())
        if not digits:
            break
        parts.append(int(digits))
    return tuple(parts)


class WxChannelClient:
    def __init__(
        self,
        base_dir: Path,
        config: Optional[Dict[str, Any]] = None,
        session=None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None,
        launcher: Optional[Callable[[Path], None]] = None,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ):
        self.base_dir = Path(base_dir).resolve()
        self.config = config or {}
        self.session = session or requests.Session()
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.launcher = launcher or self._launch_executable
        self.sleep = sleep
        self.monotonic = monotonic
        self.api_base = self.config.get(
            "wx_channel_api_url", "http://127.0.0.1:2025"
        ).rstrip("/")

    def _log(self, message: str) -> None:
        if self.log_callback:
            self.log_callback(message)

    def _request_json(
        self,
        method: str,
        url: str,
        *,
        timeout: float = 10,
        **kwargs,
    ) -> Dict[str, Any]:
        try:
            response = self.session.request(method, url, timeout=timeout, **kwargs)
        except Exception as exc:
            raise WxChannelError(f"无法连接 wx_channel: {exc}") from exc

        try:
            payload = response.json()
        except Exception as exc:
            text = getattr(response, "text", "")
            raise WxChannelError(
                f"wx_channel 返回了无效响应: {text[:200]}"
            ) from exc

        status_code = getattr(response, "status_code", 200)
        if status_code >= 400:
            message = payload.get("message") if isinstance(payload, dict) else ""
            raise WxChannelError(message or f"wx_channel HTTP {status_code}")
        if isinstance(payload, dict):
            if payload.get("success") is False:
                raise WxChannelError(payload.get("message") or "wx_channel 请求失败")
            code = payload.get("code")
            if code not in (None, 0, 200):
                raise WxChannelError(
                    payload.get("message") or f"wx_channel 错误码: {code}"
                )
        return payload

    @staticmethod
    def _data(payload: Dict[str, Any]) -> Dict[str, Any]:
        data = payload.get("data") if isinstance(payload, dict) else None
        return data if isinstance(data, dict) else payload

    def _resolve_executable(self) -> Path:
        configured = self.config.get("wx_channel_exe", "")
        if configured:
            path = Path(configured)
            if not path.is_absolute():
                path = self.base_dir / path
        else:
            path = self.base_dir / "tools" / "wx_channel" / "wx_channel.exe"
        return path.resolve()

    @staticmethod
    def _launch_executable(executable: Path) -> None:
        if not executable.exists():
            raise WxChannelError(f"未找到 wx_channel: {executable}")

        config_path = executable.parent / "config.yaml"
        parameters = f'--config "{config_path}"' if config_path.exists() else ""
        if sys.platform == "win32":
            result = ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                str(executable),
                parameters,
                str(executable.parent),
                1,
            )
            if result <= 32:
                raise WxChannelError("wx_channel 启动被取消或失败")
            return

        command = [str(executable)]
        if config_path.exists():
            command.extend(["--config", str(config_path)])
        subprocess.Popen(
            command,
            cwd=str(executable.parent),
            start_new_session=True,
        )

    def ensure_service(self) -> Dict[str, Any]:
        health_url = f"{self.api_base}/api/health"
        try:
            health = self._request_json("GET", health_url, timeout=2)
        except WxChannelError:
            executable = self._resolve_executable()
            self._log(f"正在启动本地 wx_channel: {executable}")
            self.launcher(executable)

            deadline = self.monotonic() + float(
                self.config.get("wx_channel_startup_timeout", 120)
            )
            last_error = None
            while self.monotonic() < deadline:
                try:
                    health = self._request_json("GET", health_url, timeout=2)
                    break
                except WxChannelError as exc:
                    last_error = exc
                    self.sleep(1)
            else:
                raise WxChannelError(
                    "wx_channel 启动超时；请确认已允许管理员权限和证书安装"
                ) from last_error

        data = self._data(health)
        version = str(data.get("version", ""))
        if version and _version_tuple(version) < (5, 6, 8):
            raise WxChannelError(
                f"当前 wx_channel {version} 不支持 sph 分享短链，请从上游获取支持该接口的版本"
            )
        return data

    def ensure_wechat_ready(self) -> Dict[str, Any]:
        payload = self._request_json(
            "GET", f"{self.api_base}/api/channels/status", timeout=5
        )
        data = self._data(payload)
        ready_clients = int(data.get("ready_clients") or 0)
        if ready_clients <= 0:
            raise WxChannelError(
                "微信电脑版的视频号页面尚未就绪。请在微信电脑版中打开任意视频号视频，"
                "保持页面打开后再重试"
            )
        return data

    def get_video_info(self, url: str) -> Dict[str, Any]:
        short_uri = extract_short_uri(url)
        headers = {
            "Origin": "https://channels.weixin.qq.com",
            "Referer": (
                "https://channels.weixin.qq.com/finder-preview/pages/sph"
                f"?id={short_uri}"
            ),
        }
        payload = self._request_json(
            "POST",
            PUBLIC_FEED_INFO_URL,
            timeout=15,
            headers=headers,
            json={"baseReq": {"generalToken": ""}, "shortUri": short_uri},
        )

        err_code = payload.get("errCode", payload.get("err_code", 0))
        if err_code not in (None, 0):
            raise WxChannelError(
                payload.get("errMsg") or f"微信分享信息错误码: {err_code}"
            )

        data = payload.get("data") or {}
        feed = data.get("feedInfo") or {}
        author = data.get("authorInfo") or {}
        scene = data.get("sceneInfo") or {}
        video_id = scene.get("dynamicExportId") or short_uri
        title = feed.get("description") or f"微信视频号-{short_uri}"

        duration_ms = (
            feed.get("durationMs")
            or feed.get("videoDuration")
            or (feed.get("videoPlayLen") or 0) * 1000
        )
        return {
            "id": str(video_id),
            "title": str(title).strip(),
            "uploader": str(author.get("nickname") or "未知作者").strip(),
            "thumbnail": feed.get("coverUrl") or feed.get("coverURL"),
            "timestamp": feed.get("createTime"),
            "duration": float(duration_ms or 0) / 1000,
            "webpage_url": url,
            "extractor": "wx_channel",
            "_type": "video",
        }

    def _resolve_share(self, url: str) -> Dict[str, Any]:
        try:
            payload = self._request_json(
                "POST",
                f"{self.api_base}/api/channels/share/resolve",
                timeout=70,
                json={"urls": [url], "mode": "page"},
            )
        except WxChannelError as exc:
            if "404" in str(exc) or "not found" in str(exc).lower():
                raise WxChannelError(
                    "当前 wx_channel 不支持 sph 分享短链，请检查上游版本与本项目接口是否兼容"
                ) from exc
            raise

        data = self._data(payload)
        resolved = data.get("resolved") or []
        if resolved:
            return resolved[0]

        failed = data.get("failed") or []
        reason = failed[0].get("error") if failed else "未返回视频地址"
        raise WxChannelError(f"微信视频号链接解析失败: {reason}")

    def _validate_output_path(self, output_path: Optional[str]) -> None:
        if not output_path:
            return
        expected = self.config.get(
            "wx_channel_download_path",
            self.config.get("download_path", "./downloads"),
        )
        expected_path = Path(expected)
        if not expected_path.is_absolute():
            expected_path = self.base_dir / expected_path
        requested_path = Path(output_path)
        if not requested_path.is_absolute():
            requested_path = self.base_dir / requested_path
        if requested_path.resolve() != expected_path.resolve():
            raise WxChannelError(
                f"微信视频固定保存到 {expected_path.resolve()}；"
                "请修改 wx_channel_download_path 并重启 wx_channel"
            )

    def download(self, url: str, output_path: Optional[str] = None) -> bool:
        self._validate_output_path(output_path)
        self.ensure_service()
        self.ensure_wechat_ready()
        self._log("正在通过本地 wx_channel 解析微信视频号链接...")
        item = self._resolve_share(url)

        task_id = str(item.get("id") or extract_short_uri(url))
        item["id"] = task_id
        start_payload = self._request_json(
            "POST",
            f"{self.api_base}/__wx_channels_api/batch_start",
            timeout=15,
            json={
                "videos": [item],
                "forceRedownload": False,
                "pageSource": "yt_dlp_bundle",
            },
        )
        start_data = self._data(start_payload)
        if int(start_data.get("total") or 0) < 1:
            raise WxChannelError("wx_channel 未接受下载任务")

        deadline = self.monotonic() + float(
            self.config.get("wx_channel_download_timeout", 1800)
        )
        poll_interval = float(self.config.get("wx_channel_poll_interval", 1))
        while self.monotonic() < deadline:
            payload = self._request_json(
                "POST",
                f"{self.api_base}/__wx_channels_api/batch_progress",
                timeout=10,
            )
            data = self._data(payload)
            tasks = data.get("tasks") or []
            task = next(
                (entry for entry in tasks if str(entry.get("id")) == task_id),
                None,
            )
            if task:
                status = task.get("status")
                percent = float(task.get("progress") or 0)
                if self.progress_callback:
                    self.progress_callback(
                        {
                            "status": (
                                "finished" if status == "done" else "downloading"
                            ),
                            "percent": percent,
                            "downloaded": float(task.get("downloadedMB") or 0)
                            * 1024
                            * 1024,
                            "total": float(task.get("totalMB") or 0)
                            * 1024
                            * 1024,
                            "speed": 0,
                            "eta": 0,
                            "filename": item.get("title", ""),
                        }
                    )
                if status == "done":
                    return True
                if status == "failed":
                    raise WxChannelError(
                        f"微信视频下载失败: {task.get('error') or '未知错误'}"
                    )
            if int(data.get("failed") or 0) > 0:
                raise WxChannelError("微信视频下载失败，wx_channel 未返回详细原因")
            self.sleep(poll_interval)

        raise WxChannelError("微信视频下载超时")
