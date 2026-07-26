# Container 2: ml-service
# Nimmt Text entgegen und liefert eine Zusammenfassung per HTTP zurück.
FROM python:3.11-slim

WORKDIR /app

COPY ml_service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ml_service /app/ml_service

# Modell beim Image-Build bereits herunterladen, damit der erste Request
# nach dem Start nicht durch einen langen Download blockiert wird und die
# Anwendung offline lauffähig ist (Datenschutz-Anforderung: keine
# Datenübermittlung an externe Cloud-Dienste zur Laufzeit).
RUN python -c "from transformers import pipeline; pipeline('summarization', model='facebook/bart-large-cnn')"

EXPOSE 8001

CMD ["uvicorn", "ml_service.main:app", "--host", "0.0.0.0", "--port", "8001"]
