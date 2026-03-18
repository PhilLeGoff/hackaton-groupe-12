# TODO — DocuScan AI

> Derniere mise a jour : 18/03/2026
> Equipe : 4 Fullstack (FS1-FS4) + 3 Data/IA (DI1-DI3)

## Etat actuel

**Ce qui marche** :

- Upload multi-docs → HDFS (Raw) → Airflow (8 tasks) → OCR Tesseract → NER (regex + spaCy + fuzzy) → Classification (TF-IDF+SVM / zero-shot / keywords) → Anomaly Detection (regles + Luhn + mod97 + TVA croisee + dates metier) → HDFS (Clean + Curated) → MongoDB → API REST → Frontend CRM + Conformite
- Auto-creation de case par SIRET dans Airflow
- Datasets synthetiques multi-format (PDF+PNG+JPG) avec bruit OCR, anomalies, 5 types de documents
- SIRET Luhn valides, IBAN mod97 valides
- Frontend : viewer PDF/image, boutons action (telecharger, valider, revoir), export JSON, edition inline
- Auto-remplissage conformite via endpoint `/api/cases/{id}/autofill`
- 16 endpoints backend (CRUD complet + download + autofill + metrics + pagination)
- Health-checks Docker (mongodb, hdfs-namenode, airflow-postgres)
- Tests IA (classification 5 tests + NER 16 tests + integration DI2)
- Modele SVM entraine (tfidf_svm.joblib, 611 KB) + metrics.json

**Ce qui manque (cahier des charges)** :

- **Verification inter-documents** : le cahier exige de comparer SIRET entre facture et attestation d'un meme dossier → `validate_cross_documents()` pas encore fait
- **Auto-remplissage CRM** : CaseDetailsPage utilise encore mockDocuments au lieu de l'API, pas d'appel autofill
- **Tests backend** : 3 fichiers pytest existent mais quasi-vides (2 fonctions placeholder)
- **4 boutons sans handler** : CRMPage ("+ Nouveau dossier", "Exporter"), CaseDetailsPage ("+ Ajouter un document", "Telecharger")
- **Demo live end-to-end** pas encore testee

---

## FS1 — Backend CRUD + Securite (DONE)

### P0 — Bloquant (DONE)

- [X] **POST `/api/cases`** — Creer un dossier (retourne camelCase conforme a CaseDetailResponse)
- [X] **PUT `/api/cases/{id}`** — Mettre a jour statut/infos
- [X] **POST `/api/compliances`** — Creer un controle de conformite
- [X] **PUT `/api/compliances/{id}`** — Mettre a jour decision
- [X] **PUT `/api/documents/{id}`** — Corriger/valider un document
- [X] **Validation ObjectId** sur tous les endpoints `/{id}` (InvalidId → 400)
- [X] **GET `/api/cases`** retourne `{"data": [...]}` conforme a CaseListResponse
- [X] **GET `/api/compliances`** retourne `{"data": [...]}` conforme a ComplianceListResponse
- [X] **Tous les `update_one`/`insert_one` motor sont `await`**

### P1 — Important (DONE)

- [X] **GET `/api/documents/{id}/download`** — Telecharger depuis HDFS
- [X] **Auto-creation de case** par SIRET dans Airflow
- [X] **Pagination** sur GET `/api/documents`
- [X] **Supprimer code mort** (models.py, formatters.py, extractorMetaData.py)

### P2 — Nice to have (DONE)

- [X] Variables d'environnement pour JWT_SECRET et credentials Airflow
- [X] Modeles Pydantic dans les reponses de route
- [X] Endpoint `/api/documents/{id}/metrics` OCR

### NOUVEAU — Endpoint auto-remplissage (DONE)

- [X] **GET `/api/cases/{id}/autofill`** — Agreger les donnees extraites de tous les docs du case
  - Fichier : `backend/routes/cases.py`
  - Query tous les documents avec `case_id` correspondant
  - Retourner un objet structure :
    ```
    {
      company_name, siret, vat, address,
      documents: [{type, date, amounts, status, anomalies}],
      compliance: {
        urssaf_valid: bool, urssaf_expiry: date,
        kbis_present: bool,
        rib_present: bool, iban: str,
        all_sirets_match: bool,
        anomalies: [...]
      }
    }
    ```
  - Utilise par FS2 (CRM) et FS3 (Conformite) pour pre-remplir les formulaires

---

## FS2 — Frontend CRM + Navigation + Style (QUASI DONE)

### P0 — Bloquant (DONE)

- [X] **Header branding** — Renommer "DocuFlow AI" → "DocuScan AI", logo "DF" → "DS"
- [X] **Fixer les 6 liens hardcodes** — Tous dynamiques maintenant
- [X] **Filtres CRM** — 4 boutons filtre (Tous/Conforme/A verifier/Non conforme) fonctionnels

### P0 — Auto-remplissage CRM (PARTIEL)

- [ ] **CaseDetailsPage** — Remplacer `mockDocuments` par appel API
  - Fichier : `CaseDetailsPage.jsx:185` — utilise encore `mockDocuments.map()`
