import unittest
from pathlib import Path

from scripts.wx_channel import (
    WxChannelClient,
    WxChannelError,
    is_wechat_channels_url,
)


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code
        self.text = str(payload)

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        if not self.responses:
            raise AssertionError(f"Unexpected request: {method} {url}")
        return self.responses.pop(0)


class WxChannelClientTests(unittest.TestCase):
    def test_recognizes_supported_wechat_share_urls(self):
        self.assertTrue(
            is_wechat_channels_url("https://weixin.qq.com/sph/ALHtQpYO9I")
        )
        self.assertTrue(
            is_wechat_channels_url(
                "https://channels.weixin.qq.com/finder-preview/pages/sph?id=ALHtQpYO9I"
            )
        )
        self.assertFalse(is_wechat_channels_url("https://www.bilibili.com/video/BV1x"))

    def test_get_video_info_uses_public_share_metadata(self):
        session = FakeSession(
            [
                FakeResponse(
                    {
                        "errCode": 0,
                        "data": {
                            "feedInfo": {
                                "description": "测试标题",
                                "coverUrl": "https://example.com/cover.jpg",
                                "createTime": 1710000000,
                            },
                            "authorInfo": {"nickname": "测试作者"},
                            "sceneInfo": {"dynamicExportId": "export/test"},
                        },
                    }
                )
            ]
        )
        client = WxChannelClient(
            base_dir=Path("D:/app"),
            config={},
            session=session,
        )

        info = client.get_video_info("https://weixin.qq.com/sph/ALHtQpYO9I")

        self.assertEqual("测试标题", info["title"])
        self.assertEqual("测试作者", info["uploader"])
        self.assertEqual("export/test", info["id"])
        method, url, kwargs = session.calls[0]
        self.assertEqual("POST", method)
        self.assertIn("get_feed_info", url)
        self.assertEqual("ALHtQpYO9I", kwargs["json"]["shortUri"])

    def test_download_resolves_share_and_waits_for_batch_success(self):
        item = {
            "id": "video-id",
            "title": "测试标题",
            "authorName": "测试作者",
            "url": "https://example.com/video.mp4",
            "key": "decrypt-key",
            "headers": {
                "Origin": "https://channels.weixin.qq.com",
                "Referer": "https://channels.weixin.qq.com/finder-preview/pages/feed",
            },
        }
        session = FakeSession(
            [
                FakeResponse({"success": True, "data": {"version": "5.6.8"}}),
                FakeResponse(
                    {
                        "code": 0,
                        "data": {"connected": True, "ready_clients": 1},
                    }
                ),
                FakeResponse(
                    {
                        "code": 0,
                        "data": {"resolved": [item], "failed": []},
                    }
                ),
                FakeResponse({"code": 0, "data": {"total": 1}}),
                FakeResponse(
                    {
                        "code": 0,
                        "data": {
                            "total": 1,
                            "done": 0,
                            "failed": 0,
                            "tasks": [
                                {
                                    "id": "video-id",
                                    "status": "downloading",
                                    "progress": 42,
                                }
                            ],
                        },
                    }
                ),
                FakeResponse(
                    {
                        "code": 0,
                        "data": {
                            "total": 1,
                            "done": 1,
                            "failed": 0,
                            "tasks": [
                                {
                                    "id": "video-id",
                                    "status": "done",
                                    "progress": 100,
                                }
                            ],
                        },
                    }
                ),
            ]
        )
        progress = []
        client = WxChannelClient(
            base_dir=Path("D:/app"),
            config={"wx_channel_poll_interval": 0},
            session=session,
            progress_callback=progress.append,
        )

        self.assertTrue(client.download("https://weixin.qq.com/sph/ALHtQpYO9I"))
        self.assertEqual(100, progress[-1]["percent"])
        self.assertEqual(
            "http://127.0.0.1:2025/api/channels/share/resolve",
            session.calls[2][1],
        )
        self.assertEqual(
            "http://127.0.0.1:2025/__wx_channels_api/batch_start",
            session.calls[3][1],
        )

    def test_not_ready_error_explains_how_to_prepare_wechat(self):
        session = FakeSession(
            [
                FakeResponse({"success": True, "data": {"version": "5.6.8"}}),
                FakeResponse(
                    {
                        "code": 0,
                        "data": {"connected": False, "ready_clients": 0},
                    }
                ),
            ]
        )
        client = WxChannelClient(
            base_dir=Path("D:/app"),
            config={},
            session=session,
        )

        with self.assertRaisesRegex(WxChannelError, "微信电脑版.*视频号"):
            client.download("https://weixin.qq.com/sph/ALHtQpYO9I")

    def test_share_resolution_error_is_preserved(self):
        session = FakeSession(
            [
                FakeResponse({"success": True, "data": {"version": "5.6.8"}}),
                FakeResponse(
                    {
                        "code": 0,
                        "data": {"connected": True, "ready_clients": 1},
                    }
                ),
                FakeResponse(
                    {
                        "code": 0,
                        "data": {
                            "resolved": [],
                            "failed": [
                                {
                                    "inputUrl": "https://weixin.qq.com/sph/test",
                                    "error": "page response missing media url",
                                }
                            ],
                        },
                    }
                ),
            ]
        )
        client = WxChannelClient(
            base_dir=Path("D:/app"),
            config={},
            session=session,
        )

        with self.assertRaisesRegex(WxChannelError, "missing media url"):
            client.download("https://weixin.qq.com/sph/test")

    def test_failed_batch_task_is_reported_as_failure(self):
        item = {
            "id": "video-id",
            "title": "测试标题",
            "authorName": "测试作者",
            "url": "https://example.com/video.mp4",
        }
        session = FakeSession(
            [
                FakeResponse({"success": True, "data": {"version": "5.6.8"}}),
                FakeResponse(
                    {
                        "code": 0,
                        "data": {"connected": True, "ready_clients": 1},
                    }
                ),
                FakeResponse(
                    {
                        "code": 0,
                        "data": {"resolved": [item], "failed": []},
                    }
                ),
                FakeResponse({"code": 0, "data": {"total": 1}}),
                FakeResponse(
                    {
                        "code": 0,
                        "data": {
                            "total": 1,
                            "done": 0,
                            "failed": 1,
                            "tasks": [
                                {
                                    "id": "video-id",
                                    "status": "failed",
                                    "error": "CDN rejected request",
                                }
                            ],
                        },
                    }
                ),
            ]
        )
        client = WxChannelClient(
            base_dir=Path("D:/app"),
            config={"wx_channel_poll_interval": 0},
            session=session,
        )

        with self.assertRaisesRegex(WxChannelError, "CDN rejected request"):
            client.download("https://weixin.qq.com/sph/ALHtQpYO9I")

    def test_unrelated_completed_task_does_not_count_as_success(self):
        session = FakeSession(
            [
                FakeResponse({"success": True, "data": {"version": "5.6.8"}}),
                FakeResponse({"code": 0, "data": {"ready_clients": 1}}),
                FakeResponse({"code": 0, "data": {"resolved": [{"id": "wanted"}]} }),
                FakeResponse({"code": 0, "data": {"total": 1}}),
                FakeResponse(
                    {"code": 0, "data": {"tasks": [{"id": "another", "status": "done"}]}}
                ),
            ]
        )
        ticks = iter([0, 0, 1])
        client = WxChannelClient(
            base_dir=Path("D:/app"),
            config={"wx_channel_download_timeout": 1, "wx_channel_poll_interval": 0},
            session=session,
            monotonic=lambda: next(ticks),
            sleep=lambda _: None,
        )

        with self.assertRaisesRegex(WxChannelError, "超时"):
            client.download("https://weixin.qq.com/sph/ALHtQpYO9I")


if __name__ == "__main__":
    unittest.main()
