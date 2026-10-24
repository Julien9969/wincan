"""Control mapping for the "Regards de visite & fiches simplifiées" tab."""

from dataclasses import dataclass

from pywinauto import WindowSpecification


@dataclass(frozen=True)
class RegardsControls:
    """UI elements exposed by the Regards tab."""

    pane: WindowSpecification
    arrival_node: WindowSpecification
    departure_node: WindowSpecification
    flow_direction: WindowSpecification
    inspection_direction: WindowSpecification
    arrival_combos: tuple[WindowSpecification, ...]
    arrival_name: WindowSpecification
    arrival_edits: tuple[WindowSpecification, ...]
    departure_combos: tuple[WindowSpecification, ...]
    departure_name: WindowSpecification
    departure_edits: tuple[WindowSpecification, ...]
    arrival_infiltration: WindowSpecification
    arrival_infiltration_yes: WindowSpecification
    arrival_infiltration_no: WindowSpecification
    arrival_cunette: WindowSpecification
    arrival_cunette_yes: WindowSpecification
    arrival_cunette_no: WindowSpecification
    departure_infiltration: WindowSpecification
    departure_infiltration_yes: WindowSpecification
    departure_infiltration_no: WindowSpecification
    departure_cunette: WindowSpecification
    departure_cunette_yes: WindowSpecification
    departure_cunette_no: WindowSpecification
    new_inspection_direction_left: WindowSpecification
    new_inspection_direction_right: WindowSpecification


@dataclass(frozen=True)
class NodeControls:
    pane: WindowSpecification
    name: WindowSpecification
    edits: tuple[WindowSpecification, ...]
    combos: tuple[WindowSpecification, ...]


@dataclass(frozen=True)
class BinaryChoiceControls:
    pane: WindowSpecification
    yes: WindowSpecification
    no: WindowSpecification


@dataclass(frozen=True)
class InspectionDirectionControls:
    pane: WindowSpecification
    combos: tuple[WindowSpecification, ...]
    new_left: WindowSpecification
    new_right: WindowSpecification


def _items(parent: WindowSpecification, control_type: str):
    return parent.descendants(control_type=control_type)


def _panes(parent: WindowSpecification):
    return parent.children(control_type="Pane")


def _radio_buttons(parent: WindowSpecification):
    return _items(parent, "RadioButton")


def _new_buttons(parent: WindowSpecification):
    return [
        button for button in _items(parent, "Button")
        if button.window_text() == "Nouveau"
    ]


def get_node_controls(
    pane: WindowSpecification,
    node_index: int,
) -> NodeControls:
    """Load one node pane by its order in the Regards tab."""
    nodes = _panes(pane)
    if node_index < 0 or node_index >= 2:
        raise ValueError("node_index must be 0 (arrival) or 1 (departure)")
    node = nodes[node_index]
    edits = tuple(_items(node, "Edit"))
    combos = tuple(_items(node, "ComboBox"))
    if not edits or len(combos) < 2:
        raise RuntimeError("Node pane does not expose the expected controls")
    return NodeControls(
        pane=node,
        name=edits[0],
        edits=edits,
        combos=combos,
    )


def get_node_choice_controls(
    node: WindowSpecification,
    choice_index: int,
) -> BinaryChoiceControls:
    """Load infiltration or cunette controls by nested pane order."""
    choices = _panes(node)
    if choice_index < 0 or choice_index >= 2:
        raise ValueError("choice_index must be 0 (infiltration) or 1 (cunette)")
    choice = choices[choice_index]
    radios = _radio_buttons(choice)
    if len(radios) < 2:
        raise RuntimeError("Choice pane does not expose two radio buttons")
    return BinaryChoiceControls(
        pane=choice,
        no=radios[0],
        yes=radios[1],
    )


def get_inspection_direction_controls(
    pane: WindowSpecification,
) -> InspectionDirectionControls:
    """Load the inspection-direction pane and its ordered controls."""
    sections = _panes(pane)
    if len(sections) < 4:
        raise RuntimeError("Regards tab does not expose four top-level panes")
    direction = sections[3]
    buttons = _new_buttons(direction)
    combos = tuple(_items(direction, "ComboBox"))
    if len(buttons) < 2 or len(combos) < 2:
        raise RuntimeError("Inspection direction controls are incomplete")
    return InspectionDirectionControls(
        pane=direction,
        combos=combos,
        new_left=buttons[0],
        new_right=buttons[1],
    )


def get_regards_controls(pane: WindowSpecification) -> RegardsControls:
    """Build selectors from the pane returned by ``open_regards_tab``."""
    sections = _panes(pane)
    if len(sections) < 4:
        raise RuntimeError(
            "Expected Regards tab panes in order: arrival, departure, "
            "flow direction, inspection direction"
        )
    arrival_node, departure_node, flow_direction, inspection_direction = sections[:4]
    arrival = get_node_controls(pane, 0)
    departure = get_node_controls(pane, 1)
    arrival_infiltration = get_node_choice_controls(arrival.pane, 0)
    arrival_cunette = get_node_choice_controls(arrival.pane, 1)
    departure_infiltration = get_node_choice_controls(departure.pane, 0)
    departure_cunette = get_node_choice_controls(departure.pane, 1)
    inspection = get_inspection_direction_controls(pane)

    return RegardsControls(
        pane=pane,
        arrival_node=arrival_node,
        departure_node=departure_node,
        flow_direction=flow_direction,
        inspection_direction=inspection_direction,
        arrival_combos=arrival.combos,
        arrival_name=arrival.name,
        arrival_edits=arrival.edits,
        departure_combos=departure.combos,
        departure_name=departure.name,
        departure_edits=departure.edits,
        arrival_infiltration=arrival_infiltration.pane,
        arrival_infiltration_yes=arrival_infiltration.yes,
        arrival_infiltration_no=arrival_infiltration.no,
        arrival_cunette=arrival_cunette.pane,
        arrival_cunette_yes=arrival_cunette.yes,
        arrival_cunette_no=arrival_cunette.no,
        departure_infiltration=departure_infiltration.pane,
        departure_infiltration_yes=departure_infiltration.yes,
        departure_infiltration_no=departure_infiltration.no,
        departure_cunette=departure_cunette.pane,
        departure_cunette_yes=departure_cunette.yes,
        departure_cunette_no=departure_cunette.no,
        new_inspection_direction_left=inspection.new_left,
        new_inspection_direction_right=inspection.new_right,
    )
