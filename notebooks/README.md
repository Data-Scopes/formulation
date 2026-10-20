# Notebooks

Ad-hoc explore-phase work (phase 1 in `data_manifest.toml`).

- Keep `.ipynb` files here; do not commit large exports beside them.
- Pipeline outputs from notebooks → `save_semi_structured` / `save_parquet` with a `[datasets.*]` entry (scratch tier, or `./output` via `data_manifest.local.toml` when the scratch drive is unplugged).
- See `docs/DATA.md` for tier and phase rules.
