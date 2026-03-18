from pydantic import BaseModel, Field
from typing import Optional, List

class CaseCreate(BaseModel):
    company_name: str = Field(..., example="Total Energies")
    siret: str = Field(..., min_length=14, max_length=14)
    contact: str
    sector: str

class CaseUpdate(BaseModel):
    company_name: Optional[str]
    siret: Optional[str]
    contact: Optional[str]
    sector: Optional[str]
    status: Optional[str]
    
class CaseResponse(BaseModel):
    id: str
    companyName: Optional[str]
    siret: Optional[str]
    status: Optional[str]
    documents: Optional[List[str]] = []
    owner: Optional[str]
    updatedAt: Optional[str]

class CaseDetailResponse(BaseModel):
    id: str
    companyName: Optional[str]
    siret: Optional[str]
    status: Optional[str]
    documents: Optional[List[str]] = []
    contact: Optional[str]
    sector: Optional[str]
    updatedAt: Optional[str]

class CaseListResponse(BaseModel):
    data: List[CaseResponse]