from __future__ import annotations

import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter


NOISE_PRESETS = {
    0: {"blur": 0.0, "salt_pepper": 0.0, "rotation": 0.0, "skew": 0.0, "jpeg_quality": 95},
    1: {"blur": 0.4, "salt_pepper": 0.002, "rotation": 1.5, "skew": 0.02, "jpeg_quality": 82},
    2: {"blur": 0.9, "salt_pepper": 0.006, "rotation": 3.0, "skew": 0.04, "jpeg_quality": 64},
    3: {"blur": 1.6, "salt_pepper": 0.012, "rotation": 5.0, "skew": 0.07, "jpeg_quality": 45},
}


def add_gaussian_blur(image: Image.Image, sigma: float) -> Image.Image:
    if sigma <= 0:
        return image
    return image.filter(ImageFilter.GaussianBlur(radius=sigma))


def add_salt_pepper(image: Image.Image, amount: float, rng: random.Random) -> Image.Image:
    if amount <= 0:
        return image

    noisy = image.copy()
    pixels = noisy.load()
    width, height = noisy.size
    total = int(width * height * amount)

    for _ in range(total):
        x = rng.randrange(width)
        y = rng.randrange(height)
        color = 0 if rng.random() < 0.5 else 255
        pixels[x, y] = (color, color, color)

    return noisy


def add_rotation(image: Image.Image, max_angle: float, rng: random.Random) -> Image.Image:
    if max_angle <= 0:
        return image
    angle = rng.uniform(-max_angle, max_angle)
    return image.rotate(angle, expand=False, fillcolor="white")


def add_skew(image: Image.Image, intensity: float, rng: random.Random) -> Image.Image:
    if intensity <= 0:
        return image

    width, height = image.size
    dx = width * intensity
    dy = height * intensity
    quad = (
        rng.uniform(0, dx),
        rng.uniform(0, dy),
        width - rng.uniform(0, dx),
        rng.uniform(0, dy),
        width - rng.uniform(0, dx),
        height - rng.uniform(0, dy),
        rng.uniform(0, dx),
        height - rng.uniform(0, dy),
    )
    return image.transform(image.size, Image.Transform.QUAD, quad, fillcolor="white")


def add_jpeg_artifacts(image: Image.Image, quality: int) -> Image.Image:
    if quality >= 95:
        return image

    from io import BytesIO

    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    return Image.open(buffer).convert("RGB")


def add_background_noise(image: Image.Image, rng: random.Random) -> Image.Image:
    overlay = Image.new("RGB", image.size, (245, 245, 245))
    draw = ImageDraw.Draw(overlay)
    width, height = image.size

    for _ in range(12):
        x1 = rng.randint(0, width)
        y1 = rng.randint(0, height)
        x2 = x1 + rng.randint(10, 120)
        y2 = y1 + rng.randint(1, 6)
        shade = rng.randint(215, 240)
        draw.ellipse((x1, y1, x2, y2), fill=(shade, shade, shade))

    for _ in range(8):
        y = rng.randint(0, height)
        shade = rng.randint(220, 235)
        draw.line((0, y, width, y + rng.randint(-2, 2)), fill=(shade, shade, shade), width=1)

    return ImageChops.multiply(image, overlay)


def apply_noise_pipeline(image: Image.Image, noise_level: int, rng: random.Random) -> Image.Image:
    preset = NOISE_PRESETS.get(noise_level, NOISE_PRESETS[0])
    noisy = image.convert("RGB")
    noisy = add_background_noise(noisy, rng) if noise_level > 0 else noisy
    noisy = add_rotation(noisy, preset["rotation"], rng)
    noisy = add_skew(noisy, preset["skew"], rng)
    noisy = add_gaussian_blur(noisy, preset["blur"])
    noisy = add_salt_pepper(noisy, preset["salt_pepper"], rng)
    noisy = add_jpeg_artifacts(noisy, preset["jpeg_quality"])
    return noisy
