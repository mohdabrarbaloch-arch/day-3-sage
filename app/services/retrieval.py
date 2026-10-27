"""Grounded answer retrieval.

Given a question and a document, this ranks chunks by lexical overlap
(TF-IDF over a shared vocabulary), extracts the best-matching sentences, and
returns them with a grounded flag. If nothing clears the threshold, it returns
an honest refusal instead of guessing.
"""

import math
import re
from collections import Counter

from app.services.chunking import Chunk, chunk_text, split_sentences
from app.services.guardrails import flag_question

_WORD_RE = re.compile(r"[a-z0-9]{2,}")
_STOPWORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "if",
    "of",
    "to",
    "in",
    "on",
    "for",
    "with",
    "as",
    "by",
    "at",
    "from",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "it",
    "its",
    "this",
    "that",
    "these",
    "those",
    "i",
    "you",
    "he",
    "she",
    "we",
    "they",
    "his",
    "her",
    "their",
    "our",
    "your",
    "not",
    "no",
    "so",
    "than",
    "then",
    "into",
    "over",
    "under",
    "also",
    "can",
    "will",
    "would",
    "should",
    "could",
    "may",
    "might",
    "must",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "what",
    "which",
    "who",
    "whom",
    "when",
    "where",
    "why",
    "how",
}

MIN_OVERLAP = 1
SCORE_THRESHOLD = 0.05


def _tokens(text: str) -> list[str]:
    return [w for w in _WORD_RE.findall(text.lower()) if w not in _STOPWORDS]


def _score(query_tokens: list[str], chunk: Chunk) -> float:
    body_tokens = _tokens(chunk.text)
    if not body_tokens or not query_tokens:
        return 0.0
    body_freq = Counter(body_tokens)
    overlap = sum(body_freq[w] for w in query_tokens if w in body_freq)
    if overlap < MIN_OVERLAP:
        return 0.0
    # Soft IDF: rarer words count more, so a shared rare term outscores a
    # shared stopword-free common term.
    idf = 1.0 + math.log(len(body_tokens) / max(overlap, 1))
    return overlap * idf


def answer(question: str, document: str) -> tuple[str, list[str], bool]:
    blocked, _ = flag_question(question)
    if blocked:
        return "I can't help with that request.", [], False

    q_tokens = _tokens(question)
    if not q_tokens:
        return (
            "I couldn't find anything in your uploaded files that answers that.",
            [],
            False,
        )

    chunks = chunk_text(document)
    if not chunks:
        return "This document has no readable text.", [], False

    ranked = sorted(chunks, key=lambda c: _score(q_tokens, c), reverse=True)
    best = ranked[0]
    best_score = _score(q_tokens, best)
    if best_score < SCORE_THRESHOLD:
        return (
            "I couldn't find anything in your uploaded files that answers that.",
            [],
            False,
        )

    # Pull the top sentence(s) from the best chunk.
    sentences = split_sentences(best.text)
    sentence_scores = [
        (s, _tokens(s), sum(1 for w in q_tokens if w in set(_tokens(s)))) for s in sentences
    ]
    sentence_scores = [x for x in sentence_scores if x[1]]
    sentence_scores.sort(key=lambda x: x[2], reverse=True)
    top = sentence_scores[:2]
    answer_text = " ".join(s[0] for s in top)
    citations = [s[0] for s in top]
    return answer_text, citations, True
