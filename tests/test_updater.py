import os
import sys
import unittest
from typing import List, Tuple
from unittest.mock import MagicMock, patch

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.updater import (
    check_for_updates,
    download_and_install_update,
    get_update_details,
)


class TestUpdater(unittest.TestCase):
    """Unit test suite for GitHub Releases update checking and silent installation."""

    @patch("requests.get")
    def test_check_for_updates_available(self, mock_get: MagicMock) -> None:
        """
        Verify release checking detects when newer version is published.

        :param mock_get: Mocked requests.get call.
        :return: None
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tag_name": "v2.5.0",
            "body": "Bug fixes and improvements",
            "assets": [
                {
                    "name": "IronLog_Setup.exe",
                    "browser_download_url": "https://github.com/Rusya665/iron-log/releases/download/v2.5.0/IronLog_Setup.exe",
                    "size": 52428800,
                }
            ],
        }
        mock_get.return_value = mock_response

        has_update, new_ver, url = check_for_updates("2.0.0")
        self.assertTrue(has_update)
        self.assertEqual(new_ver, "2.5.0")
        self.assertIn("IronLog_Setup.exe", url)

        details = get_update_details("2.0.0")
        self.assertTrue(details["has_update"])
        self.assertEqual(details["latest_version"], "2.5.0")
        self.assertEqual(details["release_notes"], "Bug fixes and improvements")
        self.assertEqual(details["asset_size"], 52428800)

    @patch("requests.get")
    def test_check_for_updates_already_latest(
        self, mock_get: MagicMock
    ) -> None:
        """
        Verify release checking reports no updates when running latest release.

        :param mock_get: Mocked requests.get call.
        :return: None
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tag_name": "v2.0.0",
            "assets": [],
        }
        mock_get.return_value = mock_response

        has_update, new_ver, url = check_for_updates("2.0.0")
        self.assertFalse(has_update)
        self.assertIsNone(new_ver)
        self.assertIsNone(url)

        details = get_update_details("2.0.0")
        self.assertFalse(details["has_update"])

    @patch("requests.get")
    def test_check_for_updates_network_error(self, mock_get: MagicMock) -> None:
        """
        Verify network exceptions during release check fail gracefully.

        :param mock_get: Mocked requests.get call.
        :return: None
        """
        mock_get.side_effect = Exception("Network offline")

        has_update, new_ver, url = check_for_updates("2.0.0")
        self.assertFalse(has_update)
        self.assertIsNone(new_ver)
        self.assertIsNone(url)

    @patch("subprocess.Popen")
    @patch("requests.get")
    def test_download_and_install_update(
        self, mock_get: MagicMock, mock_popen: MagicMock
    ) -> None:
        """
        Verify downloading binary stream and triggering silent installer subprocess.

        :param mock_get: Mocked requests.get call.
        :param mock_popen: Mocked subprocess.Popen call.
        :return: None
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-length": "100"}
        mock_response.iter_content.return_value = [b"a" * 50, b"b" * 50]
        mock_response.__enter__.return_value = mock_response
        mock_get.return_value = mock_response

        progress_calls: List[Tuple[int, int, float]] = []

        def _prog(dl: int, tot: int, pct: float) -> None:
            progress_calls.append((dl, tot, pct))

        ok, err = download_and_install_update(
            "https://example.com/IronLog_Setup.exe", progress_callback=_prog
        )
        self.assertTrue(ok)
        self.assertIsNone(err)
        self.assertTrue(len(progress_calls) >= 2)
        mock_popen.assert_called_once()


if __name__ == "__main__":
    unittest.main()


