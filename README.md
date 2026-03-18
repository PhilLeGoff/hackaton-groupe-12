# DocuScan AI — Plateforme Intelligente de Traitement Documentaire

Plateforme de traitement automatisé de documents administratifs (factures, devis, attestations SIRET, URSSAF, Kbis, RIB) combinant OCR, NLP et détection d'anomalies pour extraire, valider et distribuer les données vers des applications métiers.

**Projet Hackathon 2026 — 7 membres**

---

## Stack Technique

| Couche | Technologie | État |
|---|---|---|
| **Front-end** | React 19, Vite 8, TailwindCSS 4 | Fonctionnel (7 pages) |
| **Back-end / API** | FastAPI (Python) | Fonctionnel (upload + lecture) |
| **Base de données** | MongoDB (motor async) | Fonctionnel |
| **Data Lake** | Hadoop HDFS (3 zones : Raw / Clean / Curated) | Fonctionnel |
| **OCR** | À implémenter (Tesseract / EasyOCR prévu) | Vide |
| **Classification** | À implémenter | Vide |
| **NLP / NER** | À implémenter | Vide |
| **Anomaly Detection** | À implémenter | Vide |
| **Orchestration** | Apache Airflow | Fonctionnel (DAG 8 tâches) |
| **Conteneurisation** | Docker / Docker Compose | Fonctionnel (8 services) |

---

## Architecture

