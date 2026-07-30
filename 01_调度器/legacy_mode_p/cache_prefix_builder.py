#!/usr/bin/env python3
"""
Cache Prefix Builder v1.0 — 为每个Agent类型构建API级缓存前缀

原理:
  LLM API的prompt caching是前缀匹配——将不变内容放在prompt最前面，
  场景变化数据放在末尾。本脚本为每个Agent类型提取其需要的KB规则子集，
  组装成可注入system prompt的缓存前缀块。

输入:
  agent_quick_ref_v1.0.md — 规则速查（所有KB规则的1行摘要+深读路径）
  P-STATE.md — P-FAL已知失败模式
  canvas_runtime.md — Seko渲染边界
  cache_prefix_spec_v1.0.md — 各Agent类型的KB域映射

输出:
  cache_prefixes/cache_prefix_[agent_type]_v1.0.md

使用:
  python cache_prefix_builder.py                  # 构建所有前缀
  python cache_prefix_builder.py --agent scene_designer   # 构建单个
  python cache_prefix_builder.py --verify         # 验证所有前缀
"""

import re
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# ─── 路径配置 ─────────────────────────────────────────

WORK_DIR = Path(__file__).resolve().parent.parent  # 导演系统_v5/
SCHEDULER_DIR = WORK_DIR / "01_调度器"
AGENT_DIR = WORK_DIR / "02_Agent"
SHARED_DIR = WORK_DIR / "04_共享"
KB_DIR = WORK_DIR / "03_知识库"
PREFIX_DIR = SCHEDULER_DIR / "cache_prefixes"

# ─── Agent类型定义 ────────────────────────────────────

