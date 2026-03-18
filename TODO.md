# TODO — DocuScan AI

> Derniere mise a jour : 18/03/2026
> Equipe : 4 Fullstack (FS1-FS4) + 3 Data/IA (DI1-DI3)

## Etat actuel

**Ce qui marche** : Upload → HDFS → Airflow (8 tasks) → OCR (Tesseract) → NER (regex) → Classification (keywords) → Anomaly Detection (regles) → MongoDB → API GET → Frontend.
Le pipeline est coherent de bout en bout.

**Ce qui manque** :
- Frontend : 18 boutons sans handler, 6 liens hardcodes, 2 pages fetch() hardcode, mock data, pas de viewer PDF
- Backend : pas de CRUD cases/compliances, pas de pagination, code mort, validation ObjectId partielle
- IA : aucun modele ML (tout est regex/regles), pas de bruit OCR, pas de robustesse
- Data : pas de generateur KBIS, anomalies uniquement sur factures, SIRET/IBAN sans checksum valide, pas de multi-format image (PNG/JPG/JPEG)

---

## FS1 — Backend CRUD + Securite

### P0 — Bloquant

- [ ] **POST `/api/cases`** — Creer un dossier (company_name, siret, contact, sector)
  - Fichier : `backend/routes/cases.py`
- [ ] **PUT `/api/cases/{id}`** — Mettre a jour statut/infos d'un dossier
  - Fichier : `backend/routes/cases.py`
- [ ] **POST `/api/compliances`** — Creer un controle de conformite lie a un case
  - Fichier : `backend/routes/compliances.py`
- [ ] **PUT `/api/compliances/{id}`** — Mettre a jour decision (valider/rejeter/revoir)
  - Fichier : `backend/routes/compliances.py`
- [ ] **PUT `/api/documents/{id}`** — Corriger/valider un document (status, extracted_fields)
  - Fichier : `backend/routes/documents.py`
- [ ] **Validation ObjectId** sur `cases/{id}` et `compliances/{id}`
  - Ajouter `try/except InvalidId` comme dans `documents.py`

### P1 — Important

- [ ] **GET `/api/documents/{id}/download`** — Telecharger le fichier original depuis HDFS `/raw/{id}/`
  - Utiliser `httpx` pour lire HDFS WebHDFS et retourner un `StreamingResponse`
- [ ] **Auto-creation de case** — Quand un document est traite, creer ou rattacher a un case par SIRET
  - Option A : dans `sync_mongodb` du DAG Airflow
  - Option B : endpoint backend appele apres le pipeline
- [ ] **Pagination** sur GET `/api/documents` — Ajouter `?limit=&offset=&status=&type=`
- [ ] **Supprimer code mort** : `backend/model/models.py` (typo "Documment"), `backend/utils/formatters.py`, `backend/utils/extractorMetaData.py`

### P2 — Nice to have

- [ ] Deplacer JWT_SECRET et credentials Airflow (`admin:admin`) en variables d'environnement
- [ ] Utiliser les modeles Pydantic dans les reponses de route (au lieu de dicts manuels)
- [ ] Endpoint `/api/documents/{id}/metrics` pour evaluer la qualite OCR (utiliser `services/ocr_metrics.py`)

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
  - Fichier : `CRMPage.jsx:153-164` — ajouter state `activeFilter`
- [ ] **CaseDetailsPage** — Remplacer `mockDocuments` par appel API
  - Fichier : `CaseDetailsPage.jsx:185`

### P1 — Important

- [ ] **Refonte DashboardPage** — Passer en theme light (slate), utiliser composants partages, remplacer `fetch()` par axios
  - Fichier : `DashboardPage.jsx` — actuellement `bg-gray-900` + `fetch("http://127.0.0.1:8000")`
- [ ] **Refonte UploadPage** — Harmoniser style, remplacer `fetch()` par axios
  - Fichier : `UploadPage.jsx:56` — `bg-blue-500` → `bg-slate-900`
