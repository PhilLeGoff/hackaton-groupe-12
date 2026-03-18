#!/usr/bin/env python3

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
GENERATORS = {
    "factures": "generate_invoices.py",
    "devis": "generate_quotes.py",
    "attestations_urssaf": "generate_urssaf_certificates.py",
    "ribs": "generate_ribs.py",
    "kbis": "generate_kbis.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a large OCR dataset across all document types."
    )
    parser.add_argument("--count", type=int, default=500, help="Documents per type.")
    parser.add_argument("--seed", type=int, default=42, help="Base random seed.")
    parser.add_argument(
        "--format",
        choices=["both", "json", "txt"],
        default="both",
        help="Structured output format for all generators.",
    )
    parser.add_argument(
        "--image-formats",
        default="pdf,png,jpg",
        help="Comma-separated rendered formats for all generators.",
    )
    parser.add_argument(
        "--noise-level",
        type=int,
        choices=[0, 1, 2, 3],
        default=0,
        help="OCR noise level for PNG/JPG/JPEG outputs.",
    )
    parser.add_argument(
        "--fixed-layout",
        action="store_true",
        help="Disable layout variation across all generators.",
    )
    parser.add_argument(
        "--fixed-fonts",
        action="store_true",
        help="Disable font variation across all generators.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    for index, (name, script_name) in enumerate(GENERATORS.items()):
        script_path = Path(__file__).resolve().parent / script_name
        command = [
            sys.executable,
            str(script_path),
            "--count",
            str(args.count),
            "--seed",
            str(args.seed + index),
            "--format",
            args.format,
            "--image-formats",
            args.image_formats,
            "--noise-level",
            str(args.noise_level),
        ]
        if args.fixed_layout:
            command.append("--fixed-layout")
        if args.fixed_fonts:
            command.append("--fixed-fonts")
        subprocess.run(command, check=True, cwd=ROOT_DIR)
        print(f"Generated {args.count} documents for {name}.")


if __name__ == "__main__":
    main()
