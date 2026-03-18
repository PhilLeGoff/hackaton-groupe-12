#!/usr/bin/env python3
"""Test complet DI2 : fallbacks, edge cases, scenarios anomalies."""
import sys, json, random
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ia.ocr.pipeline import extract_text
from ia.classification.classifier import classify
from ia.nlp.ner import extract as extract_ner
import ia.classification.classifier as cls_mod

print("=" * 60)
print("TEST 1: FALLBACK CLASSIFICATION (sans SVM)")
print("=" * 60)

original_model = cls_mod._svm_model
original_load_attempted = cls_mod._svm_load_attempted
cls_mod._svm_model = None
cls_mod._svm_load_attempted = True

tests = [
    ("Facture", "FACTURE FOURNISSEUR\nNumero: FAC-001\nTotal HT: 1000 EUR\nTotal TTC: 1200 EUR\nSIRET: 12345678901234"),
    ("Devis", "DEVIS\nNumero de devis: DEV-001\nMontant HT: 500 EUR\nDate de validite: 2026-04-01"),
    ("RIB", "RELEVE D IDENTITE BANCAIRE\nIBAN: FR76 1234 5678 9012 3456 7890 123\nBIC: BNPAFRPP"),
    ("Attestation", "ATTESTATION DE VIGILANCE URSSAF\nSIRET: 12345678901234\nDate emission: 2026-01-01"),
    ("KBIS", "EXTRAIT KBIS\nDenomination: Test SARL\nSIREN: 123456789\nRCS Paris"),
]
for expected, text in tests:
    r = classify(text)
    ok = "OK" if r["document_type"] == expected else "FAIL"
    print(f"  {ok} | {expected:12s} -> {r['document_type']:12s} | method={r['method']}")

cls_mod._svm_model = original_model
cls_mod._svm_load_attempted = original_load_attempted

print()
print("=" * 60)
print("TEST 2: FALLBACK KEYWORDS (sans SVM, sans zero-shot)")
print("=" * 60)

cls_mod._svm_model = None
cls_mod._svm_load_attempted = True
orig_zs_pipeline = cls_mod._zs_pipeline
orig_zs_load_attempted = cls_mod._zs_load_attempted
cls_mod._zs_pipeline = None
cls_mod._zs_load_attempted = True

short_tests = [
    ("Facture", "facture montant total ttc ht"),
    ("Devis", "devis prestation validite"),
    ("RIB", "releve identite bancaire iban bic"),
    ("Attestation", "attestation urssaf vigilance cotisations"),
    ("KBIS", "extrait kbis registre commerce societes"),
]
for expected, text in short_tests:
    r = classify(text)
    ok = "OK" if r["document_type"] == expected else "FAIL"
    print(f"  {ok} | {expected:12s} -> {r['document_type']:12s} | method={r['method']}")

cls_mod._svm_model = original_model
cls_mod._svm_load_attempted = original_load_attempted
cls_mod._zs_pipeline = orig_zs_pipeline
cls_mod._zs_load_attempted = orig_zs_load_attempted

print()
print("=" * 60)
print("TEST 3: EDGE CASES")
print("=" * 60)

# Fichier vide
try:
    text = extract_text(b"", "text/plain", "empty.txt")
    print(f"  Texte vide: OCR retourne len={len(text)}")
    if text.strip():
        r = classify(text)
        print(f"  Classification texte vide: type={r['document_type']}")
    else:
        print(f"  Classification texte vide: SKIP (texte vide)")
except Exception as e:
    print(f"  Texte vide: EXCEPTION {type(e).__name__}: {e}")

# Texte random
rng = random.Random(42)
random_text = "".join(rng.choices("abcdefghijklmnop 0123456789", k=200))
r = classify(random_text)
print(f"  Texte random: type={r['document_type']}, method={r['method']}, conf={r['confidence']:.2f}")

