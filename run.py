
import logging

from lib.buttons import click_modification_parametres
from lib.caracteristique_dialog.caracteristique_collecteur import (
    get_identification_controls,
)
from lib.caracteristique_dialog.open_caracteristique import click_ok, open_regards_tab
from lib.caracteristique_dialog.regards_visite import get_arrive, get_depart, get_sens_ecoulement
from lib.connect import connect_to_canalyse, get_caracteristique_window, get_main_window
from lib.troncons import get_list_troncons, select_troncon

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
)

LOGGER = logging.getLogger(__name__)

if __name__ == "__main__":
    app = connect_to_canalyse()
    window = get_main_window(app)

    LOGGER.debug("Main window: %r", window)

    troncons = get_list_troncons(window)

    for index, troncon in enumerate(troncons):
        select_troncon(window, troncons, index)
        LOGGER.debug("Selected troncon: %r", troncons[index])

        click_modification_parametres(window)
        carac = get_caracteristique_window(window)
        
        identification = get_identification_controls(carac)
        identification.operator_name.set_edit_text("Kais Mougeot")
        # list_child_windows(window)
        # carac.set_focus()
        regards = open_regards_tab(carac)

        depart = get_depart(regards)
        # depart.n_maison.set_edit_text("1")
        depart.dim_regard.set_edit_text("400")
        depart.profondeur_ouvrage.set_edit_text("12.2")
        depart.profondeur_radier.set_edit_text("24") 
        depart.hauteur_total.set_edit_text("90")


        arrive = get_arrive(regards)
        # arrive.n_maison.set_edit_text("1")
        arrive.profondeur_ouvrage.set_edit_text("34.5")
        arrive.dim_regard.set_edit_text("300")
        arrive.profondeur_radier.set_edit_text("34")
        arrive.hauteur_total.set_edit_text("50")

        sens_ecoulement = get_sens_ecoulement(regards)
        sens_ecoulement.pane.click_input()

        click_ok(carac)

    # identification = get_identification_controls(carac)

    # identification.operator_name.set_edit_text("Test Operator")
