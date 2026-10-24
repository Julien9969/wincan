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


@dataclass(frozen=True)
class IdentificationControls:
    pane: WindowSpecification
    operator_name: WindowSpecification
    inspection_date: WindowSpecification
    inspection_time: WindowSpecification
    reference: WindowSpecification


@dataclass(frozen=True)
class InterventionControls:
    pane: WindowSpecification
    curage: WindowSpecification
    ouvrage_sous_nappe: WindowSpecification
    temperature_sous_zero: WindowSpecification


@dataclass(frozen=True)
class AdresseControls:
    pane: WindowSpecification
    emplacement: WindowSpecification


@dataclass(frozen=True)
class FieldSectionControls:
    pane: WindowSpecification
    edits: tuple[WindowSpecification, ...]
    combos: tuple[WindowSpecification, ...]


def _items(pane: WindowSpecification, control_type: str):
    return pane.descendants(control_type=control_type)


def _pane(parent: WindowSpecification, title: str) -> WindowSpecification:
    return parent.child_window(title=title, control_type="Pane")


def get_identification_controls(pane: WindowSpecification) -> IdentificationControls:
    identification = _pane(pane, "Identification")
    edits = _items(identification, "Edit")
    panes = _items(identification, "Pane")
    return IdentificationControls(
        pane=identification,
        reference=edits[0],
        operator_name=edits[1],
        inspection_time=panes[0],
        inspection_date=panes[1],
    )


def get_intervention_controls(pane: WindowSpecification) -> InterventionControls:
    intervention = _pane(pane, "Conditions d'intervention")
    checkboxes = _items(intervention, "CheckBox")
    return InterventionControls(
        pane=intervention,
        ouvrage_sous_nappe=checkboxes[0],
        curage=checkboxes[1],
        temperature_sous_zero=checkboxes[2],
    )


def get_adresse_controls(pane: WindowSpecification) -> AdresseControls:
    adresse = _pane(pane, "Adresse / Situation")
    return AdresseControls(
        pane=adresse,
        emplacement=_items(adresse, "ComboBox")[0],
    )


def get_canalisation_controls(pane: WindowSpecification) -> FieldSectionControls:
    section = _pane(pane, "Caractéristiques de la canalisation")
    return FieldSectionControls(
        pane=section,
        edits=tuple(_items(section, "Edit")),
        combos=tuple(_items(section, "ComboBox")),
    )


def get_tuyaux_controls(pane: WindowSpecification) -> FieldSectionControls:
    section = _pane(pane, "Caractéristiques des tuyaux")
    return FieldSectionControls(
        pane=section,
        edits=tuple(_items(section, "Edit")),
        combos=tuple(_items(section, "ComboBox")),
    )


def get_observations_controls(pane: WindowSpecification) -> tuple[WindowSpecification, ...]:
    section = _pane(pane, "Observations / Conclusion")
    return tuple(_items(section, "Edit"))


def get_collector_controls(pane: WindowSpecification) -> CollectorControls:
    """Return controls by pane and UI-tree order, without automation IDs."""
    adresse = get_adresse_controls(pane)
    intervention = get_intervention_controls(pane)
    canalisation = get_canalisation_controls(pane)
    tuyaux = get_tuyaux_controls(pane)
    observations = _pane(pane, "Observations / Conclusion")
    identification = get_identification_controls(pane)

    return CollectorControls(
        pane=pane,
        emplacement=adresse.emplacement,
        canalisation=canalisation.pane,
        tuyaux=tuyaux.pane,
        observations=observations,
        identification=identification.pane,
        operator_name=identification.operator_name,
        inspection_date=identification.inspection_date,
        inspection_time=identification.inspection_time,
        reference=identification.reference,
        curage=intervention.curage,
        ouvrage_sous_nappe=intervention.ouvrage_sous_nappe,
        temperature_sous_zero=intervention.temperature_sous_zero,
        canalisation_edits=canalisation.edits,
        canalisation_combos=canalisation.combos,
        tuyaux_edits=tuyaux.edits,
        tuyaux_combos=tuyaux.combos,
        observation_edits=get_observations_controls(pane),
    )