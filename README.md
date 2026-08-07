# Dokumentenzusammenfasser

In-House-Tool für ein Patentanwaltsbüro: lädt PDF-Dokumente hoch und erstellt automatisch eine Textzusammenfassung. Entwickelt im Rahmen des Portfolios DLMDSPMLSD01 (Phase 2 – Erarbeitungs-/Reflexionsphase), aufbauend auf dem in Phase 1 entwickelten Konzept.

## Architektur

Zwei Docker-Container in einem gemeinsamen Netzwerk:

| Container | Aufgabe | Port |
|---|---|---|
| `dash-app` | Frontend (Dash) + Backend-Logik: PDF-Upload, Textextraktion, Vorverarbeitung, Aufruf des ML-Service | 8050 |
| `ml-service` | FastAPI-Microservice mit HuggingFace-Modell `facebook/bart-large-cnn` | 8001 |

```
document-summarizer/
├── app/                # Dash-Frontend + Backend-Logik (Container 1)
│   ├── main.py         # Callbacks, Einstiegspunkt
│   ├── layout.py       # UI-Aufbau
│   ├── pdf_utils.py    # Dateiprüfung, Textextraktion
│   ├── preprocessing.py# Textbereinigung, Chunking
│   ├── ml_client.py    # HTTP-Client zum ml-service
│   └── config.py
├── ml_service/          # Summarization-Microservice (Container 2)
│   ├── main.py          # FastAPI-Endpunkte
│   ├── summarizer.py    # Modell-Pipeline
│   └── config.py
├── evaluation/
│   ├── evaluate_model.py   # ROUGE / Verarbeitungszeit / Kompressionsrate
│   └── results/            # Ergebnisse der Bewertung
├── tests/               # Unit-Tests (pytest)
└── docker-compose.yml
└── setup_app.bat   # Setup-Shortcut für Endnutzer
└── start_app.bat   # Start-Shortcut für Endnutzer
└── stop_app.bat    # Stop-Shortcut für Endnutzer
```

## Lokal starten (mit Docker)

Voraussetzung: Docker und Docker Compose sind installiert.

```bash
git clone https://github.com/NeliDilkova/document-summarizer.git
cd document-summarizer
docker compose up --build
```

Anschließend im Browser öffnen: [http://localhost:8050](http://localhost:8050)

Der erste Start dauert etwas länger, da das Zusammenfassungsmodell (~1,6 GB) beim Bau des `ml-service`-Images heruntergeladen wird. Danach läuft alles lokal, ohne Internetverbindung — es werden keine Daten an Dritte übermittelt.

## Über Shortcut, mit Docker im Hintergrund (Endnutzer)

https://github.com/NeliDilkova/document-summarizer.git
Code → download .zip

.zip Ordner lokal entpacken

1. Einmalig im entpackten Ordner: Doppelklick auf setup_app.bat → Build läuft durch, Fenster zeigt Fortschritt, am Ende pause.
2. Danach jederzeit: Doppelklick auf start_app.bat → Container starten (kein Neu-Build), Browser öffnet sich automatisch.
3. Am Ende der Nutzung: Doppelklick auf stop_app.bat → Container werden sauber heruntergefahren.

## Ohne Docker (Entwicklung)

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt -r ml_service/requirements.txt

# Terminal 1
uvicorn ml_service.main:app --port 8001

# Terminal 2
python -m app.main
```

## Tests ausführen

```bash
pip install pytest fastapi httpx
python -m pytest tests/ -v
```

Die Unit-Tests decken die Dateiprüfung, PDF-Textextraktion, Textvorverarbeitung, den HTTP-Client zum ML-Service sowie die FastAPI-Endpunkte ab (Modellaufrufe werden gemockt).

## Modellbewertung

```bash
pip install -r evaluation/requirements.txt
python evaluation/evaluate_model.py --num-samples 30
```

Bewertet `facebook/bart-large-cnn` auf einer Stichprobe des `cnn_dailymail`-Testdatensatzes (technische Evaluation, siehe Hinweis unten). Ergebnis der letzten Ausführung (30 Dokumente, siehe [`evaluation/results/results.json`](evaluation/results/results.json)):

| Kennzahl | Wert |
|---|---|
| ROUGE-1 (F1) | 0,347 |
| ROUGE-2 (F1) | 0,146 |
| ROUGE-L (F1) | 0,253 |
| Verarbeitungszeit (Ø) | 5,53 s / Dokument |
| Verarbeitungszeit (p95) | 6,92 s |
| Kompressionsrate (Ø) | 0,087 (≈ 9 % der Originallänge) |

**Hinweis zur Aussagekraft:** `cnn_dailymail` besteht aus Nachrichtentexten, nicht aus Patentdokumenten. Die Metriken zeigen die technische Leistungsfähigkeit von Modell und Pipeline (Geschwindigkeit, Kompression, Übereinstimmung mit Referenzzusammenfassungen), nicht die fachliche Eignung für Patentanmeldungen. Die inhaltliche Prüfung bleibt Aufgabe der Anwält:innen — die Anwendung liefert ausdrücklich nur eine Unterstützung, keine Rechtsberatung.

## Datenschutz

- Verarbeitung ausschließlich lokal bzw. innerhalb der eigenen Docker-Umgebung, keine Übermittlung an externe Cloud-Dienste.
- Hochgeladene Dateien werden nur für die Dauer der Anfrage im Arbeitsspeicher/Browser-Store gehalten.
- Format- und Größenprüfung vor jeder Verarbeitung (nur PDF, max. 20 MB).

## Lizenz

Erstellt im Rahmen eines Studienportfolios (IU Internationale Hochschule), nicht für produktiven Einsatz vorgesehen.
