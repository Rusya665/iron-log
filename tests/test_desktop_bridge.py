import os
import sys
import unittest
from unittest.mock import MagicMock, patch

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ui.desktop import WebViewBridgeApi  # noqa: E402


class TestDesktopBridge(unittest.TestCase):
    """Unit test suite for the pywebview desktop bridge interface."""

    def setUp(self) -> None:
        """
        Initialize the bridge API instance.

        :return: None
        """
        self.api = WebViewBridgeApi()

    def test_get_and_toggle_settings(self) -> None:
        """
        Verify retrieving settings dictionary and toggling boolean setting values.

        :return: None
        """
        settings = self.api.get_settings()
        self.assertIn("auto_login", settings)
        self.assertIn("show_pr", settings)

        orig_auto_login = settings["auto_login"]
        new_settings = self.api.toggle_setting("auto_login")
        self.assertEqual(new_settings["auto_login"], not orig_auto_login)

        # Toggle back
        restored_settings = self.api.toggle_setting("auto_login")
        self.assertEqual(restored_settings["auto_login"], orig_auto_login)

    def test_search_standards(self) -> None:
        """
        Verify fuzzy standard search returns matching tier records.

        :return: None
        """
        results = self.api.search_standards("bench")
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        first = results[0]
        self.assertIn("name", first)
        self.assertIn("beg", first)
        self.assertIn("int", first)

    def test_restore_pre_deload_no_profile(self) -> None:
        """
        Verify restore_pre_deload fails gracefully when no profile is active.

        :return: None
        """
        self.api.manager.get_active_profile = MagicMock(return_value=None)
        res = self.api.restore_pre_deload()
        self.assertFalse(res["success"])
        self.assertIn("error", res)

    @patch("ui.bridge.get_update_details")
    def test_check_updates(self, mock_details: MagicMock) -> None:
        """
        Verify check_updates formats update metadata response.

        :param mock_details: Mocked get_update_details function.
        :return: None
        """
        mock_details.return_value = {
            "has_update": True,
            "current_version": "2.0.0",
            "latest_version": "2.1.0",
            "download_url": "https://example.com/IronLog_Setup.exe",
            "release_notes": "Awesome features",
            "asset_size": 123456,
        }
        res = self.api.check_updates()
        self.assertTrue(res["has_update"])
        self.assertEqual(res["version"], "2.1.0")
        self.assertEqual(res["url"], "https://example.com/IronLog_Setup.exe")
        self.assertEqual(res["notes"], "Awesome features")

    def test_update_status_initial(self) -> None:
        """
        Verify initial update status payload structure.

        :return: None
        """
        status = self.api.get_update_status()
        self.assertIn("state", status)
        self.assertIn("percent", status)


if __name__ == "__main__":
    unittest.main()

