FROM apache/airflow:2.9.1-python3.11

USER root

# ---------------- INSTALL SYSTEM DEPENDENCIES ----------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-fra \
    poppler-utils \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

USER airflow

# ---------------- PYTHON DEPENDENCIES ----------------
COPY requirements.txt /opt/airflow/requirements.txt

RUN pip install --no-cache-dir -r /opt/airflow/requirements.txt