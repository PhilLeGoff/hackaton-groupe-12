from __future__ import annotations

import logging
import re
from datetime import datetime

logger = logging.getLogger("docuscan.ner")

# ---------------------------------------------------------------------------
# Fuzzy matching (optional — degrades gracefully)
# ---------------------------------------------------------------------------

_fuzzy_available = False
try:
    from rapidfuzz import fuzz, process as rf_process
    _fuzzy_available = True
except ImportError:
    pass

# ---------------------------------------------------------------------------
# spaCy NER (optional — degrades gracefully)
# ---------------------------------------------------------------------------

_spacy_nlp = None
_spacy_load_attempted = False


def _get_spacy_nlp():
    """Lazy-load spaCy French model."""
    global _spacy_nlp, _spacy_load_attempted
    if _spacy_load_attempted:
        return _spacy_nlp
    _spacy_load_attempted = True
    try:
        import spacy
        _spacy_nlp = spacy.load("fr_core_news_md")
        logger.info("spaCy fr_core_news_md loaded")
    except Exception as e:
        logger.info(f"spaCy unavailable, using regex only: {e}")
        _spacy_nlp = None
    return _spacy_nlp


# ---------------------------------------------------------------------------
# Field definitions (regex patterns)
# ---------------------------------------------------------------------------

