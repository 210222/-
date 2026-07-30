"""V5.5 Capability Profile & Prompt Adapter."""

import unittest

try:
    from mode_p_vnext import capability_adapter as ca
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class CapabilityProfileTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "capability_adapter not yet implemented")
    def test_profile_required_fields(self):
        p = ca.CapabilityProfile(
            platform="jimeng_sd2",
            version="2.0",
            negative_strategy="separate_channel",
            duration_quantization="1s",
            aspect_ratios=["9:16"],
            fps=24,
            internal_cuts_supported=True,
            reference_slots=3,
            text_overlay_supported=False,
            audio_lipsync_supported=False,
            max_prompt_chars=5000,
        )
        self.assertEqual(p.platform, "jimeng_sd2")
        self.assertTrue(p.internal_cuts_supported)

    @unittest.skipIf(not MODULE_EXISTS, "capability_adapter not yet implemented")
    def test_adapter_passes_known_fields(self):
        p = ca.CapabilityProfile("test", "1", "inline", "1s", ["9:16"], 24,
                                  True, 3, False, False, 1000)
        adapter = ca.PromptAdapter(p)
        result = adapter.adapt({"shot_id": "S1", "camera_motion": "推"})
        self.assertIn("shot_id", result)

    @unittest.skipIf(not MODULE_EXISTS, "capability_adapter not yet implemented")
    def test_unknown_capability_fails_conservative(self):
        p = ca.CapabilityProfile("test", "1", "inline", "1s", ["9:16"], 24,
                                  True, 0, False, False, 1000)
        adapter = ca.PromptAdapter(p)
        with self.assertRaises(ca.CapabilityBlockedError):
            adapter.adapt({"reference_images": ["@img1"]})  # needs slots but 0 available


if __name__ == "__main__":
    unittest.main()
