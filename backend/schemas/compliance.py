from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

class DecisionEnum(str, Enum):
    approve = "approve"
    reject = "reject"
    review = "review"

class ComplianceCreate(BaseModel):
    case_id: str
    notes: Optional[str] = ""

class ComplianceUpdate(BaseModel):
    decision: DecisionEnum
    
class GlobalCheck(BaseModel):
    label: str
    passed: bool

class RequiredDocument(BaseModel):
    name: str
    status: str
    type: str

class ComplianceAnomaly(BaseModel):
    title: str
    description: str
    level: str

class DecisionHistoryItem(BaseModel):
    action: str
    date: str
    status: str

class ComplianceResponse(BaseModel):
    id: str
    globalChecks: List[GlobalCheck] = []
    requiredDocuments: List[RequiredDocument] = []
    complianceAnomalies: List[ComplianceAnomaly] = []
    decisionHistory: List[DecisionHistoryItem] = []

class ComplianceListResponse(BaseModel):
    data: List[ComplianceResponse]