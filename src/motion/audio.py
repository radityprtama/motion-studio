"""Declarative audio clips; mixing happens once at the FFmpeg export boundary."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class AudioTrack:
    source: Path
    kind: Literal["narration", "music", "sfx"]
    start: float
    duration: float
    volume: float = 1.0
    fade_in: float = 0.0
    fade_out: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "source", Path(self.source))
        if self.kind not in ("narration", "music", "sfx"):
            raise ValueError("audio kind must be narration, music, or sfx")
        if not all(isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value) for value in (self.start, self.duration, self.volume, self.fade_in, self.fade_out)):
            raise ValueError("audio timing and volume must be finite")
        if self.start < 0 or self.duration <= 0 or self.volume < 0 or self.fade_in < 0 or self.fade_out < 0:
            raise ValueError("audio timing and volume must be non-negative; duration must be positive")
        if self.fade_in + self.fade_out > self.duration:
            raise ValueError("audio fades exceed clip duration")


class AudioTimeline:
    def __init__(self) -> None:
        self._tracks: list[AudioTrack] = []

    @property
    def tracks(self) -> tuple[AudioTrack, ...]:
        return tuple(self._tracks)

    def add(self, track: AudioTrack) -> AudioTrack:
        self._tracks.append(track)
        return track
