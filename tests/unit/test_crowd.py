import pytest

from motion.components import Crowd, Orb, Person
from motion.layout import Box
from motion.primitives import Path
from motion.renderer import render_frame
from motion.scene import PortraitScene


def test_orb_and_person_parts() -> None:
    orb = Orb(x=540, y=900, diameter=300, name="subject")
    assert tuple(orb.parts) == ("halo", "disc", "rim", "highlight")
    assert orb.anchors["center"] == (540, 900)
    person = Person(x=100, y=200, height=90, pose_variant=1, name="viewer")
    assert tuple(person.parts) == ("body", "head")
    assert person.parts["body"].fill is not None
    assert person.parts["body"].stroke is None
    with pytest.raises(ValueError, match="pose_variant"):
        Person(x=0, y=0, height=90, pose_variant=8)


def test_crowd_is_seeded_and_addressable() -> None:
    kwargs = dict(box=Box(90, 700, 990, 1440), count=100, columns=10, seed=42, highlighted=tuple(range(17)), name="people")
    first = Crowd(**kwargs)
    second = Crowd(**kwargs)
    assert tuple(first.parts) == tuple(second.parts)
    assert first.anchors == second.anchors
    assert "person:99:head" in first.parts
    assert "highlight:16:body" in first.parts
    assert "highlight:17:body" not in first.parts
    assert len([key for key in first.parts if key.startswith("highlight:")]) == 34
    assert first.anchors["person:0"][1] < first.anchors["person:90"][1]


def test_crowd_rejects_invalid_layout_and_indices() -> None:
    box = Box(0, 0, 900, 700)
    with pytest.raises(ValueError, match="highlighted"):
        Crowd(box=box, count=100, columns=10, seed=42, highlighted=(100,))
    with pytest.raises(ValueError, match="count"):
        Crowd(box=box, count=401, columns=10, seed=42)
    with pytest.raises(ValueError, match="too small"):
        Crowd(box=Box(0, 0, 100, 100), count=100, columns=10, seed=42)


def test_filled_path_has_no_implicit_outline() -> None:
    plain = PortraitScene(duration=1)
    outlined = PortraitScene(duration=1)
    points = ((-80, -80), (80, -80), (0, 80))
    plain.add(Path(x=540, y=960, points=points, closed=True, fill="#334455"))
    outlined.add(Path(x=540, y=960, points=points, closed=True, fill="#334455", stroke="#F2EBDD"))
    assert render_frame(plain, 0, width=90, height=160).tobytes() != render_frame(outlined, 0, width=90, height=160).tobytes()
