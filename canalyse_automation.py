"""Apply the loaded Tronçon configuration to the running Canalyse application."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from collections.abc import Callable

from lib.buttons import click_modification_parametres
from lib.caracteristique_dialog.caracteristique_collecteur import (
    get_identification_controls,
)
from lib.caracteristique_dialog.open_caracteristique import click_ok, open_regards_tab
from lib.caracteristique_dialog.regards_visite import (
    get_arrive,
    get_depart,
    get_sens_ecoulement,
)
from lib.connect import connect_to_canalyse, get_caracteristique_window, get_main_window
from lib.troncons import get_list_troncons, select_troncon


LOGGER = logging.getLogger(__name__)
LogCallback = Callable[[str, str], None]
ProgressCallback = Callable[[int, int, str], None]


def _set_common_node_values(node, troncon: Mapping[str, object]) -> None:
    node.dim_regard.set_edit_text(str(troncon.get("dimension_regard", "")))
    node.profondeur_ouvrage.set_edit_text(str(troncon.get("profondeur_ouvrage", "")))
    node.profondeur_radier.set_edit_text(str(troncon.get("profondeur_radier", "")))
    node.hauteur_total.set_edit_text(str(troncon.get("hauteur_total", "")))


def apply_troncons(
    troncons: Sequence[Mapping[str, object]],
    operator_name: str,
    *,
    debug: bool = False,
    log_callback: LogCallback | None = None,
    progress_callback: ProgressCallback | None = None,
) -> None:
    """Apply every loaded configuration entry to the corresponding Canalyse row.

    The list is intentionally passed in by the GUI, so XML-loaded values and
    values edited after loading follow the same path. Direction B is the only
    case that activates the flow-direction control.
    """
    if not troncons:
        raise ValueError("Aucun tronçon à appliquer")

    def log(level: int, message: str) -> None:
        LOGGER.log(level, message)
        if log_callback is not None and (debug or level != logging.DEBUG):
            log_callback(logging.getLevelName(level), message)

    def progress(index: int, message: str) -> None:
        if progress_callback is not None:
            progress_callback(index, len(troncons), message)

    log(logging.INFO, f"Démarrage de l'automatisation ({len(troncons)} tronçon(s))")
    app = connect_to_canalyse()
    window = get_main_window(app)
    window.set_focus()

    troncon_count = len(get_list_troncons(window))

    log(logging.DEBUG, f"Canalyse expose {troncon_count} tronçon(s)")
    if troncon_count < len(troncons):
        raise RuntimeError(
            f"Canalyse expose {troncon_count} tronçon(s), "
            f"mais {len(troncons)} configuration(s) doivent être appliquées"
        )

    for index in range(1, troncon_count + 1):
        progress(index, f"Tronçon {index + 1}/{len(troncons)}")
        log(logging.INFO, f"Traitement du tronçon {index + 1}/{len(troncons)}")
        
        current = get_list_troncons(window)
        troncon = troncons[index-1] 
        
        # Canalyse names rows from 1, while the Python list is zero-based.
        select_troncon(window, current, index)
        log(logging.DEBUG, f"Tronçon sélectionné : {troncon.get('nom', index + 1)}")
        log(logging.DEBUG, "Ouverture de la fenêtre des caractéristiques")
        click_modification_parametres(window)
        log(logging.DEBUG, "Bouton des caractéristiques activé; recherche de la fenêtre")
        dialog = get_caracteristique_window(window)
        dialog.set_focus()

        log(logging.DEBUG, "Fenêtre des caractéristiques trouvée")

        identification = get_identification_controls(dialog)
        identification.operator_name.set_edit_text(operator_name)
        log(logging.DEBUG, f"Opérateur renseigné : {operator_name}")

        regards = open_regards_tab(dialog)
        _set_common_node_values(get_depart(regards), troncon)
        _set_common_node_values(get_arrive(regards), troncon)
        log(logging.DEBUG, "Valeurs communes renseignées sur les deux regards")

        if troncon.get("direction", "A") == "B":
            get_sens_ecoulement(regards).pane.click_input()
            log(logging.DEBUG, "Sens d'écoulement inversé (direction B)")
        else:
            log(logging.DEBUG, "Sens d'écoulement conservé (direction A)")

        click_ok(dialog)
        progress(index + 1, f"Tronçon {index + 1}/{len(troncons)} terminé")

    log(logging.INFO, "Automatisation terminée")
