"""
Kapselt das Laden und Ausführen des Summarization-Modells.

Das Modell wird beim Start des Service genau einmal geladen (Singleton-
Pattern über Modulebene), damit nicht bei jeder Anfrage die Gewichte neu
initialisiert werden müssen. Das ist besonders auf CPU-Hardware relevant,
wie sie in einer Kanzlei-Serverumgebung üblich ist.
"""


from __future__ import annotations

import logging

from ml_service import config

logger = logging.getLogger(__name__)

_summarization_pipeline = None
_tokenizer = None

# Maximale Eingabelänge des Modells (BART: 1024 Positions-Embeddings).
_MAX_INPUT_TOKENS = 1024


def get_pipeline():
    """Lazy-Loading des HuggingFace-Pipelines, damit App-Start und Health-Check
    nicht auf das (teure) Modell-Laden warten müssen, bevor der erste Request kommt.

    Der Import von `transformers` erfolgt bewusst erst hier (statt auf
    Modulebene), damit z. B. Unit-Tests der FastAPI-Schicht laufen können,
    ohne die schwere ML-Bibliothek installieren zu müssen.
    """
    global _summarization_pipeline, _tokenizer
    if _summarization_pipeline is None:
        from transformers import pipeline, AutoTokenizer

        logger.info("Lade Summarization-Modell '%s' ...", config.MODEL_NAME)
        _summarization_pipeline = pipeline(
            "summarization",
            model=config.MODEL_NAME,
        )
        _tokenizer = AutoTokenizer.from_pretrained(config.MODEL_NAME)
        logger.info("Modell geladen.")
    return _summarization_pipeline

def _truncate_to_model_limit(text: str) -> str:
    """
    Kürzt den Text explizit auf die maximale Eingabelänge des Modells,
    bevor er an die Pipeline übergeben wird. Verlässt sich bewusst nicht
    auf das `truncation`-Argument der Pipeline, da dessen Wirkung je nach
    transformers-Version inkonsistent sein kann und in der Praxis den
    Decoder-IndexError nicht zuverlässig verhindert hat.
    """
    global _tokenizer
    tokens = _tokenizer.encode(text, add_special_tokens=False)
    if len(tokens) <= _MAX_INPUT_TOKENS:
        return text

    logger.warning(
        "Eingabetext hat %d Tokens und wird auf %d Tokens gekürzt.",
        len(tokens),
        _MAX_INPUT_TOKENS,
    )
    truncated_tokens = tokens[:_MAX_INPUT_TOKENS]
    return _tokenizer.decode(truncated_tokens, skip_special_tokens=True)

def summarize_text(text: str) -> str:
    """
    Erzeugt eine Zusammenfassung für einen einzelnen (bereits auf die
    Modell-Eingabelänge zugeschnittenen) Textabschnitt.
    """
    summarizer = get_pipeline()
    safe_text = _truncate_to_model_limit(text)

    result = summarizer(
        safe_text,
        max_length=config.MAX_SUMMARY_TOKENS,
        min_length=config.MIN_SUMMARY_TOKENS,
        do_sample=False,
    )
    return result[0]["summary_text"]
