"""Frame and FFmpeg output, with one controlled encoder boundary."""

from __future__ import annotations

from collections.abc import Callable
from math import ceil
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
import os
import subprocess

from .renderer import render_frame
from .scene import PortraitScene
from .audio import AudioTimeline


class FFmpegError(RuntimeError):
    pass


Progress = Callable[[int, int], None]


def _prepare_output(output: Path, overwrite: bool) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output {output} already exists; pass --overwrite to replace it")


def _temporary_output(output: Path) -> Path:
    with NamedTemporaryFile(prefix=f".{output.stem}-", suffix=output.suffix, dir=output.parent, delete=False) as file:
        return Path(file.name)


def render_still(
    scene: PortraitScene,
    *,
    time: float,
    output: Path,
    width: int | None = None,
    height: int | None = None,
    overwrite: bool = False,
) -> Path:
    output = output.resolve()
    _prepare_output(output, overwrite)
    frame = render_frame(scene, time, width=width, height=height)
    temporary = _temporary_output(output)
    try:
        frame.save(temporary, format="PNG")
        if output.exists() and not overwrite:
            raise FileExistsError(f"Output {output} appeared during rendering; pass --overwrite to replace it")
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    return output


def _encode_png_sequence(pattern: Path, output: Path, fps: int, frames: int) -> None:
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-framerate", str(fps), "-start_number", "0", "-i", str(pattern),
        "-frames:v", str(frames), "-c:v", "libx264", "-preset", "medium",
        "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(fps),
        "-threads", "1", "-movflags", "+faststart", str(output),
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise FFmpegError("FFmpeg executable was not found; install FFmpeg and retry") from exc
    if result.returncode != 0:
        raise FFmpegError(
            f"FFmpeg export failed. Input frames: {pattern}; expected FPS: {fps}; "
            f"exit code: {result.returncode}. stderr:\n{result.stderr.strip()}"
        )


def _mux_audio(video: Path, timeline: AudioTimeline, output: Path, duration: float) -> None:
    tracks = timeline.tracks
    if not tracks:
        raise ValueError("audio timeline has no tracks")
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(video)]
    filters = []
    for index, track in enumerate(tracks):
        if not track.source.is_file():
            raise FileNotFoundError(f"Audio source {track.source} does not exist ({track.kind} track {index})")
        if track.start >= duration:
            raise ValueError(f"Audio track {index} starts beyond video duration {duration:g}s")
        command.extend(["-i", str(track.source)])
        visible = min(track.duration, duration - track.start)
        parts = [f"atrim=0:{visible:g}", "asetpts=PTS-STARTPTS", f"volume={track.volume:g}"]
        if track.fade_in:
            parts.append(f"afade=t=in:st=0:d={min(track.fade_in, visible):g}")
        if track.fade_out:
            fade = min(track.fade_out, visible)
            parts.append(f"afade=t=out:st={visible - fade:g}:d={fade:g}")
        parts.append(f"adelay={round(track.start * 1000)}:all=1")
        filters.append(f"[{index + 1}:a]{','.join(parts)}[a{index}]")
    inputs = "".join(f"[a{index}]" for index in range(len(tracks)))
    filters.append(f"{inputs}amix=inputs={len(tracks)}:normalize=0:duration=longest,atrim=0:{duration:g}[mix]")
    command.extend(["-filter_complex", ";".join(filters), "-map", "0:v:0", "-map", "[mix]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(output)])
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise FFmpegError("FFmpeg executable was not found; install FFmpeg and retry") from exc
    if result.returncode != 0:
        raise FFmpegError(f"FFmpeg audio export failed for {video}; exit code: {result.returncode}. stderr:\n{result.stderr.strip()}")


def render_video(
    scene: PortraitScene,
    *,
    output: Path,
    width: int,
    height: int,
    fps: int,
    overwrite: bool = False,
    progress: Progress | None = None,
) -> Path:
    if fps <= 0:
        raise ValueError("output FPS must be positive")
    if width <= 0 or height <= 0 or width * scene.height != height * scene.width:
        raise ValueError("output resolution must be positive and preserve the scene aspect ratio")
    output = output.resolve()
    _prepare_output(output, overwrite)
    for index, track in enumerate(scene.audio.tracks):
        if not track.source.is_file():
            raise FileNotFoundError(f"Audio source {track.source} does not exist ({track.kind} track {index})")
        if track.start >= scene.duration:
            raise ValueError(f"Audio track {index} starts beyond scene duration {scene.duration:g}s")
    count = ceil(scene.duration * fps)
    with TemporaryDirectory(prefix="motion-frames-") as directory:
        frames_dir = Path(directory)
        for index in range(count):
            time = index / fps
            frame = render_frame(scene, time, width=width, height=height)
            frame.save(frames_dir / f"{index:06d}.png", format="PNG")
            if progress is not None:
                progress(index + 1, count)
        temporary = _temporary_output(output)
        try:
            if scene.audio.tracks:
                silent = frames_dir / "silent.mp4"
                _encode_png_sequence(frames_dir / "%06d.png", silent, fps, count)
                _mux_audio(silent, scene.audio, temporary, count / fps)
            else:
                _encode_png_sequence(frames_dir / "%06d.png", temporary, fps, count)
            if output.exists() and not overwrite:
                raise FileExistsError(f"Output {output} appeared during rendering; pass --overwrite to replace it")
            os.replace(temporary, output)
        finally:
            temporary.unlink(missing_ok=True)
    return output
