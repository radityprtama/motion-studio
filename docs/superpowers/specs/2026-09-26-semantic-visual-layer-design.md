# Motion Studio: semantic visual layer and Git reference film

Date: 2026-09-26
Status: approved design, pending written-spec review

## Purpose and boundary

Extend the working direct-time renderer with portrait layout helpers, measurable typography, explicit semantic component factories, and a second Blueprint treatment. Prove them in an approximately 18-second editable Git history film. This milestone does not add memory, a model harness, audio, or a new renderer. The existing snapshot and graph examples remain valid and visually stable.

The visual language stays restrained: deep navy, pale technical lines, muted blue, warm amber, a purposeful grid, and generous empty space. The paper treatment uses the same semantic program and geometry with lighter color tokens. No generated images, video clips, or topic-specific raster assets are used.

## Data flow and public boundary

Scene code requests pure geometry from `motion.layout`, constructs named visual parts through factories in `motion.components`, adds those parts to a `PortraitScene`, and attaches the existing explicit animation tracks to individual parts. A component is a frozen description of its primitives, bounds, and connection anchors. It does not draw pixels, own time, or mutate the scene. The scene and renderer continue evaluating each requested timestamp directly.

Example shape of the API:

```python
folder = Folder(x=540, y=800, width=620, label="project", style="blueprint")
folder.add_to(scene)
scene.animate(folder.parts["body"], FadeIn(start=0.4, duration=0.5))
scene.animate(folder.parts["tab"], DrawPath(start=0.6, duration=0.5))
node = CommitNode(x=540, y=1040, label="snapshot 01", style="blueprint")
node.add_to(scene)
scene.animate(node.parts["ring"], FadeIn(start=5.0, duration=0.3))
```

Factories may offer typed attributes for common handles, but the `parts` mapping is the stable agent-facing surface. Every part has a predictable name derived from the component instance name or a caller-supplied prefix. Duplicate scene names still fail at `scene.add`. `add_to` returns the component for chaining and adds parts in declared order; it does not create implicit animation.

## Portrait layout

`PortraitScene.content_box` remains the canonical safe rectangle in design coordinates. `motion.layout` adds an immutable `Box(left, top, right, bottom)` with validated dimensions, center, width, height, `inset`, and anchor points. A `place(box, width, height, anchor, dx=0, dy=0)` function returns the top-left position of a known-size item against a box edge or center. Supported anchors are the nine combinations of left/center/right and top/center/bottom. Pure `stack` and `grid` functions calculate boxes from count, gap, padding, direction, and alignment. They never modify scene elements. The helpers reject negative space, impossible gaps, or items larger than the target content box with errors that identify the requested size and available bounds.

The film reserves the top region for a short headline and step label, the center for the evolving project/graph, and the bottom safe region for a one-line explanatory caption. The base design uses 1080×1920 coordinates; preview and final renders retain those design coordinates and only scale output pixels. Camera motion affects world layers while headlines and captions remain fixed overlay/caption elements.

## Typography

`Text` keeps its current constructor behavior by default. Add roles `display`, `title`, `caption`, and `label` alongside `headline`, `body`, and `annotation`. A style maps each role to font, size, weight, default line height, and color. A `Text` may override `font_size`, `font_weight`, `letter_spacing`, `line_height`, and `color`, with explicit values taking precedence over style tokens. Supported weights in this milestone are regular and semibold, backed by bundled IBM Plex font files. Unknown roles or unavailable weights fail when the text is created or resolved, with a useful message.

One shared text-layout function performs wrapping and measurement using the actual Pillow font metrics. It returns line positions and a tight visible bounds rectangle; the renderer uses that same result to place glyph masks and to compute reveal bounds. Explicit newlines are preserved, words wrap at `max_width`, and a single overlong word splits by measured characters. Letter spacing is applied to both measurement and drawing, including wrapped lines. `anchor` sets left, center, or right alignment of each line around `x`; `y` remains the top of the text block. Line height is a multiplier of font size. Existing `headline`, `body`, and `annotation` sizes, regular weight, and default placement remain the compatibility baseline; the snapshot example must keep identical same-time pixels in the installed environment.

## Styles and components

