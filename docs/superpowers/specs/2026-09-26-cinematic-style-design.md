# Motion Studio: Cinematic style and procedural atmosphere

Date: 2026-09-26
Status: approved design, pending written-spec review

## Purpose and scope

Add a restrained Cinematic Dark style to the existing deterministic portrait renderer. The milestone introduces a radial-light primitive, a directly evaluated particle emitter, procedural Orb/Person/Crowd components, and subtle seeded grain and vignette. Two editable examples prove the style: an atmospheric title with one orb and a crowd statistic with a clear highlighted minority. No photographs, generated images, generated video, model calls, or mutable simulation are involved.

This milestone does not attempt a general effect graph, full blur/shadow API, 3D, or implicit parallax. The existing camera and layers supply depth through composition and separately authored motion tracks. General Blur, Shadow, and Noise effect objects remain a later milestone, informed by inspected scenes rather than speculative APIs.

## Style and rendering boundary

`PortraitScene(style="cinematic")` selects a token pack: near-black navy `#08121E`, warm off-white `#E8E4DC`, steel blue `#829EAD`, and a restrained amber `#D4A373`. It retains the same IBM Plex fonts and text-role API as Blueprint. The background replaces the Blueprint grid with a low-contrast Cairo radial lighting field and a nearly invisible horizon gradient; it must leave space for the primary visual and legible captions. No color token should suggest saturated cyan/magenta cyberpunk UI.

`Style` gains an explicit background treatment identifier and optional finishing parameters. The renderer dispatches background painting by treatment, so Blueprint pixels remain unchanged. The Cinematic frame is drawn normally in Cairo and converted to Pillow RGBA once, as it is today. A small `motion.effects` module then applies a seeded grain texture and vignette only for Cinematic frames. Finishing uses the scene seed, output dimensions, and the requested timestamp where motion is intentional. The default grain is a static seeded texture, preventing flicker. Both effects are opt-in style tokens with conservative intensities. No operation uses process-global random state or platform-salted `hash()`.

The grain texture is generated at reduced resolution with `random.Random(scene.seed)` and scaled to the output, then blended at low opacity. The vignette is a deterministic grayscale radial mask, also generated at reduced resolution and scaled. These resources may be cached by immutable keys `(seed,width,height,parameters)`, but cache state cannot alter pixels. Compositing keeps alpha opaque for final frames. A direct render at any `t` must match the same render after unrelated timestamps.

## New primitive and particle model

`RadialLight` is an immutable `Element` with center, positive radius, center color, edge color/alpha, layer, opacity, and the usual transforms. Cairo `RadialGradient` paints concentric color stops inside a circular bound. An untransformed light is a soft halo, and Scale/Fade/Move can animate it like any element. The gradient never samples random values.

`ParticleEmitter` is an immutable `Element` with a finite local `width`/`height`, `count`, explicit integer `seed`, positive `(min,max)` radius range, color, `(min_vx,max_vx,min_vy,max_vy)` velocity range in design pixels per second, and layer. It produces particle descriptors through `particles_at(t)` from `(seed, particle_index, t)`: seeded starting point and velocity, then modular wrap inside the emitter bounds. Frame N does not depend on frame N−1. `count` is capped at 400 for the CPU renderer; invalid bounds, negative time, or non-finite parameters fail with the emitter name and value. An emitter's scene position, opacity, scale, camera behavior, and z-order follow ordinary Element rules. The default alpha and count should remain atmospheric at 360×640 rather than drawing attention away from a title or statistic.

Render `RadialLight` and `ParticleEmitter` within the existing ordered element loop. Particle positions are in local coordinates so camera and element transforms apply naturally. Drawing may use subpixel circles and a small deterministic size/opacity spread. The same seed and timestamp must produce the same descriptors and frame bytes.

## Components and repetition

