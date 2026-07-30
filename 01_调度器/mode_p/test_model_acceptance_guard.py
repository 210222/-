from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from model_acceptance_guard import (
    AcceptanceGuardError,
    BOOTSTRAP_NAME,
    DP_ADVERSARIAL_INPUT,
    DP_ADVERSARIAL_SHA256,
    FIXED_INPUT,
    FIXED_INPUT_SHA256,
    bind_director,
    bind_dp,
    complete_run,
    export_dp_response,
    invalidate_run,
    prepare_run,
    reopen_incomplete_run,
    require_acceptance_director_provenance,
    require_acceptance_dp_provenance,
    sha256_file,
)


class ModelAcceptanceGuardTests(unittest.TestCase):

    def setUp(self) -> None:
        self.temp = Path(tempfile.mkdtemp(prefix="mode_p_acceptance_guard_"))
        case_dir = self.temp / "acceptance_cases"
        case_dir.mkdir()
        shutil.copy2(FIXED_INPUT, case_dir / FIXED_INPUT.name)
        shutil.copy2(
            DP_ADVERSARIAL_INPUT, case_dir / DP_ADVERSARIAL_INPUT.name
        )
        (self.temp / "MODEL_ACCEPTANCE_STATUS.md").write_text(
            "# MODE:P Model Acceptance Status\n\n"
            "status: pending\n"
            "local_implementation: passed\n"
            "local_suite: 630 passed, 0 failed\n"
            "legacy_residue: clean\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.temp, ignore_errors=True)

    def _transcript(
        self,
        run_dir: Path,
        *,
        agent_id: str,
        model: str,
        agent_type: str,
        suffix: str,
        bind_fixed_input: bool = True,
        bind_run: bool = True,
        response_text: str = "READY S1: Shot S1-1 has observable continuity.",
    ) -> Path:
        tool_use_id = f"tool-{suffix}"
        prompt_parts = ["MODE:P Agent assignment"]
        if bind_fixed_input:
            prompt_parts.append(
                str(self.temp / "acceptance_cases" / FIXED_INPUT.name)
            )
        if bind_run:
            prompt_parts.append(str(run_dir))
        prompt = "\n".join(prompt_parts)
        records = [
            {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "tool_use",
                            "id": tool_use_id,
                            "name": "Agent",
                            "input": {
                                "subagent_type": agent_type,
                                "prompt": prompt,
                            },
                        }
                    ],
                }
            },
            {
                "message": {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": "Agent launched",
                        }
                    ],
                },
                "toolUseResult": {
                    "agentId": agent_id,
                    "resolvedModel": model,
                    "status": "completed",
                    "content": [{"type": "text", "text": response_text}],
                },
            },
        ]
        path = self.temp / f"transcript-{suffix}.jsonl"
        path.write_text(
            "".join(json.dumps(item) + "\n" for item in records),
            encoding="utf-8",
        )
        return path

    def test_repository_fixed_input_has_expected_hash(self) -> None:
        self.assertEqual(sha256_file(FIXED_INPUT), FIXED_INPUT_SHA256)
        self.assertEqual(
            sha256_file(DP_ADVERSARIAL_INPUT), DP_ADVERSARIAL_SHA256
        )

    def test_prepare_creates_project_evidence_and_awaits_director(self) -> None:
        run_dir = prepare_run(
            "run-001",
            "test-owner",
            project=self.temp,
            now=datetime(2026, 7, 16, tzinfo=timezone.utc),
        )
        payload = json.loads((run_dir / BOOTSTRAP_NAME).read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], 3)
        self.assertEqual(payload["status"], "awaiting_director_agent")
        self.assertIsNone(payload["director_call_id"])
        self.assertEqual(payload["dp_agents"], [])
        self.assertEqual(
            payload["dp_adversarial_sha256"], DP_ADVERSARIAL_SHA256
        )
        status = (self.temp / "MODEL_ACCEPTANCE_STATUS.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("status: in_progress", status)
        self.assertIn(FIXED_INPUT_SHA256, status)
        self.assertIn(DP_ADVERSARIAL_SHA256, status)

    def test_prepare_rejects_tampered_input_and_existing_run(self) -> None:
        fixed = self.temp / "acceptance_cases" / FIXED_INPUT.name
        fixed.write_text("wrong script", encoding="utf-8")
        with self.assertRaisesRegex(AcceptanceGuardError, "SHA-256 mismatch"):
            prepare_run("run-001", "owner", project=self.temp)

        shutil.copy2(FIXED_INPUT, fixed)
        prepare_run("run-001", "owner", project=self.temp)
        with self.assertRaisesRegex(AcceptanceGuardError, "cannot be overwritten"):
            prepare_run("run-001", "owner", project=self.temp)
        with self.assertRaisesRegex(AcceptanceGuardError, "already in progress"):
            prepare_run("run-002", "owner", project=self.temp)

    def test_director_binding_reads_resolved_model_from_transcript(self) -> None:
        run_dir = prepare_run("run-001", "owner", project=self.temp)
        flash = self._transcript(
            run_dir,
            agent_id="director-flash",
            model="deepseek-v4-flash",
            agent_type="mode-p-director",
            suffix="director-flash",
        )
        with self.assertRaisesRegex(
            AcceptanceGuardError, "resolvedModel was deepseek-v4-flash"
        ):
            bind_director(
                run_dir,
                "director-flash",
                transcript_path=flash,
            )

        spoofed = self._transcript(
            run_dir,
            agent_id="director-spoofed",
            model="deepseek-v4-pro-extended",
            agent_type="mode-p-director",
            suffix="director-spoofed",
        )
        with self.assertRaisesRegex(
            AcceptanceGuardError, "resolvedModel was deepseek-v4-pro-extended"
        ):
            bind_director(
                run_dir,
                "director-spoofed",
                transcript_path=spoofed,
            )

        pro = self._transcript(
            run_dir,
            agent_id="director-pro",
            model="deepseek-v4-pro[1m]",
            agent_type="mode-p-director",
            suffix="director-pro",
        )
        payload = bind_director(
            run_dir,
            "director-pro",
            transcript_path=pro,
        )
        self.assertEqual(payload["status"], "director_agent_bound")
        self.assertEqual(payload["director_model"], "deepseek-v4-pro[1m]")
        self.assertEqual(
            payload["director_provenance"]["resolved_model"],
            "deepseek-v4-pro[1m]",
        )
        self.assertIn("tool_call_record_sha256", payload["director_provenance"])
        self.assertIn("tool_result_record_sha256", payload["director_provenance"])
        self.assertNotIn("transcript_sha256", payload["director_provenance"])
        portable = run_dir / payload["director_provenance"]["portable_transcript_path"]
        self.assertTrue(portable.is_file())
        self.assertEqual(
            sha256_file(portable),
            payload["director_provenance"]["portable_transcript_sha256"],
        )
        with self.assertRaisesRegex(AcceptanceGuardError, "already bound"):
            bind_director(run_dir, "director-pro", transcript_path=pro)

    def test_binding_rejects_wrong_role_or_unbound_assignment(self) -> None:
        run_dir = prepare_run("run-001", "owner", project=self.temp)
        wrong_role = self._transcript(
            run_dir,
            agent_id="wrong-role",
            model="deepseek-v4-pro",
            agent_type="mode-p-dp",
            suffix="wrong-role",
        )
        with self.assertRaisesRegex(AcceptanceGuardError, "mode-p-director"):
            bind_director(run_dir, "wrong-role", transcript_path=wrong_role)

        wrong_run = self._transcript(
            run_dir,
            agent_id="wrong-run",
            model="deepseek-v4-pro",
            agent_type="mode-p-director",
            suffix="wrong-run",
            bind_run=False,
        )
        with self.assertRaisesRegex(AcceptanceGuardError, "run directory"):
            bind_director(run_dir, "wrong-run", transcript_path=wrong_run)

    def test_each_dp_must_be_fresh_and_resolve_to_pro(self) -> None:
        run_dir = prepare_run("run-001", "owner", project=self.temp)
        director = self._transcript(
            run_dir,
            agent_id="director-pro",
            model="deepseek-v4-pro",
            agent_type="mode-p-director",
            suffix="director",
        )
        bind_director(run_dir, "director-pro", transcript_path=director)

        flash = self._transcript(
            run_dir,
            agent_id="dp-flash",
            model="deepseek-v4-flash[1m]",
            agent_type="mode-p-dp",
            suffix="dp-flash",
        )
        with self.assertRaisesRegex(
            AcceptanceGuardError, r"resolvedModel was deepseek-v4-flash\[1m\]"
        ):
            bind_dp(
                run_dir,
                "round-1",
                "dp-flash",
                transcript_path=flash,
            )

        pro = self._transcript(
            run_dir,
            agent_id="dp-pro",
            model="deepseek-v4-pro[1m]",
            agent_type="mode-p-dp",
            suffix="dp-pro",
        )
        payload = bind_dp(
            run_dir,
            "production-1",
            "dp-pro",
            transcript_path=pro,
        )
        self.assertEqual(payload["dp_agents"][0]["model"], "deepseek-v4-pro[1m]")
        dp_provenance = payload["dp_agents"][0]["provenance"]
        self.assertTrue((run_dir / dp_provenance["portable_transcript_path"]).is_file())
        with self.assertRaisesRegex(AcceptanceGuardError, "fresh Agent"):
            bind_dp(
                run_dir,
                "production-2",
                "dp-pro",
                transcript_path=pro,
            )

        exported_path = run_dir / "DP_PRODUCTION_RESPONSE.md"
        exported = export_dp_response(
            run_dir, "production-1", exported_path
        )
        self.assertEqual(
            exported_path.read_text(encoding="utf-8"),
            "READY S1: Shot S1-1 has observable continuity.\n",
        )
        self.assertEqual(
            exported["response_sha256"],
            payload["dp_agents"][0]["response_sha256"],
        )
        with self.assertRaisesRegex(AcceptanceGuardError, "already exists"):
            export_dp_response(run_dir, "production-1", exported_path)
        with self.assertRaisesRegex(AcceptanceGuardError, "inside the acceptance run"):
            export_dp_response(
                run_dir, "production-1", self.temp / "outside-response.md"
            )

        response = self.temp / "dp-response.md"
        response.write_text(
            "READY S1: Shot S1-1 has observable continuity.\n",
            encoding="utf-8",
        )

        scene = run_dir / "episode" / "scenes" / "scene_001"
        self.assertEqual(
            require_acceptance_director_provenance(scene),
            run_dir,
        )
        self.assertEqual(
            require_acceptance_dp_provenance(
                run_dir / "episode" / "batch_reviews" / "batch_001",
                "dp-pro",
                "deepseek-v4-pro",
                response,
            ),
            run_dir,
        )
        with self.assertRaisesRegex(AcceptanceGuardError, "not deepseek-v4-pro"):
            require_acceptance_dp_provenance(
                scene, "dp-pro", "deepseek-v4-flash", response
            )

        response.write_text("READY S1: parent-edited response.\n", encoding="utf-8")
        with self.assertRaisesRegex(AcceptanceGuardError, "differs"):
            require_acceptance_dp_provenance(
                scene, "dp-pro", "deepseek-v4-pro[1m]", response
            )
        response.write_text(
            "READY S1: Shot S1-1 has observable continuity.\n",
            encoding="utf-8",
        )

        (run_dir / dp_provenance["portable_transcript_path"]).write_text(
            "tampered\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(AcceptanceGuardError, "hash mismatch"):
            require_acceptance_dp_provenance(
                scene, "dp-pro", "deepseek-v4-pro[1m]", response
            )

    def test_acceptance_precheck_gate_rejects_unbound_and_invalid_runs(self) -> None:
        run_dir = prepare_run("run-001", "owner", project=self.temp)
        scene = run_dir / "episode" / "scenes" / "scene_001"
        with self.assertRaisesRegex(AcceptanceGuardError, "not valid"):
            require_acceptance_director_provenance(scene)
        invalidate_run(run_dir, "invalid model")
        with self.assertRaisesRegex(AcceptanceGuardError, "run is invalid"):
            require_acceptance_director_provenance(scene)

    def test_invalidate_preserves_attempt_and_returns_status_to_pending(self) -> None:
        run_dir = prepare_run("run-001", "owner", project=self.temp)
        payload = invalidate_run(
            run_dir,
            "actual Director resolvedModel was deepseek-v4-flash",
            now=datetime(2026, 7, 16, tzinfo=timezone.utc),
        )
        self.assertEqual(payload["status"], "invalid")
        invalid = (run_dir / "INVALID_RUN.md").read_text(encoding="utf-8")
        self.assertIn("diagnosis only", invalid)
        status = (self.temp / "MODEL_ACCEPTANCE_STATUS.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("status: pending", status)
        self.assertIn("last_invalid_attempt:", status)
        self.assertIn("new unique run ID", status)

    def test_reopen_then_complete_rejects_unclosed_runtime_state(self) -> None:
        run_dir = prepare_run("run-001", "owner", project=self.temp)
        director = self._transcript(
            run_dir,
            agent_id="director-pro",
            model="deepseek-v4-pro",
            agent_type="mode-p-director",
            suffix="director-reopen",
        )
        bind_director(run_dir, "director-pro", transcript_path=director)
        for review_id, agent_id in (
            ("adversarial-001", "dp-adversarial"),
            ("production-001", "dp-production"),
        ):
            transcript = self._transcript(
                run_dir,
                agent_id=agent_id,
                model="deepseek-v4-pro",
                agent_type="mode-p-dp",
                suffix=agent_id,
            )
            bind_dp(run_dir, review_id, agent_id, transcript_path=transcript)

        bootstrap_path = run_dir / BOOTSTRAP_NAME
        payload = json.loads(bootstrap_path.read_text(encoding="utf-8"))
        payload.update({"status": "passed", "passed_at": "premature"})
        bootstrap_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        reopened = reopen_incomplete_run(
            run_dir,
            "batch DP and episode root states were not closed",
            now=datetime(2026, 7, 18, tzinfo=timezone.utc),
        )
        self.assertEqual(reopened["status"], "director_agent_bound")
        self.assertTrue((run_dir / "PREMATURE_PASS_REPAIR.json").is_file())
        with self.assertRaisesRegex(
            AcceptanceGuardError, "adversarial DP response is missing"
        ):
            complete_run(run_dir)

    def test_complete_never_accepts_a_premarked_pass(self) -> None:
        run_dir = prepare_run("run-001", "owner", project=self.temp)
        payload_path = run_dir / BOOTSTRAP_NAME
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        payload["status"] = "passed"
        payload_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(
            AcceptanceGuardError, "provenance-bound in-progress run"
        ):
            complete_run(run_dir)


if __name__ == "__main__":
    unittest.main()
