"""Direct timestamp rendering to a fresh Cairo surface."""

from __future__ import annotations

from io import BytesIO
from math import pi
from random import Random

import cairocffi as cairo
from PIL import Image, ImageDraw, ImageFont

from .primitives import Circle, Rectangle, Text
from .scene import EvaluatedElement, PortraitScene
from .style import Style, get_style


class RenderError(RuntimeError):
    pass


def _rgba(value: str, opacity: float = 1.0) -> tuple[float, float, float, float]:
    if not value.startswith("#") or len(value) not in (7, 9):
        raise ValueError(f"Color {value!r} must be #RRGGBB or #RRGGBBAA")
    try:
        channels = tuple(int(value[index : index + 2], 16) / 255 for index in range(1, len(value), 2))
    except ValueError as exc:
        raise ValueError(f"Color {value!r} contains invalid hex digits") from exc
    red, green, blue = channels[:3]
    alpha = channels[3] if len(channels) == 4 else 1.0
    return red, green, blue, alpha * opacity


def _set_color(context: cairo.Context, color: str, opacity: float) -> None:
    context.set_source_rgba(*_rgba(color, opacity))


def _paint_background(context: cairo.Context, scene: PortraitScene, style: Style) -> None:
    _set_color(context, style.background, 1)
    context.paint()
    random = Random(scene.seed)
    for x in range(0, scene.width + 1, 90):
        context.move_to(x + 0.5, 0)
        context.line_to(x + 0.5, scene.height)
        _set_color(context, style.secondary, random.uniform(0.105, 0.18))
        context.set_line_width(2.5 if x % 360 else 3.5)
        context.stroke()
    for y in range(0, scene.height + 1, 90):
        context.move_to(0, y + 0.5)
        context.line_to(scene.width, y + 0.5)
        _set_color(context, style.secondary, random.uniform(0.105, 0.18))
        context.set_line_width(2.5 if y % 360 else 3.5)
        context.stroke()


def _draw_geometry(context: cairo.Context, state: EvaluatedElement, style: Style) -> None:
    element = state.element
    if isinstance(element, Rectangle):
        left = state.x - element.width / 2 if element.anchor == "center" else state.x
        top = state.y - element.height / 2 if element.anchor == "center" else state.y
        context.rectangle(left, top, element.width, element.height)
    elif isinstance(element, Circle):
        context.arc(state.x, state.y, element.radius, 0, 2 * pi)
    else:
        raise TypeError(f"Unsupported geometry {type(element).__name__}")
    fill = element.fill
    stroke = element.stroke
    if fill is None and stroke is None:
        fill = style.primary
    if fill is not None:
        _set_color(context, fill, state.opacity)
        if stroke is not None:
            context.fill_preserve()
        else:
            context.fill()
    if stroke is not None:
        _set_color(context, stroke, state.opacity)
        context.set_line_width(element.stroke_width)
        context.stroke()


def _wrap_lines(value: str, font: ImageFont.FreeTypeFont, max_width: float | None) -> list[str]:
    if max_width is None:
        return value.split("\n")
    lines: list[str] = []
    for paragraph in value.split("\n"):
        if not paragraph:
            lines.append("")
            continue
        line = ""
        for word in paragraph.split():
            proposal = f"{line} {word}" if line else word
            if font.getlength(proposal) <= max_width:
                line = proposal
                continue
            if line:
                lines.append(line)
                line = ""
            if font.getlength(word) <= max_width:
                line = word
                continue
            chunk = ""
            for character in word:
                if chunk and font.getlength(chunk + character) > max_width:
                    lines.append(chunk)
                    chunk = character
                else:
                    chunk += character
            line = chunk
        lines.append(line)
    return lines


def _draw_text(context: cairo.Context, state: EvaluatedElement, style: Style) -> None:
    element = state.element
    assert isinstance(element, Text)
    font_path, size = style.font_for(element.role)
    if not font_path.is_file():
        raise FileNotFoundError(f"Bundled font {font_path} is missing; reinstall motion-studio")
    font = ImageFont.truetype(font_path, size)
    lines = _wrap_lines(element.value, font, element.max_width)
    line_step = size * element.line_height
    _set_color(context, element.color or style.primary, state.opacity)
    for index, line in enumerate(lines):
        if not line:
            continue
        bbox = font.getbbox(line)
        width = max(1, bbox[2] - bbox[0])
        height = max(1, bbox[3] - bbox[1])
        mask = Image.new("L", (width, height))
        ImageDraw.Draw(mask).text((-bbox[0], -bbox[1]), line, fill=255, font=font)
        stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_A8, width)
        data = bytearray(stride * height)
        source = mask.tobytes()
        for row in range(height):
            data[row * stride : row * stride + width] = source[row * width : (row + 1) * width]
        surface = cairo.ImageSurface(cairo.FORMAT_A8, width, height, data, stride)
        if element.anchor == "left":
            left = state.x
        elif element.anchor == "right":
            left = state.x - width
        else:
            left = state.x - width / 2
        context.mask_surface(surface, left, state.y + index * line_step)


def render_frame(
    scene: PortraitScene,
    time: float,
    *,
    width: int | None = None,
    height: int | None = None,
    debug_safe: bool = False,
) -> Image.Image:
    output_width = scene.width if width is None else width
    output_height = scene.height if height is None else height
    if output_width <= 0 or output_height <= 0:
        raise ValueError("output dimensions must be positive")
    if output_width * scene.height != output_height * scene.width:
        raise ValueError("output resolution must preserve the scene aspect ratio")
    style = get_style(scene.style)
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, output_width, output_height)
    context = cairo.Context(surface)
    context.scale(output_width / scene.width, output_height / scene.height)
    _paint_background(context, scene, style)
    for state in scene.elements_at(time):
        if state.opacity <= 0:
            continue
        context.save()
        try:
            if isinstance(state.element, Text):
                _draw_text(context, state, style)
            else:
                _draw_geometry(context, state, style)
        except Exception as exc:
            label = state.element.name or type(state.element).__name__
            raise RenderError(f'Failed to render element "{label}" at t={time:.3f}s: {exc}') from exc
        finally:
            context.restore()
    if debug_safe:
        left, top, right, bottom = scene.content_box
        context.rectangle(left, top, right - left, bottom - top)
        _set_color(context, style.accent, 0.65)
        context.set_line_width(2)
        context.set_dash([12, 10])
        context.stroke()
    output = BytesIO()
    surface.write_to_png(output)
    output.seek(0)
    with Image.open(output) as image:
        return image.convert("RGBA")
