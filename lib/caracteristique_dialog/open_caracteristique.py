import logging

from pywinauto import WindowSpecification


LOGGER = logging.getLogger(__name__)

DIALOG_TITLE_RE = r".*Caractéristiques du tronçon.*"
COLLECTEUR_TAB_TITLE = r".*Caractéristiques du collecteur.*"
REGARDS_TAB_TITLE = r".*Regards de visite & fiches simplifiées.*"


def open_collecteur_tab(dialog: WindowSpecification) -> WindowSpecification:
    """Select the collector tab and return its content pane."""
    LOGGER.info("Opening tab %r", COLLECTEUR_TAB_TITLE)
    tab = dialog.child_window(
        title=COLLECTEUR_TAB_TITLE,
        control_type="TabItem",
    )
    tab.wait("ready", timeout=10)

    try:
        tab.select()
    except (AttributeError, NotImplementedError):
        tab.click_input()

    pane = dialog.child_window(
        title=COLLECTEUR_TAB_TITLE,
        control_type="Pane",
    )
    pane.wait("visible", timeout=10)
    LOGGER.info("Collector tab is open")
    return pane


def open_regards_tab(dialog: WindowSpecification):
    """Select the Regards tab and return its content pane."""
    LOGGER.info("Opening tab %r", REGARDS_TAB_TITLE)
    tab = dialog.child_window(
        title=REGARDS_TAB_TITLE,
        control_type="TabItem",
    )
    LOGGER.debug("Tab text: %s", tab.window_text())
    # tab.wait("ready", timeout=10)

    try:
        tab.select()
    except (AttributeError, NotImplementedError):
        tab.click_input()

    # pane = dialog.child_window(
    #     title=REGARDS_TAB_TITLE,
    #     control_type="Pane",
    # )
    # pane.wait("visible", timeout=10)
    LOGGER.info("Regards tab is open")