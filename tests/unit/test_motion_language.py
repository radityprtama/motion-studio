import pytest

from motion.animation import FadeIn, FadeOut, Move, Rotate, Scale, ease
from motion.composition import Parallel, Sequence, expand
from motion.primitives import Circle
from motion.scene import PortraitScene


def test_new_easings() -> None:
    assert ease("ease_out_cubic", 0.5) == 0.875
    for name in ("ease_out_cubic", "ease_in_out_cubic", "ease_out_back"):
        assert ease(name, 0) == 0
        assert ease(name, 1) == 1
    assert ease("ease_out_back", 0.8) > 1


def test_scale_and_rotation_at_arbitrary_time() -> None:
    scene = PortraitScene(duration=2)
    dot = scene.add(Circle(x=540, y=960, radius=20))
    scene.animate(dot, Scale(start=0, duration=2, from_x=1, to_x=2, from_y=1, to_y=0.5))
    scene.animate(dot, Rotate(start=0, duration=2, from_angle=0, to_angle=90))
    state = scene.elements_at(1)[0]
    assert (state.scale_x, state.scale_y, state.rotation) == (1.5, 0.75, 45)
    scene.elements_at(0)
    assert scene.elements_at(1)[0] == state


def test_invalid_scale_rejected() -> None:
    with pytest.raises(ValueError, match="positive"):
        Circle(x=0, y=0, radius=1, scale_x=0)
    with pytest.raises(ValueError, match="positive"):
        Scale(from_x=1, to_x=0)


def test_sequence_and_parallel_offsets() -> None:
    sequence = Sequence(
        FadeIn(duration=0.4),
        Move(duration=0.7, from_y=80, to_y=0),
        start=1,
    )
    leaves, end = expand(sequence)
    assert [leaf.start for leaf in leaves] == [1.0, 1.4]
    assert end == pytest.approx(2.1)
    parallel = Parallel(
        FadeIn(start=0.2),
        Move(start=0.1, from_y=80, to_y=0),
        start=1,
    )
    leaves, end = expand(parallel)
    assert [leaf.start for leaf in leaves] == [1.2, 1.1]
    assert end == pytest.approx(2.2)


def test_nested_composition_and_atomic_failure() -> None:
    nested = Sequence(
        Parallel(FadeIn(duration=0.4), Move(duration=0.7, from_y=10, to_y=0)),
        FadeOut(duration=0.3),
        start=1,
    )
    leaves, end = expand(nested)
    assert [leaf.start for leaf in leaves] == [1, 1, 1.7]
    assert end == 2
    scene = PortraitScene(duration=3)
    first = scene.add(Circle(x=0, y=0, radius=1))
    second = scene.add(Circle(x=10, y=0, radius=1))
    scene.animate(first, FadeIn(start=0, duration=1))
    with pytest.raises(ValueError, match="overlap"):
        scene.stagger((second, first), FadeIn(duration=0.7), step=0.1)
    assert scene.elements_at(0.2)[1].opacity == 1
