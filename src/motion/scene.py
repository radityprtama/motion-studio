"""Portrait scene definitions and direct timestamp evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from pathlib import Path

from .animation import Animation
from .primitives import LAYER_ORDER, Element


@dataclass(frozen=True)
class EvaluatedElement:
    element: Element
    x: float
    y: float
    opacity: float


class PortraitScene:
    def __init__(
        self,
        *,
        duration: float,
        fps: int = 30,
        seed: int = 0,
        style: str = "blueprint",
        width: int = 1080,
        height: int = 1920,
        safe_top: int = 120,
        safe_bottom: int = 220,
        content_margin: int = 90,
    ) -> None:
        if not isfinite(duration) or duration <= 0:
            raise ValueError("scene duration must be finite and positive")
        if fps <= 0 or width <= 0 or height <= 0:
            raise ValueError("scene FPS and dimensions must be positive")
        if min(safe_top, safe_bottom, content_margin) < 0:
            raise ValueError("safe zones must be non-negative")
        if safe_top + safe_bottom >= height or 2 * content_margin >= width:
            raise ValueError("safe zones leave no content area")
        self.duration = duration
        self.fps = fps
        self.seed = seed
        self.style = style
        self.width = width
        self.height = height
        self.safe_top = safe_top
        self.safe_bottom = safe_bottom
        self.content_margin = content_margin
        self._elements: list[Element] = []
        self._names: set[str] = set()
        self._tracks: dict[tuple[Element, str], list[Animation]] = {}

    @property
    def content_box(self) -> tuple[int, int, int, int]:
        return (
            self.content_margin,
            self.safe_top,
            self.width - self.content_margin,
            self.height - self.safe_bottom,
        )

    def add(self, element: Element) -> Element:
        if element in self._elements:
            raise ValueError("element has already been added to this scene")
        if element.name is not None:
            if element.name in self._names:
                raise ValueError(f"Duplicate element name {element.name!r}")
            self._names.add(element.name)
        self._elements.append(element)
        return element

    def animate(self, element: Element, animation: Animation) -> None:
        if element not in self._elements:
            raise ValueError("animate requires an element already added to the scene")
        for channel in animation.channels:
            track = self._tracks.get((element, channel), [])
            for existing in track:
                if animation.start < existing.start + existing.duration and existing.start < animation.start + animation.duration:
                    label = element.name or type(element).__name__
                    raise ValueError(f"Animations overlap on {label}.{channel}")
        for channel in animation.channels:
            track = self._tracks.setdefault((element, channel), [])
            track.append(animation)
            track.sort(key=lambda item: item.start)

    def _property_at(self, element: Element, channel: str, time: float) -> float:
        base = getattr(element, channel)
        track = self._tracks.get((element, channel), [])
        if not track:
            return base
        selected = track[0]
        for animation in track:
            if animation.start <= time:
                selected = animation
            else:
                break
        return selected.value(channel, time, base)

    def elements_at(self, time: float) -> list[EvaluatedElement]:
        if not isfinite(time) or not 0 <= time <= self.duration:
            raise ValueError(f"time must be within 0 and scene duration {self.duration:g}s")
        ordered = sorted(
            enumerate(self._elements),
            key=lambda item: (LAYER_ORDER.index(item[1].layer), item[1].z_index, item[0]),
        )
        return [
            EvaluatedElement(
                element=element,
                x=self._property_at(element, "x", time),
                y=self._property_at(element, "y", time),
                opacity=self._property_at(element, "opacity", time),
            )
            for _, element in ordered
        ]

    def render_still(self, *, time: float, output: str | Path, width: int | None = None, height: int | None = None, overwrite: bool = False) -> Path:
        from .export import render_still

        return render_still(self, time=time, output=Path(output), width=width, height=height, overwrite=overwrite)

    def render_preview(self, *, output: str | Path, width: int = 360, height: int = 640, fps: int = 15, overwrite: bool = False) -> Path:
        from .export import render_video

        return render_video(self, output=Path(output), width=width, height=height, fps=fps, overwrite=overwrite)

    def render(self, *, output: str | Path, width: int | None = None, height: int | None = None, fps: int | None = None, overwrite: bool = False) -> Path:
        from .export import render_video

        return render_video(self, output=Path(output), width=width or self.width, height=height or self.height, fps=fps or self.fps, overwrite=overwrite)
