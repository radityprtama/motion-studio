"""Provider-neutral operations a coding agent can call in separate steps."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re

from .cli import load_scene
from .config import load_config
from .export import render_video
from .inspect import sample_times
from .memory import MemoryExample, MemoryItem, MemoryMatch, MemoryStore
from .planning import ScenePlan, Storyboard
from .style import BLUEPRINT, BLUEPRINT_PAPER, CINEMATIC


COMPONENTS = ("Arrow", "Badge", "Browser", "Card", "Chart", "CommitGraph", "CommitNode", "Computer", "Crowd", "File", "Folder", "Graph", "Label", "ObjectGrid", "Orb", "Person", "Quote", "Server", "Terminal", "Timeline")
SCENE_PATTERNS = ("ComparisonScene", "ProcessScene", "TimelineScene", "GraphScene", "CrowdScene", "StatisticsScene", "EditorialScene", "QuoteScene", "HierarchyScene", "FlowScene")
_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{1,79}$")


@dataclass(frozen=True)
class ProjectInspection:
    root: Path
    request: dict | None
    storyboard: Storyboard | None
    plans: tuple[ScenePlan, ...]
    generated_scenes: tuple[Path, ...]
    previews: tuple[Path, ...]
    stills: tuple[Path, ...]
    final: tuple[Path, ...]


class MotionHarness:
    def __init__(self, *, memory_root: str | Path = "memory", examples_root: str | Path = "examples", assets_root: str | Path = "assets") -> None:
        self.memory = MemoryStore(memory_root)
        self.examples_root = Path(examples_root).resolve()
        self.assets_root = Path(assets_root).resolve()
        if not self.examples_root.is_dir() and str(examples_root) == "examples":
            self.examples_root = Path(__file__).resolve().parent / "examples"

    def list_styles(self) -> tuple[str, ...]:
        return tuple(style.name for style in (BLUEPRINT, BLUEPRINT_PAPER, CINEMATIC))

    def list_assets(self) -> tuple[Path, ...]:
        bundled = Path(__file__).resolve().parent / "assets"
        return tuple(sorted({path for root in (bundled, self.assets_root) if root.is_dir() for path in root.rglob("*") if path.is_file()}))

    def list_components(self) -> tuple[str, ...]:
        return COMPONENTS

    def list_scene_patterns(self) -> tuple[str, ...]:
        return SCENE_PATTERNS

    def list_examples(self) -> tuple[Path, ...]:
        return tuple(sorted(self.examples_root.rglob("*.py"))) if self.examples_root.is_dir() else ()

    def search_memory(self, **query: object) -> tuple[MemoryMatch, ...]:
        return self.memory.search(**query)

    def read_example(self, item_id: str) -> MemoryExample:
        return self.memory.read_example(item_id)

    def save_memory(self, item: MemoryItem, *, source: str | Path, intent: str, stills: tuple[str | Path, ...] = ()) -> Path:
        return self.memory.save(item, source=source, intent=intent, stills=stills)

    def render_still(self, source: str | Path, *, time: float, output: str | Path, width: int | None = None, height: int | None = None, overwrite: bool = False) -> Path:
        scene = self._scene(source)
        return scene.render_still(time=time, output=output, width=width, height=height, overwrite=overwrite)

    def render_contact_sheet(self, source: str | Path, *, output: str | Path, times: tuple[float, ...] | None = None, width: int = 270, height: int = 480, overwrite: bool = False) -> Path:
        scene = self._scene(source)
        return scene.render_contact_sheet(output=output, times=sample_times(scene) if times is None else times, width=width, height=height, overwrite=overwrite)

    def render_preview(self, source: str | Path, *, output: str | Path, overwrite: bool = False) -> Path:
        source = Path(source)
        config = load_config(scene_path=source)
        scene = load_scene(source, config)
        return render_video(scene, output=Path(output), width=config.preview.width, height=config.preview.height, fps=config.preview.fps, overwrite=overwrite)

    def render_scene(self, source: str | Path, *, output: str | Path, overwrite: bool = False) -> Path:
        scene = self._scene(source)
        return scene.render(output=output, overwrite=overwrite)

    def _scene(self, source: str | Path):
        source = Path(source)
        return load_scene(source, load_config(scene_path=source))

    def create_project(self, root: str | Path, *, request: dict) -> Path:
        root = Path(root).resolve()
        if root.exists():
            raise FileExistsError(root)
        if not isinstance(request, dict) or not request:
            raise ValueError("request must be a nonempty JSON object")
        json.dumps(request)
        for name in ("scene-plans", "generated-scenes", "previews", "stills", "inspection", "final"):
            (root / name).mkdir(parents=True, exist_ok=True)
        (root / "request.json").write_text(json.dumps(request, indent=2) + "\n")
        return root

    def save_storyboard(self, project: str | Path, storyboard: Storyboard) -> Path:
        return storyboard.save(Path(project) / "storyboard.json")

    def save_scene_plan(self, project: str | Path, plan: ScenePlan) -> Path:
        if not _SLUG.fullmatch(plan.scene_id):
            raise ValueError("scene plan id must be a lowercase slug")
        return plan.save(Path(project) / "scene-plans" / f"{plan.scene_id}.json")

    def inspect_project(self, root: str | Path) -> ProjectInspection:
        root = Path(root).resolve()
        request_path = root / "request.json"
        storyboard_path = root / "storyboard.json"
        return ProjectInspection(
            root=root,
            request=json.loads(request_path.read_text()) if request_path.exists() else None,
            storyboard=Storyboard.from_dict(json.loads(storyboard_path.read_text())) if storyboard_path.exists() else None,
            plans=tuple(ScenePlan.from_dict(json.loads(path.read_text())) for path in sorted((root / "scene-plans").glob("*.json"))),
            generated_scenes=tuple(sorted((root / "generated-scenes").glob("*.py"))),
            previews=tuple(sorted((root / "previews").glob("*.mp4"))),
            stills=tuple(sorted((root / "stills").glob("*.png"))),
            final=tuple(sorted((root / "final").glob("*.mp4"))),
        )
