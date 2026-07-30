"""MODE:P vNext — External Feedback Integration (V9.3).

Receives human evaluations, FFmpeg mechanical evidence, and independent
multimodal reports. Records them WITHOUT auto-modifying knowledge.

Spec references: LOOP §9 Step 15.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from mode_p_vnext.knowledge_security import assert_untrusted_text_safe


ALLOWED_FEEDBACK_SOURCES = frozenset({
    "human_evaluation",
    "ffmpeg_mechanical",
    "multimodal_report",
})


@dataclass
class ExternalFeedback:
    feedback_id: str
    source: str             # human_evaluation | ffmpeg_mechanical | multimodal_report
    content: str
    segment_id: str = ""
    project_id: str = ""
    auto_modify_knowledge: bool = False
    knowledge_modification: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.feedback_id.strip():
            raise ValueError("feedback_id must not be empty")
        if self.source not in ALLOWED_FEEDBACK_SOURCES:
            raise ValueError(f"unsupported feedback source: {self.source}")
        if self.auto_modify_knowledge or self.knowledge_modification is not None:
            raise ValueError("external feedback cannot auto-modify knowledge")
        assert_untrusted_text_safe(
            source_id=self.feedback_id,
            source_kind=f"external_feedback:{self.source}",
            project_id=self.project_id or "external_feedback",
            content=self.content,
        )

    def to_runtime_metadata(self) -> Dict[str, str]:
        """Return runtime-safe feedback metadata without raw feedback content."""
        envelope = assert_untrusted_text_safe(
            source_id=self.feedback_id,
            source_kind=f"external_feedback:{self.source}",
            project_id=self.project_id or "external_feedback",
            content=self.content,
        )
        metadata = envelope.to_runtime_metadata()
        metadata.update({
            "feedback_id": self.feedback_id,
            "source": self.source,
            "segment_id": self.segment_id,
        })
        if self.project_id:
            metadata["project_id"] = self.project_id
        return metadata


def check_feedback_project_scope(
    feedback: ExternalFeedback,
    project_id: str,
) -> None:
    """Fail closed when feedback has no explicit matching project scope."""
    if not feedback.project_id:
        raise ValueError(
            f"feedback '{feedback.feedback_id}' has no project scope"
        )
    if feedback.project_id != project_id:
        raise ValueError(
            f"feedback '{feedback.feedback_id}' belongs to project "
            f"'{feedback.project_id}', not '{project_id}'"
        )
