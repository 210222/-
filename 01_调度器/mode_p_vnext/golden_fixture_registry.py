"""MODE:P vNext — Golden Fixture Registry (V0.5).

Structured index of the four Golden scenes used for calibration and validation.
Each entry records text evidence, image/video reference hashes, user evaluations
and evidence roles WITHOUT loading media binaries.

Data sources:
- V0.1 baseline manifest (media hashes and metadata)
- GOLDEN_SET_EVIDENCE_REPORT.md (user evaluations, scene analysis)
- LOOP §13 (§13.2–§13.5) — golden expectations and knowledge questions

Spec references: LOOP §5, §13; Golden Evidence Report.
"""

from typing import Any, Dict, List, TypedDict


# ---------------------------------------------------------------------------
# Type hints
# ---------------------------------------------------------------------------

class MediaRef(TypedDict):
    path: str
    sha256: str
    width: int
    height: int
    format: str


class UserEvaluation(TypedDict):
    """Structured user evaluation separating direct statements from inferences.

    Evidence-report §2 hierarchy requires tier separation:
    - user_statement: direct user quote or paraphrase (A-level evidence)
    - audit_classification: expert inference labeled as such (B/C-level)
    - composition_result: success | deviation | failure
    - timing_result: success | deviation | failure
    - behavior_result: success | deviation | failure | n/a
    """
    user_statement: str
    audit_classification: str
    composition_result: str
    timing_result: str
    behavior_result: str


class GoldenSceneFixture(TypedDict):
    scene_id: str
    episode: str
    description: str
    storyboard_image: MediaRef
    video: MediaRef
    user_evaluation: UserEvaluation
    golden_expectations: List[str]
    evidence_roles: List[str]
    knowledge_questions: List[str]


# ---------------------------------------------------------------------------
# Golden Scene Registry
# ---------------------------------------------------------------------------

