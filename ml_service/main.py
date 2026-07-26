"""
FastAPI-Anwendung des Summarization-Microservice (Container 2: ml-service).

Stellt zwei Endpunkte bereit:
- POST /summarize: nimmt Text entgegen, gibt Zusammenfassung + Modellname zurück
- GET  /health:    einfacher Health-Check für die Dash-App bzw. Orchestrierung
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ml_service import config
from ml_service.summarizer import summarize_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Document Summarization Service")


class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Zu Zusammenfassender Textabschnitt")


class SummarizeResponse(BaseModel):
    summary: str
    model_name: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/summarize", response_model=SummarizeResponse)
def summarize(request: SummarizeRequest) -> SummarizeResponse:
    try:
        summary = summarize_text(request.text)
    except Exception as exc:  # noqa: BLE001 - Modellfehler sollen als 500 an den Client zurückgemeldet werden
        logger.exception("Fehler bei der Zusammenfassung")
        raise HTTPException(
            status_code=500, detail="Die Zusammenfassung konnte nicht erstellt werden."
        ) from exc

    return SummarizeResponse(summary=summary, model_name=config.MODEL_NAME)
