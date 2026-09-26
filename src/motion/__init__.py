"""Deterministic, code-authored motion graphics."""

from .animation import DrawPath, FadeIn, FadeOut, MaskReveal, Move, Reveal, Rotate, Scale
from .camera import Camera
from .composition import Parallel, Sequence
from .components import Arrow, CommitGraph, CommitNode, Component, File, Folder, Timeline
from .layout import Box, grid, place, stack
from .primitives import Circle, ParticleEmitter, Path, RadialLight, Rectangle, Text
from .scene import PortraitScene

__all__ = [
    "Arrow", "Box", "Camera", "Circle", "CommitGraph", "CommitNode", "Component", "DrawPath", "FadeIn", "FadeOut", "File", "Folder", "MaskReveal", "Move", "Parallel",
    "ParticleEmitter", "Path", "PortraitScene", "RadialLight", "Rectangle", "Reveal", "Rotate", "Scale", "Sequence", "Text", "Timeline",
    "grid", "place", "stack",
]
__version__ = "0.1.0"
