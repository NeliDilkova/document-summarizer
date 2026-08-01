"""
Textvorverarbeitung zwischen PDF-Extraktion und Zusammenfassungsmodell.

Enthält Bereinigung (Whitespace, Silbentrennungsartefakte aus PDF-Export)
und eine Chunking-Funktion, da Transformer-Modelle wie BART eine begrenzte
Eingabelänge (Tokens) verarbeiten können und Patentdokumente oft deutlich
länger sind.
"""

from __future__ import annotations

import re

from transformers import AutoTokenizer

_TOKENIZER = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")


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


def _token_count(text: str) -> int:
    """Zählt die tatsächliche Tokenanzahl mit dem BART-Tokenizer."""
    return len(_TOKENIZER.encode(text, add_special_tokens=False))


def chunk_text(text: str, max_tokens: int = 900, overlap_tokens: int = 50) -> list[str]:
    """
    Teilt langen Text in überlappende Abschnitte auf, damit auch Dokumente
    verarbeitet werden können, die die maximale Eingabelänge des
    Zusammenfassungsmodells überschreiten.

    Args:
        text: bereinigter Volltext.
        max_tokens: Zielgröße je Abschnitt (in tatsächlichen Tokens).
        overlap_tokens: Überlappung zwischen aufeinanderfolgenden Abschnitten,
            damit an den Grenzen keine relevanten Sätze verloren gehen.

    Returns:
        Liste von Textabschnitten. Enthält genau ein Element, wenn der Text
        bereits kurz genug ist.
    """
    if _token_count(text) <= max_tokens:
        return [text]

    # Grobe Vorab-Segmentierung anhand von Satzgrenzen, danach werden
    # Sätze so lange zusammengefasst, bis das echte Token-Limit erreicht ist.
    sentences = re.split(r"(?<=[.!?])\s+", text)

    chunks: list[str] = []
    current_sentences: list[str] = []
    current_tokens = 0

    for sentence in sentences:
        sentence_tokens = _token_count(sentence)

        if current_tokens + sentence_tokens > max_tokens and current_sentences:
            chunk = " ".join(current_sentences).strip()
            chunks.append(chunk)

            # Overlap: die letzten Sätze des vorherigen Chunks als Start
            # des nächsten Chunks übernehmen, bis overlap_tokens erreicht ist.
            overlap_sentences: list[str] = []
            overlap_count = 0
            for s in reversed(current_sentences):
                s_tokens = _token_count(s)
                if overlap_count + s_tokens > overlap_tokens:
                    break
                overlap_sentences.insert(0, s)
                overlap_count += s_tokens

            current_sentences = overlap_sentences
            current_tokens = overlap_count

        current_sentences.append(sentence)
        current_tokens += sentence_tokens

        # Sicherheitsnetz: falls ein einzelner Satz allein schon das Limit
        # überschreitet,
        # wird er selbst hart auf Tokenebene aufgeteilt, statt den Fehler
        # weiterzureichen.
        if sentence_tokens > max_tokens:
            tokens = _TOKENIZER.encode(sentence, add_special_tokens=False)
            current_sentences.pop()
            current_tokens -= sentence_tokens
            for i in range(0, len(tokens), max_tokens):
                sub_tokens = tokens[i:i + max_tokens]
                sub_text = _TOKENIZER.decode(sub_tokens, skip_special_tokens=True)
                chunks.append(sub_text.strip())

    if current_sentences:
        chunks.append(" ".join(current_sentences).strip())

    return [c for c in chunks if c]