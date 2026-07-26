"""
Textvorverarbeitung zwischen PDF-Extraktion und Zusammenfassungsmodell.

Enthält Bereinigung (Whitespace, Silbentrennungsartefakte aus PDF-Export)
und eine Chunking-Funktion, da Transformer-Modelle wie BART eine begrenzte
Eingabelänge (Tokens) verarbeiten können und Patentdokumente oft deutlich
länger sind.
"""

from __future__ import annotations

import re

# Ungefähre Zeichen-pro-Token-Faustregel für englischsprachige/technische
# Texte, um die Tokenlänge ohne eigenen Tokenizer-Aufruf abzuschätzen.
_CHARS_PER_TOKEN_ESTIMATE = 4


def clean_text(raw_text: str) -> str:
    """
    Entfernt typische Artefakte aus PDF-Textextraktion:
    - mehrfache Leerzeichen/Zeilenumbrüche
    - Silbentrennung am Zeilenende ("Patent-\nanmeldung" -> "Patentanmeldung")
    - wiederkehrende Kopf-/Fußzeilen-Whitespaces
    """
    text = raw_text.replace("\r", " ")
    # Silbentrennung am Zeilenumbruch zusammenführen.
    text = re.sub(r"-\n(?=[a-zäöüß])", "", text)
    # Zeilenumbrüche innerhalb von Absätzen durch Leerzeichen ersetzen.
    text = re.sub(r"\n+", " ", text)
    # Mehrfache Leerzeichen auf ein einzelnes reduzieren.
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def chunk_text(text: str, max_tokens: int = 900, overlap_tokens: int = 50) -> list[str]:
    """
    Teilt langen Text in überlappende Abschnitte auf, damit auch Dokumente
    verarbeitet werden können, die die maximale Eingabelänge des
    Zusammenfassungsmodells überschreiten.

    Args:
        text: bereinigter Volltext.
        max_tokens: ungefähre Zielgröße je Abschnitt (in Tokens).
        overlap_tokens: Überlappung zwischen aufeinanderfolgenden Abschnitten,
            damit an den Grenzen keine relevanten Sätze verloren gehen.

    Returns:
        Liste von Textabschnitten. Enthält genau ein Element, wenn der Text
        bereits kurz genug ist.
    """
    max_chars = max_tokens * _CHARS_PER_TOKEN_ESTIMATE
    overlap_chars = overlap_tokens * _CHARS_PER_TOKEN_ESTIMATE

    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        # An einer Satzgrenze statt mitten im Wort schneiden, falls möglich.
        if end < len(text):
            last_period = text.rfind(". ", start, end)
            if last_period != -1 and last_period > start:
                end = last_period + 1
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap_chars, start + 1)

    return [c for c in chunks if c]
