"""A vertical Git history grows a branch without changing visual worlds."""

from motion import (
    Circle,
    DrawPath,
    FadeIn,
    Move,
    Parallel,
    Path,
    PortraitScene,
    Rectangle,
    Scale,
    Text,
)


scene = PortraitScene(duration=6, fps=30, seed=42, style="blueprint")

scene.add(Rectangle(x=101, y=194, width=10, height=70, fill="#D9A66F", layer="overlay"))
scene.add(
    Text("02 / PROJECT HISTORY", x=138, y=174, role="annotation", anchor="left", color="#D9A66F", layer="overlay")
)
title = scene.add(Text("History can branch.", x=100, y=280, role="headline", anchor="left", layer="overlay"))
scene.animate(
    title,
    Parallel(
        FadeIn(duration=0.45),
        Move(duration=0.65, from_y=320, to_y=280, easing="ease_out_cubic"),
        start=0.1,
    ),
)
scene.add(Rectangle(x=540, y=520, width=880, height=2, fill="#527B93", layer="overlay"))

main_line = scene.add(
    Path(x=410, y=700, points=((0, 0), (0, 720)), stroke="#F2EBDD", stroke_width=5, name="main_history")
)
scene.animate(main_line, DrawPath(start=0.6, duration=2.8, easing="ease_in_out"))

node_positions = (700, 940, 1180, 1420)
nodes = []
for index, y in enumerate(node_positions, start=1):
    node = scene.add(
        Circle(x=410, y=y, radius=32, fill="#0D1D2B", stroke="#F2EBDD", stroke_width=5, name=f"commit_{index}")
    )
    label_x = 350 if index == 2 else 485
    label_anchor = "right" if index == 2 else "left"
    label = scene.add(
        Text(f"commit {index:02d}", x=label_x, y=y - 17, role="annotation", anchor=label_anchor, name=f"commit_label_{index}")
    )
    scene.animate(label, FadeIn(start=0.75 + (index - 1) * 0.7, duration=0.35))
    nodes.append(node)
scene.stagger(nodes, FadeIn(duration=0.35), start=0.75, step=0.7)

branch = scene.add(
    Path(
        x=410,
        y=940,
        points=((0, 0), (285, 0), (285, 280)),
        stroke="#D9A66F",
        stroke_width=6,
        name="branch_path",
    )
)
scene.animate(branch, DrawPath(start=3.45, duration=1.15, easing="ease_in_out"))
branch_node = scene.add(
    Circle(x=695, y=1220, radius=40, fill="#D9A66F", name="branch_commit")
)
scene.animate(branch_node, FadeIn(start=4.45, duration=0.4))
scene.animate(branch_node, Scale(start=4.45, duration=0.5, from_x=0.78, to_x=1, from_y=0.78, to_y=1, easing="ease_out_cubic"))
branch_label = scene.add(
    Text("branch", x=755, y=1202, role="annotation", anchor="left", color="#D9A66F", name="branch_label")
)
scene.animate(branch_label, FadeIn(start=4.6, duration=0.4))

scene.camera.animate(
    y=(960, 1040), zoom=(1, 1.08), start=4.35, duration=1.55, easing="ease_out_cubic"
)
ending = scene.add(
    Text("ONE HISTORY  /  TWO PATHS", x=540, y=1580, role="annotation", layer="captions", name="ending")
)
scene.animate(ending, FadeIn(start=5.0, duration=0.45))
