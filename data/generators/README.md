# Dataset Generators

This folder contains the dataset generation scripts used for OCR and extraction tests.

## Available Scripts

- `generate_invoices.py`: generates synthetic French supplier invoices.
- `generate_quotes.py`: generates synthetic French quotes (`devis`).
- `generate_urssaf_certificates.py`: generates synthetic URSSAF vigilance certificates.
- `generate_ribs.py`: generates synthetic RIB documents.
- `generate_kbis.py`: generates synthetic KBIS documents.
- `generate_large_dataset.py`: generates 500+ documents per type in one run.
- `generate_ner_annotations.py`: generates BIO/IOB NER ground-truth annotations from TXT+JSON pairs.
- `pdf_utils.py`: shared multi-format rendering helper used by all generators.

Default output folders:

- invoices: `data/generated/factures`
- quotes: `data/generated/pdfs/devis`
- URSSAF: `data/generated/pdfs/attestations_urssaf`
- RIB: `data/generated/pdfs/ribs`
- KBIS: `data/generated/pdfs/kbis`

## Requirements

The script works with the Python standard library only.

If you want more realistic names and addresses, install `faker`:

```bash
pip install faker
```

## Usage

Run from the repository root.

Generate invoices:

```bash
python data/generators/generate_invoices.py
```

Generate quotes:

```bash
python data/generators/generate_quotes.py
```

Generate URSSAF certificates:

```bash
python data/generators/generate_urssaf_certificates.py
```

Generate RIBs:

```bash
python data/generators/generate_ribs.py
```

Generate KBIS:

```bash
python data/generators/generate_kbis.py
```

Generate a large dataset:

```bash
python data/generators/generate_large_dataset.py --count 500 --seed 42
```

Generate NER annotations:

```bash
python data/generators/generate_ner_annotations.py
```

Generate 100 invoices:

```bash
python data/generators/generate_invoices.py --count 100
```

Generate 100 quotes:

```bash
python data/generators/generate_quotes.py --count 100
```

Generate 100 URSSAF certificates:

```bash
python data/generators/generate_urssaf_certificates.py --count 100
```

Generate 100 RIBs:

```bash
python data/generators/generate_ribs.py --count 100
```

Generate 100 KBIS:

```bash
python data/generators/generate_kbis.py --count 100
```

Generate 500 documents per type:

```bash
python data/generators/generate_large_dataset.py --count 500
```

Generate JSON plus the default rendered images:

```bash
python data/generators/generate_invoices.py --format json
python data/generators/generate_quotes.py --format json
python data/generators/generate_urssaf_certificates.py --format json
python data/generators/generate_ribs.py --format json
```

Render all image formats:

```bash
python data/generators/generate_invoices.py --image-formats pdf,png,jpg,jpeg
```

Generate into a custom folder:

```bash
python data/generators/generate_invoices.py --output-dir data/generated/custom_factures
```

Use a fixed seed for reproducible output:

```bash
python data/generators/generate_invoices.py --seed 42
python data/generators/generate_quotes.py --seed 42
python data/generators/generate_urssaf_certificates.py --seed 42
python data/generators/generate_ribs.py --seed 42
```

Control anomaly frequency:

```bash
python data/generators/generate_invoices.py --anomaly-rate 0.2
python data/generators/generate_quotes.py --anomaly-rate 0.2
python data/generators/generate_urssaf_certificates.py --anomaly-rate 0.2
python data/generators/generate_ribs.py --anomaly-rate 0.2
```

Control OCR image noise:

```bash
python data/generators/generate_invoices.py --noise-level 2
python data/generators/generate_quotes.py --noise-level 2
python data/generators/generate_urssaf_certificates.py --noise-level 2
python data/generators/generate_ribs.py --noise-level 2
python data/generators/generate_kbis.py --noise-level 2
```

Disable layout variation:

```bash
python data/generators/generate_invoices.py --fixed-layout
```

Disable font variation:

```bash
python data/generators/generate_invoices.py --fixed-fonts
```

Generate annotations for selected document types only:

```bash
python data/generators/generate_ner_annotations.py --doc-types invoices,quotes,kbis
```

Limit annotation generation to a small sample:

```bash
python data/generators/generate_ner_annotations.py --limit 10
```

## Testing

Run a quick syntax check on all generators:

```bash
python -m py_compile data/generators/*.py
```

Generate a small sample for each document type:

```bash
python data/generators/generate_invoices.py --count 2 --seed 42 --format both --image-formats pdf,png,jpg,jpeg
python data/generators/generate_quotes.py --count 2 --seed 42 --format both --image-formats pdf,png,jpg,jpeg
python data/generators/generate_urssaf_certificates.py --count 2 --seed 42 --format both --image-formats pdf,png,jpg,jpeg
python data/generators/generate_ribs.py --count 2 --seed 42 --format both --image-formats pdf,png,jpg,jpeg
python data/generators/generate_kbis.py --count 2 --seed 42 --format both --image-formats pdf,png,jpg,jpeg
```

