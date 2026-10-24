
import logging

from lib.connect import connect_to_canalyse, get_main_window
from lib.troncons import get_list_troncons, click_troncon
from lib.buttons import click_modification_parametres

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

LOGGER = logging.getLogger(__name__)

if __name__ == "__main__":
    app = connect_to_canalyse()
    window = get_main_window(app)

    troncons = get_list_troncons(window)
    click_troncon(window, troncons, 10)

    click_modification_parametres(window)
