# MODE:P 深读进度日志

> 用途：让重构前的事实核查过程可追踪。本文件不属于正式 MODE:P 管道，不修改任何现行 Agent 或调度器。
> 开始日期：2026-07-15

## 工作状态

| 阶段 | 状态 | 当前结论 |
|---|---|---|
| 调度器与版本拓扑 | 已完成 | `dispatcher_v5.0.md` 是 v5.x-v7.2 的叠加规范，旧三专家链、S/M 合并链与 C-Level 审计链并存。 |
| 核心设计 Agent | 已完成 | `Scene Designer` 已合并机位、运镜、构图和光影，但仍被 YAML、KB ID、TIME_SKELETON 和审计消费契约驱动。 |
| 核心审计/验证 Agent | 已完成 | Scene Auditor、P-Verifier、Render-Verifier 主要服务审计/可追溯性，而非导演设计。 |
| EP13/EP14/EP15 产物追踪 | 已完成 | 已完成第一轮字段去向核查：最终提示词只直接消费导演决策与锚点，YAML、KB ID、连续性清单和冲突日志均为旧链路中间信息。 |
| 知识库拆分 | 已完成 | 已将导演知识、场景知识、表演翻译、SD2.0 模型边界与 Seko 平台遗留分开。 |
| 旧模块去向矩阵 | 已完成 | 详见 `MODE_P_LOOP_REFACTOR_PLAN.md`。 |
| 新 Loop 工程规划 | 已完成 | 已形成 Director + DP + SD2.0 静默预检 + 可选渲染反馈的工程方案。 |

## 已读取的关键文件

### 调度与拓扑

- `01_调度器/dispatcher_v5.0.md`
- `01_调度器/complexity_router_v1.0.md`
- `01_调度器/mode_p_v8/loop_spec.md`
- `01_调度器/mode_p_v8/loop_controller.md`

### 设计与审计 Agent

- `02_Agent/scene_designer_v1.0.md`
- `02_Agent/scene_auditor_v1.0.md`
- `02_Agent/shot_architect_v2.0.md`
- `02_Agent/movement_designer_v2.0.md`
- `02_Agent/composition_designer_v2.0.md`
- `02_Agent/prompt_composer_v2.0.md`
- `02_Agent/p_verifier_v3.0.md`
- `02_Agent/render_verifier_v1.0.md`

### 实际输出样本

- `02_Agent/output/EP14_S1_SCENE_DESIGNER.md`
- `02_Agent/output/EP14_PLAN_案情室.md`
- `02_Agent/output/EP14_S1_导演台本.md`
- `02_Agent/output/EP13_S1_SCENE_DESIGNER_v2.md`
- `02_Agent/output/EP13_PROMPT_COMPOSER_台本.md`
- `02_Agent/output/EP15_PLAN_Rico工作室.md`

### 知识与模型边界

- `03_知识库/导演手册_视觉叙事决策框架.md`
- `03_知识库/运镜思维_导演可用运动思维.md`
- `03_知识库/04_构图思维_导演用.md`
- `03_知识库/sd2_model_capability.md`
- `04_共享/P-CONSTITUTION.md`
- `04_共享/canvas_runtime.md`

## 已确认事实

1. 旧架构的主要问题不是知识不足，而是导演决策被拆成多个领域 Agent、结构化中间物和审计证据链。
2. `Scene Designer` 是最接近新目标的旧组件，但它仍要求输出 KB 规则 ID、YAML 和时间骨架，导演注意力仍被下游协议占用。
3. 最终台本消费机位、运镜、构图、光影、角色/空间锚点和转场；大量设计理由、规则 ID、冲突日志、连续性声明和审计内容不进入最终提示词。
4. SD2.0 的时长、人数、动作复杂度、正向描述和身份漂移属于模型能力边界，应保留；Seko 的引用语法、打包格式和平台工作流不属于新目标。

## 字段去向核查：第一轮结果

以 EP13、EP14 的设计报告、PLAN 与最终台本交叉对照：

| 字段类别 | 设计/PLAN 中存在 | 最终台本是否直接消费 | 暂定去向 |
|---|---|---|---|
| 机位、景别、焦段、运镜、构图、光影、转场 | 是 | 是 | 保留为导演统一设计能力 |
| 角色、环境、光源、风格、状态变化锚点 | 是 | 是 | 保留，改为简洁的场景蓝图和镜头上下文 |
| YAML、TIME_SKELETON 数据结构 | 是 | 仅作为旧管道中间输入 | 移除运行时数据契约 |
| KB 规则 ID 与逐镜论证 | EP13 设计报告有 51 处 | 否 | 从交付物移除，知识改为内化/场景化调用 |
| 连续性检查清单、冲突裁决日志 | PLAN 中存在 | 否 | 移除独立文档，由导演与 DP 在设计对话中处理 |
| 设计依据段 | EP14 最终台本仍保留 | 不进入渲染正文 | 移除交付物；必要时仅保留极短导演修订说明 |
| 镜头参数、生成指令、音轨、转场 | 是 | 是 | 保留，但移除 Seko 特定包装 |
| 【禁止】块、@ 引用语法、平台打包字段 | 是 | 与 Seko 平台绑定 | 移除；SD2.0 硬约束改由导演/DP与静默预检处理 |

## 下一步

1. 建立“旧字段 -> 最终提示词/审计/无人消费”的字段去向表。
2. 从知识库提取导演运行时真正需要的能力包：叙事视觉、运镜、构图、光影、剪辑、表演翻译、SD2.0 边界。
3. 形成保留/合并/移除矩阵，再设计新 Loop。

## 产出

完整的工程方案已写入 `MODE_P_LOOP_REFACTOR_PLAN.md`。它包含目标系统、运行时边界、知识库重组、双循环、SD2.0 最小护栏、旧模块去向矩阵、实施阶段和验收标准。

## 实施进展（2026-07-15）

已在 `01_调度器/mode_p_v9/` 建立隔离的新运行时原型，未修改旧 MODE:P：

- `director_agent.md`：统一负责机位、运镜、构图、光影和转场的导演。
- `dp_agent.md`：仅做空间、连续性、可执行性和 SD2.0 边界复核。
- `knowledge/`：七个按需加载的知识胶囊，替代每次加载整套知识库与规则证据。
- `loop_controller.md`：导演 -> DP -> 修订 -> 最小预检 -> 两份提示词交付。
- `sd2_preflight.py`：只检查时长、正向可见语言、抽象情绪词、模糊修辞、文字请求和多人清晰面孔等模型边界；不形成审计层。

自动测试已通过。下一项不是继续扩展流程，而是用真实场景回归，验证导演输出质量与即梦画布可生成性。

### EP14 S1 静态回归

已用案情室的真实空间、人物、光源和连续性事实建立 v9 场景上下文，并直接产出两份提示词：

- `mode_p_v9/regression/STORYBOARD_EP14_S1_案情室.md`：33 行。
- `mode_p_v9/regression/VIDEO_PROMPT_EP14_S1_案情室.md`：70 行，SD2.0 最小预检通过。

这个回归证明了新格式能够保留空间、轴线、机位、构图、光影和转场决策，同时去掉旧的 YAML、PLAN、规则引用和 Seko 包装。它仍是静态样本；真实 DP 对话和即梦画布生成结果尚待验证。
