"""Explicit project defaults for scene factories and command output."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import tomllib

from .style import get_style


@dataclass(frozen=True)
class VideoSettings:
    width: int
    height: int
    fps: int

    def __post_init__(self) -> None:
        if any(type(value) is not int or value <= 0 for value in (self.width, self.height, self.fps)):
            raise ValueError("video width, height, and FPS must be positive")


@dataclass(frozen=True)
class ProjectConfig:
    default_style: str = "blueprint"
    render: VideoSettings = field(default_factory=lambda: VideoSettings(1080, 1920, 30))
    preview: VideoSettings = field(default_factory=lambda: VideoSettings(360, 640, 15))
    source: Path | None = None

    def __post_init__(self) -> None:
        get_style(self.default_style)


def find_config(scene_path: Path) -> Path | None:
    for directory in (scene_path.resolve().parent, *scene_path.resolve().parent.parents):
        candidate = directory / "motion.toml"
        if candidate.is_file():
            return candidate
    return None


def load_config(path: Path | None = None, *, scene_path: Path | None = None) -> ProjectConfig:
    source = path if path is not None else find_config(scene_path) if scene_path is not None else None
    if source is None:
        return ProjectConfig()
    source = source.resolve()
    with source.open("rb") as stream:
        data = tomllib.load(stream)
    if set(data) - {"project", "render", "preview"}:
        raise ValueError(f"Unknown section in {source}: {sorted(set(data) - {'project', 'render', 'preview'})}")
    project = data.get("project", {})
    if not isinstance(project, dict):
        raise ValueError(f"[project] in {source} must be a table")
    if set(project) - {"default_style"}:
        raise ValueError(f"Unknown project setting in {source}: {sorted(set(project) - {'default_style'})}")
    defaults = ProjectConfig()
    def settings(section: str, fallback: VideoSettings) -> VideoSettings:
        values = data.get(section, {})
        if not isinstance(values, dict):
            raise ValueError(f"[{section}] in {source} must be a table")
        if set(values) - {"width", "height", "fps"}:
            raise ValueError(f"Unknown {section} setting in {source}: {sorted(set(values) - {'width', 'height', 'fps'})}")
        return VideoSettings(values.get("width", fallback.width), values.get("height", fallback.height), values.get("fps", fallback.fps))
    return ProjectConfig(project.get("default_style", defaults.default_style), settings("render", defaults.render), settings("preview", defaults.preview), source)
