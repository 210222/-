"""
镜级分类 + 确定性预填引擎 v1.0 — MODE:P 算法核心
替代"1 Agent串行设计全部镜头"的旧算法

Phase 1: 每镜分类 — PATTERN(继承历史) | CONSTRAINT(约束自动) | CREATIVE(需LLM)
Phase 2: 确定性预填 — PATTERN+CONSTRAINT镜自动生成参数
Phase 3: 只把CREATIVE镜交给LLM并行设计
Phase 4: 组装全部结果 + Gate 0检查

预期: 17镜场景 → 5-7镜需LLM → 墙钟 = 最慢那镜(2-3分钟) 不是17镜之和(15分钟)
"""
import json
import re
import sys
import os
from collections import defaultdict

# ═══════════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════════

PATTERN_DIR = os.path.join(os.path.dirname(__file__), '..', '04_共享', 'decision_patterns')
CONSTRAINT_FILE = os.path.join(os.path.dirname(__file__), '..', '04_共享', 'constraint_definitions.json')

# 镜功能 → 默认景别/焦距 (约束驱动)
FUNCTION_DEFAULTS = {
    '开场建立':   {'shot_type': '全景',    'focal_length': '24mm',  'movement': '固定', 'function': '建立空间'},
    '物件特写':   {'shot_type': '大特写',  'focal_length': '100mm', 'movement': '固定', 'function': '冷开场·证据建立'},
    '人物建立':   {'shot_type': '近景',    'focal_length': '50mm',  'movement': '固定', 'function': '建立人物'},
    '对话双人':   {'shot_type': '中景',    'focal_length': '35mm',  'movement': '固定', 'function': '双人同框对话'},
    '单人反应':   {'shot_type': '中近景',  'focal_length': '50mm',  'movement': '固定', 'function': '单人对白接球'},
    '屏幕/证据':  {'shot_type': '特写',    'focal_length': '85mm',  'movement': '固定', 'function': '插入镜头·证据展示'},
    '过渡/转场':  {'shot_type': '中景',    'focal_length': '35mm',  'movement': '固定', 'function': '空间过渡'},
    '退场/收起':  {'shot_type': '全景',    'focal_length': '24mm',  'movement': '固定', 'function': '场景收尾'},
    '动作/运动':  {'shot_type': '中景',    'focal_length': '35mm',  'movement': '跟拍', 'function': 'CREATIVE·需LLM'},
    '情绪特写':   {'shot_type': '特写',    'focal_length': '85mm',  'movement': '固定', 'function': 'CREATIVE·需LLM'},
}


def load_patterns():
    """加载所有历史模式"""
    patterns = {}
    if not os.path.exists(PATTERN_DIR):
        return patterns

    for root, dirs, files in os.walk(PATTERN_DIR):
        for f in files:
            if f == 'pattern.json':
                path = os.path.join(root, f)
                try:
                    with open(path, 'r', encoding='utf-8') as fp:
                        p = json.load(fp)
                    scene_type = p.get('_meta', {}).get('scene_type', '')
                    patterns[scene_type] = p
                except Exception:
                    pass
    return patterns