Check that generated files exist in the repository folders:

```bash
command find data/generated/factures -maxdepth 1 -type f | sort
command find data/generated/pdfs/devis -maxdepth 1 -type f | sort
command find data/generated/pdfs/attestations_urssaf -maxdepth 1 -type f | sort
command find data/generated/pdfs/ribs -maxdepth 1 -type f | sort
command find data/generated/pdfs/kbis -maxdepth 1 -type f | sort
```

Test large dataset generation:

```bash
python data/generators/generate_large_dataset.py --count 3 --seed 42 --format both --noise-level 1
```

Validate SIRET and IBAN checksums:

```bash
python - <<'PY'
import json
from pathlib import Path
from data.generators.utils import iban_numeric_representation, luhn_checksum

invoice = json.loads(Path("data/generated/factures/fac-2026-0001.json").read_text())
rib = json.loads(Path("data/generated/pdfs/ribs/rib-0001.json").read_text())

print("supplier_siret_valid", luhn_checksum(invoice["supplier_siret"]) == 0)
print("customer_siret_valid", luhn_checksum(invoice["customer_siret"]) == 0)

iban = rib["iban"].replace(" ", "")
numeric = iban_numeric_representation(iban)
print("iban_valid", int(numeric) % 97 == 1)
PY
```

Generate and inspect BIO annotations:

```bash
python data/generators/generate_ner_annotations.py --limit 5 --output-dir data/generated/ner_test
ls -la data/generated/ner_test
sed -n '1,80p' data/generated/ner_test/summary.json
sed -n '1,80p' data/generated/ner_test/dataset.bio
sed -n '1,120p' data/generated/ner_test/manifest.json
```

Test OCR noise visually by keeping the same seed and changing only `--noise-level`:

```bash
python data/generators/generate_invoices.py --count 1 --seed 42 --noise-level 0 --output-dir data/generated/test_noise_0
python data/generators/generate_invoices.py --count 1 --seed 42 --noise-level 1 --output-dir data/generated/test_noise_1
python data/generators/generate_invoices.py --count 1 --seed 42 --noise-level 2 --output-dir data/generated/test_noise_2
python data/generators/generate_invoices.py --count 1 --seed 42 --noise-level 3 --output-dir data/generated/test_noise_3
```

Compare the generated PNG or JPG files in:

- `data/generated/test_noise_0`
- `data/generated/test_noise_1`
- `data/generated/test_noise_2`
- `data/generated/test_noise_3`

Expected result:

- `noise-level 0`: clean render
- `noise-level 1`: light degradation
- `noise-level 2`: stronger blur/compression/noise
- `noise-level 3`: strongest degradation

Test layout variation by comparing default output to `--fixed-layout`:

```bash
python data/generators/generate_invoices.py --count 1 --seed 42 --fixed-fonts --fixed-layout --output-dir data/generated/test_layout_fixed
python data/generators/generate_invoices.py --count 1 --seed 42 --fixed-fonts --output-dir data/generated/test_layout_varied
```

Expected differences:

- margins
- block spacing
- title alignment
- vertical text placement

Test font variation by comparing default output to `--fixed-fonts`:

```bash
python data/generators/generate_invoices.py --count 1 --seed 42 --fixed-layout --fixed-fonts --output-dir data/generated/test_fonts_fixed
python data/generators/generate_invoices.py --count 1 --seed 42 --fixed-layout --output-dir data/generated/test_fonts_varied
```

Expected differences:

- font family
- font size
- text darkness / visual weight

Recommended approach:

- keep the same `--seed`
- change only one flag at a time
- compare the generated PNG or JPG files side by side

## Notes

- These generators create rendered image files controlled by `--image-formats`.
- The default rendered formats are `pdf,png,jpg`.
- The `--format` flag controls whether `.json`, `.txt`, or both are written in addition to the rendered files.
- Noise is applied to PNG/JPG/JPEG outputs with `--noise-level` (`0` none, `3` strong).
- Layout variation is enabled by default in rendered outputs and can be disabled with `--fixed-layout`.
- Font variation is enabled by default in rendered outputs and can be disabled with `--fixed-fonts`.
- The NER generator writes `dataset.bio`, `manifest.json`, and `summary.json` under `data/generated/ner` by default.
- The annotation format is token-per-line with `TOKEN<TAB>LABEL`, separated by blank lines between documents.
- Each generator writes a `summary.json` file to its output folder.
