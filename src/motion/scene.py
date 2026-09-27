"""Portrait scene definitions and direct timestamp evaluation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import isfinite
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import ProjectConfig

from .animation import Animation, DrawPath, MaskReveal, Reveal
from .audio import AudioTimeline
from .effects import Effect
from .camera import Camera
from .composition import Node, expand
from .layout import Box
from .primitives import LAYER_ORDER, Element, Line, Path as MotionPath


@dataclass(frozen=True)
class EvaluatedElement:
    element: Element
    x: float
    y: float
    opacity: float
    scale_x: float
    scale_y: float
    rotation: float
    draw_progress: float
    reveal_progress: float
    reveal: Reveal | MaskReveal | None


class PortraitScene:
    @classmethod
    def from_config(cls, config: ProjectConfig, *, duration: float, **overrides: object) -> PortraitScene:
        """Construct in design coordinates; explicit scene settings win over project defaults."""
        values: dict[str, object] = dict(duration=duration, style=config.default_style, width=config.render.width, height=config.render.height, fps=config.render.fps)
        values.update(overrides)
        return cls(**values)

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
        self.camera = Camera(x=width / 2, y=height / 2)
        self.audio = AudioTimeline()
        self.effects: list[Effect] = []
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

    @property
    def safe_box(self) -> Box:
        return Box(*self.content_box)

    def add(self, element: Element) -> Element:
        if element in self._elements:
            raise ValueError("element has already been added to this scene")
        if element.name is not None:
            if element.name in self._names:
                raise ValueError(f"Duplicate element name {element.name!r}")
            self._names.add(element.name)
        self._elements.append(element)
        return element

    def add_effect(self, effect: Effect) -> None:
        """Append a deterministic frame effect in explicit application order."""
        self.effects.append(effect)

    def _attach_many(self, assignments: list[tuple[Element, Animation]]) -> None:
        staged = {key: track.copy() for key, track in self._tracks.items()}
        for element, animation in assignments:
            if element not in self._elements:
                raise ValueError("animate requires an element already added to the scene")
            if isinstance(animation, DrawPath) and not isinstance(element, (MotionPath, Line)):
                raise ValueError("DrawPath requires a Path or Line element")
            for channel in animation.channels:
                track = staged.setdefault((element, channel), [])
                for existing in track:
                    if animation.start < existing.start + existing.duration and existing.start < animation.start + animation.duration:
                        label = element.name or type(element).__name__
                        raise ValueError(f"Animations overlap on {label}.{channel}")
                track.append(animation)
                track.sort(key=lambda item: item.start)
        self._tracks = staged

    def animate(self, element: Element, animation: Node) -> None:
        leaves, _ = expand(animation)
        self._attach_many([(element, leaf) for leaf in leaves])

    def stagger(self, elements: tuple[Element, ...] | list[Element], animation: Animation, *, start: float = 0, step: float = 0.1) -> None:
        if not isfinite(start) or start < 0 or not isfinite(step) or step < 0:
            raise ValueError("stagger start and step must be finite and non-negative")
        if len(set(elements)) != len(elements):
            raise ValueError("stagger elements must be unique")
        assignments = [
            (element, replace(animation, start=start + index * step + animation.start))
            for index, element in enumerate(elements)
        ]
        self._attach_many(assignments)

    def _property_at(self, element: Element, channel: str, time: float) -> float:
        base = getattr(element, channel, 1.0)
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

    def _reveal_at(self, element: Element, time: float) -> Reveal | MaskReveal | None:
        track = self._tracks.get((element, "reveal_progress"), [])
        if not track:
            return None
        selected = track[0]
        for animation in track:
            if animation.start <= time:
                selected = animation
            else:
                break
        assert isinstance(selected, (Reveal, MaskReveal))
        return selected

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
                scale_x=self._property_at(element, "scale_x", time),
                scale_y=self._property_at(element, "scale_y", time),
                rotation=self._property_at(element, "rotation", time),
                draw_progress=self._property_at(element, "draw_progress", time),
                reveal_progress=self._property_at(element, "reveal_progress", time),
                reveal=self._reveal_at(element, time),
            )
            for _, element in ordered
        ]

    def render_still(self, *, time: float, output: str | Path, width: int | None = None, height: int | None = None, overwrite: bool = False) -> Path:
        from .export import render_still

        return render_still(self, time=time, output=Path(output), width=width, height=height, overwrite=overwrite)

    def render_contact_sheet(self, *, output: str | Path, times: tuple[float, ...] | None = None, width: int = 270, height: int = 480, columns: int = 3, overwrite: bool = False) -> Path:
        from .inspect import render_contact_sheet, sample_times

        return render_contact_sheet(self, times=times if times is not None else sample_times(self), output=output, width=width, height=height, columns=columns, overwrite=overwrite)

    def render_preview(self, *, output: str | Path, width: int = 360, height: int = 640, fps: int = 15, overwrite: bool = False) -> Path:
        from .export import render_video

        return render_video(self, output=Path(output), width=width, height=height, fps=fps, overwrite=overwrite)

    def render(self, *, output: str | Path, width: int | None = None, height: int | None = None, fps: int | None = None, overwrite: bool = False) -> Path:
        from .export import render_video

        return render_video(self, output=Path(output), width=width or self.width, height=height or self.height, fps=fps or self.fps, overwrite=overwrite)
