"""Seed 3 realistic supplier cases with documents covering all use cases.

Dossier 1: BTP — all 5 doc types, all valid (PDF + PNG + JPG)
Dossier 2: IT  — facture + RIB + KBIS, valid (PDF)
Dossier 3: Restauration — facture with amount errors + expired URSSAF (anomalies demo)

Run: docker exec -e API_URL=http://localhost:8000 docuscan-backend python /app/data/seed_demo.py
"""
import os
import time
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

API_URL = os.environ.get("API_URL", "http://localhost:8000")


# ======================================================================
# Rendering
# ======================================================================

def text_to_image(text):
    W, H = 1240, 1754
    img = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(img)
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        body_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    except OSError:
        title_font = ImageFont.load_default()
        body_font = title_font
    y = 80
    for i, line in enumerate(text.strip().split("\n")):
        if y > H - 60:
            break
        font = title_font if i == 0 else body_font
        draw.text((80, y), line, fill=(20, 20, 20), font=font)
        y += 38 if i == 0 else 26
        if not line.strip():
            y += 10
    return img


def to_pdf(img):
    buf = BytesIO()
    img.save(buf, "PDF", resolution=150.0)
    return buf.getvalue(), "application/pdf"


def to_png(img):
    buf = BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue(), "image/png"


def to_jpg(img):
    buf = BytesIO()
    img.save(buf, "JPEG", quality=92)
    return buf.getvalue(), "image/jpeg"


def send(text, filename, converter):
    img = text_to_image(text)
    data, content_type = converter(img)
    upload(data, filename, content_type)
    time.sleep(0.5)


def upload(data, filename, content_type):
    resp = requests.post(
        f"{API_URL}/api/upload",
        files={"files": (filename, BytesIO(data), content_type)},
        timeout=30,
    )
    resp.raise_for_status()
    info = resp.json().get("files", [{}])[0]
    doc_id = info.get("id", "?")
    print(f"    {filename:55s} [{content_type:16s}] -> {doc_id}")
    return doc_id


# ======================================================================
# DOSSIER 1 — Durand BTP (all doc types, all valid, 3 formats)
# SIRET valid Luhn: 44306184100025 -> check
# ======================================================================

D1 = {
    "name": "Durand Construction SARL",
    "siret": "44306184100025",
    "siren": "443061841",
    "vat": "FR40443061841",
    "iban": "FR76 3000 6000 0112 3456 7890 189",
    "bic": "BNPAFRPP",
    "address": "12 rue des Batisseurs, 75011 Paris",
    "naf": "4120A",
}

D1_FACTURE = lambda s: f"""FACTURE

Numero de facture : FACT-2026-0312
Date d'emission : 2026-03-01
Date d'echeance : 2026-04-01

FOURNISSEUR
{s['name']}
{s['address']}
SIRET : {s['siret']}
TVA intracommunautaire : {s['vat']}

CLIENT
Mairie de Bordeaux
Place Pey-Berland, 33000 Bordeaux
SIRET client : 21330063500017

LIGNES DE FACTURATION

Description                          Quantite    Prix unitaire    Montant
Renovation facade batiment A              1       12 500,00 EUR   12 500,00 EUR
Fourniture materiaux isolation            1        3 200,00 EUR    3 200,00 EUR
Main d'oeuvre qualifiee                  80h          55,00 EUR    4 400,00 EUR

Montant HT : 20 100,00 EUR
TVA (20,00%) : 4 020,00 EUR
TOTAL TTC : 24 120,00 EUR

IBAN : {s['iban']}
BIC : {s['bic']}
"""

D1_DEVIS = lambda s: f"""DEVIS

Numero de devis : DEV-2026-0089
Date d'emission : 2026-02-15
Date de validite : 2026-05-15

FOURNISSEUR
{s['name']}
{s['address']}
SIRET : {s['siret']}
TVA intracommunautaire : {s['vat']}

CLIENT
SCI Les Terrasses du Parc
78 avenue Foch, 75116 Paris

Prestations proposees

Description                              Quantite    Prix unitaire    Montant
Demolition cloisons existantes               1        2 800,00 EUR    2 800,00 EUR
Construction murs porteurs                   1        8 500,00 EUR    8 500,00 EUR
Plomberie complete salle de bain             1        4 200,00 EUR    4 200,00 EUR

Montant HT : 15 500,00 EUR
TVA (20,00%) : 3 100,00 EUR
Montant TTC : 18 600,00 EUR

Validite : 90 jours. Acompte de 30% a la commande.
"""

D1_RIB = lambda s: f"""RELEVE D'IDENTITE BANCAIRE

Titulaire du compte : {s['name']}
Adresse : {s['address']}

Banque : BNP Paribas
Code banque : 30006
Code guichet : 00001
Numero de compte : 12345678901
Cle RIB : 89

IBAN : {s['iban']}
BIC : {s['bic']}

SIRET : {s['siret']}
"""

