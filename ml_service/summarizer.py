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


def get_pipeline():
    """Lazy-Loading des HuggingFace-Pipelines, damit App-Start und Health-Check
    nicht auf das (teure) Modell-Laden warten müssen, bevor der erste Request kommt.

    Der Import von `transformers` erfolgt bewusst erst hier (statt auf
    Modulebene), damit z. B. Unit-Tests der FastAPI-Schicht laufen können,
    ohne die schwere ML-Bibliothek installieren zu müssen.
    """
    global _summarization_pipeline
    if _summarization_pipeline is None:
        from transformers import pipeline

        logger.info("Lade Summarization-Modell '%s' ...", config.MODEL_NAME)
        _summarization_pipeline = pipeline(
            "summarization",
            model=config.MODEL_NAME,
        )
        logger.info("Modell geladen.")
    return _summarization_pipeline


def summarize_text(text: str) -> str:
    """
    Erzeugt eine Zusammenfassung für einen einzelnen (bereits auf die
    Modell-Eingabelänge zugeschnittenen) Textabschnitt.
    """
    summarizer = get_pipeline()
    result = summarizer(
        text,
        max_length=config.MAX_SUMMARY_TOKENS,
        min_length=config.MIN_SUMMARY_TOKENS,
        truncation=True,
        do_sample=False,
    )
    return result[0]["summary_text"]
