"""V7.4 Targeted Revision & Affected Boundary."""

import unittest

try:
    from mode_p_vnext import targeted_revision as tr
    from mode_p_vnext import dp_response_contract as dp
    from mode_p_vnext import dp_manifest as dm
    from mode_p_vnext import dp_revision_router as router
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class TargetedRevisionTests(unittest.TestCase):
    @unittest.skipIf(not MODULE_EXISTS, "targeted_revision not yet implemented")
    def test_revision_targets_specific_objects(self):
        r = tr.TargetedRevision(
            revision_id="REV001",
            director_id="DIRECTOR_EP8",
            modified_objects=["shot S2", "boundary B2"],
            affected_boundaries=["B1→B2", "B2→B3"],
        )
        self.assertIn("shot S2", r.modified_objects)
        self.assertIn("B1→B2", r.affected_boundaries)

    @unittest.skipIf(not MODULE_EXISTS, "targeted_revision not yet implemented")
    def test_same_director_required(self):
        r = tr.TargetedRevision(
            revision_id="REV002",
            director_id="DIRECTOR_EP8",
            modified_objects=["shot S1"],
            affected_boundaries=[],
        )
        self.assertTrue(r.requires_same_director)

    @unittest.skipIf(not MODULE_EXISTS, "targeted_revision not yet implemented")
    def test_fresh_dp_context_required(self):
        r = tr.TargetedRevision(
            revision_id="REV003",
            director_id="DIRECTOR_EP8",
            modified_objects=[],
            affected_boundaries=[],
            fresh_dp_required=True,
        )
        self.assertTrue(r.fresh_dp_required)

    def _topology(self, *, frozen=()):
        return tr.RevisionTopology(
            director_id="DIRECTOR_EP8",
            object_ids=("shot:S1", "shot:S2", "shot:S3", "shot:S4", "shot:S5"),
            boundary_endpoints={
                "B1": ("shot:S1", "shot:S2"),
                "B2": ("shot:S2", "shot:S3"),
                "B7": ("shot:S4", "shot:S5"),
            },
            frozen_segment_ids=tuple(frozen),
            object_segment_ids={"shot:S1": "SEG1", "shot:S2": "SEG1", "shot:S3": "SEG1"},
        )

    def _response(self):
        return dp.DPResponse(
            response_id="DPR-S2", verdict="DIRECTED_QUESTION",
            issues=[dp.DPIssue(
                issue_id="I-S2", question="Is the object surface visible in this shot?",
                bound_to_shot="S2",
            )],
        )

    @unittest.skipIf(not MODULE_EXISTS, "targeted_revision not yet implemented")
    def test_only_bound_shot_and_adjacent_boundaries_can_change(self):
        revision = tr.TargetedRevision(
            revision_id="REV-S2", director_id="DIRECTOR_EP8", modified_objects=["shot S2"],
            affected_boundaries=["B1", "B2"], source_response_id="DPR-S2", source_issue_ids=["I-S2"],
            parent_context_id="CTX-OLD", fresh_context_id="CTX-NEW",
            base_contract_sha256="a", revised_contract_sha256="b",
        )
        tr.validate_targeted_revision(revision, self._response(), self._topology())
        revision.modified_objects = ["shot S1"]
        with self.assertRaises(tr.RevisionScopeError):
            tr.validate_targeted_revision(revision, self._response(), self._topology())
        revision.modified_objects = ["shot S2"]
        revision.affected_boundaries = ["B7"]
        with self.assertRaises(tr.RevisionScopeError):
            tr.validate_targeted_revision(revision, self._response(), self._topology())

    @unittest.skipIf(not MODULE_EXISTS, "targeted_revision not yet implemented")
    def test_frozen_segment_and_input_block_cannot_route_to_revision(self):
        revision = tr.TargetedRevision(
            revision_id="REV-FROZEN", director_id="DIRECTOR_EP8", modified_objects=["shot S2"],
            source_response_id="DPR-S2", source_issue_ids=["I-S2"],
            parent_context_id="CTX-OLD", fresh_context_id="CTX-NEW",
            base_contract_sha256="a", revised_contract_sha256="b",
        )
        with self.assertRaises(tr.RevisionScopeError):
            tr.validate_targeted_revision(revision, self._response(), self._topology(frozen=("SEG1",)))
        block = dp.DPResponse(
            response_id="DPR-BLOCK", verdict="INPUT_BLOCK",
            issues=[dp.DPIssue(issue_id="I-BLOCK", question="Missing fact binding.", bound_to_segment="SEG1")],
        )
        with self.assertRaises(tr.RevisionScopeError):
            tr.targeted_revision_from_dp(
                "REV-BLOCK", block, self._topology(), director_id="DIRECTOR_EP8",
                parent_context_id="CTX-A", fresh_context_id="CTX-B",
            )

    @unittest.skipIf(not MODULE_EXISTS, "targeted_revision not yet implemented")
    def test_production_router_binds_manifest_same_director_and_fresh_context(self):
        manifest = dm.create_dp_packet_manifest("DPM-ROUTE", {"storyboard_view": "panel"}, context_id="CTX-ROUTE")
        response = dp.DPResponse(
            response_id="DPR-ROUTE", verdict="DIRECTED_QUESTION", context_id="CTX-ROUTE",
            manifest_sha256=manifest.content_sha256,
            issues=[dp.DPIssue(issue_id="I-ROUTE", question="Is the current surface visible?", bound_to_shot="S2")],
        )
        route = router.route_dp_revision(
            revision_id="REV-ROUTE", response=response, manifest=manifest, topology=self._topology(),
            persistent_director_id="DIRECTOR_EP8", base_contract_sha256="a" * 64,
            revised_contract_sha256="b" * 64, modified_objects=["shot S2"], affected_boundaries=["B1"],
        )
        self.assertEqual(route.revision.director_id, "DIRECTOR_EP8")
        self.assertNotEqual(route.source_context_id, route.next_context_id)
        with self.assertRaises(router.DPRevisionRouteError):
            router.route_dp_revision(
                revision_id="REV-WRONG", response=response, manifest=manifest, topology=self._topology(),
                persistent_director_id="OTHER_DIRECTOR", base_contract_sha256="a" * 64,
                revised_contract_sha256="b" * 64, modified_objects=["shot S2"],
            )


if __name__ == "__main__":
    unittest.main()
