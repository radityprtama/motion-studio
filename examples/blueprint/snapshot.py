"""A commit captures one state of a changing project."""

from motion.animation import FadeIn, Move
from motion.primitives import Circle, Rectangle, Text
from motion.scene import PortraitScene


scene = PortraitScene(duration=4, fps=30, seed=42, style="blueprint")

scene.add(Rectangle(x=101, y=194, width=10, height=70, fill="#D9A66F", name="section_mark"))
scene.add(Text("01 / VERSION CONTROL", x=138, y=174, role="annotation", anchor="left", color="#D9A66F"))
headline = scene.add(
    Text("A commit saves\none project state.", x=100, y=290, role="headline", anchor="left", name="headline")
)
scene.animate(headline, FadeIn(start=0, duration=0.5))
scene.add(Rectangle(x=540, y=555, width=880, height=2, fill="#527B93"))

project = scene.add(
    Rectangle(x=540, y=915, width=735, height=545, stroke="#F2EBDD", stroke_width=3, name="project_frame")
)
scene.animate(project, FadeIn(start=0.2, duration=0.6))
project_label = scene.add(
    Text("PROJECT / NOW", x=205, y=680, role="annotation", anchor="left", color="#F2EBDD")
)
scene.animate(project_label, FadeIn(start=0.2, duration=0.6))

for index, filename in enumerate(("main.py", "notes.md", "config.toml")):
    y = 805 + index * 124
    start = 0.45 + index * 0.28
    strip = scene.add(
        Rectangle(x=540, y=y, width=590, height=84, fill="#193247", stroke="#527B93", name=f"file_{index}")
    )
    label = scene.add(
        Text(filename, x=295, y=y - 21, role="annotation", anchor="left", name=f"file_label_{index}")
    )
    scene.animate(strip, Move(start=start, duration=0.55, from_x=850, to_x=540, easing="ease_out"))
    scene.animate(strip, FadeIn(start=start, duration=0.45))
    scene.animate(label, Move(start=start, duration=0.55, from_x=605, to_x=295, easing="ease_out"))
    scene.animate(label, FadeIn(start=start, duration=0.45))

connector = scene.add(Rectangle(x=540, y=1230, width=3, height=90, fill="#F2EBDD", name="connector"))
scene.animate(connector, FadeIn(start=2.15, duration=0.35))
commit = scene.add(Circle(x=540, y=1370, radius=88, fill="#D9A66F", name="commit"))
scene.animate(commit, Move(start=2.2, duration=0.75, from_y=1435, to_y=1370, easing="ease_out"))
scene.animate(commit, FadeIn(start=2.2, duration=0.5))
number = scene.add(Text("01", x=540, y=1347, role="body", color="#0D1D2B", name="commit_number"))
scene.animate(number, FadeIn(start=2.6, duration=0.35))
label = scene.add(Text("COMMIT / SNAPSHOT", x=540, y=1515, role="annotation", name="commit_label"))
scene.animate(label, FadeIn(start=2.8, duration=0.4))
