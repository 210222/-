import unittest

from sd2_preflight import scan_prompt


class PreflightTests(unittest.TestCase):
    def test_valid_prompt_passes(self):
        prompt = """## Shot 1 | 8s
Image:
[0s] A woman stands beside the desk, eyes fixed on the open folder.
[1s] Her right hand closes the folder.
[8s] The folder rests closed beneath her right hand.
Sound: quiet room tone.
Exit: hard cut.
"""
        self.assertEqual(scan_prompt(prompt), [])

    def test_blocks_only_provable_hard_boundary_risks(self):
        prompt = """## Shot 1 | 16s
Image:
[0s] 三张清晰正脸同时看向屏幕，不要抖动。
[1s] 她悲伤地缓缓抬头，屏幕文字清晰可读。
[16s] 她的右手按在桌面上。
Sound: 室内底噪持续。
Exit: 硬切。
"""
        kinds = {issue.kind for issue in scan_prompt(prompt)}
        self.assertEqual(kinds, {"duration", "negative_language"})

    def test_advisory_quality_terms_do_not_become_fake_platform_limits(self):
        prompt = """## Shot 1 | 8s
Image:
[0s] 三张清晰正脸同时看向屏幕，屏幕文字清晰可读。
[1s] 她悲伤地缓缓抬头，同时用手按住桌面。
[8s] 她保持抬头姿态，右手按在桌面上。
Sound: 室内底噪持续。
Exit: 硬切。
"""
        self.assertEqual(scan_prompt(prompt), [])

    def test_rejects_missing_or_malformed_shot_headers(self):
        self.assertIn("missing_shot_header", {issue.kind for issue in scan_prompt("# Video\nImage: 人物站立。")})
        malformed = "## Shot 1 | medium | eight seconds\nImage: 人物站立。"
        self.assertIn("malformed_shot_header", {issue.kind for issue in scan_prompt(malformed)})

    def test_rejects_non_positive_duration_and_out_of_range_time_nodes(self):
        zero = "## Shot 1 | 0s\nImage: 人物站立。"
        self.assertIn("duration", {issue.kind for issue in scan_prompt(zero)})

        out_of_range = (
            "## Shot 1 | 8s\nImage:\n[0s] 人物站立。\n[9s] 人物抬手。\n"
            "Sound: 室内底噪。\nExit: 硬切。"
        )
        self.assertIn("time_range", {issue.kind for issue in scan_prompt(out_of_range)})

    def test_rejects_duplicate_shot_ids(self):
        prompt = "## Shot A | 4s\nImage: 人物站立。\n## Shot A | 4s\nImage: 人物坐下。"
        self.assertIn("duplicate_shot_id", {issue.kind for issue in scan_prompt(prompt)})

    def test_rejects_unresolved_director_placeholder(self):
        prompt = "## Shot A | 4s\nImage:\n[0s] [Director: fill visible action]\n[4s] 人物站定。"
        self.assertIn(
            "unresolved_placeholder",
            {issue.kind for issue in scan_prompt(prompt)},
        )

    def test_scans_camera_light_sound_and_exit_not_only_image(self):
        prompt = """## Shot 1 | 4s
Camera: 摄影机不移动。
Lighting: 主光可能来自左侧或者右侧。
Image:
[0s] 人物站在桌边。
[4s] 人物右手落在桌面。
Sound: 如果需要，加入脚步声。
Exit: 取决于动作完成时机。
"""
        kinds = {issue.kind for issue in scan_prompt(prompt)}
        self.assertIn("negative_language", kinds)
        self.assertIn("unresolved_branch", kinds)

    def test_rejects_leaked_storyboard_marker_and_non_visible_language(self):
        prompt = """## Shot 1 | 4s
Image:
[0s][SB] 人物仿佛意识到危险。
[4s] 人物右手握紧桌沿。
Sound: 室内底噪。
Exit: 硬切。
"""
        kinds = {issue.kind for issue in scan_prompt(prompt)}
        self.assertIn("derivation_marker", kinds)
        self.assertIn("non_visible_language", kinds)

if __name__ == "__main__":
    unittest.main()
