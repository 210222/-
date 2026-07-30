"""
Gate 0 确定性正则扫描器 v1.1 — MODE:P 管道前置检查
调度器自执行·零LLM·零Agent调用·纯正则+数值检查

用法: python gate0_scan.py [台本文件路径]
输出: GATE0_PRE_REPORT.md (保存到台本同目录)
"""
import re
import sys
import os
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════
# R01-R15 规则定义
# ═══════════════════════════════════════════════════════════════════

RULES = {
    "R01": {
        "name": "单段时长>15秒",
        "type": "numeric",
        "desc": "扫描每段时长标注·超过15秒→阻断",
        "severity": "🛑阻断"
    },
    "R02": {
        "name": "段首过程动词",
        "type": "regex",
        "desc": "扫描Action块中的过程动词(开始/正在/刚/持续)·这些词导致Seko渲染为已完成态",
        "severity": "🛑阻断",
        "pattern": r'(?:正在|刚(?!好)|已(?!经)|开始[^前]|持续[^时间]|一直[在以]|仍[在未])'
    },
    "R03": {
        "name": "时间模糊词",
        "type": "regex",
        "desc": "扫描Action块中的模糊时间词(缓缓/渐渐/慢慢)·用精确参数替代",
        "severity": "🛑阻断",
        "pattern": r'(?:缓缓|渐渐|慢慢|逐渐|徐徐|冉冉)'
    },
    "R04": {
        "name": "跨镜引用",
        "type": "regex",
        "desc": "扫描Action块中的跨镜引用(同上镜/参考上镜)·AI不知道上一镜",
        "severity": "🛑阻断",
        "pattern": r'(?:同上[一]?镜|参考上[一]?镜|如前所[述示]|同镜\s*[#＃]?(?:[A-Za-z]?\d+)|与镜\s*[#＃]?(?:[A-Za-z]?\d+)|参照[上前]镜|见[上前]镜)',
        "flags": re.IGNORECASE
    },
    "R05": {
        "name": "@参考图格式错误",
        "type": "pattern",
        "desc": "检查每个@图片N是否有'作为...'用途声明",
        "severity": "🛑阻断"
    },
    "R06": {
        "name": "禁止清单模糊词",
        "type": "regex",
        "desc": "扫描【禁止】块中的模糊词(稳/舒服/自然/美感)·必须精确到具体动作",
        "severity": "⚠️警告",
        "pattern": r'(?:稳(?!定)|舒服|自然(?!光|语言|过渡)|美感|漂亮)'
    },
    "R07": {
        "name": "工程符号泄漏",
        "type": "regex",
        "desc": "扫描台本中的工程符号(v_dolly/ω_pan/f/数字/°/s)·Seko不识别",
        "severity": "🛑阻断",
        "pattern": r'(?:v_dolly|ω_pan|ω_tilt|ω_roll|7-DOF|°\\/s)'
    },
    "R08": {
        "name": "镜号结构不完整",
        "type": "structure",
        "desc": "检查每镜是否含参数卡+生成指令+禁止·缺失任一→警告",
        "severity": "⚠️警告"
    },
    "R09": {
        "name": "负向词",
        "type": "regex",
        "desc": "扫描台本正文(排除【禁止】块)中的负向词·sd2.0将一切token当正向指令",
        "severity": "🛑阻断",
        "pattern": r'(?:不要|避免|禁止|不能|不应|勿[要]|别[再]|切勿|严禁|不许|不得)'
    },
    "R10": {
        "name": "外部模型名泄漏",
        "type": "regex",
        "desc": "扫描台本中的外部模型名·Seko是唯一渲染目标",
        "severity": "🛑阻断",
        "pattern": r'(?:即梦|海螺|Kling|Vidu|Seedance|可灵|万相|Runway|Pika|Sora|Luma|Dreamina|Hailuo)',
        "flags": re.IGNORECASE
    },
    "R11": {
        "name": "@声明缺少用途",
        "type": "pattern",
        "desc": "检查@图片N声明后是否有'作为'+用途描述",
        "severity": "⚠️警告"
    },
    "R12": {
        "name": "KB规则ID泄漏",
        "type": "regex",
        "desc": "扫描台本正文中的KB规则ID·这些是设计依据·不进Seko提示词",
        "severity": "⚠️警告",
        "pattern": r'(?:D-TRI-|M-MOT-|M-MOV-|C-COM-|C-KTZ-|C-FI-|C-AJS-|C-DEP-|L-3PT-|L-SRC-|E-MTC-|S-SHT-|GEN-|VS-LS-|P-REN-|P-FAL-)\\d*'
    },
    "R13": {
        "name": "骨架顺序错乱",
        "type": "order",
        "desc": "检查台本五段式顺序: Subject→Action→Camera→Style→Constraints",
        "severity": "⚠️警告"
    },
    "R14": {
        "name": "画面描述混入运镜语义",
        "type": "regex",
        "desc": "扫描Action块中的运镜语义·运镜参数应只在Camera段",
        "severity": "⚠️警告",
        "pattern": r'(?:推近(?:继续|落定|至|到|过程|中)|拉远(?:继续|至|到|过程|中)|横移(?:继续|至|到)|摇[镜摄](?:过|至|到)?|跟[拍摄随](?:着|至|到)?|镜头(?:缓[缓慢]|快[速]|慢[慢速]|匀[速])(?:推|拉|摇|移|跟))',
        "flags": re.IGNORECASE
    },
    "R15": {
        "name": "画面外声音源",
        "type": "regex",
        "desc": "扫描台本中的画面外声音描述·画面外声音→音轨",
        "severity": "⚠️警告",
        "pattern": r'(?:画框外|镜头外|屏幕外|画面外)(?:传来|响[起]|飘[来进]|涌入|听到)'
    }
}


