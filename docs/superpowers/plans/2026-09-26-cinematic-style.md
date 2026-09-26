# Cinematic Style Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

This session executes inline under the user's build authorization. No delegated agents were requested.

**Goal:** Produce a deterministic Cinematic portrait style with procedural light, particles, a repeatable crowd, and inspected examples.

**Architecture:** Style tokens select a Cairo background and conservative Pillow finishing. New visual definitions stay immutable and evaluate from time; Orb/Person/Crowd factories expose named ordinary parts. Blueprint rendering remains on its existing path.

**Tech Stack:** Python 3.12, CairoCFFI RadialGradient, Pillow RGBA compositing, FFmpeg, pytest. No new dependency.

---

## File map

| Path | Responsibility |
| --- | --- |
| `src/motion/style.py` | Cinematic tokens and explicit background/finishing parameters |
| `src/motion/primitives.py` | RadialLight and ParticleEmitter direct-time definitions |
| `src/motion/renderer.py` | Cairo gradient/light/particle painting and style dispatch |
| `src/motion/effects.py` | Seeded grain and vignette over a finished Pillow frame |
| `src/motion/components.py` | Orb, Person, and Crowd factories with named parts |
| `src/motion/__init__.py` | Public exports |
| `tests/unit/test_cinematic.py` | Determinism, validation, layering, style isolation |
| `tests/unit/test_crowd.py` | Person/Crowd parts, bounds, highlights, ordering |
| `examples/cinematic/atmospheric_title.py` | Orb and particle proof |
| `examples/cinematic/crowd_statistic.py` | 17/100 crowd proof |
| `README.md` | Authoring and render instructions |

## Task 1: Style and vector light

**Files:** Modify `src/motion/style.py`, `src/motion/primitives.py`, `src/motion/renderer.py`, `src/motion/__init__.py`; create `tests/unit/test_cinematic.py`.

- [x] Add a failing test: `get_style("cinematic").background == "#08121E"`, `RadialLight(x=0,y=0,radius=0,...)` raises, and a Cinematic still contains a soft gradient while the Blueprint baseline hash stays `a6a447d59d569b5f0622a02b7990aa4e3558c82766abf0413cdcf622eeb78cb9` at 360×640, t=2.
- [x] Run `uv run pytest tests/unit/test_cinematic.py -q`; expect missing style/primitive.
- [x] Add `Style.background_treatment` and finishing strengths with Blueprint defaults retaining the current grid. Add CINEMATIC tokens. Implement RadialLight with validated colors/radius and Cairo RadialGradient color stops, and a Cinematic radial/horizon background painter. Preserve the existing `_paint_background` Blueprint branch byte-for-byte.
- [x] Run targeted and full tests; render a 360×640 light still for inspection; commit.

## Task 2: ParticleEmitter without simulation state

**Files:** Modify `src/motion/primitives.py`, `src/motion/renderer.py`, `src/motion/__init__.py`; extend `tests/unit/test_cinematic.py`.

- [ ] Add failing tests for `ParticleEmitter(..., seed=42).particles_at(2.5)` equality after `particles_at(0.1)`, bounds/wrap at arbitrary time, count <=400, and rejected negative/non-finite time.
- [ ] Run `uv run pytest tests/unit/test_cinematic.py -q`; expect missing ParticleEmitter.
- [ ] Define immutable Particle descriptors. Generate each starting point/velocity/radius/alpha with local `Random(seed)` in stable index order; evaluate `((base + velocity*t) % extent)` in `particles_at`. Paint subpixel circles under normal element/camera transforms. Give the emitter an explicit integer seed and bounded count.
- [ ] Run targeted/full tests and compare repeated frame bytes across an intervening timestamp; commit.

## Task 3: Conservative frame finishing

**Files:** Create `src/motion/effects.py`; modify `src/motion/style.py`, `src/motion/renderer.py`; extend `tests/unit/test_cinematic.py`.

- [ ] Add failing tests: applying finishing twice to the same frame/seed gives equal bytes, changing seed changes grain, and Blueprint frames remain unchanged. Check output RGBA alpha stays 255.
- [ ] Run `uv run pytest tests/unit/test_cinematic.py -q`; expect missing effect functions.
- [ ] Generate a reduced-resolution static grain tile with `Random(seed)` and a radial vignette mask; upscale with Pillow and blend into RGB at style-defined low strengths. Cache immutable masks by seed/size/parameters only. Apply finishing after Cairo output conversion for Cinematic style.
- [ ] Render before/after 360×640 stills, inspect subtlety, run tests, and commit.

## Task 4: Orb and Crowd factories

**Files:** Modify `src/motion/primitives.py`, `src/motion/renderer.py`, `src/motion/components.py`, `src/motion/__init__.py`; create `tests/unit/test_crowd.py`.

- [ ] Add failing tests for Orb `halo/disc/rim/highlight` handles; Person `head/body` and fixed pose variants; Crowd 10×10 row-major anchors, 17 highlighted indices, deterministic offsets, invalid indices/overflow; filled Path with no stroke has no default outline.
- [ ] Run `uv run pytest tests/unit/test_crowd.py -q`; expect missing factories.
- [ ] Implement Orb from RadialLight/Circle parts. Implement Person from Circle and closed filled Path; when Path has fill and no stroke, draw only fill. Implement Crowd using `Box` and the pure grid helper, with local Random(seed) scale/offset variation bounded within cells. Return named parts and anchors for each person.
- [ ] Render Orb and 17/100 Crowd stills at 360×640, inspect spacing/contrast, run all tests, and commit.

## Task 5: Visual proof and final validation

**Files:** Create `examples/cinematic/atmospheric_title.py`, `examples/cinematic/crowd_statistic.py`; modify `README.md` and this plan.

- [ ] Build the 8-second atmospheric title with one Orb, sparse ParticleEmitter, short measured text, and one camera push. Render stills at 0/2/4/6/8 seconds; revise hierarchy before encoding.
- [ ] Build the 7-second 100-person crowd with 17 highlights, a large `17 / 100` statement and explicit count label. Stagger row reveals and use one restrained emphasis. Render key stills and revise visual density.
- [ ] Render both 360×640 at 15 FPS previews with `motion preview`; sample their encoded frames into contact sheets and inspect continuity and legibility. Render one 1080×1920 at 30 FPS final MP4 only after preview passes.
- [ ] Probe the final video for H.264/resolution/FPS/duration and decode it. Verify an out-of-order same-time frame hash; recheck the original Blueprint snapshot hash; run `uv run pytest -q` and `uv build`; inspect wheel assets.
- [ ] Document the style and public APIs in README; commit examples, tests, documentation, and checked plan state.

## Exit review

- [ ] Cinematic examples read clearly at phone preview size and avoid decorative neon effects.
- [ ] Particle and finishing output is seeded, bounded, and direct-time.
- [ ] Blueprint snapshot pixels remain unchanged.
- [ ] At least one full-resolution Cinematic video renders and decodes.
- [ ] Tests pass and the package builds.
