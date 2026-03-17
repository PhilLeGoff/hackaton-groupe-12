from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class CaseStatus(str, Enum):
    conforme = "Conforme"
    non_conforme = "Non conforme"
    review = "À vérifier"


class CaseModel(BaseModel):
    id: str = Field(alias="_id")
    company_name: str
    siret: str
    status: CaseStatus
    documents: int
    owner: str
    updated_at: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    contact: Optional[str] = None
    sector: Optional[str] = None

    class Config:
        populate_by_name = True