"""Scriptable command-line rendering of Python scene files."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys

from .export import FFmpegError, render_video
from .renderer import RenderError
from .scene import PortraitScene


class SceneLoadError(RuntimeError):
    pass


def load_scene(path: Path) -> PortraitScene:
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
    scene = getattr(module, "scene", None)
    if not isinstance(scene, PortraitScene):
        raise SceneLoadError(f"Scene file {resolved} must export a PortraitScene named 'scene'")
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
    for name in ("still", "preview", "render"):
        command = commands.add_parser(name)
        command.add_argument("scene", type=Path)
        command.add_argument("--output", type=Path)
        command.add_argument("--resolution")
        command.add_argument("--width", type=int)
        command.add_argument("--height", type=int)
        command.add_argument("--overwrite", action="store_true")
        if name == "still":
            command.add_argument("--time", type=float, required=True)
        else:
            command.add_argument("--fps", type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        scene = load_scene(args.scene)
        default_size = (360, 640) if args.command == "preview" else (scene.width, scene.height)
        width, height = _dimensions(args, default_size)
        default_output = {
            "still": Path(".build/still.png"),
            "preview": Path(".build/preview.mp4"),
            "render": Path(".build/final.mp4"),
        }[args.command]
        output = args.output or default_output
        fps = 15 if args.command == "preview" else scene.fps
        if args.command != "still" and args.fps is not None:
            fps = args.fps
        print(
            f"Scene: {args.scene} | style: {scene.style} | duration: {scene.duration:g}s | "
            f"resolution: {width}x{height} | FPS: {fps} | seed: {scene.seed}",
            file=sys.stderr,
        )
        if args.command == "still":
            result = scene.render_still(time=args.time, output=output, width=width, height=height, overwrite=args.overwrite)
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
