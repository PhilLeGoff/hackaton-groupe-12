#!/usr/bin/env python3
"""Generate synthetic French bank account details for OCR and extraction tests."""

from __future__ import annotations

import argparse
import json
import random
import textwrap
from dataclasses import dataclass
from pathlib import Path

from pdf_utils import write_text_pdf

try:
    from faker import Faker
except ImportError:  # pragma: no cover - optional dependency
    Faker = None


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT_DIR / "data" / "generated" / "pdfs" / "ribs"
BANKS = ["Societe Generale", "BNP Paribas", "Credit Agricole", "La Banque Postale"]
COMPANY_SUFFIXES = ["SARL", "SAS", "EURL", "SCI", "SA"]
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
class Rib:
    account_holder: str
    bank_name: str
    bank_address: str
    iban: str
    bic: str
    bank_code: str
    branch_code: str
    account_number: str
    rib_key: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate synthetic RIB documents for OCR and extraction tests."
    )
    parser.add_argument("-n", "--count", type=int, default=10, help="Number of RIBs.")
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


def generate_digits(rng: random.Random, length: int) -> str:
    return "".join(str(rng.randint(0, 9)) for _ in range(length))


def generate_iban(rng: random.Random) -> str:
    groups = [
        f"FR{rng.randint(10, 99)}",
        generate_digits(rng, 4),
        generate_digits(rng, 4),
        generate_digits(rng, 4),
        generate_digits(rng, 4),
        generate_digits(rng, 3),
    ]
    return " ".join(groups)


def generate_bic(rng: random.Random) -> str:
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return "".join(rng.choice(letters) for _ in range(8)) + "XXX"


def build_rib(fake: Faker | None, rng: random.Random) -> Rib:
    return Rib(
        account_holder=random_company(fake, rng),
        bank_name=rng.choice(BANKS),
        bank_address=random_address(fake, rng),
        iban=generate_iban(rng),
        bic=generate_bic(rng),
        bank_code=generate_digits(rng, 5),
        branch_code=generate_digits(rng, 5),
        account_number=generate_digits(rng, 11),
        rib_key=generate_digits(rng, 2),
    )


def rib_to_text(rib: Rib) -> str:
    return textwrap.dedent(
        f"""\
        RELEVE D'IDENTITE BANCAIRE

        Titulaire du compte : {rib.account_holder}
        Banque : {rib.bank_name}
        Adresse de la banque : {rib.bank_address}

        IBAN : {rib.iban}
        BIC : {rib.bic}
        Code banque : {rib.bank_code}
        Code guichet : {rib.branch_code}
        Numero de compte : {rib.account_number}
        Cle RIB : {rib.rib_key}

        Document fourni pour les virements fournisseurs.
        """
    ).strip() + "\n"


def rib_to_dict(rib: Rib) -> dict:
    return {
        "account_holder": rib.account_holder,
        "bank_name": rib.bank_name,
        "iban": rib.iban,
        "bic": rib.bic,
    }


def write_rib(index: int, rib: Rib, output_dir: Path, output_format: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"rib-{index:04d}"

    if output_format in {"both", "json"}:
        (output_dir / f"{stem}.json").write_text(
            json.dumps(rib_to_dict(rib), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    if output_format in {"both", "txt"}:
        txt_content = rib_to_text(rib)
        (output_dir / f"{stem}.txt").write_text(txt_content, encoding="utf-8")
    else:
        txt_content = rib_to_text(rib)

    write_text_pdf(output_dir / f"{stem}.pdf", txt_content)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    rng = random.Random(args.seed)
    fake = get_faker()
    if fake is not None and args.seed is not None:
        Faker.seed(args.seed)

    for index in range(1, args.count + 1):
        rib = build_rib(fake=fake, rng=rng)
        write_rib(index=index, rib=rib, output_dir=args.output_dir, output_format=args.format)

    summary = {
        "count": args.count,
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
