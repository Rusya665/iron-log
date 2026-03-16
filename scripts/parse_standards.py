import json
import os
import re
import sys
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

# Core file paths
CORE_DIR = os.path.join(os.path.dirname(__file__), "..", "core")
STANDARDS_FILE = os.path.join(CORE_DIR, "standards.py")
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "config.json")


def parse_raw_text(raw_text: str) -> dict:
    """Parses raw text pasted from the strengthlevel.com tables or concatenated strings."""
    parsed_data = {}
    lines = raw_text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Try finding numbers with spaces first
        numbers = re.findall(r"\d+", line)

        # Heuristic for long digit strings (e.g., 501525385371)
        if len(numbers) == 1 and len(numbers[0]) > 8:
            # Assuming 6 pairs or triplets of digits (BM, Beg, Nov, Int, Adv, Elite)
            # This is complex to automate perfectly, so we'll try to find a pattern or skip.
            # Most standards are 2-3 digits.
            pass

        if len(numbers) >= 6:
            try:
                bm = int(numbers[0])
                parsed_data[bm] = {
                    "Beginner": int(numbers[1]),
                    "Novice": int(numbers[2]),
                    "Intermediate": int(numbers[3]),
                    "Advanced": int(numbers[4]),
                    "Elite": int(numbers[5]),
                }
            except (ValueError, IndexError):
                continue
    return parsed_data


def write_to_standards(exercise_id: str, data: dict):
    """Updates the EXERCISE_STANDARDS dictionary in the standards file."""
    # This is a bit complex as we need to maintain the python file structure
    # We'll import the current dict, update it, and regenerate the file

    # 1. Load the current standards
    # Ensure project root is in path
    root_dir = os.path.join(os.path.dirname(__file__), "..")
    if root_dir not in sys.path:
        sys.path.append(root_dir)

    try:
        from core.standards import EXERCISE_STANDARDS
    except (ImportError, AttributeError):
        EXERCISE_STANDARDS = {}

    # 2. Update with new data
    # Create the entry structure: { 'name': '...', 'male': { ... }, 'female': { ... } }
    # We'll assume the GUI entry is for a specific gender or both?
    # For simplicity, we'll try to guess or use a default name
    display_name = exercise_id.replace("-", " ").title()
    if exercise_id in EXERCISE_STANDARDS:
        display_name = EXERCISE_STANDARDS[exercise_id].get("name", display_name)

    EXERCISE_STANDARDS[exercise_id] = {
        "name": display_name,
        "male": data,  # We'll assume input is male for now or prompt?
        # For simplicity, let's just use it as the data source
    }

    # 3. Regenerate core/standards.py
    # We need the core logic part first
    with open(STANDARDS_FILE, "r", encoding="utf-8") as f:
        file_content = f.read()

    core_logic_marker = (
        "# Consolidated exercise standards database\nEXERCISE_STANDARDS = {"
    )
    if core_logic_marker not in file_content:
        # If it's the old format, we can't easily auto-migrate without risks
        # But we previously reset it, so it should be fine.
        print(
            "Warning: standards.py does not have the dictionary marker. Please run scraper first."
        )
        return

    core_part = file_content.split(core_logic_marker)[0] + core_logic_marker + "\n"

    # Format the entire dictionary
    dict_content = ""
    for slug, info in sorted(EXERCISE_STANDARDS.items()):
        dict_content += f"    '{slug}': {{\n"
        dict_content += f"        'name': '{info['name']}',\n"
        for gender in ["male", "female"]:
            g_data = info.get(gender)
            if g_data:
                dict_content += f"        '{gender}': {{\n"
                for bm, lvls in sorted(g_data.items()):
                    lvls_str = ", ".join([f"'{k}': {v}" for k, v in lvls.items()])
                    dict_content += f"            {bm}: {{{lvls_str}}},\n"
                dict_content += "        }},\n"
        dict_content += "    }},\n"

    final_content = core_part + dict_content + "}\n"

    with open(STANDARDS_FILE, "w", encoding="utf-8") as f:
        f.write(final_content)


class StandardsParserApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Iron Log - Standards Parser")
        self.geometry("700x600")

        # Load registry
        self.exercises = self.load_exercise_registry()

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Header & ID Selection
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")

        self.lbl_ex = ctk.CTkLabel(
            self.top_frame, text="Select Exercise ID:", font=ctk.CTkFont(weight="bold")
        )
        self.lbl_ex.pack(side="left", padx=10, pady=10)

        exercise_names = (
            [f"{ex.id} ({ex.display_name})" for ex in self.exercises]
            if self.exercises
            else ["No Registry Found"]
        )
        self.ex_var = ctk.StringVar(value=exercise_names[0] if exercise_names else "")
        self.opt_ex = ctk.CTkOptionMenu(
            self.top_frame, values=exercise_names, variable=self.ex_var, width=300
        )
        self.opt_ex.pack(side="left", padx=10, pady=10)

        # 2. Raw Text Input
        self.lbl_hint = ctk.CTkLabel(
            self, text="Paste raw table data below (BM, Beg, Nov, Int, Adv, Elite):"
        )
        self.lbl_hint.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")

        self.txt_input = ctk.CTkTextbox(self, height=300)
        self.txt_input.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")

        # 3. Actions
        self.btn_frame = ctk.CTkFrame(self)
        self.btn_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.btn_frame.grid_columnconfigure((0, 1), weight=1)

        self.btn_clear = ctk.CTkButton(
            self.btn_frame, text="Clear", command=self.clear_input, fg_color="gray"
        )
        self.btn_clear.grid(row=0, column=0, padx=10, pady=10)

        self.btn_save = ctk.CTkButton(
            self.btn_frame,
            text="PARSE & SAVE TO STANDARDS.PY",
            command=self.process,
            fg_color="green",
            hover_color="darkgreen",
        )
        self.btn_save.grid(row=0, column=1, padx=10, pady=10)

    def load_exercise_registry(self):
        """Attempts to load EXERCISE_REGISTRY from sessions.py using config."""
        if not os.path.exists(CONFIG_FILE):
            messagebox.showwarning(
                "Config Missing", "Please run main.py first to configure session paths."
            )
            return []

        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)

        sessions_dir = config.get("sessions_dir")
        if not sessions_dir or not os.path.exists(sessions_dir):
            return []

        # Add to path to import
        if sessions_dir not in sys.path:
            sys.path.insert(0, sessions_dir)

        # Add project root to path so sessions.py can 'from core.models import ...'
        root_dir = os.path.join(os.path.dirname(__file__), "..")
        if root_dir not in sys.path:
            sys.path.append(root_dir)

        try:
            # Proactively reload if already imported (e.g. during multiple GUI runs)
            import importlib

            import sessions

            importlib.reload(sessions)
            return sessions.EXERCISE_REGISTRY
        except Exception as e:
            print(f"Error loading registry: {e}")
            return []

    def clear_input(self):
        self.txt_input.delete("1.0", "end")

    def process(self):
        raw_text = self.txt_input.get("1.0", "end").strip()
        if not raw_text:
            messagebox.showerror("Error", "Please paste some data first.")
            return

        selected_str = self.ex_var.get()
        if not selected_str or selected_str == "No Registry Found":
            messagebox.showerror("Error", "No exercise ID selected.")
            return

        # Extract ID from "id (display name)"
        exercise_id = selected_str.split(" (")[0]

        parsed = parse_raw_text(raw_text)
        if not parsed:
            messagebox.showerror(
                "Parsing Error",
                "Could not find valid numerical data. Ensure spaces exist between numbers.",
            )
            return

        try:
            write_to_standards(exercise_id, parsed)
            messagebox.showinfo(
                "Success",
                f"Standards for '{exercise_id}' appended to core/standards.py",
            )
            self.clear_input()
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save: {e}")


if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    app = StandardsParserApp()
    app.mainloop()