def load_constraints():
    """加载约束定义"""
    try:
        with open(CONSTRAINT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def extract_shots(script_text):
    """从MODE:A增强剧本中提取每镜信息"""
    shots = []

    # 按分镜块分割
    shot_blocks = re.split(r'\n### 分镜 \d+', script_text)
    if len(shot_blocks) <= 1:
        shot_blocks = re.split(r'\n## SHOT-|\n### SHOT-', script_text)

    for i, block in enumerate(shot_blocks):
        if i == 0 and '分镜' not in block:
            continue

        shot = {'shot_id': i, 'text': block[:500]}

        # 提取镜号
        m = re.search(r'分镜\s*(\d+)', block)
        if m: shot['label'] = f'镜#{m.group(1)}'

        # 提取景别
        m = re.search(r'(?:景别|shot_type)[：:]\s*(\S+)', block)
        if m: shot['existing_shot_type'] = m.group(1)

        # 提取推荐时长
        m = re.search(r'推荐时长[：:]*\s*(\d+)', block)
        if m: shot['duration'] = int(m.group(1))

        # 判断功能 (优先级从具体到通用)
        if any(w in block for w in ['转身', '走向', '后退', '站起', '运动', '动作','推近','横移','摇臂']):
            if any(w in block for w in ['对白', '说话', '对话']):
                shot['function'] = '对话双人'
            else:
                shot['function'] = '动作/运动'
        elif any(w in block for w in ['弹头', '显微镜', '锉刀', '游标卡尺', '证物']):
            shot['function'] = '物件特写'
        elif any(w in block for w in ['屏幕', 'LED', '弹道', '蓝光']):
            shot['function'] = '屏幕/证据'
        elif any(w in block for w in ['对白', '说话', '对话', '开口']):
            if any(w in block for w in ['两人', '双人', '同框', '同时']):
                shot['function'] = '对话双人'
            else:
                shot['function'] = '单人反应'
        elif any(w in block for w in ['表情', '眼神', '面部特写', '情绪']):
            shot['function'] = '情绪特写'
        elif any(w in block for w in ['反应', '倾听', '接球', '凝视']):
            shot['function'] = '单人反应'
        elif any(w in block for w in ['开场', '建立', '全景', '环境']):
            shot['function'] = '开场建立'
        elif any(w in block for w in ['离去', '关灯', '结束', '收尾', '走远']):
            shot['function'] = '退场/收起'
        elif '特写' in block or '微距' in block or 'ECU' in block:
            shot['function'] = '物件特写'
        elif '近景' in block or '中近景' in block or 'CU' in block:
            shot['function'] = '单人反应'
        else:
            shot['function'] = '单人反应'  # 默认

        shots.append(shot)

    return shots


# 功能标签 ↔ 模式setup名称映射
FUNC_TO_PATTERN = {
    '开场建立': ['establishing', 'opening_shot', 'workspace_setup'],
    '物件特写': ['evidence_ecu', 'opening_shot', 'screen_evidence'],
    '人物建立': ['character_at_work', 'character_closeup'],
    '对话双人': ['dialogue_setup', 'dialogue_master', 'transition_to_meeting'],
    '单人反应': ['single_react', 'character_closeup', 'dialogue_setup'],
    '屏幕/证据': ['screen_evidence', 'evidence_ecu'],
    '动作/运动': [],   # 必须LLM
    '情绪特写': [],    # 必须LLM
    '过渡/转场': ['transition_to_meeting', 'visitor_entrance'],
    '退场/收起': ['establishing'],
}


def classify_shot(shot, pattern, constraints):
    """对单个镜头分类"""
    func = shot.get('function', '')

    # 必须LLM判断的功能
    if func in ('动作/运动', '情绪特写'):
        return 'CREATIVE', '运动或情绪镜头需要LLM判断节奏和细节'

    # 匹配历史模式
    if pattern:
        target_names = FUNC_TO_PATTERN.get(func, [])
        verified = pattern.get('verified_camera_setups', {})
        for target in target_names:
            if target in verified:
                return 'PATTERN', f'匹配: {target}'

    # 约束驱动
    if func in FUNCTION_DEFAULTS:
        return 'CONSTRAINT', f'约束驱动: {func}'

    return 'CREATIVE', '无法匹配·需LLM'


def prefilled_shot(shot, classification, pattern, constraints):
    """为 PATTERN/CONSTRAINT 镜预填参数"""
    func = shot.get('function', '')
    result = {
        'shot_id': shot.get('shot_id'),
        'label': shot.get('label', ''),
        'classification': classification,
        'function': func,
    }

    if classification == 'PATTERN' and pattern:
        target_names = FUNC_TO_PATTERN.get(func, [])
        verified = pattern.get('verified_camera_setups', {})
        for target in target_names:
            if target in verified:
                setup = verified[target]
                result['shot_type'] = setup.get('shot_type', '')
                result['focal_length'] = setup.get('focal_length', '')
                result['angle'] = setup.get('angle', '')
                result['dof'] = setup.get('dof', '')
                result['kb_rules'] = setup.get('kb_rules', [])
                result['source'] = f'PATTERN: {target}'
                return result
        # 模式匹配失败·降级为约束驱动
        defaults = FUNCTION_DEFAULTS.get(func, FUNCTION_DEFAULTS['单人反应'])
        result['shot_type'] = defaults['shot_type']
        result['focal_length'] = defaults['focal_length']
        result['movement'] = defaults['movement']
        result['source'] = f'CONSTRAINT (pattern miss): {func}'
        return result

    if classification == 'CONSTRAINT':
        defaults = FUNCTION_DEFAULTS.get(func, FUNCTION_DEFAULTS['单人反应'])
        result['shot_type'] = defaults['shot_type']
        result['focal_length'] = defaults['focal_length']
        result['movement'] = defaults['movement']
        result['source'] = f'CONSTRAINT: {func}'

        # 焦距范围验证
        dialogue_constraints = constraints.get('domains', {}).get('对话场景', {})
        focal_ranges = dialogue_constraints.get('focal_length', {}).get('ranges', {})
        st = result['shot_type']
        if st in focal_ranges:
            result['focal_range'] = f'{focal_ranges[st][0]}-{focal_ranges[st][1]}mm'
        return result

    return result


def classify_all(script_path, scene_type=None):
    """对剧本中全部镜头执行分类+预填"""
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            script_text = f.read()
    except Exception as e:
        return None, str(e)

    patterns = load_patterns()
    constraints = load_constraints()

    # 匹配最佳模式
    best_pattern = None
    if scene_type and scene_type in patterns:
        best_pattern = patterns[scene_type]
    else:
        for ptype, p in patterns.items():
            keywords = p.get('spatial_layout', {}).get('key_elements', [])
            hits = sum(1 for kw in keywords if kw in script_text[:3000])
            if hits >= 2:
                best_pattern = p
                scene_type = ptype
                break

    shots = extract_shots(script_text)
    if not shots:
        return None, "未提取到镜头"

    results = []
    stats = defaultdict(int)

    for shot in shots:
        classification, reason = classify_shot(shot, best_pattern, constraints)
        stats[classification] += 1

        result = prefilled_shot(shot, classification, best_pattern, constraints)
        result['reason'] = reason
        results.append(result)

    return {
        'scene_type': scene_type or '未知',
        'pattern_used': best_pattern.get('_meta', {}).get('canonical_reference', '无') if best_pattern else '无',
        'total_shots': len(shots),
        'stats': dict(stats),
        'pattern_shots': stats.get('PATTERN', 0),
        'constraint_shots': stats.get('CONSTRAINT', 0),
        'creative_shots': stats.get('CREATIVE', 0),
        'llm_needed': stats.get('CREATIVE', 0),
        'llm_saved': stats.get('PATTERN', 0) + stats.get('CONSTRAINT', 0),
        'estimated_wall_clock': f'{stats.get("CREATIVE", 3) * 3}分钟 (仅{stats.get("CREATIVE", 0)}镜需LLM·并行)',
        'old_wall_clock': f'{len(shots) * 1}分钟 (串行全部{len(shots)}镜)',
        'shots': results
    }, None


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    if len(sys.argv) < 2:
        print("用法: python shot_classifier.py [MODE:A增强剧本路径] [场景类型(可选)]")
        print("示例: python shot_classifier.py 枪王_EP13_增强分镜剧本_v3.md 室内调查_实验室")
        sys.exit(1)

    script_path = sys.argv[1]
    scene_type = sys.argv[2] if len(sys.argv) > 2 else None

    result, error = classify_all(script_path, scene_type)

    if error:
        print(f"ERROR: {error}")
        sys.exit(1)

    print(f"\n## 镜级分类结果: {result['scene_type']}")
    print(f"历史模式: {result['pattern_used']}")
    print(f"总镜数: {result['total_shots']}")
    print(f"\n分类统计:")
    print(f"  PATTERN (继承历史):   {result['pattern_shots']}镜")
    print(f"  CONSTRAINT (约束自动): {result['constraint_shots']}镜")
    print(f"  CREATIVE (需LLM):     {result['creative_shots']}镜")
    print(f"\nLLM工作量: {result['llm_needed']}镜 (节省 {result['llm_saved']}镜)")
    print(f"预估墙钟: {result['estimated_wall_clock']}")
    print(f"旧算法:   {result['old_wall_clock']}")

    # 输出每镜详情
    print(f"\n## 逐镜分类")
    for s in result['shots']:
        cls = s['classification']
        icon = {'PATTERN': '♻️', 'CONSTRAINT': '⚙️', 'CREATIVE': '🧠'}.get(cls, '?')
        print(f"  {icon} {s.get('label','?')}: {cls} — {s.get('source','?')} — {s.get('reason','')}")

    # 保存
    out_path = os.path.join(os.path.dirname(script_path) if os.path.dirname(script_path) else '.',
                            '..', '02_Agent', 'output',
                            f'SHOT_CLASSIFICATION_{os.path.basename(script_path).replace(".md",".json")}')
    try:
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n分类结果: {out_path}")
    except Exception:
        pass


if __name__ == '__main__':
    main()
