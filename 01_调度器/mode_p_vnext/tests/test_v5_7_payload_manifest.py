"""V5.7 Render Payload Manifest."""

import unittest

try:
    from mode_p_vnext.schema.canonical_timeline import TimeInterval
    from mode_p_vnext.schema.generation_segment import GenerationSegment, CinematicShot
    from mode_p_vnext.schema.visibility_contract import VisibilityContract
    from mode_p_vnext.video_projection import project_video_prompt
    from mode_p_vnext.payload_compiler import compile_render_payload
    from mode_p_vnext import payload_manifest as pm
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class PayloadManifestTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "payload_manifest not yet implemented")
    def test_manifest_records_included_fields(self):
        shots = [CinematicShot("S1", "SEG1", TimeInterval(0, 24000),
                                "j", "c", "WS", "f", "m", "co", "l", "p")]
        seg = GenerationSegment("SEG1", TimeInterval(0, 24000), shots)
        view = project_video_prompt(seg)
        contract = VisibilityContract(visible_whitelist=["枪管"],
                                       narrative_only=["背景故事"])
        payload = compile_render_payload(view, contract)
        manifest = pm.create_payload_manifest(payload, contract)
        self.assertIsInstance(manifest.included_field_ids, list)
        self.assertIsInstance(manifest.excluded_field_ids, list)

    @unittest.skipIf(not MODULE_EXISTS, "payload_manifest not yet implemented")
    def test_manifest_has_content_hash(self):
        shots = [CinematicShot("S1", "SEG1", TimeInterval(0, 1000),
                                "j", "c", "WS", "f", "m", "co", "l", "p")]
        seg = GenerationSegment("SEG1", TimeInterval(0, 1000), shots)
        view = project_video_prompt(seg)
        contract = VisibilityContract(visible_whitelist=["x"])
        payload = compile_render_payload(view, contract)
        manifest = pm.create_payload_manifest(payload, contract)
        self.assertEqual(len(manifest.content_sha256), 64)


if __name__ == "__main__":
    unittest.main()