# ═══════════════════════════════════════════════════════════════════
# 区块解析
# ═══════════════════════════════════════════════════════════════════

def parse_blocks(filepath):
    """将台本文件按标记头分段·支持两种格式"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        return None, "文件不存在"
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='gbk') as f:
                content = f.read()
        except Exception as e:
            return None, f"无法读取文件: {e}"

    lines = content.split('\n')

    # 区块标记 — 扩展支持Scene Designer嵌入式格式+标准prompt_composer格式
    BLOCK_MARKERS = [
        # 元数据区 (不扫描)
        (r'^# .*设计报告|^# .*Scene Designer|^# .*导演台本', 'HEADER'),
        (r'^>.*', 'META_COMMENT'),
        # 设计元数据 (不扫描)
        (r'^## §[0-9]|^## YAML|^```yaml|^```$|^segments_camera:|^global_anchors:|^frames_hard:|^frames_soft:|^frames_movement:|^segments_movement:', 'DESIGN_META'),
        (r'^### §[0-9]', 'DESIGN_META'),
        # 场景级共享锚点 (不扫描)
        (r'^##[^#]*【场景级共享锚点】|^##\s*C\d|^场景级共享锚点', 'DECLARATION'),
        # 镜头参数卡 (REFERENCES块)
        (r'^【镜头参数卡】|^###\s*【镜头参数卡】', 'PARAM_CARD'),
        (r'^【传入参考图】|^###\s*【传入参考图】', 'REFERENCE'),
        # 图例/线稿声明 (REFERENCES块)
        (r'^使用.*仅作为|^线稿箭头标注|^图例说明', 'REFERENCE'),
        # @声明 (REFERENCES块·不扫描)
        (r'^@图片\d|^@音频\d', 'REFERENCE'),
        # 骨架五段式
        (r'^Subject:', 'DECLARATION'),
        (r'^Action:', 'ACTION_START'),
        (r'^Camera:', 'CAMERA_BLOCK'),
        (r'^Style:', 'STYLE_BLOCK'),
        (r'^Constraints:', 'CONSTRAINT_BLOCK'),
        # 生成指令
        (r'^###\s*【生成指令】', 'ACTION'),
        (r'^\d+秒:', 'ACTION'),  # 逐秒描述 (如 "0秒: ...")
        (r'^\d+-\d+秒:', 'ACTION'),  # 时间范围 (如 "0-4秒: ...")
        # 音轨
        (r'^###\s*(?:音轨|【音轨】)', 'AUDIO'),
        (r'^音轨:', 'AUDIO'),
        # 转场
        (r'^###\s*【段末转场设计】', 'TRANSITION'),
        (r'^段末转场设计:', 'TRANSITION'),
        # 禁止清单
        (r'^###\s*【禁止】|^【禁止】', 'PROHIBIT'),
        (r'^禁止:', 'PROHIBIT'),
        # 时序描述
        (r'^时序描述', 'TIMING'),
        # CV/VO (AUDIO块)
        (r'^CV:|^VO:|^SFX:', 'AUDIO'),
        # 故事板对照
        (r'^故事板对照', 'REFERENCE'),
        # 设计依据 (不扫描)
        (r'^###\s*【设计依据】|^【设计依据】', 'DESIGN_NOTES'),
        # Shot标记 (镜级)
        (r'^###\s*SHOT-|^##\s*SHOT-', 'SHOT_HEADER'),
        # 收尾
        (r'^##\s*━|^---$|^> \*\*v\d', 'CLOSING'),
    ]

    # 收集标记
    marker_hits = []
    for i, line in enumerate(lines):
        for pattern, block_type in BLOCK_MARKERS:
            if re.match(pattern, line):
                marker_hits.append((i, block_type, line.strip()[:80]))
                break

    if not marker_hits:
        # 没有任何识别标记 → 整个文件可能纯文本·谨慎处理为单ACTION块
        return [("ACTION", 1, len(lines), content)], None

    # 构建区块
    blocks = []
    for idx, (line_no, block_type, header) in enumerate(marker_hits):
        start = line_no
        end = marker_hits[idx + 1][0] if idx + 1 < len(marker_hits) else len(lines)
        block_text = '\n'.join(lines[start:end])
        blocks.append((block_type, start + 1, end, block_text))

    return blocks, None


# ═══════════════════════════════════════════════════════════════════
# 检查函数
# ═══════════════════════════════════════════════════════════════════

# 需要扫描的区块 (只有这些区块包含Seko提示词正文)
SCAN_BLOCKS = {'ACTION', 'ACTION_START', 'AUDIO', 'PROHIBIT', 'TRANSITION', 'TIMING'}
SKIP_BLOCKS = {'HEADER', 'META_COMMENT', 'DESIGN_META', 'DECLARATION', 'PARAM_CARD',
               'REFERENCE', 'CAMERA_BLOCK', 'STYLE_BLOCK', 'CONSTRAINT_BLOCK',
               'DESIGN_NOTES', 'SHOT_HEADER', 'CLOSING'}

def check_duration(blocks):
    """R01: 检查单段时长·只扫描ACTION/TRANSITION块"""
    violations = []
    for block_type, start, end, text in blocks:
        if block_type not in ('ACTION', 'ACTION_START', 'TRANSITION'):
            continue
        durations = re.findall(r'(\d+)\s*秒', text)
        for d in durations:
            if int(d) > 15:
                violations.append({
                    'rule': 'R01',
                    'severity': '🛑阻断',
                    'block': block_type,
                    'line': start,
                    'match': f'{d}秒',
                    'fix': f'单段时长{int(d)}秒>15秒·需拆分'
                })
    return violations


def check_regex(blocks, rule_id):
    """通用正则检查 · 只扫描ACTION/AUDIO/PROHIBIT/TRANSITION块"""
    rule = RULES[rule_id]
    flags = rule.get('flags', 0)
    pattern = re.compile(rule['pattern'], flags)

    violations = []
    for block_type, start, end, text in blocks:
        # 跳过非扫描区块
        if block_type in SKIP_BLOCKS:
            continue
        # R09跳过PROHIBIT块(禁止块本身可以写"不要")
        if rule_id == 'R09' and block_type == 'PROHIBIT':
            continue
        # R06只在PROHIBIT块检查
        if rule_id == 'R06' and block_type != 'PROHIBIT':
            continue
        # R14跳过AUDIO/PROHIBIT/TRANSITION
        if rule_id == 'R14' and block_type in ('AUDIO', 'PROHIBIT', 'TRANSITION'):
            continue
        # R01只在ACTION块
        if rule_id == 'R01' and block_type not in ('ACTION', 'ACTION_START', 'TRANSITION'):
            continue

        for match in pattern.finditer(text):
            line_no = start + text[:match.start()].count('\n')
            violations.append({
                'rule': rule_id,
                'severity': rule['severity'],
                'block': block_type,
                'line': line_no + 1,
                'match': match.group()[:80],
                'fix': f'修改或删除 "{match.group()[:40]}"'
            })

    return violations


def check_ref_format(blocks, rule_id):
    """R05/R11: 检查@参考图格式"""
    violations = []
    for block_type, start, end, text in blocks:
        at_lines = re.findall(r'@图片\d+.*', text)
        for line in at_lines:
            if rule_id == 'R05' and '作为' not in line:
                violations.append({
                    'rule': 'R05',
                    'severity': '🛑阻断',
                    'block': block_type,
                    'line': start,
                    'match': line.strip()[:80],
                    'fix': f'添加用途声明: {line.strip()} 作为...'
                })
            if rule_id == 'R11' and '@' in line and '作为' not in line:
                violations.append({
                    'rule': 'R11',
                    'severity': '⚠️警告',
                    'block': block_type,
                    'line': start,
                    'match': line.strip()[:80],
                    'fix': f'添加用途描述'
                })
    return violations


def check_structure(blocks):
    """R08: 检查镜号结构完整性"""
    violations = []
    action_blocks = [b for b in blocks if b[0] == 'ACTION']
    for block_type, start, end, text in action_blocks:
        has_param = '【镜头参数卡】' in text or '参数卡' in text
        has_instruct = '【生成指令】' in text or '0-' in text or '秒:' in text
        has_prohibit = '【禁止】' in text or '禁止:' in text
        missing = []
        if not has_param: missing.append('镜头参数卡')
        if not has_instruct: missing.append('生成指令')
        if not has_prohibit: missing.append('禁止清单')
        if missing:
            violations.append({
                'rule': 'R08',
                'severity': '⚠️警告',
                'block': block_type,
                'line': start,
                'match': f'缺失: {", ".join(missing)}',
                'fix': f'补充缺失的结构块: {", ".join(missing)}'
            })
    return violations


def check_skeleton_order(blocks):
    """R13: 检查五段式顺序"""
    violations = []
    for block_type, start, end, text in blocks:
        if block_type != 'ACTION':
            continue
        order = []
        for marker in ['Subject:', 'Action:', 'Camera:', 'Style:', 'Constraints:']:
            for line in text.split('\n'):
                if line.strip().startswith(marker):
                    order.append(marker.replace(':', ''))
                    break

        expected = ['Subject', 'Action', 'Camera', 'Style', 'Constraints']
        if order and order != expected:
            violations.append({
                'rule': 'R13',
                'severity': '⚠️警告',
                'block': block_type,
                'line': start,
                'match': f'实际顺序: {"→".join(order)}',
                'fix': f'修正为: Subject→Action→Camera→Style→Constraints'
            })
    return violations


# ═══════════════════════════════════════════════════════════════════
# 主扫描函数
# ═══════════════════════════════════════════════════════════════════

def gate0_scan(filepath):
    """执行完整的 Gate 0 扫描"""
    blocks, error = parse_blocks(filepath)

    if error:
        print(f"ERROR: 无法读取文件: {error}")
        return None, error

    if not blocks:
        return None, "文件为空"

    all_violations = []

    # R01: 时长检查
    all_violations.extend(check_duration(blocks))

    # R02-R04, R06-R07, R09-R10, R12, R14-R15: 正则检查
    regex_rules = ['R02', 'R03', 'R04', 'R06', 'R07', 'R09', 'R10', 'R12', 'R14', 'R15']
    for rule_id in regex_rules:
        all_violations.extend(check_regex(blocks, rule_id))

    # R05, R11: 参考图格式
    all_violations.extend(check_ref_format(blocks, 'R05'))
    all_violations.extend(check_ref_format(blocks, 'R11'))

    # R08: 结构完整性
    all_violations.extend(check_structure(blocks))

    # R13: 骨架顺序
    all_violations.extend(check_skeleton_order(blocks))

    return blocks, all_violations


# ═══════════════════════════════════════════════════════════════════
# 报告生成
# ═══════════════════════════════════════════════════════════════════

def generate_report(filepath, blocks, violations):
    """生成 GATE0_PRE_REPORT.md"""

    blocks_count = {t: 0 for t in set(b[0] for b in blocks)}
    for b in blocks:
        blocks_count[b[0]] += 1

    block_list = '\n'.join([f'  - {t}: {c} 个区块' for t, c in blocks_count.items()])

    violations_by_rule = {}
    for v in violations:
        rule = v['rule']
        if rule not in violations_by_rule:
            violations_by_rule[rule] = []
        violations_by_rule[rule].append(v)

    blocks_total = sum(1 for v in violations if v['severity'] == '🛑阻断')
    warns_total = sum(1 for v in violations if v['severity'] == '⚠️警告')

    overall = '✅ 全部通过' if not violations else (
        f'🛑 {blocks_total}项阻断' if blocks_total > 0 else f'⚠️ {warns_total}项警告'
    )

    report = f"""# Gate 0 前置扫描报告 — {os.path.basename(filepath)}

