#!/usr/bin/env python3
"""
performance_matcher.py v1.0 — 心理状态→解剖学描述 确定性匹配器
Scene Designer 前置算法 · 0 LLM · 将 KB 从参考文档变为执行算法

算法: 三 tier 自适应匹配 → N 个候选(非固定) → 每个附带完整 KB 解剖学描述
LLM 工作: 从 N 个候选确认 → 个性化调整 → 不再搜索 15 个全量

用法: python performance_matcher.py --script 剧本.txt --kb PERFORMANCE_KB.md --out candidates.yml
"""
import yaml, re, argparse, sys, io
from typing import Dict, List, Tuple
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ===== PERFORMANCE_KB 状态定义 (精简嵌入·避免文件依赖) =====

STATES = {
    "lying": {
        "name_cn": "说谎",
        "keywords": ["没有", "不是", "没看到", "不知道", "不是我", "骗", "假", "谎",
                     "在忙", "Busy", "没时间", "忘了"],
        "anatomical": {
            "eyes": "眨眼频率先抑制(0-2秒)后激增(3-5秒)·注视对方时间增加监控反应",
            "brow": "短暂眉间纵纹(<500ms微表情)·随后被抑制·眉位恢复基线",
            "mouth": "代偿性过度控制·微笑启动延迟约200ms·嘴角不对称(左低右高约1mm)",
            "hands": "自我安抚动作增加·触碰面部/颈部/衣物",
            "voice": "基频微升10-15Hz·回答前潜伏期延长·陈述句尾音微扬(不确定化)",
        }
    },
    "avoidance": {
        "name_cn": "回避",
        "keywords": ["没什么", "不用", "没事", "不知道更好", "以后再说", "不关你的事",
                     "早点关门", "别问了", "咖啡？老样子", "这么早开门"],
        "anatomical": {
            "eyes": "注视时长显著减少·视线向下方或侧方漂移·眨眼频率增加·回避直接眼接触",
            "mouth": "嘴唇内收(上下唇卷入)·或代偿性过度微笑·笑容持续时间延长但无眼部参与",
            "posture": "躯干后倾·肩部微收·与对方物理距离增加·身体朝向微偏",
            "hands": "手部动作增加·整理衣物或物品·占用双手回避手势交流",
        }
    },
    "power_play": {
        "name_cn": "权力博弈",
        "keywords": ["听我说", "你看到了什么", "不是问句", "有些事", "你不需要知道",
                     "你——是不是", "你手上有血", "拿钥匙开了"],
        "anatomical": {
            "eyes": "注视时长增加·不首先中断对视·瞳孔轻微散大·注视对方眼睛而非面部其他区域",
            "posture": "躯干前倾·占据更多空间·头位微仰·肩部展开·姿态不对称",
            "hands": "手部动作减少·静止传达控制·展示手掌(不具威胁)·手指尖塔形",
            "voice": "音量稳定·语速控制·停顿使用增加(控制节奏)·句尾下沉(陈述而非询问)",
        }
    },
    "fear_suppressed": {
        "name_cn": "恐惧(抑制)",
        "keywords": ["血", "杀", "死", "枪", "毛巾", "钥匙", "工作室",
                     "凌晨两点", "你是不是有麻烦了"],
        "anatomical": {
            "eyes": "上眼睑微抬·下眼睑收紧·巩膜暴露增加·视线快速扫描环境",
            "brow": "眉头微抬且向内收拢(恐惧微表情)·持续不到500ms·随后强行恢复基线",
            "mouth": "嘴唇微启·嘴角水平拉宽(恐惧口型)·随后被抑制·代偿性吞咽动作",
            "posture": "躯干微后倾·肩部上提(颈部保护反射)·身体准备后退但被意志抑制",
            "voice": "音量微降·语速微增或微降(不稳定)·气息变浅·停顿增多",
        }
    },
    "anger_suppressed": {
        "name_cn": "愤怒(抑制)",
        "keywords": ["忘了", "洗过", "太干净", "没结痂", "不回头", "没做"],
        "anatomical": {
            "eyes": "眼睑收紧·下眼睑微升·视线锁定对方·注视强度增加·眨眼频率减少",
            "brow": "眉头下降且向内收拢·眉间纵纹加深·上眼睑被眉部下压(愤怒三角区)",
            "mouth": "嘴唇紧抿·唇红变薄·嘴角下降·下颌肌肉隆起(咬肌收缩)",
            "hands": "手指屈曲·握拳或半握·指关节发白·或双手用力按压静止物体",
            "voice": "音量控制(刻意稳定)·语速微降·咬字加重·停顿处有未释放的呼气",
        }
    },
    "sadness_masked": {
        "name_cn": "悲伤(掩饰)",
        "keywords": ["睡不着", "在忙", "照片", "海边", "合影", "叮"],
        "anatomical": {
            "eyes": "上眼睑微垂·下眼睑微紧·视线向下·泪膜增厚(反光增强)·不形成泪滴",
            "brow": "眉头内侧微抬(悲伤微表情)·持续时间约1秒·随后被社交微笑覆盖",
            "mouth": "嘴角下降约1-2mm·与代偿性微笑交替·微笑时眼部无皱褶(假笑特征)",
            "hands": "手部动作减少·静止时间延长·可能无意识触摸慰藉物(杯子/照片)",
            "voice": "音量微降·语速微降·音调范围收缩·句尾下沉·停顿增加",
        }
    },
    "guilt": {
        "name_cn": "内疚",
        "keywords": ["不是", "不知道", "没想", "对不起", "不应该"],
        "anatomical": {
            "eyes": "注视时间减少·视线向下或向侧·不直视对方·眨眼频率增加·眼睑微垂",
            "mouth": "嘴唇内收·嘴角微降·下颌微收",
            "posture": "躯干微缩·肩部前收·身体面积缩小·头位微低",
            "hands": "手部自我接触增加·手指摩擦·触碰面部(遮盖型)",
            "voice": "音量降低·语速减慢·句尾声音减弱",
        }
    },
    "contempt": {
        "name_cn": "轻蔑",
        "keywords": ["老样子", "每天", "还是", "又是你"],
        "anatomical": {
            "eyes": "单侧眼睑微紧·视线从对方身上扫过后移开·或俯视角度注视",
            "brow": "单侧眉头上扬(轻蔑标志性不对称)·持续约1-2秒",
            "mouth": "单侧嘴角收紧上提(不对称微笑)·或上唇单侧微升",
        }
    },
    "surprise_brief": {
        "name_cn": "惊讶(短暂)",
        "keywords": ["什么", "怎么", "突然", "门铃", "推门"],
        "anatomical": {
            "eyes": "上眼睑瞬间抬高·巩膜上方暴露增加·持续约500ms·随后恢复基线",
            "brow": "双眉同时上扬·额头出现横纹·持续约500ms",
            "mouth": "下颌瞬间微降·嘴唇分开约5mm·持续约500ms·随后闭合",
        }
    },
    "focus": {
        "name_cn": "专注",
        "keywords": ["擦", "做咖啡", "盯着", "看着", "注视"],
        "anatomical": {
            "eyes": "注视时长大幅增加·视线锁定目标·眨眼频率减少50%以上",
            "brow": "眉位微降·眉间微收·非愤怒性·注意力集中的生理反应",
            "posture": "躯干前倾·头位朝向目标·身体其他部位静止·减少不必要微动作",
        }
    },
    "evaluation": {
        "name_cn": "评估/判断",
        "keywords": ["看", "扫", "扫过", "瞥", "扫视", "目光扫过"],
        "anatomical": {
            "eyes": "注视时长中等·视线在对象和远处之间交替·每次注视约2-3秒",
            "brow": "单侧眉头微抬(约1秒)·或眉头微皱(约2秒)·非对称性",
            "mouth": "嘴唇微抿·下唇可能被上齿轻咬·或嘴角微偏一侧(思考中的不对称)",
            "hands": "指尖触碰下巴或嘴唇·头部微倾",
        }
    },
    "relaxed_genuine": {
        "name_cn": "放松/真实",
        "keywords": ["早啊", "谢谢", "老样子", "常客", "每天", "日常"],
        "anatomical": {
            "eyes": "眼轮匝肌参与·下眼睑出现真实笑纹(鱼尾纹)·眼型改变·上眼睑微垂",
            "mouth": "嘴角对称上提·上唇自然升露上齿·微笑启动平滑(无延迟)·唇形自然",
            "brow": "眉位自然·无多余张力·眉间平滑",
            "posture": "姿态开放·躯干正对对方·肩部放松·身体面积正常展开",
        }
    },
    "tension": {
        "name_cn": "紧张",
        "keywords": ["等", "停", "没有动", "不回答", "沉默", "安静", "停了"],
        "anatomical": {
            "eyes": "眼睑微紧·眨眼频率增加·视线不稳定(在多个点之间快速移动)",
            "brow": "眉间微收·眉位微升·额头可能出现浅横纹",
            "mouth": "嘴唇微紧·唇红变薄·可能出现舔唇(紧张的口干)",
            "hands": "手部动作增加·手指抖动·握拳或抓握衣物·自我安抚",
            "voice": "音量不稳定·语速微增或微降·气息变浅·声带紧绷",
        }
    },
    "detachment": {
        "name_cn": "疏离",
        "keywords": ["每个人", "看着别人", "这座城市的", "有些人在被看"],
        "anatomical": {
            "eyes": "注视时长减少·视线焦点柔和(不聚焦于对方)·眼神空洞",
            "brow": "眉位平坦·无表情·无张力·眉间平滑",
            "mouth": "嘴唇自然闭合·唇形中性·无上扬无下降·无肌肉张力",
            "posture": "躯干微后倾·身体朝向微偏·与环境的物理距离增加",
            "voice": "音量中等偏低·语速微降·音调单调(范围收缩)·句尾平直",
        }
    },
    "threat_perception": {
        "name_cn": "威胁感知",
        "keywords": ["路灯杆", "棒球帽", "夹克", "口袋", "手机", "一动不动", "面朝"],
        "anatomical": {
            "eyes": "视线瞬间锁定威胁源·注视强度增加·瞳孔先散大(警戒)后收缩(评估)·眨眼暂停",
            "brow": "眉位微降·眉间微收·上眼睑微抬(增加视野)·整体眉毛向眉心集中",
            "posture": "躯干瞬间静止·准备反应(战斗/逃跑)·重心微降·颈部肌肉收紧",
            "hands": "手部动作瞬间停止·手指屈曲准备·或手部移向身体(保护性)",
        }
    },
}

