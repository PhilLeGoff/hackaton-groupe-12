from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from ia.ocr.pipeline import extract_text  # noqa: E402
from ia.nlp.ner import extract as extract_ner  # noqa: E402
from ia.classification.classifier import classify  # noqa: E402
from services.ocr_metrics import (  # noqa: E402
    character_error_rate,
    field_accuracy,
    mean,
    percentage,
    safe_counter,
    word_error_rate,
)


DOC_TYPE_BY_FOLDER = {
    "factures": "Facture",
    "devis": "Devis",
    "ribs": "RIB",
}

FIELD_MAPPING = {
    "Facture": {
        "invoice_number": "invoice_number",
        "issue_date": "issue_date",
        "due_date": "due_date",
        "supplier_siret": "supplier_siret",
        "customer_siret": "customer_siret",
        "total_ht": "total_ht",
        "total_tva": "total_tva",
        "total_ttc": "total_ttc",
    },
    "Devis": {
        "quote_number": "quote_number",
        "issue_date": "issue_date",
        "valid_until": "valid_until",
        "total_ht": "total_ht",
        "total_ttc": "total_ttc",
    },
    "RIB": {
        "supplier_name": "account_holder",
        "bank_name": "bank_name",
        "iban": "iban",
        "bic": "bic",
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate OCR quality on generated PDFs.")
    parser.add_argument(
        "--dataset-root",
        default=str(ROOT_DIR / "data" / "generated" / "pdfs"),
        help="Root directory containing generated PDF datasets.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional limit on the number of PDFs to evaluate.",
    )
    parser.add_argument(
        "--doc-type",
        choices=["Facture", "Devis", "RIB"],
        help="Restrict evaluation to a single document type.",
    )
    parser.add_argument(
        "--output-json",
        help="Optional path to write the full evaluation report as JSON.",
    )
    args = parser.parse_args()

    dataset_root = Path(args.dataset_root)
    pdf_paths = collect_pdf_paths(dataset_root, args.doc_type)
    if args.limit > 0:
        pdf_paths = pdf_paths[: args.limit]

    if not pdf_paths:
        print("No matching PDF files found.")
        return 1

    report = evaluate_dataset(pdf_paths)
    print_summary(report)

    if args.output_json:
        output_path = Path(args.output_json)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nSaved JSON report to {output_path}")

    return 0


def collect_pdf_paths(dataset_root: Path, requested_doc_type: str | None) -> list[Path]:
    pdf_paths = []

    for pdf_path in sorted(dataset_root.glob("*/*.pdf")):
        folder_name = pdf_path.parent.name
        doc_type = DOC_TYPE_BY_FOLDER.get(folder_name)
        if not doc_type:
            continue
        if requested_doc_type and doc_type != requested_doc_type:
            continue

        txt_path = pdf_path.with_suffix(".txt")
        json_path = pdf_path.with_suffix(".json")
        if txt_path.exists() and json_path.exists():
            pdf_paths.append(pdf_path)

    return pdf_paths


def evaluate_dataset(pdf_paths: list[Path]) -> dict:
    samples = []
    cer_values = []
    wer_values = []
    field_accuracy_values = []
    doc_types = []

    for pdf_path in pdf_paths:
        sample_report = evaluate_sample(pdf_path)
        samples.append(sample_report)
        cer_values.append(sample_report["ocr"]["cer"])
        wer_values.append(sample_report["ocr"]["wer"])
        field_accuracy_values.append(sample_report["fields"]["accuracy"])
        doc_types.append(sample_report["document_type"])

    by_type = {}
    for doc_type in sorted(set(doc_types)):
        typed_samples = [sample for sample in samples if sample["document_type"] == doc_type]
        by_type[doc_type] = {
            "documents": len(typed_samples),
            "avg_cer": mean([sample["ocr"]["cer"] for sample in typed_samples]),
            "avg_wer": mean([sample["ocr"]["wer"] for sample in typed_samples]),
            "avg_field_accuracy": mean([sample["fields"]["accuracy"] for sample in typed_samples]),
        }

    return {
        "documents": len(samples),
        "document_type_counts": safe_counter(doc_types),
        "avg_cer": mean(cer_values),
        "avg_wer": mean(wer_values),
        "avg_field_accuracy": mean(field_accuracy_values),
        "by_type": by_type,
        "samples": samples,
    }


def evaluate_sample(pdf_path: Path) -> dict:
    txt_path = pdf_path.with_suffix(".txt")
    json_path = pdf_path.with_suffix(".json")
    reference_text = txt_path.read_text(encoding="utf-8")
    expected_json = json.loads(json_path.read_text(encoding="utf-8"))

    raw_content = pdf_path.read_bytes()
    ocr_text = extract_text(raw_content, "application/pdf", pdf_path.name)
    ner_result = extract_ner(ocr_text)
    classification = classify(ocr_text)
    entities = ner_result.get("details", ner_result)

    analysis = {
        "ocr_text": ocr_text,
        "document_type": classification["document_type"],
        "entities": entities,
    }

    document_type = DOC_TYPE_BY_FOLDER.get(pdf_path.parent.name, analysis["document_type"])
    expected_fields = extract_expected_fields(document_type, expected_json)
    predicted_fields = extract_predicted_fields(document_type, analysis["entities"])
    field_report = field_accuracy(expected_fields, predicted_fields)

    return {
        "file": str(pdf_path.relative_to(ROOT_DIR)),
        "document_type": document_type,
        "predicted_type": analysis["document_type"],
        "ocr": {
            "cer": character_error_rate(reference_text, analysis["ocr_text"]),
            "wer": word_error_rate(reference_text, analysis["ocr_text"]),
        },
        "fields": field_report,
    }


def extract_expected_fields(document_type: str, expected_json: dict) -> dict[str, str]:
    mapping = FIELD_MAPPING.get(document_type, {})
    fields = {}

    for predicted_key, json_key in mapping.items():
        if json_key not in expected_json:
            continue
        fields[predicted_key] = stringify_expected_value(expected_json[json_key])

    return fields


def extract_predicted_fields(document_type: str, predicted_entities: dict) -> dict[str, str]:
    mapping = FIELD_MAPPING.get(document_type, {})
    return {
        predicted_key: stringify_expected_value(predicted_entities.get(predicted_key))
        for predicted_key in mapping
        if predicted_entities.get(predicted_key) not in (None, "")
    }


def stringify_expected_value(value) -> str:
    if isinstance(value, float):
        return format_amount(value)
    if value is None:
        return ""
    return str(value)


def format_amount(value: float) -> str:
    return f"{value:,.2f}".replace(",", " ").replace(".", ",")


def print_summary(report: dict):
    print("OCR evaluation summary")
    print(f"Documents: {report['documents']}")
    print(f"Average CER: {percentage(report['avg_cer'])}")
    print(f"Average WER: {percentage(report['avg_wer'])}")
    print(f"Average field accuracy: {percentage(report['avg_field_accuracy'])}")

    if report["document_type_counts"]:
        print("\nBy document type:")
        for doc_type, metrics in report["by_type"].items():
            print(
                f"- {doc_type}: {metrics['documents']} docs, "
                f"CER {percentage(metrics['avg_cer'])}, "
                f"WER {percentage(metrics['avg_wer'])}, "
                f"fields {percentage(metrics['avg_field_accuracy'])}"
            )


if __name__ == "__main__":
    raise SystemExit(main())