- [ ] **Auto-remplissage formulaire CRM**
  - Fichier : `CaseDetailsPage.jsx`
  - Appeler `GET /api/cases/{id}/autofill`
  - Pre-remplir les champs : raison sociale, SIRET, TVA, adresse
  - Afficher la liste des documents rattaches avec statut et anomalies

### P1 — Important (DONE)

- [X] **Refonte DashboardPage** — Migre vers axios
- [X] **Refonte UploadPage** — Migre vers axios

### P1 — Important (RESTE)

- [ ] **Bouton "+ Nouveau dossier"** — Formulaire/modale
- [ ] **Stats dynamiques** — Brancher sur vraies donnees
- [ ] **Activite recente** — Brancher sur flux reel ou supprimer

### P2 — Nice to have

- [ ] Boutons "Exporter" et "Actualiser" CRM
- [ ] Pagination des listes
- [ ] Integrer `react-toastify`

---

## FS3 — Frontend Documents + Compliance (DONE)

> Branche : `FS3/frontend-documents-compliance-v2` — a merger dans main

### P0 — Bloquant (DONE)

- [X] **DocumentDetailsPage : anomalies et timeline depuis l'API**
- [X] **Migrer fetch() → axios** dans DashboardPage et UploadPage

### P0 — Auto-remplissage Conformite (DONE)

- [X] **Auto-remplissage formulaire Conformite**
  - Appelle `GET /api/cases/{id}/autofill` via `Promise.allSettled`
  - Pre-remplit : attestation URSSAF valide/expiree, KBIS present, RIB present, IBAN
  - Affiche les anomalies inter-documents
  - Indicateur visuel : vert (conforme) / rouge (anomalie) / orange (incomplet)

### P1 — Important (DONE)

- [X] **Viewer PDF/image** — iframe PDF + img pour images, fallback placeholder
- [X] **Bouton "Telecharger"** → GET `/api/documents/{id}/download`
- [X] **Bouton "Valider l'extraction"** → PUT `/api/documents/{id}` status "validated"
- [X] **Bouton "Marquer a revoir"** → PUT `/api/documents/{id}` status "to_review"
- [X] **Boutons compliance** (Approuver/Rejeter/Revoir) → PUT `/api/compliances/{id}`

### P2 — Nice to have (DONE)

- [X] Edition inline des extracted_fields
- [X] Export JSON des champs extraits
- [X] Export rapport compliance JSON
- [X] Route 404 fallback

---

## FS4 — Infrastructure + DevOps (QUASI DONE)

### P0 — Bloquant (DONE)

- [X] **Fixer URLs hardcodees** — DashboardPage et UploadPage migres vers axios
- [X] **Fixer `frontend/.env`** — `VITE_API_URL` configure

### P1 — Important (DONE)

- [X] **`.dockerignore`** pour backend et frontend
- [X] **Logs Airflow** — Monter en volume
- [X] **Tests backend** — fichiers pytest crees (test_cases, test_compliances, test_documents) ⚠️ quasi-vides (2 fonctions placeholder)
- [X] **Tesseract + pdftoppm** dans Dockerfile backend
- [X] **Health-checks Docker** — mongodb (mongosh ping), hdfs-namenode (curl), airflow-postgres (pg_isready)

### P2 — Nice to have

- [ ] CI pipeline GitHub Actions
- [ ] Etoffer les tests backend (actuellement 2 fonctions placeholder)

---

## DI1 — Datasets + Generateurs (DONE)

> Tout livre : multi-format (PDF+PNG+JPG), bruit OCR (noise.py), KBIS, anomalies sur tous les types, SIRET Luhn, IBAN mod97, layout/font variation, large dataset, NER annotations BIO.

### P0 (DONE)

- [X] Multi-format output (PDF+PNG+JPG+JPEG)
- [X] Generateur KBIS
- [X] SIRET valides (Luhn)
- [X] IBAN valides (mod97)

### P1 (DONE)

- [X] Anomalies pour devis, RIB, URSSAF
- [X] Bruit OCR (noise.py)
- [X] Dataset large (500+/type)

### P2 (DONE)

- [X] Variation layout + polices
- [X] NER annotations BIO/IOB

---

## DI2 — Modeles ML : Classification + NER (DONE)

> Classifier 3 methodes en cascade + NER spaCy + fuzzy + dates multiformats + champs KBIS.

### P0 (DONE)

- [X] Classification : TF-IDF+SVM / zero-shot XLM-RoBERTa / keywords
- [X] Tests classification TXT + PDF (5 types dont KBIS)
- [X] Dependances ML (transformers, torch, scikit-learn, spacy, rapidfuzz)

### P1 (DONE)

