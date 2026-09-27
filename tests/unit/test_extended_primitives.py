from pathlib import Path

from PIL import Image as PILImage
import pytest

from motion import DrawPath, Ellipse, Image, Line, PortraitScene, RoundedRectangle, SVG
from motion.renderer import render_frame


def test_vector_and_raster_primitives_render_deterministically(tmp_path: Path) -> None:
    png = tmp_path / "asset.png"
    PILImage.new("RGBA", (8, 8), "#D9A66F").save(png)
    svg = tmp_path / "mark.svg"
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"><circle cx="10" cy="10" r="8" fill="#D9A66F"/></svg>')
    scene = PortraitScene(duration=2)
    scene.add(RoundedRectangle(x=540, y=300, width=300, height=200, radius=25, fill="#527B93"))
    scene.add(Ellipse(x=540, y=700, radius_x=90, radius_y=45, fill="#D9A66F"))
    line = scene.add(Line(x=250, y=900, dx=580, dy=0, stroke="#F2EBDD"))
    scene.animate(line, DrawPath(start=0, duration=2))
    scene.add(Image(x=540, y=1150, width=100, height=100, source=png))
    scene.add(SVG(x=540, y=1450, width=100, height=100, source=svg))
    first = render_frame(scene, 1.5, width=90, height=160).tobytes()
    render_frame(scene, .2, width=90, height=160)
    assert render_frame(scene, 1.5, width=90, height=160).tobytes() == first


def test_svg_external_resource_is_rejected(tmp_path: Path) -> None:
    svg = tmp_path / "external.svg"
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"><image href="https://example.com/a.png"/></svg>')
    scene = PortraitScene(duration=1)
    scene.add(SVG(x=540, y=960, width=100, height=100, source=svg, name="bad_asset"))
    with pytest.raises(Exception, match="bad_asset.*self-contained"):
        render_frame(scene, 0, width=90, height=160)
