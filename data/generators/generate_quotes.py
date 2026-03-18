#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import random
import textwrap
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import List

from pdf_utils import write_text_pdf

try:
    from faker import Faker
except ImportError:
    Faker = None


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = ROOT_DIR / "data" / "generated" / "pdfs" / "devis"
TVA_RATES = [0.055, 0.1, 0.2]
COMPANY_SUFFIXES = ["SARL", "SAS", "EURL", "SCI", "SA"]
ITEM_LABELS = [
    "Audit documentaire",
    "Traitement OCR",
    "Prestation de conseil IA",
    "Developpement API",
    "Abonnement plateforme",
    "Formation utilisateurs",
    "Maintenance corrective",
]
FIRST_NAMES = ["Camille", "Nora", "Sami", "Lea", "Yanis", "Sarah", "Julie", "Ines"]
LAST_NAMES = ["Martin", "Bernard", "Robert", "Durand", "Dubois", "Moreau", "Simon"]
CITIES = [
    ("Paris", "75009"),
    ("Lyon", "69003"),
    ("Lille", "59800"),
    ("Bordeaux", "33000"),
    ("Nantes", "44000"),
    ("Toulouse", "31000"),
]
STREETS = [
    "12 rue de la Republique",
    "8 avenue Victor Hugo",
    "25 boulevard Voltaire",
    "17 allee des Tilleuls",
    "42 quai de la Gare",
    "9 place du Marche",
]


@dataclass
class LineItem:
    description: str
    quantity: int
    unit_price_ht: float
    total_ht: float


@dataclass
class Quote:
    quote_number: str
    issue_date: str
    valid_until: str
    provider_name: str
    provider_address: str
    client_name: str
    client_address: str
    tva_rate: float
    total_ht: float
    total_tva: float
    total_ttc: float
    line_items: List[LineItem]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate synthetic French quotes for OCR and extraction tests."
    )
    parser.add_argument("-n", "--count", type=int, default=10, help="Number of quotes.")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory.",
    )
    parser.add_argument("--seed", type=int, default=None, help="Optional random seed.")
    parser.add_argument(
        "--format",
        choices=["both", "json", "txt"],
        default="both",
        help="Structured output format. A PDF is always generated too.",
    )
    return parser


def get_faker() -> Faker | None:
    if Faker is None:
        return None
    return Faker("fr_FR")


def random_address(fake: Faker | None, rng: random.Random) -> str:
    if fake is not None:
        return fake.address().replace("\n", ", ")
    city, postal_code = rng.choice(CITIES)
    return f"{rng.choice(STREETS)}, {postal_code} {city}"


def random_company(fake: Faker | None, rng: random.Random) -> str:
    if fake is not None:
        return fake.company()
    return f"{rng.choice(LAST_NAMES)} {rng.choice(COMPANY_SUFFIXES)}"


def random_client(rng: random.Random) -> str:
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)} Consulting"


def build_line_items(rng: random.Random) -> List[LineItem]:
    items: List[LineItem] = []
    for _ in range(rng.randint(2, 4)):
        quantity = rng.randint(1, 8)
        unit_price = round(rng.uniform(120, 1600), 2)
        total_ht = round(quantity * unit_price, 2)
        items.append(
            LineItem(
                description=rng.choice(ITEM_LABELS),
                quantity=quantity,
                unit_price_ht=unit_price,
                total_ht=total_ht,
            )
        )
    return items


def build_quote(index: int, fake: Faker | None, rng: random.Random) -> Quote:
    issue_date = date.today() - timedelta(days=rng.randint(1, 90))
    valid_until = issue_date + timedelta(days=rng.randint(10, 45))
    tva_rate = rng.choice(TVA_RATES)
    line_items = build_line_items(rng)
    total_ht = round(sum(item.total_ht for item in line_items), 2)
    total_tva = round(total_ht * tva_rate, 2)
    total_ttc = round(total_ht + total_tva, 2)

    return Quote(
        quote_number=f"DEV-2026-{index:04d}",
        issue_date=issue_date.isoformat(),
        valid_until=valid_until.isoformat(),
        provider_name=random_company(fake, rng),
        provider_address=random_address(fake, rng),
        client_name=random_client(rng),
        client_address=random_address(fake, rng),
        tva_rate=tva_rate,
        total_ht=total_ht,
        total_tva=total_tva,
        total_ttc=total_ttc,
        line_items=line_items,
    )


def format_eur(value: float) -> str:
    return f"{value:,.2f} EUR".replace(",", " ").replace(".", ",")


def format_percent(value: float) -> str:
    return f"{value * 100:.1f}".replace(".", ",").rstrip("0").rstrip(",")


def quote_to_text(quote: Quote) -> str:
    items_block = "\n".join(
        f"- {item.description} | Qt: {item.quantity} | PU HT: {format_eur(item.unit_price_ht)} | Total HT: {format_eur(item.total_ht)}"
        for item in quote.line_items
    )
    return textwrap.dedent(
        f"""\
        DEVIS

        Numero de devis : {quote.quote_number}
        Date d'emission : {quote.issue_date}
        Date de validite : {quote.valid_until}
        Prestataire : {quote.provider_name}
        Adresse prestataire : {quote.provider_address}
        Client : {quote.client_name}
        Adresse client : {quote.client_address}

        Prestations proposees :
        {items_block}

        Montant HT : {format_eur(quote.total_ht)}
        TVA ({format_percent(quote.tva_rate)}%) : {format_eur(quote.total_tva)}
        Montant TTC : {format_eur(quote.total_ttc)}
        Devis valable sous reserve d'acceptation.
        """
    ).strip() + "\n"


def quote_to_dict(quote: Quote) -> dict:
    return {
        "quote_number": quote.quote_number,
        "issue_date": quote.issue_date,
        "valid_until": quote.valid_until,
        "total_ht": quote.total_ht,
        "total_ttc": quote.total_ttc,
    }


def write_quote(quote: Quote, output_dir: Path, output_format: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = quote.quote_number.lower()

    if output_format in {"both", "json"}:
        (output_dir / f"{stem}.json").write_text(
            json.dumps(quote_to_dict(quote), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    if output_format in {"both", "txt"}:
        txt_content = quote_to_text(quote)
        (output_dir / f"{stem}.txt").write_text(txt_content, encoding="utf-8")
    else:
        txt_content = quote_to_text(quote)

    write_text_pdf(output_dir / f"{stem}.pdf", txt_content)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    rng = random.Random(args.seed)
    fake = get_faker()
    if fake is not None and args.seed is not None:
        Faker.seed(args.seed)

    quotes: List[Quote] = []
    for index in range(1, args.count + 1):
        quote = build_quote(index=index, fake=fake, rng=rng)
        write_quote(quote, args.output_dir, args.format)
        quotes.append(quote)

    summary = {
        "count": len(quotes),
        "output_dir": str(args.output_dir),
        "format": args.format,
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
