# MODE:P vNext 施工计划深度审查 v2.0

> 审查对象：架构 v2.0、首版 A0–A10 任务注册表、ReleaseLedger 控制器、
> `/mode-p-vnext-rebuild` 入口及旧 R/DDO/CPL 控制面
>
> 审查结论：首版 A0 证据失效；需以架构 v2.1 修订为新基线重新完成 A0

## 1. 审查方法

审查不是按文档标题比对，而是沿每条可执行路径检查：

1. 架构不变量能否映射到唯一工作包；
2. 工作包能否由机器状态唯一选择；
3. 写入范围是否会破坏已完成任务的 Artifact 哈希；
4. Evidence 是否能被错误任务的通配符接受；
5. 状态迁移是否表达真实阶段；
6. 旧入口能否绕过新账本；
7. 人工门是否能被普通任务 Evidence 自报；
8. A10 是否可能在未批准时完成或切换生产；
9. claim/complete/audit 的失败路径是否关闭；
10. v4 入口与外部调用边界是否保持不变。

## 2. 发现与修复

| ID | 严重度 | 发现 | 风险 | 修复 |
|---|---|---|---|---|
| F-01 | Critical | A1/A2/A4/A7/A8/A10 的 `allowed_paths` 存在目录和文件重叠 | 下游合法修改会使上游 Evidence 漂移，形成无法推进或错误失效 | v2.1 规定独占所有权；任务表拆分为两两不重叠路径 |
| F-02 | High | 控制器把所有非终态硬编码为 `REPAIR_REQUIRED` | 状态不能表达架构迁移、Shadow、Holdout、媒体和用户批准 | 每个任务声明 `pending_status`；迁移由下一任务阶段决定 |
| F-03 | High | `A1*.json` 会匹配 `A10...json` | A10 Evidence 可能被 A1 误接纳 | 全部改为 `A<n>_*.json`，并加入跨任务反匹配测试 |
| F-04 | Critical | A10 把媒体证据与用户批准当作普通 required check | 施工者可在 Evidence 中自报用户批准 | 两个独立门写入状态并绑定实时文件哈希；A10 complete 机械拒绝缺门 |
| F-05 | High | A10 拥有媒体适配器、验证节点等实现写权限 | 验收任务可能一边改实现一边批准自身 | A10 只拥有测试、运行证据、运维文档和 A10 Evidence |
| F-06 | High | A7 被归入 `TEXT_SHADOW` | 实现媒体边界被误报为已运行文本 Shadow | A7 改为 `ARCHITECTURE_MIGRATION`，A8 才是 TEXT_SHADOW |
| F-07 | High | 旧 R/DDO/CPL 只在文档中历史化，代码仍可 `next/claim` | 操作者或自动化可绕过新账本 | 旧控制器在 ReleaseLedger 生效后拒绝任务选择与推进 |
| F-08 | Medium | claim CLI 打印约 1,500 个文件的完整 manifest | 造成会话膨胀，掩盖 token、任务和审计结果 | 完整 manifest 只存 lock；CLI 返回六个摘要字段 |
| F-09 | High | 根 `CLAUDE.md` 仍把旧 repair queue 指定为 vNext 权威 | 新命令入口与根规则相互冲突 | 根规则改指向架构 v2.1 与 ReleaseLedger |
| F-10 | High | 架构输入只锁定 v2.0 单文件 | 修订可能不被任务证据绑定 | 每个 A 任务同时锁定 v2.0 与 v2.1 修订哈希 |
| F-11 | Medium | A0 首版完成后才发现上述问题 | 旧 A0 Evidence 仍可能被误认为有效 | 通过 `invalidate` 保留旧证据，再用失败 Evidence 关闭重领 |
| F-12 | High | 架构变更没有机器 rebase 路径 | 容易直接手改 state 或继续用旧哈希 | 新增仅在无锁、无完成任务时可用的架构 rebase 命令 |
| F-13 | High | 原始字节哈希会把 Git 的 LF/CRLF 检出差异误判为产物漂移 | 推送后在 Windows 重新 clone 即可能让已完成 A0 失效 | UTF-8 文本先规范化 CRLF 为 LF；二进制继续逐字节哈希，并加入跨换行回归 |

## 3. A0–A10 适配矩阵

