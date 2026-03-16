from motor.motor_asyncio import AsyncIOMotorClient

from params import MONGODBURL
client = AsyncIOMotorClient(MONGODBURL)
db = client["Hakathon"]