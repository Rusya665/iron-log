import glob
import importlib
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
import webbrowser
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk
from CTkMenuBar import CTkTitleMenu, CustomDropdownMenu

from core.profile_manager import Profile, ProfileManager
from core.updater import check_for_updates, download_and_install_update
from core.version import __version__
from core.xlsx_generator import TrainingLogProcessor


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_path, relative_path)


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class IronLogApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Iron Log - Strength Tracker")
        self.geometry("1150x720")
        self.minsize(960, 640)

        # Set the custom window icon
        icon_path = resource_path(os.path.join("media", "GUI", "biceps.ico"))
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        self.manager = ProfileManager()
        self.menu = None
        self._status_reset_id = None  # handle for the auto-reset after() call
        self.last_generated_at = None  # timestamp of last successful Excel generation
        self.init_menu()

        # Start auto-update loop if enabled
        self.update_thread_stop_event = threading.Event()
        self.start_auto_update_loop()

        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)

        # ── Resize debouncer ─────────────────────────────────────────────────
        # Use add="+" so we ADD to existing bindings rather than replacing the
        # CTkTitleMenu's <Configure> hook (which caused the menu to disappear).
        self._resize_job = None
        self.bind("<Configure>", self._on_root_configure, add="+")

        if not self.manager.profiles:
            self.show_profile_creator()
        elif (
            self.manager.remember_last_user and self.manager.active_profile_index != -1
        ):
            self.show_dashboard()
        else:
            self.show_profile_picker()

    def _on_root_configure(self, event):
        """Rate-limit CTk's expensive canvas redraws to 40 ms."""
        if event.widget is not self:
            return
        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(40, self._do_resize)

    def _do_resize(self):
        self._resize_job = None
        # Force CTk to flush pending layout in one batch instead of per-pixel
        self.update_idletasks()

    # -------------------------------------------------------------------------
    # Status bar helper
    # -------------------------------------------------------------------------
    def set_status(self, text: str, color: str = "gray", auto_reset_ms: int = 0):
        """Update the status label.  If auto_reset_ms > 0 the label resets to
        'Ready' after that many milliseconds, cancelling any previous timer."""
        if not hasattr(self, "status_label"):
            return
        # Cancel any pending auto-reset
        if self._status_reset_id is not None:
            self.after_cancel(self._status_reset_id)
            self._status_reset_id = None
        self.status_label.configure(text=text, text_color=color)
        if auto_reset_ms > 0:
            self._status_reset_id = self.after(auto_reset_ms, self._reset_status)

    def _reset_status(self):
        self._status_reset_id = None
        if hasattr(self, "status_label"):
            self.status_label.configure(text="Ready", text_color="gray")

    # -------------------------------------------------------------------------
    # Auto-update
    # -------------------------------------------------------------------------
    def start_auto_update_loop(self):
        def loop():
            while not self.update_thread_stop_event.is_set():
                if self.manager.auto_check_updates:
                    self.run_update_check(manual=False)
                # Wait 30 minutes (1800 s), checking stop_event every 5 seconds
                for _ in range(360):
                    if self.update_thread_stop_event.is_set():
                        break
                    time.sleep(5)

        t = threading.Thread(target=loop, daemon=True)
        t.start()

    def run_update_check(self, manual=False):
        def check():
            if manual:
                self.after(
                    0, lambda: self.set_status("Checking for updates...", "white")
                )

            has_update, new_version, download_url = check_for_updates(__version__)
            if has_update:
                self.after(0, lambda: self.prompt_update(new_version, download_url))
            elif manual:
                self.after(
                    0,
                    lambda: messagebox.showinfo(
                        "No Updates", f"You are on the latest version ({__version__})."
                    ),
                )
                self.after(0, lambda: self.set_status("Ready", "gray"))

        threading.Thread(target=check, daemon=True).start()

    def prompt_update(self, new_version, download_url):
        msg = f"Hey, a new version (v{new_version}) is found. Do you want me to restart and update?"
        if messagebox.askyesno("Update Available", msg):
            self.perform_update(download_url)

    def perform_update(self, download_url):
        if getattr(self, "is_updating", False):
            return
        self.is_updating = True

        dl_win = ctk.CTkToplevel(self)
        dl_win.title("Downloading Update")
        dl_win.geometry("350x150")
        dl_win.attributes("-topmost", True)

        lbl = ctk.CTkLabel(
            dl_win,
            text="Downloading new version...\n(This will take about a minute depending on internet speed)",
            font=("Roboto", 12),
        )
        lbl.pack(pady=40, padx=20)

        def download_process():
            download_and_install_update(download_url)

            def exit_app():
                self.quit()
                self.destroy()
                os._exit(0)

            self.after(0, exit_app)

        threading.Thread(target=download_process, daemon=True).start()

    # -------------------------------------------------------------------------
    # Menu
    # -------------------------------------------------------------------------
    def init_menu(self):
        if self.menu:
            self.menu.destroy()

        self.menu = CTkTitleMenu(self)

        # App Menu
        app_btn = self.menu.add_cascade("App")
        app_dropdown = CustomDropdownMenu(widget=app_btn)

        app_dropdown.add_option(
            option="About Iron Log", command=self.show_about_dialog
        )
        app_dropdown.add_separator()

        app_dropdown.add_option(
            option="Check for Updates",
            command=lambda: self.run_update_check(manual=True),
        )
        app_dropdown.add_separator()
        app_dropdown.add_option(option="New Profile", command=self.show_profile_creator)
        app_dropdown.add_option(option="Switch User", command=self.show_profile_picker)
        app_dropdown.add_separator()
        app_dropdown.add_option(
            option="Open App Data Folder", command=self.open_app_data_folder
        )
        app_dropdown.add_separator()
        app_dropdown.add_option(option="Exit", command=self.quit)

        # Settings Menu
        self.init_settings_menu()

        # Profiles Menu
        self.update_profiles_menu()

        # Experimental Menu
        self.init_experimental_menu()

    def update_profiles_menu(self):
        prof_btn = self.menu.add_cascade("Profiles")
        prof_dropdown = CustomDropdownMenu(widget=prof_btn)

        for i, profile in enumerate(self.manager.profiles):
            sub = prof_dropdown.add_submenu(profile.name)
            sub.add_option(
                option="Select", command=lambda idx=i: self.select_profile(idx)
            )
            sub.add_option(
                option="Edit", command=lambda idx=i: self.show_profile_creator(idx)
            )
            sub.add_separator()
            sub.add_option(
                option="Delete", command=lambda idx=i: self.delete_profile(idx)
            )

    def init_settings_menu(self):
        settings_btn = self.menu.add_cascade("Settings")
        settings_dropdown = CustomDropdownMenu(widget=settings_btn)

        status = "Enabled" if self.manager.remember_last_user else "Disabled"
        settings_dropdown.add_option(
            option=f"Auto-Login: {status}", command=self.toggle_auto_login
        )

        update_status = "Enabled" if self.manager.auto_check_updates else "Disabled"
        settings_dropdown.add_option(
            option=f"Auto-Update: {update_status}", command=self.toggle_auto_update
        )

        p = self.manager.get_active_profile()
        if p:
            settings_dropdown.add_separator()
            pr_status = "ON" if p.show_pr else "OFF"
            std_status = "ON" if p.show_standards else "OFF"
            mile_status = "ON" if p.show_milestones else "OFF"

            settings_dropdown.add_option(
                option=f"Show PRs: {pr_status}",
                command=lambda: self.toggle_feature("show_pr"),
            )
            settings_dropdown.add_option(
                option=f"Show Standards: {std_status}",
                command=lambda: self.toggle_feature("show_standards"),
            )
            settings_dropdown.add_option(
                option=f"Show Milestones: {mile_status}",
                command=lambda: self.toggle_feature("show_milestones"),
            )

    def init_experimental_menu(self):
        exp_btn = self.menu.add_cascade("🧪 Experimental")
        exp_dropdown = CustomDropdownMenu(widget=exp_btn)
        exp_dropdown.add_option(
            option="Prefill Mass Dates", command=self.run_bodymass_prefill
        )
        exp_dropdown.add_option(
            option="Fill-in Missing Masses", command=self.run_mass_fillin_dialog
        )
        exp_dropdown.add_separator()
        exp_dropdown.add_option(
            option="Validate sessions.py", command=self.run_validate_sessions
        )

    def show_about_dialog(self):
        win = ctk.CTkToplevel(self)
        win.title("About Iron Log")
        win.geometry("350x250")
        win.resizable(False, False)
        win.attributes("-topmost", True)
        win.after(100, win.focus_force)

        ctk.CTkLabel(win, text="Iron Log", font=("Roboto", 24, "bold")).pack(
            pady=(20, 5)
        )
        ctk.CTkLabel(
            win, text=f"Version {__version__}", font=("Roboto", 13), text_color="#aaa"
        ).pack(pady=(0, 15))

        ctk.CTkLabel(win, text="Author: Rustem Nizamov", font=("Roboto", 14)).pack(pady=5)

        def open_gh():
            import webbrowser

            webbrowser.open("https://github.com/Rusya665/iron-log")

        ctk.CTkButton(
            win,
            text="GitHub Repository",
            fg_color="#333",
            hover_color="#555",
            command=open_gh,
        ).pack(pady=20)

    def toggle_auto_login(self):
        self.manager.remember_last_user = not self.manager.remember_last_user
        self.manager.save_profiles()
        self.init_menu()
        self.set_status(
            f"Auto-Login {'enabled' if self.manager.remember_last_user else 'disabled'}",
            "gray",
            auto_reset_ms=4000,
        )

    def toggle_auto_update(self):
        self.manager.auto_check_updates = not self.manager.auto_check_updates
        self.manager.save_profiles()
        self.init_menu()
        self.set_status(
            f"Auto-Update {'enabled' if self.manager.auto_check_updates else 'disabled'}",
            "gray",
            auto_reset_ms=4000,
        )
        if self.manager.auto_check_updates:
            self.run_update_check(manual=False)

    def toggle_feature(self, feature_name):
        p = self.manager.get_active_profile()
        if p:
            current_val = getattr(p, feature_name)
            setattr(p, feature_name, not current_val)
            self.manager.save_profiles()
            self.init_menu()
            status = "enabled" if getattr(p, feature_name) else "disabled"
            feature_display = feature_name.replace("show_", "").upper()
            self.set_status(
                f"Chart Feature {feature_display} {status}", "gray", auto_reset_ms=4000
            )

    # -------------------------------------------------------------------------
    # Container helpers
    # -------------------------------------------------------------------------
    def clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    # -------------------------------------------------------------------------
    # Profile picker / creator
    # -------------------------------------------------------------------------
    def show_profile_picker(self):
        self.clear_container()

        label = ctk.CTkLabel(
            self.container, text="Select Your Profile", font=("Roboto", 24, "bold")
        )
        label.pack(pady=40)

        grid = ctk.CTkFrame(self.container, fg_color="transparent")
        grid.pack(pady=10)

        for i, profile in enumerate(self.manager.profiles):
            btn = ctk.CTkButton(
                grid,
                text=profile.name,
                width=200,
                height=100,
                command=lambda idx=i: self.select_profile(idx),
            )
            btn.grid(row=i // 3, column=i % 3, padx=10, pady=10)

        add_btn = ctk.CTkButton(
            self.container,
            text="+ New Profile",
            command=self.show_profile_creator,
            fg_color="gray",
        )
        add_btn.pack(pady=20)

    def delete_profile(self, index):
        if messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete profile '{self.manager.profiles[index].name}'?",
        ):
            self.manager.delete_profile(index)
            self.init_menu()
            if not self.manager.profiles:
                self.show_profile_creator()
            else:
                self.show_profile_picker()

    def show_profile_creator(self, profile_index=None):
        self.clear_container()
        is_edit = profile_index is not None
        title = "Edit Profile" if is_edit else "Create New Profile"
        p = self.manager.profiles[profile_index] if is_edit else None

        ctk.CTkLabel(self.container, text=title, font=("Roboto", 24, "bold")).pack(
            pady=20
        )

        form = ctk.CTkFrame(self.container)
        form.pack(pady=10, padx=50, fill="x")

        ctk.CTkLabel(form, text="Name:").grid(
            row=0, column=0, padx=10, pady=10, sticky="e"
        )
        name_entry = ctk.CTkEntry(form, placeholder_text="e.g. Rusya")
        name_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        if p:
            name_entry.insert(0, p.name)

        ctk.CTkLabel(form, text="Sex:").grid(
            row=1, column=0, padx=10, pady=10, sticky="e"
        )
        sex_var = ctk.StringVar(value=p.sex if p else "male")
        ctk.CTkRadioButton(form, text="Male", variable=sex_var, value="male").grid(
            row=1, column=1, padx=10, pady=10, sticky="w"
        )
        ctk.CTkRadioButton(form, text="Female", variable=sex_var, value="female").grid(
            row=1, column=1, padx=80, pady=10, sticky="w"
        )

        ctk.CTkLabel(form, text="Sessions Dir:").grid(
            row=2, column=0, padx=10, pady=10, sticky="e"
        )
        sessions_entry = ctk.CTkEntry(form, width=300)
        sessions_entry.grid(row=2, column=1, padx=10, pady=10)
        if p:
            sessions_entry.insert(0, p.sessions_dir)

        def browse_sessions():
            path = ctk.filedialog.askdirectory()
            if path:
                sessions_entry.delete(0, "end")
                sessions_entry.insert(0, path)

        ctk.CTkButton(form, text="Browse", width=60, command=browse_sessions).grid(
            row=2, column=2, padx=10
        )

        # Inline validation hint
        validation_label = ctk.CTkLabel(
            self.container, text="", text_color="orange", font=("Roboto", 11)
        )
        validation_label.pack()

        def save():
            name = name_entry.get().strip()
            s_dir = sessions_entry.get().strip()
            if not name or not s_dir:
                validation_label.configure(
                    text="⚠️  Name and Sessions Dir are required!"
                )
                return

            # Warn if sessions.py is not found in the chosen directory
            sessions_file = os.path.join(s_dir, "sessions.py")
            if not os.path.exists(sessions_file):
                validation_label.configure(
                    text="⚠️  sessions.py not found in that folder — generation will fail until it exists."
                )
                if not messagebox.askyesno(
                    "sessions.py Not Found",
                    f"sessions.py was not found in:\n{s_dir}\n\nSave profile anyway?",
                ):
                    return

            new_p = Profile(
                name=name,
                sessions_dir=s_dir,
                output_dir=os.path.join(s_dir, "gym"),
                sex=sex_var.get(),
            )

            if is_edit:
                self.manager.update_profile(profile_index, new_p)
                self.init_menu()
                self.show_dashboard()
            else:
                self.manager.add_profile(new_p)
                self.init_menu()
                self.show_profile_picker()

        btn_text = "Save Changes" if is_edit else "Create Profile"
        ctk.CTkButton(
            self.container, text=btn_text, command=save, fg_color="green"
        ).pack(pady=20)

        if self.manager.profiles:
            cancel_cmd = self.show_dashboard if is_edit else self.show_profile_picker
            ctk.CTkButton(self.container, text="Cancel", command=cancel_cmd).pack()

    def select_profile(self, index):
        self.manager.set_active(index)
        self.show_dashboard()

    # -------------------------------------------------------------------------
    # Dashboard
    # -------------------------------------------------------------------------
    def show_dashboard(self):
        self.clear_container()
        p = self.manager.get_active_profile()

        # ── Sidebar ──────────────────────────────────────────────────────────
        sidebar = ctk.CTkFrame(
            self.container, width=210, corner_radius=0, fg_color="#161616"
        )
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Profile name block
        ctk.CTkLabel(
            sidebar,
            text=p.name,
            font=("Roboto", 17, "bold"),
            text_color="white",
            anchor="w",
        ).pack(fill="x", padx=16, pady=(22, 2))
        ctk.CTkLabel(
            sidebar, text="Iron Log", font=("Roboto", 11), text_color="#555", anchor="w"
        ).pack(fill="x", padx=16, pady=(0, 14))
        ctk.CTkFrame(sidebar, height=1, fg_color="#2e2e2e").pack(
            fill="x", padx=16, pady=(0, 12)
        )

        # Primary actions
        _p = {
            "height": 44,
            "corner_radius": 8,
            "font": ("Roboto", 13, "bold"),
            "anchor": "center",
        }
        ctk.CTkButton(
            sidebar,
            text="🚀 Generate Excel Log",
            fg_color="#1565C0",
            hover_color="#1976D2",
            command=self.run_log_generator,
            **_p,
        ).pack(fill="x", padx=12, pady=3)
        ctk.CTkButton(
            sidebar,
            text="🗓️ Plan Next Cycle",
            fg_color="#6A1B9A",
            hover_color="#7B1FA2",
            command=self.run_plan_generator,
            **_p,
        ).pack(fill="x", padx=12, pady=3)
        ctk.CTkButton(
            sidebar,
            text="📂 Open Latest Log",
            fg_color="#1B5E20",
            hover_color="#2E7D32",
            command=self.open_latest_excel,
            **_p,
        ).pack(fill="x", padx=12, pady=3)

        ctk.CTkFrame(sidebar, height=1, fg_color="#2e2e2e").pack(
            fill="x", padx=16, pady=12
        )

        # Secondary actions
        _s = {
            "height": 36,
            "corner_radius": 7,
            "font": ("Roboto", 12),
            "anchor": "w",
            "fg_color": "#252525",
            "hover_color": "#333",
            "text_color": "#bbb",
        }
        ctk.CTkButton(
            sidebar, text="  📝  Edit Sessions", command=self.edit_sessions, **_s
        ).pack(fill="x", padx=12, pady=2)
        ctk.CTkButton(
            sidebar, text="  📊  Output Folder", command=self.open_output, **_s
        ).pack(fill="x", padx=12, pady=2)
        ctk.CTkButton(
            sidebar,
            text="  📚  Exercise Library",
            command=self.show_exercise_library,
            **_s,
        ).pack(fill="x", padx=12, pady=2)
        ctk.CTkButton(
            sidebar, text="  ⚡  Run Scraper", command=self.run_scraper, **_s
        ).pack(fill="x", padx=12, pady=2)

        # Bottom of sidebar — status + last-generated
        self.status_label = ctk.CTkLabel(
            sidebar, text="Ready", text_color="#555", font=("Roboto", 11), anchor="w"
        )
        self.status_label.pack(side="bottom", fill="x", padx=16, pady=(4, 14))

        self.last_gen_label = ctk.CTkLabel(
            sidebar, text="", text_color="#444", font=("Roboto", 10), anchor="w"
        )
        self.last_gen_label.pack(side="bottom", fill="x", padx=16, pady=(0, 2))
        if self.last_generated_at:
            self.last_gen_label.configure(text=f"Last gen: {self.last_generated_at}")

        # ── Main content ─────────────────────────────────────────────────────
        content = ctk.CTkFrame(self.container, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=18, pady=14)

        # Header row: title + refresh button
        hdr_row = ctk.CTkFrame(content, fg_color="transparent")
        hdr_row.pack(fill="x", pady=(2, 14))
        ctk.CTkLabel(hdr_row, text="Recent Sessions", font=("Roboto", 22, "bold")).pack(
            side="left"
        )
        ctk.CTkButton(
            hdr_row,
            text="↻  Refresh",
            width=100,
            height=30,
            font=("Roboto", 12),
            fg_color="#252525",
            hover_color="#333",
            command=lambda: threading.Thread(
                target=self._load_recent_sessions, daemon=True
            ).start(),
        ).pack(side="right")

        # Cards area — plain frame, no canvas overhead
        self._sessions_panel = ctk.CTkFrame(content, fg_color="transparent")
        self._sessions_panel.pack(fill="both", expand=True)

        ctk.CTkLabel(
            self._sessions_panel,
            text="Loading…",
            text_color="#555",
            font=("Roboto", 13),
        ).pack(expand=True)

        threading.Thread(target=self._load_recent_sessions, daemon=True).start()

    def _try_load_sessions(self, p):
        """Like _load_sessions but silent — safe for background threads."""
        if p.sessions_dir not in sys.path:
            sys.path.insert(0, p.sessions_dir)
        try:
            import sessions

            importlib.reload(sessions)
            return sessions
        except Exception:
            return None

    def _load_recent_sessions(self):
        """Background thread: parse the last N workout sessions and push to UI."""
        from core.plan_generator import detect_cycle

        p = self.manager.get_active_profile()
        if not p:
            self.after(0, lambda: self._update_sessions_panel(None, None))
            return

        sessions = self._try_load_sessions(p)
        if sessions is None:
            self.after(0, lambda: self._update_sessions_panel(None, None))
            return

        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        sorted_dates = sorted(
            [k for k in sessions.USER_DATA.keys() if date_pattern.match(k)],
            reverse=True,
        )

        # Determine how many cards to show based on last session's day value
        last_day_obj = None
        if sorted_dates:
            v = sessions.USER_DATA[sorted_dates[0]].get("day")
            last_day_obj = v if isinstance(v, (int, str)) else None

        if isinstance(last_day_obj, str):
            # Post-special session (PR, Deload, etc.): show only that 1 card
            show_dates = sorted_dates[:1]
        else:
            N, _ = detect_cycle(sessions.USER_DATA)
            n_cards = N if N else 3
            show_dates = sorted_dates[:n_cards]

        # Resolve display names via EXERCISE_STANDARDS
        from core.standards import EXERCISE_STANDARDS

        id_to_name = {
            slug: info.get("name", slug) for slug, info in EXERCISE_STANDARDS.items()
        }

        display_data = []
        for date_str in reversed(show_dates):  # oldest first → left-to-right
            day_data = sessions.USER_DATA[date_str]
            # Extract raw day value (int = training day, str = special session)
            v = day_data.get("day")
            day_obj = v if isinstance(v, (int, str)) else None

            exercises_summary = []
            for ex_id, log in day_data.items():
                from core.models import Log

                if not isinstance(log, Log):
                    continue
                name = id_to_name.get(ex_id, ex_id)
                display_name = name[:24] + "…" if len(name) > 24 else name

                n_sets = len(log.reps)
                if log.mass and max(log.mass) > 0:
                    if len(set(log.mass)) == 1:
                        if len(set(log.reps)) == 1:
                            summary = f"{n_sets} \u00d7 {log.reps[0]} @ {log.mass[0]}kg"
                        else:
                            reps_str = "-".join(str(r) for r in log.reps)
                            summary = f"{reps_str} @ {log.mass[0]}kg"
                    else:
                        avg = sum(log.mass) / len(log.mass)
                        summary = f"{n_sets} sets ~{avg:.1f}kg"
                else:
                    if len(set(log.reps)) == 1:
                        summary = f"{n_sets}\u00d7{log.reps[0]} (BW)"
                    else:
                        reps_str = "-".join(str(r) for r in log.reps)
                        summary = f"{reps_str} (BW)"

                exercises_summary.append((display_name, summary))

            display_data.append((date_str, day_obj, exercises_summary))

        self.after(
            0, lambda d=display_data: self._update_sessions_panel(d, last_day_obj)
        )

    def _update_sessions_panel(self, data, last_day_obj=None):
        """Main-thread callback: rebuild the recent sessions as horizontal cards.

        Uses ONLY native tk widgets (tk.Frame / tk.Label) — zero CTk canvas
        overhead — so window resizing stays instant regardless of card count.
        """
        if not hasattr(self, "_sessions_panel"):
            return
        for w in self._sessions_panel.winfo_children():
            w.destroy()

        if data is None:
            ctk.CTkLabel(
                self._sessions_panel,
                text="Could not load sessions.py — check your profile path.",
                text_color="#555",
                font=("Roboto", 13),
            ).pack(expand=True)
            return
        if not data:
            ctk.CTkLabel(
                self._sessions_panel,
                text="No sessions found.",
                text_color="#555",
                font=("Roboto", 13),
            ).pack(expand=True)
            return

        # Determine dark bg of the parent panel (set by CTk theme)
        BG_DARK = "#121212"

        # Outer row — native Frame, no canvas needed
        row = tk.Frame(self._sessions_panel, bg=BG_DARK)
        row.pack(fill="both", expand=True)
        for i in range(len(data)):
            row.columnconfigure(i, weight=1)
        row.rowconfigure(0, weight=1)

        for col_i, (date_str, day_obj, exercises) in enumerate(data):
            is_pr = isinstance(day_obj, str)

            card_bg = "#2a1a00" if is_pr else "#1c1c1e"
            hdr_fg = "#b45309" if is_pr else "#ffffff"
            sep_bg = "#5a3000" if is_pr else "#2e2e2e"

            # Card — plain tk.Frame with left/right padding via inner frame
            card = tk.Frame(
                row,
                bg=card_bg,
                bd=0,
                highlightthickness=1,
                highlightbackground="#2e2e2e",
            )
            card.grid(row=0, column=col_i, sticky="nsew", padx=6, pady=2)

            # Header label
            if isinstance(day_obj, int):
                hdr_text = f"\U0001f4c5  {date_str}  \u00b7  Day {day_obj}"
            elif isinstance(day_obj, str):
                hdr_text = f"\U0001f4c5  {date_str}  \u00b7  {day_obj}"
            else:
                hdr_text = f"\U0001f4c5  {date_str}"

            tk.Label(
                card,
                text=hdr_text,
                bg=card_bg,
                fg=hdr_fg,
                font=("Roboto", 13, "bold"),
                anchor="w",
            ).pack(fill="x", padx=14, pady=(14, 6))

            # Separator — 1-px native frame
            tk.Frame(card, bg=sep_bg, height=1).pack(fill="x", padx=10, pady=(0, 8))

            # Exercise rows
            MAX_EX = 10
            for ex_name, summary in exercises[:MAX_EX]:
                ex_row = tk.Frame(card, bg=card_bg)
                ex_row.pack(fill="x", padx=12, pady=1)
                tk.Label(
                    ex_row,
                    text=ex_name,
                    bg=card_bg,
                    fg="#dddddd",
                    font=("Roboto", 12),
                    anchor="w",
                ).pack(side="left")
                tk.Label(
                    ex_row,
                    text=summary,
                    bg=card_bg,
                    fg="#888888",
                    font=("Roboto", 11),
                    anchor="e",
                ).pack(side="right")

            if len(exercises) > MAX_EX:
                tk.Label(
                    card,
                    text=f"+ {len(exercises) - MAX_EX} more",
                    bg=card_bg,
                    fg="#444444",
                    font=("Roboto", 11),
                    anchor="w",
                ).pack(fill="x", padx=14, pady=(4, 8))
            else:
                tk.Frame(card, bg=card_bg, height=8).pack()

    def show_exercise_library(self):
        from core.standards import EXERCISE_STANDARDS

        lib_win = ctk.CTkToplevel(self)
        lib_win.title("Exercise Library")
        lib_win.geometry("600x700")
        lib_win.after(100, lib_win.focus_force)
        lib_win.after(100, lib_win.lift)

        ctk.CTkLabel(
            lib_win, text="Search Exercises", font=("Roboto", 18, "bold")
        ).pack(pady=10)

        search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(
            lib_win, textvariable=search_var, placeholder_text="Type to filter..."
        )
        search_entry.pack(fill="x", padx=20, pady=5)
        lib_win.after(150, search_entry.focus_set)

        count_label = ctk.CTkLabel(
            lib_win, text="", text_color="gray", font=("Roboto", 11)
        )
        count_label.pack()

        scroll_frame = ctk.CTkScrollableFrame(lib_win)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        LIBRARY = sorted(
            [
                (slug, info.get("name", slug))
                for slug, info in EXERCISE_STANDARDS.items()
            ],
            key=lambda x: x[1],
        )
        MAX_DISPLAY = 50

        def render_results(matches):
            for w in scroll_frame.winfo_children():
                w.destroy()
            shown = matches[:MAX_DISPLAY]
            for slug, display in shown:
                row = ctk.CTkFrame(scroll_frame, fg_color="transparent")
                row.pack(fill="x", pady=2)

                ctk.CTkLabel(row, text=display, font=("Roboto", 13)).pack(
                    side="left", padx=5
                )
                ctk.CTkLabel(
                    row, text=f"({slug})", font=("Roboto", 11), text_color="gray"
                ).pack(side="left", padx=5)

                btn_frame = ctk.CTkFrame(row, fg_color="transparent")
                btn_frame.pack(side="right")

                def copy_to_cb(s=slug):
                    self.clipboard_clear()
                    self.clipboard_append(s)
                    self.set_status(
                        f"Copied '{s}' to clipboard!", "green", auto_reset_ms=3000
                    )

                def open_link(s=slug):
                    webbrowser.open(f"https://strengthlevel.com/strength-standards/{s}")

                ctk.CTkButton(
                    btn_frame,
                    text="Copy ID",
                    width=60,
                    height=24,
                    font=("Roboto", 10),
                    command=copy_to_cb,
                ).pack(side="left", padx=2)
                ctk.CTkButton(
                    btn_frame,
                    text="View",
                    width=50,
                    height=24,
                    font=("Roboto", 10),
                    fg_color="#34495e",
                    command=open_link,
                ).pack(side="left", padx=2)

            total = len(matches)
            if total > MAX_DISPLAY:
                count_label.configure(
                    text=f"Showing {MAX_DISPLAY} of {total} — type to narrow results"
                )
            elif total == len(LIBRARY):
                count_label.configure(text=f"{total} exercises total")
            else:
                count_label.configure(text=f"{total} result{'s' if total != 1 else ''}")

        _debounce_id = [None]

        def update_list(*args):
            if _debounce_id[0] is not None:
                lib_win.after_cancel(_debounce_id[0])

            def do_search():
                _debounce_id[0] = None
                query = search_var.get().lower().strip()
                if query:
                    matches = [
                        (s, d)
                        for s, d in LIBRARY
                        if query in s.lower() or query in d.lower()
                    ]
                else:
                    matches = LIBRARY
                render_results(matches)

            _debounce_id[0] = lib_win.after(250, do_search)

        search_var.trace_add("write", update_list)
        render_results(LIBRARY)

    # -------------------------------------------------------------------------
    # Core actions
    # -------------------------------------------------------------------------
    def run_log_generator(self):
        p = self.manager.get_active_profile()
        self.set_status("Generating log...", "white")

        if p.sessions_dir not in sys.path:
            sys.path.insert(0, p.sessions_dir)

        try:
            import sessions

            importlib.reload(sessions)

            # Multi-User Safety Check
            owner = getattr(sessions, "SESSIONS_OWNER", None)
            if owner and owner.strip().lower() != p.name.strip().lower():
                msg = (
                    f"WARNING: 'SESSIONS_OWNER' in sessions.py is '{owner}', "
                    f"but current profile is '{p.name}'.\n\nContinue anyway?"
                )
                if not messagebox.askyesno("Profile Mismatch", msg):
                    self.set_status(
                        "Aborted: Profile mismatch.", "orange", auto_reset_ms=5000
                    )
                    return

            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
            os.makedirs(p.output_dir, exist_ok=True)
            filename = os.path.join(p.output_dir, f"Training_Log_{timestamp}.xlsx")

            processor = TrainingLogProcessor(
                filename,
                sessions.EXERCISE_REGISTRY,
                sessions.USER_DATA,
                sessions.BODYMASS_LOG,
                p.to_dict(),
            )

            try:
                processor.validate_data()
            except ValueError as ve:
                self.set_status(
                    "Generation Failed: Data Mismatch", "red", auto_reset_ms=8000
                )
                messagebox.showerror("Data Error", str(ve))
                return

            processor.write_headers()
            processor.process_data(sessions.USER_DATA)
            processor.write_calculations()
            processor.generate_charts()
            processor.write_definitions()
            processor.write_personal_records()
            processor.write_user_profile()
            processor.save()

            # Update last-generated timestamp
            self.last_generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
            if hasattr(self, "last_gen_label"):
                self.last_gen_label.configure(
                    text=f"Last generated: {self.last_generated_at}"
                )

            self.set_status(
                "✅ Success! Log saved to output folder.", "green", auto_reset_ms=8000
            )
            os.startfile(filename)

        except Exception as e:
            self.set_status(f"Error: {str(e)}", "red", auto_reset_ms=8000)
            messagebox.showerror("Unexpected Error", str(e))

    def run_plan_generator(self):
        p = self.manager.get_active_profile()
        file_path = os.path.join(p.sessions_dir, "sessions.py")
        if not os.path.exists(file_path):
            messagebox.showerror("Error", f"sessions.py not found in {p.sessions_dir}")
            return

        # Load sessions module to inspect Day data
        sess = self._try_load_sessions(p)
        if sess is None:
            messagebox.showerror("Error", "Could not load sessions.py")
            return

        from core.plan_generator import days_to_generate, detect_cycle

        user_data = sess.USER_DATA

        # Check if the very last session is a special (string) day value
        sorted_dates = sorted(user_data.keys())
        last_day_obj = None
        if sorted_dates:
            last_session = user_data[sorted_dates[-1]]
            v = last_session.get("day")
            last_day_obj = v if isinstance(v, (int, str)) else None

        if isinstance(last_day_obj, str):
            # State 2: string day ("PR", "small PR", etc.) — planning blocked
            messagebox.showinfo(
                "Planning Paused",
                f"Last session was a '{last_day_obj}' session.\n"
                "Start your next training day manually before planning ahead.",
            )
            return

        N, last_day_int = detect_cycle(user_data)

        if N is None:
            # State 3: cycle length unknown — too few data
            messagebox.showinfo(
                "Cycle Unknown",
                "Could not detect your split cycle yet.\n"
                "Complete at least one full cycle (all Day values returning to Day 1) "
                "before using 'Plan Next Cycle'.",
            )
            return

        day_nums = days_to_generate(N, last_day_int)
        if not day_nums:
            messagebox.showinfo(
                "Nothing to add", "All days in the current cycle are already planned."
            )
            return

        # State 1: show the preview dialog
        try:
            from core.plan_generator import build_planned_sessions

            planned = build_planned_sessions(file_path, day_nums)
        except Exception as e:
            messagebox.showerror("Plan Build Error", str(e))
            return

        if last_day_int >= N:
            why = f"Starting new cycle — all {N} days"
        else:
            days_str = ", ".join(f"Day {d}" for d in day_nums)
            why = f"Completing cycle of {N} — generating {days_str}"

        dialog = PlanPreviewDialog(self, planned, why, file_path)
        self.wait_window(dialog)

        if dialog.confirmed:
            # Refresh recent sessions panel
            threading.Thread(target=self._load_recent_sessions, daemon=True).start()
            self.set_status(
                f"✅ Added {len(planned)} session(s)", "#4caf50", auto_reset_ms=5000
            )

    # -------------------------------------------------------------------------
    # Experimental features
    # -------------------------------------------------------------------------
    def _load_sessions(self, p) -> object | None:
        """Helper: ensure sessions_dir is on sys.path, reload sessions module.
        Returns the module or None on failure (shows error dialog itself)."""
        if p.sessions_dir not in sys.path:
            sys.path.insert(0, p.sessions_dir)
        try:
            import sessions

            importlib.reload(sessions)
            return sessions
        except Exception as e:
            messagebox.showerror("Import Error", f"Could not load sessions.py:\n{e}")
            return None

    def run_validate_sessions(self):
        """Run the data-integrity check on sessions.py without generating Excel."""
        p = self.manager.get_active_profile()
        if not p:
            messagebox.showerror("Error", "No active profile.")
            return

        file_path = os.path.join(p.sessions_dir, "sessions.py")
        if not os.path.exists(file_path):
            messagebox.showerror("Error", f"sessions.py not found in {p.sessions_dir}")
            return

        self.set_status("Validating sessions.py…", "white")

        sessions = self._load_sessions(p)
        if sessions is None:
            self.set_status(
                "Validation failed: import error", "red", auto_reset_ms=6000
            )
            return

        # Open a throw-away workbook just to run validate_data()
        dummy_path = os.path.join(tempfile.gettempdir(), "_ironlog_validate_dummy.xlsx")
        try:
            processor = TrainingLogProcessor(
                dummy_path,
                sessions.EXERCISE_REGISTRY,
                sessions.USER_DATA,
                sessions.BODYMASS_LOG,
                p.to_dict(),
            )
            processor.validate_data()

            # Also report None-mass entries as a useful warning
            date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
            none_mass_dates = [
                d
                for d, v in sessions.BODYMASS_LOG.items()
                if date_pattern.match(d)
                and isinstance(v, dict)
                and v.get("mass") is None
            ]

            # Clean up the dummy workbook without persisting it
            try:
                processor.wb.close()
            except Exception:
                pass
            try:
                os.remove(dummy_path)
            except Exception:
                pass

            msg = "✅ sessions.py is valid! No data mismatches found."
            if none_mass_dates:
                msg += (
                    f"\n\n⚠️  {len(none_mass_dates)} BODYMASS_LOG "
                    f"entr{'y' if len(none_mass_dates) == 1 else 'ies'} "
                    f"still have mass=None:\n"
                )
                msg += "\n".join(f"  • {d}" for d in none_mass_dates)
                msg += (
                    "\n\nUse 🧪 Experimental → Fill-in Missing Masses to complete them."
                )

            messagebox.showinfo("Validation Result", msg)
            self.set_status("✅ Validation passed", "green", auto_reset_ms=5000)

        except ValueError as ve:
            self.set_status("❌ Validation failed", "red", auto_reset_ms=8000)
            messagebox.showerror("Validation Failed", str(ve))
            try:
                os.remove(dummy_path)
            except Exception:
                pass
        except Exception as e:
            self.set_status("Validation error", "red", auto_reset_ms=6000)
            messagebox.showerror("Unexpected Error", str(e))

    def run_bodymass_prefill(self):
        """Scan USER_DATA for real YYYY-MM-DD dates missing from BODYMASS_LOG
        and append them with {"mass": None} as placeholders."""
        p = self.manager.get_active_profile()
        if not p:
            messagebox.showerror("Error", "No active profile.")
            return

        file_path = os.path.join(p.sessions_dir, "sessions.py")
        if not os.path.exists(file_path):
            messagebox.showerror("Error", f"sessions.py not found in {p.sessions_dir}")
            return

        self.set_status("Scanning sessions.py…", "white")

        sessions = self._load_sessions(p)
        if sessions is None:
            self.set_status("Error loading sessions.py", "red", auto_reset_ms=6000)
            return

        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        user_dates = {k for k in sessions.USER_DATA.keys() if date_pattern.match(k)}
        existing_dates = set(sessions.BODYMASS_LOG.keys())
        missing = sorted(user_dates - existing_dates)

        if not missing:
            self.set_status(
                "All dates already in BODYMASS_LOG.", "gray", auto_reset_ms=4000
            )
            messagebox.showinfo(
                "Up to Date",
                "All USER_DATA dates are already in BODYMASS_LOG. Nothing to add.",
            )
            return

        date_list = "\n".join(f"  {d}" for d in missing)
        confirm = messagebox.askyesno(
            "Prefill Mass Dates",
            f"The following {len(missing)} date(s) will be added to BODYMASS_LOG "
            f'with {{"mass": None}}:\n\n{date_list}\n\nProceed?',
        )
        if not confirm:
            self.set_status("Prefill cancelled.", "gray", auto_reset_ms=3000)
            return

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()  # preserve line endings

        # Find BODYMASS_LOG's closing brace by looking for a bare '}' line
        # at column 0 after the opening line — more robust than character counting
        # since comments inside the block can contain { } characters.
        start_line = next(
            (i for i, ln in enumerate(lines) if ln.startswith("BODYMASS_LOG = {")), -1
        )
        if start_line == -1:
            messagebox.showerror(
                "Error", "Could not locate BODYMASS_LOG in sessions.py"
            )
            self.set_status("Error: BODYMASS_LOG not found", "red", auto_reset_ms=6000)
            return

        close_line = next(
            (
                i
                for i in range(start_line + 1, len(lines))
                if lines[i].rstrip("\r\n") == "}"
            ),
            -1,
        )
        if close_line == -1:
            messagebox.showerror(
                "Error", "Could not find closing brace of BODYMASS_LOG"
            )
            self.set_status("Error: parse failed", "red", auto_reset_ms=6000)
            return

        insert_text = "".join(f'    "{d}": {{"mass": None}},\n' for d in missing)
        new_lines = lines[:close_line] + [insert_text] + lines[close_line:]

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        self.set_status(
            f"✅ Added {len(missing)} date(s) to BODYMASS_LOG.",
            "green",
            auto_reset_ms=6000,
        )
        messagebox.showinfo(
            "Done",
            f"Successfully added {len(missing)} date(s) to BODYMASS_LOG in sessions.py.\n\n"
            f"Use 🧪 Experimental → Fill-in Missing Masses to enter the actual values.",
        )

    def run_mass_fillin_dialog(self):
        """Show a dialog to fill in BODYMASS_LOG entries where mass is None."""
        p = self.manager.get_active_profile()
        if not p:
            messagebox.showerror("Error", "No active profile.")
            return

        file_path = os.path.join(p.sessions_dir, "sessions.py")
        if not os.path.exists(file_path):
            messagebox.showerror("Error", f"sessions.py not found in {p.sessions_dir}")
            return

        sessions = self._load_sessions(p)
        if sessions is None:
            return

        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        none_entries = sorted(
            [
                d
                for d, v in sessions.BODYMASS_LOG.items()
                if date_pattern.match(d)
                and isinstance(v, dict)
                and v.get("mass") is None
            ]
        )

        if not none_entries:
            messagebox.showinfo(
                "All Done", "No missing mass entries in BODYMASS_LOG! 🎉"
            )
            self.set_status("No missing masses to fill.", "green", auto_reset_ms=4000)
            return

        # Build the fill-in dialog
        win = ctk.CTkToplevel(self)
        win.title("Fill-in Missing Masses")
        win.geometry("380x520")
        win.attributes("-topmost", True)
        win.after(100, win.focus_force)

        ctk.CTkLabel(
            win, text="Fill-in Missing Body Mass Values", font=("Roboto", 15, "bold")
        ).pack(pady=(15, 2))
        ctk.CTkLabel(
            win,
            text="Leave blank to keep as None",
            font=("Roboto", 11),
            text_color="gray",
        ).pack(pady=(0, 5))

        scroll = ctk.CTkScrollableFrame(win)
        scroll.pack(fill="both", expand=True, padx=15, pady=5)

        field_map: dict[str, ctk.CTkEntry] = {}
        for date_str in none_entries:
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(
                row, text=date_str, font=("Roboto", 13), width=110, anchor="w"
            ).pack(side="left", padx=5)
            entry = ctk.CTkEntry(row, placeholder_text="e.g. 83.5", width=150)
            entry.pack(side="left", padx=5)
            ctk.CTkLabel(row, text="kg", font=("Roboto", 12), text_color="gray").pack(
                side="left"
            )
            field_map[date_str] = entry

        def save_masses():
            updates: dict[str, float] = {}
            for date_str, entry in field_map.items():
                val_str = entry.get().strip()
                if not val_str:
                    continue
                try:
                    updates[date_str] = float(val_str)
                except ValueError:
                    messagebox.showerror(
                        "Invalid Input",
                        f"'{val_str}' is not a valid number for {date_str}.",
                    )
                    return

            if not updates:
                messagebox.showinfo("Nothing to Save", "No values were entered.")
                return

            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            for date_str, val in updates.items():
                # Exact match first (format guaranteed by prefill)
                old = f'"{date_str}": {{"mass": None}}'
                new = f'"{date_str}": {{"mass": {val}}}'
                if old in source:
                    source = source.replace(old, new, 1)
                else:
                    # Fallback: handle any whitespace variation
                    source = re.sub(
                        rf'("{re.escape(date_str)}")\s*:\s*\{{"mass"\s*:\s*None\}}',
                        rf'\1: {{"mass": {val}}}',
                        source,
                    )

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(source)

            win.destroy()
            self.set_status(
                f"✅ Saved {len(updates)} mass value(s).", "green", auto_reset_ms=6000
            )
            messagebox.showinfo(
                "Saved", f"Updated {len(updates)} mass value(s) in sessions.py."
            )

        ctk.CTkButton(
            win, text="💾 Save Mass Values", fg_color="green", command=save_masses
        ).pack(pady=(5, 3), padx=15, fill="x")
        ctk.CTkButton(win, text="Cancel", fg_color="gray", command=win.destroy).pack(
            pady=(0, 15), padx=15, fill="x"
        )

    # -------------------------------------------------------------------------
    # Other actions
    # -------------------------------------------------------------------------
    def open_latest_excel(self):
        """Open the most recently modified Training_Log_*.xlsx in the output folder."""
        p = self.manager.get_active_profile()
        if not p or not os.path.exists(p.output_dir):
            messagebox.showwarning(
                "Not Found",
                f"Output folder does not exist:\n{p.output_dir if p else '(no profile)'}",
            )
            self.set_status("Output folder not found.", "orange", auto_reset_ms=4000)
            return

        pattern = os.path.join(p.output_dir, "Training_Log_*.xlsx")
        matches = glob.glob(pattern)
        if not matches:
            messagebox.showwarning(
                "Not Found", f"No Training_Log_*.xlsx files found in:\n{p.output_dir}"
            )
            self.set_status("No Excel logs found.", "orange", auto_reset_ms=4000)
            return

        latest = max(matches, key=os.path.getmtime)
        self.set_status(
            f"Opening {os.path.basename(latest)}", "gray", auto_reset_ms=3000
        )
        os.startfile(latest)

    def run_scraper(self):
        self.set_status("Scraping started (check console if needed)…", "white")
        script_path = os.path.join(
            os.path.dirname(__file__), "..", "scripts", "batch_scraper.py"
        )
        try:
            subprocess.Popen([sys.executable, script_path])
        except Exception as e:
            self.set_status(f"Scraper Failed: {e}", "red", auto_reset_ms=6000)

    def edit_sessions(self):
        p = self.manager.get_active_profile()
        file_path = os.path.join(p.sessions_dir, "sessions.py")
        if os.path.exists(file_path):
            os.startfile(file_path)
        else:
            self.set_status(
                "sessions.py not found in selected directory", "red", auto_reset_ms=5000
            )

    def open_output(self):
        p = self.manager.get_active_profile()
        if os.path.exists(p.output_dir):
            os.startfile(p.output_dir)

    def open_app_data_folder(self):
        """Opens the directory where config.json and profiles.json are stored"""
        if getattr(sys, "frozen", False):
            path = os.path.join(
                os.environ.get("APPDATA", os.path.expanduser("~")), "IronLog"
            )
        else:
            path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

        os.makedirs(path, exist_ok=True)
        os.startfile(path)


