
import logging

from lib.connect import connect_to_canalyse, get_caracteristique_window, get_main_window
from lib.troncons import get_list_troncons, click_troncon
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

    troncons = get_list_troncons(window)
    click_troncon(window, troncons, 10)
    LOGGER.debug("Clicked troncon: %r", troncons[10])

    click_modification_parametres(window)

    carac = get_caracteristique_window(app)
    carac.set_focus()
    carac.print_control_identifiers()
