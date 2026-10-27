"""STEPT1ab/ae/af: fold high-freq (+ rare sidecar) phrases into family candidates.

STEPT1af order: repair → nest → overlap → name-strip → place-based role.
Freq alone does not decide merges. No auto-mint; human_role stays empty.
Inbound profile ``suggested_role`` is ignored for typology.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Sequence

from rapidfuzz import fuzz

from formulation.overlap_cue_prove import (
    DEFAULT_MIN_FRAC,
    DEFAULT_MIN_OVERLAP_N,
    annotate_short_continuations,
    assign_cue,
    induce_cue_hubs,
    is_short_continuation,
    overlap_union,
    paradigm_merge_families,
    place_band,
    role_from_place_and_cue,
    strip_incidental_names,
)
from formulation.phrases_5gram_profile import (
    ROLE_KEYWORDS,
    fixture_profile,
    normalize_phrase,
)

# rapidfuzz.fuzz.ratio is 0–100; keep the same operating point as former 0.88 SequenceMatcher.
DEFAULT_VARIANT_RATIO = 88.0
HUMAN_ROLES = (
    "scaffolding_opener",
    "scaffolding_decision",
    "null_decision",
    "carrier",
    "attendance_noise",
    "other",
    "undecided",
)

# Harvest artefact: split mid-window straddles at decision-start.
# Prefer full ``waar op``; also bare mid-phrase ``waar`` / ``waer`` (truncated 5-grams).
_BOUNDARY_WAAR_OP = re.compile(r"\bwaar\s*op\b|\bwaer\s*op\b", re.IGNORECASE)
_BOUNDARY_WAAR_BARE = re.compile(r"\bwa(?:ar|er)\b", re.IGNORECASE)

# Opposite harvest artefact: one long formula chopped into overlapping windows —
# force one family (nomineeren → visiteeren/examineeren → advis daar op → …).
GLUE_GROUPS: tuple[dict[str, Any], ...] = (
    {
        "id": "nomineer_visiteer_advies",
        "patterns": (
            re.compile(
                r"nomineer.*(visiteer|visiter)|visiteer.*examineer|visiter.*examineer",
                re.I,
            ),
            re.compile(r"examineer.*(liquideer|van alles)", re.I),
            re.compile(r"(selver|selves|selven)?\s*advi[es]+\s+daar\s+op", re.I),
            re.compile(r"uit\s+te\s+breng", re.I),
        ),
    },
)


def repair_harvest_segments(phrase_norm: str) -> list[str]:
    """Repair positional straddle inside one harvest window.

    Split when ``waar op`` (or bare mid-phrase ``waar``) sits after a prefix —
    e.g. ``advertentie waar op…`` / ``…advertentie WAAR`` → prefix + decision.
    No split if the window already starts at the decision formula.
    """
    s = normalize_phrase(phrase_norm)
    if not s:
        return []
    m = _BOUNDARY_WAAR_OP.search(s)
    if m is None:
        m = _BOUNDARY_WAAR_BARE.search(s)
        # Bare ``waar`` only when mid-phrase (truncated 5-gram ending at WAAR).
        if m is not None and m.start() == 0:
            return [s]
    if not m:
        return [s]
    if m.start() == 0:
        return [s]
    prefix = s[: m.start()].strip()
    suffix = s[m.start() :].strip()
    parts: list[str] = []
    if len(prefix.split()) >= 1:
        parts.append(prefix)
    if suffix:
        parts.append(suffix)
    return parts or [s]


def glue_group_id(phrase_norm: str) -> str | None:
    s = normalize_phrase(phrase_norm)
    for group in GLUE_GROUPS:
        if any(p.search(s) for p in group["patterns"]):
            return str(group["id"])
    return None


def _hinge_bucket(phrase_norm: str) -> str:
    glue = glue_group_id(phrase_norm)
    if glue:
        return f"glue:{glue}"
    n = phrase_norm or ""
    # Null-decision formula often opens with waar op ("WAAR op geen resolutie…");
    # keep those sliding windows with the null-decision family, not bare decision-start.
    if "geen resolutie" in n:
        return "null_decision:geen resolutie"
    # Bare decision-start (waar op without null path); do not merge with advertentie.
    if _BOUNDARY_WAAR_OP.search(n):
        return "decision_start:waar_op"
    # Referral ``handen`` / ``in handen`` — never attendance:heeren van (name bleed).
    if "handen" in n:
        return "decision_ish:handen"
    for role, keys in ROLE_KEYWORDS.items():
        for k in keys:
            if k in n:
                return f"{role}:{k}"
    toks = n.split()
    if len(toks) >= 2:
        return "tok:" + "_".join(toks[:2])
    return "tok:" + (toks[0] if toks else "empty")


def _is_nested(child: str, parent: str) -> bool:
    """True if child is a proper contiguous substring of parent (token-aware-ish)."""
    if child == parent or len(child) >= len(parent):
        return False
    if child not in parent:
        return False
    # Prefer token-boundary-ish: spaces or ends.
    idx = parent.find(child)
    before_ok = idx == 0 or parent[idx - 1] == " "
    after = idx + len(child)
    after_ok = after == len(parent) or parent[after] == " "
    return before_ok and after_ok


def nest_collapse(rows: Sequence[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Collapse pure substring children under a longer parent (Pass B).

    Children are not independent family seeds, but stay attached on the parent
    as ``_nested_members`` so they remain visible as variants.
    """
    sorted_rows = sorted(
        rows,
        key=lambda r: (-len(str(r.get("phrase_norm") or "")), -int(r.get("phrase_freq") or 0)),
    )
    # Work on copies so we can attach nested members safely.
    copies = [dict(r) for r in sorted_rows]
    for c in copies:
        c.setdefault("_nested_members", [])
    norms = [str(r.get("phrase_norm") or "") for r in copies]
    kept: list[dict[str, Any]] = []
    nested_n = 0
    for i, row in enumerate(copies):
        child = norms[i]
        parent_hit = None
        parent_idx = None
        for j in range(i):
            # Only nest under a still-kept parent (not under another dropped child).
            if copies[j] is None:
                continue
            parent = norms[j]
            if _is_nested(child, parent):
                parent_hit = copies[j]
                parent_idx = j
                break
        if parent_hit is not None and parent_idx is not None:
            nested_n += 1
            parent_hit["_nested_members"].append(row)
            copies[i] = None  # type: ignore[assignment]
            continue
        kept.append(row)
    return kept, nested_n


