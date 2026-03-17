from motor.motor_asyncio import AsyncIOMotorClient

from params import MONGODBURL
client = AsyncIOMotorClient(MONGODBURL)
db = client["Hackathon"]

document_collection = db["documents"]
case_collection = db["cases"]
compliance_collection = db["compliances"]