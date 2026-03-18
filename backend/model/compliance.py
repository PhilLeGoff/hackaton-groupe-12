from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime

class ComplianceStatus(str, Enum):
    success = "success"
    warning = "warning"
    danger = "danger"


class AnomalyLevel(str, Enum):
    info = "info"
    warning = "warning"
    danger = "danger"


class GlobalCheck(BaseModel):
    label: str
    passed: bool


class RequiredDocument(BaseModel):
    name: str
    status: str
    type: ComplianceStatus


class ComplianceAnomaly(BaseModel):
    title: str
    description: str
    level: AnomalyLevel


class DecisionStep(BaseModel):
    action: str
    date: str
    status: str


class ComplianceModel(BaseModel):
    id: str = Field(alias="_id")

    case_id: str
    global_checks: Optional[List[GlobalCheck]] = []
    required_documents: Optional[List[RequiredDocument]] = []
    anomalies: Optional[List[ComplianceAnomaly]] = []
    decision_history: Optional[List[DecisionStep]] = []

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[str] = None

    class Config:
        populate_by_name = True