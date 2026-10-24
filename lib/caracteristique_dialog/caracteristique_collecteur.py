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


def _combo(pane: WindowSpecification, auto_id: str) -> WindowSpecification:
    return pane.child_window(auto_id=auto_id, control_type="ComboBox")


def _edit(pane: WindowSpecification, auto_id: str) -> WindowSpecification:
    return pane.child_window(auto_id=auto_id, control_type="Edit")


def get_collector_controls(pane: WindowSpecification) -> CollectorControls:
    """Return named controls from the already-selected collector pane."""
    canalisation = pane.child_window(
        title="Caractéristiques de la canalisation",
        auto_id="657300",
        control_type="Pane",
    )
    tuyaux = pane.child_window(
        title="Caractéristiques des tuyaux",
        auto_id="591652",
        control_type="Pane",
    )
    observations = pane.child_window(
        title="Observations / Conclusion",
        auto_id="722694",
        control_type="Pane",
    )
    identification = pane.child_window(
        title="Identification",
        auto_id="136080",
        control_type="Pane",
    )

    return CollectorControls(
        pane=pane,
        emplacement=_combo(pane, "920082"),
        canalisation=canalisation,
        tuyaux=tuyaux,
        observations=observations,
        identification=identification,
        operator_name=_edit(identification, "136082"),
        inspection_date=identification.child_window(
            auto_id="136070",
            control_type="Pane",
        ),
        inspection_time=identification.child_window(
            auto_id="136074",
            control_type="Pane",
        ),
        reference=_edit(identification, "136072"),
        curage=pane.child_window(
            title="Curage réalisé avant l'inspection",
            auto_id="136026",
            control_type="CheckBox",
        ),
        ouvrage_sous_nappe=pane.child_window(
            title="Ouvrage sous nappe",
            auto_id="136028",
            control_type="CheckBox",
        ),
        temperature_sous_zero=pane.child_window(
            title="Température < 0°C",
            auto_id="201560",
            control_type="CheckBox",
        ),
        canalisation_edits=(_edit(canalisation, "135998"),),
        canalisation_combos=tuple(
            _combo(canalisation, auto_id)
            for auto_id in ("657274", "722754", "724678", "724174")
        ),
        tuyaux_edits=tuple(
            _edit(tuyaux, auto_id)
            for auto_id in ("136014", "136032", "136012")
        ),
        tuyaux_combos=tuple(
            _combo(tuyaux, auto_id)
            for auto_id in ("591378", "329806", "331580", "658030")
        ),
        observation_edits=tuple(
            _edit(observations, auto_id)
            for auto_id in ("1001", "136124")
        ),
    )