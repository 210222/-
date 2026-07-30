# 导演决策重构：施工完成审计矩阵

状态：`PRECONSTRUCTION_INCOMPLETE`  
当前可用表述上限：`PLANNED_PREVIEW`  
本矩阵不替代 [v1.1 施工方案](DIRECTOR_DECISION_REFACTOR_CONSTRUCTION_PLAN_V1.1.md)，而是把其完成条件映射到当前可验证证据。

| 完成条件 | 当前事实 | 证据 | 进入下一状态所需证明 |
| --- | --- | --- | --- |
| v1.1 目标、G-08 与不变量已冻结 | 已完成 | `DIRECTOR_DECISION_REFACTOR_CONSTRUCTION_PLAN_V1.1.md`、`DIRECTOR_REFACTOR_GOAL_LOCK_V1.1.json` | 任何修改均须用户批准并建立新版本；不得悄悄改写冻结文件。 |
| R1.1–R3.1 受控重验 | 已完成 | 控制器记录的 `R1.1_REVALIDATION_002` 至 `R3.1_REVALIDATION_002` | 后续源码/契约改动只可按依赖失效规则重验，不得把本记录当作未来代码证据。 |
| vNext 回归基线 | 通过但不足 | `728 passed, 416 subtests`，见 `R3.2_AUDIT_FAILURE_004.json` | 新安全边界、控制器和 DDO 实施后重跑全量套件与新增测试。 |
| 70 项证据闭合 | 未完成 | `task_evidence_ledger_v2.json`：62/70；V3.7、V9.5、V10.1–V10.6 未闭合 | 先受控实现/重验 V3.7、V9.5，再沿依赖闭合 V10.1–V10.5，最后进行全新的 V10.6 审计。 |
| 不可信文本安全边界 | 发现真实源码缺口，未授权施工 | `R3.2_SECURITY_BOUNDARY_CHANGE_REQUEST_001.md` | 新增控制器任务并允许修改 `knowledge_security`、事实、资产、外部反馈和对应测试；测试必须覆盖隔离、无泄漏、项目范围与不可自动改知识。 |
| R3.2 终态契约 | 未完成 | `R3.2_TERMINAL_STATE_CONTRACT_001.json` | 新控制器世代生成明确的 `BASELINE_REPAIR_AUDITED` 工件；不得伪造 `LOCAL_VNEXT_READY` 或把它当作 Director/生产就绪。 |
| v4 包边界 | 工作树检查失败，v4 源码未改 | `settings.local.json` 按用户要求保留；`R3.2_AUDIT_FAILURE_004.json` | 在隔离 staging 树验证包不含本地设置；原文件哈希前后相同。除非用户另行授权，不修改 v4 测试或本地文件。 |
| DDO 导演链 E0–R1 与 VEC | 尚未实施，且被冻结前置条件禁止 | v1.1 §4–§7、目标锁 `director_vnext_runtime_may_start_before_r3_2=false` | 在真实未知剧本上实现并验证 E0/S1/K1/B0/K2/B1/R1、BlockingCommit、DecisionRecord、VEC。 |
| 故事板/视频同源、参考/音色绑定 | 尚未以新导演链验证 | v1.1 §7–§8 | 同一 VEC 字段投影、AST 同源比较、角色音色/站位/道具/镜像不变量测试。 |
| 媒体视觉验收与归因 | 尚未开始 | v1.1 §9、§12 | 真实故事板与视频样本、FFmpeg 帧检查、人工/视觉审阅、OutcomeAttribution；文本审核最多 `TEXT_VALIDATED`。 |
| Shadow / Holdout / 生产切换 | 尚未开始 | v1.1 §11.2、§12 | DDO-6 小样、Holdout、回滚/并发/性能、用户明确生产批准。 |

## 强制执行顺序

```text
用户授权控制器世代重构
  -> 新安全边界任务（V3.7 / V9.5）
  -> 70 项依赖闭合与 V10.6 审计
  -> BASELINE_REPAIR_AUDITED（非生产、非 Director 运行时）
  -> 独立 DDO-0…DDO-6 队列
  -> Shadow / Holdout / 真实媒体视觉验收
  -> 用户明确批准生产切换
```

## 当前禁止项

- 不得以单元测试通过宣称真实故事板或视频已视觉验收。
- 不得把旧主连续性板、固定图片序号或上一段末帧重新引入运行时权威。
- 不得修改、移动或删除 `.claude/settings.local.json`。
- 不得在 R3.2 审计的允许范围中偷塞安全边界或 Director 源码施工。
- 不得启用 Shadow、外部生成、生产入口或 DDO 运行时。
