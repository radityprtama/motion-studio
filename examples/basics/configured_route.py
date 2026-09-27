"""An explicit scene factory uses project defaults and two direct-time keyframe tracks."""

from motion import Circle, DrawPath, FadeIn, Keyframe, Keyframes, Path, PortraitScene, Text
from motion.style import get_style


def build_scene(config):
    scene = PortraitScene.from_config(config, duration=4, seed=12)
    ink = get_style(scene.style)
    left, top, right, _ = scene.content_box
    start_x, end_x = scene.width * .28, scene.width * .72
    start_y, end_y = scene.height * .49, scene.height * .68
    turn = (end_x - start_x) / ((end_x - start_x) + (end_y - start_y))
    scene.add(Text("A signal takes a route", x=left, y=top + 130, role="headline", anchor="left", max_width=right - left, name="headline"))
    scene.add(Text("START", x=start_x, y=start_y - 85, role="annotation", color=ink.secondary, name="start_label"))
    scene.add(Text("DESTINATION", x=end_x, y=end_y + 60, role="annotation", color=ink.accent, name="destination_label"))
    route = scene.add(Path(x=start_x, y=start_y, points=((0, 0), (end_x - start_x, 0), (end_x - start_x, end_y - start_y)), stroke=ink.primary, stroke_width=5, name="route"))
    marker = scene.add(Circle(x=start_x, y=start_y, radius=22, fill=ink.accent, name="signal"))
    scene.animate(route, DrawPath(start=.5, duration=2.4))
    scene.animate(marker, FadeIn(start=.4, duration=.3))
    scene.animate(marker, Keyframes(channel="x", start=.5, duration=2.4, points=(Keyframe(0, start_x), Keyframe(turn, end_x), Keyframe(1, end_x))))
    scene.animate(marker, Keyframes(channel="y", start=.5, duration=2.4, points=(Keyframe(0, start_y), Keyframe(turn, start_y), Keyframe(1, end_y))))
    return scene
