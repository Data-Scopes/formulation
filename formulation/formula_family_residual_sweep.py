"""STEPT1ag: residual sweep of lonely / thin families after fold.

Pass 0 — triviality sieve (park, do not skim).
Pass 1 — capped absorb / truncate proposals for non-trivial leftovers.
No auto-merge; human_role untouched.
"""

from __future__ import annotations

from typing import Any, Sequence

from formulation.formula_family_fold import repair_harvest_segments
from formulation.overlap_cue_prove import is_short_continuation, strip_incidental_names
from formulation.phrases_5gram_profile import (
    DEFAULT_MIN_FREQ,
    ROLE_KEYWORDS,
    normalize_phrase,
)

DEFAULT_MAX_SOLO_MEMBERS = 2
DEFAULT_REVIEW_CAP = 60
DEFAULT_MIN_MULTI_MEMBERS = 3
DEFAULT_MAX_TRIVIAL_TOKENS = 3
# Align with Pass A high_freq: review shortlist is for cardinal mass only.
DEFAULT_MIN_REVIEW_FREQ = DEFAULT_MIN_FREQ

_FORMULA_CUES = frozenset(
    {
        "ontfangen",
        "waar_op",
        "geen_resolutie",
        "in_handen",
        "voldoening",
        "ter_advies",
    }
)

_CLOSED_CLASS = frozenset(
    {
        "de",
        "den",
        "der",
        "het",
        "een",
        "van",
        "en",
        "op",
        "in",
        "aan",
        "aen",
        "tot",
        "ter",
        "te",
        "dat",
        "is",
        "by",
        "bij",
        "haar",
        "hun",
        "uit",
        "met",
        "voor",
        "na",
        "door",
        "als",
        "of",
        "zo",
        "zoo",
        "nog",
        "ook",
        "niet",
        "geen",
        "name",  # after name-strip
    }
)

_PLACE_OFFICE = frozenset(
    {
        "provincie",
        "provincien",
        "holland",
        "zeeland",
        "utrecht",
        "gelderland",
        "overyssel",
        "friesland",
        "stad",
        "en",
        "lande",
        "griffier",
        "secretaris",
        "gedeputeerden",
        "gedeputeerde",
        "heeren",
        "heere",
        "heer",
        "hoog",
        "mog",
        "mogende",
        "mogenden",
    }
)

_FORMULA_KEYWORDS: tuple[str, ...] = tuple(
    k
    for keys in ROLE_KEYWORDS.values()
    for k in keys
) + (
    "waar op",
    "gedelibereert",
    "goedgevonden",
    "handen",
    "houdende",
    "advertentie",
    "missive",
    "requeste",
)


def _tokens(norm: str) -> list[str]:
    return [t for t in normalize_phrase(norm).split() if t]


def _exemplar_norm(fam: dict[str, Any]) -> str:
    return normalize_phrase(str(fam.get("exemplar_norm") or fam.get("exemplar") or ""))


def _has_formula_keyword(norm: str) -> bool:
    n = normalize_phrase(norm)
    return any(k in n for k in _FORMULA_KEYWORDS)


def _has_real_cue(fam: dict[str, Any]) -> bool:
    cue = str(fam.get("overlap_cue") or "")
    return cue in _FORMULA_CUES


def is_trivial_family(
    fam: dict[str, Any],
    *,
    multi_exemplars: Sequence[str] = (),
    max_tokens: int = DEFAULT_MAX_TRIVIAL_TOKENS,
) -> tuple[bool, str]:
    """Return (trivial?, reason). Multi-member formula families are never trivial here."""
    n_mem = int(fam.get("n_members") or 1)
    if n_mem >= DEFAULT_MIN_MULTI_MEMBERS:
        return False, ""

    raw = _exemplar_norm(fam)
    skel, _stripped = strip_incidental_names(raw)
    toks = _tokens(skel)
    cue = str(fam.get("overlap_cue") or "other")
    hinge = str(fam.get("hinge_bucket") or "")

    if is_short_continuation(skel) or is_short_continuation(raw):
        return True, "short_tail_f1b"

    if len(toks) <= max_tokens:
        return True, "token_len_le3"

    if hinge.startswith("tok:") and cue in ("", "other", "None") and not _has_formula_keyword(
        skel
    ):
        return True, "tok_hinge_no_cue"

    # Only closed-class / place / office filler tokens
    content = [t for t in toks if t not in _CLOSED_CLASS and t not in _PLACE_OFFICE]
    if not content and not _has_formula_keyword(skel) and cue not in _FORMULA_CUES:
        return True, "closed_class_or_place_office"

    # Pure substring of an existing multi-member exemplar
    for ex in multi_exemplars:
        exn = normalize_phrase(ex)
        if skel and skel != exn and skel in exn:
            # token-boundary-ish
            if f" {skel} " in f" {exn} " or exn.startswith(skel + " ") or exn.endswith(
                " " + skel
            ):
                return True, "substring_of_multi"

    return False, ""


