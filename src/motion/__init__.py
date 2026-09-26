"""Deterministic, code-authored motion graphics."""

from .animation import DrawPath, FadeIn, FadeOut, MaskReveal, Move, Reveal, Rotate, Scale
from .camera import Camera
from .composition import Parallel, Sequence
from .components import Component, File, Folder
from .layout import Box, grid, place, stack
from .primitives import Circle, Path, Rectangle, Text
from .scene import PortraitScene

__all__ = [
    "Box", "Camera", "Circle", "Component", "DrawPath", "FadeIn", "FadeOut", "File", "Folder", "MaskReveal", "Move", "Parallel",
    "Path", "PortraitScene", "Rectangle", "Reveal", "Rotate", "Scale", "Sequence", "Text",
    "grid", "place", "stack",
]
__version__ = "0.1.0"
