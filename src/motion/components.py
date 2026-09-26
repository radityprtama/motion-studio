"""Semantic drawings assembled from named, animatable primitives."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, hypot, isfinite
from random import Random
from types import MappingProxyType
from typing import Mapping

from .layout import Box, grid
from .primitives import Circle, Element, Path, RadialLight, Rectangle, Text
from .scene import PortraitScene
from .style import Style, get_style
from .typography import layout_text


@dataclass(frozen=True)
class Component:
    parts: Mapping[str, Element]
    bounds: Box
    anchors: Mapping[str, tuple[float, float]]

    def __post_init__(self) -> None:
        if not self.parts:
            raise ValueError("Component needs at least one part")
        names = [part.name for part in self.parts.values()]
        if any(name is None for name in names) or len(set(names)) != len(names):
            raise ValueError("Component parts need unique names")
        object.__setattr__(self, "parts", MappingProxyType(dict(self.parts)))
        object.__setattr__(self, "anchors", MappingProxyType(dict(self.anchors)))

    def add_to(self, scene: PortraitScene) -> Component:
        for part in self.parts.values():
            scene.add(part)
        return self


def _number(value: float, label: str, minimum: float = 0) -> None:
    if not isfinite(value) or value <= minimum:
        raise ValueError(f"{label} must be finite and greater than {minimum:g}; got {value!r}")


def _prefix(name: str | None, kind: str, x: float, y: float) -> str:
    result = name if name is not None else f"{kind}_{x:g}_{y:g}"
    if not result.strip():
        raise ValueError(f"{kind} name cannot be blank")
    return result


def _fit_label(label: str, text: Text, style: Style, width: float, kind: str) -> None:
    if not label.strip():
        raise ValueError(f"{kind} label cannot be blank")
    bounds = layout_text(text, style).bounds
    measured = bounds[2] - bounds[0]
    if measured > width:
        raise ValueError(f"{kind} label {label!r} needs {measured:g}px; available {width:g}px")


def Folder(
    *, x: float, y: float, width: float, label: str, style: str = "blueprint",
    name: str | None = None, height: float | None = None,
) -> Component:
    """Return a project folder with independent body, tab, and label handles."""
    _number(width, "Folder width", 220)
    height = width * 0.56 if height is None else height
    _number(height, "Folder height", 150)
    colors = get_style(style)
    prefix = _prefix(name, "folder", x, y)
    left, top = x - width / 2, y - height / 2
    label_text = Text(label, x=left + 34, y=top + height - 86, role="annotation", anchor="left", color=colors.primary, name=f"{prefix}:label")
    _fit_label(label, label_text, colors, width - 68, "Folder")
    parts = {
        "body": Rectangle(x=x, y=y, width=width, height=height, fill=colors.background, stroke=colors.primary, stroke_width=colors.component_stroke, name=f"{prefix}:body"),
        "tab": Path(x=left, y=top, points=((0, 0), (0, -54), (min(160, width * .3), -54), (min(210, width * .38), 0)), stroke=colors.primary, stroke_width=colors.component_stroke, name=f"{prefix}:tab"),
        "label": label_text,
    }
    return Component(parts, Box(left, top - 54, left + width, top + height), {"center": (x, y), "tab_center": (left + min(160, width * .3) / 2, top - 54), "entry": (x, top - 54), "exit": (x, top + height)})


def File(
    *, x: float, y: float, width: float, height: float, label: str,
    style: str = "blueprint", name: str | None = None,
) -> Component:
    """Return a paper file with a small fold and an editable label."""
    _number(width, "File width", 60)
    _number(height, "File height", 90)
    colors = get_style(style)
    prefix = _prefix(name, "file", x, y)
    left, top = x - width / 2, y - height / 2
    fold = min(42, width * .23)
    label_text = Text(label, x=x, y=top + height - 56, role="label", anchor="center", color=colors.primary, name=f"{prefix}:label")
    _fit_label(label, label_text, colors, width - 28, "File")
    parts = {
        "body": Rectangle(x=x, y=y, width=width, height=height, fill=colors.background, stroke=colors.primary, stroke_width=colors.component_stroke, name=f"{prefix}:body"),
        "fold": Path(x=left + width, y=top, points=((-fold, 0), (-fold, fold), (0, fold)), stroke=colors.secondary, stroke_width=colors.component_stroke * .75, name=f"{prefix}:fold"),
        "label": label_text,
    }
    return Component(parts, Box(left, top, left + width, top + height), {"center": (x, y), "top": (x, top), "bottom": (x, top + height)})


def Arrow(
    *, start: tuple[float, float], end: tuple[float, float], style: str = "blueprint",
    name: str | None = None, color: str | None = None, head_size: float = 22,
) -> Component:
    """A connector whose shaft and two arrowhead strokes can draw separately."""
    if len(start) != 2 or len(end) != 2 or not all(isfinite(v) for v in (*start, *end)):
        raise ValueError("Arrow endpoints must be finite (x, y) points")
    dx, dy = end[0] - start[0], end[1] - start[1]
    distance = hypot(dx, dy)
    _number(distance, "Arrow length")
    _number(head_size, "Arrow head_size")
    colors = get_style(style)
    ink = color or colors.accent
    prefix = _prefix(name, "arrow", *start)
    ux, uy = dx / distance, dy / distance
    wing_x, wing_y = -uy, ux
    base_x, base_y = end[0] - ux * head_size, end[1] - uy * head_size
    left_wing = (base_x + wing_x * head_size * .55, base_y + wing_y * head_size * .55)
    right_wing = (base_x - wing_x * head_size * .55, base_y - wing_y * head_size * .55)
    parts = {
        "shaft": Path(x=start[0], y=start[1], points=((0, 0), (dx, dy)), stroke=ink, stroke_width=colors.component_stroke, name=f"{prefix}:shaft"),
        "head_left": Path(x=end[0], y=end[1], points=((left_wing[0] - end[0], left_wing[1] - end[1]), (0, 0)), stroke=ink, stroke_width=colors.component_stroke, name=f"{prefix}:head_left"),
        "head_right": Path(x=end[0], y=end[1], points=((right_wing[0] - end[0], right_wing[1] - end[1]), (0, 0)), stroke=ink, stroke_width=colors.component_stroke, name=f"{prefix}:head_right"),
    }
    xs = (start[0], end[0], left_wing[0], right_wing[0])
    ys = (start[1], end[1], left_wing[1], right_wing[1])
    return Component(parts, Box(min(xs) - 3, min(ys) - 3, max(xs) + 3, max(ys) + 3), {"entry": start, "exit": end})


def CommitNode(
    *, x: float, y: float, label: str, style: str = "blueprint",
    name: str | None = None, radius: float = 30, highlighted: bool = False,
    label_side: str = "right",
) -> Component:
    """A graph node with a separate ring, core, and measured annotation."""
    _number(radius, "CommitNode radius", 8)
    if label_side not in ("left", "right"):
        raise ValueError("CommitNode label_side must be left or right")
    colors = get_style(style)
    prefix = _prefix(name, "commit", x, y)
    label_x = x + radius + 24 if label_side == "right" else x - radius - 24
    label_anchor = "left" if label_side == "right" else "right"
    label_text = Text(label, x=label_x, y=y - 17, role="annotation", anchor=label_anchor, color=colors.accent if highlighted else colors.primary, name=f"{prefix}:label")
    _fit_label(label, label_text, colors, 320, "CommitNode")
    label_bounds = layout_text(label_text, colors).bounds
    parts = {
        "ring": Circle(x=x, y=y, radius=radius, fill=colors.background, stroke=colors.accent if highlighted else colors.primary, stroke_width=colors.component_stroke + 1, name=f"{prefix}:ring"),
        "core": Circle(x=x, y=y, radius=max(5, radius * .22), fill=colors.accent if highlighted else colors.primary, name=f"{prefix}:core"),
        "label": label_text,
    }
    bounds = Box(min(x - radius - 3, label_bounds[0]), min(y - radius - 3, label_bounds[1]), max(x + radius + 3, label_bounds[2]), max(y + radius + 3, label_bounds[3]))
    return Component(parts, bounds, {"center": (x, y), "entry": (x, y - radius), "exit": (x, y + radius)})


def CommitGraph(
    *, records: tuple[tuple[str, str, str | None], ...],
    positions: Mapping[str, tuple[float, float]], style: str = "blueprint",
    name: str = "graph", radius: float = 30,
) -> Component:
    """An ordered history with explicit parent links and independently addressable parts."""
    if not records:
        raise ValueError("CommitGraph requires at least one record")
    ids = [item[0] for item in records]
    if len(set(ids)) != len(ids):
        raise ValueError("CommitGraph has duplicate IDs")
    if set(positions) != set(ids):
        raise ValueError(f"CommitGraph positions need IDs {ids!r}; got {list(positions)!r}")
    colors = get_style(style)
    prefix = _prefix(name, "graph", 0, 0)
    parts: dict[str, Element] = {}
    anchors: dict[str, tuple[float, float]] = {}
    seen: set[str] = set()
    for index, (item_id, label, parent_id) in enumerate(records):
        if not item_id.strip():
            raise ValueError("CommitGraph IDs cannot be blank")
        if index == 0 and parent_id is not None:
            raise ValueError("CommitGraph first record must be a root with no parent")
        if index > 0 and parent_id not in seen:
            raise ValueError(f"CommitGraph record {item_id!r} has unknown parent {parent_id!r}")
        x, y = positions[item_id]
        if not isfinite(x) or not isfinite(y):
            raise ValueError(f"CommitGraph position for {item_id!r} must be finite")
        anchors[f"node:{item_id}"] = (x, y)
        if parent_id is not None:
            parent_x, parent_y = positions[parent_id]
            dx, dy = x - parent_x, y - parent_y
            if dx == 0 and dy == 0:
                raise ValueError(f"CommitGraph record {item_id!r} overlaps its parent")
            points = ((0, 0), (dx, dy)) if dx == 0 else ((0, 0), (dx, 0), (dx, dy))
            branch = parent_id != records[index - 1][0]
            parts[f"connector:{item_id}"] = Path(x=parent_x, y=parent_y, points=points, stroke=colors.accent if branch else colors.primary, stroke_width=colors.component_stroke + 1, name=f"{prefix}:connector:{item_id}")
        seen.add(item_id)
    bounds_list = []
    for index, (item_id, label, parent_id) in enumerate(records):
        x, y = positions[item_id]
        branch = index > 0 and parent_id != records[index - 1][0]
        has_right_branch = any(
            later_parent == item_id and positions[later_id][0] > x
            for later_id, _, later_parent in records[index + 1:]
        )
        label_side = "left" if has_right_branch or (branch and x > positions[parent_id][0]) else "right"
        node = CommitNode(x=x, y=y, label=label, style=style, name=f"{prefix}:node:{item_id}", radius=radius, highlighted=branch, label_side=label_side)
        bounds_list.append(node.bounds)
        for key, element in node.parts.items():
            parts[f"node:{item_id}:{key}"] = element
    xs = [box.left for box in bounds_list] + [box.right for box in bounds_list] + [point[0] for point in positions.values()]
    ys = [box.top for box in bounds_list] + [box.bottom for box in bounds_list] + [point[1] for point in positions.values()]
    return Component(parts, Box(min(xs), min(ys), max(xs), max(ys)), anchors)


def Timeline(
    *, labels: tuple[str, ...], x: float, y: float, gap: float,
    direction: str = "vertical", style: str = "blueprint", name: str | None = None,
) -> Component:
    """An ordered sequence of ticks and labels along one axis."""
    if not labels:
        raise ValueError("Timeline needs at least one label")
    _number(gap, "Timeline gap")
    if direction not in ("vertical", "horizontal"):
        raise ValueError("Timeline direction must be vertical or horizontal")
    colors = get_style(style)
    prefix = _prefix(name, "timeline", x, y)
    parts: dict[str, Element] = {}
    anchors = {}
    if len(labels) > 1:
        end = (0, gap * (len(labels) - 1)) if direction == "vertical" else (gap * (len(labels) - 1), 0)
        parts["spine"] = Path(x=x, y=y, points=((0, 0), end), stroke=colors.secondary, stroke_width=colors.component_stroke, name=f"{prefix}:spine")
    label_boxes = []
    for index, label in enumerate(labels):
        px = x + (index * gap if direction == "horizontal" else 0)
        py = y + (index * gap if direction == "vertical" else 0)
        anchors[f"item:{index}"] = (px, py)
        parts[f"tick:{index}"] = Circle(x=px, y=py, radius=9, fill=colors.accent, name=f"{prefix}:tick:{index}")
        text_x, text_y = (px + 34, py - 15) if direction == "vertical" else (px, py + 28)
        label_text = Text(label, x=text_x, y=text_y, role="label", anchor="left" if direction == "vertical" else "center", color=colors.primary, name=f"{prefix}:label:{index}")
        _fit_label(label, label_text, colors, 300, "Timeline")
        label_boxes.append(layout_text(label_text, colors).bounds)
        parts[f"label:{index}"] = label_text
    xs = [x - 9, x + (len(labels) - 1) * gap + 9 if direction == "horizontal" else x + 9]
    ys = [y - 9, y + (len(labels) - 1) * gap + 9 if direction == "vertical" else y + 9]
    return Component(parts, Box(min(xs + [box[0] for box in label_boxes]), min(ys + [box[1] for box in label_boxes]), max(xs + [box[2] for box in label_boxes]), max(ys + [box[3] for box in label_boxes])), anchors)


def Orb(
    *, x: float, y: float, diameter: float, style: str = "cinematic", name: str | None = None,
) -> Component:
    """A restrained lit sphere assembled from independently animated parts."""
    _number(diameter, "Orb diameter", 60)
    colors = get_style(style)
    prefix = _prefix(name, "orb", x, y)
    radius = diameter / 2
    halo_radius = diameter * 1.18
    parts = {
        "halo": RadialLight(x=x, y=y, radius=halo_radius, center_color=colors.secondary + "88", edge_color=colors.secondary + "00", intensity=.55, name=f"{prefix}:halo", layer="environment"),
        "disc": Circle(x=x, y=y, radius=radius, fill=colors.background, name=f"{prefix}:disc"),
        "rim": Circle(x=x, y=y, radius=radius, fill=None, stroke=colors.secondary, stroke_width=max(2, diameter * .012), opacity=.72, name=f"{prefix}:rim"),
        "highlight": RadialLight(x=x - diameter * .13, y=y - diameter * .15, radius=diameter * .38, center_color=colors.accent + "99", edge_color=colors.accent + "00", intensity=.38, name=f"{prefix}:highlight", layer="foreground"),
    }
    return Component(parts, Box(x - halo_radius, y - halo_radius, x + halo_radius, y + halo_radius), {"center": (x, y)})


def Person(
    *, x: float, y: float, height: float, style: str = "cinematic", name: str | None = None,
    pose_variant: int = 0, opacity: float = 1.0, color: str | None = None,
) -> Component:
    """A simple head-and-body silhouette, centered on its visual mass."""
    _number(height, "Person height", 24)
    if pose_variant not in (0, 1, 2):
        raise ValueError("Person pose_variant must be 0, 1, or 2")
    colors = get_style(style)
    ink = color or colors.secondary
    prefix = _prefix(name, "person", x, y)
    lean = (pose_variant - 1) * height * .035
    shoulder = height * .17
    hem = height * .13
    top = -height * .15
    bottom = height * .47
    body = Path(
        x=x, y=y,
        points=((lean - shoulder, top), (lean + shoulder, top), (lean + shoulder * 1.25, top + height * .13),
                (lean + hem, bottom), (lean - hem, bottom), (lean - shoulder * 1.25, top + height * .13)),
        closed=True, fill=ink, stroke=None, opacity=opacity, name=f"{prefix}:body",
    )
    head = Circle(x=x + lean, y=y - height * .29, radius=height * .095, fill=ink, opacity=opacity, name=f"{prefix}:head")
    return Component(
        {"body": body, "head": head},
        Box(x - height * .26, y - height * .39, x + height * .26, y + height * .47),
        {"center": (x, y), "head": (head.x, head.y)},
    )


def Crowd(
    *, box: Box, count: int, columns: int, seed: int,
    highlighted: tuple[int, ...] | list[int] = (), style: str = "cinematic", name: str = "crowd",
) -> Component:
    """A stable grid of silhouettes with optional accent overlays."""
    if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= 400:
        raise ValueError("Crowd count must be between 1 and 400")
    if not isinstance(columns, int) or isinstance(columns, bool) or not 1 <= columns <= count:
        raise ValueError("Crowd columns must be between 1 and count")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("Crowd seed must be an integer")
    selected = set(highlighted)
    if len(selected) != len(highlighted) or any(not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < count for index in selected):
        raise ValueError("Crowd highlighted indices must be unique integers in [0, count)")
    rows = ceil(count / columns)
    cells = grid(box, rows=rows, columns=columns)
    if cells[0].width < 30 or cells[0].height < 40:
        raise ValueError(f"Crowd Box is too small for {count} people in {columns} columns; cell is {cells[0].width:g}x{cells[0].height:g}")
    prefix = _prefix(name, "crowd", box.center[0], box.center[1])
    random = Random(seed)
    colors = get_style(style)
    parts: dict[str, Element] = {}
    anchors: dict[str, tuple[float, float]] = {}
    positions = []
    for index, cell in enumerate(cells[:count]):
        jitter_x = random.uniform(-min(4, cell.width * .04), min(4, cell.width * .04))
        jitter_y = random.uniform(-min(3, cell.height * .035), min(3, cell.height * .035))
        scale = random.uniform(.9, 1.05)
        x, y = cell.center[0] + jitter_x, cell.center[1] + jitter_y
        height = min(cell.height * .73, cell.width * .9) * scale
        pose = random.randrange(3)
        positions.append((index, x, y, height, pose))
        base = Person(x=x, y=y, height=height, pose_variant=pose, style=style, opacity=.48, color=colors.secondary, name=f"{prefix}:person:{index}")
        for key, part in base.parts.items():
            parts[f"person:{index}:{key}"] = part
        anchors[f"person:{index}"] = (x, y)
    for index, x, y, height, pose in positions:
        if index in selected:
            accent = Person(x=x, y=y, height=height, pose_variant=pose, style=style, opacity=1, color=colors.accent, name=f"{prefix}:highlight:{index}")
            for key, part in accent.parts.items():
                parts[f"highlight:{index}:{key}"] = part
    return Component(parts, box, anchors)
