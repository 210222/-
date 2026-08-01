"""Deterministic owner of raw-source normalization for the v3.0 ingest chain."""

from __future__ import annotations

import codecs
import unicodedata
from collections.abc import Sequence

from mode_p_vnext.domain.artifact import DomainValidationError, SourceRef
from mode_p_vnext.domain.facts import (
    NormalizedSource,
    SourcePartition,
    normalized_text_sha256,
)


class SourceNormalizer:
    """Normalize bytes/text before any model sees source-relative offsets.

    Partition offsets are explicitly offsets in the *normalized* text. This
    avoids the unsafe conversion of legacy/raw byte offsets after CRLF, BOM,
    codec, or Unicode normalization has changed character positions.
    """

    @staticmethod
    def normalize(
        raw_source: str | bytes,
        *,
        source_id: str,
        normalized_partitions: Sequence[tuple[str, str, int, int]],
        encoding: str = "utf-8",
        locator: str | None = None,
    ) -> NormalizedSource:
        if not isinstance(source_id, str) or not source_id.strip():
            raise DomainValidationError("source_id must be non-empty")
        if not isinstance(encoding, str) or not encoding.strip():
            raise DomainValidationError("encoding must be non-empty")
        try:
            canonical_encoding = codecs.lookup(encoding).name
        except LookupError as exc:
            raise DomainValidationError("unsupported source encoding") from exc
        if isinstance(raw_source, bytes):
            try:
                text = raw_source.decode(canonical_encoding, errors="strict")
            except UnicodeDecodeError as exc:
                raise DomainValidationError("source bytes do not match the declared encoding") from exc
        elif isinstance(raw_source, str):
            text = raw_source
        else:
            raise DomainValidationError("raw_source must be str or bytes")

        if text.startswith("\ufeff"):
            text = text[1:]
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = unicodedata.normalize("NFC", text)
        if not text.strip():
            raise DomainValidationError("normalized source must contain non-whitespace text")
        if "\x00" in text or any(0xD800 <= ord(char) <= 0xDFFF for char in text):
            raise DomainValidationError("source contains forbidden code points")

        partitions: list[SourcePartition] = []
        for spec in normalized_partitions:
            if not isinstance(spec, tuple) or len(spec) != 4:
                raise DomainValidationError(
                    "normalized_partitions must contain (episode_id, scene_id, start, end) tuples"
                )
            partitions.append(
                SourcePartition(
                    episode_id=spec[0],
                    scene_id=spec[1],
                    source_start=spec[2],
                    source_end=spec[3],
                )
            )
        digest = normalized_text_sha256(text)
        return NormalizedSource(
            source_ref=SourceRef(source_id=source_id, digest=digest, locator=locator),
            normalized_text=text,
            encoding=canonical_encoding,
            character_count=len(text),
            line_start_offsets=(0,)
            + tuple(index + 1 for index, character in enumerate(text) if character == "\n"),
            partitions=tuple(partitions),
        )
