"""Fail-closed media adapters for MODE:P vNext.

Architecture ref: MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.0 §9.4 / §14 A7.

Without a real media stack, rendering and verification are unavailable:
the adapters raise instead of fabricating placeholder evidence, so text-only
pipelines can never claim visual acceptance.
"""

from mode_p_vnext.adapters.media.renderer import NoopMediaRenderer
from mode_p_vnext.adapters.media.verifier import NoopMediaVerifier

__all__ = ["NoopMediaRenderer", "NoopMediaVerifier"]
