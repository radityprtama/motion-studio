# Motion Language and Camera Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

This session executes inline, using the approved build authorization and no delegated agents.

**Goal:** Add direct-time transform composition, drawn paths, reveals, and a 2D camera, then prove them with a short Git graph scene.

**Architecture:** Primitive definitions stay immutable; animation composites expand into ordinary tracks at attachment time. The renderer applies camera transforms to world layers and element transforms to local geometry, then clips or shortens paths according to evaluated reveal values. Every frame is drawn on a new surface.

**Tech Stack:** Existing Python 3.12, CairoCFFI, Pillow, FFmpeg, pytest stack. No new dependency.

---

## File map

| Path | Responsibility |
| --- | --- |
| `src/motion/animation.py` | New easing, Scale, Rotate, DrawPath, Reveal, MaskReveal |
| `src/motion/composition.py` | Sequence/Parallel flattening with explicit offsets |
| `src/motion/camera.py` | Direct-time camera property tracks |
| `src/motion/primitives.py` | Base scale/rotation and polyline Path |
| `src/motion/scene.py` | Atomic composite attachment, stagger, evaluated state |
| `src/motion/renderer.py` | Camera/local transforms, partial paths, vector clips |
| `src/motion/__init__.py` | Public exports |
| `examples/blueprint/git_graph.py` | Inspected branch construction proof |
| `tests/unit/test_motion_language.py`, `tests/unit/test_camera.py`, `tests/unit/test_path.py` | Pure behavior and rendered contracts |
| `README.md` | Document new APIs and example commands |

## Task 1: Element transforms and animation values

**Files:** Modify `src/motion/animation.py`, `src/motion/primitives.py`, `src/motion/scene.py`, `src/motion/renderer.py`; create `tests/unit/test_motion_language.py`.

- [ ] **Step 1: Add failing tests.** Assert `ease("ease_out_cubic", 0.5) == 0.875`, all new easing endpoints, `Scale(...).value("scale_x", 0.5, 1)`, `Rotate(...).value("rotation", 0.5, 0)`, and unchanged bytes for the original snapshot at a fixed time before and after a transform-default render.
- [ ] **Step 2: Run `uv run pytest tests/unit/test_motion_language.py -q`.** Expected: missing new names.
- [ ] **Step 3: Add base fields and values.** `Element` gains `scale_x: float = 1`, `scale_y: float = 1`, `rotation: float = 0`; enforce positive finite scales. `Scale` names explicit from/to values per chosen axis and `Rotate` names from/to degrees. Easing extends the existing pure function. Add scale and rotation to `EvaluatedElement` and the same property-track lookup used by Move.
- [ ] **Step 4: Draw local geometry.** Inside each element's Cairo save/restore block, call `translate(state.x, state.y)`, `rotate(radians(state.rotation))`, then `scale(state.scale_x, state.scale_y)`. Rectangle, Circle, and Text draw relative to origin so default transforms reproduce the old scene.
- [ ] **Step 5: Run `uv run pytest -q`.** Expected: old and new tests pass. Commit transform changes.

## Task 2: Explicit composition and stagger

**Files:** Create `src/motion/composition.py`; modify `src/motion/scene.py`, `src/motion/__init__.py`; extend `tests/unit/test_motion_language.py`.

- [ ] **Step 1: Add failing tests.** For `Sequence(FadeIn(duration=.4), Move(duration=.7, from_y=80, to_y=0), start=1)`, assert expanded starts `1.0` and `1.4`. For `Parallel(FadeIn(start=.2), Move(start=.1,...), start=1)`, assert starts `1.2` and `1.1`. Assert nested timing and that a failed stagger leaves all tracks unchanged.
- [ ] **Step 2: Run the targeted tests.** Expected: imports or assertions fail.
- [ ] **Step 3: Implement flattening.** `expand(node, offset=0)` returns `(tuple[Animation, ...], absolute_end)`. A leaf is copied with `dataclasses.replace(node, start=offset+node.start)`. Parallel expands all children from its `offset+start`; Sequence moves a cursor to each child end. Empty composites fail at construction.
- [ ] **Step 4: Make attachment atomic.** Validate all expanded leaves and conflicts against copies of affected tracks, then commit every new track together. Implement `scene.stagger(elements, animation, start=0, step=.1)` by expanding one copied animation per ordered target and applying one validation transaction.
- [ ] **Step 5: Run `uv run pytest -q`.** Expected: composition and old tests pass. Commit composition.

## Task 3: Polyline paths and reveals

