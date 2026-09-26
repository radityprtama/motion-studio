import pytest

from motion.primitives import Circle
from motion.renderer import render_frame
from motion.scene import PortraitScene


def test_camera_defaults_and_direct_evaluation() -> None:
    scene = PortraitScene(duration=2)
    assert scene.camera.evaluate(0).x == 540
    assert scene.camera.evaluate(0).y == 960
    assert scene.camera.evaluate(0).zoom == 1
    scene.camera.animate(zoom=(1, 1.2), x=(540, 600), start=0, duration=2)
    at_one = scene.camera.evaluate(1)
    scene.camera.evaluate(0.1)
    assert scene.camera.evaluate(1) == at_one
    assert at_one.zoom == pytest.approx(1.1)
    assert at_one.x == 570


def test_camera_rejects_overlap_and_bad_zoom() -> None:
    scene = PortraitScene(duration=2)
    scene.camera.animate(zoom=(1, 1.2), start=0, duration=1)
    with pytest.raises(ValueError, match="overlap"):
        scene.camera.animate(zoom=(1.2, 1.3), start=0.5, duration=1)
    with pytest.raises(ValueError, match="positive"):
        scene.camera.animate(zoom=(1, 0), start=1, duration=1)


def test_overlay_stays_fixed_when_content_camera_pushes() -> None:
    world = PortraitScene(duration=1)
    world.add(Circle(x=660, y=960, radius=25, fill="#D9A66F", layer="content"))
    world.camera.animate(zoom=(1, 2), start=0, duration=1)
    world_frame = render_frame(world, 1, width=90, height=160)
    assert world_frame.getpixel((65, 80))[:3] == (217, 166, 111)
    assert world_frame.getpixel((55, 80))[:3] != (217, 166, 111)

    overlay = PortraitScene(duration=1)
    overlay.add(Circle(x=660, y=960, radius=25, fill="#D9A66F", layer="overlay"))
    overlay.camera.animate(zoom=(1, 2), start=0, duration=1)
    overlay_frame = render_frame(overlay, 1, width=90, height=160)
    assert overlay_frame.getpixel((55, 80))[:3] == (217, 166, 111)
    assert overlay_frame.getpixel((65, 80))[:3] != (217, 166, 111)
