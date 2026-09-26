"""Deterministic, code-authored motion graphics."""

from .animation import DrawPath, FadeIn, FadeOut, MaskReveal, Move, Reveal, Rotate, Scale
from .camera import Camera
from .composition import Parallel, Sequence
from .primitives import Circle, Path, Rectangle, Text
from .scene import PortraitScene

__all__ = [
    "Camera", "Circle", "DrawPath", "FadeIn", "FadeOut", "MaskReveal", "Move", "Parallel",
    "Path", "PortraitScene", "Rectangle", "Reveal", "Rotate", "Scale", "Sequence", "Text",
]
__version__ = "0.1.0"
