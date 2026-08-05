# TASK-001：当前导演知识资产盘点

## 1. 任务目标

建立当前 MODE:P 的导演知识、选择机制、经验、失败反馈、测试和运行时依赖的事实地图。
本任务只盘点和分类，不批量改写、不创建生产技能、不修改运行时。

## 2. 必须先读取

1. `CLAUDE.md`
2. `MODE_P_MIGRATION.md`
3. `03_知识库/书籍蒸馏草案_v1.0.md`
4. `02_Agent/director_agent.md`
5. `02_Agent/dp_agent.md`
6. `01_调度器/mode_p/knowledge/knowledge_index.json`
7. `01_调度器/mode_p/knowledge/core/`
8. `01_调度器/mode_p/knowledge/capsules/`
9. `05_修复与反馈/`
10. `05_项目经验/`
11. `06_测试/`
12. 与知识候选选择和验证直接相关的脚本

对于目录，先列目录和元数据，再按抽样策略读取正文。不得默认读取所有大文件。

## 3. 允许写入

```text
07_档案/导演决策系统改造方案/work/phase_0_inventory/
07_档案/导演决策系统改造方案/project_state.json
```

## 4. 禁止写入

```text
01_调度器/
02_Agent/
03_知识库/
04_共享/
05_修复与反馈/
05_项目经验/
06_测试/
MODE_P_MIGRATION.md
CLAUDE.md
```

## 5. 执行步骤

### Step 1：生产读取链

确认当前 Director 实际读取哪些核心知识、胶囊、经验和索引。输出：

- 路径；
- 调用者；
- 加载条件；
- 是否生产真源；
- 是否可能影响镜头决策；
- 是否为历史或隔离资产。

### Step 2：资产清单

为每项知识建立记录：

```json
{
  "asset_id": "",
  "path": "",
  "format": "md|json|yaml|py|other",
  "asset_type": "core|capsule|case|experience|failure|test|index|runtime",
  "status": "production|candidate|historical|unknown",
  "source_traceability": "complete|partial|missing",
  "structure_level": "summary|principle|rule|skill|case|failure|mixed",
  "has_trigger_conditions": false,
  "has_do_not_use_conditions": false,
  "has_procedure": false,
  "has_failure_signs": false,
  "has_repair_strategy": false,
  "has_examples": false,
  "used_by": [],
  "notes": []
}
```

### Step 3：抽样正文审查

采用分层抽样：

- 所有 core；
- 每类 capsule 至少 3 个；
- 所有索引；
- 经验和失败反馈每类至少 5 个；
- 与正反打、过肩、场次节拍、人物调度、连续性有关的文件优先；
- 测试中与 Director/DP/knowledge 相关的测试优先。

不得根据文件名直接判断正文能力。

### Step 4：缺口分类

至少检查：

- 只是摘要，没有触发条件；
- 只有技巧，没有戏剧问题；
- 没有禁用条件；
- 没有反例；
- 没有修复策略；
- 来源缺失；
- 规则重复或冲突；
- 检索只依赖语义相似；
- 无法追溯到场次/节拍；
- 经验不能进入后续决策；
- 测试只检查格式，不检查导演质量；
- 当前 Director 已有能力与新方案重复。

### Step 5：新旧映射

把现有资产映射到：

- Principle
- DecisionRule
- PlanningSkill
- FunctionalSkill
- AtomicSkill
- FailurePattern
- RepairStrategy
- Case
- EvaluationRule
- ConflictRule
- ArchiveOnly
- NeedsManualReview

### Step 6：试点选择

选择三类试点来源，每类给出：

- 候选文件或章节；
- 为什么具有代表性；
- 预计可转化的技能类型；
- 风险；
- 人工审核重点；
- 成功标准。

### Step 7：更新状态

完成产物后更新 `project_state.json`：

- `TASK-001` 状态；
- 实际读取文件数；
- 资产记录数；
- 未解析资产数；
- 阻塞项；
- 建议的 `TASK-002`；
- 本轮验证结果。

## 6. 必须产出

```text
work/phase_0_inventory/
├── knowledge_inventory.json
├── knowledge_gap_report.md
├── migration_map.json
├── pilot_selection.md
└── task_001_report.md
```

## 7. 验收标准

- 所有结论可追溯到真实路径；
- 区分生产、候选、历史和未知；
- 不遗漏生产实际读取的 core、capsules 和 index；
- 至少完成规定的分层抽样；
- 明确现有 Director 已经具备的能力，避免重复建设；
- 没有修改任何禁止路径；
- JSON 可解析；
- 报告明确事实、推断和未知；
- 下一任务是最小可验证工作单元，不直接进入批量迁移。

## 8. 停止条件

出现以下任一情况时停止并报告：

- 仓库治理文件冲突；
- 生产读取链无法确定；
- 目录过大且缺少安全抽样边界；
- 关键文件不可读取；
- 发现当前分支已有同类迁移正在进行；
- 需要修改禁止路径才能继续。

禁止通过猜测绕过阻塞。
