"""Expand readable timing groups into explicit animation tracks."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from math import isfinite

from .animation import Animation


@dataclass(frozen=True, init=False)
class Sequence:
    children: tuple[Animation | Sequence | Parallel, ...]
    start: float

    def __init__(self, *children: Animation | Sequence | Parallel, start: float = 0.0) -> None:
        _validate_group(children, start)
        object.__setattr__(self, "children", children)
        object.__setattr__(self, "start", start)


@dataclass(frozen=True, init=False)
class Parallel:
    children: tuple[Animation | Sequence | Parallel, ...]
    start: float

    def __init__(self, *children: Animation | Sequence | Parallel, start: float = 0.0) -> None:
        _validate_group(children, start)
        object.__setattr__(self, "children", children)
        object.__setattr__(self, "start", start)


Node = Animation | Sequence | Parallel


def _validate_group(children: tuple[Node, ...], start: float) -> None:
    if not children:
        raise ValueError("animation composition requires at least one child")
    if not isfinite(start) or start < 0:
        raise ValueError("animation composition start must be finite and non-negative")
    for child in children:
        if not isinstance(child, (Animation, Sequence, Parallel)):
            raise TypeError(f"Unsupported animation composition child {type(child).__name__}")


def expand(node: Node, offset: float = 0.0) -> tuple[tuple[Animation, ...], float]:
    """Return absolute leaf tracks and the absolute end of this node."""
    if not isfinite(offset) or offset < 0:
        raise ValueError("animation offset must be finite and non-negative")
    if isinstance(node, Animation):
        leaf = replace(node, start=offset + node.start)
        return (leaf,), leaf.start + leaf.duration
    if isinstance(node, Parallel):
        base = offset + node.start
        leaves: list[Animation] = []
        end = base
        for child in node.children:
            child_leaves, child_end = expand(child, base)
            leaves.extend(child_leaves)
            end = max(end, child_end)
        return tuple(leaves), end
    if isinstance(node, Sequence):
        cursor = offset + node.start
        leaves = []
        for child in node.children:
            child_leaves, cursor = expand(child, cursor)
            leaves.extend(child_leaves)
        return tuple(leaves), cursor
    raise TypeError(f"Unsupported animation node {type(node).__name__}")
