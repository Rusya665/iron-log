import json
import os
import tkinter as tk
from tkinter import filedialog

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "config.json")


def get_drive_paths():
    return [
        r"G:\My Drive\2025 Health",
        r"H:\My Drive\2025 Health",
        os.path.expanduser(r"~\Google Drive\2025 Health"),
        os.path.expanduser(r"~\My Drive\2025 Health"),
    ]


def detect_default_drive():
    for path in get_drive_paths():
        if os.path.exists(path):
            return path
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))


def prompt_user_for_paths() -> dict:
    default_base = detect_default_drive()

    # Hidden root for tkinter dialogs
    root = tk.Tk()
    root.withdraw()

    # 1. Output Dir
    default_output = os.path.join(default_base, "gym")
    print(f"Selecting Excel output folder... [Default: {default_output}]")
    output_dir = filedialog.askdirectory(
        title="Select folder for Excel files", initialdir=default_base
    )
    if not output_dir:
        output_dir = default_output
        print(f"Using default: {output_dir}")
    else:
        print(f"Selected: {output_dir}")

    # 2. Sessions Dir
    default_sessions = default_base
    print(f"Selecting 'sessions.py' folder... [Default: {default_sessions}]")
    sessions_dir = filedialog.askdirectory(
        title="Select folder containing sessions.py", initialdir=default_base
    )
    if not sessions_dir:
        sessions_dir = default_sessions
        print(f"Using default: {sessions_dir}")
    else:
        print(f"Selected: {sessions_dir}")

    root.destroy()

    os.makedirs(sessions_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    return {"sessions_dir": sessions_dir, "output_dir": output_dir}


def get_config(reconfigure: bool = False) -> dict:
    if not reconfigure and os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            try:
                config = json.load(f)
                if "sessions_dir" in config and "output_dir" in config:
                    return config
            except json.JSONDecodeError:
                pass

    config = prompt_user_for_paths()

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

    return config
