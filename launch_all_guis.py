"""Interactive Multi-GUI Engine Launcher for Iron Log.

Allows launching and comparing all 4 GUI engines:
  1. CustomTkinter (Original)
  2. PySide6 (Qt 6 C++)
  3. Dear PyGui (DirectX 11 GPU)
  4. PyWebView (Microsoft Edge WebView2)
  5. Launch All 4 Engines Side-by-Side
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
        print("\n🚀 Launching all 4 GUI engines simultaneously for direct side-by-side testing...\n")
        for eng in ["ctk", "pyside", "dpg", "webview"]:
            launch_engine(eng)
            time.sleep(0.3)
        print("\nAll 4 GUI windows launched! Check your taskbar / screen.")
        return

    print("=" * 60)
    print("       ⚡ IRON LOG — MULTI-ENGINE GUI TEST SUITE")
    print("=" * 60)
    print("  [1] CustomTkinter       (Original Tkinter dark mode)")
    print("  [2] PySide6             (Qt 6 C++ native rendering)")
    print("  [3] Dear PyGui          (DirectX 11 GPU accelerated)")
    print("  [4] PyWebView           (Edge WebView2 HTML/CSS/JS)")
    print("  [5] 🚀 Launch ALL 4 simultaneously")
    print("  [0] Exit")
    print("=" * 60)

    choice = input("\nEnter your choice (0-5) [Default: 5]: ").strip()
    if not choice:
        choice = "5"

    mapping = {
        "1": "ctk",
        "2": "pyside",
        "3": "dpg",
        "4": "webview",
    }

    if choice == "0":
        print("Exiting.")
        return
    elif choice == "5":
        for eng in ["ctk", "pyside", "dpg", "webview"]:
            launch_engine(eng)
            time.sleep(0.3)
        print("\nAll 4 GUI windows launched!")
    elif choice in mapping:
        eng = mapping[choice]
        print(f"\nLaunching {eng.upper()}...")
        p = launch_engine(eng)
        p.wait()
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
