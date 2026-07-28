"""Konfiguration des Summarization-Microservice (Container 2: ml-service)."""

import os

# Vortrainiertes Modell von HuggingFace. facebook/bart-large-cnn wird im
# Konzept als Zielmodell genannt (siehe UI-Skizze "Modell-Informationen").
# Über die Umgebungsvariable SUMMARIZATION_MODEL kann bei Bedarf ein
# schnelleres/kleineres Modell eingesetzt werden, ohne Code zu ändern —
# das erfüllt die im Konzept geforderte Austauschbarkeit des Modells.
MODEL_NAME: str = os.environ.get("SUMMARIZATION_MODEL", "facebook/bart-large-cnn")

# Grenzwerte für die Generierung. Werte orientieren sich an gängigen
# Empfehlungen für Nachrichtentext-Zusammenfassung (CNN/DailyMail-Domäne).
# Bei Austausch des Modells, müssen auch diese Parameter angepasst werden.
MAX_SUMMARY_TOKENS: int = int(os.environ.get("MAX_SUMMARY_TOKENS", "150"))
MIN_SUMMARY_TOKENS: int = int(os.environ.get("MIN_SUMMARY_TOKENS", "30"))

SERVICE_PORT: int = int(os.environ.get("ML_SERVICE_PORT", "8001"))
