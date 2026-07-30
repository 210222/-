"""DDO-5: VEC is projected twice without a second creative interpretation."""

from __future__ import annotations

from dataclasses import replace
from time import perf_counter

import pytest

from mode_p_vnext.director_vnext1.cache import ContentAddressedCache
from mode_p_vnext.director_vnext1.projection import (
    ProjectionBindings,
    ProjectionCompiler,
    ReferenceBinding,
    StoryboardProjection,
    VoiceBinding,
)
from mode_p_vnext.director_vnext1.validation import (
    ProjectionDependencyIndex,
    ProjectionValidationError,
    assert_projection_homology,
)
from mode_p_vnext.tests.test_ddo_3_vec import _phase_b


def _bindings() -> ProjectionBindings:
    return ProjectionBindings(
        references=(
            ReferenceBinding("R-chen-id", "asset-chen-id", "character_identity", "character", "CHEN", 100),
            ReferenceBinding("R-chen-clothes", "asset-chen-clothes", "wardrobe", "character", "CHEN", 100),
            ReferenceBinding("R-zhou-id", "asset-zhou-id", "character_identity", "character", "ZHOU", 100),
            ReferenceBinding("R-zhou-clothes", "asset-zhou-clothes", "wardrobe", "character", "ZHOU", 100),
            ReferenceBinding("R-phone", "asset-phone", "prop_geometry", "prop", "phone", 80),
            ReferenceBinding("R-scene", "asset-hospital", "scene_layout", "scene", "S2", 70),
        ),
        voices=(VoiceBinding("DIALOGUE-1", "CHEN", "voice-chen"),),
    )


def test_storyboard_and_video_have_exact_field_homology_and_bound_voice_references():
    vec = _phase_b().visual_execution_contract
    compiler = ProjectionCompiler()
    storyboard = compiler.compile_storyboard(vec, _bindings())
    video = compiler.compile_video(vec, _bindings(), adapter_version="target-v1")
    assert_projection_homology(vec, storyboard, video)
    assert storyboard.manifest.contract_fingerprint == video.manifest.contract_fingerprint == vec.fingerprint
    assert storyboard.manifest.reference_binding_fingerprint == video.manifest.reference_binding_fingerprint
    assert storyboard.manifest.audio_binding_fingerprint == video.manifest.audio_binding_fingerprint
    changed_order = replace(storyboard.shot_nodes[0], screen_order=("ZHOU-left", "CHEN-right"))
    with pytest.raises(ProjectionValidationError, match="homologous"):
        assert_projection_homology(vec, replace(storyboard, shot_nodes=(changed_order,)), video)
    incomplete = replace(_bindings(), references=_bindings().references[1:])
    with pytest.raises(ValueError, match="VEC reference requirement"):
        compiler.compile_storyboard(vec, incomplete)


def test_local_invalidation_and_adapter_only_change_do_not_replan_or_rebuild_storyboard():
    vec = _phase_b().visual_execution_contract
    cache = ContentAddressedCache()
    compiler = ProjectionCompiler(cache)
    first_storyboard = compiler.compile_storyboard(vec, _bindings())
    first_video = compiler.compile_video(vec, _bindings(), adapter_version="target-v1")
    second_storyboard = compiler.compile_storyboard(vec, _bindings())
    second_video = compiler.compile_video(vec, _bindings(), adapter_version="target-v2")
    assert second_storyboard is first_storyboard
    assert second_video is not first_video
    index = ProjectionDependencyIndex.from_vec(vec, adapter_version="target-v1")
    beat_change = index.invalidate(("beat:BEAT-1",))
    assert {"storyboard:SH-1", "video:SH-1"}.issubset(set(beat_change.invalidated_node_ids))
    assert "adapter-payload:target-v1" not in beat_change.invalidated_node_ids
    adapter_change = index.invalidate(("adapter:target-v1",))
    assert adapter_change.invalidated_node_ids == ("adapter-payload:target-v1", "adapter:target-v1")
    assert cache.stats["hits"] >= 1


def test_hot_projection_cache_meets_local_performance_budget():
    vec = _phase_b().visual_execution_contract
    compiler = ProjectionCompiler()
    start = perf_counter()
    for _ in range(100):
        compiler.compile_storyboard(vec, _bindings())
        compiler.compile_video(vec, _bindings(), adapter_version="target-v1")
    assert perf_counter() - start < 5.0
    assert compiler.cache.stats["hits"] >= 198
