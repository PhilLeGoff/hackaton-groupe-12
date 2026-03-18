"""Test classifier on PDF files (requires Tesseract -- run inside Docker).

Usage from project root:
    docker compose -f docker/docker-compose.yml exec backend \
        python -m pytest ia/classification/tests/test_classifier_pdf.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ia.ocr.pipeline import extract_text  # noqa: E402
from ia.classification.classifier import classify  # noqa: E402

DATASET_ROOT = ROOT_DIR / "data" / "generated"

FOLDER_TO_TYPE = {
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


def _load_pdf_samples() -> list[tuple[Path, str]]:
    samples = []
    seen: set[str] = set()
    for folder_rel, expected_type in FOLDER_TO_TYPE.items():
        folder = DATASET_ROOT / folder_rel
        if not folder.exists():
            continue
        for pdf_file in sorted(folder.glob("*.pdf")):
            key = str(pdf_file.resolve())
            if key in seen:
                continue
            seen.add(key)
            samples.append((pdf_file, expected_type))
    return samples


def test_pdf_classification():
    """OCR each PDF then classify -- check accuracy >= 85%."""
    samples = _load_pdf_samples()
    assert len(samples) > 0, f"No PDFs found in {DATASET_ROOT}"

    correct = 0
    total = len(samples)
    type_stats: dict[str, dict[str, int]] = {}

    for pdf_path, expected in samples:
        raw = pdf_path.read_bytes()
        ocr_text = extract_text(raw, "application/pdf", pdf_path.name)
        result = classify(ocr_text)
        predicted = result["document_type"]
        method = result.get("method", "?")
        conf = result["confidence"]

        if expected not in type_stats:
            type_stats[expected] = {"correct": 0, "total": 0}
        type_stats[expected]["total"] += 1

        if predicted == expected:
            correct += 1
            type_stats[expected]["correct"] += 1
            status = "OK"
        else:
            status = "FAIL"

        print(f"[{status}] {pdf_path.name:30s} expected={expected:12s} got={predicted:12s} conf={conf:.2f} method={method}")

    accuracy = correct / total
    print(f"\n{'='*60}")
    print(f"PDF Classification: {correct}/{total} ({accuracy:.1%})")
    print(f"{'='*60}")
    for doc_type, stats in sorted(type_stats.items()):
        type_acc = stats["correct"] / max(stats["total"], 1)
        print(f"  {doc_type:15s}: {stats['correct']}/{stats['total']} ({type_acc:.0%})")

    assert accuracy >= 0.85, f"Accuracy {accuracy:.1%} < 85% threshold"


if __name__ == "__main__":
    print("Loading PDF samples...")
    samples = _load_pdf_samples()
    print(f"Found {len(samples)} PDFs\n")

    if not samples:
        print("No PDFs found! Generate data first.")
        sys.exit(1)

    test_pdf_classification()
    print("\nTest passed!")
