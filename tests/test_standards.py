import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.standards import get_exercise_standard, get_tiered_standards, EXERCISE_STANDARDS


class TestStandards(unittest.TestCase):
    def test_exercise_standards_presence(self):
        self.assertIn("bench-press", EXERCISE_STANDARDS)
        self.assertIn("squat", EXERCISE_STANDARDS)
        self.assertIn("deadlift", EXERCISE_STANDARDS)

    def test_get_exercise_standard_bench(self):
        bodymass_log = {
            "2026-09-01": {"mass": 80.0}
        }
        std_int = get_exercise_standard(
            exercise_id="bench-press",
            target_date_str="2026-09-01",
            bodymass_log=bodymass_log,
            level="Intermediate",
            sex="male"
        )
        self.assertGreater(std_int, 0)

    def test_get_exercise_standard_missing_slug_returns_zero(self):
        bodymass_log = {"2026-09-01": {"mass": 80.0}}
        val = get_exercise_standard("nonexistent_exercise_123", "2026-09-01", bodymass_log)
        self.assertEqual(val, 0)

    def test_get_tiered_standards(self):
        tiers = get_tiered_standards("bench-press", sex="male", body_mass=80.0)
        self.assertIsNotNone(tiers)
        self.assertIn(80, tiers)
        self.assertIn("Beginner", tiers[80])
        self.assertIn("Intermediate", tiers[80])
        self.assertIn("Elite", tiers[80])
        # Elite standard must be higher than Beginner
        self.assertGreater(tiers[80]["Elite"], tiers[80]["Beginner"])


if __name__ == "__main__":
    unittest.main()
