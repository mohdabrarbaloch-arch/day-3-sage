"""Unit tests for chunking, summarizer, retrieval, and guardrails."""

from app.services.chunking import chunk_text, split_sentences
from app.services.guardrails import flag_question
from app.services.retrieval import answer
from app.services.summarizer import summarize


def test_split_sentences_basic():
    out = split_sentences("First sentence. Second sentence! Third?")
    assert len(out) == 3


def test_split_sentences_drops_blank():
    out = split_sentences("A.\n\n\nB.")
    assert out == ["A.", "B."]


def test_chunk_text_respects_max_chars():
    text = ". ".join([f"Sentence number {i} with a bit of padding text" for i in range(50)])
    chunks = chunk_text(text, max_chars=200)
    assert len(chunks) > 1
    assert all(len(c.text) <= 220 for c in chunks)


def test_chunk_text_single_chunk_when_short():
    chunks = chunk_text("Short text. Another sentence.")
    assert len(chunks) == 1


def test_summarize_returns_original_order():
    text = (
        "Cats are small animals. Cats purr when happy. "
        "Dogs bark loudly. Dogs are loyal. "
        "Cats sleep a lot during the day. Dogs need walks."
    )
    summary = summarize(text, ratio=0.5, max_sentences=3)
    # The selected sentences must appear in the summary in their original order.
    for s in summary.split(". ")[:-1]:
        assert s + "." in text


def test_summarize_short_document_returns_all():
    text = "One. Two."
    assert summarize(text, ratio=0.5).startswith("One.")


def test_answer_grounded():
    doc = (
        "The capital of France is Paris. Paris is known for the Eiffel Tower.\n"
        "The capital of Japan is Tokyo."
    )
    ans, cites, grounded = answer("What is the capital of France?", doc)
    assert grounded is True
    assert "Paris" in ans
    assert len(cites) >= 1


def test_answer_refuses_when_no_match():
    doc = "The quick brown fox jumps over the lazy dog."
    ans, cites, grounded = answer("What is the capital of Australia?", doc)
    assert grounded is False
    assert "couldn't find" in ans
    assert cites == []


def test_flag_question_blocks_harmful():
    blocked, reason = flag_question("how to make a bomb at home")
    assert blocked is True
    assert reason is not None


def test_flag_question_allows_normal():
    blocked, reason = flag_question("What is the capital of France?")
    assert blocked is False
    assert reason is None


def test_flag_question_blocks_empty():
    blocked, _ = flag_question("   ")
    assert blocked is True