`get_style("blueprint")` keeps the existing navy treatment. `get_style("blueprint-paper")` selects warm paper, dark ink, muted blue rules, and amber emphasis. Style tokens cover background/grid, primary/secondary/accent colors, typography roles, and component stroke widths. Semantic content never checks a style name to decide what a Git folder or commit means. The renderer may choose background treatment from style tokens, but the same scene construction code runs with either style.

Initial factories are `Folder`, `File`, `Arrow`, `CommitNode`, `CommitGraph`, and `Timeline`. They are built only from existing Rectangle, Circle, Path, and Text primitives, plus any small geometry primitive proven necessary by the film. Each accepts dimensions and semantic labels appropriate to its role; no component hardcodes Git-specific story text. Each exposes `parts`, `bounds`, and named anchors such as `entry`, `exit`, `center`, or `tab_center` where applicable. Anchors are design-coordinate points suitable for connectors. Factories validate sizes, label fit, and anchor geometry. A `CommitGraph` takes ordered `(id, label, parent_id)` records and caller-supplied node positions; a record with a non-immediately-preceding parent becomes an explicit branch. It returns handles keyed by IDs for each node, label, and connector so a scene can schedule path drawing and node reveals separately. Missing or duplicate IDs and unknown parents fail at construction. `Timeline` lays out caller-supplied labels as an ordered horizontal or vertical sequence with an explicit gap. Avoid a general graph solver or nested renderer scene graph.

Two scene pattern helpers, `GraphPattern` and `ProcessPattern`, may combine these components and layout functions, but only if they remove repetition found while building the film and a second example. They return ordinary components and primitives. No pattern gets a custom render method. This is an explicit scope limit: the milestone ships useful factories first and promotes repeated composition to a pattern only when real scenes justify it.

## Reference film

Create `examples/blueprint/git_history.py` as one 18-second `PortraitScene`, seed 42, style `blueprint`, 1080×1920 at 30 FPS. The six connected beats are:

1. **0–3 s:** a project folder establishes the subject and occupies the central safe area.
2. **3–6 s:** three file marks appear inside it, showing project state.
3. **6–9 s:** the current state is framed as a snapshot and resolves into the first commit node.
4. **9–12 s:** successive nodes and connectors extend a legible vertical history.
5. **12–15 s:** one amber branch draws away from the main line, then its node appears.
6. **15–18 s:** a restrained camera settle reveals the whole diagram, with a concise final caption.

The film maintains a spatial relationship between folder, file state, and graph as the explanation progresses. Reused visual parts may fade or move to clear space, but there are no black interstitial frames. Path drawing communicates causal progression; camera movement is limited to the resolution beat unless inspection proves an earlier move necessary. The diagram must read at 360×640 preview size. The lower caption stays inside the safe content area above the bottom exclusion zone. The final frame holds long enough to understand the branch.

Create a second shorter example using the same factories in `blueprint-paper` to demonstrate that semantic content survives style changes. It need not repeat the full film.

## Errors and validation

Build a minimal executable proof before writing the full film: construct a component, render it in both style treatments, and confirm named part animation. Then grow the film beat by beat. A component error names the component, invalid dimension/label, and relevant bound. Text errors name the role or font resource. Rendering errors retain the existing scene, element, and timestamp context.

Unit tests cover Box/anchor/stack/grid calculations, safe-area fit, typography wrapping and measurement against rendered masks, role and weight resolution, component part names and anchors, connector geometry, stable layer order, and style independence. Small render tests verify out-of-order same-time frame hashes and preserve the existing snapshot baseline when defaults are unchanged. Avoid font hashes as cross-platform golden fixtures; compare within one environment.

Render key direct-time stills for all six beats, especially the folder-to-snapshot and branch transitions. Generate a contact sheet from those stills and inspect composition. Inspect an encoded 360×640 at 15 FPS preview for timing, readable labels, continuity, and no accidental blank intervals. Revise source until the result reads clearly, then render the complete 1080×1920 at 30 FPS H.264 MP4. Probe the output dimensions, frame rate, duration, and decode it. Store generated media under ignored `.build/` and keep the editable program in the repository.

## Completion criteria

The milestone is complete when layout helpers and text metrics are reliable, both Blueprint treatments work, the required factories expose animatable named parts, tests pass, and the inspected 18-second Git film renders as a playable deterministic portrait video. It is also complete only if the actual preview shows a coherent visual explanation, with the final diagram legible on a phone-sized canvas.
