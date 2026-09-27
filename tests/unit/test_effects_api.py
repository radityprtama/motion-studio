from PIL import Image

from motion import Blur, Glow, Grain, Noise, PortraitScene, Shadow, Vignette
from motion.renderer import render_frame


def test_effects_are_deterministic_and_direct_time() -> None:
    scene = PortraitScene(duration=2)
    scene.add_effect(Grain(.03, seed=21))
    scene.add_effect(Vignette(.2))
    first = render_frame(scene, 1.5, width=90, height=160).tobytes()
    render_frame(scene, .2, width=90, height=160)
    assert render_frame(scene, 1.5, width=90, height=160).tobytes() == first
    assert Grain(.1, 4).apply(Image.new("RGBA", (16, 16), "white")).tobytes() == Grain(.1, 4).apply(Image.new("RGBA", (16, 16), "white")).tobytes()
    assert Noise(.1, 4).apply(Image.new("RGBA", (16, 16), "white")).tobytes() == Noise(.1, 4).apply(Image.new("RGBA", (16, 16), "white")).tobytes()


def test_transparent_asset_effects_keep_alpha() -> None:
    image = Image.new("RGBA", (50, 50), (0, 0, 0, 0))
    image.putpixel((25, 25), (255, 255, 255, 255))
    assert Blur(2).apply(image).size == (50, 50)
    assert Glow(4, .4).apply(image).size == (50, 50)
    shadowed = Shadow(dx=3, dy=3, blur=0, opacity=1).apply(image)
    assert shadowed.getpixel((28, 28))[3] > 0
