#!/usr/bin/env python3
"""Benchmark the document classifier on generated datasets.

Produces confusion matrix, precision/recall/F1 per class, and overall accuracy.

Usage:
    python ia/classification/benchmark.py
    python ia/classification/benchmark.py --data-dir data/generated --method all
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ia.classification.classifier import classify  # noqa: E402

DEFAULT_DATA_DIR = ROOT_DIR / "data" / "generated"

FOLDER_TO_LABEL = {
    "factures": "Facture",
    "pdfs/devis": "Devis",
    "pdfs/ribs": "RIB",
    "pdfs/attestations_urssaf": "Attestation",
    "pdfs/kbis": "KBIS",
    "devis": "Devis",
    "ribs": "RIB",
    "attestations_urssaf": "Attestation",
    "kbis": "KBIS",
}


def load_samples(data_dir: Path) -> list[tuple[str, str]]:
    """Load (text, expected_label) pairs from TXT files."""
    samples = []
    seen: set[str] = set()
    for folder_rel, label in FOLDER_TO_LABEL.items():
        folder = data_dir / folder_rel
        if not folder.exists():
            continue
        for txt_file in sorted(folder.glob("*.txt")):
            key = str(txt_file.resolve())
            if key in seen:
                continue
            seen.add(key)
            text = txt_file.read_text(encoding="utf-8").strip()
            if text:
                samples.append((text, label))
    return samples


def run_benchmark(samples: list[tuple[str, str]]) -> dict:
    """Classify all samples and compute metrics."""
    y_true = []
    y_pred = []
    methods = Counter()
    errors = []

    for text, expected in samples:
        result = classify(text)
        predicted = result["document_type"]
        method = result.get("method", "unknown")

        y_true.append(expected)
        y_pred.append(predicted)
        methods[method] += 1

        if predicted != expected:
            errors.append({
                "expected": expected,
                "predicted": predicted,
                "confidence": result.get("confidence", 0),
                "method": method,
                "snippet": text[:80].replace("\n", " "),
            })

    labels = sorted(set(y_true + y_pred))
    label_idx = {l: i for i, l in enumerate(labels)}
    n = len(labels)

    # Build confusion matrix
    cm = [[0] * n for _ in range(n)]
    for t, p in zip(y_true, y_pred):
        cm[label_idx[t]][label_idx[p]] += 1

    # Per-class metrics
    per_class = {}
    for label in labels:
        i = label_idx[label]
        tp = cm[i][i]
        fp = sum(cm[j][i] for j in range(n)) - tp
        fn = sum(cm[i][j] for j in range(n)) - tp
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        support = sum(cm[i])
        per_class[label] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": support,
        }

    correct = sum(cm[i][i] for i in range(n))
    total = len(y_true)
    accuracy = correct / total if total > 0 else 0.0

    return {
        "accuracy": round(accuracy, 4),
        "total": total,
        "correct": correct,
        "labels": labels,
        "confusion_matrix": cm,
        "per_class": per_class,
        "methods": dict(methods),
        "errors": errors[:20],
    }


def print_report(report: dict):
    """Pretty-print the benchmark report."""
    labels = report["labels"]
    cm = report["confusion_matrix"]

    print(f"\n{'=' * 70}")
    print(f"Classification Benchmark: {report['correct']}/{report['total']} ({report['accuracy']:.1%})")
    print(f"{'=' * 70}")

    # Per-class table
    print(f"\n{'Class':>15s}  {'Precision':>9s}  {'Recall':>9s}  {'F1':>9s}  {'Support':>7s}")
    print("-" * 55)
    for label in labels:
        m = report["per_class"][label]
        print(f"{label:>15s}  {m['precision']:>9.2%}  {m['recall']:>9.2%}  {m['f1']:>9.2%}  {m['support']:>7d}")
    print("-" * 55)
    print(f"{'Accuracy':>15s}  {'':>9s}  {'':>9s}  {report['accuracy']:>9.2%}  {report['total']:>7d}")

    # Confusion matrix
    print(f"\nConfusion Matrix:")
    header = " " * 16 + "".join(f"{l:>13s}" for l in labels)
    print(header)
    for i, row_label in enumerate(labels):
        row = "".join(f"{cm[i][j]:>13d}" for j in range(len(labels)))
        print(f"{row_label:>15s} {row}")

    # Methods used
    print(f"\nMethods: {report['methods']}")

    # Errors
    if report["errors"]:
        print(f"\nFirst {len(report['errors'])} errors:")
        for e in report["errors"][:10]:
            print(f"  {e['expected']:>12s} -> {e['predicted']:<12s} (conf={e['confidence']:.2f}, {e['method']})")


def main():
    parser = argparse.ArgumentParser(description="Benchmark document classifier")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output", type=Path, default=None, help="Save report to JSON file")
    args = parser.parse_args()

    samples = load_samples(args.data_dir)
    if not samples:
        print(f"No samples found in {args.data_dir}")
        sys.exit(1)

    print(f"Loaded {len(samples)} samples:")
    for label, count in sorted(Counter(l for _, l in samples).items()):
        print(f"  {label}: {count}")

    report = run_benchmark(samples)
    print_report(report)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"\nReport saved to {args.output}")


if __name__ == "__main__":
    main()
