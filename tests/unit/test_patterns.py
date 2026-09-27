from motion import (
    ComparisonScene, CrowdScene, EditorialScene, FlowScene, GraphScene,
    HierarchyScene, ProcessScene, QuoteScene, StatisticsScene, TimelineScene,
)
from motion.renderer import render_frame


def test_semantic_patterns_render_in_both_styles() -> None:
    scenes = (
        ComparisonScene(left="17", right="83", left_label="active", right_label="other", title="Two groups"),
        ProcessScene(steps=("Write", "Commit", "Branch"), title="A process"),
        TimelineScene(events=("Start", "Middle", "End"), title="Events"),
        GraphScene(nodes={"a": (250, 700), "b": (600, 950)}, edges=(("a", "b"),), title="Network"),
        CrowdScene(count=20, highlighted=4, title="Four of twenty"),
        StatisticsScene(values=(3, 5, 2), labels=("A", "B", "C"), title="Counts"),
        EditorialScene(headline="One clear idea", body="A quiet explanation"),
        QuoteScene(text="A scene can teach.", attribution="Motion Studio"),
        HierarchyScene(levels=("Source", "Service", "Client"), title="Layers"),
        FlowScene(steps=("Input", "Compute", "Output"), title="Flow"),
    )
    for scene in scenes:
        frame = render_frame(scene, min(scene.duration, 2.5), width=90, height=160)
        assert frame.size == (90, 160)
    assert scenes[0].style == "blueprint"
    assert scenes[4].style == "cinematic"
    alternate = StatisticsScene(values=(3, 5, 2), labels=("A", "B", "C"), title="Counts", style="cinematic")
    assert render_frame(alternate, 2.5, width=90, height=160).tobytes() != render_frame(scenes[5], 2.5, width=90, height=160).tobytes()
