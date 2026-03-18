# TODO — DocuScan AI

> Derniere mise a jour : 18/03/2026
> Equipe : 4 Fullstack (FS1-FS4) + 3 Data/IA (DI1-DI3)

## Etat actuel

**Ce qui marche** :
- Upload multi-docs → HDFS (Raw) → Airflow (8 tasks) → OCR Tesseract → NER (regex + spaCy + fuzzy) → Classification (TF-IDF+SVM / zero-shot / keywords) → Anomaly Detection (regles + Luhn + mod97 + TVA croisee + dates metier) → HDFS (Clean + Curated) → MongoDB → API REST → Frontend CRM + Conformite
- Auto-creation de case par SIRET dans Airflow
- Datasets synthetiques multi-format (PDF+PNG+JPG) avec bruit OCR, anomalies, 5 types de documents
- SIRET Luhn valides, IBAN mod97 valides

**Ce qui manque (cahier des charges)** :
- **Auto-remplissage formulaires** : le cahier exige que les formulaires CRM/Conformite soient pre-remplis par l'IA → pas encore fait
- **Verification inter-documents** : le cahier exige de comparer SIRET entre facture et attestation d'un meme dossier → pas encore fait
- Frontend : boutons sans handler, liens hardcodes, mock data, pas de viewer PDF
- Modele SVM pas encore entraine (script pret, donnees pretes, juste besoin de lancer)
- Demo live end-to-end pas encore testee

---

## FS1 — Backend CRUD + Securite (DONE)

### P0 — Bloquant (DONE)

- [x] **POST `/api/cases`** — Creer un dossier
- [x] **PUT `/api/cases/{id}`** — Mettre a jour statut/infos
- [x] **POST `/api/compliances`** — Creer un controle de conformite
- [x] **PUT `/api/compliances/{id}`** — Mettre a jour decision
- [x] **PUT `/api/documents/{id}`** — Corriger/valider un document
- [x] **Validation ObjectId** sur tous les endpoints `/{id}`

### P1 — Important (DONE)

- [x] **GET `/api/documents/{id}/download`** — Telecharger depuis HDFS
- [x] **Auto-creation de case** par SIRET dans Airflow
- [x] **Pagination** sur GET `/api/documents`
- [x] **Supprimer code mort** (models.py, formatters.py, extractorMetaData.py)

### P2 — Nice to have (DONE)

- [x] Variables d'environnement pour JWT_SECRET et credentials Airflow
- [x] Modeles Pydantic dans les reponses de route
- [x] Endpoint `/api/documents/{id}/metrics` OCR

### NOUVEAU — Endpoint auto-remplissage (cahier des charges)

- [x] **GET `/api/cases/{id}/autofill`** — Agreger les donnees extraites de tous les docs du case
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

## FS2 — Frontend CRM + Navigation + Style

### P0 — Bloquant

- [ ] **Header branding** — Renommer "DocuFlow AI" → "DocuScan AI", logo "DF" → "DS"
  - Fichier : `frontend/src/components/Header.jsx:16,19`
- [ ] **Fixer les 6 liens hardcodes** :
  - `Header.jsx:31` → `/crm/1` : lien vers `/crm`
  - `Header.jsx:34` → `/compliance/1` : lien vers page liste compliance
  - `HomePage.jsx:39,96` → `/compliance/1` : lien vers `/compliance`
  - `DocumentDetailsPage.jsx:171` → `/crm/1` : retour dynamique
  - `CompliancePage.jsx:241` → `/crm/1` : `/crm/${caseId}`
- [ ] **Filtres CRM** — Implementer les 4 boutons filtre (Tous/Conforme/A verifier/Non conforme)
  - Fichier : `CRMPage.jsx:153-164`
- [ ] **CaseDetailsPage** — Remplacer `mockDocuments` par appel API
  - Fichier : `CaseDetailsPage.jsx:185`

### P0 — Auto-remplissage CRM (cahier des charges)

- [ ] **Auto-remplissage formulaire CRM**
  - Fichier : `CaseDetailsPage.jsx`
  - Appeler `GET /api/cases/{id}/autofill` (necessite FS1)
  - Pre-remplir les champs : raison sociale, SIRET, TVA, adresse
  - Afficher la liste des documents rattaches avec statut et anomalies
  - Le formulaire doit se remplir automatiquement quand on ouvre un dossier

### P1 — Important

- [ ] **Refonte DashboardPage** — Theme light, composants partages, axios
- [ ] **Refonte UploadPage** — Harmoniser style, axios
- [ ] **Bouton "+ Nouveau dossier"** — Formulaire/modale
- [ ] **Stats dynamiques** — Brancher sur vraies donnees
- [ ] **Activite recente** — Brancher sur flux reel ou supprimer

### P2 — Nice to have

- [ ] Boutons "Exporter" et "Actualiser" CRM
- [ ] Pagination des listes
- [ ] Integrer `react-toastify`

---

## FS3 — Frontend Documents + Compliance

### P0 — Bloquant

- [ ] **DocumentDetailsPage : anomalies et timeline jamais mis a jour depuis l'API**
  - Fichier : `DocumentDetailsPage.jsx:75-76`
- [ ] **Migrer fetch() → axios** dans DashboardPage et UploadPage

### P0 — Auto-remplissage Conformite (cahier des charges)

