import json,sys
from pathlib import Path
sys.path.insert(0,'D:/tsc/导演系统_v5/01_调度器')
from mode_p_vnext.rebuild_control import RebuildControl
c=RebuildControl(Path('D:/tsc/导演系统_v5'))
l=json.loads(open(c.lock_path,'r',encoding='utf-8').read())
s=c.complete('R0.1',l['owner'],l['token'],c.root/'MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/R0.1.json')
print('OK',s['completed_tasks'],s['next_task'])
