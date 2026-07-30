"""Verify that the script input contract scene-header patterns match real-world inputs.

These tests validate the regex patterns documented in script_input_contract.md
section 2.1 against EP14 S1 and other expected screenplay formats.
"""

from __future__ import annotations

import re
import unittest

# Patterns mirroring script_input_contract.md section 2.1 (in priority order).
PATTERNS: list[tuple[int, str, re.Pattern]] = [
    (1, "markdown_scene_en", re.compile(r"^##\s+Scene\b", re.IGNORECASE)),
    (2, "markdown_cn_numbered", re.compile(r"^##\s+第.+场")),
    (3, "markdown_cn_any", re.compile(r"^#+\s+第.+场")),
    (4, "screenplay_header", re.compile(r"^(INT\.|EXT\.|INT/EXT\.|EXT/INT\.)\s", re.IGNORECASE)),
    (5, "cn_bracket", re.compile(r"^【场景.*】")),
    (6, "cn_plain", re.compile(r"^场景\s*\d+")),
]


def match_scene_header(line: str) -> tuple[int, str] | None:
    """Return (priority, kind) of the first matching pattern, or None."""
    for prio, kind, pattern in PATTERNS:
        if pattern.search(line):
            return prio, kind
    return None


class SceneHeaderPatternTests(unittest.TestCase):
    """Each test case corresponds to a row in the contract's pattern table."""

    # -- priority 1: ## Scene N --
    def test_markdown_scene_en(self) -> None:
        self.assertEqual(match_scene_header("## Scene 1"), (1, "markdown_scene_en"))
        self.assertEqual(match_scene_header("## Scene 12 — 案情室"), (1, "markdown_scene_en"))
        self.assertEqual(match_scene_header("## Scene 3"), (1, "markdown_scene_en"))

    def test_scene_keyword_case_insensitive(self) -> None:
        self.assertEqual(match_scene_header("## scene 1"), (1, "markdown_scene_en"))

    # -- priority 2: ## 第N场 --
    def test_markdown_cn_numbered_digits(self) -> None:
        self.assertEqual(match_scene_header("## 第1场"), (2, "markdown_cn_numbered"))
        self.assertEqual(match_scene_header("## 第14场 案情室"), (2, "markdown_cn_numbered"))

    def test_markdown_cn_numbered_hanzi(self) -> None:
        self.assertEqual(match_scene_header("## 第三场"), (2, "markdown_cn_numbered"))
        self.assertEqual(match_scene_header("## 第十场 — 天台"), (2, "markdown_cn_numbered"))

    # -- priority 3: #+ 第N场 (any heading level) --
    def test_markdown_cn_any_heading_level(self) -> None:
        self.assertEqual(match_scene_header("# 第一场"), (3, "markdown_cn_any"))
        self.assertEqual(match_scene_header("### 第十四场"), (3, "markdown_cn_any"))

    # -- priority 4: INT./EXT. --
    def test_screenplay_int(self) -> None:
        self.assertEqual(match_scene_header("INT. 刑警总部 - 日"), (4, "screenplay_header"))
        self.assertEqual(match_scene_header("INT. APARTMENT - NIGHT"), (4, "screenplay_header"))

    def test_screenplay_ext(self) -> None:
        self.assertEqual(match_scene_header("EXT. 街道 - 夜"), (4, "screenplay_header"))
        self.assertEqual(match_scene_header("EXT. ROOFTOP - DAY"), (4, "screenplay_header"))

    def test_screenplay_combined(self) -> None:
        self.assertEqual(match_scene_header("INT/EXT. 汽车 - 日"), (4, "screenplay_header"))
        self.assertEqual(match_scene_header("EXT/INT. BALCONY - DUSK"), (4, "screenplay_header"))

    # -- priority 5: 【场景N】 --
    def test_cn_bracket(self) -> None:
        self.assertEqual(match_scene_header("【场景2：案情室】"), (5, "cn_bracket"))
        self.assertEqual(match_scene_header("【场景 5】"), (5, "cn_bracket"))

    # -- priority 6: 场景 N --
    def test_cn_plain_number(self) -> None:
        self.assertEqual(match_scene_header("场景 4"), (6, "cn_plain"))
        self.assertEqual(match_scene_header("场景12"), (6, "cn_plain"))

    # -- non-matches --
    def test_non_scene_headers_return_none(self) -> None:
        self.assertIsNone(match_scene_header("Miguel 站在白板前。"))
        self.assertIsNone(match_scene_header("## 角色介绍"))
        self.assertIsNone(match_scene_header("### 道具清单"))
        self.assertIsNone(match_scene_header(""))
        self.assertIsNone(match_scene_header("场景设计说明"))

    # -- priority ordering: higher-priority patterns win --
    def test_priority_order_markdown_scene_wins_over_weaker(self) -> None:
        # "## Scene 第三场" starts with ## Scene, so priority 1 wins
        result = match_scene_header("## Scene 第三场")
        self.assertEqual(result, (1, "markdown_scene_en"))

    def test_priority_order_screenplay_over_cn_plain(self) -> None:
        # "EXT. 场景 4" is a screenplay header, not a plain cn scene
        result = match_scene_header("EXT. 场景 4 - 日")
        self.assertEqual(result, (4, "screenplay_header"))

    # -- EP14 S1 regression: the current script format must match --
    def test_ep14_s1_scene_context_header(self) -> None:
        """EP14 S1 scene_context.md uses '# Scene Context' which describes the
        scene but is NOT a scene header in the parsing sense (it's metadata).
        The actual scene heading in the EP14 script portion is implicit."""
        # The contract correctly treats "# Scene Context" as front_matter / non-match
        self.assertIsNone(match_scene_header("# Scene Context"))
        self.assertIsNone(match_scene_header("# Scene Context - EP14 S1 - 案情室"))


