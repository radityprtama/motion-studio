import pytest

from motion.components import Arrow, CommitGraph, CommitNode, File, Folder, Timeline
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


def test_arrow_node_and_graph_handles() -> None:
    arrow = Arrow(start=(100, 200), end=(300, 400), name="flow")
    assert arrow.anchors["entry"] == (100, 200)
    assert arrow.anchors["exit"] == (300, 400)
    node = CommitNode(x=300, y=400, label="state", name="state")
    assert tuple(node.parts) == ("ring", "core", "label")
    graph = CommitGraph(
        records=(("a", "first", None), ("b", "second", "a"), ("c", "branch", "a")),
        positions={"a": (300, 400), "b": (300, 600), "c": (500, 620)},
        name="history",
    )
    assert "connector:b" in graph.parts
    assert "connector:c" in graph.parts
    assert "node:c:ring" in graph.parts
    assert graph.anchors["node:c"] == (500, 620)


def test_graph_rejects_invalid_relationships() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        CommitGraph(records=(("a", "one", None), ("a", "two", "a")), positions={"a": (1, 2)})
    with pytest.raises(ValueError, match="unknown parent"):
        CommitGraph(records=(("a", "one", None), ("b", "two", "z")), positions={"a": (1, 2), "b": (2, 3)})


def test_timeline_ordering() -> None:
    vertical = Timeline(labels=("start", "middle", "end"), x=100, y=200, gap=150, direction="vertical")
    horizontal = Timeline(labels=("start", "middle", "end"), x=100, y=200, gap=150, direction="horizontal")
    assert vertical.anchors["item:2"] == (100, 500)
    assert horizontal.anchors["item:2"] == (400, 200)
