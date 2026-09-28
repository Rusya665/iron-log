import json
import os
import sys
import tkinter as tk
from tkinter import filedialog
from typing import Dict, List

from core.profile_manager import get_app_data_dir

_app_data_dir = get_app_data_dir()
CONFIG_FILE = os.path.join(_app_data_dir, "config.json")


def get_drive_paths() -> List[str]:
    """
    Return candidate storage directories for IronLog user data.

    :return: List of candidate directory path strings.
    """
    return [
        os.path.expanduser(r"~\Documents\IronLog"),
        os.path.expanduser(r"~\Desktop\IronLog"),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data")),
    ]


def detect_default_drive() -> str:
    """
    Find the first existing candidate data directory, falling back to local data directory.

    :return: Absolute path string to the default data directory.
    """
    for path in get_drive_paths():
        if os.path.exists(path):
            return path
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))


def prompt_user_for_paths(cli_mode: bool = False) -> Dict[str, str]:
    """
    Prompt the user to select paths for sessions and Excel output via CLI or GUI dialog.

    :param cli_mode: Whether to prompt via terminal input or Tkinter file dialogs.
    :return: Dictionary containing 'sessions_dir' and 'output_dir' paths.
    """
    default_base = detect_default_drive()

    if cli_mode:
        default_output = os.path.join(default_base, "gym")
        print(f"Selecting Excel output folder... [Default: {default_output}]")
        output_dir = input("Enter path (or press Enter for default): ").strip()
        if not output_dir:
            output_dir = default_output
            print(f"Using default: {output_dir}")
        else:
            print(f"Selected: {output_dir}")

        default_sessions = default_base
        print(f"Selecting 'sessions.py' folder... [Default: {default_sessions}]")
        sessions_dir = input("Enter path (or press Enter for default): ").strip()
        if not sessions_dir:
            sessions_dir = default_sessions
            print(f"Using default: {sessions_dir}")
        else:
            print(f"Selected: {sessions_dir}")
    else:
        root = tk.Tk()
        root.withdraw()

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


def get_config(reconfigure: bool = False, cli_mode: bool = False) -> Dict[str, str]:
    """
    Load existing configuration from disk or prompt user for paths.

    :param reconfigure: Force re-prompting for directory paths even if config file exists.
    :param cli_mode: Whether to prompt via CLI instead of Tkinter GUI.
    :return: Dictionary containing 'sessions_dir' and 'output_dir' paths.
    """
    if not reconfigure and os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            try:
                config = json.load(f)
                if "sessions_dir" in config and "output_dir" in config:
                    return config
            except json.JSONDecodeError:
                pass

    config = prompt_user_for_paths(cli_mode=cli_mode)

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

    return config
