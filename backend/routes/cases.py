from fastapi import APIRouter, HTTPException
from bson import ObjectId
from config.database import case_collection
from model.case import CaseUpdateModel,CaseCreateModel

_router = APIRouter(prefix="/api/cases", tags=["cases"])


@_router.get("")
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


@_router.get("/{case_id}")
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
        "updatedAt": case.get("updated_at"),
    }




@_router.put("/cases/{id}")
async def update_case(id: str, payload: CaseUpdateModel):
    # Vérification ID MongoDB
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID invalide")

    update_data = {k: v for k, v in payload.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour")

    result = await case_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Case non trouvée")

    return {"message": "Case mise à jour", "updated": update_data}


@_router.post("/")
async def update_case(payload: CaseCreateModel):
    try:
        result = await case_collection.insert_one(payload)
        return{
            "message":"le document a été crée",
            "data":result.__inserted_id
        }
    except:
        raise HTTPException(detail="erreur de se connecter à la db",status_code=500)




