"""General editorial and device components made from ordinary scene primitives."""

from __future__ import annotations

from math import isfinite
from typing import Callable, Mapping
from random import Random

from .components import Component
from .layout import Box, grid
from .primitives import Circle, Element, Line, Path, Rectangle, RoundedRectangle, Text
from .style import get_style
from .typography import layout_text


def _size(width: float, height: float, kind: str) -> None:
    if not all(isfinite(value) and value > 0 for value in (width, height)):
        raise ValueError(f"{kind} width and height must be finite and positive")


def _label(value: str, *, x: float, y: float, width: float, style: str, name: str, role: str = "label", anchor: str = "center", color: str | None = None) -> Text:
    if not value.strip():
        raise ValueError(f"{name} label cannot be blank")
    text = Text(value, x=x, y=y, role=role, max_width=width, anchor=anchor, color=color, name=name)
    bounds = layout_text(text, get_style(style)).bounds
    if bounds[2] - bounds[0] > width + 1:
        raise ValueError(f"{name} label exceeds available width")
    return text


def Card(*, x: float, y: float, width: float, height: float, title: str, body: str = "", style: str = "blueprint", name: str = "card") -> Component:
    _size(width, height, "Card")
    if width < 180 or height < 160:
        raise ValueError("Card needs at least 180×160")
    colors = get_style(style)
    parts: dict[str, Element] = {
        "frame": RoundedRectangle(x=x, y=y, width=width, height=height, radius=16, fill=colors.background, stroke=colors.secondary, stroke_width=colors.component_stroke, name=f"{name}:frame"),
        "accent": Rectangle(x=x - width / 2 + 14, y=y - height / 2 + 48, width=5, height=60, fill=colors.accent, name=f"{name}:accent"),
        "title": _label(title, x=x - width / 2 + 40, y=y - height / 2 + 32, width=width - 80, style=style, name=f"{name}:title", role="title", anchor="left"),
    }
    if body:
        parts["body"] = _label(body, x=x - width / 2 + 40, y=y - height / 2 + 120, width=width - 80, style=style, name=f"{name}:body", role="body", anchor="left", color=colors.secondary)
    return Component(parts, Box(x - width / 2, y - height / 2, x + width / 2, y + height / 2), {"center": (x, y)})


def Computer(*, x: float, y: float, width: float, label: str = "", style: str = "blueprint", name: str = "computer") -> Component:
    if not isfinite(width) or width < 160:
        raise ValueError("Computer width must be at least 160")
    colors = get_style(style)
    h = width * .64
    parts: dict[str, Element] = {
        "monitor": RoundedRectangle(x=x, y=y - h * .11, width=width, height=h, radius=12, fill=colors.background, stroke=colors.primary, stroke_width=colors.component_stroke, name=f"{name}:monitor"),
        "screen": Rectangle(x=x, y=y - h * .13, width=width - 32, height=h - 44, fill=colors.secondary + "33", stroke=colors.secondary, stroke_width=2, name=f"{name}:screen"),
        "stand": Path(x=x, y=y + h * .39, points=((0, 0), (0, h * .25), (-width * .18, h * .25), (width * .18, h * .25)), stroke=colors.primary, stroke_width=colors.component_stroke, name=f"{name}:stand"),
    }
    if label:
        parts["label"] = _label(label, x=x, y=y + h * .79, width=width, style=style, name=f"{name}:label")
    return Component(parts, Box(x - width / 2, y - h * .61, x + width / 2, y + h * .89), {"center": (x, y), "screen": (x, y - h * .13)})


def Server(*, x: float, y: float, width: float, height: float, label: str = "", style: str = "blueprint", name: str = "server") -> Component:
    _size(width, height, "Server")
    if width < 120 or height < 180:
        raise ValueError("Server needs at least 120×180")
    colors = get_style(style)
    parts: dict[str, Element] = {"rack": RoundedRectangle(x=x, y=y, width=width, height=height, radius=10, fill=colors.background, stroke=colors.primary, stroke_width=colors.component_stroke, name=f"{name}:rack")}
    for index in range(3):
        row_y = y - height * .28 + index * height * .28
        parts[f"bay:{index}"] = Rectangle(x=x, y=row_y, width=width - 26, height=height * .19, fill=None, stroke=colors.secondary, stroke_width=2, name=f"{name}:bay:{index}")
        parts[f"status:{index}"] = Circle(x=x + width * .32, y=row_y, radius=max(4, width * .035), fill=colors.accent if index == 0 else colors.secondary, name=f"{name}:status:{index}")
    if label:
        parts["label"] = _label(label, x=x, y=y + height * .57, width=width * 1.3, style=style, name=f"{name}:label")
    return Component(parts, Box(x - width / 2, y - height / 2, x + width / 2, y + height * .7), {"center": (x, y), "top": (x, y - height / 2)})


