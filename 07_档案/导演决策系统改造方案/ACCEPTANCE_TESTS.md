# 验收测试

## A. 项目包自身

### A1. 文件完整性

- [ ] README 能指向全部文件；
- [ ] `project_state.json` 通过 Schema；
- [ ] 两个 JSON Schema 可解析；
- [ ] 两个 YAML Schema 可解析；
- [ ] 第一任务的允许和禁止路径明确；
- [ ] 方案不要求修改当前生产真源。

### A2. 可持续执行

给一个全新 LLM 会话，只提供仓库访问和 `MASTER_SYSTEM_PROMPT.md`，应能：

1. 读取状态；
2. 找到 `TASK-001`；
3. 声明范围；
4. 完成一次资产盘点；
5. 生成规定产物；
6. 更新状态；
7. 停止，不自动批量迁移。

失败条件：

- 从头重新规划而忽略状态；
- 修改生产目录；
- 未读取文件就判断内容；
- 只输出聊天报告而不生成产物；
- 任务结束后继续执行下一 Phase。

## B. 未来知识资产

### B1. 技能可执行性

随机选择一条技能，验证是否回答：

- 它解决什么导演问题？
- 何时触发？
- 何时禁止？
- 需要什么输入？
- 执行哪些步骤？
- 如何选择候选？
- 怎样发现失败？
- 回退到哪里修复？
- 来源是什么？
- 有哪些正确、错误和边界案例？

任一核心问题无法回答，不得晋升为 `verified`。

### B2. 反模板测试

给出四个剧本表面相似、戏剧功能不同的对话场景。系统不得因都包含对话而给出同一正反打模板。

检查：

- 场次功能是否不同；
- 观众状态是否不同；
- 调度是否不同；
- 镜头策略是否由状态变化触发；
- 候选方案是否实质不同。

### B3. 反证测试

把关键事实从剧本中删除或反转，系统应降低置信度或改变导演结论，而不是维持原方案。

## C. 导演决策链

### C1. 金字塔追溯

每个重要镜头必须有：

```text
shot_id
→ beat_id
→ state_change
→ scene_function
→ episode_directive
```

追溯缺失率目标：试点阶段 `< 10%`，生产接入前 `< 2%`。

### C2. 归纳质量

本集命题和场次功能至少有两项独立证据，并列出备选解释和反证。

### C3. 演绎质量

每个关键镜头记录：

- 上层目标；
- 使用规则；
- 触发事实；
- 例外检查；
- 单一执行决定。

## D. 失败模式

第一批至少覆盖：

- `DialogueCoverageCollapse`
- `OverShoulderDependency`
- `DialogueTurnCutting`
- `CameraMovementWithoutCause`
- `ShotVarietyForItsOwnSake`
- `BlockingVacuum`
- `EmotionalFlatline`
- `PowerBlindness`
- `InformationLeak`
- `ShotRedundancy`
- `PrematureCloseUp`
- `ExhaustedEscalation`
- `ContinuityDrift`
- `SecondBySecondMechanicalPlanning`
- `LocalOptimization`

每个失败模式必须能指出：

- 可观察症状；
- 可能根因；
- 首次错误层级；
- 检测方法；
- 修复步骤；
- 不应触发的边界情况。

## E. 基准对比

与当前基线对比，生产接入前至少满足：

- 镜头追溯完整率提升；
- 无动机切镜率下降；
- 正反打/过肩默认率下降；
- 调度变化覆盖率提升；
- 信息泄露和连续性错误不增加；
- 人工偏好胜率高于基线；
- 运行成本在预先规定预算内。

任何“电影感更强”之类无法测量的描述不能代替以上指标。
