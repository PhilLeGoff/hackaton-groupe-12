from pydantic import BaseModel
from typing import Optional, Dict

class DocumentUpdate(BaseModel):
    status: str
    extracted_fields: Optional[Dict] = {}