import json
import os
import re
import sys
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional

# Core file paths
CORE_DIR = os.path.join(os.path.dirname(__file__), "..", "core")
STANDARDS_FILE = os.path.join(CORE_DIR, "standards.py")
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "config.json")


def parse_raw_text(raw_text: str) -> Dict[int, Dict[str, int]]:
    """
    Parse raw strength level table text into structured body mass tiers.

    :param raw_text: Raw multi-line string containing body mass and tier weights.
    :return: Dictionary mapping body mass (kg) to tier level target weights.
    """
    parsed_data: Dict[int, Dict[str, int]] = {}
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


def write_to_standards(exercise_id: str, data: Dict[int, Dict[str, int]]) -> None:
    """
    Update the EXERCISE_STANDARDS dictionary in the standards module file.

    :param exercise_id: Canonical exercise slug or identifier.
    :param data: Dictionary mapping body mass (kg) to tier level target weights.
    :return: None
    """
    root_dir = os.path.join(os.path.dirname(__file__), "..")
    if root_dir not in sys.path:
        sys.path.append(root_dir)

    import importlib
    from core import standards

    importlib.reload(standards)
    current_standards = getattr(standards, "EXERCISE_STANDARDS", {})

    display_name = exercise_id.replace("-", " ").title()
    if exercise_id in current_standards and isinstance(current_standards[exercise_id], dict) and "male" in current_standards[exercise_id]:
        current_standards[exercise_id]["male"].update(data)
    else:
        current_standards[exercise_id] = {
            "name": display_name,
            "male": data,
            "female": {},
        }

    header = '''import math
import re
from typing import Any, Dict, Optional


def get_exercise_standard(
    exercise_id: str,
    target_date_str: str,
    bodymass_log: Dict[str, Any],
    level: str = "Intermediate",
    sex: Optional[str] = None,
) -> int:
    """
    Retrieve standard lifted mass target for exercise and date from standards database.

    :param exercise_id: Canonical exercise slug or display name.
    :param target_date_str: Date string formatted as YYYY-MM-DD to resolve closest body mass.
    :param bodymass_log: Dictionary mapping date strings to body mass records.
    :param level: Strength tier ("Beginner", "Novice", "Intermediate", "Advanced", "Elite").
    :param sex: Biological sex ("male" or "female").
    :return: Target lifted weight in kilograms, or 0 if unmapped.
    """
    if sex is None:
        try:
            import sessions

            sex = sessions.USER_SEX
        except (ImportError, AttributeError):
            sex = "male"

    if not bodymass_log or not exercise_id:
        return 0

    dates = sorted(bodymass_log.keys())
    if not dates:
        return 0

    applicable_date = None
    for d in reversed(dates):
        if d <= target_date_str:
            bm_data = bodymass_log[d]
            bm = bm_data if isinstance(bm_data, (int, float)) else (bm_data.get("mass") or bm_data.get("weight"))
            if bm is not None and bm > 0:
                applicable_date = d
                break

    if not applicable_date:
        for d in dates:
            bm_data = bodymass_log[d]
            bm = bm_data if isinstance(bm_data, (int, float)) else (bm_data.get("mass") or bm_data.get("weight"))
            if bm is not None and bm > 0:
                applicable_date = d
                break

    if not applicable_date:
        return 0

    bm_data = bodymass_log[applicable_date]
    current_bm = (
        bm_data if isinstance(bm_data, (int, float)) else bm_data.get("mass")
    )
    if current_bm is None:
        current_bm = bm_data.get("weight", 0) if isinstance(bm_data, dict) else 0

    if not current_bm:
        return 0

    rounded_bm = int(math.ceil(round(current_bm, 2) / 5.0) * 5)
    rounded_bm = max(50, min(rounded_bm, 140))

    target_norm = exercise_id.lower().strip().replace(" ", "-")
    found_slug = None

    if target_norm in EXERCISE_STANDARDS:
        found_slug = target_norm
    else:
        for slug, info in EXERCISE_STANDARDS.items():
            if info.get("name", "").lower().strip().replace(" ", "-") == target_norm:
                found_slug = slug
                break

    if not found_slug:
        return 0

    gender_table = EXERCISE_STANDARDS[found_slug].get(sex.lower())
    if not gender_table:
        return 0

    available_bms = sorted(gender_table.keys())
    if not available_bms:
        return 0

    clipped_bm = max(available_bms[0], min(rounded_bm, available_bms[-1]))
    return gender_table[clipped_bm].get(level, 0)


def get_tiered_standards(
    exercise_id: str,
    sex: str,
    body_mass: Optional[float] = None,
) -> Optional[Dict[int, Dict[str, int]]]:
    """
    Return dictionary of strength standards across bodyweight tiers for an exercise and sex.

    :param exercise_id: Canonical exercise slug or display name.
    :param sex: Biological sex ("male" or "female").
    :param body_mass: Optional body mass in kg to return 3 adjacent tiers around user weight class.
    :return: Dictionary mapping bodyweight tiers (kg) to tier level target weights, or None.
    """
    if not exercise_id:
        return None

    target_norm = exercise_id.lower().strip().replace(" ", "-")
    found_slug = None

    if target_norm in EXERCISE_STANDARDS:
        found_slug = target_norm
    else:
        for slug, info in EXERCISE_STANDARDS.items():
            if info.get("name", "").lower().strip().replace(" ", "-") == target_norm:
                found_slug = slug
                break

    if not found_slug:
        return None

    gender_table = EXERCISE_STANDARDS[found_slug].get(sex.lower())
    if not gender_table:
        return None

    available_bms = sorted(gender_table.keys())
    if not available_bms:
        return None

    if body_mass is None or body_mass <= 0:
        return gender_table

    rounded_bm = int(math.ceil(round(body_mass, 2) / 5.0) * 5)

    results = {}
    for offset in [-5, 0, 5]:
        target_bm = rounded_bm + offset
        clipped_bm = max(available_bms[0], min(target_bm, available_bms[-1]))
        results[target_bm] = gender_table[clipped_bm]

    return results


EXERCISE_STANDARDS = {
'''

    content = header
    for ex_id, std_data in sorted(current_standards.items()):
        content += f'    "{ex_id}": {{\n'
        if isinstance(std_data, dict) and ("male" in std_data or "female" in std_data or "name" in std_data):
            name_val = std_data.get("name", ex_id.replace("-", " ").title())
            content += f'        "name": "{name_val}",\n'
            for sex_key in ["male", "female"]:
                tbl = std_data.get(sex_key, {})
                content += f'        "{sex_key}": {{\n'
                if tbl:
                    for bm, levels in sorted(tbl.items()):
                        content += f"            {bm}: {levels},\n"
                content += "        },\n"
        else:
            for bm, levels in sorted(std_data.items()):
                content += f"        {bm}: {levels},\n"
        content += "    },\n"
    content += "}\n"

    with open(STANDARDS_FILE, "w", encoding="utf-8") as f:
        f.write(content)


class StandardsParserApp(tk.Tk):
    """Tkinter graphical tool for parsing and updating exercise strength standards."""

    def __init__(self) -> None:
        """
        Initialize the standards parser GUI window and input controls.

        :return: None
        """
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

    def load_exercise_registry(self) -> List[Any]:
        """
        Load registered exercise models from the active sessions module.

        :return: List of exercise objects or empty list on failure.
        """
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
            return getattr(sessions, "EXERCISE_REGISTRY", [])
        except Exception as e:
            print(f"Error loading registry: {e}")
            return []

    def clear_input(self) -> None:
        """
        Clear text from the raw table input widget.

        :return: None
        """
        self.txt_input.delete("1.0", "end")

    def process(self) -> None:
        """
        Parse raw table text from input widget and persist entries into standards.py.

        :return: None
        """
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
