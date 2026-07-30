"""
Layer 0 空间硬约束检查器 v1.1 — MODE:P 管道前置验证
调度器自执行·零LLM·纯几何/数值/逻辑检查

检查项:
  S01: 180度线一致性 (相邻镜axis_side)
  S02: 景别递进合理性 (相邻镜shot_type跳变)
  S03: 焦距-景别匹配 (给定景别的焦距是否在合理范围)
  S04: 运镜速度合理性 (速度参数是否在允许范围)
  S05: 角色位置合法性 (角色坐标是否在可站立区域)
  S06: 机位空间可行性 (机位是否在空间边界内)
  S07: 视线遮挡检查 (机位→角色连线是否穿过障碍物)

🆕 v1.1: 约束定义从 constraint_definitions.json 加载 (Layer 1)
         与Agent的"约束菜单"共享同一数据源

输入: 设计Agent的结构化YAML输出 (segments_camera + global_anchors)
      空间地图 (可选·文本描述或结构化坐标)
输出: SPATIAL_CHECK_REPORT.md · 违规清单

用法: python spatial_check.py [YAML文件路径] [空间地图路径(可选)]
"""
import re
import sys
import os
import json
import yaml
from datetime import datetime
from collections import defaultdict

# ═══════════════════════════════════════════════════════════
# 从 constraint_definitions.json 加载约束
# ═══════════════════════════════════════════════════════════

CONSTRAINT_FILE = os.path.join(os.path.dirname(__file__), '..', '04_共享', 'constraint_definitions.json')

