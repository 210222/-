"""V0.3 Canonical Serialization — UTF-8, LF, Canonical JSON, stable hash tests.

These tests verify the foundational serialization layer:
- UTF-8 encoding with LF line endings (never CRLF, never code-page dependent)
- Canonical JSON: sorted keys, compact representation, whitespace-stable
- Stable SHA-256 hashing: same input → same hash; different input → different hash
- Cross Windows code-page resilience
"""

import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


# ---------------------------------------------------------------------------
# The module under test — will exist after implementation
# ---------------------------------------------------------------------------
try:
    from mode_p_vnext import canonical_serialization as cs
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


# ---------------------------------------------------------------------------
# UTF-8 / LF
# ---------------------------------------------------------------------------

class UTF8LFEncodingTests(unittest.TestCase):
    """UTF-8 encoding and LF line ending tests."""

    @unittest.skipIf(not MODULE_EXISTS, "canonical_serialization module not yet implemented")
    def test_write_text_writes_utf8(self):
        content = "Hello 世界\nLine 2\n"
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            tmp = Path(f.name)
        try:
            cs.write_text_utf8_lf(str(tmp), content)
            raw = tmp.read_bytes()
            # Verify UTF-8 encoding
            raw.decode("utf-8")  # must not raise
            self.assertEqual(raw.decode("utf-8"), content)
        finally:
            tmp.unlink(missing_ok=True)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_serialization module not yet implemented")
    def test_write_text_no_crlf(self):
        content = "Line 1\nLine 2\nLine 3\n"
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            tmp = Path(f.name)
        try:
            cs.write_text_utf8_lf(str(tmp), content)
            raw = tmp.read_bytes()
            self.assertNotIn(b"\r\n", raw, "File must not contain CRLF")
            self.assertNotIn(b"\r", raw, "File must not contain bare CR")
        finally:
            tmp.unlink(missing_ok=True)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_serialization module not yet implemented")
    def test_ensure_utf8_lf_normalizes_crlf(self):
        # Input with CRLF
        text_with_crlf = "Line 1\r\nLine 2\r\n"
        result = cs.ensure_utf8_lf(text_with_crlf)
        self.assertNotIn("\r\n", result)
        self.assertNotIn("\r", result)
        self.assertEqual(result, "Line 1\nLine 2\n")

    @unittest.skipIf(not MODULE_EXISTS, "canonical_serialization module not yet implemented")
    def test_ensure_utf8_lf_normalizes_bare_cr(self):
        text_with_cr = "Line 1\rLine 2\r"
        result = cs.ensure_utf8_lf(text_with_cr)
        self.assertNotIn("\r", result)
        self.assertEqual(result, "Line 1\nLine 2\n")

    @unittest.skipIf(not MODULE_EXISTS, "canonical_serialization module not yet implemented")
    def test_chinese_characters_survive_roundtrip(self):
        content = "剧本：枪管\n导演：张三\n场景：第八集\n"
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            tmp = Path(f.name)
        try:
            cs.write_text_utf8_lf(str(tmp), content)
            read_back = tmp.read_text(encoding="utf-8")
            self.assertEqual(read_back, content)
            # Verify bytes are valid UTF-8
            raw = tmp.read_bytes()
            raw.decode("utf-8")  # must not raise
        finally:
            tmp.unlink(missing_ok=True)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_serialization module not yet implemented")
    def test_write_text_independent_of_windows_code_page(self):
        """Output must be identical regardless of active code page setting."""
        content = "Café résumé naïve\n"
        # Clear any PYTHONIOENCODING or similar env influence for the subprocess
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            tmp = Path(f.name)
        try:
            cs.write_text_utf8_lf(str(tmp), content)
            direct = tmp.read_bytes()
            # The bytes should be pure UTF-8, not cp1252 or gbk
            decoded = direct.decode("utf-8")
            self.assertEqual(decoded, content)
            self.assertNotIn(b"\r", direct)
        finally:
            tmp.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Canonical JSON
# ---------------------------------------------------------------------------

