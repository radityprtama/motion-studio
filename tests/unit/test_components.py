import pytest

from motion.components import File, Folder
from motion.renderer import render_frame
from motion.scene import PortraitScene
from motion.style import get_style


def test_folder_parts_and_style_independence() -> None:
    navy = Folder(x=540, y=800, width=620, label="project", style="blueprint", name="folder")
    paper = Folder(x=540, y=800, width=620, label="project", style="blueprint-paper", name="folder")
    assert tuple(navy.parts) == ("body", "tab", "label")
    assert navy.anchors["tab_center"] == paper.anchors["tab_center"]
    assert navy.bounds == paper.bounds
    assert [part.name for part in navy.parts.values()] == ["folder:body", "folder:tab", "folder:label"]
    first = PortraitScene(duration=1, style="blueprint")
    second = PortraitScene(duration=1, style="blueprint-paper")
    navy.add_to(first)
    paper.add_to(second)
    assert render_frame(first, 0, width=90, height=160).tobytes() != render_frame(second, 0, width=90, height=160).tobytes()


def test_file_label_fit() -> None:
    file = File(x=200, y=300, width=180, height=240, label="README", name="readme")
    assert "fold" in file.parts
    with pytest.raises(ValueError, match="File label"):
        File(x=200, y=300, width=80, height=120, label="A very long filename")


def test_paper_style_tokens() -> None:
    paper = get_style("blueprint-paper")
    assert paper.background == "#F2EBDD"
    assert paper.primary == "#0D1D2B"
