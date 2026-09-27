"""Immutable visual definitions used by a scene."""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot, isfinite
from random import Random
from pathlib import Path as FilePath
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


@dataclass(frozen=True, eq=False, kw_only=True)
class RoundedRectangle(Rectangle):
    radius: float = 20.0

    def __post_init__(self) -> None:
        super().__post_init__()
        if not isfinite(self.radius) or not 0 <= self.radius <= min(self.width, self.height) / 2:
            raise ValueError("rounded rectangle radius must fit within its bounds")


@dataclass(frozen=True, eq=False, kw_only=True)
class Ellipse(Element):
    radius_x: float
    radius_y: float
    fill: str | None = None
    stroke: str | None = None
    stroke_width: float = 2.0

    def __post_init__(self) -> None:
        super().__post_init__()
        if not all(isfinite(value) and value > 0 for value in (self.radius_x, self.radius_y)):
            raise ValueError("ellipse radii must be finite and positive")
        if not isfinite(self.stroke_width) or self.stroke_width < 0:
            raise ValueError("ellipse stroke_width must be finite and non-negative")


@dataclass(frozen=True, eq=False, kw_only=True)
class Line(Element):
    dx: float
    dy: float
    stroke: str | None = None
    stroke_width: float = 3.0

    def __post_init__(self) -> None:
        super().__post_init__()
        if not all(isfinite(value) for value in (self.dx, self.dy)) or (self.dx == 0 and self.dy == 0):
            raise ValueError("line offset must be finite and nonzero")
        if not isfinite(self.stroke_width) or self.stroke_width <= 0:
            raise ValueError("line stroke_width must be finite and positive")


@dataclass(frozen=True, eq=False, kw_only=True)
class Image(Element):
    source: FilePath
    width: float
    height: float
    anchor: Literal["center", "top_left"] = "center"

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "source", FilePath(self.source))
        if not all(isfinite(value) and value > 0 for value in (self.width, self.height)):
            raise ValueError("image width and height must be finite and positive")
        if self.anchor not in ("center", "top_left"):
            raise ValueError("image anchor must be center or top_left")


@dataclass(frozen=True, eq=False, kw_only=True)
class SVG(Image):
    """A local, self-contained SVG rendered through CairoSVG."""

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.source.suffix.lower() != ".svg":
            raise ValueError("SVG source must have a .svg extension")


@dataclass(frozen=True, eq=False, kw_only=True)
class RadialLight(Element):
    radius: float
    center_color: str = "#D4A373AA"
    edge_color: str = "#D4A37300"
    intensity: float = 0.5

    def __post_init__(self) -> None:
        super().__post_init__()
        if not isfinite(self.radius) or self.radius <= 0:
            raise ValueError(f"RadialLight radius must be finite and positive; got {self.radius!r}")
        if not isfinite(self.intensity) or not 0 <= self.intensity <= 1:
            raise ValueError("RadialLight intensity must be between 0 and 1")
        for label, color in (("center_color", self.center_color), ("edge_color", self.edge_color)):
            if not isinstance(color, str) or not color.startswith("#") or len(color) not in (7, 9):
                raise ValueError(f"RadialLight {label} must be #RRGGBB or #RRGGBBAA")
            try:
                int(color[1:], 16)
            except ValueError as exc:
                raise ValueError(f"RadialLight {label} contains invalid hex digits") from exc


@dataclass(frozen=True)
class Particle:
    x: float
    y: float
    radius: float
    opacity: float


@dataclass(frozen=True, eq=False, kw_only=True)
class ParticleEmitter(Element):
    width: float
    height: float
    count: int
    seed: int
    radius_range: tuple[float, float] = (1.5, 4.0)
    velocity: tuple[float, float, float, float] = (-8.0, 8.0, -14.0, 4.0)
    color: str = "#829EAD"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not isfinite(self.width) or self.width <= 0:
            raise ValueError(f"ParticleEmitter width must be finite and positive; got {self.width!r}")
        if not isfinite(self.height) or self.height <= 0:
            raise ValueError(f"ParticleEmitter height must be finite and positive; got {self.height!r}")
        if not isinstance(self.count, int) or isinstance(self.count, bool) or not 1 <= self.count <= 400:
            raise ValueError("ParticleEmitter count must be between 1 and 400")
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise ValueError("ParticleEmitter seed must be an integer")
        if len(self.radius_range) != 2 or not all(isfinite(v) and v > 0 for v in self.radius_range) or self.radius_range[0] > self.radius_range[1]:
            raise ValueError("ParticleEmitter radius_range must be positive (min, max)")
        if len(self.velocity) != 4 or not all(isfinite(v) for v in self.velocity) or self.velocity[0] > self.velocity[1] or self.velocity[2] > self.velocity[3]:
            raise ValueError("ParticleEmitter velocity must be ordered (min_vx, max_vx, min_vy, max_vy)")
        if not isinstance(self.color, str) or not self.color.startswith("#") or len(self.color) not in (7, 9):
            raise ValueError("ParticleEmitter color must be #RRGGBB or #RRGGBBAA")
        try:
            int(self.color[1:], 16)
        except ValueError as exc:
            raise ValueError("ParticleEmitter color contains invalid hex digits") from exc

    def particles_at(self, time: float) -> tuple[Particle, ...]:
        if not isfinite(time) or time < 0:
            raise ValueError(f"ParticleEmitter time must be finite and non-negative; got {time!r}")
        random = Random(self.seed)
        result = []
        for _ in range(self.count):
            start_x = random.uniform(0, self.width)
            start_y = random.uniform(0, self.height)
            vx = random.uniform(self.velocity[0], self.velocity[1])
            vy = random.uniform(self.velocity[2], self.velocity[3])
            radius = random.uniform(*self.radius_range)
            opacity = random.uniform(0.3, 0.8)
            result.append(Particle(
                ((start_x + vx * time) % self.width) - self.width / 2,
                ((start_y + vy * time) % self.height) - self.height / 2,
                radius,
                opacity,
            ))
        return tuple(result)


@dataclass(frozen=True, eq=False)
class Text(Element):
    value: str
    role: Literal["display", "headline", "title", "body", "caption", "annotation", "label"] = "body"
    color: str | None = None
    max_width: float | None = None
    anchor: Literal["left", "center", "right"] = "center"
    line_height: float | None = None
    font_size: int | None = None
    font_family: Literal["sans", "mono"] | None = None
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
        if self.font_family not in (None, "sans", "mono"):
            raise ValueError("Text font_family must be sans or mono")
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
