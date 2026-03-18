#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = ROOT_DIR / "data" / "generated" / "ner"
DATASET_DIRS = {
    "invoices": ROOT_DIR / "data" / "generated" / "factures",
    "quotes": ROOT_DIR / "data" / "generated" / "pdfs" / "devis",
    "urssaf": ROOT_DIR / "data" / "generated" / "pdfs" / "attestations_urssaf",
    "ribs": ROOT_DIR / "data" / "generated" / "pdfs" / "ribs",
    "kbis": ROOT_DIR / "data" / "generated" / "pdfs" / "kbis",
}
TOKEN_PATTERN = re.compile(r"\S+")


@dataclass(frozen=True)
class EntityValue:
    label: str
    value: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate BIO/IOB NER annotations from synthetic dataset TXT+JSON pairs."
    )
    parser.add_argument(
        "--doc-types",
        default="invoices,quotes,urssaf,ribs,kbis",
        help="Comma-separated document types to include.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where annotation files will be written.",
    )
    parser.add_argument(
        "--scheme",
        choices=["bio", "iob"],
        default="bio",
        help="Tagging scheme. `bio` and `iob` both emit BIO/IOB2 tags.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional max number of documents per type.",
    )
    return parser


def format_eur(value: float | int) -> str:
    return f"{float(value):,.2f} EUR".replace(",", " ").replace(".", ",")


def format_percent(value: float | int) -> str:
    return f"{float(value) * 100:.1f}".replace(".", ",").rstrip("0").rstrip(",") + "%"


def format_capital(value: int) -> str:
    return f"{value:,} EUR".replace(",", " ")


