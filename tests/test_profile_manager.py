import os
import sys
import unittest
import tempfile
import shutil
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.profile_manager import Profile, ProfileManager


class TestProfileManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.profiles_path = os.path.join(self.temp_dir, "profiles.json")
        self.legacy_path = os.path.join(self.temp_dir, "config.json")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_profile_to_dict(self):
        p = Profile(
            name="Alice",
            sessions_dir="/path/to/sessions",
            output_dir="/path/to/output",
            age=28,
            sex="female",
            mass=65.0,
            show_pr=True,
            show_standards=False,
            show_milestones=True,
        )
        data = p.to_dict()
        self.assertEqual(data["name"], "Alice")
        self.assertEqual(data["sex"], "female")
        self.assertEqual(data["mass"], 65.0)
        self.assertFalse(data["show_standards"])

    def test_profile_manager_persistence(self):
        import core.profile_manager
        orig_file = core.profile_manager.PROFILES_FILE
        orig_legacy = core.profile_manager.LEGACY_CONFIG
        core.profile_manager.PROFILES_FILE = self.profiles_path
        core.profile_manager.LEGACY_CONFIG = self.legacy_path

        try:
            pm = ProfileManager()
            self.assertEqual(len(pm.profiles), 0)

            # Add profiles
            p1 = Profile(name="User1", sessions_dir="/s1", output_dir="/o1")
            p2 = Profile(name="User2", sessions_dir="/s2", output_dir="/o2")
            pm.add_profile(p1)
            pm.add_profile(p2)
            pm.set_active(1)

            # Reload fresh instance
            pm2 = ProfileManager()
            self.assertEqual(len(pm2.profiles), 2)
            self.assertEqual(pm2.active_profile_index, 1)
            active = pm2.get_active_profile()
            self.assertIsNotNone(active)
            self.assertEqual(active.name, "User2")

            # Update profile
            p2_updated = Profile(name="User2-Edited", sessions_dir="/s2_new", output_dir="/o2_new")
            pm2.update_profile(1, p2_updated)
            self.assertEqual(pm2.get_active_profile().name, "User2-Edited")

            # Delete profile
            pm2.delete_profile(0)
            self.assertEqual(len(pm2.profiles), 1)
            self.assertEqual(pm2.profiles[0].name, "User2-Edited")
        finally:
            core.profile_manager.PROFILES_FILE = orig_file
            core.profile_manager.LEGACY_CONFIG = orig_legacy


if __name__ == "__main__":
    unittest.main()
