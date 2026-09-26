from motion.animation import FadeIn, Move
from motion.primitives import Circle, Rectangle, Text
from motion.renderer import render_frame
from motion.scene import PortraitScene


def make_scene(seed: int) -> PortraitScene:
    scene = PortraitScene(duration=2, seed=seed)
    frame = scene.add(Rectangle(x=540, y=960, width=400, height=500, stroke="#F2EBDD"))
    title = scene.add(Text("A saved state", x=540, y=300, role="headline", max_width=800))
    dot = scene.add(Circle(x=540, y=1000, radius=60, fill="#D9A66F"))
    scene.animate(frame, FadeIn(start=0, duration=0.5))
    scene.animate(title, FadeIn(start=0.2, duration=0.5))
    scene.animate(dot, Move(start=0, duration=1, from_y=1100, to_y=1000))
    return scene


def test_frame_is_random_access_and_seeded() -> None:
    scene = make_scene(42)
    first = render_frame(scene, 1.5, width=90, height=160).tobytes()
    render_frame(scene, 0.1, width=90, height=160)
    assert render_frame(scene, 1.5, width=90, height=160).tobytes() == first
    assert render_frame(make_scene(43), 1.5, width=90, height=160).tobytes() != first


def test_preview_keeps_design_coordinates() -> None:
    scene = PortraitScene(duration=1)
    scene.add(Circle(x=540, y=960, radius=120, fill="#D9A66F"))
    frame = render_frame(scene, 0, width=90, height=160)
    assert frame.size == (90, 160)
    assert frame.getpixel((45, 80))[:3] == (217, 166, 111)
