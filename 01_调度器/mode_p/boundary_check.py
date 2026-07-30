"""Check shot-to-shot boundary continuity from SHOT_MANIFEST.json.

This is a deterministic local checker. It verifies:
- Boundary ID chain (SCENE_ENTRY → shot_id pairs → SCENE_EXIT)
- State key continuity at each boundary (characters, props, action phase)
- Screen direction continuity

It reads only the Manifest; Master/views are checked by master_sync_check.
It MUST NOT judge semantic quality or aesthetic choices.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import jsonschema


SCHEMA_PATH = Path(__file__).with_name("shot_manifest_schema.json")
with open(SCHEMA_PATH, encoding="utf-8") as _schema_file:
    _SCHEMA = json.load(_schema_file)


@dataclass
class BoundaryIssue:
    boundary: str  # e.g. "EP14-1 → EP14-2"
    category: str  # "boundary_id", "character", "prop", "action_phase", "light", "direction"
    detail: str


@dataclass
class BoundaryReport:
    issues: list[BoundaryIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.issues) == 0


# ---------------------------------------------------------------------------
# public entry point
# ---------------------------------------------------------------------------

def check_boundaries(manifest_path: Path) -> BoundaryReport:
    """Run all boundary checks on a manifest. Returns report; report.ok iff clean."""
    report = BoundaryReport()
    try:
        manifest = _read_manifest(manifest_path)
        jsonschema.validate(manifest, _SCHEMA)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError,
            jsonschema.ValidationError) as exc:
        report.issues.append(BoundaryIssue(
            "MANIFEST", "manifest", f"Invalid SHOT_MANIFEST.json: {exc}"
        ))
        return report
    shots = manifest["shots"]

    if manifest.get("boundaries") is not None:
        _check_shared_boundaries(manifest, report)
        return report

    # 1. Boundary ID chain
    _check_boundary_id_chain(shots, report)

    # 2. Per-boundary state key continuity
    for i in range(len(shots) - 1):
        if shots[i]["boundary_continuity"] == "continuous":
            _check_state_continuity(shots[i], shots[i + 1], report)

    return report


def _check_shared_boundaries(manifest: dict, report: BoundaryReport) -> None:
    """Validate active v4 Boundary ownership and mechanical projection."""
    shots = manifest["shots"]
    boundaries = manifest.get("boundaries")
    if not isinstance(boundaries, list) or len(boundaries) != len(shots) + 1:
        report.issues.append(BoundaryIssue(
            "SCENE", "boundary_id",
            f"Expected {len(shots) + 1} shared Boundaries, got "
            f"{len(boundaries) if isinstance(boundaries, list) else 'invalid'}",
        ))
        return

    scene_id = manifest["scene_id"]
    for index, boundary in enumerate(boundaries):
        boundary_id = f"{scene_id}-B{index}"
        expected_from = "SCENE_ENTRY" if index == 0 else shots[index - 1]["shot_id"]
        expected_to = "SCENE_EXIT" if index == len(shots) else shots[index]["shot_id"]
        if boundary["boundary_id"] != boundary_id:
            report.issues.append(BoundaryIssue(
                boundary_id, "boundary_id",
                f"Expected ID '{boundary_id}', got '{boundary['boundary_id']}'",
            ))
        if boundary["from_ref"] != expected_from or boundary["to_ref"] != expected_to:
            report.issues.append(BoundaryIssue(
                boundary_id, "boundary_id",
                f"Expected {expected_from} -> {expected_to}, got "
                f"{boundary['from_ref']} -> {boundary['to_ref']}",
            ))

        relation = boundary["relation"]
        if index == 0 and relation != "scene_entry":
            report.issues.append(BoundaryIssue(
                boundary_id, "boundary_continuity", "B0 must be scene_entry",
            ))
        elif index == len(shots) and relation != "scene_exit":
            report.issues.append(BoundaryIssue(
                boundary_id, "boundary_continuity", "Final Boundary must be scene_exit",
            ))
        elif 0 < index < len(shots) and relation not in {"continuous", "elliptical"}:
            report.issues.append(BoundaryIssue(
                boundary_id, "boundary_continuity",
                "Internal Boundary must be continuous or elliptical",
            ))

        if relation == "continuous" and (
            boundary["outgoing_state_keys"] != boundary["incoming_state_keys"]
        ):
            report.issues.append(BoundaryIssue(
                boundary_id, "state",
                "Continuous shared Boundary must expose one identical state to both Shots",
            ))

    for index, shot in enumerate(shots):
        entry = boundaries[index]
        exit_ = boundaries[index + 1]
        if shot["entry_boundary_id"] != entry["boundary_id"]:
            report.issues.append(BoundaryIssue(
                shot["shot_id"], "boundary_id", "Shot entry does not reference its shared Boundary",
            ))
        if shot["exit_boundary_id"] != exit_["boundary_id"]:
            report.issues.append(BoundaryIssue(
                shot["shot_id"], "boundary_id", "Shot exit does not reference its shared Boundary",
            ))
        if shot["opening_state_keys"] != entry["incoming_state_keys"]:
            report.issues.append(BoundaryIssue(
                shot["shot_id"], "state", "Shot opening is not projected from its entry Boundary",
            ))
        if shot["closing_state_keys"] != exit_["outgoing_state_keys"]:
            report.issues.append(BoundaryIssue(
                shot["shot_id"], "state", "Shot closing is not projected from its exit Boundary",
            ))
        if shot["boundary_continuity"] != exit_["relation"]:
            report.issues.append(BoundaryIssue(
                shot["shot_id"], "boundary_continuity",
                "Shot outgoing relation is not projected from its exit Boundary",
            ))
        if shot["transition_execution"] != exit_["transition_execution"]:
            report.issues.append(BoundaryIssue(
                shot["shot_id"], "transition_execution",
                "Shot transition execution is not projected from its exit Boundary",
            ))


# ---------------------------------------------------------------------------
# boundary ID chain
# ---------------------------------------------------------------------------

def _check_boundary_id_chain(shots: list[dict], report: BoundaryReport) -> None:
    if not shots:
        return

    if shots[0]["entry_boundary_id"] != "SCENE_ENTRY":
        report.issues.append(BoundaryIssue(
            f"→ {shots[0]['shot_id']}", "boundary_id",
            f"First shot entry must be SCENE_ENTRY, got '{shots[0]['entry_boundary_id']}'",
        ))

    if shots[-1]["exit_boundary_id"] != "SCENE_EXIT":
        report.issues.append(BoundaryIssue(
            f"{shots[-1]['shot_id']} →", "boundary_id",
            f"Last shot exit must be SCENE_EXIT, got '{shots[-1]['exit_boundary_id']}'",
        ))
    if shots[-1]["boundary_continuity"] != "scene_exit":
        report.issues.append(BoundaryIssue(
            f"{shots[-1]['shot_id']} →", "boundary_continuity",
            "Last shot boundary_continuity must be 'scene_exit'",
        ))

    for i in range(len(shots) - 1):
        a, b = shots[i], shots[i + 1]
        boundary = f"{a['shot_id']} → {b['shot_id']}"

        if a["exit_boundary_id"] != b["shot_id"]:
            report.issues.append(BoundaryIssue(
                boundary, "boundary_id",
                f"Shot A exit '{a['exit_boundary_id']}' ≠ Shot B id '{b['shot_id']}'",
            ))
        if b["entry_boundary_id"] != a["shot_id"]:
            report.issues.append(BoundaryIssue(
                boundary, "boundary_id",
                f"Shot B entry '{b['entry_boundary_id']}' ≠ Shot A id '{a['shot_id']}'",
            ))
        if a["boundary_continuity"] == "scene_exit":
            report.issues.append(BoundaryIssue(
                boundary, "boundary_continuity",
                "Only the final shot may use 'scene_exit'",
            ))


# ---------------------------------------------------------------------------
# state key continuity
# ---------------------------------------------------------------------------

def _check_state_continuity(a: dict, b: dict, report: BoundaryReport) -> None:
    """Shot A's closing state should match Shot B's opening state."""
    boundary = f"{a['shot_id']} → {b['shot_id']}"
    a_close = a["closing_state_keys"]
    b_open = b["opening_state_keys"]

    # Characters
    a_chars = {c["entity_id"]: c for c in a_close["characters"]}
    b_chars = {c["entity_id"]: c for c in b_open["characters"]}

    for eid in set(a_chars.keys()) & set(b_chars.keys()):
        ac, bc = a_chars[eid], b_chars[eid]
        for attr in ["position", "facing", "posture"]:
            if ac[attr] != bc[attr]:
                report.issues.append(BoundaryIssue(
                    boundary, "character",
                    f"{eid}.{attr}: A closing '{ac[attr]}' ≠ B opening '{bc[attr]}'",
                ))

    # Check for entities in A but missing from B (and vice versa)
    only_a = set(a_chars.keys()) - set(b_chars.keys())
    for eid in only_a:
        report.issues.append(BoundaryIssue(
            boundary, "character",
            f"Entity '{eid}' present in A closing but missing from B opening",
        ))
    only_b = set(b_chars.keys()) - set(a_chars.keys())
    for eid in only_b:
        report.issues.append(BoundaryIssue(
            boundary, "character",
            f"Entity '{eid}' present in B opening but missing from A closing",
        ))

    # Props
    a_props = {p["prop_id"]: p for p in a_close["props"]}
    b_props = {p["prop_id"]: p for p in b_open["props"]}

    for pid in set(a_props.keys()) & set(b_props.keys()):
        ap, bp = a_props[pid], b_props[pid]
        for attr in ["held_by", "location"]:
            if ap[attr] != bp[attr]:
                report.issues.append(BoundaryIssue(
                    boundary, "prop",
                    f"{pid}.{attr}: A closing '{ap[attr]}' ≠ B opening '{bp[attr]}'",
                ))

    # Props newly appearing or disappearing are notable
    only_a_p = set(a_props.keys()) - set(b_props.keys())
    for pid in only_a_p:
        report.issues.append(BoundaryIssue(
            boundary, "prop",
            f"Prop '{pid}' present in A closing but missing from B opening",
        ))
    only_b_p = set(b_props.keys()) - set(a_props.keys())
    for pid in only_b_p:
        report.issues.append(BoundaryIssue(
            boundary, "prop",
            f"Prop '{pid}' newly introduced in B — verify intention",
        ))

    # Boundary state is instantaneous: B must start at A's exact action phase.
    a_phase = a_close["action_phase"]
    b_phase = b_open["action_phase"]
    if b_phase != a_phase:
        report.issues.append(BoundaryIssue(
            boundary, "action_phase",
            f"A closing '{a_phase}' ≠ B opening '{b_phase}'",
        ))

    # Light state is canonical boundary data; tolerances would hide a jump.
    al = a_close["light_main"]
    bl = b_open["light_main"]
    for attr in ("direction", "color_temp_k", "ratio"):
        if al[attr] != bl[attr]:
            report.issues.append(BoundaryIssue(
                boundary, "light",
                f"{attr}: A closing '{al[attr]}' ≠ B opening '{bl[attr]}'",
            ))

    # Screen movement direction is distinct from world-facing orientation.
    for eid in set(a_chars.keys()) & set(b_chars.keys()):
        ac, bc = a_chars[eid], b_chars[eid]
        if ac["screen_direction"] != bc["screen_direction"]:
            report.issues.append(BoundaryIssue(
                boundary, "direction",
                f"{eid}: A closing screen_direction '{ac['screen_direction']}' "
                f"≠ B opening '{bc['screen_direction']}'",
            ))


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _read_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check shot-to-shot boundary continuity from Manifest."
    )
    parser.add_argument("manifest", type=Path, help="Path to SHOT_MANIFEST.json")
    args = parser.parse_args()

    if not args.manifest.is_file():
        print(f"File not found: {args.manifest}", file=sys.stderr)
        return 2

    report = check_boundaries(args.manifest)

    if report.ok:
        print("Boundary check passed — all boundaries consistent.")
        return 0

    for issue in report.issues:
        print(f"[{issue.category}] {issue.boundary}: {issue.detail}")
    return 1


if __name__ == "__main__":
    from cli_stdio import configure_utf8_stdio

    configure_utf8_stdio()
    raise SystemExit(main())