- [ ] **Bouton "+ Nouveau dossier"** — Formulaire/modale pour creer un case
  - Necessite : FS1 POST `/api/cases`
- [ ] **Stats dynamiques** — Brancher "Apercu rapide" sur vraies donnees
  - `CRMPage.jsx:307,312` — stats hardcodees "78%", "20"
- [ ] **Activite recente** — Brancher sur flux reel ou supprimer bloc hardcode
  - `CRMPage.jsx:262-301`

### P2 — Nice to have

- [ ] Boutons "Exporter" et "Actualiser" CRM (`CRMPage.jsx:179,182`)
- [ ] Pagination des listes de dossiers et documents
- [ ] Integrer `react-toastify` (deja installe, jamais utilise)

---

## FS3 — Frontend Documents + Compliance

### P0 — Bloquant

- [ ] **DocumentDetailsPage : anomalies et timeline jamais mis a jour depuis l'API**
  - Fichier : `DocumentDetailsPage.jsx:75-76`
  - `const [anomalies] = useState(fallback)` → ajouter setter + update dans useEffect
- [ ] **Migrer fetch() → axios** dans DashboardPage et UploadPage
  - `DashboardPage.jsx:12` : `fetch("http://127.0.0.1:8000/api/documents")` → `getDocuments()`
  - `UploadPage.jsx:56` : `fetch(...)` → `api.post("/api/upload", ...)`

### P1 — Important

- [ ] **Viewer PDF/image** — Remplacer placeholder par vrai viewer
  - `DocumentDetailsPage.jsx:180-192`
  - Options : `react-pdf`, `<embed>`, `<iframe>` → GET `/api/documents/{id}/download`
- [ ] **Bouton "Telecharger"** → GET `/api/documents/{id}/download`
- [ ] **Bouton "Valider l'extraction"** → PUT `/api/documents/{id}` `{status: "Analyse terminee"}`
- [ ] **Bouton "Marquer a revoir"** → PUT `/api/documents/{id}` `{status: "A verifier"}`
- [ ] **Boutons compliance** (Valider/Rejeter/Revoir) → PUT `/api/compliances/{id}`
  - Necessite : FS1 PUT `/api/compliances/{id}`

### P2 — Nice to have

- [ ] Bouton "Corriger les champs" — edition inline des extracted_fields
- [ ] Bouton "Export JSON" — telecharger extracted_fields
- [ ] Bouton "Exporter rapport" compliance
- [ ] Route 404 fallback dans Router.jsx

---

## FS4 — Infrastructure + DevOps

### P0 — Bloquant

- [ ] **Fixer URLs hardcodees** — DashboardPage et UploadPage ignorent `.env`
  - Utiliser l'instance axios de `api/axios.js` (cf. taches FS3)
- [ ] **Fixer `frontend/.env`** — `VITE_API_URL=http://127.0.0.1:8000` casse Docker
  - Option A : supprimer `.env`, utiliser proxy Vite deja configure
  - Option B : override `VITE_API_URL` dans `docker-compose.yml`

### P1 — Important

- [ ] **`.dockerignore`** pour backend et frontend
- [ ] **Logs Airflow** — Monter en volume (`../airflow/logs:/opt/airflow/logs`)
- [ ] **Tests backend** — pytest pour routes CRUD (`backend/tests/`)
- [ ] **Tesseract + pdftoppm** dans Dockerfile backend (requis par OCR)

### P2 — Nice to have

- [ ] Health-checks Docker pour backend et frontend
- [ ] CI pipeline (lint + tests) — GitHub Actions
- [ ] Commande `start.sh build` / `health` / `shell <service>`

---

## DI1 — Datasets + Generateurs

> Objectif : enrichir les generateurs pour produire des datasets realistes multi-format avec bruit OCR.

### P0 — Bloquant

