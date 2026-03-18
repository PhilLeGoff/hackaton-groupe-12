from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


PAGE_SIZE = (1240, 1754)
MARGIN_X = 80
MARGIN_Y = 90
CONTENT_WIDTH = PAGE_SIZE[0] - (2 * MARGIN_X)
LINE_SPACING = 16


def load_font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ]

    for candidate in candidates:
        font_path = Path(candidate)
        if font_path.exists():
            return ImageFont.truetype(str(font_path), size=size)

    return ImageFont.load_default()


def wrap_line(draw: ImageDraw.ImageDraw, line: str, font, max_width: int) -> list[str]:
    if not line:
        return [""]

    words = line.split()
    wrapped_lines = []
    current = words[0]

    for word in words[1:]:
        trial = f"{current} {word}"
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            wrapped_lines.append(current)
            current = word

    wrapped_lines.append(current)
    return wrapped_lines


def write_text_pdf(output_path: Path, text: str) -> None:
    image = Image.new("RGB", PAGE_SIZE, color="white")
    draw = ImageDraw.Draw(image)
    title_font = load_font(34, bold=True)
    body_font = load_font(24)

    current_y = MARGIN_Y
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line:
            current_y += 28
            continue

        font = title_font if current_y == MARGIN_Y else body_font
        wrapped_lines = wrap_line(draw, line, font, CONTENT_WIDTH)

        for wrapped_line in wrapped_lines:
            draw.text((MARGIN_X, current_y), wrapped_line, fill="black", font=font)
            bbox = draw.textbbox((MARGIN_X, current_y), wrapped_line, font=font)
            line_height = bbox[3] - bbox[1]
            current_y += line_height + LINE_SPACING

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, "PDF", resolution=150.0)
