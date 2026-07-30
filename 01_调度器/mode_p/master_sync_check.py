"""Check structural consistency across Master, Manifest, Storyboard, and Video.

This is a deterministic local checker. It verifies:
- Shot IDs, count, and order are identical across all four files
- Durations match
- Scene ID and durations match
- Required canonical fields exist
- Enum values are valid
- Hash integrity

It MUST NOT judge semantic quality — that is the DP's responsibility.
It reports issues per-Shot, per-field; never produces a narrative score.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from master_compiler import CompilerError, compile_master
from view_deriver import DeriverError, derive_views

# --- Patterns for extracting canonical fields from view files ---

_STORY_SHOT_RE = re.compile(
    r"^##\s+(?:Shot|镜头)\s+(?P<scene_id>[A-Za-z0-9_-]+)-(?P<number>\d+)\s*\|\s*"
    r"(?:(?P<expr>[^|\n]+)\s*\|\s*)?(?P<duration>\d+(?:\.\d+)?)s\s*$",
    re.MULTILINE,
)
_VIDEO_SHOT_RE = re.compile(
    r"^##\s+(?:Shot|镜头)\s+(?P<scene_id>[A-Za-z0-9_-]+)-(?P<number>\d+)\s*\|\s*(?P<duration>\d+(?:\.\d+)?)s\s*$",
    re.MULTILINE,
)
_VIDEO_GEN_RE = re.compile(
    r"^(?:Generation|生成模式)[：:][ \t]*(?P<label>.+)$", re.MULTILINE,
)
_VIDEO_REF_RE = re.compile(
    r"^(?:References|参考资产)[：:][ \t]*\[(?P<ids>[^\]]*)\]", re.MULTILINE,
)
_VIDEO_CAMERA_RE = re.compile(r"^(?:Camera|摄影)[：:][ \t]*(?P<text>.+)$", re.MULTILINE)
_VIDEO_COMPOSITION_RE = re.compile(r"^(?:Composition|构图)[：:][ \t]*(?P<text>.+)$", re.MULTILINE)
_VIDEO_LIGHTING_RE = re.compile(r"^(?:Lighting|光影)[：:][ \t]*(?P<text>.+)$", re.MULTILINE)
_VIDEO_PERFORMANCE_RE = re.compile(r"^(?:Performance|表演)[：:][ \t]*(?P<text>.+)$", re.MULTILINE)
_VIDEO_SOUND_RE = re.compile(r"^(?:Sound|声音)[：:][ \t]*(?P<text>.+)$", re.MULTILINE)
_VIDEO_EXIT_RE = re.compile(r"^(?:Exit|切出)[：:][ \t]*(?P<text>.+)$", re.MULTILINE)
_STORY_IMAGE_LABEL_RE = re.compile(
    r"^(?:Image Frames|Relationship Frames|Attention Frames|Action Frames|"
    r"Reveal Frames|Stillness Frames|Discovery Frames|Rhythm Frames|"
    r"Spatial Handoff Frames|关键帧|注意力帧|动作帧|揭示帧|静默帧|发现帧|节拍帧|空间交接帧)[：:][ \t]*$",
    re.MULTILINE,
)
_STORY_TIMED_LINE_RE = re.compile(r"^\[(\d+(?:\.\d+)?)s\]", re.MULTILINE)
_STORY_LEGACY_FRAME_RE = re.compile(
    r"^[ \t]*-[ \t]+\[[^\]\r\n]+\][ \t]+\S.*$", re.MULTILINE
)
_STORY_ENTRY_RE = re.compile(r"^(?:Entry|进入)[：:][ \t]*(?P<text>.+)$", re.MULTILINE)
_STORY_EXIT_RE = re.compile(r"^(?:Transition|切出)[：:][ \t]*(?P<text>.+)$", re.MULTILINE)
# Old-format storyboard fields (kept for backward-compatible validation).
_STORY_CAMERA_RE = re.compile(r"^Camera:[ \t]*(?P<text>.+)$", re.MULTILINE)
_STORY_COMPOSITION_RE = re.compile(r"^Composition:[ \t]*(?P<text>.+)$", re.MULTILINE)
_STORY_LIGHTING_RE = re.compile(r"^Lighting:[ \t]*(?P<text>.+)$", re.MULTILINE)
_STORY_PERFORMANCE_RE = re.compile(r"^Performance:[ \t]*(?P<text>.+)$", re.MULTILINE)
_GEN_LABEL_TO_MODE = {
    "纯提示词": "text_only",
    "首尾帧": "first_last_frame",
    "全能参考": "omni_reference",
}

_EXPR_LABEL_TO_MODE = {
    "对话/权力": "conversation_power",
    "多人场面": "crowd_attention",
    "动作/追逐": "action_chase",
    "悬疑/揭示": "suspense_reveal",
    "沉思/沉默": "contemplative_silence",
    "调查/物体": "investigation_object",
    "蒙太奇": "montage",
    "多空间转场": "cross_space_transition",
}


@dataclass
class SyncIssue:
    file: str
    shot_id: str | None
    field: str
    expected: str
    actual: str


@dataclass
class SyncReport:
    issues: list[SyncIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.issues) == 0

    def add(self, file: str, shot_id: str | None, field: str, expected: str, actual: str) -> None:
        self.issues.append(SyncIssue(file, shot_id, field, expected, actual))


# ---------------------------------------------------------------------------
# public entry point
# ---------------------------------------------------------------------------

def check_sync(master_path: Path, manifest_path: Path,
               storyboard_path: Path, video_path: Path) -> SyncReport:
    """Run all structural sync checks. Returns a report; report.ok is True iff clean."""
    report = SyncReport()

    try:
        manifest = _read_json(manifest_path)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        report.add("SHOT_MANIFEST.json", None, "manifest", "valid JSON", str(exc))
        return report

    try:
        expected_manifest = compile_master(master_path)
    except (CompilerError, OSError) as exc:
        report.add("DIRECTOR_MASTER.md", None, "compile", "valid Master", str(exc))
        return report

    _check_manifest_projection(manifest, expected_manifest, report)
    if not isinstance(manifest.get("shots"), list):
        report.add("SHOT_MANIFEST.json", None, "shots", "array", "missing or invalid")
        return report

    try:
        story_text = storyboard_path.read_text(encoding="utf-8")
        video_text = video_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        report.add("views", None, "read", "UTF-8 files", str(exc))
        return report

    # 1. Shot count
    m_shots = manifest["shots"]
    sb_shots = list(_STORY_SHOT_RE.finditer(story_text))
    vp_shots = list(_VIDEO_SHOT_RE.finditer(video_text))

    if len(sb_shots) != len(m_shots):
        report.add("STORYBOARD.md", None, "shot_count",
                   str(len(m_shots)), str(len(sb_shots)))
    if len(vp_shots) != len(m_shots):
        report.add("VIDEO_PROMPT.md", None, "shot_count",
                   str(len(m_shots)), str(len(vp_shots)))

    # 2. Per-shot checks
    for i, mshot in enumerate(m_shots):
        shot_id = mshot["shot_id"]

        # 3a. Storyboard: Shot ID and duration
        if i < len(sb_shots):
            _check_story_shot(sb_shots[i], mshot, report)

        # 3b. Video: Shot ID and duration
        if i < len(vp_shots):
            _check_video_shot(vp_shots[i], mshot, report)

    # 3. Video: per-shot generation mode & reference assets
    _check_video_gen_and_refs(video_text, m_shots, report)

    # 4. Required Director-authored fields remain present and non-empty.
    _check_video_required_fields(video_text, m_shots, report)
    _check_story_required_fields(
        story_text, m_shots, report, manifest.get("manifest_version", "")
    )

    # 5. Exact re-derivation proves source identity without leaking internal
    # hashes, boundary IDs, timing enums, or other runtime metadata to prompts.
    _check_exact_derivation(
        master_path, manifest_path, story_text, video_text, report
    )

    return report


# ---------------------------------------------------------------------------
# internal checks
# ---------------------------------------------------------------------------

def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _check_exact_derivation(
    master_path: Path,
    manifest_path: Path,
    story_text: str,
    video_text: str,
    report: SyncReport,
) -> None:
    """Prove both views exactly match the current deterministic derivation."""
    try:
        with tempfile.TemporaryDirectory(prefix="mode-p-sync-") as directory:
            expected_story_path = Path(directory) / "STORYBOARD.md"
            expected_video_path = Path(directory) / "VIDEO_PROMPT.md"
            derive_views(
                master_path,
                manifest_path,
                expected_story_path,
                expected_video_path,
            )
            expected_story = expected_story_path.read_text(encoding="utf-8")
            expected_video = expected_video_path.read_text(encoding="utf-8")
    except (DeriverError, OSError) as exc:
        report.add(
            "views", None, "exact_derivation",
            "views derivable from current Master and Manifest", str(exc),
        )
        return

    if story_text != expected_story:
        report.add(
            "STORYBOARD.md", None, "derived_content",
            "exact current Master derivation", "content differs",
        )
    if video_text != expected_video:
        report.add(
            "VIDEO_PROMPT.md", None, "derived_content",
            "exact current Master derivation", "content differs",
        )


def _check_manifest_projection(manifest: dict, expected: dict,
                               report: SyncReport) -> None:
    """Manifest must be the current compiler's exact mechanical projection."""
    for key in (
        "manifest_version", "scene_id", "master_version",
        "master_content_hash", "compiler_version",
    ):
        actual_value = manifest.get(key)
        expected_value = expected.get(key)
        if actual_value != expected_value:
            report.add(
                "SHOT_MANIFEST.json", None, key,
                str(expected_value), str(actual_value),
            )
    if manifest.get("shots") != expected.get("shots"):
        report.add(
            "SHOT_MANIFEST.json", None, "shots_projection",
            "exact current Master projection", "different or missing",
        )


