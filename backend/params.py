import os
from dotenv import load_dotenv
from pathlib import Path


load_dotenv()


BASE_DIR = Path(__file__).resolve().parent

MONGODBURL=os.getenv("MONGODBURL",default="mongodb://localhost:27017")
JWT_SECRET=os.getenv("JWT_SECRET", default="12c772d5f202e6e965733a956e0a32f5c12c3d500452844cb63d50c1aa478090")
ALGORITHM = "HS256"
FFMPEG_PATH=BASE_DIR / "module/windows/ffmpeg/bin"

os.environ["PATH"] += os.pathsep + os.path.abspath(FFMPEG_PATH)

####################
# constante pour la connexion au provider
###################

PROVIDER=os.getenv("PROVIDER")
PROVIDER_URL=os.getenv("PROVIDER_URL")
PROVIDER_API_KEY=os.getenv("PROVIDER_API_KEY")


if(PROVIDER is None ):
    PROVIDER="ollama"
    PROVIDER_URL="http://localhost:11434"
elif(PROVIDER.lower()=="ollama" and PROVIDER_URL is not None):
    PROVIDER=PROVIDER.lower()

elif(PROVIDER.lower()=="openai" and PROVIDER_URL is not None and PROVIDER_API_KEY is not None):
     PROVIDER=PROVIDER.lower()
else:
    raise ValueError("variables d'environement manquantes  << PROVIDER , PROVIDER_URL, PROVIDER_API_KEY>>\n la variable d'environement Provider Prend pour valeur ollama ou openai")


