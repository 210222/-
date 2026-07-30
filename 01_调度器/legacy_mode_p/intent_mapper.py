"""
意图→参数自动映射器 v1.0
输入: 意图卡 (视觉策略+情绪微调)
输出: 预填的 segments_camera 参数
"""
import json
import re
import sys
import os

STRATEGIES_FILE = os.path.join(os.path.dirname(__file__), '..', '04_共享', 'intent_strategies.json')

def load_strategies():
    with open(STRATEGIES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def map_intent_to_params(intent_card, strategies):
    """将单张意图卡映射为技术参数"""
    visual_strategy = intent_card.get('visual_strategy', '')
    emotion_note = intent_card.get('emotion_note', '')
    narrative_function = intent_card.get('narrative_function', '')

    original_key = None  # 保存原始组级策略·用于子策略回退判断

    # 从视觉策略中提取核心策略标签
    # 处理: [标签] · [标签]+[标签] · [标签·变体] · [标签]主导+内部子策略
    strategy_key = None
    strategy_keys = re.findall(r'\[([^\]]+)\]', visual_strategy)

    # 取第一个不含"主导""变体""内部"修饰词的纯标签
    for key_candidate in strategy_keys:
        # 剥离变体后缀 (·后面的部分)
        base_key = key_candidate.split('·')[0].split('：')[0].strip()
        # 跳过"主导""内部子策略"等非策略词
        if base_key in ['主导','内部子策略递进','内部子策略']:
            continue
        if base_key in strategies.get('strategies', {}):
            strategy_key = base_key
            break

    # 回退: 取第一个匹配的策略标签
    if not strategy_key and strategy_keys:
        for key_candidate in strategy_keys:
            base_key = key_candidate.split('·')[0].split('：')[0].strip()
            if base_key in strategies.get('strategies', {}):
                strategy_key = base_key
                break

    # 子策略覆盖: key_differences中按镜号匹配更精确的策略标签
    emotion_note = intent_card.get('emotion_note', '')
    shot_label = intent_card.get('shot_label', '')
    if emotion_note and shot_label:
        # 提取镜号 (如 "镜#12" 从 "镜#12.5" 可能模糊匹配)
        shot_num = re.search(r'(\d+\.?\d*)', str(shot_label))
        target_num = shot_num.group(1) if shot_num else ''
        # 在key_differences中找 "镜#12.5([策略标签]" 或 "镜#12([策略标签]"
        per_shot_pattern = re.findall(
            r'镜#\s*' + re.escape(target_num) + r'\s*[\(（]\s*\[([^\]]+)\]',
            emotion_note
        )
        if per_shot_pattern:
            for sub_key in per_shot_pattern:
                base_sub = sub_key.split('·')[0].split('：')[0].strip()
                if base_sub in strategies.get('strategies', {}):
                    strategy_key = base_sub
                    break
        # 回退: 无镜号匹配时·取第一个子策略标签
        if strategy_key == original_key and not per_shot_pattern:
            sub_strategy_keys = re.findall(r'\[([^\]]+)\]', emotion_note)
            for sub_key in sub_strategy_keys:
                base_sub = sub_key.split('·')[0].split('：')[0].strip()
                if base_sub in strategies.get('strategies', {}) and base_sub != strategy_key:
                    strategy_key = base_sub
                    break

    result = {
        'intent': intent_card,
        'confidence': 'LOW',
        'llm_required': False
    }

    original_key = strategy_key

    if strategy_key and strategy_key in strategies.get('strategies', {}):
        strat = strategies['strategies'][strategy_key]
        defaults = strat.get('default_params', {})
        llm_required = strat.get('llm_required', False)

        result['shot_type'] = defaults.get('shot_type', '')
        result['focal_length'] = defaults.get('focal_length', '')
        result['dof'] = defaults.get('dof', '')
        result['movement'] = defaults.get('movement', '')
        result['angle'] = defaults.get('angle', '')
        result['lighting'] = defaults.get('lighting', '')
        result['source'] = f'意图策略: [{strategy_key}]'
        result['llm_required'] = llm_required

        mapping_rules = strategies.get('mapping_rules', {})
        if strategy_key in mapping_rules.get('high_confidence', []):
            result['confidence'] = 'HIGH'
        elif strategy_key in mapping_rules.get('llm_override_allowed', []):
            result['confidence'] = 'MEDIUM'
            result['llm_note'] = 'LLM可覆盖默认参数'
        elif strategy_key in mapping_rules.get('llm_required', []):
            result['confidence'] = 'LOW'
            result['llm_note'] = strat.get('llm_reason', '需LLM设计')
    else:
        # 无匹配策略 → 从叙事功能尝试推导
        func_defaults = {
            '建立':  {'shot_type': '全景', 'focal_length': '24mm', 'movement': '固定'},
            '推进':  {'shot_type': '中景', 'focal_length': '35mm', 'movement': '固定或推近'},
            '转折':  {'shot_type': '近景', 'focal_length': '50mm', 'movement': '推近'},
            '揭示':  {'shot_type': '特写', 'focal_length': '85mm', 'movement': '固定'},
            '反应':  {'shot_type': '近景', 'focal_length': '50mm', 'movement': '固定'},
            '收尾':  {'shot_type': '全景', 'focal_length': '24mm', 'movement': '固定'},
        }
        for func, defaults in func_defaults.items():
            if func in narrative_function:
                result['shot_type'] = defaults['shot_type']
                result['focal_length'] = defaults['focal_length']
                result['movement'] = defaults['movement']
                result['source'] = f'叙事功能推导: {func}'
                result['confidence'] = 'MEDIUM'
                result['llm_required'] = True
                result['llm_note'] = '无策略匹配·需LLM确认'
                break

    # 环境光照覆盖 (夜景/弱光策略的特殊逻辑)
    env_overrides = strategies.get('mapping_rules', {}).get('environmental_overrides', {})
    for env_strategy, env_config in env_overrides.items():
        if strategy_key in env_config.get('overrides', []):
            rule = env_config.get('rule', '')
            result['env_override'] = f'{env_strategy}: {rule}'

    # 情绪微调影响
    result['emotion_note'] = emotion_note
    if emotion_note:
        if '压迫' in emotion_note or '收紧' in emotion_note:
            result['emotion_hint'] = '焦距可能偏长·景别可能偏紧'
        elif '释放' in emotion_note or '拉开' in emotion_note:
            result['emotion_hint'] = '焦距可能偏短·景别可能偏宽'
        elif '静止' in emotion_note or '凝视' in emotion_note:
            result['emotion_hint'] = '运镜可能静止或极慢'

    return result


def map_all(intent_cards, strategies=None):
    """批量映射·返回预填结果 + 需要LLM的镜号列表"""
    if strategies is None:
        strategies = load_strategies()

    results = []
    llm_shots = []

    for card in intent_cards:
        mapped = map_intent_to_params(card, strategies)
        results.append(mapped)
        if mapped.get('llm_required'):
            llm_shots.append(card.get('shot_id', '?'))

    # 反馈学习: 检查是否有上次LLM设计结果可回写
    feedback_file = os.path.join(os.path.dirname(__file__), '..', '02_Agent', 'output', 'FEEDBACK_LOG.json')
    feedback_data = {}
    if os.path.exists(feedback_file):
        try:
            with open(feedback_file, 'r', encoding='utf-8') as f:
                feedback_data = json.load(f)
        except Exception:
            pass

    # 对每个LOW镜·检查是否有历史LLM成功设计
    for r in results:
        if r.get('llm_required') and r.get('confidence') == 'LOW':
            shot_id = r.get('intent', {}).get('shot_id', '')
            strategy = r.get('source', '')
            # 查找反馈中同策略+同功能的成功案例
            for fb in feedback_data.get('successful_designs', []):
                intent_narrative = r.get('intent', {}).get('narrative_function', '')
                fb_narrative = fb.get('narrative_function', '')
                # 宽松匹配: 反馈中的叙事功能是意图功能的子串 或 匹配叙事功能的首段(第一个·或/之前)
                narrative_match = (fb_narrative in intent_narrative or
                                  intent_narrative.split('·')[0].split('：')[0] == fb_narrative)
                if (fb.get('strategy') in strategy and narrative_match):
                    # 找到匹配 → 置信度升为MEDIUM·使用反馈中的实际参数
                    r['confidence'] = 'MEDIUM'
                    r['feedback_match'] = fb.get('ep', '')
                    r['llm_required'] = False
                    r['shot_type'] = fb.get('shot_type', r.get('shot_type', ''))
                    r['focal_length'] = fb.get('focal_length', r.get('focal_length', ''))
                    r['movement'] = fb.get('movement', r.get('movement', ''))
                    r['source'] = f'反馈学习: {fb.get("ep","")}'
                    break

    medium_from_feedback = sum(1 for r in results if r.get('feedback_match'))

    return {
        'total': len(results),
        'high_confidence': sum(1 for r in results if r.get('confidence') == 'HIGH'),
        'medium_confidence': sum(1 for r in results if r.get('confidence') == 'MEDIUM'),
        'low_confidence': sum(1 for r in results if r.get('confidence') == 'LOW'),
        'medium_from_feedback': medium_from_feedback,
        'llm_required_shots': [r.get('intent', {}).get('shot_id', '?') for r in results if r.get('llm_required')],
        'llm_required_count': sum(1 for r in results if r.get('llm_required')),
        'shots': results
    }


def flatten_groups(data):
    """将意图组JSON展开为单镜列表"""
    shots = []
    groups = data.get('intent_groups', [])

    for g in groups:
        group_strategy = g.get('visual_strategy', '')
        group_name = g.get('group_name', '')
        narrative = g.get('narrative_function', '')
        psychology = g.get('character_psychology', '')
        audience = g.get('audience_feeling', '')
        rhythm = g.get('rhythm_position', '')
        differences = g.get('key_differences', '')
        shot_ids = g.get('shots', [])

        for sid in shot_ids:
            # 提取镜号
            import re
            m = re.search(r'(\d+\.?\d*)', str(sid))
            shot_num = m.group(1) if m else sid

            shots.append({
                'shot_id': shot_num,
                'shot_label': str(sid),
                'group_name': group_name,
                'visual_strategy': group_strategy,
                'narrative_function': narrative,
                'character_psychology': psychology,
                'audience_feeling': audience,
                'rhythm_position': rhythm,
                'emotion_note': differences,
                'group_strategy': group_strategy
            })

    return shots


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    if len(sys.argv) < 2:
        print("用法: python intent_mapper.py [意图卡JSON文件]")
        sys.exit(1)

    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        intent_cards = json.load(f)

    strategies = load_strategies()

    # 支持两种格式: 意图组(含intent_groups) 或 单镜列表
    if isinstance(intent_cards, dict) and 'intent_groups' in intent_cards:
        shots = flatten_groups(intent_cards)
    elif isinstance(intent_cards, list):
        shots = intent_cards
    else:
        shots = intent_cards.get('shots', [])

    result = map_all(shots, strategies)

    print(f"\n## 意图→参数映射结果")
    print(f"总镜数: {result['total']}")
    print(f"HIGH (直接映射):     {result['high_confidence']}镜")
    print(f"MEDIUM (LLM可覆盖):  {result['medium_confidence']}镜")
    print(f"LOW (需LLM设计):     {result['low_confidence']}镜")
    print(f"LLM工作量: {result['llm_required_count']}/{result['total']}镜")

    print(f"\n## 逐镜参数")
    for s in result['shots']:
        intent = s.get('intent', {})
        icon = {'HIGH':'✅','MEDIUM':'⚠️','LOW':'🧠'}.get(s['confidence'],'?')
        print(f"\n{icon} 镜#{intent.get('shot_id','?')} [{s['confidence']}]")
        print(f"  意图: {intent.get('narrative_function','')[:60]}")
        print(f"  策略: {s.get('source','?')}")
        print(f"  参数: {s.get('shot_type','?')} · {s.get('focal_length','?')} · {s.get('movement','?')} · {s.get('angle','?')}")
        if s.get('llm_required'):
            print(f"  ⚠️ 需LLM: {s.get('llm_note','')}")
        if s.get('emotion_hint'):
            print(f"  💡 情绪微调: {s.get('emotion_hint','')}")


if __name__ == '__main__':
    main()