def Terminal(*, x: float, y: float, width: float, height: float, lines: tuple[str, ...], style: str = "blueprint", name: str = "terminal") -> Component:
    _size(width, height, "Terminal")
    if width < 220 or height < 150:
        raise ValueError("Terminal needs at least 220×150")
    if len(lines) > 6:
        raise ValueError("Terminal supports at most six visible lines")
    colors = get_style(style)
    parts: dict[str, Element] = {
        "frame": RoundedRectangle(x=x, y=y, width=width, height=height, radius=12, fill=colors.background, stroke=colors.secondary, stroke_width=3, name=f"{name}:frame"),
        "header": Line(x=x - width / 2, y=y - height / 2 + 50, dx=width, dy=0, stroke=colors.secondary, stroke_width=2, name=f"{name}:header"),
        "prompt": _label("›_", x=x - width / 2 + 20, y=y - height / 2 + 9, width=70, style=style, name=f"{name}:prompt", anchor="left", color=colors.accent),
    }
    for index, line in enumerate(lines):
        parts[f"line:{index}"] = _label(line, x=x - width / 2 + 26, y=y - height / 2 + 70 + index * 46, width=width - 52, style=style, name=f"{name}:line:{index}", anchor="left", color=colors.primary)
    return Component(parts, Box(x - width / 2, y - height / 2, x + width / 2, y + height / 2), {"center": (x, y)})


def Browser(*, x: float, y: float, width: float, height: float, title: str, style: str = "blueprint", name: str = "browser") -> Component:
    _size(width, height, "Browser")
    if width < 240 or height < 180:
        raise ValueError("Browser needs at least 240×180")
    colors = get_style(style)
    parts: dict[str, Element] = {
        "frame": RoundedRectangle(x=x, y=y, width=width, height=height, radius=12, fill=colors.background, stroke=colors.primary, stroke_width=3, name=f"{name}:frame"),
        "chrome": Line(x=x - width / 2, y=y - height / 2 + 54, dx=width, dy=0, stroke=colors.secondary, stroke_width=2, name=f"{name}:chrome"),
        "title": _label(title, x=x, y=y - height / 2 + 10, width=width - 120, style=style, name=f"{name}:title", anchor="center"),
        "content": Rectangle(x=x, y=y + 25, width=width - 46, height=height - 110, fill=None, stroke=colors.secondary, stroke_width=2, name=f"{name}:content"),
    }
    for index in range(3):
        parts[f"dot:{index}"] = Circle(x=x - width / 2 + 24 + index * 21, y=y - height / 2 + 28, radius=5, fill=colors.accent if index == 0 else colors.secondary, name=f"{name}:dot:{index}")
    return Component(parts, Box(x - width / 2, y - height / 2, x + width / 2, y + height / 2), {"center": (x, y), "content": (x, y + 25)})


def Graph(*, nodes: Mapping[str, tuple[float, float]], edges: tuple[tuple[str, str], ...], style: str = "blueprint", name: str = "graph", radius: float = 18) -> Component:
    if not nodes or radius <= 0:
        raise ValueError("Graph needs nodes and positive radius")
    if any(not key.strip() or len(point) != 2 or not all(isfinite(value) for value in point) for key, point in nodes.items()):
        raise ValueError("Graph nodes need names and finite positions")
    if any(a not in nodes or b not in nodes or a == b for a, b in edges):
        raise ValueError("Graph edges must join distinct known nodes")
    colors = get_style(style)
    parts: dict[str, Element] = {}
    for index, (a, b) in enumerate(edges):
        ax, ay = nodes[a]
        bx, by = nodes[b]
        parts[f"edge:{index}"] = Path(x=ax, y=ay, points=((0, 0), (bx - ax, by - ay)), stroke=colors.secondary, stroke_width=colors.component_stroke, name=f"{name}:edge:{index}")
    for key, (px, py) in nodes.items():
        parts[f"node:{key}"] = Circle(x=px, y=py, radius=radius, fill=colors.background, stroke=colors.accent, stroke_width=3, name=f"{name}:node:{key}")
    xs, ys = [point[0] for point in nodes.values()], [point[1] for point in nodes.values()]
    return Component(parts, Box(min(xs) - radius, min(ys) - radius, max(xs) + radius, max(ys) + radius), dict(nodes))


