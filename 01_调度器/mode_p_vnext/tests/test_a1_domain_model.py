"""A1 v3.0 canonical-domain invariants.

These tests intentionally freeze contracts for later packages.  They do not
claim that A5 assembly, A6 projection, or visual acceptance already exists.
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
from pathlib import Path

import pytest

from mode_p_vnext.compat import LegacyCheckpointObservation, LegacyFactObservation
from mode_p_vnext.compat.legacy_checkpoint import read_legacy_b0_k2_checkpoint
from mode_p_vnext.compat.legacy_facts import read_legacy_script_fact
from mode_p_vnext.domain import (
    DOMAIN_SCHEMA_VERSION,
    SD20_MAX_GENERATION_TICKS,
    TICKS_PER_SECOND,
    ArtifactEnvelope,
    ArtifactKind,
    CanonicalTimeline,
    DecisionBasis,
    DialogueBindingIntent,
    DirectorDecision,
    DomainValidationError,
    DurationIntent,
    ExecutionDesignDraft,
    FactConfidence,
    FactExtractionDraft,
    FactKind,
    FactQualifiers,
    GenerationCapabilityProfile,
    GenerationMode,
    GenerationUnit,
    GenerationUnitTimeline,
    NormalizedSource,
    PlacementPhase,
    ReferenceBindingIntent,
    ReferenceRequirement,
    ReferenceResponsibility,
    SceneTimeline,
    ShotBoundary,
    ShotDesignDraft,
    StoryboardRole,
    TickMarker,
    TickRange,
    TimelinePlacement,
    VisualBeat,
    VisualBeatDraft,
    VisualBeatPhase,
    VisualCurvePoint,
    VisualExecutionContract,
    VisualShot,
    VoiceRequirement,
)
from mode_p_vnext.domain.artifact import canonical_sha256
from mode_p_vnext.services.fact_assembler import FactAssembler
from mode_p_vnext.services.source_normalizer import SourceNormalizer


UTC = "2026-08-01T13:00:00Z"
FACT_ID_1 = "id:" + "1" * 64
FACT_ID_2 = "id:" + "2" * 64
FACT_HANDLE_1 = "fh:" + "a" * 64
FACT_HANDLE_2 = "fh:" + "b" * 64
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64


def _source() -> NormalizedSource:
    text = "第一场\n安娜握住钥匙。\n安娜说：走吧。\n"
    return SourceNormalizer.normalize(
        text.replace("\n", "\r\n"),
        source_id="script:episode-1",
        locator="episode-1.txt",
        normalized_partitions=(("episode:1", "scene:1", 0, len(text)),),
    )


def _drafts(source: NormalizedSource) -> tuple[FactExtractionDraft, ...]:
    prop = "安娜握住钥匙。"
    dialogue = "安娜说：走吧。"
    return (
        FactExtractionDraft(
            semantic=__import__("mode_p_vnext.domain", fromlist=["FactSemantic"]).FactSemantic.PROP,
            statement=prop,
            source_start=source.normalized_text.index(prop),
            source_end=source.normalized_text.index(prop) + len(prop),
            confidence=FactConfidence.EXPLICIT,
            qualifiers=FactQualifiers("episode:1", "scene:1", subject_label="安娜"),
        ),
        FactExtractionDraft(
            semantic=__import__("mode_p_vnext.domain", fromlist=["FactSemantic"]).FactSemantic.DIALOGUE,
            statement=dialogue,
            source_start=source.normalized_text.index(dialogue),
            source_end=source.normalized_text.index(dialogue) + len(dialogue),
            confidence=FactConfidence.EXPLICIT,
            qualifiers=FactQualifiers(
                "episode:1", "scene:1", subject_label="安娜", spoken_text="走吧"
            ),
        ),
    )


def _assembled():
    source = _source()
    envelope = FactAssembler().assemble(
        normalized_source=source,
        normalized_source_artifact_id="normalized-source:1",
        drafts=_drafts(source),
        source_kind=FactKind.SCRIPT,
        producer_stage="I0.fact_assembler",
        created_at_utc=UTC,
    )
    return source, envelope


def _design(handle_1: str = FACT_HANDLE_1, handle_2: str = FACT_HANDLE_2):
    beat = VisualBeatDraft(1, VisualBeatPhase.ACTION, "安娜握紧钥匙", "钥匙", StoryboardRole.REQUIRED)
    shot_1 = ShotDesignDraft(
        shot_ordinal=1,
        blocking_beat_ordinal=1,
        duration_intent=DurationIntent.STANDARD,
        generation_mode=GenerationMode.OMNI_REFERENCE,
        composition="近景", camera="固定镜头", lighting="低调照明", performance="克制紧张",
        visual_beats=(beat,),
        reference_binding_intents=(
            ReferenceBindingIntent(1, 1, handle_1, ReferenceResponsibility.PROP_IDENTITY),
        ),
        dialogue_binding_intents=(),
        creative_notes="钥匙始终在右手。",
    )
    shot_2 = ShotDesignDraft(
        shot_ordinal=2,
        blocking_beat_ordinal=2,
        duration_intent=DurationIntent.STANDARD,
        generation_mode=GenerationMode.FIRST_LAST_FRAME,
        composition="中景", camera="缓慢推进", lighting="低调照明", performance="果断开口",
        visual_beats=(beat,),
        reference_binding_intents=(),
        dialogue_binding_intents=(DialogueBindingIntent(2, 1, handle_2, PlacementPhase.MIDDLE),),
        creative_notes="对白落在动作之后。",
    )
    return shot_1, shot_2


def _vec() -> VisualExecutionContract:
    profile = GenerationCapabilityProfile.sd20_default()
    shot_1_placement = TimelinePlacement("unit:1", "scene:1", TickRange(0, 240_000))
    shot_2_placement = TimelinePlacement("unit:2", "scene:1", TickRange(240_000, 480_000))
    scene = SceneTimeline("scene:1", TickRange(0, 480_000), (shot_1_placement, shot_2_placement))
    unit_1 = GenerationUnit(
        "unit:1", "shot:1", GenerationMode.OMNI_REFERENCE,
        GenerationUnitTimeline(240_000, "sd2.0", "3.0.0", 360_000), shot_1_placement,
    )
    unit_2 = GenerationUnit(
        "unit:2", "shot:2", GenerationMode.FIRST_LAST_FRAME,
        GenerationUnitTimeline(240_000, "sd2.0", "3.0.0", 360_000), shot_2_placement,
    )
    decision = DirectorDecision("decision:1", 1, "camera", DecisionBasis.LOCKED, ("director",), ("push",), 0, "紧张", "无")
    curve = VisualCurvePoint("curve:1", 1, "blocking:1", 60, "推进")
    beat_1 = VisualBeat(
        "beat:1", "shot:1", 1, VisualBeatPhase.ACTION, TickRange(0, 240_000),
        "握紧钥匙", "钥匙", StoryboardRole.REQUIRED, "state:0", "state:1",
        ("decision:1",), ("reference:1",), (),
    )
    beat_2 = VisualBeat(
        "beat:2", "shot:2", 1, VisualBeatPhase.ACTION, TickRange(0, 240_000),
        "开口", "安娜", StoryboardRole.REQUIRED, "state:1", "state:2",
        ("decision:1",), (), ("audio:1",),
    )
    shot_1 = VisualShot(
        "shot:1", "unit:1", 1, "blocking:1", GenerationMode.OMNI_REFERENCE, TickRange(0, 240_000),
        "近景", "固定", "低调", "克制", "钥匙在右手", (beat_1,), ("decision:1",), ("reference:1",), (),
    )
    shot_2 = VisualShot(
        "shot:2", "unit:2", 2, "blocking:2", GenerationMode.FIRST_LAST_FRAME, TickRange(0, 240_000),
        "中景", "推进", "低调", "果断", "对白后收束", (beat_2,), ("decision:1",), (), ("audio:1",),
    )
    reference = ReferenceRequirement(
        "reference:1", ReferenceResponsibility.PROP_IDENTITY, FACT_ID_1, FACT_HANDLE_1, "shot:1", "beat:1"
    )
    audio = __import__("mode_p_vnext.domain", fromlist=["AudioEvent"]).AudioEvent(
        "audio:1", FACT_ID_2, FACT_HANDLE_2, "shot:2", "beat:2", TickMarker(120_000),
        PlacementPhase.MIDDLE, "安娜", "走吧", None,
    )
    voice = VoiceRequirement("voice:1", "audio:1", "安娜", "shot:2", "beat:2")
    boundaries = (
        ShotBoundary("boundary:0", 0, 0, None, "shot:1", "scene:pre", "state:0", "进入", ("decision:1",)),
        ShotBoundary("boundary:1", 1, 240_000, "shot:1", "shot:2", "state:1", "state:1", "切换", ("decision:1",)),
        ShotBoundary("boundary:2", 2, 480_000, "shot:2", None, "state:2", "scene:post", "离场", ("decision:1",)),
    )
    return VisualExecutionContract(
        "vec:1", "episode:1", "scene:1", "execution:1", "blocking:commit:1",
        (FACT_ID_1, FACT_ID_2), (FACT_HANDLE_1, FACT_HANDLE_2), CanonicalTimeline(), scene, profile,
        (curve,), (decision,), (unit_1, unit_2), (shot_1, shot_2), boundaries, (audio,), (voice,),
        (reference,), "交给投影", DIGEST_A, DIGEST_B,
    )


def test_canonical_artifact_envelope_is_exact_payload_hashed_and_typed():
    source = _source()
    assert tuple(field.name for field in dataclasses.fields(ArtifactEnvelope)) == (
        "artifact_id", "artifact_type", "schema_version", "payload", "canonical_payload_sha256",
        "producer_stage", "parent_artifact_ids", "source_provenance", "knowledge_snapshot_digest", "created_at_utc",
    )
    envelope = ArtifactEnvelope.create(
        artifact_id="normalized-source:1", artifact_type=ArtifactKind.NORMALIZED_SOURCE,
        payload=source, producer_stage="ingest.normalize", parent_artifact_ids=(),
        source_provenance=(source.source_ref,), knowledge_snapshot_digest=None, created_at_utc=UTC,
    )
    assert envelope.canonical_payload_sha256 == canonical_sha256(source)
    with pytest.raises(DomainValidationError, match="canonical_payload_sha256"):
        dataclasses.replace(envelope, canonical_payload_sha256="0" * 64)
    with pytest.raises(DomainValidationError, match="payload type"):
        dataclasses.replace(envelope, artifact_type=ArtifactKind.FACT_REGISTRY)


def test_schema_is_v30_and_domain_is_the_only_canonical_authority():
    import mode_p_vnext.domain.artifact as artifact
    import mode_p_vnext.domain.blocking as blocking
    import mode_p_vnext.domain.decisions as decisions
    import mode_p_vnext.domain.direction as direction
    import mode_p_vnext.domain.evidence as evidence
    import mode_p_vnext.domain.facts as facts
    import mode_p_vnext.domain.ids as ids
    import mode_p_vnext.domain.knowledge as knowledge
    import mode_p_vnext.domain.projection as projection
    import mode_p_vnext.domain.release as release
    import mode_p_vnext.domain.time as time
    import mode_p_vnext.domain.vec as vec

    modules = (artifact, blocking, decisions, direction, evidence, facts, ids, knowledge, projection, release, time, vec)
    assert DOMAIN_SCHEMA_VERSION == "3.0"
    assert all(module.DOMAIN_SCHEMA_VERSION == DOMAIN_SCHEMA_VERSION for module in modules)
    names = [name for module in modules for name in module.CANONICAL_DOMAIN_TYPES]
    assert len(names) == len(set(names))
    assert projection.ProjectionAST.__module__ == "mode_p_vnext.domain.projection"
    assert vec.VisualExecutionContract.__module__ == "mode_p_vnext.domain.vec"


def test_drafts_cannot_carry_final_ids_hashes_or_raw_ticks():
    fields = {field.name for field in dataclasses.fields(ShotDesignDraft)}
    assert fields == {
        "shot_ordinal", "blocking_beat_ordinal", "duration_intent", "generation_mode", "composition",
        "camera", "lighting", "performance", "visual_beats", "reference_binding_intents",
        "dialogue_binding_intents", "creative_notes",
    }
    assert not {"shot_id", "duration_ticks", "start_tick", "end_tick", "audio_intents", "reference_intents"} & fields
    assert {field.name for field in dataclasses.fields(ExecutionDesignDraft)} == {
        "curve_points", "decisions", "shots", "transition_intents", "handoff_intent"
    }
    fact_fields = {field.name for field in dataclasses.fields(FactExtractionDraft)}
    assert fact_fields == {"semantic", "statement", "source_start", "source_end", "confidence", "qualifiers"}
    assert not {"fact_id", "fact_handle", "ordinal", "tick"} & fact_fields
    with pytest.raises(DomainValidationError, match="DurationIntent"):
        dataclasses.replace(_design()[0], duration_intent="240000")


def test_normalized_source_contract_is_canonical_and_partitioned():
    source = _source()
    assert source.normalized_text.count("\r") == 0
    assert source.encoding == "utf-8"
    assert source.line_start_offsets == (0, 4, 12, 20)
    assert source.partitions[0].scene_id == "scene:1"
    assert source.source_ref.digest == __import__("hashlib").sha256(source.normalized_text.encode()).hexdigest()
    with pytest.raises(DomainValidationError, match="partitions"):
        SourceNormalizer.normalize("x", source_id="s", normalized_partitions=())
    with pytest.raises(DomainValidationError, match="gap-free"):
        SourceNormalizer.normalize("abcd", source_id="s", normalized_partitions=(("e", "s1", 0, 2), ("e", "s2", 3, 4)))


def test_local_fact_assembler_validates_deduplicates_and_mints_opaque_handles():
    source, envelope = _assembled()
    registry = envelope.payload
    assert envelope.artifact_type is ArtifactKind.FACT_REGISTRY
    assert all(fact.fact_id.startswith("id:") and fact.fact_handle.startswith("fh:") for fact in registry.facts)
    assert all("prop" not in fact.fact_handle and "dialogue" not in fact.fact_handle for fact in registry.facts)
    assert registry.by_handle(registry.facts[0].fact_handle) is registry.facts[0]
    duplicate = dataclasses.replace(_drafts(source)[0], confidence=FactConfidence.SUPPORTED)
    rerun = FactAssembler().assemble(
        normalized_source=source, normalized_source_artifact_id="normalized-source:1",
        drafts=tuple(reversed(_drafts(source))) + (duplicate,), source_kind=FactKind.SCRIPT,
        producer_stage="I0.fact_assembler", created_at_utc=UTC,
    )
    assert len(rerun.payload.facts) == 2
    assert rerun.payload.facts[0].confidence is FactConfidence.SUPPORTED
    with pytest.raises(DomainValidationError, match="exact registry member"):
        registry.by_handle("fh:" + "f" * 64)
    unsupported = dataclasses.replace(_drafts(source)[0], statement="不存在")
    with pytest.raises(DomainValidationError, match="supported"):
        FactAssembler().assemble(
            normalized_source=source, normalized_source_artifact_id="normalized-source:1", drafts=(unsupported,),
            source_kind=FactKind.SCRIPT, producer_stage="I0.fact_assembler", created_at_utc=UTC,
        )


def test_fact_source_span_must_match_the_complete_canonical_statement():
    source = _source()
    draft = _drafts(source)[0]
    broad_span = dataclasses.replace(draft, source_start=0)

    with pytest.raises(DomainValidationError, match="complete canonical statement"):
        FactAssembler().assemble(
            normalized_source=source,
            normalized_source_artifact_id="normalized-source:1",
            drafts=(broad_span,),
            source_kind=FactKind.SCRIPT,
            producer_stage="I0.fact_assembler",
            created_at_utc=UTC,
        )


def test_fact_semantics_and_source_spans_are_typed_provenance_only():
    source, envelope = _assembled()
    dialogue = envelope.payload.by_semantic(__import__("mode_p_vnext.domain", fromlist=["FactSemantic"]).FactSemantic.DIALOGUE)[0]
    assert dialogue.validate_against_normalized_source(source) == ("安娜说：走吧。",)
    assert {field.name for field in dataclasses.fields(type(dialogue))} == {
        "fact_id", "fact_handle", "kind", "semantic", "statement", "confidence", "qualifiers", "provenance", "ordinal"
    }
    assert "tick" not in inspect.getsource(FactAssembler).casefold()
    with pytest.raises(DomainValidationError, match="spoken_text"):
        FactExtractionDraft(
            __import__("mode_p_vnext.domain", fromlist=["FactSemantic"]).FactSemantic.DIALOGUE,
            "安娜说：走吧。", 12, 20, FactConfidence.EXPLICIT,
            FactQualifiers("episode:1", "scene:1", subject_label="安娜"),
        )


def test_legacy_adapters_are_read_only_observations(tmp_path: Path):
    source = _source()
    observation = read_legacy_script_fact(
        {"fact_id": "dialogue_1", "statement": "安娜说：走吧。", "semantic": "dialogue"},
        normalized_source=source, source_start=12, source_end=20,
    )
    assert isinstance(observation, LegacyFactObservation)
    assert observation.requires_reingest is True
    assert not hasattr(observation, "fact_handle")
    checkpoint = {
        "blocking_commit": {
            "scene_id": "scene:1", "beats": [{
                "entry_state_id": "in", "exit_state_id": "out", "space_control": "room",
                    "dramatic_reason": "pressure", "dramatic_function": "wait",
                    "character_states": [{"character_id": "Anna", "gaze_target": "door"}],
                    "prop_states": [{"prop_id": "key", "holder": "Anna"}], "action_paths": ["hold"],
            }],
        }
    }
    path = tmp_path / "legacy.json"
    path.write_text(__import__("json").dumps(checkpoint), encoding="utf-8")
    legacy_checkpoint = read_legacy_b0_k2_checkpoint(path)
    assert isinstance(legacy_checkpoint, LegacyCheckpointObservation)
    assert legacy_checkpoint.requires_reassembly is True
    assert not hasattr(legacy_checkpoint, "artifact_id")


def test_24000_tick_capability_applies_per_generation_unit_not_scene():
    profile = GenerationCapabilityProfile.sd20_default()
    assert TICKS_PER_SECOND == 24_000
    assert profile.max_generation_ticks == SD20_MAX_GENERATION_TICKS == 360_000
    assert profile.option_for(DurationIntent.EXTENDED).max_ticks == 360_000
    assert _vec().scene_timeline.interval.duration_ticks == 480_000  # Scene may exceed 15 seconds.
    with pytest.raises(DomainValidationError, match="exceeds capability"):
        GenerationUnitTimeline(360_001, "sd2.0", "3.0.0", 360_000)
    with pytest.raises(DomainValidationError, match="start_tick < end_tick"):
        TickRange(10, 10)
    with pytest.raises(DomainValidationError, match="DurationIntent"):
        profile.option_for("extended")


def test_typed_reference_and_dialogue_binding_intents_are_scoped_exactly():
    shot_1, shot_2 = _design()
    assert shot_1.reference_binding_intents[0].visual_beat_ordinal == 1
    assert shot_2.dialogue_binding_intents[0].placement_phase is PlacementPhase.MIDDLE
    with pytest.raises(DomainValidationError, match="unknown VisualBeatDraft"):
        dataclasses.replace(shot_1, reference_binding_intents=(
            ReferenceBindingIntent(1, 2, FACT_HANDLE_1, ReferenceResponsibility.PROP_IDENTITY),
        ))
    with pytest.raises(DomainValidationError, match="opaque"):
        DialogueBindingIntent(1, 1, "dialogue:0001", PlacementPhase.OPENING)


def test_vec_contract_freezes_one_unit_per_shot_n_plus_one_and_bidirectional_bindings():
    vec = _vec()
    assert len(vec.generation_units) == len(vec.shots) == 2
    assert len(vec.boundaries) == 3
    assert vec.boundaries[1].scene_tick == 240_000
    assert vec.audio_events[0].media_duration_ticks is None
    with pytest.raises(DomainValidationError, match=r"N\+1"):
        dataclasses.replace(vec, boundaries=vec.boundaries[:-1])
    with pytest.raises(DomainValidationError, match="exactly one GenerationUnit"):
        dataclasses.replace(vec, generation_units=vec.generation_units[:-1])
    bad_shot = dataclasses.replace(vec.shots[0], reference_requirement_ids=())
    with pytest.raises(DomainValidationError, match="back-referenced"):
        dataclasses.replace(vec, shots=(bad_shot, vec.shots[1]))


def test_vnext_production_modules_do_not_redefine_canonical_domain_types():
    import mode_p_vnext.domain.artifact as artifact
    import mode_p_vnext.domain.blocking as blocking
    import mode_p_vnext.domain.decisions as decisions
    import mode_p_vnext.domain.direction as direction
    import mode_p_vnext.domain.evidence as evidence
    import mode_p_vnext.domain.facts as facts
    import mode_p_vnext.domain.ids as ids
    import mode_p_vnext.domain.knowledge as knowledge
    import mode_p_vnext.domain.projection as projection
    import mode_p_vnext.domain.release as release
    import mode_p_vnext.domain.time as time
    import mode_p_vnext.domain.vec as vec

    canonical = {
        name
        for module in (
            artifact,
            blocking,
            decisions,
            direction,
            evidence,
            facts,
            ids,
            knowledge,
            projection,
            release,
            time,
            vec,
        )
        for name in module.CANONICAL_DOMAIN_TYPES
    }
    package_root = Path(__file__).resolve().parents[1]
    duplicates: list[str] = []
    for source_path in sorted(package_root.rglob("*.py")):
        relative = source_path.relative_to(package_root)
        if "domain" in relative.parts or "tests" in relative.parts:
            continue
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        duplicates.extend(
            f"{node.name}@{relative.as_posix()}"
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name in canonical
        )

    assert not duplicates, "duplicate canonical domain authorities: " + ", ".join(duplicates)
