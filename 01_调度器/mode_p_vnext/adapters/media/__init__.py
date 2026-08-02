"""Fail-closed A7 media adapters; real external media is not started."""

from mode_p_vnext.adapters.media.renderer import NoopMediaRenderer
from mode_p_vnext.adapters.media.verifier import NoopMediaVerifier

__all__ = ["NoopMediaRenderer", "NoopMediaVerifier"]