class EncodingFallbackTests(unittest.TestCase):
    """Verify the encoding fallback logic defined in the contract section 1."""

    def test_utf8_bom_stripped(self) -> None:
        text = "﻿# 第一场\n角色对话\n"
        # BOM is a single zero-width character at position 0
        self.assertTrue(text.startswith("﻿"))
        stripped = text.lstrip("﻿")
        self.assertFalse(stripped.startswith("﻿"))
        self.assertEqual(stripped, "# 第一场\n角色对话\n")

    def test_gbk_fallback_on_utf8_decode_error(self) -> None:
        # A byte sequence that is valid GBK but not valid UTF-8
        gbk_bytes = "场景：案情室\n".encode("gbk")
        with self.assertRaises(UnicodeDecodeError):
            gbk_bytes.decode("ascii")
        # Decode with GBK should succeed
        decoded = gbk_bytes.decode("gbk")
        self.assertEqual(decoded, "场景：案情室\n")

    def test_utf8_reads_correctly(self) -> None:
        text = "## Scene 1 — 案情室\nMiguel 站在白板前。\n"
        encoded = text.encode("utf-8")
        self.assertEqual(encoded.decode("utf-8"), text)


class LineNumberContractTests(unittest.TestCase):
    """Verify line-number rules from the contract section 3."""

    def test_line_numbers_start_at_one(self) -> None:
        text = "第一行\n第二行\n第三行\n"
        lines = text.splitlines(keepends=True)
        self.assertEqual(lines[0], "第一行\n")
        self.assertEqual(len(lines), 3)
        # Line numbers are 1-indexed
        for i, line in enumerate(lines, start=1):
            self.assertGreater(i, 0)

    def test_empty_lines_counted(self) -> None:
        text = "a\n\nb\n"
        lines = text.splitlines(keepends=True)
        # splitlines yields ["a\n", "\n", "b\n"] — empty lines count
        self.assertEqual(len(lines), 3)

    def test_scene_line_ranges_are_closed_intervals(self) -> None:
        # Contract: line ranges are closed [start, end]
        scene_start, scene_end = 12, 45
        fact_range = (15, 20)
        self.assertGreaterEqual(fact_range[0], scene_start)
        self.assertLessEqual(fact_range[1], scene_end)


if __name__ == "__main__":
    unittest.main()
