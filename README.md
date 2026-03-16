# DocuScan AI — Plateforme Intelligente de Traitement Documentaire

Plateforme de traitement automatisé de documents administratifs (factures, devis, attestations SIRET, URSSAF, Kbis, RIB) combinant OCR, NLP et détection d'anomalies pour extraire, valider et distribuer les données vers des applications métiers.

---

## Stack Technique

| Couche | Technologie |
|---|---|
| **Front-end** | React (Vite) |
| **Back-end / API** | FastAPI (Python) |
| **Base de données** | MongoDB (base applicative : métadonnées, CRM, conformité) |
| **Data Lake** | Hadoop HDFS (3 zones : Raw / Clean / Curated) |
| **OCR** | Tesseract / EasyOCR |
| **Classification** | CNN / Random Forest (type de document) |
| **NLP / NER** | spaCy, Transformers (extraction d'entités) |
| **Anomaly Detection** | scikit-learn (incohérences inter-documents) |
| **Orchestration** | Apache Airflow |
| **Conteneurisation** | Docker / Docker Compose |
| **Génération de données** | Faker (Python) |

---

## Architecture

```
┌───────────────────────────────── Docker Compose ──────────────────────────────────┐
│                                                                                   │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐                           │
│  │  Front-end  │───▶│   FastAPI     │───▶│   MongoDB   │                           │
│  │   React     │◀───│   Backend     │◀───│  (base      │                           │
│  │             │    │              │    │  applicat.) │                           │
│  │  - Upload   │    │  - Reçoit    │    │             │                           │
│  │  - CRM      │    │    uploads   │    │ - Méta docs │                           │
│  │  - Conform. │    │  - Déclenche │    │ - CRM       │                           │
│  └─────────────┘    │    Airflow   │    │ - Conformité│                           │
│                     │  - Lit Mongo │    └──────┬──────┘                           │
│                     └──────────────┘           │ ▲                                │
│                                                │ │                                │
│                                         upload │ │ sync (étape 7)                 │
│                                                ▼ │                                │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                          Airflow DAGs                                       │   │
│  │                                                                             │   │
│  │  1. Ingestion ──▶ 2. OCR ──▶ 3. NER ──▶ 4. Classif. ──▶ 5. Validation     │   │
│  │  (MongoDB →       (Raw →     (Clean)    (Clean)         (détection          │   │
│  │   HDFS Raw)       Clean)                                 anomalies)         │   │
│  │                                                              │              │   │
│  │                                              6. Store Curated ◀─┘              │   │
│  │                                                     │                       │   │
│  │                                              7. Sync MongoDB               │   │
│  │                                                                             │   │
│  │                     ┌─────────────┐    ┌────────────────────────────────┐    │   │
│  │                     │  Couche IA  │    │         Hadoop HDFS            │    │   │
│  │                     │             │    │  Raw   │  Clean  │  Curated    │    │   │
│  │                     │ - OCR       │◀──▶│                               │    │   │
│  │                     │ - NER       │    └────────────────────────────────┘    │   │
│  │                     │ - Classif.  │                                         │   │
│  │                     │ - Anomaly   │                                         │   │
│  │                     └─────────────┘                                         │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                   │
└───────────────────────────────────────────────────────────────────────────────────┘

Flux upload   : Front-end → FastAPI → MongoDB (fichier + méta) → déclenche Airflow
Flux pipeline : Airflow : MongoDB → HDFS Raw → IA (OCR/NER/Classif/Anomaly) → HDFS Clean → HDFS Curated → sync MongoDB
Flux lecture  : Front-end → FastAPI → MongoDB (données structurées CRM, conformité)
```

### Stockage — HDFS + MongoDB

| Composant | Rôle |
|---|---|
| **HDFS — Raw** | Documents bruts (PDF, images) tels qu'uploadés |
| **HDFS — Clean** | Texte extrait par OCR (format texte brut / JSON) |
| **HDFS — Curated** | Données structurées, validées, prêtes à consommer |
| **MongoDB** | Base applicative — reçoit les uploads via FastAPI (fichier + métadonnées), puis enrichie par Airflow avec les résultats structurés (entités, classification, anomalies). Requêtée par les front-ends via FastAPI pour le CRM et la conformité |

---

## Fonctionnalités

- **Upload multi-documents** — PDF, images (JPEG, PNG), scans
- **Classification automatique** — Détection du type de document (facture, devis, attestation, Kbis, RIB)
- **OCR robuste** — Extraction de texte même sur documents bruités, flous, pivotés
- **Extraction d'entités (NER)** — SIRET, TVA, montants HT/TTC, dates d'émission/expiration
- **Détection d'incohérences inter-documents** :
  - SIRET différent entre facture et attestation
  - TVA incohérente
  - Attestation de vigilance expirée
  - Montants divergents entre devis et facture
- **Auto-remplissage** de 2 applications métiers :
  - **CRM** — Fiche fournisseur pré-remplie
  - **Outil de conformité** — Tableau de bord de validation réglementaire
- **Pipeline orchestré** via Airflow (ingestion → OCR → extraction → validation)
- **Stockage structuré** Data Lake HDFS 3 zones + MongoDB (base applicative)

---

## Structure du Projet

```
Hackathon/
├── frontend/                # Application React
│   ├── src/
│   │   ├── components/      # Composants réutilisables
│   │   ├── pages/           # Pages (Upload, CRM, Conformité, Dashboard)
│   │   ├── services/        # Appels API
│   │   └── App.jsx
│   └── package.json
│
├── backend/                 # API FastAPI
│   ├── app/
│   │   ├── routers/         # Routes API (upload, documents, crm, conformite)
│   │   ├── services/        # Logique métier (OCR, NLP, validation)
│   │   ├── models/          # Modèles Pydantic & schémas MongoDB
│   │   ├── database/        # Connexion MongoDB
│   │   └── main.py
│   └── requirements.txt
│
├── data/                    # Génération de datasets
│   ├── generators/          # Scripts Faker pour factures, devis, attestations
│   ├── templates/           # Templates de documents
│   └── samples/             # Échantillons générés
│
├── airflow/                 # DAGs Airflow
│   ├── dags/
│   │   └── document_pipeline.py
│   └── datalake/            # Interface HDFS (Raw/Clean/Curated)
│
├── ia/                      # Couche Intelligence Artificielle
│   ├── ocr/                 # Pipeline OCR (Tesseract / EasyOCR)
│   ├── classifier/          # Classification de documents (CNN / RF)
│   ├── ner/                 # Extraction d'entités (spaCy / Transformers)
│   ├── anomaly/             # Détection d'anomalies (scikit-learn)
│   └── training/            # Scripts d'entraînement et évaluation
│
├── docker/                  # Conteneurisation
│   ├── docker-compose.yml
│   ├── Dockerfile.frontend
│   ├── Dockerfile.backend
│   ├── Dockerfile.airflow
│   └── Dockerfile.hadoop
│
└── README.md
```

---

## Démarrage Rapide

### Prérequis

- Docker & Docker Compose
- Node.js 18+
- Python 3.11+

### Lancement avec Docker Compose

```bash
cd docker
docker-compose up --build
```

| Service | URL |
|---|---|
| Front-end React | http://localhost:5173 |
| API FastAPI | http://localhost:8000 |
| Swagger API docs | http://localhost:8000/docs |
| Airflow UI | http://localhost:8080 |
| MongoDB | localhost:27017 |
| HDFS NameNode UI | http://localhost:9870 |

### Lancement en développement (sans Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

---

## Génération du Dataset

```bash
cd data/generators
python generate_invoices.py      # Factures (légitimes + falsifiées)
python generate_quotes.py        # Devis
python generate_attestations.py  # Attestations SIRET / URSSAF
python generate_kbis.py          # Extraits Kbis
python generate_rib.py           # RIB
python add_noise.py              # Ajout de bruit (rotation, flou, pixelisation)
```

Les données SIREN/SIRET proviennent de l'API SIRENE de l'INSEE via [data.gouv.fr](https://www.data.gouv.fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret).

---

## Pipeline Airflow

```
ingest_from_mongo → store_raw_hdfs → run_ocr → store_clean_hdfs → extract_entities → classify_document → validate_coherence → store_curated_hdfs → sync_mongodb
```

- `ingest_from_mongo` : récupère le fichier uploadé depuis MongoDB et le dépose dans HDFS Raw
- `sync_mongodb` : pousse les données structurées (entités, classification, anomalies) dans MongoDB pour les front-ends

Le DAG `document_pipeline` s'exécute à chaque upload ou peut être déclenché manuellement depuis l'UI Airflow.

---

## API — Endpoints Principaux

| Méthode | Route | Description |
|---|---|---|
| `POST` | `/api/upload` | Upload document(s) → stockage MongoDB + déclenchement Airflow |
| `GET` | `/api/documents` | Liste des documents traités |
| `GET` | `/api/documents/{id}` | Détail d'un document + données extraites |
| `GET` | `/api/documents/{id}/anomalies` | Anomalies détectées |
| `GET` | `/api/crm/suppliers` | Données fournisseurs pour le CRM |
| `GET` | `/api/conformite/dashboard` | Tableau de bord conformité |
| `POST` | `/api/conformite/validate` | Lancer une validation inter-documents |

---

## Équipe — 7 membres

| Rôle | Périmètre |
|---|---|
| **Dev Fullstack 1** | Front-end React — pages Upload & Dashboard |
| **Dev Fullstack 2** | Front-end React — CRM & Outil de Conformité |
| **Dev Fullstack 3** | API FastAPI — routes, modèles, intégration MongoDB |
| **Dev Back-end** | API FastAPI — intégration MongoDB, endpoints Data Lake, auto-remplissage apps |
| **Data/IA 1** | Génération de datasets (Faker), OCR (Tesseract/EasyOCR), évaluation taux d'erreur |
| **Data/IA 2** | NER (spaCy/Transformers), classification de documents, détection d'anomalies |
| **Data/IA 3 — Chef de projet** | Orchestration Airflow, DAGs, monitoring, Docker, coordination & architecture |

---

## Scénarios de Test

| Scénario | Description |
|---|---|
| Facture légitime PDF | Extraction complète, aucune anomalie |
| Facture scan bruité | OCR sur image floue/pivotée, vérification robustesse |
| Incohérence SIRET | SIRET facture ≠ SIRET attestation → alerte |
| Attestation expirée | Date de validité dépassée → alerte conformité |
| TVA incohérente | Montant HT × taux ≠ TTC → alerte |
| Document falsifié | Détection de champs modifiés ou suspects |
| Multi-documents fournisseur | Validation croisée de l'ensemble du dossier |

---

## Licence

Projet académique — Hackathon 2026.
