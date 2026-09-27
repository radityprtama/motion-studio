import json

import pytest

from motion.harness import MotionHarness
from motion.planning import ScenePlan, Storyboard, StoryboardScene


def test_storyboard_and_plan_validation() -> None:
    scenes = (StoryboardScene("hook", 0, 2, "Git stores snapshots", "introduce", "folder becomes node"),)
    board = Storyboard("How Git stores history", "portrait", 2, "blueprint", scenes)
    assert Storyboard.from_dict(json.loads(json.dumps({"title": board.title, "format": board.format, "duration": board.duration, "style": board.style, "scenes": [vars(scenes[0])]}))) == board
    with pytest.raises(ValueError, match="exceeds duration"):
        Storyboard("Too short", "portrait", 1, "blueprint", scenes)
    with pytest.raises(ValueError, match="overlaps"):
        Storyboard("Overlap", "portrait", 5, "blueprint", scenes + (StoryboardScene("next", 1, 1, "", "compare", "two states"),))
    with pytest.raises(ValueError, match="scene narration"):
        StoryboardScene("bad", 0, 1, None, "introduce", "folder")
    plan = ScenePlan("hook", "snapshot", "blueprint", "folder to node", ("Folder",), ("DrawPath",))
    assert ScenePlan.from_dict(vars(plan)) == plan
    with pytest.raises(ValueError, match="lists"):
        ScenePlan("bad", "concept", "blueprint", "strategy", (42,), ())


def test_harness_preserves_intermediate_artifacts(tmp_path) -> None:
    asset_dir = tmp_path / "assets"
    asset_dir.mkdir()
    (asset_dir / "paper.png").write_bytes(b"sample")
    harness = MotionHarness(memory_root=tmp_path / "memory", assets_root=asset_dir)
    project = harness.create_project(tmp_path / "run", request={"prompt": "Explain Git history"})
    board = Storyboard("Git", "portrait", 2, "blueprint", (StoryboardScene("hook", 0, 2, "", "introduce", "folder"),))
    harness.save_storyboard(project, board)
    harness.save_scene_plan(project, ScenePlan("hook", "project", "blueprint", "folder", ("Folder",), ("FadeIn",)))
    inspection = harness.inspect_project(project)
    assert inspection.request == {"prompt": "Explain Git history"}
    assert inspection.storyboard == board
    assert [plan.scene_id for plan in inspection.plans] == ["hook"]
    assert "blueprint" in harness.list_styles()
    assert "Folder" in harness.list_components()
    assert asset_dir / "paper.png" in harness.list_assets()
    with pytest.raises(FileExistsError):
        harness.create_project(project, request={"prompt": "replace"})
