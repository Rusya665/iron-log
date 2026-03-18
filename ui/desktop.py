import customtkinter as ctk
from tkinter import messagebox
from CTkMenuBar import CTkTitleMenu, CustomDropdownMenu
import os
import sys
import subprocess
import webbrowser
from core.profile_manager import ProfileManager, Profile
from core.xlsx_generator import TrainingLogProcessor
from datetime import datetime

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class IronLogApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Iron Log - Strength Tracker")
        self.geometry("900x600")

        self.manager = ProfileManager()
        self.menu = None
        self.init_menu()
        
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)

        if not self.manager.profiles:
            self.show_profile_creator()
        elif self.manager.remember_last_user and self.manager.active_profile_index != -1:
            self.show_dashboard()
        else:
            self.show_profile_picker()

    def init_menu(self):
        if self.menu:
            # CTkTitleMenu doesn't easily allow clearing cascades.
            # We'll try to destroy the old menu and create a new one to be safe.
            self.menu.destroy()
            
        self.menu = CTkTitleMenu(self)
        
        # App Menu
        app_btn = self.menu.add_cascade("App")
        app_dropdown = CustomDropdownMenu(widget=app_btn)
        app_dropdown.add_option(option="New Profile", command=self.show_profile_creator)
        app_dropdown.add_option(option="Switch User", command=self.show_profile_picker)
        app_dropdown.add_separator()
        app_dropdown.add_option(option="Exit", command=self.quit)

        # Settings Menu
        self.init_settings_menu()

        # Profiles Menu
        self.update_profiles_menu()

    def update_profiles_menu(self):
        # Remove existing Profiles menu if it exists (simplistic update)
        # CTkTitleMenu doesn't have a direct "remove" for cascades easily in some versions, 
        # so we recreate or just add. Better approach: dynamic dropdown.
        
        prof_btn = self.menu.add_cascade("Profiles")
        prof_dropdown = CustomDropdownMenu(widget=prof_btn)
        
        for i, profile in enumerate(self.manager.profiles):
            sub = prof_dropdown.add_submenu(profile.name)
            sub.add_option(option="Select", command=lambda idx=i: self.select_profile(idx))
            sub.add_option(option="Edit", command=lambda idx=i: self.show_profile_creator(idx))
            sub.add_separator()
            sub.add_option(option="Delete", command=lambda idx=i: self.delete_profile(idx))

    def init_settings_menu(self):
        settings_btn = self.menu.add_cascade("Settings")
        settings_dropdown = CustomDropdownMenu(widget=settings_btn)
        
        status = "Enabled" if self.manager.remember_last_user else "Disabled"
        settings_dropdown.add_option(option=f"Auto-Login: {status}", command=self.toggle_auto_login)
        
        p = self.manager.get_active_profile()
        if p:
            settings_dropdown.add_separator()
            pr_status = "ON" if p.show_pr else "OFF"
            std_status = "ON" if p.show_standards else "OFF"
            mile_status = "ON" if p.show_milestones else "OFF"
            
            settings_dropdown.add_option(option=f"Show PRs: {pr_status}", command=lambda: self.toggle_feature("show_pr"))
            settings_dropdown.add_option(option=f"Show Standards: {std_status}", command=lambda: self.toggle_feature("show_standards"))
            settings_dropdown.add_option(option=f"Show Milestones: {mile_status}", command=lambda: self.toggle_feature("show_milestones"))

    def toggle_auto_login(self):
        self.manager.remember_last_user = not self.manager.remember_last_user
        self.manager.save_profiles()
        self.init_menu() # Refresh menu to show new status
        if hasattr(self, "status_label"):
            self.status_label.configure(text=f"Auto-Login {'enabled' if self.manager.remember_last_user else 'disabled'}", text_color="gray")

    def toggle_feature(self, feature_name):
        p = self.manager.get_active_profile()
        if p:
            current_val = getattr(p, feature_name)
            setattr(p, feature_name, not current_val)
            self.manager.save_profiles()
            self.init_menu()
            if hasattr(self, "status_label"):
                status = "enabled" if getattr(p, feature_name) else "disabled"
                feature_display = feature_name.replace("show_", "").upper()
                self.status_label.configure(text=f"Chart Feature {feature_display} {status}", text_color="gray")

    def clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_profile_picker(self):
        self.clear_container()
        
        label = ctk.CTkLabel(self.container, text="Select Your Profile", font=("Roboto", 24, "bold"))
        label.pack(pady=40)

        grid = ctk.CTkFrame(self.container, fg_color="transparent")
        grid.pack(pady=10)

        for i, profile in enumerate(self.manager.profiles):
            btn = ctk.CTkButton(grid, text=profile.name, width=200, height=100,
                               command=lambda idx=i: self.select_profile(idx))
            btn.grid(row=i // 3, column=i % 3, padx=10, pady=10)

        add_btn = ctk.CTkButton(self.container, text="+ New Profile", command=self.show_profile_creator, fg_color="gray")
        add_btn.pack(pady=20)

    def delete_profile(self, index):
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete profile '{self.manager.profiles[index].name}'?"):
            self.manager.delete_profile(index)
            self.init_menu() # Refresh whole menu to update profiles list
            if not self.manager.profiles:
                self.show_profile_creator()
            else:
                self.show_profile_picker()

    def show_profile_creator(self, profile_index=None):
        self.clear_container()
        is_edit = profile_index is not None
        title = "Edit Profile" if is_edit else "Create New Profile"
        p = self.manager.profiles[profile_index] if is_edit else None

        ctk.CTkLabel(self.container, text=title, font=("Roboto", 24, "bold")).pack(pady=20)
        
        form = ctk.CTkFrame(self.container)
        form.pack(pady=10, padx=50, fill="x")

        ctk.CTkLabel(form, text="Name:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        name_entry = ctk.CTkEntry(form, placeholder_text="e.g. Rusya")
        name_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        if p: name_entry.insert(0, p.name)

        ctk.CTkLabel(form, text="Sex:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        sex_var = ctk.StringVar(value=p.sex if p else "male")
        ctk.CTkRadioButton(form, text="Male", variable=sex_var, value="male").grid(row=1, column=1, padx=10, pady=10, sticky="w")
        ctk.CTkRadioButton(form, text="Female", variable=sex_var, value="female").grid(row=1, column=1, padx=80, pady=10, sticky="w")

        ctk.CTkLabel(form, text="Sessions Dir:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
        sessions_entry = ctk.CTkEntry(form, width=300)
        sessions_entry.grid(row=2, column=1, padx=10, pady=10)
        if p: sessions_entry.insert(0, p.sessions_dir)
        
        def browse_sessions():
            path = ctk.filedialog.askdirectory()
            if path:
                sessions_entry.delete(0, "end")
                sessions_entry.insert(0, path)
        
        ctk.CTkButton(form, text="Browse", width=60, command=browse_sessions).grid(row=2, column=2, padx=10)

        def save():
            name = name_entry.get()
            s_dir = sessions_entry.get()
            if not name or not s_dir:
                if hasattr(self, 'status_label'):
                    self.status_label.configure(text="Name and Sessions Dir are required!", text_color="red")
                    self.status_label.pack(side="bottom", pady=20)
                return

            new_p = Profile(
                name=name,
                sessions_dir=s_dir,
                output_dir=os.path.join(s_dir, "gym"),
                sex=sex_var.get()
            )
            
            if is_edit:
                self.manager.update_profile(profile_index, new_p)
                self.init_menu() # Update menu names
                self.show_dashboard()
            else:
                self.manager.add_profile(new_p)
                self.init_menu() # Add to menu
                self.show_profile_picker()

        btn_text = "Save Changes" if is_edit else "Create Profile"
        ctk.CTkButton(self.container, text=btn_text, command=save, fg_color="green").pack(pady=20)
        
        if self.manager.profiles:
            cancel_cmd = self.show_dashboard if is_edit else self.show_profile_picker
            ctk.CTkButton(self.container, text="Cancel", command=cancel_cmd).pack()

    def select_profile(self, index):
        self.manager.set_active(index)
        self.show_dashboard()

    def show_dashboard(self):
        self.clear_container()
        p = self.manager.get_active_profile()
        
        header = ctk.CTkFrame(self.container, height=60)
        header.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header, text=f"Welcome, {p.name}", font=("Roboto", 20, "bold")).pack(side="left", padx=20)

        main_area = ctk.CTkFrame(self.container)
        main_area.pack(fill="both", expand=True, padx=10, pady=10)

        # Actions
        ctk.CTkLabel(main_area, text="Actions", font=("Roboto", 18, "bold")).pack(pady=(20, 10))
        
        btn_box = ctk.CTkFrame(main_area, fg_color="transparent")
        btn_box.pack(pady=10)

        # Row 1: Primary Action (Spans 2 columns)
        ctk.CTkButton(btn_box, text="🚀 Generate Excel Log", height=70, font=("Roboto", 16, "bold"), 
                       command=self.run_log_generator).grid(row=0, column=0, columnspan=2, padx=10, pady=20, sticky="ew")

        # Row 2: Routine tools
        ctk.CTkButton(btn_box, text="⚡ Run Scraper", height=50, fg_color="orange", hover_color="#d35400",
                       command=self.run_scraper).grid(row=1, column=0, padx=10, pady=10)
        ctk.CTkButton(btn_box, text="📚 Exercise Library", height=50, fg_color="#3498db", 
                       command=self.show_exercise_library).grid(row=1, column=1, padx=10, pady=10)

        # Row 3: Maintenance tools
        ctk.CTkButton(btn_box, text="📝 Edit Sessions.py", height=50, fg_color="#7f8c8d", 
                       command=self.edit_sessions).grid(row=2, column=0, padx=10, pady=10)
        ctk.CTkButton(btn_box, text="📊 View Output Folder", height=50, fg_color="#34495e", 
                       command=self.open_output).grid(row=2, column=1, padx=10, pady=10)

        self.status_label = ctk.CTkLabel(main_area, text="Ready", text_color="gray")
        self.status_label.pack(side="bottom", pady=20)

    def show_exercise_library(self):
        from core.standards import EXERCISE_STANDARDS

        lib_win = ctk.CTkToplevel(self)
        lib_win.title("Exercise Library")
        lib_win.geometry("600x700")
        lib_win.after(100, lib_win.focus_force)  # Grab focus after window settles
        lib_win.after(100, lib_win.lift)

        ctk.CTkLabel(lib_win, text="Search Exercises", font=("Roboto", 18, "bold")).pack(pady=10)

        search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(lib_win, textvariable=search_var, placeholder_text="Type to filter...")
        search_entry.pack(fill="x", padx=20, pady=5)
        # Auto-focus the search box
        lib_win.after(150, search_entry.focus_set)

        count_label = ctk.CTkLabel(lib_win, text="", text_color="gray", font=("Roboto", 11))
        count_label.pack()

        scroll_frame = ctk.CTkScrollableFrame(lib_win)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Pre-sort library once — lightweight list of (slug, display) tuples
        LIBRARY = sorted(
            [(slug, info.get("name", slug)) for slug, info in EXERCISE_STANDARDS.items()],
            key=lambda x: x[1]
        )
        MAX_DISPLAY = 50  # Never render more than this many rows at once

        def render_results(matches):
            """Destroy all current rows, then build only the matching subset."""
            for w in scroll_frame.winfo_children():
                w.destroy()
            shown = matches[:MAX_DISPLAY]
            for slug, display in shown:
                row = ctk.CTkFrame(scroll_frame, fg_color="transparent")
                row.pack(fill="x", pady=2)

                ctk.CTkLabel(row, text=display, font=("Roboto", 13)).pack(side="left", padx=5)
                ctk.CTkLabel(row, text=f"({slug})", font=("Roboto", 11), text_color="gray").pack(side="left", padx=5)

                btn_frame = ctk.CTkFrame(row, fg_color="transparent")
                btn_frame.pack(side="right")

                def copy_to_cb(s=slug):
                    self.clipboard_clear()
                    self.clipboard_append(s)
                    if hasattr(self, "status_label"):
                        self.status_label.configure(text=f"Copied '{s}' to clipboard!", text_color="green")

                def open_link(s=slug):
                    webbrowser.open(f"https://strengthlevel.com/strength-standards/{s}")

                ctk.CTkButton(btn_frame, text="Copy ID", width=60, height=24,
                              font=("Roboto", 10), command=copy_to_cb).pack(side="left", padx=2)
                ctk.CTkButton(btn_frame, text="View", width=50, height=24,
                              font=("Roboto", 10), fg_color="#34495e", command=open_link).pack(side="left", padx=2)

            total = len(matches)
            if total > MAX_DISPLAY:
                count_label.configure(text=f"Showing {MAX_DISPLAY} of {total} — type to narrow results")
            elif total == len(LIBRARY):
                count_label.configure(text=f"{total} exercises total")
            else:
                count_label.configure(text=f"{total} result{'s' if total != 1 else ''}")

        _debounce_id = [None]  # mutable container so the inner function can update it

        def update_list(*args):
            # Cancel any pending search and reschedule — fires 250ms after last keypress
            if _debounce_id[0] is not None:
                lib_win.after_cancel(_debounce_id[0])

            def do_search():
                _debounce_id[0] = None
                query = search_var.get().lower().strip()
                if query:
                    matches = [(s, d) for s, d in LIBRARY if query in s.lower() or query in d.lower()]
                else:
                    matches = LIBRARY
                render_results(matches)

            _debounce_id[0] = lib_win.after(250, do_search)

        search_var.trace_add("write", update_list)
        render_results(LIBRARY)  # Initial render (first MAX_DISPLAY results)


    def run_log_generator(self):
        p = self.manager.get_active_profile()
        self.status_label.configure(text="Generating log...", text_color="white")
        
        # Inject paths
        if p.sessions_dir not in sys.path:
            sys.path.insert(0, p.sessions_dir)
            
        try:
            import sessions
            # Force reload if it was already imported (for multi-user switching)
            import importlib
            importlib.reload(sessions)
            
            # --- Multi-User Safety Check ---
            owner = getattr(sessions, "SESSIONS_OWNER", None)
            if owner and owner.strip().lower() != p.name.strip().lower():
                msg = f"WARNING: 'SESSIONS_OWNER' in sessions.py is '{owner}', but current profile is '{p.name}'.\n\nContinue anyway?"
                if not messagebox.askyesno("Profile Mismatch", msg):
                    self.status_label.configure(text="Aborted: Profile mismatch.", text_color="orange")
                    return
            # -------------------------------

            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
            os.makedirs(p.output_dir, exist_ok=True)
            filename = os.path.join(p.output_dir, f"Training_Log_{timestamp}.xlsx")

            processor = TrainingLogProcessor(filename, sessions.EXERCISE_REGISTRY, sessions.USER_DATA, sessions.BODYMASS_LOG, p.to_dict())
            
            # --- Data Integrity Check ---
            try:
                processor.validate_data()
            except ValueError as ve:
                self.status_label.configure(text="Generation Failed: Data Mismatch", text_color="red")
                messagebox.showerror("Data Error", str(ve))
                return
            # ----------------------------

            processor.write_headers()
            processor.process_data(sessions.USER_DATA)
            processor.write_calculations()
            processor.generate_charts()
            processor.write_definitions()
            processor.write_personal_records()
            processor.write_user_profile()
            processor.save()
            
            self.status_label.configure(text="Success! Log saved to output folder.", text_color="green")
            os.startfile(filename)
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}", text_color="red")
            messagebox.showerror("Unexpected Error", str(e))

    def run_scraper(self):
        # We'll call the script as a subprocess
        self.status_label.configure(text="Scraping started (check console if needed)...", text_color="white")
        script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "batch_scraper.py")
        try:
            subprocess.Popen([sys.executable, script_path])
        except Exception as e:
             self.status_label.configure(text=f"Scraper Failed: {e}", text_color="red")

    def edit_sessions(self):
        p = self.manager.get_active_profile()
        file_path = os.path.join(p.sessions_dir, "sessions.py")
        if os.path.exists(file_path):
            os.startfile(file_path)
        else:
            self.status_label.configure(text="sessions.py not found in selected directory", text_color="red")

    def open_output(self):
        p = self.manager.get_active_profile()
        if os.path.exists(p.output_dir):
            os.startfile(p.output_dir)

if __name__ == "__main__":
    app = IronLogApp()
    app.mainloop()
