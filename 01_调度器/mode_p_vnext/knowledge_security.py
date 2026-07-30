"""Untrusted-text isolation for the MODE:P vNext knowledge boundary.

Raw scripts, dialogue, source passages, asset metadata and user corrections
are evidence *data*.  They never become executable instructions for a
Director, a retriever, or a prompt compiler.  This module intentionally keeps
the raw payload out of all runtime packets and records a blocking security
event when it resembles an instruction-injection attempt.

The detector is a guardrail, not a semantic classifier: a detected payload is
quarantined for a human decision rather than rewritten or silently accepted.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata
from typing import Dict, Iterable, List, Tuple

from mode_p_vnext.canonical_serialization import canonical_json_dumps, stable_hash_sha256


class UntrustedTextBlocked(ValueError):
    """Raised only when a caller asks to activate quarantined source text."""


@dataclass(frozen=True)
class UntrustedTextEnvelope:
    """Opaque source envelope.

    ``content`` is retained only at the ingestion boundary for human review.
    ``to_runtime_metadata`` deliberately excludes it, so runtime packets can
    cite the source without injecting its words into an instruction channel.
    """

    source_id: str
    source_kind: str
    project_id: str
    content: str
    content_sha256: str

    def to_runtime_metadata(self) -> Dict[str, str]:
        return {
            "source_id": self.source_id,
            "source_kind": self.source_kind,
            "project_id": self.project_id,
            "content_sha256": self.content_sha256,
            "role": "untrusted_data",
        }


@dataclass(frozen=True)
class KnowledgeSecurityEvent:
    """A human-review event; it contains no untrusted source text."""

    event_id: str
    category: str
    source_id: str
    project_id: str
    content_sha256: str
    reason_codes: Tuple[str, ...]
    disposition: str = "HUMAN_REVIEW_REQUIRED"

    def to_dict(self) -> Dict[str, object]:
        return {
            "event_id": self.event_id,
            "category": self.category,
            "source_id": self.source_id,
            "project_id": self.project_id,
            "content_sha256": self.content_sha256,
            "reason_codes": list(self.reason_codes),
            "disposition": self.disposition,
        }


# Normalize before matching so full-width text and visually similar spacing do
# not bypass the boundary.  The list covers instruction-taking language, not
# ordinary dramatic content.  A match quarantines, it does not edit the source.
_INJECTION_PATTERNS: Tuple[Tuple[str, str], ...] = (
    ("ignore_previous", r"\bignore\s+(?:all\s+)?(?:previous|above|prior)\s+(?:rules?|instructions?|prompts?)"),
    ("system_prompt", r"\b(?:system\s+prompt|developer\s+instruction|system\s+message)\b"),
    ("tool_call", r"\b(?:call|invoke|use)\s+(?:a\s+)?tool\b"),
    ("file_read", r"\b(?:read|open|load)\s+(?:another|other|all|the)\s+files?\b"),
    ("role_override", r"\byou\s+are\s+now\b"),
    ("zh_ignore_rules", r"忽略.{0,12}(?:之前|以上|前面)?.{0,12}(?:规则|指令|提示)"),
    ("zh_system_prompt", r"(?:系统提示|系统消息|开发者指令)"),
    ("zh_tool_call", r"(?:调用|使用).{0,8}(?:工具|tool)"),
    ("zh_file_read", r"(?:读取|打开|加载).{0,12}(?:其他|所有|全部).{0,8}文件"),
    ("zh_role_override", r"你现在是"),
)


def _normalise(text: str) -> str:
    return unicodedata.normalize("NFKC", text).lower().replace("\u200b", " ")


def _hash(value: object) -> str:
    return stable_hash_sha256(canonical_json_dumps(value).encode("utf-8"))


def envelope_untrusted_text(
    source_id: str,
    source_kind: str,
    project_id: str,
    content: str,
) -> UntrustedTextEnvelope:
    """Create a labelled, hash-addressed untrusted-data envelope."""
    if not source_id or not source_kind or not project_id:
        raise ValueError("source_id, source_kind and project_id are required")
    if not isinstance(content, str):
        raise TypeError("untrusted content must be text")
    return UntrustedTextEnvelope(
        source_id=source_id,
        source_kind=source_kind,
        project_id=project_id,
        content=content,
        content_sha256=_hash({"content": content}),
    )


def inspect_untrusted_text(envelope: UntrustedTextEnvelope) -> KnowledgeSecurityEvent | None:
    """Return a blocking event when an envelope resembles an instruction.

    The function never executes, follows, strips, or transforms the source
    content.  A clean result still remains ``untrusted_data`` and can only be
    used as evidence through its metadata/hash.
    """
    normalised = _normalise(envelope.content)
    reasons = tuple(
        code for code, pattern in _INJECTION_PATTERNS if re.search(pattern, normalised)
    )
    if not reasons:
        return None
    return KnowledgeSecurityEvent(
        event_id="SEC-" + _hash({
            "source_id": envelope.source_id,
            "project_id": envelope.project_id,
            "content_sha256": envelope.content_sha256,
            "reason_codes": reasons,
        })[:16],
        category="INPUT_OR_KNOWLEDGE_INSTRUCTION_CONTAMINATION",
        source_id=envelope.source_id,
        project_id=envelope.project_id,
        content_sha256=envelope.content_sha256,
        reason_codes=reasons,
    )


def inspect_envelopes(envelopes: Iterable[UntrustedTextEnvelope]) -> List[KnowledgeSecurityEvent]:
    """Inspect many source envelopes without exposing their raw contents."""
    return [event for item in envelopes if (event := inspect_untrusted_text(item))]


def assert_untrusted_text_safe(
    source_id: str,
    source_kind: str,
    project_id: str,
    content: str,
) -> UntrustedTextEnvelope:
    """Return an envelope for clean data or fail closed without echoing content."""
    envelope = envelope_untrusted_text(source_id, source_kind, project_id, content)
    event = inspect_untrusted_text(envelope)
    if event is not None:
        raise UntrustedTextBlocked(
            "untrusted text quarantined: "
            f"source_id={event.source_id}; project_id={event.project_id}; "
            f"content_sha256={event.content_sha256}; "
            f"reason_codes={','.join(event.reason_codes)}"
        )
    return envelope


def assert_envelope_project(envelope: UntrustedTextEnvelope, project_id: str) -> None:
    """Block cross-project source reuse before it reaches a retrieval packet."""
    if envelope.project_id != project_id:
        raise UntrustedTextBlocked(
            f"untrusted source '{envelope.source_id}' belongs to project "
            f"'{envelope.project_id}', not '{project_id}'"
        )


def safe_evidence_metadata(envelope: UntrustedTextEnvelope) -> Dict[str, str]:
    """Return the only source representation permitted in runtime evidence."""
    return envelope.to_runtime_metadata()
