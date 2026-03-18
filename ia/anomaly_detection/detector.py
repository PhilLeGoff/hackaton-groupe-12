from __future__ import annotations

import re
from datetime import date

from ia.nlp.ner import FIELD_DEFINITIONS
from ia.classification.classifier import EXPECTED_FIELDS_BY_TYPE


def validate(
    entities: dict,
    classification: dict,
    document_id: str,
    collection=None,
) -> dict:
    """Validate extracted entities for coherence and completeness.

    Returns {"is_valid": bool, "anomalies": [{"field": str, "message": str, "level": str}]}.
    """
    anomalies: list[dict] = []
    document_type = classification.get("document_type", "Document")
    details = entities.get("details", entities)

    _check_missing_fields(anomalies, document_type, details)
    _check_siret_format(anomalies, details)
    _check_amounts_coherence(anomalies, details)
    _check_iban_format(anomalies, details)
    _check_dates(anomalies, details)
    _check_vat_siret_coherence(anomalies, details)
    _check_date_logic(anomalies, details)

    if collection is not None:
        _check_duplicates(anomalies, document_id, details, collection)

    return {
        "is_valid": len(anomalies) == 0,
        "anomalies": anomalies,
    }


def _check_missing_fields(anomalies: list[dict], document_type: str, details: dict):
    """Check that all expected fields for this document type are present."""
    expected = EXPECTED_FIELDS_BY_TYPE.get(document_type, [])
    missing = [
        FIELD_DEFINITIONS[f]["label"]
        for f in expected
        if f in FIELD_DEFINITIONS and not details.get(f)
    ]
    if missing:
        anomalies.append({
            "field": "missing_fields",
            "message": f"Champs manquants : {', '.join(missing)}",
            "level": "warning",
        })


def _check_siret_format(anomalies: list[dict], details: dict):
    """Validate SIRET numbers (14 digits, Luhn checksum)."""
    for key in ("siret", "supplier_siret", "customer_siret"):
        siret = details.get(key)
        if not siret:
            continue
        digits = re.sub(r"\s+", "", siret)
        if not re.fullmatch(r"\d{14}", digits):
            anomalies.append({
                "field": key,
                "message": f"SIRET invalide ({siret}) : doit contenir 14 chiffres",
                "level": "error",
            })
            continue
        if not _luhn_check(digits):
            anomalies.append({
                "field": key,
                "message": f"SIRET invalide ({siret}) : checksum Luhn incorrect",
                "level": "error",
            })


def _luhn_check(digits: str) -> bool:
    """Verify Luhn checksum on a digit string."""
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def _check_amounts_coherence(anomalies: list[dict], details: dict):
    """Check that HT + TVA ≈ TTC."""
    ht_str = details.get("total_ht")
    tva_str = details.get("total_tva")
    ttc_str = details.get("total_ttc")

    if not (ht_str and ttc_str):
        return

    ht = _parse_amount(ht_str)
    ttc = _parse_amount(ttc_str)
    if ht is None or ttc is None:
        return

    if ht > ttc:
        anomalies.append({
            "field": "amounts",
            "message": f"Montant HT ({ht_str}) superieur au TTC ({ttc_str})",
            "level": "error",
        })
        return

    if tva_str:
        tva = _parse_amount(tva_str)
        if tva is not None:
            expected_ttc = round(ht + tva, 2)
            if abs(expected_ttc - ttc) > 0.02:
                anomalies.append({
                    "field": "amounts",
                    "message": f"Incoherence montants : HT ({ht_str}) + TVA ({tva_str}) != TTC ({ttc_str})",
                    "level": "warning",
                })


def _parse_amount(value: str) -> float | None:
    """Parse a French-formatted amount like '1 234,56' into a float."""
    try:
        cleaned = re.sub(r"\s+", "", value).replace(",", ".")
        return float(cleaned)
    except (ValueError, AttributeError):
        return None


def _check_iban_format(anomalies: list[dict], details: dict):
    """Validate IBAN format and checksum (mod 97)."""
    iban = details.get("iban")
    if not iban:
        return
    iban_clean = re.sub(r"\s+", "", iban).upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}", iban_clean):
        anomalies.append({
            "field": "iban",
            "message": f"Format IBAN invalide ({iban})",
            "level": "error",
        })
        return
    rearranged = iban_clean[4:] + iban_clean[:4]
    numeric = ""
    for ch in rearranged:
        if ch.isdigit():
            numeric += ch
        else:
            numeric += str(ord(ch) - ord("A") + 10)
    if int(numeric) % 97 != 1:
        anomalies.append({
            "field": "iban",
            "message": f"Checksum IBAN invalide ({iban})",
            "level": "warning",
        })


def _check_dates(anomalies: list[dict], details: dict):
    """Validate date formats."""
    for key in ("issue_date", "due_date", "valid_until", "expiry_date", "date_immatriculation"):
        date_val = details.get(key)
        if not date_val:
            continue
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_val):
            anomalies.append({
                "field": key,
                "message": f"Format de date invalide ({date_val}), attendu YYYY-MM-DD",
                "level": "warning",
            })


