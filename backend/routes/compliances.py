from fastapi import APIRouter, HTTPException
from bson import ObjectId
from config.database import compliance_collection

_router = APIRouter(prefix="/api/compliances", tags=["compliances"])


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
        "decisionHistory": comp.get("decision_history", []),
    }
