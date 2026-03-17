from fastapi import APIRouter, HTTPException
from bson import ObjectId
from config.database import case_collection

_router = APIRouter(prefix="/api/cases", tags=["cases"])


@_router.get("")
async def get_cases():
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


@_router.get("/{case_id}")
async def get_case(case_id: str):
    case = await case_collection.find_one({"_id": ObjectId(case_id)})
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
        "updatedAt": case.get("updated_at"),
    }
