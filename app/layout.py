"""
UI-Layout der Dash-Anwendung.

Setzt die im Konzept beschriebene UI-Skizze um: Header, Upload-Bereich mit
Statusanzeige, zentraler Button, Ergebnisbereich und ein kleiner
Informationsbereich mit Modell-/Qualitätsmetriken. Bewusst minimalistisch
gehalten, damit auch technisch ungeübte Anwält:innen sich sofort zurechtfinden.
"""

from dash import dcc, html

from app import config


def build_layout() -> html.Div:
    return html.Div(
        className="app-container",
        children=[
            # --- Header ---
            html.Div(
                className="header",
                children=[
                    html.H1("Dokumentenzusammenfasser"),
                    html.P("PDF hochladen und automatisch zusammenfassen lassen."),
                    html.P("Max. zulässige Länge: 20 Seiten."),
                    html.P("Max. Datengröße: 20 MB."),
                ],
            ),
            # --- Upload-Bereich ---
            html.Div(
                className="upload-section",
                children=[
                    dcc.Upload(
                        id="pdf-upload",
                        children=html.Div(
                            ["📄 PDF auswählen oder hier ablegen"]
                        ),
                        className="upload-box",
                        multiple=False,
                        accept=".pdf",
                    ),
                    html.Div(id="upload-status", className="status-box"),
                ],
            ),
            # --- Aktionsbereich ---
            html.Div(
                className="action-section",
                children=[
                    html.Button(
                        "▶ Zusammenfassung erstellen",
                        id="summarize-button",
                        n_clicks=0,
                        disabled=True,
                    ),
                    dcc.Loading(
                        id="loading-indicator",
                        type="circle",
                        children=html.Div(id="loading-placeholder"),
                    ),
                ],
            ),
            # --- Ergebnisbereich ---
            html.Div(
                className="result-section",
                children=[
                    html.H3("Generierte Zusammenfassung"),
                    dcc.Textarea(
                        id="summary-output",
                        className="summary-textarea",
                        value="",
                        readOnly=True,
                        placeholder="Die Zusammenfassung erscheint hier, sobald die "
                        "Verarbeitung abgeschlossen ist.",
                    ),
                ],
            ),
            # --- Informationsbereich ---
            html.Div(
                className="info-section",
                children=[
                    html.Div(id="model-info-box", className="info-box"),
                    html.Div(
                        className="privacy-box",
                        children=[
                            html.Strong("⚠ Hinweis: "),
                            html.Span(config.PRIVACY_NOTICE),
                        ],
                    ),
                ],
            ),
            # Zwischenspeicher für extrahierten Text zwischen Callbacks
            # (bewusst client-seitig, damit auf dem Server nichts über die
            # eigentliche Anfrage hinaus gespeichert bleibt).
            dcc.Store(id="extracted-text-store"),
        ],
    )
