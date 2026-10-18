# STEPL1 — Missive-receipt labelled table

**Goal:** Freeze a provenanced labelled table of missive/brief receipts with *geen resolutie* (positives) plus a 10× overig sample.  
**Done when:** `missive_receipt_labelled` is registered and written via `data_io`; `aanstelling_selected` ids are excluded from positives; `uv run python -m data_io.check` is clean; pytest smoke passes.

## Prerequisites

STEPL0. Read [`plans/milestones/L1-missive-receipt-retrieval.md`](../milestones/L1-missive-receipt-retrieval.md). Reuse `resolutions_flat`, `missive_receipt_seeds`, `aanstelling_selected`. Do **not** train TF-IDF (STEPL2) or mix Track S / formula scripts in this session.

## You do

Register + tests (agent):

```bash
uv run python -m data_io.check
uv run pytest tests/test_missive_receipt_join.py -q
```

Build labelled table (user terminal; start with STEPL0 year):

```bash
uv run python scripts/join_missive_receipt_labels.py --year-min 1780 --year-max 1780
uv run python -m data_io.check
```

Widen later with the same script (`--year-min 1705 --year-max 1795`) once 1780 labels look sane.

## Cursor guides

- Package: `formulation/missive_receipt.py`. Script: `scripts/join_missive_receipt_labels.py`.
- Positives = open+close cue both-hits on `resolutions_flat` in the year window, **minus** `aanstelling_selected` ids, **plus** hand seeds (corpus match when possible; otherwise `hand_seed:{i}` text rows).
- Overig = reproducible 10× sample (`random_state=42`) in the same year window, excluding positive ids (aanstellingen may appear in overig as hard negatives).
- Labels: `missive_receipt` / `overig`. Keep archival flat fields; scoring text is `resolutions_text`.
- Do not invent resolution text. Do not run STEPL2 in this session.

## Next step

STEPL2 — char `char_wb` 3–5 TF-IDF + LR holdout on `missive_receipt_labelled` (mirror STEPR2).
