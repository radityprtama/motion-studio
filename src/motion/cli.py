"""Scriptable command-line rendering of Python scene files."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys

from .config import ProjectConfig, load_config
from .export import FFmpegError, render_video
from .inspect import sample_times
from .memory import MemoryStore
from .renderer import RenderError
from .scene import PortraitScene
from .style import BLUEPRINT, BLUEPRINT_PAPER, CINEMATIC


class SceneLoadError(RuntimeError):
    pass


def load_scene(path: Path, config: ProjectConfig | None = None) -> PortraitScene:
    resolved = path.resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"Scene file {resolved} does not exist")
    spec = importlib.util.spec_from_file_location(f"motion_scene_{resolved.stem}", resolved)
    if spec is None or spec.loader is None:
        raise SceneLoadError(f"Could not load scene file {resolved}")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise SceneLoadError(f"Could not execute scene file {resolved}: {exc}") from exc
    factory = getattr(module, "build_scene", None)
    if factory is not None:
        if not callable(factory):
            raise SceneLoadError(f"Scene file {resolved} has a non-callable build_scene")
        try:
            scene = factory(config or ProjectConfig())
        except Exception as exc:
            raise SceneLoadError(f"build_scene failed in {resolved}: {exc}") from exc
    else:
        scene = getattr(module, "scene", None)
    if not isinstance(scene, PortraitScene):
        raise SceneLoadError(f"Scene file {resolved} must export a PortraitScene named 'scene' or build_scene(config)")
    return scene


def _resolution(value: str) -> tuple[int, int]:
    try:
        width_text, height_text = value.lower().split("x", 1)
        width, height = int(width_text), int(height_text)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Resolution {value!r} must look like 1080x1920") from exc
    if width <= 0 or height <= 0:
        raise ValueError("resolution dimensions must be positive")
    return width, height


def _dimensions(args: argparse.Namespace, default: tuple[int, int]) -> tuple[int, int]:
    if args.resolution is not None:
        if args.width is not None or args.height is not None:
            raise ValueError("Use either --resolution or both --width and --height")
        return _resolution(args.resolution)
    if (args.width is None) != (args.height is None):
        raise ValueError("Provide both --width and --height")
    if args.width is not None:
        return args.width, args.height
    return default


def _progress():
    last_bucket = -1

    def report(done: int, total: int) -> None:
        nonlocal last_bucket
        percent = done * 100 // total
        bucket = percent // 10
        if bucket > last_bucket or done == total:
            print(f"[{done}/{total}] {percent}%", file=sys.stderr)
            last_bucket = bucket

    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="motion", description="Render deterministic Python motion scenes")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("still", "preview", "render", "inspect"):
        command = commands.add_parser(name)
        command.add_argument("scene", type=Path)
        command.add_argument("--config", type=Path)
        command.add_argument("--output", type=Path)
        command.add_argument("--resolution")
        command.add_argument("--width", type=int)
        command.add_argument("--height", type=int)
        command.add_argument("--overwrite", action="store_true")
        if name == "still":
            command.add_argument("--time", type=float, required=True)
        elif name == "inspect":
            command.add_argument("--times", help="comma-separated seconds; defaults to six samples")
            command.add_argument("--columns", type=int, default=3)
        else:
            command.add_argument("--fps", type=int)
    commands.add_parser("styles", help="list available visual styles")
    commands.add_parser("examples", help="list bundled source examples")
    memory = commands.add_parser("memory", help="search saved scene examples")
    memory_commands = memory.add_subparsers(dest="memory_command", required=True)
    search = memory_commands.add_parser("search")
    search.add_argument("--root", type=Path, default=Path("memory"))
    search.add_argument("--style")
    search.add_argument("--scene-type")
    search.add_argument("--concept", action="append", default=[])
    search.add_argument("--technique", action="append", default=[])
    search.add_argument("--tag", action="append", default=[])
    search.add_argument("--limit", type=int, default=5)
    search.add_argument("--min-quality", type=float, default=.5)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "styles":
            for style in (BLUEPRINT, BLUEPRINT_PAPER, CINEMATIC):
                print(f"{style.name}\t{style.background_treatment}")
            return 0
        if args.command == "examples":
            root = Path(__file__).resolve().parent / "examples"
            if not root.is_dir():
                root = Path(__file__).resolve().parents[2] / "examples"
            for path in sorted(root.rglob("*.py")) if root.is_dir() else ():
                print(path.relative_to(root))
            return 0
        if args.command == "memory":
            matches = MemoryStore(args.root).search(
                style=args.style, scene_type=args.scene_type, concepts=tuple(args.concept),
                techniques=tuple(args.technique), tags=tuple(args.tag), limit=args.limit,
                min_quality=args.min_quality,
            )
            for match in matches:
                print(f"{match.item.id}\t{match.score:.2f}\t{match.item.style}\t{match.item.scene_type}\t{match.item.quality:.2f}")
            return 0
        config = load_config(args.config, scene_path=args.scene)
        scene = load_scene(args.scene, config)
        if args.command == "preview":
            default_size = (config.preview.width, config.preview.height)
        elif args.command == "inspect":
            default_size = (max(1, config.preview.width * 3 // 4), max(1, config.preview.height * 3 // 4))
        else:
            default_size = (scene.width, scene.height)
        width, height = _dimensions(args, default_size)
        default_output = {
            "still": Path(".build/still.png"),
            "preview": Path(".build/preview.mp4"),
            "render": Path(".build/final.mp4"),
            "inspect": Path(".build/contact-sheet.png"),
        }[args.command]
        output = args.output or default_output
        fps = config.preview.fps if args.command == "preview" else scene.fps
        if args.command in ("preview", "render") and args.fps is not None:
            fps = args.fps
        print(
            f"Scene: {args.scene} | style: {scene.style} | duration: {scene.duration:g}s | "
            f"resolution: {width}x{height} | FPS: {fps} | seed: {scene.seed}",
            file=sys.stderr,
        )
        if args.command == "still":
            result = scene.render_still(time=args.time, output=output, width=width, height=height, overwrite=args.overwrite)
        elif args.command == "inspect":
            times = tuple(float(value.strip()) for value in args.times.split(",")) if args.times else sample_times(scene)
            result = scene.render_contact_sheet(output=output, times=times, width=width, height=height, columns=args.columns, overwrite=args.overwrite)
        else:
            result = render_video(
                scene, output=output, width=width, height=height,
                fps=fps, overwrite=args.overwrite, progress=_progress(),
            )
        print(result)
        return 0
    except (ValueError, FileNotFoundError, FileExistsError, SceneLoadError, RenderError, FFmpegError, OSError) as exc:
        print(f"motion: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
