from datetime import datetime, timedelta
import json
import logging

from airflow import DAG
from airflow.operators.python import PythonOperator

from helpers.mongo import get_document, update_document, get_collection
from helpers.hdfs import read as hdfs_read, write as hdfs_write

logger = logging.getLogger("docuscan.pipeline")

try:
    from ia.ocr.pipeline import extract_text
except ImportError:
    def extract_text(raw_content: bytes, content_type: str) -> str:
        return f"[PLACEHOLDER OCR] {content_type}, {len(raw_content)} bytes"

try:
    from ia.nlp.ner import extract as extract_ner, FIELD_DEFINITIONS
except ImportError:
    FIELD_DEFINITIONS = {}
    def extract_ner(ocr_text: str) -> dict:
        return {"siret": None, "vat": None, "amount_ht": None, "amount_ttc": None,
                "issue_date": None, "expiration_date": None, "company_name": None, "iban": None}

try:
    from ia.classification.classifier import classify, EXPECTED_FIELDS_BY_TYPE
except ImportError:
    EXPECTED_FIELDS_BY_TYPE = {}
    def classify(ocr_text: str) -> dict:
        return {"document_type": "unknown", "confidence": 0.0}

try:
    from ia.anomaly_detection.detector import validate
except ImportError:
    def validate(entities: dict, classification: dict, document_id: str, collection=None) -> dict:
        return {"is_valid": True, "anomalies": []}


def _get_document_id(context) -> str:
    conf = context.get("dag_run").conf or {}
    document_id = conf.get("document_id")
    if not document_id:
        raise ValueError("document_id manquant dans dag_run.conf")
    return document_id


def _set_error_status(document_id: str, task_name: str, error: str):
    try:
        update_document(document_id, {
            "status": "error",
            "error": f"{task_name}: {error}",
            "error_at": datetime.utcnow(),
        })
    except Exception:
        logger.error(f"Impossible de mettre le status error pour {document_id}")


def start_processing(**context):
    document_id = _get_document_id(context)
    update_document(document_id, {
        "status": "processing",
        "processing_started_at": datetime.utcnow(),
    })
    logger.info(f"Document {document_id} → status: processing")


def run_ocr(**context):
    document_id = _get_document_id(context)
    doc = get_document(document_id)

    filename = doc.get("filename", "unknown")
    content_type = doc.get("content_type", "unknown")
    hdfs_raw_path = f"/raw/{document_id}/{filename}"

    try:
        raw_content = hdfs_read(hdfs_raw_path)
    except Exception as e:
        _set_error_status(document_id, "run_ocr", f"Fichier introuvable dans HDFS: {hdfs_raw_path}")
        raise ValueError(f"HDFS read échoué pour {hdfs_raw_path}: {e}")

    ocr_text = extract_text(raw_content, content_type)
    if not ocr_text or ocr_text.startswith("[PLACEHOLDER"):
        logger.warning(f"OCR placeholder utilisé pour {document_id}")

    logger.info(f"OCR terminé: {len(ocr_text)} caractères")
    context["ti"].xcom_push(key="ocr_text", value=ocr_text)
    context["ti"].xcom_push(key="content_type", value=content_type)


def store_clean_hdfs(**context):
    document_id = _get_document_id(context)
    ocr_text = context["ti"].xcom_pull(task_ids="run_ocr", key="ocr_text")

    try:
        hdfs_write(f"/clean/{document_id}/ocr_text.txt", ocr_text.encode("utf-8"))
    except Exception as e:
        logger.warning(f"HDFS write clean échoué: {e}")


def extract_entities(**context):
    document_id = _get_document_id(context)
    ocr_text = context["ti"].xcom_pull(task_ids="run_ocr", key="ocr_text")

    try:
        entities = extract_ner(ocr_text)
    except Exception as e:
        _set_error_status(document_id, "extract_entities", str(e))
        raise

    logger.info(f"Entités extraites pour {document_id}: {entities}")
    context["ti"].xcom_push(key="entities", value=entities)


def classify_document(**context):
    document_id = _get_document_id(context)
    ocr_text = context["ti"].xcom_pull(task_ids="run_ocr", key="ocr_text")

    try:
        classification = classify(ocr_text)
    except Exception as e:
        _set_error_status(document_id, "classify_document", str(e))
        raise

    logger.info(f"Classification pour {document_id}: {classification}")
    context["ti"].xcom_push(key="classification", value=classification)


def validate_coherence(**context):
    document_id = _get_document_id(context)
    entities = context["ti"].xcom_pull(task_ids="extract_entities", key="entities")
    classification = context["ti"].xcom_pull(task_ids="classify_document", key="classification")

    try:
        collection = get_collection()
        validation_result = validate(entities, classification, document_id, collection=collection)
    except Exception as e:
        _set_error_status(document_id, "validate_coherence", str(e))
        raise

    validation_result["checked_at"] = datetime.utcnow().isoformat()
    logger.info(f"Validation pour {document_id}: {validation_result}")
    context["ti"].xcom_push(key="validation", value=validation_result)


