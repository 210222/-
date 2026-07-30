"""
DSPy式 Agent Prompt 优化器 v1.0 — Layer 3 优化
设计依据: Omar Khattab DSPy + Karpathy AutoResearch 循环模式

输入: 训练数据 (脚本→审核通过输出) + Agent签名 (输入输出格式)
输出: 优化后的 prompt 模板 (替代手写Agent指令)

用法: python prompt_optimizer.py [agent_name] --generate (生成候选)
       python prompt_optimizer.py [agent_name] --evaluate (评估候选)
       python prompt_optimizer.py [agent_name] --optimize (完整优化循环)
"""
import json
import sys
import os
import re
from datetime import datetime
from collections import defaultdict

TRAINING_DIR = os.path.join(os.path.dirname(__file__), '..', '06_测试', 'training_data')
AGENT_DIR = os.path.join(os.path.dirname(__file__), '..', '02_Agent')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', '02_Agent', 'output')

# ═══════════════════════════════════════════════════════════
# 训练数据格式
# ═══════════════════════════════════════════════════════════

"""
training_data/
├── scene_designer/
│   ├── ep13_鉴证科.json   # 输入: 增强剧本摘要 + 约束 · 输出: 审核通过的YAML字段
│   ├── ep14_案情室.json
│   └── ep15_Rico工作室.json
├── shot_architect/
├── movement_designer/
└── ...
"""


