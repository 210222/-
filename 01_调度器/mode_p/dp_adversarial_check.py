"""Validate fixed adversarial DP evidence without judging creative quality."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dp_contract import parse_dp_feedback, validate_dp_contract


VALID_SHOTS = {"ADV_S1-1", "ADV_S1-2"}
CATEGORY_FIELDS = {
    "camera_path": {"camera_path", "spatial_feasibility"},
    "light_source": {"light_source"},
    "shared_boundary": {"boundary_continuity", "action_continuity"},
    "view_sync": {"view_sync"},
}
_PROMPT_BRANCH_TERMS = (
    "未裁决", "分支", "如空间允许", "unresolved branch",
    "if space permits", "generator must choose", "生成模型须", "自行猜测",
)


def validate_adversarial_response(text: str) -> list[str]:
    feedback = parse_dp_feedback(text)
    valid, problems = validate_dp_contract(feedback, VALID_SHOTS)
    if not valid:
        return problems
    if feedback.status != "issues":
        return ["adversarial DP must return issues, not READY or blocked"]
    observed = {issue.field for issue in feedback.issues}
    missing = [
        category
        for category, accepted_fields in CATEGORY_FIELDS.items()
        if observed.isdisjoint(accepted_fields)
    ]
    if not any(
        issue.field == "prompt_visibility"
        or any(term in issue.detail.casefold() for term in _PROMPT_BRANCH_TERMS)
        for issue in feedback.issues
    ):
        missing.append("prompt_branch")
    if missing:
        return ["missing adversarial review categories: " + ", ".join(missing)]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("response", type=Path)
    args = parser.parse_args(argv)
    try:
        text = args.response.read_text(encoding="utf-8").lstrip("\ufeff")
    except (OSError, UnicodeError) as exc:
        print(f"Cannot read DP response: {exc}", file=sys.stderr)
        return 2
    problems = validate_adversarial_response(text)
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        return 1
    print("PASS: adversarial DP identified all five required review categories.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
