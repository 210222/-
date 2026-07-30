"""V3.4 Scene Diagnosis & Knowledge Query Schema."""

import unittest

try:
    from mode_p_vnext.schema import scene_diagnosis as sd
    from mode_p_vnext.diagnosis_artifact import (
        DirectorProblemSet,
        build_phase_a_artifact,
        validate_diagnosis_artifact,
    )
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class SceneDiagnosisTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "scene_diagnosis not yet implemented")
    def test_diagnosis_dimensions(self):
        d = sd.SceneDiagnosis(
            scene_id="EP8_SC1",
            attention_path="从人物背影持续收缩到枪管内部",
            space_issues=["枪管内部空间狭小", "单侧光源"],
            performance_issues=[],
            movement_issues=["推镜速度需配合注意力节奏"],
            lighting_issues=["避免管内被渲染为魔幻光源"],
            transition_issues=[],
            model_risks=["管内结构可能被模型误读为漩涡"],
        )
        self.assertEqual(d.scene_id, "EP8_SC1")
        self.assertEqual(len(d.model_risks), 1)

    @unittest.skipIf(not MODULE_EXISTS, "scene_diagnosis not yet implemented")
    def test_diagnosis_generates_knowledge_query(self):
        d = sd.SceneDiagnosis(
            scene_id="EP6_SC2",
            attention_path="三人注意力交替",
            space_issues=[],
            performance_issues=["微表情需被摄影机看见"],
            movement_issues=[],
            lighting_issues=[],
            transition_issues=["内部切镜时机"],
            model_risks=[],
        )
        query = sd.generate_knowledge_query(d)
        self.assertGreater(len(query.dimension_questions), 0)
        self.assertIn("attention", query.dimension_questions)

    @unittest.skipIf(not MODULE_EXISTS, "scene_diagnosis not yet implemented")
    def test_query_excludes_empty_dimensions(self):
        d = sd.SceneDiagnosis(
            scene_id="S1",
            attention_path="clear",
            space_issues=[], performance_issues=[],
            movement_issues=[], lighting_issues=[],
            transition_issues=[], model_risks=[],
        )
        query = sd.generate_knowledge_query(d)
        # Only attention has content — others should be absent or empty
        self.assertIn("attention", query.dimension_questions)
        self.assertNotIn("lighting", query.dimension_questions)

    @unittest.skipIf(not MODULE_EXISTS, "scene_diagnosis not yet implemented")
    def test_no_scene_type_label(self):
        """Diagnosis must NOT use single scene-type labels like 'action'."""
        d = sd.SceneDiagnosis(scene_id="S1", attention_path="clear")
        self.assertFalse(hasattr(d, "scene_type"))

    @unittest.skipIf(not MODULE_EXISTS, "diagnosis modules not yet implemented")
    def test_phase_a_artifact_has_problem_set_without_shot_answer(self):
        diagnosis = sd.SceneDiagnosis(
            scene_id="S_PHASE_A",
            attention_path="attention moves from the hand to the object",
            space_issues=["narrow layout may hide the prop relationship"],
            model_risks=["hand and prop may merge"],
        )
        artifact = build_phase_a_artifact(
            "DA-1",
            "EP-1",
            diagnosis,
            open_questions=["Which visibility problem must the Director resolve?"],
        )
        self.assertEqual(validate_diagnosis_artifact(artifact), [])
        payload = artifact.to_dict()
        self.assertEqual(payload["phase"], "A_DIAGNOSIS_ONLY")
        self.assertIn("attention", payload["problem_set"]["decision_domains"])
        self.assertTrue(artifact.content_sha256)

    @unittest.skipIf(not MODULE_EXISTS, "diagnosis modules not yet implemented")
    def test_phase_a_rejects_fixed_shot_answer(self):
        diagnosis = sd.SceneDiagnosis(scene_id="S_BAD", attention_path="attention question")
        bad_problem_set = DirectorProblemSet(
            knowledge_questions=["Use a 50mm lens for the close-up"],
            decision_domains=["attention"],
        )
        with self.assertRaises(ValueError):
            build_phase_a_artifact(
                "DA-BAD",
                "EP-1",
                diagnosis,
                open_questions=["What requires judgement?"],
                problem_set=bad_problem_set,
            )


if __name__ == "__main__":
    unittest.main()
