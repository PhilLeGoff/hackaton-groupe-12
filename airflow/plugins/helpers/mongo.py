"""Connexion MongoDB sync pour les tasks Airflow."""

from pymongo import MongoClient
from bson import ObjectId

MONGO_URL = "mongodb://mongodb:27017"
MONGO_DB = "Hakathon"
MONGO_COLLECTION = "documents"


def get_collection(collection_name: str = MONGO_COLLECTION):
    client = MongoClient(MONGO_URL)
    return client[MONGO_DB][collection_name]


def get_document(document_id: str) -> dict:
    collection = get_collection()
    doc = collection.find_one({"_id": ObjectId(document_id)})
    if not doc:
        raise ValueError(f"Document {document_id} introuvable")
    return doc


def update_document(document_id: str, update_fields: dict):
    collection = get_collection()
    result = collection.update_one(
        {"_id": ObjectId(document_id)},
        {"$set": update_fields},
    )
    if result.matched_count == 0:
        raise ValueError(f"Document {document_id} introuvable")
