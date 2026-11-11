import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.standards import (
    EXERCISE_STANDARDS,
    get_exercise_standard,
    get_tiered_standards,
)


class TestStandards(unittest.TestCase):
    """Unit test suite for strength standards querying and weight-class rounding."""

    def test_exercise_standards_presence(self) -> None:
        """
        Verify presence of staple benchmark exercises in the standards database.

        :return: None
        """
        self.assertIn("bench-press", EXERCISE_STANDARDS)
        self.assertIn("squat", EXERCISE_STANDARDS)
        self.assertIn("deadlift", EXERCISE_STANDARDS)

    def test_get_exercise_standard_bench(self) -> None:
        """
        Verify target lifted weight standard lookup for bench press.

        :return: None
        """
        bodymass_log = {"2026-09-01": {"mass": 80.0}}
        std_int = get_exercise_standard(
            exercise_id="bench-press",
            target_date_str="2026-09-01",
            bodymass_log=bodymass_log,
            level="Intermediate",
            sex="male",
        )
        self.assertGreater(std_int, 0)

    def test_get_exercise_standard_missing_slug_returns_zero(self) -> None:
        """
        Verify unmapped exercise slugs cleanly return 0.

        :return: None
        """
        bodymass_log = {"2026-09-01": {"mass": 80.0}}
        val = get_exercise_standard(
            "nonexistent_exercise_123", "2026-09-01", bodymass_log
        )
        self.assertEqual(val, 0)

    def test_get_tiered_standards(self) -> None:
        """
        Verify tiered standards dictionary contains Beginner, Intermediate, and Elite tiers.

        :return: None
        """
        tiers = get_tiered_standards("bench-press", sex="male", body_mass=80.0)
        self.assertIsNotNone(tiers)
        self.assertIn(80, tiers)
        self.assertIn("Beginner", tiers[80])
        self.assertIn("Intermediate", tiers[80])
        self.assertIn("Elite", tiers[80])
        # Elite standard must be higher than Beginner
        self.assertGreater(tiers[80]["Elite"], tiers[80]["Beginner"])

    def test_weight_class_ceiling_over_85(self) -> None:
        """
        Verify ceiling rule assigns weight class 90kg when athlete exceeds 85kg.

        :return: None
        """
        # When body mass is 86.45 (>85), it should select the 90kg tier
        bodymass_log = {"2026-09-01": {"mass": 86.45}}
        std_90 = get_exercise_standard(
            "squat",
            "2026-09-01",
            bodymass_log,
            level="Intermediate",
            sex="male",
        )
        # Standard for 90kg male intermediate squat is 146
        self.assertEqual(std_90, 146)

    def test_bridge_calculate_target_bm_no_hardcoded_fallback(self) -> None:
        """
        Verify ceiling weight calculation and absence of hardcoded fallback numbers.

        :return: None
        """
        from ui.bridge import WebViewBridgeApi

        # 86.45 kg -> 90 kg
        self.assertEqual(WebViewBridgeApi._calculate_target_bm(86.45), 90)
        # 85.0 kg -> 85 kg
        self.assertEqual(WebViewBridgeApi._calculate_target_bm(85.0), 85)
        # 85.05 kg -> 90 kg
        self.assertEqual(WebViewBridgeApi._calculate_target_bm(85.05), 90)
        # None or 0 -> None (NO 80kg hardcoded fallback!)
        self.assertIsNone(WebViewBridgeApi._calculate_target_bm(None))
        self.assertIsNone(WebViewBridgeApi._calculate_target_bm(0))
        self.assertIsNone(WebViewBridgeApi._calculate_target_bm(-5.0))

    def test_dual_calisthenics_reps_vs_weighted_standards(self) -> None:
        """
        Verify calisthenics lifts expose both bodyweight reps and added-kg weighted standards.

        :return: None
        """
        bodymass_log = {"2026-09-24": {"mass": 86.45}}  # 90kg weight class
        # Reps mode (default): Elite pull-ups = 30 reps
        reps_elite = get_exercise_standard(
            "pull-ups", "2026-11-10", bodymass_log, level="Elite", sex="male", weighted=False
        )
        self.assertEqual(reps_elite, 30)

        # Weighted mode (+kg belt): Intermediate pull-ups = 35 kg, Elite = 79 kg
        kg_int = get_exercise_standard(
            "pull-ups", "2026-11-10", bodymass_log, level="Intermediate", sex="male", weighted=True
        )
        kg_elite = get_exercise_standard(
            "pull-ups", "2026-11-10", bodymass_log, level="Elite", sex="male", weighted=True
        )
        self.assertEqual(kg_int, 35)
        self.assertEqual(kg_elite, 79)

        # Dips weighted mode (+kg belt): Novice = 30 kg, Intermediate = 57 kg at 90 kg class
        dips_nov = get_exercise_standard(
            "dips", "2026-11-10", bodymass_log, level="Novice", sex="male", weighted=True
        )
        self.assertEqual(dips_nov, 30)


if __name__ == "__main__":
    unittest.main()