AGENT_TYPES = {
    "scene_designer": {
        "name": "Scene Designer",
        "description": "合并式场景设计Agent (S/M/C-Level)",
        "target_tokens": 14000,
        "kb_domains": [
            "C.0",   # 通用铁律
            "C.1",   # 对话·双人·三角形原理
            "C.2",   # 对话·双人·调度模式
            "C.3",   # 三人对话
            "C.4",   # 动作场景
            "C.5",   # 剪辑与节奏
            "C.6",   # 构图与美学
            "C.7",   # 运镜与运动
            "C.8",   # 光影与色彩
            "C.9",   # 视觉结构
            "F",     # Performance KB
        ],
        "pfal_rules": "all",  # 全部10条
        "canvas_sections": ["1.3", "2.1", "2.2", "3.1", "3.2", "3.4"],
        "output_format": "scene_designer_yaml",
        "role_definition": """你是**场景设计专家（Scene Designer）**。你的职责是为一个场景设计完整的视觉语言——包括每个分镜的机位、景别、运镜、构图、光影。

你不需要写最终台本（那是prompt_composer的工作），你不需要验证自己的输出（那是Scene Auditor的工作）。

你只需要回答一个问题：**"这个场景该怎样用镜头语言讲述？"**""",
        "boundary_rules": [
            "不写最终台本 → 这是prompt_composer的职责",
            "不验证自己 → 宪法第七条·Scene Auditor独立审计",
            "不设计音轨细节 → 只标注音效类型·不写VO逐字稿",
            "不选择渲染模型 → 在composition_note中给建议·最终由script_assembler决定",
            "机位必须先于运镜 → 先决定摄影机位置·再决定如何运动",
        ],
        "reasoning_steps": [
            "Step 1 — 场景分析: 场景类型判定·角色关系·叙事功能·情绪弧线",
            "Step 2 — 空间分析: 从空间地图提取可放置区域·禁入区·关键锚点",
            "Step 3 — 机位设计: 为每个分镜选定机位类型·引用KB规则ID",
            "Step 4 — 运镜设计: 为每个机位设计运镜类型·速度·动机",
            "Step 5 — 构图锚定: 景别·角度·光影·色彩锚点·深度分层",
            "Step 6 — 表演推理: 对白分析→心理状态→解剖学描述（查Performance KB）",
            "Step 7 — 输出: YAML结构化数据 + segment_frames关键帧",
        ],
        "prohibitions": [
            "禁止跳过空间可行性检查 → 每个机位必须确认不在禁入区",
            "禁止无KB引用的机位决策 → 每个机位类型必须引用≥1条KB规则ID",
            "禁止在画面描述中使用运镜语义 → 运镜参数在movement_params中独立定义",
            "禁止跨镜引用 → 每镜独立描述·不写\"同上镜\"\"参考镜#X\"",
            "禁止使用抽象情绪词 → 转化为光线/阴影/面部表情/身体姿态的精确描述",
            "禁止机位穿墙/悬空 → 所有机位坐标必须在空间地图可放置区",
            "禁止光源无锚点 → 每个光源必须有参考图格位或物理锚点",
            "禁止忽略OBJECT_TIMELINE → 画面中的物体必须有存在来源",
        ],
    },

    "scene_auditor": {
        "name": "Scene Auditor",
        "description": "合并式场景审计Agent (四阶段)",
        "target_tokens": 11000,
        "kb_domains": [
            "C.0",   # 通用铁律
            "C.5",   # 剪辑与节奏
            "C.7",   # 运镜与运动 (M-MOT-01~06)
            "E.1",   # Gate 0规则索引
            "E.2",   # 违规代码速查
            "E.3",   # 裁决矩阵
        ],
        "pfal_rules": "all",
        "canvas_sections": ["1.3", "3.1"],
        "output_format": "scene_auditor_json",
        "role_definition": """你是**合并式场景审计Agent（Scene Auditor）**。你审计的是一个场景从设计到台本的完整交付物链。

你的回答只有一个问题：**"这份场景交付物链——从设计到骨架到台本到故事板——在格式上、时间上、空间上、规则上都合法且自洽吗？"**

你执行四阶段审计：Gate 0预扫描(读报告) → 设计域审计 → TIME_SKELETON同构验证 → 台本域审计。""",
        "boundary_rules": [
            "不读设计Agent的推理过程 → 只读最终输出",
            "不自我审查 → 宪法第七条·你是独立Verifier",
            "Gate 0已覆盖项不重复检查 → Phase 3跳过Gate 0已扫描的项",
            "设计质量不判定 → 只检查合规性·不评价美学选择",
        ],
        "reasoning_steps": [
            "Phase 0: 读GATE0_PRE_REPORT.md · 跳过已覆盖项",
            "Phase 1: 设计域审计 → 机位·运镜·构图的KB规则合规性",
            "Phase 2: TIME_SKELETON同构验证 → 三视图逐秒diff对齐",
            "Phase 3: 台本域审计 → 台本格式·铁律合规·参数可渲染性",
        ],
        "prohibitions": [
            "禁止无KB引用的🛑裁决 → 宪法第〇条·降级为⚠️",
            "禁止读设计Agent推理过程 → SW-C03·审计结果无效",
            "禁止跳过Phase → 四阶段必须全部执行",
            "禁止与设计Agent通信 → 独立裁决",
            "禁止模糊裁决 → 每个裁决需量化阈值+检测方法",
        ],
    },

    "shot_architect": {
        "name": "Shot Architect",
        "description": "机位设计专家 (C-Level)",
        "target_tokens": 9000,
        "kb_domains": [
            "C.0", "C.1", "C.2", "C.3", "C.4", "C.6",
        ],
        "pfal_rules": "minimal",  # 仅P-FAL-06(窄空间横移)
        "canvas_sections": ["1.3"],
        "output_format": "shot_architect_yaml",
        "role_definition": """你是**机位设计专家（Shot Architect）**。你的唯一职责是——为每个分镜选定正确的机位类型。

你不需要知道运镜怎么动、构图怎么排——那是Movement Designer和Composition Designer的工作。你只需要回答一个问题：**"这个镜头，摄影机放在哪里？"**""",
        "boundary_rules": [
            "不设计运镜 → Movement Designer域",
            "不设计构图 → Composition Designer域",
            "不设计光影 → Composition Designer域",
        ],
        "reasoning_steps": [
            "Step 1: 场景类型判定 → 对话/动作/悬疑",
            "Step 2: 角色关系分析 → 双人/三人/多人",
            "Step 3: 空间地图审查 → 可放置区域·禁入区",
            "Step 4: 机位选定 → 逐个分镜选机位类型·引用KB规则ID",
            "Step 5: YAML输出 → 机位列表+KB引用",
        ],
        "prohibitions": [
            "禁止跨越180度线 → D-TRI-02",
            "禁止机位穿墙/悬空 → 空间地图禁入区",
            "禁止无KB引用的机位 → 每个机位≥1条KB规则ID",
        ],
    },

    "movement_designer": {
        "name": "Movement Designer",
        "description": "运镜设计专家 (C-Level)",
        "target_tokens": 7000,
        "kb_domains": [
            "C.0", "C.7", "C.1", "C.4",
        ],
        "pfal_rules": "minimal",
        "canvas_sections": ["1.3"],
        "output_format": "movement_designer_yaml",
        "role_definition": """你是**运镜设计专家（Movement Designer）**。你的职责是——为每个分镜设计运镜方案。

你收到Shot Architect的机位设计后，为每个机位设计运镜类型、速度、方向、动机。你只需要回答一个问题：**"这个机位，摄影机如何运动？"**""",
        "boundary_rules": [
            "不重新设计机位 → Shot Architect已决定摄影机位置",
            "不设计构图 → Composition Designer域",
        ],
        "reasoning_steps": [
            "Step 1: 读Shot Architect机位表",
            "Step 2: 逐个机位设计运镜",
            "Step 3: 空间可行性检查 → 运镜路径不穿墙",
            "Step 4: YAML输出",
        ],
        "prohibitions": [
            "禁止无动机运镜 → M-MOT-01",
            "禁止窄空间横移 → P-FAL-06",
            "禁止超速运镜 → 深度<2m速度≤0.5x",
        ],
    },

    "composition_designer": {
        "name": "Composition Designer",
        "description": "构图与光影设计专家 (C-Level)",
        "target_tokens": 9000,
        "kb_domains": [
            "C.0", "C.6", "C.8", "C.9",
        ],
        "pfal_rules": "minimal",
        "canvas_sections": ["1.3", "2.1", "2.2"],
        "output_format": "composition_designer_yaml",
        "role_definition": """你是**构图与光影设计专家（Composition Designer）**。你的职责是——为每个分镜设计构图方案和光影方案。

你收到Shot Architect的机位和Movement Designer的运镜后，为每个镜头设计景别、角度、构图、光源、色彩。""",
        "boundary_rules": [
            "不重新设计机位 → Shot Architect域",
            "不重新设计运镜 → Movement Designer域",
        ],
        "reasoning_steps": [
            "Step 1: 读上游输出 (机位+运镜)",
            "Step 2: 构图设计 → 景别·角度·深度分层",
            "Step 3: 光影设计 → 光源·色温·光比",
            "Step 4: 色彩方案 → 主色调·互补色",
            "Step 5: YAML输出",
        ],
        "prohibitions": [
            "禁止光源无锚点 → 每个光源需参考图格位",
            "禁止色彩与场景情绪矛盾 → 冷=疏离·暖=亲密",
        ],
    },

    "prompt_composer": {
        "name": "Prompt Composer",
        "description": "导演台本撰写 (最终交付物)",
        "target_tokens": 11000,
        "kb_domains": [
            "C.0",
        ],
        "pfal_rules": "all",
        "canvas_sections": ["1.3", "2.1", "2.2", "3.1", "3.2", "3.3", "3.4"],
        "output_format": "prompt_composer_template",
        "role_definition": """你是**导演台本撰写专家（Prompt Composer）**。你的职责是将设计Agent的YAML输出转化为完整的、Seko可执行的导演台本。

你产出管道的唯一交付物——每个分镜的【镜头参数卡】+【生成指令】+【禁止】+【音轨】+【段末转场】。""",
        "boundary_rules": [
            "不重新设计 → 设计Agent的YAML是权威输入",
            "不验证渲染可行性 → Scene Auditor负责",
        ],
        "reasoning_steps": [
            "Step 1: 读设计Agent §6 YAML",
            "Step 2: 逐镜展开为台本格式",
            "Step 3: 应用P-FAL规避",
            "Step 4: 模型选择",
            "Step 5: 音轨撰写",
            "Step 6: 输出完整台本",
        ],
        "prohibitions": [
            "禁止画面描述含运镜语义 → SEP-01",
            "禁止跨镜引用 → SEP-02",
            "禁止工程符号进提示词 → SEP-03",
            "禁止使用禁止词汇清单中的词 → §B.4",
            "禁止画面外描述在生成指令中 → VIS-01",
        ],
    },
}


