"""A seeded grid establishes a group before one node receives focus."""

from random import Random

from motion import Box, Circle, Component, FadeIn, ObjectGrid, PortraitScene, RadialLight, Scale, Text
from motion.style import get_style


scene = PortraitScene(duration=6, style="cinematic", seed=24)
ink = get_style(scene.style)
scene.add(Text("PROCEDURAL STUDY  /  36", x=105, y=190, role="annotation", anchor="left", color=ink.accent, name="eyebrow"))
heading = scene.add(Text("One among thirty-six.", x=100, y=285, role="headline", max_width=880, anchor="left", name="heading"))
scene.animate(heading, FadeIn(start=.2, duration=.6))


def make_node(index: int, x: float, y: float, seed: int) -> Component:
    radius = Random(seed).uniform(24, 30)
    parts = {"disc": Circle(x=x, y=y, radius=radius, fill=ink.secondary, opacity=.55, name=f"node:{index}:disc")}
    if index == 14:
        parts["halo"] = RadialLight(x=x, y=y, radius=92, center_color=ink.accent + "88", edge_color=ink.accent + "00", intensity=.4, name="focus:halo", layer="environment")
        parts["ring"] = Circle(x=x, y=y, radius=radius + 12, fill=None, stroke=ink.accent, stroke_width=3, name="focus:ring")
    return Component(parts, Box(x - 92, y - 92, x + 92, y + 92), {"center": (x, y)})


nodes = ObjectGrid(box=Box(150, 620, 930, 1400), rows=6, columns=6, seed=scene.seed, item_factory=make_node)
nodes.add_to(scene)
discs = [nodes.parts[f"item:{index}:disc"] for index in range(36)]
scene.stagger(discs, FadeIn(duration=.24), start=.75, step=.045)
scene.animate(nodes.parts["item:14:halo"], FadeIn(start=3.25, duration=.7))
scene.animate(nodes.parts["item:14:ring"], FadeIn(start=3.25, duration=.5))
scene.animate(nodes.parts["item:14:ring"], Scale(start=3.25, duration=.65, from_x=.85, to_x=1, from_y=.85, to_y=1))
label = scene.add(Text("1 / 36 IN FOCUS", x=540, y=1550, role="title", color=ink.accent, name="focus:label", layer="overlay"))
scene.animate(label, FadeIn(start=4.0, duration=.55))
scene.camera.animate(zoom=(1, 1.035), start=3.4, duration=2.0, easing="ease_out_cubic")
