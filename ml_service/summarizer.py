"""
Kapselt das Laden und Ausführen des Summarization-Modells.

Das Modell wird beim Start des Service genau einmal geladen (Singleton-
Pattern über Modulebene), damit nicht bei jeder Anfrage die Gewichte neu
initialisiert werden müssen. Das ist besonders auf CPU-Hardware relevant,
wie sie in einer Kanzlei-Serverumgebung üblich ist.

Modell und Tokenizer werden bewusst direkt (statt über die HuggingFace-
Pipeline) verwendet, damit die Tokenisierung und Kürzung auf die maximale
Eingabelänge vollständig unter eigener Kontrolle bleibt.
"""

from __future__ import annotations

import logging

from ml_service import config

logger = logging.getLogger(__name__)

_model = None
_tokenizer = None

# Maximale Eingabelänge des Modells (BART: 1024 Positions-Embeddings).
_MAX_INPUT_TOKENS = 1024


def _load_model():
    """
    Lazy-Loading von Modell und Tokenizer, damit App-Start und Health-Check
    nicht auf das (teure) Modell-Laden warten müssen, bevor der erste
    Request kommt.

    Der Import von `transformers`/`torch` erfolgt bewusst erst hier (statt
    auf Modulebene), damit z. B. Unit-Tests der FastAPI-Schicht laufen
    können, ohne die schwere ML-Bibliothek installieren zu müssen.
    """
    global _model, _tokenizer
    if _model is None:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        logger.info("Lade Summarization-Modell '%s' ...", config.MODEL_NAME)
        _tokenizer = AutoTokenizer.from_pretrained(config.MODEL_NAME)
        _model = AutoModelForSeq2SeqLM.from_pretrained(config.MODEL_NAME)
        _model.eval()
        logger.info("Modell geladen.")
    return _model, _tokenizer


def summarize_text(text: str) -> str:
    """
    Erzeugt eine Zusammenfassung für einen einzelnen (bereits auf die
    Modell-Eingabelänge zugeschnittenen) Textabschnitt.

    """
    import torch

    model, tokenizer = _load_model()

    inputs = tokenizer(
        text,
        max_length=_MAX_INPUT_TOKENS,
        truncation=True,
        return_tensors="pt",
    )

    if inputs["input_ids"].shape[1] >= _MAX_INPUT_TOKENS:
        logger.warning(
            "Eingabetext wurde auf %d Tokens gekürzt (Modell-Limit erreicht).",
            _MAX_INPUT_TOKENS,
        )

    with torch.no_grad():
        summary_ids = model.generate(
            **inputs,
            max_length=config.MAX_SUMMARY_TOKENS,
            min_length=config.MIN_SUMMARY_TOKENS,
            do_sample=False,
        )

    return tokenizer.decode(summary_ids[0], skip_special_tokens=True)