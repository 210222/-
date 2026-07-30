"""Prevent internal KB rule IDs from being written into prompt deliverables."""
import sys
import json
import re

KB_PATTERN = re.compile(
    r'(?:D-TRI|A-SUS|M-MOT|M-TRK|C-KTZ|C-FI|C-AJS|L-CT|L-SCN|L-LOW|L-3PT|'
    r'COL-PRI|VS-TONE|D-DUO|D-DIA|D-POV|D-MOT|D-VLM|D-TRI-3|A-CHS|A-GEN|'
    r'A-ACT|E-PCE)-\d+|\bKB:\s|· KB:'
)

GUARDED_NAMES = {"STORYBOARD.MD", "VIDEO_PROMPT.MD"}


def is_guarded_prompt(file_path: str) -> bool:
    name = file_path.replace("\\", "/").rsplit("/", 1)[-1]
    upper = name.upper()
    return upper in GUARDED_NAMES or upper.startswith("STORYBOARD_") or "视频提示词" in name

try:
    d = json.load(sys.stdin)
    fp = d.get('tool_input', {}).get('file_path', '')
    tool_input = d.get('tool_input', {})
    c = tool_input.get('content', '') or tool_input.get('new_string', '')

    kb_matches = KB_PATTERN.findall(c)

    if is_guarded_prompt(fp) and kb_matches:
        print(json.dumps({
            "continue": False,
            "systemMessage": "KB泄漏：请移除所有KB规则ID后重试",
            "stopReason": "KB泄漏：故事板或视频提示词包含内部规则ID。请保留自然语言设计并移除规则编号。"
        }))
    else:
        print(json.dumps({"continue": True}))

except Exception as e:
    # fail-open: any error (encoding, JSON parse, etc.) allows the operation
    print(json.dumps({"continue": True}))
