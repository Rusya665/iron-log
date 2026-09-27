"""Window state manager for PyWebView windows in Iron Log."""

from typing import Optional
import webview

_MAIN_WINDOW: Optional[webview.Window] = None
_PLANNER_WINDOW: Optional[webview.Window] = None


def get_main_window() -> Optional[webview.Window]:
    """Returns the main application window instance."""
    return _MAIN_WINDOW


def set_main_window(window: Optional[webview.Window]) -> None:
    """Sets the main application window instance."""
    global _MAIN_WINDOW
    _MAIN_WINDOW = window


def get_planner_window() -> Optional[webview.Window]:
    """Returns the standalone planner window instance."""
    return _PLANNER_WINDOW


def set_planner_window(window: Optional[webview.Window]) -> None:
    """Sets the standalone planner window instance."""
    global _PLANNER_WINDOW
    _PLANNER_WINDOW = window


def close_planner_window() -> None:
    """Safely closes the standalone planner window if open."""
    global _PLANNER_WINDOW
    if _PLANNER_WINDOW:
        try:
            _PLANNER_WINDOW.destroy()
        except Exception:
            pass
        _PLANNER_WINDOW = None


def reload_main_dashboard() -> None:
    """Triggers a dashboard reload in the main window."""
    global _MAIN_WINDOW
    if _MAIN_WINDOW:
        try:
            _MAIN_WINDOW.evaluate_js("loadDashboard();")
        except Exception:
            pass


def destroy_all_windows() -> None:
    """Safely closes and destroys all active windows."""
    global _MAIN_WINDOW, _PLANNER_WINDOW
    if _PLANNER_WINDOW:
        try:
            _PLANNER_WINDOW.destroy()
        except Exception:
            pass
        _PLANNER_WINDOW = None
    if _MAIN_WINDOW:
        try:
            _MAIN_WINDOW.destroy()
        except Exception:
            pass
        _MAIN_WINDOW = None
