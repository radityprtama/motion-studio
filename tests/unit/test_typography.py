import pytest

from motion.primitives import Text
from motion.renderer import render_frame
from motion.scene import PortraitScene
from motion.style import get_style
from motion.typography import layout_text


def test_roles_and_overrides() -> None:
    style = get_style("blueprint")
    for role in ("display", "headline", "title", "body", "caption", "annotation", "label"):
        assert style.text_token(role).size > 0
    text = Text("Branch", x=500, y=400, role="title", font_size=45, font_weight="semibold", letter_spacing=3)
    layout = layout_text(text, style)
    assert layout.font.size == 45
    assert "SemiBold" in layout.font_path.name
    assert "Mono" in layout_text(Text("Branch", x=500, y=400, role="title", font_family="mono"), style).font_path.name
    assert layout.lines[0].width > layout_text(Text("Branch", x=500, y=400, role="title", font_size=45), style).lines[0].width


def test_wrap_newline_and_alignment() -> None:
    style = get_style("blueprint")
    text = Text("first line\nlonger second line", x=500, y=300, role="annotation", anchor="right", max_width=250)
    layout = layout_text(text, style)
    assert len(layout.lines) >= 3
    assert all(line.left + line.width <= 500 for line in layout.lines)
    assert all(line.width <= 250 for line in layout.lines)
    assert layout.bounds[1] == 300


def test_invalid_typography_is_rejected() -> None:
    with pytest.raises(ValueError, match="font_size"):
        Text("bad", x=0, y=0, font_size=0)
    with pytest.raises(ValueError, match="weight"):
        Text("bad", x=0, y=0, font_weight="heavy")
    with pytest.raises(ValueError, match="family"):
        Text("bad", x=0, y=0, font_family="serif")
    with pytest.raises(ValueError, match="role"):
        Text("bad", x=0, y=0, role="unknown")


def test_measured_bounds_match_drawn_mask() -> None:
    empty = PortraitScene(duration=1, width=360, height=640, safe_top=20, safe_bottom=20, content_margin=20)
    filled = PortraitScene(duration=1, width=360, height=640, safe_top=20, safe_bottom=20, content_margin=20)
    text = filled.add(Text("Measured", x=180, y=220, role="label", font_size=36, letter_spacing=2))
    reference = render_frame(empty, 0)
    frame = render_frame(filled, 0)
    changed = [
        (x, y) for y in range(190, 290) for x in range(20, 340)
        if frame.getpixel((x, y)) != reference.getpixel((x, y))
    ]
    assert changed
    left, top, right, bottom = layout_text(text, get_style("blueprint")).bounds
    assert min(x for x, _ in changed) >= left - 1
    assert max(x for x, _ in changed) <= right + 1
    assert min(y for _, y in changed) >= top - 1
    assert max(y for _, y in changed) <= bottom + 1
