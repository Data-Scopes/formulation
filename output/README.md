# Local output (scratch tier)

The committed manifest points the **scratch** tier at this directory (`./output`). Pipeline writes still go through `data_io` — not ad-hoc files in `notebooks/`. Contents are gitignored (`output/README.md` is kept).

To send scratch elsewhere (external drive), override `[tiers.scratch]` in `data_manifest.local.toml`.

Legacy orphan files (pre-manifest inbox dumps) can go in `output/_inbox/` for `archive-inventory` / `archive-scan` when `llm_archivist` is installed (`--with-archivist` at bootstrap).