# =============================================================================
# Plan Preview Dialog
# =============================================================================


class PlanPreviewDialog(ctk.CTkToplevel):
    """Editable preview of planned sessions before writing to sessions.py."""

    def __init__(self, parent, planned, why: str, file_path: str):
        super().__init__(parent)
        self.title("Plan Next Cycle")
        self.geometry("820x600")
        self.minsize(1200, 450)
        self.grab_set()  # modal
        self.confirmed = False
        self._planned = planned
        self._file_path = file_path
        self._widgets: list = []  # (session_idx, ex_idx, sets_var, reps_var, mass_var, comment_var)
        self._date_vars: list = []  # one StringVar per session

        self._build(why)

    def _build(self, why: str):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="Plan Next Cycle", font=("Roboto", 17, "bold")).pack(
            anchor="w", padx=18, pady=(14, 2)
        )
        ctk.CTkLabel(hdr, text=why, font=("Roboto", 12), text_color="#888").pack(
            anchor="w", padx=18, pady=(0, 12)
        )

        # Scrollable body
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=8)

        for s_idx, ps in enumerate(self._planned):
            # Session header row (date field + day badge)
            s_hdr = ctk.CTkFrame(scroll, fg_color="#222", corner_radius=10)
            s_hdr.pack(fill="x", pady=(10, 4))

            ctk.CTkLabel(
                s_hdr,
                text=f"Day {ps.day_number}",
                font=("Roboto", 13, "bold"),
                fg_color="#6A1B9A",
                corner_radius=6,
                width=60,
                height=26,
            ).pack(side="left", padx=12, pady=8)

            date_var = ctk.StringVar(value=ps.date_str)
            self._date_vars.append(date_var)
            ctk.CTkLabel(
                s_hdr, text="Date:", font=("Roboto", 12), text_color="#aaa"
            ).pack(side="left", padx=(8, 2))
            ctk.CTkEntry(
                s_hdr, textvariable=date_var, width=110, height=28, font=("Roboto", 12)
            ).pack(side="left", padx=(0, 12))

            # Column headers
            col_hdr = ctk.CTkFrame(scroll, fg_color="transparent")
            col_hdr.pack(fill="x", padx=8)
            for text, w in [
                ("Exercise", 200),
                ("Sets", 50),
                ("Reps", 100),
                ("Mass (kg)", 140),
                ("Comment", 0),
            ]:
                ctk.CTkLabel(
                    col_hdr,
                    text=text,
                    font=("Roboto", 11),
                    text_color="#666",
                    width=w,
                    anchor="w",
                ).pack(side="left", padx=4)

            # Exercise rows
            for e_idx, ex in enumerate(ps.exercises):
                ex_row = ctk.CTkFrame(scroll, fg_color="transparent")
                ex_row.pack(fill="x", padx=8, pady=2)

                ctk.CTkLabel(
                    ex_row,
                    text=ex.display_name,
                    font=("Roboto", 12),
                    width=200,
                    anchor="w",
                    text_color="#ddd",
                ).pack(side="left", padx=4)

                sets_v = ctk.StringVar(value=str(ex.sets))
                reps_v = ctk.StringVar(value=str(ex.reps))
                mass_v = ctk.StringVar(value=str(ex.mass))
                comment_v = ctk.StringVar(value=ex.comment)

                for var, w in [
                    (sets_v, 5),    # ~40px
                    (reps_v, 12),   # ~96px
                    (mass_v, 17),   # ~136px
                ]:  # widths in chars for tk.Entry
                    e = tk.Entry(
                        ex_row,
                        textvariable=var,
                        width=w,
                        font=("Arial", 12),
                        bg="#222222",
                        fg="#dddddd",
                        insertbackground="white",
                        relief="flat",
                        highlightbackground="#444444",
                        highlightthickness=1,
                    )
                    e.pack(side="left", padx=4, ipady=4)

                comment_e = tk.Entry(
                    ex_row,
                    textvariable=comment_v,
                    font=("Arial", 12),
                    bg="#222222",
                    fg="#dddddd",
                    insertbackground="white",
                    relief="flat",
                    highlightbackground="#444444",
                    highlightthickness=1,
                )
                comment_e.pack(side="left", padx=4, fill="x", expand=True, ipady=4)

                def make_add_mass_cb(m_var=mass_v, c_var=comment_v):
                    def cb():
                        m_str = m_var.get()
                        parts = [p.strip() for p in m_str.split(",") if p.strip()]
                        new_parts = []
                        for p in parts:
                            try:
                                v = float(p)
                                if v > 0: v += 2.5
                                new_parts.append(f"{v:g}")
                            except ValueError:
                                new_parts.append(p)
                        if new_parts:
                            m_var.set(", ".join(new_parts))
                            
                        c = c_var.get()
                        match = re.search(r'\+([0-9.]+) kg', c)
                        if match:
                            curr_plus = float(match.group(1))
                            c = re.sub(r'\+[0-9.]+ kg', f'+{curr_plus + 2.5:g} kg', c)
                        else:
                            c = (c + " +2.5 kg").strip()
                        c_var.set(c)
                    return cb
                
                def make_add_reps_cb(r_var=reps_v, c_var=comment_v):
                    def cb():
                        r_str = r_var.get()
                        parts = [p.strip() for p in r_str.split(",") if p.strip()]
                        new_parts = []
                        for p in parts:
                            try:
                                v = int(float(p))
                                v += 2
                                new_parts.append(str(v))
                            except ValueError:
                                new_parts.append(p)
                        if new_parts:
                            r_var.set(", ".join(new_parts))
                            
                        c = c_var.get()
                        match = re.search(r'\+([0-9]+) reps', c)
                        if match:
                            curr_plus = int(match.group(1))
                            c = re.sub(r'\+[0-9]+ reps', f'+{curr_plus + 2} reps', c)
                        else:
                            c = (c + " +2 reps").strip()
                        c_var.set(c)
                    return cb

                ctk.CTkButton(
                    ex_row, text="+2.5 kg", width=60, height=24, font=("Roboto", 11),
                    fg_color="#1B5E20", hover_color="#2E7D32", 
                    command=make_add_mass_cb()
                ).pack(side="left", padx=2)

                ctk.CTkButton(
                    ex_row, text="+2 Reps", width=60, height=24, font=("Roboto", 11),
                    fg_color="#6A1B9A", hover_color="#7B1FA2", 
                    command=make_add_reps_cb()
                ).pack(side="left", padx=2)

                self._widgets.append((s_idx, e_idx, sets_v, reps_v, mass_v, comment_v))

        # Footer buttons
        footer = ctk.CTkFrame(self, fg_color="#111", corner_radius=0)
        footer.pack(fill="x", side="bottom")
        ctk.CTkButton(
            footer,
            text="Cancel",
            width=110,
            fg_color="#333",
            hover_color="#444",
            command=self.destroy,
        ).pack(side="left", padx=16, pady=12)
        ctk.CTkButton(
            footer,
            text="✅  Write to sessions.py",
            width=200,
            fg_color="#1B5E20",
            hover_color="#2E7D32",
            font=("Roboto", 13, "bold"),
            command=self._on_confirm,
        ).pack(side="right", padx=16, pady=12)

    def _on_confirm(self):
        from core.plan_generator import write_planned_sessions

        # Read back all edits from widget vars
        for s_idx, e_idx, sets_v, reps_v, mass_v, comment_v in self._widgets:
            ex = self._planned[s_idx].exercises[e_idx]
            try:
                ex.sets = max(1, int(sets_v.get()))
                ex.reps = reps_v.get().strip()
                ex.mass = mass_v.get().strip()
                ex.comment = comment_v.get().strip()
            except ValueError:
                pass  # keep original if parse fails

        # Apply edited dates
        for s_idx, date_var in enumerate(self._date_vars):
            self._planned[s_idx].date_str = date_var.get().strip()

        try:
            write_planned_sessions(self._file_path, self._planned)
            self.confirmed = True
            self.destroy()
        except Exception as e:
            import tkinter.messagebox as mb

            mb.showerror("Write Error", str(e), parent=self)


if __name__ == "__main__":
    app = IronLogApp()
    app.mainloop()
