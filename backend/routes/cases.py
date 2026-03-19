from fastapi import APIRouter, HTTPException
from bson import ObjectId
from bson.errors import InvalidId
from config.database import case_collection, document_collection, compliance_collection
from schemas.case import CaseCreate, CaseUpdate, CaseDetailResponse, CaseListResponse, CaseAutofillResponse, DocumentAutofill, ComplianceAutofill

try:
    from ia.anomaly_detection.detector import validate_cross_documents
except ImportError:
    def validate_cross_documents(documents):
        return {"anomalies": [], "all_sirets_match": True}

# Mapping label humain → clé technique pour reconstruire les entités depuis extracted_fields
_LABEL_TO_KEY = {
    "Numero de facture": "invoice_number",
    "Numero de devis": "quote_number",
    "Date d'emission": "issue_date",
    "Date d'echeance": "due_date",
    "Date de validite": "valid_until",
    "Date d'expiration": "expiry_date",
    "Fournisseur": "supplier_name",
    "Client": "client_name",
    "SIRET": "siret",
    "SIRET fournisseur": "supplier_siret",
    "SIRET client": "customer_siret",
    "SIREN": "siren",
    "TVA intracommunautaire": "vat_number",
    "TVA fournisseur": "supplier_vat_number",
    "TVA client": "customer_vat_number",
    "Montant HT": "total_ht",
    "Montant TVA": "total_tva",
    "Montant TTC": "total_ttc",
    "IBAN": "iban",
    "BIC": "bic",
    "Banque": "bank_name",
    "Code NAF": "code_naf",
    "Denomination": "denomination",
    "Forme juridique": "forme_juridique",
    "Capital social": "capital_social",
    "Adresse du siege": "adresse_siege",
    "RCS": "rcs",
    "Greffe": "greffe",
    "Date d'immatriculation": "date_immatriculation",
    "Dirigeant": "dirigeant",
}

def _entities_from_extracted_fields(extracted_fields: list) -> dict:
    """Reconstruit un dict d'entités à partir de la liste extracted_fields avec labels humains."""
    entities = {}
    for f in extracted_fields:
        label = f.get("label", "")
        value = f.get("value")
        if not label or not value:
            continue
        key = _LABEL_TO_KEY.get(label, label)
        entities[key] = value
    return entities

_router = APIRouter(prefix="/api/cases", tags=["cases"])

# Get all cases
@_router.get("", response_model=CaseListResponse)
async def get_cases():
    try:
        cases = []
        async for case in case_collection.find():
            case_id = case["_id"]
            # Count documents linked to this case (try both ObjectId and string)
            doc_count = await document_collection.count_documents({"case_id": case_id})
            if doc_count == 0:
                doc_count = await document_collection.count_documents({"case_id": str(case_id)})
            cases.append({
                "id": str(case_id),
                "companyName": case.get("company_name"),
                "siret": case.get("siret"),
                "status": case.get("status"),
                "documents": doc_count,
                "owner": case.get("owner"),
                "updatedAt": case.get("updated_at"),
            })
        return {"data": cases}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"erreur de connection : {e}")