def _tokens(phrase_norm: str) -> list[str]:
    # phrase_norm should already have <START>/<END> stripped via normalize_phrase.
    return [t for t in str(phrase_norm or "").split() if t]


def _contiguous_token_overlap(a: str, b: str) -> int:
    """Longest contiguous shared token span (sliding 5-gram windows share n-1)."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0
    best = 0
    # Check each ta[i:] prefix length against tb as contiguous match.
    for i in range(len(ta)):
        for j in range(len(tb)):
            k = 0
            while (
                i + k < len(ta)
                and j + k < len(tb)
                and ta[i + k] == tb[j + k]
            ):
                k += 1
            if k > best:
                best = k
    return best


# 5-gram dump: adjacent windows of one formula share 4 tokens.
MIN_SHARED_TOKEN_SPAN = 4


def _decision_start_p(norm: str) -> bool:
    return bool(_BOUNDARY_WAAR_OP.match(norm or "") or (norm or "").startswith("waar op"))


def _straddle_conflict(a: str, b: str) -> bool:
    """True if merge would re-glue a positional harvest straddle (e.g. advertentie|waar op)."""
    a_adv = "advertentie" in a
    b_adv = "advertentie" in b
    a_w = _decision_start_p(a)
    b_w = _decision_start_p(b)
    if (a_adv and not a_w and b_w) or (b_adv and not b_w and a_w):
        return True
    return False


def _similar(a: str, b: str, *, ratio: float = DEFAULT_VARIANT_RATIO) -> bool:
    """Variant test: edit ratio, token-set ratio, or long shared token span.

    Plain ``fuzz.ratio`` misses sliding-window 5-grams of the same formula.
    Refuse only merges that re-attach a positional straddle (advertentie|waar op).
    Same-formula windows that merely share ``geen resolutie`` still merge.
    """
    if a == b:
        return True
    if _straddle_conflict(a, b):
        return False
    ga, gb = glue_group_id(a), glue_group_id(b)
    if ga and gb and ga != gb:
        return False
    # Same glue group = chopped overlapping windows of one long formula.
    if ga and ga == gb:
        return True
    if abs(len(a) - len(b)) > max(12, int(0.45 * max(len(a), len(b)))):
        if _contiguous_token_overlap(a, b) < MIN_SHARED_TOKEN_SPAN:
            return False
        return True
    if float(fuzz.ratio(a, b)) >= float(ratio):
        return True
    if float(fuzz.token_set_ratio(a, b)) >= float(ratio):
        return True
    return _contiguous_token_overlap(a, b) >= MIN_SHARED_TOKEN_SPAN


def _zone_compatible(a: dict[str, Any], b: dict[str, Any]) -> bool:
    za, zb = str(a.get("zone") or ""), str(b.get("zone") or "")
    if not za or not zb or za == "unknown" or zb == "unknown":
        return True
    return za == zb


def _row_hinge(row: dict[str, Any]) -> str:
    force = row.get("hinge_force")
    if force:
        return str(force)
    return _hinge_bucket(str(row.get("phrase_norm") or ""))


def apply_overlap_cue_pass(
    rows: Sequence[dict[str, Any]],
    edges: Sequence[dict[str, Any]],
    *,
    min_n: int = DEFAULT_MIN_OVERLAP_N,
    min_frac: float = DEFAULT_MIN_FRAC,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Collapse via overlap-union + paradigm + F1b; name-strip; no type yet.

    STEPT1af: tags place/cue/hinge only — ``suggested_role`` assigned later from place.
    """
    phrases: list[dict[str, Any]] = []
    by_norm: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        rec = dict(r)
        norm = normalize_phrase(str(rec.get("phrase_norm") or rec.get("phrase") or ""))
        if not norm:
            continue
        rec["phrase_norm"] = norm
        rec.pop("suggested_role", None)  # ignore profile typology
        by_norm[norm].append(rec)
        zone = str(rec.get("zone") or "")
        place = str(rec.get("place") or "") or place_band(
            rec.get("rel_mid") or rec.get("mean_rel_mid"),
            norm,
            cue_id=assign_cue(norm),
        )
        if zone == "opening" and place not in ("opening", "unknown"):
            place = "opening"
        elif zone == "close" and place == "opening":
            place = "decision"
        phrases.append(
            {
                "phrase_norm": norm,
                "phrase_freq": int(rec.get("phrase_freq") or 0),
                "place": place,
                "rel_mid": rec.get("rel_mid") or rec.get("mean_rel_mid"),
            }
        )

    hubs = induce_cue_hubs(phrases, edges, min_n=min_n, min_frac=min_frac)
    prove_fams = overlap_union(phrases, edges, min_n=min_n, min_frac=min_frac)
    prove_fams = paradigm_merge_families(prove_fams)
    prove_fams = annotate_short_continuations(
        prove_fams, edges, min_n=1, min_frac=0.0
    )

    fam_by_norm: dict[str, Any] = {}
    for fam in prove_fams:
        for m in fam.members:
            fam_by_norm[m] = fam

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for norm, recs in by_norm.items():
        recs_sorted = sorted(
            recs,
            key=lambda r: (-int(r.get("phrase_freq") or 0), str(r.get("phrase_norm") or "")),
        )
        head = dict(recs_sorted[0])
        same_norm_extras = recs_sorted[1:]
        if same_norm_extras:
            nested = list(head.get("_nested_members") or [])
            nested.extend(same_norm_extras)
            head["_nested_members"] = nested
        fam = fam_by_norm.get(norm)
        key = fam.family_id if fam is not None else f"solo:{norm}"
        groups[key].append(head)

    collapsed: list[dict[str, Any]] = []
    n_overlap_merges = 0
    n_short_tails = 0
    n_name_stripped = 0
    for _key, members in groups.items():
        members = sorted(
            members,
            key=lambda r: (-int(r.get("phrase_freq") or 0), str(r.get("phrase_norm") or "")),
        )
        head = dict(members[0])
        raw_norm = str(head.get("phrase_norm") or "")
        skel, stripped = strip_incidental_names(raw_norm)
        if stripped:
            n_name_stripped += 1
            head["phrase_surface"] = head.get("phrase") or raw_norm
            head["phrase_norm"] = skel
            head["name_stripped"] = stripped
            # Prefer skeleton as display exemplar when names were masked
            head["phrase"] = skel
        fam = fam_by_norm.get(raw_norm) or fam_by_norm.get(skel)
        if fam is not None:
            head["overlap_cue"] = fam.cue
            head["overlap_place"] = fam.place
            head["overlap_role"] = fam.role
            head["part_of"] = fam.part_of
            # Null hinge wins over waar_op
            if fam.cue == "geen_resolutie" or "geen resolutie" in skel:
                head["hinge_force"] = "cue:geen_resolutie"
            elif fam.cue != "other":
                head["hinge_force"] = f"cue:{fam.cue}"
            if fam.role in ("continuation", "fragment") or is_short_continuation(skel):
                head["overlap_short_tail"] = True
                n_short_tails += 1
        else:
            cue = assign_cue(skel)
            place = place_band(
                head.get("rel_mid") or head.get("mean_rel_mid"),
                skel,
                cue_id=cue,
            )
            head["overlap_cue"] = cue
            head["overlap_place"] = place
            if cue != "other":
                head["hinge_force"] = f"cue:{cue}"
        extras = members[1:]
        if extras:
            n_overlap_merges += len(extras)
            nested = list(head.get("_nested_members") or [])
            for ex in extras:
                nested.append(ex)
                nested.extend(list(ex.get("_nested_members") or []))
            head["_nested_members"] = nested
        collapsed.append(head)

    meta = {
        "n_overlap_edges_in": len(edges),
        "n_overlap_prove_families": len(prove_fams),
        "n_overlap_merges": int(n_overlap_merges),
        "n_overlap_short_tails": int(n_short_tails),
        "n_name_stripped": int(n_name_stripped),
        "n_cue_candidates": len(hubs),
        "cue_candidates": [
            {
                "cue_id": h.cue_id,
                "surface": h.surface,
                "hub_score": h.hub_score,
                "degree": h.degree,
            }
            for h in hubs[:40]
        ],
    }
    return collapsed, meta


