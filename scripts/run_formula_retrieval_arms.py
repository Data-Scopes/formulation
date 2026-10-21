#!/usr/bin/env python3
"""STEPT1q: compare retrieval arms for one formula on clean post-re-pin gold.

Gold is sampled from the *pinned* ES index (never the stale ``*_es_gold``),
with text joined from the same generation, reusing the validated sampler in
``recheck_es_gold_sample.py``.

    uv run python scripts/run_formula_retrieval_arms.py --fixture-only
    uv run python scripts/run_formula_retrieval_arms.py --type missive --per-year 15
    uv run python scripts/run_formula_retrieval_arms.py --type requeste --per-year 15
"""

from __future__ import annotations

import argparse
import json
from typing import Any

import pandas as pd

from data_io import load, save_semi_structured
from formulation.appointment_formula_type import RNG, YEAR_MAX, YEAR_MIN
from formulation.es_gold_sample import (
    flat_texts,
    stratified_gold_ids,
    verified_negatives,
)
from formulation.formula_retrieval_arms import (
    TYPES,
    build_clean_boot_cloud,
    fixture_frames,
    format_summary,
    load_type_api,
    recall_matched_fp,
    scheme_search_phrase,
    score_arms,
    summarize,
)

# STEPS1b frozen cosine cut; calibrated for opening_requeste_18c only, so for
# other types it is a starting point the step guide requires reporting beside
# the sample-calibrated one.
TFIDF_THRESHOLD_DEFAULT = 0.40

# Arms with a numeric score column; recall-matched FP (DEFECT 1) is anchored
# to the minimum gold recall across these. Anchor arms (substring_*) are
# boolean with no score, so they are excluded.
RECALL_MATCH_ARMS = ("tfidf_window", "dag_frozen", "dag_clean_boot")

# n=226 gave a Wilson half-width of +/-0.026 against a 0.05 FP gate, which
# cannot resolve it. For missive, ~55% of sampled negatives get dropped as
# actually-missive, so 2500 yields roughly 1100 clean ones.
NEG_N_DEFAULT = 2500


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--type", default="missive", choices=list(TYPES))
    p.add_argument(
        "--fixture-only",
        action="store_true",
        help="Tiny in-memory smoke (no ES / resolutions_flat)",
    )
    p.add_argument(
        "--per-year",
        type=int,
        default=15,
        help="Gold ids sampled per session_year from the pinned index",
    )
    p.add_argument(
        "--boot-per-year",
        type=int,
        default=0,
        help=(
            "ids/year for a disjoint clean bootstrap pool; 0 = bootstrap "
            "from the eval gold (confounded vs dag_frozen)"
        ),
    )
    p.add_argument(
        "--neg-n",
        type=int,
        default=NEG_N_DEFAULT,
        help=(
            f"Negatives sampled before verification (default {NEG_N_DEFAULT}). "
            "For missive, ~55% of sampled negatives get dropped as "
            "actually-missive, so 2500 yields roughly 1100 clean ones; n=226 "
            "gave a Wilson half-width of +/-0.026 against a 0.05 FP gate, "
            "which cannot resolve it."
        ),
    )
    p.add_argument("--random-state", type=int, default=RNG)
    p.add_argument(
        "--tfidf-threshold",
        type=float,
        default=TFIDF_THRESHOLD_DEFAULT,
        help=f"Cosine cut for the TF-IDF arm (default {TFIDF_THRESHOLD_DEFAULT})",
    )
    p.add_argument(
        "--no-frozen-dag",
        action="store_true",
        help="Skip the stale-bootstrap DAG arm (needs the *_es_gold sets)",
    )
    p.add_argument("--no-write", action="store_true")
    p.add_argument(
        "--json",
        action="store_true",
        help="Print the full JSON metrics instead of the readable summary",
    )
    p.add_argument(
        "--fresh",
        action="store_true",
        help="discard previously accumulated runs for these datasets instead of merging",
    )
    p.add_argument(
        "--random-within-year",
        action="store_true",
        help=(
            "sample gold randomly within each year instead of taking the "
            "lowest ids (default: systematic, comparable to the recorded "
            "recheck numbers)"
        ),
    )
    return p.parse_args(argv)


def merge_runs(
    logical: str,
    new_records: list[dict],
    *,
    key: tuple[str, str],
    fresh: bool = False,
) -> list[dict]:
    """Accumulate ``new_records`` onto the existing ``logical`` dataset.

    STEPT1q needs several runs (missive, requeste, missive with
    ``--random-within-year``, ...) and each must survive the next one, so
    this keyes on ``(record["type"], record["sampling_mode"])``: existing
    records matching ``key`` are dropped (this run replaces them), every
    other existing record is kept untouched. A missing/unreadable dataset is
    treated as empty - same defensive pattern as ``stale_metrics`` in
    ``scripts/recheck_es_gold_sample.py``. ``fresh=True`` discards the
    existing accumulation entirely and returns just ``new_records``.
    """
    if fresh:
        return list(new_records)
    try:
        rows = load(logical)
        rows = rows if isinstance(rows, list) else rows.to_dict("records")
    except Exception:
        rows = []
    kept = [r for r in rows if (r.get("type"), r.get("sampling_mode")) != key]
    return kept + list(new_records)


