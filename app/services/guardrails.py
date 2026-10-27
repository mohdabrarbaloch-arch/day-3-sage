"""Lightweight safety guardrails for inbound questions.

Sage never proxies a prompt to an external model, so the guardrails are about
input hygiene: rejecting clearly abusive or non-question payloads before they
reach the retrieval layer. They are deliberately conservative and only block
obvious cases — they are not a full moderation pipeline.
"""

import re

# A small deny-list of explicitly harmful instruction patterns. Kept tiny on
# purpose: matching more risks false positives on legitimate documents.
_BLOCK_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(how\s+to\s+(make|build|synthesize|create)\s+a?\s*(bomb|explosive|weapon))",
        re.IGNORECASE,
    ),
    re.compile(r"\b(instructions?\s+to\s+(harm|hurt|kill|injure))", re.IGNORECASE),
    re.compile(
        r"\b(produce|generate|write)\s+(child|sexual)\s+(abuse|exploitation)\s+(material|content)",
        re.IGNORECASE,
    ),
)


def flag_question(question: str) -> tuple[bool, str | None]:
    """Return (blocked, reason) for a user question."""
    text = question.strip()
    if not text:
        return True, "question is empty"
    if len(text) > 2000:
        return True, "question exceeds 2000 characters"
    for pattern in _BLOCK_PATTERNS:
        if pattern.search(text):
            return True, "request violates safety policy"
    return False, None
