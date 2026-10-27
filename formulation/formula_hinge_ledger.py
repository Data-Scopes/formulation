"""STEPT1ah: hinge archetype ledger (seed only).

Archetypes first under the locked formula-in-effect ontology.
Harvest / fold / residual rows are witnesses — not seeded here.
No witness TF-IDF, no auto-mint to formula_templates.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from data_io import load_jsonl

LOGICAL_NAME = "formula_hinge_candidates"
METRICS_NAME = "formula_hinge_metrics"
FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "formula_hinge_candidates.jsonl"
)

STATUSES = frozenset({"candidate", "from_blueprint", "pocket"})
LAYERS = frozenset({"scaffolding", "opener", "carrier"})
MOVES = frozenset(
    {"open", "refer", "decide", "null", "resume", "carrier", "unknown"}
)

REQUIRED_COLUMNS = (
    "hinge_id",
    "canonic",
    "place_band",
    "move",
    "layer",
    "status",
    "blueprint_id",
    "seed_refs",
    "human_keep",
    "human_note",
)

# Hand seed — decision scaffolding first, then L2 blueprints, then pockets.
# Omit: gedelibereert standalone, person/office strings, fold exemplars.
DEFAULT_SEED: tuple[dict[str, Any], ...] = (
    # --- decision / referral scaffolding ---
    {
        "hinge_id": "waar_op",
        "canonic": "WAAR op",
        "place_band": "decision",
        "move": "decide",
        "layer": "scaffolding",
        "status": "candidate",
        "blueprint_id": None,
        "seed_refs": [
            "docs/DECISIONS.md:2026-10-26-formula-in-effect",
            "formulation/overlap_cue_prove.py:CUE_BOOTSTRAP",
        ],
        "human_keep": None,
        "human_note": None,
    },
    {
        "hinge_id": "geen_resolutie",
        "canonic": "geen resolutie",
        "place_band": "decision",
        "move": "null",
        "layer": "scaffolding",
        "status": "candidate",
        "blueprint_id": None,
        "seed_refs": [
            "docs/DECISIONS.md:2026-10-26-formula-in-effect",
            "formulation/overlap_cue_prove.py:CUE_BOOTSTRAP",
        ],
        "human_keep": None,
        "human_note": None,
    },
    {
        "hinge_id": "goedgevonden",
        "canonic": "is goedgevonden en verstaan",
        "place_band": "decision",
        "move": "decide",
        "layer": "scaffolding",
        "status": "candidate",
        "blueprint_id": None,
        "seed_refs": [
            "docs/DECISIONS.md:2026-10-26-formula-in-effect",
            "tests/fixtures/formula_templates.jsonl:goedgevonden_decision_opener",
        ],
        "human_keep": None,
        "human_note": (
            "Positive decide scaffold. After this, 'Naar Y gestuurt voor advies' "
            "is composition (approve+refer), not one type. Typical Y: Raad van "
            "State; also Commissie 'om te … examineren'. More cues TBD — "
            "DECISIONS 2026-10-26 decision-polarity surface cues"
        ),
    },
    {
        "hinge_id": "in_handen",
        "canonic": "in handen van",
        "place_band": "referral",
        "move": "refer",
        "layer": "scaffolding",
        "status": "candidate",
        "blueprint_id": None,
        "seed_refs": [
            "docs/DECISIONS.md:2026-10-26-formula-in-effect",
            "formulation/overlap_cue_prove.py:CUE_BOOTSTRAP",
        ],
        "human_keep": None,
        "human_note": "Referral hinge — not attendance praesentibus/handen lists",
    },
    {
        "hinge_id": "advertentie",
        "canonic": "houdende advertentie",
        "place_band": "exposition",
        "move": "open",
        "layer": "scaffolding",
        "status": "candidate",
        "blueprint_id": None,
        "seed_refs": [
            "docs/DECISIONS.md:2026-10-26-harvest-artefacts",
            "docs/formula-conceptual-overview.md:formula-in-effect",
            "docs/DECISIONS.md:2026-10-26-decision-polarity-surface-cues",
        ],
        "human_keep": None,
        "human_note": (
            "Split from waar_op straddles (composition evidence, not one type). "
            "Exposition may formulaically cite execution phrases "
            "(afgewezen / afgehandeld te worden / naar-Y-gestuurt…), "
            "commissorial/advice-chain cues (resolutie commissoriaal; "
            "hebben … geexamineerd; op advies van), and earlier resolutions "
            "— citation ≠ a second decide hinge"
        ),
    },
    {
        "hinge_id": "ter_advies",
        "canonic": "ter advies",
        "place_band": "referral",
        "move": "refer",
        "layer": "scaffolding",
        "status": "candidate",
        "blueprint_id": None,
        "seed_refs": ["formulation/overlap_cue_prove.py:CUE_BOOTSTRAP"],
        "human_keep": None,
        "human_note": (
            "Bare referral cue. Distinct from post-goedgevonden "
            "'Naar Y gestuurt voor advies' (composition). Kin watchlist: "
            "'resolutie commissoriaal', 'hebben … geexamineerd', "
            "'op advies van' — roles TBD, not auto-merge"
        ),
    },
    {
        "hinge_id": "voldoening",
        "canonic": "ter voldoening",
        "place_band": "referral",
        "move": "refer",
        "layer": "scaffolding",
        "status": "candidate",
        "blueprint_id": None,
        "seed_refs": ["formulation/overlap_cue_prove.py:CUE_BOOTSTRAP"],
        "human_keep": None,
        "human_note": None,
    },
    {
        "hinge_id": "ontfangen",
        "canonic": "Ontfangen",
        "place_band": "opening",
        "move": "open",
        "layer": "scaffolding",
        "status": "candidate",
        "blueprint_id": None,
        "seed_refs": [
            "formulation/overlap_cue_prove.py:CUE_BOOTSTRAP",
            "plans/steps/STEPT1e-partition-probe.md",
        ],
        "human_keep": None,
        "human_note": "Opener scaffolding cue; missive_ontfangen is the typed L2 sibling",
    },
    # --- L2 of existing blueprints (specificity / reduced hinge) ---
    {
        "hinge_id": "requeste",
        "canonic": "Requeste",
        "place_band": "opening",
        "move": "open",
        "layer": "opener",
        "status": "from_blueprint",
        "blueprint_id": "requeste_geleesen",
        "seed_refs": [
            "docs/proofs/multi-template-registry/STEPT1v2-formula-reduction-hard-drop.md",
            "tests/fixtures/formula_templates.jsonl:requeste_geleesen",
        ],
        "human_keep": None,
        "human_note": "STEPT1v2 specificity (FP) hinge",
    },
    {
        "hinge_id": "requeste_op_de",
        "canonic": "Op de Requeste",
        "place_band": "opening",
        "move": "open",
        "layer": "opener",
        "status": "from_blueprint",
        "blueprint_id": "requeste_op_de",
        "seed_refs": ["tests/fixtures/formula_templates.jsonl:requeste_op_de"],
        "human_keep": None,
        "human_note": None,
    },
    {
        "hinge_id": "missive",
        "canonic": "Ontfangen een missive",
        "place_band": "opening",
        "move": "open",
        "layer": "opener",
        "status": "from_blueprint",
        "blueprint_id": "missive_ontfangen",
        "seed_refs": ["tests/fixtures/formula_templates.jsonl:missive_ontfangen"],
        "human_keep": None,
        "human_note": None,
    },
    {
        "hinge_id": "advies",
        "canonic": "geleesen het Advis",
        "place_band": "opening",
        "move": "open",
        "layer": "opener",
        "status": "from_blueprint",
        "blueprint_id": "advies_geleesen",
        "seed_refs": ["tests/fixtures/formula_templates.jsonl:advies_geleesen"],
        "human_keep": None,
        "human_note": None,
    },
    {
        "hinge_id": "rapport",
        "canonic": "gehoord het rapport",
        "place_band": "opening",
        "move": "open",
        "layer": "opener",
        "status": "from_blueprint",
        "blueprint_id": "rapport_gehoord",
        "seed_refs": ["tests/fixtures/formula_templates.jsonl:rapport_gehoord"],
        "human_keep": None,
        "human_note": None,
    },
    {
        "hinge_id": "welkom_sessie",
        "canonic": "verwelkomt",
        "place_band": "opening",
        "move": "open",
        "layer": "opener",
        "status": "from_blueprint",
        "blueprint_id": "appointment_installation",
        "seed_refs": [
            "tests/fixtures/formula_templates.jsonl:appointment_installation",
            "docs/proofs/multi-template-registry/STEPT1p-clause-chain-probe.md",
        ],
        "human_keep": None,
        "human_note": "STEPT1p: sessie backbone + optional welkom — hinge starts at verwelkomt",
    },
    # --- pockets (canonic null until human names) ---
    {
        "hinge_id": "voordracht",
        "canonic": None,
        "place_band": "opening",
        "move": "open",
        "layer": "carrier",
        "status": "pocket",
        "blueprint_id": None,
        "seed_refs": [
            "docs/proofs/multi-template-registry/STEPT1u-empty-band-5core.md",
            "tests/fixtures/opener_candidates.jsonl:voordracht",
        ],
        "human_keep": None,
        "human_note": "STEPT1u pocket — human must name canonic before named",
    },
    {
        "hinge_id": "conclusie_handen",
        "canonic": None,
        "place_band": "decision",
        "move": "decide",
        "layer": "carrier",
        "status": "pocket",
        "blueprint_id": None,
        "seed_refs": [
            "docs/proofs/multi-template-registry/STEPT1u-empty-band-5core.md",
            "tests/fixtures/opener_candidates.jsonl:conclusie_handen",
        ],
        "human_keep": None,
        "human_note": "STEPT1u pocket; may compose with in_handen — do not conflate with attendance",
    },
    # --- resolution/decision polarity (catalogue intent; canonic null) ---
    {
        "hinge_id": "decision_positive",
        "canonic": None,
        "place_band": "decision",
        "move": "decide",
        "layer": "carrier",
        "status": "pocket",
        "blueprint_id": None,
        "seed_refs": [
            "docs/DECISIONS.md:2026-10-26-formula-in-effect",
            "tests/fixtures/formula_hinge_candidates.jsonl:goedgevonden",
        ],
        "human_keep": None,
        "human_note": (
            "Positive resolution outcome; may coincide with goedgevonden "
            "until a distinct canonic is named — do not auto-merge"
        ),
    },
    {
        "hinge_id": "decision_negative",
        "canonic": None,
        "place_band": "decision",
        "move": "decide",
        "layer": "carrier",
        "status": "pocket",
        "blueprint_id": None,
        "seed_refs": [
            "docs/DECISIONS.md:2026-10-26-formula-in-effect",
            "docs/DECISIONS.md:2026-10-26-decision-polarity-surface-cues",
        ],
        "human_keep": None,
        "human_note": (
            "Negative / refused — proposed cue family 'afgewezen' (+ friends); "
            "canonic still null; ≠ geen_resolutie. Do not conflate with "
            "'afgehandeld te worden' (separate tentative cue)"
        ),
    },
    {
        "hinge_id": "decision_conditional",
        "canonic": None,
        "place_band": "decision",
        "move": "decide",
        "layer": "carrier",
        "status": "pocket",
        "blueprint_id": None,
        "seed_refs": ["docs/DECISIONS.md:2026-10-26-formula-in-effect"],
        "human_keep": None,
        "human_note": "Conditional resolution — canonic TBD",
    },
    {
        "hinge_id": "decision_deferred",
        "canonic": None,
        "place_band": "decision",
        "move": "decide",
        "layer": "carrier",
        "status": "pocket",
        "blueprint_id": None,
        "seed_refs": [
            "docs/DECISIONS.md:2026-10-26-formula-in-effect",
            "docs/DECISIONS.md:2026-10-26-decision-polarity-surface-cues",
        ],
        "human_keep": None,
        "human_note": (
            "Deferred / aangehouden — not null (geen_resolutie), not "
            "advertentie. Tentative cue: 'afgehandeld te worden' (to-be-"
            "handled; role TBD, may be purpose/referral-adjacent)"
        ),
    },
)

BLUEPRINT_IDS = frozenset(
    {
        "appointment_installation",
        "advies_geleesen",
        "requeste_geleesen",
        "missive_ontfangen",
        "requeste_op_de",
        "rapport_gehoord",
    }
)

DECISION_SCAFFOLD_IDS = frozenset(
    {"waar_op", "geen_resolutie", "goedgevonden", "in_handen"}
)

DECISION_POLARITY_POCKET_IDS = frozenset(
    {
        "decision_positive",
        "decision_negative",
        "decision_conditional",
        "decision_deferred",
    }
)


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    out = {k: row.get(k) for k in REQUIRED_COLUMNS}
    refs = out.get("seed_refs")
    if refs is None:
        out["seed_refs"] = []
    elif isinstance(refs, str):
        out["seed_refs"] = [refs]
    else:
        out["seed_refs"] = list(refs)
    return out


def default_seed_rows() -> list[dict[str, Any]]:
    """Return a deep-ish copy of the hand seed."""
    return [_normalize_row(dict(r)) for r in DEFAULT_SEED]


def load_fixture_rows(path: Path | None = None) -> list[dict[str, Any]]:
    p = path or FIXTURE_PATH
    return [_normalize_row(r) for r in load_jsonl(p)]


def validate_ledger(rows: list[dict[str, Any]]) -> list[str]:
    """Return human-readable problems (empty = ok)."""
    problems: list[str] = []
    ids = [str(r.get("hinge_id") or "") for r in rows]
    if len(ids) != len(set(ids)):
        problems.append("duplicate hinge_id")
    if any("gedelibereert" in i for i in ids):
        problems.append("gedelibereert must not be a hinge_id")
    n = len(rows)
    if n < 15 or n > 25:
        problems.append(f"n={n} outside band 15–25")
    for rid in DECISION_SCAFFOLD_IDS:
        if rid not in ids:
            problems.append(f"missing decision scaffold {rid}")
    linked = {
        str(r.get("blueprint_id"))
        for r in rows
        if r.get("status") == "from_blueprint" and r.get("blueprint_id")
    }
    missing_bp = BLUEPRINT_IDS - linked
    if missing_bp:
        problems.append(f"missing from_blueprint links: {sorted(missing_bp)}")
    for r in rows:
        st = r.get("status")
        if st not in STATUSES:
            problems.append(f"bad status {st!r} on {r.get('hinge_id')}")
        layer = r.get("layer")
        if layer not in LAYERS:
            problems.append(f"bad layer {layer!r} on {r.get('hinge_id')}")
        move = r.get("move")
        if move not in MOVES:
            problems.append(f"bad move {move!r} on {r.get('hinge_id')}")
        if st == "pocket" and r.get("canonic"):
            problems.append(f"pocket {r.get('hinge_id')} should have null canonic until named")
        if st == "from_blueprint" and not r.get("blueprint_id"):
            problems.append(f"from_blueprint {r.get('hinge_id')} needs blueprint_id")
        if st != "pocket" and not r.get("canonic"):
            problems.append(f"{r.get('hinge_id')} needs canonic")
    return problems


def ledger_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_layer: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_place: dict[str, int] = {}
    by_move: dict[str, int] = {}
    for r in rows:
        by_layer[str(r.get("layer"))] = by_layer.get(str(r.get("layer")), 0) + 1
        by_status[str(r.get("status"))] = by_status.get(str(r.get("status")), 0) + 1
        by_place[str(r.get("place_band"))] = by_place.get(str(r.get("place_band")), 0) + 1
        by_move[str(r.get("move"))] = by_move.get(str(r.get("move")), 0) + 1
    return {
        "step": "STEPT1ah",
        "n_hinges": len(rows),
        "by_layer": dict(sorted(by_layer.items())),
        "by_status": dict(sorted(by_status.items())),
        "by_place_band": dict(sorted(by_place.items())),
        "by_move": dict(sorted(by_move.items())),
        "note": (
            "Hinge archetypes only. Harvest rows are witnesses. "
            "No TF-IDF adjudicate / no auto-mint this step."
        ),
    }
