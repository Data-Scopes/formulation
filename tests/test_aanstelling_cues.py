"""Aanstelling cue flags and rough name extraction."""

from __future__ import annotations

import pandas as pd

from formulation.aanstelling_cues import (
    add_aanstelling_cues,
    add_rough_names,
    cue_hits,
    extract_holland_multi_names,
    extract_rough_names,
    has_aanstelling_cue,
)

_HOLLAND_PAUW = (
    "DE Heer Bentinck, eerste van de Heeren Gecommitteerde Raaden van Holland "
    "en Westvriesland, heeft, in gevolge van haar Hoog Mog. Resolutie van den "
    "5 Mey 1730, ter Vergaderinge voorgedraagen, dat in het Collegie van gemelde "
    "Heeren Gecommitteerde Raaden op heeden sessie hadden genoomen, en vervolgens "
    "in de Vergadering van haar Hoog Mog. geintroduceert stonden te worden de "
    "Heeren Pauw en vanden Bosch, weegens de Steeden Delft en Schoonhoven; en "
    "heeft gemelden Heere Bentinck daar by bekend gemaakt, dat gemelde Heeren "
    "Pauw en van - den Bosch geene Ampten besitten die hun volgens haar Hoog Mog. "
    "Resolutie van den 25 February 1723 beletten alhier ter Vergaderinge te "
    "compareeren. WAAR op gedelibereert zynde, is goedgevonden en verstaan, mits "
    "deesen te verklaaren, dat gemelde Heeren Pauw en van - den Bosch aan haar "
    "Hoog Mog. aangenaam zyn, en hebben deselve dienvolgende sessie genoomen."
)

_HOLLAND_LELY = (
    "DEn Heer Bentinck, eerste van de Heeren Gecommitteerde Raaden van Holland "
    "en Westvriesland, heeft, in gevolge van haar Hoogh Mogende Resolutie van den "
    "vyfden Mey seeventien honderd dertigh, ter Vergaderinge voorgedraagen, dat "
    "in het Collegie van gemelde Heeren Gecommitteerde Raaden op heeden sessie "
    "hadden genoomen, en vervolgens in de Vergaderingh van haar Hoogh Mogende "
    "geintroduceert stonden te worden de Heeren vander Lely, en de Fremery, "
    "weegens de Steeden Delft en Schoonhoven, en heeft gemelde Heer Bentinck "
    "daar by bekent gemaackt, dat gemelde Heeren geen Ampten besitten, die hen "
    "volgens haar Hoogh Mogende Resolutie van den vyf en twintighsten February "
    "seeventien honderd drie en twintigh beletten alhier ter Vergaderinge te "
    "compareeren. WAAR op gedelibereert zynde, is goedgevonden en verstaan, mits "
    "deesen te verklaaren, dat gemelde Heeren vander Lely, en de Fremery, aan "
    "haar Hoogh Mogende aangenaam zyn, en hebben dezelve dienvolgende sessie "
    "genoomen."
)


def test_gold_like_cues() -> None:
    text = (
        "Ontfangen een Missive houdende creditif op den Heere Onno Tamminga "
        "van Alberda; is den Heere haer aengenaem was, is deselve verwelkomt "
        "ende heeft sessie genomen."
    )
    hits = cue_hits(text)
    assert "creditief" in hits
    assert "verwelkom" in hits
    assert "sessie_genomen" in hits
    assert "aengenaem" in hits
    assert has_aanstelling_cue(text)


def test_aengenaem_not_aangenomen() -> None:
    assert "aengenaem" in cue_hits("haer aengenaem was")
    assert "aengenaem" in cue_hits("haar aangenaam was")
    assert "aengenaem" not in cue_hits("is aangenomen tot gedeputeerde")
    assert not has_aanstelling_cue("is aangenomen tot gedeputeerde")
    assert not has_aanstelling_cue("Heer")
    assert not has_aanstelling_cue(
        "WAAR op gedelibereert zynde, heeft den aanweesende Heer "
        "Gedeputeerde van de Provincie van Zeeland aangenoomen sig te verklaren."
    )


