"""An eight-second atmospheric portrait built from one procedural orb."""

from motion import FadeIn, Move, Orb, ParticleEmitter, Path, PortraitScene, Reveal, Text
from motion.style import get_style


scene = PortraitScene(duration=8, fps=30, seed=42, style="cinematic")
ink = get_style(scene.style)

scene.add(ParticleEmitter(
    x=540, y=940, width=1080, height=1740, count=75, seed=109,
    radius_range=(1.2, 3.5), velocity=(-5, 5, -11, 2),
    color=ink.secondary, opacity=.55, layer="environment", name="atmosphere",
))
scene.add(Text("FIELD NOTE  /  SIGNAL", x=105, y=190, role="annotation", anchor="left", color=ink.accent, layer="overlay", name="eyebrow"))
title = scene.add(Text("One signal\nin the noise.", x=100, y=320, role="display", anchor="left", max_width=875, layer="overlay", name="title"))
scene.animate(title, Reveal(direction="left", start=.35, duration=1.15, easing="ease_out_cubic"))
rule = scene.add(Path(x=100, y=640, points=((0, 0), (245, 0)), stroke=ink.accent, stroke_width=4, layer="overlay", name="title_rule"))
scene.animate(rule, FadeIn(start=1.15, duration=.45))

orb = Orb(x=540, y=1060, diameter=490, style=scene.style, name="signal")
orb.add_to(scene)
for key, start, duration in (("halo", .3, 1.4), ("disc", .9, 1.1), ("rim", 1.5, 1.0), ("highlight", 2.1, 1.3)):
    scene.animate(orb.parts[key], FadeIn(start=start, duration=duration, easing="ease_out_cubic"))
    scene.animate(orb.parts[key], Move(start=1.8, duration=3.4, from_y=orb.parts[key].y + 42, to_y=orb.parts[key].y, easing="ease_out_cubic"))

caption = scene.add(Text("A point of focus changes what we see.", x=540, y=1610, role="caption", layer="captions", name="caption"))
scene.animate(caption, FadeIn(start=4.5, duration=.7))
scene.camera.animate(y=(960, 1000), zoom=(1, 1.055), start=4.2, duration=3.0, easing="ease_out_cubic")
