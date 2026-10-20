#!/usr/bin/env python3
"""Fit char n-gram TF-IDF + LR on aanstelling_labelled; write holdout metrics.

Does not tune on the test split. Does not run GysBERT / e5 / SetFit.
Harvest of the unlabelled remainder is STEPR3.
"""

from __future__ import annotations

from data_io import load, save_parquet, save_semi_structured
from formulation.aanstelling_tfidf import evaluate_holdout


def main() -> None:
    labelled = load("aanstelling_labelled")
    holdout, metrics, _pipeline = evaluate_holdout(labelled)
    holdout_path = save_parquet(
        holdout,
        logical_name="aanstelling_tfidf_holdout",
        parent_sources=["aanstelling_labelled"],
        script=__file__,
    )
    metrics_path = save_semi_structured(
        [metrics],
        logical_name="aanstelling_tfidf_metrics",
        parent_sources=["aanstelling_labelled", "aanstelling_tfidf_holdout"],
        script=__file__,
    )
    recall = metrics["recall"]
    precision = metrics["precision"]
    f1 = metrics["f1"]
    print(f"wrote {holdout_path}")
    print(f"wrote {metrics_path}")
    print(
        f"holdout n_test {metrics['n_test']} "
        f"aanstelling {metrics['n_test_aanstelling']} "
        f"tuned_on_test {metrics['tuned_on_test']}"
    )
    print(f"recall {recall:.6f}")
    print(f"precision {precision:.6f}")
    print(f"f1 {f1:.6f}")
    print("record with:")
    print(f"  uv run python scripts/svz.py metric R1 recall {recall:.6f}")
    print(f"  uv run python scripts/svz.py metric R1 precision {precision:.6f}")
    print(f"  uv run python scripts/svz.py metric R1 f1 {f1:.6f}")


if __name__ == "__main__":
    main()
