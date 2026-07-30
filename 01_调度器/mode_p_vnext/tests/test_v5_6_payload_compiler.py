"""V5.6 Render Payload Compiler — excludes non-visible from forward payload."""

import unittest

try:
    from mode_p_vnext.schema.canonical_timeline import TimeInterval
    from mode_p_vnext.schema.generation_segment import GenerationSegment, CinematicShot
    from mode_p_vnext.schema.visibility_contract import VisibilityContract
    from mode_p_vnext.video_projection import project_video_prompt
    from mode_p_vnext import payload_compiler as pcc
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class PayloadCompilerTests(unittest.TestCase):
    def _make_view(self):
        shots = [CinematicShot("S1", "SEG1", TimeInterval(0, 24000),
                                "job", "cam", "WS", "focal", "mot", "comp", "light", "perf")]
        seg = GenerationSegment("SEG1", TimeInterval(0, 24000), shots)
        return project_video_prompt(seg)

    @unittest.skipIf(not MODULE_EXISTS, "payload_compiler not yet implemented")
    def test_compile_excludes_narrative_only(self):
        view = self._make_view()
        contract = VisibilityContract(
            visible_whitelist=["枪"],
            narrative_only=["人物背景故事"],
        )
        payload = pcc.compile_render_payload(view, contract)
        self.assertNotIn("人物背景故事", str(payload.fields))

    @unittest.skipIf(not MODULE_EXISTS, "payload_compiler not yet implemented")
    def test_compile_excludes_audio_only(self):
        view = self._make_view()
        contract = VisibilityContract(
            visible_whitelist=["x"],
            audio_only=["画外对白"],
        )
        payload = pcc.compile_render_payload(view, contract)
        self.assertNotIn("画外对白", str(payload.fields))

    @unittest.skipIf(not MODULE_EXISTS, "payload_compiler not yet implemented")
    def test_compile_includes_visible_whitelist(self):
        view = self._make_view()
        contract = VisibilityContract(visible_whitelist=["枪管", "双手"])
        payload = pcc.compile_render_payload(view, contract)
        self.assertIn("visible_whitelist", payload.fields)


if __name__ == "__main__":
    unittest.main()
