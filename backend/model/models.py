from pydantic import BaseModel,Field
from typing import Dict, Any,Optional

class Documment(BaseModel):
    id: Optional[str]=Field(default=None,alias="_id")
    filename: str
    content_type: str
    size: int
    metadata: Dict[str, Any]
