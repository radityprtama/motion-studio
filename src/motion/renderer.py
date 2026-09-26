"""Direct timestamp rendering to a fresh Cairo surface."""

from __future__ import annotations

from io import BytesIO
from math import pi, radians
from random import Random

import cairocffi as cairo
from PIL import Image

from .animation import MaskReveal, Reveal
from .camera import CameraState
from .primitives import Circle, Path as MotionPath, RadialLight, Rectangle, Text, partial_points
from .scene import EvaluatedElement, PortraitScene
from .style import Style, get_style
from .typography import layout_text, line_mask


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
    if style.background_treatment == "cinematic":
        _paint_cinematic_background(context, scene, style)
        return
    _set_color(context, style.background, 1)
    context.paint()
    random = Random(scene.seed)
    for x in range(0, scene.width + 1, 90):
        context.move_to(x + 0.5, 0)
        context.line_to(x + 0.5, scene.height)
        _set_color(context, style.grid_color, random.uniform(0.105, 0.18) * style.grid_opacity)
        context.set_line_width(2.5 if x % 360 else 3.5)
        context.stroke()
    for y in range(0, scene.height + 1, 90):
        context.move_to(0, y + 0.5)
        context.line_to(scene.width, y + 0.5)
        _set_color(context, style.grid_color, random.uniform(0.105, 0.18) * style.grid_opacity)
        context.set_line_width(2.5 if y % 360 else 3.5)
        context.stroke()


def _paint_cinematic_background(context: cairo.Context, scene: PortraitScene, style: Style) -> None:
    _set_color(context, style.background, 1)
    context.paint()
    gradient = cairo.RadialGradient(
        scene.width * 0.48, scene.height * 0.42, 0,
        scene.width * 0.48, scene.height * 0.42, scene.height * 0.75,
    )
    gradient.add_color_stop_rgba(0, *_rgba("#15283A"))
    gradient.add_color_stop_rgba(0.55, *_rgba("#0D1C2B"))
    gradient.add_color_stop_rgba(1, *_rgba(style.background))
    context.set_source(gradient)
    context.paint()
    horizon = cairo.LinearGradient(0, scene.height * 0.55, 0, scene.height)
    horizon.add_color_stop_rgba(0, 0, 0, 0, 0)
    horizon.add_color_stop_rgba(1, 0, 0, 0, 0.2)
    context.set_source(horizon)
    context.paint()


def _draw_geometry(context: cairo.Context, state: EvaluatedElement, style: Style, *, local: bool = False) -> None:
    element = state.element
    x = 0.0 if local else state.x
    y = 0.0 if local else state.y
    if isinstance(element, MotionPath):
        _draw_path(context, state, style, x=x, y=y)
        return
    if isinstance(element, RadialLight):
        center = _rgba(element.center_color, state.opacity * element.intensity)
        edge = _rgba(element.edge_color, state.opacity * element.intensity)
        glow = cairo.RadialGradient(x, y, 0, x, y, element.radius)
        glow.add_color_stop_rgba(0, *center)
        glow.add_color_stop_rgba(0.42, center[0], center[1], center[2], center[3] * 0.35)
        glow.add_color_stop_rgba(1, *edge)
        context.arc(x, y, element.radius, 0, 2 * pi)
        context.set_source(glow)
        context.fill()
        return
    if isinstance(element, Rectangle):
        left = x - element.width / 2 if element.anchor == "center" else x
        top = y - element.height / 2 if element.anchor == "center" else y
        context.rectangle(left, top, element.width, element.height)
    elif isinstance(element, Circle):
        context.arc(x, y, element.radius, 0, 2 * pi)
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


def _draw_path(context: cairo.Context, state: EvaluatedElement, style: Style, *, x: float, y: float) -> None:
    element = state.element
    assert isinstance(element, MotionPath)
    if state.draw_progress <= 0:
        return
    visible = partial_points(element.points, state.draw_progress, closed=element.closed)
    context.new_path()
    context.move_to(x + visible[0][0], y + visible[0][1])
    for point_x, point_y in visible[1:]:
        context.line_to(x + point_x, y + point_y)
    if element.closed and state.draw_progress >= 1:
        context.close_path()
    if element.fill is not None and state.draw_progress >= 1:
        _set_color(context, element.fill, state.opacity)
        context.fill_preserve()
    _set_color(context, element.stroke or style.primary, state.opacity)
    context.set_line_width(element.stroke_width)
    context.stroke()