**Files:** Modify `src/motion/primitives.py`, `src/motion/animation.py`, `src/motion/scene.py`, `src/motion/renderer.py`; create `tests/unit/test_path.py`.

- [ ] **Step 1: Add failing tests.** A path with lengths 30 and 70 has its drawn endpoint at `(30, 20)` when `draw_progress=.5`, starting from `(0, 0)` through `(30, 0)` to `(30, 70)`. Assert full and empty progress, zero-length segment handling, invalid all-zero length, Rectangle/Circle mask validation, and local Reveal clip bounds.
- [ ] **Step 2: Run `uv run pytest tests/unit/test_path.py -q`.** Expected: missing Path/DrawPath.
- [ ] **Step 3: Add `Path` and partial geometry.** Store immutable points and a closed flag. `partial_points(points, progress)` walks Euclidean segment lengths and interpolates the endpoint in the current segment. `DrawPath` controls `draw_progress`; an unanimated path uses one. Fill on a closed path appears only at complete progress.
- [ ] **Step 4: Add clip reveals.** `Reveal(direction=...)` animates `reveal_progress` and clips to a growing rectangle in local bounds. `MaskReveal(mask=Rectangle(...) | Circle(...))` uses a growing world-coordinate vector clip before the target local transform. Validate mask type and conflicting reveal tracks at attachment.
- [ ] **Step 5: Run tests and render tiny stills for zero, half, and full progress.** Inspect stroke continuation and clip direction. Commit path and reveal code.

## Task 4: Camera tracks and layer behavior

**Files:** Create `src/motion/camera.py`, `tests/unit/test_camera.py`; modify `src/motion/scene.py`, `src/motion/renderer.py`, `src/motion/__init__.py`.

- [ ] **Step 1: Add failing tests.** Assert camera center and zoom defaults, direct zoom at halfway through a track, rejection of overlapping zoom tracks and non-positive zoom, and a renderer test where a content dot moves under camera zoom while an overlay dot remains fixed.
- [ ] **Step 2: Run `uv run pytest tests/unit/test_camera.py -q`.** Expected: missing camera.
- [ ] **Step 3: Implement `Camera.animate`.** Accept `x`, `y`, `zoom`, and `rotation` endpoint pairs with start/duration/easing. Validate all supplied properties, then atomically add tracks. `Camera.evaluate(t)` returns a frozen state from those tracks without mutation.
- [ ] **Step 4: Apply camera only to world layers.** Around environment/content/foreground drawing, use `translate(canvas_center)`, `rotate(-camera.rotation)`, `scale(camera.zoom)`, and `translate(-camera.x, -camera.y)` in design coordinates. Background/overlay/captions use identity world camera. Preserve draw order across all layers.
- [ ] **Step 5: Run `uv run pytest -q`.** Expected: all tests pass and the original scene is unchanged. Commit camera.

## Task 5: Git graph visual proof

**Files:** Create `examples/blueprint/git_graph.py`; modify `README.md` and `src/motion/__init__.py`.

- [ ] **Step 1: Write a six-second portrait graph program.** Use a vertical polyline, three commit nodes, one branch path and node, grouped timing through Sequence/Parallel or stagger, and one camera zoom from 1 to at most 1.12. Keep annotation text in fixed overlay/captions where appropriate.
- [ ] **Step 2: Render 360 by 640 stills at 0, 1.5, 3, 4.5, and 6 seconds.** Inspect reading order, safe regions, path progression, and branch clarity; revise the program before preview.
- [ ] **Step 3: Render and inspect a 15 FPS preview.** Sample real encoded frames as a contact sheet to verify timing and absence of black cuts. Then render 1080 by 1920 at 30 FPS and probe codec, dimensions, frame rate, and duration.
- [ ] **Step 4: Recheck determinism and package health.** Run `uv run pytest -q`, render a repeated same-time still around an intervening time and compare SHA-256 hashes, then run `uv build` and inspect the wheel for assets.
- [ ] **Step 5: Document the public motion language and camera rules.** Add exact commands and a short source example to README; commit source, tests, documentation, and the tracked plan state. Keep generated media under ignored `.build/`.

## Exit review

- [ ] Old snapshot and new graph both render from editable Python scene files.
- [ ] Same-time stills match after out-of-order requests.
- [ ] Tests cover transform, composition, path, reveal, and camera rules.
- [ ] Preview and final graph exports have been visually inspected and format-probed.
- [ ] No new dependency or model-generated asset was introduced.
