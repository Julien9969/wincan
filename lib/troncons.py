import logging
from typing import List

import pywinauto
from pywinauto import Application, WindowSpecification
from pywinauto.timings import TimeoutError as PyWinAutoTimeoutError
from pywinauto.timings import Timings

TRONÇON_TEXT_PREFIX = "Tronçon n° "
LOGGER = logging.getLogger(__name__)

def get_list_troncons(window: WindowSpecification):
    troncons = window.descendants(control_type="TreeItem")
    LOGGER.debug("Found %d troncon control(s):", len(troncons))
    for index, candidate in enumerate(troncons):
        LOGGER.debug(
            "  [%d] text=%r enabled=%s visible=%s automation_id=%r",
            index,
            candidate.window_text(),
            candidate.is_enabled(),
            candidate.is_visible(),
            candidate.element_info.automation_id,
        )

    filtered_troncons = [
        troncon for troncon in troncons if troncon.window_text().startswith(TRONÇON_TEXT_PREFIX)
    ]
    LOGGER.info("Filtered troncon control(s): %d", len(filtered_troncons))
    return filtered_troncons



def click_troncon(window: WindowSpecification, troncons: List[WindowSpecification], n: int):
    if not troncons:
        raise ValueError("No troncons found")

    if n < 0 or n >= len(troncons):
        raise ValueError("Index out of range")


    troncon = next((t for t in troncons if t.window_text().startswith(f"{TRONÇON_TEXT_PREFIX}{n}")), None)
    if not troncon:
        raise ValueError("Troncon not found")

    LOGGER.info(
        "Looking for troncon: title=%r, control_type=%r",
        troncon.window_text(),
        "TreeItem",
    )

    item = window.child_window(title=troncon.window_text(), control_type="TreeItem")

    try:
        item.wait("ready", timeout=10)
    except PyWinAutoTimeoutError:
        LOGGER.exception(
            "Target troncon was not ready. Dumping the UI control tree for inspection."
        )
        window.print_control_identifiers()
        raise

    LOGGER.info("Invoking troncon %r", item.window_text())
    item.invoke()
    LOGGER.info("Troncon invoked successfully")


