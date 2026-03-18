#!/usr/bin/env python3
"""Generate synthetic URSSAF vigilance certificates for OCR and extraction tests."""

from __future__ import annotations

import argparse
import json
import random
import textwrap
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

try:
    from faker import Faker
except ImportError:  # pragma: no cover - optional dependency
    Faker = None


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT_DIR / "data" / "generated" / "pdfs" / "attestations_urssaf"
COMPANY_SUFFIXES = ["SARL", "SAS", "EURL", "SCI", "SA"]
LAST_NAMES = ["Martin", "Bernard", "Robert", "Durand", "Dubois", "Moreau", "Simon"]
URSSAF_ORGANISMS = [
    "URSSAF Hauts-de-France",
    "URSSAF Ile-de-France",
    "URSSAF Occitanie",
    "URSSAF Nouvelle-Aquitaine",
]
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
class Certificate:
    certificate_id: str
    company: str
    address: str
    siret: str
    naf_code: str
    issue_date: str
    expiry_date: str
    organism: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate synthetic URSSAF certificates for OCR and extraction tests."
    )
    parser.add_argument("-n", "--count", type=int, default=10, help="Number of certificates.")
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
        help="Output document format.",
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


def generate_siret(rng: random.Random) -> str:
    return "".join(str(rng.randint(0, 9)) for _ in range(14))


def generate_naf_code(rng: random.Random) -> str:
    return f"{rng.randint(1000, 9999)}{rng.choice(['A', 'B', 'C', 'D'])}"


def build_certificate(index: int, fake: Faker | None, rng: random.Random) -> Certificate:
    issue_date = date.today() - timedelta(days=rng.randint(1, 120))
    expiry_date = issue_date + timedelta(days=180)
    return Certificate(
        certificate_id=f"URS-2026-{index:05d}",
        company=random_company(fake, rng),
        address=random_address(fake, rng),
        siret=generate_siret(rng),
        naf_code=generate_naf_code(rng),
        issue_date=issue_date.isoformat(),
        expiry_date=expiry_date.isoformat(),
        organism=rng.choice(URSSAF_ORGANISMS),
    )


def certificate_to_text(certificate: Certificate) -> str:
    return textwrap.dedent(
        f"""\
        ATTESTATION DE VIGILANCE URSSAF

        Numero d'attestation : {certificate.certificate_id}
        Date d'emission : {certificate.issue_date}
        Date d'expiration : {certificate.expiry_date}
        Organisme : {certificate.organism}

        Entreprise : {certificate.company}
        Adresse : {certificate.address}
        SIRET : {certificate.siret}
        Code NAF : {certificate.naf_code}

        Cette attestation certifie que l'entreprise est a jour
        de ses obligations de declaration et de paiement des cotisations sociales.
        """
    ).strip() + "\n"


def certificate_to_dict(certificate: Certificate) -> dict:
    return {
        "certificate_id": certificate.certificate_id,
        "company": certificate.company,
        "siret": certificate.siret,
        "issue_date": certificate.issue_date,
        "expiry_date": certificate.expiry_date,
    }


def write_certificate(certificate: Certificate, output_dir: Path, output_format: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = certificate.certificate_id.lower()

    if output_format in {"both", "json"}:
        (output_dir / f"{stem}.json").write_text(
            json.dumps(certificate_to_dict(certificate), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    if output_format in {"both", "txt"}:
        (output_dir / f"{stem}.txt").write_text(
            certificate_to_text(certificate),
            encoding="utf-8",
        )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    rng = random.Random(args.seed)
    fake = get_faker()
    if fake is not None and args.seed is not None:
        Faker.seed(args.seed)

    for index in range(1, args.count + 1):
        certificate = build_certificate(index=index, fake=fake, rng=rng)
        write_certificate(certificate, args.output_dir, args.format)

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
