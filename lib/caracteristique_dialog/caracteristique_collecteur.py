"""Selectors for controls on the "Caractéristiques du collecteur" tab."""

from dataclasses import dataclass

from pywinauto import WindowSpecification


@dataclass(frozen=True)
class CollectorControls:
    """Stable controls exposed by the collector tab UIA tree."""

    pane: WindowSpecification
    emplacement: WindowSpecification
    canalisation: WindowSpecification
    tuyaux: WindowSpecification
    observations: WindowSpecification
    identification: WindowSpecification
    operator_name: WindowSpecification
    inspection_date: WindowSpecification
    inspection_time: WindowSpecification
    reference: WindowSpecification
    curage: WindowSpecification
    ouvrage_sous_nappe: WindowSpecification
    temperature_sous_zero: WindowSpecification
    canalisation_edits: tuple[WindowSpecification, ...]
    canalisation_combos: tuple[WindowSpecification, ...]
    tuyaux_edits: tuple[WindowSpecification, ...]
    tuyaux_combos: tuple[WindowSpecification, ...]
    observation_edits: tuple[WindowSpecification, ...]


def _items(pane: WindowSpecification, control_type: str):
    return pane.descendants(control_type=control_type)


def _pane(parent: WindowSpecification, title: str) -> WindowSpecification:
    return parent.child_window(title=title, control_type="Pane")


def get_collector_controls(pane: WindowSpecification) -> CollectorControls:
    """Return controls by pane and UI-tree order, without automation IDs."""
    adresse = _pane(pane, "Adresse / Situation")
    intervention = _pane(pane, "Conditions d'intervention")
    canalisation = _pane(pane, "Caractéristiques de la canalisation")
    tuyaux = _pane(pane, "Caractéristiques des tuyaux")
    observations = _pane(pane, "Observations / Conclusion")
    identification = _pane(pane, "Identification")

    adresse_combos = _items(adresse, "ComboBox")
    canalisation_combos = _items(canalisation, "ComboBox")
    canalisation_edits = _items(canalisation, "Edit")
    tuyaux_combos = _items(tuyaux, "ComboBox")
    tuyaux_edits = _items(tuyaux, "Edit")
    identification_edits = _items(identification, "Edit")
    identification_panes = _items(identification, "Pane")
    intervention_checkboxes = _items(intervention, "CheckBox")

    return CollectorControls(
        pane=pane,
        emplacement=adresse_combos[0],
        canalisation=canalisation,
        tuyaux=tuyaux,
        observations=observations,
        identification=identification,
        operator_name=identification_edits[1],
        inspection_date=identification_panes[1],
        inspection_time=identification_panes[0],
        reference=identification_edits[0],
        curage=intervention_checkboxes[1],
        ouvrage_sous_nappe=intervention_checkboxes[0],
        temperature_sous_zero=intervention_checkboxes[2],
        canalisation_edits=tuple(canalisation_edits),
        canalisation_combos=tuple(canalisation_combos),
        tuyaux_edits=tuple(tuyaux_edits),
        tuyaux_combos=tuple(tuyaux_combos),
        observation_edits=tuple(_items(observations, "Edit")),
    )