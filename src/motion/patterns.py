"""Reusable portrait compositions built from the public motion vocabulary."""

from __future__ import annotations

from typing import Mapping

from .animation import DrawPath, FadeIn
from .components import Arrow, Crowd, Timeline
from .components_extra import Chart, Graph, Quote
from .layout import Box
from .primitives import Line, Rectangle, Text
from .scene import PortraitScene
from .style import get_style


def _scene(*, duration: float, style: str, seed: int, title: str) -> PortraitScene:
    scene = PortraitScene(duration=duration, style=style, seed=seed)
    ink = get_style(style)
    heading = scene.add(Text(title, x=90, y=240, role="headline", max_width=900, anchor="left", color=ink.primary, name="heading"))
    scene.animate(heading, FadeIn(start=0, duration=min(.5, duration / 4)))
    return scene


def ComparisonScene(*, left: str, right: str, left_label: str, right_label: str, title: str, duration: float = 5, style: str = "blueprint", seed: int = 0) -> PortraitScene:
    scene = _scene(duration=duration, style=style, seed=seed, title=title)
    ink = get_style(style)
    for index, (value, label, x) in enumerate(((left, left_label, 300), (right, right_label, 780))):
        scene.add(Line(x=x - 190, y=760, dx=380, dy=0, stroke=ink.accent if index else ink.secondary, stroke_width=4, name=f"comparison:rule:{index}"))
        visual = scene.add(Text(value, x=x, y=900, role="display", max_width=380, color=ink.primary, name=f"comparison:value:{index}"))
        caption = scene.add(Text(label, x=x, y=1190, role="annotation", max_width=380, color=ink.secondary, name=f"comparison:label:{index}"))
        scene.animate(visual, FadeIn(start=.5 + index * .5, duration=.5))
        scene.animate(caption, FadeIn(start=.7 + index * .5, duration=.4))
    return scene


def ProcessScene(*, steps: tuple[str, ...], title: str, duration: float = 6, style: str = "blueprint", seed: int = 0) -> PortraitScene:
    if not 2 <= len(steps) <= 5:
        raise ValueError("ProcessScene needs 2–5 steps")
    scene = _scene(duration=duration, style=style, seed=seed, title=title)
    timeline = Timeline(labels=steps, x=210, y=640, gap=850 / (len(steps) - 1), style=style, name="process")
    timeline.add_to(scene)
    scene.animate(timeline.parts["spine"], DrawPath(start=.3, duration=min(duration * .6, 3)))
    for index in range(len(steps)):
        scene.animate(timeline.parts[f"tick:{index}"], FadeIn(start=.5 + index * duration * .1, duration=.3))
        scene.animate(timeline.parts[f"label:{index}"], FadeIn(start=.6 + index * duration * .1, duration=.3))
    return scene


def TimelineScene(*, events: tuple[str, ...], title: str, duration: float = 6, style: str = "blueprint", seed: int = 0) -> PortraitScene:
    return ProcessScene(steps=events, title=title, duration=duration, style=style, seed=seed)


def GraphScene(*, nodes: Mapping[str, tuple[float, float]], edges: tuple[tuple[str, str], ...], title: str, duration: float = 6, style: str = "blueprint", seed: int = 0) -> PortraitScene:
    scene = _scene(duration=duration, style=style, seed=seed, title=title)
    graph = Graph(nodes=nodes, edges=edges, style=style, name="semantic_graph", radius=22)
    graph.add_to(scene)
    for index in range(len(edges)):
        scene.animate(graph.parts[f"edge:{index}"], DrawPath(start=.4 + index * .35, duration=.65))
    for index, key in enumerate(nodes):
        scene.animate(graph.parts[f"node:{key}"], FadeIn(start=.35 + index * .3, duration=.3))
        x, y = nodes[key]
        label = scene.add(Text(key, x=x + 36, y=y - 16, role="annotation", anchor="left", color=get_style(style).primary, name=f"graph:label:{key}"))
        scene.animate(label, FadeIn(start=.45 + index * .3, duration=.3))
    return scene


def CrowdScene(*, count: int, highlighted: int, title: str, duration: float = 6, style: str = "cinematic", seed: int = 0) -> PortraitScene:
    if not 0 <= highlighted <= count:
        raise ValueError("highlighted must be between zero and count")
    scene = _scene(duration=duration, style=style, seed=seed, title=title)
    columns = 10 if count >= 50 else min(5, count)
    crowd = Crowd(box=Box(120, 650, 960, 1410), count=count, columns=columns, seed=seed, highlighted=tuple(range(highlighted)), style=style, name="pattern_crowd")
    crowd.add_to(scene)
    accent_parts = [part for name, part in crowd.parts.items() if name.startswith("highlight:")]
    scene.stagger(accent_parts, FadeIn(duration=.28), start=1, step=min(.04, 1 / max(1, highlighted)))
    ink = get_style(style)
    scene.add(Text(f"{highlighted} / {count}", x=540, y=1490, role="title", color=ink.accent, name="crowd:ratio"))
    return scene