- [ ] **Multi-format output** — Chaque generateur doit produire PDF + PNG + JPG + JPEG en plus de TXT/JSON
  - Fichier : `data/generators/pdf_utils.py`
  - `write_text_pdf()` genere deja un PDF via Pillow → ajouter `.save()` en PNG, JPG, JPEG
  - Ajouter flag `--image-formats` (defaut: `pdf,png,jpg`) pour controler les formats
  - Les 4 generateurs appellent `write_text_pdf()` → modifier pour appeler une nouvelle fonction `write_all_formats()`
- [ ] **Generateur KBIS** — `data/generators/generate_kbis.py`
  - Champs : denomination, forme juridique, capital social, adresse siege, SIRET/SIREN, RCS, greffe, date immatriculation, dirigeant
  - Meme structure que les autres (dataclass, TXT+JSON+PDF+PNG+JPG+JPEG, `--count`, `--seed`, `--output-dir`)
- [ ] **Installer Faker** — Ajouter au `requirements.txt` generateurs (fait) + s'assurer qu'il est installe dans l'env de dev
- [ ] **SIRET valides** — Generer des SIRET avec checksum Luhn correct (au lieu de 14 digits aleatoires)
  - Fichiers : tous les generateurs
- [ ] **IBAN valides** — Generer des IBAN avec checksum mod97 correct
  - Fichier : `generate_ribs.py`

### P1 — Important

- [ ] **Anomalies pour devis** — Dates incoherentes, montants faux
  - Fichier : `generate_quotes.py` — ajouter `--anomaly-rate` comme factures
- [ ] **Anomalies pour RIB** — IBAN invalide, BIC incorrect
  - Fichier : `generate_ribs.py` — ajouter `--anomaly-rate`
- [ ] **Anomalies pour URSSAF** — SIRET invalide, date expiree
  - Fichier : `generate_urssaf_certificates.py` — ajouter `--anomaly-rate`
- [ ] **Bruit OCR sur images** — Pipeline de degradation pour simuler un scan reel
  - Creer `data/generators/noise.py` avec fonctions :
    - `add_gaussian_blur(image, sigma)` — flou gaussien
    - `add_salt_pepper(image, amount)` — bruit sel/poivre
    - `add_rotation(image, max_angle)` — legere rotation (±2-5 degres)
    - `add_skew(image, intensity)` — distorsion perspective
    - `add_jpeg_artifacts(image, quality)` — compression JPEG basse qualite
    - `add_background_noise(image)` — taches, lignes, fond gris
  - Appliquer aleatoirement sur les images PNG/JPG generees
  - Flag `--noise-level` (0=aucun, 1=leger, 2=moyen, 3=fort)
- [ ] **Dataset large** — Script pour generer 500+ docs par type avec `--count 500`
  - Objectif : entrainer les modeles ML (DI2, DI3)

### P2 — Nice to have

- [ ] Variation de layout (position des blocs, colonnes, marges aleatoires)
- [ ] Variation de polices (taille, famille, gras/italique)
- [ ] Fixer README generateurs — chemins `dataset/` → `data/generators/`
- [ ] Generer ground truth annotations pour entrainement NER (format IOB/BIO)

---

## DI2 — Modeles ML : Classification + NER

> Objectif : remplacer/completer le keyword scoring et les regex par des modeles pre-entraines.

### P0 — Bloquant

- [ ] **Modele de classification pre-entraine** — Remplacer le keyword scoring par un vrai classifieur
  - Fichier : `ia/classification/classifier.py`
  - **Approche recommandee** : CamemBERT (modele francais) ou DistilBERT multilingual
    - `pip install transformers torch` (ou `transformers[torch]`)
    - Utiliser `pipeline("zero-shot-classification")` pour demarrer sans fine-tuning
    - Labels candidats : `["Facture", "Devis", "RIB", "Attestation URSSAF", "KBIS"]`
  - **Alternative legere** : TF-IDF + SVM (scikit-learn)
    - `pip install scikit-learn`
    - Entrainer sur les datasets generes (DI1)
    - Plus rapide, moins de RAM, suffisant pour 5-6 classes
  - Garder le keyword scoring comme fallback si le modele echoue
  - Interface inchangee : `classify(text) → {document_type, confidence}`
