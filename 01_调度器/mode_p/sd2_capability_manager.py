"""Strict validation and hashing for the versioned SD2 capability profile."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


_DEFAULT_PROFILE = Path(__file__).with_name("sd2_capability_profile.json")
_MODES = {"text_only", "first_last_frame", "omni_reference"}
_MEDIA_TYPES = {"image", "video", "audio"}
_ENFORCEMENT = {"hard", "advisory", "informational"}
_EVIDENCE_KINDS = {
    "official_product_page", "official_public_ui", "official_model_release",
    "official_technical_report", "user_requirement",
}
_TOP_FIELDS = {
    "schema_version", "profile_id", "description", "product", "evidence",
    "mode_contract", "model_capabilities", "modes", "project_policies",
    "quality_heuristics", "unknown_limits",
}


class CapabilityProfileError(ValueError):
    """Raised when a profile cannot safely drive deterministic checks."""


def get_hash(profile_path: Path = _DEFAULT_PROFILE) -> str:
    return hashlib.sha256(profile_path.read_bytes()).hexdigest()


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_evidence(data: dict[str, Any], issues: list[str]) -> set[str]:
    evidence = data.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        issues.append("evidence must be a non-empty array")
        return set()
    ids: list[str] = []
    for number, item in enumerate(evidence, 1):
        label = f"evidence[{number}]"
        if not isinstance(item, dict) or set(item) != {
            "evidence_id", "kind", "url", "claims"
        }:
            issues.append(f"{label} has an invalid shape")
            continue
        if not _nonempty_string(item["evidence_id"]):
            issues.append(f"{label}.evidence_id is invalid")
        else:
            ids.append(item["evidence_id"])
        if item["kind"] not in _EVIDENCE_KINDS:
            issues.append(f"{label}.kind is invalid")
        url = item["url"]
        if item["kind"] == "user_requirement":
            if url is not None:
                issues.append(f"{label}.url must be null for user requirements")
        elif not isinstance(url, str) or urlparse(url).scheme != "https":
            issues.append(f"{label}.url must be an HTTPS source")
        claims = item["claims"]
        if (
            not isinstance(claims, list) or not claims
            or any(not _nonempty_string(claim) for claim in claims)
            or len(claims) != len(set(claims))
        ):
            issues.append(f"{label}.claims must be unique non-empty strings")
    if len(ids) != len(set(ids)):
        issues.append("evidence_id values must be unique")
    return set(ids)


def _evidence_refs(
    value: Any, label: str, evidence_ids: set[str], issues: list[str]
) -> None:
    if (
        not isinstance(value, list) or not value
        or any(item not in evidence_ids for item in value)
        or len(value) != len(set(value))
    ):
        issues.append(f"{label}.evidence_ids must reference known evidence")


def validate_data(data: Any) -> list[str]:
    issues: list[str] = []
    if not isinstance(data, dict):
        return ["profile root must be an object"]
    if set(data) != _TOP_FIELDS:
        issues.append(f"top-level fields must be exactly {sorted(_TOP_FIELDS)}")
    if data.get("schema_version") != "2.0":
        issues.append("schema_version must be 2.0")
    if not _nonempty_string(data.get("profile_id")):
        issues.append("profile_id must be a non-empty string")
    if not _nonempty_string(data.get("description")):
        issues.append("description must be a non-empty string")

    product = data.get("product")
    if not isinstance(product, dict) or set(product) != {
        "platform", "model", "surface", "observed_at", "mode_selection_owner"
    }:
        issues.append("product has an invalid shape")
    else:
        for field in ("platform", "model", "surface"):
            if not _nonempty_string(product[field]):
                issues.append(f"product.{field} must be a non-empty string")
        try:
            datetime.fromisoformat(product["observed_at"])
        except (TypeError, ValueError):
            issues.append("product.observed_at must be ISO-8601")
        if product["mode_selection_owner"] != "director":
            issues.append("product.mode_selection_owner must be director")

    evidence_ids = _validate_evidence(data, issues)
    contract = data.get("mode_contract")
    if contract != {"selection": "exactly_one_per_shot", "enforcement": "hard"}:
        issues.append("mode_contract must enforce exactly one Director-selected mode")

    capabilities = data.get("model_capabilities")
    if not isinstance(capabilities, dict) or set(capabilities) != {
        "generation_duration_s", "native_output_resolutions",
        "multimodal_reference_limits",
    }:
        issues.append("model_capabilities has an invalid shape")
    else:
        duration_cap = capabilities["generation_duration_s"]
        if not isinstance(duration_cap, dict) or set(duration_cap) != {
            "min", "max", "enforcement", "evidence_ids"
        }:
            issues.append("model_capabilities.generation_duration_s has an invalid shape")
        else:
            minimum, maximum = duration_cap["min"], duration_cap["max"]
            if (
                isinstance(minimum, bool) or not isinstance(minimum, (int, float))
                or isinstance(maximum, bool) or not isinstance(maximum, (int, float))
                or minimum <= 0 or maximum < minimum
                or duration_cap["enforcement"] not in _ENFORCEMENT
            ):
                issues.append("model_capabilities.generation_duration_s is invalid")
            _evidence_refs(
                duration_cap["evidence_ids"],
                "model_capabilities.generation_duration_s",
                evidence_ids,
                issues,
            )
        resolutions = capabilities["native_output_resolutions"]
        if not isinstance(resolutions, dict) or set(resolutions) != {
            "values", "enforcement", "evidence_ids"
        }:
            issues.append("model_capabilities.native_output_resolutions has an invalid shape")
        else:
            values = resolutions["values"]
            if (
                not isinstance(values, list) or not values
                or any(not _nonempty_string(item) for item in values)
                or len(values) != len(set(values))
                or resolutions["enforcement"] not in _ENFORCEMENT
            ):
                issues.append("model_capabilities.native_output_resolutions is invalid")
            _evidence_refs(
                resolutions["evidence_ids"],
                "model_capabilities.native_output_resolutions",
                evidence_ids,
                issues,
            )
        reference_limits = capabilities["multimodal_reference_limits"]
        if not isinstance(reference_limits, dict) or set(reference_limits) != {
            "image", "video", "audio", "canvas_total", "enforcement", "evidence_ids"
        }:
            issues.append("model_capabilities.multimodal_reference_limits has an invalid shape")
        else:
            counts = [reference_limits[name] for name in ("image", "video", "audio", "canvas_total")]
            if (
                any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in counts)
                or reference_limits["canvas_total"] <= 0
                or reference_limits["enforcement"] not in _ENFORCEMENT
            ):
                issues.append("model_capabilities.multimodal_reference_limits is invalid")
            _evidence_refs(
                reference_limits["evidence_ids"],
                "model_capabilities.multimodal_reference_limits",
                evidence_ids,
                issues,
            )

    modes = data.get("modes")
    if not isinstance(modes, dict) or set(modes) != _MODES:
        issues.append(f"modes must be exactly {sorted(_MODES)}")
    else:
        for name, mode in modes.items():
            label = f"modes.{name}"
            if not isinstance(mode, dict) or set(mode) != {
                "description", "availability", "asset_count",
                "allowed_media_types", "required_responsibilities",
            }:
                issues.append(f"{label} has an invalid shape")
                continue
            if not _nonempty_string(mode["description"]):
                issues.append(f"{label}.description is invalid")
            availability = mode["availability"]
            if not isinstance(availability, dict) or set(availability) != {
                "status", "evidence_ids"
            } or availability.get("status") not in {"verified", "provisional"}:
                issues.append(f"{label}.availability is invalid")
            else:
                _evidence_refs(availability["evidence_ids"], f"{label}.availability", evidence_ids, issues)

            count = mode["asset_count"]
            if not isinstance(count, dict) or set(count) != {
                "min", "max", "enforcement", "evidence_ids"
            }:
                issues.append(f"{label}.asset_count has an invalid shape")
            else:
                minimum, maximum = count["min"], count["max"]
                if (
                    isinstance(minimum, bool) or not isinstance(minimum, int) or minimum < 0
                    or isinstance(maximum, bool) or not isinstance(maximum, int)
                    or maximum < minimum
                    or count["enforcement"] not in _ENFORCEMENT
                ):
                    issues.append(f"{label}.asset_count is invalid")
                _evidence_refs(count["evidence_ids"], f"{label}.asset_count", evidence_ids, issues)

            media = mode["allowed_media_types"]
            if not isinstance(media, dict) or set(media) != {
                "values", "enforcement", "evidence_ids"
            }:
                issues.append(f"{label}.allowed_media_types has an invalid shape")
            else:
                values = media["values"]
                if (
                    not isinstance(values, list)
                    or any(item not in _MEDIA_TYPES for item in values)
                    or len(values) != len(set(values))
                    or media["enforcement"] not in _ENFORCEMENT
                ):
                    issues.append(f"{label}.allowed_media_types is invalid")
                _evidence_refs(media["evidence_ids"], f"{label}.allowed_media_types", evidence_ids, issues)
            responsibilities = mode["required_responsibilities"]
            if (
                not isinstance(responsibilities, list)
                or any(not _nonempty_string(item) for item in responsibilities)
                or len(responsibilities) != len(set(responsibilities))
            ):
                issues.append(f"{label}.required_responsibilities is invalid")

    policies = data.get("project_policies")
    duration = policies.get("max_shot_duration_s") if isinstance(policies, dict) else None
    if not isinstance(duration, dict) or set(duration) != {"value", "enforcement", "evidence_ids"}:
        issues.append("project_policies.max_shot_duration_s has an invalid shape")
    else:
        if (
            isinstance(duration["value"], bool)
            or not isinstance(duration["value"], (int, float))
            or duration["value"] <= 0
            or duration["enforcement"] != "hard"
        ):
            issues.append("project_policies.max_shot_duration_s is invalid")
        _evidence_refs(duration["evidence_ids"], "project_policies.max_shot_duration_s", evidence_ids, issues)

    heuristics = data.get("quality_heuristics")
    if not isinstance(heuristics, dict) or not heuristics:
        issues.append("quality_heuristics must be a non-empty object")
    else:
        for name, heuristic in heuristics.items():
            if not isinstance(heuristic, dict) or set(heuristic) != {"value", "enforcement", "reason"}:
                issues.append(f"quality_heuristics.{name} has an invalid shape")
            elif heuristic["enforcement"] != "advisory" or not _nonempty_string(heuristic["reason"]):
                issues.append(f"quality_heuristics.{name} must remain advisory")

    unknown = data.get("unknown_limits")
    if (
        not isinstance(unknown, list) or not unknown
        or any(not _nonempty_string(item) for item in unknown)
        or len(unknown) != len(set(unknown))
    ):
        issues.append("unknown_limits must be unique non-empty strings")
    return issues


def load_profile(profile_path: Path = _DEFAULT_PROFILE) -> dict[str, Any]:
    try:
        data = json.loads(profile_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CapabilityProfileError(f"cannot read capability profile: {exc}") from exc
    issues = validate_data(data)
    if issues:
        raise CapabilityProfileError("; ".join(issues))
    return data


def validate_profile(profile_path: Path = _DEFAULT_PROFILE) -> tuple[bool, list[str]]:
    try:
        load_profile(profile_path)
        return True, []
    except CapabilityProfileError as exc:
        return False, [str(exc)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate or hash the SD2 capability profile.")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "hash"):
        child = sub.add_parser(command)
        child.add_argument("profile", type=Path, nargs="?", default=_DEFAULT_PROFILE)
    args = parser.parse_args()
    if args.command == "validate":
        ok, issues = validate_profile(args.profile)
        if ok:
            print("Capability profile valid.")
            return 0
        for issue in issues:
            print(issue, file=sys.stderr)
        return 1
    try:
        load_profile(args.profile)
        print(get_hash(args.profile))
        return 0
    except CapabilityProfileError as exc:
        print(exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
