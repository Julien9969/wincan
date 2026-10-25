"""Selectors for controls on the "Caractéristiques du collecteur" tab."""

import logging
from dataclasses import dataclass

from pywinauto import WindowSpecification


LOGGER = logging.getLogger(__name__)


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


@dataclass(frozen=True)
class CanalisationControls(FieldSectionControls):
    statut_reseau: WindowSpecification
    etat_reseau: WindowSpecification


def _items(pane: WindowSpecification, control_type: str):
    LOGGER.debug("Searching collector pane for %s controls", control_type)
    controls = pane.descendants(control_type=control_type)
    LOGGER.debug("Found %d %s control(s)", len(controls), control_type)
    return controls


def _pane(parent: WindowSpecification, title: str) -> WindowSpecification:
    LOGGER.debug("Resolving collector pane %r", title)
    section = parent.child_window(title=title, control_type="Pane")
    LOGGER.debug("Resolved collector pane %r", title)
    return section


def get_identification_controls(pane: WindowSpecification) -> IdentificationControls:
    LOGGER.info("Loading collector identification controls")
    identification = _pane(pane, "Identification")
    edits = _items(identification, "Edit")
    panes = _items(identification, "Pane")
    LOGGER.debug(
        "Identification controls: %d edit control(s), %d nested pane(s)",
        len(edits),
        len(panes),
    )
    if len(edits) < 2 or len(panes) < 2:
        LOGGER.error(
            "Identification controls are incomplete: %d edit(s), %d nested pane(s)",
            len(edits),
            len(panes),
        )
        raise RuntimeError(
            "Identification pane does not expose the expected controls"
        )
    return IdentificationControls(
        pane=identification,
        reference=edits[0],
        operator_name=edits[1],
        inspection_time=panes[0],
        inspection_date=panes[1],
    )


def get_intervention_controls(pane: WindowSpecification) -> InterventionControls:
    LOGGER.info("Loading collector intervention controls")
    intervention = _pane(pane, "Conditions d'intervention")
    checkboxes = _items(intervention, "CheckBox")
    if len(checkboxes) < 3:
        LOGGER.error(
            "Intervention pane has %d checkbox(es); expected at least 3",
            len(checkboxes),
        )
        raise RuntimeError(
            "Intervention pane does not expose the expected checkboxes"
        )
    LOGGER.debug("Intervention controls mapped: %d checkbox(es)", len(checkboxes))
    return InterventionControls(
        pane=intervention,
        ouvrage_sous_nappe=checkboxes[0],
        curage=checkboxes[1],
        temperature_sous_zero=checkboxes[2],
    )


def get_adresse_controls(pane: WindowSpecification) -> AdresseControls:
    LOGGER.info("Loading collector address controls")
    adresse = _pane(pane, "Adresse / Situation")
    combos = _items(adresse, "ComboBox")
    if not combos:
        LOGGER.error("Address pane has no combo boxes")
        raise RuntimeError("Address pane does not expose an emplacement combo box")
    LOGGER.debug("Address controls mapped: %d combo box(es)", len(combos))
    return AdresseControls(pane=adresse, emplacement=combos[0])


def get_canalisation_controls(pane: WindowSpecification) -> CanalisationControls:
    LOGGER.info("Loading collector canalisation controls")
    section = _pane(pane, "Caractéristiques de la canalisation")
    edits = tuple(_items(section, "Edit"))
    combos = tuple(_items(section, "ComboBox"))
    LOGGER.debug(
        "Canalisation controls mapped: %d edit control(s), %d combo box(es)",
        len(edits),
        len(combos),
    )
    if len(combos) < 2:
        LOGGER.error(
            "Canalisation pane has %d combo box(es); expected at least 2",
            len(combos),
        )
        raise RuntimeError(
            "Canalisation pane does not expose the expected combo boxes"
        )
    return CanalisationControls(
        pane=section,
        edits=edits,
        combos=combos,
        statut_reseau=combos[0],
        etat_reseau=combos[1],
    )


def get_tuyaux_controls(pane: WindowSpecification) -> FieldSectionControls:
    LOGGER.info("Loading collector tuyaux controls")
    section = _pane(pane, "Caractéristiques des tuyaux")
    edits = tuple(_items(section, "Edit"))
    combos = tuple(_items(section, "ComboBox"))
    LOGGER.debug(
        "Tuyaux controls mapped: %d edit control(s), %d combo box(es)",
        len(edits),
        len(combos),
    )
    return FieldSectionControls(
        pane=section,
        edits=edits,
        combos=combos,
    )


def get_observations_controls(pane: WindowSpecification) -> tuple[WindowSpecification, ...]:
    LOGGER.info("Loading collector observation controls")
    section = _pane(pane, "Observations / Conclusion")
    edits = tuple(_items(section, "Edit"))
    LOGGER.debug("Observation controls mapped: %d edit control(s)", len(edits))
    return edits


def get_collector_controls(pane: WindowSpecification) -> CollectorControls:
    """Return controls by pane and UI-tree order, without automation IDs."""
    LOGGER.info("Loading all collector controls")
    adresse = get_adresse_controls(pane)
    intervention = get_intervention_controls(pane)
    canalisation = get_canalisation_controls(pane)
    tuyaux = get_tuyaux_controls(pane)
    observations = _pane(pane, "Observations / Conclusion")
    identification = get_identification_controls(pane)
    observation_edits = get_observations_controls(pane)
    LOGGER.info("All collector controls loaded successfully")

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
        observation_edits=observation_edits,
    )