# Get case by ID
@_router.get("/{case_id}", response_model=CaseDetailResponse)
async def get_case(case_id: str):
    try:
        oid = ObjectId(case_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid case ID")

    case = await case_collection.find_one({"_id": oid})

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Count documents linked to this case
    doc_count = await document_collection.count_documents({"case_id": oid})
    if doc_count == 0:
        doc_count = await document_collection.count_documents({"case_id": str(oid)})

    return {
        "id": str(case["_id"]),
        "companyName": case.get("company_name"),
        "siret": case.get("siret"),
        "status": case.get("status"),
        "documents": doc_count,
        "contact": case.get("contact"),
        "sector": case.get("sector"),
        "updatedAt": case.get("updated_at")
    }

# Create case
@_router.post("", response_model=CaseDetailResponse)
async def create_case(payload: CaseCreate):
    case = payload.model_dump()
    case["status"] = "pending"
    result = await case_collection.insert_one(case)

    return {
        "id": str(result.inserted_id),
        "companyName": case.get("company_name"),
        "siret": case.get("siret"),
        "status": case.get("status"),
        "documents": 0,
        "contact": case.get("contact"),
        "sector": case.get("sector"),
        "updatedAt": case.get("updated_at")
    }
      
# Update case
@_router.put("/{case_id}")
async def update_case(case_id: str, payload: CaseUpdate):
    try:
        object_id = ObjectId(case_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid case ID")

    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    try:
     # comment: 
     result = await case_collection.update_one(
        {"_id": object_id},
        {"$set": update_data}
        )
    except Exception as e:
        raise HTTPException(detail="erreur de se connecter à la db",status_code=500)


    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Case not found")

    return {"message": "Case updated"}

# Get case autofill data
@_router.get("/{case_id}/autofill", response_model=CaseAutofillResponse)
async def get_case_autofill(case_id: str):
    try:
        oid = ObjectId(case_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid case ID")

    case = await case_collection.find_one({"_id": oid})
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Collect all documents for this case (try both ObjectId and string for case_id)
    documents = []
    raw_docs = []
    vat_found = None
    iban_found = None
    address_found = None
    company_name_found = None

    # Documents can have case_id as ObjectId or string depending on creation path
    doc_cursor_results = []
    async for doc in document_collection.find({"case_id": oid}):
        doc_cursor_results.append(doc)
    if not doc_cursor_results:
        async for doc in document_collection.find({"case_id": str(oid)}):
            doc_cursor_results.append(doc)

    for doc in doc_cursor_results:
        doc_type = doc.get("type") or (doc.get("classification") or {}).get("document_type")
        raw_entities = doc.get("entities") or {}
        extracted = doc.get("extracted_fields") or []

        # Use the "details" sub-dict from NER if available (contains granular fields)
        entities = raw_entities.get("details", raw_entities) if isinstance(raw_entities, dict) else {}

        # Fallback: rebuild entities from extracted_fields using label→key mapping
        if not entities and isinstance(extracted, list):
            entities = _entities_from_extracted_fields(extracted)

        raw_docs.append({
            "type": doc_type,
            "entities": entities,
            "extracted_fields": extracted,
        })

        # Extract useful fields for autofill — try all known key variants
        if not vat_found:
            vat_found = (
                raw_entities.get("vat")  # top-level NER key
                or entities.get("vat_number")
                or entities.get("supplier_vat_number")
            )
        if not iban_found:
            iban_found = raw_entities.get("iban") or entities.get("iban")
        if not address_found:
            address_found = entities.get("adresse_siege") or entities.get("address") or entities.get("supplier_address")
        if not company_name_found:
            company_name_found = (
                raw_entities.get("company_name")
                or entities.get("supplier_name")
                or entities.get("denomination")
                or entities.get("client_name")
            )

        documents.append(DocumentAutofill(
            type=doc_type,
            date=str(doc.get("created_at") or doc.get("processed_at") or ""),
            amounts={
                "ht": raw_entities.get("amount_ht") or entities.get("total_ht"),
                "ttc": raw_entities.get("amount_ttc") or entities.get("total_ttc")
            },
            status=doc.get("status"),
            anomalies=doc.get("anomalies") or []
        ))

    # Cross-validate documents
    cross_result = validate_cross_documents(raw_docs)

    # Detect document presence
    doc_types = [d.type for d in documents if d.type]
    doc_types_lower = [t.lower() for t in doc_types]
    kbis_present = any("kbis" in t for t in doc_types_lower)
    rib_present = any("rib" in t or "bank" in t for t in doc_types_lower)
    urssaf_present = any("urssaf" in t or "attestation" in t for t in doc_types_lower)

    # Check URSSAF expiry from cross-validation
    urssaf_valid = urssaf_present and not any(
        a.get("field") == "urssaf_expiry" and a.get("level") == "error"
        for a in cross_result.get("anomalies", [])
    )
    urssaf_expiry = None
    for doc_raw in raw_docs:
        doc_type_lower = (doc_raw.get("type") or "").lower()
        if "urssaf" in doc_type_lower or "attestation" in doc_type_lower:
            ents = doc_raw.get("entities") or {}
            urssaf_expiry = (
                ents.get("expiry_date")
                or ents.get("expiration_date")
                or ents.get("valid_until")
                or ents.get("due_date")
            )
            break

    compliance = ComplianceAutofill(
        urssaf_valid=urssaf_valid,
        urssaf_expiry=urssaf_expiry,
        kbis_present=kbis_present,
        rib_present=rib_present,
        iban=iban_found,
        all_sirets_match=cross_result.get("all_sirets_match", True),
        anomalies=cross_result.get("anomalies", [])
    )

    return CaseAutofillResponse(
        company_name=company_name_found or case.get("company_name"),
        siret=case.get("siret"),
        vat=vat_found or case.get("vat"),
        address=address_found or case.get("address"),
        documents=documents,
        compliance=compliance
    )