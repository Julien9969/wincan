"""Click the Canalyse 2 button named "Modification des paramètres"."""

import logging

from pywinauto import Application
from pywinauto.timings import TimeoutError as PyWinAutoTimeoutError
from pywinauto.timings import Timings


APP_PATH = r"C:\Program Files (x86)\Canalyse 2\Canalyse2.exe"
WINDOW_TITLE_RE = r".*Canalyse*"
BUTTON_TEXT = "Modification des paramètres"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
LOGGER = logging.getLogger(__name__)


def main():
    Timings.window_find_timeout = 10
    LOGGER.info("Connecting to Canalyse 2: %s", APP_PATH)
    app = Application(backend="uia").connect(path=APP_PATH, timeout=10)
    LOGGER.info("Connected to process(es): %s", app.process)

    window = app.window(title_re=WINDOW_TITLE_RE)
    LOGGER.info(
        "Main window: title=%r, handle=%s, visible=%s",
        window.window_text(),
        window.handle,
        window.is_visible(),
    )

    button = window.child_window(title=BUTTON_TEXT, control_type="Button")
    LOGGER.info(
        "Looking for button: title=%r, control_type=%r",
        BUTTON_TEXT,
        "Button",
    )

    buttons = window.descendants(control_type="Button")
    LOGGER.info("Found %d button control(s):", len(buttons))
    for index, candidate in enumerate(buttons):
        LOGGER.info(
            "  [%d] text=%r enabled=%s visible=%s automation_id=%r",
            index,
            candidate.window_text(),
            candidate.is_enabled(),
            candidate.is_visible(),
            candidate.element_info.automation_id,
        )

    try:
        button.wait("ready", timeout=10)
    except PyWinAutoTimeoutError:
        LOGGER.exception(
            "Target button was not ready. Dumping the UI control tree for inspection."
        )
        window.print_control_identifiers()
        raise

    LOGGER.info("Invoking button %r", BUTTON_TEXT)
    button.invoke()
    LOGGER.info("Button invoked successfully")


if __name__ == "__main__":
    main()
