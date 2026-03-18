#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import random
import textwrap
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from pdf_utils import parse_image_formats, write_all_formats
from utils import generate_siren as generate_valid_siren, generate_siret as generate_valid_siret

try:
    from faker import Faker
except ImportError:
    Faker = None


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = ROOT_DIR / "data" / "generated" / "pdfs" / "kbis"

COMPANY_SUFFIXES = ["SARL", "SAS", "EURL", "SCI", "SA"]
LEGAL_FORMS = [
    "Societe a responsabilite limitee (SARL)",
    "Societe par actions simplifiee (SAS)",
    "Entreprise unipersonnelle a responsabilite limitee (EURL)",
    "Societe anonyme (SA)",
    "Societe civile immobiliere (SCI)",
]
LAST_NAMES = ["Martin", "Bernard", "Petit", "Robert", "Richard", "Durand", "Dubois", "Moreau", "Simon"]
FIRST_NAMES = ["Camille", "Nora", "Sami", "Lea", "Yanis", "Sarah", "Julie", "Ines", "Thomas"]
GREFFES = ["Paris", "Lyon", "Lille", "Bordeaux", "Nantes", "Toulouse", "Rennes"]
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
class Kbis:
    denomination: str
    forme_juridique: str
    capital_social: int
    adresse_siege: str
    siren: str
    siret: str
    rcs: str
    greffe: str
    date_immatriculation: str
    dirigeant: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate synthetic KBIS documents for OCR and extraction tests."
    )
    parser.add_argument("-n", "--count", type=int, default=10, help="Number of KBIS documents.")
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
        help="Structured output format.",
    )
    parser.add_argument(
        "--image-formats",
        default="pdf,png,jpg",
        help="Comma-separated rendered formats. Example: pdf,png,jpg,jpeg",
    )
    parser.add_argument(
        "--noise-level",
        type=int,
        choices=[0, 1, 2, 3],
        default=0,
        help="OCR noise level for rendered PNG/JPG/JPEG images.",
    )
    parser.add_argument(
        "--fixed-layout",
        action="store_true",
        help="Disable layout variation in rendered outputs.",
    )
    parser.add_argument(
        "--fixed-fonts",
        action="store_true",
        help="Disable font variation in rendered outputs.",
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


def random_manager(fake: Faker | None, rng: random.Random) -> str:
    if fake is not None:
        return fake.name()
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"


def format_capital(amount: int) -> str:
    return f"{amount:,} EUR".replace(",", " ")


def build_kbis(fake: Faker | None, rng: random.Random) -> Kbis:
    denomination = random_company(fake, rng)
    forme_juridique = rng.choice(LEGAL_FORMS)
    capital_social = rng.randrange(1000, 500001, 500)
    adresse_siege = random_address(fake, rng)
    siren = generate_valid_siren(rng)
    _, siret = generate_valid_siret(rng, siren=siren)
    greffe = rng.choice(GREFFES)
    immatriculation = date.today() - timedelta(days=rng.randint(180, 5000))
    rcs = f"RCS {greffe} {siren}"
    dirigeant = random_manager(fake, rng)

    return Kbis(
        denomination=denomination,
        forme_juridique=forme_juridique,
        capital_social=capital_social,
        adresse_siege=adresse_siege,
        siren=siren,
        siret=siret,
        rcs=rcs,
        greffe=greffe,
        date_immatriculation=immatriculation.isoformat(),
        dirigeant=dirigeant,
    )


def kbis_to_text(kbis: Kbis) -> str:
    return textwrap.dedent(
        f"""\
        EXTRAIT KBIS

        Denomination : {kbis.denomination}
        Forme juridique : {kbis.forme_juridique}
        Capital social : {format_capital(kbis.capital_social)}
        Adresse du siege : {kbis.adresse_siege}

        SIREN : {kbis.siren}
        SIRET : {kbis.siret}
        RCS : {kbis.rcs}
        Greffe : {kbis.greffe}
        Date d'immatriculation : {kbis.date_immatriculation}
        Dirigeant : {kbis.dirigeant}

        Document certifiant l'existence juridique de l'entreprise.
        """
    ).strip() + "\n"


def kbis_to_dict(kbis: Kbis) -> dict:
    return {
        "denomination": kbis.denomination,
        "forme_juridique": kbis.forme_juridique,
        "capital_social": kbis.capital_social,
        "adresse_siege": kbis.adresse_siege,
        "siren": kbis.siren,
        "siret": kbis.siret,
        "rcs": kbis.rcs,
        "greffe": kbis.greffe,
        "date_immatriculation": kbis.date_immatriculation,
        "dirigeant": kbis.dirigeant,
    }


def write_kbis(
    index: int,
    kbis: Kbis,
    output_dir: Path,
    output_format: str,
    image_formats: tuple[str, ...],
    noise_level: int,
    rng: random.Random,
    layout_variation: bool,
    font_variation: bool,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"kbis-{index:04d}"
    txt_content = kbis_to_text(kbis)

    if output_format in {"both", "json"}:
        (output_dir / f"{stem}.json").write_text(
            json.dumps(kbis_to_dict(kbis), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    if output_format in {"both", "txt"}:
        (output_dir / f"{stem}.txt").write_text(txt_content, encoding="utf-8")

    write_all_formats(
        output_dir / stem,
        txt_content,
        image_formats,
        noise_level=noise_level,
        rng=rng,
        layout_variation=layout_variation,
        font_variation=font_variation,
    )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    rng = random.Random(args.seed)
    fake = get_faker()
    image_formats = parse_image_formats(args.image_formats)
    if fake is not None and args.seed is not None:
        Faker.seed(args.seed)

    for index in range(1, args.count + 1):
        kbis = build_kbis(fake=fake, rng=rng)
        write_kbis(
            index=index,
            kbis=kbis,
            output_dir=args.output_dir,
            output_format=args.format,
            image_formats=image_formats,
            noise_level=args.noise_level,
            rng=rng,
            layout_variation=not args.fixed_layout,
            font_variation=not args.fixed_fonts,
        )

    summary = {
        "count": args.count,
        "output_dir": str(args.output_dir),
        "format": args.format,
        "image_formats": list(image_formats),
        "noise_level": args.noise_level,
        "layout_variation": not args.fixed_layout,
        "font_variation": not args.fixed_fonts,
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
