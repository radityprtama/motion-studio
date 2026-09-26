import pytest

from motion.animation import FadeIn, FadeOut, Move, ease, progress


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
