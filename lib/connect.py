
import logging

from pywinauto import Application, Desktop, WindowSpecification
from pywinauto.timings import Timings

APP_PATH = r"C:\Program Files (x86)\Canalyse 2\Canalyse2.exe"
MAIN_WINDOW_NAME = r".*Canalyse.*"
CARACTERISTIQUE_WINDOW_NAME = r".*Caractéristiques du tronçon.*"
LOGGER = logging.getLogger(__name__)


def connect_to_canalyse():
    Timings.window_find_timeout = 5
    LOGGER.info("Connecting to Canalyse 2: %s", APP_PATH)
    app = Application(backend="uia").connect(path=APP_PATH, timeout=10)
    LOGGER.info("Connected to process(es): %s", app.process)
    return app


def get_window(app, window_title_re) -> WindowSpecification:
    window = app.window(title_re=window_title_re)

    LOGGER.info(
        "Window: title=%r, handle=%s, visible=%s",
        window.window_text(),
        window.handle,
        window.is_visible(),
    )
    return window

def get_main_window(app) -> WindowSpecification:
    return get_window(app, MAIN_WINDOW_NAME)

def get_caracteristique_window(app) -> WindowSpecification:
    return get_window(app, CARACTERISTIQUE_WINDOW_NAME)


def list_windows(app=None):
    """Log visible top-level windows available to the automation session."""
    windows = app.windows() if app is not None else Desktop(backend="uia").windows()
    LOGGER.info("Found %d top-level window(s):", len(windows))
    for index, window in enumerate(windows):
        LOGGER.info(
            "  [%d] title=%r handle=%s class=%r process=%s visible=%s",
            index,
            window.window_text(),
            window.handle,
            window.element_info.class_name,
            window.process_id(),
            window.is_visible(),
        )
    return windows


def list_child_windows(window: WindowSpecification):
    """Log Window controls exposed inside a parent window."""
    child_windows = window.descendants(control_type="Window")
    LOGGER.info(
        "Found %d nested window control(s) inside %r:",
        len(child_windows),
        window.window_text(),
    )
    for index, child in enumerate(child_windows):
        LOGGER.info(
            "  [%d] title=%r handle=%s class=%r process=%s visible=%s",
            index,
            child.window_text(),
            child.handle,
            child.element_info.class_name,
            child.process_id(),
            child.is_visible(),
        )
    return child_windows


if __name__ == "__main__":
    list_windows(connect_to_canalyse())
