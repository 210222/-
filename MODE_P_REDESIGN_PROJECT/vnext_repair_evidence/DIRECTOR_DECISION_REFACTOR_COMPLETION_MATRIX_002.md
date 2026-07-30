# 导演决策重构：完成审计矩阵 v2

状态：`TEXT_PIPELINE_IMPLEMENTED_COMPLETION_EVIDENCE_OPEN`  
当前可用表述上限：`PLANNED_PREVIEW`  
审计权威：

- `DIRECTOR_DECISION_REFACTOR_CONSTRUCTION_PLAN.md` §17
- `DIRECTOR_DECISION_REFACTOR_CONSTRUCTION_PLAN_V1.1.md` §12
- 当前工作树、控制器状态和可重复测试结果

本矩阵替代 `DIRECTOR_DECISION_REFACTOR_COMPLETION_MATRIX_001.md` 的施工前快照；旧文件只读保留。

## 一、11 项完成条件

| # | 完成条件 | 当前判定 | 当前证据 | 未闭合证据 |
|---|---|---|---|---|
| 1 | 真实 Director 在未知剧本完成 Phase A/B | 未完成 | `DirectorAgent` 接口、fixture 顺序测试 | 真实 DeepSeek Provider、未知 Holdout 的 E0/S1/K1/B0/K2/B1/R1 调用记录和合法 VEC |
| 2 | 知识有选择、冲突裁决和适用性证据 | 部分完成 | K1/K2 预算、适用性、禁用条件、冲突卡暴露测试 | `ConflictDecisionRecord`、真实胶囊目录、no-knowledge/K1-only/K1+K2 消融结果 |
| 3 | VEC 是唯一创意真源 | 文本层完成 | BlockingCommit 前置、DecisionRecord、VEC fail-closed | 真实 Director 输出而非 fixture 手工 VEC |
| 4 | 无主板、无固定图片 2/3/4、无末帧强制首帧 | 新链完成 | 新命名空间无主板依赖；泄漏扫描拒绝旧语义 | REG-13/14 的独立诊断码、fixture 和 mutation 证据 |
| 5 | Storyboard/Video 由同一 VEC 机械编译 | 文本层完成 | 双 AST、contract fingerprint、node provenance、字段同源测试 | Golden 反向回放和真实媒体预测验证 |
| 6 | 时间、引用、音色、服装、站位、视线、道具完整 | 文本层完成 | VEC 字段、Reference/Voice binding、prop/mirror/axis 约束 | 真实故事板/视频中的视觉与声音验收 |
| 7 | 18 项历史问题全部回归通过 | 部分完成 | 已覆盖 global/hash/旧图片序号/下一段/负向名词/重复对白等 | REG-01～18 逐项测试、fixture、诊断码、修复层和媒体责任表 |
| 8 | Golden、未知 Holdout、知识消融通过 | 未完成 | 旧 vNext Golden 设施；新冻结 Holdout 数据结构 | vNext.1 VEC Golden 回放、未知 Holdout 真实运行、消融和模板复制检查 |
| 9 | 实际故事板与视频通过硬不变量和阈值 | 未完成 | Render Run Record 和分 Segment FFmpeg 抽帧计划 | 七类真实媒体样本、帧检、视觉评分、阈值校准和用户验收 |
| 10 | 性能、崩溃恢复、并发、回滚、生产隔离通过 | 部分完成 | R2.1/R3.1 基础设施；本地编译热缓存测试；生产入口未变 | 新 Director 链 P95、调用数、冷调用下降 40%、热修订下降 70%、链路恢复/并发/回滚演练 |
| 11 | 用户明确批准生产切换 | 未完成 | OwnerApprovalGate fail-closed；生产入口仍为 v4 | 实际媒体通过后由用户明确给出批准；批准前不得切换 |

## 二、DeepSeek 权限边界

DeepSeek 是文本模型，只允许审查：

- 剧本、SceneIntent、DecisionPacket、BlockingCommit、DecisionRecord 和 VEC 的逻辑；
- Storyboard/Video AST 同源；
- 对白去重、音色/引用职责、局部时间、Prompt 泄漏和可执行性。

DeepSeek 的最高结论是 `TEXT_VALIDATED`，不得裁决：

- 实际人物身份、服装、数量；
- 镜像、轴线、站位、视线；
- 手部、手机持手、正反面和朝向；
- 实际构图、运镜、光影、表演；
- 实际故事板是否预示视频。

上述视觉结果只能由用户或具备视觉能力的评估器结合实际媒体与 FFmpeg 帧完成。

## 三、收尾执行顺序

```text
CPL-0 当前完成审计与独立收尾队列
  → CPL-1 知识来源、适用性、冲突裁决
  → CPL-2 真实 DeepSeek Provider 与未知剧本文本 Shadow
  → CPL-3 REG-01～REG-18 逐项回归与 mutation
  → CPL-4 Golden/Holdout/消融/性能/恢复/回滚
  → CPL-5 真实媒体、视觉验收、阈值校准和用户批准
```

在 CPL-5 之前不得把 `PLANNED_PREVIEW`、`TEXT_VALIDATED` 或
`DIRECTOR_TEXT_PIPELINE_IMPLEMENTED` 描述为重构全部完成。
