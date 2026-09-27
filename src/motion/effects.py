"""Conservative, deterministic finishing for opaque portrait frames."""

from __future__ import annotations

from functools import lru_cache
from math import hypot
from random import Random
from dataclasses import dataclass
from typing import Protocol

from PIL import Image, ImageChops, ImageFilter

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


class Effect(Protocol):
    def apply(self, image: Image.Image) -> Image.Image: ...


@dataclass(frozen=True)
class Blur:
    radius: float

    def __post_init__(self) -> None:
        if not 0 <= self.radius <= 100:
            raise ValueError("Blur radius must be between 0 and 100")

    def apply(self, image: Image.Image) -> Image.Image:
        return image.filter(ImageFilter.GaussianBlur(self.radius))


@dataclass(frozen=True)
class Glow:
    radius: float = 18
    strength: float = .35
    color: str = "#D4A373"

    def __post_init__(self) -> None:
        if not 0 < self.radius <= 100 or not 0 <= self.strength <= 1:
            raise ValueError("Glow radius must be positive and strength between 0 and 1")

    def apply(self, image: Image.Image) -> Image.Image:
        base = image.convert("RGBA")
        brightness = base.convert("RGB").convert("L").point(lambda value: max(0, min(255, round((value - 160) * 2.7))))
        blurred = brightness.filter(ImageFilter.GaussianBlur(self.radius)).point(lambda value: round(value * self.strength))
        glow = Image.new("RGBA", base.size, self.color)
        glow.putalpha(blurred)
        return Image.alpha_composite(base, glow)


@dataclass(frozen=True)
class Shadow:
    dx: int = 8
    dy: int = 12
    blur: float = 12
    opacity: float = .35
    color: str = "#000000"

    def __post_init__(self) -> None:
        if not 0 <= self.blur <= 100 or not 0 <= self.opacity <= 1:
            raise ValueError("Shadow blur and opacity must be non-negative and bounded")

    def apply(self, image: Image.Image) -> Image.Image:
        source = image.convert("RGBA")
        alpha = Image.new("L", source.size)
        alpha.paste(source.getchannel("A"), (self.dx, self.dy))
        alpha = alpha.filter(ImageFilter.GaussianBlur(self.blur)).point(lambda value: round(value * self.opacity))
        shadow = Image.new("RGBA", source.size, self.color)
        shadow.putalpha(alpha)
        return Image.alpha_composite(shadow, source)


@dataclass(frozen=True)
class Grain:
    strength: float
    seed: int

    def __post_init__(self) -> None:
        if not 0 <= self.strength <= 1:
            raise ValueError("Grain strength must be between 0 and 1")

    def apply(self, image: Image.Image) -> Image.Image:
        base = image.convert("RGBA")
        rgb = base.convert("RGB")
        noise = _grain(self.seed, *base.size)
        result = Image.blend(rgb, Image.merge("RGB", (noise, noise, noise)), self.strength).convert("RGBA")
        result.putalpha(base.getchannel("A"))
        return result


@dataclass(frozen=True)
class Noise:
    strength: float
    seed: int

    def __post_init__(self) -> None:
        if not 0 <= self.strength <= 1:
            raise ValueError("Noise strength must be between 0 and 1")

    def apply(self, image: Image.Image) -> Image.Image:
        base = image.convert("RGBA")
        random = Random(self.seed)
        data = bytes(random.randrange(256) for _ in range(base.width * base.height))
        noise = Image.frombytes("L", base.size, data)
        result = Image.blend(base.convert("RGB"), Image.merge("RGB", (noise, noise, noise)), self.strength).convert("RGBA")
        result.putalpha(base.getchannel("A"))
        return result


@dataclass(frozen=True)
class Vignette:
    strength: float

    def __post_init__(self) -> None:
        if not 0 <= self.strength <= 1:
            raise ValueError("Vignette strength must be between 0 and 1")

    def apply(self, image: Image.Image) -> Image.Image:
        base = image.convert("RGBA")
        mask = _vignette(*base.size, self.strength)
        result = ImageChops.multiply(base.convert("RGB"), Image.merge("RGB", (mask, mask, mask))).convert("RGBA")
        result.putalpha(base.getchannel("A"))
        return result
