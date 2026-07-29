"""
HTTP-Client für die Kommunikation mit dem Summarization-Microservice
(Container 2: ml-service).

Die Trennung von Anwendungslogik (Container 1) und Modell-Inferenz
(Container 2) folgt dem Konzept: Das rechenintensive Modell kann so
unabhängig skaliert oder ausgetauscht werden, ohne die Dash-Anwendung
anzufassen.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass

import requests

from app import config


class MLServiceError(Exception):
    """Wird ausgelöst, wenn der ML-Service nicht erreichbar ist oder einen Fehler meldet."""


@dataclass
class SummaryResult:
    """Ergebnis eines Summarization-Aufrufs inklusive Kennzahlen für die UI."""

    summary: str
    model_name: str
    processing_time_seconds: float
    input_characters: int
    summary_characters: int
    extractive_coverage: float  # Anteil der Zusammenfassung, der aus dem Original stammt (0.0–1.0)

    @property
    def compression_rate(self) -> float:
        """Verhältnis von Zusammenfassung zu Originaltext (kleiner = kompakter)."""
        if self.input_characters == 0:
            return 0.0
        return round(self.summary_characters / self.input_characters, 3)


def summarize(text_chunks: list[str]) -> SummaryResult:
    """
    Ruft den ML-Service für jeden Textabschnitt einzeln auf und fügt die
    Teilzusammenfassungen zu einer Gesamtzusammenfassung zusammen.

    Bei mehreren Abschnitten (langes Dokument) wird "map-reduce"-artig
    vorgegangen: jeder Abschnitt wird separat zusammengefasst, die
    Teilergebnisse werden anschließend aneinandergereiht. Das hält die
    Implementierung einfach und vermeidet einen zweiten Modellaufruf.
    """
    start_time = time.perf_counter()
    partial_summaries = []
    model_name = "unknown"

    for chunk in text_chunks:
        response = _call_service(chunk)
        partial_summaries.append(response["summary"].strip())
        model_name = response.get("model_name", model_name)

    full_summary = " ".join(partial_summaries).strip()
    elapsed = time.perf_counter() - start_time

    original_text = " ".join(text_chunks)
    input_chars = sum(len(c) for c in text_chunks)
    coverage = calculate_extractive_coverage(original_text, full_summary)

    return SummaryResult(
        summary=full_summary,
        model_name=model_name,
        processing_time_seconds=round(elapsed, 2),
        input_characters=input_chars,
        summary_characters=len(full_summary),
        extractive_coverage=coverage,
    )


def _call_service(text: str) -> dict:
    try:
        response = requests.post(
            f"{config.ML_SERVICE_URL}/summarize",
            json={"text": text},
            timeout=config.ML_SERVICE_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as exc:
        raise MLServiceError(
            "Der Zusammenfassungsdienst ist aktuell nicht erreichbar. "
            "Bitte versuche es in Kürze erneut."
        ) from exc


def check_health() -> bool:
    """Prüft, ob der ML-Service erreichbar ist (für einen Status-Indikator in der UI)."""
    try:
        response = requests.get(f"{config.ML_SERVICE_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def _tokenize(text: str) -> list[str]:
    """
    Sprachunabhängige Tokenisierung durch einfache Wortgrenzenerkennung.
    Funktioniert identisch für Deutsch, Englisch und andere Sprachen mit
    lateinischer Schrift, da keine Stoppwörter oder Sprachregeln verwendet
    werden.
    """
    return re.findall(r"\w+", text.lower())


def calculate_extractive_coverage(original_text: str, summary_text: str) -> float:
    """
    Berechnet die Extractive Fragment Coverage nach Grusky et al. (2018):
    den Anteil der Wörter in der Zusammenfassung, die aus zusammenhängenden
    Textstellen des Originaldokuments stammen.

    Diese Metrik ist bewusst sprachunabhängig (keine Stoppwörter, kein
    Sprachmodell) und eignet sich daher sowohl für den englischen
    Trainingskontext des Modells als auch für deutschsprachige
    Patentdokumente im produktiven Einsatz.
    """
    source_tokens = _tokenize(original_text)
    summary_tokens = _tokenize(summary_text)

    if not summary_tokens:
        return 0.0

    source_text_joined = " ".join(source_tokens)
    covered_count = 0
    i = 0

    while i < len(summary_tokens):
        match_length = 0
        for j in range(i + 1, len(summary_tokens) + 1):
            candidate = " ".join(summary_tokens[i:j])
            if candidate in source_text_joined:
                match_length = j - i
            else:
                break

        if match_length > 0:
            covered_count += match_length
            i += match_length
        else:
            i += 1

    return round(covered_count / len(summary_tokens), 2)