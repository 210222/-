"""Register and select text-only visual evidence bound to indexed media hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from asset_indexer import AssetIndexError, load_asset_index_metadata


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_ASSET_INDEX = _PROJECT_ROOT / "ASSET_INDEX.json"
_DEFAULT_CARD_INDEX = _PROJECT_ROOT / "ASSET_CARD_INDEX.json"
VALID_STATUSES = {"verified", "unverified", "stale"}
VALID_SOURCES = {"user_description", "detailed_analysis", "confirmed_spec"}
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_ENTRY_FIELDS = {
    "asset_id", "media_sha256", "card_sha256", "status", "source",
    "card_path", "scope_terms", "allowed_responsibilities",
}


class AssetCardError(ValueError):
    """Raised when a text asset card is missing, stale, or not source-bound."""


def _hash_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _portable_path(index_path: Path, raw: Any) -> Path:
    if not isinstance(raw, str) or not raw or "\\" in raw:
        raise AssetCardError("card_path must be a portable relative path")
    portable = PurePosixPath(raw)
    if portable.is_absolute() or ".." in portable.parts:
        raise AssetCardError("card_path must stay beneath the card index")
    resolved = (index_path.parent / Path(*portable.parts)).resolve()
    try:
        resolved.relative_to(index_path.parent.resolve())
    except ValueError as exc:
        raise AssetCardError("card_path escapes the card index root") from exc
    return resolved


def _validate_index(data: Any, index_path: Path, *, verify_cards: bool) -> list[str]:
    issues: list[str] = []
    required = {"schema_version", "description", "updated_at", "card_count", "cards"}
    if not isinstance(data, dict) or set(data) != required:
        return [f"card index fields must be exactly {sorted(required)}"]
    if data["schema_version"] != "1.0":
        issues.append("schema_version must be 1.0")
    if not isinstance(data["description"], str) or not data["description"].strip():
        issues.append("description must be a non-empty string")
    try:
        datetime.fromisoformat(data["updated_at"])
    except (TypeError, ValueError):
        issues.append("updated_at must be ISO-8601")
    cards = data["cards"]
    if not isinstance(cards, list):
        return issues + ["cards must be an array"]
    if data["card_count"] != len(cards):
        issues.append("card_count does not match cards length")
    seen: set[str] = set()
    for number, card in enumerate(cards, 1):
        label = f"cards[{number}]"
        if not isinstance(card, dict) or set(card) != _ENTRY_FIELDS:
            issues.append(f"{label} fields must be exactly {sorted(_ENTRY_FIELDS)}")
            continue
        asset_id = card["asset_id"]
        if not isinstance(asset_id, str) or not asset_id:
            issues.append(f"{label}.asset_id is invalid")
        elif asset_id in seen:
            issues.append(f"duplicate asset_id: {asset_id}")
        seen.add(asset_id)
        for field in ("media_sha256", "card_sha256"):
            if not isinstance(card[field], str) or not _HASH_RE.fullmatch(card[field]):
                issues.append(f"{label}.{field} is invalid")
        if card["status"] not in VALID_STATUSES:
            issues.append(f"{label}.status is invalid")
        if card["source"] not in VALID_SOURCES:
            issues.append(f"{label}.source is invalid")
        for field in ("scope_terms", "allowed_responsibilities"):
            values = card[field]
            if (
                not isinstance(values, list)
                or any(not isinstance(value, str) or not value.strip() for value in values)
                or len(values) != len(set(values))
            ):
                issues.append(f"{label}.{field} must contain unique non-empty strings")
        try:
            card_path = _portable_path(index_path, card["card_path"])
            if verify_cards:
                if not card_path.is_file():
                    issues.append(f"{label}.card_path is missing")
                elif _hash_bytes(card_path.read_bytes()) != card["card_sha256"]:
                    issues.append(f"{label}.card_sha256 does not match the card body")
        except AssetCardError as exc:
            issues.append(str(exc))
    return issues


def load_card_index_metadata(index_path: Path = _DEFAULT_CARD_INDEX) -> dict[str, Any]:
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AssetCardError(f"cannot read asset card index: {exc}") from exc
    issues = _validate_index(data, index_path, verify_cards=False)
    if issues:
        raise AssetCardError("; ".join(issues))
    return data


def load_card_index(index_path: Path = _DEFAULT_CARD_INDEX) -> dict[str, Any]:
    data = load_card_index_metadata(index_path)
    issues = _validate_index(data, index_path, verify_cards=True)
    if issues:
        raise AssetCardError("; ".join(issues))
    return data


def _asset_map(asset_index_path: Path) -> dict[str, dict[str, Any]]:
    try:
        assets = load_asset_index_metadata(asset_index_path)["assets"]
    except AssetIndexError as exc:
        raise AssetCardError(str(exc)) from exc
    return {asset["asset_id"]: asset for asset in assets}


def register_card(
    asset_id: str,
    source_markdown: Path,
    *,
    source: str,
    scope_terms: list[str],
    allowed_responsibilities: list[str],
    status: str = "verified",
    asset_index_path: Path = _DEFAULT_ASSET_INDEX,
    card_index_path: Path = _DEFAULT_CARD_INDEX,
) -> dict[str, Any]:
    if source not in VALID_SOURCES:
        raise AssetCardError(f"invalid source: {source}")
    if status not in {"verified", "unverified"}:
        raise AssetCardError("new cards may be verified or unverified")
    assets = _asset_map(asset_index_path)
    asset = assets.get(asset_id)
    if asset is None:
        raise AssetCardError(f"unknown asset_id: {asset_id}")
    if status == "verified" and asset["status"] != "available":
        raise AssetCardError("a verified card requires an available indexed media asset")
    try:
        source_text = source_markdown.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as exc:
        raise AssetCardError(f"cannot read card source: {exc}") from exc
    if not source_text:
        raise AssetCardError("card source cannot be empty")
    scope_terms = list(dict.fromkeys(term.strip() for term in scope_terms if term.strip()))
    allowed_responsibilities = list(dict.fromkeys(
        item.strip() for item in allowed_responsibilities if item.strip()
    ))
    if not scope_terms or not allowed_responsibilities:
        raise AssetCardError("scope terms and allowed responsibilities cannot be empty")

    body = "\n".join([
        f"# Asset Card: {asset_id}",
        "",
        f"Status: {status}",
        f"Source: {source}",
        f"Media SHA-256: {asset['content_sha256']}",
        "Allowed responsibilities: " + ", ".join(allowed_responsibilities),
        "Scope terms: " + ", ".join(scope_terms),
        "",
        "## Verified Visual Evidence" if status == "verified" else "## Unverified Visual Notes",
        "",
        source_text,
        "",
    ])
    card_relative = PurePosixPath("asset_cards") / f"{asset_id}.md"
    card_path = _portable_path(card_index_path, card_relative.as_posix())
    card_path.parent.mkdir(parents=True, exist_ok=True)
    card_path.write_bytes(body.encode("utf-8"))
    entry = {
        "asset_id": asset_id,
        "media_sha256": asset["content_sha256"],
        "card_sha256": _hash_bytes(body.encode("utf-8")),
        "status": status,
        "source": source,
        "card_path": card_relative.as_posix(),
        "scope_terms": scope_terms,
        "allowed_responsibilities": allowed_responsibilities,
    }
    data = load_card_index_metadata(card_index_path)
    cards = [card for card in data["cards"] if card["asset_id"] != asset_id]
    cards.append(entry)
    data["cards"] = sorted(cards, key=lambda item: item["asset_id"])
    data["card_count"] = len(cards)
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    _atomic_json(card_index_path, data)
    load_card_index(card_index_path)
    return entry


def refresh_staleness(
    card_index_path: Path = _DEFAULT_CARD_INDEX,
    asset_index_path: Path = _DEFAULT_ASSET_INDEX,
) -> dict[str, Any]:
    data = load_card_index(card_index_path)
    assets = _asset_map(asset_index_path)
    changed = False
    for card in data["cards"]:
        asset = assets.get(card["asset_id"])
        stale = (
            asset is None
            or asset["status"] != "available"
            or asset["content_sha256"] != card["media_sha256"]
        )
        if stale and card["status"] == "verified":
            card["status"] = "stale"
            changed = True
    if changed:
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        _atomic_json(card_index_path, data)
    return data


def _model_card_text(path: Path) -> str:
    """Remove local provenance fields that do not help a creative/review model."""
    return "\n".join(
        line for line in path.read_text(encoding="utf-8").splitlines()
        if not line.startswith(("Media SHA-256:", "Status:"))
    ).strip()


def select_verified_cards(
    references: list[dict[str, str]],
    *,
    card_index_path: Path = _DEFAULT_CARD_INDEX,
    asset_index_path: Path = _DEFAULT_ASSET_INDEX,
    max_chars: int = 6000,
) -> str:
    if max_chars < 1:
        raise AssetCardError("max_chars must be positive")
    if not references:
        return ""
    data = refresh_staleness(card_index_path, asset_index_path)
    cards = {card["asset_id"]: card for card in data["cards"]}
    blocks: list[str] = []
    used = 0
    for reference in references:
        asset_id = reference["asset_id"]
        responsibility = reference["responsibility"]
        card = cards.get(asset_id)
        if card is None or card["status"] != "verified":
            raise AssetCardError(f"reference '{asset_id}' lacks a current verified text card")
        if responsibility not in card["allowed_responsibilities"]:
            raise AssetCardError(
                f"reference '{asset_id}' card does not allow responsibility '{responsibility}'"
            )
        text = _model_card_text(_portable_path(card_index_path, card["card_path"]))
        block = f"## {asset_id}|{responsibility}\n\n{text}\n"
        if used + len(block) > max_chars:
            raise AssetCardError(
                f"selected asset cards exceed the {max_chars}-character context budget"
            )
        blocks.append(block)
        used += len(block)
    return "\n".join(blocks).strip() + "\n"


def select_relevant_cards(
    context_text: str,
    *,
    card_index_path: Path = _DEFAULT_CARD_INDEX,
    asset_index_path: Path = _DEFAULT_ASSET_INDEX,
    max_chars: int = 6000,
) -> str:
    """Select verified candidate cards by deterministic scope-term matches."""
    if not context_text.strip():
        return ""
    if not 1 <= max_chars <= 10000:
        raise AssetCardError("Director card budget must be between 1 and 10000 characters")
    data = refresh_staleness(card_index_path, asset_index_path)
    folded = context_text.casefold()
    ranked: list[tuple[int, str, dict[str, Any]]] = []
    for card in data["cards"]:
        if card["status"] != "verified":
            continue
        score = sum(folded.count(term.casefold()) for term in card["scope_terms"])
        if score:
            ranked.append((-score, card["asset_id"], card))
    blocks: list[str] = []
    used = 0
    for _, asset_id, card in sorted(ranked):
        text = _model_card_text(_portable_path(card_index_path, card["card_path"]))
        responsibilities = ", ".join(card["allowed_responsibilities"])
        block = (
            f"## Candidate {asset_id}\n\n"
            f"Permitted responsibilities: {responsibilities}\n\n{text}\n"
        )
        if used + len(block) > max_chars:
            continue
        blocks.append(block)
        used += len(block)
    return "\n".join(blocks).strip() + ("\n" if blocks else "")


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage MODE:P text asset cards.")
    sub = parser.add_subparsers(dest="command", required=True)
    register = sub.add_parser("register")
    register.add_argument("asset_id")
    register.add_argument("source_markdown", type=Path)
    register.add_argument("--source", choices=sorted(VALID_SOURCES), required=True)
    register.add_argument("--scope", action="append", required=True)
    register.add_argument("--responsibility", action="append", required=True)
    register.add_argument("--status", choices=["verified", "unverified"], default="verified")
    register.add_argument("--assets", type=Path, default=_DEFAULT_ASSET_INDEX)
    register.add_argument("--cards", type=Path, default=_DEFAULT_CARD_INDEX)
    validate = sub.add_parser("validate")
    validate.add_argument("--assets", type=Path, default=_DEFAULT_ASSET_INDEX)
    validate.add_argument("--cards", type=Path, default=_DEFAULT_CARD_INDEX)
    match = sub.add_parser("match")
    match.add_argument("context", type=Path)
    match.add_argument("--assets", type=Path, default=_DEFAULT_ASSET_INDEX)
    match.add_argument("--cards", type=Path, default=_DEFAULT_CARD_INDEX)
    match.add_argument("--budget", type=int, default=6000)
    match.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "register":
            entry = register_card(
                args.asset_id, args.source_markdown, source=args.source,
                scope_terms=args.scope, allowed_responsibilities=args.responsibility,
                status=args.status, asset_index_path=args.assets,
                card_index_path=args.cards,
            )
            print(f"Asset card registered: {entry['asset_id']} ({entry['status']})")
        elif args.command == "validate":
            data = refresh_staleness(args.cards, args.assets)
            print(f"Asset cards valid: {data['card_count']}")
        else:
            context = args.context.read_text(encoding="utf-8")
            selected = select_relevant_cards(
                context,
                card_index_path=args.cards,
                asset_index_path=args.assets,
                max_chars=args.budget,
            )
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(selected, encoding="utf-8")
                print(f"Relevant asset cards -> {args.output}")
            else:
                print(selected, end="")
        return 0
    except AssetCardError as exc:
        print(f"Asset card error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
