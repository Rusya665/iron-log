"""Dual-Engine GUI Launcher for Iron Log.

Allows launching and comparing:
  1. PyWebView       (Premier Modern HTML5/CSS/JS Engine)
  2. CustomTkinter   (Original Legacy Tkinter Engine)
  3. Launch Both Side-by-Side
"""

import os
import subprocess
import sys
import time

PYTHON_EXE = sys.executable
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def launch_engine(engine_name: str):
    cmd = [PYTHON_EXE, os.path.join(BASE_DIR, "main.py"), "--gui", engine_name]
    t0 = time.perf_counter()
    p = subprocess.Popen(cmd, cwd=BASE_DIR)
    t1 = time.perf_counter()
    print(f"[{engine_name.upper()}] Process spawned in {(t1 - t0)*1000:.1f}ms (PID: {p.pid})")
    return p


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ["--all", "all"]:
        print("\n🚀 Launching PyWebView and CustomTkinter side-by-side...\n")
        launch_engine("webview")
        time.sleep(0.3)
        launch_engine("ctk")
        print("\nBoth GUI windows launched!")
        return

    print("=" * 60)
    print("       ⚡ IRON LOG — GUI ENGINE LAUNCHER")
    print("=" * 60)
    print("  [1] PyWebView       (Premier Modern Microsoft Edge Engine)")
    print("  [2] CustomTkinter   (Legacy Fallback)")
    print("  [3] 🚀 Launch BOTH side-by-side")
    print("  [0] Exit")
    print("=" * 60)

    choice = input("\nEnter your choice (0-3) [Default: 1]: ").strip()
    if not choice:
        choice = "1"

    if choice == "0":
        print("Exiting.")
        return
    elif choice == "1":
        p = launch_engine("webview")
        p.wait()
    elif choice == "2":
        p = launch_engine("ctk")
        p.wait()
    elif choice == "3":
        launch_engine("webview")
        time.sleep(0.3)
        launch_engine("ctk")
        print("\nBoth windows launched!")
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
