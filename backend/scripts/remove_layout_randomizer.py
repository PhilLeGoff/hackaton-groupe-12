from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATASET_ROOT = ROOT_DIR / "data" / "generated" / "pdfs"
RANDOM_LAYOUT_KEYS = {"layout_variant", "layout_positions"}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Strip random layout metadata from generated dataset JSON files."
    )
    parser.add_argument(
        "--dataset-root",
        default=str(DEFAULT_DATASET_ROOT),
        help="Root directory containing generated PDF dataset JSON files.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only report files that still contain random layout metadata.",
    )
    args = parser.parse_args()

    dataset_root = Path(args.dataset_root)
    json_paths = sorted(dataset_root.glob("*/*.json"))
    updated = 0
    flagged = []

    for json_path in json_paths:
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue

        present_keys = RANDOM_LAYOUT_KEYS.intersection(payload)
        if not present_keys:
            continue

        flagged.append(str(json_path.relative_to(ROOT_DIR)))
        if args.check:
            continue

        for key in RANDOM_LAYOUT_KEYS:
            payload.pop(key, None)

        json_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        updated += 1

    if args.check:
        print(f"Files with random layout metadata: {len(flagged)}")
        for path in flagged[:20]:
            print(path)
        if len(flagged) > 20:
            print(f"... and {len(flagged) - 20} more")
        return 1 if flagged else 0

    print(f"Updated {updated} JSON files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
