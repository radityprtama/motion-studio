"""Conservative, deterministic finishing for opaque portrait frames."""

from __future__ import annotations

from functools import lru_cache
from math import hypot
from random import Random

from PIL import Image, ImageChops

from .style import Style


@lru_cache(maxsize=24)
def _grain(seed: int, width: int, height: int) -> Image.Image:
    small_width = max(1, width // 2)
    small_height = max(1, height // 2)
    random = Random(seed)
    data = bytes(random.randrange(72, 185) for _ in range(small_width * small_height))
    return Image.frombytes("L", (small_width, small_height), data).resize((width, height), Image.Resampling.BILINEAR)


@lru_cache(maxsize=24)
def _vignette(width: int, height: int, strength: float) -> Image.Image:
    small_width = max(1, width // 6)
    small_height = max(1, height // 6)
    values = bytearray(small_width * small_height)
    for y in range(small_height):
        ny = ((y + 0.5) / small_height - 0.5) / 0.69
        for x in range(small_width):
            nx = ((x + 0.5) / small_width - 0.5) / 0.7
            distance = hypot(nx, ny)
            attenuation = strength * max(0.0, (distance - 0.18) / 0.85) ** 1.5
            values[y * small_width + x] = max(0, min(255, round(255 * (1 - attenuation))))
    return Image.frombytes("L", (small_width, small_height), bytes(values)).resize((width, height), Image.Resampling.BILINEAR)


def finish_frame(frame: Image.Image, *, style: Style, seed: int) -> Image.Image:
    """Apply static seeded grain and a subtle vignette without changing alpha."""
    if style.grain_strength == 0 and style.vignette_strength == 0:
        return frame
    if not 0 <= style.grain_strength <= 1 or not 0 <= style.vignette_strength <= 1:
        raise ValueError("Finishing strengths must be between 0 and 1")
    width, height = frame.size
    rgb = frame.convert("RGB")
    if style.vignette_strength:
        mask = _vignette(width, height, style.vignette_strength)
        rgb = ImageChops.multiply(rgb, Image.merge("RGB", (mask, mask, mask)))
    if style.grain_strength:
        noise = _grain(seed, width, height)
        rgb = Image.blend(rgb, Image.merge("RGB", (noise, noise, noise)), style.grain_strength)
    result = rgb.convert("RGBA")
    result.putalpha(255)
    return result