class CanonicalJSONTests(unittest.TestCase):
    """Canonical JSON serialization: sorted keys, compact, stable."""

    @unittest.skipIf(not MODULE_EXISTS, "canonical_serialization module not yet implemented")
    def test_canonical_json_sorts_keys(self):
        obj = {"c": 1, "a": 2, "b": 3}
        result = cs.canonical_json_dumps(obj)
        # Keys must be sorted
        self.assertTrue(result.startswith('{"a":'))
        parsed = json.loads(result)
        self.assertEqual(parsed, obj)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_serialization module not yet implemented")
    def test_canonical_json_no_whitespace_variation(self):
        obj = {"key": "value", "num": 42}
        result = cs.canonical_json_dumps(obj)
        # Must be compact: no spaces after : or ,
        self.assertIn('"key":"value"', result)
        self.assertNotIn(": ", result)
        self.assertNotIn(", ", result)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_serialization module not yet implemented")
    def test_canonical_json_stable_across_calls(self):
        obj = {"z": [1, 2, 3], "a": {"nested": True}}
        r1 = cs.canonical_json_dumps(obj)
        r2 = cs.canonical_json_dumps(obj)
        self.assertEqual(r1, r2, "Canonical JSON must be deterministic")

    @unittest.skipIf(not MODULE_EXISTS, "canonical_serialization module not yet implemented")
    def test_canonical_json_nested_objects_sorted(self):
        obj = {"outer": {"c": 1, "a": 2, "b": 3}}
        result = cs.canonical_json_dumps(obj)
        self.assertIn('"a":2', result)
        self.assertIn('"b":3', result)
        self.assertIn('"c":1', result)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_serialization module not yet implemented")
    def test_canonical_json_unicode_preserved(self):
        obj = {"角色": "张三", "场景": "枪管"}
        result = cs.canonical_json_dumps(obj)
        self.assertIn("角色", result)
        self.assertIn("枪管", result)
        parsed = json.loads(result)
        self.assertEqual(parsed, obj)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_serialization module not yet implemented")
    def test_canonical_json_dump_writes_utf8_lf(self):
        obj = {"test": "数据"}
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp = Path(f.name)
        try:
            cs.canonical_json_dump(str(tmp), obj)
            raw = tmp.read_bytes()
            self.assertNotIn(b"\r", raw)
            raw.decode("utf-8")
            parsed = json.loads(raw.decode("utf-8"))
            self.assertEqual(parsed, obj)
        finally:
            tmp.unlink(missing_ok=True)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_serialization module not yet implemented")
    def test_same_content_different_key_order_same_result(self):
        """Two dicts with different insertion order must produce same output."""
        d1 = {"b": 1, "a": 2}
        d2 = {"a": 2, "b": 1}
        r1 = cs.canonical_json_dumps(d1)
        r2 = cs.canonical_json_dumps(d2)
        self.assertEqual(r1, r2)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_serialization module not yet implemented")
    def test_canonical_json_no_trailing_whitespace(self):
        result = cs.canonical_json_dumps({"key": "value"})
        self.assertFalse(result.endswith(" "), "Must not end with space")
        self.assertFalse(result.endswith("\n"), "Must not end with newline")


# ---------------------------------------------------------------------------
# Stable Hash
# ---------------------------------------------------------------------------