def collect_sample(
    type_key: str,
    *,
    per_year: int,
    boot_per_year: int,
    neg_n: int,
    random_state: int,
    random_within_year: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Clean stratified gold + individually verified negatives + boot pool.

    ``boot_per_year > 0`` samples a second, disjoint stratified id set (ids
    present in the eval gold are dropped) and joins its text into a pool for
    ``build_clean_boot_cloud``, so the clean DAG arm can match ``dag_frozen``
    on bootstrap volume without reusing eval rows. ``boot_per_year == 0``
    returns an empty pool, which keeps today's eval-gold-bootstrap behaviour.
    """
    from formulation.republic_es import RepublicEsClient

    client = RepublicEsClient()
    pt = TYPES[type_key]["proposition_type"]

    gold_ids = stratified_gold_ids(
        client,
        pt,
        per_year=per_year,
        random_within_year=random_within_year,
        random_seed=random_state,
    )
    gold = flat_texts(gold_ids)
    gold_id_set = {r["id"] for r in gold_ids}

    if boot_per_year > 0:
        pool_ids = stratified_gold_ids(
            client,
            pt,
            per_year=boot_per_year,
            random_within_year=random_within_year,
            random_seed=random_state,
        )
        pool_ids = [r for r in pool_ids if r["id"] not in gold_id_set]
        pool = flat_texts(pool_ids)
    else:
        pool = pd.DataFrame(columns=["id", "year", "resolutions_text"])

    exclude = gold_id_set | set(pool["id"].astype(str).tolist())
    neg, n_dropped = verified_negatives(
        client,
        exclude=exclude,
        n=neg_n,
        proposition_type=pt,
        random_state=random_state,
    )
    sampling_mode = "random_within_year" if random_within_year else "systematic_id_asc"
    return (
        gold,
        neg,
        pool,
        {
            "index": client.config.resolutions_index,
            "sampling": (
                f"stratified {per_year}/year {YEAR_MIN}-{YEAR_MAX} ({sampling_mode})"
            ),
            "n_gold_requested": len(gold_ids),
            "n_negatives_dropped": int(n_dropped),
            "sampling_mode": sampling_mode,
        },
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    api = load_type_api(args.type)

    if args.fixture_only:
        gold, neg = fixture_frames()
        pool = pd.DataFrame(columns=["id", "year", "resolutions_text"])
        meta = {
            "index": "fixture",
            "sampling": "fixture_frames",
            "n_gold_requested": len(gold),
            "n_negatives_dropped": 0,
            "sampling_mode": (
                "random_within_year" if args.random_within_year else "systematic_id_asc"
            ),
        }
        parents = None
    else:
        gold, neg, pool, meta = collect_sample(
            args.type,
            per_year=int(args.per_year),
            boot_per_year=int(args.boot_per_year),
            neg_n=int(args.neg_n),
            random_state=int(args.random_state),
            random_within_year=bool(args.random_within_year),
        )
        parents = ["resolutions_flat"]
        print(
            f"clean sample: {len(gold)} gold / {len(neg)} negatives / "
            f"{len(pool)} boot pool",
            flush=True,
        )

    if gold.empty:
        raise SystemExit("no gold rows joined - check the pinned index")

    clouds: dict[str, Any] = {}
    cuts: dict[str, float] = {}

    # Arm 4: cloud re-bootstrapped from a disjoint pool when available, else
    # from the clean sample (what G1 is judged on).
    boot_cloud, boot_cut, boot_notes = build_clean_boot_cloud(
        gold, api=api, pool=pool, random_state=int(args.random_state)
    )
    clouds["dag_clean_boot"] = boot_cloud
    cuts["dag_clean_boot"] = boot_cut

    # Arm 3: the deployed frozen model (cloud bootstrapped from stale gold).
    if args.fixture_only or args.no_frozen_dag:
        reason = "fixture_only" if args.fixture_only else "--no-frozen-dag"
        print(f"skipping dag_frozen ({reason})", flush=True)
    else:
        model = api["fit_presence"]()
        clouds["dag_frozen"] = model["cloud"]
        cuts["dag_frozen"] = float(model["operating_cut"])

    scored, tfidf_threshold_p20 = score_arms(
        gold,
        neg,
        api=api,
        clouds=clouds,
        cuts=cuts,
        tfidf_threshold=float(args.tfidf_threshold),
    )
    # Record both TF-IDF thresholds (frozen + this-sample p20) alongside the
    # DAG cuts already in `cuts`, so metrics["cuts"] carries every arm's cut.
    cuts["tfidf_window"] = float(args.tfidf_threshold)
    cuts["tfidf_window_p20"] = float(tfidf_threshold_p20)

    gold_scored = scored.loc[scored["role"] == "gold"].reset_index(drop=True)
    neg_scored = scored.loc[scored["role"] == "negative"].reset_index(drop=True)

    arms = [
        "substring_wording",
        "substring_scheme",
        "tfidf_window",
        "tfidf_window_p20",
        *[a for a in ("dag_frozen", "dag_clean_boot") if a in clouds],
    ]

    metrics = summarize(
        type_key=args.type,
        gold=gold_scored,
        neg=neg_scored,
        arms=arms,
        cuts=cuts,
        tfidf_threshold=float(args.tfidf_threshold),
        index=str(meta["index"]),
        sampling=str(meta["sampling"]),
        n_gold_requested=int(meta["n_gold_requested"]),
        n_negatives_dropped=int(meta["n_negatives_dropped"]),
    )
    metrics["fixture_only"] = bool(args.fixture_only)
    metrics["sampling_mode"] = str(meta["sampling_mode"])
    metrics["sampling_seed"] = int(args.random_state)
    metrics["clean_boot_notes"] = {
        k: boot_notes.get(k)
        for k in ("n_bootstrap", "n_holdout", "cut_rule", "n_hits_accepted")
        if k in boot_notes
    }
    metrics["n_bootstrap_pool"] = int(len(pool))
    metrics["bootstrap_source"] = str(boot_notes.get("bootstrap_source"))

    # DEFECT 1: dag_frozen/dag_clean_boot (and tfidf_window) were each firing
    # at their OWN cut, so a raw FP comparison between them conflates
    # "looser cut" with "worse arm". Anchor every scored arm to the same
    # gold recall (the minimum achieved across them) before comparing FP.
    rates_by_arm = {r["arm"]: r for r in metrics["arms"]}
    score_arms_present = [
        a
        for a in RECALL_MATCH_ARMS
        if f"{a}_score" in gold_scored.columns
        and gold_scored[f"{a}_score"].notna().any()
    ]
    recall_matched: dict[str, Any] = {
        "note": (
            "Anchor arms (substring_wording, substring_scheme) are boolean "
            "with no score column, so they are excluded from recall-matched FP."
        )
    }
    if score_arms_present:
        target_recall = min(
            rates_by_arm[a]["recall"]
            for a in score_arms_present
            if a in rates_by_arm and rates_by_arm[a].get("recall") is not None
        )
        for a in score_arms_present:
            recall_matched[a] = recall_matched_fp(
                gold_scored[f"{a}_score"].dropna().astype(float).tolist(),
                neg_scored[f"{a}_score"].dropna().astype(float).tolist(),
                target_recall,
            )
    metrics["recall_matched"] = recall_matched

    # DEFECT 3 (anchor patterns): the actual regex fired per anchor arm, so a
    # period/type mismatch (e.g. a 17c phrase on 18c text) is visible.
    metrics["anchor_patterns"] = {
        "substring_wording": api["token_re"].pattern,
        "substring_scheme": scheme_search_phrase(api["scheme"]),
    }

    if args.json:
        print(json.dumps(metrics, indent=2, ensure_ascii=False, default=str))
    else:
        print(format_summary(metrics))

    if not args.no_write:
        key = (str(args.type), str(meta["sampling_mode"]))
        scored_rows = scored.to_dict(orient="records")
        for row in scored_rows:
            row["type"] = args.type
            row["sampling_mode"] = str(meta["sampling_mode"])

        metrics_records = merge_runs(
            "formula_retrieval_arms_metrics", [metrics], key=key, fresh=args.fresh
        )
        scores_records = merge_runs(
            "formula_retrieval_arms_scores", scored_rows, key=key, fresh=args.fresh
        )

        save_semi_structured(
            metrics_records,
            logical_name="formula_retrieval_arms_metrics",
            script=__file__,
            description=(
                f"STEPT1q {args.type}: per-arm recall/FP + span agreement on "
                "clean post-re-pin stratified gold"
            ),
            parent_sources=parents,
        )
        save_semi_structured(
            scores_records,
            logical_name="formula_retrieval_arms_scores",
            script=__file__,
            description=(
                f"STEPT1q {args.type}: per-row arm fire flags + token spans"
            ),
            parent_sources=parents,
        )
        print(
            "wrote formula_retrieval_arms_metrics / formula_retrieval_arms_scores "
            f"({len(scored_rows)} rows this run, {len(scores_records)} rows "
            "accumulated total)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
