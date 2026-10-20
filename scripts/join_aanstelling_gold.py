#!/usr/bin/env python3
"""Join gold aanstelling URNs to resolutions_flat and freeze a labelled table.

Writes ``aanstelling_labelled`` (positives + 10× overig sample) through data_io.
Stratified 80/20 split is STEPR2. No Elasticsearch, no FormulaSearch.
"""

from __future__ import annotations

import pandas as pd

from data_io import load, resolve, save_parquet
from formulation.aanstelling import (
    LABEL_AANSTELLING,
    LABEL_OVERIG,
    RECOVERY_NAIVE,
    build_labelled_table,
)


def main() -> None:
    flat = load("resolutions_flat")
    gold = pd.read_excel(resolve("delegates_resolutie_refs"))
    relocations = load("aanstelling_gold_relocations")
    labelled = build_labelled_table(flat, gold, relocations)
    path = save_parquet(
        labelled,
        logical_name="aanstelling_labelled",
        parent_sources=[
            "resolutions_flat",
            "delegates_resolutie_refs",
            "aanstelling_gold_relocations",
        ],
        script=__file__,
    )
    n_pos = int(labelled["label"].eq(LABEL_AANSTELLING).sum())
    n_neg = int(labelled["label"].eq(LABEL_OVERIG).sum())
    n_reloc = int(
        labelled["label"].eq(LABEL_AANSTELLING)
        & labelled["join_recovery"].ne(RECOVERY_NAIVE)
        & labelled["join_recovery"].ne("")
    )
    print(f"wrote {path}")
    print(f"rows {len(labelled)} aanstelling {n_pos} overig {n_neg} relocated_or_kept {n_reloc}")


if __name__ == "__main__":
    main()
