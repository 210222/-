#!/usr/bin/env python3
"""
Enhanced merge: Scene Designer + Movement Designer → unified assembler input.
Fixes the 20% data gap: movement deep data, audio extraction, reference mapping.
"""
import yaml, sys, re, json
from collections import defaultdict

def derive_speed_tier(speed_str):
    """Normalize speed to canonical S-tier."""
    s = str(speed_str)
    m = re.search(r'S(\d+)', s)
    if m: return f'S{m.group(1)}'
    m = re.search(r'(\d+\.?\d*)\s*x', s)
    if m:
        v = float(m.group(1))
        if v <= 0.03: return 'S1'
        if v <= 0.1: return 'S1'
        if v <= 0.3: return 'S2'
        if v <= 0.6: return 'S3'
        if v <= 1.0: return 'S4'
        if v <= 1.5: return 'S5'
        if v <= 2.5: return 'S6'
        if v <= 4.0: return 'S7'
        return 'S8'
    return 'S0' if s in ('S0', '固定', '静态', '') else 'S0'

def derive_camera_fixed(movement_type, speed_tier):
    """Determine if camera is static."""
    t = str(movement_type); st = str(speed_tier)
    return (t == '固定' or st == 'S0' or '静态' in t)

def extract_audio_per_shot(segment_frames):
    """Extract audio descriptions from keyframes, grouped by shot_id."""
    shot_audio = defaultdict(list)
    for sf in segment_frames:
        sid = sf.get('shot_id', sf.get('segment_id', ''))
        for kf in sf.get('keyframes', []):
            audio = kf.get('audio', '')
            if audio and audio not in shot_audio[sid]:
                shot_audio[sid].append(audio)
    return {k: ' | '.join(v) for k, v in shot_audio.items()}