def extract_training_data(ep_name, scene_name, script_file, output_file, agent_type="scene_designer"):
    """从EP输出中提取训练数据对"""
    agent_dir = os.path.join(TRAINING_DIR, agent_type)
    os.makedirs(agent_dir, exist_ok=True)

    # 读取脚本(输入)
    script_input = ""
    if os.path.exists(script_file):
        with open(script_file, 'r', encoding='utf-8') as f:
            content = f.read()
        # 提取场景描述·角色信息·空间信息
        scene_match = re.search(r'##\s*第\d+幕[：:]\s*(.+?)(?:\n|$)', content)
        script_input = {
            'scene_name': scene_match.group(1).strip() if scene_match else scene_name,
            'script_file': os.path.basename(script_file),
            'script_excerpt': content[:2000]  # 前2000字符
        }

    # 读取输出(期望答案)
    expected_output = {}
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取YAML中的关键字段
        yaml_match = re.search(r'segments_camera:\n((?:\s+-.*\n(?:\s+.*\n)*)+)', content)
        if yaml_match:
            expected_output['segments_camera_count'] = len(re.findall(r'\s+- segment_id:', yaml_match.group(1)))

        # 提取global_anchors
        anchor_match = re.search(r'global_anchors:.*?(?=\n\S|\Z)', content, re.DOTALL)
        if anchor_match:
            expected_output['has_global_anchors'] = True

        # 统计shot_type分布
        shot_types = re.findall(r'shot_type:\s*"([^"]*)"', content)
        expected_output['shot_type_distribution'] = {t: shot_types.count(t) for t in set(shot_types)}
        expected_output['total_shots'] = len(shot_types)

        # 检查axis_side一致性
        axis_sides = re.findall(r'axis_side:\s*"([^"]*)"', content)
        expected_output['axis_side_consistent'] = len(set(axis_sides)) <= 1
        expected_output['axis_side_values'] = list(set(axis_sides))

    training_pair = {
        'ep': ep_name,
        'scene': scene_name,
        'agent_type': agent_type,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'input': script_input,
        'expected_output': expected_output
    }

    out_path = os.path.join(agent_dir, f'{ep_name}_{scene_name}.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(training_pair, f, ensure_ascii=False, indent=2)

    return out_path


def generate_prompt_candidates(agent_type):
    """为一个Agent类型生成多个prompt候选版本"""

    candidates = []

    if agent_type == "scene_designer":
        # 候选A: 当前版本 (v7.0·约束菜单+历史模式)
        candidates.append({
            'id': 'candidate_A_current',
            'name': 'v7.0 约束菜单 + 历史模式 (当前版本)',
            'approach': '约束菜单 + Step -1历史检索 + Step 0场景判定 + 三域设计',
            'estimated_tokens_per_call': 23000,
            'key_features': ['约束菜单替代KB全文', '历史模式继承', 'P-FAL清单', '结构化YAML输出']
        })

        # 候选B: 极简版 (只给约束·不给参考·减少上下文)
        candidates.append({
            'id': 'candidate_B_minimal',
            'name': '极简版 · 纯约束驱动',
            'approach': '只给约束菜单 + 剧本·不加载历史模式·不加载CONTEXT_PACKAGE详细',
            'estimated_tokens_per_call': 15000,
            'key_features': ['最短上下文', 'Agent不被历史案例影响', '可能丢失已验证方案']
        })

        # 候选C: 详细版 (加更多KB引用和设计论证)
        candidates.append({
            'id': 'candidate_C_detailed',
            'name': '详细版 · 完整KB支撑',
            'approach': '约束菜单 + 历史模式 + 关键KB规则全文(非全部866条·仅激活的17条)',
            'estimated_tokens_per_call': 35000,
            'key_features': ['规则全文支撑决策', '减少Agent猜测', '上下文较重']
        })

        # 候选D: 对比版 (先看历史方案·自己纠偏)
        candidates.append({
            'id': 'candidate_D_contrastive',
            'name': '对比版 · 历史方案+自我纠偏',
            'approach': '加载历史模式→Agent先判断历史方案是否适用→适用的继承·不适用的标注原因→从头设计',
            'estimated_tokens_per_call': 28000,
            'key_features': ['强制纠偏步骤', '避免盲目继承', '需要更多推理']
        })

    elif agent_type == "shot_architect":
        candidates = [
            {
                'id': 'candidate_A_current',
                'name': 'v7.0 约束纯机位',
                'approach': '约束菜单(仅机位域) + 空间地图 + 纯机位输出·不含运镜和构图',
                'estimated_tokens_per_call': 18000
            }
        ]

    return candidates


def define_metrics():
    """定义评估指标体系"""
    return {
        'structural_completeness': {
            'weight': 0.25,
            'description': '输出是否包含所有必填YAML字段',
            'check': 'segments_camera存在·global_anchors存在·axis_side标注·kb_rule_ids标注'
        },
        'constraint_compliance': {
            'weight': 0.25,
            'description': '输出是否通过Layer 0硬约束检查',
            'check': 'spatial_check.py 阻断数=0·gate0_scan.py 阻断数(台本级)=0'
        },
        'design_quality': {
            'weight': 0.30,
            'description': '设计是否与审核通过的参考方案接近',
            'check': 'shot_type分布与参考方案的相关性·机位类型是否匹配场景类型'
        },
        'token_efficiency': {
            'weight': 0.10,
            'description': 'Agent输入token数',
            'check': '目标: ≤25000 tokens'
        },
        'kb_rule_coverage': {
            'weight': 0.10,
            'description': 'KB规则ID引用覆盖率',
            'check': '参考方案中有多少KB规则在候选方案的输出中被引用'
        }
    }


def evaluate_candidate(candidate, training_data, metrics):
    """评估一个prompt候选"""
    scores = {}

    # 这里在实际运行时会:
    # 1. 用候选prompt调用Agent
    # 2. 跑spatial_check + gate0_scan
    # 3. 对比训练数据的expected_output
    # 4. 计算各项指标分数

    # 目前用训练数据的结构完整性做初步评估
    for ep_data in training_data:
        expected = ep_data.get('expected_output', {})

        # 结构完整性
        if expected.get('segments_camera_count', 0) > 0:
            scores['structural_completeness'] = 0.8  # 有YAML输出
        else:
            scores['structural_completeness'] = 0.2

        # 180度线一致性
        if expected.get('axis_side_consistent', False):
            scores['constraint_compliance'] = 0.9
        else:
            scores['constraint_compliance'] = 0.4

        # Token效率 (基于候选的预估)
        target = 25000
        estimated = candidate.get('estimated_tokens_per_call', 30000)
        scores['token_efficiency'] = max(0, min(1, target / estimated))

        # KB覆盖 (shot_type分布是否含标准术语)
        shot_dist = expected.get('shot_type_distribution', {})
        valid_terms = ['全景','中全景','中景','中近景','近景','特写','大特写','极特写']
        valid_count = sum(1 for t in shot_dist if any(v in t for v in valid_terms))
        total = max(len(shot_dist), 1)
        scores['kb_rule_coverage'] = valid_count / total

        # 设计质量 (shot_type多样性)
        total_shots = expected.get('total_shots', 1)
        unique_types = len(shot_dist)
        ideal_min = max(1, min(3, total_shots))
        scores['design_quality'] = min(1, unique_types / ideal_min)

    # 加权总分
    total = sum(scores.get(m, 0) * metrics[m]['weight'] for m in metrics)
    return total, scores


def optimize_loop(agent_type, max_rounds=3):
    """完整优化循环 (Karpathy式·保留最优)"""

    candidates = generate_prompt_candidates(agent_type)
    metrics = define_metrics()

    # 加载训练数据
    training_data = []
    agent_dir = os.path.join(TRAINING_DIR, agent_type)
    if os.path.exists(agent_dir):
        for f in os.listdir(agent_dir):
            if f.endswith('.json'):
                with open(os.path.join(agent_dir, f), 'r', encoding='utf-8') as fp:
                    training_data.append(json.load(fp))

    if not training_data:
        return None, "无训练数据·请先运行 --extract"

    # 评估所有候选
    results = []
    for candidate in candidates:
        score, detail = evaluate_candidate(candidate, training_data, metrics)
        results.append({
            'candidate': candidate,
            'total_score': score,
            'detail_scores': detail
        })

    # 排序
    results.sort(key=lambda r: r['total_score'], reverse=True)
    best = results[0]

    return {
        'agent_type': agent_type,
        'training_data_count': len(training_data),
        'candidates_evaluated': len(candidates),
        'best_candidate': best['candidate']['name'],
        'best_score': f"{best['total_score']:.2f}",
        'all_results': results,
        'ranking': [f"{i+1}. {r['candidate']['name']} ({r['total_score']:.2f})"
                    for i, r in enumerate(results)]
    }


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    if len(sys.argv) < 2:
        print("用法: python prompt_optimizer.py [agent_name] [--extract|--generate|--optimize]")
        print("Agent: scene_designer | shot_architect | movement_designer | composition_designer")
        print()
        print("--extract   从EP输出中提取训练数据")
        print("--generate  生成prompt候选版本")
        print("--optimize  运行完整优化循环·输出最优prompt")
        sys.exit(1)

    agent_type = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else '--generate'

    if command == '--generate':
        candidates = generate_prompt_candidates(agent_type)
        print(f"\n## {agent_type} Prompt 候选版本\n")
        for c in candidates:
            print(f"### {c['id']}: {c['name']}")
            print(f"  方案: {c['approach']}")
            print(f"  预估token: {c['estimated_tokens_per_call']:,}")
            print(f"  特点: {', '.join(c['key_features'])}")
            print()

    elif command == '--extract':
        # 从EP13提取
        ep13_script = os.path.join(os.path.dirname(__file__), '..', '枪王_EP13_增强分镜剧本_v3.md')
        ep13_output = os.path.join(OUTPUT_DIR, 'EP13_S1_SCENE_DESIGNER_v2.md')
        path = extract_training_data('EP13', '鉴证科实验室', ep13_script, ep13_output, agent_type)
        print(f"提取: {path}")

        # EP14
        ep14_script = os.path.join(os.path.dirname(__file__), '..', 'DIRECTOR_REPORT_EP13.md')
        ep14_output = os.path.join(OUTPUT_DIR, 'EP14_S1_SCENE_DESIGNER.md')
        if os.path.exists(ep14_output):
            path = extract_training_data('EP14', '案情室', ep14_script, ep14_output, agent_type)
            print(f"提取: {path}")

        # EP15
        ep15_script = os.path.join(os.path.dirname(__file__), '..', '枪王_EP13_增强分镜剧本_v3.md')
        ep15_output = os.path.join(OUTPUT_DIR, 'EP15_S1_导演台本.md')
        path = extract_training_data('EP15', 'Rico工作室', ep15_script, ep15_output, agent_type)
        print(f"提取: {path}")

    elif command == '--optimize':
        print(f"\n## {agent_type} 优化循环\n")
        print("生成候选prompt → 对训练数据评估 → 保留最优\n")
        result = optimize_loop(agent_type)

        if isinstance(result, str):
            print(f"错误: {result}")
        else:
            print(f"训练数据: {result['training_data_count']}个EP")
            print(f"候选数: {result['candidates_evaluated']}")
            print(f"\n### 排名:")
            for rank in result['ranking']:
                print(f"  {rank}")
            print(f"\n### 最优: {result['best_candidate']} (得分: {result['best_score']})")


if __name__ == '__main__':
    main()
