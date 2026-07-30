from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from asset_card_registry import (
    AssetCardError,
    refresh_staleness,
    register_card,
    select_relevant_cards,
    select_verified_cards,
)
from asset_indexer import scan_directory


class AssetCardRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="mode_p_cards_")
        self.root = Path(self.temp.name)
        self.assets = self.root / "assets"
        self.assets.mkdir()
        (self.assets / "room.png").write_bytes(b"image-v1")
        self.asset_index = self.root / "ASSET_INDEX.json"
        index = scan_directory(self.assets, self.asset_index)
        self.asset_id = index["assets"][0]["asset_id"]
        self.card_index = self.root / "ASSET_CARD_INDEX.json"
        self.card_index.write_text(json.dumps({
            "schema_version": "1.0",
            "description": "test cards",
            "updated_at": "2026-07-17T00:00:00+00:00",
            "card_count": 0,
            "cards": [],
        }), encoding="utf-8")
        self.analysis = self.root / "analysis.md"
        self.analysis.write_text(
            "Room is 4m wide. Window is on the east wall. Uncertain ceiling height.",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _register(self) -> None:
        register_card(
            self.asset_id,
            self.analysis,
            source="detailed_analysis",
            scope_terms=["room", "interior"],
            allowed_responsibilities=["location", "continuity"],
            asset_index_path=self.asset_index,
            card_index_path=self.card_index,
        )

    def test_verified_card_is_hash_bound_and_selectable_without_media_read(self) -> None:
        self._register()
        packet = select_verified_cards(
            [{"asset_id": self.asset_id, "responsibility": "location"}],
            card_index_path=self.card_index,
            asset_index_path=self.asset_index,
            max_chars=3000,
        )
        self.assertIn("Window is on the east wall", packet)
        self.assertIn(f"{self.asset_id}|location", packet)
        self.assertNotIn("Media SHA-256", packet)

    def test_relevant_selection_uses_scope_terms_and_budget(self) -> None:
        self._register()
        selected = select_relevant_cards(
            "The scene enters the ROOM interior.",
            card_index_path=self.card_index,
            asset_index_path=self.asset_index,
            max_chars=3000,
        )
        self.assertIn(f"Candidate {self.asset_id}", selected)
        self.assertIn("Permitted responsibilities", selected)
        self.assertNotIn("Media SHA-256", selected)
        self.assertEqual(
            select_relevant_cards(
                "A beach at noon.",
                card_index_path=self.card_index,
                asset_index_path=self.asset_index,
            ),
            "",
        )

    def test_changed_media_marks_verified_card_stale(self) -> None:
        self._register()
        (self.assets / "room.png").write_bytes(b"image-v2")
        scan_directory(self.assets, self.asset_index)
        refreshed = refresh_staleness(self.card_index, self.asset_index)
        self.assertEqual(refreshed["cards"][0]["status"], "stale")
        with self.assertRaisesRegex(AssetCardError, "lacks a current verified"):
            select_verified_cards(
                [{"asset_id": self.asset_id, "responsibility": "location"}],
                card_index_path=self.card_index,
                asset_index_path=self.asset_index,
            )

    def test_unallowed_responsibility_and_budget_fail_closed(self) -> None:
        self._register()
        with self.assertRaisesRegex(AssetCardError, "does not allow"):
            select_verified_cards(
                [{"asset_id": self.asset_id, "responsibility": "identity"}],
                card_index_path=self.card_index,
                asset_index_path=self.asset_index,
            )
        with self.assertRaisesRegex(AssetCardError, "context budget"):
            select_verified_cards(
                [{"asset_id": self.asset_id, "responsibility": "location"}],
                card_index_path=self.card_index,
                asset_index_path=self.asset_index,
                max_chars=10,
            )


if __name__ == "__main__":
    unittest.main()