```
                              ┌───────────────┐
                              │  Utilisateur   │
                              │  Upload PDF /  │
                              │  JPEG / PNG    │
                              └───────┬───────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Docker Compose                                     │
│                                                                                 │
│  ┌──────────────┐       ┌──────────────┐       ┌──────────────┐                │
│  │              │       │              │       │              │                │
│  │   React      │──────▶│   FastAPI     │──────▶│   MongoDB    │                │
│  │   Front-end  │◀──────│   Backend     │◀──────│              │                │
│  │   :5173      │       │   :8000      │       │  Hackathon   │                │
│  │              │       │              │       │  (database)  │                │
│  │  Upload      │       │  /api/upload │       │              │                │
│  │  Dashboard   │       │  /api/docs   │       │  documents   │                │
│  │  CRM         │       │  /api/cases  │       │  cases       │                │
│  │  Conformité  │       │  /api/compl. │       │  compliances │                │
│  │              │       │              │       │              │                │
│  └──────────────┘       └──────┬───────┘       └──────▲───────┘                │
│                                │                      │                         │
│                    ┌───────────┴───────────┐          │ sync                    │
│                    │                       │          │ (tâche 8)               │
│                    ▼                       ▼          │                         │
│  ┌─────────────────────┐    ┌──────────────────────────────────────────────┐   │
│  │                     │    │                                              │   │
│  │    Hadoop HDFS      │    │     Airflow DAG — document_pipeline          │   │
│  │    :9870 (WebHDFS)  │    │     :8080 (UI)                              │   │
│  │                     │    │                                              │   │
│  │  ┌───────────────┐  │◀──│──  1. start_processing                       │   │
│  │  │   Raw Zone    │──│──▶│──  2. run_ocr (⚠ placeholder)               │   │
│  │  │   /raw/{id}/  │  │   │                                              │   │
│  │  ├───────────────┤  │◀──│──  3. store_clean_hdfs                       │   │
│  │  │  Clean Zone   │  │   │  4. extract_entities  (⚠ placeholder)       │   │
│  │  │  /clean/{id}/ │  │   │  5. classify_document (⚠ placeholder)       │   │
│  │  ├───────────────┤  │   │  6. validate_coherence (⚠ placeholder)      │   │
│  │  │ Curated Zone  │  │◀──│──  7. store_curated_hdfs                     │   │
│  │  │ /curated/{id}/│  │   │  8. sync_mongodb ──────────────────────────│───┘
│  │  └───────────────┘  │   │                                              │
│  └─────────────────────┘   │  ┌────────────┐                              │
│                             │  │ ia/ (VIDE) │  Modules IA à implémenter   │
│                             │  │ ocr/       │  → fallback placeholders    │
│                             │  │ nlp/       │     actuellement utilisés   │
│                             │  │ classif/   │                              │
│                             │  │ anomaly/   │                              │
│                             │  └────────────┘                              │
│                             └──────────────────────────────────────────────┘
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Flux upload** : Front → FastAPI → métadonnées MongoDB + fichier HDFS Raw → trigger Airflow DAG
**Flux pipeline** : Airflow lit HDFS Raw → OCR → HDFS Clean → NER/Classif/Anomaly → HDFS Curated → sync MongoDB
**Flux lecture** : Front → FastAPI → MongoDB (données structurées)

### Stockage — HDFS + MongoDB

| Composant | Rôle |
|---|---|
| **HDFS — Raw** `/raw/{id}/` | Documents bruts (PDF, images) écrits par le backend via WebHDFS à l'upload |
| **HDFS — Clean** `/clean/{id}/` | Texte extrait par OCR (format texte brut) |
| **HDFS — Curated** `/curated/{id}/` | Données structurées enrichies (JSON) |
| **MongoDB** `Hackathon` | Base applicative — métadonnées documents, résultats IA (entités, classification, anomalies), cases, compliances |

---

## Structure du Projet

```
hackaton-groupe-12/
├── frontend/                  # Application React 19 + Vite 8 + TailwindCSS 4
│   ├── src/
│   │   ├── api/               # Appels API (axios, documents, cases, compliance)
│   │   ├── components/        # Layout, Header, Button, StatCard, SectionCard, StatusBadge
│   │   ├── pages/             # 7 pages (Home, CRM, CaseDetails, Document, Compliance, Upload, Dashboard)
│   │   ├── data/              # Données mock (fallback si API vide/erreur)
│   │   └── Router.jsx         # Configuration des routes
│   ├── .env                   # VITE_API_URL=http://127.0.0.1:8000
│   ├── vite.config.js         # Proxy /api, server config
│   └── package.json
│
├── backend/                   # API FastAPI (Python)
│   ├── main.py                # Entry point, CORS middleware
│   ├── params.py              # Variables d'environnement
│   ├── Dockerfile
│   ├── requirement.txt        # fastapi, motor, httpx, pypdf, python-docx, Pillow
│   ├── config/database.py     # Motor async client, collections
│   ├── model/                 # Pydantic models (document, case, compliance)
│   ├── routes/                # uploadsRoute, documents, cases, compliances
│   └── utils/                 # logger, extractorMetaData (inutilisé), formatters (inutilisé)
│
├── ia/                        # Couche IA — ⚠ VIDE (scaffolding .gitkeep uniquement)
│   ├── ocr/                   # Pipeline OCR à implémenter
│   ├── nlp/                   # Extraction d'entités NER à implémenter
│   ├── classification/        # Classification de documents à implémenter
│   └── anomaly_detection/     # Détection d'anomalies à implémenter
│
├── airflow/                   # Orchestration Apache Airflow
│   ├── dags/
│   │   └── document_pipeline.py   # DAG 8 tâches (import IA avec fallback placeholder)
│   ├── plugins/helpers/
│   │   ├── mongo.py           # Client pymongo sync
│   │   └── hdfs.py            # Client WebHDFS REST
│   └── requirements.txt       # pymongo, requests
│
├── data/                      # Datasets — ⚠ VIDE
│   ├── datasets/              # (vide)
│   └── templates/             # (vide)
│
├── docker/
│   └── docker-compose.yml     # 8 services (mongo, backend, frontend, hdfs×2, airflow×3)
│
├── start.sh                   # Script de gestion Docker (up, down, restart, logs, status, clean)
├── CLAUDE.md                  # Instructions pour Claude Code
└── README.md
```

---

## Démarrage Rapide

### Prérequis

- Docker & Docker Compose
- Node.js 18+ (pour le dev frontend hors Docker)
- Python 3.11+ (pour le dev backend hors Docker)

### Lancement avec Docker Compose

```bash
./start.sh up              # Build + start tous les services
./start.sh down            # Arrêter
./start.sh logs            # Suivre les logs
./start.sh logs backend    # Logs d'un service spécifique
./start.sh status          # État des conteneurs
./start.sh clean           # Stop + supprime les volumes
```

Ou manuellement :
```bash
cd docker && docker compose up --build
```

| Service | URL | Credentials |
|---|---|---|
| Front-end React | http://localhost:5173 | — |
| API FastAPI | http://localhost:8000 | — |
| Swagger API docs | http://localhost:8000/docs | — |
| Airflow UI | http://localhost:8080 | admin / admin |
| MongoDB | localhost:27017 | pas d'auth |
| HDFS NameNode UI | http://localhost:9870 | — |

### Lancement en développement (sans Docker)

```bash
# Backend
cd backend
pip install -r requirement.txt
uvicorn main:app --reload     # http://localhost:8000

