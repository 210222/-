"""R1.4 — Golden structural expectation constants.

Stable fixture constants, never recomputed at test time from the artifact
under test. These expectations are the authority for the structural runner.
"""

from mode_p_vnext.structural_runner import CaseExpectation

# Canonical artifact SHA-256 values computed from R1.3 production renderers
# with frozen golden_cases.py, storyboard_renderer.py, video_renderer.py.
# These are FIXTURE CONSTANTS — do not recompute at test time.

GOLDEN_EXPECTATIONS = {
    "gun_barrel": CaseExpectation(
        case_id="gun_barrel",
        segment_start_s=0.0,
        segment_end_s=13.0,
        expected_sb_panel_count=13,
        expected_vp_timeline_count=13,
        expected_cut_times=(),
        expected_ref_duties=(
            ("@图片1",  "为分镜参考"),
            ("@rico",   "rico 作为主角，保持外貌服装一致"),
        ),
        prohibition_route="human_qa_only",
        prohibition_body_sha256="202bd0aebb29974e4f47ae3768d0bbdc40e50a4f1a8aa5193fba0f592937d971",
        required_sb_sections=(
            "references", "style", "annotation_legend",
            "shared_visual_anchors", "numbering", "timeline",
        ),
        required_vp_sections=(
            "upload_refs", "reference_duties", "duration",
            "numbering", "arrow_explanation", "storyboard_priority",
            "target_style", "lighting", "timeline",
            "audio", "prohibitions", "transitions",
        ),
        canonical_sb_sha256=(
            "cee4b7a8f7c1b99faa50872ecd5deec0eaaa8bd664a3a8811b80a98f50bf08fc"
        ),
        canonical_vp_sha256=(
            "ee009fd2838cd0e63bfc1e9b43711c52a05b5f70ab69d826e414a6f0ccdf4085"
        ),
        scene_root="gun_barrel",
        contract_fingerprint=(
            "a58d920afecd7a9634b6c0468288ced39b195d5c9b8e025b458fb0889e953eb2"
        ),
        semantic_sources_sha256=(
            "b0c89c360c53c917861e3bbf6ed2437f7fe6755d8527f142bcd882ee71caafd2"
        ),
        expected_segment_id="段2 · 工作室·枪管检查",
        expected_sb_character_refs=("Rico背对镜头",),
        expected_sb_scene_refs=("台灯",),
        expected_sb_prop_refs=(),
        expected_terminal_nodes=(
            ("hold", 13.0, 13.0),
            ("audio", 13.0, 13.0),
        ),
        expected_transitions=(
            "End of segment: tube opening frame held→hum hard cut→"
            "0.3s silence→Segment 3",
            "画面保持→嗡声硬切断→段3",
        ),
        expectation_fingerprint="2af8bc25d6f2e0d7da2833018ecbee00d9f086251833d35220276b10db3a015d",
    ),
    "audience": CaseExpectation(
        case_id="audience",
        segment_start_s=0.0,
        segment_end_s=12.0,
        expected_sb_panel_count=14,  # 12 panels + 2 boundary nodes (sb_node=True)
        expected_vp_timeline_count=12,
        expected_cut_times=(3.0, 8.0),
        expected_ref_duties=(
            ("@图片1", (
                "STORYBOARD_LINEART_场景B.png"
                "(黑白线稿故事板·12格·构图+机位+人物位置参考)"
            )),
            ("@Isabela", (
                "人物/伊莎贝拉・科斯塔（Isabela Costa）.txt"
                "(面部·鹅蛋脸·灰绿色眼睛·暖棕卷发·燕麦色针织开衫)"
            )),
        ),
        prohibition_route="inline_supported",
        prohibition_body_sha256="0cfe10791feea31bd1b0e8ad1a9ef01ddbb77eeb59a32785ee3c2d5bd070ca1c",
        required_sb_sections=(
            "references", "style", "annotation_legend",
            "shared_visual_anchors", "numbering", "timeline",
        ),
        required_vp_sections=(
            "upload_refs", "reference_duties", "duration",
            "numbering", "arrow_explanation", "storyboard_priority",
            "target_style", "lighting", "timeline",
            "audio", "prohibitions", "transitions",
        ),
        canonical_sb_sha256=(
            "7b1b300a257a9302ca6b51e022eb96adeea437d999024bdc2447be9d52f530e1"
        ),
        canonical_vp_sha256=(
            "9f422252e1e1385d161a5cf3164bbc9fb75519f063084f0bac0df0a10a5df341"
        ),
        scene_root="audience",
        contract_fingerprint=(
            "5b2f582e0253c9abc3a57623be078426faffa1e204cf30d4a84420505fc5509f"
        ),
        semantic_sources_sha256=(
            "36774ace5282a1c29490c87b5357a77f32f75112dbe3536104c0e130a8d4d13d"
        ),
        expected_segment_id="段3 · 观众席",
        expected_sb_character_refs=("Isabela",),
        expected_sb_scene_refs=("观众席",),
        expected_sb_prop_refs=(),
        expected_terminal_nodes=(),
        expected_transitions=(
            "格8s→格9s [切]: 切至镜B-3·手机WhatsApp特写。"
            "景别跳跃MCU→ECU(有动机:信息揭示)。",
        ),
        expectation_fingerprint="be92ae296437a87450ed376881384ef8d7cc8cecaf8aa64689e6f1e5fa61d8fa",
    ),
    "prep_area": CaseExpectation(
        case_id="prep_area",
        segment_start_s=0.0,
        segment_end_s=10.0,
        expected_sb_panel_count=10,
        expected_vp_timeline_count=10,
        expected_cut_times=(),
        expected_ref_duties=(
            ("@图片1", (
                "STORYBOARD_LINEART_场景C1.png"
                "(黑白线稿故事板·镜C1-1(7格)+C1-2(10格)·构图+机位参考)"
            )),
        ),
        prohibition_route="inline_supported",
        prohibition_body_sha256="baebbc7aa218f8bfbbcf760290b0309985314a628efbbbf4af59eb885af2de4b",
        required_sb_sections=(
            "references", "style", "annotation_legend",
            "shared_visual_anchors", "numbering", "timeline",
        ),
        required_vp_sections=(
            "upload_refs", "reference_duties", "duration",
            "numbering", "arrow_explanation", "storyboard_priority",
            "target_style", "lighting", "timeline",
            "audio", "prohibitions", "transitions",
        ),
        canonical_sb_sha256=(
            "8ef104a06fbd85fff1c24086bf69686e63542d6470b1225840cdd58dd9677968"
        ),
        canonical_vp_sha256=(
            "83bf4799f9da7cf01633995b5fd3bcea93b88221c576b936872eab990320faf2"
        ),
        scene_root="prep_area",
        contract_fingerprint=(
            "2a3af10f59c5530c3bee74b3c988115b33af6993fbcf89a866ca583db06f6298"
        ),
        semantic_sources_sha256=(
            "c7da5a2ddd36b7fb796fad5c70be15350e73a23d4542b3e349f1cf0a1089e58d"
        ),
        expected_segment_id="段4 · 备赛区",
        expected_sb_character_refs=("Rico", "Iuri"),
        expected_sb_scene_refs=("备赛区",),
        expected_sb_prop_refs=(),
        expected_terminal_nodes=(),
        expected_transitions=("一个走向亮处·一个留在暗处。",),
        expectation_fingerprint="2d8a3a6991f54bded65ed801db75ca1c3213526ec016980658b70ab98aaf77d3",
    ),
    "alley": CaseExpectation(
        case_id="alley",
        segment_start_s=0.0,
        segment_end_s=13.0,
        expected_sb_panel_count=15,  # 13 panels + 2 boundary nodes (sb_node=True)
        expected_vp_timeline_count=13,
        expected_cut_times=(5.0, 9.0),
        expected_ref_duties=(
            ("@图片1", (
                "STORYBOARD_LINEART_场景D.png"
                "(黑白线稿故事板·D-1(6格)+D-2(5格)+D-3(8格)+D-4(5格)"
                "+俯视运动图·构图+机位+人物走位参考)"
            )),
        ),
        prohibition_route="human_qa_only",
        prohibition_body_sha256="82813ce3ac9bcd11d54ba93a925b0e0ec57a4e7982cc58ddc2b1770afa0bed1f",
        required_sb_sections=(
            "references", "style", "annotation_legend",
            "shared_visual_anchors", "numbering", "timeline",
        ),
        required_vp_sections=(
            "upload_refs", "reference_duties", "duration",
            "numbering", "arrow_explanation", "storyboard_priority",
            "target_style", "lighting", "timeline",
            "audio", "prohibitions", "transitions",
        ),
        canonical_sb_sha256=(
            "5244bc264c24c91a2e3902ae4c4900dd1fb2eb417058e596c7e223f5505665f9"
        ),
        canonical_vp_sha256=(
            "ad931e9e900f7446c1cc4eadb03224ab2b31733e42d26f30b911eb99f4de30f4"
        ),
        scene_root="alley",
        contract_fingerprint=(
            "de3c36afaf894f900c253bb31e8fcfaee2938e2543f27f92104934e720c1f0a2"
        ),
        semantic_sources_sha256=(
            "a2a9e3ba503f8fb92dc23d368706db56a543ff0fa73de0ae9e67e30a9ed64aa8"
        ),
        expected_segment_id="段5 · 窄巷",
        expected_sb_character_refs=("Pedro",),
        expected_sb_scene_refs=("窄巷",),
        expected_sb_prop_refs=(),
        expected_terminal_nodes=(),
        expected_transitions=(
            "@转场: 微推近至轿车中近景→落幅静止→切→"
            "场景E·广播声提前0.5秒渗入",
            "落幅静止。黑色轿车·车窗漆黑·无声·静止。",
        ),
        expectation_fingerprint="167f511c9bba318f9a311a722ec8d564bd298cd1a522619d71e143131c42b3a3",
    ),
}