- [ ] **Tests classification** — Tester sur chaque type de document genere
  - Matrice de confusion sur dataset de test (100+ docs par type)
  - Mesurer precision, recall, F1-score par classe
  - Creer `ia/classification/tests/test_classifier.py`
- [ ] **Ajouter dependances ML** dans les requirements
  - `backend/requirement.txt` : ajouter `transformers`, `torch` (ou `scikit-learn`)
  - `airflow/requirements.txt` : idem (les modules IA sont montes dans Airflow)

### P1 — Important

- [ ] **Fine-tuning classification** — Entrainer sur les datasets generes
  - Script `ia/classification/train.py`
  - Charger les JSON generes → extraire texte + label (nom du dossier parent)
  - Split train/val/test (70/15/15)
  - Sauvegarder modele dans `ia/classification/model/`
  - Evaluer et logger metriques
- [ ] **Ameliorer NER** — Completer les regex avec spaCy NER
  - `pip install spacy` + `python -m spacy download fr_core_news_md`
  - Utiliser spaCy pour extraire ORG, DATE, MONEY, LOC
  - Garder les regex pour les champs specifiques (SIRET, IBAN, TVA)
  - Fusionner resultats spaCy + regex
  - Fichier : `ia/nlp/ner.py`
- [ ] **Gerer formats de date supplementaires** — Actuellement seulement `YYYY-MM-DD`
  - Ajouter : `DD/MM/YYYY`, `DD-MM-YYYY`, `JJ mois AAAA` (ex: "18 mars 2026")
- [ ] **Robustesse OCR** — Gerer le bruit dans les regex NER
  - Utiliser `fuzzywuzzy` ou `rapidfuzz` pour match approximatif des labels
  - Tolerant aux typos OCR (ex: "Nurnero de facture" → "Numero de facture")

### P2 — Nice to have

- [ ] Entrainer un modele spaCy NER custom sur les documents generes (format IOB)
- [ ] Multi-label classification (un document peut etre plusieurs types)
- [ ] Extraction de champs KBIS dans NER (denomination, RCS, greffe, etc.)
- [ ] Benchmark NER : mesurer taux de champs trouves vs attendus par type

---

## DI3 — Modeles ML : Anomaly Detection + Pipeline

> Objectif : completer les regles deterministes par un modele ML de detection d'anomalies.

### P0 — Bloquant

- [ ] **Modele de detection d'anomalies** — Completer les regles par un modele unsupervised
  - Fichier : `ia/anomaly_detection/detector.py`
  - **Approche recommandee** : Isolation Forest (scikit-learn)
    - Features : total_ht, total_tva, total_ttc, nb_items, ecart_dates, longueur_texte
    - Entrainer sur les documents "normaux" generes (sans anomalies)
    - Score d'anomalie [-1, 1] en plus du booleen is_valid
    - `pip install scikit-learn joblib`
  - **Alternative** : Autoencoder simple (PyTorch/Keras)
    - Input = vecteur d'entites normalisees
    - Reconstruction error = score d'anomalie
  - Garder les regles deterministes (Luhn, mod97, montants) en complement
  - Interface enrichie : `validate() → {is_valid, anomalies, anomaly_score}`
- [ ] **Tests anomaly detection** — Tester avec les factures a anomalies injectees
  - Les 5 scenarios du generateur (SIRET incoherent, TVA fausse, date expiree, TTC faux, multi)
  - Verifier que `validate()` detecte chaque scenario
  - Mesurer precision/recall sur anomalies
  - Creer `ia/anomaly_detection/tests/test_detector.py`