D1_URSSAF = lambda s: f"""ATTESTATION DE VIGILANCE

Organisme : URSSAF Ile-de-France
Numero d'attestation : ATT-2026-DC-00142

Date d'emission : 2026-01-10
Date d'expiration : 2026-07-10

Entreprise : {s['name']}
SIRET : {s['siret']}
Code NAF : {s['naf']}
Adresse : {s['address']}

La presente attestation certifie que l'entreprise mentionnee ci-dessus
est a jour de ses obligations declaratives et de paiement.

Nombre de salaries declares : 23
Dernier bordereau recu : Decembre 2025

Fait a Paris, le 10 janvier 2026.
Le Directeur Regional
"""

D1_KBIS = lambda s: f"""EXTRAIT KBIS

Greffe : Greffe du Tribunal de Commerce de Paris
RCS : RCS Paris 443 061 841
Date d'immatriculation : 2015-03-22

Denomination : {s['name']}
Forme juridique : SARL
Capital social : 50 000 EUR
Adresse du siege : {s['address']}

SIRET : {s['siret']}
SIREN : {s['siren']}
Code NAF : {s['naf']}

Dirigeant : Jean-Pierre Durand

Activite : Travaux de construction et renovation.

Le present extrait a ete delivre le 5 mars 2026.
"""


# ======================================================================
# DOSSIER 2 — TechNova IT (facture + RIB + KBIS, PDF only)
# SIRET valid Luhn: 90255807400012
# ======================================================================

D2 = {
    "name": "TechNova Solutions SAS",
    "siret": "90255807400012",
    "siren": "902558074",
    "vat": "FR28902558074",
    "iban": "FR76 1820 6000 5531 2890 0128 072",
    "bic": "AGRIFRPP",
    "address": "8 avenue de l'Innovation, 69003 Lyon",
    "naf": "6201Z",
}

D2_FACTURE = lambda s: f"""FACTURE

Numero de facture : TN-2026-0455
Date d'emission : 2026-03-10
Date d'echeance : 2026-04-10

FOURNISSEUR
{s['name']}
{s['address']}
SIRET : {s['siret']}
TVA intracommunautaire : {s['vat']}

CLIENT
Groupe Casino
1 Esplanade de France, 42000 Saint-Etienne
SIRET client : 55450117600046

LIGNES DE FACTURATION

Description                                  Quantite    Prix unitaire    Montant
Developpement API microservices                 120h         95,00 EUR   11 400,00 EUR
Integration plateforme cloud AWS                 40h        110,00 EUR    4 400,00 EUR
Licence logicielle annuelle                       1       2 500,00 EUR    2 500,00 EUR

Montant HT : 18 300,00 EUR
TVA (20,00%) : 3 660,00 EUR
TOTAL TTC : 21 960,00 EUR

Paiement par virement sous 30 jours.
IBAN : {s['iban']}
BIC : {s['bic']}
"""

D2_RIB = lambda s: f"""RELEVE D'IDENTITE BANCAIRE

Titulaire du compte : {s['name']}
Adresse : {s['address']}

Banque : Credit Agricole
Code banque : 18206
Code guichet : 00055
Numero de compte : 31289001280
Cle RIB : 72

IBAN : {s['iban']}
BIC : {s['bic']}

SIRET : {s['siret']}
"""

D2_KBIS = lambda s: f"""EXTRAIT KBIS

Greffe : Greffe du Tribunal de Commerce de Lyon
RCS : RCS Lyon 902 558 074
Date d'immatriculation : 2020-09-01

Denomination : {s['name']}
Forme juridique : SAS
Capital social : 120 000 EUR
Adresse du siege : {s['address']}

SIRET : {s['siret']}
SIREN : {s['siren']}
Code NAF : {s['naf']}

Dirigeant : Sophie Martin

Activite : Conseil et developpement en systemes informatiques.

Le present extrait a ete delivre le 8 mars 2026.
"""


# ======================================================================
# DOSSIER 3 — Provence Traiteur (anomalies: montants incohérents + URSSAF expiré)
# SIRET valid Luhn: 53784217600019
# ======================================================================

D3 = {
    "name": "Les Jardins de Provence EURL",
    "siret": "53784217600019",
    "siren": "537842176",
    "vat": "FR81537842176",
    "iban": "FR76 4255 9000 4141 2000 5670 146",
    "bic": "CABORFRP",
    "address": "Route de Cavaillon, 84300 Les Taillades",
    "naf": "5610A",
}

