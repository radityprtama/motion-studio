"""A small 2D camera with direct-time property tracks."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .animation import ease, progress


@dataclass(frozen=True)
class CameraState:
    x: float
    y: float
    zoom: float
    rotation: float


@dataclass(frozen=True)
class _CameraTrack:
    start: float
    duration: float
    from_value: float
    to_value: float
    easing: str

    def value(self, time: float) -> float:
        amount = ease(self.easing, progress(time, start=self.start, duration=self.duration))
        return self.from_value + (self.to_value - self.from_value) * amount


class Camera:
    def __init__(self, *, x: float, y: float, zoom: float = 1, rotation: float = 0) -> None:
        values = (x, y, zoom, rotation)
        if not all(isfinite(value) for value in values) or zoom <= 0:
            raise ValueError("camera position and rotation must be finite; zoom must be positive")
        self._base = CameraState(x=x, y=y, zoom=zoom, rotation=rotation)
        self._tracks: dict[str, list[_CameraTrack]] = {}

    def animate(
        self,
        *,
        x: tuple[float, float] | None = None,
        y: tuple[float, float] | None = None,
        zoom: tuple[float, float] | None = None,
        rotation: tuple[float, float] | None = None,
        start: float = 0,
        duration: float = 1,
        easing: str = "linear",
    ) -> None:
        if not isfinite(start) or start < 0 or not isfinite(duration) or duration <= 0:
            raise ValueError("camera start and duration must be finite; start >= 0 and duration > 0")
        ease(easing, 0)
        changes = {name: pair for name, pair in (("x", x), ("y", y), ("zoom", zoom), ("rotation", rotation)) if pair is not None}
        if not changes:
            raise ValueError("camera.animate requires x, y, zoom, or rotation")
        staged = {name: tracks.copy() for name, tracks in self._tracks.items()}
        for name, pair in changes.items():
            if len(pair) != 2 or not all(isfinite(value) for value in pair):
                raise ValueError(f"camera {name} requires two finite endpoint values")
            if name == "zoom" and (pair[0] <= 0 or pair[1] <= 0):
                raise ValueError("camera zoom endpoints must be positive")
            track = _CameraTrack(start, duration, pair[0], pair[1], easing)
            channel = staged.setdefault(name, [])
            for existing in channel:
                if start < existing.start + existing.duration and existing.start < start + duration:
                    raise ValueError(f"camera {name} animations overlap")
            channel.append(track)
            channel.sort(key=lambda item: item.start)
        self._tracks = staged

    def _value_at(self, name: str, time: float) -> float:
        tracks = self._tracks.get(name, [])
        if not tracks:
            return getattr(self._base, name)
        selected = tracks[0]
        for track in tracks:
            if track.start <= time:
                selected = track
            else:
                break
        return selected.value(time)

    def evaluate(self, time: float) -> CameraState:
        if not isfinite(time) or time < 0:
            raise ValueError("camera time must be finite and non-negative")
        state = CameraState(
            x=self._value_at("x", time),
            y=self._value_at("y", time),
            zoom=self._value_at("zoom", time),
            rotation=self._value_at("rotation", time),
        )
        if state.zoom <= 0:
            raise ValueError(f"camera zoom is non-positive at t={time:.3f}s")
        return state
