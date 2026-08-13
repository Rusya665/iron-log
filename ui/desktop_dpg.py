"""Dear PyGui (DirectX 11 / GPU-Accelerated) Desktop GUI for Iron Log.

Provides sub-millisecond input latency, smooth 144Hz hardware-accelerated rendering,
instant dynamic search filtering, and full feature parity with iron-log core.
"""

import os
import re
import sys
import threading
import webbrowser
from datetime import datetime
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
        self.status_msg = "Ready"
        self.planned_sessions: List[PlannedSession] = []

    def setup_theme_and_font(self):
        # 1. Fonts
        with dpg.font_registry():
            font_path = "C:/Windows/Fonts/segoeui.ttf"
            if os.path.exists(font_path):
                self.default_font = dpg.add_font(font_path, 15)
                self.bold_font = dpg.add_font("C:/Windows/Fonts/segoeuib.ttf", 16) if os.path.exists("C:/Windows/Fonts/segoeuib.ttf") else self.default_font
                self.title_font = dpg.add_font("C:/Windows/Fonts/segoeuib.ttf", 18) if os.path.exists("C:/Windows/Fonts/segoeuib.ttf") else self.default_font
            else:
                self.default_font = None

        # 2. Modern Dark Zinc Theme
        with dpg.theme() as modern_theme:
            with dpg.theme_component(dpg.mvAll):
                # Rounding & Geometry
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 6)
                dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 4)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 5)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 6)

                # Modern Dark Palette
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (18, 18, 20))       # #121214
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (24, 24, 27))        # #18181b
                dpg.add_theme_color(dpg.mvThemeCol_Border, (39, 39, 42))         # #27272a
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (39, 39, 42))        # #27272a
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (63, 63, 70)) # #3f3f46
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (82, 82, 91))
                dpg.add_theme_color(dpg.mvThemeCol_Text, (244, 244, 245))        # #f4f4f5
                dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, (161, 161, 170))

                # Buttons
                dpg.add_theme_color(dpg.mvThemeCol_Button, (39, 39, 42))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (63, 63, 70))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (82, 82, 91))

                # Headers / Tabs
                dpg.add_theme_color(dpg.mvThemeCol_Header, (37, 99, 235, 120))
                dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (37, 99, 235, 200))
                dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (29, 78, 216))

        dpg.bind_theme(modern_theme)
        if self.default_font:
            dpg.bind_font(self.default_font)

    def build_ui(self):
        with dpg.window(tag="PrimaryWindow", no_title_bar=True, no_move=True, no_resize=True):
            # 1. Header Row
            with dpg.child_window(height=52, border=True):
                with dpg.group(horizontal=True):
                    dpg.add_text("⚡ IRON LOG", color=(56, 189, 248))
                    dpg.add_text(f"v{__version__}", color=(161, 161, 170))
                    dpg.add_spacer(width=20)

                    dpg.add_text("Profile:")
                    prof_names = [p.name for p in self.manager.profiles] or ["Default User"]
                    active_name = self.manager.get_active_profile().name if self.manager.get_active_profile() else prof_names[0]
                    dpg.add_combo(
                        items=prof_names,
                        default_value=active_name,
                        width=160,
                        tag="profile_combo",
                        callback=self._on_profile_select,
                    )
                    dpg.add_button(label="+ New Profile", callback=self._show_new_profile_dialog)

                    dpg.add_spacer(width=20)
                    dpg.add_text("Engine: Dear PyGui (DirectX 11 GPU)", color=(74, 222, 128))

            dpg.add_spacer(height=4)

            # 2. Metric Stat Cards Row
            with dpg.group(horizontal=True):
                # Total Sessions
                with dpg.child_window(width=240, height=85, border=True):
                    dpg.add_text("TOTAL SESSIONS", color=(161, 161, 170))
                    dpg.add_text("--", tag="stat_total_val", color=(56, 189, 248))
                    dpg.add_text("-- this year", tag="stat_total_sub", color=(113, 113, 122))

                # Last Workout
                with dpg.child_window(width=240, height=85, border=True):
                    dpg.add_text("LAST WORKOUT", color=(161, 161, 170))
                    dpg.add_text("--", tag="stat_last_val", color=(56, 189, 248))
                    dpg.add_text("Latest session date", tag="stat_last_sub", color=(113, 113, 122))

                # Active Split
                with dpg.child_window(width=240, height=85, border=True):
                    dpg.add_text("ACTIVE SPLIT", color=(161, 161, 170))
                    dpg.add_text("--", tag="stat_split_val", color=(56, 189, 248))
                    dpg.add_button(label="View Routine Details", callback=self._show_split_details, small=True)

                # Body Mass
                with dpg.child_window(width=-1, height=85, border=True):
                    dpg.add_text("BODY MASS", color=(161, 161, 170))
                    dpg.add_text("-- kg", tag="stat_mass_val", color=(56, 189, 248))
                    dpg.add_text("From bodymass log", color=(113, 113, 122))

            dpg.add_spacer(height=4)

            # 3. Action Toolbar Row
            with dpg.child_window(height=48, border=True):
                with dpg.group(horizontal=True):
                    dpg.add_button(label="📊 Generate Excel Log", callback=self._generate_excel)
                    dpg.add_button(label="📅 Cycle Planner", callback=self._show_planner)
                    dpg.add_button(label="🏋️ Strength Standards", callback=self._show_standards_browser)
                    dpg.add_button(label="🔄 Split Details", callback=self._show_split_details)
                    dpg.add_spacer(width=10)
                    dpg.add_button(label="Edit sessions.py", callback=self._edit_sessions)
                    dpg.add_button(label="Open Output", callback=self._open_output)

            dpg.add_spacer(height=4)

            # 4. Recent Sessions Panel
            dpg.add_text("Recent Workout Sessions (Active Cycle)", color=(161, 161, 170))
            with dpg.child_window(tag="sessions_panel", height=-36, border=True):
                dpg.add_text("Loading workout sessions...", tag="sessions_loading_txt")

            # 5. Status Footer
            with dpg.child_window(height=26, border=False):
                dpg.add_text("Ready", tag="status_bar_txt", color=(161, 161, 170))

    def load_active_data(self):
        p = self.manager.get_active_profile()
        if not p:
            dpg.set_value("status_bar_txt", "No profile selected")
            return

        sessions_file = getattr(p, "sessions_file", None) or os.path.join(p.sessions_dir, "sessions.py")
        if not os.path.exists(sessions_file):
            dpg.set_value("status_bar_txt", f"sessions.py not found at: {sessions_file}")
            return

        try:
            sessions_dir = os.path.dirname(sessions_file)
            if sessions_dir not in sys.path:
                sys.path.insert(0, sessions_dir)

            import importlib
            if "sessions" in sys.modules:
                sess = importlib.reload(sys.modules["sessions"])
            else:
                import sessions as sess

            self.active_sessions = sess
            user_data = getattr(sess, "USER_DATA", {})
            stats = calculate_gym_stats(user_data)
            self.cached_stats = stats

            # Update Stat Cards
            dpg.set_value("stat_total_val", str(stats.get("total_days", "--")))
            dpg.set_value("stat_total_sub", f"{stats.get('this_year_days', 0)} this year")

            dpg.set_value("stat_last_val", str(stats.get("latest_workout_date", "--")))
            dpg.set_value("stat_last_sub", f"Day {stats.get('latest_workout_day', '')}")

            weeks = stats.get("current_split_weeks", 0.0)
            dpg.set_value("stat_split_val", f"{weeks:.1f} Weeks")

            bm_log = getattr(sess, "BODYMASS_LOG", {})
            if bm_log:
                sorted_bm = sorted(bm_log.items(), key=lambda x: str(x[0]), reverse=True)
                dpg.set_value("stat_mass_val", f"{sorted_bm[0][1]} kg")
            else:
                dpg.set_value("stat_mass_val", f"{p.mass} kg")

            # Rebuild Horizontal Sessions Panel
            dpg.delete_item("sessions_panel", children_only=True)
            with dpg.group(horizontal=True, parent="sessions_panel"):
                date_pat = re.compile(r"^\d{4}-\d{2}-\d{2}$")
                sorted_dates = sorted([d for d in user_data.keys() if date_pat.match(d)], reverse=True)
                N, _ = detect_cycle(user_data)
                show_dates = sorted_dates[: N if N else 3]

                for d_str in reversed(show_dates):
                    day_data = user_data[d_str]
                    with dpg.child_window(width=250, height=-1, border=True):
                        dpg.add_text(f"📅 {d_str} (Day {day_data.get('day', '?')})", color=(56, 189, 248))
                        dpg.add_separator()

                        for ex_id, log in day_data.items():
                            if not isinstance(log, Log):
                                continue
                            info = EXERCISE_STANDARDS.get(ex_id, {})
                            name = info.get("name", ex_id)
                            reps_str = ",".join(str(r) for r in log.reps)
                            mass_str = f" @ {log.mass[0]}kg" if log.mass and max(log.mass) > 0 else " (BW)"

                            dpg.add_text(f"• {name[:22]}", color=(244, 244, 245))
                            dpg.add_text(f"   [{reps_str}]{mass_str}", color=(161, 161, 170))

            dpg.set_value("status_bar_txt", f"Loaded profile: {p.name} ({sessions_file})")

        except Exception as e:
            dpg.set_value("status_bar_txt", f"Error loading sessions: {e}")

    def _on_profile_select(self, sender, app_data):
        for idx, prof in enumerate(self.manager.profiles):
            if prof.name == app_data:
                self.manager.set_active(idx)
                self.load_active_data()
                break

    def _show_new_profile_dialog(self):
        if dpg.does_item_exist("modal_new_profile"):
            dpg.delete_item("modal_new_profile")

        with dpg.window(label="Create New Profile", modal=True, show=True, tag="modal_new_profile", width=340, height=180, pos=(300, 200)):
            dpg.add_text("Enter Profile Name:")
            dpg.add_input_text(tag="in_new_prof_name", width=-1)
            dpg.add_spacer(height=10)

            def _save():
                val = dpg.get_value("in_new_prof_name").strip()
                if val:
                    self.manager.add_profile(Profile(name=val, sessions_dir="", output_dir="", sex="male"))
                    dpg.configure_item("profile_combo", items=[p.name for p in self.manager.profiles], default_value=val)
                    self.load_active_data()
                    dpg.delete_item("modal_new_profile")

            with dpg.group(horizontal=True):
                dpg.add_button(label="Create", callback=_save, width=100)
                dpg.add_button(label="Cancel", callback=lambda: dpg.delete_item("modal_new_profile"), width=100)

    def _generate_excel(self):
        p = self.manager.get_active_profile()
        if not p or not self.active_sessions:
            dpg.set_value("status_bar_txt", "Error: No active profile or sessions loaded.")
            return

        dpg.set_value("status_bar_txt", "Generating Excel report in background...")

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

                dpg.set_value("status_bar_txt", f"✅ Created Excel log: {filename}")
                try:
                    os.startfile(filename)
                except Exception:
                    pass
            except Exception as e:
                dpg.set_value("status_bar_txt", f"Excel generation error: {e}")

        threading.Thread(target=_task, daemon=True).start()

    def _show_standards_browser(self):
        if dpg.does_item_exist("win_standards"):
            dpg.delete_item("win_standards")

        p = self.manager.get_active_profile()
        sex = getattr(p, "sex", "male") if p else "male"
        mass = getattr(p, "mass", 80.0) if p else 80.0

        with dpg.window(label="Exercise Standards Browser — Dear PyGui", tag="win_standards", width=820, height=540, pos=(120, 100)):
            with dpg.group(horizontal=True):
                dpg.add_text("Search:")
                dpg.add_input_text(
                    hint="Filter by exercise name or slug...",
                    tag="standards_search_in",
                    width=400,
                    callback=self._filter_standards_table,
                )

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

                self._populate_standards_rows("", sex, mass)

    def _filter_standards_table(self, sender, app_data):
        p = self.manager.get_active_profile()
        sex = getattr(p, "sex", "male") if p else "male"
        mass = getattr(p, "mass", 80.0) if p else 80.0
        self._populate_standards_rows(app_data, sex, mass)

    def _populate_standards_rows(self, query: str, sex: str, mass: float):
        q = query.strip().lower()
        # Clear previous rows
        children = dpg.get_item_children("tbl_standards", 1) or []
        for c in children:
            dpg.delete_item(c)

        for slug, info in EXERCISE_STANDARDS.items():
            name = info.get("name", slug)
            if q and (q not in name.lower() and q not in slug.lower()):
                continue

            standards = get_tiered_standards(slug, sex, mass)
            target_bm = int(mass / 5.0) * 5
            level_dict = standards.get(target_bm, {}) if standards else {}

            with dpg.table_row(parent="tbl_standards"):
                dpg.add_text(name)
                dpg.add_text(slug, color=(56, 189, 248))
                for lvl in ["Beginner", "Novice", "Intermediate", "Advanced", "Elite"]:
                    v = level_dict.get(lvl, "-")
                    dpg.add_text(f"{v}kg" if isinstance(v, (int, float)) else str(v))

                with dpg.group(horizontal=True):
                    dpg.add_button(label="Copy", small=True, callback=lambda _, s=slug: self._copy_to_clip(s))
                    py_code = f'{slug.replace("-", "_")} = "{slug}"'
                    dpg.add_button(label="Copy Py", small=True, callback=lambda _, c=py_code: self._copy_to_clip(c))
                    dpg.add_button(label="View", small=True, callback=lambda _, s=slug: webbrowser.open(f"https://strengthlevel.com/strength-standards/{s}"))

    def _copy_to_clip(self, text: str):
        dpg.set_clipboard_text(text)
        dpg.set_value("status_bar_txt", f"Copied '{text}' to clipboard!")

    def _show_split_details(self):
        if dpg.does_item_exist("win_split"):
            dpg.delete_item("win_split")

        stats = self.cached_stats
        with dpg.window(label="Split Routine Details — Dear PyGui", tag="win_split", width=560, height=400, pos=(180, 140)):
            dpg.add_text("Routine Overview", color=(56, 189, 248))
            dpg.add_separator()
            dpg.add_text(f"• Active Split Duration: {stats.get('current_split_weeks', 0.0):.1f} Weeks")
            dpg.add_text(f"• Detected Cycle Length: {stats.get('cycle_length', 'N/A')} Days")
            dpg.add_text(f"• Total Recorded Sessions: {stats.get('total_days', 0)}")
            dpg.add_spacer(height=10)

            dpg.add_text("Recent Cycle History:")
            with dpg.table(header_row=True, height=-1):
                dpg.add_table_column(label="Date")
                dpg.add_table_column(label="Day")
                dpg.add_table_column(label="Exercises Count")

                sessions = stats.get("split_sessions_details", [])
                for s in reversed(sessions):
                    with dpg.table_row():
                        dpg.add_text(s.get("date_str", ""))
                        dpg.add_text(str(s.get("day", "")))
                        dpg.add_text(str(len(s.get("exercises", []))))

    def _show_planner(self):
        p = self.manager.get_active_profile()
        if not p or not self.active_sessions:
            dpg.set_value("status_bar_txt", "Select a valid profile first.")
            return

        sessions_file = getattr(p, "sessions_file", None) or os.path.join(p.sessions_dir, "sessions.py")
        user_data = getattr(self.active_sessions, "USER_DATA", {})
        N, last_day = detect_cycle(user_data)
        if N is None:
            dpg.set_value("status_bar_txt", "Could not detect split cycle length yet.")
            return

        day_nums = days_to_generate(N, last_day)
        if not day_nums:
            dpg.set_value("status_bar_txt", "All days in the current cycle are already planned.")
            return

        try:
            self.planned_sessions = build_planned_sessions(sessions_file, day_nums)
            self._render_planner_window(sessions_file)
        except Exception as e:
            dpg.set_value("status_bar_txt", f"Error building plan: {e}")

    def _render_planner_window(self, sessions_file: str):
        if dpg.does_item_exist("win_planner"):
            dpg.delete_item("win_planner")

        with dpg.window(label="Dynamic Cycle Planner — Dear PyGui", tag="win_planner", width=940, height=620, pos=(80, 60)):
            with dpg.group(horizontal=True):
                dpg.add_button(label="Deload (-10%)", callback=self._apply_deload)
                dpg.add_button(label="+ Add Day", callback=self._add_plan_day)
                dpg.add_spacer(width=20)
                dpg.add_button(label="💾 Save Plan to sessions.py", callback=lambda: self._save_plan(sessions_file))

            dpg.add_spacer(height=6)

            with dpg.child_window(tag="planner_container", height=-1, border=False):
                self._draw_plan_days()

    def _draw_plan_days(self):
        dpg.delete_item("planner_container", children_only=True)

        for d_idx, ps in enumerate(self.planned_sessions):
            with dpg.child_window(parent="planner_container", height=240, border=True):
                with dpg.group(horizontal=True):
                    dpg.add_text(f"Day {ps.day_num}", color=(56, 189, 248))
                    dpg.add_input_text(default_value=ps.date_str, width=120, callback=lambda s, a, p=ps: setattr(p, "date_str", a))
                    dpg.add_spacer(width=10)
                    dpg.add_button(label="+ Add Exercise", small=True, callback=lambda _, s=ps: self._add_exercise_to_plan(s))
                    dpg.add_button(label="Delete Day", small=True, callback=lambda _, idx=d_idx: self._remove_plan_day(idx))

                dpg.add_separator()

                # Table of exercises
                with dpg.table(header_row=True, height=-1):
                    dpg.add_table_column(label="Order", width_fixed=True, init_width_or_weight=60)
                    dpg.add_table_column(label="Exercise Variable", width_stretch=True)
                    dpg.add_table_column(label="Sets", width_fixed=True, init_width_or_weight=50)
                    dpg.add_table_column(label="Reps", width_fixed=True, init_width_or_weight=90)
                    dpg.add_table_column(label="Mass (kg)", width_fixed=True, init_width_or_weight=90)
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
                            dpg.add_button(label="✕", small=True, callback=lambda _, s=ps, e=ex: self._remove_ex_from_plan(s, e))

    def _move_ex_up(self, ps: PlannedSession, ex: PlannedExercise):
        idx = ps.exercises.index(ex)
        if idx > 0:
            ps.exercises[idx - 1], ps.exercises[idx] = ps.exercises[idx], ps.exercises[idx - 1]
            self._draw_plan_days()

    def _move_ex_down(self, ps: PlannedSession, ex: PlannedExercise):
        idx = ps.exercises.index(ex)
        if idx < len(ps.exercises) - 1:
            ps.exercises[idx], ps.exercises[idx + 1] = ps.exercises[idx + 1], ps.exercises[idx]
            self._draw_plan_days()

    def _add_exercise_to_plan(self, ps: PlannedSession):
        ps.exercises.append(PlannedExercise(var_name="exercise", sets=3, reps="5", mass="0", comment=""))
        self._draw_plan_days()

    def _remove_ex_from_plan(self, ps: PlannedSession, ex: PlannedExercise):
        if ex in ps.exercises:
            ps.exercises.remove(ex)
            self._draw_plan_days()

    def _add_plan_day(self):
        new_num = len(self.planned_sessions) + 1
        self.planned_sessions.append(PlannedSession(day_num=new_num, date_str="", exercises=[]))
        self._draw_plan_days()

    def _remove_plan_day(self, idx: int):
        if 0 <= idx < len(self.planned_sessions):
            self.planned_sessions.pop(idx)
            for i, ps in enumerate(self.planned_sessions, 1):
                ps.day_num = i
            self._draw_plan_days()

    def _apply_deload(self):
        for ps in self.planned_sessions:
            for ex in ps.exercises:
                try:
                    m = float(ex.mass)
                    ex.mass = str(round(m * 0.9 * 2) / 2)
                    ex.comment = "Deload -10%"
                except ValueError:
                    pass
        self._draw_plan_days()

    def _save_plan(self, sessions_file: str):
        try:
            write_planned_sessions(sessions_file, self.planned_sessions)
            dpg.set_value("status_bar_txt", "✅ Plan successfully written to sessions.py!")
            if dpg.does_item_exist("win_planner"):
                dpg.delete_item("win_planner")
            self.load_active_data()
        except Exception as e:
            dpg.set_value("status_bar_txt", f"Error saving plan: {e}")

    def _edit_sessions(self):
        p = self.manager.get_active_profile()
        if p and p.sessions_dir:
            file_path = os.path.join(p.sessions_dir, "sessions.py")
            if os.path.exists(file_path):
                os.startfile(file_path)

    def _open_output(self):
        p = self.manager.get_active_profile()
        if p and p.output_dir and os.path.exists(p.output_dir):
            os.startfile(p.output_dir)


def run_dpg_app():
    dpg.create_context()
    app = IronLogDearPyGuiApp()
    app.setup_theme_and_font()
    app.build_ui()

    dpg.create_viewport(title=f"Iron Log {__version__} (Dear PyGui GPU Edition)", width=1100, height=720, min_width=960, min_height=580)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("PrimaryWindow", True)

    app.load_active_data()

    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    run_dpg_app()
