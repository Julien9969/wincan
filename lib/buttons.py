import logging

import pywinauto
from pywinauto import Application, WindowSpecification
from pywinauto.timings import TimeoutError as PyWinAutoTimeoutError
from pywinauto.timings import Timings


BUTTON_TEXT = "Modification des paramètres"
LOGGER = logging.getLogger(__name__)

def list_buttons(window: WindowSpecification):
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

def click_button(window: WindowSpecification, button_text: str):
    LOGGER.info(
        "Looking for button: title=%r, control_type=%r",
        button_text,
        "Button",
    )
    button = window.child_window(title=button_text, control_type="Button")

    try:
        button.wait("ready", timeout=10)
    except PyWinAutoTimeoutError:
        LOGGER.exception(
            "Target button was not ready. Dumping the UI control tree for inspection."
        )
        window.print_control_identifiers()
        raise

    LOGGER.info("Invoking button %r", button_text)
    button.invoke()
    LOGGER.info("Button invoked successfully")


def click_modification_parametres(window: WindowSpecification):
    click_button(window, BUTTON_TEXT)