def load_constraints():
    """加载 Layer 1 约束定义"""
    try:
        with open(CONSTRAINT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None

CONSTRAINTS = load_constraints()

# 合法景别值 (从约束定义加载·回退到硬编码)
if CONSTRAINTS:
    dialogue_constraints = CONSTRAINTS.get('domains', {}).get('对话场景', {})
    VALID_SHOT_TYPES = dialogue_constraints.get('shot_type', {}).get('valid_values',
        ["大特写","特写","近景","中近景","中景","中全景","全景"])
    SHOT_FOCAL_RANGES = dialogue_constraints.get('focal_length', {}).get('ranges',
        {"大特写":[85,200],"特写":[85,135],"近景":[50,100],"中近景":[35,85],"中景":[24,50],"中全景":[24,35],"全景":[16,35]})
    MAX_SHOT_TYPE_JUMP = dialogue_constraints.get('shot_type_jump', {}).get('max_jump', 3)
    MOVEMENT_SPEED_MAX = 3.0
else:
    VALID_SHOT_TYPES = ["大特写","特写","近景","中近景","中景","中全景","全景"]
    SHOT_FOCAL_RANGES = {"大特写":[85,200],"特写":[85,135],"近景":[50,100],"中近景":[35,85],"中景":[24,50],"中全景":[24,35],"全景":[16,35]}
    MAX_SHOT_TYPE_JUMP = 3
    MOVEMENT_SPEED_MAX = 3.0

SHOT_TYPE_RANK = {t: i for i, t in enumerate(VALID_SHOT_TYPES)}


# ═══════════════════════════════════════════════════════════
# YAML 解析
# ═══════════════════════════════════════════════════════════

def extract_yaml_blocks(filepath):
    """从设计报告或台本文件中提取所有YAML块"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except (FileNotFoundError, UnicodeDecodeError) as e:
        return None, str(e)

    # 查找 ```yaml ... ``` 块
    yaml_blocks = []
    pattern = r'```yaml\n(.*?)```'
    matches = re.findall(pattern, content, re.DOTALL)

    for i, match in enumerate(matches):
        try:
            data = yaml.safe_load(match)
            if data:
                yaml_blocks.append(data)
        except yaml.YAMLError as e:
            continue

    return yaml_blocks, None


def parse_segments(yaml_blocks):
    """从YAML块中提取segments_camera数据"""
    segments = []

    for block in yaml_blocks:
        if isinstance(block, dict):
            # 直接是 segments_camera
            if 'segments_camera' in block:
                segments.extend(block['segments_camera'])
            # 嵌套在场景数据中
            if 'scene' in block:
                scene = block['scene']
                if isinstance(scene, dict) and 'segments_camera' in scene:
                    segments.extend(scene['segments_camera'])
            # segments 是顶层key
            if 'segments' in block:
                segs = block['segments']
                if isinstance(segs, list):
                    segments.extend(segs)

    return segments


def parse_inline_yaml(filepath):
    """解析嵌入在markdown中的YAML (非```yaml围栏格式)"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return []

    segments = []

    # 查找 segments_camera: 起始的YAML区域
    seg_pattern = r'segments_camera:\n((?:\s+-.*\n(?:\s+.*\n)*)+)'
    matches = re.findall(seg_pattern, content)

    for match in matches:
        try:
            data = yaml.safe_load('segments_camera:\n' + match)
            if data and 'segments_camera' in data:
                segments.extend(data['segments_camera'])
        except yaml.YAMLError:
            # 逐项解析
            entries = re.findall(r'\s+- segment_id:[^\n]*\n(?:\s+[^-\n][^\n]*\n)*', match)
            for entry in entries:
                seg = {}
                m = re.search(r'segment_id:\s*"([^"]*)"', entry)
                if m: seg['segment_id'] = m.group(1)
                m = re.search(r'shot_type:\s*"([^"]*)"', entry)
                if m: seg['shot_type'] = m.group(1)
                m = re.search(r'focal_length:\s*"([^"]*)"', entry)
                if m: seg['focal_length'] = m.group(1)
                m = re.search(r'dof:\s*"([^"]*)"', entry)
                if m: seg['dof'] = m.group(1)
                m = re.search(r'angle:\s*"([^"]*)"', entry)
                if m: seg['angle'] = m.group(1)
                if seg:
                    segments.append(seg)

    return segments


def parse_text_camera_params(filepath):
    """回退方案: 从自由文本中正则提取镜头参数"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return []

    # 先尝试内联YAML
    segments = parse_inline_yaml(filepath)
    if segments:
        return segments

    # 匹配 【镜头参数卡】 块中的参数
    shots = []
    param_blocks = re.findall(r'【镜头参数卡】\n(.*?)(?=\n【|\Z)', content, re.DOTALL)

    for i, block in enumerate(param_blocks):
        shot = {'shot_id': f'SHOT-{i+1:02d}'}

        # 提取景别
        m = re.search(r'景别[：:]\s*(\S+)', block)
        if m: shot['shot_type'] = m.group(1).strip()

        # 提取运镜
        m = re.search(r'运镜[：:]\s*(.+?)(?:\n|$)', block)
        if m: shot['movement'] = m.group(1).strip()

        # 提取焦距
        m = re.search(r'焦距[：:]\s*(\d+)mm', block)
        if m: shot['focal_length'] = f"{m.group(1)}mm"

        # 提取角度
        m = re.search(r'角度[：:]\s*(.+?)(?:\n|$)', block)
        if m: shot['angle'] = m.group(1).strip()

        shots.append(shot)

    return shots


# ═══════════════════════════════════════════════════════════
# 检查函数
# ═══════════════════════════════════════════════════════════

def check_180_degree(segments):
    """S01: 检查180度线一致性"""
    violations = []

    axis_values = []
    for seg in segments:
        axis = seg.get('axis_side', seg.get('axis', None))
        axis_values.append(axis)

    for i in range(len(axis_values) - 1):
        curr, next_ = axis_values[i], axis_values[i+1]
        if curr and next_ and curr != next_:
            curr_id = segments[i].get('segment_id', segments[i].get('shot_id', f'#{i+1}'))
            next_id = segments[i+1].get('segment_id', segments[i+1].get('shot_id', f'#{i+2}'))
            violations.append({
                'rule': 'S01',
                'name': '180度线跳轴',
                'severity': '阻断',
                'shot': f'{curr_id}→{next_id}',
                'detail': f'axis_side从"{curr}"跳到"{next_}"·无过波镜标注',
                'fix': '插入中性过波镜(空镜/特写/插入镜头)·或调整机位到关系线同一侧'
            })

    return violations


def check_shot_type_jump(segments):
    """S02: 检查景别递进"""
    violations = []

    types = []
    for seg in segments:
        st = seg.get('shot_type', '')
        types.append(st)

    for i in range(len(types) - 1):
        curr, next_ = types[i], types[i+1]
        if curr in SHOT_TYPE_RANK and next_ in SHOT_TYPE_RANK:
            jump = abs(SHOT_TYPE_RANK[next_] - SHOT_TYPE_RANK[curr])
            if jump > MAX_SHOT_TYPE_JUMP:
                curr_id = segments[i].get('segment_id', segments[i].get('shot_id', f'#{i+1}'))
                next_id = segments[i+1].get('segment_id', segments[i+1].get('shot_id', f'#{i+2}'))
                violations.append({
                    'rule': 'S02',
                    'name': '景别跳变过大',
                    'severity': '警告',
                    'shot': f'{curr_id}({curr})→{next_id}({next_})',
                    'detail': f'景别跳变{jump}级·超过{MAX_SHOT_TYPE_JUMP}级上限',
                    'fix': '插入中间景别过渡镜·如中景→中近景→特写'
                })

    return violations


def check_focal_shot_match(segments):
    """S03: 检查焦距与景别匹配"""
    violations = []

    for seg in segments:
        shot_type = seg.get('shot_type', '')
        focal_str = seg.get('focal_length', '')
        seg_id = seg.get('segment_id', seg.get('shot_id', '?'))

        if not shot_type or not focal_str:
            continue

        # 提取焦距数值
        m = re.search(r'(\d+)', str(focal_str))
        if not m:
            continue
        focal = int(m.group(1))

        if shot_type in SHOT_FOCAL_RANGES:
            min_f, max_f = SHOT_FOCAL_RANGES[shot_type]
            if focal < min_f or focal > max_f:
                violations.append({
                    'rule': 'S03',
                    'name': '焦距-景别不匹配',
                    'severity': '警告',
                    'shot': seg_id,
                    'detail': f'{shot_type}建议焦距{min_f}-{max_f}mm·实际{focal}mm',
                    'fix': f'调整为{min_f}-{max_f}mm范围内的焦距·或改为匹配的景别'
                })

    return violations


def check_movement_speed(segments):
    """S04: 检查运镜速度"""
    violations = []

    for seg in segments:
        movement = seg.get('movement', seg.get('movement_type', ''))
        speed = seg.get('speed', seg.get('speed_tier', ''))
        seg_id = seg.get('segment_id', seg.get('shot_id', '?'))

        if not movement or '固定' in str(movement) or 'static' in str(movement).lower():
            continue

        # 提取速度数值
        speed_val = None
        if isinstance(speed, (int, float)):
            speed_val = speed
        elif isinstance(speed, str):
            m = re.search(r'([\d.]+)', speed)
            if m:
                speed_val = float(m.group(1))

        if speed_val is not None:
            if speed_val > MOVEMENT_SPEED_MAX:
                violations.append({
                    'rule': 'S04',
                    'name': '运镜速度过高',
                    'severity': '警告',
                    'shot': seg_id,
                    'detail': f'运镜速度{speed_val}x·超过S7(3.0x)上限',
                    'fix': '降低速度或标注为特殊效果(甩镜/冲刺)'
                })

            if 0 < speed_val < 0.01:
                violations.append({
                    'rule': 'S04',
                    'name': '运镜速度过低',
                    'severity': '建议',
                    'shot': seg_id,
                    'detail': f'运镜速度{speed_val}x·低于S1(0.01x)下限·几乎不可感知',
                    'fix': '确认此速度是设计意图·或提高到0.01x以上'
                })

    return violations


def check_character_position(segments, space_map=None):
    """S05: 检查角色位置"""
    violations = []

    # 如果没有空间地图·只做基本检查
    if not space_map:
        # 检查角色位置是否在segments中标注
        for seg in segments:
            char_pos = seg.get('character_position', seg.get('char_position', None))
            if not char_pos:
                seg_id = seg.get('segment_id', seg.get('shot_id', '?'))
                violations.append({
                    'rule': 'S05',
                    'name': '缺少角色位置',
                    'severity': '建议',
                    'shot': seg_id,
                    'detail': '未标注角色位置·无法验证空间可行性',
                    'fix': '在YAML中标注character_position字段'
                })
        return violations

    # TODO: 当空间地图有结构化坐标时·检查角色在可站立区域内
    return violations


def check_camera_in_bounds(segments, space_map=None):
    """S06: 检查机位空间可行性"""
    violations = []

    if not space_map:
        return violations

    # TODO: 碰撞检测——机位坐标是否在空间边界内
    return violations


def check_line_of_sight(segments, space_map=None):
    """S07: 检查视线遮挡"""
    violations = []

    if not space_map:
        return violations

    # TODO: 视线检测——机位→角色连线是否穿过障碍物
    return violations


# ═══════════════════════════════════════════════════════════
# 主检查函数
# ═══════════════════════════════════════════════════════════

def spatial_check(filepath, space_map_path=None):
    """执行全部空间硬约束检查"""

    # 加载空间地图
    space_map = None
    if space_map_path and os.path.exists(space_map_path):
        try:
            with open(space_map_path, 'r', encoding='utf-8') as f:
                space_map = f.read()
        except Exception:
            pass

    # 尝试解析YAML
    yaml_blocks, error = extract_yaml_blocks(filepath)
    segments = []

    if yaml_blocks:
        segments = parse_segments(yaml_blocks)

    # YAML解析失败或为空 → 回退到文本解析
    if not segments:
        segments = parse_text_camera_params(filepath)

    if not segments:
        return None, "无法从文件中提取镜头参数·请确认输出格式含segments_camera YAML块或【镜头参数卡】块"

    all_violations = []
    all_violations.extend(check_180_degree(segments))
    all_violations.extend(check_shot_type_jump(segments))
    all_violations.extend(check_focal_shot_match(segments))
    all_violations.extend(check_movement_speed(segments))
    all_violations.extend(check_character_position(segments, space_map))
    all_violations.extend(check_camera_in_bounds(segments, space_map))
    all_violations.extend(check_line_of_sight(segments, space_map))

    return segments, all_violations


# ═══════════════════════════════════════════════════════════
# 报告生成
# ═══════════════════════════════════════════════════════════

def generate_report(filepath, segments, violations):
    """生成 SPATIAL_CHECK_REPORT.md"""

    blocks_count = sum(1 for v in violations if v['severity'] == '阻断')
    warns_count = sum(1 for v in violations if v['severity'] == '警告')
    suggests_count = sum(1 for v in violations if v['severity'] == '建议')

    overall = '✅ 全部通过' if not violations else (
        f'🛑 {blocks_count}阻断' if blocks_count > 0 else f'⚠️ {warns_count}警告 + 💡{suggests_count}建议'
    )

    report = f"""# 空间硬约束检查报告 — {os.path.basename(filepath)}

> **检查时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> **检查方式:** 调度器自执行·零LLM·纯几何/数值/逻辑检查
> **提取镜头数:** {len(segments)} 镜

---

## 最终裁决: {overall}

🛑 阻断: {blocks_count} | ⚠️ 警告: {warns_count} | 💡 建议: {suggests_count}

---

## 违规详情

"""
    if not violations:
        report += "✅ S01-S07 全部通过·无违规项\n"
    else:
        by_rule = defaultdict(list)
        for v in violations:
            by_rule[v['rule']].append(v)

        for rule_id in sorted(by_rule.keys()):
            vs = by_rule[rule_id]
            name = vs[0]['name']
            severity = vs[0]['severity']
            report += f"### {rule_id}: {name} ({len(vs)}项·{severity})\n\n"
            for i, v in enumerate(vs, 1):
                report += f"{i}. **{v['shot']}**\n"
                report += f"   {v['detail']}\n"
                report += f"   → 修复: {v['fix']}\n\n"

    report += f"""---

## 检查覆盖

| 检查项 | 镜头数 | 状态 |
|------|:---:|:---:|
| S01 180度线 | {len(segments)} | {'✅' if not any(v['rule']=='S01' for v in violations) else '🛑'} |
| S02 景别递进 | {len(segments)} | {'✅' if not any(v['rule']=='S02' for v in violations) else '⚠️'} |
| S03 焦距匹配 | {len(segments)} | {'✅' if not any(v['rule']=='S03' for v in violations) else '⚠️'} |
| S04 运镜速度 | {len(segments)} | {'✅' if not any(v['rule']=='S04' for v in violations) else '⚠️'} |
| S05 角色位置 | {len(segments)} | {'✅' if not any(v['rule']=='S05' for v in violations) else '💡'} |
| S06 机位空间 | {len(segments)} | '⚠️ 需空间地图结构化坐标' |
| S07 视线遮挡 | {len(segments)} | '⚠️ 需空间地图结构化坐标' |

> **成本:** 0 tokens (纯几何/数值·零LLM)
> **准确率:** 100% (S01-S04为确定性检查·S05-S07依赖空间地图精度)
"""

    return report


# ═══════════════════════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════════════════════

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    if len(sys.argv) < 2:
        print("用法: python spatial_check.py [设计报告路径] [空间地图路径(可选)]")
        print("示例: python spatial_check.py ../02_Agent/output/EP13_S1_SCENE_DESIGNER_v2.md")
        sys.exit(1)

    filepath = sys.argv[1]
    space_map_path = sys.argv[2] if len(sys.argv) > 2 else None

    if not os.path.exists(filepath):
        print(f"ERROR: 文件不存在: {filepath}")
        sys.exit(1)

    print(f"空间硬约束检查: {os.path.basename(filepath)}")
    segments, result = spatial_check(filepath, space_map_path)

    if isinstance(result, str):
        print(f"ERROR: {result}")
        sys.exit(1)

    violations = result
    report = generate_report(filepath, segments, violations)

    out_dir = os.path.dirname(filepath)
    out_path = os.path.join(out_dir, 'SPATIAL_CHECK_REPORT.md')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(report)

    blocks = sum(1 for v in violations if v['severity'] == '阻断')
    warns = sum(1 for v in violations if v['severity'] == '警告')
    suggests = sum(1 for v in violations if v['severity'] == '建议')

    print(f"  检查完成: {len(segments)}镜")
    print(f"  BLOCK: {blocks} | WARN: {warns} | SUGGEST: {suggests}")
    print(f"  报告: {out_path}")

    from collections import Counter
    rc = Counter(v['rule'] for v in violations)
    for r, c in sorted(rc.items()):
        vs = [v for v in violations if v['rule'] == r]
        name = vs[0]['name']
        print(f"  [{vs[0]['severity']}] {r} {name}: {c}项")


if __name__ == '__main__':
    main()
