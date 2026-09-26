"""Immutable visual definitions used by a scene."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
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
    layer: Layer = "content"
    z_index: int = 0

    def __post_init__(self) -> None:
        if not isfinite(self.x) or not isfinite(self.y):
            raise ValueError("element coordinates must be finite")
        if not isfinite(self.opacity) or not 0 <= self.opacity <= 1:
            raise ValueError("element opacity must be between 0 and 1")
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
    role: Literal["headline", "body", "annotation"] = "body"
    color: str | None = None
    max_width: float | None = None
    anchor: Literal["left", "center", "right"] = "center"
    line_height: float = 1.18

    def __post_init__(self) -> None:
        super().__post_init__()
        if not isinstance(self.value, str):
            raise TypeError("Text value must be a string")
        if self.role not in ("headline", "body", "annotation"):
            raise ValueError("Text role must be headline, body, or annotation")
        if self.max_width is not None and (not isfinite(self.max_width) or self.max_width <= 0):
            raise ValueError("Text max_width must be finite and positive")
        if not isfinite(self.line_height) or self.line_height <= 0:
            raise ValueError("Text line_height must be finite and positive")
        if self.anchor not in ("left", "center", "right"):
            raise ValueError("Text anchor must be left, center, or right")
