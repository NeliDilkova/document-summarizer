"""
Dateiprüfung und Textextraktion aus PDF-Dokumenten (Backend-Logik).

Dieses Modul ist bewusst von der Dash-Oberfläche getrennt (siehe Konzept,
Abschnitt "Softwarearchitektur"), damit die PDF-Verarbeitung unabhängig
getestet und bei Bedarf ausgetauscht werden kann (z. B. gegen eine andere
Extraktionsbibliothek).
"""

from __future__ import annotations

import base64
import io
import logging
from dataclasses import dataclass

from pypdf import PdfReader

from app import config

logger = logging.getLogger(__name__)


class InvalidFileError(Exception):
    """Wird ausgelöst, wenn die hochgeladene Datei nicht verarbeitet werden darf."""


class NoTextExtractedError(Exception):
    """Wird ausgelöst, wenn aus dem PDF kein verwertbarer Text extrahiert werden kann."""


@dataclass
class ExtractionResult:
    """Ergebnis der PDF-Textextraktion inklusive Metadaten für die UI."""

    text: str
    num_pages: int
    num_characters: int


def decode_upload(contents: str) -> bytes:
    """
    Wandelt den von dash-core-components gelieferten Base64-String
    (Format: "data:<mime>;base64,<payload>") in Rohbytes um.
    """
    try:
        _, encoded = contents.split(",", 1)
        return base64.b64decode(encoded)
    except (ValueError, base64.binascii.Error) as exc:  # type: ignore[attr-defined]
        raise InvalidFileError("Die Datei konnte nicht dekodiert werden.") from exc


def validate_file(filename: str, file_bytes: bytes) -> None:
    """
    Prüft Dateiformat und Dateigröße, bevor überhaupt versucht wird, den
    Text zu extrahieren. Entspricht der Pflichtanforderung "Validierung von
    Dateiformaten, Größenbegrenzung" aus dem Konzept.
    """
    if not filename.lower().endswith(config.ALLOWED_EXTENSION):
        raise InvalidFileError(
            f"Nur PDF-Dateien werden unterstützt (erhalten: '{filename}')."
        )

    if len(file_bytes) == 0:
        raise InvalidFileError("Die hochgeladene Datei ist leer.")

    if len(file_bytes) > config.MAX_FILE_SIZE_BYTES:
        raise InvalidFileError(
            f"Die Datei ist größer als das erlaubte Limit von "
            f"{config.MAX_FILE_SIZE_MB} MB."
        )


def extract_text(file_bytes: bytes) -> ExtractionResult:
    """
    Extrahiert den Text aus allen Seiten eines PDF-Dokuments.

    Raises:
        NoTextExtractedError: wenn das PDF beschädigt ist oder keinen
            maschinenlesbaren Text enthält (z. B. reine Scan-PDFs ohne OCR).
    """
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
    except Exception as exc:  # noqa: BLE001 - bewusst breit, da pypdf verschiedene Fehler wirft
        raise NoTextExtractedError(
            "Die Datei konnte nicht als PDF gelesen werden."
        ) from exc

    pages_text = []
    for page in reader.pages:
        try:
            pages_text.append(page.extract_text() or "")
        except Exception:  # noqa: BLE001 - einzelne defekte Seiten sollen nicht die ganze Extraktion stoppen
            logger.warning("Konnte Text einer Seite nicht extrahieren, überspringe.")
            pages_text.append("")

    full_text = "\n".join(pages_text).strip()

    if not full_text:
        raise NoTextExtractedError(
            "Aus diesem PDF konnte kein Text extrahiert werden. "
            "Vermutlich handelt es sich um ein gescanntes Dokument ohne OCR-Text."
        )

    return ExtractionResult(
        text=full_text,
        num_pages=len(reader.pages),
        num_characters=len(full_text),
    )
