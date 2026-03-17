# Image Python légère
FROM python:3.11-slim

# Dossier de travail dans le container
WORKDIR /app

# Copie des dépendances d'abord (pour profiter du cache Docker)
COPY requirement.txt .

# Installation des dépendances
RUN pip install --no-cache-dir -r requirement.txt

# Copie du code source
COPY . .

# Port exposé par l'API
EXPOSE 8000

# Lancement de l'API avec uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
