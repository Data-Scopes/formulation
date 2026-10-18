# STEPS1b — Calibrate TF-IDF window threshold

**Goal:** Freeze (or raise) the STEPS1 cosine cut using span metrics + window score distribution, so provincial *ter Vergaderinge* neighbours drop while true `IS ter Vergaderinge geleesen de Requeste` openings remain.  
**Done when:** a `docs/DECISIONS.md` entry records the frozen threshold (and optional peak-dedup rule); metrics note updated; no template gap / proposer extraction in this session.

## Prerequisites

STEPS0–4 judged (framework + stop). Read STEPS3 `formula_boundary_span_metrics` / spans and STEPS1 `formula_tfidf_window_metrics`. Do **not** add semantic slots (proposer after *Requeste*) here — deferred until after this cut.

## You do

Inspect (advise; light):

```bash
uv run python - <<'PY'
import pandas as pd
from data_io import load

m = load("formula_tfidf_window_metrics")
print(m[0] if isinstance(m, list) else m)

spans = pd.DataFrame(load("formula_boundary_spans"))
dag = spans[spans.method == "dag"].copy()
dag["span_len"] = dag["local_end"] - dag["local_start"]
print("align>=6", (dag.align_score >= 6).sum(), "/", len(dag))
print("span_len vs tfidf (dag):")
print(dag.groupby(pd.cut(dag.tfidf_score, [0, 0.35, 0.40, 0.45, 0.50, 1.0])).agg(
    n=("id", "count"), align_mean=("align_score", "mean"), len_mean=("span_len", "mean")
))
PY
```

Re-frame with a candidate cut (user terminal):

```bash
uv run python scripts/run_tfidf_window_framing.py --year 1780 --limit 200 --threshold 0.40
# optional: re-run span harvest on the new windows, compare full 6-token rate
uv run python scripts/run_span_harvest.py --from-windows
```

Record the frozen cut:

```bash
uv run python scripts/svz.py decision "STEPS1 freeze cosine threshold" \
  --context "..." --decision "..." --reason "..."
```

## Cursor guides

- Evidence: STEPS3 short spans / low align scores concentrate on STEPS1 neighbours below true openings; raise cut and/or peak-dedup, do not train GysBERT.
- Keep `opening_requeste_18c` (ends at *Requeste*). No proposer / variable-slot template extension in this step.
- 17c templates stay deferred. Do not mix L1 missive labelling into framing scripts.
- Package/script unchanged unless `--threshold` CLI is missing — then add a flag only.

## Next step

Re-bootstrap slot-cloud / re-harvest spans at the frozen cut if the candidate set changes materially; or resume Track L STEPL2. Clear the chat before the next step.
