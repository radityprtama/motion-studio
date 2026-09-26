# Semantic Visual Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

This session executes inline under the user's existing build authorization; no delegated agents are requested.

**Goal:** Add measurable portrait layout, typography, and semantic primitives, then render an inspected 18-second Git history film in Blueprint style.

**Architecture:** Layout functions produce immutable design-coordinate boxes. Typography has one measured layout used by both bounds and drawing. Component factories return ordinary named elements plus bounds and anchors, so existing scene tracks and Cairo renderer remain the only animation/rendering mechanisms.

**Tech Stack:** Python 3.12, CairoCFFI, Pillow, bundled IBM Plex fonts, FFmpeg, pytest.

---

## File map

| Path | Responsibility |
| --- | --- |
| `src/motion/layout.py` | Pure Box, place, stack, and grid calculations |
| `src/motion/typography.py` | Font resolution, measured wrapping, line positions, visible bounds |
| `src/motion/style.py` | Blueprint navy/paper tokens and text roles |
| `src/motion/primitives.py` | Text role and explicit typography overrides |
| `src/motion/renderer.py` | Use shared typography and style background tokens |
| `src/motion/components.py` | Frozen bundles and Folder/File/Arrow/CommitNode/CommitGraph/Timeline factories |
| `src/motion/scene.py` | Expose content Box while preserving current content_box tuple API |
| `src/motion/__init__.py` | Public layout and component exports |
| `examples/blueprint/git_history.py` | 18-second reference program |
| `examples/blueprint/paper_process.py` | Short paper-style reuse proof |
| `tests/unit/test_layout.py` | Layout and safe area contracts |
| `tests/unit/test_typography.py` | Wrapping, alignment, override, rendered-bound contracts |
| `tests/unit/test_components.py` | Part handles, anchors, graph validation, style independence |
| `README.md` | Authoring, preview, still, and reference-film commands |

## Task 1: Pure portrait geometry

**Files:** Create `src/motion/layout.py`, `tests/unit/test_layout.py`; modify `src/motion/scene.py`, `src/motion/__init__.py`.

- [ ] **Step 1: Write failing tests.** Assert `Box(90,120,990,1700).center == (540,910)`, `inset(10)` returns `(100,130,980,1690)`, `place(...,100,50,"center") == (490,885)`, vertical stack with two 100px items and 20px gap centers inside the box, and an impossible grid raises `ValueError` naming the available box.
- [ ] **Step 2: Run `uv run pytest tests/unit/test_layout.py -q`.** Expected: import failure for `motion.layout`.
- [ ] **Step 3: Implement immutable geometry.** Define `Box(left,top,right,bottom)` with finite ordered edges, computed width/height/center, inset, and nine named anchor points. Implement `place(box,width,height,anchor,dx=0,dy=0) -> (left,top)`, `stack(box,sizes,gap,direction="vertical",align="center") -> tuple[Box,...]`, and `grid(box,rows,columns,gap_x=0,gap_y=0,padding=0) -> tuple[Box,...]`. Validate every requested size and reject overflow. Expose `PortraitScene.safe_box` as `Box(*content_box)`.
- [ ] **Step 4: Run `uv run pytest tests/unit/test_layout.py -q` and `uv run pytest -q`.** Expected: all pass; `content_box` stays a tuple for old consumers.
- [ ] **Step 5: Commit layout source, tests, and exports.**

## Task 2: Shared measured typography

**Files:** Create `src/motion/typography.py`, `tests/unit/test_typography.py`; modify `src/motion/primitives.py`, `src/motion/style.py`, `src/motion/renderer.py`; add bundled semibold font.

- [ ] **Step 1: Write failing tests.** Check all seven roles resolve, explicit size/weight/letter spacing override tokens, `measure_text` preserves newlines, wraps within `max_width`, positions left/center/right lines against the same x, and render bounds agree with the measured visible rectangle within one pixel at design resolution. Record the current snapshot hash at one timestamp before the change.
- [ ] **Step 2: Run `uv run pytest tests/unit/test_typography.py -q`.** Expected: missing roles and shared layout function.
- [ ] **Step 3: Resolve typography tokens.** Add regular/semibold font paths and role tokens in `Style`. Keep existing headline/body/annotation font sizes 84/50/36 and regular weight. Add `Text.font_size`, `font_weight`, `letter_spacing` optional overrides and the new roles; validate positive size/line height and finite spacing. Bundle IBM Plex Sans Semibold under the same OFL license; fail clearly if a requested font file is absent.
- [ ] **Step 4: Unify measure and draw.** Implement `layout_text(text,style) -> TextLayout` with Pillow `getlength`/`getbbox`, preserved newlines, measured word and character wrapping, line origins, and visible bounds. Use its line masks in `_draw_text` and its bounds in `_element_bounds`; render per glyph only when nonzero letter spacing. Preserve the old zero-spacing mask placement and role defaults.
- [ ] **Step 5: Run targeted and full tests, then render the baseline snapshot at the recorded timestamp.** Expected: same hash and all tests pass. Commit.

