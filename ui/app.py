"""Application runner and window lifecycle manager for Iron Log GUI."""

import os
import sys

import webview

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from core.version import __version__  # noqa: E402
from ui import window_manager  # noqa: E402
from ui.bridge import WebViewBridgeApi  # noqa: E402
from ui.templates import HTML_TEMPLATE  # noqa: E402


def run_webview_app() -> None:
    """
    Initialize and run the PyWebView desktop application window.

    :return: None.
    """
    api = WebViewBridgeApi()
    main_window = webview.create_window(
        title=f"Iron Log - Strength Tracker v{__version__} (PyWebView Edition)",
        html=HTML_TEMPLATE,
        js_api=api,
        width=1160,
        height=740,
        min_size=(960, 600),
        background_color="#0A0D14",
    )
    window_manager.set_main_window(main_window)
    webview.start(debug=False)


# Alias for standard entry point
run_desktop_app = run_webview_app

if __name__ == "__main__":
    run_webview_app()
