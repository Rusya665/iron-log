import json
import os
import re
import sys
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

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

        numbers = re.findall(r"\d+", line)

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
    root_dir = os.path.join(os.path.dirname(__file__), "..")
    if root_dir not in sys.path:
        sys.path.append(root_dir)

    import importlib
    from core import standards

    importlib.reload(standards)
    current_standards = getattr(standards, "EXERCISE_STANDARDS", {})

    current_standards[exercise_id] = data

    header = '''import re

def get_exercise_standard(exercise_id: str, target_date_str: str, bodymass_log: dict, level: str = "Intermediate") -> int:
    """
    Retrieves the exercise standard from the consolidated EXERCISE_STANDARDS dictionary.
    Requires an exact match on the exercise_id.
    """
    if not bodymass_log or not exercise_id:
        return 0
        
    dates = sorted(bodymass_log.keys())
    if not dates:
        return 0
        
    applicable_date = dates[0]
    for d in dates:
        if d <= target_date_str:
            applicable_date = d
        else:
            break
            
    bm_data = bodymass_log[applicable_date]
    current_bm = bm_data if isinstance(bm_data, (int, float)) else bm_data.get("mass", 0)
    
    if not current_bm:
        return 0
        
    rounded_bm = int(round(current_bm / 5.0) * 5.0)
    rounded_bm = max(50, min(rounded_bm, 140))
    
    if exercise_id not in EXERCISE_STANDARDS:
        return 0
        
    table = EXERCISE_STANDARDS[exercise_id]
    available_bms = sorted(table.keys())
    if not available_bms:
        return 0
        
    clipped_bm = max(available_bms[0], min(rounded_bm, available_bms[-1]))
    return table[clipped_bm].get(level, 0)

# Consolidate exercise standards database
EXERCISE_STANDARDS = {
'''

    content = header
    for ex_id, std_data in sorted(current_standards.items()):
        content += f'    "{ex_id}": {{\n'
        for bm, levels in sorted(std_data.items()):
            content += f"        {bm}: {levels},\n"
        content += "    },\n"
    content += "}\n"

    with open(STANDARDS_FILE, "w", encoding="utf-8") as f:
        f.write(content)


class StandardsParserApp(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("Iron Log - Standards Parser Tool")
        self.geometry("750x650")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Exercise Registry Selector
        self.top_frame = ttk.Frame(self)
        self.top_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        ttk.Label(self.top_frame, text="Select Target Exercise:").pack(
            side="left", padx=(0, 10)
        )

        self.registry = self.load_exercise_registry()
        exercise_names = (
            [f"{ex.id} ({ex.name})" for ex in self.registry]
            if self.registry
            else ["No Registry Found"]
        )

        self.ex_var = tk.StringVar(value=exercise_names[0] if exercise_names else "")
        self.opt_ex = ttk.Combobox(
            self.top_frame, values=exercise_names, textvariable=self.ex_var, width=40, state="readonly"
        )
        self.opt_ex.pack(side="left", padx=10, pady=10)

        # 2. Raw Text Input
        self.lbl_hint = ttk.Label(
            self, text="Paste raw table data below (BM, Beg, Nov, Int, Adv, Elite):"
        )
        self.lbl_hint.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")

        self.txt_input = tk.Text(self, height=18, font=("Consolas", 10), bg="#1e1e1e", fg="#ffffff", insertbackground="white")
        self.txt_input.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")

        # 3. Actions
        self.btn_frame = ttk.Frame(self)
        self.btn_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.btn_clear = ttk.Button(
            self.btn_frame, text="Clear", command=self.clear_input
        )
        self.btn_clear.pack(side="left", padx=10, pady=10)

        self.btn_save = ttk.Button(
            self.btn_frame,
            text="PARSE & SAVE TO STANDARDS.PY",
            command=self.process,
        )
        self.btn_save.pack(side="right", padx=10, pady=10)

    def load_exercise_registry(self):
        """Attempts to load EXERCISE_REGISTRY from sessions.py using config."""
        if not os.path.exists(CONFIG_FILE):
            return []

        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)

        sessions_dir = config.get("sessions_dir")
        if not sessions_dir or not os.path.exists(sessions_dir):
            return []

        if sessions_dir not in sys.path:
            sys.path.insert(0, sessions_dir)

        root_dir = os.path.join(os.path.dirname(__file__), "..")
        if root_dir not in sys.path:
            sys.path.append(root_dir)

        try:
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
    app = StandardsParserApp()
    app.mainloop()
