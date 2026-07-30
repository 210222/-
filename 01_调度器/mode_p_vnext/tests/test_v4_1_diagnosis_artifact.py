"""V4.1 Scene Diagnosis Artifact — formal artifact wrapping diagnosis, no shot answers."""

import unittest

try:
    from mode_p_vnext.schema.scene_diagnosis import SceneDiagnosis
    from mode_p_vnext import diagnosis_artifact as da
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class DiagnosisArtifactTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "diagnosis_artifact not yet implemented")
    def test_artifact_wraps_diagnosis(self):
        diag = SceneDiagnosis(scene_id="S1", attention_path="推镜注意力收缩")
        artifact = da.DiagnosisArtifact(
            artifact_id="DA001",
            episode_id="EP8",
            diagnosis=diag,
            user_visual_constraints=["管内不能有魔幻光源"],
        )
        self.assertEqual(artifact.diagnosis.scene_id, "S1")
        self.assertEqual(len(artifact.user_visual_constraints), 1)

    @unittest.skipIf(not MODULE_EXISTS, "diagnosis_artifact not yet implemented")
    def test_artifact_has_no_shot_answers(self):
        """Artifact contains diagnosis questions, NOT shot/camera answers."""
        diag = SceneDiagnosis(scene_id="S1", attention_path="test")
        artifact = da.DiagnosisArtifact("DA1", "EP1", diag)
        self.assertFalse(hasattr(artifact, "shots"))
        self.assertFalse(hasattr(artifact, "camera_positions"))

    @unittest.skipIf(not MODULE_EXISTS, "diagnosis_artifact not yet implemented")
    def test_open_questions_must_be_populated(self):
        """If diagnosis has model_risks, open_questions must address them."""
        diag = SceneDiagnosis(scene_id="S1", model_risks=["漩涡误读"])
        artifact = da.DiagnosisArtifact("DA1", "EP1", diag,
                                         open_questions=[])
        violations = da.validate_diagnosis_artifact(artifact)
        self.assertGreater(len(violations), 0)

    @unittest.skipIf(not MODULE_EXISTS, "diagnosis_artifact not yet implemented")
    def test_artifact_to_dict(self):
        diag = SceneDiagnosis(scene_id="S1", attention_path="test")
        artifact = da.DiagnosisArtifact("DA1", "EP1", diag,
                                         open_questions=["如何处理管内渲染?"])
        d = artifact.to_dict()
        self.assertEqual(d["artifact_id"], "DA1")
        self.assertIn("open_questions", d)


if __name__ == "__main__":
    unittest.main()
