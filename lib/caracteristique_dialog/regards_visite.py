"""Control mapping for the "Regards de visite & fiches simplifiées" tab."""

import logging
import re
from dataclasses import dataclass

from pywinauto import WindowSpecification


LOGGER = logging.getLogger(__name__)
_PANE_CACHE: dict[int, dict[str, WindowSpecification]] = {}


@dataclass(frozen=True)
class NodeControls:
    pane: WindowSpecification
    name: WindowSpecification
    edits: tuple[WindowSpecification, ...]
    combos: tuple[WindowSpecification, ...]
    n_maison: WindowSpecification
    profondeur_ouvrage: WindowSpecification
    item3: WindowSpecification
    profondeur_radier: WindowSpecification
    heuteur_total: WindowSpecification


@dataclass(frozen=True)
class InspectionDirectionControls:
    pane: WindowSpecification
    combos: tuple[WindowSpecification, ...]
    new_left: WindowSpecification
    new_right: WindowSpecification


@dataclass(frozen=True)
class FlowDirectionControls:
    pane: WindowSpecification


def _items(parent: WindowSpecification, control_type: str):
    LOGGER.debug("Searching Regards pane for %s controls", control_type)
    controls = parent.descendants(control_type=control_type)
    LOGGER.debug("Found %d %s control(s)", len(controls), control_type)
    return controls


def _panes(parent: WindowSpecification):
    cache_key = id(parent)
    cached = _PANE_CACHE.get(cache_key)
    if cached is not None:
        LOGGER.debug("Using cached Regards pane mapping")
        return cached

    LOGGER.debug("Searching Regards tab for named panes")
    panes = parent.descendants(control_type="Pane")
    LOGGER.debug("Found %d Regards pane(s)", len(panes))

    named_panes = {}
    expected_titles = {
        "arrive": r"Noeud d'arrivée",
        "depart": r"Noeud de départ",
        "ecoulement": r"Sens de l'écoulement",
        "inspection": r"Sens de l'inspection",
    }
    for pane in panes:
        title = pane.window_text()
        LOGGER.debug("Regards pane found: %r", title)
        for name, pattern in expected_titles.items():
            if re.search(pattern, title, re.IGNORECASE):
                named_panes[name] = pane

    missing = set(expected_titles) - set(named_panes)
    if missing:
        LOGGER.error("Missing Regards pane(s): %s", ", ".join(sorted(missing)))
        raise RuntimeError(
            "Could not find Regards pane(s): " + ", ".join(sorted(missing))
        )
    LOGGER.debug("Regards panes mapped: %s", ", ".join(named_panes))
    _PANE_CACHE[cache_key] = named_panes
    return named_panes


def _get_section(pane: WindowSpecification, name: str) -> WindowSpecification:
    LOGGER.debug("Resolving Regards pane %r", name)
    section = _panes(pane)[name]
    LOGGER.debug("Resolved Regards pane %r", name)
    return section


def _get_node(node: WindowSpecification) -> NodeControls:
    LOGGER.debug("Loading node controls")
    edits = tuple(_items(node, "Edit"))
    combos = tuple(_items(node, "ComboBox"))
    if len(edits) < 6 or len(combos) < 2:
        LOGGER.error(
            "Node pane has %d edit control(s) and %d combo box(es); "
            "expected at least 6 edits and 2 combo boxes",
            len(edits),
            len(combos),
        )
        raise RuntimeError("Node pane does not expose the expected controls")
    combo_edits = tuple(combos[0].children(control_type="Edit"))
    if not combo_edits:
        combo_edits = tuple(combos[0].descendants(control_type="Edit"))
    LOGGER.debug(
        "First node combo box contains %d Edit control(s)",
        len(combo_edits),
    )
    if not combo_edits:
        LOGGER.error("First node combo box does not contain an Edit control")
        raise RuntimeError(
            "First node combo box does not expose its embedded Edit control"
        )
    LOGGER.debug(
        "Node controls mapped: %d edit control(s), %d combo box(es)",
        len(edits),
        len(combos),
    )
    return NodeControls(
        pane=node,
        name=edits[1],
        edits=edits,
        combos=combos,
        n_maison=edits[0],
        profondeur_ouvrage=edits[2],
        item3=combo_edits[0],
        profondeur_radier=edits[4],
        heuteur_total=edits[5],
    )


def get_arrive(pane: WindowSpecification) -> NodeControls:
    """Return controls for the arrival node."""
    LOGGER.info("Loading arrival-node controls")
    return _get_node(_get_section(pane, "arrive"))


def get_depart(pane: WindowSpecification) -> NodeControls:
    """Return controls for the departure node."""
    LOGGER.info("Loading departure-node controls")
    return _get_node(_get_section(pane, "depart"))


def get_sens_inspection(pane: WindowSpecification) -> InspectionDirectionControls:
    """Return controls for the inspection direction."""
    LOGGER.info("Loading inspection-direction controls")
    section = _get_section(pane, "inspection")
    buttons = [
        button for button in _items(section, "Button")
        if button.window_text() == "Nouveau"
    ]
    combos = tuple(_items(section, "ComboBox"))
    if len(buttons) < 2 or len(combos) < 2:
        LOGGER.error(
            "Inspection pane has %d Nouveau button(s) and %d combo box(es); "
            "expected at least 2 of each",
            len(buttons),
            len(combos),
        )
        raise RuntimeError("Inspection direction controls are incomplete")
    LOGGER.debug(
        "Inspection controls mapped: %d Nouveau button(s), %d combo box(es)",
        len(buttons),
        len(combos),
    )
    return InspectionDirectionControls(
        pane=section,
        combos=combos,
        new_left=buttons[0],
        new_right=buttons[1],
    )


def get_sens_ecoulement(pane: WindowSpecification) -> FlowDirectionControls:
    """Return the flow-direction pane."""
    LOGGER.info("Loading flow-direction pane")
    return FlowDirectionControls(pane=_get_section(pane, "ecoulement"))
