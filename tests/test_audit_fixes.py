import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.models import Exercise, Log
from core.plan_generator import (
    PlannedExercise,
    PlannedSession,
    build_planned_sessions,
    calculate_gym_stats,
    write_planned_sessions,
)
from core.profile_manager import Profile, ProfileManager
from core.xlsx_generator import TrainingLogProcessor
from ui.bridge import WebViewBridgeApi


class TestAuditFixes(unittest.TestCase):
    """Test suite verifying all fixes from the architecture & bug audit."""

    def setUp(self) -> None:
        import core.profile_manager
        self.temp_dir = tempfile.mkdtemp(prefix="ironlog_test_fixes_")
        self.orig_profiles_file = core.profile_manager.PROFILES_FILE
        self.orig_legacy_config = core.profile_manager.LEGACY_CONFIG
        self.orig_root_profiles = core.profile_manager.ROOT_PROFILES_FILE
        core.profile_manager.PROFILES_FILE = os.path.join(self.temp_dir, "test_profiles.json")
        core.profile_manager.LEGACY_CONFIG = os.path.join(self.temp_dir, "test_config.json")
        core.profile_manager.ROOT_PROFILES_FILE = os.path.join(self.temp_dir, "nonexistent.json")

    def tearDown(self) -> None:
        import core.profile_manager
        import shutil
        core.profile_manager.PROFILES_FILE = self.orig_profiles_file
        core.profile_manager.LEGACY_CONFIG = self.orig_legacy_config
        core.profile_manager.ROOT_PROFILES_FILE = self.orig_root_profiles
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_multi_profile_loading(self) -> None:
        """2.1: Multi-profile switching loads target sessions.py rather than stale module."""
        dir_a = os.path.join(self.temp_dir, "profile_a")
        dir_b = os.path.join(self.temp_dir, "profile_b")
        os.makedirs(dir_a, exist_ok=True)
        os.makedirs(dir_b, exist_ok=True)

        file_a = os.path.join(dir_a, "sessions.py")
        file_b = os.path.join(dir_b, "sessions.py")

        with open(file_a, "w", encoding="utf-8") as f:
            f.write('SESSIONS_OWNER = "Alice"\nUSER_SEX = "female"\nBODYMASS_LOG = {"2026-01-01": 60.0}\nUSER_DATA = {}\nEXERCISE_REGISTRY = []\n')

        with open(file_b, "w", encoding="utf-8") as f:
            f.write('SESSIONS_OWNER = "Bob"\nUSER_SEX = "male"\nBODYMASS_LOG = {"2026-01-01": 80.0}\nUSER_DATA = {}\nEXERCISE_REGISTRY = []\n')

        api = WebViewBridgeApi()
        prof_a = Profile(name="Alice", sessions_dir=dir_a, output_dir=dir_a)
        prof_b = Profile(name="Bob", sessions_dir=dir_b, output_dir=dir_b)

        sess_a, path_a = api._load_sessions(prof_a)
        self.assertIsNotNone(sess_a)
        self.assertEqual(sess_a.SESSIONS_OWNER, "Alice")
        self.assertEqual(sys.modules["sessions"].SESSIONS_OWNER, "Alice")

        sess_b, path_b = api._load_sessions(prof_b)
        self.assertIsNotNone(sess_b)
        self.assertEqual(sess_b.SESSIONS_OWNER, "Bob")
        self.assertEqual(sys.modules["sessions"].SESSIONS_OWNER, "Bob")

    def test_split_details_modal_keys(self) -> None:
        """2.2: calculate_gym_stats returns split_sessions_details with date_str, day, and exercises."""
        user_data = {
            "2026-01-01": {"day": 1, "bench-press": Log([8, 8, 8], [80, 80, 80])},
            "2026-01-03": {"day": 2, "squat": Log([5, 5, 5], [120, 120, 120])},
        }
        stats = calculate_gym_stats(user_data)
        self.assertIn("split_sessions_details", stats)
        self.assertIn("split_sessions_dates", stats)
        details = stats["split_sessions_details"]
        self.assertEqual(len(details), 2)
        first = details[0]
        self.assertIn("date_str", first)
        self.assertIn("day", first)
        self.assertIn("exercises", first)
        self.assertIsInstance(first["exercises"], list)
        self.assertEqual(first["day"], 1)

    def test_hyphen_resolution_in_plan_generator(self) -> None:
        """2.3: Hyphenated exercise keys in USER_DATA resolve correctly to variable & display names."""
        sessions_file = os.path.join(self.temp_dir, "sessions.py")
        with open(sessions_file, "w", encoding="utf-8") as f:
            f.write(
                'from core.models import Log, Exercise\n'
                'bench_press = "bench-press"\n'
                'SESSIONS_OWNER = "Tester"\n'
                'USER_SEX = "male"\n'
                'BODYMASS_LOG = {"2026-01-01": 80.0}\n'
                'EXERCISE_REGISTRY = [Exercise(bench_press)]\n'
                'USER_DATA = {\n'
                '    "2026-01-01": {\n'
                '        "day": 1,\n'
                '        "bench-press": Log([8, 8, 8], [80.0, 80.0, 80.0]),\n'
                '    }\n'
                '}\n'
            )
        planned = build_planned_sessions(sessions_file, [1])
        self.assertEqual(len(planned), 1)
        self.assertEqual(len(planned[0].exercises), 1)
        ex = planned[0].exercises[0]
        # Should resolve to defined variable bench_press and proper display name Bench Press
        self.assertEqual(ex.var_name, "bench_press")
        self.assertIn("Bench Press", ex.display_name)

    def test_empty_bodymass_log_raises_value_error(self) -> None:
        """2.4: TrainingLogProcessor raises ValueError (not SystemExit) when BODYMASS_LOG is empty."""
        dummy_out = os.path.join(self.temp_dir, "dummy.xlsx")
        with self.assertRaises(ValueError) as ctx:
            TrainingLogProcessor(dummy_out, [], {}, {})
        self.assertIn("BODYMASS_LOG", str(ctx.exception))

    def test_save_profile_preserves_attributes(self) -> None:
        """2.5: Editing a profile preserves existing non-form attributes."""
        api = WebViewBridgeApi()
        orig_profile = Profile(
            name="ExistingUser",
            sessions_dir=self.temp_dir,
            output_dir=os.path.join(self.temp_dir, "custom_output"),
            age=32,
            sex="male",
            mass=82.5,
            show_pr=False,
            show_standards=False,
            show_milestones=False,
        )
        api.manager.profiles = [orig_profile]
        api.manager.active_profile_index = 0

        # Save edit changing name and sex
        edit_data = {
            "name": "UpdatedUser",
            "sessions_dir": self.temp_dir,
            "sex": "female",
        }
        res = api.save_profile(edit_data, is_edit=True, index=0)
        self.assertTrue(res["success"])

        updated = api.manager.profiles[0]
        self.assertEqual(updated.name, "UpdatedUser")
        self.assertEqual(updated.sex, "female")
        # Preserved attributes
        self.assertEqual(updated.age, 32)
        self.assertEqual(updated.mass, 82.5)
        self.assertFalse(updated.show_pr)
        self.assertFalse(updated.show_standards)
        self.assertFalse(updated.show_milestones)
        self.assertEqual(updated.output_dir, os.path.join(self.temp_dir, "custom_output"))

    def test_remember_last_user_respected(self) -> None:
        """2.6: ProfileManager sets active_profile_index = -1 when remember_last_user is False."""
        pm = ProfileManager()
        pm.profiles = [Profile(name="User1", sessions_dir=self.temp_dir, output_dir=self.temp_dir)]
        pm.active_profile_index = 0
        pm.remember_last_user = False

        profiles_file = os.path.join(self.temp_dir, "test_profiles.json")
        with patch("core.profile_manager.PROFILES_FILE", profiles_file):
            pm.save_profiles()
            # Reload
            pm2 = ProfileManager()
            pm2.load_profiles()
            self.assertEqual(pm2.active_profile_index, -1)

    def test_chart_legend_deletion_when_milestones_false(self) -> None:
        """2.8: generate_charts does not delete primary series when show_milestones=False."""
        out_xlsx = os.path.join(self.temp_dir, "test_charts.xlsx")
        ex = Exercise("squat", "Squat")
        user_data = {
            "2026-01-01": {"squat": Log([5, 5, 5], [100.0, 100.0, 100.0])}
        }
        bodymass_log = {"2026-01-01": 80.0}
        user_profile = {"sex": "male", "show_milestones": False}

        with TrainingLogProcessor(
            out_xlsx, [ex], user_data, bodymass_log, user_profile=user_profile
        ) as proc:
            proc.write_headers()
            proc.process_data(user_data)
            proc.write_calculations()
            proc.generate_charts()
            proc.save()

        self.assertTrue(os.path.exists(out_xlsx))

    def test_write_planned_sessions_robust_brace_and_sanitization(self) -> None:
        """2.9 & 3: write_planned_sessions sanitizes comments/dates and stops at matching closing brace."""
        sessions_file = os.path.join(self.temp_dir, "sessions.py")
        with open(sessions_file, "w", encoding="utf-8") as f:
            f.write(
                'from core.models import Log, Exercise\n'
                'squat = "squat"\n'
                'BODYMASS_LOG = {"2026-01-01": 80.0}\n'
                'EXERCISE_REGISTRY = [Exercise(squat)]\n'
                'USER_DATA = {\n'
                '    "2026-01-01": {\n'
                '        day: 1,\n'
                '        squat: Log([5], [100.0]),\n'
                '    },\n'
                '}\n'
                '# trailing comment after user data\n'
            )

        planned = [
            PlannedSession(
                day_number=2,
                date_str="2026-01-03",
                exercises=[
                    PlannedExercise(
                        var_name="squat",
                        display_name="Squat",
                        sets=3,
                        reps="5, 5, 5",
                        mass="102.5, 102.5, 102.5",
                        comment="line1\nline2 injection attempt",
                    )
                ],
            )
        ]
        write_planned_sessions(sessions_file, planned)

        with open(sessions_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Comment newlines must be sanitized
        self.assertNotIn("\nline2", content)
        self.assertIn("line1 line2 injection attempt", content)
        # File must remain valid syntax
        import ast
        ast.parse(content)

    def test_bodymass_prefill_single_line_dict(self) -> None:
        """2.9: run_bodymass_prefill handles single-line BODYMASS_LOG = {} without corrupting USER_DATA."""
        sessions_file = os.path.join(self.temp_dir, "sessions.py")
        with open(sessions_file, "w", encoding="utf-8") as f:
            f.write(
                'from core.models import Log, Exercise\n'
                'squat = "squat"\n'
                'BODYMASS_LOG = {}\n'
                'EXERCISE_REGISTRY = [Exercise(squat)]\n'
                'USER_DATA = {\n'
                '    "2026-01-05": {\n'
                '        "day": 1,\n'
                '        "squat": Log([5], [100.0]),\n'
                '    },\n'
                '}\n'
            )

        api = WebViewBridgeApi()
        prof = Profile(name="SingleLineUser", sessions_dir=self.temp_dir, output_dir=self.temp_dir)
        api.manager.profiles = [prof]
        api.manager.active_profile_index = 0

        res = api.run_bodymass_prefill()
        self.assertTrue(res["success"])
        self.assertEqual(res["count"], 1)

        with open(sessions_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify BODYMASS_LOG has the entry and USER_DATA is not corrupted
        self.assertIn('"2026-01-05": {"mass": None}', content)
        import ast
        tree = ast.parse(content)
        self.assertIsNotNone(tree)

    def test_updater_rejects_untrusted_url(self) -> None:
        """3: Updater rejects non-whitelisted download URLs."""
        from core.updater import download_and_install_update
        success, err = download_and_install_update("http://malicious-site.com/payload.zip")
        self.assertFalse(success)
        self.assertIn("Untrusted download URL", str(err))

    def test_training_log_processor_context_manager_closes_wb(self) -> None:
        """2.10: TrainingLogProcessor context manager ensures workbook handle is closed."""
        dummy_out = os.path.join(self.temp_dir, "ctx_test.xlsx")
        ex = Exercise("squat", "Squat")
        proc = TrainingLogProcessor(dummy_out, [ex], {}, {"2026-01-01": 80.0})
        with proc:
            self.assertIsNotNone(proc.wb)
        self.assertIsNone(proc.wb)

    def test_syntax_error_captured_and_sys_modules_cleaned(self) -> None:
        """Verify bridge._load_sessions captures SyntaxError detail and cleans sys.modules."""
        bad_dir = os.path.join(self.temp_dir, "syntax_err_profile")
        os.makedirs(bad_dir, exist_ok=True)
        bad_file = os.path.join(bad_dir, "sessions.py")
        with open(bad_file, "w", encoding="utf-8") as f:
            f.write(
                'USER_DATA = {\n'
                '    "2026-01-01": {\n'
                '        "day": 1,\n'
                '        "squat": 8. do try syntax error\n'
                '    }\n'
                '}\n'
            )

        api = WebViewBridgeApi()
        prof = Profile(name="BrokenUser", sessions_dir=bad_dir, output_dir=bad_dir)
        api.manager.profiles = [prof]
        api.manager.active_profile_index = 0

        sess, file_path = api._load_sessions(prof)
        self.assertIsNone(sess)
        self.assertNotIn("sessions", sys.modules)
        self.assertIsNotNone(api._last_sessions_error)
        self.assertIn("SyntaxError in sessions.py", api._last_sessions_error)
        self.assertIn("line 4", api._last_sessions_error)

        active_data = api.get_active_data()
        self.assertFalse(active_data["success"])
        self.assertIn("SyntaxError in sessions.py", active_data["error"])

        excel_data = api.generate_excel()
        self.assertFalse(excel_data["success"])
        self.assertIn("SyntaxError in sessions.py", excel_data["error"])

        validate_data = api.run_validate_sessions()
        self.assertFalse(validate_data["success"])
        self.assertIn("SyntaxError in sessions.py", validate_data["error"])

    def test_plan_generator_clean_sys_modules_on_failure(self) -> None:
        """Verify core.plan_generator._load_sessions_module cleans sys.modules on failure."""
        from core.plan_generator import _load_sessions_module
        bad_dir = os.path.join(self.temp_dir, "plan_syntax_err")
        os.makedirs(bad_dir, exist_ok=True)
        bad_file = os.path.join(bad_dir, "sessions.py")
        with open(bad_file, "w", encoding="utf-8") as f:
            f.write("def broken_syntax(:\n    pass\n")

        with self.assertRaises(SyntaxError):
            _load_sessions_module(bad_file)

        self.assertNotIn("sessions", sys.modules)

    def test_save_profile_strips_quotes_and_py_path(self) -> None:
        """Verify save_profile strips quotes/whitespace and normalizes .py file paths to directories."""
        api = WebViewBridgeApi()
        api.manager.profiles = []
        api.manager.active_profile_index = -1

        sub_dir = os.path.join(self.temp_dir, "quoted_folder")
        os.makedirs(sub_dir, exist_ok=True)
        fake_py = os.path.join(sub_dir, "sessions.py")
        with open(fake_py, "w", encoding="utf-8") as f:
            f.write("# dummy sessions\n")

        # 1. Quoted file path with quotes and whitespace
        quoted_input = f'  "{fake_py}"  '
        res = api.save_profile({"name": "QuotedUser", "sessions_dir": quoted_input, "sex": "male"})
        self.assertTrue(res["success"])
        saved_prof = api.manager.profiles[0]
        self.assertEqual(os.path.normpath(saved_prof.sessions_dir), os.path.normpath(sub_dir))

        # 2. Single-quoted directory path
        quoted_dir = f"  '{sub_dir}'  "
        res2 = api.save_profile({"name": "QuotedDirUser", "sessions_dir": quoted_dir, "sex": "female"})
        self.assertTrue(res2["success"])
        saved_prof2 = api.manager.profiles[1]
        self.assertEqual(os.path.normpath(saved_prof2.sessions_dir), os.path.normpath(sub_dir))

    def test_profile_model_normalizes_paths_on_init(self) -> None:
        """Verify Profile.__init__ automatically strips quotes and normalizes .py paths."""
        py_path = os.path.join(self.temp_dir, "sample.py")
        p = Profile(
            name="InitUser",
            sessions_dir=f'  "{py_path}"  ',
            output_dir='  "C:/custom/out"  ',
        )
        self.assertEqual(os.path.normpath(p.sessions_dir), os.path.normpath(self.temp_dir))
        self.assertEqual(p.output_dir, "C:/custom/out")

    def test_resolve_sessions_file_helper(self) -> None:
        """Verify bridge._resolve_sessions_file resolves both folder and direct file paths."""
        api = WebViewBridgeApi()
        # 1. Folder path
        prof_dir = Profile(name="DirProf", sessions_dir=self.temp_dir, output_dir=self.temp_dir)
        sf, sd = api._resolve_sessions_file(prof_dir)
        self.assertEqual(os.path.normpath(sf), os.path.normpath(os.path.join(self.temp_dir, "sessions.py")))
        self.assertEqual(os.path.normpath(sd), os.path.normpath(self.temp_dir))

        # 2. Explicit .py file path
        custom_file = os.path.join(self.temp_dir, "my_custom_sessions.py")
        prof_file = Profile(name="FileProf", sessions_dir=self.temp_dir, output_dir=self.temp_dir)
        prof_file.sessions_dir = custom_file  # Manually set to file
        sf2, sd2 = api._resolve_sessions_file(prof_file)
        self.assertEqual(os.path.normpath(sf2), os.path.normpath(custom_file))
        self.assertEqual(os.path.normpath(sd2), os.path.normpath(self.temp_dir))

    def test_runtime_error_captured_with_line_number(self) -> None:
        """Verify bridge._load_sessions extracts line number for runtime exceptions (e.g. NameError)."""
        runtime_dir = os.path.join(self.temp_dir, "runtime_err_prof")
        os.makedirs(runtime_dir, exist_ok=True)
        bad_file = os.path.join(runtime_dir, "sessions.py")
        with open(bad_file, "w", encoding="utf-8") as f:
            f.write("val1 = 10\nval2 = 20\ncrash = undefined_variable_here + 5\n")

        api = WebViewBridgeApi()
        prof = Profile(name="RuntimeErrUser", sessions_dir=runtime_dir, output_dir=runtime_dir)
        sess, _ = api._load_sessions(prof)
        self.assertIsNone(sess)
        self.assertNotIn("sessions", sys.modules)
        self.assertIsNotNone(api._last_sessions_error)
        self.assertIn("NameError in sessions.py line 3", api._last_sessions_error)
        self.assertIn("undefined_variable_here", api._last_sessions_error)

    def test_plan_generator_directory_or_file_loading(self) -> None:
        """Verify core.plan_generator._load_sessions_module works when passed directory or file."""
        from core.plan_generator import _load_sessions_module
        plan_dir = os.path.join(self.temp_dir, "plan_mod_test")
        os.makedirs(plan_dir, exist_ok=True)
        sess_file = os.path.join(plan_dir, "sessions.py")
        with open(sess_file, "w", encoding="utf-8") as f:
            f.write("VAL = 42\n")

        # Passing file
        m1 = _load_sessions_module(sess_file)
        self.assertEqual(m1.VAL, 42)

        # Passing directory
        m2 = _load_sessions_module(plan_dir)
        self.assertEqual(m2.VAL, 42)


if __name__ == "__main__":
    unittest.main()

