# Motion Studio agent entry point

For scene authoring, visual review, memory use, or agent automation, read [SKILL.md](SKILL.md) before changing a scene. It gives the working order and acceptance checks. Treat the rendered frame and preview as evidence; Python execution alone does not validate motion design.

Project contracts:

- Source scenes use `PortraitScene` and export `scene` or `build_scene(config)`. The latter receives explicit project defaults from `motion.toml`.
- Evaluate visuals from time and seed. Keep assets local and stable. Use named primitives and component parts so timing remains inspectable.
- Run `uv run pytest -q` after engine changes. Render representative stills and a preview after visual changes.
- Use `motion inspect` for cheap composition review and `motion still` for a specific timestamp. Render final resolution after preview review.
- Store reusable scenes through `MemoryStore` with intent, metadata, source, stills, and honest feedback. Quality below 0.5 stays out of default retrieval.
- When answering questions about a library, SDK, API, or CLI, resolve its Context7 library ID first and query its current documentation.

The [README](README.md) covers installation and public APIs. The working code and tests are authoritative if prose becomes stale.
