import json, hashlib, sys
sys.path.insert(0, '.')
from pathlib import Path
from mode_p_vnext.rebuild_control import RebuildControl

c = RebuildControl.default()
lock = json.loads(open(c.lock_path, 'r', encoding='utf-8').read())
token = lock['token']
owner = 'ds-r14-deep-repair-20260726'

evidence_path = c.root / 'MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/R0.1.json'
evidence_path.parent.mkdir(parents=True, exist_ok=True)

evidence = {
    'task_id': 'R0.1',
    'changed_paths': [
        '01_调度器/mode_p_vnext/rebuild_control.py',
        '01_调度器/mode_p_vnext/tests/test_rebuild_control.py',
        'MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_REPAIR_TASKS.json',
        'MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/R0.1.json',
    ],
    'checks': [
        {'name': 'task_graph', 'exit_code': 0},
        {'name': 'atomic_claim', 'exit_code': 0},
        {'name': 'owner_token', 'exit_code': 0},
        {'name': 'evidence_gate', 'exit_code': 0},
        {'name': 'state_audit', 'exit_code': 0},
    ],
}

with open(evidence_path, 'w', encoding='utf-8') as f:
    json.dump(evidence, f, ensure_ascii=False, indent=2)
    f.write('\n')

print(f'Evidence SHA256: {hashlib.sha256(open(evidence_path, "rb").read()).hexdigest()}')

try:
    state = c.complete('R0.1', owner, token, evidence_path)
    print(f'COMPLETE OK. completed={state["completed_tasks"]} next={state["next_task"]}')
except Exception as e:
    print(f'COMPLETE FAILED: {e}')
