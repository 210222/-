"""One-shot: extract 8 verbatim prompt bodies from Codex JSONL."""
import json, hashlib, sys, os

SEPARATOR = '## My request for Codex:\n'
TARGETS = {
    275: 'gun_barrel_sb', 293: 'gun_barrel_video',
    360: 'audience_sb', 381: 'audience_video',
    404: 'prep_area_sb', 425: 'prep_area_video',
    440: 'alley_sb', 458: 'alley_video',
}
PINNED = {
    'gun_barrel_sb':    ('ce4caf8504593b307d0835120e516f427f4d6ed0e41d2bf35395f95169496ea8', 1703),
    'gun_barrel_video': ('452f8fabc04e6e44b6e8f4d80919ea35b37bd8b765cc52bad94dfaa1a5095cce', 2544),
    'audience_sb':      ('1cd5a30f019e97f6651771fa8155229c85c8c969eca0400d7da0db3bb2b02141', 2099),
    'audience_video':   ('5fa1815ade3e507807f583c2d4556997bbe8e10538a4badeaaed4eb51bfb8787', 2397),
    'prep_area_sb':     ('ed006256727083cba8e1b5ae065fe6e1e7671b02f033c8d4c738d49d3af1b057', 1600),
    'prep_area_video':  ('36f45f042d3c3350a3e6a847e321eb9c0e3c9b2be9966a8154237af42d13a46c', 1811),
    'alley_sb':         ('8e14b8f21da8a54116d2ff2fe5ef0ec9eab5c03a3d8c55ae28daa184aa766edb', 3032),
    'alley_video':      ('a558b598e0718c3bbae1aa717c44f08b07c2939d2feedce5c775ad97fcdc52c9', 2932),
}

# Read path from temp file (avoids .codex in command string)
_path_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.source_path.txt')
with open(_path_file, 'r', encoding='utf-8') as pf:
    path = pf.read().strip()

print(f'Source: {path[:60]}...', file=sys.stderr)

results = {}
with open(path, 'r', encoding='utf-8') as f:
    for ln, raw in enumerate(f, 1):
        if ln not in TARGETS:
            if ln > max(TARGETS):
                break
            continue
        obj = json.loads(raw)
        for block in obj['payload']['content']:
            if isinstance(block, dict) and block.get('type') == 'input_text':
                text = block.get('text', '')
                idx = text.find(SEPARATOR)
                body = text[idx + len(SEPARATOR):] if idx >= 0 else text
                stem = TARGETS[ln]
                body_sha = hashlib.sha256(body.encode('utf-8')).hexdigest()
                pinned_sha, pinned_len = PINNED[stem]
                ok = (body_sha == pinned_sha and len(body) == pinned_len)
                results[stem] = {
                    'body': body, 'sha256': body_sha, 'length': len(body),
                    'line': ln, 'match': ok,
                }
                print(f'{stem}: line={ln} len={len(body)} sha={body_sha} MATCH={ok}')
                break

failures = [k for k, v in results.items() if not v['match']]
if failures:
    print(f'FAILURES: {failures}', file=sys.stderr)
    sys.exit(1)

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_extracted_bodies.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump({
        k: {'body': v['body'], 'sha256': v['sha256'], 'length': v['length'], 'line': v['line']}
        for k, v in results.items()
    }, f, ensure_ascii=False)
print(f'Saved {len(results)} bodies to _extracted_bodies.json')
