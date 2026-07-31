# MODE:P vNext 架构 v2.1 施工协议

> 状态：架构 v2.1 权威包的施工基线
>
> 唯一施工入口：`/mode-p-vnext-rebuild [optional exact next A-task]`
>
> 唯一机器任务表：`MODE_P_VNEXT_RELEASE_TASKS.json`
>
> 唯一机器状态：`MODE_P_VNEXT_RELEASE_STATE.json`
>
> 唯一控制器：`python -m mode_p_vnext.release_control`
>
> 生产边界：v4 保持唯一生产入口；本协议不授权生产切换。

## 1. 为什么施工文件必须迁移

架构 v2.1 保持并强化了“停止给旧 B1 Prompt 追加规则”的路线。如果施工仍由 R、DDO、
CPL 三套队列分别选择任务，就会继续产生以下矛盾：

- R 队列要求先修旧控制面；
- DDO 队列同时宣称旧文本管道已经完成；
- CPL 队列继续尝试让模型生成最终 VEC；
- 三个状态都可能自称权威；
- 已失败的 27K B1 边界会被当作提示词问题继续修补。

因此，从本文件生效起，旧队列只作为审计历史。它们的完成记录、失败记录和产物可以
成为迁移输入，但不能选择新任务，不能授予 A0–A10 完成，也不能授权 Shadow、媒体
通过或生产切换。

### 1.1 本轮不改变的原设计

施工治理修复不得改变以下产品架构：

- Director 内循环负责统一视觉设计，媒体外循环用真实结果反馈；
- Director 拥有设计权，DP 独立复核并只提交 RevisionRequest；
- 模型只输出创意 Draft，ID、哈希、tick、边界、Timeline 和 VEC 由本地确定性组装；
- 单一 Artifact、24000 tick 时间基、单一 ProjectionAST 和双交付同源；
- Prompt 按 StageSignature 编译，B1 Prompt 12K、Schema 4.5K 硬上限不变；
- 只有真实媒体证据与明确用户批准才能进入生产切换提案；
- v4 在独立生产切换任务得到批准前保持唯一生产入口。

Fable 5、Claude 系统提示词资料和旧代码库只提供双循环、状态推进、上下文分层等
原理参考；不把泄露提示词复制成 MODE:P 的长系统提示词，也不恢复旧多 Agent 形态。

## 2. 权威优先级

施工时只按以下顺序读取：

1. 用户在当前任务中的最新明确指令；
2. 架构 v2.1 权威包：
   `MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.0.md` +
   `MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.1_AMENDMENT.md`；
3. `MODE_P_VNEXT_RELEASE_TASKS.json`；
4. `MODE_P_VNEXT_RELEASE_STATE.json`；
5. 本施工协议；
6. 当前 A 任务直接引用的旧 Evidence 和兼容输入。

以下文件降级为 `HISTORICAL_READ_ONLY`：

- `MODE_P_VNEXT_REPAIR_TASKS.json` / `MODE_P_VNEXT_REBUILD_STATE.json`；
- `MODE_P_VNEXT_DIRECTOR_V1_1_TASKS.json` /
  `MODE_P_VNEXT_DIRECTOR_V1_1_STATE.json`；
- `MODE_P_VNEXT_COMPLETION_TASKS.json` /
  `MODE_P_VNEXT_COMPLETION_STATE.json`；
- 旧 `MODE_P_VNEXT_REBUILD_LOOP.md` 和旧进度 Markdown。

不得删除或重写这些历史文件。新控制器通过
`MODE_P_VNEXT_RELEASE_STATE.json.legacy_imports` 记录其导入快照。

## 3. ReleaseLedger 文件职责

| 文件 | 职责 | 可否手改运行状态 |
|---|---|---|
| `MODE_P_VNEXT_RELEASE_TASKS.json` | A0–A10 依赖、范围、检查和固定命令 | 只允许 A0 正式迁移时修改 |
| `MODE_P_VNEXT_RELEASE_STATE.json` | 当前任务、完成证据、失效记录和发布上限 | 否 |
| `MODE_P_VNEXT_RELEASE.lock.json` | 当前唯一写锁 | 否 |
| `vnext_repair_evidence/A<n>_*.json` | 单任务事实摘要；编号必须带分隔符 | 可创建，但不能自行推进状态 |
| `vnext_owner_approvals/*.json` | 用户对已绑定媒体证据的独立批准 | 不属于任何 A 任务写入范围 |
| `release_control.py` | audit/next/claim/complete/fail/recover/invalidate/rebase/gates | 只有它能改变状态和锁 |

