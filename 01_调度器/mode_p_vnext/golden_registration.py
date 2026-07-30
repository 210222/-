"""MODE:P vNext — Four Golden Case Structured Registration (V8.1).

Registers prompts, storyboards, videos, responsibilities, and user quality
evaluations for the four Golden scenes. Cross-references V0.5 fixture hashes.

Spec references: LOOP §13; Golden Evidence Report.
"""

from __future__ import annotations

from typing import Any, Dict, List, TypedDict


class GoldenCaseRegistration(TypedDict):
    scene_name: str
    episode: str
    storyboard_prompt_ref: str
    video_prompt_ref: str
    storyboard_image_sha256: str
    video_sha256: str
    user_statement: str
    audit_classification: str
    evidence_roles: List[str]


GOLDEN_CASES: Dict[str, GoldenCaseRegistration] = {
    "gun_barrel_ep8": {
        "scene_name": "第八集枪管",
        "episode": "EP8",
        "storyboard_prompt_ref": "GOLDEN_SET_EVIDENCE_REPORT.md §6.2",
        "video_prompt_ref": "GOLDEN_SET_EVIDENCE_REPORT.md §6.4",
        "storyboard_image_sha256": "d995353f808a26cdaa360ea174baeaed0f84c6390c26314f6915e7f255c3ac1b",
        "video_sha256": "3b405440ea1723c32081568fe6f99e8275550be081f007af90b0689e5ea336c9",
        "user_statement": "单一注意力路径成功执行——连续摄影从背影到管内金属落幅，视频未将管内结构渲染为魔幻隧道。",
        "audit_classification": (
            "INFERENCE: 设计只有一条注意力收缩链，且同一链被时间、编号、箭头、焦段、"
            "构图和文字多次编码。模型自由度集中在运动平滑度而非事件路径。"
        ),
        "evidence_roles": [
            "continuous_attention_contraction",
            "single_shot_no_cut",
            "storyboard_video_correction",
        ],
    },
    "audience_ep6": {
        "scene_name": "第六集观众席",
        "episode": "EP6",
        "storyboard_prompt_ref": "GOLDEN_SET_EVIDENCE_REPORT.md §7.2",
        "video_prompt_ref": "GOLDEN_SET_EVIDENCE_REPORT.md §7.4",
        "storyboard_image_sha256": "59595027cd4a75c09727431f33a40ac615a9c7c44b45c58696367fbd7b0bbe1d",
        "video_sha256": "8fee5725cb1d4289133f2a11c5d1e59881a01bc60302daf29e4e9dcc9e420459",
        "user_statement": "切镜结构被视频模型成功执行——一个视频内出现两次真实硬切。景别递进清晰：WS环境→双人中景→手机特写。",
        "audit_classification": (
            "INFERENCE: 三镜结构同时存在于编号、时间范围、故事板构图、切镜分隔、"
            "景别跳跃和信息尺度递进中。一个Generation Segment内存在多个"
            "Cinematic Shot是已被实际视频验证的能力。手机UI存在生成补全泄漏——"
            "模型自动补充了额外灰色回复气泡。"
        ),
        "evidence_roles": [
            "internal_cuts_in_generation_segment",
            "scale_progression_ws_to_ecu",
            "ai_ui_risk_mitigation",
        ],
    },
    "prep_area_ep6": {
        "scene_name": "第六集备赛区擦肩",
        "episode": "EP6",
        "storyboard_prompt_ref": "GOLDEN_SET_EVIDENCE_REPORT.md §9.2",
        "video_prompt_ref": "GOLDEN_SET_EVIDENCE_REPORT.md §9.4",
        "storyboard_image_sha256": "96487289a5f5c6b226737b70b6d90026fac62544c0ddc99c4391c005b2678bd6",
        "video_sha256": "4108f6dcf0c51d88c42f134054705e8296cd5926c61d80dce7c32e022ec9401a",
        "user_statement": (
            "构图成功——人物空间关系和擦肩动作清晰。固定机位、明暗空间对角关系成立。"
        ),
        "audit_classification": (
            "INFERENCE: 设计始终为单一连续固定机位镜头（§9.1确认：一个固定机位，"
            "一个连续镜头）。实际失败为时序偏移（伊乌里约2.5s入画而非5s）和"
            "行为偏移（伊乌里约4s回头看Rico而非不看）。视频持续9.04s而非~10s。"
            "微表演（嘴角微表情）在当前机位不可见。此样本是诊断时序/行为偏移"
            "与Golden Expectation差距的关键案例。"
        ),
        "evidence_roles": [
            "composition_success_timing_deviation",
            "shoulder_brush_spatial_clarity",
            "early_entrance_diagnostic",
            "behavior_deviation_diagnostic",
        ],
    },
    "alley_ep6": {
        "scene_name": "第六集贫民窟窄巷",
        "episode": "EP6",
        "storyboard_prompt_ref": "GOLDEN_SET_EVIDENCE_REPORT.md §8.2",
        "video_prompt_ref": "GOLDEN_SET_EVIDENCE_REPORT.md §8.4",
        "storyboard_image_sha256": "e749c64c5536e4b279c539f2444079d10a0225497606bba69bb2d6d557412839",
        "video_sha256": "0df347a25f69175ba50d79d3e48a26978db73ec1c0cd59ef30ca2c56dcd372ce",
        "user_statement": (
            "用户明确高度评价运镜——'最后一组的运镜和效果非常好'。"
            "事件拓扑被忠实保留：追球→Pedro→天空→直升机→轿车顺序完整。"
        ),
        "audit_classification": (
            "INFERENCE: 模型改变的是节点连接方式而非事件顺序、运动方向或落幅。"
            "非字面执行（直升机独立切镜、取消9s机械硬切、连续重构完成注意力交接）"
            "属于受控优化（OPTIMIZABLE），不应判为失败。证明'锁定节点+弹性连接'模式可行。"
        ),
        "evidence_roles": [
            "narrative_topology_preserved",
            "connection_optimization_allowed",
            "user_high_evaluation_camera_movement",
        ],
    },
}
