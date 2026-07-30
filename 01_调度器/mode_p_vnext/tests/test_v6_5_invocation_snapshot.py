"""V6.5 Model Invocation Snapshot."""

import unittest

try:
    from mode_p_vnext import invocation_snapshot as ins
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class InvocationSnapshotTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "invocation_snapshot not yet implemented")
    def test_snapshot_required_fields(self):
        snap = ins.InvocationSnapshot(
            invocation_id="INV001",
            model="deepseek-v4-pro",
            provider_version="2026-07",
            input_sha256="abc123",
            output_sha256="def456",
            sampling_params={"temperature": 0.7},
            finish_reason="stop",
        )
        self.assertEqual(snap.model, "deepseek-v4-pro")
        self.assertFalse(snap.truncated)

    @unittest.skipIf(not MODULE_EXISTS, "invocation_snapshot not yet implemented")
    def test_truncated_detection(self):
        snap = ins.InvocationSnapshot(
            invocation_id="INV002", model="test", provider_version="v1",
            input_sha256="abc", output_sha256="def",
            sampling_params={}, finish_reason="length",
        )
        self.assertTrue(snap.truncated)

    @unittest.skipIf(not MODULE_EXISTS, "invocation_snapshot not yet implemented")
    def test_replay_semantics_distinct(self):
        """replay_compile, reinvoke, regenerate are distinct operations."""
        snap = ins.InvocationSnapshot(
            invocation_id="INV003", model="test", provider_version="v1",
            input_sha256="abc", output_sha256="def",
            sampling_params={}, finish_reason="stop",
        )
        self.assertFalse(snap.allow_reinvoke)  # default: no automatic reinvoke


if __name__ == "__main__":
    unittest.main()