def normalize_text_value(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        normalized = value.strip()
        return normalized or None
    return str(value)


def add_entity(entities: list[EntityValue], seen: set[tuple[str, str]], label: str, value: object) -> None:
    normalized = normalize_text_value(value)
    if normalized is None:
        return
    key = (label, normalized)
    if key in seen:
        return
    seen.add(key)
    entities.append(EntityValue(label=label, value=normalized))


def extract_labeled_field(text: str, label: str) -> str | None:
    pattern = re.compile(rf"^\s*{re.escape(label)}\s*:\s*(.+?)\s*$", re.MULTILINE)
    match = pattern.search(text)
    if match:
        return match.group(1).strip()
    return None


def extract_multiline_invoice_names(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    supplier_match = re.search(
        r"FOURNISSEUR\s+(.+?)\s+(.+?)\s+SIRET\s*:\s*(.+?)\s+TVA intracommunautaire",
        text,
        re.DOTALL,
    )
    if supplier_match:
        fields["supplier_name"] = supplier_match.group(1).strip()
        fields["supplier_address"] = supplier_match.group(2).strip()
    customer_match = re.search(
        r"CLIENT\s+(.+?)\s+(.+?)\s+SIRET\s*:\s*(.+?)\s+TVA intracommunautaire",
        text,
        re.DOTALL,
    )
    if customer_match:
        fields["customer_name"] = customer_match.group(1).strip()
        fields["customer_address"] = customer_match.group(2).strip()
    return fields


def render_kbis_text(record: dict) -> str:
    return (
        "EXTRAIT KBIS\n\n"
        f"Denomination : {record['denomination']}\n"
        f"Forme juridique : {record['forme_juridique']}\n"
        f"Capital social : {format_capital(record['capital_social'])}\n"
        f"Adresse du siege : {record['adresse_siege']}\n\n"
        f"SIREN : {record['siren']}\n"
        f"SIRET : {record['siret']}\n"
        f"RCS : {record['rcs']}\n"
        f"Greffe : {record['greffe']}\n"
        f"Date d'immatriculation : {record['date_immatriculation']}\n"
        f"Dirigeant : {record['dirigeant']}\n\n"
        "Document certifiant l'existence juridique de l'entreprise.\n"
    )


def render_invoice_text(record: dict) -> str:
    line_block = "\n".join(
        f"- {item['description']} | Total HT: {format_eur(item['total_ht'])}"
        for item in record.get("line_items", [])
    )
    return (
        "FACTURE FOURNISSEUR\n\n"
        f"Numero de facture : {record['invoice_number']}\n"
        f"Date d'emission : {record['issue_date']}\n"
        f"Date d'echeance : {record['due_date']}\n\n"
        "FOURNISSEUR\n"
        f"{record['supplier_name']}\n"
        f"{record['supplier_address']}\n"
        f"SIRET : {record['supplier_siret']}\n"
        f"TVA intracommunautaire : {record['supplier_vat']}\n\n"
        "CLIENT\n"
        f"{record['customer_name']}\n"
        f"{record['customer_address']}\n"
        f"SIRET : {record['customer_siret']}\n"
        f"TVA intracommunautaire : {record['customer_vat']}\n\n"
        "LIGNES DE FACTURATION\n"
        f"{line_block}\n\n"
        f"TOTAL HT : {format_eur(record['total_ht'])}\n"
        f"TVA ({format_percent(record['tva_rate'])}) : {format_eur(record['total_tva'])}\n"
        f"TOTAL TTC : {format_eur(record['total_ttc'])}\n"
    )


def render_quote_text(record: dict) -> str:
    return (
        "DEVIS\n\n"
        f"Numero de devis : {record['quote_number']}\n"
        f"Date d'emission : {record['issue_date']}\n"
        f"Date de validite : {record['valid_until']}\n"
        f"Montant HT : {format_eur(record['total_ht'])}\n"
        f"Montant TTC : {format_eur(record['total_ttc'])}\n"
    )


def render_urssaf_text(record: dict) -> str:
    return (
        "ATTESTATION DE VIGILANCE URSSAF\n\n"
        f"Numero d'attestation : {record['certificate_id']}\n"
        f"Date d'emission : {record['issue_date']}\n"
        f"Date d'expiration : {record['expiry_date']}\n"
        f"Entreprise : {record['company']}\n"
        f"SIRET : {record['siret']}\n"
    )


def render_rib_text(record: dict) -> str:
    return (
        "RELEVE D'IDENTITE BANCAIRE\n\n"
        f"Titulaire du compte : {record['account_holder']}\n"
        f"Banque : {record['bank_name']}\n"
        f"IBAN : {record['iban']}\n"
        f"BIC : {record['bic']}\n"
    )


def render_record_text(doc_type: str, record: dict) -> str:
    if doc_type == "invoices":
        return render_invoice_text(record)
    if doc_type == "quotes":
        return render_quote_text(record)
    if doc_type == "urssaf":
        return render_urssaf_text(record)
    if doc_type == "ribs":
        return render_rib_text(record)
    if doc_type == "kbis":
        return render_kbis_text(record)
    raise ValueError(f"Unsupported doc type: {doc_type}")


def load_text_for_record(doc_type: str, txt_path: Path, record: dict) -> tuple[str, str]:
    if txt_path.exists():
        return txt_path.read_text(encoding="utf-8"), "txt"
    return render_record_text(doc_type, record), "reconstructed"


def collect_invoice_entities(record: dict, text: str) -> list[EntityValue]:
    entities: list[EntityValue] = []
    seen: set[tuple[str, str]] = set()
    invoice_fields = extract_multiline_invoice_names(text)

    add_entity(entities, seen, "INVOICE_NUMBER", record.get("invoice_number"))
    add_entity(entities, seen, "ISSUE_DATE", record.get("issue_date"))
    add_entity(entities, seen, "DUE_DATE", record.get("due_date"))
    add_entity(entities, seen, "SUPPLIER_NAME", record.get("supplier_name") or invoice_fields.get("supplier_name"))
    add_entity(
        entities,
        seen,
        "SUPPLIER_ADDRESS",
        record.get("supplier_address") or invoice_fields.get("supplier_address"),
    )
    add_entity(entities, seen, "SUPPLIER_SIRET", record.get("supplier_siret"))
    add_entity(entities, seen, "SUPPLIER_VAT", record.get("supplier_vat"))
    add_entity(entities, seen, "CUSTOMER_NAME", record.get("customer_name") or invoice_fields.get("customer_name"))
    add_entity(
        entities,
        seen,
        "CUSTOMER_ADDRESS",
        record.get("customer_address") or invoice_fields.get("customer_address"),
    )
    add_entity(entities, seen, "CUSTOMER_SIRET", record.get("customer_siret"))
    add_entity(entities, seen, "CUSTOMER_VAT", record.get("customer_vat"))
    add_entity(entities, seen, "TOTAL_HT", format_eur(record["total_ht"]))
    if "total_tva" in record:
        add_entity(entities, seen, "TOTAL_TVA", format_eur(record["total_tva"]))
    add_entity(entities, seen, "TOTAL_TTC", format_eur(record["total_ttc"]))
    if "tva_rate" in record:
        add_entity(entities, seen, "TVA_RATE", format_percent(record["tva_rate"]))

    for item in record.get("line_items", []):
        add_entity(entities, seen, "LINE_ITEM_DESCRIPTION", item.get("description"))

    return entities


def collect_quote_entities(record: dict, text: str) -> list[EntityValue]:
    entities: list[EntityValue] = []
    seen: set[tuple[str, str]] = set()

    add_entity(entities, seen, "QUOTE_NUMBER", record.get("quote_number"))
    add_entity(entities, seen, "ISSUE_DATE", record.get("issue_date"))
    add_entity(entities, seen, "VALID_UNTIL", record.get("valid_until"))
    add_entity(entities, seen, "PROVIDER_NAME", extract_labeled_field(text, "Prestataire"))
    add_entity(entities, seen, "PROVIDER_ADDRESS", extract_labeled_field(text, "Adresse prestataire"))
    add_entity(entities, seen, "CLIENT_NAME", extract_labeled_field(text, "Client"))
    add_entity(entities, seen, "CLIENT_ADDRESS", extract_labeled_field(text, "Adresse client"))
    if "total_ht" in record:
        add_entity(entities, seen, "TOTAL_HT", format_eur(record["total_ht"]))
    tva_value = extract_labeled_field(text, "TVA (5,5%)")
    if tva_value is None:
        tva_match = re.search(r"TVA\s*\(([^)]+)\)\s*:\s*(.+)", text)
        if tva_match:
            add_entity(entities, seen, "TVA_RATE", tva_match.group(1))
            add_entity(entities, seen, "TOTAL_TVA", tva_match.group(2).strip())
    if "total_ttc" in record:
        add_entity(entities, seen, "TOTAL_TTC", format_eur(record["total_ttc"]))

    for match in re.finditer(r"^\s*-\s*(.+?)\s+\|\s+Qt:", text, re.MULTILINE):
        add_entity(entities, seen, "LINE_ITEM_DESCRIPTION", match.group(1).strip())

    return entities


def collect_urssaf_entities(record: dict, text: str) -> list[EntityValue]:
    entities: list[EntityValue] = []
    seen: set[tuple[str, str]] = set()

    add_entity(entities, seen, "CERTIFICATE_ID", record.get("certificate_id"))
    add_entity(entities, seen, "ISSUE_DATE", record.get("issue_date"))
    add_entity(entities, seen, "EXPIRY_DATE", record.get("expiry_date"))
    add_entity(entities, seen, "ORGANISM", extract_labeled_field(text, "Organisme"))
    add_entity(entities, seen, "COMPANY", record.get("company") or extract_labeled_field(text, "Entreprise"))
    add_entity(entities, seen, "ADDRESS", extract_labeled_field(text, "Adresse"))
    add_entity(entities, seen, "SIRET", record.get("siret"))
    add_entity(entities, seen, "NAF_CODE", extract_labeled_field(text, "Code NAF"))
    return entities


def collect_rib_entities(record: dict, text: str) -> list[EntityValue]:
    entities: list[EntityValue] = []
    seen: set[tuple[str, str]] = set()

    add_entity(
        entities,
        seen,
        "ACCOUNT_HOLDER",
        record.get("account_holder") or extract_labeled_field(text, "Titulaire du compte"),
    )
    add_entity(entities, seen, "BANK_NAME", record.get("bank_name") or extract_labeled_field(text, "Banque"))
    add_entity(entities, seen, "BANK_ADDRESS", extract_labeled_field(text, "Adresse de la banque"))
    add_entity(entities, seen, "IBAN", record.get("iban"))
    add_entity(entities, seen, "BIC", record.get("bic"))
    add_entity(entities, seen, "BANK_CODE", extract_labeled_field(text, "Code banque"))
    add_entity(entities, seen, "BRANCH_CODE", extract_labeled_field(text, "Code guichet"))
    add_entity(entities, seen, "ACCOUNT_NUMBER", extract_labeled_field(text, "Numero de compte"))
    add_entity(entities, seen, "RIB_KEY", extract_labeled_field(text, "Cle RIB"))
    return entities


def collect_kbis_entities(record: dict, text: str) -> list[EntityValue]:
    entities: list[EntityValue] = []
    seen: set[tuple[str, str]] = set()

    add_entity(entities, seen, "DENOMINATION", record.get("denomination"))
    add_entity(entities, seen, "LEGAL_FORM", record.get("forme_juridique"))
    add_entity(entities, seen, "CAPITAL_SOCIAL", format_capital(record["capital_social"]))
    add_entity(entities, seen, "HEADQUARTERS_ADDRESS", record.get("adresse_siege"))
    add_entity(entities, seen, "SIREN", record.get("siren"))
    add_entity(entities, seen, "SIRET", record.get("siret"))
    add_entity(entities, seen, "RCS", record.get("rcs"))
    add_entity(entities, seen, "GREFFE", record.get("greffe"))
    add_entity(entities, seen, "REGISTRATION_DATE", record.get("date_immatriculation"))
    add_entity(entities, seen, "MANAGER", record.get("dirigeant"))
    return entities


def collect_entities(doc_type: str, record: dict, text: str) -> list[EntityValue]:
    if doc_type == "invoices":
        return collect_invoice_entities(record, text)
    if doc_type == "quotes":
        return collect_quote_entities(record, text)
    if doc_type == "urssaf":
        return collect_urssaf_entities(record, text)
    if doc_type == "ribs":
        return collect_rib_entities(record, text)
    if doc_type == "kbis":
        return collect_kbis_entities(record, text)
    raise ValueError(f"Unsupported doc type: {doc_type}")


def find_non_overlapping_span(text: str, value: str, occupied: list[tuple[int, int]]) -> tuple[int, int] | None:
    start = 0
    while True:
        index = text.find(value, start)
        if index == -1:
            return None
        span = (index, index + len(value))
        if not any(span[0] < end and span[1] > begin for begin, end in occupied):
            return span
        start = index + 1


def build_token_annotations(text: str, entities: list[EntityValue], scheme: str) -> tuple[list[str], list[dict]]:
    token_spans = [(match.group(0), match.start(), match.end()) for match in TOKEN_PATTERN.finditer(text)]
    occupied: list[tuple[int, int]] = []
    entity_spans: list[dict] = []

    for entity in entities:
        span = find_non_overlapping_span(text, entity.value, occupied)
        if span is None:
            continue
        occupied.append(span)
        entity_spans.append({"label": entity.label, "value": entity.value, "start": span[0], "end": span[1]})

    lines: list[str] = []
    for token, start, end in token_spans:
        assigned = None
        for entity in entity_spans:
            if start >= entity["start"] and end <= entity["end"]:
                prefix = "B"
                if start > entity["start"]:
                    prefix = "I"
                assigned = f"{prefix}-{entity['label']}"
                break
        lines.append(f"{token}\t{assigned or 'O'}")

    return lines, entity_spans


def maybe_reconstruct_text(
    doc_type: str,
    record: dict,
    text: str,
    text_source: str,
    entities: list[EntityValue],
    entity_spans: list[dict],
) -> tuple[str, str, list[EntityValue], list[dict]]:
    if text_source != "txt":
        return text, text_source, entities, entity_spans
    if not entities:
        return text, text_source, entities, entity_spans
    if len(entity_spans) >= max(1, len(entities) // 2):
        return text, text_source, entities, entity_spans

    reconstructed_text = render_record_text(doc_type, record)
    reconstructed_entities = collect_entities(doc_type, record, reconstructed_text)
    _, reconstructed_spans = build_token_annotations(reconstructed_text, reconstructed_entities, "bio")
    if len(reconstructed_spans) > len(entity_spans):
        return reconstructed_text, "reconstructed_fallback", reconstructed_entities, reconstructed_spans
    return text, text_source, entities, entity_spans


def iter_records(doc_type: str, limit: int | None) -> list[tuple[Path, Path]]:
    dataset_dir = DATASET_DIRS[doc_type]
    json_files = sorted(path for path in dataset_dir.glob("*.json") if path.name != "summary.json")
    if limit is not None:
        json_files = json_files[:limit]
    return [(json_path, json_path.with_suffix(".txt")) for json_path in json_files]


def write_outputs(
    output_dir: Path,
    scheme: str,
    combined_lines: list[str],
    manifest: list[dict],
    stats: dict,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / f"dataset.{scheme}").write_text("\n".join(combined_lines).rstrip() + "\n", encoding="utf-8")
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "summary.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    doc_types = [doc_type.strip() for doc_type in args.doc_types.split(",") if doc_type.strip()]

    combined_lines: list[str] = []
    manifest: list[dict] = []
    stats = {
        "scheme": args.scheme,
        "doc_types": doc_types,
        "documents": 0,
        "tokens": 0,
        "labeled_tokens": 0,
        "entities": 0,
        "by_type": {},
    }

    for doc_type in doc_types:
        if doc_type not in DATASET_DIRS:
            raise ValueError(f"Unknown doc type: {doc_type}")

        type_stats = {"documents": 0, "tokens": 0, "labeled_tokens": 0, "entities": 0}
        for json_path, txt_path in iter_records(doc_type, args.limit):
            record = json.loads(json_path.read_text(encoding="utf-8"))
            text, text_source = load_text_for_record(doc_type, txt_path, record)
            entities = collect_entities(doc_type, record, text)
            annotation_lines, entity_spans = build_token_annotations(text, entities, args.scheme)
            text, text_source, entities, entity_spans = maybe_reconstruct_text(
                doc_type,
                record,
                text,
                text_source,
                entities,
                entity_spans,
            )
            annotation_lines, entity_spans = build_token_annotations(text, entities, args.scheme)

            combined_lines.extend(annotation_lines)
            combined_lines.append("")

            labeled_tokens = sum(1 for line in annotation_lines if not line.endswith("\tO"))
            type_stats["documents"] += 1
            type_stats["tokens"] += len(annotation_lines)
            type_stats["labeled_tokens"] += labeled_tokens
            type_stats["entities"] += len(entity_spans)

            manifest.append(
                {
                    "doc_type": doc_type,
                    "json_path": str(json_path.relative_to(ROOT_DIR)),
                    "txt_path": str(txt_path.relative_to(ROOT_DIR)) if txt_path.exists() else None,
                    "text_source": text_source,
                    "tokens": len(annotation_lines),
                    "labeled_tokens": labeled_tokens,
                    "entities": entity_spans,
                }
            )

        stats["by_type"][doc_type] = type_stats
        stats["documents"] += type_stats["documents"]
        stats["tokens"] += type_stats["tokens"]
        stats["labeled_tokens"] += type_stats["labeled_tokens"]
        stats["entities"] += type_stats["entities"]

    write_outputs(args.output_dir, args.scheme, combined_lines, manifest, stats)


if __name__ == "__main__":
    main()
