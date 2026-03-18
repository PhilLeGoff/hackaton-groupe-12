"""Tests for the NER extraction module.

Run from project root:
    python -m pytest ia/nlp/tests/test_ner.py -v
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ia.nlp.ner import extract, _normalize_date  # noqa: E402

DATASET_ROOT = ROOT_DIR / "data" / "generated"


# ---------------------------------------------------------------------------
# Date normalization tests
# ---------------------------------------------------------------------------

def test_normalize_date_iso():
    assert _normalize_date("2026-03-18") == "2026-03-18"


def test_normalize_date_french_slash():
    assert _normalize_date("18/03/2026") == "2026-03-18"


def test_normalize_date_french_dash():
    assert _normalize_date("18-03-2026") == "2026-03-18"


def test_normalize_date_french_text():
    assert _normalize_date("18 mars 2026") == "2026-03-18"


def test_normalize_date_french_text_single_digit():
    assert _normalize_date("3 janvier 2025") == "2025-01-03"


# ---------------------------------------------------------------------------
# Invoice NER tests
# ---------------------------------------------------------------------------

def _load_invoice_pairs() -> list[tuple[str, dict]]:
    """Load (txt_content, json_ground_truth) pairs for invoices."""
    folder = DATASET_ROOT / "factures"
    if not folder.exists():
        return []
    pairs = []
    for json_file in sorted(folder.glob("*.json")):
        if json_file.name == "summary.json":
            continue
        txt_file = json_file.with_suffix(".txt")
        if not txt_file.exists():
            continue
        text = txt_file.read_text(encoding="utf-8")
        ground_truth = json.loads(json_file.read_text(encoding="utf-8"))
        pairs.append((text, ground_truth))
    return pairs


def test_invoice_siret_extraction():
    """Test that NER extracts valid SIRETs from invoices."""
    pairs = _load_invoice_pairs()
    if not pairs:
        return

    found = 0
    for text, gt in pairs:
        result = extract(text)
        details = result.get("details", {})
        supplier_siret = details.get("supplier_siret")
        if supplier_siret and len(supplier_siret.replace(" ", "")) == 14:
            found += 1

    ratio = found / len(pairs)
    assert ratio >= 0.8, f"Only {found}/{len(pairs)} invoices had supplier SIRET extracted"


def test_invoice_amounts_extraction():
    """Test that NER extracts HT and TTC amounts from invoices."""
    pairs = _load_invoice_pairs()
    if not pairs:
        return

    found_ht = 0
    found_ttc = 0
    for text, gt in pairs:
        result = extract(text)
        if result.get("amount_ht"):
            found_ht += 1
        if result.get("amount_ttc"):
            found_ttc += 1

    assert found_ht / len(pairs) >= 0.8, f"Only {found_ht}/{len(pairs)} had HT"
    assert found_ttc / len(pairs) >= 0.8, f"Only {found_ttc}/{len(pairs)} had TTC"


def test_invoice_dates_extraction():
    """Test that NER extracts dates from invoices."""
    pairs = _load_invoice_pairs()
    if not pairs:
        return

    found = 0
    for text, gt in pairs:
        result = extract(text)
        if result.get("issue_date"):
            found += 1

    assert found / len(pairs) >= 0.8, f"Only {found}/{len(pairs)} had issue_date"


# ---------------------------------------------------------------------------
# RIB NER tests
# ---------------------------------------------------------------------------

def _load_rib_pairs() -> list[tuple[str, dict]]:
    folder = DATASET_ROOT / "ribs"
    if not folder.exists():
        folder = DATASET_ROOT / "pdfs" / "ribs"
    if not folder.exists():
        return []
    pairs = []
    for json_file in sorted(folder.glob("*.json")):
        if json_file.name == "summary.json":
            continue
        txt_file = json_file.with_suffix(".txt")
        if not txt_file.exists():
            continue
        text = txt_file.read_text(encoding="utf-8")
        ground_truth = json.loads(json_file.read_text(encoding="utf-8"))
        pairs.append((text, ground_truth))
    return pairs


def test_rib_iban_extraction():
    """Test that NER extracts IBANs from RIBs."""
    pairs = _load_rib_pairs()
    if not pairs:
        return

    found = 0
    for text, gt in pairs:
        result = extract(text)
        if result.get("iban"):
            found += 1

    assert found / len(pairs) >= 0.9, f"Only {found}/{len(pairs)} RIBs had IBAN"


def test_rib_bic_extraction():
    """Test that NER extracts BICs from RIBs."""
    pairs = _load_rib_pairs()
    if not pairs:
        return

    found = 0
    for text, gt in pairs:
        result = extract(text)
        details = result.get("details", {})
        if details.get("bic"):
            found += 1

    assert found / len(pairs) >= 0.9, f"Only {found}/{len(pairs)} RIBs had BIC"


# ---------------------------------------------------------------------------
# KBIS NER tests
# ---------------------------------------------------------------------------

def _load_kbis_pairs() -> list[tuple[str, dict]]:
    folder = DATASET_ROOT / "kbis"
    if not folder.exists():
        folder = DATASET_ROOT / "pdfs" / "kbis"
    if not folder.exists():
        return []
    pairs = []
    for json_file in sorted(folder.glob("*.json")):
        if json_file.name == "summary.json":
            continue
        txt_file = json_file.with_suffix(".txt")
        if not txt_file.exists():
            continue
        text = txt_file.read_text(encoding="utf-8")
        ground_truth = json.loads(json_file.read_text(encoding="utf-8"))
        pairs.append((text, ground_truth))
    return pairs


def test_kbis_siret_extraction():
    """Test that NER extracts SIRET from KBIS documents."""
    pairs = _load_kbis_pairs()
    if not pairs:
        return

    found = 0
    for text, gt in pairs:
        result = extract(text)
        details = result.get("details", {})
        if details.get("siret"):
            found += 1

    assert found / len(pairs) >= 0.9, f"Only {found}/{len(pairs)} KBIS had SIRET"


def test_kbis_denomination_extraction():
    """Test that NER extracts denomination from KBIS documents."""
    pairs = _load_kbis_pairs()
    if not pairs:
        return

    found = 0
    for text, gt in pairs:
        result = extract(text)
        details = result.get("details", {})
        if details.get("denomination"):
            found += 1

    assert found / len(pairs) >= 0.9, f"Only {found}/{len(pairs)} KBIS had denomination"


def test_kbis_rcs_extraction():
    """Test that NER extracts RCS from KBIS documents."""
    pairs = _load_kbis_pairs()
    if not pairs:
        return

    found = 0
    for text, gt in pairs:
        result = extract(text)
        details = result.get("details", {})
        if details.get("rcs"):
            found += 1

    assert found / len(pairs) >= 0.8, f"Only {found}/{len(pairs)} KBIS had RCS"


# ---------------------------------------------------------------------------
# General NER tests
# ---------------------------------------------------------------------------

def test_extract_returns_all_canonical_keys():
    """Test that extract() always returns all expected keys."""
    result = extract("Some random text with no entities.")
    expected_keys = {"siret", "vat", "amount_ht", "amount_ttc", "issue_date",
                     "expiration_date", "company_name", "iban", "details"}
    assert set(result.keys()) == expected_keys


def test_extract_empty_text():
    """Test that extract() handles empty text gracefully."""
    result = extract("")
    assert result["siret"] is None
    assert result["company_name"] is None


def test_extract_comprehensive():
    """Test NER on all available document types, measure field extraction rate."""
    all_results = []

    for folder_name, doc_type in [
        ("factures", "Facture"),
        ("devis", "Devis"),
        ("pdfs/devis", "Devis"),
        ("ribs", "RIB"),
        ("pdfs/ribs", "RIB"),
        ("attestations_urssaf", "Attestation"),
        ("pdfs/attestations_urssaf", "Attestation"),
        ("kbis", "KBIS"),
        ("pdfs/kbis", "KBIS"),
    ]:
        folder = DATASET_ROOT / folder_name
        if not folder.exists():
            continue
        for txt_file in sorted(folder.glob("*.txt"))[:10]:
            text = txt_file.read_text(encoding="utf-8")
            result = extract(text)
            details = result.get("details", {})
            non_null = sum(1 for v in details.values() if v is not None)
            all_results.append((doc_type, non_null, len(details)))

    if not all_results:
        return

    total_fields = sum(r[1] for r in all_results)
    total_possible = sum(r[2] for r in all_results)
    print(f"\nNER Comprehensive: {total_fields} fields extracted across {len(all_results)} documents")
    assert total_fields > 0, "No fields extracted at all"


if __name__ == "__main__":
    print("Running NER tests...\n")
    test_normalize_date_iso()
    test_normalize_date_french_slash()
    test_normalize_date_french_dash()
    test_normalize_date_french_text()
    test_normalize_date_french_text_single_digit()
    test_extract_returns_all_canonical_keys()
    test_extract_empty_text()
    test_invoice_siret_extraction()
    test_invoice_amounts_extraction()
    test_invoice_dates_extraction()
    test_rib_iban_extraction()
    test_rib_bic_extraction()
    test_kbis_siret_extraction()
    test_kbis_denomination_extraction()
    test_kbis_rcs_extraction()
    test_extract_comprehensive()
    print("\nAll NER tests passed!")
