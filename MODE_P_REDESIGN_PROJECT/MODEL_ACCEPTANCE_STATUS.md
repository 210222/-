# MODE:P Model Acceptance Status

status: MODEL_ACCEPTANCE_PASSED
updated_at: 2026-07-19T14:47:54.861303+00:00
local_implementation: passed
local_suite: unittest discover 685 tests passed, 0 failed
legacy_residue: clean
semantic_gates: B1-B5, D4, adversarial DP all passed
protocol: MODE_P_REDESIGN_PROJECT/MODEL_ACCEPTANCE_PROTOCOL.md
input: MODE_P_REDESIGN_PROJECT/acceptance_cases/director_transfer_4scenes.md
input_sha256: 6cb709ad33294d0caf5aedb3ab6b528ab9cdcd0ff15e81240e8559bbf3b15073
evidence_dir: model_acceptance_runs/run-015
owner: claude-code
director_model: deepseek-v4-pro
dp_model: deepseek-v4-pro
dp_reviews: 2 (adversarial plus production)
dp_result: READY (all 4 scenes; batch state committed)
episode_review: PASS
adversarial_dp: PASS (5/5 categories identified)
delivery_storyboard_sha256: cca1bbad39cde6dbdf3f0cf8e58df28b65238415d2d70f2802aa0461913900be
delivery_video_prompt_sha256: 28405638d3520a8519dcdbddc3be4228ddc04cdab840ecd5396829cb15b28155
director_quality_review: B1-B5 with scene/shot evidence
transfer_review: D4 with 3-dialogue-scene comparison

本状态由 model_acceptance_guard complete 在验证模型来源、批次 DP 状态、分集根状态、
Episode Review、双文件原子交付及语义证据后生成。P8.8 外部即梦真实渲染仍未执行。