def StatisticsScene(*, values: tuple[float, ...], labels: tuple[str, ...], title: str, duration: float = 6, style: str = "blueprint", seed: int = 0) -> PortraitScene:
    scene = _scene(duration=duration, style=style, seed=seed, title=title)
    chart = Chart(box=Box(130, 650, 950, 1450), values=values, labels=labels, style=style, name="statistics")
    chart.add_to(scene)
    for index in range(len(values)):
        scene.animate(chart.parts[f"bar:{index}"], FadeIn(start=.6 + index * .23, duration=.4))
        scene.animate(chart.parts[f"value:{index}"], FadeIn(start=.8 + index * .23, duration=.3))
    return scene


def QuoteScene(*, text: str, attribution: str, title: str = "", duration: float = 5, style: str = "blueprint", seed: int = 0) -> PortraitScene:
    scene = _scene(duration=duration, style=style, seed=seed, title=title or "IN THEIR WORDS")
    quote = Quote(x=540, y=950, width=800, text=text, attribution=attribution, style=style, name="quote")
    quote.add_to(scene)
    scene.animate(quote.parts["text"], FadeIn(start=.6, duration=.7))
    if "attribution" in quote.parts:
        scene.animate(quote.parts["attribution"], FadeIn(start=1.1, duration=.5))
    return scene


def EditorialScene(*, headline: str, body: str, duration: float = 5, style: str = "cinematic", seed: int = 0) -> PortraitScene:
    scene = PortraitScene(duration=duration, style=style, seed=seed)
    ink = get_style(style)
    scene.add(Rectangle(x=130, y=460, width=6, height=110, fill=ink.accent, name="editorial:mark"))
    heading = scene.add(Text(headline, x=165, y=620, role="display", max_width=790, anchor="left", color=ink.primary, name="editorial:headline"))
    body_element = scene.add(Text(body, x=165, y=1320, role="body", max_width=730, anchor="left", color=ink.secondary, name="editorial:body"))
    scene.animate(heading, FadeIn(start=.4, duration=.7))
    scene.animate(body_element, FadeIn(start=1.2, duration=.5))
    return scene


def HierarchyScene(*, levels: tuple[str, ...], title: str, duration: float = 6, style: str = "blueprint", seed: int = 0) -> PortraitScene:
    if not 2 <= len(levels) <= 5:
        raise ValueError("HierarchyScene needs 2–5 levels")
    scene = _scene(duration=duration, style=style, seed=seed, title=title)
    ink = get_style(style)
    gap = 850 / (len(levels) - 1)
    for index, label in enumerate(levels):
        y = 640 + index * gap
        width = 320 + index * 110
        frame = scene.add(Rectangle(x=540, y=y, width=width, height=120, fill=ink.background, stroke=ink.accent if index == 0 else ink.secondary, stroke_width=3, name=f"hierarchy:frame:{index}"))
        text = scene.add(Text(label, x=540, y=y - 22, role="title", max_width=width - 30, color=ink.primary, name=f"hierarchy:label:{index}"))
        scene.animate(frame, FadeIn(start=.5 + index * .35, duration=.4))
        scene.animate(text, FadeIn(start=.6 + index * .35, duration=.35))
        if index:
            connector = scene.add(Line(x=540, y=y - gap + 60, dx=0, dy=gap - 120, stroke=ink.secondary, stroke_width=3, name=f"hierarchy:connector:{index}"))
            scene.animate(connector, DrawPath(start=.65 + (index - 1) * .35, duration=.45))
    return scene


def FlowScene(*, steps: tuple[str, ...], title: str, duration: float = 6, style: str = "blueprint", seed: int = 0) -> PortraitScene:
    if not 2 <= len(steps) <= 5:
        raise ValueError("FlowScene needs 2–5 steps")
    scene = _scene(duration=duration, style=style, seed=seed, title=title)
    ink = get_style(style)
    gap = 850 / (len(steps) - 1)
    for index, label in enumerate(steps):
        y = 620 + index * gap
        frame = scene.add(Rectangle(x=540, y=y, width=600, height=110, fill=ink.background, stroke=ink.secondary, stroke_width=3, name=f"flow:box:{index}"))
        text = scene.add(Text(label, x=540, y=y - 22, role="title", max_width=550, color=ink.primary, name=f"flow:label:{index}"))
        scene.animate(frame, FadeIn(start=.4 + index * .4, duration=.35))
        scene.animate(text, FadeIn(start=.5 + index * .4, duration=.3))
        if index:
            arrow = Arrow(start=(540, y - gap + 55), end=(540, y - 55), style=style, name=f"flow:arrow:{index}")
            arrow.add_to(scene)
            scene.animate(arrow.parts["shaft"], DrawPath(start=.5 + (index - 1) * .4, duration=.5))
    return scene
