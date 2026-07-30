"""Generate TEST_KEYFRAME_PLAN.yml with 3 shots, 6 keyframes, performance data."""
import yaml

t = {
    "scene": {"name": "EP2 test", "total_duration_s": 22, "total_shots": 3,
              "axis_side": "A", "static_shots": 3, "static_ratio": 1.0},
    "global_anchors": {
        "character": {
            "Isabela": ["warm light wraps her face Rembrandt triangle"],
            "Rico": ["white shirt wet hair backlit silhouette"],
        },
        "environment": {"description": "Cafe 10-12m depth", "spatial_anchor": "door->counter"},
        "lighting": {
            "description": "cool-warm dual source system",
            "anchor_sources": [
                {"source": "door morning", "kelvin": 6000, "direction": "horizontal", "ref_grid": "grid upper mid"},
                {"source": "bar pendant", "kelvin": 3000, "direction": "vertical down", "ref_grid": "grid right"},
            ]
        },
        "style_spine": {"description": "cool vs warm confrontation", "palette_anchors": ["amber", "steel"]},
        "constraints": ["A-side locked", "P-FAL-10 alt single mouth"]
    },
    "time_skeleton": [
        {
            "segment_id": "s1", "shot_id": "#2", "time_range": [0, 8], "duration_s": 8,
            "global_sec_start": 0, "shot_type": "MS", "focal_length": "50mm",
            "dof": "f/2.8", "angle": "eye level", "axis_side": "A",
            "camera_position": "D zone counter front X=8m", "camera_type": "single fix",
            "movement": "static", "movement_speed_tier": "S0",
            "camera_fixed": True, "actor_fixed": True,
            "kb_rule_ids": ["D-TRI-06", "L-3PT-02"],
            "characters_in_frame": ["Isabela"],
            "segment_frames": {
                "characters_in_frame": ["Isabela"],
                "keyframes": [
                    {
                        "kf_id": "s1-1", "sec_offset": 0, "global_sec": 0,
                        "type": "hold", "hold_until": 6,
                        "action_anchor": "wiping cups clockwise mechanical repetition",
                        "performance": {
                            "facial": {
                                "eyes": "lids half lowered gaze on cup rim not focusing",
                                "brow": "neutral no muscle tension",
                                "mouth": "lips closed natural no activity"
                            },
                            "body": {
                                "posture": "standing behind counter weight centered slight forward lean",
                                "hands": "left holds cup right white cloth rotating wrist steady speed"
                            }
                        },
                        "lighting": "L3 3000K Rembrandt triangle light",
                        "spatial": "marble counter cup shelf bg",
                        "audio": "espresso steam hiss fridge hum"
                    },
                    {
                        "kf_id": "s1-2", "sec_offset": 6, "global_sec": 6,
                        "type": "event",
                        "action_anchor": "phone screen lights up hand stops gaze shifts to screen",
                        "performance": {
                            "facial": {
                                "eyes": "gaze jerks from cup to phone pupil adapts to screen brightness",
                                "brow": "slight frown vertical line appears between brows",
                                "mouth": "lower lip tightens lip line flattens"
                            },
                            "body": {
                                "posture": "body leans forward weight shifts toward phone",
                                "hands": "right hand wiping motion stops abruptly left reaches for phone"
                            }
                        },
                        "lighting": "L3 warm + phone cool white from below face",
                        "spatial": "marble counter phone flat screen up",
                        "audio": "phone vibration buzz wiping sound stops"
                    }
                ]
            },
            "transition_to": "s2", "transition_type": "cut",
            "transition_motivation": "MS to insert phone screen"
        },
        {
            "segment_id": "s2", "shot_id": "#9", "time_range": [8, 16], "duration_s": 8,
            "global_sec_start": 8, "shot_type": "MS", "focal_length": "35mm",
            "dof": "f/5.6", "angle": "eye level", "axis_side": "A",
            "camera_position": "C zone looking at door", "camera_type": "external reverse fix",
            "movement": "static", "movement_speed_tier": "S0",
            "camera_fixed": True, "actor_fixed": True,
            "kb_rule_ids": ["D-TRI-05", "A-SUS-02"],
            "characters_in_frame": ["Rico"],
            "segment_frames": {
                "characters_in_frame": ["Rico"],
                "keyframes": [
                    {
                        "kf_id": "s2-1", "sec_offset": 0, "global_sec": 8,
                        "type": "hold", "hold_until": 10,
                        "action_anchor": "door closed cafe quiet distant bar warm glow",
                        "lighting": "L1 door cool L3 distant warm depth gradient",
                        "spatial": "door to counter 10m axis",
                        "audio": "fridge hum only"
                    },
                    {
                        "kf_id": "s2-2", "sec_offset": 2, "global_sec": 10,
                        "type": "event",
                        "action_anchor": "door opens brass bell swings cold blue light floods in Rico backlit silhouette",
                        "performance": {
                            "facial": {
                                "eyes": "face invisible in strong backlight only edge light outlines hair",
                                "brow": "not visible in silhouette",
                                "mouth": "not visible in silhouette"
                            },
                            "body": {
                                "posture": "standing straight shoulder width weight centered arms at sides"
                            }
                        },
                        "lighting": "L1 6000K strong backlight Rico front dark white shirt translucent glow",
                        "spatial": "doorway frame mid-left of composition",
                        "audio": "brass bell clear ring door hinge soft creak"
                    },
                    {
                        "kf_id": "s2-3", "sec_offset": 4, "global_sec": 12,
                        "type": "hold", "hold_until": 16,
                        "action_anchor": "Rico stands in doorway still looking toward counter Isabela far right tiny figure",
                        "lighting": "door cool + distant bar warm each figure wrapped in different color temp",
                        "spatial": "Rico door left Isabela counter extreme right 8m apart",
                        "audio": "silence fridge hum"
                    }
                ]
            },
            "transition_to": "s3", "transition_type": "cut",
            "transition_motivation": "Rico entrance to Isabela reaction"
        },
        {
            "segment_id": "s3", "shot_id": "#18", "time_range": [16, 22], "duration_s": 6,
            "global_sec_start": 16, "shot_type": "ECU", "focal_length": "85mm",
            "dof": "f/2.8", "angle": "slight top-down 30 deg", "axis_side": "N/A insert",
            "camera_position": "D zone above counter surface", "camera_type": "insert ECU fix",
            "movement": "static", "movement_speed_tier": "S0",
            "camera_fixed": True, "actor_fixed": True,
            "kb_rule_ids": ["C-KTZ-02", "C-FI-01"],
            "characters_in_frame": [],
            "segment_frames": {
                "characters_in_frame": [],
                "keyframes": [
                    {
                        "kf_id": "s3-1", "sec_offset": 0, "global_sec": 16,
                        "type": "hold", "hold_until": 22,
                        "action_anchor": "white ceramic coffee cup center frame empty faint reflection on bottom marble texture",
                        "lighting": "L3 3000K pendant top light warm glow on cup rim",
                        "spatial": "marble counter extremely shallow DOF cup only element in focus",
                        "audio": "absolute silence fridge compressor hum very faint"
                    }
                ]
            },
            "transition_to": "END", "transition_type": "cut",
        },
    ],
    "dialogue_map": [
        {
            "shot_id": "#9",
            "entries": [
                {"speaker": "Rico", "text_pt": "so early opening?", "global_sec_start": 12,
                 "duration_s": 2.5, "direction": "looking at her across 8m"}
            ]
        }
    ],
}

with open("C:/Users/JT/Desktop/枪王/场景/第二集/TEST_KEYFRAME_PLAN.yml", "w", encoding="utf-8") as f:
    yaml.dump(t, f, allow_unicode=True, default_flow_style=False)

kfs = sum(len(s["segment_frames"]["keyframes"]) for s in t["time_skeleton"])
print(f"Test PLAN: {len(t['time_skeleton'])} shots, {kfs} keyframes, "
      f"{sum(len(e['entries']) for e in t['dialogue_map'])} dialogue entries")
