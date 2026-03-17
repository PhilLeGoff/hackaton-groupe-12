from fastapi import APIRouter, HTTPException
from backend.config.database import db
from config.database import document_collection

router = APIRouter(prefix="/api/documents", tags=["documents"])

@router.get("")
async def get_documents():

    documents = []

    async for doc in document_collection.find():

        documents.append({
            "id": doc["_id"],
            "name": doc.get("name"),
            "type": doc.get("type"),
            "status": doc.get("status"),
            "confidence": f"{doc.get('confidence', 0)}%"
        })

    return documents
  


@router.get("/{document_id}")
async def get_document(document_id: str):

    doc = await document_collection.find_one({"_id": document_id})

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": doc["_id"],
        "name": doc.get("name"),
        "type": doc.get("type"),
        "status": doc.get("status"),
        "confidence": f"{doc.get('confidence', 0)}%",

        "extractedFields": [
            {
                "label": f["label"],
                "value": f["value"],
                "confidence": f"{f.get('confidence', 0)}%"
            }
            for f in doc.get("extracted_fields", [])
        ],

        "anomalies": doc.get("anomalies", []),

        "timeline": doc.get("timeline", [])
    }