# ===== 角色默认状态 =====

CHARACTER_BASELINE = {
    "Isabela": {
        "default_states": ["relaxed_genuine", "avoidance", "fear_suppressed", "sadness_masked"],
        "baseline": "真实度高·微表情×2·假笑可识别",
        "notes": "对Sera=真实·对Rico=矛盾(表层关心+深层恐惧)",
    },
    "Rico": {
        "default_states": ["power_play", "avoidance", "threat_perception", "lying"],
        "baseline": "专家掩饰者·微表情×0.5·注视增加·静止增加",
        "notes": "比Isabela更早知道威胁·每句对白表层日常+深层警惕",
    },
    "Sera": {
        "default_states": ["relaxed_genuine", "surprise_brief"],
        "baseline": "普通人·无特殊调整",
        "notes": "正常世界锚点·对白简短·无复杂心理",
    },
    "BaseballCapMan": {
        "default_states": ["threat_perception", "focus"],
        "baseline": "不可读·仅身体语言·面部禁用performance",
        "notes": "帽檐阴影遮眼·全场景一镜",
    },
    "VO": {
        "default_states": ["detachment"],
        "baseline": "上帝视角·叙述性·无角色约束",
        "notes": "句尾平直·音调单调",
    },
}

# ===== 上下文模式 =====

