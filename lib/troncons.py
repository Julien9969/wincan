import logging
from typing import List

from pywinauto import WindowSpecification
from pywinauto.timings import TimeoutError as PyWinAutoTimeoutError

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

    LOGGER.debug("Clicking troncon: %d", n)
    troncon = next((t for t in troncons if t.window_text().startswith(f"{TRONÇON_TEXT_PREFIX}{n}")), None)
    if not troncon:
        raise ValueError("Troncon not found")

    LOGGER.info(
        "Looking for troncon: title=%r, control_type=%r",
        troncon.window_text(),
        "TreeItem",
    )


    LOGGER.info("Selecting troncon item %r", troncon.window_text())
    try:
        troncon.select()
    except (AttributeError, NotImplementedError):
        LOGGER.debug("TreeItem selection is unavailable; using click_input().")
        troncon.click_input()
    LOGGER.info("Troncon selected successfully")

