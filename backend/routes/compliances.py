from fastapi import APIRouter, HTTPException
from config.database import compliance_collection

router = APIRouter(prefix="/api/compliances", tags=["compliances"])

@router.get("")
async def get_compliances():
    compliances = []

    async for comp in compliance_collection.find():
        compliances.append({
            "id": comp["_id"],
            "globalChecks": comp.get("global_checks", []),
            "requiredDocuments": comp.get("required_documents", []),
            "complianceAnomalies": comp.get("anomalies", []),
            "decisionHistory": comp.get("decision_history", [])
        })

    return compliances

@router.get("/{compliance_id}")
async def get_compliance(compliance_id: str):

    comp = await compliance_collection.find_one({"_id": compliance_id})

    if not comp:
        raise HTTPException(status_code=404, detail="Compliance not found")

    return {
        "globalChecks": comp.get("global_checks", []),
        "requiredDocuments": comp.get("required_documents", []),
        "complianceAnomalies": comp.get("anomalies", []),
        "decisionHistory": comp.get("decision_history", [])
    }