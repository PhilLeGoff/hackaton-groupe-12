from fastapi import APIRouter, HTTPException
from bson import ObjectId
from config.database import case_collection
from bson import ObjectId
from bson.errors import InvalidId
from schemas.case import CaseCreate, CaseUpdate

_router = APIRouter(prefix="/api/cases", tags=["cases"])

# Get all cases
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

# Get case by ID
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
        "updatedAt": case.get("updated_at")
    }

# Create case
@_router.post("")
async def create_case(payload: CaseCreate):
    case = payload.model_dump()
    case["status"] = "pending"

    result = case_collection.insert_one(case)
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

    result = case_collection.update_one(
        {"_id": object_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Case not found")

    return {"message": "Case updated"}
