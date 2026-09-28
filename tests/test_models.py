import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.models import Exercise, Log


class TestModels(unittest.TestCase):
    """Unit test suite for Exercise and Log data models."""

    def test_log_initialization(self) -> None:
        """
        Verify Log dataclass correctly stores reps and mass lists.

        :return: None
        """
        log = Log(reps=[5, 5, 5], mass=[100.0, 100.0, 102.5])
        self.assertEqual(log.reps, [5, 5, 5])
        self.assertEqual(log.mass, [100.0, 100.0, 102.5])

    def test_log_empty(self) -> None:
        """
        Verify Log dataclass accepts empty sequence fields.

        :return: None
        """
        log = Log(reps=[], mass=[])
        self.assertEqual(len(log.reps), 0)
        self.assertEqual(len(log.mass), 0)

    def test_exercise_default_display_name(self) -> None:
        """
        Verify Exercise dataclass defaults display_name to id.

        :return: None
        """
        ex = Exercise(id="bench_press")
        self.assertEqual(ex.id, "bench_press")
        self.assertEqual(ex.display_name, "bench_press")

    def test_exercise_custom_display_name(self) -> None:
        """
        Verify Exercise dataclass retains explicit display_name.

        :return: None
        """
        ex = Exercise(id="bench_press", display_name="Bench Press (Barbell)")
        self.assertEqual(ex.id, "bench_press")
        self.assertEqual(ex.display_name, "Bench Press (Barbell)")


if __name__ == "__main__":
    unittest.main()