def store_curated_hdfs(**context):
    document_id = _get_document_id(context)

    curated_data = {
        "document_id": document_id,
        "ocr_text": context["ti"].xcom_pull(task_ids="run_ocr", key="ocr_text"),
        "entities": context["ti"].xcom_pull(task_ids="extract_entities", key="entities"),
        "classification": context["ti"].xcom_pull(task_ids="classify_document", key="classification"),
        "validation": context["ti"].xcom_pull(task_ids="validate_coherence", key="validation"),
        "processed_at": datetime.utcnow().isoformat(),
    }

    try:
        hdfs_write(f"/curated/{document_id}/result.json", json.dumps(curated_data, ensure_ascii=False).encode("utf-8"))
    except Exception as e:
        logger.warning(f"HDFS write curated échoué: {e}")

    context["ti"].xcom_push(key="curated_data", value=curated_data)


def _build_extracted_fields(entities_details: dict) -> list:
    """Build extracted fields list from detailed entities."""
    fields = []
    for field_name, field_def in FIELD_DEFINITIONS.items():
        value = entities_details.get(field_name)
        if not value:
            continue
        fields.append({
            "label": field_def["label"],
            "value": value,
            "confidence": 95.0,
        })
    return fields


def _compute_confidence(document_type: str, extracted_fields: list) -> int:
    """Compute confidence score based on expected vs found fields."""
    expected = EXPECTED_FIELDS_BY_TYPE.get(document_type, [])
    if not expected:
        return 70 if extracted_fields else 35
    expected_labels = {
        FIELD_DEFINITIONS[f]["label"]
        for f in expected
        if f in FIELD_DEFINITIONS
    }
    matched = sum(1 for f in extracted_fields if f["label"] in expected_labels)
    ratio = matched / max(len(expected), 1)
    return max(35, min(99, round(ratio * 100)))


def sync_mongodb(**context):
    document_id = _get_document_id(context)
    curated_data = context["ti"].xcom_pull(task_ids="store_curated_hdfs", key="curated_data")

    entities = curated_data.get("entities", {})
    classification = curated_data.get("classification", {})
    validation = curated_data.get("validation", {})

    entities_details = entities.get("details", entities)
    extracted_fields = _build_extracted_fields(entities_details)
    document_type = classification.get("document_type", "Document")
    confidence = _compute_confidence(document_type, extracted_fields)
    anomalies = validation.get("anomalies", [])
    has_anomalies = not validation.get("is_valid", True)

    now = datetime.utcnow().isoformat()
    status = "Analyse terminee" if not has_anomalies else "A verifier"

    try:
        update_document(document_id, {
            "status": status,
            "ocr_text": curated_data.get("ocr_text"),
            "entities": entities,
            "classification": classification,
            "validation": validation,
            "type": document_type,
            "confidence": confidence,
            "extracted_fields": extracted_fields,
            "anomalies": anomalies,
            "timeline": [
                {"step": "Upload", "status": "completed", "date": now},
                {"step": "OCR", "status": "completed", "date": now},
                {"step": "Extraction NER", "status": "completed", "date": now},
                {"step": "Classification", "status": "completed", "date": now},
                {"step": "Validation", "status": status, "date": now},
            ],
            "processed_at": datetime.utcnow(),
        })
        logger.info(f"Document {document_id} → status: {status}")
    except Exception as e:
        _set_error_status(document_id, "sync_mongodb", str(e))
        raise


with DAG(
    dag_id="document_pipeline",
    default_args={
        "owner": "docuscan",
        "depends_on_past": False,
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 1,
        "retry_delay": timedelta(seconds=10),
    },
    description="Pipeline de traitement documentaire DocuScan AI",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    is_paused_upon_creation=False,
    tags=["docuscan", "pipeline", "ocr", "nlp"],
) as dag:

    t1 = PythonOperator(task_id="start_processing", python_callable=start_processing)
    t2 = PythonOperator(task_id="run_ocr", python_callable=run_ocr)
    t3 = PythonOperator(task_id="store_clean_hdfs", python_callable=store_clean_hdfs)
    t4 = PythonOperator(task_id="extract_entities", python_callable=extract_entities)
    t5 = PythonOperator(task_id="classify_document", python_callable=classify_document)
    t6 = PythonOperator(task_id="validate_coherence", python_callable=validate_coherence)
    t7 = PythonOperator(task_id="store_curated_hdfs", python_callable=store_curated_hdfs)
    t8 = PythonOperator(task_id="sync_mongodb", python_callable=sync_mongodb)

    t1 >> t2 >> t3 >> t4 >> t5 >> t6 >> t7 >> t8
