#!/usr/bin/env python3
"""Generate synthetic French supplier invoices for the hackathon dataset."""

from __future__ import annotations

import argparse
import json
import random
import textwrap
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import List

try:
    from faker import Faker
except ImportError:  # pragma: no cover - optional dependency
    Faker = None


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT_DIR / "data" / "generated" / "factures"


TVA_RATES = [0.055, 0.1, 0.2]
PAYMENT_TERMS = [15, 30, 45, 60]
CURRENCIES = ["EUR"]
COMPANY_SUFFIXES = ["SARL", "SAS", "EURL", "SCI", "SA"]
ITEM_LABELS = [
    "Audit documentaire",
    "Traitement OCR",
    "Prestation de conseil IA",
    "Developpement API",
    "Abonnement plateforme",
    "Formation utilisateurs",
    "Maintenance corrective",
    "Integration CRM",
    "Controle de conformite",
    "Archivage numerique",
]
FIRST_NAMES = [
    "Camille",
    "Nora",
    "Sami",
    "Lea",
    "Yanis",
    "Sarah",
    "Mehdi",
    "Julie",
    "Ines",
    "Thomas",
]
LAST_NAMES = [
    "Martin",
    "Bernard",
    "Petit",
    "Robert",
    "Richard",
    "Durand",
    "Dubois",
    "Moreau",
    "Laurent",
    "Simon",
]
CITIES = [
    ("Paris", "75009"),
    ("Lyon", "69003"),
    ("Marseille", "13008"),
    ("Lille", "59800"),
    ("Bordeaux", "33000"),
    ("Nantes", "44000"),
    ("Toulouse", "31000"),
    ("Rennes", "35000"),
]
STREETS = [
    "12 rue de la Republique",
    "8 avenue Victor Hugo",
    "25 boulevard Voltaire",
    "3 rue des Lilas",
    "17 allee des Tilleuls",
    "42 quai de la Gare",
    "9 place du Marche",
    "66 rue Nationale",
]


@dataclass
class LineItem:
    description: str
    quantity: int
    unit_price_ht: float
    total_ht: float


@dataclass
class Invoice:
    invoice_number: str
    issue_date: str
    due_date: str
    supplier_name: str
    supplier_address: str
    supplier_siret: str
    supplier_vat: str
    customer_name: str
    customer_address: str
    customer_siret: str
    customer_vat: str
    payment_terms_days: int
    currency: str
    tva_rate: float
    total_ht: float
    total_tva: float
    total_ttc: float
    line_items: List[LineItem]
    scenario: str
    anomalies: List[str]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate synthetic French invoices for OCR and extraction tests."
    )
    parser.add_argument("-n", "--count", type=int, default=10, help="Number of invoices.")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for reproducible data.",
    )
    parser.add_argument(
        "--anomaly-rate",
        type=float,
        default=0.35,
        help="Share of invoices containing one or more anomalies.",
    )
    parser.add_argument(
        "--format",
        choices=["both", "json", "txt"],
        default="both",
        help="Output document format.",
    )
    return parser


def get_faker() -> Faker | None:
    if Faker is None:
        return None
    fake = Faker("fr_FR")
    return fake


def generate_siret(rng: random.Random) -> str:
    return "".join(str(rng.randint(0, 9)) for _ in range(14))


def generate_vat_from_siren(siret: str, rng: random.Random) -> str:
    key = rng.randint(10, 99)
    return f"FR{key}{siret[:9]}"


def random_address(fake: Faker | None, rng: random.Random) -> str:
    if fake is not None:
        return fake.address().replace("\n", ", ")
    city, postal_code = rng.choice(CITIES)
    return f"{rng.choice(STREETS)}, {postal_code} {city}"


def random_company(fake: Faker | None, rng: random.Random) -> str:
    if fake is not None:
        return fake.company()
    return f"{rng.choice(LAST_NAMES)} {rng.choice(COMPANY_SUFFIXES)}"


def random_contact_company(rng: random.Random) -> str:
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)} Consulting"


def build_line_items(rng: random.Random) -> List[LineItem]:
    line_items: List[LineItem] = []
    for _ in range(rng.randint(2, 5)):
        quantity = rng.randint(1, 8)
        unit_price = round(rng.uniform(90, 1600), 2)
        total_ht = round(quantity * unit_price, 2)
        line_items.append(
            LineItem(
                description=rng.choice(ITEM_LABELS),
                quantity=quantity,
                unit_price_ht=unit_price,
                total_ht=total_ht,
            )
        )
    return line_items


def choose_scenario(rng: random.Random, anomaly_rate: float) -> tuple[str, List[str]]:
    if rng.random() > anomaly_rate:
        return "legitime", []

    scenarios = [
        ("siret_incoherent", ["SIRET client incoherent"]),
        ("tva_incoherente", ["Montant TVA incoherent"]),
        ("date_echeance_depassee", ["Date d'echeance deja depassee"]),
        ("montant_ttc_incoherent", ["Montant TTC incoherent"]),
        ("multi_anomalies", ["SIRET client incoherent", "Montant TTC incoherent"]),
    ]
    return rng.choice(scenarios)


