"""Pure timeline values. No animation depends on a previous frame."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .primitives import Circle, Rectangle


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def progress(time: float, *, start: float, duration: float) -> float:
    if not all(isfinite(value) for value in (time, start, duration)):
        raise ValueError("time, start, and duration must be finite")
    if duration <= 0:
        raise ValueError("animation duration must be greater than zero")
    return _clamp01((time - start) / duration)


def ease(name: str, amount: float) -> float:
    t = _clamp01(amount)
    if name == "linear":
        return t
    if name == "ease_in":
        return t * t
    if name == "ease_out":
        return 1 - (1 - t) ** 2
    if name == "ease_in_out":
        return t * t * (3 - 2 * t)
    if name == "ease_out_cubic":
        return 1 - (1 - t) ** 3
    if name == "ease_in_out_cubic":
        return 4 * t**3 if t < 0.5 else 1 - ((-2 * t + 2) ** 3) / 2
    if name == "ease_out_back":
        if t == 0 or t == 1:
            return t
        amount = t - 1
        return 1 + 2.70158 * amount**3 + 1.70158 * amount**2
    raise ValueError(
        f"Unknown easing {name!r}; choose linear, ease_in, ease_out, ease_in_out, "
        "ease_out_cubic, ease_in_out_cubic, or ease_out_back"
    )


@dataclass(frozen=True, kw_only=True)
class Animation:
    start: float = 0.0
    duration: float = 1.0
    easing: str = "linear"

    def __post_init__(self) -> None:
        if not isfinite(self.start) or self.start < 0:
            raise ValueError("animation start must be a finite non-negative time")
        if not isfinite(self.duration) or self.duration <= 0:
            raise ValueError("animation duration must be finite and greater than zero")
        ease(self.easing, 0)

    @property
    def channels(self) -> tuple[str, ...]:
        raise NotImplementedError

    def value(self, channel: str, time: float, base: float) -> float:
        raise NotImplementedError

    def amount(self, time: float) -> float:
        return ease(self.easing, progress(time, start=self.start, duration=self.duration))


@dataclass(frozen=True, kw_only=True)
class Move(Animation):
    from_x: float | None = None
    to_x: float | None = None
    from_y: float | None = None
    to_y: float | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if (self.from_x is None) != (self.to_x is None) or (self.from_y is None) != (self.to_y is None):
            raise ValueError("Move requires both from and to values for each animated axis")
        if self.from_x is None and self.from_y is None:
            raise ValueError("Move requires at least one axis")
        for value in (self.from_x, self.to_x, self.from_y, self.to_y):
            if value is not None and not isfinite(value):
                raise ValueError("Move endpoints must be finite")

    @property
    def channels(self) -> tuple[str, ...]:
        return tuple(channel for channel, value in (("x", self.from_x), ("y", self.from_y)) if value is not None)

    def value(self, channel: str, time: float, base: float) -> float:
        endpoints = {"x": (self.from_x, self.to_x), "y": (self.from_y, self.to_y)}
        if channel not in self.channels:
            raise ValueError(f"Move does not animate {channel!r}")
        start, end = endpoints[channel]
        assert start is not None and end is not None
        return start + (end - start) * self.amount(time)


@dataclass(frozen=True, kw_only=True)
class FadeIn(Animation):
    @property
    def channels(self) -> tuple[str, ...]:
        return ("opacity",)

    def value(self, channel: str, time: float, base: float) -> float:
        if channel != "opacity":
            raise ValueError(f"FadeIn does not animate {channel!r}")
        return base * self.amount(time)


@dataclass(frozen=True, kw_only=True)
class FadeOut(Animation):
    @property
    def channels(self) -> tuple[str, ...]:
        return ("opacity",)

    def value(self, channel: str, time: float, base: float) -> float:
        if channel != "opacity":
            raise ValueError(f"FadeOut does not animate {channel!r}")
        return base * (1 - self.amount(time))


@dataclass(frozen=True, kw_only=True)
class Scale(Animation):
    from_x: float | None = None
    to_x: float | None = None
    from_y: float | None = None
    to_y: float | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if (self.from_x is None) != (self.to_x is None) or (self.from_y is None) != (self.to_y is None):
            raise ValueError("Scale requires both from and to values for each animated axis")
        if self.from_x is None and self.from_y is None:
            raise ValueError("Scale requires at least one axis")
        for value in (self.from_x, self.to_x, self.from_y, self.to_y):
            if value is not None and (not isfinite(value) or value <= 0):
                raise ValueError("Scale endpoints must be finite and positive")

    @property
    def channels(self) -> tuple[str, ...]:
        return tuple(channel for channel, value in (("scale_x", self.from_x), ("scale_y", self.from_y)) if value is not None)

    def value(self, channel: str, time: float, base: float) -> float:
        endpoints = {"scale_x": (self.from_x, self.to_x), "scale_y": (self.from_y, self.to_y)}
        if channel not in self.channels:
            raise ValueError(f"Scale does not animate {channel!r}")
        start, end = endpoints[channel]
        assert start is not None and end is not None
        value = start + (end - start) * self.amount(time)
        if value <= 0:
            raise ValueError(f"Scale on {channel} is non-positive at t={time:.3f}s")
        return value


@dataclass(frozen=True, kw_only=True)
class Rotate(Animation):
    from_angle: float
    to_angle: float

    def __post_init__(self) -> None:
        super().__post_init__()
        if not isfinite(self.from_angle) or not isfinite(self.to_angle):
            raise ValueError("Rotate angles must be finite degrees")

    @property
    def channels(self) -> tuple[str, ...]:
        return ("rotation",)

    def value(self, channel: str, time: float, base: float) -> float:
        if channel != "rotation":
            raise ValueError(f"Rotate does not animate {channel!r}")
        return self.from_angle + (self.to_angle - self.from_angle) * self.amount(time)


@dataclass(frozen=True, kw_only=True)
class DrawPath(Animation):
    @property
    def channels(self) -> tuple[str, ...]:
        return ("draw_progress",)

    def value(self, channel: str, time: float, base: float) -> float:
        if channel != "draw_progress":
            raise ValueError(f"DrawPath does not animate {channel!r}")
        return self.amount(time)


@dataclass(frozen=True, kw_only=True)
class Reveal(Animation):
    direction: str = "left"

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.direction not in ("left", "right", "top", "bottom"):
            raise ValueError("Reveal direction must be left, right, top, or bottom")

    @property
    def channels(self) -> tuple[str, ...]:
        return ("reveal_progress",)

    def value(self, channel: str, time: float, base: float) -> float:
        if channel != "reveal_progress":
            raise ValueError(f"Reveal does not animate {channel!r}")
        return self.amount(time)


@dataclass(frozen=True, kw_only=True)
class MaskReveal(Animation):
    mask: Rectangle | Circle

    def __post_init__(self) -> None:
        super().__post_init__()
        if not isinstance(self.mask, (Rectangle, Circle)):
            raise TypeError("MaskReveal mask must be a Rectangle or Circle")

    @property
    def channels(self) -> tuple[str, ...]:
        return ("reveal_progress",)

    def value(self, channel: str, time: float, base: float) -> float:
        if channel != "reveal_progress":
            raise ValueError(f"MaskReveal does not animate {channel!r}")
        return self.amount(time)
