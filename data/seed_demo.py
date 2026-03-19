"""Seed 3 realistic supplier cases with documents covering all use cases.

Dossier 1: BTP — 5 doc types, tout conforme (PDF + PNG + JPG)
Dossier 2: Restauration — anomalies per-document (montants faux + URSSAF expiree)
Dossier 3: Transport — anomalies inter-documents (SIRET different entre facture et KBIS)

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
# DOSSIER 1 — Durand BTP (tout conforme, 5 types, 3 formats)
# SIREN 443061841 Luhn OK | SIRET 44306184110004 Luhn OK | TVA key 64
# ======================================================================

D1 = {
    "name": "Durand Construction SARL",
    "siret": "44306184110004",
    "siren": "443061841",
    "vat": "FR64443061841",
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
# DOSSIER 2 — Jardins de Provence (anomalies per-document)
# SIREN 537842171 Luhn OK | SIRET 53784217110001 Luhn OK | TVA key 07
# Anomalies: montants HT+TVA!=TTC sur facture + URSSAF expiree
# ======================================================================

D2 = {
    "name": "Les Jardins de Provence EURL",
    "siret": "53784217110001",
    "siren": "537842171",
    "vat": "FR07537842171",
    "iban": "FR73 4255 9000 4141 2000 5670 146",
    "bic": "CABORFRP",
    "address": "Route de Cavaillon, 84300 Les Taillades",
    "naf": "5610A",
}

# Anomalie: HT + TVA != TTC (9970 + 1994 = 11964 != 12500)
D2_FACTURE = lambda s: f"""FACTURE

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

# Anomalie: URSSAF expiree (2025-09-01 < today)
D2_URSSAF = lambda s: f"""ATTESTATION DE VIGILANCE

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

D2_RIB = lambda s: f"""RELEVE D'IDENTITE BANCAIRE

Titulaire du compte : {s['name']}
Adresse : {s['address']}

Banque : Credit Agricole Provence
Code banque : 42559
Code guichet : 00041
Numero de compte : 41200056701
Cle RIB : 89

IBAN : {s['iban']}
BIC : {s['bic']}

SIRET : {s['siret']}
"""


# ======================================================================
# DOSSIER 3 — TransExpress (anomalies inter-documents)
# Facture + RIB utilisent SIRET A, KBIS utilise SIRET B (different!)
# => cross-doc: "SIRET different entre documents du meme dossier"
# Chaque document est individuellement valide
# SIREN A: 812345676 | SIRET A: 81234567610008 | TVA A: FR19812345676
# SIREN B: 812345684 | SIRET B: 81234568410002 | TVA B: FR43812345684
# ======================================================================

D3_MAIN = {
    "name": "TransExpress Logistique SAS",
    "siret": "81234567610008",
    "siren": "812345676",
    "vat": "FR19812345676",
    "iban": "FR73 2004 1000 0134 5678 9012 345",
    "bic": "PSSTFRPP",
    "address": "45 zone industrielle des Pins, 13400 Aubagne",
    "naf": "4941A",
}

# KBIS avec un SIRET different (ancien etablissement / erreur)
D3_KBIS_DATA = {
    "name": "TransExpress Logistique SAS",
    "siret": "81234568410002",
    "siren": "812345684",
    "vat": "FR43812345684",
    "address": "45 zone industrielle des Pins, 13400 Aubagne",
    "naf": "4941A",
}

D3_FACTURE = lambda s: f"""FACTURE

Numero de facture : TE-2026-0192
Date d'emission : 2026-03-12
Date d'echeance : 2026-04-12

FOURNISSEUR
{s['name']}
{s['address']}
SIRET : {s['siret']}
TVA intracommunautaire : {s['vat']}

CLIENT
Leroy Merlin SAS
Rue Chanzy, 59260 Lezennes
SIRET client : 38474058200018

LIGNES DE FACTURATION

Description                              Quantite    Prix unitaire    Montant
Transport palettes 20T Aubagne-Paris         3        1 850,00 EUR    5 550,00 EUR
Manutention et chargement                    3          320,00 EUR      960,00 EUR
Assurance marchandises                       1          180,00 EUR      180,00 EUR

Montant HT : 6 690,00 EUR
TVA (20,00%) : 1 338,00 EUR
TOTAL TTC : 8 028,00 EUR

Paiement par virement sous 30 jours.
IBAN : {s['iban']}
BIC : {s['bic']}
"""

D3_RIB = lambda s: f"""RELEVE D'IDENTITE BANCAIRE

Titulaire du compte : {s['name']}
Adresse : {s['address']}

Banque : La Banque Postale
Code banque : 20041
Code guichet : 00001
Numero de compte : 34567890123
Cle RIB : 88

IBAN : {s['iban']}
BIC : {s['bic']}