def variant_fold(
    rows: Sequence[dict[str, Any]],
    *,
    ratio: float = DEFAULT_VARIANT_RATIO,
) -> tuple[list[dict[str, Any]], int]:
    """Group near-duplicate surfaces within hinge buckets (Pass C)."""
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        buckets[_row_hinge(r)].append(dict(r))

    families: list[dict[str, Any]] = []
    merges = 0
    fam_i = 0
    for _bucket, members in sorted(buckets.items(), key=lambda kv: kv[0]):
        members = sorted(
            members,
            key=lambda r: (-int(r.get("phrase_freq") or 0), str(r.get("phrase_norm") or "")),
        )
        clusters: list[list[dict[str, Any]]] = []
        for row in members:
            placed = False
            row_norm = str(row.get("phrase_norm") or "")
            for cluster in clusters:
                head = cluster[0]
                # Independent freq + different zone → do not merge (distinct-type signal).
                if not _zone_compatible(head, row):
                    ha = int(head.get("phrase_freq") or 0)
                    hb = int(row.get("phrase_freq") or 0)
                    if min(ha, hb) >= 0.3 * max(ha, hb, 1):
                        continue
                # Match any member so sliding 5-gram windows chain into one family.
                if any(
                    _similar(
                        str(m.get("phrase_norm") or ""),
                        row_norm,
                        ratio=ratio,
                    )
                    for m in cluster
                ):
                    cluster.append(row)
                    merges += 1
                    placed = True
                    break
            if not placed:
                clusters.append([row])

        for cluster in clusters:
            fam_i += 1
            exemplar = cluster[0]
            # Expand Pass B nested substring children into visible members.
            expanded: list[dict[str, Any]] = []
            seen_norms: set[str] = set()
            for m in cluster:
                for piece in (m, *list(m.get("_nested_members") or [])):
                    pn = str(piece.get("phrase_norm") or "")
                    if pn in seen_norms:
                        continue
                    seen_norms.add(pn)
                    expanded.append(piece)
            member_phrases = [
                {
                    "phrase": m.get("phrase"),
                    "phrase_norm": m.get("phrase_norm"),
                    "phrase_freq": int(m.get("phrase_freq") or 0),
                    "zone": m.get("zone"),
                    "lcats": m.get("lcats"),
                    "source": m.get("source"),
                }
                for m in expanded
            ]
            cluster = expanded  # for zone/lcats tallies below
            zones = [str(m.get("zone") or "unknown") for m in cluster]
            lcats = [str(m.get("lcats") or "unknown") for m in cluster]
            top_zone = max(set(zones), key=zones.count)
            top_lcats = max(set(lcats), key=lcats.count)
            # STEPT1af: leave suggested_role unset until place-based assign
            families.append(
                {
                    "family_id": f"fam_{fam_i:04d}",
                    "exemplar": exemplar.get("phrase"),
                    "exemplar_norm": exemplar.get("phrase_norm"),
                    "phrase_freq_max": int(exemplar.get("phrase_freq") or 0),
                    "n_members": len(cluster),
                    "members": member_phrases,
                    "hinge_bucket": _row_hinge(exemplar),
                    "zone": top_zone,
                    "lcats": top_lcats,
                    "suggested_role": None,
                    "human_role": None,
                    "variant_of": None,
                    "protected_any": any(bool(m.get("protected")) for m in cluster),
                    "sources": sorted(
                        {str(m.get("source") or "") for m in cluster if m.get("source")}
                    ),
                    "overlap_cue": exemplar.get("overlap_cue"),
                    "overlap_place": exemplar.get("overlap_place"),
                    "overlap_role": exemplar.get("overlap_role"),
                    "part_of": exemplar.get("part_of"),
                    "overlap_short_tail": bool(exemplar.get("overlap_short_tail")),
                    "name_stripped": exemplar.get("name_stripped"),
                }
            )
    families.sort(key=lambda f: (-int(f["phrase_freq_max"]), f["family_id"]))
    # Re-id after sort for stable skim order.
    for i, fam in enumerate(families, start=1):
        fam["family_id"] = f"fam_{i:04d}"
    return families, merges