def propose_truncate(fam: dict[str, Any]) -> dict[str, Any] | None:
    """If exemplar straddles WAAR / bare waar, propose prefix split."""
    raw = _exemplar_norm(fam)
    parts = repair_harvest_segments(raw)
    if len(parts) < 2:
        return None
    return {
        "action": "truncate_or_split",
        "prefix": parts[0],
        "suffix": parts[1],
        "note": "mid-waar straddle; prefix may absorb elsewhere, suffix may join decision",
    }


def propose_absorb(
    fam: dict[str, Any],
    multi_families: Sequence[dict[str, Any]],
) -> dict[str, Any] | None:
    """Containment / shared place+cue / skeleton overlap → absorb_into proposal."""
    skel, _ = strip_incidental_names(_exemplar_norm(fam))
    if not skel:
        return None
    place = str(fam.get("overlap_place") or fam.get("zone") or "")
    cue = str(fam.get("overlap_cue") or "")

    best: dict[str, Any] | None = None
    best_score = 0
    for mf in multi_families:
        mex = _exemplar_norm(mf)
        mskel, _ = strip_incidental_names(mex)
        if not mskel:
            continue
        score = 0
        reason = ""
        if skel in mskel or mskel in skel:
            score += 3
            reason = "containment"
        # shared cue (real)
        mcue = str(mf.get("overlap_cue") or "")
        if cue in _FORMULA_CUES and cue == mcue:
            score += 2
            reason = reason or "shared_cue"
        mplace = str(mf.get("overlap_place") or mf.get("zone") or "")
        if place and mplace and place == mplace and score > 0:
            score += 1
        # token overlap ≥ 3 consecutive
        st, mt = _tokens(skel), _tokens(mskel)
        if len(st) >= 3 and len(mt) >= 3:
            for i in range(len(st) - 2):
                tri = " ".join(st[i : i + 3])
                if tri in mskel:
                    score += 2
                    reason = reason or "shared_trigram"
                    break
        if score > best_score:
            best_score = score
            best = {
                "action": "absorb_into",
                "absorb_into": mf.get("family_id"),
                "absorb_exemplar": mf.get("exemplar"),
                "score": score,
                "reason": reason,
            }
    if best is not None and best_score >= 3:
        return best
    return None


def _park_trivial(
    fam: dict[str, Any],
    *,
    reason: str,
) -> dict[str, Any]:
    return {
        "family_id": fam.get("family_id"),
        "exemplar": fam.get("exemplar"),
        "exemplar_norm": _exemplar_norm(fam),
        "n_members": int(fam.get("n_members") or 1),
        "phrase_freq_max": int(fam.get("phrase_freq_max") or 0),
        "suggested_role": fam.get("suggested_role"),
        "overlap_cue": fam.get("overlap_cue"),
        "hinge_bucket": fam.get("hinge_bucket"),
        "disposition": "trivial",
        "trivial_reason": reason,
        "human_keep": None,
    }


