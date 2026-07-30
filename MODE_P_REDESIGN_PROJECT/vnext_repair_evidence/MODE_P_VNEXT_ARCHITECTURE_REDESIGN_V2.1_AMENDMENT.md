# MODE:P vNext 架构 v2.1 规范性修订案

> 状态：规范性（Normative）
>
> 生效范围：MODE:P vNext 架构迁移与发布控制面
>
> 基础架构：
> `MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.0.md`
>
> 基础架构 SHA-256：
> `44a44931444299f511ba4d5e5b931c99e07511e3ee6d922bf307bcacde80f8cf`
>
> 版本：2.1

本修订案不重写 v2.0 的导演双循环、Artifact、时间基、Prompt 编译、
Projection、知识、验证和生产隔离设计。它只修复施工审查发现的控制语义缺口。
本修订案与 v2.0 合称“架构 v2.1 权威包”；两者冲突时以本修订案为准。

## ADR-015：架构与施工方案的权威关系

权威顺序固定为：

1. 用户当前、明确且合法的目标与生产安全边界；
2. 经版本化并锁定哈希的架构权威包；
3. 从架构生成的机器任务注册表；
4. 施工协议与命令入口；
5. R、DDO、CPL 及其他旧实现和旧 Evidence。

施工方案是架构的可执行投影，不能反向覆盖架构。发现不一致时：

- 若施工方案偏离已明确架构，修施工方案；
- 若架构存在歧义、遗漏或自相矛盾，当前任务必须失败关闭；
- 先发布带版本和哈希的新架构修订，再重生成施工方案；
- 禁止在未修订架构时用控制器特例掩盖规范缺口。

## ADR-016：工作包拥有独占写入所有权

每个 A 工作包必须拥有互不重叠的 `allowed_paths`。目录通配符、精确文件和
Evidence 通配符都参与重叠检查。

- 已完成工作包的绑定产物保持不可变；
- 后续工作包只能消费这些产物，不能修改；
- 后续验收发现上游产物缺陷时，必须按依赖图先失效后继任务，再失效并重做真正
  拥有该文件的任务；
- A10 是验收与证据工作包，不获得实现代码写权限；
- 为避免接口在下游才被迫改写，A1 必须冻结领域 Schema，A2 必须冻结状态与恢复
  端口，A4 必须冻结 Provider 端口，之后才能推进依赖任务。

机器审计必须拒绝路径所有权重叠。`A1_*.json`、`A10_*.json` 等 Evidence
模式必须包含任务编号后的分隔符，不能使用会跨任务匹配的 `A1*.json`。

## ADR-017：状态由下一工作包阶段决定

非终态不得统一写成 `REPAIR_REQUIRED`。当前任务完成、失败、失效或恢复后，
ReleaseLedger 的待施工状态由需要执行的工作包声明：

| 待执行工作包 | 状态 |
|---|---|
| A0 | `BASELINE_REPAIR_REQUIRED` |
| A1–A7 | `ARCHITECTURE_MIGRATION_REQUIRED` |
| A8 | `TEXT_SHADOW_REQUIRED` |
| A9 | `HOLDOUT_EVALUATION_REQUIRED` |
| A10 媒体门前 | `MEDIA_EVIDENCE_REQUIRED` |
| A10 媒体门通过、用户门未通过 | `OWNER_APPROVAL_REQUIRED` |
| A10 完成 | `PRODUCTION_SWITCH_PROPOSAL_ELIGIBLE` |

`IN_PROGRESS` 只表示唯一写锁已被领取，不代表阶段验收通过。

## ADR-018：A10 是一个工作包、两个独立人工门

A10 保持单一工作包，以避免新增并列发布账本；但它内部包含有序、独立的两个门：

1. **MEDIA_EVIDENCE**：真实媒体小样、帧级证据、v4/vNext 对照和归因通过；
2. **OWNER_APPROVAL**：用户在查看已绑定的媒体证据后明确批准预览结果。

控制要求：

- 媒体门 Evidence 必须位于 A10 运行目录、可复算 SHA-256，并由控制器写入账本；
- 用户批准 Evidence 必须位于施工任务无写权限的独立批准目录；
- 用户批准必须绑定已登记媒体 Evidence 的 SHA-256；
- A10 自身 Evidence 中写入 `owner_approval_explicit: 0` 之类的检查结果，不足以
  通过用户门；
- A10 `complete` 必须机械验证两个门、证据文件和实时哈希；
- 新媒体 Evidence 会使旧用户批准自动失效；
- 任一门都不得设置 `production_switch_authorized=true`。

本地控制器无法凭空证明操作者的现实身份，因此用户批准仍是明确的人机操作边界。
施工 Agent 不得代替用户调用用户批准命令；控制器负责保证“没有独立、哈希绑定的
批准记录就无法完成 A10”。

## ADR-019：旧控制面在代码层失去任务选择权

当项目根存在 `authority=SOLE_VNEXT_CONSTRUCTION_LEDGER` 的发布状态时：

- R、DDO、CPL 控制器的 `next`、`claim`、`complete`、`invalidate` 必须失败；
- 旧状态和 `audit/status` 保持可读；
- 为释放既有陈旧锁，旧控制器的 `fail/recover` 可继续使用；
- 只有 `mode_p_vnext.release_control` 能选择或完成新的 A 工作包。

文档中的“历史只读”必须由代码门实现，不能仅依赖操作者记忆。

## ADR-020：控制输出有界

claim-time 全工作区清单继续完整保存在独占 lock 中，用于完成时计算真实增量；
CLI 只返回以下摘要：

- `task_id`
- `owner`
- `token`
- `acquired_at`
- `manifest_file_count`
- `manifest_sha256`

状态、审计和完成输出可以包含必要证据，但禁止把千级文件清单打印到会话上下文。

## v2.1 工作包阶段校正

- A0：控制面与架构基线治理；
- A1–A7：`ARCHITECTURE_MIGRATION`；
- A8：首次完整 `TEXT_SHADOW`；
- A9：`HOLDOUT_EVALUATION`；
- A10：`MEDIA_EVIDENCE`，内部顺序进入 `OWNER_APPROVAL`；
- 生产切换仍是 A0–A10 之外、需要用户另行授权的独立任务。

其中 A7 负责实现确定性 Gate、独立 DP、Revision 路由和媒体端口边界，它尚未运行
完整文本 Shadow，因此 v2.0 中把 A7 隐含归入 TEXT_SHADOW 的解释被本修订案废止。

## 架构变更协议

架构权威包中的每个文件必须由任务注册表锁定路径和 SHA-256。任何文件漂移：

1. 已完成任务的审计立即失败；
2. 不能继续领取后继任务；
3. 必须形成架构变更 Evidence；
4. 在无活动锁、无有效后继完成记录时，通过 ReleaseLedger 的架构 rebase 操作
   登记新版本；
5. 重新完成 A0 后才可继续。

禁止直接编辑机器状态伪造 rebase。

## v2.1 验收不变量

1. 架构权威包的所有文件哈希均被每个 A 任务锁定。
2. A0–A10 的 `allowed_paths` 两两不重叠。
3. 阶段状态与下一任务一致。
4. 旧控制器不能选择或推进任务。
5. A10 没有实现代码写权限。
6. A10 未登记两个独立门时不能完成。
7. A10 完成后仍为 `v4_unchanged`，且生产切换未授权。
8. claim 输出不包含 `claim_manifest`，lock 内仍保留完整清单。

