from __future__ import annotations

import re
import subprocess
import zipfile
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree import ElementTree


OCR_LANG = "fra+eng"
OCR_TIMEOUT_SECONDS = 90


class OCRError(RuntimeError):
    pass


def extract_text(raw_content: bytes, content_type: str, filename: str = "") -> str:
    if content_type == "text/plain":
        return _decode_text(raw_content)

    if content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return _extract_docx_text(raw_content)

    with TemporaryDirectory(prefix="upload-ocr-") as tmpdir:
        suffix = Path(filename).suffix if filename else _guess_suffix(content_type)
        input_path = Path(tmpdir) / f"document{suffix}"
        input_path.write_bytes(raw_content)

        if content_type == "application/pdf":
            pdf_text = _extract_pdf_text(input_path)
            if pdf_text.strip():
                return _normalize_whitespace(pdf_text)
            return _normalize_whitespace(_run_pdf_ocr(input_path, Path(tmpdir)))

        return _normalize_whitespace(_run_tesseract(input_path))


def _decode_text(content: bytes) -> str:
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            return _normalize_whitespace(content.decode(encoding))
        except UnicodeDecodeError:
            continue
    return _normalize_whitespace(content.decode("utf-8", errors="ignore"))


def _extract_docx_text(content: bytes) -> str:
    try:
        with zipfile.ZipFile(BytesIO(content)) as archive:
            xml_content = archive.read("word/document.xml")
    except (KeyError, zipfile.BadZipFile) as exc:
        raise OCRError("Impossible de lire le contenu du DOCX.") from exc

    root = ElementTree.fromstring(xml_content)
    namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    texts = [
        node.text.strip()
        for node in root.findall(".//w:t", namespaces)
        if node.text and node.text.strip()
    ]
    return _normalize_whitespace("\n".join(texts))


def _extract_pdf_text(input_path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""
    try:
        reader = PdfReader(str(input_path))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception:
        return ""
    return "\n".join(pages)


def _run_pdf_ocr(input_path: Path, tmpdir: Path) -> str:
    if not _shutil_which("pdftoppm"):
        raise OCRError("OCR PDF indisponible: pdftoppm est requis.")

    output_prefix = tmpdir / "page"
    try:
        subprocess.run(
            ["pdftoppm", "-png", str(input_path), str(output_prefix)],
            check=True, capture_output=True, text=True, timeout=OCR_TIMEOUT_SECONDS,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise OCRError("La conversion du PDF en images a echoue.") from exc

    page_images = sorted(tmpdir.glob("page-*.png"))
    if not page_images:
        raise OCRError("Aucune image n'a ete generee a partir du PDF.")

    return "\n".join(_run_tesseract(img) for img in page_images)


def _run_tesseract(input_path: Path) -> str:
    if not _shutil_which("tesseract"):
        raise OCRError("Tesseract n'est pas installe sur la machine.")

    try:
        result = subprocess.run(
            ["tesseract", str(input_path), "stdout", "-l", OCR_LANG, "--psm", "6"],
            check=True, capture_output=True, text=True, timeout=OCR_TIMEOUT_SECONDS,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise OCRError("L'execution OCR a echoue.") from exc

    return result.stdout


def _is_spaced_line(line: str) -> bool:
    """Check if a line has the spaced-letter pattern (e.g. 'F A C T U R E')."""
    tokens = line.split()
    if len(tokens) < 4:
        return False
    single_char_count = sum(1 for t in tokens if len(t) == 1)
    return (single_char_count / len(tokens)) > 0.6


def _fix_spaced_line_raw(raw_line: str) -> str:
    """Fix a spaced-letter line using original spacing to detect word boundaries.

    In the raw PDF text, word boundaries have wider gaps (2+ spaces) than
    letter spacing (1 space). E.g.:
      'F a c t u r e   n °   1 2 3 4 5' → 'Facture n° 12345'
    """
    # Split on gaps of 2+ spaces → word groups
    groups = re.split(r' {2,}', raw_line.strip())
    words = []
    for group in groups:
        group = group.strip()
        if not group:
            continue
        tokens = group.split(' ')
        single_chars = sum(1 for t in tokens if len(t) == 1)
        if len(tokens) >= 2 and single_chars / len(tokens) > 0.6:
            # Join single chars within this word group
            words.append("".join(tokens))
        else:
            words.append(group)
    return " ".join(words)


def _normalize_whitespace(text: str) -> str:
    result_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Check for spaced-letter pattern BEFORE collapsing spaces
        normalized = re.sub(r"[ \t]+", " ", stripped).strip()
        if _is_spaced_line(normalized):
            result_lines.append(_fix_spaced_line_raw(stripped))
        else:
            result_lines.append(normalized)
    return "\n".join(result_lines)


def _guess_suffix(content_type: str) -> str:
    return {
        "application/pdf": ".pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "text/plain": ".txt",
    }.get(content_type, ".bin")


def _shutil_which(binary: str) -> str | None:
    try:
        from shutil import which
    except ImportError:
        return None
    return which(binary)
