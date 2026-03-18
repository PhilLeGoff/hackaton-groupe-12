#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import random
import textwrap
from dataclasses import dataclass
from pathlib import Path

from pdf_utils import parse_image_formats, write_all_formats
from utils import generate_bic, generate_french_rib, invalidate_bic, invalidate_iban

try:
    from faker import Faker
except ImportError:
    Faker = None


ROOT_DIR = Path(__file__).resolve().parents[2]
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
    scenario: str
    anomalies: list[str]


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
        "--anomaly-rate",
        type=float,
        default=0.2,
        help="Share of RIBs containing one or more anomalies.",
    )
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


def generate_digits(rng: random.Random, length: int) -> str:
    return "".join(str(rng.randint(0, 9)) for _ in range(length))


def choose_scenario(rng: random.Random, anomaly_rate: float) -> tuple[str, list[str]]:
    if rng.random() > anomaly_rate:
        return "legitime", []
    scenarios = [
        ("iban_invalide", ["IBAN invalide"]),
        ("bic_incorrect", ["BIC incorrect"]),
        ("multi_anomalies", ["IBAN invalide", "BIC incorrect"]),
    ]
    return rng.choice(scenarios)


def build_rib(fake: Faker | None, rng: random.Random, anomaly_rate: float) -> Rib:
    scenario, anomalies = choose_scenario(rng, anomaly_rate)
    rib_details = generate_french_rib(rng)
    iban = rib_details["iban"]
    bic = generate_bic(rng)

    if scenario in {"iban_invalide", "multi_anomalies"}:
        iban = invalidate_iban(iban)
    if scenario in {"bic_incorrect", "multi_anomalies"}:
        bic = invalidate_bic(bic)

    return Rib(
        account_holder=random_company(fake, rng),
        bank_name=rng.choice(BANKS),
        bank_address=random_address(fake, rng),
        iban=iban,
        bic=bic,
        bank_code=rib_details["bank_code"],
        branch_code=rib_details["branch_code"],
        account_number=rib_details["account_number"],
        rib_key=rib_details["rib_key"],
        scenario=scenario,
        anomalies=anomalies,
    )


def rib_to_text(rib: Rib) -> str:
    anomalies = ", ".join(rib.anomalies) if rib.anomalies else "Aucune"
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
        Scenario dataset : {rib.scenario}
        Anomalies attendues : {anomalies}
        """
    ).strip() + "\n"


def rib_to_dict(rib: Rib) -> dict:
    return {
        "account_holder": rib.account_holder,
        "bank_name": rib.bank_name,
        "iban": rib.iban,
        "bic": rib.bic,
        "scenario": rib.scenario,
        "anomalies": rib.anomalies,
    }


def write_rib(
    index: int,
    rib: Rib,
    output_dir: Path,
    output_format: str,
    image_formats: tuple[str, ...],
    noise_level: int,
    rng: random.Random,
    layout_variation: bool,
    font_variation: bool,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"rib-{index:04d}"
    txt_content = rib_to_text(rib)

    if output_format in {"both", "json"}:
        (output_dir / f"{stem}.json").write_text(
            json.dumps(rib_to_dict(rib), ensure_ascii=False, indent=2) + "\n",
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
    scenarios: list[str] = []
    if fake is not None and args.seed is not None:
        Faker.seed(args.seed)

    for index in range(1, args.count + 1):
        rib = build_rib(fake=fake, rng=rng, anomaly_rate=args.anomaly_rate)
        write_rib(
            index=index,
            rib=rib,
            output_dir=args.output_dir,
            output_format=args.format,
            image_formats=image_formats,
            noise_level=args.noise_level,
            rng=rng,
            layout_variation=not args.fixed_layout,
            font_variation=not args.fixed_fonts,
        )
        scenarios.append(rib.scenario)

    scenario_counts: dict[str, int] = {}
    for scenario in scenarios:
        scenario_counts[scenario] = scenario_counts.get(scenario, 0) + 1
    summary = {
        "count": args.count,
        "output_dir": str(args.output_dir),
        "format": args.format,
        "image_formats": list(image_formats),
        "noise_level": args.noise_level,
        "layout_variation": not args.fixed_layout,
        "font_variation": not args.fixed_fonts,
        "scenarios": scenario_counts,
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