> **扫描时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> **扫描方式:** 调度器自执行·零LLM·零Agent调用·纯正则/数值/格式检查
> **扫描文件:** {filepath}

---

## 区块解析结果

{block_list}

---

## 最终裁决: {overall}

🛑 阻断: {blocks_total} 项 | ⚠️ 警告: {warns_total} 项

---

## 违规详情

"""

    if not violations:
        report += "✅ R01-R15 全部通过·无违规项\n"
    else:
        for rule_id in sorted(violations_by_rule.keys()):
            rule = RULES.get(rule_id, {})
            vs = violations_by_rule[rule_id]
            report += f"### {rule_id}: {rule.get('name', '未知')} ({len(vs)}项)\n\n"
            report += f"**说明:** {rule.get('desc', '')}\n"
            report += f"**严重度:** {rule.get('severity', '⚠️警告')}\n\n"
            for i, v in enumerate(vs, 1):
                report += f"{i}. **行{v['line']}** [{v['block']}]\n"
                report += f"   匹配: `{v['match']}`\n"
                report += f"   修复: {v['fix']}\n\n"

    report += """---

## 后续流程

"""
    if blocks_total > 0:
        report += f"""**🛑 Gate 0 未通过** — 返回设计Agent修复(上限1轮)
修复后调度器重新运行本扫描。
如第2轮仍有🛑 → 管道终止·输出阻断报告
"""
    else:
        report += """**✅ Gate 0 通过** — 进入 Scene Auditor 审计
