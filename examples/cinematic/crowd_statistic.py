"""A seeded 100-person crowd resolves into a clear 17-of-100 statistic."""

from motion import Box, Crowd, FadeIn, ParticleEmitter, PortraitScene, Scale, Text
from motion.style import get_style


scene = PortraitScene(duration=7, fps=30, seed=42, style="cinematic")
ink = get_style(scene.style)

scene.add(ParticleEmitter(
    x=540, y=960, width=1080, height=1740, count=25, seed=38,
    radius_range=(1.0, 2.5), velocity=(-3, 3, -7, 1),
    color=ink.secondary, opacity=.28, layer="environment", name="quiet_particles",
))
scene.add(Text("FIELD NOTE  /  SCALE", x=105, y=190, role="annotation", anchor="left", color=ink.accent, layer="overlay", name="eyebrow"))
heading = scene.add(Text("A hundred individuals.", x=100, y=285, role="headline", anchor="left", max_width=890, layer="overlay", name="heading"))
scene.animate(heading, FadeIn(start=.25, duration=.65))

crowd = Crowd(
    box=Box(105, 760, 975, 1450), count=100, columns=10, seed=42,
    highlighted=tuple(range(17)), style=scene.style, name="people",
)
crowd.add_to(scene)
for index in range(100):
    start = .85 + (index // 10) * .22
    for key in ("body", "head"):
        scene.animate(crowd.parts[f"person:{index}:{key}"], FadeIn(start=start, duration=.38))
for index in range(17):
    start = 3.45 + index * .045
    for key in ("body", "head"):
        scene.animate(crowd.parts[f"highlight:{index}:{key}"], FadeIn(start=start, duration=.28))

stat = scene.add(Text("17 / 100", x=540, y=520, role="display", color=ink.primary, layer="overlay", name="statistic"))
scene.animate(stat, FadeIn(start=4.35, duration=.6))
scene.animate(stat, Scale(start=4.35, duration=.75, from_x=.96, to_x=1, from_y=.96, to_y=1, easing="ease_out_cubic"))
label = scene.add(Text("17 HIGHLIGHTED  /  100 TOTAL", x=540, y=1510, role="label", color=ink.accent, layer="overlay", name="count_label"))
scene.animate(label, FadeIn(start=4.65, duration=.5))
caption = scene.add(Text("Scale gives the number meaning.", x=540, y=1605, role="caption", layer="captions", name="caption"))
scene.animate(caption, FadeIn(start=5.1, duration=.55))
scene.camera.animate(y=(960, 985), zoom=(1, 1.035), start=4.6, duration=2.1, easing="ease_out_cubic")