# Texte anglais
r = classify("INVOICE number INV-001 Total amount 5000 USD Due date 2026-01-15")
print(f"  Texte anglais: type={r['document_type']}, method={r['method']}")

# NER sur texte vide
entities = extract_ner("")
has = sum(1 for k, v in entities.items() if v and k != "details")
print(f"  NER texte vide: {has} champs")

# NER sur texte random
entities = extract_ner(random_text)
has = sum(1 for k, v in entities.items() if v and k != "details")
print(f"  NER texte random: {has} champs")

# OCR formats
print()
print("  Formats OCR:")
try:
    t = extract_text(b"Hello world test", "text/plain", "test.txt")
    print(f"    text/plain: OK (len={len(t)})")
except Exception as e:
    print(f"    text/plain: FAIL {e}")

try:
    t = extract_text(b"\x89PNG\r\n\x1a\n", "image/png", "bad.png")
    print(f"    PNG corrompu: retourne len={len(t)}")
except Exception as e:
    print(f"    PNG corrompu: EXCEPTION {type(e).__name__} (attendu)")

try:
    t = extract_text(b"not a pdf", "application/pdf", "bad.pdf")
    print(f"    PDF corrompu: retourne len={len(t)}")
except Exception as e:
    print(f"    PDF corrompu: EXCEPTION {type(e).__name__} (attendu)")

print()
print("=" * 60)
print("TEST 4: SCENARIOS ANOMALIES")
print("=" * 60)

DATA_BASE = Path(__file__).resolve().parents[1] / "data" / "generated"
if not DATA_BASE.exists():
    DATA_BASE = Path("/opt/airflow/data/generated")

FOLDERS = {
    "factures": "Facture",
    "pdfs/devis": "Devis",
    "pdfs/ribs": "RIB",
    "pdfs/attestations_urssaf": "Attestation",
    "pdfs/kbis": "KBIS",
}

scenario_stats = Counter()
scenario_class = Counter()
scenario_ner = Counter()

for rel_folder, expected_type in FOLDERS.items():
    folder = DATA_BASE / rel_folder
    if not folder.exists():
        print(f"  SKIP {folder}")
        continue
    jsons = sorted(folder.glob("*.json"))
    for jf in jsons:
        if jf.name == "summary.json":
            continue
        meta = json.loads(jf.read_text())
        scenario = meta.get("scenario", "unknown")

        txt_file = jf.with_suffix(".txt")
        if not txt_file.exists():
            continue

        text = txt_file.read_text()
        cls_result = classify(text)
        entities = extract_ner(text)

        key = f"{expected_type}/{scenario}"
        scenario_stats[key] += 1

        if cls_result["document_type"] == expected_type:
            scenario_class[key] += 1

        has_entities = sum(1 for k, v in entities.items() if v and k != "details") > 0
        if has_entities:
            scenario_ner[key] += 1

print(f"  {'Scenario':<45s} | {'Total':>5s} | {'Class':>5s} | {'NER':>5s}")
print(f"  {'-'*45}-+-{'-'*5}-+-{'-'*5}-+-{'-'*5}")
for key in sorted(scenario_stats.keys()):
    t = scenario_stats[key]
    c = scenario_class[key]
    n = scenario_ner[key]
    status = "OK" if c == t else "FAIL"
    print(f"  {key:<45s} | {t:>5d} | {c:>5d} | {n:>5d}  {status}")

total = sum(scenario_stats.values())
total_c = sum(scenario_class.values())
total_n = sum(scenario_ner.values())
print(f"  {'-'*45}-+-{'-'*5}-+-{'-'*5}-+-{'-'*5}")
print(f"  {'TOTAL':<45s} | {total:>5d} | {total_c:>5d} | {total_n:>5d}")
print(f"\n  Classification: {total_c}/{total} ({total_c/total*100:.1f}%)")
print(f"  NER:            {total_n}/{total} ({total_n/total*100:.1f}%)")
