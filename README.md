# Motion Studio

Motion Studio is a local Python toolkit for code-authored portrait motion graphics. A scene is a deterministic animation program: it defines visual elements, timing, style, and a seed. Cairo draws the geometry, Pillow handles bundled-font text masks and raster finishing, CairoSVG loads self-contained SVGs, and FFmpeg encodes and mixes the result.

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

`uv sync` installs Pillow, CairoCFFI, CairoSVG, and their small supporting packages. The engine uses only local assets. No model, cloud service, or API key is required.

The project bundles IBM Plex Sans and IBM Plex Mono, in Regular and SemiBold weights, under the [SIL Open Font License](src/motion/assets/fonts/OFL.txt). The files come from the [official IBM Plex repository](https://github.com/IBM/plex/tree/master/packages). Keeping fonts with the package makes text placement independent of host font discovery.

## Render the first scene

The editable [snapshot scene](examples/blueprint/snapshot.py) is a four-second explanation of a Git commit.

```bash
uv run motion still examples/blueprint/snapshot.py --time 2.5 --output .build/still.png
uv run motion preview examples/blueprint/snapshot.py --output .build/preview.mp4
uv run motion render examples/blueprint/snapshot.py --resolution 1080x1920 --fps 30 --output .build/final.mp4
```

The preview defaults to 360×640 at 15 FPS. Final rendering defaults to the scene's 1080×1920 design size and 30 FPS. Pass `--width` and `--height` together, or `--resolution WIDTHxHEIGHT`, to change output size. This initial renderer preserves a 9:16 aspect ratio. Existing output files are protected; pass `--overwrite` when replacement is intentional.

Build a labeled contact sheet from direct timestamps:

```bash
uv run motion inspect examples/blueprint/git_history.py --times 0,3,6,9,12,18 --output .build/git_history/sheet.png
uv run motion styles
uv run motion examples
```

`motion inspect` defaults to six evenly spaced samples in three columns. It draws only those frames, without encoding a video.

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

The Cinematic examples show a different visual language from the same deterministic engine: [atmospheric_title.py](examples/cinematic/atmospheric_title.py) uses a procedural orb and particle field; [crowd_statistic.py](examples/cinematic/crowd_statistic.py) highlights 17 of 100 procedural silhouettes.

```bash
uv run motion preview examples/cinematic/atmospheric_title.py --output .build/cinematic/atmospheric-preview.mp4
uv run motion preview examples/cinematic/crowd_statistic.py --output .build/cinematic/crowd-preview.mp4
uv run motion render examples/cinematic/crowd_statistic.py --resolution 1080x1920 --fps 30 --output .build/cinematic/crowd-final.mp4
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

`scene.safe_box` exposes that area as a `Box`. Pure `place`, `stack`, and `grid` helpers calculate positions in design coordinates and reject overflow. Text roles are `display`, `headline`, `title`, `body`, `caption`, `annotation`, and `label`. Text uses bundled font metrics for wrapping, alignment, visible bounds, and drawing. Explicit `font_family` (`sans` or `mono`), `font_size`, `font_weight`, `line_height`, and `letter_spacing` override style defaults.

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

The broader component vocabulary includes `Card`, `Computer`, `Server`, `Terminal`, `Browser`, `Graph`, `Chart`, `Quote`, `Label`, and `Badge`. All produce named primitive parts with bounds and anchors. `ComparisonScene`, `ProcessScene`, `TimelineScene`, `GraphScene`, `CrowdScene`, `StatisticsScene`, `EditorialScene`, `QuoteScene`, `HierarchyScene`, and `FlowScene` are semantic portrait compositions built on the same public API. Use them as editable starting points; the [request flow](examples/blueprint/request_flow.py) and [statistics composition](examples/portrait/statistics_composition.py) show two treatments. The [example map](examples/README.md) describes every source.

`cinematic` selects a near-black background, subtle seeded grain/vignette, and a muted steel-blue/amber palette. `RadialLight` uses a Cairo gradient; `ParticleEmitter` calculates each particle directly from its explicit seed and requested timestamp. `Orb`, `Person`, and `Crowd` are factories with named parts. `Crowd` accepts a `Box`, count, columns, seed, and highlighted indices. For highlighted people it returns ordinary base parts plus accent overlay parts such as `highlight:16:head`, so a scene can reveal emphasis at a chosen time. `ObjectGrid` repeats a component factory with a stable seed per item; [object_grid.py](examples/cinematic/object_grid.py) shows a 36-node study. The style has no model-generated imagery or frame-to-frame simulation.

Primitives also include `RoundedRectangle`, `Ellipse`, `Line`, `Image`, and `SVG`. Images are local raster assets; SVG files must be self-contained. `Blur`, `Glow`, `Grain`, `Noise`, and `Vignette` can be added as explicit frame effects with `scene.add_effect(effect)`. `Shadow.apply(image)` prepares a transparent raster asset before it is placed in a scene. Use full-frame effects sparingly because they cost more than vector drawing. The style guides are [Blueprint](styles/blueprint/STYLE.md) and [Cinematic](styles/cinematic/STYLE.md).

Elements are drawn in `background`, `environment`, `content`, `foreground`, `overlay`, and `captions` order. Within a layer, `z_index` and then addition order decide which element is in front. Elements are immutable definitions. `Move`, `FadeIn`, and `FadeOut` calculate values from the requested timestamp and do not mutate a previous frame. Overlapping animations of the same property are rejected.

## Paths, composition, and camera

`Path` takes local polyline points. `DrawPath` reveals equal fractions of measured length over equal time, even when its segments differ in length. `Reveal` clips an element from a specified direction. `MaskReveal` uses a Rectangle or Circle definition as a growing vector clip. The mask remains applied at full progress.

`Scale` and `Rotate` animate an element around its anchor. `Keyframes(channel="x", points=(Keyframe(0, 100), Keyframe(.5, 400), Keyframe(1, 300)))` defines an explicit multi-stop property track. `Sequence` places its child animations one after another; `Parallel` gives them a shared start. A child's `start` is relative to its containing group. `scene.stagger(elements, animation, start=..., step=...)` copies one animation across an ordered set of elements. These operations expand to explicit property tracks when attached, and conflicts are checked before anything is changed.

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

## Project configuration and audio

The repository's [motion.toml](motion.toml) defines project defaults. A scene can export `build_scene(config)` instead of a module-level `scene`:

```python
from motion import PortraitScene

def build_scene(config):
    return PortraitScene.from_config(config, duration=5, seed=42, style="cinematic")
```

Library defaults feed project settings; explicit scene arguments override them; CLI output flags override the render dimensions or FPS. Legacy scene files exporting `scene` continue to work. `--config path/to/motion.toml` selects a configuration explicitly, otherwise the CLI searches upward from the scene file. Preview defaults are independent of final render defaults. [configured_route.py](examples/basics/configured_route.py) is an executable factory example.

Audio belongs to the scene timeline and is mixed once by FFmpeg during final or preview export:

```python
from pathlib import Path
from motion import AudioTrack

scene.audio.add(AudioTrack(Path("assets/narration.wav"), "narration", start=0, duration=4.5, volume=1, fade_in=.1, fade_out=.2))
```

Kinds are `narration`, `music`, and `sfx`. Every track has start, duration, volume, fade in, and fade out. The engine does not synthesize speech. Use stable local files and resolve relative paths deliberately in a scene script.

## Memory and agent integration

`MemoryStore` keeps useful scenes in `memory/scenes/<id>/` with `metadata.json`, `intent.md`, editable `scene.py`, and representative PNG stills. Retrieval filters style and scene type, scores exact concept/technique/tag matches with quality, and excludes items below quality 0.5 by default. Feedback can revise quality and append comments without altering scene source.

```bash
uv run motion memory search --style blueprint --concept branching --limit 5
```

The provider-neutral `MotionHarness` exposes style, asset, component, scene-pattern, and example discovery; memory search/read/save; still, contact sheet, preview, and final render; and project artifact inspection. `Storyboard` and `ScenePlan` are typed, validated, JSON-serializable planning boundaries. A run can keep `request.json`, `storyboard.json`, `scene-plans/`, `generated-scenes/`, `previews/`, `stills/`, `inspection/`, and `final/`. A future coding agent can supply the planning and scene code without changing the renderer. [SKILL.md](SKILL.md) gives that agent the full working loop; [AGENTS.md](AGENTS.md) is the repository entry point.

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

v0.1 includes the deterministic portrait engine, two style packs, semantic components and patterns, direct-time tooling, filesystem memory, typed plans, audio export, and the inspected Git history film. The next roadmap is automatic vision-based review, semantic retrieval, additional styles, subtitle timing, and optional model-provider adapters. Those additions belong outside the deterministic renderer.

Run the fast test suite with `uv run pytest -q`. Build installable artifacts with `uv build`. FFmpeg integration tests use tiny videos; there are no large video fixtures.
