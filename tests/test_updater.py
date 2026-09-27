import os
import sys
import unittest
from unittest.mock import patch, MagicMock

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.updater import check_for_updates


class TestUpdater(unittest.TestCase):
    @patch("requests.get")
    def test_check_for_updates_available(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tag_name": "v2.5.0",
            "assets": [
                {
                    "name": "IronLog_Setup.exe",
                    "browser_download_url": "https://github.com/Rusya665/iron-log/releases/download/v2.5.0/IronLog_Setup.exe",
                }
            ],
        }
        mock_get.return_value = mock_response

        has_update, new_ver, url = check_for_updates("2.0.0")
        self.assertTrue(has_update)
        self.assertEqual(new_ver, "2.5.0")
        self.assertIn("IronLog_Setup.exe", url)

    @patch("requests.get")
    def test_check_for_updates_already_latest(self, mock_get):
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

    @patch("requests.get")
    def test_check_for_updates_network_error(self, mock_get):
        mock_get.side_effect = Exception("Network offline")

        has_update, new_ver, url = check_for_updates("2.0.0")
        self.assertFalse(has_update)
        self.assertIsNone(new_ver)
        self.assertIsNone(url)


if __name__ == "__main__":
    unittest.main()
