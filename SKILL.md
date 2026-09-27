---
name: motion-programmer
description: Use when planning, writing, rendering, inspecting, revising, or saving deterministic portrait motion scenes in this repository.
---

# Motion programmer

Build a visual explanation from Python scene code. A model may write the program; Cairo, Pillow, and FFmpeg produce the pixels. Keep each stage inspectable.

## Working loop

1. **Name the narrative job.** Write one sentence describing what the viewer should understand at the end of the scene. Record audience, duration, format, and style. Completion: the scene has one clear information goal.
2. **Choose a visual concept.** Pick a pattern from `motion.harness.MotionHarness.list_scene_patterns()` or describe a custom composition. Map the key nouns to components and the key relationships to paths, arrows, spacing, or transformation. Completion: the visual can be sketched without listing animation methods.
3. **Search memory.** Query `MemoryStore.search(style=..., concepts=(...), techniques=(...))` and inspect matching `intent.md`, `scene.py`, and stills via `read_example`. Reuse a treatment only when its intent matches; quality and feedback are evidence, not instructions. Completion: cite the useful example or record that no relevant one exists.
4. **Plan the beat.** Write a `StoryboardScene` and `ScenePlan` before substantial implementation. Use `MotionHarness.create_project`, `save_storyboard`, and `save_scene_plan` for a multi-scene run. Completion: timing, visual strategy, needed components, and memory queries are explicit.
5. **Write the smallest scene that communicates.** Use `PortraitScene`, style tokens, named elements, explicit start/duration, and one clear focal point per beat. Prefer connected object transformations when the explanation benefits from continuity. Completion: a reader can identify what exists and when each part appears from the source.
6. **Inspect stills.** Render opening, transition, and resolved timestamps with `motion still` or a contact sheet with `motion inspect`. Check safe area, readable text, hierarchy, overlaps, and whether the visual expresses the intended relationship. Completion: every sampled frame has a clear focal point and fits the portrait canvas.
7. **Inspect motion.** Render `motion preview` at 360×640 and 15 FPS. Watch entry, hold, transition, and exit. Check whether motion introduces, explains, connects, emphasizes, compares, reveals, or directs attention. Revise source, then repeat stills and preview. Completion: motion clarifies the idea and the pace allows reading.
8. **Finalize and remember.** Render at 1080×1920 and 30 FPS; verify codec, dimensions, and playback with `ffprobe` or a decode check. Save a useful scene and representative stills through `MemoryStore.save`, then record feedback with `add_feedback`. Completion: editable source and inspection artifacts accompany the final video.

The loop is **create → render → inspect → correct → remember**. Import success and valid PNGs do not establish visual quality.

## Authoring contract

```python
from motion import DrawPath, FadeIn, Folder, PortraitScene

scene = PortraitScene(duration=5, style="blueprint", seed=42)
folder = Folder(x=540, y=950, width=620, label="project", name="project")
folder.add_to(scene)
scene.animate(folder.parts["body"], FadeIn(start=.2, duration=.5))
scene.animate(folder.parts["tab"], DrawPath(start=.6, duration=.8))
```

`scene` can also be built by `build_scene(config)` with `PortraitScene.from_config(config, duration=..., ...)`. Precedence is library defaults → `motion.toml` → explicit scene arguments → CLI output overrides. Output resolution preserves the scene aspect ratio. The design space is 1080×1920 by default even when previewing at 360×640.

Elements are immutable definitions. `scene.elements_at(t)` evaluates explicit property tracks at a requested timestamp. `FadeIn`, `FadeOut`, `Move`, `Scale`, `Rotate`, `Keyframe`/`Keyframes`, `DrawPath`, `Reveal`, `MaskReveal`, `Sequence`, `Parallel`, and `scene.stagger` use explicit timing. Overlapping animations on one property are errors. Camera x/y, zoom, and rotation evaluate at time `t`; background, overlay, and captions remain fixed while environment, content, and foreground move. Use the camera for a motivated push or reframe, then let the viewer read.