def _check_story_shot(sm: re.Match, mshot: dict, report: SyncReport) -> None:
    shot_id = mshot["shot_id"]
    sb_scene = sm.group("scene_id")
    sb_num = int(sm.group("number"))
    sb_dur = Decimal(sm.group("duration"))

    actual_id = f"{sb_scene}-{sb_num}"
    if actual_id != shot_id:
        report.add("STORYBOARD.md", shot_id, "shot_id", shot_id, actual_id)

    expected_dur = Decimal(str(mshot["duration"]))
    if sb_dur != expected_dur:
        report.add("STORYBOARD.md", shot_id, "duration",
                   str(expected_dur), str(sb_dur))

    # Old-format storyboard headers carry an expression label; validate it
    # when present.  New-format headers omit it (profile is implicit from
    # the surrounding field set).
    sb_expr = sm.group("expr")
    if sb_expr is not None:
        sb_expr_label = sb_expr.strip()
        expected_mode = mshot["scene_expression"]
        actual_mode = _EXPR_LABEL_TO_MODE.get(sb_expr_label)
        if actual_mode is None:
            report.add("STORYBOARD.md", shot_id, "scene_expression",
                       f"one of {sorted(_EXPR_LABEL_TO_MODE.keys())}", sb_expr_label)
        elif actual_mode != expected_mode:
            report.add("STORYBOARD.md", shot_id, "scene_expression",
                       expected_mode, actual_mode)


