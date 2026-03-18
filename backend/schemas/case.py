from pydantic import BaseModel, Field
from typing import Optional, List, Any

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
    
class DocumentAutofill(BaseModel):
    type: Optional[str]
    date: Optional[str]
    amounts: Optional[dict] = {}
    status: Optional[str]
    anomalies: List[Any] = []

class ComplianceAutofill(BaseModel):
    urssaf_valid: bool = False
    urssaf_expiry: Optional[str]
    kbis_present: bool = False
    rib_present: bool = False
    iban: Optional[str]
    all_sirets_match: bool = False
    anomalies: List[Any] = []

class CaseAutofillResponse(BaseModel):
    company_name: Optional[str]
    siret: Optional[str]
    vat: Optional[str]
    address: Optional[str]
    documents: List[DocumentAutofill] = []
    compliance: ComplianceAutofill = ComplianceAutofill()