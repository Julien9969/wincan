
import logging

from lib.caracteristique_dialog.caracteristique_collecteur import (
    get_identification_controls,
)
from lib.caracteristique_dialog.open_caracteristique import open_regards_tab
from lib.connect import connect_to_canalyse, get_caracteristique_window, get_main_window

logging.basicConfig(
    level=logging.INFO,
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
    # list_child_windows(window)
    carac = get_caracteristique_window(window)
    carac.set_focus()

    identification = get_identification_controls(carac)

    identification.operator_name.set_edit_text("Test Operator")
    
    open_regards_tab(carac)
    
    carac.print_control_identifiers()