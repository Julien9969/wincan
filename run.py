
import logging

from lib.caracteristique_dialog.caracteristique_collecteur import get_collector_controls
from lib.caracteristique_dialog.open_caracteristique import open_regards_tab
from lib.connect import connect_to_canalyse, get_caracteristique_window, get_main_window, list_child_windows, list_windows
from lib.troncons import get_list_troncons, select_troncon
from lib.buttons import click_modification_parametres

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
)

LOGGER = logging.getLogger(__name__)

if __name__ == "__main__":
    app = connect_to_canalyse()
    window = get_main_window(app)

    LOGGER.debug("Main window: %r", window)

    # troncons = get_list_troncons(window)
    # select_troncon(window, troncons, 10)
    # LOGGER.debug("Selected troncon: %r", troncons[10])

    # click_modification_parametres(window)
    list_child_windows(window)
    carac = get_caracteristique_window(window)
    carac.set_focus()

    collector_controls = get_collector_controls(carac)

    collector_controls.operator_name.set_text("Test Operator")
    
    open_regards_tab(carac)
    
    # carac.print_control_identifiers()