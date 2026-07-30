"""Deterministic hard-boundary checks for derived SD2.0 video prompts.

Advisory quality risks such as readable faces, generated text, emotional wording,
or action complexity belong to the current capability profile and fresh DP review.
This module blocks only syntax and timing conditions it can prove mechanically.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


NEGATIVE_TERMS = (
    "不要", "禁止", "避免", "不能", "不应", "切勿", "严禁", "不得",
)
UNRESOLVED_PLACEHOLDERS = (
    "[Director:", "<Director:", "{{", "}}", "TBD", "TODO", "待定", "待补",
)
UNCERTAIN_TERMS = (
    "可能", "也许", "或许", "或者", "取决于", "视情况", "任选", "二选一", "如果",
)
# Slash between two Chinese words is an unresolved branch: 站/坐, 前景/侧景.
_SLASH_BRANCH_RE = re.compile(r"[一-鿿]+/[一-鿿]+")
NON_VISIBLE_TERMS = (
    "仿佛", "好像", "似乎", "内心", "心想", "意识到", "想起", "感觉到", "感到",
)
NEGATIVE_ACTION = re.compile(
    r"不(?:移动|微笑|眨眼|转身|说话|抖动|变形|出现|看向|动作|走动|奔跑|"
    r"停下|露出|显示|改变|闪烁|漂移|切换|模糊|发声|回头|抬头|低头)"
)
ENGLISH_NEGATIVE = re.compile(r"\b(?:no|not|without|avoid|never|do not)\b", re.IGNORECASE)
ENGLISH_UNCERTAIN = re.compile(r"\b(?:maybe|perhaps|possibly|if|either|or)\b", re.IGNORECASE)
ANGLE_PLACEHOLDER = re.compile(r"<[^>\r\n]+>")
SHOT_HEADER = re.compile(
    r"^##\s*(?:Shot|镜头)\s+(?P<shot_id>[^|\r\n]+?)\s*\|\s*(?P<duration>-?\d+(?:\.\d+)?)\s*(?:s|秒)\s*$",
    re.MULTILINE | re.IGNORECASE,
)
SHOT_PREFIX = re.compile(r"^##\s*(?:Shot|镜头)\b.*$", re.MULTILINE | re.IGNORECASE)
TIME_NODE = re.compile(r"\[\s*(?P<time>-?\d+(?:\.\d+)?)\s*(?:s|秒)\s*\]", re.IGNORECASE)
TIMED_LINE = re.compile(
    r"^\[\s*(?P<time>-?\d+(?:\.\d+)?)\s*(?:s|秒)\s*\]\s*(?P<text>\S.*)$",
    re.MULTILINE | re.IGNORECASE,
)
IMAGE_BLOCK = re.compile(
    r"^(?:Image|画面)[：:]\s*(?P<text>.*?)(?=^(?:Sound|声音)[：:])",
    re.MULTILINE | re.DOTALL | re.IGNORECASE,
)
SOUND_BLOCK = re.compile(
    r"^(?:Sound|声音)[：:]\s*(?P<text>.*?)(?=^(?:Exit|切出)[：:])",
    re.MULTILINE | re.DOTALL | re.IGNORECASE,
)
EXIT_BLOCK = re.compile(
    r"^(?:Exit|切出)[：:]\s*(?P<text>.*?)(?=^##\s*(?:Shot|镜头)\s+|\Z)",
    re.MULTILINE | re.DOTALL | re.IGNORECASE,
)


@dataclass(frozen=True)
class Issue:
    kind: str
    message: str


def scan_prompt(text: str) -> list[Issue]:
    issues: list[Issue] = []

    for marker in UNRESOLVED_PLACEHOLDERS:
        if marker in text:
            issues.append(Issue(
                "unresolved_placeholder",
                f"Video prompt contains unresolved template marker '{marker}'.",
            ))
    for placeholder in ANGLE_PLACEHOLDER.findall(text):
        issues.append(Issue(
            "unresolved_placeholder",
            f"Video prompt contains unresolved angle-bracket placeholder '{placeholder}'.",
        ))

    shot_matches = list(SHOT_HEADER.finditer(text))
    shot_prefixes = list(SHOT_PREFIX.finditer(text))
    if not shot_prefixes:
        issues.append(Issue("missing_shot_header", "Video prompt contains no parseable Shot header."))
    elif len(shot_matches) != len(shot_prefixes):
        issues.append(Issue("malformed_shot_header", "One or more Shot headers do not use '## Shot <id> | <duration>s'."))

    seen_ids: set[str] = set()
    for index, match in enumerate(shot_matches):
        shot_id = match.group("shot_id").strip()
        duration = float(match.group("duration"))
        if shot_id in seen_ids:
            issues.append(Issue("duplicate_shot_id", f"Shot ID '{shot_id}' appears more than once."))
        seen_ids.add(shot_id)
        if duration <= 0:
            issues.append(Issue("duration", f"Shot {shot_id} duration must be greater than 0s."))
        if duration > 15:
            issues.append(Issue("duration", f"Shot {shot_id} duration is {duration:g}s; SD2.0 segments must be 15s or shorter."))

        block_end = shot_matches[index + 1].start() if index + 1 < len(shot_matches) else len(text)
        shot_block = text[match.end():block_end]
        image_matches = list(IMAGE_BLOCK.finditer(shot_block))
        sound_matches = list(SOUND_BLOCK.finditer(shot_block))
        exit_matches = list(EXIT_BLOCK.finditer(shot_block))
        if len(image_matches) != 1:
            issues.append(Issue(
                "image_block",
                f"Shot {shot_id} must contain exactly one Image block; found {len(image_matches)}.",
            ))
        else:
            image_text = image_matches[0].group("text").strip()
            nodes = list(TIMED_LINE.finditer(image_text))
            covered = "\n".join(node.group(0) for node in nodes).strip()
            if not nodes or covered != image_text:
                issues.append(Issue(
                    "timeline_shape",
                    f"Shot {shot_id} Image block must contain one visible event per timed line.",
                ))
            else:
                times = [float(node.group("time")) for node in nodes]
                if times[0] != 0 or times[-1] != duration:
                    issues.append(Issue(
                        "timeline_bounds",
                        f"Shot {shot_id} Image timeline must start at 0s and end at {duration:g}s.",
                    ))
                if any(right <= left for left, right in zip(times, times[1:])):
                    issues.append(Issue(
                        "timeline_order",
                        f"Shot {shot_id} Image time nodes must be strictly increasing.",
                    ))
                for node in times:
                    if node < 0 or node > duration:
                        issues.append(Issue(
                            "time_range",
                            f"Shot {shot_id} time node {node:g}s is outside 0-{duration:g}s.",
                        ))
            if "[SB]" in image_text:
                issues.append(Issue(
                    "derivation_marker",
                    f"Shot {shot_id} leaks internal [SB] markers into the final video prompt.",
                ))
        if len(sound_matches) != 1 or not (
            sound_matches and sound_matches[0].group("text").strip()
        ):
            issues.append(Issue(
                "sound_block", f"Shot {shot_id} requires one non-empty Sound block."
            ))
        if len(exit_matches) != 1 or not (
            exit_matches and exit_matches[0].group("text").strip()
        ):
            issues.append(Issue(
                "exit_block", f"Shot {shot_id} requires one non-empty Exit block."
            ))
        _scan_executable_language(shot_block, f"Shot {shot_id}", issues)

    # Scene Blueprint and Sound Baseline are also executable context. Scan the
    # pre-shot portion rather than limiting language checks to Image blocks.
    scene_prefix = text[:shot_matches[0].start()] if shot_matches else text
    _scan_executable_language(scene_prefix, "Scene context", issues)
    return issues


def _scan_executable_language(text: str, scope: str, issues: list[Issue]) -> None:
    for term in NEGATIVE_TERMS:
        if term in text:
            issues.append(Issue(
                "negative_language",
                f"{scope} contains negative instruction '{term}'. Rewrite as a positive visible instruction.",
            ))
    action_match = NEGATIVE_ACTION.search(text)
    if action_match:
        issues.append(Issue(
            "negative_language",
            f"{scope} contains negative action '{action_match.group(0)}'. State the visible positive condition.",
        ))
    english_negative = ENGLISH_NEGATIVE.search(text)
    if english_negative:
        issues.append(Issue(
            "negative_language",
            f"{scope} contains English negative instruction '{english_negative.group(0)}'.",
        ))
    for term in UNCERTAIN_TERMS:
        if term in text:
            issues.append(Issue(
                "unresolved_branch",
                f"{scope} contains unresolved branch term '{term}'. Director must choose one executable result.",
            ))
    # A standalone Chinese '或' also presents alternatives. Longer words above
    # are reported once and removed before this high-confidence remainder check.
    without_longer_or = text.replace("或者", "").replace("或许", "")
    if "或" in without_longer_or:
        issues.append(Issue(
            "unresolved_branch",
            f"{scope} contains '或'. Director must replace alternatives with one decision.",
        ))
    slash_branch = _SLASH_BRANCH_RE.search(text)
    if slash_branch:
        issues.append(Issue(
            "unresolved_branch",
            f"{scope} contains slash-branch '{slash_branch.group(0)}'. Director must choose one result.",
        ))
    english_uncertain = ENGLISH_UNCERTAIN.search(text)
    if english_uncertain:
        issues.append(Issue(
            "unresolved_branch",
            f"{scope} contains English branch term '{english_uncertain.group(0)}'.",
        ))
    for term in NON_VISIBLE_TERMS:
        if term in text:
            issues.append(Issue(
                "non_visible_language",
                f"{scope} contains non-visible expression '{term}'. Translate it into observable action or image state.",
            ))


def main() -> int:
    parser = argparse.ArgumentParser(description="Check MODE:P video prompts against minimal SD2.0 boundaries.")
    parser.add_argument("prompt", type=Path, help="Path to VIDEO_PROMPT markdown")
    args = parser.parse_args()

    try:
        text = args.prompt.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = args.prompt.read_text(encoding="gbk")
    except OSError as exc:
        print(f"Cannot read prompt: {exc}", file=sys.stderr)
        return 2

    text = text.lstrip("\ufeff")
    issues = scan_prompt(text)
    if not issues:
        print("SD2.0 preflight passed.")
        return 0

    for issue in issues:
        print(f"{issue.kind}: {issue.message}")
    return 1



if __name__ == "__main__":
    raise SystemExit(main())