def _expand_harvest_artefacts(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Repair sliding-window harvest: split at waar/waar op; no type assignment."""
    expanded: list[dict[str, Any]] = []
    for r in rows:
        rec = dict(r)
        full = normalize_phrase(str(rec.get("phrase") or ""))
        rec["phrase_full_norm"] = full
        rec.pop("suggested_role", None)
        segments = repair_harvest_segments(full)
        for seg in segments:
            piece = dict(rec)
            piece["phrase_norm"] = seg
            glue = glue_group_id(seg)
            if glue:
                piece["glue_group"] = glue
            piece["harvest_repaired"] = len(segments) > 1
            expanded.append(piece)
    return expanded


def _assign_family_roles(families: list[dict[str, Any]]) -> None:
    """STEPT1af: type from place + cue after overlap/grouping/name-strip."""
    for f in families:
        if f.get("overlap_short_tail"):
            f["suggested_role"] = "undecided"
            continue
        hb = str(f.get("hinge_bucket") or "")
        if hb.startswith("glue:"):
            f["suggested_role"] = "carrier"
            f["glue_group"] = hb.split(":", 1)[-1]
            continue
        cue = str(f.get("overlap_cue") or "")
        place = str(f.get("overlap_place") or "")
        norm = str(f.get("exemplar_norm") or "")
        if not cue or cue == "None":
            cue = assign_cue(norm)
            f["overlap_cue"] = cue
        if not place or place == "None":
            # Map coarse zone → place band when overlap did not run
            zone = str(f.get("zone") or "")
            if zone == "opening":
                place = "opening"
            elif zone == "close":
                place = "decision"
            elif zone == "body":
                place = "exposition"
            else:
                place = place_band(
                    f.get("mean_rel_mid") or f.get("rel_mid"),
                    norm,
                    cue_id=cue,
                )
            f["overlap_place"] = place
        # Null hinge / surface wins
        if "geen resolutie" in norm or hb.startswith("null_decision") or hb.startswith(
            "cue:geen_resolutie"
        ):
            f["suggested_role"] = "null_decision"
            continue
        f["suggested_role"] = role_from_place_and_cue(
            place=place,
            cue=cue,
            exemplar_norm=norm,
            short_tail=False,
        )


def fold_phrases(
    rows: Sequence[dict[str, Any]],
    *,
    variant_ratio: float = DEFAULT_VARIANT_RATIO,
    overlap_edges: Sequence[dict[str, Any]] | None = None,
    overlap_min_n: int = DEFAULT_MIN_OVERLAP_N,
    overlap_min_frac: float = DEFAULT_MIN_FRAC,
) -> dict[str, Any]:
    """Repair → nest → optional overlap → name-strip → variant → place-based role.

    STEPT1af: inbound ``suggested_role`` is ignored; typology assigned last.
    """
    cleaned = []
    for r in rows:
        rec = dict(r)
        rec["phrase_norm"] = normalize_phrase(str(rec.get("phrase") or ""))
        rec.pop("suggested_role", None)
        # Carry mean_rel_mid as rel_mid for place_band when present
        if rec.get("rel_mid") is None and rec.get("mean_rel_mid") is not None:
            rec["rel_mid"] = rec.get("mean_rel_mid")
        cleaned.append(rec)

    repaired = _expand_harvest_artefacts(cleaned)
    n_split_rows = sum(1 for r in repaired if r.get("harvest_repaired"))
    after_nest, n_nested = nest_collapse(repaired)

    overlap_meta: dict[str, Any] = {}
    if overlap_edges is not None:
        after_nest, overlap_meta = apply_overlap_cue_pass(
            after_nest,
            overlap_edges,
            min_n=overlap_min_n,
            min_frac=overlap_min_frac,
        )
    else:
        # Name-strip even without overlap edges
        stripped_rows: list[dict[str, Any]] = []
        n_name = 0
        for r in after_nest:
            rec = dict(r)
            skel, spans = strip_incidental_names(str(rec.get("phrase_norm") or ""))
            if spans:
                n_name += 1
                rec["phrase_surface"] = rec.get("phrase") or rec.get("phrase_norm")
                rec["phrase_norm"] = skel
                rec["phrase"] = skel
                rec["name_stripped"] = spans
            stripped_rows.append(rec)
        after_nest = stripped_rows
        overlap_meta = {"n_name_stripped": n_name}

    families, n_merges = variant_fold(after_nest, ratio=variant_ratio)
    _assign_family_roles(families)

    role_hist: dict[str, int] = defaultdict(int)
    for f in families:
        role_hist[str(f.get("suggested_role") or "undecided")] += 1

    step = "STEPT1af" if overlap_edges is not None else "STEPT1af-no-overlap"
    metrics = {
        "step": step,
        "n_input_phrases": len(cleaned),
        "n_after_harvest_repair": len(repaired),
        "n_boundary_split_segments": int(n_split_rows),
        "n_after_nest": len(after_nest),
        "n_nested_dropped": int(n_nested),
        "n_variant_merges": int(n_merges),
        "n_families": len(families),
        "variant_ratio": float(variant_ratio),
        "suggested_role_hist": dict(sorted(role_hist.items())),
        "human_roles_enum": list(HUMAN_ROLES),
        "overlap_enabled": overlap_edges is not None,
        "type_after_overlap": True,
        "note": (
            "STEPT1af: overlap→group→name-strip→type-from-place. "
            "Profile suggested_role ignored. No auto-mint."
        ),
    }
    metrics.update(overlap_meta)
    return {"metrics": metrics, "families": families}


def fixture_fold() -> dict[str, Any]:
    prof = fixture_profile()
    rows = list(prof["high_freq"]) + list(prof["rare_sidecar"])
    # Add an orthographic variant of missive opener for merge test.
    rows.append(
        {
            "phrase": "Ontfangen een missive van den",
            "phrase_norm": "ontfangen een missive van den",
            "phrase_freq": 88000,
            "zone": "opening",
            "lcats": "small",
            "suggested_role": "scaffolding_opener",
            "protected": False,
            "source": "high_freq",
        }
    )
    return fold_phrases(rows)
