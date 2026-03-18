from fastapi import APIRouter, HTTPException
from bson import ObjectId
from config.database import case_collection, document_collection, compliance_collection
from bson import ObjectId
from bson.errors import InvalidId
from schemas.case import CaseCreate, CaseUpdate, CaseDetailResponse, CaseListResponse, CaseAutofillResponse, DocumentAutofill, ComplianceAutofill

_router = APIRouter(prefix="/api/cases", tags=["cases"])

# Get all cases
@_router.get("", response_model=CaseListResponse)
async def get_cases():
    try:
        # comment: 
        cases = []
        async for case in case_collection.find():
            cases.append({
            "id": str(case["_id"]),
            "companyName": case.get("company_name"),
            "siret": case.get("siret"),
            "status": case.get("status"),
            "documents": case.get("documents"),
            "owner": case.get("owner"),
            "updatedAt": case.get("updated_at"),
            })
        return cases
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"erreur de connection : {e}")
    # end try

# Get case by ID
@_router.get("/{case_id}", response_model=CaseDetailResponse)
async def get_case(case_id: str):
    try:
        # comment: 
        case = await case_collection.find_one({"_id": ObjectId(case_id)})
    except Exception as e:
        raise HTTPException(detail="erreur de se connecter à la db",status_code=500)
    # end try
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    return {
        "id": str(case["_id"]),
        "companyName": case.get("company_name"),
        "siret": case.get("siret"),
        "status": case.get("status"),
        "documents": case.get("documents"),
        "contact": case.get("contact"),
        "sector": case.get("sector"),
        "updatedAt": case.get("updated_at")
    }

# Create case
@_router.post("", response_model=CaseDetailResponse)
async def create_case(payload: CaseCreate):
    case = payload.model_dump()
    case["status"] = "pending"
    try:
        # comment: 
        result = case_collection.insert_one(case)
    except Exception as e:
        raise HTTPException(detail="erreur de se connecter à la db",status_code=500)
    # end try
    
    case["_id"] = str(result.inserted_id)

    return case
      
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
     result = case_collection.update_one(
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

    documents = []
    async for doc in document_collection.find({"case_id": oid}):
        documents.append(DocumentAutofill(
            type=doc.get("type") or doc.get("classification", {}).get("document_type"),
            date=doc.get("created_at") or doc.get("processed_at"),
            amounts={
                "ht": doc.get("extracted_fields", {}).get("amount_ht"),
                "ttc": doc.get("extracted_fields", {}).get("amount_ttc")
            },
            status=doc.get("status"),
            anomalies=doc.get("anomalies", [])
        ))

    compliance_data = await compliance_collection.find_one({"case_id": oid})
    if compliance_data:
        global_checks = {c["label"]: c["passed"] for c in compliance_data.get("global_checks", [])}
        required_docs = {d["name"]: d["status"] for d in compliance_data.get("required_documents", [])}

        urssaf_valid = global_checks.get("Attestation URSSAF présente", False)
        kbis_present = required_docs.get("KBIS", "Manquant") == "Présent"
        rib_present = required_docs.get("RIB", "Manquant") == "Présent"
        iban = None
        for doc in documents:
            if doc.type in ["RIB", "Bank"]:
                iban = next((f["value"] for f in doc.anomalies if f.get("label")=="iban"), None)
                break

        all_sirets_match = global_checks.get("SIRET cohérent sur les pièces", False)

        anomalies = compliance_data.get("anomalies", [])

        compliance = ComplianceAutofill(
            urssaf_valid=urssaf_valid,
            urssaf_expiry=compliance_data.get("urssaf_expiry"),
            kbis_present=kbis_present,
            rib_present=rib_present,
            iban=iban,
            all_sirets_match=all_sirets_match,
            anomalies=anomalies
        )
    else:
        compliance = ComplianceAutofill()

    return CaseAutofillResponse(
        company_name=case.get("company_name"),
        siret=case.get("siret"),
        vat=case.get("vat"),
        address=case.get("address"),
        documents=documents,
        compliance=compliance
    )