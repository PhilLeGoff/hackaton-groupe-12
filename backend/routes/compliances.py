from fastapi import APIRouter, HTTPException
from bson import ObjectId
from config.database import compliance_collection
from bson import ObjectId
from bson.errors import InvalidId
from schemas.compliance import ComplianceCreate, ComplianceUpdate

_router = APIRouter(prefix="/api/compliances", tags=["compliances"])

# Get all compliances
@_router.get("")
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
    return compliances

# Get compliance by ID
@_router.get("/{compliance_id}")
async def get_compliance(compliance_id: str):
    comp = await compliance_collection.find_one({"_id": ObjectId(compliance_id)})
    if not comp:
        raise HTTPException(status_code=404, detail="Compliance not found")

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

    result = compliance_collection.insert_one(compliance)
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

    result = compliance_collection.update_one(
        {"_id": object_id},
        {"$set": {
            "decision": payload.decision,
            "status": "done"
        }}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Compliance not found")

    return {"message": "Compliance updated"}
