"""Unit-Tests für Dateiprüfung und Textextraktion (app/pdf_utils.py)."""

import base64
import io
import sys
from pathlib import Path

import pytest
from pypdf import PdfWriter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import config, pdf_utils


def _make_pdf_bytes(text_pages: int = 1) -> bytes:
    """Erzeugt ein minimales, gültiges PDF ohne Text (nur leere Seiten) für Tests,
    die reine Dateiformat-/Größenprüfung testen sollen."""
    writer = PdfWriter()
    for _ in range(text_pages):
        writer.add_blank_page(width=200, height=200)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def _to_data_url(file_bytes: bytes) -> str:
    encoded = base64.b64encode(file_bytes).decode("utf-8")
    return f"data:application/pdf;base64,{encoded}"


def test_decode_upload_roundtrip():
    original = b"%PDF-1.4 test content"
    data_url = _to_data_url(original)
    assert pdf_utils.decode_upload(data_url) == original


def test_validate_file_rejects_wrong_extension():
    with pytest.raises(pdf_utils.InvalidFileError):
        pdf_utils.validate_file("dokument.docx", b"irrelevant")


def test_validate_file_rejects_empty_file():
    with pytest.raises(pdf_utils.InvalidFileError):
        pdf_utils.validate_file("dokument.pdf", b"")


def test_validate_file_rejects_oversized_file():
    oversized = b"0" * (config.MAX_FILE_SIZE_BYTES + 1)
    with pytest.raises(pdf_utils.InvalidFileError):
        pdf_utils.validate_file("dokument.pdf", oversized)


def test_validate_file_accepts_valid_pdf():
    valid_bytes = _make_pdf_bytes()
    # Sollte keine Exception auslösen.
    pdf_utils.validate_file("dokument.pdf", valid_bytes)


def test_extract_text_raises_when_pdf_has_no_text():
    blank_pdf = _make_pdf_bytes(text_pages=1)
    with pytest.raises(pdf_utils.NoTextExtractedError):
        pdf_utils.extract_text(blank_pdf)


def test_extract_text_raises_on_corrupted_file():
    with pytest.raises(pdf_utils.NoTextExtractedError):
        pdf_utils.extract_text(b"das ist definitiv kein PDF")
