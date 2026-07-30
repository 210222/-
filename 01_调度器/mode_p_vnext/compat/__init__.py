"""Read-only adapters from retained legacy artifacts into canonical vNext data."""

from .legacy_checkpoint import read_legacy_b0_k2_checkpoint

__all__ = ("read_legacy_b0_k2_checkpoint",)
