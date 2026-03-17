from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from utils.logger import logger
from routes.uploadsRoute import _router as uploadRouter
from routes.compliances import _router as complianceRouter
from routes.documents import _router as documentRouter
from routes.cases import _router as caseRouter

app=FastAPI(title="ceci est l'api permettant d'analyser des documents",
            version="1.0",
            contact={
                "name":"Taise de these NGANGA YABIE",
                "email":"gihamos@gmail.com"
            })


 #Pour autoriser la communication entre le frontend et le backend en environnement local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(uploadRouter)
logger.info(msg="Demarage de l'application")

app.include_router(complianceRouter)
logger.info(msg="Route de compliance ajoutée à l'application")

app.include_router(documentRouter)
logger.info(msg="Route de document ajoutée à l'application")

app.include_router(caseRouter)
logger.info(msg="Route de case ajoutée à l'application")

@app.get("/")
def home():
    return {
        "message": "api fonctionnel"
    } 