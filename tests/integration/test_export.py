import json
import shutil
import subprocess

import pytest

from motion import export
from motion.primitives import Circle
from motion.scene import PortraitScene


def small_scene() -> PortraitScene:
    scene = PortraitScene(duration=0.4, seed=17)
    scene.add(Circle(x=540, y=960, radius=100, fill="#D9A66F"))
    return scene


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="FFmpeg tools unavailable")
def test_export_video_format_and_output_safety(tmp_path) -> None:
    output = tmp_path / "clip.mp4"
    small_scene().render(output=output, width=90, height=160, fps=10)
    info = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name,width,height,r_frame_rate,nb_frames", "-of", "json", str(output)],
        check=True,
        capture_output=True,
        text=True,
    )
    stream = json.loads(info.stdout)["streams"][0]
    assert stream["codec_name"] == "h264"
    assert (stream["width"], stream["height"]) == (90, 160)
    assert stream["r_frame_rate"] == "10/1"
    assert stream["nb_frames"] == "4"
    original = output.read_bytes()
    with pytest.raises(FileExistsError):
        small_scene().render(output=output, width=90, height=160, fps=10)
    assert output.read_bytes() == original


def test_still_and_invalid_timestamp(tmp_path) -> None:
    scene = small_scene()
    output = tmp_path / "still.png"
    scene.render_still(time=0.2, output=output, width=90, height=160)
    assert output.is_file()
    with pytest.raises(ValueError, match="time"):
        scene.render_still(time=1.0, output=tmp_path / "bad.png")


def test_failed_encode_preserves_existing_output(tmp_path, monkeypatch) -> None:
    output = tmp_path / "existing.mp4"
    output.write_bytes(b"user video")

    def fail_encode(*args) -> None:
        raise export.FFmpegError("encoder failed: bad codec")

    monkeypatch.setattr(export, "_encode_png_sequence", fail_encode)
    with pytest.raises(export.FFmpegError, match="bad codec"):
        small_scene().render(output=output, width=90, height=160, fps=10, overwrite=True)
    assert output.read_bytes() == b"user video"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["existing.mp4"]
