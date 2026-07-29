"""
Einstiegspunkt der Dash-Anwendung (Container 1: dash-app).

Enthält die Callback-Logik, die Frontend-Interaktionen (Upload, Button-Klick)
mit der Backend-Logik (Dateiprüfung, Textextraktion, Vorverarbeitung,
Aufruf des Summarization-Microservice) verbindet. Entspricht dem im Konzept
beschriebenen UML-Sequenzdiagramm.
"""

from __future__ import annotations

import logging

import dash
from dash import Input, Output, State, html
from dash.exceptions import PreventUpdate

from app import config, ml_client, pdf_utils, preprocessing
from app.layout import build_layout

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = dash.Dash(__name__, title="Dokumentenzusammenfasser")
server = app.server  # für WSGI-Server (z. B. gunicorn) im Container
app.layout = build_layout()

MAX_PAGES = 20


@app.callback(
    Output("upload-status", "children"),
    Output("upload-status", "className"),
    Output("extracted-text-store", "data"),
    Output("summarize-button", "disabled"),
    Input("pdf-upload", "contents"),
    State("pdf-upload", "filename"),
    prevent_initial_call=True,
)
def handle_upload(contents: str | None, filename: str | None):
    """
    Validiert und verarbeitet die hochgeladene Datei, sobald sie ausgewählt
    wurde. Extrahierter Text wird nur im Browser zwischengelegt,
    damit auf dem Server keine Kopie über die Anfrage hinaus verbleibt.
    """
    if contents is None or filename is None:
        raise PreventUpdate

    try:
        file_bytes = pdf_utils.decode_upload(contents)
        pdf_utils.validate_file(filename, file_bytes)
        extraction = pdf_utils.extract_text(file_bytes)
    except pdf_utils.InvalidFileError as exc:
        return f"❌ Ungültige Datei: {exc}", "status-box status-error", None, True
    except pdf_utils.NoTextExtractedError as exc:
        return f"❌ {exc}", "status-box status-error", None, True

    if extraction.num_pages > MAX_PAGES:
        status_message = (
            f"⚠ Das Dokument hat {extraction.num_pages} Seiten und überschreitet "
            f"die aktuell erlaubte Grenze von {MAX_PAGES} Seiten.\n"
            "Bitte wende dich an die Administration, wenn größere Dokumente "
            "freigegeben oder zusammengefasst werden sollen."
        )
        return status_message, "status-box status-warning", None, True

    cleaned_text = preprocessing.clean_text(extraction.text)
    status_message = (
        f"✅ '{filename}' erfolgreich verarbeitet "
        f"({extraction.num_pages} Seiten, {extraction.num_characters} Zeichen)."
    )
    return status_message, "status-box status-success", cleaned_text, False


@app.callback(
    Output("summary-output", "value"),
    Output("model-info-box", "children"),
    Input("summarize-button", "n_clicks"),
    State("extracted-text-store", "data"),
    running=[
        (Output("summarize-button", "disabled"), True, False),
        (
            Output("model-info-box", "children"),
            html.Div(
                "⏳ Zusammenfassung wird erstellt. Dies kann je nach "
                "Dokumentlänge einige Sekunden dauern …"
            ),
            html.Div(),
        ),
    ],
    prevent_initial_call=True,
)
def handle_summarize(n_clicks: int, cleaned_text: str | None):
    """Startet die Zusammenfassung, sobald der Nutzer auf den Button klickt."""
    if not cleaned_text:
        raise PreventUpdate

    chunks = preprocessing.chunk_text(cleaned_text)

    try:
        result = ml_client.summarize(chunks)
    except ml_client.MLServiceError as exc:
        return f"⚠ {exc}", html.Div("Modellstatus: nicht erreichbar")

    info_box = html.Div(
        [
            html.P(f"Modell: {result.model_name}"),
            html.P(f"Verarbeitungsdauer: {result.processing_time_seconds} s"),
            html.P(
                [
                    html.Strong("Textnähe zum Original: "),
                    f"{result.extractive_coverage * 100:.0f} % ",
                    html.Span(
                        "(Anteil der Zusammenfassung, der wortwörtlich aus "
                        "zusammenhängenden Textstellen des Originaldokuments "
                        "stammt — ein höherer Wert zeigt, dass sich die "
                        "Zusammenfassung eng am tatsächlichen Dokumentinhalt "
                        "orientiert.)",
                        className="metric-explanation",
                    ),
                ]
            ),
            html.P(
                [
                    html.Strong("Kompressionsrate: "),
                    f"{result.compression_rate}",
                    html.Span(
                        " (Verhältnis der Zeichenanzahl von Zusammenfassung zu "
                        "Originaltext — z. B. bedeutet 0,1, dass die "
                        "Zusammenfassung etwa 10 % der ursprünglichen "
                        "Textlänge hat.)",
                        className="metric-explanation",
                    ),
                ]
            ),
            html.P(f"Abschnitte verarbeitet: {len(chunks)}"),
        ]
    )
    return result.summary, info_box


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.APP_PORT, debug=False)