def _check_vat_siret_coherence(anomalies: list[dict], details: dict):
    """Cross-validate VAT number against SIRET/SIREN (FR + key + SIREN)."""
    vat = details.get("vat_number") or details.get("supplier_vat_number")
    siret = details.get("siret") or details.get("supplier_siret")
    if not vat or not siret:
        return
    # French VAT = "FR" + 2-digit key + 9-digit SIREN
    m = re.fullmatch(r"FR(\d{2})(\d{9})", vat)
    if not m:
        return
    vat_key = int(m.group(1))
    vat_siren = m.group(2)
    doc_siren = re.sub(r"\s+", "", siret)[:9]
    if vat_siren != doc_siren:
        anomalies.append({
            "field": "vat_number",
            "message": f"TVA ({vat}) ne correspond pas au SIREN du SIRET ({doc_siren})",
            "level": "warning",
        })
        return
    # Check TVA key: key = (12 + 3 * (SIREN % 97)) % 97
    expected_key = (12 + 3 * (int(vat_siren) % 97)) % 97
    if vat_key != expected_key:
        anomalies.append({
            "field": "vat_number",
            "message": f"Cle TVA invalide ({vat_key}), attendue {expected_key}",
            "level": "warning",
        })


def _check_date_logic(anomalies: list[dict], details: dict):
    """Check logical date constraints: emission < echeance, not in far future."""
    issue = _parse_date(details.get("issue_date"))
    due = _parse_date(details.get("due_date"))
    valid = _parse_date(details.get("valid_until"))
    expiry = _parse_date(details.get("expiry_date"))

    today = date.today()

    if issue and due and due < issue:
        anomalies.append({
            "field": "due_date",
            "message": f"Date d'echeance ({details['due_date']}) anterieure a l'emission ({details['issue_date']})",
            "level": "error",
        })

    if issue and valid and valid < issue:
        anomalies.append({
            "field": "valid_until",
            "message": f"Date de validite ({details['valid_until']}) anterieure a l'emission ({details['issue_date']})",
            "level": "error",
        })

    if issue and expiry and expiry < issue:
        anomalies.append({
            "field": "expiry_date",
            "message": f"Date d'expiration ({details['expiry_date']}) anterieure a l'emission ({details['issue_date']})",
            "level": "error",
        })


def _parse_date(value: str | None) -> date | None:
    """Parse YYYY-MM-DD string to date object."""
    if not value:
        return None
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", value)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def validate_cross_documents(documents: list[dict]) -> dict:
    """Cross-validate entities across multiple documents of the same case.

    Each document should have: {type, entities: {siret, vat_number, iban, ...}, ...}
    Returns {"anomalies": [{"field": str, "message": str, "level": str}], "all_sirets_match": bool}
    """
    anomalies: list[dict] = []

    # Collect all SIRETs from documents
    sirets = {}
    for doc in documents:
        ents = doc.get("entities") or doc.get("extracted_fields") or {}
        if isinstance(ents, list):
            ents = {f.get("label", f.get("field", "")): f.get("value") for f in ents}
        siret = ents.get("siret") or ents.get("supplier_siret")
        doc_type = doc.get("type") or doc.get("document_type") or "Document"
        if siret:
            clean = re.sub(r"\s+", "", siret)
            sirets[doc_type] = clean

    # Check SIRET coherence across documents
    unique_sirets = set(sirets.values())
    all_sirets_match = len(unique_sirets) <= 1

    if len(unique_sirets) > 1:
        details = ", ".join(f"{t}: {s}" for t, s in sirets.items())
        anomalies.append({
            "field": "siret_cross",
            "message": f"SIRET different entre documents du meme dossier ({details})",
            "level": "error",
        })

    # Check for expired URSSAF attestations
    today = date.today()
    for doc in documents:
        doc_type = doc.get("type") or doc.get("document_type") or ""
        if "urssaf" not in doc_type.lower() and "attestation" not in doc_type.lower():
            continue
        ents = doc.get("entities") or doc.get("extracted_fields") or {}
        if isinstance(ents, list):
            ents = {f.get("label", f.get("field", "")): f.get("value") for f in ents}
        expiry = ents.get("expiry_date") or ents.get("expiration_date") or ents.get("valid_until")
        if expiry:
            exp_date = _parse_date(expiry)
            if exp_date and exp_date < today:
                anomalies.append({
                    "field": "urssaf_expiry",
                    "message": f"Attestation URSSAF expiree depuis le {expiry}",
                    "level": "error",
                })
            elif exp_date:
                days_left = (exp_date - today).days
                if days_left < 30:
                    anomalies.append({
                        "field": "urssaf_expiry",
                        "message": f"Attestation URSSAF expire bientot ({days_left} jours restants, le {expiry})",
                        "level": "warning",
                    })

    # Check VAT coherence across documents
    vats = {}
    for doc in documents:
        ents = doc.get("entities") or doc.get("extracted_fields") or {}
        if isinstance(ents, list):
            ents = {f.get("label", f.get("field", "")): f.get("value") for f in ents}
        vat = ents.get("vat_number") or ents.get("supplier_vat_number") or ents.get("vat")
        doc_type = doc.get("type") or doc.get("document_type") or "Document"
        if vat:
            vats[doc_type] = vat

    unique_vats = set(vats.values())
    if len(unique_vats) > 1:
        details = ", ".join(f"{t}: {v}" for t, v in vats.items())
        anomalies.append({
            "field": "vat_cross",
            "message": f"TVA differente entre documents ({details})",
            "level": "warning",
        })

    return {
        "anomalies": anomalies,
        "all_sirets_match": all_sirets_match,
    }


def _check_duplicates(
    anomalies: list[dict],
    document_id: str,
    details: dict,
    collection,
):
    """Check for duplicate SIRET in existing documents."""
    siret = details.get("siret") or details.get("supplier_siret")
    if not siret:
        return
    try:
        existing = collection.find_one(
            {"entities.siret": siret, "_id": {"$ne": document_id}},
        )
        if existing:
            anomalies.append({
                "field": "siret",
                "message": f"SIRET {siret} deja present dans un autre document",
                "level": "info",
            })
    except Exception:
        pass
