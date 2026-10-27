#!/usr/bin/env python3
"""STEPT1ad: prove overlap-cue fold principles (fixture-first).

Does not wire into ``formula_family_fold``. Never writes formula_templates.

    uv run pytest tests/test_overlap_cue_prove.py -q
    uv run python scripts/prove_overlap_cue_fold.py --fixture-only
    # optional (user runs; needs local.toml path for overlap dump):
    # uv run python scripts/prove_overlap_cue_fold.py --overlap --year 1780 --skim-top 60
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from formulation.overlap_cue_prove import (
    DEFAULT_MIN_FRAC,
    DEFAULT_MIN_OVERLAP_N,
    DEFAULT_SKIM_TOP,
    ProveFamily,
    annotate_short_continuations,
    assign_cue,
    attach_corpus_presence,
    bootstrap_cue_ids,
    cardinal_shortlist,
    induce_cue_hubs,
    is_short_continuation,
    iter_overlap_edges,
    overlap_union,
    paradigm_merge_families,
    place_band,
    prove_fold,
    substring_presence,
)
from formulation.phrases_5gram_profile import normalize_phrase

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PHRASES = ROOT / "tests/fixtures/overlap_cue_prove_phrases.jsonl"
FIXTURE_EDGES = ROOT / "tests/fixtures/overlap_cue_prove_edges.jsonl"
NOTES_PATH = ROOT / "docs/proofs/multi-template-registry/STEPT1ad-overlap-cue-fold.md"

FIXTURE_TEXTS: list[tuple[str, str]] = [
    (
        "r1",
        "WAAR op gedelibereert zynde is goedgevonden en verstaan dat men zal …",
    ),
    (
        "r2",
        "Ontfangen een missive van den heer X, houdende dat de saecken …",
    ),
    (
        "r3",
        "Ontfangen twee brieven van den raed, …",
    ),
    (
        "r4",
        "IS na voorgaande deliberatie goedgevonden en verstaan …",
    ),
]


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def load_fixture() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return _load_jsonl(FIXTURE_PHRASES), _load_jsonl(FIXTURE_EDGES)


def _gedelib_windows(phrases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = (
        "waar op gedelibereert zynde is",
        "op gedelibereert zynde is goedgevonden",
        "gedelibereert zynde is goedgevonden en",
        "zynde is goedgevonden en verstaan",
    )
    by = {normalize_phrase(str(p["phrase_norm"])): p for p in phrases}
    return [by[k] for k in keys if k in by]


def run_scenarios(
    phrases: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    *,
    min_n: int = DEFAULT_MIN_OVERLAP_N,
    min_frac: float = DEFAULT_MIN_FRAC,
    skim_top: int = DEFAULT_SKIM_TOP,
) -> list[dict[str, Any]]:
    """Named principle scenarios → pass/fail rows."""
    rows: list[dict[str, Any]] = []
    texts = [t for _, t in FIXTURE_TEXTS]
    text_ids = [i for i, _ in FIXTURE_TEXTS]

    # 1a Overlap chain → one family
    g_phrases = _gedelib_windows(phrases)
    g_edges = [
        e
        for e in edges
        if normalize_phrase(str(e["phrase1"]))
        in {normalize_phrase(str(p["phrase_norm"])) for p in g_phrases}
        or normalize_phrase(str(e["phrase2"]))
        in {normalize_phrase(str(p["phrase_norm"])) for p in g_phrases}
    ]
    chain = overlap_union(g_phrases, g_edges, min_n=min_n, min_frac=min_frac)
    ok_chain = len(chain) == 1 and chain[0].cue == "waar_op"
    rows.append(
        {
            "scenario": "overlap_chain",
            "n_families": len(chain),
            "exemplar": chain[0].exemplar if chain else "",
            "cue": chain[0].cue if chain else "",
            "place": chain[0].place if chain else "",
            "corpus_flag": "",
            "pass": ok_chain,
            "note": "3–4 gedelibereert windows + edges → 1 family under waar_op",
        }
    )

    # 1b Same windows, no edges → still split
    split = overlap_union(g_phrases, [], min_n=min_n, min_frac=min_frac)
    ok_split = len(split) == len(g_phrases)
    rows.append(
        {
            "scenario": "no_edge_split",
            "n_families": len(split),
            "exemplar": "",
            "cue": "",
            "place": "",
            "corpus_flag": "",
            "pass": ok_split,
            "note": "same windows, empty edges → still split",
        }
    )

    # 2 Overlap count ≠ corpus prevalence
    full = prove_fold(
        phrases,
        edges,
        min_n=min_n,
        min_frac=min_frac,
        texts=texts,
        text_ids=text_ids,
        skim_top=skim_top,
    )
    fam0 = next((f for f in full["families"] if f.cue == "waar_op"), None)
    ov = float(fam0.overlap_edges_used[0]["overlap_freq"]) if fam0 and fam0.overlap_edges_used else 0.0
    hit = float(fam0.corpus_n_hit or 0) if fam0 else -1.0
    # Presence uses corpus_* ; merge weight uses overlap_freq — fields differ
    stats = substring_presence(
        fam0.exemplar if fam0 else "waar op",
        texts,
        ids=text_ids,
    )
    ok_fields = (
        stats["presence_field"] == "corpus_hit_rate"
        and stats["merge_weight_field"] == "overlap_freq"
        and ov != hit  # different numeric meaning (large overlap_freq vs small n_hit)
    )
    rows.append(
        {
            "scenario": "overlap_freq_vs_presence",
            "n_families": 1,
            "exemplar": fam0.exemplar if fam0 else "",
            "cue": fam0.cue if fam0 else "",
            "place": fam0.place if fam0 else "",
            "corpus_flag": fam0.corpus_flag if fam0 else "",
            "pass": ok_fields,
            "note": f"overlap_freq={ov:.0f} vs corpus_n_hit={hit:.0f} (different fields)",
        }
    )

    # 3 Bottom-up cues + dominant waar_op
    hubs = induce_cue_hubs(phrases, edges, min_n=min_n, min_frac=min_frac)
    induced_ids = {h.cue_id for h in hubs}
    seeds = bootstrap_cue_ids()
    has_induced = any(i not in seeds for i in induced_ids) or any(
        "deliberatie" in h.surface for h in hubs
    )
    ok_dom = bool(fam0 and fam0.cue == "waar_op")
    rows.append(
        {
            "scenario": "bottom_up_cues",
            "n_families": len(hubs),
            "exemplar": hubs[0].surface if hubs else "",
            "cue": hubs[0].cue_id if hubs else "",
            "place": "",
            "corpus_flag": "",
            "pass": has_induced and ok_dom and "waar_op" in seeds,
            "note": f"seeds={sorted(seeds)}; induced={len(hubs)}; dominant waar_op={ok_dom}",
        }
    )

    # 4 Place bands — same cue, different place → no merge
    place_phrases = [
        {
            "phrase_norm": "ontfangen een brief van den heer",
            "phrase_freq": 100,
            "place": "opening",
            "cue": "ontfangen",
        },
        {
            "phrase_norm": "ontfangen een brief van den heer",
            "phrase_freq": 40,
            "place": "elaboration",
            "cue": "ontfangen",
        },
    ]
    place_fams = overlap_union(place_phrases, [], min_n=1, min_frac=0.0)
    # Also try a fake high-frac edge — still refuse cross-place
    cross_edge = [
        {
            "phrase1": "ontfangen een brief van den heer",
            "phrase2": "ontfangen een brief van den heer",
            "overlap_freq": 9999,
            "phrase1_frac": 1.0,
            "phrase2_frac": 1.0,
        }
    ]
    place_fams2 = overlap_union(place_phrases, cross_edge, min_n=1, min_frac=0.0)
    ok_place = len(place_fams) == 2 and len(place_fams2) == 2
    bands = {place_band(0.05, "ontfangen een missive"), place_band(0.75, "waar op gedelibereert")}
    rows.append(
        {
            "scenario": "place_bands",
            "n_families": len(place_fams2),
            "exemplar": "",
            "cue": "ontfangen",
            "place": ",".join(sorted({f.place for f in place_fams2})),
            "corpus_flag": "",
            "pass": ok_place and "opening" in bands and "decision" in bands,
            "note": "cross-place similars stay 2 families even with fake edge",
        }
    )

    # 5 Paradigm slots (opening-band ontfangen only)
    def _has_brief(p: dict[str, Any]) -> bool:
        n = normalize_phrase(str(p["phrase_norm"]))
        return "brief" in n.split() or "brieven" in n.split()

    brief_phrases = [
        p
        for p in phrases
        if _has_brief(p)
        and str(p.get("place") or place_band(p.get("rel_mid"), str(p["phrase_norm"])))
        == "opening"
    ]
    missive_phrases = [
        p
        for p in phrases
        if "missive" in normalize_phrase(str(p["phrase_norm"])).split()
        or "missiven" in normalize_phrase(str(p["phrase_norm"])).split()
    ]
    para = paradigm_merge_families(
        overlap_union(brief_phrases + missive_phrases, [], min_n=1, min_frac=0.0)
    )
    brief_fams = [f for f in para if "brief" in f.exemplar]
    miss_fams = [f for f in para if "missive" in f.exemplar]
    ok_para = len(brief_fams) == 1 and len(miss_fams) >= 1
    # brief family should contain both een/twee
    if brief_fams:
        mem = set(brief_fams[0].members)
        ok_para = ok_para and any("twee" in m for m in mem) and any(
            "een brief" in m for m in mem
        )
    rows.append(
        {
            "scenario": "paradigm_slots",
            "n_families": len(para),
            "exemplar": brief_fams[0].exemplar if brief_fams else "",
            "cue": "ontfangen",
            "place": brief_fams[0].place if brief_fams else "",
            "corpus_flag": "",
            "pass": ok_para,
            "note": "een brief + twee brieven merge; missive stays apart",
        }
    )

    # 6 Straddle refuse
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
    s_fams = overlap_union(straddles, s_edges, min_n=min_n, min_frac=min_frac)
    ok_straddle = len(s_fams) == 2
    rows.append(
        {
            "scenario": "straddle_refuse",
            "n_families": len(s_fams),
            "exemplar": "",
            "cue": "",
            "place": "",
            "corpus_flag": "",
            "pass": ok_straddle,
            "note": "advertentie|waar op edge does not re-glue",
        }
    )

    # 7 Cardinal corpus-test + shortlist cap
    shortlist = full["shortlist"]
    zero = attach_corpus_presence(
        [
            ProveFamily(
                family_id="ghost",
                exemplar="xyzzy nonexistent formula phrase qq",
                members=["xyzzy nonexistent formula phrase qq"],
                cue="other",
                place="unknown",
                phrase_freq_max=1.0,
            )
        ],
        texts,
        ids=text_ids,
    )[0]
    ok_corp = (
        len(shortlist) <= skim_top
        and all(not is_short_continuation(f.exemplar) for f in shortlist)
        and zero is not None
        and zero.corpus_flag == "review"
        and any((f.corpus_n_hit or 0) >= 1 for f in shortlist if f.cue == "waar_op")
    )
    rows.append(
        {
            "scenario": "cardinal_corpus_test",
            "n_families": len(shortlist),
            "exemplar": shortlist[0].exemplar if shortlist else "",
            "cue": shortlist[0].cue if shortlist else "",
            "place": shortlist[0].place if shortlist else "",
            "corpus_flag": shortlist[0].corpus_flag if shortlist else "",
            "pass": ok_corp,
            "note": f"shortlist≤{skim_top}; zero-hit→review; no short tails",
        }
    )

    # 8 No auto-mint
    ok_mint = all(f.human_role is None for f in full["families"])
    rows.append(
        {
            "scenario": "no_auto_mint",
            "n_families": len(full["families"]),
            "exemplar": "",
            "cue": "",
            "place": "",
            "corpus_flag": "",
            "pass": ok_mint,
            "note": "human_role always None; no formula_templates write",
        }
    )

    # 9 Split F1a/F1b short tails
    linked = annotate_short_continuations(
        overlap_union(phrases, edges, min_n=1, min_frac=0.0),
        edges,
        min_n=1,
        min_frac=0.0,
    )
    shorts = [f for f in linked if is_short_continuation(f.exemplar) or f.role in ("continuation", "fragment")]
    card = cardinal_shortlist(linked, skim_top=skim_top)
    ok_f1b = (
        all(not is_short_continuation(f.exemplar) for f in card)
        and any(f.role == "continuation" and f.part_of for f in shorts)
    )
    rows.append(
        {
            "scenario": "split_f1a_f1b",
            "n_families": len(shorts),
            "exemplar": next((f.exemplar for f in shorts), ""),
            "cue": "",
            "place": "",
            "corpus_flag": next((f.corpus_flag or "" for f in shorts), ""),
            "pass": ok_f1b,
            "note": "houdende dat suppressed from cardinals; part_of linked when edged",
        }
    )

    return rows


def _print_table(rows: list[dict[str, Any]]) -> None:
    cols = ("scenario", "n_families", "exemplar", "cue", "place", "corpus_flag", "pass")
    widths = {c: max(len(c), max(len(str(r.get(c, ""))[:40]) for r in rows)) for c in cols}
    hdr = " | ".join(c.ljust(widths[c]) for c in cols)
    print(hdr)
    print("-+-".join("-" * widths[c] for c in cols))
    for r in rows:
        print(
            " | ".join(
                str(r.get(c, ""))[:40].ljust(widths[c]) for c in cols
            )
        )
    n_pass = sum(1 for r in rows if r["pass"])
    print(f"\n{n_pass}/{len(rows)} scenarios PASS")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--fixture-only",
        action="store_true",
        default=True,
        help="Run named fixture scenarios (default)",
    )
    ap.add_argument(
        "--overlap",
        action="store_true",
        help="Stream phrases_5gram_overlap (optional; user runs)",
    )
    ap.add_argument("--year", type=int, default=None, help="Optional year slice (heavy)")
    ap.add_argument("--skim-top", type=int, default=DEFAULT_SKIM_TOP)
    ap.add_argument("--min-n", type=int, default=DEFAULT_MIN_OVERLAP_N)
    ap.add_argument("--min-frac", type=float, default=DEFAULT_MIN_FRAC)
    args = ap.parse_args()

    phrases, edges = load_fixture()
    # Fixture edges use high fracs but some links (houdende) are below DEFAULT_MIN_N;
    # scenarios that need the deliberation chain use DEFAULT; F1b uses min_n=1 inside.
    rows = run_scenarios(
        phrases,
        edges,
        min_n=args.min_n,
        min_frac=args.min_frac,
        skim_top=args.skim_top,
    )
    _print_table(rows)

    if args.overlap:
        from data_io import resolve

        path = resolve("phrases_5gram_overlap")
        print(f"\n[--overlap] streaming {path} (first kept edges sample)…")
        n = 0
        for _e in iter_overlap_edges(path, min_n=args.min_n, min_frac=args.min_frac):
            n += 1
            if n >= 5:
                break
        print(f"  saw ≥{n} kept edges (stream ok); full year fold is a later wire-up step")
        if args.year is not None:
            print(
                f"  --year {args.year}: not applied in prove (no fold wire); "
                "use after STEPT1ae"
            )

    # Cue smoke
    print("\nCue assign smoke:")
    for s in (
        "WAAR op gedelibereert zynde is",
        "ontfangen een missive van",
        "houdende dat",
        "na voorgaande deliberatie goedgevonden",
    ):
        print(f"  {assign_cue(s):24s}  {s}")

    failed = [r["scenario"] for r in rows if not r["pass"]]
    if failed:
        raise SystemExit(f"FAIL: {', '.join(failed)}")
    print(f"\nNOTES: fill {NOTES_PATH.relative_to(ROOT)} after review")


if __name__ == "__main__":
    main()
