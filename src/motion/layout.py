"""Pure geometry for arranging content in portrait design coordinates."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Literal


Anchor = Literal[
    "top_left", "top_center", "top_right",
    "center_left", "center", "center_right",
    "bottom_left", "bottom_center", "bottom_right",
]


@dataclass(frozen=True)
class Box:
    left: float
    top: float
    right: float
    bottom: float

    def __post_init__(self) -> None:
        if not all(isfinite(value) for value in (self.left, self.top, self.right, self.bottom)):
            raise ValueError("Box edges must be finite")
        if self.right <= self.left or self.bottom <= self.top:
            raise ValueError("Box needs positive width and height")

    @property
    def width(self) -> float:
        return self.right - self.left

    @property
    def height(self) -> float:
        return self.bottom - self.top

    @property
    def center(self) -> tuple[float, float]:
        return ((self.left + self.right) / 2, (self.top + self.bottom) / 2)

    def inset(self, padding: float) -> Box:
        if not isfinite(padding) or padding < 0:
            raise ValueError("Box inset must be finite and non-negative")
        if 2 * padding >= min(self.width, self.height):
            raise ValueError(f"Box inset {padding:g} exceeds available {self.width:g}x{self.height:g}")
        return Box(self.left + padding, self.top + padding, self.right - padding, self.bottom - padding)

    def point(self, anchor: Anchor) -> tuple[float, float]:
        parts = anchor.split("_") if anchor != "center" else ["center", "center"]
        if len(parts) != 2 or parts[0] not in ("top", "center", "bottom") or parts[1] not in ("left", "center", "right"):
            raise ValueError(f"Unknown anchor {anchor!r}")
        x = {"left": self.left, "center": self.center[0], "right": self.right}[parts[1]]
        y = {"top": self.top, "center": self.center[1], "bottom": self.bottom}[parts[0]]
        return x, y


def _size(width: float, height: float, box: Box) -> None:
    if not all(isfinite(value) and value > 0 for value in (width, height)):
        raise ValueError("Requested width and height must be finite and positive")
    if width > box.width or height > box.height:
        raise ValueError(f"Requested {width:g}x{height:g} exceeds available {box.width:g}x{box.height:g}")


def place(box: Box, width: float, height: float, anchor: Anchor, *, dx: float = 0, dy: float = 0) -> tuple[float, float]:
    _size(width, height, box)
    if not isfinite(dx) or not isfinite(dy):
        raise ValueError("Placement offsets must be finite")
    x, y = box.point(anchor)
    vertical, horizontal = ("center", "center") if anchor == "center" else anchor.split("_")
    left = x - {"left": 0, "center": width / 2, "right": width}[horizontal] + dx
    top = y - {"top": 0, "center": height / 2, "bottom": height}[vertical] + dy
    if left < box.left or top < box.top or left + width > box.right or top + height > box.bottom:
        raise ValueError(f"Placement falls outside available {box.width:g}x{box.height:g}")
    return left, top


def stack(
    box: Box, sizes: list[tuple[float, float]] | tuple[tuple[float, float], ...],
    *, gap: float = 0, direction: Literal["vertical", "horizontal"] = "vertical",
    align: Literal["left", "center", "right", "top", "bottom"] = "center",
) -> tuple[Box, ...]:
    if not isfinite(gap) or gap < 0:
        raise ValueError("Stack gap must be finite and non-negative")
    if direction not in ("vertical", "horizontal"):
        raise ValueError("Stack direction must be vertical or horizontal")
    if align not in (("left", "center", "right") if direction == "vertical" else ("top", "center", "bottom")):
        raise ValueError(f"Unsupported {direction} stack alignment {align!r}")
    for width, height in sizes:
        _size(width, height, box)
    used = sum(height if direction == "vertical" else width for width, height in sizes) + gap * max(0, len(sizes) - 1)
    available = box.height if direction == "vertical" else box.width
    if used > available:
        raise ValueError(f"Stack needs {used:g} along {direction}; available {box.width:g}x{box.height:g}")
    cursor = box.top if direction == "vertical" else box.left
    result = []
    for width, height in sizes:
        if direction == "vertical":
            left = {"left": box.left, "center": box.center[0] - width / 2, "right": box.right - width}[align]
            result.append(Box(left, cursor, left + width, cursor + height))
            cursor += height + gap
        else:
            top = {"top": box.top, "center": box.center[1] - height / 2, "bottom": box.bottom - height}[align]
            result.append(Box(cursor, top, cursor + width, top + height))
            cursor += width + gap
    return tuple(result)


def grid(box: Box, *, rows: int, columns: int, gap_x: float = 0, gap_y: float = 0, padding: float = 0) -> tuple[Box, ...]:
    if rows <= 0 or columns <= 0:
        raise ValueError("Grid rows and columns must be positive")
    if not all(isfinite(value) and value >= 0 for value in (gap_x, gap_y, padding)):
        raise ValueError("Grid gaps and padding must be finite and non-negative")
    usable_width = box.width - 2 * padding - gap_x * (columns - 1)
    usable_height = box.height - 2 * padding - gap_y * (rows - 1)
    if usable_width <= 0 or usable_height <= 0:
        raise ValueError(f"Grid gaps/padding exceed available {box.width:g}x{box.height:g}")
    cell_width = usable_width / columns
    cell_height = usable_height / rows
    return tuple(
        Box(
            box.left + padding + column * (cell_width + gap_x),
            box.top + padding + row * (cell_height + gap_y),
            box.left + padding + column * (cell_width + gap_x) + cell_width,
            box.top + padding + row * (cell_height + gap_y) + cell_height,
        )
        for row in range(rows) for column in range(columns)
    )