Scene Auditor Phase 0 跳过(已由本扫描完成)
Scene Auditor 从 Phase 1 开始执行
"""

    report += """
> **成本:** 0 tokens (纯正则·零LLM·调度器主会话执行)
> **准确率:** 100% (正则匹配不依赖概率)
"""

    return report


# ═══════════════════════════════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════════════════════════════

def main():
    # 修复 Windows 控制台 GBK 编码问题
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    if len(sys.argv) < 2:
        print("用法: python gate0_scan.py [台本文件路径]")
        print("示例: python gate0_scan.py ../02_Agent/output/EP15_S1_导演台本.md")
        sys.exit(1)

    filepath = sys.argv[1]

    if not os.path.exists(filepath):
        print(f"ERROR: 文件不存在: {filepath}")
        sys.exit(1)

    print(f"Gate 0 扫描: {os.path.basename(filepath)}")
    print(f"   R01-R15 正则扫描中...")

    blocks, result = gate0_scan(filepath)

    if isinstance(result, str):
        print(f"ERROR: 扫描失败: {result}")
        sys.exit(1)

    violations = result
    report = generate_report(filepath, blocks, violations)

    # 保存报告
    out_dir = os.path.dirname(filepath)
    out_path = os.path.join(out_dir, 'GATE0_PRE_REPORT.md')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(report)

    blocks_count = sum(1 for v in violations if v['severity'] == '🛑阻断')
    warns_count = sum(1 for v in violations if v['severity'] == '⚠️警告')

    print(f"   扫描完成")
    print(f"   BLOCK: {blocks_count} | WARN: {warns_count}")
    print(f"   报告: {out_path}")

    # 按规则汇总
    if violations:
        print(f"\n   违规明细:")
        from collections import Counter
        rule_counts = Counter(v['rule'] for v in violations)
        for rule_id, count in sorted(rule_counts.items()):
            severity = RULES.get(rule_id, {}).get('severity', '?')
            name = RULES.get(rule_id, {}).get('name', '?')
            print(f"     [{severity}] {rule_id} {name}: {count}项")


if __name__ == '__main__':
    main()
