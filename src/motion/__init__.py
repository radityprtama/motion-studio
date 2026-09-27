"""Deterministic, code-authored motion graphics."""

from .animation import DrawPath, FadeIn, FadeOut, Keyframe, Keyframes, MaskReveal, Move, Reveal, Rotate, Scale
from .audio import AudioTimeline, AudioTrack
from .camera import Camera
from .composition import Parallel, Sequence
from .components import Arrow, CommitGraph, CommitNode, Component, Crowd, File, Folder, Orb, Person, Timeline
from .components_extra import Badge, Browser, Card, Chart, Computer, Graph, Label, ObjectGrid, Quote, Server, Terminal
from .effects import Blur, Glow, Grain, Noise, Shadow, Vignette
from .layout import Box, grid, place, stack
from .patterns import ComparisonScene, CrowdScene, EditorialScene, FlowScene, GraphScene, HierarchyScene, ProcessScene, QuoteScene, StatisticsScene, TimelineScene
from .primitives import Circle, Ellipse, Image, Line, ParticleEmitter, Path, RadialLight, Rectangle, RoundedRectangle, SVG, Text
from .scene import PortraitScene

__all__ = [
    "Arrow", "AudioTimeline", "AudioTrack", "Badge", "Box", "Browser", "Camera", "Card", "Chart", "Circle", "CommitGraph", "CommitNode", "ComparisonScene", "Component", "Computer", "Crowd", "CrowdScene", "DrawPath", "EditorialScene", "FadeIn", "FadeOut", "File", "FlowScene", "Folder", "Graph", "GraphScene", "HierarchyScene", "Keyframe", "Keyframes", "Label", "MaskReveal", "Move", "ObjectGrid", "Orb", "Parallel", "Person", "ProcessScene", "Quote", "QuoteScene", "Server", "StatisticsScene", "Terminal", "TimelineScene",
    "ParticleEmitter", "Path", "PortraitScene", "RadialLight", "Rectangle", "Reveal", "Rotate", "RoundedRectangle", "Ellipse", "Line", "Image", "SVG", "Scale", "Sequence", "Text", "Timeline", "Blur", "Glow", "Grain", "Noise", "Shadow", "Vignette",
    "grid", "place", "stack",
]
__version__ = "0.1.0"
