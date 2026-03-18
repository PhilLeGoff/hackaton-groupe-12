# TODO — DocuScan AI

> Derniere mise a jour : 18/03/2026
> Equipe : 4 Fullstack (FS1-FS4) + 3 Data/IA (DI1-DI3)

## Etat actuel

**Ce qui marche** :

- Upload multi-docs → HDFS (Raw) → Airflow (8 tasks) → OCR Tesseract → NER (regex + spaCy + fuzzy) → Classification (TF-IDF+SVM / zero-shot / keywords) → Anomaly Detection (regles + Luhn + mod97 + TVA croisee + dates metier) → HDFS (Clean + Curated) → MongoDB → API REST → Frontend CRM + Conformite
- Auto-creation de case par SIRET dans Airflow
- Datasets synthetiques multi-format (PDF+PNG+JPG) avec bruit OCR, anomalies, 5 types de documents
- SIRET Luhn valides, IBAN mod97 valides
- Frontend : menu responsive, viewer PDF/image, boutons action (telecharger, valider, revoir), export JSON, filtrage valeurs OCR invalides
- Auto-remplissage conformite via endpoint `/api/cases/{id}/autofill`
- 16+ endpoints backend (CRUD complet + download + autofill + metrics + pagination)
- Health-checks Docker (mongodb, hdfs-namenode, airflow-postgres)
- Tests IA (classification 5 tests + NER 16 tests)
- Modele SVM entraine (tfidf_svm.joblib)
- Correction OCR texte espace (PDF design type Canva)
- Plus aucune donnee mock — toutes les pages affichent des donnees reelles

**Ce qui manque (cahier des charges)** :

- **Verification inter-documents** : le cahier exige de comparer SIRET entre facture et attestation d'un meme dossier → `validate_cross_documents()` pas encore fait
- **Tests backend** : quasi-vides (2 fonctions placeholder)

---

## FS1 — Backend CRUD + Securite (DONE)

- [X] POST/PUT `/api/cases` — CRUD complet
- [X] POST/PUT `/api/compliances` — CRUD complet
- [X] PUT `/api/documents/{id}` — Corriger/valider
- [X] Validation ObjectId sur tous les endpoints
- [X] GET `/api/documents/{id}/download` — Telecharger depuis HDFS
- [X] Auto-creation de case par SIRET dans Airflow
- [X] Pagination sur GET `/api/documents`
- [X] Endpoint `/api/cases/{id}/autofill`
- [X] Endpoint `/api/documents/{id}/metrics`

---

## FS2 — Frontend CRM + Navigation + Style (DONE)

- [X] Header branding DocuScan AI + menu hamburger mobile
- [X] Liens dynamiques (plus de hardcode)
- [X] Filtres CRM (Tous/Conforme/A verifier/Non conforme)
- [X] CRMPage — creation de dossier + recherche + export
- [X] Suppression de toutes les donnees mock
- [X] Utils statusUtils.js (normalisation statuts)

---

## FS3 — Frontend Documents + Compliance (DONE)

- [X] DocumentDetailsPage — anomalies et timeline depuis l'API
- [X] Filtrage valeurs OCR invalides (garbage text)
- [X] Nettoyage messages anomalies (valeurs illisibles remplacees)
- [X] Viewer PDF/image + bouton Telecharger
- [X] Boutons Valider/Marquer a revoir
- [X] Auto-remplissage conformite via autofill
- [X] Edition inline des extracted_fields
- [X] Export JSON
- [X] Suppression Button.jsx (code mort)

---

## FS4 — Infrastructure + DevOps (DONE)

- [X] `.dockerignore` backend et frontend
- [X] Health-checks Docker
- [X] Tesseract + spaCy dans Dockerfile backend
- [X] Logs Airflow montes en volume
- [X] `.gitignore` pour fichiers de test locaux

### RESTE

- [ ] CI pipeline GitHub Actions
- [ ] Etoffer tests backend pytest

---

## DI1 — Datasets + Generateurs (DONE)

- [X] Multi-format output (PDF+PNG+JPG)
- [X] 5 types : factures, devis, KBIS, URSSAF, RIB
- [X] SIRET Luhn + IBAN mod97 valides
- [X] Bruit OCR (noise.py)
- [X] Dataset large (500+/type)
- [X] Variation layout + polices
- [X] NER annotations BIO/IOB

---

## DI2 — Modeles ML : Classification + NER (DONE)

- [X] Classification 3 methodes cascade : TF-IDF+SVM / zero-shot XLM-RoBERTa / keywords
- [X] NER regex + spaCy fr_core_news_md + rapidfuzz
- [X] Patterns flexibles (€, dates DD/MM/YY, factures sans deux-points, Sous total, A L'ATTENTION DE)
- [X] Correction conflits alias TVA
- [X] Filtre faux positifs spaCy (blacklist ORG + PER)
- [X] Tests classification + NER (21 tests)
- [X] Script entrainement + benchmark

---

## DI3 — Anomaly Detection (PARTIEL)

### DONE

- [X] `validate()` avec 10+ checks : champs manquants, SIRET Luhn, IBAN mod97, TVA/SIREN coherence, dates format + logique, montants HT+TVA=TTC

### RESTE A FAIRE

- [ ] **Verification inter-documents** (EXIGENCE CAHIER DES CHARGES)
  - `validate_cross_documents(case_id, collection)`
  - SIRET coherent entre facture/attestation/KBIS
  - Attestation URSSAF non expiree
  - KBIS non radie
  - RIB present si facture presente
  - TVA coherente SIREN/KBIS
- [ ] Tests anomaly detection
- [ ] Isolation Forest (unsupervised)
- [ ] Detection doublons par numero facture/devis

---

## RESTE A FAIRE — PRIORITES

```
PRIORITE 1 — Exigences cahier des charges :
  DI3 : verification inter-documents (validate_cross_documents)
  DI3 : tests anomaly detection

PRIORITE 2 — Polish demo :
  FS4 : etoffer tests backend pytest
  DI3 : Isolation Forest, scoring anomalie
  Test end-to-end complet en Docker

PRIORITE 3 — Nice to have :
  FS4 : CI GitHub Actions
  DI2 : modele spaCy NER custom
  DI3 : detection doublons, montants aberrants
  FS2 : pagination, toastify
```
