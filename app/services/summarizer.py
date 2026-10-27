"""Extractive, position-aware summarization.

This is deliberately NOT a generative model. It scores sentences by their
position (lead/body), their term frequency, and their resemblance to the
document's central vocabulary, then returns the top-K sentences in their
original order. The result can never hallucinate — every sentence it returns
is a sentence that was actually in the document.
"""

import math
import re
from collections import Counter

from app.services.chunking import split_sentences

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

_WORD_RE = re.compile(r"[a-z0-9]{2,}")


def _tokens(text: str) -> list[str]:
    return [w for w in _WORD_RE.findall(text.lower()) if w not in _STOPWORDS]


def _sentence_scores(sentences: list[str]) -> list[float]:
    n = len(sentences)
    if n == 0:
        return []

    tok_lists = [_tokens(s) for s in sentences]
    freqs: Counter[str] = Counter()
    for toks in tok_lists:
        freqs.update(toks)

    scores: list[float] = []
    for i, toks in enumerate(tok_lists):
        if not toks:
            scores.append(0.0)
            continue
        # 1. Term frequency, weighted by inverse document frequency.
        tf = 0.0
        for w in toks:
            tf += 1.0 + math.log(freqs[w])
        tf /= len(toks)
        # 2. Position bonus — lead sentences are usually informative.
        position = 1.0 - (i / max(n - 1, 1)) * 0.7
        scores.append(tf * position)
    return scores


def summarize(text: str, ratio: float = 0.3, max_sentences: int = 8) -> str:
    sentences = split_sentences(text)
    if not sentences:
        return ""
    target = max(1, min(max_sentences, round(len(sentences) * ratio)))
    if target >= len(sentences):
        return " ".join(sentences)

    scores = _sentence_scores(sentences)
    ranked = sorted(range(len(sentences)), key=lambda i: scores[i], reverse=True)
    chosen = sorted(ranked[:target])
    return " ".join(sentences[i] for i in chosen)
