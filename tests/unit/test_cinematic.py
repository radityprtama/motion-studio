from hashlib import sha256
from pathlib import Path

import pytest
from PIL import Image

from motion.cli import load_scene
from motion.effects import finish_frame
from motion.primitives import ParticleEmitter, RadialLight
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


def test_particles_are_bounded_and_direct_time() -> None:
    emitter = ParticleEmitter(x=540, y=960, width=600, height=800, count=40, seed=42)
    at_two = emitter.particles_at(2.5)
    emitter.particles_at(0.1)
    assert emitter.particles_at(2.5) == at_two
    assert len(at_two) == 40
    assert all(-300 <= p.x < 300 and -400 <= p.y < 400 for p in at_two)
    assert ParticleEmitter(x=540, y=960, width=600, height=800, count=40, seed=43).particles_at(2.5) != at_two


def test_particle_parameters_and_time_are_validated() -> None:
    with pytest.raises(ValueError, match="count"):
        ParticleEmitter(x=0, y=0, width=100, height=100, count=401, seed=1)
    with pytest.raises(ValueError, match="width"):
        ParticleEmitter(x=0, y=0, width=0, height=100, count=1, seed=1)
    with pytest.raises(ValueError, match="seed"):
        ParticleEmitter(x=0, y=0, width=100, height=100, count=1, seed=1.2)
    with pytest.raises(ValueError, match="time"):
        ParticleEmitter(x=0, y=0, width=100, height=100, count=1, seed=1).particles_at(-1)


def test_particle_frame_is_random_access() -> None:
    scene = PortraitScene(duration=3, style="cinematic", seed=42)
    scene.add(ParticleEmitter(x=540, y=960, width=800, height=1200, count=20, seed=42, name="stars"))
    at_two = render_frame(scene, 2, width=90, height=160).tobytes()
    render_frame(scene, 0.25, width=90, height=160)
    assert render_frame(scene, 2, width=90, height=160).tobytes() == at_two


def test_finishing_is_seeded_and_preserves_alpha() -> None:
    style = get_style("cinematic")
    base = Image.new("RGBA", (90, 160), (12, 24, 36, 255))
    first = finish_frame(base, style=style, seed=42)
    assert first.tobytes() == finish_frame(base, style=style, seed=42).tobytes()
    assert first.tobytes() != finish_frame(base, style=style, seed=43).tobytes()
    assert first.getpixel((45, 80))[3] == 255
    assert first.getpixel((0, 0))[3] == 255
    assert finish_frame(base, style=get_style("blueprint"), seed=42).tobytes() == base.tobytes()
