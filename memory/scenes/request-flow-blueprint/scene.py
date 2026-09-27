"""A vertical request journey using semantic device parts and one directed link."""

from motion import Arrow, Computer, DrawPath, FadeIn, PortraitScene, Server, Text
from motion.style import get_style


scene = PortraitScene(duration=7, style="blueprint", seed=31)
ink = get_style(scene.style)

scene.add(Text("FIELD NOTE  /  02", x=90, y=180, role="annotation", anchor="left", color=ink.accent, name="eyebrow"))
headline = scene.add(Text("Where a request goes", x=90, y=310, role="headline", max_width=840, anchor="left", name="headline"))
scene.animate(headline, FadeIn(start=.15, duration=.55))

computer = Computer(x=540, y=640, width=470, label="CLIENT", name="client")
computer.add_to(scene)
for part in computer.parts.values():
    scene.animate(part, FadeIn(start=.45, duration=.55))

connection = Arrow(start=(540, 900), end=(540, 1050), name="request", style=scene.style)
connection.add_to(scene)
scene.animate(connection.parts["shaft"], DrawPath(start=1.6, duration=.95))
scene.animate(connection.parts["head_left"], DrawPath(start=2.5, duration=.25))
scene.animate(connection.parts["head_right"], DrawPath(start=2.5, duration=.25))

server = Server(x=540, y=1310, width=300, height=390, label="SERVER", name="server")
server.add_to(scene)
for key, part in server.parts.items():
    scene.animate(part, FadeIn(start=2.4 if key == "rack" else 2.9, duration=.45))

caption = scene.add(Text("A request travels to a service, then returns as a response.", x=90, y=1640, role="caption", max_width=900, anchor="left", color=ink.primary, name="caption", layer="captions"))
scene.animate(caption, FadeIn(start=4.2, duration=.7))
scene.camera.animate(zoom=(1, 1.035), start=3.3, duration=2.8, easing="ease_out_cubic")
