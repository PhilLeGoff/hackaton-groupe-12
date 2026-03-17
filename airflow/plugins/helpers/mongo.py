"""Connexion MongoDB sync pour les tasks Airflow."""

import os
from pymongo import MongoClient
from bson import ObjectId

MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongodb:27017")
MONGO_DB = "Hackathon"
MONGO_COLLECTION = "documents"

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URL)
    return _client


def get_collection(collection_name: str = MONGO_COLLECTION):
    return _get_client()[MONGO_DB][collection_name]


def get_document(document_id: str) -> dict:
    doc = get_collection().find_one({"_id": ObjectId(document_id)})
    if not doc:
        raise ValueError(f"Document {document_id} introuvable")
    return doc


def update_document(document_id: str, update_fields: dict):
    result = get_collection().update_one(
        {"_id": ObjectId(document_id)},
        {"$set": update_fields},
    )
    if result.matched_count == 0:
        raise ValueError(f"Document {document_id} introuvable")
