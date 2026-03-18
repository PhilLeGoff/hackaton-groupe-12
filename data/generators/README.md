# Dataset Generator

This folder contains the dataset generation scripts used for OCR and extraction tests.

## Available Scripts

- `generate_invoices.py`: generates synthetic French supplier invoices.
- `generate_quotes.py`: generates synthetic French quotes (`devis`).
- `generate_urssaf_certificates.py`: generates synthetic URSSAF vigilance certificates.
- `generate_ribs.py`: generates synthetic RIB documents.
- `pdf_utils.py`: shared PDF rendering helper used by all generators.

Default output folders:

- invoices: `data/generated/factures`
- quotes: `data/generated/pdfs/devis`
- URSSAF: `data/generated/pdfs/attestations_urssaf`
- RIB: `data/generated/pdfs/ribs`

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
python dataset/generate_invoices.py
```

Generate quotes:

```bash
python dataset/generate_quotes.py
```

Generate URSSAF certificates:

```bash
python dataset/generate_urssaf_certificates.py
```

Generate RIBs:

```bash
python dataset/generate_ribs.py
```

Generate 100 invoices:

```bash
python dataset/generate_invoices.py --count 100
```

Generate 100 quotes:

```bash
python dataset/generate_quotes.py --count 100
```

Generate 100 URSSAF certificates:

```bash
python dataset/generate_urssaf_certificates.py --count 100
```

Generate 100 RIBs:

```bash
python dataset/generate_ribs.py --count 100
```

Generate JSON plus PDFs only:

```bash
python dataset/generate_invoices.py --format json
python dataset/generate_quotes.py --format json
python dataset/generate_urssaf_certificates.py --format json
python dataset/generate_ribs.py --format json
```

Generate into a custom folder:

```bash
python dataset/generate_invoices.py --output-dir data/generated/custom_factures
```

Use a fixed seed for reproducible output:

```bash
python dataset/generate_invoices.py --seed 42
python dataset/generate_quotes.py --seed 42
python dataset/generate_urssaf_certificates.py --seed 42
python dataset/generate_ribs.py --seed 42
```

Control anomaly frequency:

```bash
python dataset/generate_invoices.py --anomaly-rate 0.2
```

## Notes

- These generators always create a `.pdf` file for each document.
- The `--format` flag controls whether `.json`, `.txt`, or both are written in addition to the PDF.
- These generators do not add layout position randomizer metadata.
- Each generator writes a `summary.json` file to its output folder.
