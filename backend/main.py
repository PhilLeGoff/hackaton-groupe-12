from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from utils.logger import logger
from routes.uploadsRoute import _router as uploadRouter
from routes.documents import _router as documentRouter
from routes.cases import _router as caseRouter
from routes.compliances import _router as complianceRouter

app = FastAPI(
    title="DocuScan AI API",
    version="1.0",
)

# Autoriser le frontend (React) à communiquer avec le backend en local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(uploadRouter)
app.include_router(documentRouter)
app.include_router(caseRouter)
app.include_router(complianceRouter)

logger.info(msg="Demarage de l'application")


@app.get("/")
def home():
    return {"message": "api fonctionnel"}