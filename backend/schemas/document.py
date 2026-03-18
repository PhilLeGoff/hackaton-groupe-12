from pydantic import BaseModel
from typing import Optional, Dict, List, Any

class DocumentUpdate(BaseModel):
    status: str
    extracted_fields: Optional[Dict] = {}
    
class ExtractedField(BaseModel):
    label: str
    value: Any
    confidence: float

class TimelineItem(BaseModel):
    step: str
    status: str
    date: str

class DocumentResponse(BaseModel):
    id: str
    name: Optional[str]
    type: Optional[str]
    status: Optional[str]
    confidence: Optional[float]

class DocumentDetailResponse(DocumentResponse):
    ocr_text: Optional[str]
    entities: Optional[dict]
    classification: Optional[dict]
    validation: Optional[dict]
    extractedFields: List[ExtractedField] = []
    anomalies: List[Any] = []
    timeline: List[TimelineItem] = []

class PaginatedDocumentResponse(BaseModel):
    data: List[DocumentResponse]
    total: int
    limit: int
    offset: int

class FieldAccuracyDetail(BaseModel):
    expected: str | None
    predicted: str | None
    matched: bool


class FieldAccuracyResponse(BaseModel):
    matched_fields: int
    total_fields: int
    accuracy: float
    details: Dict[str, FieldAccuracyDetail]


class OCRMetricsResponse(BaseModel):
    character_error_rate: float
    word_error_rate: float
    field_accuracy: FieldAccuracyResponse
    summary: Dict[str, Any]