#!/usr/bin/env python3
"""Fit char n-gram TF-IDF + LR on missive_receipt_labelled; write holdout metrics.

Closed gate: holdout metrics only. Does not tune on the test split.
Does not run GysBERT / e5 / SetFit. Does not harvest the remainder (STEPL3).
"""

from __future__ import annotations

from data_io import load, save_parquet, save_semi_structured
from formulation.missive_receipt_tfidf import evaluate_holdout


def main() -> None:
    labelled = load("missive_receipt_labelled")
    holdout, metrics, _pipeline = evaluate_holdout(labelled)
    holdout_path = save_parquet(
        holdout,
        logical_name="missive_receipt_tfidf_holdout",
        parent_sources=["missive_receipt_labelled"],
        script=__file__,
    )
    metrics_path = save_semi_structured(
        [metrics],
        logical_name="missive_receipt_tfidf_metrics",
        parent_sources=["missive_receipt_labelled", "missive_receipt_tfidf_holdout"],
        script=__file__,
    )
    recall = metrics["recall"]
    precision = metrics["precision"]
    f1 = metrics["f1"]
    print(f"wrote {holdout_path}")
    print(f"wrote {metrics_path}")
    print(
        f"holdout n_test {metrics['n_test']} "
        f"missive_receipt {metrics['n_test_missive_receipt']} "
        f"tuned_on_test {metrics['tuned_on_test']}"
    )
    print(f"recall {recall:.6f}")
    print(f"precision {precision:.6f}")
    print(f"f1 {f1:.6f}")
    print("record with:")
    print(f"  uv run python scripts/svz.py metric L1 recall {recall:.6f}")
    print(f"  uv run python scripts/svz.py metric L1 precision {precision:.6f}")
    print(f"  uv run python scripts/svz.py metric L1 f1 {f1:.6f}")


if __name__ == "__main__":
    main()
