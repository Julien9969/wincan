"""Apply the loaded Tronçon configuration to the running Canalyse application."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from collections.abc import Callable
from threading import Event

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
    cancel_event: Event | None = None,
) -> None:
    """Apply every loaded configuration entry to the corresponding Canalyse row.

    The list is intentionally passed in by the GUI, so XML-loaded values and
    values edited after loading follow the same path. Direction B is the only
    case that activates the flow-direction control.
    """
    if not troncons:
        raise ValueError("Aucun tronçon à appliquer")

    def log(level: str, message: str) -> None:
        getattr(LOGGER, level)(message)
        if log_callback is not None and (debug or level != "debug"):
            log_callback(level.upper(), message)

    def progress(index: int, message: str) -> None:
        if progress_callback is not None:
            progress_callback(index, len(troncons), message)

    log("info", f"Démarrage de l'automatisation ({len(troncons)} tronçon(s))")
    app = connect_to_canalyse()
    window = get_main_window(app)
    available = get_list_troncons(window)
    log("debug", f"Canalyse expose {len(available)} tronçon(s)")
    if len(available) < len(troncons):
        raise RuntimeError(
            f"Canalyse expose {len(available)} tronçon(s), "
            f"mais {len(troncons)} configuration(s) doivent être appliquées"
        )

    for index, troncon in enumerate(troncons):
        if cancel_event is not None and cancel_event.is_set():
            log("info", "Automatisation annulée par l'utilisateur")
            return
        progress(index, f"Tronçon {index + 1}/{len(troncons)}")
        log("info", f"Traitement du tronçon {index + 1}/{len(troncons)}")
        current = get_list_troncons(window)
        # Canalyse names rows from 1, while the Python list is zero-based.
        select_troncon(window, current, index)
        log("debug", f"Tronçon sélectionné : {troncon.get('nom', index + 1)}")
        click_modification_parametres(window)
        dialog = get_caracteristique_window(app)

        identification = get_identification_controls(dialog)
        identification.operator_name.set_edit_text(operator_name)
        log("debug", f"Opérateur renseigné : {operator_name}")

        regards = open_regards_tab(dialog)
        _set_common_node_values(get_depart(regards), troncon)
        _set_common_node_values(get_arrive(regards), troncon)
        log("debug", "Valeurs communes renseignées sur les deux regards")

        if troncon.get("direction", "A") == "B":
            get_sens_ecoulement(regards).pane.click_input()
            log("debug", "Sens d'écoulement inversé (direction B)")
        else:
            log("debug", "Sens d'écoulement conservé (direction A)")

        click_ok(dialog)
        progress(index + 1, f"Tronçon {index + 1}/{len(troncons)} terminé")

    log("info", "Automatisation terminée")
