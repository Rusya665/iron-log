"""Dear PyGui (DirectX 11 GPU) Desktop GUI for Iron Log.

Styled to match the exact CustomTkinter sidebar, cards, color palette,
and full Cycler (Dynamic Workout Plan Generator) workflow.
"""

import copy
import glob
import importlib
import os
import re
import sys
import threading
import webbrowser
from datetime import datetime, timedelta
from typing import List, Optional

import dearpygui.dearpygui as dpg

from core.models import Log
from core.plan_generator import (
    PlannedExercise,
    PlannedSession,
    build_planned_sessions,
    calculate_gym_stats,
    days_to_generate,
    detect_cycle,
    get_genuinely_new_exercises,
    write_planned_sessions,
)
from core.profile_manager import Profile, ProfileManager
from core.standards import EXERCISE_STANDARDS, get_tiered_standards
from core.version import __version__
from core.xlsx_generator import TrainingLogProcessor


class IronLogDearPyGuiApp:
    def __init__(self):
        self.manager = ProfileManager()
        self.active_sessions = None
        self.cached_stats = {}
        self.planned_sessions: List[PlannedSession] = []
        self.last_generated_at = None

    def setup_theme_and_font(self):
        with dpg.font_registry():
            font_path = "C:/Windows/Fonts/segoeui.ttf"
            if os.path.exists(font_path):
                self.default_font = dpg.add_font(font_path, 15)
                self.title_font = dpg.add_font("C:/Windows/Fonts/segoeuib.ttf", 17) if os.path.exists("C:/Windows/Fonts/segoeuib.ttf") else self.default_font
                self.big_font = dpg.add_font("C:/Windows/Fonts/segoeuib.ttf", 22) if os.path.exists("C:/Windows/Fonts/segoeuib.ttf") else self.default_font
            else:
                self.default_font = None

        with dpg.theme() as ctk_theme:
            with dpg.theme_component(dpg.mvAll):
                # Geometry
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 7)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 0)
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 6)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 6)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 6)

                # CTk Dark Backgrounds
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (18, 18, 18))       # #121212
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (28, 28, 30))        # #1c1c1e
                dpg.add_theme_color(dpg.mvThemeCol_Border, (46, 46, 46))         # #2e2e2e
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (37, 37, 37))        # #252525
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (51, 51, 51)) # #333333
                dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255))
                dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, (119, 119, 119))

                # Default Button Style (#252525)
                dpg.add_theme_color(dpg.mvThemeCol_Button, (37, 37, 37))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (51, 51, 51))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (28, 28, 30))

        dpg.bind_theme(ctk_theme)
        if self.default_font:
            dpg.bind_font(self.default_font)

    def build_ui(self):
        with dpg.window(tag="PrimaryWindow", no_title_bar=True, no_move=True, no_resize=True):
            with dpg.group(horizontal=True):
                # ── 1. LEFT SIDEBAR (Width 210, #161616) ──────────────────────
                with dpg.child_window(width=210, height=-1, border=True, tag="sidebar_container"):
                    prof = self.manager.get_active_profile()
                    dpg.add_text(prof.name if prof else "Default User", tag="sidebar_prof_name", color=(255, 255, 255))
                    dpg.add_text("Iron Log (Dear PyGui GPU)", color=(85, 85, 85))
                    dpg.add_separator()
                    dpg.add_spacer(height=4)

                    # Primary Action Buttons
                    btn_gen = dpg.add_button(label="🚀 Generate Excel Log", width=-1, height=42, callback=self.run_log_generator)
                    self._set_button_color(btn_gen, (21, 101, 192), (25, 118, 210))  # #1565C0

                    btn_plan = dpg.add_button(label="🗓️ Plan Next Cycle", width=-1, height=42, callback=self.run_plan_generator)
                    self._set_button_color(btn_plan, (106, 27, 154), (123, 31, 162)) # #6A1B9A

                    btn_open = dpg.add_button(label="📂 Open Latest Log", width=-1, height=42, callback=self.open_latest_excel)
                    self._set_button_color(btn_open, (27, 94, 32), (46, 125, 50))    # #1B5E20

                    dpg.add_spacer(height=4)
                    dpg.add_separator()
                    dpg.add_spacer(height=4)

                    # Secondary Buttons
                    dpg.add_button(label="  📝  Edit Sessions", width=-1, height=34, callback=self.edit_sessions)
                    dpg.add_button(label="  📊  Output Folder", width=-1, height=34, callback=self.open_output)
                    dpg.add_button(label="  📚  Exercise Library", width=-1, height=34, callback=self.show_exercise_library)
                    dpg.add_button(label="  🔄  Split Details", width=-1, height=34, callback=self.show_split_details)

                    dpg.add_spacer(height=20)
                    dpg.add_text("Ready", tag="sidebar_status", color=(85, 85, 85))
                    dpg.add_text("", tag="sidebar_last_gen", color=(68, 68, 68))

                # ── 2. MAIN CONTENT AREA (#121212) ────────────────────────────
                with dpg.child_window(width=-1, height=-1, border=False):
                    # Header Row
                    with dpg.group(horizontal=True):
                        dpg.add_text("Recent Sessions", tag="header_title", color=(255, 255, 255))
                        dpg.add_spacer(width=20)
                        dpg.add_button(label="↻  Refresh", width=100, height=30, callback=self.load_active_data)

                    dpg.add_spacer(height=6)

                    # 3 Stats Cards Row
                    with dpg.group(horizontal=True):
                        # Card 1: Gym Attendance
                        with dpg.child_window(width=260, height=96, border=True):
                            dpg.add_text("GYM ATTENDANCE", color=(119, 119, 119))
                            dpg.add_text("-- Days", tag="c1_val", color=(255, 255, 255))
                            dpg.add_text("-- this year · -- this month", tag="c1_sub", color=(85, 85, 85))

                        # Card 2: Current Split Duration
                        with dpg.child_window(width=260, height=96, border=True):
                            dpg.add_text("CURRENT SPLIT DURATION", color=(119, 119, 119))
                            dpg.add_text("-- Weeks", tag="c2_val", color=(255, 255, 255))
                            dpg.add_button(label="Click for Split Details", small=True, callback=self.show_split_details)

                        # Card 3: Last Workout
                        with dpg.child_window(width=260, height=96, border=True):
                            dpg.add_text("LAST WORKOUT", color=(119, 119, 119))
                            dpg.add_text("--", tag="c3_val", color=(255, 255, 255))
                            dpg.add_text("Day --", tag="c3_sub", color=(85, 85, 85))

                    dpg.add_spacer(height=10)

                    # Recent Workout Sessions Card Row
                    with dpg.child_window(tag="sessions_grid", height=-1, border=False):
                        dpg.add_text("Loading workout sessions...", tag="sessions_loading_txt")

    def _set_button_color(self, btn, bg_rgb, hover_rgb):
        with dpg.theme() as b_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, bg_rgb)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, hover_rgb)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, bg_rgb)
        dpg.bind_item_theme(btn, b_theme)

    def load_active_data(self):
        p = self.manager.get_active_profile()
        if not p:
            dpg.set_value("sidebar_status", "No profile selected")
            return

        sessions_file = getattr(p, "sessions_file", None) or os.path.join(p.sessions_dir, "sessions.py")
        if not os.path.exists(sessions_file):
            dpg.set_value("sidebar_status", f"sessions.py not found at {sessions_file}")
            return

        try:
            sessions_dir = os.path.dirname(sessions_file)
            if sessions_dir not in sys.path:
                sys.path.insert(0, sessions_dir)

            if "sessions" in sys.modules:
                sess = importlib.reload(sys.modules["sessions"])
            else:
                import sessions as sess

            self.active_sessions = sess
            user_data = getattr(sess, "USER_DATA", {})
            stats = calculate_gym_stats(user_data)
            self.cached_stats = stats

            # Update Header & Stats Cards
            dpg.set_value("sidebar_prof_name", p.name)
            dpg.set_value("c1_val", f"{stats.get('total_days', 0)} Days")
            dpg.set_value("c1_sub", f"{stats.get('this_year_days', 0)} this year · {stats.get('this_month_days', 0)} this month")

            dpg.set_value("c2_val", f"{stats.get('current_split_weeks', 0.0):.1f} Weeks")

            dpg.set_value("c3_val", str(stats.get("latest_workout_date", "N/A")))
            dpg.set_value("c3_sub", f"Day {stats.get('latest_workout_day', 'N/A')}")

            # Rebuild Horizontal Workout Cards
            dpg.delete_item("sessions_grid", children_only=True)
            with dpg.group(horizontal=True, parent="sessions_grid"):
                date_pat = re.compile(r"^\d{4}-\d{2}-\d{2}$")
                sorted_dates = sorted([d for d in user_data.keys() if date_pat.match(d)], reverse=True)
                N, _ = detect_cycle(user_data)
                show_dates = sorted_dates[: N if N else 3]

                for d_str in reversed(show_dates):
                    day_data = user_data[d_str]
                    v = day_data.get("day")
                    is_pr = isinstance(v, str) and v.upper() == "PR"

                    with dpg.child_window(width=260, height=-1, border=True):
                        hdr_text = f"📅  {d_str}  ·  Day {v}" if isinstance(v, int) else f"📅  {d_str}  ·  {v}"
                        dpg.add_text(hdr_text, color=(180, 83, 9) if is_pr else (255, 255, 255))
                        dpg.add_separator()

                        for ex_id, log in day_data.items():
                            if not isinstance(log, Log):
                                continue
                            info = EXERCISE_STANDARDS.get(ex_id, {})
                            ex_name = info.get("name", ex_id)
                            reps_str = "-".join(str(r) for r in log.reps) if len(set(log.reps)) > 1 else f"{len(log.reps)} × {log.reps[0]}"
                            mass_str = f" @ {log.mass[0]}kg" if log.mass and max(log.mass) > 0 else " (BW)"

                            with dpg.group(horizontal=True):
                                dpg.add_text(f"• {ex_name[:20]}", color=(221, 221, 221))
                                dpg.add_spacer(width=6)
                                dpg.add_text(f"{reps_str}{mass_str}", color=(136, 136, 136))

            dpg.set_value("sidebar_status", f"Ready ({p.name})")

        except Exception as e:
            dpg.set_value("sidebar_status", f"Error: {e}")

    def run_log_generator(self):
        p = self.manager.get_active_profile()
        if not p or not self.active_sessions:
            dpg.set_value("sidebar_status", "No profile loaded.")
            return

        dpg.set_value("sidebar_status", "Generating Excel Log...")

        def _task():
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
                filename = os.path.join(p.output_dir, f"Training_Log_{timestamp}.xlsx")
                processor = TrainingLogProcessor(
                    filename,
                    self.active_sessions.EXERCISE_REGISTRY,
                    self.active_sessions.USER_DATA,
                    self.active_sessions.BODYMASS_LOG,
                    p.to_dict(),
                )
                processor.validate_data()
                processor.write_headers()
                processor.process_data(self.active_sessions.USER_DATA)
                processor.write_calculations()
                processor.generate_charts()
                processor.write_definitions()
                processor.write_personal_records()
                processor.write_user_profile()
                processor.save()

                self.last_generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
                dpg.set_value("sidebar_status", "✅ Excel log created!")
                dpg.set_value("sidebar_last_gen", f"Last gen: {self.last_generated_at}")
                try:
                    os.startfile(filename)
                except Exception:
                    pass
            except Exception as e:
                dpg.set_value("sidebar_status", f"Error: {e}")

        threading.Thread(target=_task, daemon=True).start()

    def run_plan_generator(self):
        p = self.manager.get_active_profile()
        if not p or not self.active_sessions:
            dpg.set_value("sidebar_status", "Select a valid profile first.")
            return

        sessions_file = getattr(p, "sessions_file", None) or os.path.join(p.sessions_dir, "sessions.py")
        user_data = getattr(self.active_sessions, "USER_DATA", {})
        N, last_day_int = detect_cycle(user_data)

        if N is None:
            dpg.set_value("sidebar_status", "Could not detect split cycle length yet.")
            return

        day_nums = days_to_generate(N, last_day_int)
        if not day_nums:
            dpg.set_value("sidebar_status", "All days in the current cycle are already planned.")
            return

        try:
            self.planned_sessions = build_planned_sessions(sessions_file, day_nums)
            self._render_cycler_modal(sessions_file, N, last_day_int)
        except Exception as e:
            dpg.set_value("sidebar_status", f"Plan build error: {e}")

    def _render_cycler_modal(self, sessions_file: str, N: int, last_day_int: int):
        if dpg.does_item_exist("modal_cycler"):
            dpg.delete_item("modal_cycler")

        why = f"Starting new cycle — all {N} days" if (last_day_int or 0) >= N else f"Completing cycle of {N}"

        with dpg.window(label=f"Plan Next Cycle ({why})", modal=True, show=True, tag="modal_cycler", width=980, height=680, pos=(60, 40)):
            # Banner
            dpg.add_text(f"Plan Next Cycle ({why})", color=(255, 255, 255))
            dpg.add_text("Define your training split. Type an exercise name to configure sets/reps.", color=(136, 136, 136))
            dpg.add_separator()

            # Planned days list
            with dpg.child_window(tag="cycler_days_container", height=-60, border=False):
                self._draw_cycler_days()

            # Footer
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_button(label="Cancel", width=100, height=32, callback=lambda: dpg.delete_item("modal_cycler"))
                
                b_add = dpg.add_button(label="+ Add Day", width=110, height=32, callback=self._add_plan_day)
                self._set_button_color(b_add, (106, 27, 154), (123, 31, 162))

                b_del = dpg.add_button(label="🧪 Deload (-10%)", width=140, height=32, callback=self._apply_deload)
                self._set_button_color(b_del, (51, 51, 51), (68, 68, 68))

                dpg.add_spacer(width=200)

                b_save = dpg.add_button(label="✅ Write to sessions.py", width=200, height=32, callback=lambda: self._save_plan(sessions_file))
                self._set_button_color(b_save, (27, 94, 32), (46, 125, 50))

    def _draw_cycler_days(self):
        dpg.delete_item("cycler_days_container", children_only=True)

        for d_idx, ps in enumerate(self.planned_sessions):
            with dpg.child_window(parent="cycler_days_container", height=240, border=True):
                # Day Header
                with dpg.group(horizontal=True):
                    dpg.add_button(label=f"Day {ps.day_number}", width=70, height=26)
                    dpg.add_text("Date:")
                    dpg.add_input_text(default_value=ps.date_str, width=120, callback=lambda s, a, p=ps: setattr(p, "date_str", a))
                    dpg.add_spacer(width=10)

                    b_ex = dpg.add_button(label="+ Add Exercise", small=True, callback=lambda _, s=ps: self._add_ex_to_plan(s))
                    self._set_button_color(b_ex, (2, 119, 189), (1, 87, 155))

                    b_del_d = dpg.add_button(label="🗑️", small=True, callback=lambda _, idx=d_idx: self._remove_plan_day(idx))
                    self._set_button_color(b_del_d, (90, 26, 26), (198, 40, 40))

                dpg.add_separator()

                # Table
                with dpg.table(header_row=True, height=-1):
                    dpg.add_table_column(label="Order", width_fixed=True, init_width_or_weight=60)
                    dpg.add_table_column(label="Exercise Variable", width_stretch=True)
                    dpg.add_table_column(label="Sets", width_fixed=True, init_width_or_weight=55)
                    dpg.add_table_column(label="Reps", width_fixed=True, init_width_or_weight=95)
                    dpg.add_table_column(label="Mass (kg)", width_fixed=True, init_width_or_weight=100)
                    dpg.add_table_column(label="Comment", width_fixed=True, init_width_or_weight=140)
                    dpg.add_table_column(label="Del", width_fixed=True, init_width_or_weight=40)

                    for ex_idx, ex in enumerate(ps.exercises):
                        with dpg.table_row():
                            with dpg.group(horizontal=True):
                                dpg.add_button(label="▲", small=True, callback=lambda _, s=ps, e=ex: self._move_ex_up(s, e))
                                dpg.add_button(label="▼", small=True, callback=lambda _, s=ps, e=ex: self._move_ex_down(s, e))

                            dpg.add_input_text(default_value=ex.var_name, width=-1, callback=lambda s, a, e=ex: setattr(e, "var_name", a))
                            dpg.add_input_text(default_value=str(ex.sets), width=-1, callback=lambda s, a, e=ex: setattr(e, "sets", a))
                            dpg.add_input_text(default_value=str(ex.reps), width=-1, callback=lambda s, a, e=ex: setattr(e, "reps", a))
                            dpg.add_input_text(default_value=str(ex.mass), width=-1, callback=lambda s, a, e=ex: setattr(e, "mass", a))
                            dpg.add_input_text(default_value=str(ex.comment), width=-1, callback=lambda s, a, e=ex: setattr(e, "comment", a))
                            
                            b_del_ex = dpg.add_button(label="✕", small=True, callback=lambda _, s=ps, e=ex: self._remove_ex_from_plan(s, e))
                            self._set_button_color(b_del_ex, (90, 26, 26), (198, 40, 40))

    def _move_ex_up(self, ps: PlannedSession, ex: PlannedExercise):
        idx = ps.exercises.index(ex)
        if idx > 0:
            ps.exercises[idx - 1], ps.exercises[idx] = ps.exercises[idx], ps.exercises[idx - 1]
            self._draw_cycler_days()

    def _move_ex_down(self, ps: PlannedSession, ex: PlannedExercise):
        idx = ps.exercises.index(ex)
        if idx < len(ps.exercises) - 1:
            ps.exercises[idx], ps.exercises[idx + 1] = ps.exercises[idx + 1], ps.exercises[idx]
            self._draw_cycler_days()

    def _add_ex_to_plan(self, ps: PlannedSession):
        ps.exercises.append(PlannedExercise(var_name="exercise", display_name="Exercise", sets=3, reps="5", mass="0", comment=""))
        self._draw_cycler_days()

    def _remove_ex_from_plan(self, ps: PlannedSession, ex: PlannedExercise):
        if ex in ps.exercises:
            ps.exercises.remove(ex)
            self._draw_cycler_days()

    def _add_plan_day(self):
        new_num = len(self.planned_sessions) + 1
        self.planned_sessions.append(PlannedSession(day_number=new_num, date_str="", exercises=[]))
        self._draw_cycler_days()

    def _remove_plan_day(self, idx: int):
        if 0 <= idx < len(self.planned_sessions):
            self.planned_sessions.pop(idx)
            for i, ps in enumerate(self.planned_sessions, 1):
                ps.day_number = i
            self._draw_cycler_days()

    def _apply_deload(self):
        for ps in self.planned_sessions:
            for ex in ps.exercises:
                try:
                    m = float(ex.mass)
                    ex.mass = str(round(m * 0.9 * 2) / 2)
                    ex.comment = "Deload -10%"
                except ValueError:
                    pass
        self._draw_cycler_days()

    def _save_plan(self, sessions_file: str):
        try:
            write_planned_sessions(sessions_file, self.planned_sessions)
            dpg.set_value("sidebar_status", f"✅ Added {len(self.planned_sessions)} session(s)")
            if dpg.does_item_exist("modal_cycler"):
                dpg.delete_item("modal_cycler")
            self.load_active_data()
        except Exception as e:
            dpg.set_value("sidebar_status", f"Error saving plan: {e}")

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

    def show_exercise_library(self):
        if dpg.does_item_exist("win_standards"):
            dpg.delete_item("win_standards")

        p = self.manager.get_active_profile()
        sex = getattr(p, "sex", "male") if p else "male"
        mass = getattr(p, "mass", 80.0) if p else 80.0

        with dpg.window(label="Exercise Standards Library — Dear PyGui", tag="win_standards", width=820, height=540, pos=(120, 100)):
            with dpg.group(horizontal=True):
                dpg.add_text("Search:")
                dpg.add_input_text(hint="Filter by exercise name or slug...", width=400, callback=lambda s, a: self._filter_standards(a, sex, mass))

            dpg.add_spacer(height=5)
            with dpg.table(header_row=True, resizable=True, scrollY=True, height=-1, tag="tbl_standards"):
                dpg.add_table_column(label="Exercise Name", width_stretch=True)
                dpg.add_table_column(label="Slug", width_fixed=True, init_width_or_weight=160)
                dpg.add_table_column(label="Beg", width_fixed=True, init_width_or_weight=50)
                dpg.add_table_column(label="Nov", width_fixed=True, init_width_or_weight=50)
                dpg.add_table_column(label="Int", width_fixed=True, init_width_or_weight=50)
                dpg.add_table_column(label="Adv", width_fixed=True, init_width_or_weight=50)
                dpg.add_table_column(label="Eli", width_fixed=True, init_width_or_weight=50)
                dpg.add_table_column(label="Actions", width_fixed=True, init_width_or_weight=170)

                self._populate_standards("", sex, mass)

    def _filter_standards(self, query, sex, mass):
        self._populate_standards(query, sex, mass)

    def _populate_standards(self, q, sex, mass):
        q = q.strip().lower()
        children = dpg.get_item_children("tbl_standards", 1) or []
        for c in children:
            dpg.delete_item(c)

        target_bm = int(mass / 5.0) * 5
        for slug, info in EXERCISE_STANDARDS.items():
            name = info.get("name", slug)
            if q and (q not in name.lower() and q not in slug.lower()):
                continue

            standards = get_tiered_standards(slug, sex, mass)
            lvl_dict = standards.get(target_bm, {}) if standards else {}

            with dpg.table_row(parent="tbl_standards"):
                dpg.add_text(name)
                dpg.add_text(slug, color=(56, 189, 248))
                for lvl in ["Beginner", "Novice", "Intermediate", "Advanced", "Elite"]:
                    v = lvl_dict.get(lvl, "-")
                    dpg.add_text(f"{v}kg" if isinstance(v, (int, float)) else str(v))

                with dpg.group(horizontal=True):
                    dpg.add_button(label="Copy", small=True, callback=lambda _, s=slug: dpg.set_clipboard_text(s))
                    py_code = f'{slug.replace("-", "_")} = "{slug}"'
                    b_py = dpg.add_button(label="Copy Py", small=True, callback=lambda _, c=py_code: dpg.set_clipboard_text(c))
                    self._set_button_color(b_py, (27, 94, 32), (46, 125, 50))
                    b_v = dpg.add_button(label="View", small=True, callback=lambda _, s=slug: webbrowser.open(f"https://strengthlevel.com/strength-standards/{s}"))
                    self._set_button_color(b_v, (21, 101, 192), (25, 118, 210))

    def show_split_details(self):
        if dpg.does_item_exist("win_split"):
            dpg.delete_item("win_split")

        stats = self.cached_stats
        with dpg.window(label="Current Split Details — Dear PyGui", tag="win_split", width=580, height=420, pos=(180, 140)):
            dpg.add_text("CURRENT SPLIT ROUTINE", color=(119, 119, 119))
            dpg.add_separator()
            dpg.add_text(f"• Active Split Duration: {stats.get('current_split_weeks', 0.0):.1f} Weeks")
            dpg.add_text(f"• Detected Cycle Length: {stats.get('cycle_length', 'N/A')} Days")
            dpg.add_text(f"• Total Recorded Sessions: {stats.get('total_days', 0)}")
            dpg.add_spacer(height=10)

            dpg.add_text("Recent Split Sessions History:")
            with dpg.table(header_row=True, height=-1):
                dpg.add_table_column(label="Date")
                dpg.add_table_column(label="Day")
                dpg.add_table_column(label="Exercises Count")

                sessions = stats.get("split_sessions_details", [])
                for s in reversed(sessions):
                    with dpg.table_row():
                        dpg.add_text(s.get("date_str", ""))
                        dpg.add_text(f"Day {s.get('day', '')}")
                        dpg.add_text(str(len(s.get("exercises", []))))


def run_dpg_app():
    dpg.create_context()
    app = IronLogDearPyGuiApp()
    app.setup_theme_and_font()
    app.build_ui()

    dpg.create_viewport(title=f"Iron Log {__version__} (Dear PyGui Edition)", width=1100, height=720, min_width=960, min_height=580)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("PrimaryWindow", True)

    app.load_active_data()

    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    run_dpg_app()
