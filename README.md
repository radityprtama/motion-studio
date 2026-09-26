# Motion Studio

Motion Studio is a local Python toolkit for code-authored portrait motion graphics. A scene is a deterministic animation program: it defines visual elements, timing, style, and a seed. Cairo draws the geometry, Pillow handles bundled-font text masks, and FFmpeg encodes the frames.

It is not a text-to-video model. It does not generate images or video with a model. A future coding agent can plan and write scene programs, inspect their rendered output, and revise them while this renderer stays independent of the model provider.

## Requirements and installation

- Python 3.12 or newer. The repository uses `uv` to install Python 3.12 and create a local environment.
- The Cairo shared library (`libcairo`) available to `cairocffi`.
- FFmpeg and `ffprobe` on `PATH`, with the `libx264` encoder.

```bash
uv python install 3.12
uv sync --extra dev
uv run motion --help
```

The project bundles IBM Plex Sans and IBM Plex Mono under the [SIL Open Font License](src/motion/assets/fonts/OFL.txt). The files come from the official IBM Plex repository: [Sans Regular](https://github.com/IBM/plex/blob/master/packages/plex-sans/fonts/complete/ttf/IBMPlexSans-Regular.ttf), [Mono Regular](https://github.com/IBM/plex/blob/master/packages/plex-mono/fonts/complete/ttf/IBMPlexMono-Regular.ttf), and [license](https://github.com/IBM/plex/blob/master/LICENSE.txt). Keeping fonts with the package makes text placement independent of host font discovery.

## Render the first scene

The editable [snapshot scene](examples/blueprint/snapshot.py) is a four-second explanation of a Git commit.

```bash
uv run motion still examples/blueprint/snapshot.py --time 2.5 --output .build/still.png
uv run motion preview examples/blueprint/snapshot.py --output .build/preview.mp4
uv run motion render examples/blueprint/snapshot.py --resolution 1080x1920 --fps 30 --output .build/final.mp4
```

The preview defaults to 360×640 at 15 FPS. Final rendering defaults to the scene's 1080×1920 design size and 30 FPS. Pass `--width` and `--height` together, or `--resolution WIDTHxHEIGHT`, to change output size. This initial renderer preserves a 9:16 aspect ratio. Existing output files are protected; pass `--overwrite` when replacement is intentional.

The second editable example, [Git graph](examples/blueprint/git_graph.py), draws a history line, splits a branch, and finishes with a restrained camera push:

```bash
uv run motion preview examples/blueprint/git_graph.py --output .build/git-graph-preview.mp4
uv run motion still examples/blueprint/git_graph.py --time 4.5 --output .build/git-graph-still.png
```

To verify the final video:

```bash
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,nb_frames -of json .build/final.mp4
```

## Write a scene

```python
from motion import Circle, FadeIn, Move, PortraitScene, Text

scene = PortraitScene(duration=4, fps=30, seed=42, style="blueprint")
title = scene.add(Text("A commit saves a snapshot", x=540, y=300, role="headline"))
node = scene.add(Circle(x=540, y=1100, radius=80, fill="#D9A66F"))

scene.animate(title, FadeIn(start=0, duration=0.5))
scene.animate(node, Move(start=1, duration=1, from_y=1200, to_y=1100))
scene.animate(node, FadeIn(start=1, duration=0.5))
```

Save the file with a module-level variable named `scene`. The CLI loads that scene definition. The Python API also exposes `scene.render_still(...)`, `scene.render_preview(...)`, and `scene.render(...)`.

`PortraitScene` uses 1080×1920 design coordinates by default. Its safe area starts 120 pixels below the top and ends 220 pixels above the bottom, with 90-pixel side margins. `scene.content_box` returns `(left, top, right, bottom)`. The renderer scales the design space for previews, so scene code keeps one composition.

Elements are drawn in `background`, `environment`, `content`, `foreground`, `overlay`, and `captions` order. Within a layer, `z_index` and then addition order decide which element is in front. Elements are immutable definitions. `Move`, `FadeIn`, and `FadeOut` calculate values from the requested timestamp and do not mutate a previous frame. Overlapping animations of the same property are rejected.

## Paths, composition, and camera

`Path` takes local polyline points. `DrawPath` reveals equal fractions of measured length over equal time, even when its segments differ in length. `Reveal` clips an element from a specified direction. `MaskReveal` uses a Rectangle or Circle definition as a growing vector clip. The mask remains applied at full progress.

`Scale` and `Rotate` animate an element around its anchor. `Sequence` places its child animations one after another; `Parallel` gives them a shared start. A child's `start` is relative to its containing group. `scene.stagger(elements, animation, start=..., step=...)` copies one animation across an ordered set of elements. These operations expand to explicit property tracks when attached, and conflicts are checked before anything is changed.

```python
from motion import Circle, DrawPath, FadeIn, Parallel, Path, PortraitScene, Scale

scene = PortraitScene(duration=3, seed=42)
line = scene.add(Path(x=500, y=700, points=((0, 0), (0, 500)), stroke_width=5))
node = scene.add(Circle(x=500, y=1200, radius=30))
scene.animate(line, DrawPath(start=0.2, duration=2))
scene.animate(node, Parallel(FadeIn(duration=0.4), Scale(duration=0.4, from_x=0.85, to_x=1, from_y=0.85, to_y=1), start=2))
scene.camera.animate(zoom=(1, 1.08), start=1, duration=2, easing="ease_out_cubic")
```

Camera position, zoom, and rotation are also direct-time tracks. It moves the `environment`, `content`, and `foreground` layers. Background, overlay, and captions remain fixed on the portrait canvas. Increasing camera zoom pushes in. The public angle unit is degrees.

## Determinism

The same scene code, bundled assets, seed, dependency versions, and output settings produce the same frames in the same rendering environment. Every frame is evaluated directly from its timestamp. The seeded Blueprint grid is reconstructed from the scene seed for each frame. The tests compare decoded pixel bytes from repeated and out-of-order requests. Encoded MP4 byte equality is not promised across FFmpeg versions or platforms.

## Architecture and workflow

```text
Python scene definition
  -> property evaluation at time t
  -> fresh Cairo frame with Pillow font masks
  -> numbered PNG frames
  -> one FFmpeg encoder boundary
  -> preview or final MP4
```

For motion design, start with the narrative purpose, choose a visual concept, write the smallest scene that explains it, inspect opening and resolved stills, inspect preview motion, revise, then render final. A successful import or MP4 encode does not prove that the composition works. The [first-slice design](docs/superpowers/specs/2026-09-26-motion-studio-foundation-design.md) records the renderer contract and visual decisions.

The current working foundation has Rectangle, Circle, Text, Path, direct-time transforms and camera, animation composition, reveals, stills, previews, final video export, portrait safe areas, Blueprint tokens, and deterministic frame tests. The staged v0.1 roadmap adds layout, semantic components, and more scene patterns; a restrained Cinematic style; contact sheets and audio; filesystem memory; typed storyboard and scene plans; a provider-neutral harness; a comprehensive agent skill; and a 15–20 second Git-history reference film. Those parts should be built only after their preceding visual examples have been inspected.

Run the test suite with `uv run pytest -q`.
