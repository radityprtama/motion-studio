"""Deterministic, code-authored motion graphics."""

from .animation import FadeIn, FadeOut, Move
from .primitives import Circle, Rectangle, Text
from .scene import PortraitScene

__all__ = ["Circle", "FadeIn", "FadeOut", "Move", "PortraitScene", "Rectangle", "Text"]
__version__ = "0.1.0"
