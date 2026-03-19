#!/usr/bin/env python3
"""Train a TF-IDF + SVM classifier on generated document datasets.

Usage (from project root):
    python ia/classification/train.py
    python ia/classification/train.py --data-dir data/generated --seed 42
    python ia/classification/train.py --test-size 0.2 --output-dir ia/classification/model

The trained model is saved as a joblib file and can be loaded by classifier.py.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = ROOT_DIR / "data" / "generated"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "model"

FOLDER_TO_LABEL = {
    "factures": "Facture",
    "devis": "Devis",
    "ribs": "RIB",
    "urssaf": "Attestation",
    "attestations_urssaf": "Attestation",
    "kbis": "KBIS",
    # Also support pdfs/ subdirectory structure
    "pdfs/devis": "Devis",
    "pdfs/ribs": "RIB",
    "pdfs/attestations_urssaf": "Attestation",
    "pdfs/kbis": "KBIS",
}

def load_dataset(data_dir: Path) -> tuple[list[str], list[str]]:
    """Load .txt samples (silver layer) and labels from generated dataset directories."""
    texts: list[str] = []
    labels: list[str] = []
    seen_files: set[str] = set()

    for folder_rel, label in FOLDER_TO_LABEL.items():
        folder = data_dir / folder_rel
        if not folder.exists():
            continue
        for txt_file in sorted(folder.glob("*.txt")):
            abs_path = str(txt_file.resolve())
            if abs_path in seen_files:
                continue
            seen_files.add(abs_path)
            text = txt_file.read_text(encoding="utf-8").strip()
            if text:
                texts.append(text)
                labels.append(label)

    return texts, labels


def train_model(
    texts: list[str],
    labels: list[str],
    test_size: float = 0.2,
    seed: int = 42,
) -> tuple[Pipeline, dict]:
    """Train TF-IDF + LinearSVC and return (model, metrics)."""
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=test_size, random_state=seed, stratify=labels,
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 2),
            sublinear_tf=True,
            strip_accents="unicode",
        )),
        ("svm", LinearSVC(
            C=1.0,
            max_iter=10000,
            class_weight="balanced",
            random_state=seed,
        )),
    ])

    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    report = classification_report(y_test, y_pred, output_dict=True)
    cm = confusion_matrix(y_test, y_pred, labels=sorted(set(labels)))

    metrics = {
        "train_size": len(X_train),
        "test_size": len(X_test),
        "accuracy": report["accuracy"],
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
        "labels": sorted(set(labels)),
    }

    print(f"\nTrain: {len(X_train)} | Test: {len(X_test)}")
    print(f"Accuracy: {report['accuracy']:.2%}")
    print(f"\n{classification_report(y_test, y_pred)}")
    print("Confusion Matrix:")
    label_list = sorted(set(labels))
    header = "            " + "  ".join(f"{l:>12s}" for l in label_list)
    print(header)
    for i, row_label in enumerate(label_list):
        row = "  ".join(f"{cm[i][j]:>12d}" for j in range(len(label_list)))
        print(f"{row_label:>12s}{row}")

    return pipeline, metrics


def main():
    parser = argparse.ArgumentParser(description="Train TF-IDF + SVM document classifier")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    print(f"Loading data from {args.data_dir}...")
    texts, labels = load_dataset(args.data_dir)

    if len(texts) < 10:
        print(f"Only {len(texts)} samples found. Need at least 10.")
        print("Generate data first: python data/generators/generate_large_dataset.py --count 100 --seed 42")
        sys.exit(1)

    print(f"Loaded {len(texts)} samples:")
    for label, count in sorted(Counter(labels).items()):
        print(f"  {label}: {count}")

    pipeline, metrics = train_model(texts, labels, args.test_size, args.seed)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    model_path = args.output_dir / "tfidf_svm.joblib"
    metrics_path = args.output_dir / "metrics.json"

    joblib.dump(pipeline, model_path)
    metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\nModel saved to {model_path}")
    print(f"Metrics saved to {metrics_path}")


if __name__ == "__main__":
    main()
