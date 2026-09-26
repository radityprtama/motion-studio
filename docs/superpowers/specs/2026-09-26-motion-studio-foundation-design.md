# Motion Studio: first rendering slice

Date: 2026-09-26
Status: approved design

## Purpose and scope

This is the first implementation slice of a Python motion studio whose programs, rather than a generative image or video model, produce every frame. It proves that a readable portrait scene program can render an intentional motion graphic at arbitrary timestamps and encode a playable MP4. The larger v0.1 scope remains the product goal, but its components, scene patterns, memory, harness, audio, and full Git demo follow this verified slice.

The repository was empty at design time. FFmpeg 5.1.9 with `libx264` is installed. The host Python is 3.11.2, so the project will use a local Python 3.12 environment managed by `uv`. The Cairo shared library is installed; Python graphics packages are not.

## Chosen approach

Use Cairo for vector drawing through `cairocffi`, Pillow for bundled-font text measurement and raster masks, and FFmpeg for video encoding. `cairocffi` is a Cairo binding that avoids a local Pycairo C-extension build while using the same system Cairo renderer. NumPy is deferred until a procedural effect needs it. A Pillow-only renderer would weaken path and transform work; an SVG intermediate would add conversion and error surfaces to the first milestone.

The first style is Blueprint on deep navy. Warm paper is a later variant of the same style. The scene's meaning is independent of these tokens.

## Scene contract

The public authoring surface for this slice is explicit:

```python
scene = PortraitScene(duration=4.0, fps=30, seed=42, style="blueprint")
title = Text("A commit saves a snapshot", x=540, y=330, role="headline")
scene.add(title)
scene.animate(title, FadeIn(start=0.0, duration=0.5))
scene.render_still(time=2.5, output="still.png")
scene.render_preview(output="preview.mp4")
scene.render(output="final.mp4")
```

The scene contains duration, frame rate, seed, style, elements, and animation assignments. Elements are immutable definitions with an optional name, base geometry, layer, and `z_index`. Addition order breaks final drawing-order ties. Duplicate explicit names are errors. The renderer never mutates definitions or carries state from the previous frame.

The first primitives are Rectangle, Circle, and Text. They support position, size where relevant, opacity, layer, and z-order. The first animations are Move, FadeIn, and FadeOut. Move names its affected axes and explicit starting and ending values. FadeIn evaluates from zero to the element's base opacity; FadeOut evaluates from the base opacity to zero. All use `start`, `duration`, and an easing name. Values are clamped before and after an animation. Animations on different properties compose. Animations whose half-open active intervals `[start, start + duration)` overlap on the same element property are rejected with an actionable error. A later non-overlapping animation takes over at its stated start; between animations, the last end value holds. This rule gives direct timestamp evaluation without frame history.

Use seconds as the public timing unit. Rendered frames sample `t = frame_index / output_fps` for `frame_index` in `0..ceil(duration * output_fps)-1`; these samples are strictly before duration. A requested still accepts `0 <= t <= duration`. Easing and interpolation are pure functions. The slice implements linear, ease-in, ease-out, and ease-in-out; the remaining requested easing functions belong to the animation milestone.

## Portrait coordinates and style

Scene coordinates use a 1080 by 1920 portrait design space. Default safe areas are 120 pixels at the top, 220 at the bottom, and 90 at each side. `PortraitScene` exposes the content rectangle and safe-zone helpers. Optional debug guides can be rendered into inspection stills but never into final output by default. Content is not silently repositioned or clipped to the safe area.

Preview renders scale the design space to 360 by 640 at 15 FPS. This changes raster size and temporal sampling, not element coordinates or layout. Explicit CLI output settings override scene output settings; scene settings override library defaults. A project configuration file is introduced in a later tooling milestone, at which point it sits between library defaults and scene settings.

The first Blueprint tokens use deep navy `#0D1D2B`, warm off-white `#F2EBDD`, technical blue `#527B93` for secondary strokes, and restrained amber `#D9A66F` for the saved snapshot. Navy supports pale diagram marks; amber marks the one narrative change. A faint grid makes spatial relationships read like a drawing, without competing with the content. Bundle licensed IBM Plex Sans and IBM Plex Mono files: sans for the primary explanation, mono for small technical annotations. Typography uses measured glyph widths and boxes from Pillow, with wrapping based on those measurements. Pillow creates an alpha mask from the bundled font; Cairo applies that mask in element order, preserving normal layering. Missing font files fail explicitly.

Design read: short-form technical explainer for portrait viewers in a Blueprint visual language. Dials: ENERGY 2, RHYTHM 2, MOTION 2. Each screen has one clear focal point. Motion introduces, connects, or emphasizes information. It does not add repeated bouncing or decorative fades.

