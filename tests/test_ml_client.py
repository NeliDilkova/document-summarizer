"""
Unit-Tests für den HTTP-Client des ML-Service (app/ml_client.py).

Der eigentliche Netzwerkaufruf wird mit monkeypatch ersetzt, damit die Tests
schnell und ohne laufenden ml-service-Container ausführbar sind.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import ml_client


class _FakeResponse:
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise ml_client.requests.exceptions.HTTPError("error")

    def json(self):
        return self._json_data


def test_summarize_single_chunk(monkeypatch):
    def fake_post(url, json, timeout):
        assert "summarize" in url
        return _FakeResponse({"summary": "Kurze Zusammenfassung.", "model_name": "facebook/bart-large-cnn"})

    monkeypatch.setattr(ml_client.requests, "post", fake_post)

    result = ml_client.summarize(["Ein langer Ausgangstext."])

    assert result.summary == "Kurze Zusammenfassung."
    assert result.model_name == "facebook/bart-large-cnn"
    assert result.compression_rate > 0


def test_summarize_joins_multiple_chunks(monkeypatch):
    call_count = {"n": 0}

    def fake_post(url, json, timeout):
        call_count["n"] += 1
        return _FakeResponse({"summary": f"Teil {call_count['n']}.", "model_name": "test-model"})

    monkeypatch.setattr(ml_client.requests, "post", fake_post)

    result = ml_client.summarize(["Abschnitt eins.", "Abschnitt zwei."])

    assert result.summary == "Teil 1. Teil 2."
    assert call_count["n"] == 2


def test_summarize_raises_ml_service_error_on_connection_failure(monkeypatch):
    def fake_post(url, json, timeout):
        raise ml_client.requests.exceptions.ConnectionError("service down")

    monkeypatch.setattr(ml_client.requests, "post", fake_post)

    with pytest.raises(ml_client.MLServiceError):
        ml_client.summarize(["Text"])


def test_check_health_returns_true_on_200(monkeypatch):
    monkeypatch.setattr(ml_client.requests, "get", lambda url, timeout: _FakeResponse({}, 200))
    assert ml_client.check_health() is True


def test_check_health_returns_false_on_exception(monkeypatch):
    def fake_get(url, timeout):
        raise ml_client.requests.exceptions.ConnectionError()

    monkeypatch.setattr(ml_client.requests, "get", fake_get)
    assert ml_client.check_health() is False
