"""Visual tokens are separate from the meaning of a scene."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TypographyToken:
    family: str
    size: int
    weight: str = "regular"
    line_height: float = 1.18
    color: str | None = None


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
    grid_color: str = "#527B93"
    grid_opacity: float = 1.0
    component_stroke: float = 4.0

    def text_token(self, role: str) -> TypographyToken:
        tokens = {
            "display": TypographyToken("sans", 112, "semibold", 1.08),
            "headline": TypographyToken("sans", self.headline_size),
            "title": TypographyToken("sans", 62, "semibold", 1.14),
            "body": TypographyToken("sans", self.body_size),
            "caption": TypographyToken("sans", 38, "regular", 1.2),
            "annotation": TypographyToken("mono", self.annotation_size),
            "label": TypographyToken("mono", 30),
        }
        try:
            return tokens[role]
        except KeyError as exc:
            raise ValueError(f"Unknown text role {role!r}; available roles: {', '.join(tokens)}") from exc

    def font_path(self, family: str, weight: str) -> Path:
        if family not in ("sans", "mono") or weight not in ("regular", "semibold"):
            raise ValueError(f"Unsupported font family/weight: {family}/{weight}")
        suffix = "Regular" if weight == "regular" else "SemiBold"
        name = "Sans" if family == "sans" else "Mono"
        path = _FONT_DIR / f"IBMPlex{name}-{suffix}.ttf"
        if not path.is_file():
            raise FileNotFoundError(f"Bundled font {path} is missing; reinstall motion-studio")
        return path

    def font_for(self, role: str) -> tuple[Path, int]:
        token = self.text_token(role)
        return self.font_path(token.family, token.weight), token.size


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
