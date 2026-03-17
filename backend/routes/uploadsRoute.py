from fastapi import APIRouter, UploadFile, File, HTTPException

_router = APIRouter()

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/jpeg",
    "image/jpg",
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

        results.append({
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(content)
        })

    return {"files": results}
