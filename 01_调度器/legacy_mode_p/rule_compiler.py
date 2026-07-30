"""
规则知识图谱编译器 v1.0 — Layer 知识图谱
输入: scene_type + rule_graph.json
输出: 激活的规则集 + 约束菜单 + 影响追溯

用法: python rule_compiler.py [scene_type] [--menu] [--trace rule_id]
"""
import json
import sys
import os
from collections import deque

GRAPH_FILE = os.path.join(os.path.dirname(__file__), '..', '04_共享', 'rule_graph.json')
GRAPH_FULL_FILE = os.path.join(os.path.dirname(__file__), '..', '04_共享', 'rule_graph_full.json')
CONSTRAINT_FILE = os.path.join(os.path.dirname(__file__), '..', '04_共享', 'constraint_definitions.json')


def load_graph():
    # 优先加载全量图·回退到对话域图
    for path in [GRAPH_FULL_FILE, GRAPH_FILE]:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    return {}


def load_constraints():
    try:
        with open(CONSTRAINT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def traverse_graph(graph, seed_rules):
    """从种子规则开始·沿triggers边BFS遍历·收集全部激活规则"""
    nodes = graph.get('nodes', {})
    visited = set()
    queue = deque(seed_rules)
    activated = []

    while queue:
        rule_id = queue.popleft()
        if rule_id in visited:
            continue
        if rule_id not in nodes:
            continue
        visited.add(rule_id)
        activated.append(rule_id)

        node = nodes[rule_id]
        # 沿所有关系类型传播
        for rel_type in ['triggers', 'commonly_paired_with', 'provides_basis_for']:
            for neighbor in node.get(rel_type, []):
                if neighbor not in visited:
                    queue.append(neighbor)

    return activated


def trace_impact(graph, violated_rule):
    """追溯违规的影响链"""
    nodes = graph.get('nodes', {})
    if violated_rule not in nodes:
        return []

    # BFS反向追溯·谁依赖这条规则
    impacted = set()
    queue = deque([violated_rule])

    while queue:
        rule_id = queue.popleft()
        node = nodes.get(rule_id, {})
        impacted.add(rule_id)

        # 检查所有节点·谁triggers/requires这条规则
        for other_id, other_node in nodes.items():
            if other_id in impacted:
                continue
            for rel_type in ['triggers', 'requires', 'commonly_paired_with', 'provides_basis_for']:
                if rule_id in other_node.get(rel_type, []):
                    if other_id not in impacted:
                        queue.append(other_id)
                    break

    impacted.discard(violated_rule)
    return sorted(impacted)


def compile_scene(scene_type, graph, constraints=None):
    """为场景类型编译完整激活规则集·支持全量图和对话域图"""

    # 全量图格式 (v2.0)
    if 'scene_activation_extended' in graph:
        sa = graph.get('scene_activation_extended', {}).get(scene_type, {})
        domains = graph.get('domains', {})

        # 收集所有域的P0规则
        all_p0 = []
        for domain_name, domain_info in domains.items():
            all_p0.extend(domain_info.get('key_nodes', []))

        # 跨域边
        cross_edges = graph.get('cross_domain_edges', [])
        from_rules = [e['from'] for e in cross_edges if e.get('type') != 'metarule']
        to_rules = [e['to'] for e in cross_edges if e.get('type') != 'metarule' and e['to'] != 'ALL']
        cross_domain_rules = list(set(from_rules + to_rules))

        total = len(all_p0)
        cross = len(cross_domain_rules)

        return {
            'scene_type': scene_type,
            'format': 'v2.0 全量图',
            'total_domains': len(domains),
            'total_p0_rules': total,
            'cross_domain_edges': cross,
            'activated_p0': sa.get('p0_count', 0),
            'cross_domain': sa.get('cross_domain', []),
            'domains_summary': {d: domains[d]['p0_count'] for d in domains}
        }

    # 对话域图格式 (v1.0)
    scene_activation = graph.get('scene_activation', {}).get(scene_type)
    if not scene_activation:
        return None

    seed_rules = scene_activation.get('seed_rules', [])
    graph_activated = traverse_graph(graph, seed_rules)
    auto_activated = scene_activation.get('auto_activated_by_graph', [])
    all_rules = sorted(set(graph_activated + auto_activated))

    result = {
        'scene_type': scene_type,
        'format': 'v1.0 对话域',
        'seed_rules': seed_rules,
        'activation_reason': scene_activation.get('activation_reason', ''),
        'graph_traversed': graph_activated,
        'total_activated': len(all_rules),
        'all_rules': all_rules,
        'rule_details': {}
    }

    nodes = graph.get('nodes', {})
    for rule_id in all_rules:
        if rule_id in nodes:
            result['rule_details'][rule_id] = {
                'name': nodes[rule_id].get('name', ''),
                'priority': nodes[rule_id].get('priority', ''),
                'triggers': nodes[rule_id].get('triggers', []),
                'conflicts_with': nodes[rule_id].get('conflicts_with', [])
            }

    return result


def generate_menu(compiled, constraints=None):
    """从编译结果生成约束菜单"""
    if not compiled:
        return "未找到场景类型·无法生成菜单"

    rules = compiled['rule_details']
    p0_rules = [rid for rid, info in rules.items() if info['priority'] == 'P0']
    p1_rules = [rid for rid, info in rules.items() if info['priority'] == 'P1']

    menu = f"""
## 🎯 场景规则激活 — {compiled['scene_type']}

**种子规则:** {', '.join(compiled['seed_rules'])}
**激活理由:** {compiled['activation_reason']}
**通过关系网络激活:** {len(compiled['graph_traversed'])}条
**总激活:** {compiled['total_activated']}条 (P0: {len(p0_rules)} · P1: {len(p1_rules)})

### P0 必须检查 (硬约束):
"""
    for rid in p0_rules:
        info = rules[rid]
        triggers = f" → 触发: {', '.join(info['triggers'][:3])}" if info['triggers'] else ""
        conflicts = f" ⚠️与{', '.join(info['conflicts_with'][:2])}冲突" if info.get('conflicts_with') else ""
        menu += f"  [{rid}] {info['name']}{triggers}{conflicts}\n"

    menu += "\n### P1 建议检查 (软约束):\n"
    for rid in p1_rules[:10]:
        info = rules[rid]
        menu += f"  [{rid}] {info['name']}\n"
    if len(p1_rules) > 10:
        menu += f"  ... 共{len(p1_rules)}条P1规则\n"

    menu += f"""
### 冲突关系:

"""
    for rid, info in rules.items():
        for conflict in info.get('conflicts_with', []):
            if conflict in rules:
                menu += f"  ⚠️ [{rid}] {info['name']} ↔ [{conflict}] {rules[conflict]['name']}\n"
                menu += f"     裁决: 选一个做主·另一个做补充·标注意图\n"

    if not any(info.get('conflicts_with') for info in rules.values()):
        menu += "  无冲突\n"

    return menu


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    if len(sys.argv) < 2:
        print("用法: python rule_compiler.py [scene_type] [--menu] [--trace rule_id]")
        print("场景类型: 双人对话 | 三人对话 | 打斗")
        print("示例: python rule_compiler.py 双人对话 --menu")
        print("示例: python rule_compiler.py 双人对话 --trace D-TRI-02")
        sys.exit(1)

    scene_type = sys.argv[1]
    show_menu = '--menu' in sys.argv
    trace_rule = None
    for i, arg in enumerate(sys.argv):
        if arg == '--trace' and i + 1 < len(sys.argv):
            trace_rule = sys.argv[i + 1]
            break

    graph = load_graph()
    constraints = load_constraints()

    if trace_rule:
        impacted = trace_impact(graph, trace_rule)
        node = graph.get('nodes', {}).get(trace_rule, {})
        print(f"\n## 影响追溯: [{trace_rule}] {node.get('name', '?')}")
        print(f"\n如果违反 {trace_rule}:")
        if impacted:
            print(f"  受影响规则 ({len(impacted)}条):")
            for rid in impacted:
                info = graph['nodes'].get(rid, {})
                print(f"    [{rid}] {info.get('name', '?')}")
        else:
            print(f"  无级联影响")
        return

    compiled = compile_scene(scene_type, graph, constraints)

    if not compiled:
        print(f"错误: 未找到场景类型 '{scene_type}'")
        print(f"可用类型: {list(graph.get('scene_activation', {}).keys())}")
        sys.exit(1)

    print(f"\n## 编译结果: {scene_type}")
    if compiled.get('format') == 'v2.0 全量图':
        print(f"覆盖域: {compiled['total_domains']}个")
        print(f"P0规则总数: {compiled['total_p0_rules']}条")
        print(f"跨域边: {compiled['cross_domain_edges']}条")
        print(f"场景激活P0: {compiled['activated_p0']}条")
        print(f"跨域激活: {', '.join(compiled['cross_domain'])}")
        print(f"\n域分布: {compiled['domains_summary']}")
    else:
        print(f"种子规则: {', '.join(compiled['seed_rules'])}")
        print(f"图遍历激活: {compiled['graph_traversed']}")
        print(f"总激活: {compiled['total_activated']}条")

    if show_menu:
        menu = generate_menu(compiled, constraints)
        print(menu)


if __name__ == '__main__':
    main()
