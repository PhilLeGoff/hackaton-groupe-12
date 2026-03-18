import hashlib
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException
import httpx
from bson import ObjectId

from config.database import document_collection
from params import HDFS_WEBHDFS_URL, AIRFLOW_BASE_URL

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
    "text/plain",
}

MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 Mo
MAX_FILES = 3
HDFS_USER = "root"


async def _hdfs_mkdir(path: str):
    url = f"{HDFS_WEBHDFS_URL}{path}?op=MKDIRS&user.name={HDFS_USER}"
    async with httpx.AsyncClient() as client:
        resp = await client.put(url, timeout=10)
        resp.raise_for_status()


async def _hdfs_write(path: str, data: bytes):
    parent = "/".join(path.split("/")[:-1])
    if parent:
        await _hdfs_mkdir(parent)
    url = f"{HDFS_WEBHDFS_URL}{path}?op=CREATE&user.name={HDFS_USER}&overwrite=true"
    async with httpx.AsyncClient() as client:
        resp = await client.put(url, follow_redirects=False, timeout=30)
        if resp.status_code == 307:
            redirect_url = resp.headers["Location"]
            resp2 = await client.put(redirect_url, content=data, timeout=60)
            resp2.raise_for_status()
        else:
            resp.raise_for_status()


async def _trigger_dag(document_id: str):
    url = f"{AIRFLOW_BASE_URL}/api/v1/dags/document_pipeline/dagRuns"
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            json={"conf": {"document_id": document_id}},
            auth=("admin", "admin"),
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        resp.raise_for_status()
@_router.post(
    "/api/upload",
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
async def upload(files: list[UploadFile] = File(...)):
    if len(files) > MAX_FILES:
        raise HTTPException(
            status_code=413,
            detail=f"Maximum {MAX_FILES} fichiers par upload",
        )

    results = []

    for file in files:
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=403,
                detail=f"Format non supporté : {file.content_type}",
            )

        content = await file.read()

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Le fichier {file.filename} dépasse {MAX_FILE_SIZE // (1024 * 1024)} Mo",
            )

        # Hash pour éviter les doublons
        file_hash = hashlib.sha256(content).hexdigest()
        existing = await document_collection.find_one({"file_hash": file_hash})
        if existing:
            results.append({
                "id": str(existing["_id"]),
                "filename": file.filename,
                "status": "duplicate",
                "message": "Document déjà uploadé",
            })
            continue

        # Sauvegarder métadonnées dans MongoDB
        doc = {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(content),
            "file_hash": file_hash,
            "status": "uploaded",
            "created_at": datetime.utcnow(),
        }
        insert_result = await document_collection.insert_one(doc)
        doc_id = str(insert_result.inserted_id)

        # Écrire fichier dans HDFS /raw/{id}/
        hdfs_path = f"/raw/{doc_id}/{file.filename}"
        try:
            await _hdfs_write(hdfs_path, content)
        except Exception as e:
            await document_collection.update_one(
                {"_id": ObjectId(doc_id)},
                {"$set": {"status": "error", "error": f"HDFS write: {e}"}},
            )
            raise HTTPException(status_code=500, detail=f"Erreur HDFS: {e}")

        # Trigger DAG Airflow
        try:
            await _trigger_dag(doc_id)
        except Exception as e:
            await document_collection.update_one(
                {"_id": ObjectId(doc_id)},
                {"$set": {"status": "error", "error": f"Airflow trigger: {e}"}},
            )
            raise HTTPException(status_code=500, detail=f"Erreur Airflow: {e}")

        results.append({
            "id": doc_id,
            "filename": file.filename,
            "status": "uploaded",
        })

    return {"files": results}
