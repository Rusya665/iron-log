import json
import os
import shutil
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import core.config


class TestConfig(unittest.TestCase):
    """Unit test suite for configuration path resolution and loading."""

    def setUp(self) -> None:
        """
        Create temporary directory and mock configuration path.

        :return: None
        """
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "config.json")
        self.orig_config_file = core.config.CONFIG_FILE
        core.config.CONFIG_FILE = self.config_path

    def tearDown(self) -> None:
        """
        Restore original configuration file path and remove temporary directory.

        :return: None
        """
        core.config.CONFIG_FILE = self.orig_config_file
        shutil.rmtree(self.temp_dir)

    def test_get_drive_paths(self) -> None:
        """
        Verify available cloud drive search returns non-empty list of paths.

        :return: None
        """
        paths = core.config.get_drive_paths()
        self.assertIsInstance(paths, list)
        self.assertGreater(len(paths), 0)

    def test_get_config_reads_existing(self) -> None:
        """
        Verify get_config accurately deserializes existing JSON file values.

        :return: None
        """
        sample = {
            "sessions_dir": "/mock/sessions",
            "output_dir": "/mock/gym",
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(sample, f)

        cfg = core.config.get_config(reconfigure=False)
        self.assertEqual(cfg["sessions_dir"], "/mock/sessions")
        self.assertEqual(cfg["output_dir"], "/mock/gym")


if __name__ == "__main__":
    unittest.main()

