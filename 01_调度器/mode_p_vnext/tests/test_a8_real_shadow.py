"""A8 raw-source-to-Projection text-shadow acceptance coverage.

The fake ports below stand in only for the two external native text calls.
Every canonical artifact, fact handle, ID, tick, VEC, Projection, Gate 0
result, persistent commit, and resumed-state check is produced by the real
runtime composition under ``mode_p_vnext.cli``.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping

import pytest

from mode_p_vnext import cli
from mode_p_vnext.domain.evidence import DPReviewVerdict
from mode_p_vnext.pipeline.verification_nodes import DPReviewDraft
from mode_p_vnext.ports.structured_text import (
    GenerationPolicy,
    ModelDraft,
    TextCallEvidence,
)
from mode_p_vnext.prompts.compiler import PromptCompiler
from mode_p_vnext.prompts.signatures import Stage, StageSignature


_SOURCE = (
    'Mira enters the archive. A brass key rests on the desk. '
    'Mira says, "Open the south door."'
)


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class _RecordingStructuredProvider:
    """A schema-conforming test port with no final-artifact surface."""

    provider_id = "a8-test-recording-structured-port"

    def __init__(self) -> None:
        self.calls: list[tuple[str, Mapping[str, Any]]] = []
        self.payloads: list[Mapping[str, Any]] = []

    @staticmethod
    def _i0_fact(
        source: str,
        *,
        statement: str,
        semantic_type: str,
        subject_id: str,
        spoken_text: str | None = None,
    ) -> dict[str, Any]:
        start = source.index(statement)
        value: dict[str, Any] = {
            "source_start": start,
            "source_end": start + len(statement),
            "semantic_type": semantic_type,
            "statement": statement,
            "subject_id": subject_id,
            "scene_hint": "scene-1",
        }
        if spoken_text is not None:
            value["spoken_text"] = spoken_text
        return value

    def _payload(self, stage: Stage, approved_input: Mapping[str, Any]) -> Mapping[str, Any]:
        if stage is Stage.I0:
            source = str(approved_input["normalized_source"])
            return {
                "facts": [
                    self._i0_fact(source, statement="Mira", semantic_type="character", subject_id="Mira"),
                    self._i0_fact(source, statement="archive", semantic_type="setting", subject_id="archive"),
                    self._i0_fact(source, statement="brass key", semantic_type="prop", subject_id="brass key"),
                    self._i0_fact(
                        source,
                        statement="Open the south door.",
                        semantic_type="dialogue",
                        subject_id="Mira",
                        spoken_text="Open the south door.",
                    ),
                ]
            }
        if stage is Stage.E0:
            return {
                "dramatic_promise": "Mira must choose whether the discovered key opens the south door.",
                "audience_contract": "The discovery is legible before the decision.",
                "tension_curve": ["arrival", "discovery", "choice"],
                "visual_principles": ["keep Mira and the key spatially legible"],
                "continuity_priorities": ["the brass key remains on the desk before Mira takes it"],
                "unresolved_questions": ["What is beyond the south door?"],
            }
        if stage is Stage.S1:
            return {
                "scene_purpose": "Turn Mira's entry into an informed choice about the south door.",
                "state_change": "Mira moves from searching to deciding.",
                "audience_information": ["The key is present and tied to the south door."],
                "character_knowledge": ["Mira sees the key before speaking."],
                "performance_questions": ["How does Mira hold back urgency?"],
                "director_problems": ["Keep the door decision connected to the visible key."],
                "continuity_effects": ["The key must remain identifiable across the handoff."],
                "unresolved_questions": ["Whether Mira opens the door is deferred."],
            }
        if stage is Stage.B0:
            return {
                "beats": [
                    {
                        "ordinal": 1,
                        "dramatic_action": "Mira notices the brass key and commits to the south-door question.",
                        "character_states": [{"character": "Mira", "posture": "alert"}],
                        "prop_states": [{"prop": "brass key", "location": "desk"}],
                        "gaze_relations": ["Mira looks from the key toward the south door."],
                        "action_paths": ["entry", "notice key", "speak decision"],
                        "continuity_effect": "The key stays visibly associated with the desk and door decision.",
                    }
                ]
            }
        if stage is Stage.B1:
            references = list(approved_input["reference_requirements"])
            dialogue = list(approved_input["dialogue"])
            character = next(item for item in references if item["semantic"] == "character")
            prop = next(item for item in references if item["semantic"] == "prop")
            spoken = dialogue[0]
            return {
                "curve_points": [
                    {
                        "dramatic_beat_ordinal": 1,
                        "intensity": 58,
                        "explanation": "The visible key focuses Mira's decision.",
                    }
                ],
                "decisions": [
                    {
                        "scope": "archive discovery framing",
                        "basis": "choice",
                        "locked_by": [],
                        "options": ["hold on Mira and key", "cut immediately to the key"],
                        "selected_index": 0,
                        "rationale": "The choice keeps character intention connected to the prop.",
                        "tradeoff": "The key receives less isolated screen emphasis.",
                    }
                ],
                "shots": [
                    {
                        "shot_ordinal": 1,
                        "blocking_beat_ordinal": 1,
                        "duration_intent": "brief",
                        "generation_mode": "text_only",
                        "composition": "Mira and the key share the desk-side frame.",
                        "camera": "A restrained forward settle follows Mira's notice.",
                        "lighting": "Archive light catches the brass key without hiding Mira.",
                        "performance": "Mira registers the discovery before speaking.",
                        "visual_beats": [
                            {
                                "visual_beat_ordinal": 1,
                                "phase": "action",
                                "subject_state": "Mira is alert beside the desk.",
                                "attention": "The brass key anchors the south-door decision.",
                                "storyboard_role": "required",
                            }
                        ],
                        "reference_binding_intents": [
                            {
                                "shot_ordinal": 1,
                                "visual_beat_ordinal": 1,
                                "fact_handle": character["fact_handle"],
                                "responsibility": "character_identity",
                            },
                            {
                                "shot_ordinal": 1,
                                "visual_beat_ordinal": 1,
                                "fact_handle": prop["fact_handle"],
                                "responsibility": "prop_identity",
                            },
                        ],
                        "dialogue_binding_intents": [
                            {
                                "shot_ordinal": 1,
                                "visual_beat_ordinal": 1,
                                "fact_handle": spoken["fact_handle"],
                                "placement_phase": "middle",
                            }
                        ],
                        "creative_notes": "No external media is started by this text-only shadow.",
                    }
                ],
                "transition_intents": [],
                "handoff_intent": "The Projection hands off a text-validated storyboard and video manifest only.",
            }
        raise AssertionError(f"unexpected structured stage {stage.value}")

    def generate(
        self,
        signature: StageSignature,
        approved_input: Mapping[str, Any],
        policy: GenerationPolicy,
    ) -> tuple[ModelDraft, TextCallEvidence]:
        payload = self._payload(signature.stage, approved_input)
        self.calls.append((signature.stage.value, dict(approved_input)))
        self.payloads.append(payload)
        compiled = PromptCompiler().compile(signature, approved_input)
        return (
            ModelDraft(signature.stage, signature.contract_name, payload),
            TextCallEvidence(
                provider=self.provider_id,
                requested_model=policy.requested_model,
                resolved_model="a8-test-model",
                stage=signature.stage,
                signature_version=signature.version,
                schema_digest=compiled.schema_digest,
                approved_input_digest=compiled.approved_input_digest,
                request_digest=_sha("request:" + signature.stage.value),
                response_digest=_sha("response:" + signature.stage.value),
                prompt_characters=1,
                schema_characters=1,
                response_characters=1,
                latency_ms=0,
                attempt=1,
                accepted=True,
                rejection_code=None,
            ),
        )


class _FreshDPReviewer:
    reviewer_id = "a8-test-fresh-dp"

    def __init__(self) -> None:
        self.calls: list[str] = []

    def review(self, packet: Any, context: Any) -> tuple[DPReviewDraft, Mapping[str, Any]]:
        self.calls.append(context.session_id)
        return (
            DPReviewDraft(DPReviewVerdict.APPROVED, (), ()),
            {
                "reviewer_id": self.reviewer_id,
                "fresh_session_id": context.session_id,
                "review_packet_digest": context.review_packet_digest,
                "prior_history_refs": [],
                "forbidden_input_refs": [],
                "request_digest": _sha("dp-request"),
                "response_digest": _sha("dp-response"),
                "latency_ms": 0,
                "claim_ceiling": "TEXT_VALIDATED",
            },
        )


class _MisboundAuditProvider(_RecordingStructuredProvider):
    """Simulates a port whose audit claims a different approved input."""

    def generate(
        self,
        signature: StageSignature,
        approved_input: Mapping[str, Any],
        policy: GenerationPolicy,
    ) -> tuple[ModelDraft, TextCallEvidence]:
        draft, evidence = super().generate(signature, approved_input, policy)
        return draft, replace(evidence, approved_input_digest=_sha("wrong-approved-input"))


def _invoke(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    *,
    provider: _RecordingStructuredProvider,
    reviewer: _FreshDPReviewer,
    run_id: str,
    stop_after: str | None = None,
    runs_root: Path | None = None,
) -> tuple[int, Mapping[str, Any], Path]:
    source = tmp_path / "unknown-original-script.txt"
    source.write_text(_SOURCE, encoding="utf-8")
    selected_runs_root = runs_root or (tmp_path / "a8-runs")
    monkeypatch.setattr(cli, "build_text_shadow_provider", lambda args: provider)
    monkeypatch.setattr(cli, "build_text_shadow_dp_reviewer", lambda args: reviewer)
    argv = [
        "text-shadow",
        "--source", str(source),
        "--runs-root", str(selected_runs_root),
        "--episode-id", "episode-1",
        "--scene-id", "scene-1",
        "--run-id", run_id,
    ]
    if stop_after is not None:
        argv.extend(("--stop-after", stop_after))
    code = cli.main(argv)
    captured = capsys.readouterr()
    stream = captured.out if code == 0 else captured.err
    assert stream, captured
    return code, json.loads(stream), selected_runs_root / run_id


def test_a8_real_cli_runs_unknown_source_through_local_projection_and_fresh_dp(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    provider = _RecordingStructuredProvider()
    reviewer = _FreshDPReviewer()

    code, response, run_dir = _invoke(
        monkeypatch, capsys, tmp_path, provider=provider, reviewer=reviewer, run_id="complete-run"
    )

    assert code == 0
    result = response["text_shadow"]
    assert result["status"] == "TEXT_VALIDATED"
    assert result["claim_ceiling"] == "TEXT_VALIDATED"
    assert result["accepted_nodes"] == list(cli._A8_NODE_ORDER)
    assert result["external_media_started"] is False
    assert result["v4_write"] is False
    assert result["production_switch_authorized"] is False
    assert [stage for stage, _ in provider.calls] == ["I0", "E0", "S1", "B0", "B1"]
    assert len(reviewer.calls) == 1

    run_record = json.loads((run_dir / "TEXT_SHADOW_RUN.json").read_text(encoding="utf-8"))
    assert run_record["claim_ceiling"] == "TEXT_VALIDATED"
    assert run_record["external_media_started"] is False
    assert run_record["v4_write"] is False
    assert run_record["source_digest"] == hashlib.sha256(_SOURCE.encode("utf-8")).hexdigest()
    result_record = json.loads((run_dir / "TEXT_SHADOW_RESULT.json").read_text(encoding="utf-8"))
    assert result_record["result"]["projection_ast_artifact_id"] == result["projection_ast_artifact_id"]

    registry_files = list((run_dir / "artifacts" / "fact_registry").glob("*.json"))
    assert len(registry_files) == 1
    registry = json.loads(registry_files[0].read_text(encoding="utf-8"))["payload"]
    assert all(fact["fact_handle"].startswith("fh:") for fact in registry["facts"])
    assert all(fact["fact_id"].startswith("id:") for fact in registry["facts"])
    assert all(fact["provenance"][0]["source_ref"]["digest"] == run_record["source_digest"] for fact in registry["facts"])

    vec_files = list((run_dir / "artifacts" / "visual_execution_contract").glob("*.json"))
    assert len(vec_files) == 1
    vec_payload = json.loads(vec_files[0].read_text(encoding="utf-8"))["payload"]
    vec_text = json.dumps(vec_payload, ensure_ascii=False)
    assert "source_start" not in vec_text
    assert "source_end" not in vec_text
    assert "start_tick" in vec_text
    assert "end_tick" in vec_text

    supplied = json.dumps(provider.payloads, ensure_ascii=False).casefold()
    assert "contract_id" not in supplied
    assert "start_tick" not in supplied
    assert "end_tick" not in supplied


def test_a8_resume_rehydrates_accepted_nodes_without_recalling_text_or_dp(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    provider = _RecordingStructuredProvider()
    reviewer = _FreshDPReviewer()

    first_code, first, run_dir = _invoke(
        monkeypatch,
        capsys,
        tmp_path,
        provider=provider,
        reviewer=reviewer,
        run_id="resume-run",
        stop_after="S1",
    )
    assert first_code == 0
    assert first["text_shadow"]["status"] == "PAUSED"
    assert first["text_shadow"]["accepted_nodes"] == ["I0", "E0", "S1"]
    assert [stage for stage, _ in provider.calls] == ["I0", "E0", "S1"]
    assert reviewer.calls == []

    second_code, second, _ = _invoke(
        monkeypatch, capsys, tmp_path, provider=provider, reviewer=reviewer, run_id="resume-run"
    )
    assert second_code == 0
    assert second["text_shadow"]["status"] == "TEXT_VALIDATED"
    assert second["text_shadow"]["reused_existing_run"] is True
    assert [stage for stage, _ in provider.calls] == ["I0", "E0", "S1", "B0", "B1"]
    assert len(reviewer.calls) == 1
    assert (run_dir / "RUN.json").is_file()

    third_code, third, _ = _invoke(
        monkeypatch, capsys, tmp_path, provider=provider, reviewer=reviewer, run_id="resume-run"
    )
    assert third_code == 0
    assert third["text_shadow"]["status"] == "TEXT_VALIDATED"
    assert third["text_shadow"]["runtime_state_sha256"] == second["text_shadow"]["runtime_state_sha256"]
    assert third["text_shadow"]["result_record_sha256"] == second["text_shadow"]["result_record_sha256"]
    assert [stage for stage, _ in provider.calls] == ["I0", "E0", "S1", "B0", "B1"]
    assert len(reviewer.calls) == 1


def test_a8_rejects_tampered_hash_bound_runtime_run_record(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    provider = _RecordingStructuredProvider()
    reviewer = _FreshDPReviewer()
    first_code, _, run_dir = _invoke(
        monkeypatch,
        capsys,
        tmp_path,
        provider=provider,
        reviewer=reviewer,
        run_id="tamper-run",
        stop_after="I0",
    )
    assert first_code == 0
    (run_dir / "RUN.json").write_text('{"tampered":true}', encoding="utf-8")

    second_code, second, _ = _invoke(
        monkeypatch, capsys, tmp_path, provider=provider, reviewer=reviewer, run_id="tamper-run"
    )
    assert second_code == 2
    assert second["status"] == "ERROR"
    assert second["error_type"] in {"TextShadowStorageError", "A8TextShadowError"}
    assert len(provider.calls) == 1
    assert reviewer.calls == []


def test_a8_refuses_a_v4_storage_root_before_any_shadow_write(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    provider = _RecordingStructuredProvider()
    reviewer = _FreshDPReviewer()
    v4_root = Path(cli.__file__).resolve().parents[1] / "mode_p" / f"a8-forbidden-{tmp_path.name}"

    code, response, _ = _invoke(
        monkeypatch,
        capsys,
        tmp_path,
        provider=provider,
        reviewer=reviewer,
        run_id="forbidden-v4-root",
        runs_root=v4_root,
    )

    assert code == 2
    assert response["status"] == "ERROR"
    assert response["error_type"] == "TextShadowStorageError"
    assert provider.calls == []
    assert reviewer.calls == []
    assert not v4_root.exists()


def test_a8_rejects_a_text_call_audit_not_bound_to_its_preflighted_input(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    provider = _MisboundAuditProvider()
    reviewer = _FreshDPReviewer()

    code, response, run_dir = _invoke(
        monkeypatch,
        capsys,
        tmp_path,
        provider=provider,
        reviewer=reviewer,
        run_id="misbound-audit",
    )

    assert code == 2
    assert response["status"] == "ERROR"
    assert response["error_type"] == "A8TextShadowError"
    assert [stage for stage, _ in provider.calls] == ["I0"]
    assert reviewer.calls == []
    assert not (run_dir / "stage_records" / "I0.json").exists()


def test_a8_single_real_cli_entry_delegates_to_cli_main() -> None:
    """``python -m mode_p_vnext`` is the one real CLI entry into cli.main.

    The __main__ module is a pure delegation shim, the parser identifies
    itself as that module invocation, and the module entry actually runs.
    """

    main_py = Path(cli.__file__).with_name("__main__.py")
    source = main_py.read_text(encoding="utf-8")
    assert "from .cli import main" in source
    assert 'raise SystemExit(main())' in source
    assert 'if __name__ == "__main__":' in source

    parser = cli.build_parser()
    assert parser.prog == "python -m mode_p_vnext"
    assert callable(cli.main)

    package_parent = Path(cli.__file__).resolve().parents[1]
    run = subprocess.run(
        [sys.executable, "-m", "mode_p_vnext", "--help"],
        cwd=str(package_parent),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert run.returncode == 0, run.stderr
    assert "--help" in run.stdout
    assert "text-shadow" in run.stdout


def test_a8_fact_provenance_carries_typed_source_spans_into_the_registry_only(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    """I0 provenance is typed: exact source spans in the fact registry only.

    Every fact's single source span must slice the normalized source back to
    exactly the canonical statement at the exact character offsets, and the
    span must carry the typed episode/scene partition identity.  Once facts
    leave the registry and enter the VEC, only ticks remain.
    """

    provider = _RecordingStructuredProvider()
    reviewer = _FreshDPReviewer()

    code, _, run_dir = _invoke(
        monkeypatch, capsys, tmp_path, provider=provider, reviewer=reviewer, run_id="span-run"
    )
    assert code == 0
    run_record = json.loads((run_dir / "TEXT_SHADOW_RUN.json").read_text(encoding="utf-8"))
    registry_files = list((run_dir / "artifacts" / "fact_registry").glob("*.json"))
    assert len(registry_files) == 1
    registry = json.loads(registry_files[0].read_text(encoding="utf-8"))["payload"]

    facts = registry["facts"]
    assert len(facts) == 4
    for fact in facts:
        assert len(fact["provenance"]) == 1
        span = fact["provenance"][0]
        assert span["source_ref"]["digest"] == run_record["source_digest"]
        assert span["episode_id"] == "episode-1"
        assert span["scene_id"] == "scene-1"
        start, end = span["source_start"], span["source_end"]
        assert isinstance(start, int) and isinstance(end, int)
        assert 0 <= start < end <= len(_SOURCE)
        assert _SOURCE.index(fact["statement"]) == start
        assert _SOURCE[start:end] == fact["statement"]

    vec_files = list((run_dir / "artifacts" / "visual_execution_contract").glob("*.json"))
    assert len(vec_files) == 1
    vec_text = json.dumps(
        json.loads(vec_files[0].read_text(encoding="utf-8"))["payload"], ensure_ascii=False
    )
    assert "source_start" not in vec_text
    assert "source_end" not in vec_text
    assert "start_tick" in vec_text
    assert "end_tick" in vec_text


def test_a8_gate0_receipt_binds_the_fresh_dp_session_in_one_run(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    """The A8 run's result, Gate 0 receipt, review packet, and DP review
    result form one hash-bound chain: Projection bundle precedes Gate 0, and
    the fresh DP reviews only through that receipt.
    """

    provider = _RecordingStructuredProvider()
    reviewer = _FreshDPReviewer()

    code, response, run_dir = _invoke(
        monkeypatch, capsys, tmp_path, provider=provider, reviewer=reviewer, run_id="bound-run"
    )
    assert code == 0
    result = response["text_shadow"]
    gate0_id = result["gate0_result_artifact_id"]
    dp_result_id = result["dp_review_result_artifact_id"]
    assert gate0_id.startswith("id:")
    assert dp_result_id.startswith("id:")
    assert result["dp_fresh_session_id"]
    assert len(result["dp_audit_sha256"]) == 64
    assert len(result["run_record_sha256"]) == 64

    def _single_artifact(kind: str) -> dict[str, Any]:
        files = list((run_dir / "artifacts" / kind).glob("*.json"))
        assert len(files) == 1, kind
        return json.loads(files[0].read_text(encoding="utf-8"))

    gate0 = _single_artifact("gate0_result")
    packet = _single_artifact("review_packet")
    dp = _single_artifact("dp_review_result")

    # Gate 0 is the deterministic receipt over this run's projection bundle.
    assert gate0["payload"]["result_id"] == gate0_id
    assert gate0["payload"]["passed"] is True
    assert gate0["payload"]["failed_check_ids"] == []
    assert result["projection_ast_artifact_id"] in gate0["payload"]["target_artifact_ids"]
    assert result["vec_artifact_id"] in gate0["payload"]["target_artifact_ids"]

    # The fresh DP receives the gate0 receipt through the review packet only.
    assert gate0_id in packet["payload"]["gate_result_refs"]
    assert dp["payload"]["review_packet_artifact_id"] == packet["payload"]["packet_id"]
    assert packet["payload"]["packet_id"].startswith("id:")
    assert dp["payload"]["verdict"] == DPReviewVerdict.APPROVED.value
    assert dp["payload"]["finding_codes"] == []
    assert dp["payload"]["revision_request_artifact_ids"] == []
    assert len(dp["payload"]["independent_context_digest"]) == 64
