
import logging

from lib.caracteristique_dialog.caracteristique_collecteur import (
    get_identification_controls,
)
from lib.caracteristique_dialog.open_caracteristique import open_regards_tab
from lib.caracteristique_dialog.regards_visite import get_arrive, get_depart, get_sens_ecoulement
from lib.connect import connect_to_canalyse, get_caracteristique_window, get_main_window

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
    # list_child_windows(window)
    carac = get_caracteristique_window(window)
    carac.set_focus()

    depart = get_depart(carac)
    depart.item1.set_edit_text("1")
    depart.item2.set_edit_text("2")
    depart.item3.set_edit_text("3")
    depart.item4.set_edit_text("4") 
    depart.item5.set_edit_text("5")


    arrive = get_arrive(carac)
    arrive.item1.set_edit_text("1")
    arrive.item2.set_edit_text("2")
    arrive.item3.set_edit_text("3")
    arrive.item4.set_edit_text("4")
    arrive.item5.set_edit_text("5")

    sens_ecoulement = get_sens_ecoulement(carac)
    sens_ecoulement.click_input()

    # identification = get_identification_controls(carac)

    # identification.operator_name.set_edit_text("Test Operator")
    
    # open_regards_tab(carac)
    
    # carac.print_control_identifiers()
