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


def _combo(parent: WindowSpecification, auto_id: str) -> WindowSpecification:
    return parent.child_window(auto_id=auto_id, control_type="ComboBox")


def _edit(parent: WindowSpecification, auto_id: str) -> WindowSpecification:
    return parent.child_window(auto_id=auto_id, control_type="Edit")


def _pane(parent: WindowSpecification, auto_id: str) -> WindowSpecification:
    return parent.child_window(auto_id=auto_id, control_type="Pane")


def _radio(parent: WindowSpecification, title: str, auto_id: str):
    return parent.child_window(
        title=title,
        auto_id=auto_id,
        control_type="RadioButton",
    )


def _button(parent: WindowSpecification, auto_id: str) -> WindowSpecification:
    return parent.child_window(
        title="Nouveau",
        auto_id=auto_id,
        control_type="Button",
    )


def get_regards_controls(pane: WindowSpecification) -> RegardsControls:
    """Build selectors from the pane returned by ``open_regards_tab``."""
    arrival_node = _pane(pane, "460628")
    departure_node = _pane(pane, "528186")
    arrival_infiltration = _pane(arrival_node, "657230")
    arrival_cunette = _pane(arrival_node, "790338")
    departure_infiltration = _pane(departure_node, "722954")
    departure_cunette = _pane(departure_node, "789110")

    return RegardsControls(
        pane=pane,
        arrival_node=arrival_node,
        departure_node=departure_node,
        flow_direction=_pane(pane, "201662"),
        inspection_direction=_pane(pane, "331582"),
        arrival_combos=(
            _combo(arrival_node, "724784"),
            _combo(arrival_node, "1311628"),
        ),
        arrival_name=_edit(arrival_node, "1001"),
        arrival_edits=tuple(
            _edit(arrival_node, auto_id)
            for auto_id in ("201590", "136048", "266910", "397794", "332594")
        ),
        departure_combos=(
            _combo(departure_node, "657254"),
            _combo(departure_node, "722824"),
        ),
        departure_name=_edit(departure_node, "1001"),
        departure_edits=tuple(
            _edit(departure_node, auto_id)
            for auto_id in ("332580", "463664", "463610", "398108", "201664")
        ),
        arrival_infiltration=arrival_infiltration,
        arrival_infiltration_yes=_radio(arrival_infiltration, "Oui", "591684"),
        arrival_infiltration_no=_radio(arrival_infiltration, "Non", "526150"),
        arrival_cunette=arrival_cunette,
        arrival_cunette_yes=_radio(arrival_cunette, "Oui", "526348"),
        arrival_cunette_no=_radio(arrival_cunette, "Non", "591904"),
        departure_infiltration=departure_infiltration,
        departure_infiltration_yes=_radio(departure_infiltration, "Oui", "657268"),
        departure_infiltration_no=_radio(departure_infiltration, "Non", "591736"),
        departure_cunette=departure_cunette,
        departure_cunette_yes=_radio(departure_cunette, "Oui", "920228"),
        departure_cunette_no=_radio(departure_cunette, "Non", "526156"),
        new_inspection_direction_left=_button(pane, "201668"),
        new_inspection_direction_right=_button(pane, "201670"),
    )
