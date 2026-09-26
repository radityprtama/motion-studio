from hashlib import sha256
from pathlib import Path

import pytest

from motion.cli import load_scene
from motion.primitives import RadialLight
from motion.renderer import render_frame
from motion.scene import PortraitScene
from motion.style import get_style


def test_cinematic_tokens_and_light_validation() -> None:
    style = get_style("cinematic")
    assert style.background == "#08121E"
    assert style.background_treatment == "cinematic"
    with pytest.raises(ValueError, match="RadialLight radius"):
        RadialLight(x=0, y=0, radius=0)


def test_cinematic_background_and_light_are_visible() -> None:
    empty = PortraitScene(duration=1, style="cinematic")
    lit = PortraitScene(duration=1, style="cinematic")
    lit.add(RadialLight(x=540, y=960, radius=350, name="light"))
    base = render_frame(empty, 0, width=90, height=160)
    with_light = render_frame(lit, 0, width=90, height=160)
    assert base.getpixel((45, 80)) != base.getpixel((0, 0))
    assert base.getpixel((45, 80)) != with_light.getpixel((45, 80))


def test_blueprint_snapshot_baseline() -> None:
    scene = load_scene(Path("examples/blueprint/snapshot.py"))
    digest = sha256(render_frame(scene, 2, width=360, height=640).tobytes()).hexdigest()
    assert digest == "a6a447d59d569b5f0622a02b7990aa4e3558c82766abf0413cdcf622eeb78cb9"