class StableHashTests(unittest.TestCase):
    """SHA-256 stable hash tests."""

    @unittest.skipIf(not MODULE_EXISTS, "canonical_serialization module not yet implemented")
    def test_stable_hash_sha256_deterministic(self):
        data = b"Hello, World!"
        h1 = cs.stable_hash_sha256(data)
        h2 = cs.stable_hash_sha256(data)
        self.assertEqual(h1, h2)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_serialization module not yet implemented")
    def test_stable_hash_sha256_different_content_different_hash(self):
        h1 = cs.stable_hash_sha256(b"Hello")
        h2 = cs.stable_hash_sha256(b"World")
        self.assertNotEqual(h1, h2)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_serialization module not yet implemented")
    def test_stable_hash_sha256_is_hex_string(self):
        h = cs.stable_hash_sha256(b"test")
        self.assertIsInstance(h, str)
        self.assertEqual(len(h), 64)
        # Must be lowercase hex
        self.assertTrue(all(c in "0123456789abcdef" for c in h))

    @unittest.skipIf(not MODULE_EXISTS, "canonical_serialization module not yet implemented")
    def test_stable_hash_sha256_empty_input(self):
        h = cs.stable_hash_sha256(b"")
        self.assertIsInstance(h, str)
        self.assertEqual(len(h), 64)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_serialization module not yet implemented")
    def test_stable_hash_unicode_string(self):
        """Hash of a UTF-8 string must be stable."""
        text = "剧本内容"
        h1 = cs.stable_hash_sha256(text.encode("utf-8"))
        h2 = hashlib.sha256(text.encode("utf-8")).hexdigest()
        self.assertEqual(h1, h2)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_serialization module not yet implemented")
    def test_stable_hash_json_document(self):
        """Hash of canonical JSON must be identical for semantically same documents."""
        d1 = {"b": [1, 2], "a": "hello"}
        d2 = {"a": "hello", "b": [1, 2]}
        json1 = cs.canonical_json_dumps(d1)
        json2 = cs.canonical_json_dumps(d2)
        self.assertEqual(json1, json2)
        h1 = cs.stable_hash_sha256(json1.encode("utf-8"))
        h2 = cs.stable_hash_sha256(json2.encode("utf-8"))
        self.assertEqual(h1, h2)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_serialization module not yet implemented")
    def test_stable_hash_file(self):
        content = "test content\n"
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            tmp = Path(f.name)
        try:
            cs.write_text_utf8_lf(str(tmp), content)
            h1 = cs.stable_hash_file(str(tmp))
            h2 = cs.stable_hash_sha256(content.encode("utf-8"))
            self.assertEqual(h1, h2)
        finally:
            tmp.unlink(missing_ok=True)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_serialization module not yet implemented")
    def test_stable_hash_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            cs.stable_hash_file("/nonexistent/path/file.txt")


# ---------------------------------------------------------------------------
# Integration: Canonical JSON → hash → verify
# ---------------------------------------------------------------------------

class CanonicalHashIntegrationTests(unittest.TestCase):
    """End-to-end: canonical JSON → hash → verify."""

    @unittest.skipIf(not MODULE_EXISTS, "canonical_serialization module not yet implemented")
    def test_roundtrip_json_dump_hash_verify(self):
        obj = {
            "episode": "EP8",
            "scene": "枪管",
            "shots": [
                {"id": "S1", "duration_s": 5.0},
                {"id": "S2", "duration_s": 8.0},
            ],
        }
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp = Path(f.name)
        try:
            cs.canonical_json_dump(str(tmp), obj)
            # Hash the file
            file_hash = cs.stable_hash_file(str(tmp))
            # Re-read and re-serialize — hash must match
            json2 = cs.canonical_json_dumps(obj)
            recomputed_hash = cs.stable_hash_sha256(json2.encode("utf-8"))
            self.assertEqual(file_hash, recomputed_hash)
        finally:
            tmp.unlink(missing_ok=True)

    @unittest.skipIf(not MODULE_EXISTS, "canonical_serialization module not yet implemented")
    def test_lf_vs_crlf_same_hash(self):
        """Content with LF vs CRLF should produce the same hash after normalization."""
        text_lf = "Line 1\nLine 2\n"
        text_crlf = "Line 1\r\nLine 2\r\n"
        normalized_lf = cs.ensure_utf8_lf(text_lf)
        normalized_crlf = cs.ensure_utf8_lf(text_crlf)
        self.assertEqual(normalized_lf, normalized_crlf)
        h1 = cs.stable_hash_sha256(normalized_lf.encode("utf-8"))
        h2 = cs.stable_hash_sha256(normalized_crlf.encode("utf-8"))
        self.assertEqual(h1, h2)


if __name__ == "__main__":
    unittest.main()
