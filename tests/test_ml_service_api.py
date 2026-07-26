"""
Unit-Tests für die FastAPI-Schicht des ML-Service (ml_service/main.py).

Das eigentliche Transformer-Modell wird gemockt, damit die Tests ohne
GPU/CPU-intensiven Modell-Download laufen und trotzdem die HTTP-Schicht
(Validierung, Statuscodes, Fehlerbehandlung) prüfen.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

from ml_service import main


@pytest.fixture(autouse=True)
def _mock_summarizer(monkeypatch):
    monkeypatch.setattr(main, "summarize_text", lambda text: f"Zusammenfassung von: {text[:20]}")
    yield


client = TestClient(main.app)


def test_health_endpoint_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_summarize_endpoint_returns_summary():
    response = client.post("/summarize", json={"text": "Ein langer Beispieltext für den Test."})
    assert response.status_code == 200
    body = response.json()
    assert "summary" in body
    assert body["model_name"]


def test_summarize_endpoint_rejects_empty_text():
    response = client.post("/summarize", json={"text": ""})
    assert response.status_code == 422  # Pydantic-Validierung: min_length=1


def test_summarize_endpoint_returns_500_on_model_error(monkeypatch):
    def raise_error(text):
        raise RuntimeError("Modellfehler")

    monkeypatch.setattr(main, "summarize_text", raise_error)
    response = client.post("/summarize", json={"text": "Text"})
    assert response.status_code == 500
