# Motion Studio Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

This session uses inline execution because the user authorized the build and did not request delegated agents. Neither execution skill is installed, so the checked steps below are the execution record.

**Goal:** Render a deterministic four-second Blueprint portrait animation from Python as arbitrary stills, a small preview, and a playable 1080 by 1920 MP4.

**Architecture:** A scene stores immutable elements and time tracks. A renderer evaluates a fresh frame at the requested time, draws vector marks with Cairo, and places measured bundled-font text through Pillow alpha masks. An export module owns temporary PNG frames and the one FFmpeg invocation.

**Tech Stack:** Python 3.12, `cairocffi`, Pillow, pytest, FFmpeg 5.1+, `uv`. NumPy enters when procedural effects need it.

---

## File map

| Path | Responsibility |
| --- | --- |
| `pyproject.toml`, `.python-version`, `uv.lock` | Package, CLI entry point, reproducible Python dependencies |
| `src/motion/assets/fonts/` | Vendored IBM Plex Sans and Mono plus upstream license, included in the wheel |
| `src/motion/animation.py` | Easing, progress, Move, FadeIn, FadeOut, pure property evaluation |
| `src/motion/primitives.py` | Immutable Rectangle, Circle, Text definitions |
| `src/motion/style.py` | Blueprint colors, type tokens, font paths |
| `src/motion/scene.py` | Portrait safe area, element registry, track assignment and ordering |
| `src/motion/renderer.py` | Fresh Cairo surface at any timestamp, text masks, seeded grid |
| `src/motion/export.py` | Still, preview, frame directory, FFmpeg, output safety |
| `src/motion/cli.py` | Noninteractive `motion` command and scene-file loader |
| `src/motion/__init__.py` | Small public API |
| `examples/blueprint/snapshot.py` | Editable four-second proof scene |
| `tests/unit/`, `tests/integration/` | Cheap pure tests, render hashes, FFmpeg probe |
| `README.md` | Install and first rendering workflow |

## Task 1: Package and assets

**Files:** Create `pyproject.toml`, `.python-version`, `.gitignore`, `src/motion/assets/fonts/IBMPlexSans-Regular.ttf`, `src/motion/assets/fonts/IBMPlexMono-Regular.ttf`, `src/motion/assets/fonts/OFL.txt`, `src/motion/__init__.py`.

- [ ] **Step 1: Establish Python.** Run `uv python install 3.12`, then set `.python-version` to `3.12`.
- [ ] **Step 2: Add package metadata.** Use this dependency and entry-point core in `pyproject.toml`:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "motion-studio"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["cairocffi>=1.7,<2", "Pillow>=11,<13"]

[project.optional-dependencies]
dev = ["pytest>=8,<10"]

[project.scripts]
motion = "motion.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["src/motion"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 3: Vendor fonts from IBM's official Plex repository.** Download the two complete TTF files and the repository's OFL license into `src/motion/assets/fonts/`; commit the exact bytes and record the upstream paths in `README.md`. Resolve bundled paths through `importlib.resources.files("motion")`. The [official repository](https://github.com/IBM/plex) confirms the Open Font License.
- [ ] **Step 4: Install and smoke-check.** Run `uv sync --extra dev` and `uv run python -c 'import cairocffi, PIL; print("graphics imports OK")'`. Expected: `graphics imports OK`.
- [ ] **Step 5: Commit.** Commit package setup and font assets separately from renderer code.

## Task 2: Pure timeline and scene definitions

**Files:** Create `src/motion/animation.py`, `src/motion/primitives.py`, `src/motion/scene.py`, `tests/unit/test_animation.py`, `tests/unit/test_scene.py`.

- [ ] **Step 1: Write failing pure tests.** Include these exact assertions:

```python
assert progress(2.0, start=2.0, duration=1.0) == 0.0
assert progress(2.5, start=2.0, duration=1.0) == 0.5
assert progress(3.0, start=2.0, duration=1.0) == 1.0
assert Move(start=0, duration=1, from_x=0, to_x=100).value("x", 0.5, 10) == 50
assert FadeIn(start=1, duration=1).value("opacity", 0, 0.8) == 0
assert FadeIn(start=1, duration=1).value("opacity", 2, 0.8) == 0.8
```

Also assert a `PortraitScene` content box of `(90, 120, 990, 1700)`, stable layer/z/addition ordering, same-property overlap rejection, and out-of-order evaluation giving the same value.

- [ ] **Step 2: Run `uv run pytest tests/unit -q`.** Expected: import failures for missing motion modules.
- [ ] **Step 3: Implement immutable primitive definitions and pure animation values.** Use `@dataclass(frozen=True, kw_only=True)` for elements, `progress = clamp((t-start)/duration, 0, 1)`, and a fixed easing dictionary. Reject non-finite times, non-positive durations, invalid opacities, missing Move endpoint pairs, and unknown easing names. The scene stores entries as `(element, insertion_index)` and tracks keyed by element identity and property; it never mutates a primitive when evaluating.
- [ ] **Step 4: Implement explicit conflict and ordering rules.** Intervals are half-open `[start, start+duration)`. Different properties compose; overlapping assignments to the same property fail on `scene.animate`. Sort visible elements by `(layer_rank, z_index, insertion_index)` with ranks `background, environment, content, foreground, overlay, captions`.
- [ ] **Step 5: Run `uv run pytest tests/unit -q`.** Expected: all pure tests pass. Commit timeline, definitions, and tests.

## Task 3: Fresh-frame vector and text renderer

**Files:** Create `src/motion/style.py`, `src/motion/renderer.py`, `tests/unit/test_renderer.py`.

