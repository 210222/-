"""Regression checks for the executable Claude Code MODE:P entry points."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import re
import subprocess
import unittest
from pathlib import Path

from dp_contract import DP_VALID_FIELDS


ROOT = Path(__file__).resolve().parents[2]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _sha256_if_exists(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _is_packaged_by_simple_gitignore(relative: str) -> bool:
    normalised = relative.replace("\\", "/")
    ignored = [
        line.strip().replace("\\", "/")
        for line in _read(".gitignore").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    return not any(
        normalised == pattern or fnmatch.fnmatchcase(normalised, pattern)
        for pattern in ignored
    )


def _frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\n(?P<body>.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise AssertionError("missing YAML frontmatter")
    values: dict[str, str] = {}
    for raw in match.group("body").splitlines():
        if ":" in raw:
            key, value = raw.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def _run_hook(command: str, payload: dict) -> dict:
    result = subprocess.run(
        command,
        cwd=ROOT / "01_调度器" / "mode_p",
        input=json.dumps(payload, ensure_ascii=False),
        text=True,
        capture_output=True,
        shell=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return json.loads(result.stdout)


class ClaudeAgentDefinitionTests(unittest.TestCase):

    def test_director_is_a_valid_writable_custom_agent(self) -> None:
        text = _read(".claude/agents/mode-p-director.md")
        meta = _frontmatter(text)
        self.assertEqual(meta["name"], "mode-p-director")
        self.assertTrue(meta["description"])
        self.assertEqual(meta["model"], "inherit")
        self.assertIn("Read", meta["tools"])
        self.assertIn("Write", meta["tools"])
        self.assertNotIn("Agent", meta["tools"])
        self.assertNotIn("Bash", meta["tools"])
        self.assertIn("02_Agent/director_agent.md", text)
        self.assertIn("never author `STORYBOARD.md`", text)
        self.assertIn("parent\nClaude Code task", text)
        self.assertIn("global model-name", text)
        self.assertIn("allowlist", text)

    def test_dp_is_a_valid_read_only_custom_agent(self) -> None:
        text = _read(".claude/agents/mode-p-dp.md")
        meta = _frontmatter(text)
        self.assertEqual(meta["name"], "mode-p-dp")
        self.assertTrue(meta["description"])
        self.assertEqual(meta["model"], "inherit")
        self.assertIn("Read", meta["tools"])
        for forbidden in ("Write", "Edit", "Bash", "Agent"):
            self.assertNotIn(forbidden, meta["tools"])
        self.assertIn("02_Agent/dp_agent.md", text)
        self.assertIn("DP_INPUT_BLOCKED", text)
        self.assertIn("parent Claude Code task", text)
        self.assertIn("global model-name", text)
        self.assertIn("allowlist", text)
        self.assertNotIn("batch Masters", meta["description"])
        self.assertIn("Provenance and hash\ncurrentness are local-runtime", text)
        self.assertNotIn("hash\ndoes not match the assignment", text)


class ActiveCommandTests(unittest.TestCase):

    def test_machine_local_permissions_are_not_packaged(self) -> None:
        local_path = ROOT / ".claude" / "settings.local.json"
        before_hash = _sha256_if_exists(local_path)
        self.assertIn(
            ".claude/settings.local.json",
            _read(".gitignore").replace("\\", "/"),
        )
        self.assertFalse(
            _is_packaged_by_simple_gitignore(".claude/settings.local.json")
        )
        self.assertEqual(before_hash, _sha256_if_exists(local_path))

    def test_kb_guard_hook_is_project_relative_and_executable(self) -> None:
        settings = json.loads(_read(".claude/settings.json").lstrip("\ufeff"))
        hook = settings["hooks"]["PreToolUse"][0]["hooks"][0]
        command = hook["command"]
        self.assertNotRegex(command, r"[A-Za-z]:[\\/]")
        self.assertIn(".claude/hooks/kb-guard.ps1", command.replace("\\", "/"))

        allowed = _run_hook(
            command,
            {
                "tool_name": "Write",
                "tool_input": {
                    "file_path": "delivery/STORYBOARD.md",
                    "content": "普通内容",
                },
            },
        )
        blocked = _run_hook(
            command,
            {
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": "delivery/VIDEO_PROMPT.md",
                    "new_string": "internal D-TRI-01",
                },
            },
        )
        self.assertTrue(allowed["continue"])
        self.assertFalse(blocked["continue"])

    def test_codex_kb_guard_is_root_name_independent_and_executable(self) -> None:
        settings = json.loads(_read(".codex/hooks.json").lstrip("\ufeff"))
        hook = settings["hooks"]["PreToolUse"][0]["hooks"][0]
        command = hook["command"]
        self.assertNotRegex(command, r"[A-Za-z]:[\\/]")
        self.assertNotIn("导演系统_v5", command)
        self.assertIn(".codex/hooks/kb-guard.ps1", command.replace("\\", "/"))

        blocked = _run_hook(
            command,
            {
                "tool_name": "Write",
                "tool_input": {
                    "file_path": "delivery/STORYBOARD.md",
                    "content": "internal D-TRI-01",
                },
            },
        )
        self.assertFalse(blocked["continue"])

    def test_pilot_command_is_independent_episode_and_batch_director(self) -> None:
        text = _read(".claude/commands/mode-p-pilot.md")
        meta = _frontmatter(text)
        self.assertIn("<episode-script-path>", meta["argument-hint"])
        self.assertIn("Agent", meta["allowed-tools"])
        required = (
            "$ARGUMENTS",
            "current Claude Code task is the orchestrator",
            "one persistent `mode-p-director` Agent",
            "Resume that same Director",
            "one new `mode-p-dp` Agent",
            "actual\n  `resolvedModel`",
            "DIRECTOR_MASTER.md",
            "python -m batch_dp prepare",
            "python -m batch_dp submit",
            "python -m director_session bind",
            "python -m director_session resume",
            "python -m episode_delivery assemble",
            "EPISODE_VISUAL_BIBLE.md",
            "EPISODE_CONTINUITY_LEDGER.md",
            "delivery/STORYBOARD.md",
            "delivery/VIDEO_PROMPT.md",
            "Automatic project resolution",
            "Missing images are not a blocker",
            "Apply the selected scene-expression Profile",
        )
        for marker in required:
            self.assertIn(marker, text)
        for exact_cli_marker in (
            "--scene-session <INDEX=PATH>",
            "--model-name <resolvedModel>",
            "--model-call-id <call-id>",
            "episode_delivery assemble <episode-review-session> <episode-session>",
            "Strong reasoning model discipline",
            "DeepSeek V4 Pro",
        ):
            self.assertIn(exact_cli_marker, text)
        self.assertNotIn("invoke mode-p-director agent for each scene", text)
        self.assertNotIn("python -m run_mode_p submit", text)
        self.assertNotIn("dispatcher_v5.0.md", text)
        self.assertNotIn("--scenes", text)
        self.assertNotIn("--session-dir", text)
        self.assertNotIn("<project>", text)

    def test_mode_p_alias_cannot_reactivate_single_scene_pipeline(self) -> None:
        text = _read(".claude/commands/mode-p.md")
        meta = _frontmatter(text)
        self.assertIn("<episode-script-path>", meta["argument-hint"])
        self.assertIn(".claude/commands/mode-p-pilot.md", text)
        self.assertIn("retired single-scene controller", text)
        self.assertNotIn("run_mode_p.py init", text)

    def test_rebuild_command_audits_after_all_tasks_are_checked(self) -> None:
        text = _read(".claude/commands/mode-p-rebuild.md")
        meta = _frontmatter(text)
        self.assertIn("local completion audit", meta["description"])
        self.assertIn("Local Completion Audit", text)
        self.assertIn("python -m pytest . -q", text)
        self.assertIn("python -m legacy_residue_check", text)
        self.assertIn("LOCAL_REBUILD_READY", text)
        self.assertIn("NO_LOCAL_DRIFT", text)
        self.assertIn("Do not start /mode-p-accept automatically", text)
        self.assertNotIn("Agent", meta["allowed-tools"])

    def test_vnext_rebuild_is_isolated_and_cannot_switch_production(self) -> None:
        text = _read(".claude/commands/mode-p-vnext-rebuild.md")
        meta = _frontmatter(text)
        self.assertIn("vNext engineering task", meta["description"])
        self.assertNotIn("Agent", meta["allowed-tools"])
        required = (
            "MODE_P_VNEXT_CONSTRUCTION_V2.md",
            "MODE_P_VNEXT_RELEASE_TASKS.json",
            "MODE_P_VNEXT_RELEASE_STATE.json",
            "release_control audit",
            "release_control status",
            "release_control next",
            "release_control claim",
            "release_control complete",
            "release_control fail",
            "release_control recover",
            "release_control invalidate",
            "one A0-A10 task",
            "black-box",
            "PRODUCTION_SWITCH: NOT_PERFORMED",
            "Do not start Shadow, media generation, or production switching automatically",
            "Never directly edit state",
            "historical evidence only",
        )
        for marker in required:
            self.assertIn(marker, text)
        forbidden = (
            "python -m run_mode_p submit",
            "python -m mode_p_pilot",
            "python -m batch_dp",
            "python -m mode_p_vnext.rebuild_control claim",
            "MODE_P_VNEXT_LOOP_REPAIR_PLAN.md",
            "MODE_P_VNEXT_REPAIR_TASKS.json",
        )
        for marker in forbidden:
            self.assertNotIn(marker, text)

        command = _read(".claude/commands/mode-p-vnext-rebuild.md")
        root_guidance = _read("CLAUDE.md")
        construction = _read(
            "MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_CONSTRUCTION_V2.md"
        )

        for marker in (
            "release_control audit",
            "release_control status",
            "release_control next",
            "release_control claim",
            "release_control complete",
            "release_control fail",
            "release_control recover",
            "release_control invalidate",
            "verification_commands",
            "产物哈希",
        ):
            self.assertIn(marker, command + "\n" + construction)

        self.assertIn("only `/mode-p-rebuild`", root_guidance)
        for stale in (
            "currently R0.1",
            "READ_PROGRESS",
            "MARK_IN_PROGRESS",
            "实施计划中第一项前置任务全部完成的 `[ ]` 任务",
            "`MODE_P_VNEXT_PROGRESS.md` 写入命令",
            "/mode-p-vnext-rebuild V0.1",
        ):
            self.assertNotIn(stale, command + "\n" + construction)

        for marker in (
            "HISTORICAL_READ_ONLY",
            "B1 Prompt 硬上限 12K",
            "B1 Draft Schema 硬上限 4.5K",
            "模型只输出 Draft",
            "文本验证不能设置 `media_visual_acceptance=true`",
            "任何 A 任务都不得修改 `/mode-p-pilot`",
            "首个合法施工任务只能是 A0",
        ):
            self.assertIn(marker, construction)

    def test_real_model_acceptance_is_an_explicit_separate_command(self) -> None:
        rebuild = _read(".claude/commands/mode-p-rebuild.md")
        self.assertIn("Do not create a model-acceptance run", rebuild)
        self.assertNotIn("model_acceptance_guard prepare", rebuild)

        text = _read(".claude/commands/mode-p-accept.md")
        meta = _frontmatter(text)
        self.assertIn("Agent", meta["allowed-tools"])
        required = (
            "python -m model_acceptance_guard bind-director",
            "python -m model_acceptance_guard bind-dp",
            "must be invoked explicitly by the user",
            "Never schedule it with /loop",
            "deepseek-v4-pro",
            "new unique run ID",
            "Never reuse run-001",
            "mode-p-director",
            "newly launched mode-p-dp",
            "`model: inherit`",
            "one scene's `DIRECTOR_MASTER.md` per Write call",
            "Never use TaskStop",
            "never launch a second Director",
            "A Hook error makes\nthe current acceptance run invalid",
        )
        for marker in required:
            self.assertIn(marker, text)
        self.assertIn("`provenance/` snapshots", text)

        protocol = _read("MODE_P_REDESIGN_PROJECT/MODEL_ACCEPTANCE_PROTOCOL.md")
        self.assertIn("_MINI_SCRIPT", protocol)
        self.assertIn("主 Claude Code 任务只编排", protocol)
        self.assertIn("不接受手填 --model", protocol)
        self.assertIn("不得用临时 Python 片段", protocol)
        self.assertIn("run-001", protocol)


class CanonicalRoleContractTests(unittest.TestCase):

    def test_director_uses_current_knowledge_and_master_only(self) -> None:
        text = _read("02_Agent/director_agent.md")
        for name in (
            "knowledge/core/director_core.md",
            "knowledge/core/sd2.md",
            "knowledge/core/performance.md",
            "knowledge/core/editing_transition.md",
        ):
            self.assertIn(name, text)
        self.assertIn("0 < duration <= 15s", text)
        self.assertIn("second_nodes", text)
        self.assertIn("half_second_nodes", text)
        self.assertIn("first_last_frame", text)
        self.assertIn("omni_reference", text)
        self.assertIn("不得直接创作或修补 `STORYBOARD.md`", text)
        self.assertNotIn("最多两张", text)
        self.assertNotIn("face_count", text)
        self.assertIn("### 3.1 决策顺序", text)
        self.assertIn("当前分集事实 > 已提交连续性", text)
        self.assertIn("可执行字段必须作出单一决定", text)
        self.assertIn("未裁决分支", text)
        self.assertIn("分集级持续导演契约", text)
        self.assertIn("视觉时间线", text)
        self.assertIn("共享 Boundary", text)
        self.assertNotIn("故事板关键帧：[D]", text)
        self.assertNotIn("视频时间线：[D]", text)

    def test_compact_runtime_contract_leaves_derived_ids_local(self) -> None:
        text = _read("01_调度器/mode_p/director_runtime_contract.md")
        self.assertIn("边界 ID 由本地编译器", text)
        for mechanical in (
            "父版本：", "创建时间：", "最后修改：", "进入边界 ID：[M]",
            "交出边界 ID：[M]", "对应 LOOP_SPEC：",
        ):
            self.assertNotIn(mechanical, text)
        self.assertIn("视觉时间线：[D]", text)
        self.assertIn("## Boundary <scene_id>-B0", text)

    def test_dp_document_matches_executable_contract(self) -> None:
        text = _read("02_Agent/dp_agent.md")
        self.assertIn("<ShotID>: <field> —", text)
        for field in DP_VALID_FIELDS:
            self.assertIn(f"`{field}`", text)
        self.assertNotIn("face_count", text)
        self.assertIn("不可把一切过轴都视为错误", text)
        self.assertIn("执行确定性", text)
        self.assertIn("未裁决分支", text)

    def test_root_guidance_has_no_deleted_or_legacy_active_command(self) -> None:
        text = _read("CLAUDE.md")
        self.assertIn("current Claude Code task is the orchestrator", text)
        self.assertIn("persistent `mode-p-director` subagent", text)
        self.assertIn("new `mode-p-dp` subagent", text)
        self.assertIn("Master is the sole design source", text)
        self.assertNotIn("batch_budget", text)
        self.assertNotIn("dispatcher_v5.0", text)
        self.assertNotIn("Director output is exactly DIRECTOR_MASTER.md +", text)

    def test_rebuild_loop_is_reasoning_model_compatible_without_context_bloat(self) -> None:
        text = _read("MODE_P_REDESIGN_PROJECT/CLAUDE_CODE_REBUILD_LOOP.md")
        self.assertIn("DeepSeek V4 Pro", text)
        self.assertIn("model: inherit", text)
        self.assertIn("不追加“输出完整思维链”要求", text)
        self.assertIn("更大上下文窗口不是加载全库的理由", text)


if __name__ == "__main__":
    unittest.main()
