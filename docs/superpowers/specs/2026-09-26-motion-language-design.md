# Motion Studio: motion language and camera

Date: 2026-09-26
Status: approved design

## Purpose and boundary

This milestone extends the working portrait renderer with explicit transform tracks, path drawing, animation composition, directional and vector-mask reveals, and a 2D camera. The scene remains a flat ordered list of immutable visual definitions. Every frame still renders from the scene and one timestamp. Memory, audio, semantic components, layout engines, and the long Git film remain separate milestones.

The existing four-second snapshot scene and its hashes must continue to render. No new graphics dependency is needed. Cairo already provides paths, transforms, clips, and masks; Pillow remains the bundled-font source.

## Element transforms and timing

Every element gains base `scale_x=1`, `scale_y=1`, and `rotation=0` in degrees. Scale values must be finite and greater than zero; rotation must be finite. A renderer applies translation to the evaluated `(x, y)`, then rotation, then scale, and draws in local coordinates around the element anchor. Existing Rectangle and Circle positions keep their current appearance at default transform values. Text uses the same Cairo transform, so its Pillow mask follows element movement and rotation. An element's opacity applies after transform.

`Scale` names explicit `from_x/to_x` and/or `from_y/to_y` scale values. `Rotate` names explicit starting and ending angles in degrees. They use the same `start`, `duration`, and easing rules as Move. Add `ease_out_cubic`, `ease_in_out_cubic`, and `ease_out_back`, with exact endpoint values of zero and one. The back easing may overshoot between endpoints; scale evaluation must still be positive at every sampled point or produce an actionable error.

The scene rejects overlapping animations on the same element property. Different properties compose. A direct animation's `start` is an absolute scene time. All composite child starts are relative to their composite:

- `Sequence(start=S, children=(...))`: begin with `cursor=S`; for each child, place it at `cursor + child.start`, then set `cursor` to that child's absolute end. Nested composites use their computed duration. It expands to primitive tracks when attached to an element.
- `Parallel(start=S, children=(...))`: each child starts at `S + child.start`. Its duration is the latest child end.
- `scene.stagger(elements, animation, start=S, step=D)`: copy the animation for ordered element `i` at `S + i*D + animation.start`. The call is atomic: any invalid target or overlap leaves all elements unchanged.

Nested Sequence and Parallel structures are allowed and flattened at attachment time. A composite does not create frame-time mutation. The expanded tracks remain available for inspection by an agent or debugger.

## Paths and reveals

`Path(points=((x0, y0), ...), closed=False, stroke=..., stroke_width=...)` is a polyline in local coordinates relative to its element position. It requires at least two finite points and a positive stroke width. A two-point Path serves as a line. Closed paths may fill as well as stroke. Smooth curves are deferred until an inspected scene demonstrates a need; branching Git history is legible with straight segments.

`DrawPath(start, duration, easing)` applies only to Path and evaluates `draw_progress` from zero before start to one after end. Segment lengths are measured geometrically, and the renderer draws all complete segments plus the correct fraction of the current segment. A zero-length segment is ignored; a path with no positive total length is rejected. Equal time increments therefore reveal equal total path length, even across unequal segments. An unanimated Path draws completely. A filled closed Path shows its fill only when drawing reaches one, while its stroke reveals progressively.

`Reveal(direction, start, duration, easing)` applies a rectangular clip to an element's local bounds, growing from left, right, top, or bottom. `MaskReveal(mask, start, duration, easing)` accepts an immutable Rectangle or Circle definition in scene coordinates. Its filled clip grows from zero to the mask's full dimensions around the mask anchor. The mask is a definition used only for clipping, not an independently drawn scene element. Unsupported mask types fail at scene-definition time. Both reveal animations evaluate a `reveal_progress` track and cannot overlap each other on one target; they can combine with Move, Scale, Rotate, Fade, or DrawPath.

## Camera

Each PortraitScene owns a 2D camera. Its default focal position is the center of the design canvas, zoom is one, and rotation is zero degrees. The explicit API is `scene.camera.animate(zoom=(1.0, 1.12), start=0, duration=5, easing="ease_out_cubic")`; position and rotation accept analogous `x=(from,to)`, `y=(from,to)`, and `rotation=(from,to)` arguments. Each call may animate multiple camera properties. Camera tracks follow the same overlap and direct-evaluation rules as element tracks. Zoom must remain positive.

For environment, content, and foreground layers, the renderer translates the camera focal point to the portrait center, applies inverse camera rotation and multiplies world coordinates by zoom, then translates by the negative camera position. Increasing zoom therefore pushes in. Background, overlay, and captions remain fixed in canvas coordinates. The camera transform affects the mask coordinates for masked world elements as well as their drawings. Depth and parallax are future extensions; no element gets an implicit depth value in this milestone.

## Visual proof and verification

Create a short Blueprint Git graph scene that extends the first snapshot visual language. Commit nodes appear along a vertical line, a branch splits, and the camera makes one subtle push when the finished relationship is visible. Path drawing shows progression and causality; node timing follows the path. Motion has no bounce and no decorative rotation. The branch diagram occupies the portrait content area, leaving the lower caption safe region clear.

Render stills before, during, and after the split, then inspect a 360 by 640 preview. Revise timing and composition based on those images. Produce a full-resolution MP4 only when the preview reads clearly. Preserve the original snapshot scene as a regression example.

Unit tests cover easing endpoints and overshoot, composition expansion offsets, atomic stagger validation, path-length partial reveal, transform order, camera value evaluation, fixed versus camera-affected layers, mask bounds, invalid values, and stable ordering. Render tests compare same-timestamp pixels after intervening timestamps and compare the old snapshot example's output before and after the engine change in the same environment. Integration checks probe the new preview and final video formats without committing large video fixtures.

The milestone is complete when both example scenes render, arbitrary stills remain independent of frame order, the camera and path examples communicate the intended relationship in inspected output, and all tests pass.