def build_invoice(index: int, fake: Faker | None, rng: random.Random, anomaly_rate: float) -> Invoice:
    supplier_name = random_company(fake, rng)
    customer_name = random_contact_company(rng)
    supplier_siret = generate_siret(rng)
    customer_siret = generate_siret(rng)
    supplier_vat = generate_vat_from_siren(supplier_siret, rng)
    customer_vat = generate_vat_from_siren(customer_siret, rng)
    issue_date = date.today() - timedelta(days=rng.randint(1, 120))
    payment_terms = rng.choice(PAYMENT_TERMS)
    due_date = issue_date + timedelta(days=payment_terms)
    currency = rng.choice(CURRENCIES)
    tva_rate = rng.choice(TVA_RATES)
    line_items = build_line_items(rng)
    total_ht = round(sum(item.total_ht for item in line_items), 2)
    total_tva = round(total_ht * tva_rate, 2)
    total_ttc = round(total_ht + total_tva, 2)

    scenario, anomalies = choose_scenario(rng, anomaly_rate)

    if scenario in {"siret_incoherent", "multi_anomalies"}:
        customer_siret = generate_siret(rng)
    if scenario == "tva_incoherente":
        total_tva = round(total_tva + rng.uniform(7.0, 150.0), 2)
    if scenario == "date_echeance_depassee":
        due_date = issue_date - timedelta(days=rng.randint(1, 20))
    if scenario in {"montant_ttc_incoherent", "multi_anomalies"}:
        total_ttc = round(total_ht + total_tva + rng.uniform(10.0, 250.0), 2)

    return Invoice(
        invoice_number=f"FAC-2026-{index:04d}",
        issue_date=issue_date.isoformat(),
        due_date=due_date.isoformat(),
        supplier_name=supplier_name,
        supplier_address=random_address(fake, rng),
        supplier_siret=supplier_siret,
        supplier_vat=supplier_vat,
        customer_name=customer_name,
        customer_address=random_address(fake, rng),
        customer_siret=customer_siret,
        customer_vat=customer_vat,
        payment_terms_days=payment_terms,
        currency=currency,
        tva_rate=tva_rate,
        total_ht=total_ht,
        total_tva=total_tva,
        total_ttc=total_ttc,
        line_items=line_items,
        scenario=scenario,
        anomalies=anomalies,
    )


def format_eur(value: float) -> str:
    return f"{value:,.2f} EUR".replace(",", " ").replace(".", ",")


def format_percent(value: float) -> str:
    return f"{value * 100:.1f}".replace(".", ",").rstrip("0").rstrip(",")


def invoice_to_text(invoice: Invoice) -> str:
    items_block = "\n".join(
        f"{idx}. {item.description} | Qt: {item.quantity} | PU HT: {format_eur(item.unit_price_ht)} | Total HT: {format_eur(item.total_ht)}"
        for idx, item in enumerate(invoice.line_items, start=1)
    )
    anomalies = ", ".join(invoice.anomalies) if invoice.anomalies else "Aucune"

    return textwrap.dedent(
        f"""\
        FACTURE FOURNISSEUR

        Numero de facture : {invoice.invoice_number}
        Date d'emission   : {invoice.issue_date}
        Date d'echeance   : {invoice.due_date}
        Conditions de paiement : {invoice.payment_terms_days} jours
        Devise            : {invoice.currency}

        FOURNISSEUR
        {invoice.supplier_name}
        {invoice.supplier_address}
        SIRET : {invoice.supplier_siret}
        TVA intracommunautaire : {invoice.supplier_vat}

        CLIENT
        {invoice.customer_name}
        {invoice.customer_address}
        SIRET : {invoice.customer_siret}
        TVA intracommunautaire : {invoice.customer_vat}

        LIGNES DE FACTURATION
        {items_block}

        TOTAL HT  : {format_eur(invoice.total_ht)}
        TVA ({format_percent(invoice.tva_rate)}%) : {format_eur(invoice.total_tva)}
        TOTAL TTC : {format_eur(invoice.total_ttc)}

        Mention : Paiement par virement bancaire sous {invoice.payment_terms_days} jours.
        Scenario dataset : {invoice.scenario}
        Anomalies attendues : {anomalies}
        """
    ).strip() + "\n"


def invoice_to_dict(invoice: Invoice) -> dict:
    payload = asdict(invoice)
    payload["line_items"] = [asdict(item) for item in invoice.line_items]
    return payload


def write_invoice(invoice: Invoice, output_dir: Path, output_format: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = invoice.invoice_number.lower()

    if output_format in {"both", "json"}:
        json_path = output_dir / f"{stem}.json"
        json_path.write_text(
            json.dumps(invoice_to_dict(invoice), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    if output_format in {"both", "txt"}:
        txt_path = output_dir / f"{stem}.txt"
        txt_path.write_text(invoice_to_text(invoice), encoding="utf-8")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    rng = random.Random(args.seed)
    fake = get_faker()
    if fake is not None and args.seed is not None:
        Faker.seed(args.seed)

    invoices: List[Invoice] = []
    for index in range(1, args.count + 1):
        invoice = build_invoice(index=index, fake=fake, rng=rng, anomaly_rate=args.anomaly_rate)
        write_invoice(invoice, args.output_dir, args.format)
        invoices.append(invoice)

    summary = {
        "count": len(invoices),
        "output_dir": str(args.output_dir),
        "format": args.format,
        "scenarios": {},
    }
    for invoice in invoices:
        summary["scenarios"].setdefault(invoice.scenario, 0)
        summary["scenarios"][invoice.scenario] += 1

    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