## Rendering and export flow

1. Load a scene file that exports `scene` and validate its definitions.
2. Select output dimensions and FPS from defaults, scene, and explicit CLI flags.
3. At each sampled time, evaluate all element properties from definitions and animation assignments.
4. Draw a fresh Cairo image surface in stable layer, z, and addition order. Text is measured and masked from the bundled font through Pillow.
5. Write numbered PNG frames into a newly created temporary directory.
6. Invoke FFmpeg from one export adapter using the PNG sequence as an explicit-frame-rate input, `libx264`, and `yuv420p`. Encode to a temporary output and move it into place only after FFmpeg succeeds. Refuse to replace an existing user output unless overwrite was explicitly requested. Capture stderr and report the command context on failure. Clean only the temporary directory this invocation created.

`motion still <scene> --time ...`, `motion preview <scene>`, and `motion render <scene>` are the first CLI commands. The CLI prints style, duration, resolution, FPS, seed, frame count, and bounded progress updates. A scene can also call the matching Python methods. The later tooling milestone adds contact sheets and fuller configuration.

The frame promise is deterministic for the same code, bundled assets, dependency versions, seed, and settings in the same rendering environment. Tests compare decoded PNG pixel bytes or hashes, including renders requested out of order. MP4 byte equality is not promised because container metadata and encoder versions may differ; visual frames and timing are the relevant contract.

## First proof scene

A four-second portrait Blueprint composition explains that a commit records a project snapshot. A headline anchors the upper content zone. Three simple file marks enter a project frame, then the composition resolves toward one highlighted commit circle and a concise annotation. The main visual occupies the portrait center; the lower safe region stays clear. The scene uses only the first three primitives and Move/Fade animations. Its source remains editable and contains no prerecorded frames or generated imagery.

The proof scene is checked through representative stills, a 360 by 640 preview, and a 1080 by 1920, 30 FPS final MP4. Inspection covers hierarchy, spacing, typography, color restraint, and whether each motion serves the explanation. If a visual issue appears, fix the scene or renderer and rerender before calling the slice complete.

## Errors and verification

Validation errors identify the scene file, element, property, and invalid timing or value. Drawing failures identify scene, element, and timestamp and preserve the original exception. Resource errors name the missing font or file. FFmpeg failures include expected input pattern, FPS, exit code, and relevant stderr. An interrupted export leaves no user-owned files deleted.

Unit tests cover interpolation boundaries, easing endpoints, animation composition and overlap rejection, frame sample times, stable layer/z ordering, safe-area math, and output setting precedence. A small render test compares frame hashes from repeated and out-of-order timestamp requests. An integration test runs FFmpeg on a short low-resolution clip and verifies its dimensions, frame rate, duration, and codec with `ffprobe`. The full-size proof render is a milestone artifact, not a fixture committed to tests. Snapshot tests avoid promising identical font rasterization across different platform versions.

The slice is complete only when the package installs under Python 3.12, the CLI and Python API render still/preview/final outputs, the final MP4 plays, the deterministic frame tests pass, and a human inspection finds the proof scene intentionally composed.

## Subsequent implementation milestones

After this slice, expand in this order, validating each with stills and preview motion before moving on:

1. Full animation language, path drawing, camera, transform composition, and explicit layering.
2. Portrait layout helpers, typography roles, safe-zone examples, and procedural components required by the Git narrative.
3. Complete Blueprint style, useful semantic scene patterns, and a basic restrained Cinematic style with procedural particles and effects.
4. Preview/contact-sheet tooling, project configuration, audio timeline and centralized FFmpeg composition.
5. Filesystem memory with quality-weighted retrieval and feedback; typed storyboard and scene-plan schemas; provider-neutral agent harness and inspection artifacts.
6. Multiple instructional examples, a polished 15–20 second Git-history program, visual revision, preview, stills, contact sheet, and 1080 by 1920 final render.
7. Comprehensive README, AGENTS.md, and agent-facing SKILL.md documenting the create, render, inspect, revise, and remember loop.

Each milestone gets a focused plan. Future model integration, vector search, GPU rendering, web UI, and distributed rendering remain outside v0.1.

## Documentation consulted

- [CairoCFFI image surfaces, contexts, and masks](https://doc.courtbouillon.org/cairocffi/stable/api.html)
- [Pillow font loading and metrics](https://github.com/python-pillow/pillow/blob/main/docs/reference/ImageFont.rst)
- [FFmpeg image sequence input and frame rate](https://ffmpeg.org/ffmpeg-all.html)