def sweep_families(
    families: Sequence[dict[str, Any]],
    *,
    max_solo_members: int = DEFAULT_MAX_SOLO_MEMBERS,
    min_multi_members: int = DEFAULT_MIN_MULTI_MEMBERS,
    review_cap: int = DEFAULT_REVIEW_CAP,
    min_review_freq: int = DEFAULT_MIN_REVIEW_FREQ,
) -> dict[str, Any]:
    """Classify residuals: trivial park + capped review (absorb/truncate/both).

    Review eligibility requires phrase_freq_max >= min_review_freq (Pass A floor).
    Cap is a count limit on top of that floor — not a substitute for it.
    """
    multi = [f for f in families if int(f.get("n_members") or 1) >= min_multi_members]
    thin = [f for f in families if int(f.get("n_members") or 1) <= max_solo_members]
    multi_exemplars = [_exemplar_norm(f) for f in multi]

    trivial_rows: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []

    for fam in thin:
        trivial, reason = is_trivial_family(fam, multi_exemplars=multi_exemplars)
        if trivial:
            trivial_rows.append(_park_trivial(fam, reason=reason or "trivial"))
            continue

        freq = int(fam.get("phrase_freq_max") or 0)
        if freq < min_review_freq:
            trivial_rows.append(_park_trivial(fam, reason="freq_below_min"))
            continue

        # Non-trivial thin: only review if cue / keyword / absorb or truncate signal
        trunc = propose_truncate(fam)
        absorb = propose_absorb(fam, multi)
        has_signal = (
            _has_real_cue(fam)
            or _has_formula_keyword(_exemplar_norm(fam))
            or trunc is not None
            or absorb is not None
        )
        if not has_signal:
            trivial_rows.append(_park_trivial(fam, reason="no_cue_keyword_or_link"))
            continue

        actions = []
        if absorb:
            actions.append(absorb)
        if trunc:
            actions.append(trunc)
        disposition = "review"
        if absorb and trunc:
            disposition = "review_both"
        elif absorb:
            disposition = "review_absorb"
        elif trunc:
            disposition = "review_truncate"

        candidates.append(
            {
                "family_id": fam.get("family_id"),
                "exemplar": fam.get("exemplar"),
                "exemplar_norm": _exemplar_norm(fam),
                "n_members": int(fam.get("n_members") or 1),
                "phrase_freq_max": freq,
                "suggested_role": fam.get("suggested_role"),
                "overlap_cue": fam.get("overlap_cue"),
                "overlap_place": fam.get("overlap_place"),
                "hinge_bucket": fam.get("hinge_bucket"),
                "disposition": disposition,
                "proposals": actions,
                "human_keep": None,
                "human_absorb_into": None,
                "human_note": None,
            }
        )

    # Cap review: prefer more proposals + higher freq (floor already applied)
    candidates.sort(
        key=lambda r: (
            -len(r.get("proposals") or []),
            -int(r.get("phrase_freq_max") or 0),
            str(r.get("family_id") or ""),
        )
    )
    review = candidates[: max(0, review_cap)]
    overflow = candidates[review_cap:]
    for row in overflow:
        trivial_rows.append(
            {
                **{k: row[k] for k in (
                    "family_id",
                    "exemplar",
                    "exemplar_norm",
                    "n_members",
                    "phrase_freq_max",
                    "suggested_role",
                    "overlap_cue",
                    "hinge_bucket",
                )},
                "disposition": "trivial",
                "trivial_reason": "review_cap_overflow",
                "human_keep": None,
            }
        )

    reason_hist: dict[str, int] = {}
    for t in trivial_rows:
        rr = str(t.get("trivial_reason") or "")
        reason_hist[rr] = reason_hist.get(rr, 0) + 1

    metrics = {
        "step": "STEPT1ag",
        "n_input_families": len(families),
        "n_multi": len(multi),
        "n_thin": len(thin),
        "n_trivial": len(trivial_rows),
        "n_review": len(review),
        "n_review_capped_out": len(overflow),
        "review_cap": int(review_cap),
        "min_review_freq": int(min_review_freq),
        "trivial_reason_hist": dict(sorted(reason_hist.items())),
        "note": (
            "Trivial park is not skimmed. Review requires phrase_freq_max >= "
            "min_review_freq; count-cap is on top of that floor. No auto-merge."
        ),
    }
    return {
        "metrics": metrics,
        "trivial": trivial_rows,
        "review": review,
    }


def fixture_sweep() -> dict[str, Any]:
    """Tiny in-memory families for unit tests / --fixture-only."""
    families = [
        {
            "family_id": "fam_m001",
            "exemplar": "WAAR op gedelibereert zynde is",
            "exemplar_norm": "waar op gedelibereert zynde is",
            "n_members": 5,
            "phrase_freq_max": 90000,
            "overlap_cue": "waar_op",
            "overlap_place": "decision",
            "suggested_role": "scaffolding_decision",
            "hinge_bucket": "cue:waar_op",
        },
        {
            "family_id": "fam_s_tok",
            "exemplar": "van de",
            "exemplar_norm": "van de",
            "n_members": 1,
            "phrase_freq_max": 50000,
            "overlap_cue": "other",
            "suggested_role": "carrier",
            "hinge_bucket": "tok:van_de",
        },
        {
            "family_id": "fam_s_waar",
            "exemplar": "houdende advertentie WAAR op",
            "exemplar_norm": "houdende advertentie waar op",
            "n_members": 1,
            "phrase_freq_max": 8000,
            "overlap_cue": "other",
            "suggested_role": "carrier",
            "hinge_bucket": "tok:houdende_advertentie",
        },
        {
            "family_id": "fam_s_chain",
            "exemplar": "op gedelibereert zynde is",
            "exemplar_norm": "op gedelibereert zynde is",
            "n_members": 1,
            "phrase_freq_max": 7000,
            "overlap_cue": "waar_op",
            "overlap_place": "decision",
            "suggested_role": "scaffolding_decision",
            "hinge_bucket": "cue:waar_op",
        },
        {
            "family_id": "fam_s_houdende",
            "exemplar": "houdende dat",
            "exemplar_norm": "houdende dat",
            "n_members": 1,
            "phrase_freq_max": 400,
            "overlap_cue": "other",
            "suggested_role": "undecided",
            "hinge_bucket": "tok:houdende_dat",
        },
        {
            "family_id": "fam_s_prov",
            "exemplar": "van de Provincie van Holland",
            "exemplar_norm": "van de provincie van holland",
            "n_members": 1,
            "phrase_freq_max": 3000,
            "overlap_cue": "other",
            "suggested_role": "carrier",
            "hinge_bucket": "tok:van_de",
        },
    ]
    return sweep_families(families, review_cap=20)