Seed every randomized visual. `ParticleEmitter`, `Crowd`, Blueprint grid variation, grain, and noise derive output from seed and timestamp; never depend on a previous rendered frame. Local image and SVG assets must be stable. SVG input is self-contained; external resources are rejected. Audio tracks are declarative `AudioTrack` values on `scene.audio`; FFmpeg mixes them at export. No TTS runs in the engine.

## Portrait composition

`scene.safe_box` is the usable box. Defaults: 120 px top exclusion, 220 px bottom exclusion, and 90 px side margins. Put headings in the upper safe region, the main relationship in the central field, and captions above the bottom exclusion. Inspect text at preview size. A line can be technically inside the safe box and still too small to read.

Use `Box`, `place`, `stack`, and `grid` for predictable geometry. Use measured `Text` roles (`display`, `headline`, `title`, `body`, `caption`, `annotation`, `label`) and `max_width` for wrapping. Use `motion.typography.layout_text` when a component needs an exact bound. Bundled IBM Plex fonts avoid host font substitution.

Blueprint uses deep navy or warm paper, pale technical strokes, sparse amber emphasis, a measured grid, and diagram construction. Cinematic uses near-black space, muted steel blue, restrained amber light, procedural silhouettes, and slow emphasis. A style changes visual language while semantic content stays the same. See `styles/blueprint/STYLE.md` and `styles/cinematic/STYLE.md`.

Components return named `parts`, `bounds`, and `anchors`. Animate `parts` directly. `Folder`, `File`, `Arrow`, `CommitGraph`, `Computer`, `Server`, `Terminal`, `Browser`, `Graph`, `Chart`, `Crowd`, `Quote`, and other factories are in `motion`. Scene patterns (`ProcessScene`, `GraphScene`, `StatisticsScene`, and others) supply reusable compositions; edit their source or compose primitives directly when the narrative needs a different structure. Avoid topic-specific generic factories.

## Inspection commands

```bash
uv run motion styles
uv run motion examples
uv run motion memory search --style blueprint --concept branching --limit 5
uv run motion still examples/blueprint/git_history.py --time 9 --resolution 360x640 --output .build/check.png
uv run motion inspect examples/blueprint/git_history.py --times 0,3,6,9,12,18 --output .build/sheet.png
uv run motion preview examples/blueprint/git_history.py --output .build/preview.mp4
uv run motion render examples/blueprint/git_history.py --resolution 1080x1920 --fps 30 --output .build/final.mp4
```

The `MotionHarness` exposes `list_styles`, `list_assets`, `list_components`, `list_scene_patterns`, `search_memory`, `read_example`, `render_still`, `render_contact_sheet`, `render_preview`, `render_scene`, `inspect_project`, and `save_memory`. Keep a run's `request.json`, `storyboard.json`, `scene-plans/`, `generated-scenes/`, `previews/`, `stills/`, `inspection/`, and `final/`. Model provider integration belongs outside this library.

## Visual review

- Check one dominant subject at each beat; supporting marks should defer.
- Read at actual preview scale. Remove copy that competes with the diagram.
- Inspect the first and last frames, plus moments immediately before and after every major reveal.
- Verify connectors actually join the objects they claim to relate.
- Watch continuity across cuts: reuse a spatial relation or object when it carries meaning; make editorial cuts deliberate.
- Compare the still with the scene intent. If the image alone cannot explain the relationship, revise composition before adding motion.

Motion should introduce, explain, connect, emphasize, compare, reveal, transition, establish scale, direct attention, show causality, or show progression. Question animation that serves none of these purposes. Resist bouncing every object, separate fades for every item, gratuitous rotation, constant camera motion, glow or particles on every beat, excessive cards, dashboard framing for unrelated subjects, and repeated center-aligned slide compositions.

## Performance and failure diagnosis

Render stills before full previews and previews before final resolution. A frame at `t` should render without frames `0..t`; test out-of-order timestamps when changing evaluation. Keep effects restrained: full-frame Blur and Noise cost more than vector strokes. Reuse immutable fonts, SVG conversions, and raster assets through the existing caches. Do not add a frame simulation loop for particles.

Errors name the element and timestamp where possible. For a failure, inspect the named source element, asset path, style, and requested timestamp; reproduce with `motion still`. FFmpeg errors include stderr and frame input details. Preserve the previous output until a replacement finishes successfully.