全项目只能存在一个活动的 v2 ReleaseLedger 写锁。旧 R/DDO/CPL lock 不得再用于
新施工；如果发现任何旧锁仍处于活动状态，A0 必须先 fail-closed 并人工审计。

## 4. 阶段与工作包

| 任务 | 阶段 | 结果 |
|---|---|---|
| A0 | BASELINE_REPAIR | 单一账本、旧队列历史化、v4 基线冻结 |
| A1 | ARCHITECTURE_MIGRATION | 唯一领域模型、Artifact 外壳和 24000 tick 时间基 |
| A2 | ARCHITECTURE_MIGRATION | 持久状态图、checkpoint、原子提交和失效 |
| A3 | ARCHITECTURE_MIGRATION | 单一 K1/K2、Snapshot、冲突与经验晋升 |
| A4 | ARCHITECTURE_MIGRATION | 声明式 StageSignature、预算门和 Provider 端口 |
| A5 | ARCHITECTURE_MIGRATION | Draft 与本地 Blocking/Timeline/VEC 组装 |
| A6 | ARCHITECTURE_MIGRATION | 单一 ProjectionAST 和双交付编译 |
| A7 | ARCHITECTURE_MIGRATION | Gate 0、独立 DP、修订路由与媒体证据边界 |
| A8 | TEXT_SHADOW | 顶层 CLI 的真实、可恢复文本 Shadow |
| A9 | HOLDOUT_EVALUATION | 冻结评测器与 PromptLab |
| A10 | MEDIA_EVIDENCE | 真实媒体、用户批准和回滚准备，不切生产 |

任务必须按依赖顺序完成。A10 完成最多使系统具有“提出独立生产切换方案”的资格，
不等于已经切换生产。

每个工作包对 `allowed_paths` 拥有独占写入所有权，任务之间不得存在目录、文件或
Evidence 通配符重叠。后续任务发现上游缺陷时，必须先失效后继任务，再回到真正拥有
该文件的工作包；不得在下游任务中顺手修改上游产物。A10 是验收工作包，没有实现
代码写权限。

### A3 规范知识权威边界

A3 独占 `knowledge_retriever.py`、`knowledge_flow.py` 与 `knowledge_snapshot.py` 的迁移写入权。后两者仅可保留为面向既有调用者的兼容适配入口；不得继续定义或生成第二个运行时 `KnowledgeSnapshot`、K1 或 K2 权威。A3 完成时，唯一可用于 vNext 运行、封存与回放的知识快照必须是 `mode_p_vnext.domain.knowledge.KnowledgeSnapshot`，并由 `ArtifactEnvelope` 绑定完整性。

## 5. 单轮施工流程

从 `01_调度器` 执行：

```powershell
python -m mode_p_vnext.release_control audit
python -m mode_p_vnext.release_control status
python -m mode_p_vnext.release_control next
```

只有 `next` 返回的唯一任务可以领取：

```powershell
python -m mode_p_vnext.release_control claim A0 --owner <unique-run-id>
```

领取成功后：

1. 保存返回的 token；CLI 只显示 token、owner、任务和 manifest 摘要，完整
   manifest 只保存在 lock；
2. 只读取该任务的 `spec_refs`、直接依赖 Evidence 和必要活动文件；
3. 只修改 `allowed_paths`；
4. 先增加失败测试或机械验证，再实现最小完整行为；
5. 运行 `required_checks` 和任务注册的回归；
6. 写入一个 `vnext_repair_evidence/A<id>_*.json`；
7. 只通过 `complete` 运行注册表中的固定命令并推进状态；
8. 停止，不在一轮中越过多个工作包。

Evidence 至少包含：

```json
{
  "task_id": "A0",
  "changed_paths": [],
  "checks": [
    {"name": "single_release_ledger", "exit_code": 0}
  ]
}
```

控制器会自行记录 Evidence 哈希、产物哈希、锁定输入哈希以及真实执行的
`verification_commands` 固定命令。
手写 `exit_code: 0` 不能替代控制器执行。

所有 UTF-8 文本哈希在计算前把 CRLF 规范化为 LF；二进制文件保持逐字节哈希。
这样同一 Git 内容在 Windows 与其他平台检出后不会产生伪漂移，同时媒体和其他二进制
证据的任何字节变化仍会被拒绝。

