"""Semantic drawings assembled from named, animatable primitives."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from typing import Mapping

from .layout import Box
from .primitives import Circle, Element, Path, Rectangle, Text
from .scene import PortraitScene
from .style import Style, get_style
from .typography import layout_text


@dataclass(frozen=True)
class Component:
    parts: Mapping[str, Element]
    bounds: Box
    anchors: Mapping[str, tuple[float, float]]

    def __post_init__(self) -> None:
        if not self.parts:
            raise ValueError("Component needs at least one part")
        names = [part.name for part in self.parts.values()]
        if any(name is None for name in names) or len(set(names)) != len(names):
            raise ValueError("Component parts need unique names")
        object.__setattr__(self, "parts", MappingProxyType(dict(self.parts)))
        object.__setattr__(self, "anchors", MappingProxyType(dict(self.anchors)))

    def add_to(self, scene: PortraitScene) -> Component:
        for part in self.parts.values():
            scene.add(part)
        return self


def _number(value: float, label: str, minimum: float = 0) -> None:
    if not isfinite(value) or value <= minimum:
        raise ValueError(f"{label} must be finite and greater than {minimum:g}; got {value!r}")


def _prefix(name: str | None, kind: str, x: float, y: float) -> str:
    result = name if name is not None else f"{kind}_{x:g}_{y:g}"
    if not result.strip():
        raise ValueError(f"{kind} name cannot be blank")
    return result


def _fit_label(label: str, text: Text, style: Style, width: float, kind: str) -> None:
    if not label.strip():
        raise ValueError(f"{kind} label cannot be blank")
    bounds = layout_text(text, style).bounds
    measured = bounds[2] - bounds[0]
    if measured > width:
        raise ValueError(f"{kind} label {label!r} needs {measured:g}px; available {width:g}px")


def Folder(
    *, x: float, y: float, width: float, label: str, style: str = "blueprint",
    name: str | None = None, height: float | None = None,
) -> Component:
    """Return a project folder with independent body, tab, and label handles."""
    _number(width, "Folder width", 220)
    height = width * 0.56 if height is None else height
    _number(height, "Folder height", 150)
    colors = get_style(style)
    prefix = _prefix(name, "folder", x, y)
    left, top = x - width / 2, y - height / 2
    label_text = Text(label, x=left + 34, y=top + height - 86, role="annotation", anchor="left", color=colors.primary, name=f"{prefix}:label")
    _fit_label(label, label_text, colors, width - 68, "Folder")
    parts = {
        "body": Rectangle(x=x, y=y, width=width, height=height, fill=colors.background, stroke=colors.primary, stroke_width=colors.component_stroke, name=f"{prefix}:body"),
        "tab": Path(x=left, y=top, points=((0, 0), (0, -54), (min(160, width * .3), -54), (min(210, width * .38), 0)), stroke=colors.primary, stroke_width=colors.component_stroke, name=f"{prefix}:tab"),
        "label": label_text,
    }
    return Component(parts, Box(left, top - 54, left + width, top + height), {"center": (x, y), "tab_center": (left + min(160, width * .3) / 2, top - 54), "entry": (x, top - 54), "exit": (x, top + height)})


def File(
    *, x: float, y: float, width: float, height: float, label: str,
    style: str = "blueprint", name: str | None = None,
) -> Component:
    """Return a paper file with a small fold and an editable label."""
    _number(width, "File width", 60)
    _number(height, "File height", 90)
    colors = get_style(style)
    prefix = _prefix(name, "file", x, y)
    left, top = x - width / 2, y - height / 2
    fold = min(42, width * .23)
    label_text = Text(label, x=x, y=top + height - 56, role="label", anchor="center", color=colors.primary, name=f"{prefix}:label")
    _fit_label(label, label_text, colors, width - 28, "File")
    parts = {
        "body": Rectangle(x=x, y=y, width=width, height=height, fill=colors.background, stroke=colors.primary, stroke_width=colors.component_stroke, name=f"{prefix}:body"),
        "fold": Path(x=left + width, y=top, points=((-fold, 0), (-fold, fold), (0, fold)), stroke=colors.secondary, stroke_width=colors.component_stroke * .75, name=f"{prefix}:fold"),
        "label": label_text,
    }
    return Component(parts, Box(left, top, left + width, top + height), {"center": (x, y), "top": (x, top), "bottom": (x, top + height)})
