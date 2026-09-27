from pathlib import Path

from PIL import Image
import pytest
import shutil
import subprocess
import json

from motion.cli import load_scene, main
from motion.config import load_config
from motion.inspect import render_contact_sheet
from motion.scene import PortraitScene


def test_config_scene_factory_and_cli_override(tmp_path: Path) -> None:
    config_path = tmp_path / "motion.toml"
    config_path.write_text('[project]\ndefault_style = "cinematic"\n[render]\nwidth = 540\nheight = 960\nfps = 24\n[preview]\nwidth = 180\nheight = 320\nfps = 12\n')
    source = tmp_path / "scene.py"
    source.write_text('from motion import PortraitScene, Circle\ndef build_scene(config):\n    scene = PortraitScene.from_config(config, duration=1, fps=25)\n    scene.add(Circle(x=270, y=480, radius=50))\n    return scene\n')
    config = load_config(scene_path=source)
    scene = load_scene(source, config)
    assert (scene.width, scene.height, scene.fps, scene.style) == (540, 960, 25, "cinematic")
    output = tmp_path / "frame.png"
    assert main(["still", str(source), "--time", "0.5", "--resolution", "90x160", "--output", str(output)]) == 0
    with Image.open(output) as image:
        assert image.size == (90, 160)


def test_contact_sheet_renders_direct_times_and_protects_output(tmp_path: Path) -> None:
    scene = PortraitScene(duration=2)
    output = tmp_path / "sheet.png"
    render_contact_sheet(scene, times=(2, 0, 1), output=output, width=90, height=160)
    with Image.open(output) as image:
        assert image.size == (334, 226)
    before = output.read_bytes()
    with pytest.raises(FileExistsError):
        render_contact_sheet(scene, times=(0,), output=output, width=90, height=160)
    assert output.read_bytes() == before


def test_invalid_project_setting_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "motion.toml"
    source.write_text("[render]\nfps = 0\n")
    with pytest.raises(ValueError, match="positive"):
        load_config(source)


@pytest.mark.skipif(not shutil.which("ffprobe"), reason="ffprobe unavailable")
def test_preview_config_then_cli_output_override(tmp_path: Path) -> None:
    (tmp_path / "motion.toml").write_text("[preview]\nwidth = 180\nheight = 320\nfps = 12\n")
    source = tmp_path / "scene.py"
    source.write_text("from motion import PortraitScene\nscene = PortraitScene(duration=.25)\n")
    configured = tmp_path / "configured.mp4"
    assert main(["preview", str(source), "--output", str(configured)]) == 0
    overridden = tmp_path / "overridden.mp4"
    assert main(["preview", str(source), "--resolution", "90x160", "--fps", "8", "--output", str(overridden)]) == 0
    def stream(path):
        result = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate", "-of", "json", str(path)], capture_output=True, text=True, check=True)
        return json.loads(result.stdout)["streams"][0]
    assert (stream(configured)["width"], stream(configured)["height"], stream(configured)["r_frame_rate"]) == (180, 320, "12/1")
    assert (stream(overridden)["width"], stream(overridden)["height"], stream(overridden)["r_frame_rate"]) == (90, 160, "8/1")
