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


def _set_node_values(
    node,
    troncon: Mapping[str, object],
    profondeur_radier_key: str,
    log_callback: LogCallback | None = None,
) -> None:
    dimension_regard = str(troncon.get("dimension_regard", ""))
    profondeur_ouvrage = str(troncon.get("profondeur_ouvrage", ""))
    profondeur_radier = str(
        troncon.get(
            profondeur_radier_key,
            troncon.get("profondeur_radier", ""),
        )
    )
    hauteur_total = str(troncon.get("hauteur_total", ""))
    message = (
        "Filling regard values: dimension_regard=%r, profondeur_ouvrage=%r, "
        "profondeur_radier=%r, hauteur_total=%r"
    )
    LOGGER.debug(
        message,
        dimension_regard,
        profondeur_ouvrage,
        profondeur_radier,
        hauteur_total,
    )
    if log_callback is not None:
        log_callback(
            "DEBUG",
            message
            % (
                dimension_regard,
                profondeur_ouvrage,
                profondeur_radier,
                hauteur_total,
            ),
        )
    node.dim_regard.set_edit_text(dimension_regard)
    node.profondeur_ouvrage.set_edit_text(profondeur_ouvrage)
    node.profondeur_radier.set_edit_text(profondeur_radier)
    node.hauteur_total.set_edit_text(hauteur_total)


def apply_troncons(
    troncons: Sequence[Mapping[str, object]],
    operator_name: str,
    *,
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
        if log_callback is not None:
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

    for index, troncon in enumerate(troncons):
        row_number = index + 1
        progress(row_number, f"Tronçon {row_number}/{len(troncons)}")
        log(logging.INFO, f"Traitement du tronçon {row_number}/{len(troncons)}")

        current = get_list_troncons(window)

        # Canalyse names rows from 1, while the Python list is zero-based.
        select_troncon(window, current, index)
        log(logging.DEBUG, f"Tronçon sélectionné : {troncon.get('nom', row_number)}")
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
        depart = get_depart(regards)
        _set_node_values(depart, troncon, "profondeur_depart", log_callback)
        log(logging.DEBUG, "Valeurs renseignées sur le regard de départ")
        arrive = get_arrive(regards)
        _set_node_values(arrive, troncon, "profondeur_arrivee", log_callback)
        log(logging.DEBUG, "Valeurs renseignées sur le regard d'arrivée")

        flow_direction = troncon.get(
            "sens_ecoulement",
            troncon.get("direction", "A"),
        )
        if flow_direction == "B":
            sens_ecoulement = get_sens_ecoulement(regards)
            sens_ecoulement.pane.click_input()
            log(logging.DEBUG, "Sens d'écoulement inversé (sens_ecoulement B)")
        else:
            log(logging.DEBUG, "Sens d'écoulement conservé (sens_ecoulement A)")
        dialog.set_focus()

        click_ok(dialog)
        progress(row_number, f"Tronçon {row_number}/{len(troncons)} terminé")

    log(logging.INFO, "Automatisation terminée")
