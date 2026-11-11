import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.models import Log
from core.plan_generator import (
    _is_deload_block,
    _next_date_after,
    _suggest_progression,
    build_planned_sessions,
    build_pre_deload_baseline,
    calculate_gym_stats,
    days_to_generate,
    detect_cycle,
    get_deload_dates,
)


class TestPlanGenerator(unittest.TestCase):
    """Unit test suite for split cycle detection and planned session generation."""

    def test_detect_cycle_full(self) -> None:
        """
        Verify completed training cycle detection for a 3-day split.

        :return: None
        """
        # 3-day split: Day 1, 2, 3, 1, 2, 3
        user_data = {
            "2026-09-01": {"day": 1},
            "2026-09-03": {"day": 2},
            "2026-09-05": {"day": 3},
            "2026-09-08": {"day": 1},
            "2026-09-10": {"day": 2},
            "2026-09-12": {"day": 3},
        }
        cycle_len, last_day = detect_cycle(user_data)
        self.assertEqual(cycle_len, 3)
        self.assertEqual(last_day, 3)

    def test_detect_cycle_midway(self) -> None:
        """
        Verify partial split detection when cycle is only partially completed.

        :return: None
        """
        # 3-day split where only Day 1 of the new cycle is completed
        user_data = {
            "2026-09-01": {"day": 1},
            "2026-09-03": {"day": 2},
            "2026-09-05": {"day": 3},
            "2026-09-08": {"day": 1},
        }
        cycle_len, last_day = detect_cycle(user_data)
        self.assertEqual(cycle_len, 3)
        self.assertEqual(last_day, 1)

    def test_detect_cycle_four_day_split(self) -> None:
        """
        Verify split cycle length detection on 4-day training schedule.

        :return: None
        """
        user_data = {
            "2026-09-01": {"day": 1},
            "2026-09-03": {"day": 2},
            "2026-09-05": {"day": 3},
            "2026-09-07": {"day": 4},
            "2026-09-09": {"day": 1},
            "2026-09-11": {"day": 2},
        }
        cycle_len, last_day = detect_cycle(user_data)
        self.assertEqual(cycle_len, 4)
        self.assertEqual(last_day, 2)

    def test_detect_cycle_empty_or_single(self) -> None:
        """
        Verify cycle detection handling for empty or single session histories.

        :return: None
        """
        self.assertEqual(detect_cycle({}), (None, None))
        self.assertEqual(detect_cycle({"2026-09-01": {"day": 1}}), (1, 1))

    def test_days_to_generate(self) -> None:
        """
        Verify remaining cycle day sequences to generate based on completed day.

        :return: None
        """
        # Completed cycle -> start new full cycle [1, 2, 3]
        self.assertEqual(days_to_generate(3, 3), [1, 2, 3])
        # Completed day 1 of 3 -> remaining is [2, 3]
        self.assertEqual(days_to_generate(3, 1), [2, 3])
        # Completed day 2 of 4 -> remaining is [3, 4]
        self.assertEqual(days_to_generate(4, 2), [3, 4])
        # Last day exceeds N -> full cycle
        self.assertEqual(days_to_generate(3, 4), [1, 2, 3])

    def test_suggest_progression_uniform(self) -> None:
        """
        Verify progression suggestions when all sets share identical weight and reps.

        :return: None
        """
        reps = [5, 5, 5]
        mass = [100.0, 100.0, 100.0]
        prog = _suggest_progression(reps, mass)
        self.assertEqual(prog["sets"], 3)
        self.assertEqual(prog["reps"], "5")
        self.assertEqual(prog["mass"], "100")

    def test_suggest_progression_varied(self) -> None:
        """
        Verify progression suggestions when sets feature ascending or varying values.

        :return: None
        """
        reps = [5, 4, 3]
        mass = [100.0, 102.5, 105.0]
        prog = _suggest_progression(reps, mass)
        self.assertEqual(prog["sets"], 3)
        self.assertEqual(prog["reps"], "5, 4, 3")
        self.assertEqual(prog["mass"], "100, 102.5, 105")

    def test_suggest_progression_float_reps(self) -> None:
        """
        Verify floating point rep values format cleanly to integers.

        :return: None
        """
        reps = [6.0, 6.0, 6.0]
        mass = [20.0, 20.0, 20.0]
        prog = _suggest_progression(reps, mass)
        self.assertEqual(prog["reps"], "6")

    def test_next_date_after(self) -> None:
        """
        Verify projected dates alternate by 2 days from the latest logged workout.

        :return: None
        """
        user_data = {"2026-09-10": {}}
        dates = _next_date_after(user_data, 3)
        self.assertEqual(dates, ["2026-09-12", "2026-09-14", "2026-09-16"])

    def test_is_deload_block(self) -> None:
        """
        Verify detection of deload keywords within python source lines.

        :return: None
        """
        deload_lines = [
            "        squat: Log([3, 3, 3], [80, 80, 80]),  # 20% decreased deload",
            "        crunches: Log([20, 20], [0, 0]),",
        ]
        normal_lines = [
            "        squat: Log([3, 3, 3], [100, 100, 100]),  # +2.5 kg",
            "        crunches: Log([20, 20], [0, 0]),",
        ]
        self.assertTrue(_is_deload_block(deload_lines))
        self.assertFalse(_is_deload_block(normal_lines))

    def test_build_pre_deload_baseline_integration(self) -> None:
        """
        Verify baseline generation correctly skips deload blocks and recovers pre-deload masses.

        :return: None
        """
        temp_dir = tempfile.mkdtemp()
        sessions_file = os.path.join(temp_dir, "sessions.py")

        sample_code = """
from core.models import Log

day = "day"
squat = "squat"
deadlift = "deadlift"

USER_DATA = {
    "2026-09-10": {  # Day 1
        day: 1,
        squat: Log([3, 3, 3], [100, 100, 100]),  # clean heavy
    },
    "2026-09-12": {  # Day 2
        day: 2,
        deadlift: Log([3, 3, 3], [160, 160, 160]),  # clean heavy
    },
    "2026-09-15": {  # Day 1
        day: 1,
        squat: Log([3, 3, 3], [80, 80, 80]),  # 20% decreased deload
    },
    "2026-09-17": {  # Day 2
        day: 2,
        deadlift: Log([3, 3, 3], [128, 128, 128]),  # 20% decreased deload
    },
}
"""
        try:
            with open(sessions_file, "w", encoding="utf-8") as f:
                f.write(sample_code)

            # Request days [1, 2] at 100% pre-deload
            planned = build_pre_deload_baseline(sessions_file, [1, 2], 100.0)
            self.assertEqual(len(planned), 2)

            # Day 1 should have pre-deload squat at 100 kg, NOT the 80 kg deload
            day1_ex = {e.var_name: e for e in planned[0].exercises}
            self.assertIn("squat", day1_ex)
            self.assertEqual(day1_ex["squat"].mass, "100")

            # Day 2 should have pre-deload deadlift at 160 kg, NOT the 128 kg deload
            day2_ex = {e.var_name: e for e in planned[1].exercises}
            self.assertIn("deadlift", day2_ex)
            self.assertEqual(day2_ex["deadlift"].mass, "160")

            # Test scaling factor (e.g. 90% pre-deload)
            planned_scaled = build_pre_deload_baseline(sessions_file, [1], 90.0)
            day1_scaled_ex = {e.var_name: e for e in planned_scaled[0].exercises}
            # 100 * 0.9 = 90.0
            self.assertEqual(day1_scaled_ex["squat"].mass, "90")
        finally:
            shutil.rmtree(temp_dir)

    def test_calculate_gym_stats(self) -> None:
        """
        Verify workout count, latest date, and latest split day aggregations.

        :return: None
        """
        user_data = {
            "2026-01-05": {"day": 1, "squat": Log([5], [100])},
            "2026-01-07": {"day": 2, "bench": Log([5], [80])},
            "2026-01-09": {"day": 3, "deadlift": Log([5], [140])},
        }
        stats = calculate_gym_stats(user_data)
        self.assertEqual(stats["total_days"], 3)
        self.assertEqual(stats["latest_workout_date"], "2026-01-09")
        self.assertEqual(stats["latest_workout_day"], 3)

    def test_build_planned_sessions_alternating_exercises(self) -> None:
        """
        Verify planner rotates alternating Week A / Week B exercises and restores pre-deload alternation.

        :return: None
        """
        temp_dir = tempfile.mkdtemp()
        sessions_file = os.path.join(temp_dir, "sessions.py")

        sample_code = """
from core.models import Log

day = "day"
bench_press = "bench-press"
dumbbell_bench_press = "dumbbell-bench-press"
dips = "dips"
pull_ups = "pull-ups"

USER_DATA = {
    "2026-11-26": {  # Day 3
        day: 3,
        bench_press: Log([4, 4, 4], [85, 85, 85]),
        dumbbell_bench_press: Log([8, 8, 8], [27.5, 27.5, 27.5]),
        pull_ups: Log([6, 6, 6], [15, 15, 15]),
    },
    "2026-12-03": {  # Day 3
        day: 3,
        bench_press: Log([4, 4, 4], [87.5, 87.5, 87.5]),
        dips: Log([8, 8, 8], [15, 15, 15]),
        pull_ups: Log([6, 6, 6], [17.5, 17.5, 17.5]),
    },
}
"""
        try:
            with open(sessions_file, "w", encoding="utf-8") as f:
                f.write(sample_code)

            # After Week A (DB Bench 27.5) -> Week B (Dips 15), Week 3 must plan DB Bench @ 27.5
            planned_w3 = build_planned_sessions(sessions_file, [3])
            self.assertEqual(len(planned_w3), 1)
            w3_vars = [e.var_name for e in planned_w3[0].exercises]
            self.assertEqual(w3_vars, ["bench_press", "dumbbell_bench_press", "pull_ups"])
            w3_map = {e.var_name: e for e in planned_w3[0].exercises}
            self.assertEqual(w3_map["dumbbell_bench_press"].mass, "27.5")
            self.assertEqual(w3_map["bench_press"].mass, "87.5")

            # Add Week 3 (DB Bench 30) + Week 4 Deload, then verify pre-deload restores Dips @ 15
            idx = sample_code.rfind("}")
            sample_code_with_deload = (
                sample_code[:idx]
                + """    "2026-12-10": {  # Day 3
        day: 3,
        bench_press: Log([3, 3, 3], [90, 90, 90]),
        dumbbell_bench_press: Log([8, 8, 8], [30, 30, 30]),
        pull_ups: Log([6, 6, 6], [20, 20, 20]),
    },
    "2026-12-17": {  # Day 3
        day: 3,
        bench_press: Log([3, 3, 3], [70, 70, 70]),  # deload
        dumbbell_bench_press: Log([8, 8, 8], [22.5, 22.5, 22.5]),  # deload
        pull_ups: Log([6, 6, 6], [10, 10, 10]),  # deload
    },
}
"""
            )
            with open(sessions_file, "w", encoding="utf-8") as f:
                f.write(sample_code_with_deload)

            restored = build_pre_deload_baseline(sessions_file, [3], 100.0)
            restored_vars = [e.var_name for e in restored[0].exercises]
            self.assertEqual(restored_vars, ["bench_press", "dips", "pull_ups"])
            restored_map = {e.var_name: e for e in restored[0].exercises}
            self.assertEqual(restored_map["dips"].mass, "15")
        finally:
            shutil.rmtree(temp_dir)

    def test_build_planned_sessions_rare_substitute_guard(self) -> None:
        """
        Verify a rare 1-off substitute neither hijacks an established primary nor prevents recovery to it.

        :return: None
        """
        temp_dir = tempfile.mkdtemp()
        sessions_file = os.path.join(temp_dir, "sessions.py")

        # Day 1 has 4x Smith + 1x Seated (latest is Smith -> should stay Smith)
        # Day 2 has 3x Smith then 1x Seated (latest is Seated -> should recover to Smith)
        sample_code = """
from core.models import Log

day = "day"
squat = "squat"
pause_squat = "pause-squat"
dead_lift = "deadlift"
pause_deadlift = "pause-deadlift"
crunches = "crunches"
smith_calf = "smith-calf"
seated_calf = "seated-calf"

USER_DATA = {
    "2026-10-01": {day: 1, squat: Log([5], [100]), pause_squat: Log([5], [80]), smith_calf: Log([8], [20]), crunches: Log([15], [0])},
    "2026-10-03": {day: 2, dead_lift: Log([5], [140]), pause_deadlift: Log([5], [115]), smith_calf: Log([8], [25]), crunches: Log([15], [0])},
    "2026-10-08": {day: 1, squat: Log([5], [100]), pause_squat: Log([5], [80]), smith_calf: Log([8], [20]), crunches: Log([15], [0])},
    "2026-10-10": {day: 2, dead_lift: Log([5], [140]), pause_deadlift: Log([5], [115]), smith_calf: Log([8], [25]), crunches: Log([15], [0])},
    "2026-10-15": {day: 1, squat: Log([5], [100]), pause_squat: Log([5], [80]), smith_calf: Log([8], [20]), crunches: Log([15], [0])},
    "2026-10-17": {day: 2, dead_lift: Log([5], [140]), pause_deadlift: Log([5], [115]), smith_calf: Log([8], [30]), crunches: Log([15], [0])},
    "2026-10-22": {day: 1, squat: Log([5], [100]), pause_squat: Log([5], [80]), seated_calf: Log([8], [55]), crunches: Log([15], [0])},
    "2026-10-29": {day: 1, squat: Log([5], [100]), pause_squat: Log([5], [80]), smith_calf: Log([8], [22.5]), crunches: Log([15], [0])},
    "2026-11-01": {day: 2, dead_lift: Log([5], [140]), pause_deadlift: Log([5], [115]), seated_calf: Log([8], [50]), crunches: Log([15], [0])},
}
"""
        try:
            with open(sessions_file, "w", encoding="utf-8") as f:
                f.write(sample_code)

            planned = build_planned_sessions(sessions_file, [1, 2])
            d1_vars = [e.var_name for e in planned[0].exercises]
            d2_vars = [e.var_name for e in planned[1].exercises]
            self.assertEqual(d1_vars, ["squat", "pause_squat", "smith_calf", "crunches"])
            self.assertEqual(d2_vars, ["dead_lift", "pause_deadlift", "smith_calf", "crunches"])
        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main()