def _check_video_shot(vm: re.Match, mshot: dict, report: SyncReport) -> None:
    shot_id = mshot["shot_id"]
    vp_scene = vm.group("scene_id")
    vp_num = int(vm.group("number"))
    vp_dur = Decimal(vm.group("duration"))

    actual_id = f"{vp_scene}-{vp_num}"
    if actual_id != shot_id:
        report.add("VIDEO_PROMPT.md", shot_id, "shot_id", shot_id, actual_id)

    expected_dur = Decimal(str(mshot["duration"]))
    if vp_dur != expected_dur:
        report.add("VIDEO_PROMPT.md", shot_id, "duration",
                   str(expected_dur), str(vp_dur))


def _check_video_gen_and_refs(video_text: str, m_shots: list[dict],
                              report: SyncReport) -> None:
    """Check each video shot block for generation mode and reference assets."""
    # Split video into shot blocks
    blocks = _split_video_blocks(video_text)
    for i, mshot in enumerate(m_shots):
        shot_id = mshot["shot_id"]
        if i >= len(blocks):
            continue
        block = blocks[i]

        # Generation mode
        generation_matches = list(_VIDEO_GEN_RE.finditer(block))
        if len(generation_matches) == 1:
            gm = generation_matches[0]
            label = gm.group("label").strip()
            expected_mode = mshot["generation_mode"]
            actual_mode = _GEN_LABEL_TO_MODE.get(label)
            if actual_mode is None:
                report.add("VIDEO_PROMPT.md", shot_id, "generation_mode",
                           f"one of {sorted(_GEN_LABEL_TO_MODE.keys())}", label)
            elif actual_mode != expected_mode:
                report.add("VIDEO_PROMPT.md", shot_id, "generation_mode",
                           expected_mode, actual_mode)
        elif not generation_matches:
            report.add("VIDEO_PROMPT.md", shot_id, "generation_mode",
                       "present", "missing")
        else:
            report.add("VIDEO_PROMPT.md", shot_id, "generation_mode",
                       "exactly one", f"{len(generation_matches)} fields")

        # Reference assets (video uses "asset_id|responsibility" format)
        ref_entries = []
        reference_matches = list(_VIDEO_REF_RE.finditer(block))
        if len(reference_matches) > 1:
            report.add("VIDEO_PROMPT.md", shot_id, "reference_assets",
                       "at most one References field", f"{len(reference_matches)} fields")
        rm = reference_matches[0] if reference_matches else None
        if rm and rm.group("ids").strip():
            for token in rm.group("ids").split(","):
                token = token.strip()
                if token:
                    parts = token.split("|", 1)
                    ref_entries.append({
                        "asset_id": parts[0].strip(),
                        "responsibility": parts[1].strip() if len(parts) > 1 else "",
                    })

        expected_refs = [
            (a["asset_id"], a["responsibility"])
            for a in mshot["reference_assets"]
        ]
        actual_refs = [
            (r["asset_id"], r["responsibility"])
            for r in ref_entries
        ]
        if actual_refs != expected_refs:
            report.add("VIDEO_PROMPT.md", shot_id, "reference_assets",
                       str(expected_refs), str(actual_refs))


