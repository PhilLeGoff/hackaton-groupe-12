from fastapi import APIRouter, UploadFile, File, HTTPException

_router = APIRouter()

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/jpg",
    "text/plain"
}

MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 Mo

@_router.post("/")
async def load(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Format non supporté : {file.content_type}. "
                f"Formats acceptés : {', '.join(ALLOWED_MIME_TYPES)}"
            )
        )

    # Traitement du fichier ici
    content = await file.read()
    
    # Vérification de la taille
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Le fichier dépasse la taille maximale autorisée de 2 Mo."
        )

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(content)
    }