- [ ] **Tester pipeline complet en Docker**
  - `./start.sh up` → upload document → verifier MongoDB → verifier Airflow UI
  - S'assurer que les vrais modules IA sont utilises (pas les fallbacks)

### P1 — Important

- [ ] **Script d'entrainement anomaly detection**
  - `ia/anomaly_detection/train.py`
  - Charger les JSON generes (normaux + anomalies)
  - Extraire features numeriques
  - Entrainer Isolation Forest
  - Sauvegarder modele (`ia/anomaly_detection/model/iforest.joblib`)
  - Evaluer sur jeu de test avec anomalies labelees
- [ ] **Validation croisee TVA** — Verifier TVA = "FR" + cle + SIREN (9 premiers chiffres du SIRET)
  - Fichier : `ia/anomaly_detection/detector.py`
- [ ] **Validation dates metier** — date emission < date echeance, dates pas dans le futur lointain
  - Fichier : `ia/anomaly_detection/detector.py:_check_dates()`
- [ ] **Detection doublons** — Ameliorer pour detecter aussi doublons par numero facture/devis
- [ ] **Scoring d'anomalie** — Severity score pour prioriser les alertes
  - Ajouter `anomaly_score: float` dans le retour de `validate()`
  - Frontend peut afficher un indicateur de risque

### P2 — Nice to have

- [ ] Detection montants aberrants (hors norme statistique vs docs precedents)
- [ ] Rapport de validation exportable en JSON/PDF
- [ ] Dashboard metriques IA (precision OCR, accuracy NER, F1 classification)
- [ ] Monitoring Prometheus/Grafana pour le pipeline

---

## DEPENDANCES ENTRE TACHES

```
DI1 (datasets multi-format + bruit) ──→ DI2 (entrainement classification)
                                    ──→ DI3 (entrainement anomaly detection)

DI2 (modele classification)         ──→ DI3 (validation pipeline complet)

FS1 (CRUD backend)                  ──→ FS2 (bouton nouveau dossier, lien case↔docs)
                                    ──→ FS3 (boutons valider/rejeter, download)

FS4 (fix URLs)                      ──→ FS3 (migration fetch→axios)

DI3 (test pipeline Docker)          ──→ Toute l'equipe (validation end-to-end)
```

## ORDRE SUGGERE

● Matin J1 — Tout le monde en parallèle :
  - FS1 : CRUD cases/compliances + validation ObjectId + supprimer code mort
  - FS2 : branding Header, fixer liens hardcodés, filtres CRM
  - FS3 : fix anomalies/timeline useState, migration fetch→axios, fix URLs
  - FS4 : .dockerignore, Tesseract dans Dockerfile, rebuild conteneurs
  - DI1 : multi-format output (PDF+PNG+JPG+JPEG), SIRET/IBAN valides, générateur KBIS
  - DI2 : intégrer modèle pré-entraîné (zero-shot ou TF-IDF+SVM) + tests
  - DI3 : tests anomaly detection + tester pipeline Docker

  Après-midi J1 — Features principales :
  - FS1 : endpoint download, auto-création case par SIRET
  - FS2 : refonte Dashboard/Upload (style + axios), CaseDetailsPage→API
  - FS3 : viewer PDF/image, boutons action (valider/rejeter/télécharger)
  - FS4 : tests pytest
  - DI1 : anomalies sur devis/RIB/URSSAF, pipeline bruit OCR, dataset large (500+/type)
  - DI2 : fine-tuning classification, améliorer NER (spaCy + fuzzy), formats dates
  - DI3 : Isolation Forest + script train, scoring d'anomalie

  Matin J2 — Finalisation + intégration :
  - FS1+FS2+FS3 : pagination, stats dynamiques, toastify, polish UX
  - FS4 : CI pipeline
  - DI1+DI2+DI3 : benchmark complet (matrice de confusion, F1), validation croisée TVA, test end-to-end Docker
