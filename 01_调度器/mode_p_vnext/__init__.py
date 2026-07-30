"""MODE:P vNext — Isolated Rewrite Package.

This package is the engineering workspace for the MODE:P vNext rewrite.
It MUST NOT import from v4 (mode_p) creative modules.
"""

# ---------------------------------------------------------------------------
# Package identity
# ---------------------------------------------------------------------------
__version__ = "0.1.0"
__mode_p_vnext__ = True

# ---------------------------------------------------------------------------
# Isolation guard: vNext must not import v4 creative compiler modules.
# This check runs at import time as a safety net.
# ---------------------------------------------------------------------------
_V4_CREATIVE_MODULES = frozenset({
    "master_compiler",
    "view_deriver",
    "director_session",
    "batch_scheduler",
    "batch_state_machine",
    "batch_dp",
    "dp_contract",
    "dp_adversarial_check",
    "episode_review",
    "episode_delivery",
    "episode_templates",
    "director_master_template",
    "director_runtime_contract",
    "mode_p_pilot",
    "pilot_strategy",
    "bootstrap_loader",
    "context_retriever",
    "knowledge_indexer",
    "knowledge_curator",
    "cache_manager",
    "asset_card_registry",
    "asset_indexer",
    "master_sync_check",
    "dependency_invalidator",
    "episode_docs_check",
})


def _check_isolation() -> None:
    """Verify no v4 creative modules have been imported into sys.modules."""
    import sys
    violations = []
    for mod_name in sorted(sys.modules):
        if not mod_name.startswith("mode_p."):
            continue
        leaf = mod_name.split(".", 1)[1] if "." in mod_name else ""
        if leaf in _V4_CREATIVE_MODULES:
            violations.append(mod_name)
    if violations:
        raise ImportError(
            "mode_p_vnext isolation violation: v4 creative modules already "
            f"imported: {', '.join(violations)}"
        )


_check_isolation()