`Orb(...)` returns a `Component` with named `halo`, `disc`, `rim`, and `highlight` primitives and a center anchor. Its visual hierarchy is a dim radial halo, a dark solid disc, one restrained edge stroke, and a small reflected light. Callers choose position, diameter, colors through style, and part names; no topic-specific asset is embedded.

`Person(...)` returns named `head` and `body` primitives. It is a simple readable silhouette, not a detailed character illustration. The body is a closed filled Path or equivalent vector shape, and the head is a Circle. Explicit `height`, `pose_variant` from a small fixed set, opacity, and style control variation. To support fill-only silhouettes, a closed Path with `fill` and `stroke=None` must not acquire an implicit outline; existing unfilled paths keep their current default stroke behavior.

`Crowd(...)` produces a stable row-major grid of Person parts inside a caller-supplied Box. It takes `count`, `columns`, `seed`, `highlighted` indices, and style. Positions are derived from Box geometry; seeded scale and small offsets provide controlled imperfection without losing the grid. Highlighted people use the accent color while others use subdued steel-blue. The returned Component exposes `person:<index>:head/body` part names and each person's center anchor, so a scene may animate selected figures separately. Reject highlighted indices outside `[0,count)`, counts above 400, or a Box too small for the requested figures. Avoid a layout engine beyond the existing pure Box/grid functions.

## Visual proof

1. `examples/cinematic/atmospheric_title.py` is an 8-second portrait scene: a single orb establishes the visual world, a short title and caption appear with measured typography, a sparse particle field drifts slowly, and the camera makes one modest push. Use broad negative space. Render direct-time stills at 0, 2, 4, 6, and 8 seconds, then inspect a 360×640 at 15 FPS encoded preview.
2. `examples/cinematic/crowd_statistic.py` is a 7-second portrait scene: a 10×10 grid appears in rows, exactly 17 people become amber, and one large `17 / 100` statement resolves beside or above the grid. The highlighted set must be legible without relying only on color; a short label states the count. The composition must keep the lower caption within the portrait safe area. Inspect key stills and an encoded preview.

Both examples use the real scene API and style tokens. The second example is the semantic reuse test: the crowd primitive conveys a quantity without locking it to a particular topic. Motion is limited to introduction, emphasis, and camera direction. There is no decorative bouncing, excessive glow, or constant particle motion.

## Errors, tests, and performance

New errors identify the primitive or component, invalid parameter, and timestamp when evaluation fails. Renderer errors continue wrapping the element name and time. Particle creation validates its explicit seed and finite bounds at construction; `particles_at(t)` rejects invalid time. A failed Crowd construction must not partially add elements to a scene because construction happens before `add_to`.

Unit tests cover style tokens, fill-only Path behavior, radial-light validation, particle determinism and arbitrary-time evaluation, particle bounds, emitter layering, Crowd highlights and stable ordering, and style-specific finishing. A render test compares same-time frames after an intervening timestamp. The original Blueprint snapshot hash (`a6a447d59d569b5f0622a02b7990aa4e3558c82766abf0413cdcf622eeb78cb9` at 360×640 and 2.0s in this environment) stays unchanged. Do not use cross-platform font or effect hashes as golden fixtures.

Keep preview rendering efficient: radial gradients use Cairo directly; grain/vignette are reduced-resolution Pillow masks; particle positions are analytical. Measure the examples before optimizing further. Render one final-resolution example only after its preview passes visual inspection. Probe its format and decode it with FFmpeg. Generated media belongs under ignored `.build/`; source and tests are committed.

## Completion criteria

The Cinematic pack is usable when both examples read clearly at phone preview size, direct-time stills are repeatable, particles are seeded and bounded, finishing is subtle, Blueprint renders remain stable, tests pass, and at least one full-resolution Cinematic MP4 renders and decodes successfully.

## Library references

- [CairoCFFI radial gradient and context API](https://doc.courtbouillon.org/cairocffi/stable/api.html)
- [Pillow compositing and filters](https://pillow.readthedocs.io/en/stable/reference/Image.html)
