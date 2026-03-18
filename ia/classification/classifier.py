from __future__ import annotations

import logging
from pathlib import Path

from ia.nlp.ner import FIELD_DEFINITIONS

logger = logging.getLogger("docuscan.classifier")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CANDIDATE_LABELS = ["Facture", "Devis", "RIB", "Attestation URSSAF", "KBIS"]

LABEL_MAPPING = {
    "Attestation URSSAF": "Attestation",
}

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
    "Attestation": ["issue_date", "siret", "certificate_id", "naf_code"],
    "KBIS": ["siret", "siren", "denomination", "forme_juridique", "rcs", "greffe", "dirigeant"],
    "Document": [],
}

# ---------------------------------------------------------------------------
# TF-IDF + SVM model (lazy loaded — fastest method)
# ---------------------------------------------------------------------------

_svm_model = None
_svm_load_attempted = False

MODEL_DIR = Path(__file__).resolve().parent / "model"


def _get_svm_model():
    """Lazy-load the trained TF-IDF + SVM model from disk."""
    global _svm_model, _svm_load_attempted
    if _svm_load_attempted:
        return _svm_model
    _svm_load_attempted = True
    model_path = MODEL_DIR / "tfidf_svm.joblib"
    if not model_path.exists():
        logger.info(f"No SVM model found at {model_path}")
        return None
    try:
        import joblib
        _svm_model = joblib.load(model_path)
        logger.info("TF-IDF + SVM model loaded")
    except Exception as e:
        logger.warning(f"Failed to load SVM model: {e}")
        _svm_model = None
    return _svm_model


# ---------------------------------------------------------------------------
# Zero-shot model (lazy loaded — slower but no training needed)
# ---------------------------------------------------------------------------

_zs_pipeline = None
_zs_load_attempted = False


def _get_zero_shot_pipeline():
    """Lazy-load the zero-shot classification pipeline (XLM-RoBERTa)."""
    global _zs_pipeline, _zs_load_attempted
    if _zs_load_attempted:
        return _zs_pipeline
    _zs_load_attempted = True
    try:
        from transformers import pipeline as hf_pipeline
        _zs_pipeline = hf_pipeline(
            "zero-shot-classification",
            model="joeddav/xlm-roberta-large-xnli",
            device=-1,
        )
        logger.info("Zero-shot classification model loaded")
    except Exception as e:
        logger.warning(f"Zero-shot model unavailable: {e}")
        _zs_pipeline = None
    return _zs_pipeline


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify(text: str) -> dict:
    """Classify a document based on its OCR text content.

    Priority: TF-IDF+SVM (fast) -> zero-shot NLI (accurate) -> keywords (fallback).
    Returns {"document_type": str, "confidence": float, "method": str}.
    """
    # 1. Try TF-IDF + SVM (fastest, needs training)
    svm = _get_svm_model()
    if svm is not None:
        result = _classify_svm(svm, text)
        if result["confidence"] >= 0.5:
            return result

    # 2. Try zero-shot NLI (slower, no training needed)
    zs = _get_zero_shot_pipeline()
    if zs is not None:
        result = _classify_zero_shot(zs, text)
        if result["confidence"] >= 0.4:
            return result

    # 3. Keyword fallback (always works)
    return _classify_keywords(text)


# ---------------------------------------------------------------------------
# TF-IDF + SVM classification
# ---------------------------------------------------------------------------

def _classify_svm(model, text: str) -> dict:
    """Run TF-IDF + SVM classification."""
    truncated = text.strip()[:3000]
    if not truncated:
        return {"document_type": "Document", "confidence": 0.0, "method": "svm-empty"}
    try:
        predicted = model.predict([truncated])[0]
        # Get decision function scores for confidence estimation
        decision = model.decision_function([truncated])[0]
        if hasattr(decision, '__len__'):
            # Multi-class: use softmax-like normalization
            import numpy as np
            exp_scores = np.exp(decision - np.max(decision))
            probs = exp_scores / exp_scores.sum()
            confidence = round(float(np.max(probs)), 2)
        else:
            # Binary: sigmoid
            import numpy as np
            confidence = round(float(1.0 / (1.0 + np.exp(-abs(decision)))), 2)

        return {
            "document_type": predicted,
            "confidence": confidence,
            "method": "tfidf-svm",
        }
    except Exception as e:
        logger.warning(f"SVM inference failed: {e}")
        return {"document_type": "Document", "confidence": 0.0, "method": "svm-error"}


# ---------------------------------------------------------------------------
# Zero-shot classification
# ---------------------------------------------------------------------------

def _classify_zero_shot(zs_pipeline, text: str) -> dict:
    """Run zero-shot classification on truncated text."""
    truncated = text.strip()[:1500]
    if not truncated:
        return {"document_type": "Document", "confidence": 0.0, "method": "zero-shot-empty"}
    try:
        result = zs_pipeline(
            truncated,
            candidate_labels=CANDIDATE_LABELS,
            hypothesis_template="Ce document est un {}.",
        )
        raw_label = result["labels"][0]
        label = LABEL_MAPPING.get(raw_label, raw_label)
        confidence = round(result["scores"][0], 2)
        return {
            "document_type": label,
            "confidence": confidence,
            "method": "zero-shot",
            "all_scores": {
                LABEL_MAPPING.get(l, l): round(s, 3)
                for l, s in zip(result["labels"], result["scores"])
            },
        }
    except Exception as e:
        logger.warning(f"Zero-shot inference failed: {e}")
        return {"document_type": "Document", "confidence": 0.0, "method": "zero-shot-error"}


# ---------------------------------------------------------------------------
# Keyword fallback (original logic)
# ---------------------------------------------------------------------------

def _classify_keywords(text: str) -> dict:
    """Classify using keyword matching (fallback)."""
    document_type = _detect_type(text)
    confidence = _compute_confidence(document_type, text)
    return {"document_type": document_type, "confidence": confidence, "method": "keywords"}


def _detect_type(text: str) -> str:
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
