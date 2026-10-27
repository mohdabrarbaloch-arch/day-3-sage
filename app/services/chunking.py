"""Split text into sentence-chunks with stable positional metadata.

Every chunk carries the sentence index, a character offset, and a page hint
(derived from form-feed / paragraph breaks in PDF text). This is what lets the
UI show *where* an answer came from.
"""

import re
from dataclasses import dataclass

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+|(?<=\n)\s*")


@dataclass(frozen=True)
class Chunk:
    index: int
    text: str
    start: int
    end: int
    page: int


def split_sentences(text: str) -> list[str]:
    raw = _SENTENCE_RE.split(text)
    out: list[str] = []
    for part in raw:
        part = part.strip()
        if part:
            out.append(part)
    return out


def chunk_text(text: str, max_chars: int = 1200) -> list[Chunk]:
    """Group sentences into chunks no larger than max_chars.

    Pages are approximated by form-feed characters, which PyPDF2 often emits
    between PDF pages.
    """
    sentences = split_sentences(text)
    chunks: list[Chunk] = []
    current: list[str] = []
    current_len = 0
    page = 1
    start = 0

    def _flush(page: int) -> None:
        nonlocal current, current_len, start
        if not current:
            return
        body = " ".join(current)
        chunks.append(
            Chunk(
                index=len(chunks),
                text=body,
                start=start,
                end=start + len(body),
                page=page,
            )
        )
        start += len(body)
        current = []
        current_len = 0

    for sentence in sentences:
        # A form-feed signals a new page in extracted PDF text.
        if "\f" in sentence:
            _flush(page)
            page += 1
            sentence = sentence.replace("\f", " ").strip()
            if not sentence:
                continue
        if current and current_len + len(sentence) + 1 > max_chars:
            _flush(page)
        current.append(sentence)
        current_len += len(sentence) + 1

    _flush(page)
    return chunks
