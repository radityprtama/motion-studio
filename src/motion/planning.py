"""Typed, serializable planning artifacts; no model provider is involved."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from pathlib import Path
import json


def _positive(value: float, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value <= 0:
        raise ValueError(f"{label} must be finite and positive")


def _text(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} cannot be blank")


@dataclass(frozen=True)
class StoryboardScene:
    id: str
    start: float
    duration: float
    narration: str
    intent: str
    visual_concept: str

    def __post_init__(self) -> None:
        _text(self.id, "scene id")
        if isinstance(self.start, bool) or not isinstance(self.start, (int, float)) or not isfinite(self.start) or self.start < 0:
            raise ValueError("scene start must be finite and non-negative")
        _positive(self.duration, "scene duration")
        if not isinstance(self.narration, str):
            raise ValueError("scene narration must be a string")
        _text(self.intent, "scene intent")
        _text(self.visual_concept, "visual concept")


@dataclass(frozen=True)
class Storyboard:
    title: str
    format: str
    duration: float
    style: str
    scenes: tuple[StoryboardScene, ...]

    def __post_init__(self) -> None:
        _text(self.title, "storyboard title")
        if self.format != "portrait":
            raise ValueError("v0.1 storyboard format must be portrait")
        _positive(self.duration, "storyboard duration")
        _text(self.style, "storyboard style")
        if not self.scenes:
            raise ValueError("storyboard needs at least one scene")
        ids = [scene.id for scene in self.scenes]
        if len(ids) != len(set(ids)):
            raise ValueError("storyboard scene ids must be unique")
        previous_end = 0.0
        for scene in self.scenes:
            if scene.start < previous_end - 1e-9:
                raise ValueError(f"storyboard scene {scene.id} overlaps its predecessor")
            if scene.start + scene.duration > self.duration + 1e-9:
                raise ValueError(f"storyboard scene {scene.id} exceeds duration")
            previous_end = scene.start + scene.duration

    @classmethod
    def from_dict(cls, data: dict) -> Storyboard:
        return cls(**{**data, "scenes": tuple(StoryboardScene(**scene) for scene in data["scenes"])})

    def save(self, path: str | Path) -> Path:
        return _save_json(path, asdict(self))


@dataclass(frozen=True)
class ScenePlan:
    scene_id: str
    concept: str
    style: str
    visual_strategy: str
    components: tuple[str, ...]
    techniques: tuple[str, ...]
    memory_queries: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for label in ("scene_id", "concept", "style", "visual_strategy"):
            _text(getattr(self, label), label)
        if any(not isinstance(value, str) or not value.strip() for value in (*self.components, *self.techniques, *self.memory_queries)):
            raise ValueError("scene plan lists cannot contain blank terms")

    @classmethod
    def from_dict(cls, data: dict) -> ScenePlan:
        return cls(**{**data, **{key: tuple(data.get(key, ())) for key in ("components", "techniques", "memory_queries")}})

    def save(self, path: str | Path) -> Path:
        return _save_json(path, asdict(self))


def _save_json(path: str | Path, data: dict) -> Path:
    result = Path(path)
    result.parent.mkdir(parents=True, exist_ok=True)
    if result.exists():
        raise FileExistsError(result)
    result.write_text(json.dumps(data, indent=2) + "\n")
    return result