- [X] Script entrainement TF-IDF+SVM (`ia/classification/train.py`)
- [X] Benchmark matrice de confusion + F1 (`ia/classification/benchmark.py`)
- [X] NER spaCy fr_core_news_md (ORG, PER, LOC) + fusion regex
- [X] Fuzzy matching rapidfuzz (seuil 75%) pour typos OCR
- [X] Dates : DD/MM/YYYY, DD-MM-YYYY, "18 mars 2026" → YYYY-MM-DD
- [X] Champs KBIS (denomination, forme_juridique, rcs, greffe, dirigeant, siren)
- [X] Tests NER (`ia/nlp/tests/test_ner.py`)
- [X] Validation croisee TVA/SIRET dans detector.py
- [X] Validation dates metier (emission < echeance) dans detector.py
- [X] spaCy dans Dockerfile backend

### RESTE A FAIRE — Entrainement effectif

- [ ] **Entrainer le modele SVM en Docker** et sauvegarder metriques
  - `docker compose exec backend python ia/classification/train.py --data-dir data/generated --seed 42`
  - `docker compose exec backend python ia/classification/benchmark.py`
  - Avoir la matrice de confusion prete pour le pitch

### P2 — Nice to have

- [ ] Modele spaCy NER custom sur annotations BIO

---

## DI3 — Anomaly Detection + Verification inter-documents (PARTIEL)

> Objectif : completer les regles deterministes + verification coherence ENTRE documents d'un meme dossier.

> Etat actuel : `validate()` existe avec 10 checks (champs manquants, SIRET Luhn, IBAN mod97, TVA/SIREN coherence, dates format + logique, montants HT+TVA=TTC, doublons MongoDB). Pas de verification inter-documents, pas de tests, pas d'Isolation Forest.

### P0 — Bloquant

- [ ] **Verification inter-documents** (EXIGENCE CAHIER DES CHARGES)
  - Fichier : `ia/anomaly_detection/detector.py`
  - Nouvelle fonction : `validate_cross_documents(case_id, collection)`
  - Query MongoDB : tous les documents du meme `case_id`
  - Verifications :
    - **SIRET coherent** : le SIRET de la facture doit correspondre au SIRET de l'attestation URSSAF et du KBIS du meme dossier
    - **Attestation URSSAF non expiree** : date d'expiration > date de la facture
    - **KBIS non radie** : date d'immatriculation presente et pas de radiation
    - **RIB present** : si facture presente, un RIB doit exister dans le dossier
    - **TVA coherente** : le numero TVA de la facture correspond au SIREN du KBIS
  - Retourne : `{is_coherent: bool, cross_anomalies: [{documents, field, message, level}]}`
  - Appeler dans le DAG Airflow (task `validate_coherence`) apres la validation per-document
- [ ] **Tests anomaly detection** — Tester avec les 5 scenarios d'anomalies injectees
  - Creer `ia/anomaly_detection/tests/test_detector.py`
  - Tester validation per-document ET inter-documents
- [ ] **Tester pipeline complet en Docker**
  - Upload → Airflow → MongoDB → verifier que les vrais modules IA tournent

### P1 — Important

- [ ] **Isolation Forest** — Modele unsupervised pour detecter anomalies statistiques
  - Script `ia/anomaly_detection/train.py`
  - Features : total_ht, total_tva, total_ttc, ecart_dates, longueur_texte
  - Sauvegarder `ia/anomaly_detection/model/iforest.joblib`
- [ ] **Detection doublons** par numero facture/devis
- [ ] **Scoring d'anomalie** — `anomaly_score: float` dans le retour

### P2 — Nice to have

- [ ] Detection montants aberrants (hors norme statistique)
- [ ] Rapport de validation exportable
- [ ] Dashboard metriques IA

---

## DEPENDANCES ENTRE TACHES

```
DI1 (DONE) ──→ DI2 (DONE) ──→ DI3 (verification inter-docs)
                                  ↓
FS1 (DONE) ──→ FS1 autofill (DONE)
                    ↓
              FS2 auto-remplissage CRM (A FAIRE)
              FS3 auto-remplissage Conformite (DONE)
                    ↓
              DI3 fournit les anomalies inter-docs → FS3 les affiche

FS4 (DONE) ──→ FS3 migration fetch→axios (DONE)
```

## RESTE A FAIRE — PRIORITES

```
PRIORITE 1 — Exigences cahier des charges :
  DI3 : verification inter-documents (validate_cross_documents)
  DI3 : tests anomaly detection
  FS2 : CaseDetailsPage → API au lieu de mockDocuments
  FS2 : auto-remplissage CRM via autofill endpoint
  Merger branche FS3/frontend-documents-compliance-v2 dans main

PRIORITE 2 — Polish demo :
  FS2 : boutons sans handler ("+ Nouveau dossier", "Exporter", "+ Ajouter un document")
  FS2 : stats dynamiques HomePage
  DI3 : Isolation Forest, scoring anomalie
  FS4 : etoffer tests backend pytest
  Test end-to-end complet en Docker

PRIORITE 3 — Nice to have :
  FS4 : CI GitHub Actions
  DI2 : modele spaCy NER custom
  DI3 : detection doublons, montants aberrants
  FS2 : pagination, toastify
```