## 6. 失败、恢复与失效

- 实现或检查失败：写失败 Evidence，调用 `release_control fail`；
- 状态为 `IN_PROGRESS` 但进程崩溃：先 `audit`，再按审计结果
  `release_control recover`；
- 已完成任务的 Evidence、锁定架构或绑定产物漂移：
  `release_control invalidate`；
- 不得删除 lock 来“解锁”；
- 不得直接编辑 state 来跳过依赖；
- 不得因为旧 DDO/CPL 已通过某些测试，就在新账本中预勾 A 任务。

架构文件本身存在缺口时，不能把修改偷塞进任务表：当前 A0 必须先失败，在无活动锁、
无完成 A 任务时通过 `release_control rebase-architecture` 登记带哈希的新权威包，
然后重新领取 A0。不得直接编辑 state 伪造架构 rebase。

阶段待施工状态由下一任务决定，不再统一使用 `REPAIR_REQUIRED`：

```text
A0       -> BASELINE_REPAIR_REQUIRED
A1-A7    -> ARCHITECTURE_MIGRATION_REQUIRED
A8       -> TEXT_SHADOW_REQUIRED
A9       -> HOLDOUT_EVALUATION_REQUIRED
A10      -> MEDIA_EVIDENCE_REQUIRED
A10 媒体门后 -> OWNER_APPROVAL_REQUIRED（账本 gate 状态）
```

## 7. 架构施工硬边界

- `domain` 不得导入 Provider、文件系统、CLI、v4 或评测代码；
- 模型只输出 Draft，不输出最终 VEC、ID、哈希或可本地推导镜像；
- B1 Prompt 硬上限 12K 字符，B1 Draft Schema 硬上限 4.5K；
- Prompt 与 JSON Schema 分通道；传输能力不足时 fail-closed；
- Storyboard 与 Video 只能从一个 ProjectionAST 编译；
- 文本验证不能设置 `media_visual_acceptance=true`；
- A0–A7 禁止真实外部创作调用；
- A8 只允许注册范围内的隔离文本 Shadow；
- A10 的外部媒体和用户批准必须有真实证据；
- 任何 A 任务都不得修改 `/mode-p-pilot` 或默认生产入口。

### 7.1 A10 双门

A10 的普通 Evidence 不能自报人工门通过。完成前必须分别登记：

```powershell
python -m mode_p_vnext.release_control record-media-acceptance `
  --owner <A10-owner> --token <A10-token> --evidence <A10-media-evidence>
```

媒体 Evidence 必须在 `vnext_release_runs/A10/`，包含真实运行、帧证据、
v4/vNext 对照，并明确 `production_switch_authorized=false`。

用户查看该媒体证据后，必须亲自创建位于 `vnext_owner_approvals/` 的批准 Evidence，
再显式执行：

```powershell
python -m mode_p_vnext.release_control record-owner-approval `
  --approved-by <user-identity> --evidence <owner-approval-evidence>
```

施工 Agent 不得代替用户执行第二条命令。批准 Evidence 必须绑定当前媒体 Evidence
的 SHA-256；更换媒体 Evidence 会自动撤销旧批准。两个门通过仍不授权生产切换。

## 8. 当前迁移起点

新账本初始状态为：

```text
status = BASELINE_REPAIR_REQUIRED
next_task = A0
completed_tasks = []
production_entry = v4_unchanged
```

旧状态导入结果：

| 旧队列 | 导入状态 | 处理 |
|---|---|---|
| R | `REPAIR_REQUIRED`, next R0.2 | 历史证据，不继续选任务 |
| DDO | `DIRECTOR_TEXT_PIPELINE_IMPLEMENTED` | 历史实现，不授予 A 任务完成 |
| CPL | `REPAIR_REQUIRED`, next CPL-2 | 记录为架构边界失败，不恢复旧 B1 |

首个合法施工任务只能是 A0。

## 9. 完成报告

单任务完成只报告：

```text
TASK_COMPLETED: A<n>
NEXT_TASK: A<n+1> | NONE
PRODUCTION_ENTRY: v4_unchanged
EVIDENCE: <path + sha256>
```

全队列完成也不得报告“已生产上线”。只能报告：

```text
ARCHITECTURE_V2_IMPLEMENTED
OWNER_APPROVED_PREVIEW: true
PRODUCTION_SWITCH: NOT_PERFORMED
NEXT_EXPLICIT_STEP: separate production-switch proposal
```
