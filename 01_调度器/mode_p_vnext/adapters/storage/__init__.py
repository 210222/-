"""Persistent storage adapters owned by the v3.1 text-shadow composition."""

from .shadow_run import TextShadowStorage, TextShadowStorageError

__all__ = ["TextShadowStorage", "TextShadowStorageError"]
