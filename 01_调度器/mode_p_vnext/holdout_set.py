"""MODE:P vNext — Holdout Set (V8.4).

New scenes not part of the four Golden calibration cases. Used exclusively
for validation — must NOT participate in template design or knowledge
extraction. Prevents overfitting to the four success samples.

Spec references: LOOP §13.8; Omission P1-11.
"""

from __future__ import annotations

from typing import Any, Dict

HOLDOUT_SCENES: Dict[str, Dict[str, Any]] = {
    "ep13_investigation_lab": {
        "scene_name": "EP13 鉴证科实验室",
        "episode": "EP13",
        "holdout": True,
        "reason": "未参与四组 Golden 校准——用作独立验证",
    },
    "ep14_case_room": {
        "scene_name": "EP14 案情室",
        "episode": "EP14",
        "holdout": True,
        "reason": "未参与四组 Golden 校准——用作独立验证",
    },
    "ep15_rico_studio": {
        "scene_name": "EP15 Rico工作室",
        "episode": "EP15",
        "holdout": True,
        "reason": "未参与四组 Golden 校准——用作独立验证",
    },
}
