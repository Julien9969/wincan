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


def get_regards_controls(pane: WindowSpecification) -> RegardsControls:
    """Build selectors from the pane returned by ``open_regards_tab``."""
    sections = _panes(pane)
    if len(sections) < 4:
        raise RuntimeError(
            "Expected Regards tab panes in order: arrival, departure, "
            "flow direction, inspection direction"
        )
    arrival_node, departure_node, flow_direction, inspection_direction = sections[:4]

    arrival_sections = _panes(arrival_node)
    departure_sections = _panes(departure_node)
    if len(arrival_sections) < 2 or len(departure_sections) < 2:
        raise RuntimeError("Expected infiltration and cunette panes for both nodes")

    arrival_infiltration, arrival_cunette = arrival_sections[:2]
    departure_infiltration, departure_cunette = departure_sections[:2]
    arrival_edits = _items(arrival_node, "Edit")
    departure_edits = _items(departure_node, "Edit")
    arrival_combos = _items(arrival_node, "ComboBox")
    departure_combos = _items(departure_node, "ComboBox")
    arrival_infiltration_radios = _radio_buttons(arrival_infiltration)
    arrival_cunette_radios = _radio_buttons(arrival_cunette)
    departure_infiltration_radios = _radio_buttons(departure_infiltration)
    departure_cunette_radios = _radio_buttons(departure_cunette)
    inspection_buttons = _new_buttons(inspection_direction)
    inspection_combos = _items(inspection_direction, "ComboBox")

    if not all(
        (
            len(arrival_edits) >= 1,
            len(departure_edits) >= 1,
            len(arrival_combos) >= 2,
            len(departure_combos) >= 2,
            len(arrival_infiltration_radios) >= 2,
            len(arrival_cunette_radios) >= 2,
            len(departure_infiltration_radios) >= 2,
            len(departure_cunette_radios) >= 2,
            len(inspection_buttons) >= 2,
            len(inspection_combos) >= 2,
        )
    ):
        raise RuntimeError("Regards tab control order does not match the known UI")

    return RegardsControls(
        pane=pane,
        arrival_node=arrival_node,
        departure_node=departure_node,
        flow_direction=flow_direction,
        inspection_direction=inspection_direction,
        arrival_combos=tuple(arrival_combos),
        arrival_name=arrival_edits[0],
        arrival_edits=tuple(arrival_edits),
        departure_combos=tuple(departure_combos),
        departure_name=departure_edits[0],
        departure_edits=tuple(departure_edits),
        arrival_infiltration=arrival_infiltration,
        arrival_infiltration_yes=arrival_infiltration_radios[1],
        arrival_infiltration_no=arrival_infiltration_radios[0],
        arrival_cunette=arrival_cunette,
        arrival_cunette_yes=arrival_cunette_radios[1],
        arrival_cunette_no=arrival_cunette_radios[0],
        departure_infiltration=departure_infiltration,
        departure_infiltration_yes=departure_infiltration_radios[1],
        departure_infiltration_no=departure_infiltration_radios[0],
        departure_cunette=departure_cunette,
        departure_cunette_yes=departure_cunette_radios[1],
        departure_cunette_no=departure_cunette_radios[0],
        new_inspection_direction_left=inspection_buttons[0],
        new_inspection_direction_right=inspection_buttons[1],
    )
