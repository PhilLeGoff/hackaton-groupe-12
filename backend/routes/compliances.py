from fastapi import APIRouter, HTTPException
from bson import ObjectId
from bson.errors import InvalidId
from config.database import compliance_collection, case_collection
from schemas.compliance import ComplianceCreate, ComplianceUpdate, ComplianceResponse, ComplianceListResponse

_router = APIRouter(prefix="/api/compliances", tags=["compliances"])

# Get all compliances
@_router.get("", response_model=ComplianceListResponse)
async def get_compliances():
    compliances = []
    async for comp in compliance_collection.find():
        compliances.append({
            "id": str(comp["_id"]),
            "globalChecks": comp.get("global_checks", []),
            "requiredDocuments": comp.get("required_documents", []),
            "complianceAnomalies": comp.get("anomalies", []),
            "decisionHistory": comp.get("decision_history", []),
        })
    return {"data": compliances}

# Get compliance by ID
@_router.get("/{compliance_id}", response_model=ComplianceResponse)
async def get_compliance(compliance_id: str):
    try:
        oid = ObjectId(compliance_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid compliance ID")

    comp = await compliance_collection.find_one({"_id": oid})
    if not comp:
        raise HTTPException(status_code=404, detail="Compliance not found")

    return {
        "id": str(comp["_id"]),
        "globalChecks": comp.get("global_checks", []),
        "requiredDocuments": comp.get("required_documents", []),
        "complianceAnomalies": comp.get("anomalies", []),
        "decisionHistory": comp.get("decision_history", [])
    }
  
# Get compliance by case ID
@_router.get("/case/{case_id}", response_model=ComplianceResponse)
async def get_compliance_by_case(case_id: str):
    try:
        oid = ObjectId(case_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid case ID")

    comp = await compliance_collection.find_one({"case_id": oid})
    if not comp:
        raise HTTPException(status_code=404, detail="No compliance found for this case")

    return {
        "id": str(comp["_id"]),
        "globalChecks": comp.get("global_checks", []),
        "requiredDocuments": comp.get("required_documents", []),
        "complianceAnomalies": comp.get("anomalies", []),
        "decisionHistory": comp.get("decision_history", [])
    }

# Create compliance
@_router.post("")
async def create_compliance(payload: ComplianceCreate):
    try:
        case_id = ObjectId(payload.case_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid case ID")

    compliance = {
        "case_id": case_id,
        "status": "pending",
        "decision": None,
        "notes": payload.notes
    }

    result = await compliance_collection.insert_one(compliance)
    compliance["_id"] = str(result.inserted_id)
    compliance["case_id"] = str(case_id)

    return compliance


# Update compliance
@_router.put("/{compliance_id}")
async def update_compliance(compliance_id: str, payload: ComplianceUpdate):
    try:
        object_id = ObjectId(compliance_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid compliance ID")

    result = await compliance_collection.update_one(
        {"_id": object_id},
        {"$set": {
            "decision": payload.decision,
            "status": "done"
        }}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Compliance not found")

    # Sync case status based on decision
    comp = await compliance_collection.find_one({"_id": object_id})
    if comp and comp.get("case_id"):
        decision_to_status = {
            "approve": "approved",
            "reject": "rejected",
            "review": "pending",
        }
        case_status = decision_to_status.get(payload.decision, "pending")
        await case_collection.update_one(
            {"_id": comp["case_id"]},
            {"$set": {"status": case_status}}
        )

    return {"message": "Compliance updated"}
