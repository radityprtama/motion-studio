"""An editable statistical portrait built from a semantic scene pattern."""

from motion import FadeIn, StatisticsScene, Text
from motion.style import get_style


scene = StatisticsScene(
    values=(56, 34, 18), labels=("START", "ITERATE", "FINISH"),
    title="Illustrative build times", duration=7, style="blueprint-paper", seed=18,
)
scene.add(Text("SAMPLE DATA  /  MINUTES", x=130, y=530, role="annotation", anchor="left", color=get_style(scene.style).accent, name="unit"))
result = scene.add(Text("56 → 18 min", x=540, y=1530, role="title", color=get_style(scene.style).primary, name="result", layer="overlay"))
scene.animate(result, FadeIn(start=2.8, duration=.6))
