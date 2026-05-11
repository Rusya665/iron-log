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
from datetime import datetime, timedelta
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


class SimpleToolTip:
    """A generic tooltip for any widget."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.display_timer = None

        self.widget.bind("<Enter>", self.on_enter, add="+")
        self.widget.bind("<Leave>", self.on_leave, add="+")
        self.widget.bind("<ButtonPress>", self.on_leave, add="+")

    def on_enter(self, event=None):
        self._cancel_timer()
        self.display_timer = self.widget.after(500, self.show_tip)

    def on_leave(self, event=None):
        self._cancel_timer()
        self.hide_tip()

    def _cancel_timer(self):
        if self.display_timer:
            self.widget.after_cancel(self.display_timer)
            self.display_timer = None

    def show_tip(self):
        if self.tip_window:
            return
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.overrideredirect(True)
        tw.wm_attributes("-topmost", True)
        
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        tw.geometry(f"+{x}+{y}")

        container = tk.Frame(tw, bg="#1c1c1e", highlightthickness=1, highlightbackground="#333")
        container.pack(padx=1, pady=1)

        tk.Label(
            container,
            text=self.text,
            bg="#1c1c1e",
            fg="#aaa",
            font=("Roboto", 11),
            justify="left",
            padx=8,
            pady=4
        ).pack()

    def hide_tip(self):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


class ExerciseToolTip:
    """
    A custom tooltip for exercises that shows strength standards on hover.
    Includes technical stability fixes: timer management, screen coordinate
    tracking, and borderless topmost window.
    """

    def __init__(self, widget, exercise_id, sex, mass=None, lift=None, is_pr=False):
        self.widget = widget
        self.exercise_id = exercise_id
        self.sex = sex
        self.mass = mass
        self.lift = lift
        self.is_pr = is_pr
        self.tip_window = None
        self.display_timer = None
        self.is_expanded = False

        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
        self.widget.bind("<Button-1>", self.on_click, add="+")

    def on_enter(self, event=None):
        self._cancel_timers()
        self.display_timer = self.widget.after(400, self.show_tip)

    def on_leave(self, event=None):
        self._cancel_timers()
        self.hide_tip()
        self.is_expanded = False

    def on_click(self, event=None):
        # Expand on left-click if tip is visible and not already expanded
        if self.tip_window and not self.is_expanded:
            self.expand_tip()

    def _cancel_timers(self):
        if self.display_timer:
            self.widget.after_cancel(self.display_timer)
            self.display_timer = None

    def show_tip(self):
        if self.tip_window:
            return

        # Resolved standards
        from core.standards import get_tiered_standards

        standards = get_tiered_standards(
            self.exercise_id, self.sex, self.mass if not self.is_expanded else None
        )

        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.overrideredirect(True)
        tw.wm_attributes("-topmost", True)

        # Calculate position
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        tw.geometry(f"+{x}+{y}")

        # Use a frame with a border to simulate CTk look
        container = tk.Frame(tw, bg="#1c1c1e", highlightthickness=1, highlightbackground="#333")
        container.pack(padx=1, pady=1)

        if not standards:
            tk.Label(
                container,
                text="  Standards not available  ",
                bg="#1c1c1e",
                fg="#aaa",
                font=("Roboto", 11),
            ).pack(padx=10, pady=5)
        else:
            self._render_table(container, standards)

    def expand_tip(self):
        self.is_expanded = True
        self.hide_tip()
        self.show_tip()

    def hide_tip(self):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

    def _render_table(self, container, standards):
        # We use grid layout with uniform columns to ensure perfect alignment
        # even with proportional fonts like Roboto.
        
        # Header row
        header = tk.Frame(container, bg="#252525")
        header.pack(fill="x")
        for i in range(6):
            header.columnconfigure(i, weight=1, uniform="std_col")

        cols = ["Mass", "Beg", "Nov", "Int", "Adv", "Eli"]
        for i, c in enumerate(cols):
            tk.Label(
                header,
                text=c,
                bg="#252525",
                fg="white",
                font=("Roboto", 10, "bold"),
                anchor="center",
            ).grid(row=0, column=i, padx=4, pady=2, sticky="ew")

        # Data rows
        target_rounded_bm = int(self.mass / 5.0) * 5 if self.mass else -1

        for bm, levels in sorted(standards.items()):
            is_current_mass_row = bm == target_rounded_bm
            
            row_bg = "#252525" if is_current_mass_row else "#1c1c1e"
            row = tk.Frame(container, bg=row_bg)
            row.pack(fill="x")
            for i in range(6):
                row.columnconfigure(i, weight=1, uniform="std_col")
            
            row_font = ("Roboto", 10, "bold") if is_current_mass_row else ("Roboto", 10)

            # Mass Column
            tk.Label(
                row,
                text=f"{bm}kg",
                bg=row_bg,
                fg="#90caf9",
                font=row_font,
                anchor="w",
            ).grid(row=0, column=0, padx=4, sticky="ew")
            
            # Standards columns
            for i, level in enumerate(["Beginner", "Novice", "Intermediate", "Advanced", "Elite"], 1):
                val = levels.get(level, "-")
                
                # Check achievement for PR sessions
                achieved = False
                if self.is_pr and self.lift and isinstance(val, (int, float)):
                    if self.lift >= val:
                        achieved = True
                
                text_color = "#4ade80" if achieved else "#dddddd"
                cell_font = ("Roboto", 10, "bold") if (achieved or is_current_mass_row) else ("Roboto", 10)
                
                tk.Label(
                    row,
                    text=str(val),
                    bg=row_bg,
                    fg=text_color,
                    font=cell_font,
                    anchor="center",
                ).grid(row=0, column=i, padx=4, sticky="ew")


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

    def _resolve_mass_for_date(self, date_str, bm_log):
        if not bm_log:
            return None
        dates = sorted(bm_log.keys())
        applicable_date = None
        for d in dates:
            if d <= date_str:
                applicable_date = d
            else:
                break
        if not applicable_date:
            return None
        bm_entry = bm_log[applicable_date]
        return (
            bm_entry if isinstance(bm_entry, (int, float)) else bm_entry.get("mass", 0)
        )

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

        app_dropdown.add_option(option="About Iron Log", command=self.show_about_dialog)
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

        ctk.CTkLabel(win, text="Author: Rustem Nizamov", font=("Roboto", 14)).pack(
            pady=5
        )

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

        ctk.CTkLabel(form, text="Data Folder:").grid(
            row=2, column=0, padx=10, pady=10, sticky="e"
        )
        sessions_entry = ctk.CTkEntry(form, width=300)
        sessions_entry.grid(row=2, column=1, padx=10, pady=10)

        hint = ctk.CTkLabel(
            form,
            text="Each user needs their own folder.\nExcel logs will be saved in a 'gym' subfolder here.",
            font=("Roboto", 11),
            text_color="gray",
            justify="left",
        )
        hint.grid(row=3, column=1, sticky="w", padx=10, pady=(0, 10))

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

            # ── Isolation Guard ──────────────────────────────────────────────
            sessions_file = os.path.join(s_dir, "sessions.py")
            if os.path.exists(sessions_file):
                from core.plan_generator import detect_sessions_owner

                existing_owner = detect_sessions_owner(sessions_file)

                if existing_owner and existing_owner.strip().lower() != name.lower():
                    msg = (
                        f"This folder already contains data belonging to '{existing_owner}'.\n\n"
                        f"Choose 'Yes' to use this data as your own.\n"
                        f"Choose 'No' to START FRESH (this will overwrite modern data for {name}).\n"
                        f"Choose 'Cancel' to pick a different folder."
                    )
                    res = messagebox.askyesnocancel("Folder Already in Use", msg)
                    if res is None:  # Cancel
                        return
                    if res is False:  # Start Fresh
                        if messagebox.askyesno(
                            "Confirm Fresh Start",
                            f"Are you sure you want to initialize a NEW split for {name}?\n\nThis will clear any old logs in this folder.",
                        ):
                            new_p = Profile(
                                name=name,
                                sessions_dir=s_dir,
                                output_dir=os.path.join(s_dir, "gym"),
                                sex=sex_var.get(),
                            )
                            self._launch_initial_split_builder(
                                new_p, sessions_file, is_edit, profile_index
                            )
                            return
                        else:
                            return
                    # if True (Yes), we fall through and use the existing owner's name
                    # to ensure the profile name matches SESSIONS_OWNER in sessions.py.
                    name = existing_owner

            elif not os.path.exists(sessions_file):
                validation_label.configure(
                    text="⚠️  sessions.py not found in that folder!"
                )
                if messagebox.askyesno(
                    "sessions.py Not Found",
                    f"sessions.py was not found in:\n{s_dir}\n\nDo you want to initialize it with a new split now?",
                ):
                    new_p = Profile(
                        name=name,
                        sessions_dir=s_dir,
                        output_dir=os.path.join(s_dir, "gym"),
                        sex=sex_var.get(),
                    )
                    self._launch_initial_split_builder(
                        new_p, sessions_file, is_edit, profile_index
                    )
                    return
                elif not messagebox.askyesno(
                    "Save anyway", "Save profile anyway without sessions.py?"
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

    def _launch_initial_split_builder(self, p, sessions_file, is_edit, profile_index):
        dialog = DynamicPlanDialog(
            self,
            sessions_file,
            p,
            title="Create Initial Split",
            mode="initial",
            profile_is_edit=is_edit,
            profile_index=profile_index,
        )
        self.wait_window(dialog)

    def select_profile(self, index):
        self.manager.set_active(index)
        self.show_dashboard()

    # -------------------------------------------------------------------------
    # Dashboard
    # -------------------------------------------------------------------------
    def show_dashboard(self):
        self.clear_container()
        p = self.manager.get_active_profile()
        if not p:
            # Fallback to profile management if no active profile found
            self.show_profile_manager()
            return

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
            mass = self._resolve_mass_for_date(date_str, getattr(sessions, "BODYMASS_LOG", {}))

            exercises_summary = []
            for ex_id, log in day_data.items():
                from core.models import Log

                if not isinstance(log, Log):
                    continue
                name = id_to_name.get(ex_id, ex_id)
                display_name = name[:24] + "…" if len(name) > 24 else name

                n_sets = len(log.reps)
                max_lift = max(log.mass) if log.mass else 0
                
                # Format reps
                if len(set(log.reps)) == 1:
                    reps_part = f"{n_sets} \u00d7 {log.reps[0]}"
                else:
                    reps_part = "-".join(str(r) for r in log.reps)

                # Format mass
                if log.mass and max(log.mass) > 0:
                    if len(set(log.mass)) == 1:
                        mass_part = f" @ {log.mass[0]}kg"
                    else:
                        m_min, m_max = min(log.mass), max(log.mass)
                        mass_part = f" @ {m_min}-{m_max}kg"
                else:
                    mass_part = " (BW)"
                    max_lift = mass if mass else 0

                summary = f"{reps_part}{mass_part}"
                exercises_summary.append((ex_id, display_name, summary, max_lift))

            display_data.append((date_str, day_obj, exercises_summary, mass))

        # Check for profile mismatch
        owner = getattr(sessions, "SESSIONS_OWNER", None)
        is_mismatch = owner and owner.strip().lower() != p.name.lower()

        self.after(
            0,
            lambda d=display_data: self._update_sessions_panel(
                d, last_day_obj, mismatch_owner=owner if is_mismatch else None
            ),
        )

    def _update_sessions_panel(self, data, last_day_obj=None, mismatch_owner=None):
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

        if mismatch_owner:
            banner = tk.Frame(self._sessions_panel, bg="#b91c1c", height=30)
            banner.pack(fill="x", pady=(0, 10))
            tk.Label(
                banner,
                text=f"⚠️ PROFILE MISMATCH: This data belongs to {mismatch_owner} (Profile: {self.manager.get_active_profile().name})",
                bg="#b91c1c",
                fg="white",
                font=("Roboto", 11, "bold"),
            ).pack(pady=4)

        # Outer row — native Frame, no canvas needed
        row = tk.Frame(self._sessions_panel, bg=BG_DARK)
        row.pack(fill="both", expand=True)
        for i in range(len(data)):
            row.columnconfigure(i, weight=1)
        row.rowconfigure(0, weight=1)

        for col_i, (date_str, day_obj, exercises, mass) in enumerate(data):
            is_pr = isinstance(day_obj, str) and day_obj.upper() == "PR"
            
            card_bg = "#2a1a00" if isinstance(day_obj, str) else "#1c1c1e"
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
            for ex_id, ex_name, summary, lift in exercises[:MAX_EX]:
                ex_row = tk.Frame(card, bg=card_bg)
                ex_row.pack(fill="x", padx=12, pady=1)
                name_lbl = tk.Label(
                    ex_row,
                    text=ex_name,
                    bg=card_bg,
                    fg="#dddddd",
                    font=("Roboto", 12),
                    anchor="w",
                )
                name_lbl.pack(side="left")
                tk.Label(
                    ex_row,
                    text=summary,
                    bg=card_bg,
                    fg="#888888",
                    font=("Roboto", 11),
                    anchor="e",
                ).pack(side="right")

                # Bind tooltip
                ExerciseToolTip(
                    name_lbl,
                    ex_id,
                    self.manager.get_active_profile().sex,
                    mass=mass,
                    lift=lift,
                    is_pr=is_pr,
                )

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
            # State 2: string day ("PR", "small PR", etc.) — prompt to configure a new cycle
            if messagebox.askyesno(
                "New Cycle",
                f"Last session was a '{last_day_obj}' session.\n"
                "Would you like to build a new N-Day cycle now?",
            ):
                self._launch_post_pr_builder(p, file_path)
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

        # State 1: normal cycle planning mode
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

        dialog = DynamicPlanDialog(
            self,
            file_path,
            p,
            start_planned=planned,
            title=f"Plan Next Cycle ({why})",
            mode="normal",
        )
        self.wait_window(dialog)

        if dialog.confirmed:
            # Refresh recent sessions panel
            threading.Thread(target=self._load_recent_sessions, daemon=True).start()
            self.set_status(
                f"✅ Added {len(planned)} session(s)", "#4caf50", auto_reset_ms=5000
            )

    def _launch_post_pr_builder(self, p, sessions_file):
        from core.plan_generator import build_planned_sessions, detect_cycle

        sess = self._try_load_sessions(p)
        if sess is None:
            return

        N, last_day_int = detect_cycle(sess.USER_DATA)
        if N is None:
            N = 3
        days_to_plan = list(range(1, N + 1))
        try:
            planned = build_planned_sessions(sessions_file, days_to_plan)
        except Exception:
            planned = None

        dialog = DynamicPlanDialog(
            self,
            sessions_file,
            p,
            start_planned=planned,
            title="Configure New Split",
            mode="post_pr",
        )
        self.wait_window(dialog)

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
# Dynamic Plan Dialog
# =============================================================================


class DynamicPlanDialog(ctk.CTkToplevel):
    """Dynamically build an N-Day split from scratch or edit a generated cycle layout."""

    def __init__(
        self,
        parent,
        file_path: str,
        profile,
        start_planned=None,
        title="Split Builder",
        mode="initial",
        profile_is_edit=False,
        profile_index=None,
    ):
        super().__init__(parent)
        self.title(title)
        self.geometry("980x700")
        self.minsize(980, 500)
        self.grab_set()

        self.confirmed = False

        self._parent_app = parent
        self._file_path = file_path
        self._profile = profile
        self._mode = mode  # 'initial', 'post_pr', 'normal'
        self._profile_is_edit = profile_is_edit
        self._profile_index = profile_index

        import copy

        from core.plan_generator import PlannedSession

        # Default to 3 days if completely empty
        if start_planned:
            self._planned = copy.deepcopy(start_planned)
        else:
            now = datetime.now()
            self._planned = [
                PlannedSession(day_number=1, date_str=now.strftime("%Y-%m-%d"), exercises=[]),
                PlannedSession(day_number=2, date_str=(now + timedelta(days=2)).strftime("%Y-%m-%d"), exercises=[]),
                PlannedSession(day_number=3, date_str=(now + timedelta(days=4)).strftime("%Y-%m-%d"), exercises=[]),
            ]

        self._widgets = []
        self._date_vars = []

        self._main_container = ctk.CTkFrame(self, fg_color="transparent")
        self._main_container.pack(fill="both", expand=True)

        self.scroll = ctk.CTkScrollableFrame(
            self._main_container, fg_color="transparent"
        )
        self.scroll.pack(fill="both", expand=True, padx=12, pady=8)

        # Footer
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
            text="+ Add Day",
            width=110,
            fg_color="#6A1B9A",
            hover_color="#7B1FA2",
            command=self._add_day,
        ).pack(side="left", padx=16, pady=12)

        def _handle_experimental(val):
            if val == "Deload Next Cycle":
                self._prompt_deload()
            elif val == "Restore from Pre-Deload":
                self._prompt_restore_pre_deload()
            # Reset the menu title
            self.after(100, lambda: exp_menu.set("🧪 Experimental"))

        exp_menu = ctk.CTkOptionMenu(
            footer,
            values=["Deload Next Cycle", "Restore from Pre-Deload"],
            command=_handle_experimental,
            font=("Roboto", 13),
            fg_color="#333",
            button_color="#444",
            button_hover_color="#555",
            dropdown_font=("Roboto", 12),
            width=160
        )
        exp_menu.set("🧪 Experimental")
        exp_menu.pack(side="left", padx=16, pady=12)

        save_btn_text = (
            "✅ Save Split"
            if self._mode in ["initial", "post_pr"]
            else "✅ Write to sessions.py"
        )
        ctk.CTkButton(
            footer,
            text=save_btn_text,
            width=200,
            fg_color="#1B5E20",
            hover_color="#2E7D32",
            font=("Roboto", 13, "bold"),
            command=self._on_confirm,
        ).pack(side="right", padx=16, pady=12)

        from core.standards import EXERCISE_STANDARDS

        self._standards = EXERCISE_STANDARDS

        self._build_content()

    def _prompt_deload(self):
        dialog = ctk.CTkInputDialog(text="Enter deload percentage (e.g., 10 for 10%):", title="Deload")
        val = dialog.get_input()
        if val is None:
            return
        try:
            percent = float(val)
            if percent <= 0 or percent >= 100:
                messagebox.showerror("Error", "Percentage must be between 0 and 100")
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid number")
            return
            
        self._save_state()
        
        factor = 1.0 - (percent / 100.0)
        for ps in self._planned:
            for ex in ps.exercises:
                try:
                    current_mass = float(ex.mass)
                    if current_mass > 0:
                        new_mass = current_mass * factor
                        # round to nearest 2.5
                        new_mass = round(new_mass / 2.5) * 2.5
                        ex.mass = f"{new_mass:g}"
                        if ex.comment:
                            ex.comment += f" | {percent:g}% decreased deload"
                        else:
                            ex.comment = f"{percent:g}% decreased deload"
                except ValueError:
                    pass
        
        self._build_content()

    def _prompt_restore_pre_deload(self):
        """Rebuild the plan from the last non-deload cycle at full (100%) weight.
        The user can then apply a deload via 'Deload Next Cycle' if desired."""
        self._save_state()

        day_numbers = [ps.day_number for ps in self._planned]
        try:
            from core.plan_generator import build_pre_deload_baseline

            new_planned = build_pre_deload_baseline(
                self._file_path, day_numbers, 100.0
            )
        except Exception as e:
            messagebox.showerror("Error", f"Could not read pre-deload sessions:\n{e}")
            return

        # Check we actually found baseline data
        total_exercises = sum(len(ps.exercises) for ps in new_planned)
        if total_exercises == 0:
            messagebox.showwarning(
                "Nothing Found",
                "No pre-deload sessions were found in sessions.py.\n"
                "Make sure your normal sessions have no 'deload' in their comments.",
            )
            return

        # Preserve dates the user may have already edited
        for orig, fresh in zip(self._planned, new_planned):
            fresh.date_str = orig.date_str

        self._planned = new_planned
        self._build_content()

    def _remove_day(self, index):
        self._save_state()
        if 0 <= index < len(self._planned):
            self._planned.pop(index)
            # Re-number remaining days
            for i, ps in enumerate(self._planned):
                ps.day_number = i + 1
            self._build_content()

    def _add_day(self):
        self._save_state()
        from core.plan_generator import PlannedSession

        dn = len(self._planned) + 1
        base_date = datetime.now().strftime("%Y-%m-%d")
        if self._planned:
            base_date = self._planned[-1].date_str
        self._planned.append(
            PlannedSession(day_number=dn, date_str=base_date, exercises=[])
        )
        self._build_content()

    def _save_state(self):
        for (
            ps,
            ex,
            row_frame,
            name_str,
            sets_v,
            reps_v,
            mass_v,
            comment_v,
        ) in self._widgets:
            if not row_frame.winfo_exists():
                continue
            ex.var_name = name_str.get().strip()
            try:
                ex.sets = max(1, int(sets_v.get()))
            except ValueError:
                pass
            ex.reps = reps_v.get().strip()
            ex.mass = mass_v.get().strip()
            ex.comment = comment_v.get().strip()

        for ps, date_var in self._date_vars:
            ps.date_str = date_var.get().strip()

    def _build_content(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        self._widgets.clear()
        self._date_vars.clear()
        self._day_containers = []

        hdr = ctk.CTkFrame(self.scroll, fg_color="#1a1a1a", corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text=self.title(), font=("Roboto", 17, "bold")).pack(
            anchor="w", padx=10, pady=(10, 2)
        )
        txt = (
            "Define your training split. Type an exercise name to configure sets/reps.\n"
            "An autocomplete drop-down will suggest exercises from the library as you type."
        )
        ctk.CTkLabel(
            hdr, text=txt, font=("Roboto", 12), text_color="#888", justify="left"
        ).pack(anchor="w", padx=10, pady=(0, 10))

        for s_idx, ps in enumerate(self._planned):
            day_container = ctk.CTkFrame(self.scroll, fg_color="transparent")
            day_container.pack(fill="x", pady=4)
            self._day_containers.append(day_container)

            s_hdr = ctk.CTkFrame(day_container, fg_color="#222", corner_radius=10)
            s_hdr.pack(fill="x", pady=(10, 4))

            ctk.CTkLabel(
                s_hdr,
                text=f"Day {ps.day_number}",
                font=("Roboto", 13, "bold"),
                fg_color="#00695c",
                corner_radius=6,
                width=60,
                height=26,
            ).pack(side="left", padx=12, pady=8)

            date_var = ctk.StringVar(value=ps.date_str)
            self._date_vars.append((ps, date_var))
            ctk.CTkLabel(
                s_hdr, text="Date:", font=("Roboto", 12), text_color="#aaa"
            ).pack(side="left", padx=(8, 2))
            ctk.CTkEntry(
                s_hdr, textvariable=date_var, width=110, height=28, font=("Roboto", 12)
            ).pack(side="left", padx=(0, 12))

            del_btn = ctk.CTkButton(
                s_hdr,
                text="🗑️",
                width=34,
                height=28,
                fg_color="#5a1a1a",
                hover_color="#c62828",
                command=lambda idx=s_idx: self._remove_day(idx),
            )
            del_btn.pack(side="right", padx=12)
            SimpleToolTip(del_btn, "Remove Day")

            ctk.CTkButton(
                s_hdr,
                text="+ Add Exercise",
                width=100,
                height=28,
                fg_color="#0277bd",
                hover_color="#01579b",
                command=lambda p=ps, c=day_container: self._fast_add_exercise(p, c),
            ).pack(side="right", padx=12)

            col_hdr = ctk.CTkFrame(day_container, fg_color="transparent")
            col_hdr.pack(fill="x", padx=8)

            # Matched widths for alignment: 215, 55, 115, 165, remainder, etc.
            # Base tk.Entry width is in chars.
            # width=24 -> ~215px | width=5 -> ~55px | width=12 -> ~115px | width=17 -> ~165px
            layout = [
                ("Exercise Name / Slug", 215),
                ("Sets", 55),
                ("Reps", 115),
                ("Mass (kg)", 165),
                ("Comment", 150),
                ("Quick Actions", 0),
            ]
            for text, w in layout:
                ctk.CTkLabel(
                    col_hdr,
                    text=text,
                    font=("Roboto", 11, "bold"),
                    text_color="#777",
                    width=w,
                    anchor="w",
                ).pack(side="left", padx=4)

            for ex in ps.exercises:
                self._build_exercise_row(ps, ex, day_container)

    def _fast_add_exercise(self, ps, container):
        self._save_state()
        from core.plan_generator import PlannedExercise

        new_ex = PlannedExercise(
            var_name="", display_name="", sets=3, reps="8", mass="0", comment=""
        )
        ps.exercises.append(new_ex)
        self._build_exercise_row(ps, new_ex, container)

    def _fast_remove_exercise(self, ps, ex, row_frame):
        self._save_state()
        if ex in ps.exercises:
            ps.exercises.remove(ex)
        row_frame.destroy()

    def _build_exercise_row(self, ps, ex, container):
        ex_row = ctk.CTkFrame(container, fg_color="transparent")
        ex_row.pack(fill="x", padx=8, pady=2)

        name_v = ctk.StringVar(value=ex.var_name)
        sets_v = ctk.StringVar(value=str(ex.sets))
        reps_v = ctk.StringVar(value=str(ex.reps))
        mass_v = ctk.StringVar(value=str(ex.mass))
        comment_v = ctk.StringVar(value=ex.comment)

        name_e = tk.Entry(
            ex_row,
            textvariable=name_v,
            width=24,
            font=("Arial", 12),
            bg="#222222",
            fg="#dddddd",
            insertbackground="white",
            relief="flat",
            highlightbackground="#444444",
            highlightthickness=1,
        )
        name_e.pack(side="left", padx=4, ipady=4)

        self._setup_autocomplete(name_e, name_v)

        for var, w in [(sets_v, 5), (reps_v, 12), (mass_v, 17)]:
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
            width=15,
            font=("Arial", 12),
            bg="#222222",
            fg="#dddddd",
            insertbackground="white",
            relief="flat",
            highlightbackground="#444444",
            highlightthickness=1,
        )
        comment_e.pack(side="left", padx=4, fill="x", expand=True, ipady=4)

        # Helpers
        def make_add_mass_cb(m_var=mass_v, c_var=comment_v):
            def cb():
                m_str = m_var.get()
                parts = [p.strip() for p in m_str.split(",") if p.strip()]
                new_parts = []
                for p in parts:
                    try:
                        v = float(p)
                        if v > 0:
                            v += 2.5
                        new_parts.append(f"{v:g}")
                    except ValueError:
                        new_parts.append(p)
                if new_parts:
                    m_var.set(", ".join(new_parts))

                c = c_var.get()
                import re

                match = re.search(r"\+([0-9.]+) kg", c)
                if match:
                    curr_plus = float(match.group(1))
                    c = re.sub(r"\+[0-9.]+ kg", f"+{curr_plus + 2.5:g} kg", c)
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
                import re

                match = re.search(r"\+([0-9]+) reps", c)
                if match:
                    curr_plus = int(match.group(1))
                    c = re.sub(r"\+[0-9]+ reps", f"+{curr_plus + 2} reps", c)
                else:
                    c = (c + " +2 reps").strip()
                c_var.set(c)

            return cb

        ctk.CTkButton(
            ex_row,
            text="+2.5 kg",
            width=60,
            height=24,
            font=("Roboto", 11),
            fg_color="#1B5E20",
            hover_color="#2E7D32",
            command=make_add_mass_cb(),
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            ex_row,
            text="+2 Reps",
            width=60,
            height=24,
            font=("Roboto", 11),
            fg_color="#6A1B9A",
            hover_color="#7B1FA2",
            command=make_add_reps_cb(),
        ).pack(side="left", padx=2)

        del_ex_btn = ctk.CTkButton(
            ex_row,
            text="X",
            width=28,
            height=24,
            fg_color="#c62828",
            hover_color="#b71c1c",
            command=lambda: self._fast_remove_exercise(ps, ex, ex_row),
        )
        del_ex_btn.pack(side="left", padx=2)
        SimpleToolTip(del_ex_btn, "Remove Exercise")

        self._widgets.append(
            (ps, ex, ex_row, name_v, sets_v, reps_v, mass_v, comment_v)
        )

    def _setup_autocomplete(self, entry, var):
        # State held via entry dictionary
        if not hasattr(entry, "popup"):
            entry.popup = None

        def on_keyrelease(event):
            # ignore navigation keys
            if event.keysym in ("Up", "Down", "Return", "Escape", "Left", "Right"):
                return

            import re

            val = re.sub(r"\W+", "_", var.get().lower()).strip("_")
            if val and val[0].isdigit():
                val = "_" + val

            if not val:
                close_popup()
                entry.config(fg="#dddddd")
                return

            matches = [s for s in self._standards if val in s]

            # color validation
            if val in self._standards:
                entry.config(fg="#4caf50")
            elif matches:
                entry.config(fg="#ffeb3b")
            else:
                entry.config(fg="#ffab91")

            if not matches or val in self._standards:
                close_popup()
                return

            if not entry.popup:
                entry.popup = tk.Toplevel(entry)
                entry.popup.wm_overrideredirect(True)
                entry.popup.configure(bg="#333333")

                listbox = tk.Listbox(
                    entry.popup,
                    font=("Arial", 11),
                    bg="#333",
                    fg="#ddd",
                    selectbackground="#0277bd",
                    highlightthickness=1,
                    highlightbackground="#555",
                    highlightcolor="#555",
                )
                listbox.pack(fill="both", expand=True)

                def on_select(e=None):
                    if not listbox.curselection():
                        return
                    sel = listbox.get(listbox.curselection()[0])
                    var.set(sel)
                    if entry.winfo_exists():
                        entry.config(fg="#4caf50")
                    close_popup()
                    if entry.winfo_exists():
                        try:
                            entry.focus_set()
                            entry.icursor(tk.END)
                        except tk.TclError:
                            pass

                listbox.bind("<ButtonRelease-1>", on_select)
                entry.popup.listbox = listbox
            else:
                entry.popup.listbox.delete(0, tk.END)

            # Compute position globally
            x = entry.winfo_rootx()
            y = entry.winfo_rooty() + entry.winfo_height()
            w = entry.winfo_width()
            h = min(100, len(matches) * 22) + 2
            entry.popup.wm_geometry(f"{w}x{h}+{x}+{y}")

            for m in matches:
                entry.popup.listbox.insert(tk.END, m)

        def on_updown(event):
            if not entry.popup:
                return
            lb = entry.popup.listbox
            curr = lb.curselection()
            idx = curr[0] if curr else -1
            if event.keysym == "Down":
                idx = min(idx + 1, lb.size() - 1)
            elif event.keysym == "Up":
                idx = max(idx - 1, 0)
            lb.selection_clear(0, tk.END)
            lb.selection_set(idx)
            lb.see(idx)
            return "break"

        def on_return(event):
            if entry.popup and entry.popup.listbox.curselection():
                sel = entry.popup.listbox.get(entry.popup.listbox.curselection()[0])
                var.set(sel)
                entry.config(fg="#4caf50")
                close_popup()
                return "break"

        def close_popup(*args):
            # Check winfo_exists() to avoid TclError if window closed during after() delay
            if not entry.winfo_exists():
                return
            if entry.popup:
                entry.popup.destroy()
                entry.popup = None

        entry.bind("<KeyRelease>", on_keyrelease)
        entry.bind("<Down>", on_updown)
        entry.bind("<Up>", on_updown)
        entry.bind("<Return>", on_return)
        # Delay closing so mouse clicks can register
        entry.bind("<FocusOut>", lambda e: entry.after(150, close_popup))
        self.bind("<Configure>", lambda e: close_popup(), add="+")

    def _on_confirm(self):
        self._save_state()

        # Validation
        for s_idx, ps in enumerate(self._planned):
            for e_idx, ex in enumerate(ps.exercises):
                if not ex.var_name.strip():
                    import tkinter.messagebox as mb

                    mb.showerror(
                        "Validation Error",
                        f"Exercise name cannot be empty (Day {ps.day_number}, row {e_idx + 1}).",
                        parent=self,
                    )
                    return

                reps_list = [r.strip() for r in str(ex.reps).split(",") if r.strip()]
                mass_list = [m.strip() for m in str(ex.mass).split(",") if m.strip()]

                if len(reps_list) > 1 and len(reps_list) != ex.sets:
                    import tkinter.messagebox as mb

                    mb.showerror(
                        "Validation Error",
                        f"In '{ex.var_name}' (Day {ps.day_number}): You specified {ex.sets} sets, but provided {len(reps_list)} rep values.\nProvide 1 unified value, or exactly {ex.sets}.",
                        parent=self,
                    )
                    return

                if len(mass_list) > 1 and len(mass_list) != ex.sets:
                    import tkinter.messagebox as mb

                    mb.showerror(
                        "Validation Error",
                        f"In '{ex.var_name}' (Day {ps.day_number}): You specified {ex.sets} sets, but provided {len(mass_list)} mass values.\nProvide 1 unified value, or exactly {ex.sets}.",
                        parent=self,
                    )
                    return

        try:
            if self._mode == "initial":
                if self._profile_is_edit:
                    self._parent_app.manager.update_profile(
                        self._profile_index, self._profile
                    )
                else:
                    self._parent_app.manager.add_profile(self._profile)
                    self._parent_app.manager.set_active(len(self._parent_app.manager.profiles) - 1)
                self._parent_app.init_menu()

                from core.plan_generator import create_initial_sessions_py

                create_initial_sessions_py(
                    self._file_path,
                    self._profile.name,
                    self._profile.sex,
                    self._planned,
                )

                self._parent_app.show_dashboard()
                self._parent_app.set_status("✅ Initial split created!", "green", 5000)
            else:
                from core.plan_generator import write_planned_sessions

                write_planned_sessions(self._file_path, self._planned)

                import threading

                threading.Thread(
                    target=self._parent_app._load_recent_sessions, daemon=True
                ).start()
                self._parent_app.set_status(
                    f"✅ Created plan with {len(self._planned)} days",
                    "#4caf50",
                    auto_reset_ms=5000,
                )

            self.confirmed = True
            self.destroy()

        except Exception as e:
            import tkinter.messagebox as mb

            mb.showerror("Save Error", str(e), parent=self)


if __name__ == "__main__":
    app = IronLogApp()
    app.mainloop()