GOLDEN_SCENES: Dict[str, GoldenSceneFixture] = {
    #
    # 第八集 枪管 — continuous attention contraction
    #
    "gun_barrel_ep8": {
        "scene_id": "gun_barrel_ep8",
        "episode": "EP8",
        "description": (
            "第八集枪管：背影→右侧→管口→管内的单一连续摄影路径，"
            "注意力从人物到枪口到管内金属内壁持续收缩，无切镜。"
            "故事板设计了管内落幅，视频提示词主动纠正故事板歧义"
            "（防止管内结构被错误渲染为魔幻漩涡）。"
        ),
        "storyboard_image": {
            "path": "C:\\Users\\JT\\Downloads\\第八集-图片.png",
            "sha256": "d995353f808a26cdaa360ea174baeaed0f84c6390c26314f6915e7f255c3ac1b",
            "width": 2560,
            "height": 1440,
            "format": "PNG",
        },
        "video": {
            "path": "C:\\Users\\JT\\Downloads\\第八集-视频.mp4",
            "sha256": "3b405440ea1723c32081568fe6f99e8275550be081f007af90b0689e5ea336c9",
            "width": 734,
            "height": 1280,
            "format": "HEVC, 24fps, 13.042s",
        },
        "user_evaluation": {
            "user_statement": (
                "单一注意力路径成功执行：连续摄影从背影到管内金属落幅，"
                "视频未将管内结构渲染为魔幻隧道。"
            ),
            "audit_classification": (
                "INFERENCE: 设计只有一条注意力收缩链，且同一链被时间、编号、"
                "箭头、焦段、构图和文字多次编码。模型自由度集中在运动平滑度"
                "而非事件路径。构成A级成功案例。"
            ),
            "composition_result": "success",
            "timing_result": "success",
            "behavior_result": "success",
        },
        "golden_expectations": [
            "单一Segment，单一连续Shot，无切镜。",
            "背影到右侧到管口到管内的注意力持续收缩路径。",
            "最终金属内壁填满画面作为落幅。",
            "不出现魔幻漩涡或非物理管内结构。",
            "注意力路径只被时间、编号、箭头、焦段、构图和文字多次编码——"
            "模型自由度集中在运动平滑度而非事件路径。",
        ],
        "evidence_roles": [
            "continuous_attention_contraction",        # 连续注意力收缩范例
            "single_shot_no_cut",                       # 无切镜单镜头
            "storyboard_video_correction",              # 故事板歧义→视频文字纠正
            "attention_path_redundant_encoding",        # 注意力路径多重编码
            "exterior_to_interior_transition",          # 外到内过渡
        ],
        "knowledge_questions": [
            "环境到物体内部的注意力收缩如何设计？",
            "连续运镜的起幅、路径和落幅如何保持单一焦点？",
            "故事板视觉歧义（如管内结构）如何用视频文字主动纠正？",
            "同一个注意力链如何通过时间、编号、箭头、焦段、构图和文字"
            "多次编码从而提高模型执行概率？",
        ],
    },

    #
    # 第六集 观众席 — three internal cuts in one generation segment
    #
    "audience_ep6": {
        "scene_id": "audience_ep6",
        "episode": "EP6",
        "description": (
            "第六集观众席：一个Generation Segment内三个Cinematic Shot，"
            "WS→双人MCU→手机ECU，两次真实硬切由视频模型执行。"
            "伊莎贝拉左、乔右；手机UI必须只显示设计中明确存在的"
            "对话气泡和空白负空间，不自动补充回复或通知。"
        ),
        "storyboard_image": {
            "path": "C:\\Users\\JT\\Downloads\\第6集：比赛日-图片 (4).png",
            "sha256": "59595027cd4a75c09727431f33a40ac615a9c7c44b45c58696367fbd7b0bbe1d",
            "width": 2560,
            "height": 1440,
            "format": "PNG",
        },
        "video": {
            "path": "C:\\Users\\JT\\Downloads\\第6集：比赛日-视频 (6).mp4",
            "sha256": "8fee5725cb1d4289133f2a11c5d1e59881a01bc60302daf29e4e9dcc9e420459",
            "width": 734,
            "height": 1280,
            "format": "HEVC, 24fps, 12.042s",
        },
        "user_evaluation": {
            "user_statement": (
                "切镜结构被视频模型成功执行——一个视频内出现两次真实硬切。"
                "景别递进清晰：WS环境→双人中景→手机特写。"
            ),
            "audit_classification": (
                "INFERENCE: 三镜结构同时存在于编号、时间范围、故事板构图、"
                "切镜分隔、景别跳跃和信息尺度递进中。手机UI存在生成补全泄漏——"
                "模型自动补充了额外灰色回复气泡，'无回复、无已读、无正在输入'"
                "未被完全执行。结构成功但UI控制失败。"
            ),
            "composition_result": "success",
            "timing_result": "success",
            "behavior_result": "deviation",
        },
        "golden_expectations": [
            "一个Segment内三个Cinematic Shot（WS→双人MCU→手机ECU）。",
            "内部两次切镜。",
            "伊莎贝拉左、乔右。",
            "手机无回复、无已读、无正在输入——"
            "画面只包含设计中明确存在的对话气泡和空白负空间。",
            "不自动补充回复、通知或状态符号。",
        ],
        "evidence_roles": [
            "internal_cuts_in_generation_segment",      # 生成段内切镜
            "scale_progression_ws_to_ecu",              # 景别递进WS→ECU
            "character_screen_direction",               # 角色屏幕方向
            "ai_ui_risk_mitigation",                    # AI UI/文字风险缓解
            "negative_space_as_information",            # 负空间表达信息缺失
        ],
        "knowledge_questions": [
            "空间、关系、证据的信息尺度递进如何设计？",
            "内部切镜能否作为同一生成段的拓扑结构（而非独立生成文件）？",
            "AI生成的文字和UI如何通过正向物理闭合而非否定句来控制？",
            "信息缺失（无人回复）如何通过可见负空间表达？",
            "屏幕参考、后期合成和生成模型之间的职责如何选择？",
        ],
    },

    #
    # 第六集 备赛区擦肩 — single fixed-position continuous shot;
    # composition success, timing + behavior deviation diagnostic
    #
    "prep_area_ep6": {
        "scene_id": "prep_area_ep6",
        "episode": "EP6",
        "description": (
            "第六集备赛区擦肩：设计为单一连续固定机位镜头（§9.1："
            "一个固定机位，一个连续镜头）。构图成功——Rico右侧前景、"
            "伊乌里从左侧入画、中央通道到远端靶场、明暗空间对角关系成立。"
            "实际失败为时序偏移（伊乌里约2.5s入画而非设计的~5s）和行为偏移"
            "（伊乌里约4s回头看Rico）。视频持续9.04s而非~10s。"
            "是诊断时序/行为偏移与Golden Expectation差距的关键样本。"
        ),
        "storyboard_image": {
            "path": "C:\\Users\\JT\\Downloads\\第6集：比赛日-图片 (5).png",
            "sha256": "96487289a5f5c6b226737b70b6d90026fac62544c0ddc99c4391c005b2678bd6",
            "width": 2560,
            "height": 1440,
            "format": "PNG",
        },
        "video": {
            "path": "C:\\Users\\JT\\Downloads\\第6集：比赛日-视频 (7).mp4",
            "sha256": "4108f6dcf0c51d88c42f134054705e8296cd5926c61d80dce7c32e022ec9401a",
            "width": 734,
            "height": 1280,
            "format": "HEVC, 24fps, 9.042s",
        },
        "user_evaluation": {
            "user_statement": (
                "构图成功——人物空间关系和擦肩动作清晰。"
                "固定机位、明暗空间对角关系成立。"
            ),
            "audit_classification": (
                "INFERENCE: 设计始终为单一连续固定机位镜头——证据报告§9.1明确："
                "一个固定机位，一个连续镜头；§9.5确认FFmpeg未检出真实硬切。"
                "实际失败为：(a)时序偏移——伊乌里约2.5s入画而非~5s，"
                "0-4s等待段被模型压缩；(b)行为偏移——伊乌里约4s回头看Rico"
                "（违反'不看Rico'）；(c)微表演不可见——当前机位看不到嘴角微表情，"
                "模型用更明显的回头替代表达；(d)时长9.04s而非~10s。"
                "历史视频应标注为：构图/空间方向成功，行为/时序/微表演可见性失败。"
            ),
            "composition_result": "success",
            "timing_result": "deviation",
            "behavior_result": "deviation",
        },
        "golden_expectations": [
            "单一连续固定机位镜头——设计无内部切镜（§9.1, §13.5确认）。",
            "Rico在画面右侧前景擦枪，不抬头。",
            "伊乌里在规定时间（~5s）前不得入画——中央通道在前段保持空。",
            "伊乌里经过时不看Rico——'通过面部确认表达潜台词'与当前机位"
            "的可见性冲突必须在设计中区分。",
            "擦肩距离成立——两人近距离经过但不超过1m。",
            "Rico手部停顿可读——约0.8-1.5s可见静止。",
            "伊乌里走向远端亮区，Rico留在暗处。",
        ],
        "evidence_roles": [
            "composition_success_timing_deviation",     # 构图成功+时序偏离诊断
            "shoulder_brush_spatial_clarity",            # 擦肩空间清晰度
            "early_entrance_diagnostic",                 # 首次入画时间偏移诊断
            "behavior_deviation_diagnostic",             # 行为偏移（回头看）诊断
            "micro_performance_visibility_diagnostic",   # 微表演可见性诊断
        ],
        "knowledge_questions": [
            "如何在保证构图清晰度的前提下强制模型遵守'空区保持'——"
            "中央通道在前段必须是空的，等待本身具有叙事功能？",
            "背影机位与面部微表演矛盾如何解决——"
            "是调整机位还是将微表演移到可验证的身体部位？",
            "'不看Rico'作为禁止项为何失败——"
            "是模型忽略了禁止项，还是正向叙事暗示了两人的可读交流？",
            "长保持（HOLD）为何被模型压缩——"
            "如何让模型理解重复状态不等于可跳过的帧？",
            "首次入画时间如何作为LOCKED约束明确写入？",
        ],
    },

    #
    # 第六集 贫民窟窄巷 — faithful topology, optimized connections
    #
    "alley_ep6": {
        "scene_id": "alley_ep6",
        "episode": "EP6",
        "description": (
            "第六集贫民窟窄巷：忠实于叙事拓扑（Pedro追球→抬头→"
            "直升机→轿车的顺序全部保留），但在不改变叙事硬约束的"
            "范围内优化了连接方式。用户明确高度评价运镜。"
            "证明模型可以在节点之间优化而不破坏事件路径。"
        ),
        "storyboard_image": {
            "path": "C:\\Users\\JT\\Downloads\\第6集：比赛日-图片 (6).png",
            "sha256": "e749c64c5536e4b279c539f2444079d10a0225497606bba69bb2d6d557412839",
            "width": 2560,
            "height": 1440,
            "format": "PNG",
        },
        "video": {
            "path": "C:\\Users\\JT\\Downloads\\第6集：比赛日-视频 (8).mp4",
            "sha256": "0df347a25f69175ba50d79d3e48a26978db73ec1c0cd59ef30ca2c56dcd372ce",
            "width": 734,
            "height": 1280,
            "format": "HEVC, 24fps, 13.042s",
        },
        "user_evaluation": {
            "user_statement": (
                "用户明确高度评价运镜——'最后一组的运镜和效果非常好，"
                "以AI制作结果衡量属于成功效果。'"
                "事件拓扑被忠实保留：追球→Pedro→天空→直升机→轿车顺序完整。"
            ),
            "audit_classification": (
                "INFERENCE: 模型改变的是节点连接方式而非事件顺序、运动方向"
                "或最终落幅。非字面执行包括：(a)直升机新增独立城市天空镜头，"
                "(b)取消9s机械硬切改为连续重构，(c)Pedro退出与轿车扩大同步发生。"
                "这些属于OPTIMIZABLE——连接优化但锁定节点不变。证明'锁定节点+"
                "弹性连接'模式可在实际视频模型中工作。"
            ),
            "composition_result": "success",
            "timing_result": "success",
            "behavior_result": "success",
        },
        "golden_expectations": [
            "Pedro追球、抬头、直升机、轿车的顺序不可改变。",
            "直升机画右到画左。",
            "轿车静止、熄灯、无人。",
            "叙事拓扑节点保持LOCKED，连接方式可OPTIMIZABLE。",
        ],
        "evidence_roles": [
            "narrative_topology_preserved",              # 叙事拓扑保留
            "connection_optimization_allowed",            # 连接方式允许优化
            "user_high_evaluation_camera_movement",       # 用户高评运镜
            "locked_vs_optimizable_boundary",             # LOCKED/OPTIMIZABLE边界
        ],
        "knowledge_questions": [
            "如何在锁定事件拓扑节点的同时允许模型优化连接方式？",
            "用户评价'运镜好'的具体标准是什么——路径自然化还是节奏？",
            "如何区分OPTIMIZABLE的连接优化和LOCKED破坏？",
            "故事板中的拓扑信息是否足够让视频模型理解不可变顺序？",
        ],
    },
}