def _element_bounds(state: EvaluatedElement, style: Style, *, local: bool) -> tuple[float, float, float, float]:
    element = state.element
    x = 0.0 if local else state.x
    y = 0.0 if local else state.y
    if isinstance(element, Rectangle):
        left = x - element.width / 2 if element.anchor == "center" else x
        top = y - element.height / 2 if element.anchor == "center" else y
        return left, top, left + element.width, top + element.height
    if isinstance(element, Circle):
        return x - element.radius, y - element.radius, x + element.radius, y + element.radius
    if isinstance(element, RadialLight):
        return x - element.radius, y - element.radius, x + element.radius, y + element.radius
    if isinstance(element, MotionPath):
        xs = [point[0] for point in element.points]
        ys = [point[1] for point in element.points]
        padding = element.stroke_width / 2 + 1
        return x + min(xs) - padding, y + min(ys) - padding, x + max(xs) + padding, y + max(ys) + padding
    if isinstance(element, Text):
        return layout_text(element, style, local=local, x=x, y=y).bounds
    raise TypeError(f"Unsupported element {type(element).__name__}")


def _clip_direction(context: cairo.Context, state: EvaluatedElement, style: Style, *, local: bool) -> None:
    reveal = state.reveal
    assert isinstance(reveal, Reveal)
    left, top, right, bottom = _element_bounds(state, style, local=local)
    amount = state.reveal_progress
    width = right - left
    height = bottom - top
    if reveal.direction == "left":
        context.rectangle(left, top, width * amount, height)
    elif reveal.direction == "right":
        context.rectangle(right - width * amount, top, width * amount, height)
    elif reveal.direction == "top":
        context.rectangle(left, top, width, height * amount)
    else:
        context.rectangle(left, bottom - height * amount, width, height * amount)
    context.clip()


def _clip_mask(context: cairo.Context, state: EvaluatedElement) -> None:
    reveal = state.reveal
    assert isinstance(reveal, MaskReveal)
    mask = reveal.mask
    amount = state.reveal_progress
    matrix = context.get_matrix()
    context.translate(mask.x, mask.y)
    context.rotate(radians(mask.rotation))
    context.scale(mask.scale_x, mask.scale_y)
    if isinstance(mask, Rectangle):
        width = mask.width * amount
        height = mask.height * amount
        if mask.anchor == "center":
            context.rectangle(-width / 2, -height / 2, width, height)
        else:
            context.rectangle(0, 0, width, height)
    else:
        assert isinstance(mask, Circle)
        context.arc(0, 0, mask.radius * amount, 0, 2 * pi)
    context.clip()
    context.set_matrix(matrix)


def _apply_camera(context: cairo.Context, scene: PortraitScene, camera: CameraState) -> None:
    if camera.x == scene.width / 2 and camera.y == scene.height / 2 and camera.zoom == 1 and camera.rotation == 0:
        return
    context.translate(scene.width / 2, scene.height / 2)
    context.rotate(-radians(camera.rotation))
    context.scale(camera.zoom, camera.zoom)
    context.translate(-camera.x, -camera.y)


def _draw_text(context: cairo.Context, state: EvaluatedElement, style: Style, *, local: bool = False) -> None:
    element = state.element
    assert isinstance(element, Text)
    x = 0.0 if local else state.x
    y = 0.0 if local else state.y
    layout = layout_text(element, style, local=local, x=x, y=y)
    token = style.text_token(element.role)
    _set_color(context, element.color or token.color or style.primary, state.opacity)
    for line in layout.lines:
        if not line.value:
            continue
        mask = line_mask(line, layout.font, layout.letter_spacing)
        width, height = mask.size
        stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_A8, width)
        data = bytearray(stride * height)
        source = mask.tobytes()
        for row in range(height):
            data[row * stride : row * stride + width] = source[row * width : (row + 1) * width]
        surface = cairo.ImageSurface(cairo.FORMAT_A8, width, height, data, stride)
        context.mask_surface(surface, line.left, line.top)


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
    camera = scene.camera.evaluate(time)
    for state in scene.elements_at(time):
        if state.opacity <= 0 or (state.reveal is not None and state.reveal_progress <= 0):
            continue
        context.save()
        try:
            if state.element.layer in ("environment", "content", "foreground"):
                _apply_camera(context, scene, camera)
            if isinstance(state.reveal, MaskReveal):
                _clip_mask(context, state)
            transformed = state.scale_x != 1 or state.scale_y != 1 or state.rotation != 0
            if transformed:
                context.translate(state.x, state.y)
                context.rotate(radians(state.rotation))
                context.scale(state.scale_x, state.scale_y)
            if isinstance(state.reveal, Reveal) and state.reveal_progress < 1:
                _clip_direction(context, state, style, local=transformed)
            if isinstance(state.element, Text):
                _draw_text(context, state, style, local=transformed)
            else:
                _draw_geometry(context, state, style, local=transformed)
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
