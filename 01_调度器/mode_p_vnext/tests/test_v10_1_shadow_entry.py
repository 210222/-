"""V10.1 vnext_shadow Entrypoint — isolated comparison, not dual-system co-run."""

import json
import tempfile
import unittest
from pathlib import Path

try:
    from mode_p_vnext import shadow_entry as se
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class ShadowEntryTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "shadow_entry not yet implemented")
    def test_shadow_mode_is_shadow_only(self):
        cfg = se.ShadowConfig(
            episode_script_path="test_episode.md",
            session_dir="/tmp/shadow_test",
            mode="shadow_only",
        )
        self.assertEqual(cfg.mode, "shadow_only")
        self.assertFalse(cfg.affects_production)

    @unittest.skipIf(not MODULE_EXISTS, "shadow_entry not yet implemented")
    def test_shadow_isolated_from_v4(self):
        cfg = se.ShadowConfig(
            episode_script_path="test.md",
            session_dir="/tmp/shadow_isolated",
            mode="shadow_only",
        )
        self.assertTrue(cfg.isolated_session)
        self.assertFalse(cfg.use_v4_cache)
        self.assertFalse(cfg.use_v4_generation_chain)

    @unittest.skipIf(not MODULE_EXISTS, "shadow_entry not yet implemented")
    def test_shadow_no_delivery_output(self):
        """Shadow produces comparison artifacts, NOT v4 delivery."""
        cfg = se.ShadowConfig("test.md", "/tmp/s", "shadow_only")
        self.assertFalse(cfg.writes_to_v4_delivery)

    @unittest.skipIf(not MODULE_EXISTS, "shadow_entry not yet implemented")
    def test_shadow_result_marks_comparison(self):
        result = se.ShadowResult(
            run_id="SHADOW_001",
            vnext_output={"storyboard": "..."},
            comparison_ready=True,
        )
        self.assertTrue(result.comparison_ready)
        self.assertFalse(result.production_ready)

    @unittest.skipIf(not MODULE_EXISTS, "shadow_entry not yet implemented")
    def test_real_shadow_writes_isolated_manifest_and_no_external_submission(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = root / "episode.md"
            script.write_text("# EP35\n\n周从文走向门口。", encoding="utf-8")
            result = se.run_shadow(
                se.ShadowConfig(
                    episode_script_path=str(script),
                    session_dir=str(root / "vnext-session"),
                    episode_id="EP35",
                )
            )
            manifest_path = Path(result.manifest_path)
            self.assertTrue(manifest_path.is_file())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["mode"], "shadow_only")
            self.assertTrue(manifest["comparison_ready"])
            self.assertFalse(manifest["production_ready"])
            self.assertFalse(manifest["isolation"]["external_submission"])
            self.assertFalse(manifest["isolation"]["writes_to_v4_delivery"])
            self.assertIn("master", json.loads(
                (Path(result.run_root) / manifest["comparison_path"]).read_text(encoding="utf-8")
            )["categories"])
            self.assertTrue(
                (Path(result.run_root) / "commits" / manifest["atomic_commit"]["commit_id"] / "COMMIT_MANIFEST.json").is_file()
            )

    @unittest.skipIf(not MODULE_EXISTS, "shadow_entry not yet implemented")
    def test_same_shadow_input_is_idempotent_but_source_collision_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = root / "episode.md"
            script.write_text("scene one", encoding="utf-8")
            config = se.ShadowConfig(str(script), str(root / "shadow"), episode_id="EP1")
            first = se.run_shadow(config)
            second = se.run_shadow(config)
            self.assertEqual(first.run_id, second.run_id)
            self.assertTrue(second.reused_existing_run)

            script.write_text("scene two", encoding="utf-8")
            with self.assertRaises(se.ShadowError):
                se.run_shadow(
                    se.ShadowConfig(
                        str(script),
                        str(root / "shadow"),
                        episode_id="EP1",
                        run_id=first.run_id,
                    )
                )

    @unittest.skipIf(not MODULE_EXISTS, "shadow_entry not yet implemented")
    def test_shadow_refuses_v4_delivery_or_external_submission_configuration(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = root / "episode.md"
            script.write_text("scene", encoding="utf-8")
            with self.assertRaises(se.ShadowError):
                se.run_shadow(
                    se.ShadowConfig(
                        str(script),
                        str(root / "shadow"),
                        use_v4_generation_chain=True,
                    )
                )


if __name__ == "__main__":
    unittest.main()
