from motion import Badge, Browser, Card, Chart, Circle, Component, Computer, Graph, Label, ObjectGrid, PortraitScene, Quote, Server, Terminal
from motion.layout import Box
from motion.renderer import render_frame


def test_extended_components_are_named_and_renderable() -> None:
    scene = PortraitScene(duration=1)
    components = (
        Card(x=300, y=300, width=360, height=250, title="State"),
        Computer(x=740, y=300, width=240, name="computer"),
        Server(x=220, y=790, width=170, height=260, label="Node", name="server"),
        Terminal(x=700, y=730, width=440, height=250, lines=("build", "complete"), name="terminal"),
        Browser(x=300, y=1250, width=380, height=250, title="docs", name="browser"),
        Chart(box=Box(560, 1050, 960, 1370), values=(1, 3, 2), labels=("A", "B", "C"), name="chart"),
        Badge(x=240, y=1600, text="READY", name="badge"),
        Label(x=550, y=1600, text="REFERENCE", name="label"),
    )
    for component in components:
        component.add_to(scene)
        assert all(part.name for part in component.parts.values())
    assert render_frame(scene, .5, width=180, height=320).size == (180, 320)


def test_graph_and_quote_have_semantic_parts() -> None:
    graph = Graph(nodes={"a": (200, 300), "b": (500, 600)}, edges=(("a", "b"),))
    quote = Quote(x=540, y=1000, width=600, text="Keep the signal clear.", attribution="Motion principle")
    assert "edge:0" in graph.parts and "node:a" in graph.parts
    assert "text" in quote.parts and "attribution" in quote.parts


def test_object_grid_repeats_with_explicit_stable_seeds() -> None:
    used = []
    def item(index, x, y, seed):
        used.append(seed)
        return Component({"disc": Circle(x=x, y=y, radius=12, name=f"disc:{index}")}, Box(x - 12, y - 12, x + 12, y + 12), {"center": (x, y)})
    first = ObjectGrid(box=Box(100, 100, 300, 300), rows=2, columns=2, seed=42, item_factory=item)
    seeds = tuple(used)
    used.clear()
    second = ObjectGrid(box=Box(100, 100, 300, 300), rows=2, columns=2, seed=42, item_factory=item)
    assert tuple(used) == seeds and len(set(seeds)) == 4
    assert first.anchors == second.anchors
    assert len(first.parts) == 4
