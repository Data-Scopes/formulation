"""Unit tests for STEPT1ad overlap_cue_prove (fixture only)."""

from __future__ import annotations

import json
from pathlib import Path

from formulation.overlap_cue_prove import (
    ProveFamily,
    annotate_short_continuations,
    assign_cue,
    attach_corpus_presence,
    bootstrap_cue_ids,
    cardinal_shortlist,
    induce_cue_hubs,
    is_short_continuation,
    overlap_union,
    paradigm_merge_families,
    paradigm_skeleton,
    place_band,
    prove_fold,
    straddle_conflict,
    substring_presence,
)
from formulation.phrases_5gram_profile import normalize_phrase

ROOT = Path(__file__).resolve().parents[1]
PHRASES = ROOT / "tests/fixtures/overlap_cue_prove_phrases.jsonl"
EDGES = ROOT / "tests/fixtures/overlap_cue_prove_edges.jsonl"


def _load(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _gedelib(phrases: list[dict]) -> list[dict]:
    want = {
        "waar op gedelibereert zynde is",
        "op gedelibereert zynde is goedgevonden",
        "gedelibereert zynde is goedgevonden en",
        "zynde is goedgevonden en verstaan",
    }
    return [p for p in phrases if normalize_phrase(str(p["phrase_norm"])) in want]


def test_overlap_chain_merges_and_no_edge_splits() -> None:
    phrases, edges = _load(PHRASES), _load(EDGES)
    g = _gedelib(phrases)
    merged = overlap_union(g, edges, min_n=500, min_frac=0.7)
    assert len(merged) == 1
    assert merged[0].cue == "waar_op"
    assert len(merged[0].members) == 4

    split = overlap_union(g, [], min_n=500, min_frac=0.7)
    assert len(split) == 4


def test_overlap_freq_is_not_corpus_presence() -> None:
    stats = substring_presence(
        "waar op gedelibereert zynde is",
        ["WAAR op gedelibereert zynde is goedgevonden …"],
        ids=["r1"],
    )
    assert stats["presence_field"] == "corpus_hit_rate"
    assert stats["merge_weight_field"] == "overlap_freq"
    assert stats["corpus_n_hit"] == 1
    # merge weight lives on edges, not in presence dict
    assert "overlap_freq" not in stats or stats.get("overlap_freq") is None


def test_bottom_up_cues_and_dominant_waar_op() -> None:
    phrases, edges = _load(PHRASES), _load(EDGES)
    assert "waar_op" in bootstrap_cue_ids()
    assert "gedelibereert_zijnde" not in bootstrap_cue_ids()
    assert assign_cue("ontfangen een missive van") == "ontfangen"
    assert assign_cue("waar op geen resolutie is") == "geen_resolutie"
    hubs = induce_cue_hubs(phrases, edges, min_n=500, min_frac=0.7)
    assert any("deliberatie" in h.surface for h in hubs)
    g = _gedelib(phrases)
    fam = overlap_union(g, edges, min_n=500, min_frac=0.7)[0]
    assert fam.cue == "waar_op"


def test_role_from_place_not_opener_abs() -> None:
    from formulation.overlap_cue_prove import role_from_place_and_cue

    assert (
        role_from_place_and_cue(
            place="exposition",
            cue="other",
            exemplar_norm="gedeputeerden van de provincie van",
        )
        == "carrier"
    )
    assert (
        role_from_place_and_cue(
            place="decision",
            cue="waar_op",
            exemplar_norm="waar op gedelibereert zynde is",
        )
        == "scaffolding_decision"
    )


def test_place_bands_hard_gate() -> None:
    assert place_band(0.05, "ontfangen een missive") == "opening"
    assert place_band(0.75, "waar op gedelibereert zynde") == "decision"
    phrases = [
        {
            "phrase_norm": "ontfangen een brief van den heer",
            "phrase_freq": 100,
            "place": "opening",
        },
        {
            "phrase_norm": "ontfangen een brief van den heer",
            "phrase_freq": 40,
            "place": "elaboration",
        },
    ]
    edge = [
        {
            "phrase1": "ontfangen een brief van den heer",
            "phrase2": "ontfangen een brief van den heer",
            "overlap_freq": 9999,
            "phrase1_frac": 1.0,
            "phrase2_frac": 1.0,
        }
    ]
    fams = overlap_union(phrases, edge, min_n=1, min_frac=0.0)
    assert len(fams) == 2
    assert {f.place for f in fams} == {"opening", "elaboration"}


def test_paradigm_slots_brief_not_missive() -> None:
    phrases = [
        {"phrase_norm": "ontfangen een brief van", "phrase_freq": 5000, "rel_mid": 0.08},
        {"phrase_norm": "ontfangen twee brieven van", "phrase_freq": 1200, "rel_mid": 0.09},
        {"phrase_norm": "ontfangen een missive van", "phrase_freq": 7000, "rel_mid": 0.07},
    ]
    assert paradigm_skeleton("ontfangen een brief van") == paradigm_skeleton(
        "ontfangen twee brieven van"
    )
    fams = paradigm_merge_families(overlap_union(phrases, [], min_n=1, min_frac=0.0))
    brief = [f for f in fams if "brief" in f.exemplar or any("brief" in m for m in f.members)]
    miss = [f for f in fams if "missive" in f.exemplar]
    assert len(brief) == 1
    assert any("twee" in m for m in brief[0].members)
    assert len(miss) == 1


def test_straddle_refuse() -> None:
    assert straddle_conflict("advertentie waar op geen", "waar op geen resolutie is")
    phrases, edges = _load(PHRASES), _load(EDGES)
    straddles = [
        p
        for p in phrases
        if normalize_phrase(str(p["phrase_norm"]))
        in ("advertentie waar op geen", "waar op geen resolutie is")
    ]
    s_edges = [
        e
        for e in edges
        if "advertentie" in normalize_phrase(str(e["phrase1"]))
        or "advertentie" in normalize_phrase(str(e["phrase2"]))
    ]
    fams = overlap_union(straddles, s_edges, min_n=500, min_frac=0.7)
    assert len(fams) == 2


def test_cardinal_corpus_and_no_auto_mint() -> None:
    phrases, edges = _load(PHRASES), _load(EDGES)
    texts = [
        "WAAR op gedelibereert zynde is goedgevonden en verstaan",
        "Ontfangen een missive van den heer, houdende dat …",
    ]
    out = prove_fold(
        phrases,
        edges,
        min_n=500,
        min_frac=0.7,
        texts=texts,
        text_ids=["a", "b"],
        skim_top=10,
        link_min_n=1,
    )
    assert all(f.human_role is None for f in out["families"])
    short = out["shortlist"]
    assert len(short) <= 10
    assert all(not is_short_continuation(f.exemplar) for f in short)
    ghost = attach_corpus_presence(
        [
            ProveFamily(
                family_id="g",
                exemplar="xyzzy no such formula",
                members=["xyzzy no such formula"],
                cue="other",
                place="unknown",
                phrase_freq_max=1,
            )
        ],
        texts,
    )[0]
    assert ghost.corpus_flag == "review"


def test_split_f1a_f1b_best_effort() -> None:
    phrases, edges = _load(PHRASES), _load(EDGES)
    fams = annotate_short_continuations(
        overlap_union(phrases, edges, min_n=1, min_frac=0.0),
        edges,
        min_n=1,
        min_frac=0.0,
    )
    shorts = [f for f in fams if is_short_continuation(f.exemplar)]
    assert shorts
    assert all(f.role in ("continuation", "fragment") for f in shorts)
    assert any(f.part_of for f in shorts)
    card = cardinal_shortlist(fams, skim_top=40)
    assert all(not is_short_continuation(f.exemplar) for f in card)
