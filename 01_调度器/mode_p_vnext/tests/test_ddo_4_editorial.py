"""DDO-4 editorial modes are diagnostic-only and revisions stay bounded."""

from __future__ import annotations

from dataclasses import replace

import pytest

from mode_p_vnext.director_vnext1.editorial import (
    DIALOGUE_REDUNDANCY,
    MUTE_VISUAL_LOGIC,
    TEXT_REVIEW_FAILED,
    TEXT_VALIDATED,
    EditorialIssue,
    review_both_modes,
    review_vec_text,
)
from mode_p_vnext.director_vnext1.revision import (
    OutcomeAttribution,
    RevisionLimitReached,
    propose_revision,
)
from mode_p_vnext.tests.test_ddo_3_vec import _phase_b


def test_two_review_modes_are_text_only_and_never_claim_visual_realization():
    vec = _phase_b().visual_execution_contract
    bundle = review_both_modes(vec)
    assert bundle.mute_visual_logic.mode == MUTE_VISUAL_LOGIC
    assert bundle.dialogue_redundancy.mode == DIALOGUE_REDUNDANCY
    assert bundle.status == TEXT_VALIDATED
    assert {bundle.mute_visual_logic.status, bundle.dialogue_redundancy.status} == {TEXT_VALIDATED}


def test_dialogue_repetition_is_observed_not_solved_by_editorial_takeover():
    vec = _phase_b().visual_execution_contract
    duplicate = replace(vec.dialogue_events[0], event_id="DIALOGUE-2", start_tick=40, end_tick=60)
    second_shot = replace(vec.shots[0], shot_id="SH-2", segment_id="SEG-2", start_tick=0, end_tick=100, dialogue_event_ids=("DIALOGUE-2",))
    # Keep a separate local segment so the VEC remains structurally valid.
    second_segment = replace(vec.segments[0], segment_id="SEG-2", shot_ids=("SH-2",))
    duplicate = replace(duplicate, segment_id="SEG-2")
    changed = replace(vec, segments=(vec.segments[0], second_segment), shots=(vec.shots[0], second_shot), dialogue_events=(vec.dialogue_events[0], duplicate))
    review = review_vec_text(changed, DIALOGUE_REDUNDANCY)
    assert review.status == TEXT_REVIEW_FAILED
    issue = review.issues[0]
    assert issue.issue_code == "DIALOGUE_TEXT_REPEATED"
    assert "camera" not in issue.observation.lower()


def test_editorial_cannot_take_over_execution_and_revision_is_targeted_and_bounded():
    with pytest.raises(ValueError, match="cannot prescribe"):
        EditorialIssue("I-1", "BAD", "blocking", ("shot:SH-1",), "use a camera move", ("shot:SH-1",))
    vec = _phase_b().visual_execution_contract
    duplicate = replace(vec.dialogue_events[0], event_id="DIALOGUE-2", start_tick=40, end_tick=60)
    second_shot = replace(vec.shots[0], shot_id="SH-2", segment_id="SEG-2", dialogue_event_ids=("DIALOGUE-2",))
    second_segment = replace(vec.segments[0], segment_id="SEG-2", shot_ids=("SH-2",))
    duplicate = replace(duplicate, segment_id="SEG-2")
    review = review_vec_text(replace(vec, segments=(vec.segments[0], second_segment), shots=(vec.shots[0], second_shot), dialogue_events=(vec.dialogue_events[0], duplicate)), DIALOGUE_REDUNDANCY)
    attribution = OutcomeAttribution("ATTR-1", "VEC_field", ("dialogue:DIALOGUE-2",), "the second event duplicates approved dialogue text")
    request = propose_revision(review, (review.issues[0].issue_id,), attribution, frozen_node_ids=("segment:completed",), prior_automatic_attempts=1)
    assert request.attempt_number == 2
    assert request.affected_node_ids == ("dialogue:DIALOGUE-1", "dialogue:DIALOGUE-2")
    with pytest.raises(RevisionLimitReached):
        propose_revision(review, (review.issues[0].issue_id,), attribution, prior_automatic_attempts=2)
