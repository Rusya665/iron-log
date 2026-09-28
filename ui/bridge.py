"""Python backend bridge API for Iron Log PyWebView GUI."""

import glob
import importlib
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser
from datetime import datetime
from typing import Any, Dict, List, Optional

import webview

from core.models import Log
from core.plan_generator import (
    PlannedExercise,
    PlannedSession,
    build_planned_sessions,
    calculate_gym_stats,
    days_to_generate,
    detect_cycle,
    write_planned_sessions,
)
from core.profile_manager import Profile, ProfileManager
from core.standards import EXERCISE_STANDARDS, get_tiered_standards
from core.updater import (
    download_and_install_update,
    get_update_details,
)
from core.version import __version__
from core.xlsx_generator import TrainingLogProcessor
from ui import window_manager
from ui.templates import PLANNER_HTML_TEMPLATE


class WebViewBridgeApi:
    """Python backend bridge API matching 100% of CustomTkinter engine features."""

    def __init__(self):
        self.manager = ProfileManager()
        self.last_gen_time = ""
        self.update_status = {
            "state": "idle",
            "downloaded": 0,
            "total": 0,
            "percent": 0.0,
            "error": None,
        }

    def _load_sessions(self, p: Profile):
        sessions_file = getattr(p, "sessions_file", None) or os.path.join(p.sessions_dir, "sessions.py")
        if not os.path.exists(sessions_file):
            return None, sessions_file

        sessions_dir = os.path.dirname(sessions_file)
        if sessions_dir not in sys.path:
            sys.path.insert(0, sessions_dir)

        if "sessions" in sys.modules:
            sess = importlib.reload(sys.modules["sessions"])
        else:
            import sessions as sess
        return sess, sessions_file

    def open_planner_window(self):
        """Spawns the Dynamic Plan Cycler as a dedicated standalone window."""
        planner_win = window_manager.get_planner_window()
        if planner_win:
            try:
                planner_win.show()
                return {"success": True}
            except Exception:
                window_manager.set_planner_window(None)

        new_planner = webview.create_window(
            title="Iron Log - Plan Next Cycle",
            html=PLANNER_HTML_TEMPLATE,
            js_api=self,
            width=1100,
            height=750,
            min_size=(860, 560),
            background_color="#0A0D14",
        )
        window_manager.set_planner_window(new_planner)
        return {"success": True}

    def get_settings(self) -> Dict[str, Any]:
        p = self.manager.get_active_profile()
        return {
            "auto_login": self.manager.remember_last_user,
            "auto_update": self.manager.auto_check_updates,
            "show_pr": getattr(p, "show_pr", True) if p else True,
            "show_standards": getattr(p, "show_standards", True) if p else True,
            "show_milestones": getattr(p, "show_milestones", True) if p else True,
        }

    def toggle_setting(self, setting_name: str) -> Dict[str, Any]:
        p = self.manager.get_active_profile()
        if setting_name == "auto_login":
            self.manager.remember_last_user = not self.manager.remember_last_user
        elif setting_name == "auto_update":
            self.manager.auto_check_updates = not self.manager.auto_check_updates
        elif p and hasattr(p, setting_name):
            setattr(p, setting_name, not getattr(p, setting_name))
        self.manager.save_profiles()
        return self.get_settings()

    def get_profiles(self) -> Dict[str, Any]:
        return {
            "active_index": self.manager.active_profile_index,
            "profiles": [p.to_dict() for p in self.manager.profiles],
        }

    def select_profile(self, index: int) -> Dict[str, Any]:
        self.manager.set_active(index)
        return {"success": True}

    def save_profile(self, profile_data: Dict[str, Any], is_edit: bool = False, index: int = 0) -> Dict[str, Any]:
        name = profile_data.get("name", "").strip()
        s_dir = profile_data.get("sessions_dir", "").strip()
        sex = profile_data.get("sex", "male")

        if not name:
            return {"success": False, "error": "Profile name cannot be empty."}
        if not s_dir:
            return {"success": False, "error": "Data folder path cannot be empty."}

        new_p = Profile(
            name=name,
            sessions_dir=s_dir,
            output_dir=os.path.join(s_dir, "gym"),
            sex=sex,
        )
        if is_edit:
            self.manager.update_profile(index, new_p)
        else:
            self.manager.add_profile(new_p)
            self.manager.set_active(len(self.manager.profiles) - 1)
        return {"success": True}

    def delete_profile(self, index: int) -> Dict[str, Any]:
        if 0 <= index < len(self.manager.profiles):
            self.manager.delete_profile(index)
            return {"success": True}
        return {"success": False, "error": "Invalid profile index"}

    def browse_folder(self) -> str:
        import tkinter as tk
        from tkinter import filedialog
        r = tk.Tk()
        r.withdraw()
        r.attributes("-topmost", True)
        path = filedialog.askdirectory(parent=r)
        r.destroy()
        return path or ""

    def check_updates(self) -> Dict[str, Any]:
        info = get_update_details(__version__)
        return {
            "has_update": info["has_update"],
            "version": info["latest_version"],
            "url": info["download_url"],
            "current": __version__,
            "notes": info["release_notes"],
            "size": info["asset_size"],
        }

    def start_update(self, download_url: str) -> Dict[str, Any]:
        """Initiates the background download and silent update process."""
        self.update_status = {
            "state": "downloading",
            "downloaded": 0,
            "total": 0,
            "percent": 0.0,
            "error": None,
        }

        def _worker():
            def _progress(dl: int, total: int, pct: float):
                self.update_status["downloaded"] = dl
                self.update_status["total"] = total
                self.update_status["percent"] = round(pct, 1)

            ok, err = download_and_install_update(download_url, progress_callback=_progress)
            if not ok:
                self.update_status["state"] = "error"
                self.update_status["error"] = err or "Download failed"
                return

            self.update_status["state"] = "installing"
            self.update_status["percent"] = 100.0

            # Brief pause so frontend can render the "Restarting to install..." UI
            time.sleep(1.2)

            window_manager.destroy_all_windows()
            os._exit(0)

        threading.Thread(target=_worker, daemon=True).start()
        return {"success": True}

    def get_update_status(self) -> Dict[str, Any]:
        """Returns the current state of the update download / installation."""
        return self.update_status

    def get_active_data(self) -> Dict[str, Any]:
        p = self.manager.get_active_profile()
        if not p:
            return {"success": False, "error": "No profile selected"}

        sess, file_path = self._load_sessions(p)
        if not sess:
            return {"success": False, "error": f"sessions.py not found at {file_path}"}

        user_data = getattr(sess, "USER_DATA", {})
        bm_log = getattr(sess, "BODYMASS_LOG", {})
        stats = calculate_gym_stats(user_data)

        date_pat = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        sorted_dates = sorted([d for d in user_data.keys() if date_pat.match(d)], reverse=True)
        N, _ = detect_cycle(user_data)
        show_dates = sorted_dates[: N if N else 3]

        recent_sessions = []
        for d_str in reversed(show_dates):
            day_data = user_data[d_str]
            v = day_data.get("day")
            day_obj = v if isinstance(v, (int, str)) else None

            # Resolve mass for date
            mass = None
            if bm_log:
                for d in sorted(bm_log.keys()):
                    if d <= d_str:
                        bm_entry = bm_log[d]
                        mass = bm_entry if isinstance(bm_entry, (int, float)) else bm_entry.get("mass", 0)
                    else:
                        break

            exs = []
            for ex_id, log in day_data.items():
                if not isinstance(log, Log):
                    continue
                info = EXERCISE_STANDARDS.get(ex_id, {})
                display_name = info.get("name", ex_id)

                # Format reps
                n_sets = len(log.reps)
                if len(set(log.reps)) == 1:
                    reps_part = f"{n_sets} × {log.reps[0]}"
                else:
                    reps_part = "-".join(str(r) for r in log.reps)

                # Format mass
                max_lift = max(log.mass) if log.mass else 0
                if log.mass and max(log.mass) > 0:
                    if len(set(log.mass)) == 1:
                        mass_part = f" @ {log.mass[0]}kg"
                    else:
                        mass_part = f" @ {min(log.mass)}-{max(log.mass)}kg"
                else:
                    mass_part = " (BW)"
                    max_lift = mass if mass else 0

                summary = f"{reps_part}{mass_part}"
                exs.append({
                    "id": ex_id,
                    "name": display_name,
                    "summary": summary,
                    "max_lift": max_lift,
                })

            recent_sessions.append({
                "date": d_str,
                "day": day_obj,
                "mass": mass,
                "exercises": exs,
            })

        clean_stats = {
            "total_days": stats.get("total_days", 0),
            "this_year_days": stats.get("this_year_days", 0),
            "this_month_days": stats.get("this_month_days", 0),
            "latest_workout_date": stats.get("latest_workout_date", "N/A"),
            "latest_workout_day": stats.get("latest_workout_day", "N/A"),
            "current_split_weeks": stats.get("current_split_weeks", 0.0),
            "current_split_start": stats.get("current_split_start", "N/A"),
            "cycle_length": stats.get("cycle_length", "N/A"),
            "split_days_exercises": stats.get("split_days_exercises", {}),
            "split_sessions_details": [
                {"date_str": s.get("date_str", ""), "day": s.get("day", ""), "exercises": list(s.get("exercises", []))}
                for s in stats.get("split_sessions_details", [])
            ],
        }

        return {
            "success": True,
            "profile_name": p.name,
            "stats": clean_stats,
            "sessions": recent_sessions,
        }

    def _resolve_user_mass(self, explicit_mass: Optional[float] = None) -> Optional[float]:
        """Resolves user mass dynamically without any hardcoded fallbacks.
        Order of precedence:
        1. Explicit mass passed (e.g. from session hover, if > 0)
        2. Latest logged mass in sessions.py BODYMASS_LOG
        3. Profile configured mass (if > 0)
        Returns None if no mass is recorded anywhere.
        """
        if explicit_mass is not None and float(explicit_mass) > 0:
            return float(explicit_mass)

        p = self.manager.get_active_profile()
        if p:
            sess, _ = self._load_sessions(p)
            if sess:
                bm_log = getattr(sess, "BODYMASS_LOG", {})
                if bm_log:
                    for d in sorted(bm_log.keys(), reverse=True):
                        bm_data = bm_log[d]
                        m = bm_data if isinstance(bm_data, (int, float)) else (bm_data.get("mass") or bm_data.get("weight"))
                        if m and float(m) > 0:
                            return float(m)
            prof_mass = getattr(p, "mass", 0.0)
            if prof_mass and float(prof_mass) > 0:
                return float(prof_mass)

        return None

    @staticmethod
    def _calculate_target_bm(mass: Optional[float]) -> Optional[int]:
        """Calculates target standard tier without hardcoded fallbacks.
        Uses weight class ceiling (5kg tiers: e.g. >85kg to 90kg -> 90).
        Returns None if mass is not recorded.
        """
        if mass is None or mass <= 0:
            return None
        import math
        return int(math.ceil(round(mass, 2) / 5.0) * 5)

    def get_exercise_standards_table(self, exercise_id: str, mass: Optional[float] = None) -> Dict[str, Any]:
        p = self.manager.get_active_profile()
        sex = getattr(p, "sex", "male") if p else "male"
        resolved_mass = self._resolve_user_mass(mass)
        standards = get_tiered_standards(exercise_id, sex, None)
        target_bm = self._calculate_target_bm(resolved_mass)
        name = EXERCISE_STANDARDS.get(exercise_id, {}).get("name", exercise_id)
        return {
            "exercise_id": exercise_id,
            "name": name,
            "target_bm": target_bm,
            "standards": standards or {},
        }

    def generate_excel(self) -> Dict[str, Any]:
        p = self.manager.get_active_profile()
        if not p:
            return {"success": False, "error": "No profile"}

        sess, _ = self._load_sessions(p)
        if not sess:
            return {"success": False, "error": "Could not load sessions.py"}

        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
            filename = os.path.join(p.output_dir, f"Training_Log_{timestamp}.xlsx")
            processor = TrainingLogProcessor(
                filename,
                sess.EXERCISE_REGISTRY,
                sess.USER_DATA,
                sess.BODYMASS_LOG,
                p.to_dict(),
            )
            processor.validate_data()
            processor.write_headers()
            processor.process_data(sess.USER_DATA)
            processor.write_calculations()
            processor.generate_charts()
            processor.write_definitions()
            processor.write_personal_records()
            processor.write_user_profile()
            processor.save()

            self.last_gen_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            try:
                os.startfile(filename)
            except Exception:
                pass

            return {"success": True, "time": self.last_gen_time}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_scraper(self) -> Dict[str, Any]:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts", "batch_scraper.py"))
        try:
            subprocess.Popen([sys.executable, script_path])
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_validate_sessions(self) -> Dict[str, Any]:
        p = self.manager.get_active_profile()
        if not p:
            return {"success": False, "error": "No active profile"}
        sess, _ = self._load_sessions(p)
        if not sess:
            return {"success": False, "error": "Could not load sessions.py"}

        dummy_path = os.path.join(tempfile.gettempdir(), "_ironlog_validate_dummy.xlsx")
        try:
            processor = TrainingLogProcessor(
                dummy_path,
                sess.EXERCISE_REGISTRY,
                sess.USER_DATA,
                sess.BODYMASS_LOG,
                p.to_dict(),
            )
            processor.validate_data()

            date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
            none_mass_dates = [
                d for d, v in getattr(sess, "BODYMASS_LOG", {}).items()
                if date_pattern.match(d) and isinstance(v, dict) and v.get("mass") is None
            ]

            try:
                processor.wb.close()
            except Exception:
                pass
            try:
                os.remove(dummy_path)
            except Exception:
                pass

            return {
                "success": True,
                "message": "sessions.py is valid! No data mismatches found.",
                "none_mass_dates": none_mass_dates,
            }
        except ValueError as ve:
            try:
                os.remove(dummy_path)
            except Exception:
                pass
            return {"success": False, "error": f"Validation Failed: {ve}"}
        except Exception as e:
            try:
                os.remove(dummy_path)
            except Exception:
                pass
            return {"success": False, "error": f"Unexpected error: {e}"}

    def run_bodymass_prefill(self) -> Dict[str, Any]:
        p = self.manager.get_active_profile()
        if not p:
            return {"success": False, "error": "No active profile"}
        sessions_file = getattr(p, "sessions_file", None) or os.path.join(p.sessions_dir, "sessions.py")
        if not os.path.exists(sessions_file):
            return {"success": False, "error": f"sessions.py not found at {sessions_file}"}

        sess, _ = self._load_sessions(p)
        if not sess:
            return {"success": False, "error": "Could not load sessions.py"}

        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        user_dates = {k for k in getattr(sess, "USER_DATA", {}).keys() if date_pattern.match(k)}
        existing_dates = set(getattr(sess, "BODYMASS_LOG", {}).keys())
        missing = sorted(user_dates - existing_dates)

        if not missing:
            return {"success": True, "count": 0, "message": "All workout dates are already present in BODYMASS_LOG."}

        with open(sessions_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        start_line = next((i for i, ln in enumerate(lines) if ln.startswith("BODYMASS_LOG = {")), -1)
        if start_line == -1:
            return {"success": False, "error": "Could not locate BODYMASS_LOG in sessions.py"}

        close_line = next((i for i in range(start_line + 1, len(lines)) if lines[i].rstrip("\r\n") == "}"), -1)
        if close_line == -1:
            return {"success": False, "error": "Could not find closing brace of BODYMASS_LOG"}

        insert_text = "".join(f'    "{d}": {{"mass": None}},\n' for d in missing)
        new_lines = lines[:close_line] + [insert_text] + lines[close_line:]

        with open(sessions_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        return {"success": True, "count": len(missing), "dates": missing}

    def get_missing_masses(self) -> Dict[str, Any]:
        p = self.manager.get_active_profile()
        if not p:
            return {"success": False, "error": "No active profile"}
        sess, _ = self._load_sessions(p)
        if not sess:
            return {"success": False, "error": "Could not load sessions.py"}

        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        none_entries = sorted([
            d for d, v in getattr(sess, "BODYMASS_LOG", {}).items()
            if date_pattern.match(d) and isinstance(v, dict) and v.get("mass") is None
        ])
        return {"success": True, "entries": none_entries}

    def save_missing_masses(self, updates: Dict[str, float]) -> Dict[str, Any]:
        p = self.manager.get_active_profile()
        if not p:
            return {"success": False, "error": "No active profile"}
        sessions_file = getattr(p, "sessions_file", None) or os.path.join(p.sessions_dir, "sessions.py")
        if not os.path.exists(sessions_file):
            return {"success": False, "error": "sessions.py not found"}

        with open(sessions_file, "r", encoding="utf-8") as f:
            source = f.read()

        count = 0
        for date_str, val in updates.items():
            old = f'"{date_str}": {{"mass": None}}'
            new = f'"{date_str}": {{"mass": {val}}}'
            if old in source:
                source = source.replace(old, new, 1)
                count += 1
            else:
                subbed, n = re.subn(
                    rf'("{re.escape(date_str)}")\s*:\s*\{{"mass"\s*:\s*None\}}',
                    rf'\1: {{"mass": {val}}}',
                    source,
                )
                if n > 0:
                    source = subbed
                    count += n

        with open(sessions_file, "w", encoding="utf-8") as f:
            f.write(source)

        return {"success": True, "count": count}

    def get_plan(self) -> Dict[str, Any]:
        p = self.manager.get_active_profile()
        if not p:
            return {"success": False, "error": "No profile"}

        sess, file_path = self._load_sessions(p)
        if not sess:
            return {"success": False, "error": "Could not load sessions.py"}

        user_data = getattr(sess, "USER_DATA", {})
        N, last_day_int = detect_cycle(user_data)
        if N is None:
            return {"success": False, "error": "Could not detect your split cycle yet."}

        day_nums = days_to_generate(N, last_day_int)
        if not day_nums:
            return {"success": False, "error": "All days in current cycle are already planned."}

        try:
            planned = build_planned_sessions(file_path, day_nums)
            why = f"Starting new cycle — all {N} days" if (last_day_int or 0) >= N else f"Completing cycle of {N}"
            serializable_plan = [
                {
                    "day_num": ps.day_number,
                    "date_str": ps.date_str,
                    "exercises": [
                        {
                            "var_name": ex.var_name,
                            "display_name": getattr(ex, "display_name", ex.var_name),
                            "sets": ex.sets,
                            "reps": ex.reps,
                            "mass": ex.mass,
                            "comment": ex.comment,
                        }
                        for ex in ps.exercises
                    ],
                }
                for ps in planned
            ]
            return {"success": True, "planned": serializable_plan, "why": why}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def restore_pre_deload(
        self, day_numbers: Optional[List[int]] = None, scale_pct: float = 100.0
    ) -> Dict[str, Any]:
        p = self.manager.get_active_profile()
        if not p:
            return {"success": False, "error": "No profile"}

        sess, file_path = self._load_sessions(p)
        if not sess:
            return {"success": False, "error": "Could not load sessions.py"}

        user_data = getattr(sess, "USER_DATA", {})
        N, last_day_int = detect_cycle(user_data)
        if not day_numbers:
            if N is None:
                return {"success": False, "error": "Could not detect split cycle."}
            day_numbers = days_to_generate(N, last_day_int) or list(range(1, N + 1))

        try:
            from core.plan_generator import build_pre_deload_baseline

            planned = build_pre_deload_baseline(file_path, day_numbers, scale_pct)
            total_exercises = sum(len(ps.exercises) for ps in planned)
            if total_exercises == 0:
                return {
                    "success": False,
                    "error": (
                        "No pre-deload sessions found in sessions.py.\n"
                        "Make sure your normal sessions don't have 'deload' in their comments."
                    ),
                }

            serializable_plan = [
                {
                    "day_num": ps.day_number,
                    "date_str": ps.date_str,
                    "exercises": [
                        {
                            "var_name": ex.var_name,
                            "display_name": getattr(ex, "display_name", ex.var_name),
                            "sets": ex.sets,
                            "reps": ex.reps,
                            "mass": ex.mass,
                            "comment": ex.comment,
                        }
                        for ex in ps.exercises
                    ],
                }
                for ps in planned
            ]
            return {"success": True, "planned": serializable_plan}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def save_plan(self, planned_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        p = self.manager.get_active_profile()
        if not p:
            return {"success": False, "error": "No profile"}

        sessions_file = getattr(p, "sessions_file", None) or os.path.join(p.sessions_dir, "sessions.py")
        try:
            planned_objs = []
            for d in planned_data:
                ex_objs = [
                    PlannedExercise(
                        var_name=e.get("var_name", "exercise"),
                        display_name=e.get("display_name", e.get("var_name", "exercise")),
                        sets=int(e.get("sets", 3)),
                        reps=str(e.get("reps", "5")),
                        mass=str(e.get("mass", "0")),
                        comment=str(e.get("comment", "")),
                    )
                    for e in d.get("exercises", [])
                ]
                planned_objs.append(
                    PlannedSession(day_number=int(d.get("day_num", 1)), date_str=d.get("date_str", ""), exercises=ex_objs)
                )

            write_planned_sessions(sessions_file, planned_objs)

            # Close standalone planner window if open and reload dashboard
            window_manager.close_planner_window()
            window_manager.reload_main_dashboard()

            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_standards(self, query: str) -> List[Dict[str, Any]]:
        p = self.manager.get_active_profile()
        sex = getattr(p, "sex", "male") if p else "male"
        resolved_mass = self._resolve_user_mass()
        target_bm = self._calculate_target_bm(resolved_mass)

        q = (query or "").strip().lower()
        results = []

        for slug, info in EXERCISE_STANDARDS.items():
            name = info.get("name", slug)
            if q and (q not in name.lower() and q not in slug.lower()):
                continue

            standards = get_tiered_standards(slug, sex, resolved_mass)
            levels = standards.get(target_bm, {}) if (standards and target_bm) else {}

            results.append({
                "slug": slug,
                "name": name,
                "beg": levels.get("Beginner", "-"),
                "nov": levels.get("Novice", "-"),
                "int": levels.get("Intermediate", "-"),
                "adv": levels.get("Advanced", "-"),
                "eli": levels.get("Elite", "-"),
            })
        return results

    def copy_clipboard(self, text: str):
        import tkinter as tk
        r = tk.Tk()
        r.withdraw()
        r.clipboard_clear()
        r.clipboard_append(text)
        r.update()
        r.destroy()

    def open_url(self, url: str):
        webbrowser.open(url)

    def open_latest_excel(self):
        p = self.manager.get_active_profile()
        if p and p.output_dir and os.path.exists(p.output_dir):
            files = sorted(glob.glob(os.path.join(p.output_dir, "Training_Log_*.xlsx")), reverse=True)
            if files:
                os.startfile(files[0])

    def edit_sessions(self):
        p = self.manager.get_active_profile()
        if p and p.sessions_dir:
            f = os.path.join(p.sessions_dir, "sessions.py")
            if os.path.exists(f):
                os.startfile(f)

    def open_output(self):
        p = self.manager.get_active_profile()
        if p and p.output_dir and os.path.exists(p.output_dir):
            os.startfile(p.output_dir)

    def open_app_data_folder(self):
        if getattr(sys, "frozen", False):
            path = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "IronLog")
        else:
            path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        os.makedirs(path, exist_ok=True)
        os.startfile(path)


