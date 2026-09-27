import os
import sys
import unittest
from unittest.mock import MagicMock, patch

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ui.desktop import WebViewBridgeApi
from core.profile_manager import Profile


class TestDesktopBridge(unittest.TestCase):
    def setUp(self):
        self.api = WebViewBridgeApi()

    def test_get_and_toggle_settings(self):
        settings = self.api.get_settings()
        self.assertIn("auto_login", settings)
        self.assertIn("show_pr", settings)
        
        orig_auto_login = settings["auto_login"]
        new_settings = self.api.toggle_setting("auto_login")
        self.assertEqual(new_settings["auto_login"], not orig_auto_login)
        
        # Toggle back
        restored_settings = self.api.toggle_setting("auto_login")
        self.assertEqual(restored_settings["auto_login"], orig_auto_login)

    def test_search_standards(self):
        results = self.api.search_standards("bench")
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        first = results[0]
        self.assertIn("name", first)
        self.assertIn("beg", first)
        self.assertIn("int", first)

    def test_restore_pre_deload_no_profile(self):
        self.api.manager.get_active_profile = MagicMock(return_value=None)
        res = self.api.restore_pre_deload()
        self.assertFalse(res["success"])
        self.assertIn("error", res)


if __name__ == "__main__":
    unittest.main()