## Task 3: Style treatments and first component proof

**Files:** Modify `src/motion/style.py`, `src/motion/renderer.py`; create `src/motion/components.py`, `tests/unit/test_components.py`.

- [ ] **Step 1: Write failing tests.** `get_style("blueprint-paper")` returns warm background/dark ink; a `Folder` has `body`, `tab`, and `label` named parts, finite bounds, and a `tab_center` anchor. Rendering the same folder geometry in navy and paper produces different pixels with equal part positions.
- [ ] **Step 2: Run `uv run pytest tests/unit/test_components.py -q`.** Expected: missing style and component types.
- [ ] **Step 3: Implement style tokens.** Add `blueprint-paper`; configure grid color/opacity and component stroke tokens. Keep the existing navy grid and colors unchanged. Make `_paint_background` consume tokens.
- [ ] **Step 4: Implement `Component(parts,bounds,anchors).add_to(scene)`.** Use immutable mappings/order. Implement Folder with a stroked body, tab Path, and label Text; implement File with body, fold Path, and label. Part names derive from an explicit prefix or deterministic component ID argument, and `add_to` simply loops through parts calling `scene.add`.
- [ ] **Step 5: Render one folder at 360x640 in each style, inspect the images, run all tests, and commit.**

## Task 4: Diagram components

**Files:** Modify `src/motion/components.py`, `src/motion/__init__.py`; extend `tests/unit/test_components.py`.

- [ ] **Step 1: Write failing tests.** Arrow `entry`/`exit` match endpoints; CommitNode has `ring`, `core`, and `label`; CommitGraph rejects duplicate/missing IDs and unknown parents, and exposes one connector for each nonroot record; Timeline yields ordered anchors in both orientations.
- [ ] **Step 2: Run `uv run pytest tests/unit/test_components.py -q`.** Expected: missing factory names or contracts.
- [ ] **Step 3: Implement Arrow and CommitNode.** Both return named Path/Circle/Text parts, measured label fit, bounds, and anchors. Arrow accepts start/end points; CommitNode accepts x/y/label/radius and style.
- [ ] **Step 4: Implement CommitGraph and Timeline.** Graph accepts ordered `(id,label,parent_id)` records with caller positions; each connector is a Path between named node anchors and branches use accent color. Timeline accepts labels, orientation, gap, and origin; it returns individually addressable tick/label parts. Reject unbounded labels and nonpositive gaps.
- [ ] **Step 5: Run all tests, render a tiny graph in both styles, inspect, and commit.**

## Task 5: Reference film and visual revision

**Files:** Create `examples/blueprint/git_history.py`, `examples/blueprint/paper_process.py`; modify `README.md`.

- [ ] **Step 1: Implement and render beats 1–2.** Make a seed-42, 18s PortraitScene. Keep a fixed headline/step label; place Folder and three Files within `safe_box`. Render stills at 0, 2, 4, 6s at 360x640 and inspect spacing and readability.
- [ ] **Step 2: Implement beats 3–4.** Use explicit component handles with existing Fade/Move/Scale/DrawPath tracks; transform the visual focus from snapshot frame to first node, then draw ordered commits. Render 7.5, 9, 10.5, and 12s stills and revise collisions.
- [ ] **Step 3: Implement beats 5–6.** Draw one amber branch, reveal its node, make one camera settle, hold the final diagram with caption. Render 13.5, 15, 16.5, 18s stills. Keep the final caption above the bottom exclusion zone.
- [ ] **Step 4: Add a short paper example using Folder/File/Arrow or Timeline.** Render one matching semantic arrangement in both styles and inspect whether hierarchy survives.
- [ ] **Step 5: Render preview and contact sheet under `.build/git_history/`.** Run `uv run motion preview examples/blueprint/git_history.py --output .build/git_history/preview.mp4 --overwrite`; render representative stills with `motion still`; build a Pillow contact sheet from those stills. Inspect frames sampled from the encoded preview; revise timing and layout until each beat is legible and transitions remain continuous.
- [ ] **Step 6: Render final MP4.** Run `uv run motion render examples/blueprint/git_history.py --resolution 1080x1920 --fps 30 --output .build/git_history/final.mp4 --overwrite`; probe with `ffprobe` for H.264, 1080x1920, 30fps, and 18s; decode with ffmpeg to null. Render the same arbitrary timestamp twice around an intervening timestamp and compare SHA-256 hashes.
- [ ] **Step 7: Run `uv run pytest -q` and `uv build`.** Confirm wheel includes fonts, update README with public component and film commands, and commit the scene/docs/plan state.

## Exit review

- [ ] Layout and typography are measured in design coordinates and do not depend on prior frames.
- [ ] Both Blueprint treatments render the same semantic components.
- [ ] Named component parts can be animated with ordinary scene tracks.
- [ ] Preview, stills, contact sheet, and final video have been inspected.
- [ ] Existing examples remain visually stable and all tests pass.
