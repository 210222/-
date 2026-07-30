"""One-shot: replace 8 prompt fixtures with verbatim Codex bodies."""
import json, hashlib, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))

# Load extracted bodies
with open(os.path.join(HERE, '_extracted_bodies.json'), 'r', encoding='utf-8') as f:
    bodies = json.load(f)

# Fixture definitions: stem -> (scene_id, prompt_type, source_section, body_key)
FIXTURES = {
    'gun_barrel_sb_prompt.json':    ('gun_barrel_ep8', 'storyboard', 'GOLDEN_SET_EVIDENCE_REPORT.md §6.2', 'gun_barrel_sb'),
    'gun_barrel_video_prompt.json': ('gun_barrel_ep8', 'video',      'GOLDEN_SET_EVIDENCE_REPORT.md §6.4', 'gun_barrel_video'),
    'audience_sb_prompt.json':      ('audience_ep6',   'storyboard', 'GOLDEN_SET_EVIDENCE_REPORT.md §7.2', 'audience_sb'),
    'audience_video_prompt.json':   ('audience_ep6',   'video',      'GOLDEN_SET_EVIDENCE_REPORT.md §7.4', 'audience_video'),
    'prep_area_sb_prompt.json':     ('prep_area_ep6',  'storyboard', 'GOLDEN_SET_EVIDENCE_REPORT.md §9.2', 'prep_area_sb'),
    'prep_area_video_prompt.json':  ('prep_area_ep6',  'video',      'GOLDEN_SET_EVIDENCE_REPORT.md §9.4', 'prep_area_video'),
    'alley_sb_prompt.json':         ('alley_ep6',      'storyboard', 'GOLDEN_SET_EVIDENCE_REPORT.md §8.2', 'alley_sb'),
    'alley_video_prompt.json':      ('alley_ep6',      'video',      'GOLDEN_SET_EVIDENCE_REPORT.md §8.4', 'alley_video'),
}

manifest = {}
for fname, (scene_id, prompt_type, source_section, body_key) in sorted(FIXTURES.items()):
    body_data = bodies[body_key]
    body_text = body_data['body']
    body_sha = body_data['sha256']
    body_len = body_data['length']
    body_line = body_data['line']

    fixture = {
        "scene_id": scene_id,
        "prompt_type": prompt_type,
        "prompt_text": body_text,
        "source_kind": "codex_user_message",
        "source_body_length": body_len,
        "source_body_sha256": body_sha,
        "source_fidelity": "verbatim",
        "source_jsonl_line": body_line,
        "source_section": source_section,
        "integrity_note": (
            f"Verbatim user-submitted prompt text extracted from Codex JSONL "
            f"line {body_line}. Body SHA-256: {body_sha}. "
            f"Character count (code points): {body_len}. "
            f"Extraction rule: first input_text content block after "
            f"'## My request for Codex:\\n' separator."
        ),
    }

    out_path = os.path.join(HERE, fname)
    json_bytes = json.dumps(fixture, ensure_ascii=False, indent=2, sort_keys=True).encode('utf-8') + b'\n'
    with open(out_path, 'wb') as f:
        f.write(json_bytes)
    file_hash = hashlib.sha256(json_bytes).hexdigest()
    manifest[fname] = file_hash
    assert len(body_text) == body_len
    assert hashlib.sha256(body_text.encode('utf-8')).hexdigest() == body_sha
    print(f'{fname}: body_len={body_len} body_sha={body_sha} file_sha={file_hash} OK')

# Write manifest
manifest_path = os.path.join(HERE, 'prompt_fixture_manifest.json')
manifest_doc = {
    'schema_version': '1.0',
    'fixture_count': len(manifest),
    'fixtures': manifest,
}
with open(manifest_path, 'w', encoding='utf-8') as f:
    json.dump(manifest_doc, f, ensure_ascii=False, indent=2, sort_keys=True)
    f.write('\n')
print(f'\nManifest: {len(manifest)} fixtures')
