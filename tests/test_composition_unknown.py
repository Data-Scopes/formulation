"""Unit smoke for STEPT1i composition unknown (no parquet)."""

from __future__ import annotations

from formulation.appointment_formula_type import FORMULA_TYPE_ID as APPOINTMENT_ID
from formulation.composition_unknown import (
    MOTIF_EMPTY,
    MOTIF_FILLER,
    MOTIF_KNOWN,
    MOTIF_NOVEL,
    accepted_core,
    build_composition_frame,
    classify_motif,
    fixture_composition_frame,
    summarize_composition_unknown,
)
from formulation.formula_type_composition_graph import COMPOSITION_ROOT


def test_accepted_core_drops_ontfangen() -> None:
    bag = (APPOINTMENT_ID, COMPOSITION_ROOT)
    assert accepted_core(bag) == (APPOINTMENT_ID,)
    assert accepted_core((COMPOSITION_ROOT,)) == ()


def test_same_core_with_without_ontfangen_is_known_sparse() -> None:
    frame = fixture_composition_frame()
    appt = frame.loc[frame["accepted_core"] == (APPOINTMENT_ID,)]
    assert len(appt) >= 5
    assert (appt["motif_class"] == MOTIF_KNOWN).all()
    # Variation: more than one exact bag under same core
    assert appt["present_bag"].nunique() >= 2


def test_filler_and_empty_and_novel() -> None:
    frame = fixture_composition_frame()
    assert MOTIF_FILLER in set(frame["motif_class"])
    assert MOTIF_EMPTY in set(frame["motif_class"])
    assert MOTIF_NOVEL in set(frame["motif_class"])
    filler = frame.loc[frame["motif_class"] == MOTIF_FILLER]
    assert not filler["composition_unknown"].any()
    undecided = frame.loc[frame["composition_unknown"]]
    assert set(undecided["motif_class"]) <= {MOTIF_EMPTY, MOTIF_NOVEL}


def test_classify_rare_core_is_novel_tail() -> None:
    # support 1 < min_support 5
    assert (
        classify_motif((APPOINTMENT_ID,), (APPOINTMENT_ID,), 1, min_support=5)
        == MOTIF_NOVEL
    )


def test_summarize_proto_blueprints() -> None:
    frame = fixture_composition_frame()
    metrics = summarize_composition_unknown(frame, year=1780, min_support=5)
    assert metrics["step"] == "STEPT1i"
    assert metrics["n_proto_blueprints"] >= 2
    assert "subtypes" not in metrics
    cores = {tuple(r["accepted_core"]) for r in metrics["proto_blueprints"]}
    assert (APPOINTMENT_ID,) in cores
    # Within-core variation recorded
    appt_row = next(
        r for r in metrics["proto_blueprints"] if r["accepted_core"] == [APPOINTMENT_ID]
    )
    assert appt_row["n_unique_exact_bags"] >= 2


def test_build_composition_frame_roundtrip() -> None:
    import pandas as pd

    raw = pd.DataFrame(
        {
            "id": ["a", "b"],
            "year": [1780, 1780],
            "present_bag": [(), (COMPOSITION_ROOT,)],
        }
    )
    frame = build_composition_frame(raw, min_support=5)
    assert frame.loc[0, "motif_class"] == MOTIF_EMPTY
    assert frame.loc[1, "motif_class"] == MOTIF_FILLER
