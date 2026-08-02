"""Persistent storage adapters owned by the v3.0 text-shadow composition."""

from .shadow_run import TextShadowStorage, TextShadowStorageError

__all__ = ["TextShadowStorage", "TextShadowStorageError"]
