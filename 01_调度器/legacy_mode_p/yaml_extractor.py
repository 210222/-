"""
YAML提取器 v1.0 — 从Agent完整输出中提取下游需要的YAML块
解决: 下游Agent被迫读1,068行全文·实际只需150行YAML

用法: python yaml_extractor.py [输入文件] [--domain movement|composition|all]
输出: 提取的YAML块保存为独立的 .yml 文件
"""
import re
import sys
import os

DOMAIN_MARKERS = {
    'camera':    (r'(?:segments_camera:|§4 机位域|机位域YAML)', 'segments_camera'),
    'movement':  (r'(?:segments_movement:|§5 运镜域|运镜域YAML)', 'segments_movement'),
    'composition': (r'(?:global_anchors:|§6 构图|构图光影域YAML)', 'global_anchors'),
    'frames_hard': (r'frames_hard:', 'frames_hard'),
    'frames_soft': (r'frames_soft:', 'frames_soft'),
    'frames_movement': (r'frames_movement:', 'frames_movement'),
    'transitions': (r'segments_transitions:', 'segments_transitions'),
}

def extract_yaml_sections(filepath, domain='all'):
    """从Agent输出中提取指定域的YAML块"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return None, str(e)

    lines = content.split('\n')
    extracted = {}

    # 查找YAML起始行
    in_yaml = False
    yaml_lines = []
    current_section = None

    for i, line in enumerate(lines):
        # 检测YAML块开始 (```yaml 或 `yaml)
        if re.match(r'^```yaml|^`yaml', line.strip()):
            in_yaml = True
            yaml_lines = []
            continue

        # 检测YAML块结束
        if in_yaml and re.match(r'^```', line.strip()):
            in_yaml = False
            if yaml_lines and current_section:
                extracted[current_section] = '\n'.join(yaml_lines)
            yaml_lines = []
            current_section = None
            continue

        if in_yaml:
            yaml_lines.append(line)

        # 检测裸YAML开始 (segments_camera: 等直接在markdown中)
        for key, (marker, clean_name) in DOMAIN_MARKERS.items():
            if re.search(marker, line):
                if not in_yaml and clean_name not in extracted:
                    # 裸YAML——跟着缩进行
                    current_section = clean_name
                    bare_yaml = [line]
                    j = i + 1
                    while j < len(lines) and (lines[j].startswith('  ') or lines[j].strip() == ''):
                        bare_yaml.append(lines[j])
                        j += 1
                    extracted[clean_name] = '\n'.join(bare_yaml)
                    current_section = None

    return extracted, None


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    if len(sys.argv) < 2:
        print("用法: python yaml_extractor.py [输入文件] [--domain movement|camera|composition|all]")
        print("示例: python yaml_extractor.py EP13_SCENE_DESIGNER.md --domain movement")
        sys.exit(1)

    filepath = sys.argv[1]
    domain = 'all'
    for i, arg in enumerate(sys.argv):
        if arg == '--domain' and i+1 < len(sys.argv):
            domain = sys.argv[i+1]

    if not os.path.exists(filepath):
        print(f"ERROR: 文件不存在: {filepath}")
        sys.exit(1)

    extracted, error = extract_yaml_sections(filepath, domain)
    if error:
        print(f"ERROR: {error}")
        sys.exit(1)

    out_dir = os.path.dirname(filepath)
    base = os.path.splitext(os.path.basename(filepath))[0]

    for section, yaml_text in extracted.items():
        out_path = os.path.join(out_dir, f'{base}_{section}.yml')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(yaml_text)
        lines = yaml_text.count('\n') + 1
        print(f"{section}: {lines}行 → {out_path}")

    if not extracted:
        print("未找到YAML块·请确认输入文件格式")
    else:
        print(f"\n共提取 {len(extracted)} 个YAML块")


if __name__ == '__main__':
    main()
