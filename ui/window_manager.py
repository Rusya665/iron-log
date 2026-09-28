"""Window state manager for PyWebView windows in Iron Log."""

from typing import Optional
import webview

_MAIN_WINDOW: Optional[webview.Window] = None
_PLANNER_WINDOW: Optional[webview.Window] = None


def get_main_window() -> Optional[webview.Window]:
    """
    Retrieve the active main application window instance.

    :return: Window instance if initialized, None otherwise.
    """
    return _MAIN_WINDOW


def set_main_window(window: Optional[webview.Window]) -> None:
    """
    Assign the active main application window instance.

    :param window: PyWebView Window instance or None when closed.
    :return: None.
    """
    global _MAIN_WINDOW
    _MAIN_WINDOW = window


def get_planner_window() -> Optional[webview.Window]:
    """
    Retrieve the active standalone planner window instance.

    :return: Planner Window instance if open, None otherwise.
    """
    return _PLANNER_WINDOW


def set_planner_window(window: Optional[webview.Window]) -> None:
    """
    Assign the active standalone planner window instance.

    :param window: PyWebView Window instance or None when closed.
    :return: None.
    """
    global _PLANNER_WINDOW
    _PLANNER_WINDOW = window


def close_planner_window() -> None:
    """
    Safely close and destroy the standalone planner window if open.

    :return: None.
    """
    global _PLANNER_WINDOW
    if _PLANNER_WINDOW:
        try:
            _PLANNER_WINDOW.destroy()
        except Exception:
            pass
        _PLANNER_WINDOW = None


def reload_main_dashboard() -> None:
    """
    Execute JavaScript dashboard reload in the active main window.

    :return: None.
    """
    global _MAIN_WINDOW
    if _MAIN_WINDOW:
        try:
            _MAIN_WINDOW.evaluate_js("loadDashboard();")
        except Exception:
            pass


def destroy_all_windows() -> None:
    """
    Safely close and destroy all currently active PyWebView windows.

    :return: None.
    """
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
