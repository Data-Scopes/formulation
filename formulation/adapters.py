"""Turn REPUBLIC-style resolution records into token streams for FormulaSearch.

``FormulaSearch`` iterates documents as sequences of tokens (``for token in doc``)
and some methods also look up ``doc['id']``. This module wraps sample records so
those contracts hold, while copying archival fields (section, offsets, ids)
onto each doc — position in the resolution is part of formula meaning later.

Does not talk to Elasticsearch or import ``republic.*``. Corpus files are
registered in STEP2; this adapter only shapes records already in memory.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator, Mapping, Sequence
from typing import Any

# Word or punctuation token; enough for the first slice without coupling to
# fuzzy-search internals. Records may also supply ``tokens`` / ``words``.
_TOKEN_RE = re.compile(r"\w+|[^\w\s]", flags=re.UNICODE)


class TokenDoc(Sequence[str]):
    """Iterable of token strings with archival metadata attached.

    ``words`` is what FormulaSearch consumes. All other fields from the source
    record are kept on ``metadata`` (and via ``doc[key]``) so they are not
    dropped during the transform.
    """

    def __init__(self, words: Sequence[str], metadata: Mapping[str, Any] | None = None) -> None:
        self.words = list(words)
        self.metadata = dict(metadata or {})

    def __iter__(self) -> Iterator[str]:
        return iter(self.words)

    def __len__(self) -> int:
        return len(self.words)

    def __getitem__(self, item: int | slice | str) -> Any:
        if isinstance(item, (int, slice)):
            return self.words[item]
        if item == "words":
            return self.words
        if item == "id":
            return self.metadata.get("id") or self.metadata.get("resolution_id")
        try:
            return self.metadata[item]
        except KeyError as exc:
            raise KeyError(item) from exc

    def __repr__(self) -> str:
        doc_id = self["id"]
        return f"TokenDoc(id={doc_id!r}, n_tokens={len(self.words)})"


def tokenize_text(text: str) -> list[str]:
    """Split text into word and punctuation tokens."""
    return _TOKEN_RE.findall(text)


def _tokens_from_record(record: Mapping[str, Any]) -> list[str]:
    for key in ("tokens", "words"):
        value = record.get(key)
        if isinstance(value, list) and value:
            return [str(token) for token in value]
    text = record.get("text")
    if isinstance(text, str) and text.strip():
        return tokenize_text(text)
    raise ValueError(
        "Resolution record needs 'tokens', 'words', or non-empty 'text' "
        "so FormulaSearch can iterate token strings."
    )


def iter_token_docs(records: Iterable[Mapping[str, Any]]) -> Iterator[TokenDoc]:
    """Yield FormulaSearch-ready docs from resolution records.

    Prefers an existing ``tokens`` / ``words`` list; otherwise tokenizes
    ``text``. Every source field is copied onto ``TokenDoc.metadata``.
    """
    for record in records:
        metadata = dict(record)
        words = _tokens_from_record(record)
        yield TokenDoc(words=words, metadata=metadata)
