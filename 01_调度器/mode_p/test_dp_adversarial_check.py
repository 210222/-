from __future__ import annotations

import unittest

from dp_adversarial_check import validate_adversarial_response


COMPLETE = """\
ADV_S1-1: camera_path - The path crosses the desk volume.
ADV_S1-1: light_source - The wall light has no physical source.
ADV_S1-1: prompt_visibility - The image contains an unresolved camera branch.
ADV_S1-2: boundary_continuity - The continuous handoff changes Mara from right to left.
ADV_S1-2: view_sync - Storyboard and video disagree on coat color and the prior action.
"""


class AdversarialDpCheckTests(unittest.TestCase):
    def test_complete_review_passes(self) -> None:
        self.assertEqual(validate_adversarial_response(COMPLETE), [])

    def test_unresolved_branch_may_be_reported_as_camera_path(self) -> None:
        text = COMPLETE.replace(
            "ADV_S1-1: camera_path - The path crosses the desk volume.\n",
            "ADV_S1-1: spatial_feasibility - The path crosses the desk volume.\n",
        ).replace(
            "ADV_S1-1: prompt_visibility - The image contains an unresolved camera branch.\n",
            "ADV_S1-1: camera_path - The camera instruction contains an unresolved branch.\n",
        )

        self.assertEqual(validate_adversarial_response(text), [])

    def test_ready_fails(self) -> None:
        text = "READY ADV_S1: Shot ADV_S1-1 has an executable camera path and light."
        self.assertTrue(validate_adversarial_response(text))

    def test_missing_category_fails(self) -> None:
        self.assertTrue(
            validate_adversarial_response(
                COMPLETE.replace(
                    "ADV_S1-2: view_sync - Storyboard and video disagree on coat color and the prior action.\n",
                    "",
                )
            )
        )


if __name__ == "__main__":
    unittest.main()
