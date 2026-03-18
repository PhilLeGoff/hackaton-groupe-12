from fastapi import APIRouter, HTTPException, Query
from bson import ObjectId
from bson.errors import InvalidId
from fastapi.responses import StreamingResponse
from config.database import document_collection
from bson import ObjectId
from bson.errors import InvalidId
from schemas.document import DocumentUpdate, PaginatedDocumentResponse, DocumentDetailResponse, OCRMetricsResponse
import httpx
from params import HDFS_WEBHDFS_URL
from typing import Optional
from services.ocr_metrics import (
    character_error_rate,
    word_error_rate,
    field_accuracy,
    percentage,
)

_router = APIRouter(prefix="/api/documents", tags=["documents"])

# Helper functions to read type, confidence, and anomalies from document
def _get_type(doc: dict) -> str | None:
    """Read document type from top-level or nested classification."""
    doc_type = doc.get("type")
    if doc_type:
        return doc_type
    classification = doc.get("classification")
    if isinstance(classification, dict):
        return classification.get("document_type")
    return None

def _get_confidence(doc: dict) -> float:
    """Read confidence as a float from top-level or nested classification."""
    confidence = doc.get("confidence")
    if isinstance(confidence, (int, float)):
        return float(confidence)
    classification = doc.get("classification")
    if isinstance(classification, dict):
        conf = classification.get("confidence", 0)
        if isinstance(conf, float) and conf <= 1.0:
            return round(conf * 100)
        return float(conf)
    return 0.0

def _get_anomalies(doc: dict) -> list:
    """Read anomalies from top-level or nested validation."""
    anomalies = doc.get("anomalies")
    if isinstance(anomalies, list) and anomalies:
        return anomalies
    validation = doc.get("validation")
    if isinstance(validation, dict):
        return validation.get("anomalies", [])
    return []

# Get all documents with pagination, filtering by status and type
@_router.get("", response_model=PaginatedDocumentResponse)
async def get_documents(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    type: Optional[str] = None
):
    documents = []
    query = {}

    try:
        if status:
            query["status"] = status

        cursor = document_collection.find(query).skip(offset).limit(limit)

        async for doc in cursor:
            doc_type = _get_type(doc)

            if type and doc_type != type:
                continue

            documents.append({
                "id": str(doc["_id"]),
                "name": doc.get("name") or doc.get("filename"),
                "type": doc_type,
                "status": doc.get("status"),
                "confidence": _get_confidence(doc),
            })

        total = await document_collection.count_documents(query)

        return {
            "data": documents,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Impossible de se connecter a la base de donnees"
        )

# Get document by ID
@_router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(document_id: str):
    try:
        oid = ObjectId(document_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="ID de document invalide")

    doc = await document_collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": str(doc["_id"]),
        "name": doc.get("name") or doc.get("filename"),
        "type": _get_type(doc),
        "status": doc.get("status"),
        "confidence": _get_confidence(doc),
        "ocr_text": doc.get("ocr_text"),
        "entities": doc.get("entities"),
        "classification": doc.get("classification"),
        "validation": doc.get("validation"),
        "extractedFields": [
            {"label": f["label"], "value": f["value"], "confidence": f.get("confidence", 0)}
            for f in doc.get("extracted_fields", [])
        ],
        "anomalies": _get_anomalies(doc),
        "timeline": doc.get("timeline", []),
    }
    
# Update document 
@_router.put("/{document_id}")
async def update_document(document_id: str, payload: DocumentUpdate):
    try:
        object_id = ObjectId(document_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid document ID")

    result = document_collection.update_one(
        {"_id": object_id},
        {"$set": payload.model_dump()}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")

    return {"message": "Document updated"}


@_router.get("/{document_id}/download")
async def download_document(document_id: str):
    try:
        ObjectId(document_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid document ID")

    hdfs_path = f"/raw/{document_id}"

    url = f"{HDFS_WEBHDFS_URL}{hdfs_path}?op=OPEN"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, follow_redirects=True)

        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="File not found in HDFS")

        return StreamingResponse(
            response.aiter_bytes(),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={document_id}"
            }
        )
        
# Get OCR metrics for a document
@_router.get("/{document_id}/metrics", response_model=OCRMetricsResponse)
async def get_document_metrics(document_id: str):
    try:
        oid = ObjectId(document_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid document ID")

    doc = await document_collection.find_one({"_id": oid})

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    ocr_text = doc.get("ocr_text", "")

    reference_text = doc.get("reference_text", "")

    cer = character_error_rate(reference_text, ocr_text)
    wer = word_error_rate(reference_text, ocr_text)

    extracted_fields = {
        f["label"]: f["value"]
        for f in doc.get("extracted_fields", [])
    }

    expected_fields = doc.get("expected_fields", {})

    field_acc = field_accuracy(expected_fields, extracted_fields)

    return {
        "character_error_rate": cer,
        "word_error_rate": wer,
        "field_accuracy": field_acc,
        "summary": {
            "cer_percent": percentage(cer),
            "wer_percent": percentage(wer),
            "field_accuracy_percent": percentage(field_acc["accuracy"]),
        },
    }