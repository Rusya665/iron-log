import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.models import Log
from core.xlsx_generator import (
    calc_vol,
    calc_avg_mass,
    calc_stdev,
    calc_brzycki,
    METRICS_CONFIG,
)


class TestMetrics(unittest.TestCase):
    def test_calc_vol(self):
        log = Log(reps=[10, 8, 6], mass=[50.0, 60.0, 70.0])
        # 10*50 + 8*60 + 6*70 = 500 + 480 + 420 = 1400.0
        self.assertEqual(calc_vol(log), 1400.0)

    def test_calc_vol_bodyweight(self):
        log = Log(reps=[20, 20, 20], mass=[0.0, 0.0, 0.0])
        self.assertEqual(calc_vol(log), 0.0)

    def test_calc_vol_empty(self):
        log = Log(reps=[], mass=[])
        self.assertEqual(calc_vol(log), 0.0)

    def test_calc_avg_mass(self):
        log = Log(reps=[5, 5, 5], mass=[80.0, 90.0, 100.0])
        self.assertAlmostEqual(calc_avg_mass(log), 90.0)

    def test_calc_avg_mass_empty(self):
        log = Log(reps=[], mass=[])
        self.assertEqual(calc_avg_mass(log), 0)

    def test_calc_stdev(self):
        log = Log(reps=[5, 5], mass=[80.0, 100.0])
        # stdev of [80, 100] is ~14.142
        self.assertAlmostEqual(calc_stdev(log), 14.1421356, places=4)

    def test_calc_stdev_single_or_empty(self):
        log_single = Log(reps=[5], mass=[100.0])
        self.assertEqual(calc_stdev(log_single), 0)
        log_empty = Log(reps=[], mass=[])
        self.assertEqual(calc_stdev(log_empty), 0)

    def test_calc_brzycki_single_rep(self):
        # 1 rep at 100 kg should yield 100 kg
        log = Log(reps=[1], mass=[100.0])
        # 100 * (36 / (37 - 1)) = 100 * 1 = 100.0
        self.assertAlmostEqual(calc_brzycki(log), 100.0)

    def test_calc_brzycki_three_reps(self):
        # 3 reps at 160 kg: 160 * (36 / 34) = 169.41176...
        log = Log(reps=[3], mass=[160.0])
        self.assertAlmostEqual(calc_brzycki(log), 160.0 * (36 / 34), places=4)

    def test_calc_brzycki_multiple_sets_picks_max(self):
        # Set 1: 100kg x 5 -> 100 * (36 / 32) = 112.5
        # Set 2: 110kg x 3 -> 110 * (36 / 34) = 116.47
        log = Log(reps=[5, 3], mass=[100.0, 110.0])
        expected = 110.0 * (36 / 34)
        self.assertAlmostEqual(calc_brzycki(log), expected, places=4)

    def test_calc_brzycki_bodyweight_returns_max_reps(self):
        # When mass is 0 (bodyweight exercise like crunches/pushups), returns max reps
        log = Log(reps=[15, 20, 18], mass=[0.0, 0.0, 0.0])
        self.assertEqual(calc_brzycki(log), 20)

    def test_calc_brzycki_empty(self):
        log = Log(reps=[], mass=[])
        self.assertEqual(calc_brzycki(log), 0)

    def test_calc_brzycki_high_reps_edge_case(self):
        # When reps >= 37, avoids division by zero or negative denominator
        log = Log(reps=[37, 40], mass=[50.0, 40.0])
        self.assertGreater(calc_brzycki(log), 0)

    def test_metrics_config_sanity(self):
        metric_names = [m.name for m in METRICS_CONFIG]
        self.assertIn("Volume", metric_names)
        self.assertIn("Est 1RM", metric_names)
        self.assertIn("Avg Mass", metric_names)
        self.assertIn("Avg Reps", metric_names)


if __name__ == "__main__":
    unittest.main()
