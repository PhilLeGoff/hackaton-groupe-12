from pydantic import BaseModel
from typing import List


class UploadFileResponse(BaseModel):
    id: str
    filename: str
    status: str
    message: str | None = None


class UploadResponse(BaseModel):
    files: List[UploadFileResponse]