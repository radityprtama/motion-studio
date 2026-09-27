from pathlib import Path

import pytest

from motion.memory import MemoryItem, MemoryStore


def test_memory_search_feedback_and_preservation(tmp_path: Path) -> None:
    source = tmp_path / "scene.py"
    source.write_text("scene = 'editable'\n")
    store = MemoryStore(tmp_path / "memory")
    first = MemoryItem("01-branch", "blueprint", "graph", ("branching", "history"), ("path-drawing",), quality=.92)
    second = MemoryItem("02-weak", "blueprint", "graph", ("branching",), quality=.31)
    third = MemoryItem("03-other", "cinematic", "crowd", ("scale",), quality=.99)
    for item in (first, second, third):
        store.save(item, source=source, intent="Explain the concept visually")
    assert [match.item.id for match in store.search(concepts=("branching",), style="blueprint")] == ["01-branch"]
    assert store.read_example("01-branch").source == source.read_text()
    with pytest.raises(FileExistsError):
        store.save(first, source=source, intent="duplicate")
    revised = store.add_feedback("02-weak", quality=.8, comment="Fixed safe area")
    assert revised.feedback == ("Fixed safe area",)
    assert [match.item.id for match in store.search(concepts=("branching",), style="blueprint")] == ["01-branch", "02-weak"]
    assert store.read_example("01-branch").source == source.read_text()
    store.add_feedback("03-other", quality=.2, comment="Too much glow")
    assert store.search(concepts=("scale",)) == ()
    assert [match.item.id for match in store.search(concepts=("scale",), min_quality=0)] == ["03-other"]


def test_memory_id_cannot_escape_root(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="slug"):
        MemoryItem("../outside", "blueprint", "graph")
    with pytest.raises(ValueError, match="invalid memory id"):
        MemoryStore(tmp_path).read_example("../outside")
