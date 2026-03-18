"""Tests for the document classifier on generated datasets.

Run from the project root:
    python -m pytest ia/classification/tests/test_classifier.py -v
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ia.classification.classifier import classify  # noqa: E402

DATASET_ROOT = ROOT_DIR / "data" / "generated"

FOLDER_TO_TYPE = {
    "factures": "Facture",
    "pdfs/devis": "Devis",
    "pdfs/ribs": "RIB",
    "pdfs/attestations_urssaf": "Attestation",
    "pdfs/kbis": "KBIS",
    # Flat structure fallback
    "devis": "Devis",
    "ribs": "RIB",
    "attestations_urssaf": "Attestation",
    "kbis": "KBIS",
}


def _load_test_data() -> list[tuple[str, str]]:
    """Load (text_content, expected_type) pairs from generated TXT files."""
    samples = []
    seen: set[str] = set()
    for folder_rel, expected_type in FOLDER_TO_TYPE.items():
        folder = DATASET_ROOT / folder_rel
        if not folder.exists():
            continue
        for txt_file in sorted(folder.glob("*.txt")):
            key = str(txt_file.resolve())
            if key in seen:
                continue
            seen.add(key)
            text = txt_file.read_text(encoding="utf-8")
            if text.strip():
                samples.append((text, expected_type))
    return samples


def test_classification_accuracy():
    """Test that classifier achieves >= 90% accuracy on generated dataset."""
    samples = _load_test_data()
    assert len(samples) > 0, (
        f"No test data found in {DATASET_ROOT}. "
        "Run the generators first."
    )

    correct = 0
    total = len(samples)
    errors = []
    type_stats: dict[str, dict[str, int]] = {}

    for text, expected in samples:
        result = classify(text)
        predicted = result["document_type"]
        method = result.get("method", "unknown")

        if expected not in type_stats:
            type_stats[expected] = {"correct": 0, "total": 0}
        type_stats[expected]["total"] += 1

        if predicted == expected:
            correct += 1
            type_stats[expected]["correct"] += 1
        else:
            errors.append(
                f"  Expected={expected}, Got={predicted} (confidence={result['confidence']}, method={method})"
            )

    accuracy = correct / total
    print(f"\n{'='*60}")
    print(f"Classification Results: {correct}/{total} ({accuracy:.1%})")
    print(f"{'='*60}")

    for doc_type, stats in sorted(type_stats.items()):
        type_acc = stats["correct"] / max(stats["total"], 1)
        print(f"  {doc_type:15s}: {stats['correct']}/{stats['total']} ({type_acc:.0%})")

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for e in errors[:10]:
            print(e)

    assert accuracy >= 0.90, f"Accuracy {accuracy:.1%} < 90% threshold"


def test_classification_returns_valid_types():
    """Test that classifier always returns a known document type."""
    valid_types = {"Facture", "Devis", "RIB", "Attestation", "KBIS", "Document"}
    samples = _load_test_data()
    for text, _ in samples[:10]:
        result = classify(text)
        assert result["document_type"] in valid_types, f"Unknown type: {result['document_type']}"
        assert 0.0 <= result["confidence"] <= 1.0, f"Bad confidence: {result['confidence']}"


def test_classification_has_method():
    """Test that classifier returns the method used."""
    samples = _load_test_data()
    if not samples:
        return
    result = classify(samples[0][0])
    assert "method" in result, "Missing 'method' key in classify() result"
    assert result["method"] in {"tfidf-svm", "zero-shot", "keywords", "zero-shot-error", "svm-error"}


def test_empty_text():
    """Test classifier handles empty/minimal text."""
    result = classify("")
    assert result["document_type"] == "Document"

    result = classify("hello world")
    assert result["document_type"] is not None


def test_kbis_classification():
    """Test that KBIS documents are correctly classified."""
    kbis_text = """EXTRAIT KBIS

    Denomination : Martin SAS
    Forme juridique : Societe par actions simplifiee (SAS)
    Capital social : 50 000 EUR
    SIREN : 123456789
    SIRET : 12345678901234
    RCS : RCS Paris 123456789
    Greffe : Paris
    Date d'immatriculation : 2020-01-15
    Dirigeant : Jean Martin
    """
    result = classify(kbis_text)
    assert result["document_type"] == "KBIS", f"Expected KBIS, got {result['document_type']}"


if __name__ == "__main__":
    print("Loading test data...")
    samples = _load_test_data()
    print(f"Found {len(samples)} samples")

    if not samples:
        print("No data! Generate first.")
        sys.exit(1)

    print("\nRunning classification on all samples...\n")
    test_classification_accuracy()
    test_classification_returns_valid_types()
    test_classification_has_method()
    test_empty_text()
    test_kbis_classification()
    print("\nAll tests passed!")