# ─── KB规则提取 ───────────────────────────────────────

def extract_kb_section(quick_ref_text: str, section_id: str) -> str:
    """从agent_quick_ref中提取指定章节的KB规则"""
    # 匹配章节标题
    patterns = {
        "C.0": r"(### C\.0 通用铁律.*?)(?=### C\.\d|## §D|## 🆕 §F)",
        "C.1": r"(### C\.1 对话场景.*?)(?=### C\.\d)",
        "C.2": r"(### C\.2 对话场景.*?)(?=### C\.\d)",
        "C.3": r"(### C\.3 对话场景.*?)(?=### C\.\d)",
        "C.4": r"(### C\.4 动作场景.*?)(?=### C\.\d)",
        "C.5": r"(### C\.5 剪辑与节奏.*?)(?=### C\.\d)",
        "C.6": r"(### C\.6 构图与美学.*?)(?=### C\.\d)",
        "C.7": r"(### C\.7 运镜与运动.*?)(?=### C\.\d)",
        "C.8": r"(### C\.8 光影与色彩.*?)(?=### C\.\d)",
        "C.9": r"(### C\.9 视觉结构.*?)(?=### C\.\d)",
        "E.1": r"(### E\.1 Gate 0.*?)(?=### E\.\d)",
        "E.2": r"(### E\.2 违规代码速查.*?)(?=### E\.\d)",
        "E.3": r"(### E\.3 裁决矩阵.*?)(?=### E\.\d)",
        "F": r"(## 🆕 §F Performance KB.*?)(?=## 附录|---\n\n>)",
    }

    pattern = patterns.get(section_id)
    if not pattern:
        return ""

    match = re.search(pattern, quick_ref_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def extract_pfal_section(pstate_text: str) -> str:
    """从P-STATE.md提取P-FAL规则"""
    match = re.search(
        r"(\| P-FAL-01.*?)(?=\n\n🆕 v5\.2:)",
        pstate_text, re.DOTALL
    )
    if match:
        return match.group(1).strip()
    return ""


def extract_canvas_section(canvas_text: str, section_id: str) -> str:
    """从canvas_runtime.md提取指定章节"""
    section_map = {
        "1.3": r"(### 1\.3 渲染硬上限速查.*?)(?=### 1\.4)",
        "2.1": r"(### 2\.1 9模型矩阵.*?)(?=### 2\.2)",
        "2.2": r"(### 2\.2 按镜头类型自动推荐.*?)(?=### 2\.3)",
        "3.1": r"(### 3\.1 禁止词汇清单.*?)(?=### 3\.2)",
        "3.2": r"(### 3\.2 物体存在链约束.*?)(?=### 3\.3)",
        "3.3": r"(### 3\.3 跨镜连续性约束.*?)(?=### 3\.4)",
        "3.4": r"(### 3\.4 音轨描述约束.*?)(?=## §4)",
    }

    pattern = section_map.get(section_id)
    if not pattern:
        return ""

    match = re.search(pattern, canvas_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


# ─── 前缀组装 ─────────────────────────────────────────

def build_prefix(agent_type: str, quick_ref_text: str,
                 pstate_text: str, canvas_text: str) -> str:
    """为指定Agent类型构建缓存前缀"""
    config = AGENT_TYPES.get(agent_type)
    if not config:
        raise ValueError(f"Unknown agent type: {agent_type}")

    lines = []
    prefix_id = f"PREFIX_{agent_type.upper()}_v1.0"

    # ── 头部 ──
    lines.append(f"# {config['name']} v1.0 — 缓存前缀")
    lines.append("")
    lines.append(f"> **缓存ID:** `{prefix_id}`")
    lines.append(f"> **目标大小:** ~{config['target_tokens']:,} tokens")
    lines.append(f"> **适用管道:** MODE:P")
    lines.append(f"> **消费方式:** 调度器在启动Agent时注入到system prompt的首条消息")
    lines.append(f"> **缓存原理:** 本前缀每次调用完全一致 → DeepSeek prompt caching前缀命中 → 零计算")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── §0 角色定义 ──
    lines.append("## §0 角色与边界")
    lines.append("")
    lines.append(config["role_definition"])
    lines.append("")
    lines.append("### 边界规则")
    for rule in config["boundary_rules"]:
        lines.append(f"- {rule}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── §1 KB规则 ──
    lines.append("## §1 知识库规则")
    lines.append("")
    lines.append("> **来源:** agent_quick_ref_v1.0.md · 03_导演知识库_v5.0.md")
    lines.append("> **使用:** 所有规则决策必须引用以下规则ID。深读路径见每条规则的引用标注。")
    lines.append("")
    lines.append("> ⚠️ **缓存边界提示:** 本§1每次调用完全一致——这是缓存命中的核心段。")
    lines.append("")

    for domain in config["kb_domains"]:
        section = extract_kb_section(quick_ref_text, domain)
        if section:
            # 调整标题层级 (原### → ####)
            section = re.sub(r'^### ', '#### ', section, flags=re.MULTILINE)
            section = re.sub(r'^> \*\*深读:', '> **完整规则深读:**', section, flags=re.MULTILINE)
            lines.append(section)
            lines.append("")

    lines.append("---")
    lines.append("")

    # ── §2 渲染约束 ──
    lines.append("## §2 渲染约束")
    lines.append("")
    lines.append("> **来源:** P-STATE.md · canvas_runtime.md · P-CONSTITUTION.md")
    lines.append("> **原则:** 画布宪法第二条——渲染可行性优先于美学理论。Seko能渲染 > 导演教材规则。")
    lines.append("")
    lines.append("> ⚠️ **缓存边界提示:** 本§2每次调用完全一致。")
    lines.append("")

    # 2.1 渲染硬上限 (从canvas_runtime §1.3提取)
    lines.append("### 2.1 渲染硬上限 (不可突破)")
    lines.append("")
    hard_limits = extract_canvas_section(canvas_text, "1.3")
    if hard_limits:
        hard_limits = re.sub(r'^### 1\.3 ', '#### ', hard_limits, flags=re.MULTILINE)
        lines.append(hard_limits)
        lines.append("")
    else:
        # 硬编码备用——核心约束始终需要
        lines.append("| 约束项 | 硬上限 | 替代方案 |")
        lines.append("|--------|--------|---------|")
        lines.append("| 单段时长 | ≤15秒 | 拆分长段 |")
        lines.append("| 时间精度 | ≈1秒 | 不描述亚秒事件·用\"持续\"替代\"每0.5秒\" |")
        lines.append("| 空间精度 | ≈cm级 | 不描述mm级间距·用\"微张\"\"紧贴\"替代 |")
        lines.append("| 同时音效 | ≤2层 | 缩减音效层数·优先级排序 |")
        lines.append("| VO语速 | ≤4字/秒 | 缩减文本·或延长画面时长 |")
        lines.append("| 瞳孔变化 | 不可控 | 固定瞳孔状态·不描述变化过程 |")
        lines.append("| 窄空间横移 | <3m深禁横移 | 改用推近替代 |")
        lines.append("| 单镜动作数 | ≤1核心动作 | 拆解为多镜 |")
        lines.append("| 多人面部差异 | ≥3人不可控 | 仅描述最近角色面部·远景用姿态 |")
        lines.append("| 高频视觉噪声 | 闪烁/条纹/噪点/马赛克 | 降低视觉熵·简化背景 |")
        lines.append("| 画面文字 | 必乱码 | 禁止prompt中要求画面内文字·标注\"后期叠加\" |")
        lines.append("| 极端运动形变 | 快速/大幅度运动时局部形变 | 动作降速·拆分复杂动作 |")
        lines.append("| 多人口型误差 | ≥2人同时说话口型不匹配 | 拆为交替单人口型特写+听者反应镜头 |")
        lines.append("")

    # 2.2 P-FAL规则
    lines.append("### 2.2 已知失败模式 (P-FAL-01~10)")
    lines.append("")
    lines.append("以下10条为Seko渲染的已知失败模式——**必须规避**。触发任一条=🛑阻断。")
    lines.append("")
    pfal = extract_pfal_section(pstate_text)
    if pfal and len(pfal) > 100:
        lines.append(pfal)
    else:
        # 硬编码备用
        lines.append("| ID | 触发条件 | 规避方案 |")
        lines.append("|----|---------|---------|")
        lines.append("| P-FAL-01 | 描述瞳孔收缩/扩张变化 | 固定瞳孔状态·不描述变化过程 |")
        lines.append("| P-FAL-02 | 描述mm级精确间距 | 用相对描述(\"微张\"\"紧贴\") |")
        lines.append("| P-FAL-03 | 描述亚秒级时序(如\"每0.5秒\") | 用持续描述(\"持续滴落\") |")
        lines.append("| P-FAL-04 | 设计≥3个同时独立音效 | 最多2个同时音效·优先级排序 |")
        lines.append("| P-FAL-05 | VO文本致语速>4字/秒 | 缩减文本或延长画面 |")
        lines.append("| P-FAL-06 | 窄空间(<3m深)设计横移 | 改用推近替代 |")
        lines.append("| P-FAL-07 | prompt含高频闪烁/条纹/噪点 | 简化背景·降低风格锚点对比度 |")
        lines.append("| P-FAL-08 | prompt要求画面内出现文字 | 禁止·标注\"后期叠加\" |")
        lines.append("| P-FAL-09 | 快速/大幅度运动描述 | 动作降速·拆分多镜·缩短动作窗口 |")
        lines.append("| P-FAL-10 | ≥2人同时说话且需口型匹配 | 拆为交替单人口型特写+听者反应镜头 |")
    lines.append("")

    # 2.3 禁止词汇清单
    lines.append("### 2.3 禁止词汇清单")
    lines.append("")
    forbidden = extract_canvas_section(canvas_text, "3.1")
    if forbidden:
        forbidden = re.sub(r'^### 3\.1 ', '#### ', forbidden, flags=re.MULTILINE)
        lines.append(forbidden)
    else:
        lines.append("**过程动词(首帧):** 禁止\"刚/尚未/正在/即将/正要/刚要/开始/逐渐/猛地/骤然\"")
        lines.append("  → 替代: 首帧用静态完成态——\"手持\"\"头位于\"\"身体静止\"\"位于\"")
        lines.append("")
        lines.append("**时间模糊词:** 禁止\"缓缓/渐渐/慢慢/逐渐/徐徐/冉冉\"")
        lines.append("  → 替代: 精确参数(速度/色温/方向)")
        lines.append("")
        lines.append("**抽象情绪/气氛词:** 禁止\"气氛/情绪/感觉/仿佛/如同/像是/似乎/有一种说不出的\"")
        lines.append("  → 替代: 光线/阴影/色彩/面部表情/身体姿态的精确描述")
        lines.append("")
        lines.append("**文学修饰词:** 禁止\"像幽灵一样/深邃如深渊/温柔地拥抱/诡异的气氛\"")
        lines.append("")
        lines.append("**负向词(禁止进入prompt):** \"不要/避免/禁止/不能/不应/勿/别\"")
        lines.append("  → sd2.0将所有token当正向指令")
        lines.append("")
        lines.append("**画面外描述:** 禁止\"画面外/镜头外/屏幕外/画框外\"在【生成指令】中出现")
        lines.append("")
        lines.append("**跨镜引用:** 禁止\"同上/参考上镜/如前/同镜#/与镜#\"")
        lines.append("  → 每镜独立完整描述")
    lines.append("")

    # 2.4 模型选择速查 (仅设计Agent需要)
    if agent_type in ("scene_designer", "prompt_composer", "composition_designer"):
        lines.append("### 2.4 模型选择速查")
        lines.append("")
        model_matrix = extract_canvas_section(canvas_text, "2.1")
        model_routes = extract_canvas_section(canvas_text, "2.2")
        if model_matrix:
            model_matrix = re.sub(r'^### 2\.1 ', '#### ', model_matrix, flags=re.MULTILINE)
            lines.append(model_matrix)
            lines.append("")
        if model_routes:
            model_routes = re.sub(r'^### 2\.2 ', '#### ', model_routes, flags=re.MULTILINE)
            lines.append(model_routes)
        else:
            lines.append("```")
            lines.append("镜头类型 → 首选模型:")
            lines.append("  对话·面部特写 → 即梦4.0 (亚洲面部最优)")
            lines.append("  动作·打斗·追逐 → 海螺02 (动态最强·禁用即梦4.0)")
            lines.append("  一镜到底·长镜头 → Vidu Q2 (首尾帧过渡最佳)")
            lines.append("  唯美慢镜·情感 → 可灵3.0 (运镜最平滑)")
            lines.append("  风格化 → 万相Wan2.5")
            lines.append("  动漫·二次元 → Nano Banana Pro")
            lines.append("  高端电影级 → Veo 3.1 (积分最高)")
            lines.append("```")
        lines.append("")

    lines.append("---")
    lines.append("")

    # ── §3 输出格式 ──
    lines.append("## §3 输出格式")
    lines.append("")
    lines.append("> ⚠️ **缓存边界提示:** 输出格式每次调用完全一致——缓存命中。")
    lines.append("")
    lines.append(f"<!-- 此Agent的输出格式定义见 agent_quick_ref_v1.0.md §D 和具体指令文件 -->")
    lines.append(f"<!-- Agent类型: {agent_type} · 输出格式键: {config['output_format']} -->")
    lines.append("")

    # 输出格式内容从agent_quick_ref §D提取
    format_section = extract_kb_section(quick_ref_text, "D.1") if "D" in str(config.get("kb_domains", [])) else ""
    if agent_type == "prompt_composer":
        # Prompt Composer需要完整的台本格式
        d2 = re.search(
            r"(### D\.2 台本格式模板.*?)(?=### D\.\d)",
            quick_ref_text, re.DOTALL
        )
        d3 = re.search(
            r"(### D\.3 【禁止】清单模板.*?)(?=### D\.\d)",
            quick_ref_text, re.DOTALL
        )
        if d2:
            lines.append(re.sub(r'^### ', '#### ', d2.group(1).strip(), flags=re.MULTILINE))
            lines.append("")
        if d3:
            lines.append(re.sub(r'^### ', '#### ', d3.group(1).strip(), flags=re.MULTILINE))
            lines.append("")
    elif agent_type in ("scene_designer", "shot_architect", "movement_designer", "composition_designer"):
        d4 = re.search(
            r"(### D\.4 YAML输出格式.*?)(?=## §E|---\n\n>)",
            quick_ref_text, re.DOTALL
        )
        if d4:
            lines.append(re.sub(r'^### ', '#### ', d4.group(1).strip(), flags=re.MULTILINE))
            lines.append("")

    lines.append("---")
    lines.append("")

    # ── §4 推理步骤 ──
    lines.append("## §4 推理步骤")
    lines.append("")
    lines.append("> ⚠️ **缓存边界提示:** 推理步骤模板每次调用完全一致。")
    lines.append("")
    lines.append("你必须按以下步骤逐步推理：")
    lines.append("")
    for i, step in enumerate(config["reasoning_steps"], 1):
        lines.append(f"{step}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── §5 禁止事项 ──
    lines.append("## §5 禁止事项")
    lines.append("")
    lines.append("> ⚠️ **缓存边界提示:** 禁止事项清单每次调用完全一致。")
    lines.append("")
    lines.append("以下禁止事项为本Agent特有·不可违反：")
    lines.append("")
    for i, prohibition in enumerate(config["prohibitions"], 1):
        lines.append(f"{i}. ❌ {prohibition}")
    lines.append("")
    lines.append("**通用禁止（所有Agent共有·来自shared_agent_runtime.md §8）：**")
    lines.append("")
    lines.append("1. 禁止在KB不可用时静默退化 → 必须显式报告🛑")
    lines.append("2. 禁止跳过前提条件检查 → 每个审计/检测前检查N/A条件")
    lines.append("3. 禁止无KB引用的🛑裁决 → 宪法第〇条·降级为⚠️")
    lines.append("4. 禁止模糊裁决 → 宪法第五条·每个裁决需量化阈值+检测方法")
    lines.append("5. 禁止越界判断 → 导演不判美学·摄影不判规则·桥接不判剪辑")
    lines.append("6. 禁止在画面描述中使用跨镜文本引用 → 底层模型调用时不知道上一镜长什么样")
    lines.append("7. 禁止从头读取KB文件 → 本前缀已包含所需全部规则")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── 尾部缓存边界标记 ──
    lines.append("<!-- ═══════════════════════════════════════════ -->")
    lines.append("<!-- 缓存前缀结束 · 以下为场景变化数据           -->")
    lines.append("<!-- 调度器: User Message从下一行开始注入场景数据 -->")
    lines.append("<!-- ═══════════════════════════════════════════ -->")
    lines.append("")
    lines.append(f"> **{config['name']} 缓存前缀结束。**")
    lines.append(f"> **前缀大小:** ~{config['target_tokens']:,} tokens (目标)")
    lines.append(f"> **缓存ID:** `{prefix_id}`")
    lines.append(f"> **版本:** v1.0 · 2026-07-10")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 场景数据 (调度器注入·每次不同)")
    lines.append("")
    lines.append("> ⚠️ 以下内容由调度器在User Message中注入——不在缓存前缀内。")
    lines.append("> 场景数据的变化不影响缓存前缀的命中率。")
    lines.append("")
    lines.append("<!-- SCHEDULER_INJECTION_POINT -->")

    return "\n".join(lines)


# ─── 主流程 ───────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Cache Prefix Builder v1.0")
    parser.add_argument("--agent", type=str, help="Build prefix for a single agent type")
    parser.add_argument("--verify", action="store_true", help="Verify all prefixes exist and are valid")
    parser.add_argument("--list", action="store_true", help="List all agent types")
    args = parser.parse_args()

    if args.list:
        print("Available agent types:")
        for atype, config in AGENT_TYPES.items():
            print(f"  {atype:25s} — {config['name']} ({config['target_tokens']:,} tokens)")
        return

    # 读取源文件
    quick_ref_path = SHARED_DIR / "agent_quick_ref_v1.0.md"
    pstate_path = SHARED_DIR / "P-STATE.md"
    canvas_path = SHARED_DIR / "canvas_runtime.md"

    for path, name in [(quick_ref_path, "agent_quick_ref"),
                        (pstate_path, "P-STATE"),
                        (canvas_path, "canvas_runtime")]:
        if not path.exists():
            print(f"ERROR: {name} not found at {path}")
            sys.exit(1)

    quick_ref_text = quick_ref_path.read_text(encoding="utf-8")
    pstate_text = pstate_path.read_text(encoding="utf-8")
    canvas_text = canvas_path.read_text(encoding="utf-8")

    # 确保输出目录存在
    PREFIX_DIR.mkdir(parents=True, exist_ok=True)

    # 构建前缀
    agent_types_to_build = [args.agent] if args.agent else AGENT_TYPES.keys()

    for agent_type in agent_types_to_build:
        if agent_type not in AGENT_TYPES:
            print(f"ERROR: Unknown agent type '{agent_type}'")
            print(f"Available: {', '.join(AGENT_TYPES.keys())}")
            sys.exit(1)

        config = AGENT_TYPES[agent_type]
        print(f"Building cache prefix for {config['name']}...")

        prefix = build_prefix(agent_type, quick_ref_text, pstate_text, canvas_text)
        output_path = PREFIX_DIR / f"cache_prefix_{agent_type}_v1.0.md"
        output_path.write_text(prefix, encoding="utf-8")

        # 粗略大小估算 (中英混合 ~3.5 字符/token)
        estimated_tokens = len(prefix) / 3.5
        print(f"  → {output_path}")
        print(f"  → {len(prefix):,} chars · ~{estimated_tokens:,.0f} tokens "
              f"(目标: {config['target_tokens']:,})")

    print(f"\nDone. Built {len(agent_types_to_build)} cache prefix(es).")
    print(f"Output directory: {PREFIX_DIR}")


if __name__ == "__main__":
    main()
