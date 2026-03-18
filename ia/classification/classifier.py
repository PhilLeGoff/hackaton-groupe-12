from __future__ import annotations

from ia.nlp.ner import FIELD_DEFINITIONS


DOCUMENT_RULES = {
    "Facture": ["FACTURE", "Numero de facture", "TOTAL TTC", "Date d'echeance"],
    "Devis": ["DEVIS", "Numero de devis", "Date de validite"],
    "RIB": ["IBAN", "BIC", "Releve d'identite bancaire"],
    "Attestation": ["ATTESTATION", "URSSAF", "vigilance"],
    "KBIS": ["KBIS", "RCS", "Greffe"],
}

EXPECTED_FIELDS_BY_TYPE = {
    "Facture": ["invoice_number", "issue_date", "due_date", "supplier_siret", "total_ttc"],
    "Devis": ["quote_number", "issue_date", "valid_until", "supplier_name", "total_ttc"],
    "RIB": ["supplier_name", "bank_name", "iban", "bic", "bank_code", "branch_code", "account_number", "rib_key"],
    "Attestation": ["issue_date", "siret"],
    "KBIS": ["siret"],
    "Document": [],
}


def classify(text: str) -> dict:
    """Classify a document based on its OCR text content.

    Returns {"document_type": str, "confidence": float}.
    """
    document_type = _detect_type(text)
    confidence = _compute_confidence(document_type, text)
    return {"document_type": document_type, "confidence": confidence}


def _detect_type(text: str) -> str:
    """Score each document type by counting keyword matches in the text."""
    text_upper = text.upper()
    best_type = "Document"
    best_score = 0

    for doc_type, markers in DOCUMENT_RULES.items():
        score = sum(1 for marker in markers if marker.upper() in text_upper)
        if score > best_score:
            best_score = score
            best_type = doc_type

    if best_type == "Document":
        text_lower = text.lower()
        if "facture" in text_lower or "fact" in text_lower:
            return "Facture"
        if "devis" in text_lower:
            return "Devis"
        if "iban" in text_lower or "releve d" in text_lower:
            return "RIB"
        if "kbis" in text_lower or "rcs" in text_lower:
            return "KBIS"
        if "urssaf" in text_lower or "attestation" in text_lower:
            return "Attestation"

    return best_type


def _compute_confidence(document_type: str, text: str) -> float:
    """Estimate confidence based on how many expected fields are present."""
    expected = EXPECTED_FIELDS_BY_TYPE.get(document_type, [])
    if not expected:
        return 0.5

    found = 0
    for field_name in expected:
        field_def = FIELD_DEFINITIONS.get(field_name)
        if not field_def:
            continue
        label = field_def["label"]
        if label.lower() in text.lower():
            found += 1

    ratio = found / max(len(expected), 1)
    return round(max(0.35, min(0.99, ratio)), 2)
