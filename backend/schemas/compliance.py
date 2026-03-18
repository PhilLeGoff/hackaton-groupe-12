from pydantic import BaseModel
from typing import Optional
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