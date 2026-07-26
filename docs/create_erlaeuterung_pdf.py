"""Erzeugt das 1-seitige DIN-A4-Erläuterungsdokument für Phase 2 (PebblePad-Abgabe)."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    ListFlowable,
    ListItem,
)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

pdfmetrics.registerFont(TTFont("Inter", "/tmp/fonts/Inter-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Inter-Bold", "/tmp/fonts/Inter-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DMSans-Bold", "/tmp/fonts/DMSans-Bold.ttf"))

TEXT = HexColor("#28251D")
MUTED = HexColor("#7A7974")
ACCENT = HexColor("#01696F")

OUTPUT_PATH = "/home/user/workspace/document-summarizer/docs/Dilkova-Gnoyke_Neli_UPS10753889_DLMDSPMLSD01_P2_Erlaeuterung.pdf"
REPO_URL = "https://github.com/NeliDilkova/document-summarizer"

doc = SimpleDocTemplate(
    OUTPUT_PATH,
    pagesize=A4,
    title="Erläuterung Phase 2 – Dokumentenzusammenfasser",
    author="Perplexity Computer",
    topMargin=18 * mm,
    bottomMargin=16 * mm,
    leftMargin=20 * mm,
    rightMargin=20 * mm,
)

styles = {
    "title": ParagraphStyle(
        "title", fontName="DMSans-Bold", fontSize=17, leading=21,
        textColor=TEXT, spaceAfter=2,
    ),
    "subtitle": ParagraphStyle(
        "subtitle", fontName="Inter", fontSize=10, leading=13,
        textColor=MUTED, spaceAfter=10,
    ),
    "h2": ParagraphStyle(
        "h2", fontName="Inter-Bold", fontSize=11.5, leading=14,
        textColor=ACCENT, spaceBefore=9, spaceAfter=4,
    ),
    "body": ParagraphStyle(
        "body", fontName="Inter", fontSize=9.5, leading=13.5,
        textColor=TEXT, alignment=TA_LEFT, spaceAfter=4,
    ),
    "bullet": ParagraphStyle(
        "bullet", fontName="Inter", fontSize=9.5, leading=13,
        textColor=TEXT, leftIndent=0,
    ),
    "small": ParagraphStyle(
        "small", fontName="Inter", fontSize=8.3, leading=11,
        textColor=MUTED,
    ),
}

story = []

story.append(Paragraph("Dokumentenzusammenfasser – Erläuterung zur Umsetzung", styles["title"]))
story.append(Paragraph("Phase 2: Erarbeitungs-/Reflexionsphase &nbsp;|&nbsp; Portfolio DLMDSPMLSD01", styles["subtitle"]))

story.append(Paragraph("Umsetzung", styles["h2"]))
story.append(Paragraph(
    "Das in Phase 1 festgelegte Konzept wurde vollständig als lauffähige Anwendung umgesetzt: "
    "eine Dash-Weboberfläche zum Hochladen von PDF-Dokumenten und ein separater Microservice, "
    "der die Zusammenfassung erstellt. Beide Komponenten laufen als eigene Docker-Container "
    "(<font name='Inter-Bold'>dash-app</font> und <font name='Inter-Bold'>ml-service</font>) in einem gemeinsamen Netzwerk "
    "und lassen sich mit einem einzigen Befehl (<font name='Inter-Bold'>docker compose up</font>) starten – "
    "plattformunabhängig, wie in der Aufgabenstellung gefordert. Für die Zusammenfassung kommt das "
    "vortrainierte Modell <font name='Inter-Bold'>facebook/bart-large-cnn</font> über eine FastAPI-Schnittstelle zum Einsatz. "
    "Die Backend-Logik (Dateiprüfung, Textextraktion mit pypdf, Textbereinigung und Aufteilung "
    "langer Dokumente) ist bewusst von der Oberfläche getrennt, damit sie unabhängig testbar bleibt.",
    styles["body"],
))

story.append(Paragraph("Vorgehen in dieser Phase", styles["h2"]))
steps = [
    "Projektstruktur angelegt (app/, ml_service/, evaluation/, tests/) entlang der im Konzept skizzierten Architektur.",
    "Dash-Frontend und Backend-Logik implementiert: Upload, Validierung, PDF-Textextraktion, Vorverarbeitung, Ergebnisanzeige.",
    "Summarization-Microservice mit FastAPI und HuggingFace-Modell umgesetzt (Endpunkte /summarize, /health).",
    "Docker-Setup für beide Container erstellt und lokal getestet (docker-compose.yml, zwei Dockerfiles).",
    "21 Unit-Tests für Dateiprüfung, Textvorverarbeitung, ML-Client und ML-Service-API geschrieben – alle bestehen.",
    "Modell auf einer Stichprobe von 30 Dokumenten aus cnn_dailymail bewertet (ROUGE, Verarbeitungszeit, Kompressionsrate).",
    "Öffentliches GitHub-Repository eingerichtet, Code mit Commit-Historie versioniert und gepusht.",
]
story.append(ListFlowable(
    [ListItem(Paragraph(s, styles["bullet"]), spaceAfter=3) for s in steps],
    bulletType="bullet", start="•", leftIndent=12,
))

story.append(Paragraph("Modellbewertung", styles["h2"]))
story.append(Paragraph(
    "Bewertet wurde facebook/bart-large-cnn auf 30 Dokumenten des cnn_dailymail-Testdatensatzes "
    "(Skript: evaluation/evaluate_model.py). Da es sich um Nachrichtentexte statt Patentdokumente handelt, "
    "zeigen die Werte die technische Leistungsfähigkeit von Modell und Pipeline, nicht die fachliche Eignung "
    "für Patentanmeldungen.",
    styles["body"],
))

table_data = [
    ["ROUGE-1 (F1)", "ROUGE-2 (F1)", "ROUGE-L (F1)", "Zeit / Dok.", "Kompressionsrate"],
    ["0,347", "0,146", "0,253", "5,53 s (Ø)", "≈ 9 %"],
]
table = Table(table_data, colWidths=[68 * mm, 26 * mm, 26 * mm, 24 * mm, 30 * mm])
table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#0F5C5C")),
    ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
    ("FONTNAME", (0, 0), (-1, 0), "Inter-Bold"),
    ("FONTNAME", (0, 1), (-1, 1), "Inter"),
    ("FONTSIZE", (0, 0), (-1, -1), 8.7),
    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#D4D1CA")),
    ("ROWBACKGROUNDS", (0, 1), (-1, 1), [HexColor("#F7F6F2")]),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
]))
story.append(table)
story.append(Spacer(1, 4))

story.append(Paragraph("Code-Dokumentation & Versionsverwaltung", styles["h2"]))
story.append(Paragraph(
    "Der gesamte Code ist mit deutschsprachigen Docstrings und Kommentaren versehen, die Entscheidungen "
    "(z. B. Trennung von Frontend/Backend, Chunking langer Dokumente) begründen statt nur zu beschreiben, "
    "was der Code tut. Die Versionierung erfolgt über Git; das Repository ist öffentlich einsehbar unter:",
    styles["body"],
))
story.append(Paragraph(
    f'<a href="{REPO_URL}" color="#01696F"><font name="Inter-Bold">{REPO_URL}</font></a>',
    styles["body"],
))

story.append(Spacer(1, 6))
story.append(Paragraph(
    "Erstellt von Neli Dilkova-Gnoyke (Matrikelnummer UPS10753889) · Portfolio DLMDSPMLSD01 · Juli 2026",
    styles["small"],
))

doc.build(story)
print(f"PDF erstellt: {OUTPUT_PATH}")
