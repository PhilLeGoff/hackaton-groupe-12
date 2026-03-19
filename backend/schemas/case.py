from pydantic import BaseModel, Field
from typing import Optional, List, Any

# --- Création / Mise à jour d'un cas ---
class CaseCreate(BaseModel):
    company_name: str = Field(..., example="Total Energies")
    siret: str = Field(..., min_length=14, max_length=14)
    contact: Optional[str] = None
    sector: Optional[str] = None

class CaseUpdate(BaseModel):
    company_name: Optional[str] = None
    siret: Optional[str] = None
    contact: Optional[str] = None
    sector: Optional[str] = None
    status: Optional[str] = None
    vat: Optional[str] = None
    iban: Optional[str] = None
    address: Optional[str] = None

# --- Réponse simple ---
class CaseResponse(BaseModel):
    id: str
    companyName: Optional[str] = None
    siret: Optional[str] = None
    status: Optional[str] = None
    documents: int = 0
    owner: Optional[str] = None
    updatedAt: Optional[str] = None

# --- Détails d'un cas ---
class CaseDetailResponse(BaseModel):
    id: str
    companyName: Optional[str] = None
    siret: Optional[str] = None
    status: Optional[str] = None
    documents: int = 0
    contact: Optional[str] = None
    sector: Optional[str] = None
    updatedAt: Optional[str] = None

# --- Liste de cas ---
class CaseListResponse(BaseModel):
    data: List[CaseResponse] = []

# --- Autofill documents ---
class DocumentAutofill(BaseModel):
    type: Optional[str] = None
    date: Optional[str] = None
    amounts: dict = {}  # dictionnaire vide par défaut
    status: Optional[str] = None
    anomalies: List[Any] = []

# --- Autofill compliance ---
class ComplianceAutofill(BaseModel):
    urssaf_valid: bool = False
    urssaf_expiry: Optional[str] = None
    kbis_present: bool = False
    rib_present: bool = False
    iban: Optional[str] = None
    all_sirets_match: bool = False
    anomalies: List[Any] = []

# --- Réponse autofill complète ---
class CaseAutofillResponse(BaseModel):
    company_name: Optional[str] = None
    siret: Optional[str] = None
    vat: Optional[str] = None
    address: Optional[str] = None
    documents: List[DocumentAutofill] = []
    compliance: ComplianceAutofill = ComplianceAutofill()  # déjà initialisé avec valeurs par défaut