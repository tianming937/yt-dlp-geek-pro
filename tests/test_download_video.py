import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.download_video import VideoDownloader


class VideoDownloaderErrorHandlingTests(unittest.TestCase):
    @patch("scripts.download_video.yt_dlp.YoutubeDL")
    def test_nonzero_yt_dlp_exit_code_is_reported_as_failure(self, youtube_dl):
        ydl = MagicMock()
        ydl.extract_info.return_value = {"id": "video-id", "_type": "video"}
        ydl.download.return_value = 1
        youtube_dl.return_value.__enter__.return_value = ydl

        downloader = VideoDownloader()

        self.assertFalse(downloader.download("https://example.com/video"))
        self.assertIn("yt-dlp", downloader.last_error)

    @patch("scripts.download_video.yt_dlp.YoutubeDL")
    def test_metadata_probe_uses_configured_proxy_and_cookies(self, youtube_dl):
        with tempfile.TemporaryDirectory() as temp:
            cookie_file = Path(temp) / "cookies.txt"
            cookie_file.write_text("", encoding="utf-8")
            config_file = Path(temp) / "config.json"
            config_file.write_text(
                json.dumps(
                    {"proxy": "http://127.0.0.1:7890", "cookies_file": str(cookie_file)}
                ),
                encoding="utf-8",
            )
            youtube_dl.return_value.__enter__.return_value.extract_info.return_value = {
                "id": "video-id", "_type": "video"
            }

            downloader = VideoDownloader(config_path=str(config_file))
            self.assertIsNotNone(downloader.get_video_info("https://example.com/video"))
            options = youtube_dl.call_args.args[0]
            self.assertEqual("http://127.0.0.1:7890", options["proxy"])
            self.assertEqual(str(cookie_file), options["cookiefile"])


if __name__ == "__main__":
    unittest.main()