CONTEXT_PATTERNS = {
    "质问": ["anger_suppressed", "fear_suppressed", "power_play"],
    "沉默": ["tension", "avoidance", "guilt"],
    "日常": ["relaxed_genuine"],
    "监视": ["threat_perception", "focus"],
    "离别": ["sadness_masked", "avoidance"],
    "发现": ["surprise_brief", "fear_suppressed", "evaluation"],
    "掩饰": ["lying", "avoidance", "tension"],
    "回忆": ["sadness_masked", "detachment"],
}


# ===== 主算法 =====

def parse_dialogue(script_path: str) -> List[Dict]:
    """从剧本提取对白·附带上下文角色和场景"""
    with open(script_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    dialogues = []
    context_stack = []
    speaker_map = {"伊莎贝拉": "Isabela", "塞拉": "Sera"}

    for i, line in enumerate(lines):
        # Track context from action descriptions
        stripped = line.strip()
        if stripped.startswith("△"):
            context_stack.append(stripped[2:])
            if len(context_stack) > 3:
                context_stack.pop(0)

        # CV lines (direction in parentheses is optional)
        m = re.match(r"CV\s+(\S+)(?:[（(](.*?)[）)])?[：:](.+)", line)
        if m:
            speaker_raw = m.group(1)
            dialogues.append({
                "speaker": speaker_map.get(speaker_raw, speaker_raw),
                "text": m.group(3).strip(),
                "direction": m.group(2),
                "context": " ".join(context_stack[-3:]),
                "line_num": i + 1,
            })
            context_stack = []

        # VO lines
        m = re.match(r"VO[：:](.+)", line)
        if m:
            dialogues.append({
                "speaker": "VO",
                "text": m.group(1).strip(),
                "direction": "低沉男声·叙述性",
                "context": " ".join(context_stack[-3:]),
                "line_num": i + 1,
            })

    return dialogues


def match(dialogue: Dict) -> List[Dict]:
    """
    三 tier 自适应匹配。
    返回所有候选·不截断·附带分数、来源、完整解剖学描述。
    """
    text = dialogue["text"]
    speaker = dialogue["speaker"]
    direction = dialogue.get("direction", "")
    context = dialogue.get("context", "")
    combined = text + (direction or "") + (context or "")

    candidates = {}  # state_name -> {score, sources, anatomical}

    # Tier 1: 关键词匹配 (权重 3·特异性加权)
    # 计算每个关键词的全局特异性(匹配的状态数越少越特异)
    kw_specificity = {}
    for kw in set(kw for sd in STATES.values() for kw in sd["keywords"]):
        match_count = sum(1 for sd in STATES.values() if kw in sd["keywords"])
        kw_specificity[kw] = 3.0 / match_count  # 独占=3分·3个状态共享=1分

    for state_name, state_data in STATES.items():
        hits = [kw for kw in state_data["keywords"] if kw in combined]
        if hits:
            specificity_score = sum(kw_specificity.get(h, 0.5) for h in hits)
            candidates[state_name] = {
                "score": round(specificity_score, 1),
                "sources": [f"keyword:{h}" for h in hits[:3]],
                "anatomical": state_data["anatomical"],
                "name_cn": state_data["name_cn"],
            }

    # Tier 2: 角色默认状态 (权重 2·不覆盖 Tier 1)
    char_data = CHARACTER_BASELINE.get(speaker, {})
    for state_name in char_data.get("default_states", []):
        if state_name not in candidates and state_name in STATES:
            candidates[state_name] = {
                "score": 2,
                "sources": [f"character:{speaker}"],
                "anatomical": STATES[state_name]["anatomical"],
                "name_cn": STATES[state_name]["name_cn"],
            }

    # Tier 3: 上下文模式 (权重 1·不覆盖 Tier 1/2)
    for pattern, states in CONTEXT_PATTERNS.items():
        if pattern in combined:
            for state_name in states:
                if state_name not in candidates and state_name in STATES:
                    candidates[state_name] = {
                        "score": 1,
                        "sources": [f"context:{pattern}"],
                        "anatomical": STATES[state_name]["anatomical"],
                        "name_cn": STATES[state_name]["name_cn"],
                    }

    # Sort by score desc
    result = sorted(candidates.values(), key=lambda x: -x["score"])
    # Add state key
    for r in result:
        for sk, sv in STATES.items():
            if sv["name_cn"] == r["name_cn"]:
                r["state_key"] = sk
                break

    return result


def pre_compute(script_path: str, output_path: str) -> dict:
    """主入口：提取对白→匹配→输出候选"""
    dialogues = parse_dialogue(script_path)

    results = []
    for d in dialogues:
        candidates = match(d)
        results.append({
            "speaker": d["speaker"],
            "text": d["text"],
            "direction": d.get("direction", ""),
            "line_num": d["line_num"],
            "candidates": candidates,
            "candidate_count": len(candidates),
        })

    # Stats
    total = len(dialogues)
    avg_candidates = sum(r["candidate_count"] for r in results) / max(total, 1)
    tier1 = sum(1 for r in results if any("keyword" in c["sources"][0] for c in r["candidates"][:1]))
    tier2 = sum(1 for r in results if r["candidates"] and r["candidates"][0]["score"] == 2)
    tier3 = sum(1 for r in results if r["candidates"] and r["candidates"][0]["score"] == 1)

    output = {
        "meta": {
            "total_dialogues": total,
            "avg_candidates": round(avg_candidates, 1),
            "tier1_keyword_matches": tier1,
            "tier2_character_defaults": tier2,
            "tier3_context_patterns": tier3,
            "states_in_kb": len(STATES),
            "matcher_version": "v1.0",
        },
        "dialogues": results,
        # Include full KB for LLM reference
        "_kb_speed_ref": {
            sk: {"name_cn": sv["name_cn"], "keywords": sv["keywords"][:5],
                 "eyes": sv["anatomical"].get("eyes", "")[:60]}
            for sk, sv in STATES.items()
        }
    }

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(output, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"=== performance_matcher v1.0 ===")
    print(f"  Dialogues: {total}")
    print(f"  Avg candidates: {avg_candidates} (vs 15 full search)")
    print(f"  Tier 1 (keyword): {tier1}")
    print(f"  Tier 2 (character): {tier2}")
    print(f"  Tier 3 (context): {tier3}")
    print(f"  LLM work: confirm from N candidates (not search 15)")
    print(f"  Output: {output_path}")

    return output


def main():
    p = argparse.ArgumentParser(description="performance_matcher.py v1.0")
    p.add_argument("--script", required=True, help="Script .txt path")
    p.add_argument("--out", required=True, help="Output candidates .yml path")
    args = p.parse_args()
    pre_compute(args.script, args.out)


if __name__ == "__main__":
    main()
