"""Direct-time contact sheets for quick composition review."""

from __future__ import annotations

from math import ceil, isfinite
from pathlib import Path
import os

from PIL import Image, ImageDraw, ImageFont

from .export import _prepare_output, _temporary_output
from .renderer import render_frame
from .scene import PortraitScene


def sample_times(scene: PortraitScene, count: int = 6) -> tuple[float, ...]:
    if count < 2:
        raise ValueError("contact sheet needs at least two samples")
    return tuple(scene.duration * index / (count - 1) for index in range(count))


def render_contact_sheet(
    scene: PortraitScene, *, times: tuple[float, ...], output: str | Path,
    width: int = 270, height: int = 480, columns: int = 3,
    overwrite: bool = False,
) -> Path:
    if not times or columns <= 0:
        raise ValueError("contact sheet needs times and positive columns")
    if any(not isfinite(time) or time < 0 or time > scene.duration for time in times):
        raise ValueError(f"contact sheet times must be within 0 and {scene.duration:g}s")
    if width <= 0 or height <= 0:
        raise ValueError("contact sheet cell size must be positive")
    output = Path(output).resolve()
    _prepare_output(output, overwrite)
    gutter, label_height = 16, 34
    rows = ceil(len(times) / columns)
    sheet = Image.new("RGB", (columns * (width + gutter) + gutter, rows * (height + label_height + gutter) + gutter), "#172431")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=18)
    for index, time in enumerate(times):
        x = gutter + (index % columns) * (width + gutter)
        y = gutter + (index // columns) * (height + label_height + gutter)
        sheet.paste(render_frame(scene, time, width=width, height=height).convert("RGB"), (x, y))
        draw.text((x + 2, y + height + 5), f"{time:.2f} s", fill="#F2EBDD", font=font)
    temporary = _temporary_output(output)
    try:
        sheet.save(temporary, format="PNG")
        if output.exists() and not overwrite:
            raise FileExistsError(f"Output {output} appeared during rendering; pass --overwrite to replace it")
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    return output
