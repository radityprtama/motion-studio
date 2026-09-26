"""The same procedural vocabulary in the warm paper Blueprint treatment."""

from motion import Arrow, CommitNode, FadeIn, Folder, PortraitScene, Text
from motion.style import get_style


scene = PortraitScene(duration=5, seed=42, style="blueprint-paper")
ink = get_style(scene.style)
scene.add(Text("Project state", x=100, y=260, role="headline", anchor="left", color=ink.primary, name="title"))
scene.add(Text("A saved state becomes a point in history.", x=100, y=405, role="body", anchor="left", max_width=830, color=ink.secondary, name="subhead"))
folder = Folder(x=540, y=810, width=640, label="project", style=scene.style, name="project")
folder.add_to(scene)
arrow = Arrow(start=(540, 1060), end=(540, 1250), style=scene.style, name="becomes")
arrow.add_to(scene)
node = CommitNode(x=540, y=1350, label="saved state", style=scene.style, name="state")
node.add_to(scene)
for part in folder.parts.values():
    scene.animate(part, FadeIn(start=0.2, duration=0.6))
for part in arrow.parts.values():
    scene.animate(part, FadeIn(start=1.5, duration=0.5))
for part in node.parts.values():
    scene.animate(part, FadeIn(start=2.3, duration=0.5))
