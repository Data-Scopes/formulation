"""STEPT1ad prove: overlap-chain + cue + place fold (separate from production fold).

Demonstrates principles before wiring into ``formula_family_fold``. No auto-mint;
never writes ``formula_templates`` / ``human_role``.
"""

from __future__ import annotations

import gzip
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Sequence

from rapidfuzz import fuzz

from formulation.phrases_5gram_profile import normalize_phrase

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PLACE_BANDS = ("opening", "exposition", "decision", "elaboration", "unknown")

DEFAULT_MIN_OVERLAP_N = 500
DEFAULT_MIN_FRAC = 0.7
DEFAULT_SKELETON_TOKEN_SET = 92.0
DEFAULT_SKIM_TOP = 60
DEFAULT_HUB_MIN_DEGREE = 2

# Bootstrap cue seeds (lexicon stays open; hubs may induce more).
# ``geen_resolutie`` before ``waar_op`` so null path wins on dual surfaces.
# Deliberation windows join via overlap edges under ``waar_op`` — no gedelibereert
# cue (STEPT1af: that seed split decision scaffolding).
CUE_BOOTSTRAP: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("geen_resolutie", re.compile(r"\bgeen\s+resolutie\b", re.I)),
    ("ontfangen", re.compile(r"\bontfangen\b", re.I)),
    ("waar_op", re.compile(r"\bwaar\s*op\b|\bwaer\s*op\b", re.I)),
    # Bare ``handen`` is still referral (not attendance).
    ("in_handen", re.compile(r"\b(in\s+)?handen\b", re.I)),
    ("voldoening", re.compile(r"\b(ter\s+)?voldoening\b", re.I)),
    ("ter_advies", re.compile(r"\bter\s+advi[es]+\b", re.I)),
)

# Short continuations are never cardinals (F1b).
SHORT_CONTINUATION: tuple[str, ...] = ("houdende dat", "houdende")

_CARDINAL_RE = re.compile(
    r"\b(een|twee|drie|vier|vijf|zes|zeven|acht|negen|tien|\d+)\b",
    re.I,
)
_BRIEF_RE = re.compile(r"\bbrieven\b", re.I)
_WAAR_OP_RE = re.compile(r"\bwaar\s*op\b|\bwaer\s*op\b", re.I)
_DECISION_CUE_RE = re.compile(
    r"\b(waar\s*op|gedelibereer|goedgevonden|goetgevonden|goedtgevonden|"
    r"verstaan|geconcludeer)\b",
    re.I,
)
_ELAB_RE = re.compile(r"\b(mits\s+deesen|mits\s+desen|diensvolgende)\b", re.I)


# ---------------------------------------------------------------------------
# Place bands
# ---------------------------------------------------------------------------


def place_band(
    rel_mid: float | None,
    phrase_norm: str,
    *,
    cue_id: str | None = None,
) -> str:
    """Map relative mid (+ cue/text context) to a fine place band.

    Fallback when ``rel_mid`` is missing: cue-driven guess, else ``unknown``.
    """
    s = normalize_phrase(phrase_norm)
    cue = cue_id or assign_cue(s)

    if _ELAB_RE.search(s):
        return "elaboration"
    if cue in ("waar_op", "geen_resolutie") or _DECISION_CUE_RE.search(s):
        return "decision"
    if cue == "ontfangen":
        return "opening"
    if cue in ("in_handen", "voldoening", "ter_advies"):
        # Referral / advice often mid-to-late; prefer exposition unless late mid.
        if rel_mid is not None and float(rel_mid) >= 2.0 / 3.0:
            return "elaboration"
        return "exposition"

    if rel_mid is None:
        return "unknown"
    try:
        m = float(rel_mid)
    except (TypeError, ValueError):
        return "unknown"
    if m != m:
        return "unknown"
    if m < 0.20:
        return "opening"
    if m < 0.55:
        return "exposition"
    if m < 0.85:
        return "decision"
    return "elaboration"


# ---------------------------------------------------------------------------
# Cues
# ---------------------------------------------------------------------------


