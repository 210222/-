"""MODE:P vNext — Read-Only Fixture Data.

This sub-package holds read-only test fixtures and baseline data used for
deterministic verification (Golden case text, canonical examples, expected
outputs, etc.). Fixture data MUST NOT be modified by vNext runtime code.

READ_ONLY: All files in this directory are immutable reference data.
Do not mutate, rewrite, or derive runtime state from fixture contents.
"""

FIXTURES_READ_ONLY = True