# Anomalie: HT + TVA != TTC (erreur volontaire)
D3_FACTURE = lambda s: f"""FACTURE

Numero de facture : JP-2026-0078
Date d'emission : 2026-03-15
Date d'echeance : 2026-04-15

FOURNISSEUR
{s['name']}
{s['address']}
SIRET : {s['siret']}
TVA intracommunautaire : {s['vat']}

CLIENT
Hotel Le Meridien
Place de la Comedie, 34000 Montpellier

LIGNES DE FACTURATION

Description                              Quantite    Prix unitaire    Montant
Service traiteur reception 150 couverts      1        8 500,00 EUR    8 500,00 EUR
Location materiel et vaisselle               1        1 200,00 EUR    1 200,00 EUR
Personnel de service supplementaire         6h          45,00 EUR      270,00 EUR

Montant HT : 9 970,00 EUR
TVA (20,00%) : 1 994,00 EUR
TOTAL TTC : 12 500,00 EUR

Reglement par virement a reception.
"""

# Anomalie: URSSAF expiree (date dans le passe)
D3_URSSAF = lambda s: f"""ATTESTATION DE VIGILANCE

Organisme : URSSAF Provence-Alpes-Cote d'Azur
Numero d'attestation : ATT-2025-JP-00891

Date d'emission : 2025-03-01
Date d'expiration : 2025-09-01

Entreprise : {s['name']}
SIRET : {s['siret']}
Code NAF : {s['naf']}
Adresse : {s['address']}

La presente attestation certifie que l'entreprise mentionnee ci-dessus
est a jour de ses obligations declaratives et de paiement.

Nombre de salaries declares : 8

Fait a Marseille, le 1er mars 2025.
"""

D3_RIB = lambda s: f"""RELEVE D'IDENTITE BANCAIRE

Titulaire du compte : {s['name']}
Adresse : {s['address']}

Banque : Credit Agricole Provence
Code banque : 42559
Code guichet : 00041
Numero de compte : 41200056701
Cle RIB : 46

IBAN : {s['iban']}
BIC : {s['bic']}

SIRET : {s['siret']}
"""


# ======================================================================
# Main
# ======================================================================

def main():
    print("=" * 65)
    print("SEED DEMO — 3 dossiers fournisseurs")
    print("=" * 65)

    # --- Dossier 1: BTP — 5 docs, 3 formats ---
    print(f"\n  Dossier 1: {D1['name']}")
    print(f"  SIRET: {D1['siret']} | 5 documents | 3 formats")
    print()
    send(D1_FACTURE(D1), "Facture_Durand_FACT-2026-0312.pdf", to_pdf)
    send(D1_DEVIS(D1), "Devis_Durand_DEV-2026-0089.png", to_png)
    send(D1_RIB(D1), "RIB_Durand_BNP.jpg", to_jpg)
    send(D1_URSSAF(D1), "Attestation_URSSAF_Durand_2026.pdf", to_pdf)
    send(D1_KBIS(D1), "Kbis_Durand_Paris.pdf", to_pdf)

    time.sleep(1)

    # --- Dossier 2: IT — 3 docs, PDF ---
    print(f"\n  Dossier 2: {D2['name']}")
    print(f"  SIRET: {D2['siret']} | 3 documents | PDF")
    print()
    send(D2_FACTURE(D2), "Facture_TechNova_TN-2026-0455.pdf", to_pdf)
    send(D2_RIB(D2), "RIB_TechNova_CreditAgricole.pdf", to_pdf)
    send(D2_KBIS(D2), "Kbis_TechNova_Lyon.pdf", to_pdf)

    time.sleep(1)

    # --- Dossier 3: Restauration — anomalies ---
    print(f"\n  Dossier 3: {D3['name']}")
    print(f"  SIRET: {D3['siret']} | 3 documents | anomalies attendues")
    print()
    send(D3_FACTURE(D3), "Facture_JardinsProvence_JP-2026-0078.jpg", to_jpg)
    send(D3_URSSAF(D3), "Attestation_URSSAF_JardinsProvence_2025.png", to_png)
    send(D3_RIB(D3), "RIB_JardinsProvence_CA.pdf", to_pdf)

    print(f"\n{'=' * 65}")
    print(f"11 documents uploades pour 3 dossiers fournisseurs")
    print()
    print(f"  Dossier 1 (BTP)          : facture PDF + devis PNG + RIB JPG + URSSAF PDF + KBIS PDF")
    print(f"  Dossier 2 (IT)           : facture PDF + RIB PDF + KBIS PDF")
    print(f"  Dossier 3 (Restauration) : facture JPG (montants faux) + URSSAF PNG (expiree) + RIB PDF")
    print(f"\nCas d'usage couverts:")
    print(f"  - 5 types de documents (Facture, Devis, RIB, Attestation, KBIS)")
    print(f"  - 3 formats (PDF, PNG, JPG)")
    print(f"  - Dossier complet sans anomalie")
    print(f"  - Dossier partiel sans anomalie")
    print(f"  - Dossier avec anomalies (montants HT+TVA!=TTC, URSSAF expiree)")
    print(f"  - Auto-creation de dossier par SIRET")
    print(f"{'=' * 65}")


if __name__ == "__main__":
    main()