def assign_cue(
    phrase_norm: str,
    *,
    extra_patterns: Sequence[tuple[str, re.Pattern[str]]] = (),
) -> str:
    """First matching bootstrap (+ optional induced) cue; else ``other``."""
    s = normalize_phrase(phrase_norm)
    for cue_id, pat in (*CUE_BOOTSTRAP, *extra_patterns):
        if pat.search(s):
            return cue_id
    return "other"


def is_short_continuation(phrase_norm: str) -> bool:
    s = normalize_phrase(phrase_norm)
    if s in SHORT_CONTINUATION:
        return True
    # Token-length ≤ 3 and starts with houdende
    toks = s.split()
    return bool(toks) and toks[0] == "houdende" and len(toks) <= 3


def bootstrap_cue_ids() -> frozenset[str]:
    return frozenset(c for c, _ in CUE_BOOTSTRAP)


@dataclass
class CueCandidate:
    cue_id: str
    surface: str
    hub_score: float
    degree: int
    phrase_freq: float
    induced: bool = True


def induce_cue_hubs(
    phrases: Sequence[dict[str, Any]],
    edges: Sequence[dict[str, Any]],
    *,
    min_degree: int = DEFAULT_HUB_MIN_DEGREE,
    min_frac: float = DEFAULT_MIN_FRAC,
    min_n: int = DEFAULT_MIN_OVERLAP_N,
) -> list[CueCandidate]:
    """Propose cue hubs from high-degree overlap endpoints not in bootstrap.

    Emits ``cue_candidates`` for NOTES — not templates.
    """
    known = bootstrap_cue_ids()
    by_norm = {normalize_phrase(str(p.get("phrase_norm") or p.get("phrase") or "")): p for p in phrases}
    degree: dict[str, int] = defaultdict(int)
    for e in edges:
        if not _edge_passes(e, min_n=min_n, min_frac=min_frac):
            continue
        a = normalize_phrase(str(e.get("phrase1") or ""))
        b = normalize_phrase(str(e.get("phrase2") or ""))
        if a not in by_norm or b not in by_norm:
            continue
        degree[a] += 1
        degree[b] += 1

    out: list[CueCandidate] = []
    for surface, deg in degree.items():
        if deg < min_degree:
            continue
        if assign_cue(surface) != "other":
            continue
        # Skip short tails
        if is_short_continuation(surface):
            continue
        row = by_norm[surface]
        freq = float(row.get("phrase_freq") or 0)
        # Hub label: first 2–3 content tokens as provisional id
        toks = [t for t in surface.split() if t not in {"de", "den", "het", "een", "van", "en"}]
        if len(toks) < 2:
            continue
        cue_id = "_".join(toks[:3])
        if cue_id in known:
            continue
        out.append(
            CueCandidate(
                cue_id=cue_id,
                surface=surface,
                hub_score=freq * deg,
                degree=deg,
                phrase_freq=freq,
                induced=True,
            )
        )
    out.sort(key=lambda c: (-c.hub_score, c.cue_id))
    return out


# ---------------------------------------------------------------------------
# Edges / straddle
# ---------------------------------------------------------------------------


def _decision_start_p(norm: str) -> bool:
    return bool(_WAAR_OP_RE.match(norm or "") or (norm or "").startswith("waar op"))


def straddle_conflict(a: str, b: str) -> bool:
    """Refuse re-gluing advertentie|waar op harvest straddles."""
    a_n, b_n = normalize_phrase(a), normalize_phrase(b)
    a_adv = "advertentie" in a_n
    b_adv = "advertentie" in b_n
    a_w = _decision_start_p(a_n)
    b_w = _decision_start_p(b_n)
    if (a_adv and not a_w and b_w) or (b_adv and not b_w and a_w):
        return True
    return False


def _edge_passes(
    edge: dict[str, Any],
    *,
    min_n: int = DEFAULT_MIN_OVERLAP_N,
    min_frac: float = DEFAULT_MIN_FRAC,
) -> bool:
    try:
        n = float(edge.get("overlap_freq") or 0)
        f1 = float(edge.get("phrase1_frac") or 0)
        f2 = float(edge.get("phrase2_frac") or 0)
    except (TypeError, ValueError):
        return False
    return n >= min_n and min(f1, f2) >= min_frac


