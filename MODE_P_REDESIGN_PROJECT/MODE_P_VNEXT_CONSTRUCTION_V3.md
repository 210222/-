<!-- MODE_P_VNEXT_AUTHORITY: architecture-v3.0 -->

# MODE:P vNext 架构 v3.0 施工协议

> 状态：v3.0 单一权威架构的活动施工基线
>
> 唯一施工入口：`/mode-p-vnext-rebuild [optional exact next A-task]`
>
> 唯一控制器：`python -m mode_p_vnext.release_control`
>
> 生产边界：`production_entry=v4_unchanged`；A0–A10 不授权生产切换

## 1. 权威与停止条件

施工只服从：

1. `vnext_repair_evidence/MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V3.0.md`；
2. `MODE_P_VNEXT_RELEASE_TASKS.json`；
3. `MODE_P_VNEXT_RELEASE_STATE.json`；
4. 本协议。

架构优先于施工表。若任务的路径、前置类型或验收条件不能实现 v3.0，执行者必须在
当前任务写失败证据并调用 `release_control fail`。不得使用 v2.x、R、DDO、CPL、
V0–V10 或 `director_vnext1` 的旧方案绕过。v2.3 已正式否决。

## 2. 每轮固定序列

从 `01_调度器` 运行：

```text
python -m mode_p_vnext.release_control audit
python -m mode_p_vnext.release_control status
python -m mode_p_vnext.release_control next
```

只有 `audit.ok=true` 时继续。`next` 必须返回唯一 A 任务；用户参数若存在，必须与它
完全一致。随后：

```text
python -m mode_p_vnext.release_control claim <task> --owner <unique-run-id>
```

保留 token。成功 claim 前禁止实现写入；成功 claim 后只允许修改该任务的
`allowed_paths`。不得直接改 state、lock、completed_tasks、gate 或旧队列。

## 3. 实现纪律

- 一轮只完成一个 A 包，不得提前进入下一包。
- 先建立可复现失败或机械观察，再做最小完整实现。
- 模型只输出创作 Draft；本地代码生成 ID、hash、tick、Boundary、binding、VEC 和
  Projection。
- 事实 source span 只能用于 provenance/order，不得进入时间公式。
- 默认 SD2.0 的 15 秒能力上限作用于每个 Shot，不作用于 Scene 总时长。
- reference/audio 绑定必须来自 typed intents，且落到具体 Shot/VisualBeat；不得解析
  fact ID、statement 或 free text 建立绑定。
- B1 prompt `<12000` 字符，schema `<4500` 字符，在 provider 调用前检查。
- Storyboard/Video 只能从一个 canonical ProjectionAST 派生。
- DP 每轮独立，只能输出范围化 RevisionRequest，不能替 Director 设计。
- A0–A7 不运行外部媒体；文本结果永远不能宣称视觉通过。
- v4 只通过注册的黑盒测试观察，不向 vNext 导入或写入。

## 4. 路径与验证

任务之间拥有独占写入所有权。通配路径按保守重叠规则检查；Evidence 路径只能是
该任务精确的 `A<id>_*.json`。用户工作区中 claim 前存在的无关改动属于用户，不得
暂存、覆盖或删除。

开发期间可运行 focused test 和相关回归；完成时必须运行注册表中该任务的全部
`verification_commands`。测试必须使用仓库 fixture 或临时目录，不能依赖个人盘符、
用户名或未提交的历史输出。外部 fixture 必须显式分类。

Evidence 至少包含：

- `task_id`；
- 完整 `changed_paths`；
- 与 `required_checks` 一一对应的 checks；
- 重要诊断、非目标和生产边界；
- `production_entry=v4_unchanged`；
- `production_switch_authorized=false`。

控制器重新运行注册命令并生成权威 `verification_results`、架构输入哈希和产物哈希，
不能用手写“通过”代替。

## 5. 完成、失败和失效

完成：

```text
python -m mode_p_vnext.release_control complete <task> \
  --owner <run-id> --token <token> --evidence <A-task-evidence.json>
```

失败：

```text
python -m mode_p_vnext.release_control fail <task> \
  --owner <run-id> --token <token> --evidence <failure-evidence.json>
```

控制/架构漂移必须使用 `invalidate` 撤销已完成任务；需要新架构时，先清空所有受影响
完成与活动锁，再注册一份完整新权威文档并调用 `rebase-architecture`。禁止再建立
“base + 多个 amendment”的活动权威包。

任务完成后只暂存 Evidence 中绑定的本轮文件，提交并推送 Git，然后停止。报告下一个
任务但不认领它。

## 6. A0–A10 边界摘要

| 包 | 边界 |
|---|---|
| A0 | v3.0、控制器、活动入口和 v4 隔离 |
| A1 | 领域、NormalizedSource/FactAssembler、time capability、typed intents |
| A2 | 持久状态、事务、恢复、失效、并发 |
| A3 | K1/K2、Snapshot、安全与晋升 |
| A4 | Stage signatures、prompt budget、provider |
| A5 | Blocking/Timeline/VEC 确定性编译 |
| A6 | 单一 ProjectionAST 与双交付 |
| A7 | Gate 0、fresh DP、media/approval ports |
| A8 | raw source 到 Projection 的真实可恢复文本影子 |
| A9 | 未见样本、质量/成本/延迟与架构回归 |
| A10 | 真实媒体、frame evidence、v4 对照、用户预览批准 |

A10 完成也只能得到 `PRODUCTION_SWITCH_PROPOSAL_ELIGIBLE`。生产切换是独立项目，
必须重新授权。
