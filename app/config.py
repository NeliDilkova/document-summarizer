"""
Zentrale Konfiguration der Dash-Anwendung (Container 1: dash-app).

Alle Werte sind über Umgebungsvariablen überschreibbar, damit die Anwendung
ohne Codeänderung in unterschiedlichen Umgebungen (lokal, Docker, Kanzlei-
Server) betrieben werden kann.
"""

import os

# URL des Summarization-Microservice (Container 2). Innerhalb des
# docker-compose-Netzwerks ist das der Servicename "ml-service".
ML_SERVICE_URL: str = os.environ.get("ML_SERVICE_URL", "http://localhost:8001")

# Maximale Dateigröße für den PDF-Upload in Megabyte. Schützt vor
# versehentlich zu großen Uploads und offensichtlichem Missbrauch.
MAX_FILE_SIZE_MB: int = int(os.environ.get("MAX_FILE_SIZE_MB", "20"))
MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024

# Nur PDF-Dateien werden akzeptiert (fachliche Vorgabe: UI zur PDF-Dateieingabe).
ALLOWED_EXTENSION: str = ".pdf"

# Timeout (Sekunden) für den HTTP-Aufruf an den ML-Service. Große Dokumente
# benötigen auf CPU-Hardware spürbar länger als kurze Texte.
ML_SERVICE_TIMEOUT: int = int(os.environ.get("ML_SERVICE_TIMEOUT", "180"))

# Port, auf dem die Dash-App innerhalb des Containers lauscht.
APP_PORT: int = int(os.environ.get("APP_PORT", "8050"))

# Datenschutz-Hinweistext, der in der Oberfläche angezeigt wird (siehe
# Konzept, Abschnitt "Datenschutz und Datensicherheit").
PRIVACY_NOTICE: str = (
    "Die Zusammenfassung ist eine maschinelle Verdichtung und ersetzt keine "
    "fachliche Prüfung durch den Patentanwalt. Hochgeladene Dateien werden nur "
    "für die Dauer der Verarbeitung gespeichert und danach automatisch gelöscht."
)
