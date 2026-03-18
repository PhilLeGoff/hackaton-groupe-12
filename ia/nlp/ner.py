from __future__ import annotations

import re


FIELD_DEFINITIONS = {
    "invoice_number": {
        "label": "Numero de facture",
        "patterns": [
            r"Numero de facture\s*[:\-]\s*([A-Z0-9\-\/]+)",
            r"Facture\s*(?:n[°o]\s*)?[:\-]\s*([A-Z0-9\-\/]+)",
        ],
    },
    "quote_number": {
        "label": "Numero de devis",
        "patterns": [
            r"Numero de devis\s*[:\-]\s*([A-Z0-9\-\/]+)",
            r"Devis\s*(?:n[°o]\s*)?[:\-]\s*([A-Z0-9\-\/]+)",
        ],
    },
    "issue_date": {
        "label": "Date d'emission",
        "patterns": [r"Date d[''\u2019]emission\s*[:\-]\s*([0-9]{4}-[0-9]{2}-[0-9]{2})"],
    },
    "due_date": {
        "label": "Date d'echeance",
        "patterns": [r"Date d[''\u2019]echeance\s*[:\-]\s*([0-9]{4}-[0-9]{2}-[0-9]{2})"],
    },
    "valid_until": {
        "label": "Date de validite",
        "patterns": [r"Date de validite\s*[:\-]\s*([0-9]{4}-[0-9]{2}-[0-9]{2})"],
    },
    "supplier_name": {
        "label": "Fournisseur",
        "patterns": [
            r"Fournisseur\s*[:\-]\s*([^\n]+)",
            r"Prestataire\s*[:\-]\s*([^\n]+)",
            r"Titulaire du compte\s*[:\-]\s*([^\n]+)",
            r"FOURNISSEUR\s+([^\n]+)",
        ],
    },
    "client_name": {
        "label": "Client",
        "patterns": [r"CLIENT\s+([^\n]+)", r"Client\s*[:\-]\s*([^\n]+)"],
    },
    "siret": {
        "label": "SIRET",
        "patterns": [r"SIRET\s*[:\-]?\s*([0-9 ]{14,17})"],
    },
    "supplier_siret": {
        "label": "SIRET fournisseur",
        "patterns": [r"SIRET fournisseur\s*[:\-]?\s*([0-9 ]{14,17})"],
    },
    "customer_siret": {
        "label": "SIRET client",
        "patterns": [r"SIRET client\s*[:\-]?\s*([0-9 ]{14,17})"],
    },
    "vat_number": {
        "label": "TVA intracommunautaire",
        "patterns": [r"TVA(?: intracommunautaire)?\s*[:\-]?\s*(FR[0-9A-Z]{2,})"],
    },
    "supplier_vat_number": {
        "label": "TVA fournisseur",
        "patterns": [r"TVA fournisseur\s*[:\-]?\s*(FR[0-9A-Z]{2,})"],
    },
    "customer_vat_number": {
        "label": "TVA client",
        "patterns": [r"TVA client\s*[:\-]?\s*(FR[0-9A-Z]{2,})"],
    },
    "total_ht": {
        "label": "Montant HT",
        "patterns": [r"(?:TOTAL HT|Montant HT)\s*[:\-]?\s*([0-9 ]+,[0-9]{2})\s*EUR"],
    },
    "total_tva": {
        "label": "Montant TVA",
        "patterns": [r"TVA(?: \([0-9]+(?:,[0-9]+)?%\))?\s*[:\-]?\s*([0-9 ]+,[0-9]{2})\s*EUR"],
    },
    "total_ttc": {
        "label": "Montant TTC",
        "patterns": [r"(?:TOTAL TTC|Montant TTC)\s*[:\-]?\s*([0-9 ]+,[0-9]{2})\s*EUR"],
    },
    "iban": {
        "label": "IBAN",
        "patterns": [r"IBAN\s*[:\-]?\s*([A-Z]{2}[0-9A-Z ]{13,34})"],
    },
    "bic": {
        "label": "BIC",
        "patterns": [r"BIC\s*[:\-]?\s*([A-Z0-9]{8,11})"],
    },
    "bank_name": {
        "label": "Banque",
        "patterns": [r"Banque\s*[:\-]\s*([^\n]+)"],
    },
    "bank_code": {
        "label": "Code banque",
        "patterns": [r"Code banque\s*[:\-]\s*([0-9]{5})"],
    },
    "branch_code": {
        "label": "Code guichet",
        "patterns": [r"Code guichet\s*[:\-]\s*([0-9]{5})"],
    },
    "account_number": {
        "label": "Numero de compte",
        "patterns": [r"Numero de compte\s*[:\-]\s*([0-9]{11})"],
    },
    "rib_key": {
        "label": "Cle RIB",
        "patterns": [r"Cle RIB\s*[:\-]\s*([0-9]{2})"],
    },
}

_LABEL_ALIASES = {
    "invoice_number": ["numero de facture"],
    "quote_number": ["numero de devis"],
    "issue_date": ["date d emission"],
    "due_date": ["date d echeance"],
    "valid_until": ["date de validite"],
    "supplier_name": ["fournisseur", "prestataire", "titulaire du compte"],
    "client_name": ["client"],
    "siret": ["siret"],
    "supplier_siret": ["siret fournisseur"],
    "customer_siret": ["siret client"],
    "vat_number": ["tva intracommunautaire", "tva"],
    "supplier_vat_number": ["tva fournisseur"],
    "customer_vat_number": ["tva client"],
    "total_ht": ["total ht", "montant ht"],
    "total_tva": ["tva"],
    "total_ttc": ["total ttc", "montant ttc"],
    "iban": ["iban"],
    "bic": ["bic"],
    "bank_name": ["banque"],
    "bank_code": ["code banque"],
    "branch_code": ["code guichet"],
    "account_number": ["numero de compte"],
    "rib_key": ["cle rib"],
}


