"""Filesystem examples with explicit metadata, feedback, and ranked retrieval."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
import os
import re
import shutil
from tempfile import NamedTemporaryFile


_ID = re.compile(r"^[a-z0-9][a-z0-9-]{1,79}$")


@dataclass(frozen=True)
class MemoryItem:
    id: str
    style: str
    scene_type: str
    concepts: tuple[str, ...] = ()
    techniques: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    quality: float = 0.5
    feedback: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not _ID.fullmatch(self.id):
            raise ValueError("memory id must be a lowercase slug of 2–80 characters")
        if not isinstance(self.style, str) or not isinstance(self.scene_type, str) or not self.style.strip() or not self.scene_type.strip():
            raise ValueError("memory style and scene_type cannot be blank")
        if isinstance(self.quality, bool) or not isinstance(self.quality, (int, float)) or not 0 <= self.quality <= 1:
            raise ValueError("memory quality must be between 0 and 1")
        for group in (self.concepts, self.techniques, self.tags, self.feedback):
            if isinstance(group, str) or any(not isinstance(value, str) or not value.strip() for value in group):
                raise ValueError("memory terms and feedback cannot be blank")

    @classmethod
    def from_dict(cls, value: dict) -> MemoryItem:
        allowed = set(cls.__dataclass_fields__)
        unknown = set(value) - allowed
        if unknown:
            raise ValueError(f"unknown memory fields: {sorted(unknown)}")
        for key in ("concepts", "techniques", "tags", "feedback"):
            if key in value and not isinstance(value[key], (list, tuple)):
                raise ValueError(f"memory {key} must be a list")
        return cls(**{key: tuple(item) if key in {"concepts", "techniques", "tags", "feedback"} else item for key, item in value.items()})


@dataclass(frozen=True)
class MemoryMatch:
    item: MemoryItem
    score: float


@dataclass(frozen=True)
class MemoryExample:
    item: MemoryItem
    intent: str
    source: str
    stills: tuple[Path, ...]


class MemoryStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    @property
    def scenes_dir(self) -> Path:
        return self.root / "scenes"

    def _directory(self, item_id: str) -> Path:
        if not _ID.fullmatch(item_id):
            raise ValueError("invalid memory id")
        return self.scenes_dir / item_id

    def list_items(self) -> tuple[MemoryItem, ...]:
        if not self.scenes_dir.is_dir():
            return ()
        items = []
        for path in sorted(self.scenes_dir.glob("*/metadata.json")):
            item = MemoryItem.from_dict(json.loads(path.read_text()))
            if path.parent.name != item.id:
                raise ValueError(f"memory id mismatch in {path}")
            items.append(item)
        return tuple(items)

    def read_example(self, item_id: str) -> MemoryExample:
        directory = self._directory(item_id)
        item = MemoryItem.from_dict(json.loads((directory / "metadata.json").read_text()))
        if item.id != item_id:
            raise ValueError(f"memory id mismatch in {directory}")
        return MemoryExample(item, (directory / "intent.md").read_text(), (directory / "scene.py").read_text(), tuple(sorted((directory / "stills").glob("*.png"))))

    def save(self, item: MemoryItem, *, source: str | Path, intent: str, stills: tuple[str | Path, ...] = ()) -> Path:
        if not intent.strip():
            raise ValueError("memory intent cannot be blank")
        directory = self._directory(item.id)
        if directory.exists():
            raise FileExistsError(f"Memory example {item.id} already exists")
        source_path = Path(source)
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        for still in stills:
            if not Path(still).is_file():
                raise FileNotFoundError(still)
        directory.mkdir(parents=True)
        try:
            shutil.copyfile(source_path, directory / "scene.py")
            (directory / "intent.md").write_text(intent.rstrip() + "\n")
            (directory / "metadata.json").write_text(json.dumps(asdict(item), indent=2) + "\n")
            if stills:
                (directory / "stills").mkdir()
                for index, still in enumerate(stills):
                    shutil.copyfile(still, directory / "stills" / f"{index:02d}.png")
        except BaseException:
            shutil.rmtree(directory)
            raise
        return directory

    def add_feedback(self, item_id: str, *, quality: float, comment: str) -> MemoryItem:
        if not comment.strip():
            raise ValueError("feedback comment cannot be blank")
        directory = self._directory(item_id)
        path = directory / "metadata.json"
        current = self.read_example(item_id).item
        revised = MemoryItem(**{**asdict(current), "quality": quality, "feedback": current.feedback + (comment,)})
        with NamedTemporaryFile(mode="w", prefix=".metadata-", suffix=".json", dir=directory, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(asdict(revised), stream, indent=2)
            stream.write("\n")
        try:
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
        return revised

    def search(
        self, *, style: str | None = None, scene_type: str | None = None,
        concepts: tuple[str, ...] = (), techniques: tuple[str, ...] = (), tags: tuple[str, ...] = (),
        limit: int = 5, min_quality: float = 0.5,
    ) -> tuple[MemoryMatch, ...]:
        if limit <= 0 or not 0 <= min_quality <= 1:
            raise ValueError("limit must be positive and min_quality between 0 and 1")
        terms = {term.casefold() for term in (*concepts, *techniques, *tags)}
        results = []
        for item in self.list_items():
            if item.quality < min_quality or (style and item.style != style) or (scene_type and item.scene_type != scene_type):
                continue
            item_terms = {term.casefold() for term in (*item.concepts, *item.techniques, *item.tags)}
            overlap = len(terms & item_terms)
            if terms and not overlap:
                continue
            score = item.quality * 2 + (overlap / len(terms) if terms else 0)
            results.append(MemoryMatch(item, score))
        return tuple(sorted(results, key=lambda match: (-match.score, match.item.id))[:limit])
