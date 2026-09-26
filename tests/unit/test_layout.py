import pytest

from motion.layout import Box, grid, place, stack
from motion.scene import PortraitScene


def test_box_anchors_and_safe_area() -> None:
    box = Box(90, 120, 990, 1700)
    assert box.center == (540, 910)
    assert box.inset(10) == Box(100, 130, 980, 1690)
    assert place(box, 100, 50, "center") == (490, 885)
    assert place(box, 100, 50, "bottom_right") == (890, 1650)
    scene = PortraitScene(duration=1)
    assert scene.safe_box == Box(*scene.content_box)


def test_stack_and_grid_fit() -> None:
    box = Box(0, 0, 300, 300)
    assert stack(box, [(100, 100), (100, 100)], gap=20) == (
        Box(100, 0, 200, 100),
        Box(100, 120, 200, 220),
    )
    assert grid(box, rows=2, columns=2, gap_x=20, gap_y=20) == (
        Box(0, 0, 140, 140), Box(160, 0, 300, 140),
        Box(0, 160, 140, 300), Box(160, 160, 300, 300),
    )


def test_overflow_names_available_bounds() -> None:
    with pytest.raises(ValueError, match="available 100x100"):
        stack(Box(0, 0, 100, 100), [(80, 80), (80, 80)], gap=10)
    with pytest.raises(ValueError, match="available 100x100"):
        grid(Box(0, 0, 100, 100), rows=2, columns=2, gap_x=120)