def extract(text: str) -> dict:
    """Extract named entities from OCR text using regex patterns.

    Returns a dict with all detected fields. Keys expected by the Airflow
    pipeline (siret, vat, amount_ht, amount_ttc, issue_date, expiration_date,
    company_name, iban) are always present (None when not found).
    """
    entities = _extract_all_fields(text)

    # Map to the canonical keys expected by Airflow
    return {
        "siret": entities.get("siret") or entities.get("supplier_siret"),
        "vat": entities.get("vat_number") or entities.get("supplier_vat_number"),
        "amount_ht": entities.get("total_ht"),
        "amount_ttc": entities.get("total_ttc"),
        "issue_date": entities.get("issue_date"),
        "expiration_date": entities.get("due_date") or entities.get("valid_until"),
        "company_name": entities.get("supplier_name") or entities.get("client_name"),
        "iban": entities.get("iban"),
        # Keep all detailed fields for downstream consumers
        "details": entities,
    }


def _extract_all_fields(text: str) -> dict:
    """Full entity extraction with section-aware logic."""
    entities: dict[str, str | None] = {}
    label_values = _extract_labeled_values(text)
    supplier_block = _extract_section(text, "FOURNISSEUR", "CLIENT")
    client_block = _extract_section(
        text,
        "CLIENT",
        "LIGNES DE FACTURATION|Prestations proposees|Montant HT|TOTAL HT|Document fourni",
    )

    for field_name, field_def in FIELD_DEFINITIONS.items():
        entities[field_name] = _extract_field_value(
            field_name, text, label_values, field_def["patterns"],
        )

    if label_values.get("siret"):
        siret_values = label_values["siret"]
        entities["supplier_siret"] = siret_values[0] if siret_values else None
        entities["customer_siret"] = siret_values[1] if len(siret_values) > 1 else None
        entities["siret"] = entities["supplier_siret"] or entities.get("siret")

    if label_values.get("tva intracommunautaire"):
        vat_values = label_values["tva intracommunautaire"]
        entities["supplier_vat_number"] = vat_values[0] if vat_values else None
        entities["customer_vat_number"] = vat_values[1] if len(vat_values) > 1 else None
        entities["vat_number"] = entities["supplier_vat_number"] or entities.get("vat_number")

    if supplier_block:
        entities["supplier_name"] = (
            _first_nonempty_line(supplier_block, prefer_plain_line=True)
            or entities.get("supplier_name")
        )
        entities["supplier_siret"] = (
            _find_first_match(supplier_block, [r"SIRET\s*[:\-]?\s*([0-9 ]{14,17})"])
            or entities.get("supplier_siret")
        )
        entities["supplier_vat_number"] = (
            _find_first_match(supplier_block, [r"TVA(?: intracommunautaire)?\s*[:\-]?\s*(FR[0-9A-Z]{2,})"])
            or entities.get("supplier_vat_number")
        )

    if client_block:
        entities["client_name"] = (
            _first_nonempty_line(client_block, prefer_plain_line=True)
            or entities.get("client_name")
        )
        entities["customer_siret"] = (
            _find_first_match(client_block, [r"SIRET\s*[:\-]?\s*([0-9 ]{14,17})"])
            or entities.get("customer_siret")
        )
        entities["customer_vat_number"] = (
            _find_first_match(client_block, [r"TVA(?: intracommunautaire)?\s*[:\-]?\s*(FR[0-9A-Z]{2,})"])
            or entities.get("customer_vat_number")
        )

    for siret_key in ("siret", "supplier_siret", "customer_siret"):
        if entities.get(siret_key):
            entities[siret_key] = re.sub(r"\s+", "", entities[siret_key])

    if entities.get("iban"):
        entities["iban"] = re.sub(r"\s+", " ", entities["iban"]).strip()

    return entities


def _find_first_match(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return _normalize_value(match.group(1))
    return None


def _normalize_value(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" :\n\t")


def _normalize_label(label: str) -> str:
    return _normalize_value(label).lower().replace("\u2019", " ").replace("'", " ")


def _extract_labeled_values(text: str) -> dict[str, list[str]]:
    labeled_values: dict[str, list[str]] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        label, value = line.split(":", 1)
        normalized_label = _normalize_label(label)
        normalized_value = _normalize_value(value)
        if not normalized_label or not normalized_value:
            continue
        labeled_values.setdefault(normalized_label, []).append(normalized_value)
    return labeled_values


def _extract_field_value(
    field_name: str,
    text: str,
    label_values: dict[str, list[str]],
    patterns: list[str],
) -> str | None:
    for alias in _LABEL_ALIASES.get(field_name, []):
        values = label_values.get(alias)
        if values:
            return values[0]
    return _find_first_match(text, patterns)


def _extract_section(text: str, start_marker: str, end_marker_pattern: str) -> str:
    pattern = (
        rf"(?:^|\n)\s*{re.escape(start_marker)}\s*\n+"
        rf"(.*?)(?=(?:^|\n)\s*(?:{end_marker_pattern})\b|$)"
    )
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL | re.MULTILINE)
    if not match:
        return ""
    return match.group(1).strip()


def _first_nonempty_line(text: str, prefer_plain_line: bool = False) -> str | None:
    for line in text.splitlines():
        normalized_line = _normalize_value(line)
        if normalized_line:
            if prefer_plain_line and ":" in normalized_line:
                continue
            return normalized_line
    return None