- [ ] **Auto-remplissage formulaire Conformite**
  - Fichier : `CompliancePage.jsx`
  - Appeler `GET /api/cases/{id}/autofill` (necessite FS1)
  - Pre-remplir : attestation URSSAF valide/expiree, KBIS present, RIB present
  - Afficher les anomalies inter-documents detectees par DI3
  - Indicateur visuel : vert (conforme) / rouge (anomalie) / orange (incomplet)

### P1 — Important

- [ ] **Viewer PDF/image** — Remplacer placeholder par vrai viewer
- [ ] **Bouton "Telecharger"** → GET `/api/documents/{id}/download`
- [ ] **Bouton "Valider l'extraction"** → PUT `/api/documents/{id}`
- [ ] **Bouton "Marquer a revoir"** → PUT `/api/documents/{id}`
- [ ] **Boutons compliance** (Valider/Rejeter/Revoir) → PUT `/api/compliances/{id}`

### P2 — Nice to have

- [ ] Edition inline des extracted_fields
- [ ] Export JSON des champs extraits
- [ ] Export rapport compliance
- [ ] Route 404 fallback

---

## FS4 — Infrastructure + DevOps

### P0 — Bloquant

- [ ] **Fixer URLs hardcodees** — DashboardPage et UploadPage ignorent `.env`
- [ ] **Fixer `frontend/.env`** — `VITE_API_URL=http://127.0.0.1:8000` casse Docker

### P1 — Important

- [ ] **`.dockerignore`** pour backend et frontend
- [ ] **Logs Airflow** — Monter en volume
- [ ] **Tests backend** — pytest pour routes CRUD
- [x] **Tesseract + pdftoppm** dans Dockerfile backend (fait par DI2)

### P2 — Nice to have

- [ ] Health-checks Docker
- [ ] CI pipeline GitHub Actions

---

## DI1 — Datasets + Generateurs (DONE)

> Tout livre : multi-format (PDF+PNG+JPG), bruit OCR (noise.py), KBIS, anomalies sur tous les types, SIRET Luhn, IBAN mod97, layout/font variation, large dataset, NER annotations BIO.

### P0 (DONE)

- [x] Multi-format output (PDF+PNG+JPG+JPEG)
- [x] Generateur KBIS
- [x] SIRET valides (Luhn)
- [x] IBAN valides (mod97)

### P1 (DONE)

- [x] Anomalies pour devis, RIB, URSSAF
- [x] Bruit OCR (noise.py)
- [x] Dataset large (500+/type)

### P2 (DONE)

- [x] Variation layout + polices
- [x] NER annotations BIO/IOB

---

## DI2 — Modeles ML : Classification + NER (DONE)

> Classifier 3 methodes en cascade + NER spaCy + fuzzy + dates multiformats + champs KBIS.

### P0 (DONE)

- [x] Classification : TF-IDF+SVM / zero-shot XLM-RoBERTa / keywords
- [x] Tests classification TXT + PDF (5 types dont KBIS)
- [x] Dependances ML (transformers, torch, scikit-learn, spacy, rapidfuzz)

### P1 (DONE)

- [x] Script entrainement TF-IDF+SVM (`ia/classification/train.py`)
- [x] Benchmark matrice de confusion + F1 (`ia/classification/benchmark.py`)
- [x] NER spaCy fr_core_news_md (ORG, PER, LOC) + fusion regex
- [x] Fuzzy matching rapidfuzz (seuil 75%) pour typos OCR
- [x] Dates : DD/MM/YYYY, DD-MM-YYYY, "18 mars 2026" → YYYY-MM-DD
- [x] Champs KBIS (denomination, forme_juridique, rcs, greffe, dirigeant, siren)
- [x] Tests NER (`ia/nlp/tests/test_ner.py`)
- [x] Validation croisee TVA/SIRET dans detector.py
- [x] Validation dates metier (emission < echeance) dans detector.py
- [x] spaCy dans Dockerfile backend

### RESTE A FAIRE — Entrainement effectif

- [ ] **Entrainer le modele SVM en Docker** et sauvegarder metriques
  - `docker compose exec backend python ia/classification/train.py --data-dir data/generated --seed 42`
  - `docker compose exec backend python ia/classification/benchmark.py`
  - Avoir la matrice de confusion prete pour le pitch

### P2 — Nice to have

- [ ] Modele spaCy NER custom sur annotations BIO

---

## DI3 — Anomaly Detection + Verification inter-documents

> Objectif : completer les regles deterministes + verification coherence ENTRE documents d'un meme dossier.

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
FS1 (DONE) ──→ FS1 autofill endpoint
                    ↓
              FS2 auto-remplissage CRM
              FS3 auto-remplissage Conformite
                    ↓
              DI3 fournit les anomalies inter-docs → FS3 les affiche

FS4 (fix URLs) ──→ FS3 (migration fetch→axios)
```

## ORDRE SUGGERE (temps restant)

```
PRIORITE 1 — Exigences cahier des charges manquantes :
  DI3 : verification inter-documents (detector.py)
  FS1 : endpoint GET /api/cases/{id}/autofill
  FS2 : auto-remplissage formulaire CRM
  FS3 : auto-remplissage formulaire Conformite
  DI2 : entrainer SVM en Docker + benchmark

PRIORITE 2 — Demo live fonctionnelle :
  FS2 : header branding, liens hardcodes, filtres CRM
  FS3 : anomalies/timeline depuis API, fetch→axios
  FS4 : fix URLs frontend
  FS3 : viewer PDF, boutons action

PRIORITE 3 — Polish :
  FS2 : stats dynamiques, refonte Dashboard/Upload
  DI3 : Isolation Forest, scoring
  FS4 : tests, dockerignore, logs
```
