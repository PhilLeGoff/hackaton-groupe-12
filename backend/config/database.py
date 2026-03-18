from motor.motor_asyncio import AsyncIOMotorClient

from params import MONGODBURL

def get_db():
    try:
        # comment:
        client = AsyncIOMotorClient(MONGODBURL)
        return client["Hackathon"] 
    except Exception as e:
        raise RuntimeError(e)
    # end try
    
    
db = get_db()

document_collection = db["documents"]
case_collection = db["cases"]
compliance_collection = db["compliances"]