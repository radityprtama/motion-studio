"""Measured text layout shared by drawing, clipping, and components."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, floor
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .primitives import Text
from .style import Style


@dataclass(frozen=True)
class LineLayout:
    value: str
    left: float
    top: float
    width: int
    height: int
    bbox: tuple[int, int, int, int]


@dataclass(frozen=True)
class TextLayout:
    lines: tuple[LineLayout, ...]
    bounds: tuple[float, float, float, float]
    font_path: Path
    font: ImageFont.FreeTypeFont
    letter_spacing: float


def _bbox(value: str, font: ImageFont.FreeTypeFont, spacing: float) -> tuple[int, int, int, int]:
    if not value:
        return 0, 0, 0, 0
    if spacing == 0:
        return font.getbbox(value)
    boxes = []
    for index, character in enumerate(value):
        origin = font.getlength(value[:index]) + index * spacing
        left, top, right, bottom = font.getbbox(character)
        boxes.append((origin + left, top, origin + right, bottom))
    return floor(min(box[0] for box in boxes)), min(box[1] for box in boxes), ceil(max(box[2] for box in boxes)), max(box[3] for box in boxes)


def _advance(value: str, font: ImageFont.FreeTypeFont, spacing: float) -> float:
    return font.getlength(value) + max(0, len(value) - 1) * spacing


def _wrap(value: str, font: ImageFont.FreeTypeFont, width: float | None, spacing: float) -> list[str]:
    if width is None:
        return value.split("\n")
    lines = []
    for paragraph in value.split("\n"):
        if not paragraph:
            lines.append("")
            continue
        line = ""
        for word in paragraph.split():
            proposal = f"{line} {word}" if line else word
            if _advance(proposal, font, spacing) <= width:
                line = proposal
                continue
            if line:
                lines.append(line)
                line = ""
            if _advance(word, font, spacing) <= width:
                line = word
                continue
            chunk = ""
            for character in word:
                if chunk and _advance(chunk + character, font, spacing) > width:
                    lines.append(chunk)
                    chunk = character
                else:
                    chunk += character
            line = chunk
        lines.append(line)
    return lines


def layout_text(text: Text, style: Style, *, local: bool = False, x: float | None = None, y: float | None = None) -> TextLayout:
    token = style.text_token(text.role)
    path = style.font_path(token.family, text.font_weight or token.weight)
    font = ImageFont.truetype(path, text.font_size or token.size)
    spacing = text.letter_spacing
    anchor_x = 0.0 if local else (text.x if x is None else x)
    top_y = 0.0 if local else (text.y if y is None else y)
    step = font.size * (text.line_height if text.line_height is not None else token.line_height)
    result = []
    for index, line in enumerate(_wrap(text.value, font, text.max_width, spacing)):
        bounds = _bbox(line, font, spacing)
        width = max(0, bounds[2] - bounds[0])
        height = max(0, bounds[3] - bounds[1])
        left = anchor_x if text.anchor == "left" else (anchor_x - width if text.anchor == "right" else anchor_x - width / 2)
        result.append(LineLayout(line, left, top_y + index * step, width, height, bounds))
    right = max((line.left + line.width for line in result), default=anchor_x)
    left = min((line.left for line in result), default=anchor_x)
    bottom = max((line.top + line.height for line in result), default=top_y)
    return TextLayout(tuple(result), (left, top_y, right, bottom), path, font, spacing)


def line_mask(line: LineLayout, font: ImageFont.FreeTypeFont, spacing: float) -> Image.Image:
    mask = Image.new("L", (max(1, line.width), max(1, line.height)))
    draw = ImageDraw.Draw(mask)
    if spacing == 0:
        draw.text((-line.bbox[0], -line.bbox[1]), line.value, fill=255, font=font)
    else:
        for index, character in enumerate(line.value):
            origin = font.getlength(line.value[:index]) + index * spacing
            draw.text((origin - line.bbox[0], -line.bbox[1]), character, fill=255, font=font)
    return mask
