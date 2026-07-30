# MODE:P 导演决策重构变更记录

## 2026-07-29 — v1.1 冻结前施工范围

- 类型：目标与验收合同修正；不是运行时实现完成记录。
- 原因：v1.0 已经包含 `blocking-first`、两阶段检索和同源 VEC 原则，但没有把它们连成一个可失败、
  可追溯的 Director 决策链。用户指出这一缺口后，必须先补全施工目标，不能在局部修复中偏移。
- 新施工方案：[DIRECTOR_DECISION_REFACTOR_CONSTRUCTION_PLAN_V1.1.md](DIRECTOR_DECISION_REFACTOR_CONSTRUCTION_PLAN_V1.1.md)
  - SHA-256：`6309b31867d74065f4297f57f7a2fb5cee41f933aec0e149a9127466ef8338ce`
- 新机器目标锁：[DIRECTOR_REFACTOR_GOAL_LOCK_V1.1.json](DIRECTOR_REFACTOR_GOAL_LOCK_V1.1.json)
  - SHA-256：`0bd185474534d83366058fe1b3a2acc10ff347db8370246b7d9765ea57a281dc`
- 新增：`G-08` 和 `INV-DIR-01` 至 `INV-DIR-07`；固定 E0/S1/K1/B0/K2/B1/R1 链、
  `BlockingCommit` 前置、候选/约束锁、知识置信度门控、无默认转场、只提问的双模式审查与媒体归因。
- 保留：v4 入口、R0–R3 历史证据、无主板/无固定图片槽位、文本与视觉验收的边界。
- 不授予：DDO 实现完成、Shadow/Pilot/Canary/Production、实际故事板或视频视觉通过。
- 先决条件：R3.2 必须先解决基线 cohort、70 项证据和机器终态合同；之后才能创建独立 DDO 队列。
