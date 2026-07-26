"""
Modellbewertung des Summarization-Modells (facebook/bart-large-cnn) auf einer
Stichprobe des cnn_dailymail-Datensatzes.

Gemessene Kennzahlen (siehe Aufgabenstellung "standardmäßige
Leistungskennzahlen"):
  - ROUGE-1 / ROUGE-2 / ROUGE-L (F1): Überlappung mit menschlicher
    Referenzzusammenfassung ("highlights" im Datensatz)
  - Verarbeitungszeit pro Dokument (Sekunden)
  - Kompressionsrate: Verhältnis Zusammenfassung/Originaltext (Zeichen)

Wichtig (siehe Konzept, Abschnitt "Grenzen der Bewertung"): cnn_dailymail
enthält Nachrichtentexte, keine Patentdokumente. Die Metriken zeigen daher
die technische Leistungsfähigkeit des Modells/der Pipeline, nicht die
fachliche Eignung für Patentanmeldungen — das bleibt Aufgabe der Anwält:innen.

Nutzung:
    python evaluation/evaluate_model.py --num-samples 50 --output evaluation/results/results.json
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pandas as pd
from datasets import load_dataset
from rouge_score import rouge_scorer
from transformers import pipeline

MODEL_NAME = "facebook/bart-large-cnn"
# Hinweis: Der Datensatz ist auf dem HuggingFace Hub unter dem Namespace
# "abisee" verzeichnet (Original-Autor des Datensatzes).
DATASET_NAME = "abisee/cnn_dailymail"
DATASET_VERSION = "3.0.0"


def run_evaluation(num_samples: int, model_name: str = MODEL_NAME) -> dict:
    print(f"Lade Datensatz '{DATASET_NAME}' ({DATASET_VERSION}), Test-Split (Streaming) ...")
    # Streaming vermeidet den Download des kompletten Test-Splits (mehrere
    # hundert MB), da für die Bewertung nur eine Stichprobe benötigt wird.
    dataset = load_dataset(DATASET_NAME, DATASET_VERSION, split="test", streaming=True)
    sample = list(dataset.take(num_samples))

    print(f"Lade Modell '{model_name}' ...")
    summarizer = pipeline("summarization", model=model_name)
    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)

    rows = []
    for example in sample:
        article = example["article"]
        reference_summary = example["highlights"]

        # BART-Modelle haben ein Tokenlimit (~1024 Tokens); überlange Artikel
        # werden auf eine grobe Zeichen-Obergrenze zugeschnitten, damit die
        # Pipeline nicht abbricht. Für die eigentliche Anwendung übernimmt
        # app/preprocessing.py das Chunking langer Dokumente.
        truncated_article = article[:4000]

        start = time.perf_counter()
        generated = summarizer(
            truncated_article, max_length=180, min_length=30, do_sample=False
        )[0]["summary_text"]
        elapsed = time.perf_counter() - start

        scores = scorer.score(reference_summary, generated)
        compression_rate = (
            len(generated) / len(article) if len(article) > 0 else 0.0
        )

        rows.append(
            {
                "rouge1_f": scores["rouge1"].fmeasure,
                "rouge2_f": scores["rouge2"].fmeasure,
                "rougeL_f": scores["rougeL"].fmeasure,
                "processing_time_seconds": elapsed,
                "compression_rate": compression_rate,
                "input_characters": len(article),
                "summary_characters": len(generated),
            }
        )

    df = pd.DataFrame(rows)
    summary_stats = {
        "model_name": model_name,
        "dataset": f"{DATASET_NAME} ({DATASET_VERSION}), test split",
        "num_samples": len(df),
        "rouge1_f_mean": round(df["rouge1_f"].mean(), 4),
        "rouge2_f_mean": round(df["rouge2_f"].mean(), 4),
        "rougeL_f_mean": round(df["rougeL_f"].mean(), 4),
        "processing_time_seconds_mean": round(df["processing_time_seconds"].mean(), 2),
        "processing_time_seconds_p95": round(df["processing_time_seconds"].quantile(0.95), 2),
        "compression_rate_mean": round(df["compression_rate"].mean(), 4),
    }
    return summary_stats, df


def main():
    parser = argparse.ArgumentParser(description="Modellbewertung des Summarization-Modells")
    parser.add_argument("--num-samples", type=int, default=50, help="Anzahl Dokumente aus cnn_dailymail")
    parser.add_argument("--model-name", type=str, default=MODEL_NAME)
    parser.add_argument(
        "--output",
        type=str,
        default="evaluation/results/results.json",
        help="Pfad für die Ergebnis-JSON-Datei",
    )
    args = parser.parse_args()

    summary_stats, df = run_evaluation(args.num_samples, args.model_name)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(summary_stats, f, ensure_ascii=False, indent=2)

    csv_path = output_path.with_suffix(".csv")
    df.to_csv(csv_path, index=False)

    print("\n=== Ergebnisse der Modellbewertung ===")
    for key, value in summary_stats.items():
        print(f"{key}: {value}")
    print(f"\nZusammenfassung gespeichert unter: {output_path}")
    print(f"Detailwerte je Dokument gespeichert unter: {csv_path}")


if __name__ == "__main__":
    main()
