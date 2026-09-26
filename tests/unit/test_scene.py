import pytest

from motion.animation import FadeIn, FadeOut, Move
from motion.primitives import Circle, Rectangle, Text
from motion.scene import PortraitScene


def test_safe_area_and_ordering() -> None:
    scene = PortraitScene(duration=2)
    assert scene.content_box == (90, 120, 990, 1700)
    top = Text("top", x=0, y=0, layer="captions")
    middle = Circle(x=0, y=0, radius=10, z_index=1)
    first = Rectangle(x=0, y=0, width=10, height=10)
    second = Rectangle(x=0, y=0, width=10, height=10)
    for element in (top, middle, first, second):
        scene.add(element)
    assert [state.element for state in scene.elements_at(0)] == [first, second, middle, top]


def test_evaluation_is_independent_of_request_order() -> None:
    scene = PortraitScene(duration=3)
    dot = scene.add(Circle(x=10, y=20, radius=10))
    scene.animate(dot, Move(start=0, duration=2, from_x=10, to_x=110))
    scene.animate(dot, FadeIn(start=0.5, duration=0.5))
    at_one = scene.elements_at(1)[0]
    scene.elements_at(0.1)
    assert scene.elements_at(1)[0] == at_one
    assert at_one.x == 60
    assert at_one.opacity == 1


def test_overlapping_channels_rejected_but_adjacent_allowed() -> None:
    scene = PortraitScene(duration=4)
    dot = scene.add(Circle(x=0, y=0, radius=10))
    scene.animate(dot, FadeIn(start=0, duration=1))
    with pytest.raises(ValueError, match="overlap"):
        scene.animate(dot, FadeOut(start=0.5, duration=1))
    scene.animate(dot, FadeOut(start=1, duration=1))
    assert scene.elements_at(1.5)[0].opacity == 0.5


def test_duplicate_names_rejected() -> None:
    scene = PortraitScene(duration=1)
    scene.add(Circle(x=0, y=0, radius=1, name="dot"))
    with pytest.raises(ValueError, match="Duplicate"):
        scene.add(Circle(x=1, y=1, radius=1, name="dot"))
