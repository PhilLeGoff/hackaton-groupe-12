import pytest
from httpx import AsyncClient
from main import app  # chemin vers ton main.py FastAPI

@pytest.mark.asyncio
async def test_create_document():
    async with AsyncClient(app=app, base_url="http://test") as client:

        # récupéreration de tous les documents
        response2 = await client.get("/documents")
        assert response2.status_code == 200
        print(len(response2.json())) 
        print(response2.json()[0])