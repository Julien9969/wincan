import logging

from pywinauto import WindowSpecification


LOGGER = logging.getLogger(__name__)

DIALOG_TITLE_RE = r".*Caractéristiques du tronçon.*"
COLLECTEUR_TAB_TITLE = r".*Caractéristiques du collecteur.*"
REGARDS_TAB_TITLE = r".*Regards de visite & fiches simplifiées.*"


def open_collecteur_tab(dialog: WindowSpecification):
    """Select the collector tab and return its content pane."""
    LOGGER.info("Opening tab %r", COLLECTEUR_TAB_TITLE)
    tab = dialog.child_window(
        title_re=COLLECTEUR_TAB_TITLE,
        control_type="TabItem",
    )
    LOGGER.debug("Tab text: %s", tab.window_text())
    try:
        tab.click_input()
    except (AttributeError, NotImplementedError):
        LOGGER.info("Tab selection is unavailable")
        raise RuntimeError("Cannot select the collector tab")
    LOGGER.info("Collector tab is open")
    return dialog


def open_regards_tab(dialog: WindowSpecification):
    """Select the Regards tab and return its content pane."""
    LOGGER.info("Opening tab %r", REGARDS_TAB_TITLE)
    tab = dialog.child_window(
        title_re=REGARDS_TAB_TITLE,
        control_type="TabItem",
    )
    LOGGER.debug("Tab text: %s", tab.window_text())

    try:
        tab.click_input()
    except (AttributeError, NotImplementedError):
        LOGGER.info("Tab selection is unavailable")
        raise RuntimeError("Cannot select the Regards tab")
    LOGGER.info("Regards tab is open")
    return dialog
    