"""Fill one Canalyse Tronçon from a generated WinCan text file.

Usage:
    python fill_one_troncon.py input.txt

The script opens the first #B01/#B02/#B03 record only. It leaves the dialog
open for inspection and manual confirmation.
"""

from __future__ import annotations

import argparse
import csv
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import generate_wincan as protocol

if TYPE_CHECKING:
    from pywinauto import WindowSpecification


LOGGER = logging.getLogger(__name__)


def _read_record(path: Path) -> dict[str, list[str]]:
    blocks: dict[str, list[str]] = {}
    current = None
    with path.open("r", encoding="iso-8859-1", newline="") as source:
        for raw_line in source:
            line = raw_line.rstrip("\r\n")
            if line.startswith("#"):
                current = line.split("=", 1)[0]
                continue
            if current in {"#B01", "#B02", "#B03"} and current not in blocks:
                blocks[current] = next(csv.reader([line]))

    missing = {"#B01", "#B02", "#B03"} - blocks.keys()
    if missing:
        raise ValueError(f"First Tronçon is missing blocks: {', '.join(sorted(missing))}")
    return blocks


def _code_label(table, code: str) -> str:
    pairs = table.items() if isinstance(table, dict) else table
    for item_code, label in pairs:
        if item_code == code:
            return label
    return code


def _select_code(combo: "WindowSpecification", code: str, table) -> None:
    label = _code_label(table, code)
    candidates = (code, label, f"{code} - {label}")
    texts = []
    try:
        texts = combo.texts()
    except Exception:
        LOGGER.debug("Could not read combo items", exc_info=True)

    for candidate in candidates:
        if not texts or candidate in texts:
            try:
                combo.select(candidate)
                return
            except (LookupError, RuntimeError):
                LOGGER.debug("Could not select combo value %r", candidate, exc_info=True)

    for text in texts:
        if text == code or text.startswith(f"{code} - ") or label == text:
            combo.select(text)
            return
    raise ValueError(f"Code {code!r} is not available in combo {texts!r}")


def _set_text(control: "WindowSpecification", value: str) -> None:
    control.set_edit_text(value)


def _set_check(control: "WindowSpecification", checked: bool) -> None:
    state = control.get_toggle_state()
    if bool(state) != checked:
        control.toggle()


def _fill_regards(dialog: "WindowSpecification", b01: list[str]) -> None:
    from lib.caracteristique_dialog.open_caracteristique import open_regards_tab
    from lib.caracteristique_dialog.regards_visite import get_regards_controls

    regards = get_regards_controls(open_regards_tab(dialog))
    _set_text(regards.departure_name, b01[1])
    _set_text(regards.arrival_name, b01[3])
    LOGGER.info("Filled nodes: %s -> %s", b01[1], b01[3])


def _fill_collecteur(
    dialog: "WindowSpecification",
    b01: list[str],
    b02: list[str],
    b03: list[str],
) -> None:
    from lib.caracteristique_dialog.caracteristique_collecteur import (
        get_collector_controls,
    )
    from lib.caracteristique_dialog.open_caracteristique import open_collecteur_tab

    controls = get_collector_controls(open_collecteur_tab(dialog))

    _select_code(controls.emplacement, b01[6], protocol.EMPLACEMENT_CODES)
    _set_check(controls.curage, b01[11] == "A")

    _set_text(controls.operator_name, b02[5])
    _set_text(controls.canalisation_edits[0], b02[11])

    for combo, code, table in (
        (controls.canalisation_combos[0], b03[10], protocol.USAGE_RESEAU_CODES),
        (controls.canalisation_combos[1], b03[9], protocol.TYPE_ECOULEMENT_CODES),
        (controls.canalisation_combos[2], b03[11], protocol.ETAT_RESEAU_CODES),
        (controls.canalisation_combos[3], b02[10], protocol.STATUT_RESEAU_CODES),
    ):
        _select_code(combo, code, table)

    _set_text(controls.tuyaux_edits[0], b03[1])
    _set_text(controls.tuyaux_edits[1], b03[7])
    _set_text(controls.tuyaux_edits[2], b03[8])
    for combo, code, table in (
        (controls.tuyaux_combos[0], b03[0], protocol.FORME_CODES),
        (controls.tuyaux_combos[1], b03[3], protocol.MATERIAU_CODES),
    ):
        _select_code(combo, code, table)


def fill_first_troncon(path: Path) -> None:
    from lib.buttons import click_modification_parametres
    from lib.caracteristique_dialog.open_caracteristique import DIALOG_TITLE_RE
    from lib.connect import connect_to_canalyse, get_main_window

    blocks = _read_record(path)
    app = connect_to_canalyse()
    main_window = get_main_window(app)
    click_modification_parametres(main_window)

    dialog = app.window(title_re=DIALOG_TITLE_RE)
    dialog.wait("visible", timeout=10)
    _fill_regards(dialog, blocks["#B01"])
    _fill_collecteur(dialog, blocks["#B01"], blocks["#B02"], blocks["#B03"])
    LOGGER.info("First Tronçon filled; dialog left open for review.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Generated WinCan .txt file")
    args = parser.parse_args()
    fill_first_troncon(args.input)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    main()