- [ ] **Step 1: Write a small frame test.** Render at `t=1.5`, then at `t=0.1`, then at `t=1.5` again; compare decoded RGBA bytes of the first and third frames. Render with a second seed and assert the subtle grid background changes while element geometry does not.
- [ ] **Step 2: Run `uv run pytest tests/unit/test_renderer.py -q`.** Expected: renderer import failure.
- [ ] **Step 3: Add Blueprint tokens.** Use `#0D1D2B` background, `#F2EBDD` primary marks, `#527B93` secondary strokes, and `#D9A66F` for the snapshot. Define headline/body/annotation sizes in design-space pixels and resolve both fonts by path relative to the repository, failing with the path when absent.
- [ ] **Step 4: Render each frame from scratch.** Create a Cairo ARGB32 image surface at output dimensions, scale its context from the 1080 by 1920 scene space, paint the background, draw a faint seeded grid, and draw evaluated primitives in scene order. Use `context.save()` and `context.restore()` around each element. Multiply element alpha by fill/stroke alpha. The grid uses a new `random.Random(scene.seed)` per frame, so it is stable at arbitrary timestamps.
- [ ] **Step 5: Draw text from bundled fonts.** Use `ImageFont.truetype(path, size)` and `getlength`/`getbbox` for wrapping and anchoring. Build an `L` mask, copy its bytes into a Cairo A8 surface with aligned stride, set the text color, and call `context.mask_surface(mask_surface, x, y)`. This preserves element order without relying on host font discovery.
- [ ] **Step 6: Run tests and inspect two PNGs.** Run `uv run pytest tests/unit -q`, render opening and resolved stills, and use image inspection. Fix clipped text, weak hierarchy, or unsafe placement before export work. Commit renderer and tests.

## Task 4: Output adapter and CLI

**Files:** Create `src/motion/export.py`, `src/motion/cli.py`, `tests/integration/test_export.py`.

- [ ] **Step 1: Add integration expectations.** A 0.4-second 90 by 160 scene at 10 FPS yields four frames; `ffprobe` reports H.264, 90 by 160, 10 FPS. An existing output path fails unless `overwrite=True`. A nonzero FFmpeg exit surfaces stderr and does not replace an existing file.
- [ ] **Step 2: Run `uv run pytest tests/integration -q`.** Expected: missing export module.
- [ ] **Step 3: Implement output methods.** `render_still` calls the frame renderer once at any validated `0 <= t <= duration`. `render_preview` selects 360 by 640 at 15 FPS unless explicit overrides are supplied. `render` defaults to 1080 by 1920 at the scene FPS. Both video methods write numbered PNGs in `TemporaryDirectory` and use exactly one adapter function to call FFmpeg with `-framerate`, `libx264`, and `yuv420p`. Encode to a sibling temporary file; replace the destination only after success.
- [ ] **Step 4: Add `motion still`, `motion preview`, and `motion render`.** Load a Python path with `importlib.util.spec_from_file_location`, require a `scene` export of type `PortraitScene`, and parse `--time`, `--output`, `--resolution`, `--fps`, and `--overwrite` as appropriate. Emit bounded progress and actionable errors with scene, element, time, resource, or FFmpeg context. Reject output aspect ratios other than 9:16 in this slice.
- [ ] **Step 5: Run `uv run pytest -q` and `uv run motion --help`.** Expected: passing tests and three subcommands. Commit export and CLI.

## Task 5: Proof scene, documentation, and rendered evidence

**Files:** Create `examples/blueprint/snapshot.py`, `README.md`; update `src/motion/__init__.py` with public exports.

- [ ] **Step 1: Author the four-second scene.** In a 1080 by 1920 Blueprint canvas, place a headline in the upper content area, a project frame and three file marks in the middle, and a single amber commit circle in the lower-middle area. Animate file marks in sequence, fade the project toward the commit, and hold the resolved diagram long enough to read. Every visible movement must introduce, connect, or emphasize the snapshot relationship.
- [ ] **Step 2: Render checkpoints.** Run `uv run motion still examples/blueprint/snapshot.py --time 0 --output .build/stills/start.png`, then times `1.5`, `3.0`, and `4.0`. Inspect them at original size and thumbnail size. Correct clipping, contrast, or hierarchy defects in scene or renderer code and rerender.
- [ ] **Step 3: Render motion evidence.** Run `uv run motion preview examples/blueprint/snapshot.py --output .build/preview.mp4`; inspect playback. Then run `uv run motion render examples/blueprint/snapshot.py --resolution 1080x1920 --fps 30 --output .build/final.mp4` and inspect playback. Verify final with `ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate -of json .build/final.mp4`.
- [ ] **Step 4: Verify determinism.** Render the same still twice with the same seed and compare SHA-256 hashes; request another timestamp between those renders and repeat the hash check. Keep a test for this property, not a platform-specific golden bitmap.
- [ ] **Step 5: Document first-use commands and boundaries.** README covers what the system is, its non-generative renderer, Python/FFmpeg prerequisites, installation, scene API, still/preview/final commands, determinism, and the staged v0.1 roadmap. Commit source, tests, and README. Keep `.build/` ignored; rendered artifacts are evidence in the workspace, not test fixtures.

## Exit review

- [ ] `uv run pytest -q` passes.
- [ ] `uv run motion --help` shows still, preview, and render.
- [ ] Still hashes match for repeated and out-of-order requests.
- [ ] Preview and final MP4s play, and `ffprobe` confirms the requested final format.
- [ ] Opening, middle, and resolved stills have been visually inspected and corrected.
- [ ] The implementation covers every first-slice requirement in the approved design; later v0.1 milestones remain explicitly tracked.
