import pytest

from motion.animation import FadeIn, FadeOut, Keyframe, Keyframes, Move, ease, progress
from motion.primitives import Circle
from motion.scene import PortraitScene


def test_progress_boundaries() -> None:
    assert progress(1.0, start=2.0, duration=1.0) == 0.0
    assert progress(2.0, start=2.0, duration=1.0) == 0.0
    assert progress(2.5, start=2.0, duration=1.0) == 0.5
    assert progress(3.0, start=2.0, duration=1.0) == 1.0
    assert progress(4.0, start=2.0, duration=1.0) == 1.0


@pytest.mark.parametrize("name", ["linear", "ease_in", "ease_out", "ease_in_out"])
def test_easing_endpoints(name: str) -> None:
    assert ease(name, 0.0) == 0.0
    assert ease(name, 1.0) == 1.0


def test_move_and_fade_at_arbitrary_time() -> None:
    move = Move(start=0, duration=1, from_x=0, to_x=100)
    fade = FadeIn(start=1, duration=1)
    assert move.value("x", 0.5, 10) == 50
    assert fade.value("opacity", 0, 0.8) == 0
    assert fade.value("opacity", 2, 0.8) == 0.8
    assert FadeOut(start=1, duration=1).value("opacity", 2, 0.8) == 0


def test_invalid_animation_values() -> None:
    with pytest.raises(ValueError, match="duration"):
        Move(duration=0, from_x=0, to_x=10)
    with pytest.raises(ValueError, match="both"):
        Move(from_x=0)
    with pytest.raises(ValueError, match="axis"):
        Move()
    with pytest.raises(ValueError, match="easing"):
        FadeIn(easing="unknown")


def test_keyframes_are_direct_time_and_validate_channels() -> None:
    motion = Keyframes(channel="x", points=(Keyframe(0, 0), Keyframe(.5, 100), Keyframe(1, 50)), start=2, duration=2)
    assert motion.value("x", 2, 0) == 0
    assert motion.value("x", 3, 0) == 100
    assert motion.value("x", 3.5, 0) == 75
    assert motion.value("x", 4, 0) == 50
    scene = PortraitScene(duration=5)
    dot = scene.add(Circle(x=0, y=960, radius=20))
    scene.animate(dot, motion)
    assert scene.elements_at(3.5)[0].x == 75
    with pytest.raises(ValueError, match="strictly increasing"):
        Keyframes(channel="x", points=(Keyframe(0, 0), Keyframe(.5, 1), Keyframe(.5, 2), Keyframe(1, 3)))
    with pytest.raises(ValueError, match="opacity"):
        Keyframes(channel="opacity", points=(Keyframe(0, 0), Keyframe(1, 2)))
