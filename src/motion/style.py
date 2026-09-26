"""Visual tokens are separate from the meaning of a scene."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


_FONT_DIR = Path(__file__).resolve().parent / "assets" / "fonts"


@dataclass(frozen=True)
class Style:
    name: str
    background: str
    primary: str
    secondary: str
    accent: str
    sans_font: Path
    mono_font: Path
    headline_size: int
    body_size: int
    annotation_size: int

    def font_for(self, role: str) -> tuple[Path, int]:
        if role == "headline":
            return self.sans_font, self.headline_size
        if role == "body":
            return self.sans_font, self.body_size
        if role == "annotation":
            return self.mono_font, self.annotation_size
        raise ValueError(f"Unknown text role {role!r}")


BLUEPRINT = Style(
    name="blueprint",
    background="#0D1D2B",
    primary="#F2EBDD",
    secondary="#527B93",
    accent="#D9A66F",
    sans_font=_FONT_DIR / "IBMPlexSans-Regular.ttf",
    mono_font=_FONT_DIR / "IBMPlexMono-Regular.ttf",
    headline_size=84,
    body_size=50,
    annotation_size=36,
)


def get_style(name: str) -> Style:
    if name == "blueprint":
        return BLUEPRINT
    raise ValueError(f"Unknown style {name!r}; available style: blueprint")
