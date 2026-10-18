#!/usr/bin/env python3
"""Build missive_receipt_labelled (cue both-hits + seeds + 10× overig).

Excludes aanstelling_selected ids from positives. STEPL2 does the TF-IDF split.
"""

from __future__ import annotations

import argparse

from data_io import load, save_parquet
from formulation.missive_receipt import (
    LABEL_MISSIVE,
    LABEL_OVERIG,
    SOURCE_HAND_SEED,
    build_labelled_table,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--year-min",
        type=int,
        default=1780,
        help="Inclusive year window for cue both-hits and overig (default: 1780)",
    )
    parser.add_argument(
        "--year-max",
        type=int,
        default=1780,
        help="Inclusive year window for cue both-hits and overig (default: 1780)",
    )
    parser.add_argument(
        "--no-unmatched-seeds",
        action="store_true",
        help="Drop hand seeds that do not match any resolutions_flat text",
    )
    args = parser.parse_args()

    flat = load("resolutions_flat")
    seeds = load("missive_receipt_seeds")
    selected = load("aanstelling_selected")
    exclude_ids = selected["id"].astype(str).tolist()

    labelled = build_labelled_table(
        flat,
        seeds,
        exclude_ids=exclude_ids,
        year_min=args.year_min,
        year_max=args.year_max,
        include_unmatched_seeds=not args.no_unmatched_seeds,
    )
    path = save_parquet(
        labelled,
        logical_name="missive_receipt_labelled",
        parent_sources=[
            "resolutions_flat",
            "missive_receipt_seeds",
            "aanstelling_selected",
        ],
        script=__file__,
    )

    n_pos = int(labelled["label"].eq(LABEL_MISSIVE).sum())
    n_neg = int(labelled["label"].eq(LABEL_OVERIG).sum())
    n_hand = int(
        (
            labelled["label"].eq(LABEL_MISSIVE)
            & labelled["positive_source"]
            .astype(str)
            .str.contains(SOURCE_HAND_SEED, regex=False)
        ).sum()
    )
    print(f"wrote {path}")
    print(
        f"rows {len(labelled)} missive_receipt {n_pos} overig {n_neg} "
        f"hand_seed_source {n_hand} years {args.year_min}-{args.year_max}"
    )


if __name__ == "__main__":
    main()
