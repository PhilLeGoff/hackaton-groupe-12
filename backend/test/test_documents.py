import pytest
from httpx import AsyncClient
from main import app  # chemin vers ton main.py FastAPI

@pytest.mark.asyncio
async def test_create_document():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # création du document
        response = await client.post("/documents", json={"name": "test.pdf", "type": "pdf"})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test.pdf"

        # récupéreration de tous les documents
        response2 = await client.get("/documents")
        assert response2.status_code == 200
        assert len(response2.json()) == 1