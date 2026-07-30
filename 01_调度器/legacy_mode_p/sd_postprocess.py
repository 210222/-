#!/usr/bin/env python3
"""
sd_postprocess.py v1.0 — Scene Designer 后处理器 (确定性·0 tokens)

职责:
  1. 合并 v1.0 YAML (segments_camera + segments_movement + global_anchors)
     与 v2.0 Agent 输出 (segment_frames + dialogue_map)
  2. 验证 keyframe 覆盖完整性
  3. 验证 performance 文本合规 (正则·零LLM)
  4. 输出完整 v2.0 YAML

使用:
  python sd_postprocess.py --v1 EP2_SCENE_DESIGNER_v1.yml --kf KEYFRAMES.yml --out EP2_SCENE_DESIGNER_v2.yml
"""
import yaml, re, argparse, sys, io
from typing import Dict, List

# Fix Windows GBK encoding for print
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

NL = "\n"

# ===== Text quality checks (Gate 0 R02/R16·零LLM) =====

R02_FORBIDDEN = re.compile(r"开始|正在|刚|已|持续|继续|一直|仍|缓缓|渐渐|慢慢|逐渐")
R16_FORBIDDEN = re.compile(r"悲伤|愤怒|恐惧|紧张|焦虑|压抑|绝望|兴奋|厌恶|震惊")

def check_action_anchor(text: str) -> List[str]:
    """Return list of R02 violations in action_anchor text."""
    return R02_FORBIDDEN.findall(text)

def check_performance(perf: Dict) -> List[str]:
    """Return list of R16 violations in performance fields."""
    violations = []
    for section in ["facial", "body"]:
        for field, value in perf.get(section, {}).items():
            if isinstance(value, str):
                hits = R16_FORBIDDEN.findall(value)
                for h in hits:
                    violations.append(f"R16:{h} in performance.{section}.{field}")
    return violations

def validate_keyframe_coverage(segment_frames: List[Dict], segments_camera: List[Dict]) -> List[str]:
    """Verify keyframes cover all seconds — using assembler-compatible logic (global_sec-based)."""
    errors = []
    cam_by_id = {cam.get("segment_id", cam.get("shot_id", "")): cam for cam in segments_camera}

    for sf in segment_frames:
        sid = sf.get("segment_id", sf.get("shot_id", ""))
        cam = cam_by_id.get(sid, {})
        tr = cam.get("time_range", [0, 0])
        dur = tr[1] - tr[0]
        start = tr[0]
        kfs = sf.get("keyframes", [])

        if not kfs:
            errors.append(f"COVERAGE: {sid} has no keyframes")
            continue
        if kfs[0].get("sec_offset", -1) != 0:
            errors.append(f"COVERAGE: {sid} first keyframe not at sec_offset=0")

        # Use assembler logic: keyframe N covers [kf_N.global_sec, kf_N+1.global_sec)
        # Last keyframe covers [last.global_sec, segment_end)
        for offset in range(dur):
            gs = start + offset
            # Find covering keyframe
            covered_by = None
            for i, kf in enumerate(kfs):
                kf_gs = kf.get("global_sec", start + kf.get("sec_offset", 0))
                next_gs = kfs[i+1].get("global_sec", start + dur) if i+1 < len(kfs) else (start + dur)
                if kf_gs <= gs < next_gs:
                    covered_by = kf.get("kf_id", "?")
                    break
            if covered_by is None:
                errors.append(f"COVERAGE: {sid} second {gs} not covered by any keyframe")

    return errors

# ===== Main =====

def postprocess(v1_path: str, kf_path: str, output_path: str) -> str:
    # Load v1.0 YAML
    with open(v1_path, "r", encoding="utf-8") as f:
        v1 = yaml.safe_load(f)

    # Load Agent-produced keyframes + dialogue_map
    with open(kf_path, "r", encoding="utf-8") as f:
        kf_data = yaml.safe_load(f)

    scene = v1.get("scene", {})
    global_anchors = v1.get("global_anchors", {})
    segments_camera = v1.get("segments_camera", [])
    segments_movement = v1.get("segments_movement", [])
    segment_frames = kf_data.get("segment_frames", [])
    dialogue_map = kf_data.get("dialogue_map", [])

    # ===== Validate =====
    errors = []
    warnings = []

    # 1. Coverage check
    errors.extend(validate_keyframe_coverage(segment_frames, segments_camera))

    # 2. Text quality check
    for sf in segment_frames:
        sid = sf.get("shot_id", sf.get("segment_id", "?"))
        for kf in sf.get("keyframes", []):
            aa = kf.get("action_anchor", "")
            r02_hits = check_action_anchor(aa)
            if r02_hits:
                errors.append(f"R02:{sid} kf {kf.get('kf_id','?')} action_anchor contains: {r02_hits}")

            perf = kf.get("performance", {})
            r16_hits = check_performance(perf)
            if r16_hits:
                errors.append(f"R16:{sid} kf {kf.get('kf_id','?')}: {r16_hits}")

    # 3. Dialogue map coverage
    if not dialogue_map:
        warnings.append("dialogue_map is empty")
    else:
        total_entries = sum(len(dm.get("entries", [])) for dm in dialogue_map)
        if total_entries < 5:
            warnings.append(f"dialogue_map has only {total_entries} entries (expected 13+ for EP2)")

    # ===== Report =====
    print(f"=== sd_postprocess v1.0 ===")
    print(f"  segments_camera: {len(segments_camera)}")
    print(f"  segments_movement: {len(segments_movement)}")
    print(f"  segment_frames: {len(segment_frames)}")
    print(f"  keyframes total: {sum(len(sf.get('keyframes',[])) for sf in segment_frames)}")
    print(f"  dialogue_map: {len(dialogue_map)} shots, {sum(len(dm.get('entries',[])) for dm in dialogue_map)} entries")
    print(f"  Errors: {len(errors)}")
    print(f"  Warnings: {len(warnings)}")

    if errors:
        print(f"\n  ERRORS ({len(errors)}):")
        for e in errors[:10]:
            print(f"    {e[:100]}")
        if len(errors) > 10:
            print(f"    ... and {len(errors)-10} more")

    if warnings:
        print(f"\n  WARNINGS ({len(warnings)}):")
        for w in warnings[:5]:
            print(f"    {w[:100]}")

    # ===== Assemble output =====
    output = {
        "scene": scene,
        "global_anchors": global_anchors,
        "segments_camera": segments_camera,
        "segments_movement": segments_movement,
        "segment_frames": segment_frames,
        "dialogue_map": dialogue_map,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(output, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    verdict = "BLOCKED" if errors else ("WARN" if warnings else "PASS")
    print(f"\n  Verdict: {verdict}")
    print(f"  Output: {output_path}")

    return verdict


def main():
    p = argparse.ArgumentParser(description="sd_postprocess.py v1.0")
    p.add_argument("--v1", required=True, help="v1.0 Scene Designer YAML")
    p.add_argument("--kf", required=True, help="Agent-produced keyframes + dialogue_map YAML")
    p.add_argument("--out", required=True, help="Output complete v2.0 YAML path")
    args = p.parse_args()
    verdict = postprocess(args.v1, args.kf, args.out)
    sys.exit(0 if verdict != "BLOCKED" else 1)


if __name__ == "__main__":
    main()
