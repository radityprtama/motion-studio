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

The project bundles IBM Plex Sans and IBM Plex Mono, in Regular and SemiBold weights, under the [SIL Open Font License](src/motion/assets/fonts/OFL.txt). The files come from the [official IBM Plex repository](https://github.com/IBM/plex/tree/master/packages). Keeping fonts with the package makes text placement independent of host font discovery.

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

The [18-second Git history film](examples/blueprint/git_history.py) uses named Folder, File, and CommitGraph parts to show the project becoming a snapshot and then a branching history. Its caption and heading stay fixed while the diagram receives one subtle camera move:

```bash
uv run motion preview examples/blueprint/git_history.py --output .build/git_history/preview.mp4
uv run motion still examples/blueprint/git_history.py --time 13.5 --resolution 360x640 --output .build/git_history/branch.png
uv run motion render examples/blueprint/git_history.py --resolution 1080x1920 --fps 30 --output .build/git_history/final.mp4
```

The preview is 360×640 at 15 FPS; the final render is 1080×1920 at 30 FPS. The editable program creates every frame through Cairo and Pillow. Media under `.build/` is ignored by Git. [paper_process.py](examples/blueprint/paper_process.py) uses the same component vocabulary with the warm paper Blueprint treatment.

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

`scene.safe_box` exposes that area as a `Box`. Pure `place`, `stack`, and `grid` helpers calculate positions in design coordinates and reject overflow. Text roles are `display`, `headline`, `title`, `body`, `caption`, `annotation`, and `label`. Text uses bundled font metrics for wrapping, alignment, visible bounds, and drawing. Explicit `font_size`, `font_weight`, `line_height`, and `letter_spacing` override style defaults.

## Semantic components and styles

Components are small factories for ordinary scene primitives. Each returns named `parts`, a `bounds` box, and `anchors` for connectors. Add the parts to a scene and animate them with the same tracks used for any primitive:

```python
from motion import DrawPath, FadeIn, Folder, PortraitScene

scene = PortraitScene(duration=3, style="blueprint", seed=42)
folder = Folder(x=540, y=900, width=620, label="project", name="project")
folder.add_to(scene)
scene.animate(folder.parts["body"], FadeIn(start=0.2, duration=0.5))
scene.animate(folder.parts["tab"], DrawPath(start=0.5, duration=0.6))
```

`Folder`, `File`, `Arrow`, `CommitNode`, `CommitGraph`, and `Timeline` are available. A `CommitGraph` takes ordered `(id, label, parent_id)` records and explicit positions. Its `parts` include `connector:<id>` and `node:<id>:ring/core/label`, so path and node timing remain visible in source. `blueprint` is the deep navy treatment; `blueprint-paper` uses warm paper and dark ink. Semantic components take a style name, while the scene chooses the matching background treatment.

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

The working foundation now includes portrait layout, measured typography, semantic Folder/File/Arrow/CommitGraph/Timeline components, two Blueprint treatments, and the inspected Git history film. The remaining v0.1 roadmap includes more primitives and scene patterns; a restrained Cinematic style; contact-sheet CLI and audio; filesystem memory; typed storyboard and scene plans; a provider-neutral harness; and a comprehensive agent skill. Build each visual feature with a render/inspect/revise loop.

Run the test suite with `uv run pytest -q`.
