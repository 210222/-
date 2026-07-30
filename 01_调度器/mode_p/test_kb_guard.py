from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HOOK = ROOT / ".claude" / "hooks" / "kb-guard.py"


def run_hook(tool_input: dict[str, str]) -> dict[str, object]:
    payload = json.dumps({"tool_input": tool_input}, ensure_ascii=False)
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout)


class KbGuardTests(unittest.TestCase):
    def test_blocks_rule_id_in_canonical_prompt_name(self) -> None:
        result = run_hook({"file_path": "session/delivery/VIDEO_PROMPT.md", "content": "使用 D-TRI-01。"})
        self.assertFalse(result["continue"])

    def test_checks_edit_new_string(self) -> None:
        result = run_hook({"file_path": "session/working/STORYBOARD.md", "new_string": "KB: internal"})
        self.assertFalse(result["continue"])

    def test_allows_internal_master(self) -> None:
        result = run_hook({"file_path": "session/DIRECTOR_MASTER.md", "content": "D-TRI-01"})
        self.assertTrue(result["continue"])


if __name__ == "__main__":
    unittest.main()
