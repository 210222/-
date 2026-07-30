"""Regression locks for known prompt leakage and continuity failures."""

import pytest

from mode_p_vnext.director_vnext1.projection import ProjectionBindings, ProjectionCompiler
from mode_p_vnext.director_vnext1.validation import (
    ProjectionValidationError,
    assert_no_repeated_dialogue,
    assert_prompt_pure,
)
from mode_p_vnext.tests.test_ddo_3_vec import _phase_b
from mode_p_vnext.tests.test_ddo_5_projection import _bindings


@pytest.mark.parametrize(
    "leak",
    [
        "global 0s: hold the relation",
        "状态摘要 SHA256: abcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcd",
        "@图片4 is the previous video frame",
        "下一段连续续播",
        "不要出现手机",
        "戏剧反讽: the line returns",
    ],
)
def test_prompt_purity_rejects_historical_metadata_and_negative_noun_leaks(leak):
    with pytest.raises(ProjectionValidationError):
        assert_prompt_pure(leak)


def test_compiled_prompts_contain_local_timeline_without_global_or_internal_metadata():
    vec = _phase_b().visual_execution_contract
    compiler = ProjectionCompiler()
    storyboard = compiler.compile_storyboard(vec, _bindings())
    video = compiler.compile_video(vec, _bindings(), adapter_version="target-v1")
    assert "global" not in storyboard.prompt_text.lower()
    assert "global" not in video.prompt_text.lower()
    assert "VEC-S2" not in video.prompt_text
    assert "SH-1" not in video.prompt_text


def test_completed_segment_dialogue_cannot_be_repeated_in_a_new_video_contract():
    vec = _phase_b().visual_execution_contract
    with pytest.raises(ProjectionValidationError, match="repeats a completed"):
        assert_no_repeated_dialogue(vec, (("CHEN", "Come with me."),))
