from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    facture = "Facture"
    kbis = "KBIS"
    rib = "RIB"
    devis = "Devis"
    attestation = "Attestation"

class DocumentStatus(str, Enum):
    uploaded = "Upload"
    processing = "En cours"
    done = "Analyse terminée"
    review = "À vérifier"
    error = "Erreur"

class AnomalyLevel(str, Enum):
    info = "info"
    warning = "warning"
    error = "error"


class ConfidenceField(BaseModel):
    label: str
    value: str
    confidence: Optional[float] = None

class Anomaly(BaseModel):
    title: str
    description: str
    level: AnomalyLevel

class TimelineStep(BaseModel):
    step: str
    status: str
    date: str


class DocumentModel(BaseModel):
    id: str = Field(alias="_id")

    name: str
    type: DocumentType
    status: DocumentStatus
    confidence: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    extracted_fields: Optional[List[ConfidenceField]] = []
    anomalies: Optional[List[Anomaly]] = []
    timeline: Optional[List[TimelineStep]] = []
    ocr_text: Optional[str] = None
    raw_path: Optional[str] = None
    clean_path: Optional[str] = None
    curated_path: Optional[str] = None

    class Config:
        populate_by_name = True