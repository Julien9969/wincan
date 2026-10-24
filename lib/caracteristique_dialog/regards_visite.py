"""Control mapping for the "Regards de visite & fiches simplifiées" tab."""

import logging
from dataclasses import dataclass

from pywinauto import WindowSpecification


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class NodeControls:
    pane: WindowSpecification
    name: WindowSpecification
    edits: tuple[WindowSpecification, ...]
    combos: tuple[WindowSpecification, ...]
    item1: WindowSpecification
    item2: WindowSpecification
    item3: WindowSpecification
    item4: WindowSpecification
    item5: WindowSpecification


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
    LOGGER.debug("Searching Regards tab for top-level panes")
    panes = parent.children(control_type="Pane")
    LOGGER.debug("Found %d top-level pane(s)", len(panes))
    return panes


def _get_section(pane: WindowSpecification, index: int) -> WindowSpecification:
    LOGGER.debug("Resolving Regards pane at index %d", index)
    sections = _panes(pane)
    if len(sections) < 4:
        LOGGER.error(
            "Regards tab has %d pane(s); expected at least 4",
            len(sections),
        )
        raise RuntimeError(
            "Expected Regards panes in order: arrival, departure, "
            "flow direction, inspection direction"
        )
    LOGGER.debug("Resolved Regards pane at index %d", index)
    return sections[index]


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
        item1=edits[0],
        item2=edits[2],
        item3=edits[3],
        item4=edits[4],
        item5=edits[5],
    )


def get_arrive(pane: WindowSpecification) -> NodeControls:
    """Return controls for the arrival node."""
    LOGGER.info("Loading arrival-node controls")
    return _get_node(_get_section(pane, 0))


def get_depart(pane: WindowSpecification) -> NodeControls:
    """Return controls for the departure node."""
    LOGGER.info("Loading departure-node controls")
    return _get_node(_get_section(pane, 1))


def get_sens_inspection(pane: WindowSpecification) -> InspectionDirectionControls:
    """Return controls for the inspection direction."""
    LOGGER.info("Loading inspection-direction controls")
    section = _get_section(pane, 3)
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
    return FlowDirectionControls(pane=_get_section(pane, 2))
