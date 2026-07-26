"""Unit-Tests für die Textvorverarbeitung (app/preprocessing.py)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.preprocessing import chunk_text, clean_text


def test_clean_text_removes_hyphenation_across_linebreak():
    raw = "Die Patent-\nanmeldung wurde eingereicht."
    assert clean_text(raw) == "Die Patentanmeldung wurde eingereicht."


def test_clean_text_collapses_whitespace_and_newlines():
    raw = "Zeile eins\n\nZeile   zwei\r\nZeile drei"
    result = clean_text(raw)
    assert "\n" not in result
    assert "  " not in result
    assert "Zeile eins Zeile zwei Zeile drei" == result


def test_chunk_text_returns_single_chunk_for_short_text():
    text = "Ein kurzer Satz."
    chunks = chunk_text(text, max_tokens=100)
    assert chunks == [text]


def test_chunk_text_splits_long_text_into_multiple_chunks():
    # Ein langer künstlicher Text, der die Chunk-Grenze überschreiten muss.
    sentence = "Dies ist ein Testsatz zur Ueberpruefung der Chunk-Funktion. "
    long_text = sentence * 200  # deutlich über max_tokens * 4 Zeichen
    chunks = chunk_text(long_text, max_tokens=100, overlap_tokens=10)

    assert len(chunks) > 1
    # Jeder Chunk sollte nicht wesentlich länger sein als vorgegeben.
    for chunk in chunks:
        assert len(chunk) <= 100 * 4 + 200  # Toleranz für Satzgrenzen-Suche


def test_chunk_text_no_empty_chunks():
    long_text = "Wort " * 2000
    chunks = chunk_text(long_text, max_tokens=50)
    assert all(chunk.strip() for chunk in chunks)
