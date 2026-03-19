FROM apache/airflow:2.9.1-python3.11

USER root

# ---------------- SYSTEM DEPENDENCIES (cached layer) ----------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-fra \
    poppler-utils \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

USER airflow

# ---------------- AIRFLOW DEPS (cached layer — changes rarely) ----------------
COPY airflow/requirements.txt /opt/airflow/requirements.txt
RUN pip install --no-cache-dir -r /opt/airflow/requirements.txt

# ---------------- IA DEPS (cached layer — heavy, changes rarely) ----------------
COPY ia/requirements.txt /tmp/ia-requirements.txt
RUN pip install --no-cache-dir -r /tmp/ia-requirements.txt

# ---------------- ML MODELS (cached layer — downloaded once) ----------------
RUN python -m spacy download fr_core_news_md