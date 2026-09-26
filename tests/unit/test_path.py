import pytest

from motion.animation import DrawPath, MaskReveal, Reveal
from motion.primitives import Circle, Path, Rectangle, partial_points
from motion.renderer import render_frame
from motion.scene import PortraitScene


def test_partial_path_uses_measured_length() -> None:
    points = ((0, 0), (30, 0), (30, 70))
    assert partial_points(points, 0) == ((0, 0),)
    assert partial_points(points, 0.5) == ((0, 0), (30, 0), (30, 20))
    assert partial_points(points, 1) == points
    assert partial_points(((0, 0), (0, 0), (10, 0)), 0.5) == ((0, 0), (5, 0))


def test_invalid_path_and_draw_attachment() -> None:
    with pytest.raises(ValueError, match="two"):
        Path(x=0, y=0, points=((0, 0),))
    with pytest.raises(ValueError, match="positive"):
        Path(x=0, y=0, points=((0, 0), (0, 0)))
    scene = PortraitScene(duration=1)
    circle = scene.add(Circle(x=0, y=0, radius=10))
    with pytest.raises(ValueError, match="Path"):
        scene.animate(circle, DrawPath(duration=1))


def test_reveal_and_mask_clip_pixels() -> None:
    scene = PortraitScene(duration=1)
    box = scene.add(Rectangle(x=540, y=960, width=400, height=200, fill="#D9A66F"))
    scene.animate(box, Reveal(direction="left", duration=1))
    frame = render_frame(scene, 0.5, width=90, height=160)
    assert frame.getpixel((35, 80))[:3] == (217, 166, 111)
    assert frame.getpixel((55, 80))[:3] != (217, 166, 111)

    masked = PortraitScene(duration=1)
    target = masked.add(Rectangle(x=540, y=960, width=600, height=600, fill="#D9A66F"))
    masked.animate(target, MaskReveal(mask=Circle(x=540, y=960, radius=200), duration=1))
    frame = render_frame(masked, 0.5, width=90, height=160)
    assert frame.getpixel((45, 80))[:3] == (217, 166, 111)
    assert frame.getpixel((57, 80))[:3] != (217, 166, 111)
    full = render_frame(masked, 1, width=90, height=160)
    assert full.getpixel((45, 80))[:3] == (217, 166, 111)
    assert full.getpixel((60, 95))[:3] != (217, 166, 111)


def test_mask_type_rejected() -> None:
    with pytest.raises(TypeError, match="Rectangle or Circle"):
        MaskReveal(mask=object())
