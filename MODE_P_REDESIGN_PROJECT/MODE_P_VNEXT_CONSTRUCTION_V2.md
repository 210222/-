# MODE:P vNext 架构 v2.x 施工协议（历史只读）

> 状态：`HISTORICAL_READ_ONLY`
>
> v2.3 处置：`REJECTED_BY_WHOLE_SYSTEM_AUDIT`

本文件不再是活动施工入口，不能选择、认领或完成任何 A 任务。v2.0–v2.3 的架构
叠加方式已经由 v3.0 单一权威基线取代。

活动施工必须读取：

- `vnext_repair_evidence/MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V3.0.md`
- `MODE_P_VNEXT_CONSTRUCTION_V3.md`
- `MODE_P_VNEXT_RELEASE_TASKS.json`
- `MODE_P_VNEXT_RELEASE_STATE.json`

唯一控制器仍为 `python -m mode_p_vnext.release_control`。生产入口保持
`v4_unchanged`，本历史文件不授权生产切换。
