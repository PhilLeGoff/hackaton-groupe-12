from fastapi import APIRouter, HTTPException
from bson import ObjectId
from bson.errors import InvalidId
from config.database import document_collection
from bson import ObjectId
from bson.errors import InvalidId
from schemas.document import DocumentUpdate

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

# Get all documents
@_router.get("")
async def get_documents():
    documents = []
    try:
        async for doc in document_collection.find():
            documents.append({
                "id": str(doc["_id"]),
                "name": doc.get("name") or doc.get("filename"),
                "type": _get_type(doc),
                "status": doc.get("status"),
                "confidence": _get_confidence(doc),
            })
        return documents
    except Exception:
        raise HTTPException(status_code=500, detail="Impossible de se connecter a la base de donnees")

# Get document by ID
@_router.get("/{document_id}")
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
