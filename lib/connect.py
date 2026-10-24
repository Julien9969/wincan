
import logging

from pywinauto import Application, WindowSpecification
import pywinauto
from pywinauto.timings import TimeoutError as PyWinAutoTimeoutError
from pywinauto.timings import Timings

APP_PATH = r"C:\Program Files (x86)\Canalyse 2\Canalyse2.exe"
MAIN_WINDOW_NAME = r".*Canalyse.*"
CARACTERISTIQUE_WINDOW_NAME = r".*Caractéristiques.*"
LOGGER = logging.getLogger(__name__)


def connect_to_canalyse():
    Timings.window_find_timeout = 10
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

if __name__ == "__main__":
    connect_to_canalyse()
