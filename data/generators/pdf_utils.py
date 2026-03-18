from __future__ import annotations

from pathlib import Path
import random

from PIL import Image, ImageDraw, ImageFont
from noise import apply_noise_pipeline


PAGE_SIZE = (1240, 1754)
MARGIN_X = 80
MARGIN_Y = 90
CONTENT_WIDTH = PAGE_SIZE[0] - (2 * MARGIN_X)
LINE_SPACING = 16
DEFAULT_IMAGE_FORMATS = ("pdf", "png", "jpg")
FONT_FAMILIES = {
    "sans": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ],
    "sans_bold": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    ],
    "serif": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/dejavu/DejaVuSerif.ttf",
    ],
    "serif_bold": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSerif-Bold.ttf",
    ],
    "mono": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/dejavu/DejaVuSansMono.ttf",
    ],
    "mono_bold": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSansMono-Bold.ttf",
    ],
}


def parse_image_formats(raw_value: str | None) -> tuple[str, ...]:
    if not raw_value:
        return DEFAULT_IMAGE_FORMATS

    supported_formats = {"pdf", "png", "jpg", "jpeg"}
    normalized_formats = []

    for item in raw_value.split(","):
        image_format = item.strip().lower()
        if not image_format:
            continue
        if image_format not in supported_formats:
            raise ValueError(
                f"Unsupported image format '{image_format}'. Use pdf,png,jpg,jpeg."
            )
        normalized_formats.append(image_format)

    return tuple(dict.fromkeys(normalized_formats)) or DEFAULT_IMAGE_FORMATS


def load_font(size: int, family: str = "sans", bold: bool = False):
    family_key = f"{family}_bold" if bold else family
    candidates = FONT_FAMILIES.get(family_key, FONT_FAMILIES["sans_bold" if bold else "sans"])

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


def choose_render_variant(
    rng: random.Random | None,
    layout_variation: bool,
    font_variation: bool,
) -> dict:
    local_rng = rng or random.Random()

    title_align = local_rng.choice(["left", "left", "center"]) if layout_variation else "left"
    family = local_rng.choice(["sans", "serif", "mono"]) if font_variation else "sans"

    return {
        "margin_x": local_rng.randint(55, 105) if layout_variation else MARGIN_X,
        "margin_y": local_rng.randint(70, 120) if layout_variation else MARGIN_Y,
        "section_gap": local_rng.randint(20, 34) if layout_variation else 28,
        "line_spacing": local_rng.randint(10, 22) if layout_variation else LINE_SPACING,
        "title_align": title_align,
        "title_size": local_rng.randint(30, 40) if font_variation else 34,
        "body_size": local_rng.randint(21, 27) if font_variation else 24,
        "body_family": family,
        "title_family": local_rng.choice(["sans", "serif"]) if font_variation else "sans",
        "title_fill": local_rng.randint(0, 50),
        "body_fill": local_rng.randint(0, 35),
    }


def render_text_image(
    text: str,
    rng: random.Random | None = None,
    layout_variation: bool = True,
    font_variation: bool = True,
) -> Image.Image:
    image = Image.new("RGB", PAGE_SIZE, color="white")
    draw = ImageDraw.Draw(image)
    variant = choose_render_variant(rng, layout_variation, font_variation)
    title_font = load_font(variant["title_size"], family=variant["title_family"], bold=True)
    body_font = load_font(variant["body_size"], family=variant["body_family"])

    margin_x = variant["margin_x"]
    margin_y = variant["margin_y"]
    content_width = PAGE_SIZE[0] - (2 * margin_x)
    current_y = margin_y
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line:
            current_y += variant["section_gap"]
            continue

        is_title_line = current_y == margin_y
        font = title_font if is_title_line else body_font
        wrapped_lines = wrap_line(draw, line, font, content_width)

        for wrapped_line in wrapped_lines:
            if is_title_line and variant["title_align"] == "center":
                text_width = draw.textlength(wrapped_line, font=font)
                x_position = max(margin_x, int((PAGE_SIZE[0] - text_width) / 2))
            else:
                x_position = margin_x

            fill_value = variant["title_fill"] if is_title_line else variant["body_fill"]
            draw.text((x_position, current_y), wrapped_line, fill=(fill_value, fill_value, fill_value), font=font)
            bbox = draw.textbbox((x_position, current_y), wrapped_line, font=font)
            line_height = bbox[3] - bbox[1]
            current_y += line_height + variant["line_spacing"]

    return image


def write_text_pdf(output_path: Path, text: str) -> None:
    image = render_text_image(text)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, "PDF", resolution=150.0)


def write_all_formats(
    output_stem: Path,
    text: str,
    image_formats: tuple[str, ...],
    noise_level: int = 0,
    rng: random.Random | None = None,
    layout_variation: bool = True,
    font_variation: bool = True,
) -> None:
    image = render_text_image(
        text,
        rng=rng,
        layout_variation=layout_variation,
        font_variation=font_variation,
    )
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    local_rng = rng or random.Random()

    for image_format in image_formats:
        if image_format == "pdf":
            image.save(output_stem.with_suffix(".pdf"), "PDF", resolution=150.0)
        elif image_format == "png":
            rendered_image = apply_noise_pipeline(image, noise_level, local_rng)
            rendered_image.save(output_stem.with_suffix(".png"), "PNG")
        elif image_format in {"jpg", "jpeg"}:
            rendered_image = apply_noise_pipeline(image, noise_level, local_rng)
            rendered_image.save(output_stem.with_suffix(f".{image_format}"), "JPEG", quality=95)
        else:
            raise ValueError(f"Unsupported image format '{image_format}'.")
