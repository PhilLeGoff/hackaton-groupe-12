from fastapi import APIRouter, HTTPException
from bson import ObjectId
from config.database import document_collection

_router = APIRouter(prefix="/api/documents", tags=["documents"])


@_router.get("")
async def get_documents():
    documents = []
    try:
         async for doc in document_collection.find():
            documents.append({
            "id": str(doc["_id"]),
            "name": doc.get("name") or doc.get("filename"),
            "type": doc.get("type"),
            "status": doc.get("status"),
            "confidence": f"{doc.get('confidence', 0)}%",
         })
         return documents
        # comment: 
    except Exception as e:
        raise HTTPException(status_code=500,detail="impossible de se connecté à la base de donnée")
    # end try
   
   
   
   
   
   
   
   
   


@_router.get("/{document_id}")
async def get_document(document_id: str):
    doc = await document_collection.find_one({"_id": ObjectId(document_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": str(doc["_id"]),
        "name": doc.get("name") or doc.get("filename"),
        "type": doc.get("type"),
        "status": doc.get("status"),
        "confidence": f"{doc.get('confidence', 0)}%",
        "ocr_text": doc.get("ocr_text"),
        "entities": doc.get("entities"),
        "classification": doc.get("classification"),
        "validation": doc.get("validation"),
        "extractedFields": [
            {"label": f["label"], "value": f["value"], "confidence": f"{f.get('confidence', 0)}%"}
            for f in doc.get("extracted_fields", [])
        ],
        "anomalies": doc.get("anomalies", []),
        "timeline": doc.get("timeline", []),
    }