# Frontend
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

> **Note** : MongoDB, HDFS et Airflow doivent tourner (via Docker ou en local) pour que le backend fonctionne complètement.

---

## API — Endpoints

| Méthode | Route | Description | État |
|---|---|---|---|
| `GET` | `/` | Health check | OK |
| `POST` | `/api/upload` | Upload fichier(s) → MongoDB + HDFS + trigger Airflow | OK |
| `GET` | `/api/documents` | Liste des documents | OK |
| `GET` | `/api/documents/{id}` | Détail document (OCR, entités, classification, validation) | OK |
| `GET` | `/api/cases` | Liste des dossiers | OK (vide — pas de logique de création) |
| `GET` | `/api/cases/{id}` | Détail dossier | OK |
| `GET` | `/api/compliances` | Liste conformités | OK (vide — pas de logique de création) |
| `GET` | `/api/compliances/{id}` | Détail conformité | OK |

**Manquant** : POST/PUT/DELETE pour cases et compliances, création automatique de dossiers après traitement IA.

---

## Pipeline Airflow

DAG `document_pipeline` — 8 tâches séquentielles, déclenché par le backend à chaque upload :

```
start_processing → run_ocr → store_clean_hdfs → extract_entities → classify_document → validate_coherence → store_curated_hdfs → sync_mongodb
```

| Tâche | Description | État |
|---|---|---|
| `start_processing` | Status MongoDB → "processing" | OK |
| `run_ocr` | Lit fichier HDFS Raw, appelle `ia.ocr.pipeline.extract_text()` | Placeholder |
| `store_clean_hdfs` | Écrit le texte OCR dans HDFS Clean | OK |
| `extract_entities` | Appelle `ia.nlp.ner.extract()` | Placeholder |
| `classify_document` | Appelle `ia.classification.classifier.classify()` | Placeholder |
| `validate_coherence` | Appelle `ia.anomaly_detection.detector.validate()` | Placeholder |
| `store_curated_hdfs` | Écrit le JSON enrichi dans HDFS Curated | OK |
| `sync_mongodb` | Met à jour le document MongoDB avec tous les résultats | OK |

### Interfaces attendues des modules IA

```python
# ia/ocr/pipeline.py
def extract_text(raw_content: bytes, content_type: str) -> str

# ia/nlp/ner.py
def extract(ocr_text: str) -> dict
# Retour : {siret, vat, amount_ht, amount_ttc, issue_date, expiration_date, company_name, iban}

# ia/classification/classifier.py
def classify(ocr_text: str) -> dict
# Retour : {document_type: str, confidence: float}

# ia/anomaly_detection/detector.py
def validate(entities: dict, classification: dict, document_id: str, collection=None) -> dict
# Retour : {is_valid: bool, anomalies: list[str]}
```

---

## Équipe — 7 membres

| Rôle | Périmètre |
|---|---|
| **Dev Fullstack 1** | Front-end React — pages Upload & Dashboard |
| **Dev Fullstack 2** | Front-end React — CRM & Outil de Conformité |
| **Dev Fullstack 3** | API FastAPI — routes, modèles, intégration MongoDB |
| **Dev Back-end** | API FastAPI — intégration MongoDB, endpoints Data Lake, auto-remplissage apps |
| **Data/IA 1** | Génération de datasets, OCR (Tesseract/EasyOCR) |
| **Data/IA 2** | NER, classification de documents, détection d'anomalies |
| **Data/IA 3 — Chef de projet** | Orchestration Airflow, DAGs, monitoring, Docker, coordination |

---

## Scénarios de Test

| Scénario | Description |
|---|---|
| Facture légitime PDF | Extraction complète, aucune anomalie |
| Facture scan bruité | OCR sur image floue/pivotée, vérification robustesse |
| Incohérence SIRET | SIRET facture ≠ SIRET attestation → alerte |
| Attestation expirée | Date de validité dépassée → alerte conformité |
| TVA incohérente | Montant HT × taux ≠ TTC → alerte |
| Multi-documents fournisseur | Validation croisée de l'ensemble du dossier |

> **Note** : Ces scénarios nécessitent l'implémentation des modules IA et la création de datasets de test.

---

## Licence

Projet académique — Hackathon 2026.
