import pytest
import mongomock
from motor.motor_asyncio import AsyncIOMotorClient
from unittest.mock import patch

# Patch AsyncIOMotorClient pour utiliser mongomock
@pytest.fixture(autouse=True)
def mock_motor():
    # crée un client mongomock (DB en mémoire)
    mock_client = mongomock.MongoClient()

    # patch de AsyncIOMotorClient pour renvoyer notre mock
    with patch("motor.motor_asyncio.AsyncIOMotorClient", return_value=mock_client):
        yield