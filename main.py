import argparse
import os
import sys
import subprocess
from datetime import datetime

# Ensure local imports work correctly
sys.path.append(os.path.dirname(__file__))

from core.config import get_config
from core.xlsx_generator import TrainingLogProcessor

def open_file(path_to_file):
    if sys.platform == "win32":
        os.startfile(path_to_file)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, path_to_file])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Iron Log Generator")
    parser.add_argument("--reconfigure", action="store_true", help="Prompt to reconfigure directory paths")
    args = parser.parse_args()

    config = get_config(reconfigure=args.reconfigure)
    
    sessions_dir = config.get("sessions_dir")
    output_dir = config.get("output_dir")

    # Dynamically load sessions.py from the configured directory
    if sessions_dir not in sys.path:
        sys.path.insert(0, sessions_dir)

    try:
        import sessions
    except ImportError as e:
        print(f"CRITICAL ERROR: Could not import 'sessions.py' from {sessions_dir}")
        print(f"Details: {e}")
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    filename = os.path.join(output_dir, f"Training_Log_{timestamp}.xlsx")

    # The constructor call for TrainingLogProcessor is updated to pass the config object
    # as the instruction implies changes related to stand-alone logic removal from xlsx_generator.py
    app = TrainingLogProcessor(filename, sessions.EXERCISE_REGISTRY, sessions.USER_DATA, sessions.BODYWEIGHT_LOG)
    app.write_headers()
    app.process_data(sessions.USER_DATA)
    app.write_calculations()
    app.generate_charts()
    app.write_definitions()
    app.save()
    
    open_file(filename)