| 任务 | 架构职责 | 独占产物边界 | 阶段出口 |
|---|---|---|---|
| A0 | ReleaseLedger、基线、旧队列历史化 | 控制器、控制测试、入口、施工文档与 A0 Evidence | `ARCHITECTURE_MIGRATION_REQUIRED` |
| A1 | 领域 Artifact、Draft、ID、24000 tick | `domain/**`、`compat/**` | `ARCHITECTURE_MIGRATION_REQUIRED` |
| A2 | 状态图、checkpoint、事务和失效 | 状态/运行时端口与 A2 测试 | `ARCHITECTURE_MIGRATION_REQUIRED` |
| A3 | K1/K2、Snapshot、冲突与晋升 | `knowledge_retriever.py` 与 A3 测试 | `ARCHITECTURE_MIGRATION_REQUIRED` |
| A4 | StageSignature、Prompt 预算、Provider | `prompts/**`、Provider port/adapter | `ARCHITECTURE_MIGRATION_REQUIRED` |
| A5 | Blocking、Timeline、VEC 本地组装 | 三个 assembler 与 A5 测试 | `ARCHITECTURE_MIGRATION_REQUIRED` |
| A6 | 单一 ProjectionAST 与双交付编译 | projection/delivery 与 A6 测试 | `ARCHITECTURE_MIGRATION_REQUIRED` |
| A7 | Gate、独立 DP、Revision、媒体端口 | gate/router/verification/media ports | `TEXT_SHADOW_REQUIRED` |
| A8 | 完整可恢复文本 Shadow | episode/scene nodes、storage、CLI、A8 runs | `HOLDOUT_EVALUATION_REQUIRED` |
| A9 | 冻结评测器与 PromptLab | `evaluation/**` | `MEDIA_EVIDENCE_REQUIRED` |
| A10 | 媒体、帧证据、回滚和用户批准 | A10 tests/runs/operations/evidence；无实现代码 | 双门后进入提案资格 |

## 4. 路径所有权判定

路径冲突按以下规则机械判定：

- 完全相同的模式冲突；
- `x/**` 与 `x` 或 `x/...` 冲突；
- 一个 glob 能匹配另一任务的精确文件时冲突；
- Evidence 使用样例文件名进行交叉匹配，任何非本任务匹配都失败。

测试必须遍历全部任务两两比较，而不是只检查已知冲突列表。

## 5. A10 双门攻击面审查

已拒绝以下伪通过路径：

- 在 A10 Evidence 中手写两个 check 为 0；
- 只设置布尔值、不保存证据路径；
- 保存路径后修改证据文件；
- 用户批准绑定旧媒体 Evidence 后替换媒体 Evidence；
- 在 owner approval 中夹带生产切换授权；
- 用 A10 验收任务修改媒体适配器后立即自验；
- A10 全绿后自动切换生产。

可接受边界：

- MEDIA Evidence 由 A10 真实运行产生，并由控制器登记哈希；
- OWNER Evidence 位于 A 任务无写权限的独立目录，明确绑定 MEDIA 哈希；
- 控制器复算两个文件哈希；
- 本地身份仍由明确用户操作负责，代码不伪称具备外部身份认证。

## 6. 遗留风险与处理

| 风险 | 处理 |
|---|---|
| 本地用户身份不能由普通文件系统证明 | 明确保留人机批准边界；禁止 Agent 代调 owner 命令；若未来接入签名身份再升级 |
| A1 冻结 Schema 后发现接口缺陷 | 按反向依赖顺序失效，回到拥有该文件的工作包，不允许下游偷改 |
| 工作区已有大量无关未跟踪文件 | claim manifest 记录基线；complete 只阻止本轮新增/修改未声明文件，不认领既有用户文件 |
| 旧控制器存在历史陈旧锁 | 保留旧 `fail/recover`，但禁止继续 `next/claim/complete/invalidate` |
| v2.0 与 v2.1 被单独读取 | README、根入口、任务表和 state 都指向“权威包”，并锁定两个哈希 |

## 7. 通过条件

A0 只有在以下事实同时成立时才能重新完成：

1. v2.0 + v2.1 哈希均被任务表和 state 绑定；
2. 路径所有权测试对 A0–A10 全量通过；
3. 阶段状态迁移测试通过；
4. 旧控制器选择/推进被代码拒绝；
5. claim 输出有界；
6. A10 双门缺失、漂移和越权测试通过；
7. 根入口、命令和 README 只把 ReleaseLedger 作为 vNext 权威；
8. v4 活动入口回归通过；
9. 旧通用控制器回归通过；
10. 最终 A0 Evidence 与控制器实际执行结果一致。
