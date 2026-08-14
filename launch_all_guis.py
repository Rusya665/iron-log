"""Dual-Engine GUI Launcher for Iron Log.

Immediately launches both PyWebView and CustomTkinter side-by-side.
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
    print("\n>>> Launching PyWebView and CustomTkinter side-by-side...\n")
    p1 = launch_engine("webview")
    time.sleep(0.3)
    p2 = launch_engine("ctk")
    print("\nBoth GUI windows successfully launched!\n")


if __name__ == "__main__":
    main()
