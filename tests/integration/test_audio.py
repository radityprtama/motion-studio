import json
import math
import shutil
import struct
import subprocess
import wave

import pytest

from motion import AudioTrack, PortraitScene


def test_audio_track_validation() -> None:
    with pytest.raises(ValueError, match="fades exceed"):
        AudioTrack("tone.wav", "music", 0, 1, fade_in=.7, fade_out=.7)


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="FFmpeg unavailable")
def test_audio_is_muxed_with_video(tmp_path) -> None:
    tone = tmp_path / "tone.wav"
    with wave.open(str(tone), "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(8000)
        samples = [round(9000 * math.sin(2 * math.pi * 440 * i / 8000)) for i in range(3200)]
        writer.writeframes(struct.pack(f"<{len(samples)}h", *samples))
    scene = PortraitScene(duration=.4)
    scene.audio.add(AudioTrack(tone, "music", 0, .4, volume=.5, fade_in=.05, fade_out=.05))
    output = tmp_path / "with-audio.mp4"
    scene.render(output=output, width=90, height=160, fps=10)
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "json", str(output)], capture_output=True, text=True, check=True)
    assert {stream["codec_type"] for stream in json.loads(result.stdout)["streams"]} == {"video", "audio"}


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="FFmpeg unavailable")
def test_missing_audio_keeps_existing_output(tmp_path) -> None:
    output = tmp_path / "existing.mp4"
    output.write_bytes(b"user video")
    scene = PortraitScene(duration=.2)
    scene.audio.add(AudioTrack(tmp_path / "missing.wav", "narration", 0, .2))
    with pytest.raises(FileNotFoundError, match="missing.wav"):
        scene.render(output=output, width=90, height=160, fps=10, overwrite=True)
    assert output.read_bytes() == b"user video"
