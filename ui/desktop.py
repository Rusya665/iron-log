"""
Iron Log - Desktop GUI module facade.

Provides backward-compatible exports for:
  - WebViewBridgeApi
  - run_desktop_app / run_webview_app
  - HTML_TEMPLATE / PLANNER_HTML_TEMPLATE
  - Updater functions for testing and external hooks
"""

import os
import sys

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from core.updater import (  # noqa: E402
    check_for_updates,
    download_and_install_update,
    get_update_details,
)
from core.version import __version__  # noqa: E402
from ui import window_manager  # noqa: E402
from ui.app import run_desktop_app, run_webview_app  # noqa: E402
from ui.bridge import WebViewBridgeApi  # noqa: E402
from ui.templates import HTML_TEMPLATE, PLANNER_HTML_TEMPLATE  # noqa: E402


from typing import Any

# Backward-compatible window references
def __getattr__(name: str) -> Any:
    """
    Resolve backward-compatible dynamic window references.

    :param name: Attribute identifier requested.
    :return: Window instance from window manager.
    :raises AttributeError: If attribute name is not recognized.
    """
    if name == "_MAIN_WINDOW":
        return window_manager.get_main_window()
    if name == "_PLANNER_WINDOW":
        return window_manager.get_planner_window()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    "WebViewBridgeApi",
    "run_webview_app",
    "run_desktop_app",
    "HTML_TEMPLATE",
    "PLANNER_HTML_TEMPLATE",
    "get_update_details",
    "download_and_install_update",
    "check_for_updates",
    "__version__",
]

if __name__ == "__main__":
    run_webview_app()