def iter_overlap_edges(
    path: Path | str,
    *,
    min_n: int = DEFAULT_MIN_OVERLAP_N,
    min_frac: float = DEFAULT_MIN_FRAC,
) -> Iterator[dict[str, Any]]:
    """Stream overlap TSV(.gz); yield kept edges only. Do not load whole dump."""
    p = Path(path)
    opener = gzip.open if str(p).endswith(".gz") else open
    with opener(p, "rt", encoding="utf-8", errors="replace") as fh:  # type: ignore[arg-type]
        header = fh.readline()
        cols = [c.strip() for c in header.split("\t")]
        idx = {c: i for i, c in enumerate(cols)}
        need = ("phrase1", "phrase2", "overlap_freq", "phrase1_frac", "phrase2_frac")
        for name in need:
            if name not in idx:
                raise ValueError(f"overlap TSV missing column {name!r}")
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < len(cols):
                continue
            edge = {
                "phrase1": parts[idx["phrase1"]],
                "phrase2": parts[idx["phrase2"]],
                "overlap_freq": parts[idx["overlap_freq"]],
                "phrase1_frac": parts[idx["phrase1_frac"]],
                "phrase2_frac": parts[idx["phrase2_frac"]],
            }
            if _edge_passes(edge, min_n=min_n, min_frac=min_frac):
                yield edge


# ---------------------------------------------------------------------------
# Union-Find
# ---------------------------------------------------------------------------


