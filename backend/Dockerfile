# Image Python légère
FROM python:3.11-slim

# Tesseract OCR + poppler (pdftoppm) pour le pipeline OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-fra \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Dossier de travail dans le container
WORKDIR /app



RUN python -m pip install --upgrade pip

# Copie des dépendances d'abord (pour profiter du cache Docker)
COPY requirements.txt .


# Installation des dépendances
RUN pip install --no-cache-dir -r requirements.txt


# Copie du code source
COPY . .

# Port exposé par l'API
EXPOSE 8000

# Lancement de l'API avec uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
