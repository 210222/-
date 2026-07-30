# MODE:P vNext 操作边界与回滚演练（R3.1）

> 当前状态：**Rebuild / 安全控制面，不是生产发布授权。**  
> 生产唯一入口：现有 v4 MODE:P。  
> 本文不授权 Shadow、Pilot、Canary、Production、外部生成、真实入口切换或实际媒体验收。

## 1. 绝对边界

- vNext Rebuild 下四种 gate（`shadow`、`pilot`、`canary`、`production`）全部默认关闭，且没有可调用的启用命令；`FeatureGate` 会拒绝每一项启用请求。
- 真实 `/mode-p-pilot` 入口在 R3.1 **没有被修改**。`rollback.py` 只在专用、临时的 vNext control root 中演练控制状态，不能宣称已经完成真实入口切换。
- 不得读取或写入 v4 cache、旧 Session、旧交付、旧知识索引；不得用 v4 作为 vNext 隐藏 fallback。
- 不得发送到外部生成平台；不得因文本/结构检查通过而宣称故事板或视频已视觉验收。
- 不得手改 `RELEASE_CONTROL.json`、rollback manifest、入口指针、Session、delivery、控制器 state 或 lock。不得删除 vNext commit、证据或事故记录。

## 2. 发布阶段（未来流程，不由 R3.1 执行）

| 状态 | 范围 | 前提 | 是否可自动晋升 |
| --- | --- | --- | --- |
| `current` | v4 | 默认安全状态 | 不适用 |
| `vnext_shadow` | 同文本、独立输出 | 隔离目录、无外送、只做多维对照 | 否 |
| `vnext_pilot` | 一次一个场景 | 用户故事板批准、该场真实生成评价 | 否 |
| `vnext_canary` | 一个完整分集 | Episode Review、回滚演练、用户明确批准 | 否 |
| `vnext_production` | 默认入口 | P0/P1、Golden、回归、故障恢复、用户明确批准 | 否 |

Shadow 的对照必须分别报告结构、时序、切镜、可见性、知识使用与格式；不得简化成单一相似度分数。Pilot/Canary/Production 的审批必须是带范围和证据的人工记录，不得用模型文本、布尔值或自动重试伪造。

## 3. R3.1 已实现的安全控制面

`01_调度器/mode_p_vnext/feature_gate.py`：

- `FeatureGate()` 仅接受 `phase="rebuild"`，有效模式恒为 `current`；
- 任意 `enable_shadow`、`enable_pilot`、`enable_canary`、`enable_production` 均 fail-closed；
- `assert_submission_allowed()` 永远拒绝外部提交；
- 即使 control record 损坏或包含未来 release 状态，Rebuild 视图仍返回 `current`。

`01_调度器/mode_p_vnext/rollback.py`：

- `RollbackManifest` 只绑定已经存在的只读 v4 archive 文件、其 SHA-256/大小、vNext 证据哈希、保留 commit 与受影响范围；它不会复制、删除或改写这些源文件；
- `rollback_to_current()` 原子写入 **vNext control root** 中的 `RELEASE_CONTROL.json`，记录操作者、时间、原因、范围、manifest 哈希，并且路由为 `current`；
- `arm_kill_switch()` 用一次原子替换同时写入 `current` 路由与熔断锁存。相同 incident request 可幂等读取；不同 request 不得覆盖原事故；R3.1 不提供 clear 或重新启用 API；
- 缺失、损坏、路径逃逸、符号链接、哈希漂移或不完整 manifest 一律拒绝或退回 `current`，不猜测 vNext 可用。

## 4. 回滚与急停演练流程

本流程只可使用临时、专用 control root 和已准备的只读 archive；不得对真实入口或真实交付执行。

1. 停止/拒绝新的 vNext 调用与外部提交；保存当前日志、证据和最后一个有效交付的哈希。
2. 用 `RollbackController.create_manifest()` 绑定 read-only archive、entry、保留 vNext evidence/commits 和明确 episode/scene scope。创建前后分别记录 archive 与 vNext evidence 的树哈希。
3. 用 `verify_manifest()` 复核 entry、每个 archive artifact、release evidence、范围和 manifest integrity。任一漂移即停止，标为 `ABANDONED_DRILL`，不可重试覆盖。
4. 普通演练调用 `rollback_to_current()`；紧急事故调用 `arm_kill_switch()`。二者都只原子更新 control root 的单一状态文件，绝不回写 v4。
5. 复核 `resolve_effective_entry()` 为 `current`，复核 archive、旧 Session、delivery、vNext commits/evidence 的前后哈希未变化；记录 actor、time、reason、scope、pre/post control hash。
6. 急停后不得自动恢复。任何未来重新进入发布流程都需要新的用户明确批准、全新预检、Golden/回归/恢复证据；不得直接编辑 JSON 或 flag。

## 5. 可执行验证

从 `D:\tsc\导演系统_v5\01_调度器` 执行：

```powershell
python -m pytest `
 mode_p_vnext/tests/test_v10_1_shadow_entry.py `
 mode_p_vnext/tests/test_v10_2_comparison_report.py `
 mode_p_vnext/tests/test_v10_3_feature_gate.py `
 mode_p_vnext/tests/test_v10_4_rollback.py `
 mode_p_vnext/tests/test_v10_5_kill_switch.py -q
```

该命令只验证文本/结构/文件完整性与安全控制面；它不运行模型、不生成媒体、不更改生产入口。若 pytest 因环境拒绝写 `.pytest_cache` 而出现 warning，可记录 warning；测试断言本身仍需全部通过。

## 6. 与导演决策优化的关系

R3.1 不实现创意判断，也不能以“已有回滚/熔断”冒充导演优化。导演工作在后续 vNext.1 队列中实施，必须依次形成：

```text
EpisodeDirectionState → SceneIntent/DirectorProblemSet → K1 → BlockingCommit
→ K2 → Candidate/DirectorDecisionRecord → VEC → EditorialReview
```

该链的正式目标、字段、知识置信度门控、双审查与结果归因，见
`vnext_repair_evidence/DIRECTOR_DECISION_OPTIMIZATION_CHANGE_REQUEST_001.md`。在它同步冻结进施工方案与目标锁之前，不能声称导演决策优化已经实现。