def test_extract_rough_name_from_creditief() -> None:
    text = (
        "houdende creditif op den Heere Jan van Eck, om als extraordinaris "
        "Gedeputeerde wegen de Provincie"
    )
    names = extract_rough_names(text)
    assert names
    assert "Jan van Eck" in names[0]


def test_extract_op_den_heer() -> None:
    text = (
        "commissie op den heer Willem Egmont vander Nyenburgh, om wegen "
        "de provincie ter Vergaderinge"
    )
    names = extract_rough_names(text)
    assert any("Nyenburgh" in n or "Egmont" in n for n in names)


def test_add_columns() -> None:
    frame = pd.DataFrame(
        {
            "id": ["a", "b"],
            "resolutions_text": [
                "creditif op den Heere Willem Hooft; verwelkomt, sessie genomen",
                "Heer",
            ],
        }
    )
    out = add_rough_names(add_aanstelling_cues(frame))
    assert bool(out.loc[0, "has_aanstelling_cue"])
    assert "Willem Hooft" in out.loc[0, "rough_names"]
    assert not bool(out.loc[1, "has_aanstelling_cue"])
    assert out.loc[1, "rough_names"] == ""


def test_holland_multi_cues_and_split_names() -> None:
    for text in (_HOLLAND_PAUW, _HOLLAND_LELY):
        hits = cue_hits(text)
        assert "holland_multi" in hits
        assert "aengenaem" in hits
        assert "sessie_genomen" in hits
        assert has_aanstelling_cue(text)

    assert extract_holland_multi_names(_HOLLAND_PAUW) == ["Pauw", "vanden Bosch"]
    assert extract_holland_multi_names(_HOLLAND_LELY) == [
        "vander Lely",
        "de Fremery",
    ]
    assert extract_rough_names(_HOLLAND_PAUW) == ["Pauw", "vanden Bosch"]

    frame = pd.DataFrame(
        {"id": ["p", "l"], "resolutions_text": [_HOLLAND_PAUW, _HOLLAND_LELY]}
    )
    out = add_rough_names(add_aanstelling_cues(frame))
    assert bool(out.loc[0, "cue_holland_multi"])
    assert out.loc[0, "holland_multi_names"] == "Pauw; vanden Bosch"
    assert out.loc[1, "holland_multi_names"] == "vander Lely; de Fremery"
    assert out.loc[0, "n_holland_multi_names"] == 2


def test_extract_17c_gecommitteert_and_opden() -> None:
    assert extract_rough_names(
        "opden heer Albert van Benthem, oudt Burgermr. der Stadt Utrecht, om ter"
    ) == ["Albert van Benthem"]
    names = extract_rough_names(
        "hebben gecommitteert den Heere Albert Burch out Burgermr. der Stadt"
    )
    assert names and names[0] == "Albert Burch"
    names = extract_rough_names(
        "gecommitteert ter vergaderinge van haer Ho:Mo: henrick ter Culen "
        "Borgmr. der Stadt Swoll, om op alle"
    )
    assert names and "ter Culen" in names[0]
    assert "verwelkom" in cue_hits(
        "den gemelten heere Bevelinckhoven verwellecompt, ende heeft sessie genomen"
    )
    assert extract_rough_names(
        "den gem: heere van Nijeveen, haer aengenaem was, is deselve verwellekomt"
    ) == ["van Nijeveen"]


def test_bulk_fill_review_rules() -> None:
    from formulation.aanstelling_selection import bulk_fill_review_suspect

    frame = pd.DataFrame(
        {
            "id": ["a", "b", "c", "d"],
            "cue_hits": [
                "sessie_genomen",
                "sessie_genomen;aengenaem",
                "verwelkom",
                "aengenaem",
            ],
            "review": ["", "", "", "keep"],
        }
    )
    out = bulk_fill_review_suspect(frame)
    assert list(out["review"]) == ["keep", "keep", "drop", "keep"]
    assert list(out["review_source"]) == ["rule", "rule", "rule", "human"]
