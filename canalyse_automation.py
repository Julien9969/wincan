"""Apply the loaded Tronçon configuration to the running Canalyse application."""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping, Sequence
from collections.abc import Callable
from time import sleep

from lib.buttons import click_modification_parametres
from lib.caracteristique_dialog.caracteristique_collecteur import (
    get_canalisation_controls,
    get_identification_controls,
)
from lib.caracteristique_dialog.open_caracteristique import click_ok, open_collecteur_tab, open_regards_tab
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


def _format_dimension_regard(value: object) -> str:
    """Format known regard dimensions and preserve free-form descriptions."""
    dimension = str(value).strip()
    if not dimension:
        return ""

    circular = re.fullmatch(r"Ø?\s*(\d+(?:[.,]\d+)?)", dimension, re.IGNORECASE)
    if circular:
        return f"Ø{circular.group(1)}"

    rectangular = re.fullmatch(
        r"(\d+(?:[.,]\d+)?)\s*[x×]\s*(\d+(?:[.,]\d+)?)",
        dimension,
        re.IGNORECASE,
    )
    if rectangular:
        return f"{rectangular.group(1)} x {rectangular.group(2)}"

    return dimension


def _set_node_values(
    node,
    troncon: Mapping[str, object],
    side: str,
    log_callback: LogCallback | None = None,
) -> None:
    if side not in ("depart", "arrive"):
        raise ValueError(f"Unknown node side: {side}")

    dimension_regard = _format_dimension_regard(
        troncon.get(f"dimension_regard_{side}", "")
    )
    profondeur_ouvrage = str(troncon.get(f"profondeur_ouvrage_{side}", ""))
    profondeur_radier = str(troncon.get(f"profondeur_radier_{side}", ""))
    hauteur_total = str(troncon.get(f"hauteur_total_{side}", ""))
    if not profondeur_ouvrage:
        profondeur_ouvrage = hauteur_total
    elif not hauteur_total:
        hauteur_total = profondeur_ouvrage
    message = (
        "Filling %s regard values: dimension_regard=%r, profondeur_ouvrage=%r, "
        "profondeur_radier=%r, hauteur_total=%r"
    )
    LOGGER.debug(
        message,
        side,
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
                side,
                dimension_regard,
                profondeur_ouvrage,
                profondeur_radier,
                hauteur_total,
            ),
        )

    for control, value in (
        (node.dim_regard, dimension_regard),
        (node.profondeur_ouvrage, profondeur_ouvrage),
        (node.profondeur_radier, profondeur_radier),
        (node.hauteur_total, hauteur_total),
    ):
        control.set_focus()
        control.select()
        control.type_keys("^a")
        control.type_keys(value)
        control.type_keys("{TAB}")

def set_canalisation_values(
    controls,
    troncon: Mapping[str, object],
    log_callback: LogCallback | None = None,
) -> None:
    """Set the values of the canalisation controls based on the troncon mapping."""
    # STATUT_RESEAU_CODES = {"": "Non précisé", "A": "En service", "B": "Hors service", "C": "Désaffecté"}
    # ETAT_RESEAU_CODES = {"A": "Neuf", "B": "Ancien"}
    # set statut_reseau move up in the combobox then down 0 for in_service, 1 for out_of_service, 2 for desafected 
    
    value = str(troncon.get("statut_reseau", ""))
    control = controls.statut_reseau
    control.type_keys("{UP}")
    control.type_keys("{UP}")

    if value == "B":
        control.type_keys("{DOWN}")
    elif value == "C":
        control.type_keys("{DOWN}")
        control.type_keys("{DOWN}")
    control.type_keys("{TAB}")

    # set etat_reseau move up in the combobox then down 0 for new, 1 for old
    value = str(troncon.get("etat_reseau", ""))
    control = controls.etat_reseau
    control.type_keys("{UP}")

    if value == "B":
        control.type_keys("{DOWN}")

    control.type_keys("{TAB}")
    

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
        if log_callback is not None:
            log_callback(logging.getLevelName(level), message)
        LOGGER.log(level, message)

    def progress(index: int, message: str) -> None:
        if progress_callback is not None:
            progress_callback(index, len(troncons), message)

    log(logging.INFO, f"Démarrage de l'automatisation ({len(troncons)} tronçon(s))")
    log(logging.INFO, "Connexion à Canalyse...")
    app = connect_to_canalyse(log_callback=log_callback)
    log(logging.INFO, "Connexion à Canalyse établie")
    log(logging.INFO, "Recherche de la fenêtre principale...")
    window = get_main_window(app)
    log(logging.INFO, "Fenêtre principale trouvée")
    log(logging.INFO, "Activation de la fenêtre principale...")
    window.set_focus()
    log(logging.INFO, "Fenêtre principale activée")

    log(logging.INFO, "Recherche des tronçons...")
    troncon_count = len(get_list_troncons(window))
    log(logging.INFO, f"Tronçons trouvés : {troncon_count}")

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

        log(logging.INFO, "Actualisation de la liste des tronçons...")
        current = get_list_troncons(window)
        log(logging.INFO, f"Liste actualisée : {len(current)} tronçon(s)")

        # Canalyse names rows from 1, while the Python list is zero-based.
        log(logging.INFO, f"Sélection du tronçon {row_number}...")
        select_troncon(window, current, index)
        log(logging.INFO, f"Tronçon {row_number} sélectionné")
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

        cara_cana = get_canalisation_controls(dialog)

        set_canalisation_values(cara_cana, troncon, log_callback=log_callback)

        regards = open_regards_tab(dialog)
        depart = get_depart(regards)
        _set_node_values(depart, troncon, "depart", log_callback)
        log(logging.DEBUG, "Valeurs renseignées sur le regard de départ")
        arrive = get_arrive(regards)
        _set_node_values(arrive, troncon, "arrive", log_callback)
        log(logging.DEBUG, "Valeurs renseignées sur le regard d'arrivée")

        flow_direction = str(
            troncon.get(
                "sens_ecoulement",
                troncon.get("direction", "A"),
            )
        ).strip().upper()
        log(logging.DEBUG, f"Sens d'écoulement demandé : {flow_direction!r}")
        if flow_direction == "B":
            sens_ecoulement = get_sens_ecoulement(regards)
            sens_ecoulement.pane.set_focus()
            sens_ecoulement.pane.click_input()
            log(logging.DEBUG, "Sens d'écoulement inversé (sens_ecoulement B)")
        else:
            log(logging.DEBUG, "Sens d'écoulement conservé (sens_ecoulement A)")
        # dialog.set_focus()

        # open_collecteur_tab(dialog)
        # dialog.set_focus()

        # sleep(1)  # Wait for the dialog to be ready for validation

        click_ok(dialog)
        progress(row_number, f"Tronçon {row_number}/{len(troncons)} terminé")

    log(logging.INFO, "Automatisation terminée")
