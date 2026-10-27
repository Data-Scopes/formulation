"""STEPT1aa: stream-profile phrases-5_gram dump (freq gate + rare/protected sidecar).

Never load the full ~26.7M-row dump into memory. Pass A = phrase_freq gate
(scaffolding-heavy); protected seeds + optional mid-body low-freq top-N recover
rare carriers Doc B warns the sieve will drop.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Sequence

import pandas as pd

from formulation.formula_type_position import CLOSE_CUT, OPENING_CUT

DEFAULT_MIN_FREQ = 500
DEFAULT_RARE_MIN_FREQ = 50
DEFAULT_RARE_TOP_N = 200
DEFAULT_TOP_N_PER_ROLE = 150
DEFAULT_CHUNKSIZE = 200_000
OPENER_ABS_CUT = 20  # SelectByPhrases legacy
DECISION_ABS_CUT = 120  # frm_frm_frm goedgevonden skim
LEGACY_OPEN_REL = 0.2

# Legacy df_year / classifier_test (include very_small to avoid NaN <50).
LCATS_BINS = [0, 50, 100, 500, 1000, 100_000]
LCATS_LABELS = ["very_small", "small", "medium", "large", "verylarge"]

ROLE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "opener_ish": (
        "ontfangen",
        "requeste",
        "geleesen",
        "gelesen",
        "missive",
        "rapport",
        "voordracht",
        "voorgedragen",
        "advis",
        "advies",
        "gehoord",
        "gehoort",
    ),
    "decision_ish": (
        "goedgevonden",
        "verstaan",
        "in handen",
        "geconcludeert",
        "geconcludeerd",
        "conclusie",
    ),
    "null_decision": ("geen resolutie",),
    "attendance": ("praeside", "praesentibus", "heeren van"),
}

# Named seeds always kept even below MIN_FREQ (blueprint + STEPT1u pockets + decision glue).
DEFAULT_PROTECTED_SEEDS: tuple[str, ...] = (
    "is den selven verwelkomt",
    "geleesen het advis",
    "ter vergaderinge geleesen de requeste",
    "ontfangen een missive",
    "op de requeste",
    "is gehoord het rapport",
    "is gehoort het rapport",
    "voordracht",
    "voorgedragen",
    "in handen van",
    "goedgevonden en verstaan",
    "geen resolutie is gevallen",
    "waar op gedelibereert",
)


_NLP_SENTINEL_RE = re.compile(r"<\s*(start|end)\s*>", re.IGNORECASE)


def normalize_phrase(text: str) -> str:
    """Lowercase + squeeze spaces; drop ``<START>`` / ``<END>`` NLP parse artefacts."""
    s = _NLP_SENTINEL_RE.sub(" ", str(text or ""))
    return re.sub(r"\s+", " ", s.strip().lower())


def lcats_from_doc_len(doc_len: float | int) -> str:
    try:
        n = float(doc_len)
    except (TypeError, ValueError):
        return "unknown"
    if n != n:  # NaN
        return "unknown"
    cat = pd.cut([n], bins=LCATS_BINS, labels=LCATS_LABELS, include_lowest=True)[0]
    if cat is None or (isinstance(cat, float) and cat != cat):
        return "unknown"
    return str(cat)


def zone_from_rel(
    rel_start: float,
    rel_end: float | None = None,
    *,
    opening_cut: float = OPENING_CUT,
    close_cut: float = CLOSE_CUT,
) -> str:
    try:
        a = float(rel_start)
        b = float(rel_end) if rel_end is not None else a
        mid = (a + b) / 2.0
    except (TypeError, ValueError):
        return "unknown"
    if mid != mid:
        return "unknown"
    if mid < opening_cut:
        return "opening"
    if mid < close_cut:
        return "body"
    return "close"


def keyword_role(phrase_norm: str) -> str:
    n = phrase_norm or ""
    # Referral close (in handen / handen van …) is never attendance noise —
    # even when the window also contains ``heeren van`` (delegate name bleed).
    if "handen" in n:
        return "decision_ish"
    for role, keys in ROLE_KEYWORDS.items():
        if any(k in n for k in keys):
            return role
    return "other"


def suggested_role(
    phrase_norm: str,
    *,
    zone: str,
    pos_start: float | None,
    opener_abs: bool,
    opener_rel: bool,
) -> str:
    """Provisional profile hint only — fold recomputes after overlap (STEPT1af).

    Do **not** drive opener from any-hit ``opener_abs`` / ``opener_rel`` (that
    labeled mid-text content as scaffolding_opener). Keywords + majority zone
    only; fold ignores this for typology when overlap-first path runs.
    """
    del pos_start, opener_abs, opener_rel  # kept for call-site compat; unused
    kr = keyword_role(phrase_norm)
    if kr == "attendance":
        return "attendance_noise"
    if kr == "null_decision":
        return "null_decision"
    if kr == "decision_ish":
        return "scaffolding_decision"
    if kr == "opener_ish" or zone == "opening":
        return "scaffolding_opener"
    if zone == "body" and kr == "other":
        return "carrier"
    if zone == "close":
        return "carrier"
    return "other"


def is_protected(phrase_norm: str, seeds: Sequence[str]) -> bool:
    return any(s and s in phrase_norm for s in seeds)


def load_protected_seeds(
    extra: Sequence[str] | None = None,
    *,
    include_opener_candidates: bool = True,
) -> list[str]:
    seeds = [normalize_phrase(s) for s in DEFAULT_PROTECTED_SEEDS]
    if include_opener_candidates:
        try:
            from formulation.opener_candidates import load_queue

            for row in load_queue():
                canonic = row.get("canonic")
                if canonic:
                    # Drop "+" multi-clause markers; keep clause fragments.
                    for part in str(canonic).split("+"):
                        n = normalize_phrase(part)
                        if len(n) >= 6:
                            seeds.append(n)
                cid = normalize_phrase(str(row.get("candidate_id") or ""))
                if cid and len(cid) >= 4:
                    seeds.append(cid.replace("_", " "))
        except Exception:
            pass
    if extra:
        seeds.extend(normalize_phrase(s) for s in extra if s)
    # Unique, longest-first so more specific seeds match first in reports.
    uniq = sorted(set(s for s in seeds if s), key=lambda s: (-len(s), s))
    return uniq


@dataclass
class PhraseAgg:
    phrase: str
    phrase_norm: str
    phrase_freq: int
    n_occ: int = 0
    sum_rel_mid: float = 0.0
    sum_pos_start: float = 0.0
    zone_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    lcats_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    n_opener_abs: int = 0
    n_opener_rel: int = 0
    protected: bool = False
    below_gate: bool = False
    source: str = "high_freq"  # high_freq | protected | rare_midbody

    def add(
        self,
        *,
        rel_mid: float,
        pos_start: float,
        zone: str,
        lcats: str,
        opener_abs: bool,
        opener_rel: bool,
    ) -> None:
        self.n_occ += 1
        self.sum_rel_mid += rel_mid
        self.sum_pos_start += pos_start
        self.zone_counts[zone] += 1
        self.lcats_counts[lcats] += 1
        if opener_abs:
            self.n_opener_abs += 1
        if opener_rel:
            self.n_opener_rel += 1

    def to_record(self) -> dict[str, Any]:
        mean_rel = self.sum_rel_mid / self.n_occ if self.n_occ else None
        mean_pos = self.sum_pos_start / self.n_occ if self.n_occ else None
        top_zone = (
            max(self.zone_counts.items(), key=lambda kv: kv[1])[0]
            if self.zone_counts
            else "unknown"
        )
        top_lcats = (
            max(self.lcats_counts.items(), key=lambda kv: kv[1])[0]
            if self.lcats_counts
            else "unknown"
        )
        opener_abs = self.n_opener_abs > 0
        opener_rel = self.n_opener_rel > 0
        return {
            "phrase": self.phrase,
            "phrase_norm": self.phrase_norm,
            "phrase_freq": int(self.phrase_freq),
            "n_occ_stream": int(self.n_occ),
            "mean_rel_mid": round(mean_rel, 4) if mean_rel is not None else None,
            "mean_pos_start": round(mean_pos, 2) if mean_pos is not None else None,
            "zone": top_zone,
            "zone_counts": {k: int(v) for k, v in sorted(self.zone_counts.items())},
            "lcats": top_lcats,
            "lcats_counts": {k: int(v) for k, v in sorted(self.lcats_counts.items())},
            "opener_abs": bool(opener_abs),
            "opener_rel": bool(opener_rel),
            "keyword_role": keyword_role(self.phrase_norm),
            "suggested_role": suggested_role(
                self.phrase_norm,
                zone=top_zone,
                pos_start=mean_pos,
                opener_abs=opener_abs,
                opener_rel=opener_rel,
            ),
            "protected": bool(self.protected),
            "below_gate": bool(self.below_gate),
            "source": self.source,
        }


def _iter_chunks(
    path: Path,
    *,
    chunksize: int = DEFAULT_CHUNKSIZE,
    with_doc_id: bool = False,
) -> Iterator[pd.DataFrame]:
    usecols = [
        "phrase",
        "doc_len",
        "pos_start",
        "rel_pos_start",
        "pos_end",
        "rel_pos_end",
        "phrase_freq",
        "length_bin",
    ]
    if with_doc_id:
        usecols = ["doc_id", *usecols]
    reader = pd.read_csv(
        path,
        sep="\t",
        compression="gzip" if str(path).endswith(".gz") else None,
        chunksize=chunksize,
        usecols=lambda c: c in usecols,
        dtype={"phrase": "string"},
    )
    for chunk in reader:
        yield chunk


def _touch_agg(
    store: dict[str, PhraseAgg],
    *,
    phrase: str,
    pnorm: str,
    freq: int,
    prot: bool,
    below: bool,
    source: str,
    n_occ: int,
    sum_rel_mid: float,
    sum_pos_start: float,
    zone_counts: dict[str, int],
    lcats_counts: dict[str, int],
    n_opener_abs: int,
    n_opener_rel: int,
) -> None:
    agg = store.get(pnorm)
    if agg is None:
        agg = PhraseAgg(
            phrase=phrase,
            phrase_norm=pnorm,
            phrase_freq=freq,
            protected=prot,
            below_gate=below,
            source=source,
        )
        store[pnorm] = agg
    else:
        agg.phrase_freq = max(agg.phrase_freq, freq)
        if prot:
            agg.protected = True
    agg.n_occ += int(n_occ)
    agg.sum_rel_mid += float(sum_rel_mid)
    agg.sum_pos_start += float(sum_pos_start)
    for z, c in zone_counts.items():
        agg.zone_counts[z] += int(c)
    for lc, c in lcats_counts.items():
        agg.lcats_counts[lc] += int(c)
    agg.n_opener_abs += int(n_opener_abs)
    agg.n_opener_rel += int(n_opener_rel)


def _protected_mask(norms: pd.Series, seeds_norm: Sequence[str]) -> pd.Series:
    mask = pd.Series(False, index=norms.index)
    for s in seeds_norm:
        if s:
            mask = mask | norms.str.contains(re.escape(s), regex=True, na=False)
    return mask


def profile_phrases_stream(
    path: Path | str,
    *,
    min_freq: int = DEFAULT_MIN_FREQ,
    rare_min_freq: int = DEFAULT_RARE_MIN_FREQ,
    rare_top_n: int = DEFAULT_RARE_TOP_N,
    chunksize: int = DEFAULT_CHUNKSIZE,
    protected_seeds: Sequence[str] | None = None,
    max_rows: int | None = None,
    year_substr: str | None = None,
) -> dict[str, Any]:
    """Stream the dump; return high_freq rows, rare sidecar, and metrics."""
    path = Path(path)
    seeds = list(protected_seeds) if protected_seeds is not None else load_protected_seeds()
    seeds_norm = [normalize_phrase(s) for s in seeds]

    high: dict[str, PhraseAgg] = {}
    rare_body: dict[str, PhraseAgg] = {}
    protected_below: dict[str, PhraseAgg] = {}

    rows_scanned = 0
    rows_high = 0
    rows_protected_hit = 0
    rows_rare_cand = 0

    for chunk in _iter_chunks(
        path, chunksize=chunksize, with_doc_id=bool(year_substr)
    ):
        if year_substr and "doc_id" in chunk.columns:
            chunk = chunk.loc[
                chunk["doc_id"].astype(str).str.contains(year_substr, na=False)
            ]
        if chunk.empty:
            continue

        if max_rows is not None and rows_scanned >= max_rows:
            break
        if max_rows is not None and rows_scanned + len(chunk) > max_rows:
            chunk = chunk.iloc[: max(0, max_rows - rows_scanned)]
        rows_scanned += len(chunk)
        if chunk.empty:
            break

        chunk = chunk.copy()
        chunk["phrase_freq"] = (
            pd.to_numeric(chunk["phrase_freq"], errors="coerce").fillna(0).astype(int)
        )
        chunk["doc_len"] = pd.to_numeric(chunk["doc_len"], errors="coerce")
        chunk["pos_start"] = pd.to_numeric(chunk["pos_start"], errors="coerce").fillna(
            -1
        )
        chunk["rel_pos_start"] = pd.to_numeric(
            chunk["rel_pos_start"], errors="coerce"
        ).fillna(0.0)
        chunk["rel_pos_end"] = pd.to_numeric(
            chunk["rel_pos_end"], errors="coerce"
        ).fillna(chunk["rel_pos_start"])
        chunk["phrase"] = chunk["phrase"].astype(str)
        chunk = chunk.loc[chunk["phrase"].ne("") & chunk["phrase"].ne("nan")]
        if chunk.empty:
            continue

        chunk["phrase_norm"] = (
            chunk["phrase"]
            .str.strip()
            .str.lower()
            .str.replace(r"\s+", " ", regex=True)
        )
        chunk["rel_mid"] = (chunk["rel_pos_start"] + chunk["rel_pos_end"]) / 2.0
        chunk["zone"] = "body"
        chunk.loc[chunk["rel_mid"] < OPENING_CUT, "zone"] = "opening"
        chunk.loc[chunk["rel_mid"] >= CLOSE_CUT, "zone"] = "close"
        chunk["lcats"] = pd.cut(
            chunk["doc_len"],
            bins=LCATS_BINS,
            labels=LCATS_LABELS,
            include_lowest=True,
        ).astype(str)
        chunk.loc[chunk["lcats"].isin(["nan", "NaN", "None"]), "lcats"] = "unknown"
        chunk["opener_abs"] = (chunk["pos_start"] >= 0) & (
            chunk["pos_start"] < OPENER_ABS_CUT
        )
        chunk["opener_rel"] = chunk["rel_pos_start"] < LEGACY_OPEN_REL
        chunk["protected"] = _protected_mask(chunk["phrase_norm"], seeds_norm)

        keep_high = chunk["phrase_freq"] >= min_freq
        keep_prot = (~keep_high) & chunk["protected"]
        opener_pat = "|".join(re.escape(k) for k in ROLE_KEYWORDS["opener_ish"])
        att_pat = "|".join(re.escape(k) for k in ROLE_KEYWORDS["attendance"])
        keep_rare = (
            (~keep_high)
            & (~chunk["protected"])
            & (chunk["phrase_freq"] >= rare_min_freq)
            & (chunk["zone"] == "body")
            & (~chunk["phrase_norm"].str.contains(opener_pat, regex=True, na=False))
            & (~chunk["phrase_norm"].str.contains(att_pat, regex=True, na=False))
        )

        rows_high += int(keep_high.sum())
        rows_protected_hit += int(keep_prot.sum())
        rows_rare_cand += int(keep_rare.sum())

        for mask, store, source, below in (
            (keep_high, high, "high_freq", False),
            (keep_prot, protected_below, "protected", True),
            (keep_rare, rare_body, "rare_midbody", True),
        ):
            sub = chunk.loc[mask]
            if sub.empty:
                continue
            for pnorm, grp in sub.groupby("phrase_norm", sort=False):
                row0 = grp.iloc[0]
                zc = grp["zone"].value_counts().to_dict()
                lc = grp["lcats"].value_counts().to_dict()
                _touch_agg(
                    store,
                    phrase=str(row0["phrase"]),
                    pnorm=str(pnorm),
                    freq=int(grp["phrase_freq"].max()),
                    prot=bool(grp["protected"].any()),
                    below=below,
                    source=source,
                    n_occ=len(grp),
                    sum_rel_mid=float(grp["rel_mid"].sum()),
                    sum_pos_start=float(grp["pos_start"].sum()),
                    zone_counts={str(k): int(v) for k, v in zc.items()},
                    lcats_counts={str(k): int(v) for k, v in lc.items()},
                    n_opener_abs=int(grp["opener_abs"].sum()),
                    n_opener_rel=int(grp["opener_rel"].sum()),
                )

    high_rows = sorted(
        (a.to_record() for a in high.values()),
        key=lambda r: (-int(r["phrase_freq"]), r["phrase_norm"]),
    )

    rare_sorted = sorted(
        rare_body.values(),
        key=lambda a: (-a.phrase_freq, a.phrase_norm),
    )[:rare_top_n]
    sidecar: list[dict[str, Any]] = []
    seen: set[str] = set()
    for a in protected_below.values():
        sidecar.append(a.to_record())
        seen.add(a.phrase_norm)
    for a in rare_sorted:
        if a.phrase_norm in seen or a.phrase_norm in high:
            continue
        sidecar.append(a.to_record())
        seen.add(a.phrase_norm)
    sidecar.sort(key=lambda r: (-int(r["phrase_freq"]), r["phrase_norm"]))

    by_role: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in high_rows:
        by_role[str(r["suggested_role"])].append(r)
    top_by_role = {
        role: rows[:DEFAULT_TOP_N_PER_ROLE] for role, rows in sorted(by_role.items())
    }

    metrics = {
        "step": "STEPT1aa",
        "source_path": str(path),
        "min_freq": int(min_freq),
        "rare_min_freq": int(rare_min_freq),
        "rare_top_n": int(rare_top_n),
        "rows_scanned": int(rows_scanned),
        "rows_high_occ": int(rows_high),
        "rows_protected_hit": int(rows_protected_hit),
        "rows_rare_midbody_cand": int(rows_rare_cand),
        "n_high_freq": len(high_rows),
        "n_protected_below_gate": len(protected_below),
        "n_rare_sidecar": len(sidecar),
        "n_protected_seeds": len(seeds_norm),
        "year_substr": year_substr,
        "max_rows": max_rows,
        "zone_cuts": {
            "opening_lt": OPENING_CUT,
            "close_ge": CLOSE_CUT,
            "opener_abs_lt": OPENER_ABS_CUT,
            "opener_rel_lt": LEGACY_OPEN_REL,
            "decision_abs_lte": DECISION_ABS_CUT,
        },
        "lcats_bins": LCATS_BINS,
        "lcats_labels": LCATS_LABELS,
        "note": (
            "Pass A phrase_freq gate is scaffolding-biased; "
            "rare/protected sidecar recovers named seeds + mid-body low-freq top-N. "
            "No fold / no auto-mint."
        ),
        "top_by_suggested_role_n": {k: len(v) for k, v in top_by_role.items()},
    }
    return {
        "metrics": metrics,
        "high_freq": high_rows,
        "rare_sidecar": sidecar,
        "top_by_role": top_by_role,
    }


def fixture_profile() -> dict[str, Any]:
    """Tiny in-memory profile for tests (no SSD dump)."""
    rows = [
        {
            "phrase": "Ontfangen een Missive van den",
            "doc_len": 80,
            "pos_start": 0,
            "rel_pos_start": 0.0,
            "rel_pos_end": 0.1,
            "phrase_freq": 90000,
        },
        {
            "phrase": "zynde is goedgevonden en verstaan",
            "doc_len": 200,
            "pos_start": 150,
            "rel_pos_start": 0.75,
            "rel_pos_end": 0.85,
            "phrase_freq": 60000,
        },
        {
            "phrase": "geen resolutie is gevallen",
            "doc_len": 60,
            "pos_start": 40,
            "rel_pos_start": 0.7,
            "rel_pos_end": 0.9,
            "phrase_freq": 80000,
        },
        {
            "phrase": "IS gehoord het rapport van",
            "doc_len": 120,
            "pos_start": 5,
            "rel_pos_start": 0.05,
            "rel_pos_end": 0.15,
            "phrase_freq": 40,  # below gate but protected
        },
        {
            "phrase": "byzondere mid-body carrier phrase xx",
            "doc_len": 300,
            "pos_start": 140,
            "rel_pos_start": 0.45,
            "rel_pos_end": 0.55,
            "phrase_freq": 80,  # rare mid-body
        },
        {
            "phrase": "Ontfangen een Missive van den Heere",  # nested longer
            "doc_len": 80,
            "pos_start": 0,
            "rel_pos_start": 0.0,
            "rel_pos_end": 0.12,
            "phrase_freq": 49000,
        },
    ]
    # Write temp-less: aggregate manually via PhraseAgg path
    high: dict[str, PhraseAgg] = {}
    rare: dict[str, PhraseAgg] = {}
    prot: dict[str, PhraseAgg] = {}
    seeds = load_protected_seeds(include_opener_candidates=False)
    min_freq = 500
    for r in rows:
        pnorm = normalize_phrase(r["phrase"])
        freq = int(r["phrase_freq"])
        zone = zone_from_rel(r["rel_pos_start"], r["rel_pos_end"])
        lc = lcats_from_doc_len(r["doc_len"])
        ps = float(r["pos_start"])
        opener_abs = ps < OPENER_ABS_CUT
        opener_rel = float(r["rel_pos_start"]) < LEGACY_OPEN_REL
        is_prot = is_protected(pnorm, seeds)
        below = freq < min_freq
        agg = PhraseAgg(
            phrase=r["phrase"],
            phrase_norm=pnorm,
            phrase_freq=freq,
            protected=is_prot,
            below_gate=below,
            source=(
                "high_freq"
                if not below
                else ("protected" if is_prot else "rare_midbody")
            ),
        )
        agg.add(
            rel_mid=(float(r["rel_pos_start"]) + float(r["rel_pos_end"])) / 2,
            pos_start=ps,
            zone=zone,
            lcats=lc,
            opener_abs=opener_abs,
            opener_rel=opener_rel,
        )
        if not below:
            high[pnorm] = agg
        elif is_prot:
            prot[pnorm] = agg
        elif zone == "body":
            rare[pnorm] = agg

    high_rows = [a.to_record() for a in high.values()]
    sidecar = [a.to_record() for a in list(prot.values()) + list(rare.values())]
    return {
        "metrics": {
            "step": "STEPT1aa",
            "fixture": True,
            "min_freq": min_freq,
            "n_high_freq": len(high_rows),
            "n_protected_below_gate": len(prot),
            "n_rare_sidecar": len(sidecar),
            "rows_scanned": len(rows),
        },
        "high_freq": high_rows,
        "rare_sidecar": sidecar,
    }


def write_profile_xlsx(
    path: Path | str,
    *,
    high_freq: Sequence[dict[str, Any]],
    rare_sidecar: Sequence[dict[str, Any]],
    metrics: dict[str, Any],
    top_n: int = 200,
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    high_df = pd.DataFrame(list(high_freq)[:top_n])
    rare_df = pd.DataFrame(list(rare_sidecar)[:top_n])
    meta_df = pd.DataFrame([{"key": k, "value": str(v)} for k, v in metrics.items()])
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        high_df.to_excel(writer, sheet_name="high_freq", index=False)
        rare_df.to_excel(writer, sheet_name="rare_sidecar", index=False)
        meta_df.to_excel(writer, sheet_name="metrics", index=False)
    return path