class _UF:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}
        self.rank: dict[str, int] = {}

    def add(self, x: str) -> None:
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0

    def find(self, x: str) -> str:
        self.add(x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1


@dataclass
class ProveFamily:
    family_id: str
    exemplar: str
    members: list[str]
    cue: str
    place: str
    phrase_freq_max: float
    overlap_edges_used: list[dict[str, Any]] = field(default_factory=list)
    role: str = "family"  # family | continuation | fragment
    part_of: str | None = None
    human_role: None = None  # always empty — prove never sets this
    corpus_n_docs: int | None = None
    corpus_n_hit: int | None = None
    corpus_hit_rate: float | None = None
    corpus_flag: str | None = None
    corpus_examples: list[str] = field(default_factory=list)

    def to_row(self) -> dict[str, Any]:
        return {
            "family_id": self.family_id,
            "exemplar": self.exemplar,
            "members": list(self.members),
            "cue": self.cue,
            "place": self.place,
            "phrase_freq_max": self.phrase_freq_max,
            "n_overlap_edges": len(self.overlap_edges_used),
            "overlap_freq_max": max(
                (float(e.get("overlap_freq") or 0) for e in self.overlap_edges_used),
                default=0.0,
            ),
            "role": self.role,
            "part_of": self.part_of,
            "human_role": self.human_role,
            "corpus_n_docs": self.corpus_n_docs,
            "corpus_n_hit": self.corpus_n_hit,
            "corpus_hit_rate": self.corpus_hit_rate,
            "corpus_flag": self.corpus_flag,
            "corpus_examples": list(self.corpus_examples),
        }


def _phrase_key(norm: str, place: str) -> str:
    """Same surface in different place bands stays a distinct node."""
    return f"{norm}@@{place}"


def _phrase_meta(phrases: Sequence[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for p in phrases:
        norm = normalize_phrase(str(p.get("phrase_norm") or p.get("phrase") or ""))
        if not norm:
            continue
        cue = str(p.get("cue") or assign_cue(norm))
        place = str(p.get("place") or "") or place_band(
            p.get("rel_mid"),
            norm,
            cue_id=cue,
        )
        key = _phrase_key(norm, place)
        # Keep highest-freq row per (norm, place).
        prev = out.get(key)
        freq = float(p.get("phrase_freq") or 0)
        if prev is not None and float(prev["phrase_freq"]) >= freq:
            continue
        out[key] = {
            "key": key,
            "phrase_norm": norm,
            "phrase_freq": freq,
            "cue": cue,
            "place": place,
            "rel_mid": p.get("rel_mid"),
        }
    return out


def _keys_for_norm(meta: dict[str, dict[str, Any]], norm: str) -> list[str]:
    return [k for k, v in meta.items() if v["phrase_norm"] == norm]


def _dominant_cue(member_keys: Sequence[str], meta: dict[str, dict[str, Any]]) -> str:
    """Null wins over waar_op; else waar_op when chain-linked; else highest-freq cue."""
    cues: list[tuple[float, str, str]] = []
    for mk in member_keys:
        info = meta.get(mk) or {}
        norm = str(info.get("phrase_norm") or "")
        cue = str(info.get("cue") or "other")
        if cue == "geen_resolutie" or "geen resolutie" in norm:
            return "geen_resolutie"
        cues.append((float(info.get("phrase_freq") or 0), cue, mk))
    if any(c == "waar_op" for _, c, _ in cues):
        return "waar_op"
    cues.sort(key=lambda t: (-t[0], t[1]))
    for _, c, _ in cues:
        if c != "other":
            return c
    return "other"


def overlap_union(
    phrases: Sequence[dict[str, Any]],
    edges: Sequence[dict[str, Any]],
    *,
    min_n: int = DEFAULT_MIN_OVERLAP_N,
    min_frac: float = DEFAULT_MIN_FRAC,
) -> list[ProveFamily]:
    """Union-Find within place; refuse straddle / cross-place."""
    meta = _phrase_meta(phrases)
    if not meta:
        return []

    uf = _UF()
    for key in meta:
        uf.add(key)

    used_edges: dict[str, list[dict[str, Any]]] = defaultdict(list)
    edge_records: list[tuple[str, str, dict[str, Any]]] = []

    for e in edges:
        if not _edge_passes(e, min_n=min_n, min_frac=min_frac):
            continue
        a_norm = normalize_phrase(str(e.get("phrase1") or ""))
        b_norm = normalize_phrase(str(e.get("phrase2") or ""))
        if straddle_conflict(a_norm, b_norm):
            continue
        a_keys = _keys_for_norm(meta, a_norm)
        b_keys = _keys_for_norm(meta, b_norm)
        for ak in a_keys:
            for bk in b_keys:
                if meta[ak]["place"] != meta[bk]["place"]:
                    continue
                ca, cb = meta[ak]["cue"], meta[bk]["cue"]
                decision_pair = (
                    {ca, cb}
                    <= {
                        "waar_op",
                        "other",
                        "geen_resolutie",
                    }
                    or "waar_op" in (ca, cb)
                    or "geen_resolutie" in (ca, cb)
                )
                if (
                    ca != "other"
                    and cb != "other"
                    and ca != cb
                    and not decision_pair
                    and {ca, cb} & {"ontfangen", "in_handen", "voldoening", "ter_advies"}
                    and ca != cb
                ):
                    continue
                uf.union(ak, bk)
                edge_records.append((ak, bk, dict(e)))

    comps: dict[str, list[str]] = defaultdict(list)
    for key in meta:
        comps[uf.find(key)].append(key)

    for ak, _bk, e in edge_records:
        used_edges[uf.find(ak)].append(e)

    families: list[ProveFamily] = []
    ranked = sorted(
        comps.items(),
        key=lambda kv: -max(meta[m]["phrase_freq"] for m in kv[1]),
    )
    for i, (_root, member_keys) in enumerate(ranked):
        members_sorted = sorted(
            member_keys, key=lambda m: (-meta[m]["phrase_freq"], meta[m]["phrase_norm"])
        )
        head = members_sorted[0]
        exemplar = meta[head]["phrase_norm"]
        member_norms = []
        seen_n: set[str] = set()
        for mk in members_sorted:
            n = meta[mk]["phrase_norm"]
            if n not in seen_n:
                seen_n.add(n)
                member_norms.append(n)
        cue = _dominant_cue(members_sorted, meta)
        place = meta[head]["place"]
        fam = ProveFamily(
            family_id=f"fam_{i:04d}",
            exemplar=exemplar,
            members=member_norms,
            cue=cue,
            place=place,
            phrase_freq_max=float(meta[head]["phrase_freq"]),
            overlap_edges_used=list(used_edges.get(_root, [])),
        )
        families.append(fam)
    return families


# ---------------------------------------------------------------------------
# Paradigm / skeleton
# ---------------------------------------------------------------------------


def paradigm_skeleton(phrase_norm: str) -> str:
    """Mask cardinals + same-noun plural (brief/brieven); keep missive ≠ brief."""
    s = normalize_phrase(phrase_norm)
    s = _CARDINAL_RE.sub("NUM", s)
    s = _BRIEF_RE.sub("brief", s)
    return re.sub(r"\s+", " ", s).strip()


def skeletons_match(a: str, b: str, *, min_token_set: float = DEFAULT_SKELETON_TOKEN_SET) -> bool:
    sa, sb = paradigm_skeleton(a), paradigm_skeleton(b)
    if sa == sb:
        return True
    return float(fuzz.token_set_ratio(sa, sb)) >= min_token_set


def paradigm_merge_families(
    families: Sequence[ProveFamily],
    *,
    min_token_set: float = DEFAULT_SKELETON_TOKEN_SET,
) -> list[ProveFamily]:
    """Merge families that share cue+place and matching skeletons (no edge required)."""
    if not families:
        return []
    uf = _UF()
    ids = [f.family_id for f in families]
    by_id = {f.family_id: f for f in families}
    for fid in ids:
        uf.add(fid)
    for i, a in enumerate(families):
        for b in families[i + 1 :]:
            if a.cue != b.cue or a.place != b.place:
                continue
            if a.cue == "other":
                continue
            if skeletons_match(a.exemplar, b.exemplar, min_token_set=min_token_set):
                uf.union(a.family_id, b.family_id)

    groups: dict[str, list[ProveFamily]] = defaultdict(list)
    for fid in ids:
        groups[uf.find(fid)].append(by_id[fid])

    out: list[ProveFamily] = []
    for i, (_r, group) in enumerate(
        sorted(groups.items(), key=lambda kv: -max(f.phrase_freq_max for f in kv[1]))
    ):
        group_sorted = sorted(group, key=lambda f: (-f.phrase_freq_max, f.exemplar))
        head = group_sorted[0]
        members: list[str] = []
        edges: list[dict[str, Any]] = []
        seen: set[str] = set()
        for f in group_sorted:
            for m in f.members:
                if m not in seen:
                    seen.add(m)
                    members.append(m)
            edges.extend(f.overlap_edges_used)
        members.sort(
            key=lambda m: (
                -next(
                    (g.phrase_freq_max for g in group_sorted if m in g.members),
                    0.0,
                ),
                m,
            )
        )
        out.append(
            ProveFamily(
                family_id=f"fam_{i:04d}",
                exemplar=head.exemplar,
                members=members,
                cue=head.cue,
                place=head.place,
                phrase_freq_max=head.phrase_freq_max,
                overlap_edges_used=edges,
                role=head.role,
                part_of=head.part_of,
            )
        )
    return out


# ---------------------------------------------------------------------------
# Short tails / F1a–F1b
# ---------------------------------------------------------------------------


def annotate_short_continuations(
    families: Sequence[ProveFamily],
    edges: Sequence[dict[str, Any]] | None = None,
    *,
    min_n: int = 1,
    min_frac: float = 0.0,
) -> list[ProveFamily]:
    """Suppress short tails as cardinals; link part_of when edge evidence is clear."""
    edges = list(edges or [])
    opener_ids = {
        f.family_id: f
        for f in families
        if f.cue == "ontfangen" and not is_short_continuation(f.exemplar)
    }
    # Build norm → family_id for openers
    opener_by_member: dict[str, str] = {}
    for f in opener_ids.values():
        for m in f.members:
            opener_by_member[m] = f.family_id

    out: list[ProveFamily] = []
    for f in families:
        if not any(is_short_continuation(m) for m in f.members) and not is_short_continuation(
            f.exemplar
        ):
            out.append(f)
            continue
        # Short-tail family (or mixed — treat as continuation if exemplar is short)
        part_of: str | None = None
        for e in edges:
            if not _edge_passes(e, min_n=min_n, min_frac=min_frac):
                # Allow low bar for fixture links
                try:
                    n = float(e.get("overlap_freq") or 0)
                except (TypeError, ValueError):
                    n = 0
                if n < min_n:
                    continue
            a = normalize_phrase(str(e.get("phrase1") or ""))
            b = normalize_phrase(str(e.get("phrase2") or ""))
            for short, other in ((a, b), (b, a)):
                if not is_short_continuation(short):
                    continue
                if short not in f.members and short != f.exemplar:
                    continue
                if other in opener_by_member:
                    part_of = opener_by_member[other]
                    break
            if part_of:
                break
        role = "continuation" if part_of else "fragment"
        out.append(
            ProveFamily(
                family_id=f.family_id,
                exemplar=f.exemplar,
                members=list(f.members),
                cue=f.cue,
                place=f.place,
                phrase_freq_max=f.phrase_freq_max,
                overlap_edges_used=list(f.overlap_edges_used),
                role=role,
                part_of=part_of,
                corpus_flag="ok" if part_of else "review",
            )
        )
    return out


# ---------------------------------------------------------------------------
# Cardinal shortlist + corpus presence
# ---------------------------------------------------------------------------


def cardinal_shortlist(
    families: Sequence[ProveFamily],
    *,
    skim_top: int = DEFAULT_SKIM_TOP,
) -> list[ProveFamily]:
    """Manageable skim: exclude continuations/fragments; cap by freq."""
    eligible = [
        f
        for f in families
        if f.role == "family"
        and not is_short_continuation(f.exemplar)
        and f.human_role is None
    ]
    ranked = sorted(eligible, key=lambda f: (-f.phrase_freq_max, f.exemplar))
    return ranked[: max(0, skim_top)]


def substring_presence(
    exemplar: str,
    texts: Sequence[str],
    *,
    ids: Sequence[str] | None = None,
    example_cap: int = 3,
) -> dict[str, Any]:
    """Case-insensitive substring hits. Separate from overlap_freq (merge weight)."""
    needle = normalize_phrase(exemplar)
    n_docs = len(texts)
    hits = 0
    examples: list[str] = []
    id_list = list(ids) if ids is not None else [str(i) for i in range(n_docs)]
    for i, text in enumerate(texts):
        hay = normalize_phrase(str(text or ""))
        if needle and needle in hay:
            hits += 1
            if len(examples) < example_cap:
                examples.append(id_list[i] if i < len(id_list) else str(i))
    rate = (hits / n_docs) if n_docs else 0.0
    flag = "review" if hits == 0 else "ok"
    return {
        "corpus_n_docs": n_docs,
        "corpus_n_hit": hits,
        "corpus_hit_rate": rate,
        "corpus_flag": flag,
        "corpus_examples": examples,
        # Explicit: presence is not overlap_freq
        "presence_field": "corpus_hit_rate",
        "merge_weight_field": "overlap_freq",
    }


def attach_corpus_presence(
    families: Sequence[ProveFamily],
    texts: Sequence[str],
    *,
    ids: Sequence[str] | None = None,
) -> list[ProveFamily]:
    out: list[ProveFamily] = []
    for f in families:
        if f.role != "family":
            out.append(f)
            continue
        stats = substring_presence(f.exemplar, texts, ids=ids)
        out.append(
            ProveFamily(
                family_id=f.family_id,
                exemplar=f.exemplar,
                members=list(f.members),
                cue=f.cue,
                place=f.place,
                phrase_freq_max=f.phrase_freq_max,
                overlap_edges_used=list(f.overlap_edges_used),
                role=f.role,
                part_of=f.part_of,
                corpus_n_docs=int(stats["corpus_n_docs"]),
                corpus_n_hit=int(stats["corpus_n_hit"]),
                corpus_hit_rate=float(stats["corpus_hit_rate"]),
                corpus_flag=str(stats["corpus_flag"]),
                corpus_examples=list(stats["corpus_examples"]),
            )
        )
    return out


def prove_fold(
    phrases: Sequence[dict[str, Any]],
    edges: Sequence[dict[str, Any]],
    *,
    min_n: int = DEFAULT_MIN_OVERLAP_N,
    min_frac: float = DEFAULT_MIN_FRAC,
    texts: Sequence[str] | None = None,
    text_ids: Sequence[str] | None = None,
    skim_top: int = DEFAULT_SKIM_TOP,
    link_min_n: int = 1,
) -> dict[str, Any]:
    """Full prove pipeline on in-memory phrases + edges (+ optional texts)."""
    hubs = induce_cue_hubs(phrases, edges, min_n=min_n, min_frac=min_frac)
    families = overlap_union(phrases, edges, min_n=min_n, min_frac=min_frac)
    families = paradigm_merge_families(families)
    families = annotate_short_continuations(
        families, edges, min_n=link_min_n, min_frac=0.0
    )
    if texts is not None:
        families = attach_corpus_presence(families, texts, ids=text_ids)
    shortlist = cardinal_shortlist(families, skim_top=skim_top)
    return {
        "families": families,
        "shortlist": shortlist,
        "cue_candidates": hubs,
        "n_families": len(families),
        "n_shortlist": len(shortlist),
        "n_cue_candidates": len(hubs),
    }


def collect_edges_for_norms(
    path: Path | str,
    norms: set[str] | Sequence[str],
    *,
    min_n: int = DEFAULT_MIN_OVERLAP_N,
    min_frac: float = DEFAULT_MIN_FRAC,
) -> list[dict[str, Any]]:
    """Stream overlap dump; keep edges whose both ends are in ``norms``."""
    want = {normalize_phrase(n) for n in norms if normalize_phrase(n)}
    if not want:
        return []
    out: list[dict[str, Any]] = []
    for e in iter_overlap_edges(path, min_n=min_n, min_frac=min_frac):
        a = normalize_phrase(str(e.get("phrase1") or ""))
        b = normalize_phrase(str(e.get("phrase2") or ""))
        if a in want and b in want:
            out.append(e)
    return out


# Cue → suggested_role for fold wire-up (human_role still empty).
# STEPT1af: prefer ``role_from_place_and_cue``; this map is a thin cue fallback.
CUE_SUGGESTED_ROLE: dict[str, str] = {
    "ontfangen": "scaffolding_opener",
    "waar_op": "scaffolding_decision",
    "geen_resolutie": "null_decision",
    "in_handen": "scaffolding_decision",
    "voldoening": "carrier",
    "ter_advies": "carrier",
}

# Office/person fillers to mask before exemplar / hinge (STEPT1af).
_GRIFFIER_NAME_RE = re.compile(r"\b(griffier|secretaris)\s+\S+", re.I)
_HEEREN_VAN_NAME_RE = re.compile(
    r"\bheeren\s+van\s+(?!de\b|den\b|der\b|haar\b)(\S+(?:\s+\S+){0,3})",
    re.I,
)


def strip_incidental_names(phrase_norm: str) -> tuple[str, list[str]]:
    """Mask person/office fillers; return (skeleton, stripped_spans).

    Heuristic only — not NER. Skeleton is for hinge/exemplar; originals stay
    as member evidence upstream.
    """
    s = normalize_phrase(phrase_norm)
    stripped: list[str] = []
    if not s:
        return s, stripped

    def _sub_griffier(m: re.Match[str]) -> str:
        stripped.append(m.group(0))
        return f"{m.group(1).lower()} NAME"

    s2 = _GRIFFIER_NAME_RE.sub(_sub_griffier, s)

    def _sub_heeren(m: re.Match[str]) -> str:
        stripped.append(m.group(0))
        return "heeren van NAME"

    s2 = _HEEREN_VAN_NAME_RE.sub(_sub_heeren, s2)
    s2 = re.sub(r"\s+", " ", s2).strip()
    return s2, stripped


def role_from_place_and_cue(
    *,
    place: str,
    cue: str,
    exemplar_norm: str,
    short_tail: bool = False,
) -> str:
    """STEPT1af: assign suggested_role from place + cue after overlap (not before)."""
    if short_tail:
        return "undecided"
    n = normalize_phrase(exemplar_norm)
    cue = cue or "other"
    place = place or "unknown"

    if "geen resolutie" in n or cue == "geen_resolutie":
        return "null_decision"
    if "praeside" in n or "praesentibus" in n:
        return "attendance_noise"
    # handen / referral is decision scaffolding, never attendance
    if "handen" in n or cue == "in_handen":
        return "scaffolding_decision"
    if cue == "ontfangen" or place == "opening":
        return "scaffolding_opener"
    if cue == "waar_op" or place == "decision":
        return "scaffolding_decision"
    if place in ("exposition", "elaboration"):
        return "carrier"
    if cue in CUE_SUGGESTED_ROLE:
        return CUE_SUGGESTED_ROLE[cue]
    return "carrier" if place != "unknown" else "other"