SIRET : {s['siret']}
"""

# KBIS avec SIRET DIFFERENT (812345684 au lieu de 812345676)
D3_KBIS = lambda s: f"""EXTRAIT KBIS

Greffe : Greffe du Tribunal de Commerce de Marseille
RCS : RCS Marseille 812 345 684
Date d'immatriculation : 2019-06-15

Denomination : {s['name']}
Forme juridique : SAS
Capital social : 200 000 EUR
Adresse du siege : {s['address']}

SIRET : {s['siret']}
SIREN : {s['siren']}
Code NAF : {s['naf']}

Dirigeant : Marc Lefebvre

Activite : Transport routier de marchandises.

Le present extrait a ete delivre le 2 mars 2026.
"""

D3_URSSAF = lambda s: f"""ATTESTATION DE VIGILANCE

Organisme : URSSAF Provence-Alpes-Cote d'Azur
Numero d'attestation : ATT-2026-TE-00467

Date d'emission : 2026-02-01
Date d'expiration : 2026-08-01

Entreprise : {s['name']}
SIRET : {s['siret']}
Code NAF : {s['naf']}
Adresse : {s['address']}

La presente attestation certifie que l'entreprise mentionnee ci-dessus
est a jour de ses obligations declaratives et de paiement.

Nombre de salaries declares : 35

Fait a Marseille, le 1er fevrier 2026.
"""


# ======================================================================
# Main
# ======================================================================

def main():
    print("=" * 65)
    print("SEED DEMO — 3 dossiers fournisseurs")
    print("=" * 65)

    # --- Dossier 1: BTP — tout conforme, 5 docs, 3 formats ---
    print(f"\n  Dossier 1: {D1['name']}")
    print(f"  SIRET: {D1['siret']} | 5 documents | tout conforme")
    print()
    send(D1_FACTURE(D1), "Facture_Durand_FACT-2026-0312.pdf", to_pdf)
    send(D1_DEVIS(D1), "Devis_Durand_DEV-2026-0089.png", to_png)
    send(D1_RIB(D1), "RIB_Durand_BNP.jpg", to_jpg)
    send(D1_URSSAF(D1), "Attestation_URSSAF_Durand_2026.pdf", to_pdf)
    send(D1_KBIS(D1), "Kbis_Durand_Paris.pdf", to_pdf)

    time.sleep(1)

    # --- Dossier 2: Restauration — anomalies per-document ---
    print(f"\n  Dossier 2: {D2['name']}")
    print(f"  SIRET: {D2['siret']} | 3 documents | anomalies per-document")
    print()
    send(D2_FACTURE(D2), "Facture_JardinsProvence_JP-2026-0078.jpg", to_jpg)
    send(D2_URSSAF(D2), "Attestation_URSSAF_JardinsProvence_2025.png", to_png)
    send(D2_RIB(D2), "RIB_JardinsProvence_CA.pdf", to_pdf)

    time.sleep(1)

    # --- Dossier 3: Transport — anomalies inter-documents ---
    print(f"\n  Dossier 3: {D3_MAIN['name']}")
    print(f"  SIRET facture/RIB: {D3_MAIN['siret']} | SIRET KBIS: {D3_KBIS_DATA['siret']}")
    print(f"  4 documents | anomalie inter-document (SIRET different)")
    print()
    send(D3_FACTURE(D3_MAIN), "Facture_TransExpress_TE-2026-0192.pdf", to_pdf)
    send(D3_RIB(D3_MAIN), "RIB_TransExpress_BanquePostale.pdf", to_pdf)
    send(D3_KBIS(D3_KBIS_DATA), "Kbis_TransExpress_Marseille.pdf", to_pdf)
    send(D3_URSSAF(D3_MAIN), "Attestation_URSSAF_TransExpress_2026.png", to_png)

    print(f"\n{'=' * 65}")
    print(f"12 documents uploades pour 3 dossiers fournisseurs")
    print()
    print(f"  Dossier 1 (BTP)          : 5 docs, tout conforme")
    print(f"  Dossier 2 (Restauration) : 3 docs, anomalies per-document")
    print(f"    - Facture: montants HT+TVA != TTC")
    print(f"    - URSSAF: attestation expiree (2025-09-01)")
    print(f"  Dossier 3 (Transport)    : 4 docs, anomalie inter-document")
    print(f"    - SIRET facture/RIB != SIRET KBIS")
    print(f"\nCas d'usage couverts:")
    print(f"  - 5 types de documents (Facture, Devis, RIB, Attestation, KBIS)")
    print(f"  - 3 formats (PDF, PNG, JPG)")
    print(f"  - Dossier complet conforme")
    print(f"  - Dossier avec anomalies per-document")
    print(f"  - Dossier avec anomalies inter-documents")
    print(f"  - Auto-creation de dossier par SIRET")
    print(f"{'=' * 65}")


if __name__ == "__main__":
    main()
