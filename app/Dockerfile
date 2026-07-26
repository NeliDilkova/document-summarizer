# Container 1: dash-app
# Enthält Frontend (Dash) und Backend-Logik (PDF-Verarbeitung) in einem Prozess.
FROM python:3.11-slim

WORKDIR /app

COPY app/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Paketstruktur "app.*" beibehalten, damit relative Imports funktionieren.
COPY app /app/app

EXPOSE 8050

CMD ["gunicorn", "--bind", "0.0.0.0:8050", "--workers", "2", "--timeout", "180", "app.main:server"]