def _check_video_required_fields(video_text: str, m_shots: list[dict],
                                  report: SyncReport) -> None:
    """Verify each video shot has exactly one non-empty required source field."""
    blocks = _split_video_blocks(video_text)
    for i, mshot in enumerate(m_shots):
        shot_id = mshot["shot_id"]
        if i >= len(blocks):
            continue
        block = blocks[i]

        for pattern, field_name in [
            (_VIDEO_CAMERA_RE, "摄影"),
            (_VIDEO_COMPOSITION_RE, "构图"),
            (_VIDEO_LIGHTING_RE, "光影"),
            (_VIDEO_PERFORMANCE_RE, "表演"),
            (_VIDEO_SOUND_RE, "声音"),
            (_VIDEO_EXIT_RE, "切出"),
        ]:
            matches = list(pattern.finditer(block))
            if len(matches) != 1 or not matches[0].group("text").strip():
                report.add("VIDEO_PROMPT.md", shot_id, field_name,
                           "exactly one non-empty field",
                           "empty/missing" if not matches else f"{len(matches)} fields")

        image_labels = re.findall(r"^(?:Image|画面)[：:]\s*$", block, re.MULTILINE)
        time_nodes = re.findall(r"^\[(\d+(?:\.\d+)?)s\]", block, re.MULTILINE)
        if len(image_labels) != 1 or not time_nodes:
            report.add("VIDEO_PROMPT.md", shot_id, "Image timeline",
                       "one Image block with time nodes",
                       f"Image labels={len(image_labels)}, time nodes={len(time_nodes)}")


