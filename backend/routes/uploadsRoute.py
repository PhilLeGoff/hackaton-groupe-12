from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, HTTPException

from config.database import document_collection
from services.document_processing import DocumentProcessingError, process_document
from utils.extractorMetaData import extract_docx_metadata, extract_pdf_metadata

_router = APIRouter()

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/jpeg",
    "image/jpg",
    "image/png",
    "text/plain"
}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 Mo

@_router.post(
    "/Load",
    openapi_extra={
        "requestBody": {
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "files": {
                                "type": "array",
                                "items": {"type": "string", "format": "binary"}
                            }
                        }
                    }
                }
            }
        }
    }
)
async def load(files: list[UploadFile] = File(...)):
    results = []

    for file in files:
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=403,
                detail=f"Format non supporté : {file.content_type}"
            )

        content = await file.read()

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Le fichier {file.filename} dépasse la taille maximale autorisée."
            )

        try:
            analysis = process_document(content, file.content_type, file.filename or "document")
        except DocumentProcessingError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        metadata = {}
        if file.content_type == "application/pdf":
            metadata = extract_pdf_metadata(content)
        elif (
            file.content_type
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ):
            metadata = extract_docx_metadata(content)

        document_id = str(uuid4())
        document_record = {
            "_id": document_id,
            "name": file.filename,
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(content),
            "type": analysis["document_type"],
            "status": analysis["status"],
            "confidence": analysis["confidence"],
            "metadata": metadata,
            "ocr_text": analysis["ocr_text"],
            "entities": analysis["entities"],
            "extracted_fields": analysis["extracted_fields"],
            "anomalies": analysis["anomalies"],
            "timeline": analysis["timeline"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        await document_collection.insert_one(document_record)

        results.append({
            "id": document_id,
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(content),
            "type": analysis["document_type"],
            "status": analysis["status"],
            "confidence": analysis["confidence"],
            "fields": analysis["extracted_fields"],
        })

    return {"files": results}
