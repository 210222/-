"""DDO-6 creates evidence/approval machinery without external submission."""

from __future__ import annotations

from dataclasses import replace

import pytest

from mode_p_vnext.director_vnext1.holdout import FrozenHoldoutSet, HoldoutCase
from mode_p_vnext.director_vnext1.render_evidence import (
    OwnerApprovalGate,
    RenderRunRecord,
    ShadowExecutionPlan,
    build_ffmpeg_frame_plan,
)
from mode_p_vnext.tests.test_ddo_3_vec import _phase_b


HASH = "d" * 64


def test_holdout_is_frozen_and_disjoint_from_golden_cases():
    holdout = FrozenHoldoutSet(
        "HOLDOUT-v1", ("GOLDEN-A",),
        (HoldoutCase("HOLDOUT-A", HASH, ("departure", "prop")),),
    )
    assert holdout.assert_case_is_held_out("HOLDOUT-A").script_sha256 == HASH
    assert len(holdout.fingerprint) == 64
    with pytest.raises(ValueError, match="disjoint"):
        FrozenHoldoutSet("bad", ("HOLDOUT-A",), (HoldoutCase("HOLDOUT-A", HASH, ("x",)),))


def test_render_record_and_ffmpeg_frame_plan_require_observable_media_evidence():
    vec = _phase_b().visual_execution_contract
    planned = RenderRunRecord("RR-video", "video", vec.fingerprint, "target-video", "PLANNED")
    assert planned.status == "PLANNED"
    with pytest.raises(ValueError, match="media path"):
        RenderRunRecord("RR-bad", "video", vec.fingerprint, "target-video", "RENDERED")
    plan = build_ffmpeg_frame_plan(vec, input_video_paths={"SEG-1": "D:/renders/segment.mp4"}, output_directory="D:/frames")
    kinds = {item.kind for item in plan.targets}
    assert {"opening", "panel", "ending"}.issubset(kinds)
    command = plan.commands("D:/video-tools/ffmpeg.exe")[0]
    assert command[0].endswith("ffmpeg.exe") and "-frames:v" in command and "D:/renders/segment.mp4" in command


def test_owner_approval_is_required_and_ddo6_cannot_switch_production():
    vec = _phase_b().visual_execution_contract
    shadow = ShadowExecutionPlan("SHADOW-1", vec.fingerprint, "holdout-fingerprint", "D:/shadow")
    assert shadow.external_submission_allowed is False and shadow.production_switch_allowed is False
    planned_story = RenderRunRecord("RR-story", "storyboard", vec.fingerprint, "target-story", "PLANNED")
    planned_video = RenderRunRecord("RR-video", "video", vec.fingerprint, "target-video", "PLANNED")
    pending = OwnerApprovalGate("APP-1", vec.fingerprint, planned_story, planned_video)
    assert pending.owner_approval_recorded is False and pending.production_switch_authorized is False
    with pytest.raises(ValueError, match="requires accepted"):
        OwnerApprovalGate("APP-2", vec.fingerprint, planned_story, planned_video, owner_approval_recorded=True)
    accepted_story = RenderRunRecord("RR-story-ok", "storyboard", vec.fingerprint, "target-story", "VISUALLY_ACCEPTED", "D:/renders/story.png", HASH, "owner", "all hard invariants reviewed")
    accepted_video = RenderRunRecord("RR-video-ok", "video", vec.fingerprint, "target-video", "VISUALLY_ACCEPTED", "D:/renders/video.mp4", HASH, "owner", "all hard invariants reviewed")
    approved = OwnerApprovalGate("APP-3", vec.fingerprint, accepted_story, accepted_video, owner_approval_recorded=True)
    assert approved.production_switch_authorized is False
    with pytest.raises(ValueError, match="cannot authorize"):
        replace(approved, production_switch_authorized=True)
