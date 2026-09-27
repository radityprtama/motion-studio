"""An editable 18-second portrait explanation of how Git stores history."""

from motion import (
    CommitGraph, DrawPath, FadeIn, FadeOut, File, Folder, Move, Path,
    PortraitScene, Rectangle, Text,
)
from motion.style import get_style


scene = PortraitScene(duration=18, fps=30, seed=42, style="blueprint")
ink = get_style(scene.style)

# The reading frame is fixed while the project and history occupy one world.
scene.add(Rectangle(x=101, y=196, width=9, height=70, fill=ink.accent, layer="overlay", name="editorial_mark"))
scene.add(Text("FIELD NOTE  /  01", x=139, y=176, role="annotation", anchor="left", color=ink.accent, layer="overlay", name="eyebrow"))
title = scene.add(Text("How Git stores\nhistory", x=100, y=285, role="headline", anchor="left", layer="overlay", name="title"))
scene.animate(title, FadeIn(start=0.15, duration=0.65))
scene.add(Rectangle(x=540, y=555, width=880, height=2, fill=ink.secondary, layer="overlay", name="title_rule"))
scene.add(Text("STATE  →  SNAPSHOT  →  HISTORY", x=100, y=580, role="label", anchor="left", color=ink.secondary, layer="overlay", name="visual_key"))

captions = (
    ("A project starts as a set of files.", 0.55, 2.75),
    ("Files are the current project state.", 3.2, 5.85),
    ("A commit captures one snapshot.", 6.25, 8.9),
    ("New commits connect into history.", 9.05, 11.85),
    ("A branch starts another path.", 12.15, 14.85),
    ("One history. More than one path.", 15.15, 18.0),
)
for index, (line, begin, end) in enumerate(captions):
    caption = scene.add(Text(line, x=540, y=1615, role="caption", layer="captions", name=f"caption_{index}"))
    scene.animate(caption, FadeIn(start=begin, duration=0.35))
    if end < scene.duration:
        scene.animate(caption, FadeOut(start=end - 0.3, duration=0.3))

folder = Folder(x=540, y=930, width=650, height=500, label="project / working state", style=scene.style, name="project")
folder.add_to(scene)
scene.animate(folder.parts["body"], FadeIn(start=0.45, duration=0.65))
scene.animate(folder.parts["tab"], DrawPath(start=0.75, duration=0.75, easing="ease_out_cubic"))
scene.animate(folder.parts["label"], FadeIn(start=1.25, duration=0.45))

files = []
for index, (filename, x) in enumerate((("main", 355), ("notes", 540), ("config", 725))):
    item = File(x=x, y=905, width=160, height=190, label=filename, style=scene.style, name=f"file_{index}")
    item.add_to(scene)
    start = 3.25 + index * 0.62
    scene.animate(item.parts["body"], FadeIn(start=start, duration=0.4))
    scene.animate(item.parts["body"], Move(start=start, duration=0.5, from_y=965, to_y=905, easing="ease_out_cubic"))
    scene.animate(item.parts["fold"], DrawPath(start=start + 0.18, duration=0.4))
    scene.animate(item.parts["label"], FadeIn(start=start + 0.28, duration=0.3))
    files.append(item)

# A frame and one connector visually capture the working state as a commit.
snapshot = scene.add(Path(
    x=540, y=960, points=((-385, -305), (385, -305), (385, 305), (-385, 305)),
    closed=True, stroke=ink.accent, stroke_width=5, name="snapshot_frame",
))
scene.animate(snapshot, DrawPath(start=6.15, duration=1.1, easing="ease_in_out_cubic"))
scene.animate(snapshot, FadeOut(start=8.4, duration=0.55))
snapshot_label = scene.add(Text("SNAPSHOT / 01", x=795, y=1290, role="label", anchor="right", color=ink.accent, name="snapshot_label"))
scene.animate(snapshot_label, FadeIn(start=6.9, duration=0.4))
scene.animate(snapshot_label, FadeOut(start=8.4, duration=0.55))
capture = scene.add(Path(x=540, y=1265, points=((0, 0), (0, 100)), stroke=ink.accent, stroke_width=5, name="capture_connector"))
scene.animate(capture, DrawPath(start=7.2, duration=0.7))
scene.animate(capture, FadeOut(start=8.7, duration=0.35))

for part in folder.parts.values():
    scene.animate(part, FadeOut(start=8.4, duration=0.55))
for item in files:
    for part in item.parts.values():
        scene.animate(part, FadeOut(start=8.4, duration=0.55))

# Older state begins low; newer state grows upward, like a Git log.
graph = CommitGraph(
    records=(
        ("01", "snapshot 01", None),
        ("02", "change 02", "01"),
        ("03", "change 03", "02"),
        ("04", "change 04", "03"),
        ("branch", "branch", "02"),
    ),
    positions={"01": (540, 1390), "02": (540, 1170), "03": (540, 950), "04": (540, 730), "branch": (780, 1050)},
    style=scene.style,
    name="history",
    radius=31,
)
graph.add_to(scene)
for item_id, start in (("01", 7.8), ("02", 9.75), ("03", 10.55), ("04", 11.35), ("branch", 13.7)):
    for part_name in ("ring", "core", "label"):
        scene.animate(graph.parts[f"node:{item_id}:{part_name}"], FadeIn(start=start, duration=0.34))
for item_id, start, duration in (("02", 9.1, 0.65), ("03", 9.95, 0.6), ("04", 10.75, 0.6), ("branch", 12.45, 1.25)):
    scene.animate(graph.parts[f"connector:{item_id}"], DrawPath(start=start, duration=duration, easing="ease_in_out_cubic"))

scene.camera.animate(y=(960, 1015), zoom=(1, 0.94), start=15.0, duration=1.65, easing="ease_out_cubic")
summary = scene.add(Text("PROJECT  /  COMMITS  /  BRANCH", x=540, y=1510, role="label", layer="overlay", color=ink.accent, name="summary"))
scene.animate(summary, FadeIn(start=15.65, duration=0.5))
