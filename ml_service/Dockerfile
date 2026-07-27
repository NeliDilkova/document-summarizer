# Container 2: ml-service
# Nimmt Text entgegen und liefert eine Zusammenfassung per HTTP zurück.
FROM python:3.11-slim

WORKDIR /app

COPY ml_service/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY ml_service /app/ml_service

RUN python -c "from transformers import pipeline; pipeline('summarization', model='facebook/bart-large-cnn')"

EXPOSE 8001

CMD ["uvicorn", "ml_service.main:app", "--host", "0.0.0.0", "--port", "8001"]
