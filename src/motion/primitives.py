"""Immutable visual definitions used by a scene."""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot, isfinite
from typing import Literal


Layer = Literal["background", "environment", "content", "foreground", "overlay", "captions"]
LAYER_ORDER: tuple[Layer, ...] = (
    "background", "environment", "content", "foreground", "overlay", "captions"
)


@dataclass(frozen=True, eq=False, kw_only=True)
class Element:
    x: float
    y: float
    name: str | None = None
    opacity: float = 1.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    rotation: float = 0.0
    layer: Layer = "content"
    z_index: int = 0

    def __post_init__(self) -> None:
        if not isfinite(self.x) or not isfinite(self.y):
            raise ValueError("element coordinates must be finite")
        if not isfinite(self.opacity) or not 0 <= self.opacity <= 1:
            raise ValueError("element opacity must be between 0 and 1")
        if not isfinite(self.scale_x) or not isfinite(self.scale_y) or self.scale_x <= 0 or self.scale_y <= 0:
            raise ValueError("element scales must be finite and positive")
        if not isfinite(self.rotation):
            raise ValueError("element rotation must be finite degrees")
        if self.layer not in LAYER_ORDER:
            raise ValueError(f"Unknown layer {self.layer!r}; choose from {LAYER_ORDER}")
        if self.name is not None and not self.name.strip():
            raise ValueError("element name cannot be blank")


@dataclass(frozen=True, eq=False, kw_only=True)
class Rectangle(Element):
    width: float
    height: float
    fill: str | None = None
    stroke: str | None = None
    stroke_width: float = 2.0
    anchor: Literal["center", "top_left"] = "center"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not isfinite(self.width) or not isfinite(self.height) or self.width <= 0 or self.height <= 0:
            raise ValueError("rectangle width and height must be finite and positive")
        if not isfinite(self.stroke_width) or self.stroke_width < 0:
            raise ValueError("stroke_width must be finite and non-negative")
        if self.anchor not in ("center", "top_left"):
            raise ValueError("rectangle anchor must be center or top_left")


@dataclass(frozen=True, eq=False, kw_only=True)
class Circle(Element):
    radius: float
    fill: str | None = None
    stroke: str | None = None
    stroke_width: float = 2.0

    def __post_init__(self) -> None:
        super().__post_init__()
        if not isfinite(self.radius) or self.radius <= 0:
            raise ValueError("circle radius must be finite and positive")
        if not isfinite(self.stroke_width) or self.stroke_width < 0:
            raise ValueError("stroke_width must be finite and non-negative")


@dataclass(frozen=True, eq=False)
class Text(Element):
    value: str
    role: Literal["display", "headline", "title", "body", "caption", "annotation", "label"] = "body"
    color: str | None = None
    max_width: float | None = None
    anchor: Literal["left", "center", "right"] = "center"
    line_height: float | None = None
    font_size: int | None = None
    font_weight: Literal["regular", "semibold"] | None = None
    letter_spacing: float = 0.0

    def __post_init__(self) -> None:
        super().__post_init__()
        if not isinstance(self.value, str):
            raise TypeError("Text value must be a string")
        if self.role not in ("display", "headline", "title", "body", "caption", "annotation", "label"):
            raise ValueError(f"Unknown Text role {self.role!r}")
        if self.max_width is not None and (not isfinite(self.max_width) or self.max_width <= 0):
            raise ValueError("Text max_width must be finite and positive")
        if self.line_height is not None and (not isfinite(self.line_height) or self.line_height <= 0):
            raise ValueError("Text line_height must be finite and positive")
        if self.font_size is not None and (not isinstance(self.font_size, int) or self.font_size <= 0):
            raise ValueError("Text font_size must be a positive integer")
        if self.font_weight not in (None, "regular", "semibold"):
            raise ValueError("Text font_weight must be regular or semibold")
        if not isfinite(self.letter_spacing):
            raise ValueError("Text letter_spacing must be finite")
        if self.anchor not in ("left", "center", "right"):
            raise ValueError("Text anchor must be left, center, or right")


def partial_points(
    points: tuple[tuple[float, float], ...], amount: float, *, closed: bool = False
) -> tuple[tuple[float, float], ...]:
    """Return the portion of a polyline visible at a length fraction."""
    segments = points + ((points[0],) if closed else ())
    lengths = [hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(segments, segments[1:])]
    total = sum(lengths)
    if total <= 0:
        raise ValueError("Path must have positive total length")
    if amount <= 0:
        return (points[0],)
    if amount >= 1:
        return segments
    remaining = amount * total
    visible = [points[0]]
    for (start, end), length in zip(zip(segments, segments[1:]), lengths):
        if length == 0:
            continue
        if remaining >= length:
            visible.append(end)
            remaining -= length
            continue
        fraction = remaining / length
        visible.append((start[0] + (end[0] - start[0]) * fraction, start[1] + (end[1] - start[1]) * fraction))
        break
    return tuple(visible)


@dataclass(frozen=True, eq=False, kw_only=True)
class Path(Element):
    points: tuple[tuple[float, float], ...]
    closed: bool = False
    stroke: str | None = None
    stroke_width: float = 3.0
    fill: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        points = tuple(tuple(point) for point in self.points)
        object.__setattr__(self, "points", points)
        if len(points) < 2:
            raise ValueError("Path requires at least two points")
        if any(len(point) != 2 or not all(isfinite(value) for value in point) for point in points):
            raise ValueError("Path points must contain finite x and y coordinates")
        if not isfinite(self.stroke_width) or self.stroke_width <= 0:
            raise ValueError("Path stroke_width must be finite and positive")
        if self.fill is not None and not self.closed:
            raise ValueError("Path fill requires a closed path")
        if sum(hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:])) == 0:
            raise ValueError("Path must have positive total length")