FIELD_DEFINITIONS = {
    "invoice_number": {
        "label": "Numero de facture",
        "patterns": [
            r"Numero de facture\s*[:\-]\s*([A-Z0-9\-\/]+)",
            r"Facture\s*(?:n[°o]\s*)?[:\-]\s*([A-Z0-9\-\/]+)",
            r"Facture\s+n[°o]\s*([A-Z0-9\-\/]+)",
            r"FACTURE\s+N[°O]?\s*([A-Z0-9\-\/]+)",
        ],
    },
    "quote_number": {
        "label": "Numero de devis",
        "patterns": [
            r"Numero de devis\s*[:\-]\s*([A-Z0-9\-\/]+)",
            r"Devis\s*(?:n[°o]\s*)?[:\-]\s*([A-Z0-9\-\/]+)",
        ],
    },
    "certificate_id": {
        "label": "Numero d'attestation",
        "patterns": [
            r"Numero d[''\u2019]attestation\s*[:\-]\s*([A-Z0-9\-]+)",
        ],
    },
    "issue_date": {
        "label": "Date d'emission",
        "patterns": [
            r"Date d[''\u2019]emission\s*[:\-]\s*(\d{4}-\d{2}-\d{2})",
            r"Date d[''\u2019]emission\s*[:\-]\s*(\d{2}[/\-]\d{2}[/\-]\d{4})",
            r"Date d[''\u2019]emission\s*[:\-]\s*(\d{2}[/\-]\d{2}[/\-]\d{2})",
            r"Date d[''\u2019]emission\s*[:\-]\s*(\d{1,2}\s+\w+\s+\d{4})",
            r"Date\s*[:\-]\s*(\d{2}[/\-]\d{2}[/\-]\d{4})",
            r"Date\s*[:\-]\s*(\d{2}[/\-]\d{2}[/\-]\d{2})",
        ],
    },
    "due_date": {
        "label": "Date d'echeance",
        "patterns": [
            r"Date d[''\u2019]echeance\s*[:\-]\s*(\d{4}-\d{2}-\d{2})",
            r"Date d[''\u2019]echeance\s*[:\-]\s*(\d{2}[/\-]\d{2}[/\-]\d{4})",
            r"Date d[''\u2019]echeance\s*[:\-]\s*(\d{1,2}\s+\w+\s+\d{4})",
        ],
    },
    "valid_until": {
        "label": "Date de validite",
        "patterns": [
            r"Date de validite\s*[:\-]\s*(\d{4}-\d{2}-\d{2})",
            r"Date de validite\s*[:\-]\s*(\d{2}[/\-]\d{2}[/\-]\d{4})",
            r"Date de validite\s*[:\-]\s*(\d{1,2}\s+\w+\s+\d{4})",
        ],
    },
    "expiry_date": {
        "label": "Date d'expiration",
        "patterns": [
            r"Date d[''\u2019]expiration\s*[:\-]\s*(\d{4}-\d{2}-\d{2})",
            r"Date d[''\u2019]expiration\s*[:\-]\s*(\d{2}[/\-]\d{2}[/\-]\d{4})",
            r"Date d[''\u2019]expiration\s*[:\-]\s*(\d{1,2}\s+\w+\s+\d{4})",
        ],
    },
    "supplier_name": {
        "label": "Fournisseur",
        "patterns": [
            r"Fournisseur\s*[:\-]\s*([^\n]+)",
            r"Prestataire\s*[:\-]\s*([^\n]+)",
            r"Titulaire du compte\s*[:\-]\s*([^\n]+)",
            r"Entreprise\s*[:\-]\s*([^\n]+)",
            r"FOURNISSEUR\s+([^\n]+)",
            r"[Pp]aiement\s+[àa]\s+l[''\u2019 ]?ordre\s+de\s+([^\n]+)",
        ],
    },
    "client_name": {
        "label": "Client",
        "patterns": [
            r"CLIENT\s*[:\-]\s*([^\n]+)",
            r"([A-ZÀ-Ÿ][A-ZÀ-Ÿ ]+)\s+[ÀA]\s+L[''\u2019]?ATTENTION\s+DE",
            r"([A-ZÀ-Ÿ][A-ZÀ-Ÿ ]+)\s+[ÀA]\s+L?ATTENTION\s+DE",
            r"[ÀA]\s+[Ll][''\u2019]?attention\s+de\s*[:\-]?\s*([^\n]+)",
        ],
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
    "siren": {
        "label": "SIREN",
        "patterns": [r"SIREN\s*[:\-]?\s*([0-9 ]{9,11})"],
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
        "patterns": [
            r"(?:TOTAL HT|Montant HT)\s*[:\-]?\s*([0-9 ]+[.,][0-9]{2})\s*(?:EUR|€)",
            r"(?:TOTAL HT|Montant HT)\s*[:\-]?\s*([0-9 ]+)\s*(?:EUR|€)",
            r"[Ss]ous\s*-?\s*[Tt]otal\s*[:\-]?\s*([0-9 ]+[.,][0-9]{2})\s*(?:EUR|€)",
            r"[Ss]ous\s*-?\s*[Tt]otal\s*[:\-]?\s*([0-9 ]+)\s*(?:EUR|€)",
        ],
    },
    "total_tva": {
        "label": "Montant TVA",
        "patterns": [
            r"TVA\s*(?:\([0-9]+(?:[.,][0-9]+)?%?\))?\s*[:\-]?\s*([0-9 ]+[.,][0-9]{2})\s*(?:EUR|€)",
            r"TVA\s*(?:\([0-9]+(?:[.,][0-9]+)?%?\))?\s*[:\-]?\s*([0-9 ]+)\s*(?:EUR|€)",
        ],
    },
    "total_ttc": {
        "label": "Montant TTC",
        "patterns": [
            r"(?:TOTAL TTC|Montant TTC)\s*[:\-]?\s*([0-9 ]+[.,][0-9]{2})\s*(?:EUR|€)",
            r"(?:TOTAL TTC|Montant TTC)\s*[:\-]?\s*([0-9 ]+)\s*(?:EUR|€)",
            r"(?:^|\n)\s*TOTAL\s*[:\-]?\s*([0-9 ]+[.,][0-9]{2})\s*(?:EUR|€)",
            r"(?:^|\n)\s*TOTAL\s*[:\-]?\s*([0-9 ]+)\s*(?:EUR|€)",
        ],
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
    "naf_code": {
        "label": "Code NAF",
        "patterns": [r"Code NAF\s*[:\-]\s*([0-9]{4}[A-Z])"],
    },
    "organism": {
        "label": "Organisme",
        "patterns": [r"Organisme\s*[:\-]\s*([^\n]+)"],
    },
    # KBIS fields
    "denomination": {
        "label": "Denomination",
        "patterns": [r"Denomination\s*[:\-]\s*([^\n]+)"],
    },
    "forme_juridique": {
        "label": "Forme juridique",
        "patterns": [r"Forme juridique\s*[:\-]\s*([^\n]+)"],
    },
    "capital_social": {
        "label": "Capital social",
        "patterns": [r"Capital social\s*[:\-]\s*([0-9 ]+\s*EUR)"],
    },
    "adresse_siege": {
        "label": "Adresse du siege",
        "patterns": [r"Adresse du siege\s*[:\-]\s*([^\n]+)"],
    },
    "rcs": {
        "label": "RCS",
        "patterns": [r"RCS\s*[:\-]\s*(RCS\s+[^\n]+|[^\n]+)"],
    },
    "greffe": {
        "label": "Greffe",
        "patterns": [r"Greffe\s*[:\-]\s*([^\n]+)"],
    },
    "date_immatriculation": {
        "label": "Date d'immatriculation",
        "patterns": [
            r"Date d[''\u2019]immatriculation\s*[:\-]\s*(\d{4}-\d{2}-\d{2})",
            r"Date d[''\u2019]immatriculation\s*[:\-]\s*(\d{2}[/\-]\d{2}[/\-]\d{4})",
        ],
    },
    "dirigeant": {
        "label": "Dirigeant",
        "patterns": [r"Dirigeant\s*[:\-]\s*([^\n]+)"],
    },
}

# Label aliases for fuzzy matching and label-value extraction
_LABEL_ALIASES = {
    "invoice_number": ["numero de facture"],
    "quote_number": ["numero de devis"],
    "certificate_id": ["numero d attestation"],
    "issue_date": ["date d emission"],
    "due_date": ["date d echeance"],
    "valid_until": ["date de validite"],
    "expiry_date": ["date d expiration"],
    "supplier_name": ["fournisseur", "prestataire", "titulaire du compte", "entreprise"],
    "client_name": ["client"],
    "siret": ["siret"],
    "supplier_siret": ["siret fournisseur"],
    "customer_siret": ["siret client"],
    "siren": ["siren"],
    "vat_number": ["tva intracommunautaire", "numero de tva"],
    "supplier_vat_number": ["tva fournisseur"],
    "customer_vat_number": ["tva client"],
    "total_ht": ["total ht", "montant ht", "sous total", "sous-total", "subtotal"],
    "total_tva": ["montant tva", "tva montant"],
    "total_ttc": ["total ttc", "montant ttc", "total"],
    "iban": ["iban"],
    "bic": ["bic"],
    "bank_name": ["banque"],
    "bank_code": ["code banque"],
    "branch_code": ["code guichet"],
    "account_number": ["numero de compte"],
    "rib_key": ["cle rib"],
    "naf_code": ["code naf"],
    "organism": ["organisme"],
    "denomination": ["denomination"],
    "forme_juridique": ["forme juridique"],
    "capital_social": ["capital social"],
    "adresse_siege": ["adresse du siege"],
    "rcs": ["rcs"],
    "greffe": ["greffe"],
    "date_immatriculation": ["date d immatriculation"],
    "dirigeant": ["dirigeant"],
}

# French month names for date parsing
_FRENCH_MONTHS = {
    "janvier": 1, "fevrier": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "aout": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12,
    # with accents
    "f\u00e9vrier": 2, "ao\u00fbt": 8, "d\u00e9cembre": 12,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract(text: str) -> dict:
    """Extract named entities from OCR text.

    Uses regex patterns, optional spaCy NER, and optional fuzzy matching.
    Returns a dict with canonical keys expected by the Airflow pipeline.
    """
    entities = _extract_all_fields(text)

    # Enrich with spaCy NER
    _enrich_with_spacy(text, entities)

    return {
        "siret": entities.get("siret") or entities.get("supplier_siret"),
        "vat": entities.get("vat_number") or entities.get("supplier_vat_number"),
        "amount_ht": entities.get("total_ht"),
        "amount_ttc": entities.get("total_ttc"),
        "issue_date": entities.get("issue_date"),
        "expiration_date": entities.get("due_date") or entities.get("valid_until") or entities.get("expiry_date"),
        "company_name": entities.get("supplier_name") or entities.get("client_name") or entities.get("denomination"),
        "iban": entities.get("iban"),
        "details": entities,
    }


# ---------------------------------------------------------------------------
# Date normalization
# ---------------------------------------------------------------------------

def _normalize_date(value: str) -> str:
    """Normalize various French date formats to YYYY-MM-DD."""
    value = value.strip()

    # Already ISO format
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return value

    # DD/MM/YYYY or DD-MM-YYYY
    m = re.fullmatch(r"(\d{2})[/\-](\d{2})[/\-](\d{4})", value)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"

    # DD/MM/YY (2-digit year)
    m = re.fullmatch(r"(\d{2})[/\-](\d{2})[/\-](\d{2})", value)
    if m:
        year = int(m.group(3))
        year = 2000 + year if year < 50 else 1900 + year
        return f"{year}-{m.group(2)}-{m.group(1)}"

    # "18 mars 2026", "3 janvier 2025"
    m = re.fullmatch(r"(\d{1,2})\s+(\w+)\s+(\d{4})", value)
    if m:
        day = int(m.group(1))
        month_name = m.group(2).lower()
        year = int(m.group(3))
        month = _FRENCH_MONTHS.get(month_name)
        if month:
            return f"{year}-{month:02d}-{day:02d}"

    return value


# ---------------------------------------------------------------------------
# Core extraction
# ---------------------------------------------------------------------------

def _extract_all_fields(text: str) -> dict:
    """Full entity extraction with section-aware logic and fuzzy matching."""
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

    # Multi-SIRET handling (invoices have supplier + customer)
    if label_values.get("siret"):
        siret_values = label_values["siret"]
        entities["supplier_siret"] = siret_values[0] if siret_values else None
        entities["customer_siret"] = siret_values[1] if len(siret_values) > 1 else None
        entities["siret"] = entities["supplier_siret"] or entities.get("siret")

    # Multi-VAT handling
    if label_values.get("tva intracommunautaire"):
        vat_values = label_values["tva intracommunautaire"]
        entities["supplier_vat_number"] = vat_values[0] if vat_values else None
        entities["customer_vat_number"] = vat_values[1] if len(vat_values) > 1 else None
        entities["vat_number"] = entities["supplier_vat_number"] or entities.get("vat_number")

    # Section-aware extraction for invoices
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

    # Normalize SIRET (remove spaces)
    for siret_key in ("siret", "supplier_siret", "customer_siret"):
        if entities.get(siret_key):
            entities[siret_key] = re.sub(r"\s+", "", entities[siret_key])

    # Normalize SIREN (remove spaces)
    if entities.get("siren"):
        entities["siren"] = re.sub(r"\s+", "", entities["siren"])

    # Normalize IBAN (keep formatted with spaces)
    if entities.get("iban"):
        entities["iban"] = re.sub(r"\s+", " ", entities["iban"]).strip()

    # Normalize dates to ISO format
    for date_key in ("issue_date", "due_date", "valid_until", "expiry_date", "date_immatriculation"):
        if entities.get(date_key):
            entities[date_key] = _normalize_date(entities[date_key])

    return entities


# ---------------------------------------------------------------------------
# spaCy NER enrichment
# ---------------------------------------------------------------------------

_SPACY_ORG_BLACKLIST = {
    "total", "facture", "devis", "attestation", "kbis", "rib",
    "tva", "urssaf", "siret", "siren", "iban", "bic", "eur",
    "description", "prix", "quantité", "merci",
}


def _enrich_with_spacy(text: str, entities: dict):
    """Use spaCy NER to fill gaps in regex extraction."""
    nlp = _get_spacy_nlp()
    if nlp is None:
        return

    # Only process first 5000 chars for performance
    doc = nlp(text[:5000])

    for ent in doc.ents:
        if ent.label_ == "ORG":
            # Skip common false positives
            if ent.text.strip().lower() in _SPACY_ORG_BLACKLIST:
                continue
            # Fill company name if not found by regex
            if not entities.get("supplier_name") and not entities.get("denomination"):
                entities["supplier_name"] = ent.text
        elif ent.label_ == "PER":
            # Fill dirigeant if not found — skip false positives
            if not entities.get("dirigeant"):
                per_text = ent.text.strip()
                per_lower = per_text.lower()
                # Reject common false positives and short strings
                if (per_lower not in _SPACY_ORG_BLACKLIST
                        and len(per_text) > 3
                        and not per_lower.startswith(("facture", "montant", "numero", "total"))):
                    entities["dirigeant"] = per_text
        elif ent.label_ == "LOC":
            # Fill address if not found
            if not entities.get("adresse_siege") and not entities.get("supplier_name"):
                pass  # Location alone isn't enough for address
        elif ent.label_ == "MISC":
            # Could be RCS, etc.
            if "RCS" in ent.text and not entities.get("rcs"):
                entities["rcs"] = ent.text


# ---------------------------------------------------------------------------
# Fuzzy matching for OCR-degraded labels
# ---------------------------------------------------------------------------

def _fuzzy_match_label(raw_label: str) -> str | None:
    """Try to match a noisy OCR label to known field aliases using fuzzy matching."""
    if not _fuzzy_available:
        return None

    all_aliases: dict[str, str] = {}
    for field_name, aliases in _LABEL_ALIASES.items():
        for alias in aliases:
            all_aliases[alias] = field_name

    result = rf_process.extractOne(
        raw_label,
        all_aliases.keys(),
        scorer=fuzz.ratio,
        score_cutoff=75,
    )
    if result:
        matched_alias, score, _ = result
        return all_aliases[matched_alias]
    return None


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

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
    """Extract label:value pairs from text lines, with fuzzy matching for OCR noise."""
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

        # Also try fuzzy matching for the label
        if _fuzzy_available:
            fuzzy_field = _fuzzy_match_label(normalized_label)
            if fuzzy_field:
                for alias in _LABEL_ALIASES.get(fuzzy_field, []):
                    if alias != normalized_label:
                        labeled_values.setdefault(alias, []).append(normalized_value)

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