def main():
    sd_path = sys.argv[1]
    md_path = sys.argv[2] if len(sys.argv) > 2 else None
    out_path = sys.argv[3] if len(sys.argv) > 3 else sd_path.replace('.yml', '_enhanced.yml')

    with open(sd_path, 'r', encoding='utf-8') as f:
        sd = yaml.safe_load(f)

    # Load Movement Designer data if available
    md = {}
    if md_path:
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                md = yaml.safe_load(f)
        except: pass

    # Build Movement Designer lookups
    md_movements = {}
    md_transitions = {}
    if md:
        for m in md.get('segments_movement', []):
            for key in ('segment_id', 'shot_id'):
                v = m.get(key, '')
                if v: md_movements[v] = m
        for t in md.get('segments_transitions', []):
            key = t.get('from_shot', t.get('from_segment', ''))
            if key: md_transitions[key] = t

    # Extract audio from keyframes
    shot_audio = extract_audio_per_shot(sd.get('segment_frames', []))

    # Reference image mapping (from CONTEXT_PACKAGE §5)
    REF_GRID_MAP = {
        '航拍': '格1-1 高空俯瞰大道',
        '大道': '格2-2 大道纵深',
        '街角': '格1-2 街角+消防栓',
        '石板': '格2-1 石板路棕榈',
        '消防栓': '格3-2 消防栓近景',
        '格栅': '格3-1 下水道格栅',
        '橱窗': '格3-3 奢侈品橱窗',
        '十字': '格1-3 雨夜十字路口',
        '手枪': '枪械三视图 左/中/右',
        'Rico': 'Rico角色参考图',
        'Miguel': 'Miguel角色参考图',
        'Isabela': 'Isabela角色参考图',
        'Pedro': 'Pedro角色参考图',
    }

    # Map shot_list → segments_camera (enriched)
    segments_camera = []
    for s in sd.get('shot_list', []):
        sid = s.get('shot_id', '')
        pos = s.get('camera_position', '')

        # Merge Movement Designer deep data
        md_mov = md_movements.get(sid, {})
        movement_type = md_mov.get('movement_type', md_mov.get('movement', s.get('camera_type', '固定')))
        speed_tier = derive_speed_tier(md_mov.get('speed_tier', s.get('speed', 'S0')))
        camera_fixed = derive_camera_fixed(movement_type, speed_tier)
        speed_curve = md_mov.get('speed_curve', {})
        movement_path = md_mov.get('path', '')
        movement_motivation = md_mov.get('motivation', '')

        # Reference image mapping
        refs = []
        pos_lower = pos.lower() if pos else ''
        scale_str = s.get('scale', '')
        chars = s.get('characters', [])
        narrative = s.get('narrative', '')

        # Scene-wide defaults (entire scene = 保利斯塔大街)
        if '航拍' in pos or '远景' in scale_str:
            refs.append('格1-1 高空俯瞰大道')
        else:
            refs.append('格2-2 大道纵深透视')  # all street-level shots

        # Specific grid matching from REF_GRID_MAP
        for kw, grid in REF_GRID_MAP.items():
            if kw in ('Rico', 'Miguel', 'Isabela', 'Pedro', '手枪'):
                continue  # character/prop refs handled separately
            if kw in pos or kw in narrative or kw in scale_str or kw in s.get('camera_type', ''):
                if grid not in refs: refs.append(grid)

        # Character refs
        for ch in chars:
            refs.append(f'{ch}角色参考图')

        # Prop refs
        if '手枪' in narrative or '枪' in narrative or '枪' in pos:
            refs.append('枪械三视图 左/中/右')

        seg = {
            'segment_id': sid,
            'shot_id': sid,
            'scale': s.get('scale', ''),
            'angle': s.get('angle', ''),
            'focal_length': s.get('focal_length', ''),
            'camera_position': pos,
            'camera_type': s.get('camera_type', ''),
            'time_range': s.get('time_range', [0, 6]),
            'duration_s': s['time_range'][1] - s['time_range'][0] if 'time_range' in s else 6,
            'global_sec_start': s.get('time_range', [0, 6])[0],
            'global_sec_end': s.get('time_range', [0, 6])[1] - 1,
            'characters': s.get('characters', []),
            'kb_rules': s.get('kb_rules', []),
            'narrative': s.get('narrative', ''),
            'emotion': s.get('emotion', ''),
            # Movement data (from Movement Designer or Scene Designer fallback)
            'movement': movement_type,
            'movement_speed_tier': speed_tier,
            'camera_fixed': camera_fixed,
            'speed_curve': speed_curve,
            'movement_path': movement_path,
            'movement_motivation': movement_motivation,
            # Reference images
            'reference_images': refs,
            # Audio extracted from keyframes
            'shot_audio': shot_audio.get(sid, ''),
        }
        segments_camera.append(seg)

    # Build segments_movement from Movement Designer
    segments_movement = []
    if md:
        for m in md.get('segments_movement', []):
            segments_movement.append({
                'segment_id': m.get('segment_id', m.get('shot_id', '')),
                'movement': m.get('movement_type', m.get('movement', '')),
                'movement_speed_tier': derive_speed_tier(m.get('speed_tier', 'S0')),
                'camera_fixed': derive_camera_fixed(m.get('movement_type', ''), m.get('speed_tier', 'S0')),
                'speed_curve': m.get('speed_curve', {}),
                'path': m.get('path', ''),
                'start_state': m.get('start_state', ''),
                'end_state': m.get('end_state', ''),
                'kb_rule_ids': m.get('kb_rules', []),
                'motivation': m.get('motivation', ''),
                'spatial_feasibility': m.get('spatial_feasibility', ''),
                'p_fal_check': m.get('p_fal_check', []),
                'emotion_value': m.get('emotion_value', ''),
                'transition_to': m.get('transition_to', ''),
                'transition_type': m.get('transition_type', ''),
            })

    # Build segments_transitions from Movement Designer
    segments_transitions = md.get('segments_transitions', []) if md else []

    # Preserve original segment_frames (keyframes with performance, description_visual, audio)
    segment_frames = sd.get('segment_frames', [])

    # Build output
    out = {
        'scene': sd.get('scene', {}),
        'segments_camera': segments_camera,
        'segments_movement': segments_movement,
        'segments_transitions': segments_transitions,
        'segment_frames': segment_frames,
        'dialogue_map': sd.get('dialogue_map', []),
        'global_anchors': sd.get('global_anchors', {}),
        'composition_anchors': sd.get('composition_anchors', {}),
    }

    with open(out_path, 'w', encoding='utf-8') as f:
        yaml.dump(out, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    print(f"Enhanced merge: {len(segments_camera)} shots, "
          f"{len(segments_movement)} movements, "
          f"{len(segments_transitions)} transitions, "
          f"{len(segment_frames)} keyframe groups → {out_path}")

if __name__ == '__main__':
    main()
