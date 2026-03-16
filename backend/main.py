from fastapi import FastAPI
from utils.logger import logger
from routes.uploadsRoute import _router as uploadRouter

app=FastAPI(title="ceci est l'api permettant d'analyser des documents",
            version="1.0",
            contact={
                "name":"Taise de these NGANGA YABIE",
                "email":"gihamos@gmail.com"
            })


app.include_router(uploadRouter)
logger.info(msg="Demarage de l'application")


@app.get("/")
def home():
    return {
        "message": "api fonctionnel"
    } 