def _check_story_required_fields(story_text: str, m_shots: list[dict],
                                 report: SyncReport,
                                 manifest_version: str) -> None:
    """Verify Storyboard has focus frames and exit handoff per shot."""
    blocks = _split_story_blocks(story_text)
    # Detect format: old-format storyboards carry Camera / Composition / Lighting
    # fields; new-format storyboards carry only profile-specific fields + frames.
    is_old_format = bool(_STORY_CAMERA_RE.search(story_text) or
                         re.search(r"^Camera:", story_text, re.MULTILINE))

    for i, mshot in enumerate(m_shots):
        shot_id = mshot["shot_id"]
        if i >= len(blocks):
            continue
        block = blocks[i]

        # Manifest 1.2 derives storyboard frames from the unified visual timeline,
        # so every frame must retain its explicit timestamp.  Manifest 1.1 is the
        # supported historical contract: its Director-authored focus frames are
        # labelled bullets without timestamps.  Do not apply the 1.2 requirement
        # to 1.1 evidence, but still require at least two concrete frame states.
        label_match = _STORY_IMAGE_LABEL_RE.search(block)
        if not label_match:
            report.add("STORYBOARD.md", shot_id, "focus_frames",
                       "exactly one focus frame label line", "missing")
        else:
            after_label = block[label_match.end():]
            if manifest_version == "1.1":
                legacy_frames = _STORY_LEGACY_FRAME_RE.findall(after_label)
                if len(legacy_frames) < 2:
                    report.add("STORYBOARD.md", shot_id, "focus_frames",
                               "at least 2 labelled legacy frame lines",
                               str(len(legacy_frames)))
            else:
                timed_lines = _STORY_TIMED_LINE_RE.findall(after_label)
                if len(timed_lines) < 2:
                    report.add("STORYBOARD.md", shot_id, "focus_frames",
                               "at least 2 timed frame lines",
                               str(len(timed_lines)))

        # Old-format extra checks.
        if is_old_format:
            for pattern, field_name in [
                (_STORY_CAMERA_RE, "Camera"),
                (_STORY_COMPOSITION_RE, "Composition"),
                (_STORY_LIGHTING_RE, "Lighting"),
                (_STORY_PERFORMANCE_RE, "Performance"),
            ]:
                matches = list(pattern.finditer(block))
                if len(matches) != 1 or not matches[0].group("text").strip():
                    report.add("STORYBOARD.md", shot_id, field_name,
                               "exactly one non-empty field",
                               "empty/missing" if not matches else f"{len(matches)} fields")

        # Exit handoff (both formats).
        exit_matches = list(_STORY_EXIT_RE.finditer(block))
        if not exit_matches:
            exit_matches = list(re.finditer(r"^Transition:", block, re.MULTILINE))
        if len(exit_matches) != 1 or not exit_matches[0].group("text").strip():
            report.add("STORYBOARD.md", shot_id, "exit",
                       "exactly one non-empty exit handoff",
                       "empty/missing" if not exit_matches else f"{len(exit_matches)} fields")


def _split_video_blocks(text: str) -> list[str]:
    """Split video prompt into per-shot blocks."""
    blocks = []
    current_start = None
    for m in _VIDEO_SHOT_RE.finditer(text):
        if current_start is not None:
            blocks.append(text[current_start:m.start()])
        current_start = m.start()
    if current_start is not None:
        blocks.append(text[current_start:])
    return blocks


def _split_story_blocks(text: str) -> list[str]:
    """Split storyboard prompt into per-shot blocks."""
    blocks = []
    current_start = None
    for match in _STORY_SHOT_RE.finditer(text):
        if current_start is not None:
            blocks.append(text[current_start:match.start()])
        current_start = match.start()
    if current_start is not None:
        blocks.append(text[current_start:])
    return blocks


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check structural consistency across MODE:P output files."
    )
    parser.add_argument("master", type=Path, help="Path to DIRECTOR_MASTER.md")
    parser.add_argument("manifest", type=Path, help="Path to SHOT_MANIFEST.json")
    parser.add_argument("storyboard", type=Path, help="Path to STORYBOARD.md")
    parser.add_argument("video", type=Path, help="Path to VIDEO_PROMPT.md")
    args = parser.parse_args()

    for p in [args.master, args.manifest, args.storyboard, args.video]:
        if not p.is_file():
            print(f"File not found: {p}", file=sys.stderr)
            return 2

    report = check_sync(args.master, args.manifest, args.storyboard, args.video)

    if report.ok:
        print("Sync check passed — all canonical fields consistent.")
        return 0

    for issue in report.issues:
        loc = f"{issue.file}"
        if issue.shot_id:
            loc += f" [{issue.shot_id}]"
        print(f"{loc}  {issue.field}: expected={issue.expected}  actual={issue.actual}")
    return 1


if __name__ == "__main__":
    from cli_stdio import configure_utf8_stdio

    configure_utf8_stdio()
    raise SystemExit(main())
