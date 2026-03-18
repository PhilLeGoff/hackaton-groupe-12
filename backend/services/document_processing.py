from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import re
import subprocess
import zipfile
from xml.etree import ElementTree


OCR_LANG = "fra+eng"
OCR_TIMEOUT_SECONDS = 90

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
        "patterns": [r"Date d['’]emission\s*[:\-]\s*([0-9]{4}-[0-9]{2}-[0-9]{2})"],
    },
    "due_date": {
        "label": "Date d'echeance",
        "patterns": [r"Date d['’]echeance\s*[:\-]\s*([0-9]{4}-[0-9]{2}-[0-9]{2})"],
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


class DocumentProcessingError(RuntimeError):
    pass


def process_document(content: bytes, content_type: str, filename: str) -> dict:
    ocr_text = extract_text(content, content_type, filename)
    entities = extract_entities(ocr_text)
    document_type = classify_document(filename, ocr_text, entities)
    extracted_fields = build_extracted_fields(entities)
    confidence = compute_confidence(document_type, extracted_fields)
    anomalies = build_anomalies(ocr_text, document_type, entities)
    status = "Analyse terminée" if not anomalies else "À vérifier"

    return {
        "ocr_text": ocr_text,
        "entities": entities,
        "document_type": document_type,
        "extracted_fields": extracted_fields,
        "confidence": confidence,
        "status": status,
        "anomalies": anomalies,
        "timeline": build_timeline(status),
    }


def extract_text(content: bytes, content_type: str, filename: str) -> str:
    if content_type == "text/plain":
        return decode_text(content)

    if content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_docx_text(content)

    with TemporaryDirectory(prefix="upload-ocr-") as tmpdir:
        suffix = Path(filename).suffix or guess_suffix(content_type)
        input_path = Path(tmpdir) / f"document{suffix}"
        input_path.write_bytes(content)

        if content_type == "application/pdf":
            pdf_text = extract_pdf_text(input_path)
            if pdf_text.strip():
                return normalize_whitespace(pdf_text)

            return normalize_whitespace(run_pdf_ocr(input_path, Path(tmpdir)))

        return normalize_whitespace(run_tesseract(input_path))


def decode_text(content: bytes) -> str:
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            return normalize_whitespace(content.decode(encoding))
        except UnicodeDecodeError:
            continue

    return normalize_whitespace(content.decode("utf-8", errors="ignore"))


def extract_docx_text(content: bytes) -> str:
    try:
        with zipfile.ZipFile(BytesIO(content)) as archive:
            xml_content = archive.read("word/document.xml")
    except (KeyError, zipfile.BadZipFile) as exc:
        raise DocumentProcessingError("Impossible de lire le contenu du DOCX.") from exc

    root = ElementTree.fromstring(xml_content)
    namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    texts = [
        node.text.strip()
        for node in root.findall(".//w:t", namespaces)
        if node.text and node.text.strip()
    ]
    return normalize_whitespace("\n".join(texts))


def extract_pdf_text(input_path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""

    try:
        reader = PdfReader(str(input_path))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception:
        return ""

    return "\n".join(pages)


def run_pdf_ocr(input_path: Path, tmpdir: Path) -> str:
    if not shutil_which("pdftoppm"):
        raise DocumentProcessingError(
            "OCR PDF indisponible: pdftoppm est requis pour convertir le PDF en images."
        )

    output_prefix = tmpdir / "page"
    command = [
        "pdftoppm",
        "-png",
        str(input_path),
        str(output_prefix),
    ]

    try:
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=OCR_TIMEOUT_SECONDS,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise DocumentProcessingError("La conversion du PDF en images a échoué.") from exc

    page_images = sorted(tmpdir.glob("page-*.png"))
    if not page_images:
        raise DocumentProcessingError("Aucune image n'a été générée à partir du PDF.")

    texts = [run_tesseract(page_image) for page_image in page_images]
    return "\n".join(texts)


def run_tesseract(input_path: Path) -> str:
    if not shutil_which("tesseract"):
        raise DocumentProcessingError("Tesseract n'est pas installé sur la machine.")

    command = [
        "tesseract",
        str(input_path),
        "stdout",
        "-l",
        OCR_LANG,
        "--psm",
        "6",
    ]

    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=OCR_TIMEOUT_SECONDS,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise DocumentProcessingError("L'exécution OCR a échoué.") from exc

    return result.stdout


def extract_entities(text: str) -> dict:
    entities = {}
    label_values = extract_labeled_values(text)
    supplier_block = extract_section(text, "FOURNISSEUR", "CLIENT")
    client_block = extract_section(
        text,
        "CLIENT",
        "LIGNES DE FACTURATION|Prestations proposees|Montant HT|TOTAL HT|Document fourni",
    )

    for field_name, field_definition in FIELD_DEFINITIONS.items():
        entities[field_name] = extract_field_value(field_name, text, label_values, field_definition["patterns"])

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
        entities["supplier_name"] = first_nonempty_line(
            supplier_block,
            prefer_plain_line=True,
        ) or entities.get("supplier_name")
        entities["supplier_siret"] = find_first_match(
            supplier_block,
            [r"SIRET\s*[:\-]?\s*([0-9 ]{14,17})"],
        ) or entities.get("supplier_siret")
        entities["supplier_vat_number"] = find_first_match(
            supplier_block,
            [r"TVA(?: intracommunautaire)?\s*[:\-]?\s*(FR[0-9A-Z]{2,})"],
        ) or entities.get("supplier_vat_number")

    if client_block:
        entities["client_name"] = first_nonempty_line(
            client_block,
            prefer_plain_line=True,
        ) or entities.get("client_name")
        entities["customer_siret"] = find_first_match(
            client_block,
            [r"SIRET\s*[:\-]?\s*([0-9 ]{14,17})"],
        ) or entities.get("customer_siret")
        entities["customer_vat_number"] = find_first_match(
            client_block,
            [r"TVA(?: intracommunautaire)?\s*[:\-]?\s*(FR[0-9A-Z]{2,})"],
        ) or entities.get("customer_vat_number")

    for siret_key in ("siret", "supplier_siret", "customer_siret"):
        if entities.get(siret_key):
            entities[siret_key] = re.sub(r"\s+", "", entities[siret_key])

    if entities.get("iban"):
        entities["iban"] = re.sub(r"\s+", " ", entities["iban"]).strip()

    return entities


def find_first_match(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return normalize_value(match.group(1))

    return None


def normalize_value(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" :\n\t")


def extract_labeled_values(text: str) -> dict[str, list[str]]:
    labeled_values: dict[str, list[str]] = {}

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue

        label, value = line.split(":", 1)
        normalized_label = normalize_label(label)
        normalized_value = normalize_value(value)
        if not normalized_label or not normalized_value:
            continue

        labeled_values.setdefault(normalized_label, []).append(normalized_value)

    return labeled_values


def extract_field_value(
    field_name: str,
    text: str,
    label_values: dict[str, list[str]],
    patterns: list[str],
) -> str | None:
    label_aliases = {
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

    for alias in label_aliases.get(field_name, []):
        values = label_values.get(alias)
        if values:
            return values[0]

    return find_first_match(text, patterns)


def normalize_label(label: str) -> str:
    return normalize_value(label).lower().replace("'", " ").replace("’", " ")


def extract_section(text: str, start_marker: str, end_marker_pattern: str) -> str:
    pattern = (
        rf"(?:^|\n)\s*{re.escape(start_marker)}\s*\n+"
        rf"(.*?)(?=(?:^|\n)\s*(?:{end_marker_pattern})\b|$)"
    )
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL | re.MULTILINE)
    if not match:
        return ""

    return match.group(1).strip()


def first_nonempty_line(text: str, prefer_plain_line: bool = False) -> str | None:
    for line in text.splitlines():
        normalized_line = normalize_value(line)
        if normalized_line:
            if prefer_plain_line and ":" in normalized_line:
                continue
            return normalized_line

    return None


def classify_document(filename: str, text: str, entities: dict) -> str:
    text_upper = text.upper()

    best_type = "Document"
    best_score = 0

    for document_type, markers in DOCUMENT_RULES.items():
        score = sum(1 for marker in markers if marker.upper() in text_upper)
        if score > best_score:
            best_score = score
            best_type = document_type

    if best_type == "Document":
        name = filename.lower()
        if "fact" in name:
            return "Facture"
        if "devis" in name or entities.get("quote_number"):
            return "Devis"
        if "rib" in name or entities.get("iban"):
            return "RIB"
        if "kbis" in name:
            return "KBIS"

    return best_type


def build_extracted_fields(entities: dict) -> list[dict]:
    fields = []

    for field_name, field_definition in FIELD_DEFINITIONS.items():
        value = entities.get(field_name)
        if not value:
            continue

        fields.append(
            {
                "label": field_definition["label"],
                "value": value,
                "confidence": 95.0,
            }
        )

    return fields


def compute_confidence(document_type: str, extracted_fields: list[dict]) -> int:
    expected_fields = EXPECTED_FIELDS_BY_TYPE.get(document_type, [])
    if not expected_fields:
        return 70 if extracted_fields else 35

    expected_labels = {
        FIELD_DEFINITIONS[field_name]["label"]
        for field_name in expected_fields
        if field_name in FIELD_DEFINITIONS
    }
    matched = sum(1 for field in extracted_fields if field["label"] in expected_labels)
    ratio = matched / max(len(expected_fields), 1)
    return max(35, min(99, round(ratio * 100)))


def build_anomalies(text: str, document_type: str, entities: dict) -> list[dict]:
    anomalies = []

    if not text.strip():
        anomalies.append(
            {
                "title": "OCR vide",
                "description": "Aucun texte exploitable n'a été extrait du document.",
                "level": "error",
            }
        )
        return anomalies

    expected_fields = EXPECTED_FIELDS_BY_TYPE.get(document_type, [])
    missing_fields = [
        FIELD_DEFINITIONS[field_name]["label"]
        for field_name in expected_fields
        if not entities.get(field_name)
    ]

    if missing_fields:
        anomalies.append(
            {
                "title": "Champs manquants",
                "description": "Extraction incomplète: " + ", ".join(missing_fields),
                "level": "warning",
            }
        )

    return anomalies


def build_timeline(status: str) -> list[dict]:
    now = datetime.utcnow().isoformat()
    return [
        {"step": "Upload", "status": "completed", "date": now},
        {"step": "OCR", "status": "completed", "date": now},
        {"step": "Extraction regex", "status": "completed", "date": now},
        {"step": "Analyse", "status": status, "date": now},
    ]


def normalize_whitespace(text: str) -> str:
    normalized_lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in normalized_lines if line)


def guess_suffix(content_type: str) -> str:
    return {
        "application/pdf": ".pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "text/plain": ".txt",
    }.get(content_type, ".bin")


def shutil_which(binary: str) -> str | None:
    try:
        from shutil import which
    except ImportError:
        return None

    return which(binary)
