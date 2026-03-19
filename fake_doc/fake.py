from faker import Faker
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
import random
from datetime import datetime

fake = Faker("fr_FR")
styles = getSampleStyleSheet()


# =========================
#  UTILS
# =========================
def generate_bank_info(valid=True):
    iban = fake.iban()
    bic = fake.swift()

    if not valid:
        # Corruption IBAN / BIC
        if random.random() < 0.5:
            iban = iban[:-4] + "XXXX"
        if random.random() < 0.5:
            bic = "XXXXXXX"

    return iban, bic


# =========================
#  FACTURE NORMALE
# =========================
def generate_invoice(filename):
    doc = SimpleDocTemplate(filename, pagesize=A4)
    elements = []

    company = fake.company()
    client = fake.name()

    elements.append(Paragraph(f"<b>{company}</b>", styles["Title"]))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(f"Client : {client}", styles["Normal"]))
    elements.append(Spacer(1, 10))

    invoice_number = f"FAC-{random.randint(10000,99999)}"
    date = datetime.now().strftime("%d/%m/%Y")

    elements.append(Paragraph(f"Facture : {invoice_number}", styles["Normal"]))
    elements.append(Paragraph(f"Date : {date}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    data = [["Description", "Qté", "Prix", "Total"]]

    total_ht = 0
    for _ in range(3):
        qty = random.randint(1, 5)
        price = round(random.uniform(20, 100), 2)
        total = round(qty * price, 2)

        total_ht += total
        data.append([fake.word(), qty, price, total])

    tva = round(total_ht * 0.2, 2)
    total_ttc = total_ht + tva

    data.append(["", "", "HT", total_ht])
    data.append(["", "", "TVA", tva])
    data.append(["", "", "TTC", total_ttc])

    table = Table(data)
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)

    # RIB valide
    iban, bic = generate_bank_info(valid=True)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"IBAN: {iban}", styles["Normal"]))
    elements.append(Paragraph(f"BIC: {bic}", styles["Normal"]))

    doc.build(elements)


# =========================
#  FACTURE AVEC ANOMALIES
# =========================
def generate_invoice_with_anomalies(filename):
    doc = SimpleDocTemplate(filename, pagesize=A4)
    elements = []

    company = fake.company()
    client = fake.name()

    elements.append(Paragraph(f"<b>{company}</b>", styles["Title"]))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(f"Client : {client}", styles["Normal"]))
    elements.append(Spacer(1, 10))

    invoice_number = f"FAC-{random.randint(10000,99999)}"
    elements.append(Paragraph(f"Facture : {invoice_number}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    data = [["Description", "Qté", "Prix", "Total"]]

    total_ht = 0
    for _ in range(3):
        qty = random.randint(1, 5)
        price = round(random.uniform(20, 100), 2)

        # erreur volontaire
        total = round(qty * price + random.randint(-10, 10), 2)

        total_ht += total
        data.append([fake.word(), qty, price, total])

    # TVA incohérente
    tva = round(total_ht * random.uniform(0.1, 0.4), 2)

    # total faux
    total_ttc = total_ht + tva + random.randint(-20, 20)

    data.append(["", "", "HT", total_ht])
    data.append(["", "", "TVA", tva])
    data.append(["", "", "TTC", total_ttc])

    table = Table(data)
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.red)
    ]))

    elements.append(table)

    # RIB invalide
    iban, bic = generate_bank_info(valid=False)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"IBAN: {iban}", styles["Normal"]))
    elements.append(Paragraph(f"BIC: {bic}", styles["Normal"]))

    doc.build(elements)


# =========================
#  RIB NORMAL
# =========================
def generate_rib(filename):
    doc = SimpleDocTemplate(filename, pagesize=A4)
    elements = []

    name = fake.name()
    iban, bic = generate_bank_info(valid=True)

    elements.append(Paragraph("<b>RELEVÉ D'IDENTITÉ BANCAIRE</b>", styles["Title"]))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph(f"Titulaire : {name}", styles["Normal"]))
    elements.append(Paragraph(f"IBAN : {iban}", styles["Normal"]))
    elements.append(Paragraph(f"BIC : {bic}", styles["Normal"]))

    doc.build(elements)


# =========================
# RIB AVEC ANOMALIES
# =========================
def generate_rib_with_anomalies(filename):
    doc = SimpleDocTemplate(filename, pagesize=A4)
    elements = []

    name = fake.name()
    iban, bic = generate_bank_info(valid=False)

    elements.append(Paragraph("<b>RIB</b>", styles["Title"]))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph(f"Titulaire : {name}", styles["Normal"]))

    # 
    elements.append(Paragraph(f"IBAN : {iban}", styles["Normal"]))
    elements.append(Paragraph(f"BIC : {bic}", styles["Normal"]))

    doc.build(elements)


# =========================
# TEST
# =========================
if __name__ == "__main__":
    generate_invoice("./doc/facture_normale.pdf")
    generate_invoice_with_anomalies("./doc/facture_fraude.pdf")
    generate_rib("./doc/rib_normal.pdf")
    generate_rib_with_anomalies("./doc/rib_fraude.pdf")