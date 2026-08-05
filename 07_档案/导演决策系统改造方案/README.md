# 导演决策系统知识库改造项目包

状态：`PROPOSAL / 非运行时`  
版本：`0.1.0`  
创建日期：`2026-08-05`

## 1. 这个项目包解决什么问题

当前 MODE:P 已经拥有持续分集 Director、DP 审查、Visual Bible、Continuity Ledger 和
`DIRECTOR_MASTER.md` 单一设计真源。当前主要缺口不是“再增加镜头术语”，而是将现有导演书籍
知识胶囊改造成可以被 LLM 条件化调用、反证、评价和持续进化的导演决策资产。

本项目的目标是建立以下闭环：

```text
完整剧本事实
→ 本集导演命题
→ 场次功能
→ 戏剧节拍变化
→ 人物调度与观众视点
→ 摄影与剪辑执行
→ Director Critic / DP
→ 失败定位与经验回写
→ 下一轮知识与决策改进
```

## 2. 与现有 MODE:P 的关系

本项目包位于 `07_档案`，默认不参与运行时加载，不修改以下当前有效真源：

- `01_调度器/dispatcher_v5.0.md`
- `01_调度器/mode_p/`
- `02_Agent/director_agent.md`
- `02_Agent/dp_agent.md`
- `04_共享/CONSTITUTION.md`
- `04_共享/canvas_runtime.md`
- `04_共享/shared_agent_runtime.md`

在 Phase 0—Phase 2 完成前，禁止把本项目中的 Schema、Prompt 或候选知识直接加入生产索引。
只有通过基准测试和人工复核的资产，才允许通过单独 PR 接入当前运行时。

## 2.1 与现有《书籍蒸馏草案 v1.0》的关系

仓库已经存在 `03_知识库/书籍蒸馏草案_v1.0.md`，其中提出 RIA-TV++ 蒸馏、三重验证、
诱饵测试、胶囊安装以及“全剧情绪弧 → 场景张力 → 镜头选择”的初步思路。

本项目包不否定该草案，而是把它升级为可持续执行工程：

- 将四级链扩展为可追溯的五层导演金字塔；
- 明确归纳与演绎分别在哪些节点使用；
- 增加技能、状态、失败模式和项目状态 Schema；
- 增加单次运行协议、任务队列、停止条件和完成证据；
- 增加基准测试、反证、错误回退和生产接入隔离；
- 把“直接写胶囊并注册索引”改为“候选区 → 试点 → 基准 → 人工复核 → 独立接入 PR”。

`书籍蒸馏草案_v1.0.md` 是 Phase 0 必须盘点和映射的既有设计输入，不应被重复改写或直接覆盖。

## 3. 文件索引

| 文件 | 用途 |
|---|---|
| `GOAL.md` | 项目长期目标、金字塔层级和不可违反的原则 |
| `MASTER_SYSTEM_PROMPT.md` | 可直接交给 LLM 的持续执行系统提示词 |
| `EXECUTION_PLAN.md` | Phase 0—8 的执行步骤、产物、质量门和停止条件 |
| `TASK_001_ASSET_INVENTORY.md` | 第一轮可直接执行的资产盘点任务 |
| `ACCEPTANCE_TESTS.md` | 方案和未来实现的验收测试 |
| `project_state.json` | 跨运行恢复状态的唯一项目状态入口 |
| `schemas/director_skill.schema.yaml` | 导演技能资产契约 |
| `schemas/director_state.schema.json` | 剧集、场次、节拍、镜头决策状态契约 |
| `schemas/project_state.schema.json` | 项目进度状态契约 |
| `schemas/failure_pattern.schema.yaml` | 失败模式与修复策略契约 |

## 4. 第一次运行

把 `MASTER_SYSTEM_PROMPT.md` 作为系统指令，让 LLM 依次读取：

1. 本目录的 `GOAL.md`
2. 本目录的 `EXECUTION_PLAN.md`
3. 本目录的 `project_state.json`
4. 本目录的 `TASK_001_ASSET_INVENTORY.md`
5. 仓库根目录 `CLAUDE.md`
6. 当前 MODE:P 的有效文件和知识目录

第一轮只执行资产盘点，不批量改写知识，不修改生产索引，不修改 Director 或 Dispatcher。

预期第一轮产物：

```text
work/phase_0_inventory/
├── knowledge_inventory.json
├── knowledge_gap_report.md
├── migration_map.json
├── pilot_selection.md
└── task_001_report.md
```

并更新本目录的 `project_state.json`。

## 5. 持续执行方式

每次运行只能选择一个最小可验证工作单元：

```text
读取 project_state
→ 选择 next_task
→ 声明输入和完成标准
→ 执行
→ 运行质量门
→ 保存产物
→ 更新 project_state
→ 停止
```

禁止在一次运行中从资产盘点直接跳到批量蒸馏或模型训练。

## 6. 成功判据

知识库改造不是以知识条目数量衡量，而以以下能力衡量：

- Agent 能先说明场次为什么存在，再设计镜头；
- 对话场景不再默认退化为正反打和过肩覆盖；
- 每个镜头能够追溯到节拍变化、场次功能和本集导演命题；
- 失败可以定位到剧本理解、场次、节拍、调度、摄影、剪辑或连续性层；
- 用户反馈可以变成结构化失败经验，并影响后续场次；
- 逐秒推演只用于动作与生成执行，不代替导演层面的戏剧判断；
- 经过验证的知识可以稳定接入现有 Director，而不破坏 MODE:P 当前生产链。
