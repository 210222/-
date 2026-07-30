"""Knowledge Curator — non-runtime tool for curating MODE:P experience knowledge.

The Knowledge Curator extracts, organizes, and promotes experience candidates
from external render evidence. It is a NON-RUNTIME tool: it does not call
the rendering engine, and is not part of the critical Director/DP pipeline.

Usage:
    python -m knowledge_curator ingest <render_case_id>
    python -m knowledge_curator curate [--candidate-id <id>]
    python -m knowledge_curator list [--status <status>]
    python -m knowledge_curator review <candidate_id>
    python -m knowledge_curator export --format json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from render_evidence import (
    EXPERIENCE_DIR,
    RenderEvidence,
    UserObservation,
    ExperienceCandidate,
    load_render_case,
    save_candidate,
    load_candidate,
    list_candidates,
    promote_candidate,
    validate_candidate,
    validate_candidate_evidence,
)


def _generate_candidate_id(title: str, evidence_ids: list[str]) -> str:
    """Generate a stable candidate ID from title and evidence."""
    seed = f"{title}|{'|'.join(sorted(evidence_ids))}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]


def ingest_render_case(evidence_id: str, base_dir: Path | None = None
                       ) -> ExperienceCandidate | None:
    """Ingest one render case and produce a candidate experience.

    Returns None if no actionable observations exist, or a new candidate.
    """
    if base_dir is None:
        base_dir = EXPERIENCE_DIR

    try:
        evidence, observations = load_render_case(evidence_id, base_dir)
    except FileNotFoundError:
        return None

    if not observations:
        return None

    # Collect actionable observations
    actionable = [o for o in observations if o.confidence in ("high", "medium")]
    if not actionable:
        return None

    # Synthesize a candidate from observations
    what_worked = "; ".join(
        o.what_worked for o in actionable if o.what_worked
    ) or "No positive findings recorded"
    what_failed = "; ".join(
        o.what_failed for o in actionable if o.what_failed
    ) or "No failures recorded"

    title = (
        f"[{evidence.generation_mode}] "
        f"{what_failed[:80] if what_failed != 'No failures recorded' else what_worked[:80]}"
    )

    candidate = ExperienceCandidate(
        candidate_id=_generate_candidate_id(title, [evidence_id]),
        title=title,
        description=(
            f"Scene: {evidence.scene_id}, Shots: {', '.join(evidence.shot_ids)}. "
            f"Mode: {evidence.generation_mode}. "
            f"Worked: {what_worked}. Failed: {what_failed}."
        ),
        evidence_ids=[evidence_id],
        observation_ids=[o.observation_id for o in actionable],
        applicability=(
            f"{evidence.generation_mode} mode with "
            f"{', '.join(evidence.reference_assets) if evidence.reference_assets else 'no references'}"
        ),
        non_applicability="",
        invariants=[f"generation_mode={evidence.generation_mode}"],
        variables=["prompt_details", "reference_asset_count"],
        generation_mode=evidence.generation_mode,
        reference_pattern=",".join(
            f"{a}:identity" for a in evidence.reference_assets
        ),
        master_version=evidence.master_version,
        asset_versions=dict(evidence.asset_versions),
        status="candidate",
    )

    save_candidate(candidate, base_dir)
    return candidate


def curate_candidates(base_dir: Path | None = None) -> dict[str, Any]:
    """Review all candidates and suggest promotions based on evidence rules.

    Rules:
    - candidate -> repeated: at least 2 independent evidence_ids
    - candidate -> rejected: no evidence, or single low-confidence observation
    """
    if base_dir is None:
        base_dir = EXPERIENCE_DIR

    result = {
        "candidates_reviewed": 0,
        "promoted_to_repeated": [],
        "suggested_rejection": [],
        "needs_more_evidence": [],
    }

    for cid in list_candidates("candidate", base_dir):
        cand = load_candidate(cid, base_dir)
        if cand is None:
            continue
        result["candidates_reviewed"] += 1

        unique_evidence = set(cand.evidence_ids)
        unique_obs = set(cand.observation_ids)
        evidence_errors, _scene_ids = validate_candidate_evidence(cand, base_dir)

        if len(unique_evidence) < 1 or evidence_errors:
            result["suggested_rejection"].append({
                "candidate_id": cid,
                "reason": (
                    "No real render evidence attached"
                    if len(unique_evidence) < 1
                    else "; ".join(evidence_errors)
                ),
            })
        elif len(unique_evidence) >= 2 and len(unique_obs) >= 2:
            # Has multiple independent evidence sources
            result["promoted_to_repeated"].append({
                "candidate_id": cid,
                "evidence_count": len(unique_evidence),
                "observation_count": len(unique_obs),
            })
        else:
            result["needs_more_evidence"].append({
                "candidate_id": cid,
                "evidence_count": len(unique_evidence),
                "observation_count": len(unique_obs),
            })

    return result


def export_knowledge(base_dir: Path | None = None,
                     status: str = "validated") -> list[dict[str, Any]]:
    """Export validated knowledge for integration into knowledge_index.json."""
    if base_dir is None:
        base_dir = EXPERIENCE_DIR

    exported: list[dict[str, Any]] = []
    for cid in list_candidates(status, base_dir):
        cand = load_candidate(cid, base_dir)
        if cand is None:
            continue
        errors = validate_candidate(cand)
        evidence_errors, scene_ids = validate_candidate_evidence(cand, base_dir)
        if cand.status == "validated" and len(scene_ids) < 2:
            evidence_errors.append(
                "validated knowledge requires evidence from at least two different scenes"
            )
        if errors or evidence_errors:
            raise ValueError(
                f"Cannot export invalid knowledge candidate {cid}: "
                + "; ".join(errors + evidence_errors)
            )
        exported.append({
            "candidate_id": cand.candidate_id,
            "title": cand.title,
            "description": cand.description,
            "applicability": cand.applicability,
            "non_applicability": cand.non_applicability,
            "invariants": cand.invariants,
            "variables": cand.variables,
            "generation_mode": cand.generation_mode,
            "reference_pattern": cand.reference_pattern,
            "evidence_count": len(cand.evidence_ids),
            "status": cand.status,
            "updated_at": cand.updated_at,
        })

    return exported


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Knowledge Curator — curate MODE:P experience from external renders."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ingest
    ingest_p = sub.add_parser("ingest", help="Ingest a render case into a candidate")
    ingest_p.add_argument("evidence_id", help="Render case evidence ID")

    # curate
    sub.add_parser("curate", help="Review candidates and suggest promotions")

    # list
    list_p = sub.add_parser("list", help="List candidates")
    list_p.add_argument("--status", default="candidate",
                        choices=("candidate", "repeated", "validated", "rejected"))

    # review
    review_p = sub.add_parser("review", help="Review a specific candidate")
    review_p.add_argument("candidate_id")

    # export
    export_p = sub.add_parser("export", help="Export validated knowledge")
    export_p.add_argument("--format", default="json", choices=("json",))
    export_p.add_argument("--status", default="validated")

    args = parser.parse_args()

    if args.command == "ingest":
        try:
            candidate = ingest_render_case(args.evidence_id)
            if candidate is None:
                print(f"No actionable observations in render case {args.evidence_id}")
                return 1
            print(f"Created candidate: {candidate.candidate_id}")
            print(f"  Title: {candidate.title}")
            print(f"  Evidence: {candidate.evidence_ids}")
            print(f"  Observations: {candidate.observation_ids}")
            return 0
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return 1

    if args.command == "curate":
        result = curate_candidates()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "list":
        ids = list_candidates(args.status)
        if ids:
            for cid in ids:
                cand = load_candidate(cid)
                status_line = f"  [{cand.status}] {cid}: {cand.title[:100]}" if cand else f"  {cid}"
                print(status_line)
        else:
            print(f"(no {args.status} candidates)")
        return 0

    if args.command == "review":
        cand = load_candidate(args.candidate_id)
        if cand is None:
            print(f"Candidate not found: {args.candidate_id}")
            return 1
        errors = validate_candidate(cand)
        if errors:
            print(f"VALIDATION ERRORS:")
            for e in errors:
                print(f"  - {e}")
        print(f"ID: {cand.candidate_id}")
        print(f"Status: {cand.status}")
        print(f"Title: {cand.title}")
        print(f"Description: {cand.description}")
        print(f"Applicability: {cand.applicability}")
        print(f"Non-applicability: {cand.non_applicability}")
        print(f"Invariants: {cand.invariants}")
        print(f"Variables: {cand.variables}")
        print(f"Evidence IDs: {cand.evidence_ids}")
        print(f"Observation IDs: {cand.observation_ids}")
        print(f"Generation Mode: {cand.generation_mode}")
        print(f"Reference Pattern: {cand.reference_pattern}")
        print(f"Created: {cand.created_at}")
        print(f"Updated: {cand.updated_at}")
        return 0

    if args.command == "export":
        data = export_knowledge(status=args.status)
        if args.format == "json":
            print(json.dumps({
                "schema_version": "1.0",
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "status": args.status,
                "count": len(data),
                "entries": data,
            }, ensure_ascii=False, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
