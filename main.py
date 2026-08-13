import argparse
import sys
import os

# Ensure local imports work correctly
sys.path.append(os.path.dirname(__file__))

def run_gui(engine: str = "ctk"):
    if engine == "pyside":
        from ui.desktop_pyside import run_pyside_app
        run_pyside_app()
    elif engine == "dpg":
        from ui.desktop_dpg import run_dpg_app
        run_dpg_app()
    elif engine == "webview":
        from ui.desktop_webview import run_webview_app
        run_webview_app()
    elif engine == "all":
        import subprocess
        python_exe = sys.executable
        cwd = os.path.dirname(__file__)
        print("Launching all 4 GUI engines simultaneously...")
        subprocess.Popen([python_exe, "main.py", "--gui", "ctk"], cwd=cwd)
        subprocess.Popen([python_exe, "main.py", "--gui", "pyside"], cwd=cwd)
        subprocess.Popen([python_exe, "main.py", "--gui", "dpg"], cwd=cwd)
        subprocess.Popen([python_exe, "main.py", "--gui", "webview"], cwd=cwd)
    else:
        from ui.desktop import IronLogApp
        app = IronLogApp()
        app.mainloop()


def run_cli(args):
    from core.config import get_config
    from core.xlsx_generator import TrainingLogProcessor
    from datetime import datetime

    config = get_config(reconfigure=args.reconfigure, cli_mode=True)
    sessions_dir = config.get("sessions_dir")
    output_dir = config.get("output_dir")

    if sessions_dir not in sys.path:
        sys.path.insert(0, sessions_dir)

    try:
        import sessions
    except ImportError:
        print(f"CRITICAL ERROR: Could not import 'sessions.py' from {sessions_dir}")
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    filename = os.path.join(output_dir, f"Training_Log_{timestamp}.xlsx")

    # Pass an empty profile dict as CLI doesn't have profile awareness yet
    app = TrainingLogProcessor(filename, sessions.EXERCISE_REGISTRY, sessions.USER_DATA, sessions.BODYMASS_LOG)
    try:
        app.validate_data()
    except ValueError as ve:
        print(f"Data Error: {ve}")
        sys.exit(1)
    app.write_headers()
    app.process_data(sessions.USER_DATA)
    app.write_calculations()
    app.generate_charts()
    app.write_definitions()
    app.write_personal_records()
    app.write_user_profile()
    app.save()
    
    if sys.platform == "win32":
        os.startfile(filename)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Iron Log Launcher")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode")
    parser.add_argument("--reconfigure", action="store_true", help="[CLI Only] Prompt to reconfigure paths")
    parser.add_argument(
        "--gui",
        choices=["ctk", "pyside", "dpg", "webview", "all"],
        default="ctk",
        help="Select GUI engine: ctk (CustomTkinter), pyside (PySide6 / Qt 6), dpg (Dear PyGui GPU), webview (PyWebView Edge), or all",
    )
    args = parser.parse_args()

    if args.cli:
        run_cli(args)
    else:
        run_gui(args.gui)