def Chart(*, box: Box, values: tuple[float, ...], labels: tuple[str, ...], style: str = "blueprint", name: str = "chart") -> Component:
    if not values or len(values) != len(labels) or len(values) > 12:
        raise ValueError("Chart needs 1–12 values with matching labels")
    if any(not isfinite(value) or value < 0 for value in values) or max(values) <= 0:
        raise ValueError("Chart values must be finite, non-negative, and include a positive value")
    colors = get_style(style)
    slot = box.width / len(values)
    if slot < 55 or box.height < 150:
        raise ValueError("Chart box is too small for values")
    baseline = box.bottom - 55
    usable = box.height - 100
    parts: dict[str, Element] = {"baseline": Line(x=box.left, y=baseline, dx=box.width, dy=0, stroke=colors.secondary, stroke_width=2, name=f"{name}:baseline")}
    anchors = {}
    for index, (value, label) in enumerate(zip(values, labels)):
        px = box.left + (index + .5) * slot
        bar_height = max(2, usable * value / max(values))
        parts[f"bar:{index}"] = Rectangle(x=px, y=baseline - bar_height / 2, width=slot * .58, height=bar_height, fill=colors.accent if index == values.index(max(values)) else colors.secondary, name=f"{name}:bar:{index}")
        parts[f"value:{index}"] = _label(f"{value:g}", x=px, y=baseline - bar_height - 50, width=slot - 8, style=style, name=f"{name}:value:{index}", role="annotation", color=colors.primary)
        parts[f"label:{index}"] = _label(label, x=px, y=baseline + 12, width=slot - 8, style=style, name=f"{name}:label:{index}", role="annotation")
        anchors[f"bar:{index}"] = (px, baseline - bar_height)
    return Component(parts, box, anchors)


def Quote(*, x: float, y: float, width: float, text: str, attribution: str = "", style: str = "blueprint", name: str = "quote") -> Component:
    if not isfinite(width) or width < 240:
        raise ValueError("Quote width must be at least 240")
    colors = get_style(style)
    parts: dict[str, Element] = {
        "rule": Rectangle(x=x - width / 2 + 3, y=y, width=6, height=260, fill=colors.accent, name=f"{name}:rule"),
        "text": _label(text, x=x - width / 2 + 30, y=y - 130, width=width - 45, style=style, name=f"{name}:text", role="headline", anchor="left"),
    }
    if attribution:
        parts["attribution"] = _label(attribution, x=x - width / 2 + 30, y=y + 166, width=width - 45, style=style, name=f"{name}:attribution", role="annotation", anchor="left", color=colors.secondary)
    return Component(parts, Box(x - width / 2, y - 140, x + width / 2, y + 220), {"center": (x, y)})


def Label(*, x: float, y: float, text: str, width: float = 320, style: str = "blueprint", name: str = "label") -> Component:
    colors = get_style(style)
    parts: dict[str, Element] = {
        "tick": Rectangle(x=x, y=y + 17, width=4, height=34, fill=colors.accent, name=f"{name}:tick"),
        "text": _label(text, x=x + 17, y=y, width=width - 17, style=style, name=f"{name}:text", role="annotation", anchor="left"),
    }
    return Component(parts, Box(x, y, x + width, y + 42), {"left": (x, y), "center": (x + width / 2, y + 21)})


def Badge(*, x: float, y: float, text: str, width: float = 180, style: str = "blueprint", name: str = "badge") -> Component:
    if not isfinite(width) or width < 80:
        raise ValueError("Badge width must be at least 80")
    colors = get_style(style)
    parts: dict[str, Element] = {
        "frame": RoundedRectangle(x=x, y=y, width=width, height=64, radius=32, fill=colors.background, stroke=colors.accent, stroke_width=2, name=f"{name}:frame"),
        "text": _label(text, x=x, y=y - 18, width=width - 24, style=style, name=f"{name}:text", role="label", color=colors.accent),
    }
    return Component(parts, Box(x - width / 2, y - 32, x + width / 2, y + 32), {"center": (x, y)})


def ObjectGrid(*, box: Box, rows: int, columns: int, seed: int, item_factory: Callable[[int, float, float, int], Component]) -> Component:
    """Repeat a component factory at cell centers with a stable seed for each item."""
    if type(seed) is not int:
        raise ValueError("ObjectGrid seed must be an integer")
    cells = grid(box, rows=rows, columns=columns)
    random = Random(seed)
    parts: dict[str, Element] = {}
    anchors: dict[str, tuple[float, float]] = {}
    for index, cell in enumerate(cells):
        x, y = cell.center
        component = item_factory(index, x, y, random.getrandbits(63))
        if not isinstance(component, Component):
            raise TypeError("ObjectGrid item_factory must return a Component")
        anchors[f"item:{index}"] = (x, y)
        for part_name, element in component.parts.items():
            parts[f"item:{index}:{part_name}"] = element
    return Component(parts, box, anchors)
