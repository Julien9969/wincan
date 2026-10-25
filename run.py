
import logging
from contextlib import contextmanager
from time import perf_counter

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


@contextmanager
def timed_step(name: str):
    started = perf_counter()
    LOGGER.info("START %s", name)
    try:
        yield
    finally:
        LOGGER.info("END %s (%.3f s)", name, perf_counter() - started)


if __name__ == "__main__":
    app = connect_to_canalyse()
    window = get_main_window(app)

    LOGGER.debug("Main window: %r", window)

    troncon_count = len(get_list_troncons(window))

    for index in range(1, troncon_count):
        with timed_step(f"Tronçon {index}: refresh and select"):
            troncons = get_list_troncons(window)
            select_troncon(window, troncons, index)
        LOGGER.debug("Selected troncon: %r", troncons[index])

        with timed_step(f"Tronçon {index}: open characteristics dialog"):
            click_modification_parametres(window)
            carac = get_caracteristique_window(window)

        with timed_step(f"Tronçon {index}: load collector identification"):
            identification = get_identification_controls(carac)
            identification.operator_name.set_edit_text("Kais Mougeot")
            LOGGER.debug("Collector identification loaded")

        # list_child_windows(window)
        carac.set_focus()
        with timed_step(f"Tronçon {index}: open Regards tab"):
            regards = open_regards_tab(carac)

        with timed_step(f"Tronçon {index}: fill departure node"):
            depart = get_depart(regards)
            # depart.n_maison.set_edit_text("1")
            depart.dim_regard.set_edit_text("400")
            depart.profondeur_ouvrage.set_edit_text("12.2")
            depart.profondeur_radier.set_edit_text("24")
            depart.hauteur_total.set_edit_text("90")

        with timed_step(f"Tronçon {index}: fill arrival node"):
            arrive = get_arrive(regards)
            # arrive.n_maison.set_edit_text("1")
            arrive.profondeur_ouvrage.set_edit_text("34.5")
            arrive.dim_regard.set_edit_text("300")
            arrive.profondeur_radier.set_edit_text("34")
            arrive.hauteur_total.set_edit_text("50")

        with timed_step(f"Tronçon {index}: set flow direction"):
            sens_ecoulement = get_sens_ecoulement(regards)
            sens_ecoulement.pane.click_input()

        with timed_step(f"Tronçon {index}: validate dialog"):
            click_ok(carac)

    # identification = get_identification_controls(carac)

    # identification.operator_name.set_edit_text("Test Operator")
