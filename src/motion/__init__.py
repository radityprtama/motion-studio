"""Deterministic, code-authored motion graphics."""

from .animation import FadeIn, FadeOut, Move
from .camera import Camera
from .composition import Parallel, Sequence
from .primitives import Circle, Rectangle, Text
from .scene import PortraitScene

__all__ = ["Camera", "Circle", "FadeIn", "FadeOut", "Move", "Parallel", "PortraitScene", "Rectangle", "Sequence", "Text"]
__version__ = "0.1.0"
