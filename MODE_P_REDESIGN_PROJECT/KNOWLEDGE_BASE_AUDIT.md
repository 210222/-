# MODE:P vNext 完整知识库语义审计

> 状态：设计审计基线；不修改当前运行时，不代表已完成生产实现。
>
> 审计目的：确认 MODE:P vNext 的知识架构来自项目现有知识资产、真实成功样本和当前运行边界，而不是先写一个抽象 K0-K4 方案再反向套用。
>
> 高权重证据仍以 `GOLDEN_SET_EVIDENCE_REPORT.md` 为准。本报告审计“知识怎样参与导演判断”，不以书本规则推翻真实生成结果。

---

## 1. 审计结论

项目不是“没有知识”，而是存在三个结构性问题：

1. **离线知识很多，但书本摘录过早被改写成了可执行硬规则。**
2. **单次运行知识虽然已经缩小，却主要按场景类型胶囊组织，尚未按当前导演问题精确检索。**
3. **真实生成经验管道已经有雏形，但当前没有一条已验证经验进入运行时。**

因此不能简单扩充现有胶囊，也不能把 `03_导演知识库_v5.0.md` 直接塞回上下文。正确方向是：

> 保存全部离线来源；把来源拆成带适用条件、反条件、冲突关系和证据等级的决策卡；先由 Director 做场景诊断，再由确定性检索器组装小型问题包；最终创意答案仍由同一个 Director 决定。

本审计也确认，先前提出的 K0-K4 分层方向可保留，但需要以下实质修正后才可称为生产设计：

- K0 不是一个无差别大仓库，而是必须区分原始来源、旧版重复、能力声明、项目案例和隔离内容。
- K1 只能保留判断顺序，不能保留固定摄影答案或固定模型能力数字。
- K2 必须从“场景类型胶囊”改为“单一导演问题的决策卡”。
- K3 必须绑定真实 Storyboard-Video 配对证据和用户评价。
- K4 必须只保存用户确认的项目偏好，不能把一次生成偶然性升级为通用规则。

---

## 2. 审计范围与可复核清单

本次覆盖两个知识根目录，共 24 个文件、424,473 bytes：

- `03_知识库`：10 个离线来源文件。
- `01_调度器/mode_p/knowledge`：4 个 Core、9 个 Capsule、1 个 Index。

### 2.1 离线来源清单

| 文件 | bytes | 行数 | SHA256前12位 | 审计定位 |
|---|---:|---:|---|---|
| `03_导演知识库_v4.0.md` | 42,661 | 418 | `74c7ece77d68` | 旧版归档；禁止独立检索 |
| `03_导演知识库_v5.0.md` | 167,622 | 1,413 | `6e507a7d63c1` | 最大导演规则源；只作候选提取 |
| `04_编剧知识库_v1.1.md` | 39,596 | 477 | `9b33017259f3` | 因果、空间、信息与连续性诊断源；改写剧本部分隔离 |
| `04_构图思维_导演用.md` | 27,644 | 302 | `fe5b6c9b526f` | 构图候选源；意图到技法映射必须软化 |
| `运镜思维_导演可用运动思维.md` | 31,180 | 432 | `ef42f79e93ef` | 运镜候选源；不得直接输出镜头答案 |
| `导演手册_视觉叙事决策框架.md` | 12,663 | 218 | `24cf80f1a42b` | 诊断流程候选源 |
| `PERFORMANCE_KB.md` | 12,647 | 271 | `4c95aa7f36c9` | 表演可见性候选源；固定心理映射和伪精度隔离 |
| `sd2_model_capability.md` | 7,207 | 166 | `035789b9efd9` | 历史能力声明；不得作为当前永久事实 |
| `sd2_storyboard_prompt_quality_standard.md` | 37,907 | 929 | `060de62e310a` | Storyboard/Video Prompt 质量与正向描述候选源 |
| `distillation_engine_v1.0.md` | 8,929 | 263 | `9d597ba75a16` | 旧蒸馏流程参考；不直接恢复旧阈值和集成方式 |

### 2.2 当前运行知识清单

| 文件组 | 数量 | 角色 | 当前审计结论 |
|---|---:|---|---|
| `core/*.md` | 4 | Director 常驻知识 | 可作为 K1 候选基线，但仍需按新 schema 精简与版本化 |
| `capsules/*.md` | 9 | 场景类型补充知识 | 可拆成 K2 候选；不应继续以整颗场景胶囊作为最终粒度 |
| `knowledge_index.json` | 1 | 元数据索引 | 结构可迁移；需改为决策卡索引和冲突图 |

精确文件清单：

| 文件 | bytes | 行数 | SHA256前12位 | 目标处置 |
|---|---:|---:|---|---|
| `core/director_core.md` | 4,427 | 39 | `c5ec56aa5967` | K1 候选基线 |
| `core/editing_transition.md` | 2,574 | 25 | `84eac446041f` | K1/K2 拆分候选 |
| `core/performance.md` | 2,452 | 26 | `26e54571f131` | K1 可见性 + K2 景别策略 |
| `core/sd2.md` | 1,862 | 17 | `f32d2483b5a8` | K1 能力接口，不保存固定上限 |
| `capsules/action_chase.md` | 936 | 18 | `fa675e161488` | K2 迁移候选 |
| `capsules/contemplative_silence.md` | 601 | 7 | `d3f715319b1a` | K2 迁移候选 |
| `capsules/cross_space_transition.md` | 2,403 | 38 | `e556ebbcc60c` | K2 迁移候选 |
| `capsules/crowd_attention.md` | 2,235 | 40 | `0235b532792b` | K2 迁移候选 |
| `capsules/dialogue_power.md` | 1,171 | 20 | `87bae44403cd` | K2 迁移候选 |
| `capsules/investigation_object.md` | 2,176 | 40 | `1c24275557e0` | K2 迁移候选 |
| `capsules/montage.md` | 2,205 | 39 | `ed95f34cde7c` | K2 迁移候选 |
| `capsules/omni_reference.md` | 3,051 | 43 | `99a7175d7b64` | K2 参考职责候选 |
| `capsules/suspense_reveal.md` | 876 | 17 | `7d28694a1e9a` | K2 迁移候选 |
| `knowledge_index.json` | 9,448 | 362 | `b5fe30538fad` | 工具元数据；重建索引 |

当前 9 个 Capsule 的 `verified_count` 全部为 `0`，`experience_status` 全部为 `none`。这意味着它们目前是整理后的理论知识，不是经过真实生成闭环验证的经验。

---

## 3. 实际知识领域地图

完整知识源覆盖的不是九种“场景模板”，而是以下相互依赖的导演问题域：

| 问题域 | 主要来源 | 对 MODE:P 的正确用途 |
|---|---|---|
| 戏剧变化与场景目标 | 编剧知识库、导演手册、director_core | 建立场景变化、信息差和注意力目标，不直接决定焦段 |
| 空间拓扑与人物调度 | 导演 v5、编剧知识库、director_core | 约束轴线、入口、视线、遮挡、相对距离和走位可执行性 |
| 注意力与揭示 | 导演 v5、构图思维、悬疑/物件 Capsule | 决定观众何时看见什么、起幅到落幅如何收缩或转移 |
| 构图与视觉流 | 导演 v5、构图思维、Framed Ink/Visual Story 摘录 | 提供构图变量和权衡，不把形状、颜色固定映射成情绪答案 |
| 摄影机运动 | 运镜思维、导演 v5、action/suspense Capsule | 判断运动动机、路径、参照物、起落幅和复杂度 |
| 剪辑与转场 | editing_transition、导演 v5、cross-space Capsule | 判断切点动机、视听锚、内部切镜与生成段边界 |
| 光影、色彩与材质 | 导演 v5、director_core | 建立物理光源、曝光关系、注意力分布和连续性 |
| 表演可见性 | PERFORMANCE_KB、runtime performance | 将人物意图转成当前景别能读到的身体通道，避免不可见微动作 |
| 声音与音画关系 | 导演 v5、editing_transition | 设计声桥、画外空间和静默；不得把画外声源自动生成进画面 |
| 参考资产职责 | runtime sd2、omni_reference、SD2 资料 | 明确人物、场景、道具、故事板、音频各自约束什么 |
| 生成能力与提示词 | SD2 两份来源、runtime sd2 | 通过版本化 Capability Profile 约束复杂度和字段路由 |
| 可见性与生成泄漏 | 成功样本、用户确认问题、prompt standard | 分开 visible、occluded、narrative-only、audio-only，并做正向闭合 |
| 真实案例与用户审美 | 四组 Storyboard-Video 配对 | 形成 K3 不变量、可优化区、失败信号和用户质量标签 |

结论：单一 `dialogue`、`action`、`suspense` 标签只能作为召回入口之一，不能作为知识答案。

---

## 4. 可以保留的高价值资产

### 4.1 当前 Core 的正确方向

当前四个 Core 已经包含一些应保留的原则：

- 先判断戏剧变化和注意力，再选择镜头。
- 空间、走位、相机、构图和光线联动。
- 切镜应有信息、动作、情绪或空间动机。
- 表演动作必须在当前景别可见。
- 模型能力必须通过 profile 声明，不能写成永久真理。
- 参考图需要明确职责，不能靠引用数量替代导演判断。

这些内容适合被重写为精简 K1，而不是被旧版 1100 条规则覆盖。

### 4.2 离线大库的正确价值

`03_导演知识库_v5.0.md` 的价值不是“1100+ 可直接执行规则”，而是：

- 空间、轴线、调度、构图、运镜、剪辑、光影、声音领域覆盖广。
- 多数条目保留了来源名和规则 ID，可用于来源追踪。
- 同一问题经常存在不同方法，可拆成互斥或互补的导演选项。
- 含有许多有用的失败观察，例如缺乏运动动机、视线不连续、视觉重点混乱。

### 4.3 已有经验闭环组件

当前项目的 `render_evidence.py` 与 `knowledge_curator.py` 已经提供了可复用基础：

- RenderEvidence、UserObservation、ExperienceCandidate 分层。
- candidate → repeated → validated → rejected 状态。
- validated 要求多个证据、多个场景、用户批准和回归通过。
- 验证记录与回滚快照。

新方案应扩展这条链，而不是另建一个没有证据约束的自动学习器。

---

## 5. 重复、冲突与风险审计

### 5.1 版本重复

对非空行做精确比较，v4 的 352 条非空行中有 290 条也存在于 v5，精确重合约 82.4%。

处理规则：

- v4 保留在 K0 归档，用于历史溯源。
- v4 不参与运行时召回，也不与 v5 重复计票。
- 若 v4 独有条目有价值，必须单独提取并标明 `superseded_source`，不能整库复活。

### 5.2 书本经验被错误升级为硬规则

| 旧知识表达 | 风险 | vNext 处理 |
|---|---|---|
| “知识库规则优先于 LLM” | 静态规则压制当前剧本和真实生成证据 | 删除静态优先关系；采用证据与适用性裁决 |
| “所有动作场景首镜必须定场” | 排除直接入戏、主观开场、声音先行等有效设计 | 变成带条件的定向选项，不是 P0 |
| “每个静态对话至少两个主镜头” | 把覆盖率误当导演意图 | 改为连续性和注意力覆盖问题 |
| “深空间=冲突，平空间=和谐” | 把可选视觉关系写成固定语义 | 卡片列出可能效果、反例和上下文依赖 |
| “水平/垂直/斜线固定代表某情绪” | 文化语境和具体画面被抹平 | 只作为候选读法，不可自动选技法 |
| “红色永远等于危险/激情” | 符号学过度简化 | 记录项目语境、面积、明度、文化与连续性 |
| 固定三级曝光、固定比例、固定毫米/毫秒 | 伪精度进入文本生成 | 只有经目标模型或项目验证的数值才能进 Capability/Profile |

### 5.3 库内自相矛盾

| 冲突 | 审计判断 |
|---|---|
| 轴线规则写成绝对禁止，同时同库又列出连续越轴、cutaway、重新立轴等合法手段 | 应拆为“连续性风险卡”和“有动机越轴卡”，由 Director 判断 |
| Prompt 标准一处强调一镜一动作，另一处承认复合运镜可工作 | 应由复杂度预算和参考可读性裁决，不做绝对上限 |
| 运镜资料要求运动镜头一定以静止起止，真实窄巷样本却在受控动态连接中效果更好 | 真实配对证据优先；静止起落是稳定策略，不是硬规则 |
| PERFORMANCE_KB 用极细微固定面部变化表达心理，runtime performance 又强调景别可见性 | 保留可见性原则；固定心理到肌肉映射降级/隔离 |
| SD2 旧资料含固定人物或参考上限，runtime 测试已主动禁止无验证硬上限 | 能力只能进版本化 Capability Profile |
| `@禁止` 作为人类审计有效，但有些模型可能把否定词名词生成出来 | 人类 VIDEO_PROMPT 与实际 Render Payload 分域路由 |

### 5.4 与真实样本冲突

- 枪管样本说明，一个 Generation Segment 可以包含连续的景别收缩、弧形绕行和焦段语义变化；不能用“一段只允许单一运动”的旧规则拆坏。
- 观众席样本说明，同一生成段内部可以稳定保留三段切镜；但“无回复/无正在输入”只写缺失条件会被模型补成额外 UI，必须增加可见性白名单和正向空白闭合。
- 备赛区样本说明，固定的微表情和精确时间描述并不保证可见；机位、人物朝向、占画比例和动作通道优先。
- 窄巷样本说明，字面切点不是唯一成功标准；只要起幅、注意力转移、运动方向、威胁落幅和剧情事实保持，模型可优化连接方式。

### 5.5 能力资料的时效风险

`sd2_model_capability.md` 和 Prompt 标准中的平台声明只能作为“待验证能力候选”。任何来源自称“官方”“固定限制”都不能直接成为运行事实；必须绑定：

- 平台/模型标识。
- 版本或发布日期。
- 实际测试日期。
- 测试输入和结果证据。
- 适用画幅、时长、参考模式和负向通道。
- 到期或复验条件。

---

## 6. 逐文件处置矩阵

| 文件/文件组 | 目标层 | 处置 |
|---|---|---|
| 导演知识库 v4 | K0-Archive | 只读历史归档，不召回 |
| 导演知识库 v5 | K0-Source | 按单一 claim 提取 K2 候选；取消原 P0-P3 的直接运行权威 |
| 编剧知识库 v1.1 | K0-Source | 因果、信息、空间、连续性可转诊断卡；改写/增删剧本建议默认隔离 |
| 构图思维 | K0-Source | 拆成构图变量、权衡、反例卡；禁止意图到构图一键映射 |
| 运镜思维 | K0-Source | 拆成运动动机、路径、起落幅、参照物和失败卡 |
| 导演手册 | K0-Source | 提取诊断顺序与跨域问题；不保留固定答案 |
| PERFORMANCE_KB | K0-Quarantine/Source | 可见通道可提取；固定心理肌肉映射和伪精度隔离 |
| SD2 capability | K0-CapabilityCandidate | 经目标模型验证后才进 Capability Profile |
| Prompt quality standard | K0-Source | 格式、参考职责、正向描述可提取；平台声明需验证 |
| distillation engine | K0-LegacyMethod | 仅保留候选→人工闸门思想；旧集成和阈值不恢复 |
| runtime director_core | K1-Candidate | 精简为判断顺序，加入注意力拓扑与 Visibility Contract |
| runtime editing_transition | K1/K2-Candidate | 常驻只留切换判断；具体转场拆卡 |
| runtime performance | K1/K2-Candidate | 常驻只留可见性原则；各景别策略拆卡 |
| runtime sd2 | K1-Interface | 只保留 capability-first 和 reference responsibility 接口 |
| 9 个 runtime Capsule | K2-MigrationCandidate | 拆成单问题卡；在验证前不标为 K3 经验 |
| knowledge_index.json | Tooling | 迁移为 card index + contradiction graph + provenance，不是知识正文 |
| 四组配对样本 | K3-Golden | 建立真实案例模式、用户质量标签和失败信号 |
| 用户确认的格式/偏移偏好 | K4-Project | 项目内启用，跨项目不自动晋升 |

---

## 7. 修正后的证据与裁决体系

### 7.1 事实优先于知识

SCRIPT_FACTS、Continuity、用户明确要求和已批准 Storyboard 是当前任务约束，不属于可被知识投票覆盖的“证据”。任何知识卡与这些事实冲突时直接排除。

### 7.2 知识证据等级

| 等级 | 定义 | 运行权重 |
|---|---|---|
| E5 | 用户批准的真实 Storyboard-Video 配对案例，含质量评价 | 最高经验权重 |
| E4 | 目标模型/平台的可复现能力测试，或当前运行时可复现测试 | 能力与可执行性权重 |
| E3 | 可追溯的一手电影/表演/视觉来源，但未在本项目验证 | 提供候选判断 |
| E2 | 项目内人工综合、二手整理或跨书归纳 | 需要冲突检查 |
| E1 | 旧管道规则、社区声明、无上下文经验 | 仅候选，不得形成硬约束 |
| E0 | 已被真实证据反驳、来源不明或危险伪精度 | 隔离/拒绝 |

E5 也不能把一次偶然实现升级成普遍摄影法则。它只高权重证明该样本的 `invariants`、`variables` 和 `failure_signals`。

证据等级只描述来源可信度，不描述当前可用性。每次召回前还必须独立检查：

- target_model_match
- generation_mode_match
- aspect_match
- reference_mode_match
- recency_status
- replication_scope
- project_relevance

任何硬适用性不匹配都先排除，再比较 E0-E5。旧模型上的用户认可案例不能覆盖当前目标模型已验证的不兼容能力。

### 7.3 同等级冲突

检索器不得静默选择一个“胜者”。它必须：

1. 标出冲突字段。
2. 同时保留最多两个真正相关的选项。
3. 向 Director 提交需要裁决的问题。
4. 在 Master 中记录最终选择和当前场景理由。

---

## 8. 决策卡生产 Schema

每张 K2 决策卡只回答一个导演问题，至少包含：

~~~yaml
knowledge_id: CAM-MOTIVE-001
schema_version: 1.0.0
title: 摄影机移动是否有可观察动机
decision_domain: camera_movement
claim_type: heuristic
director_question: 当前注意力变化是否需要摄影机移动完成
applies_when: []
non_applicability: []
required_facts: []
director_variables: []
options_and_tradeoffs: []
observable_failures: []
counterexamples: []
model_dependencies: []
visibility_risk_class: []
positive_closure_requirements: []
negative_routing_constraints: []
must_not_decide: []
source_refs: []
evidence_tier: E3
evidence_records: []
contradicts: []
supersedes: []
status: candidate
version: 1.0.0
last_reviewed_at: null
~~~

关键含义：

- `options_and_tradeoffs` 提供选择空间，不提供当前场景答案。
- `counterexamples` 防止把教材经验绝对化。
- `must_not_decide` 明确算法和卡片无权决定的创意变量。
- `model_dependencies` 把电影知识与生成模型能力分开。
- `contradicts` 让冲突成为显式数据，不靠大模型猜。
- `status` 至少包含 candidate、active、validated、deprecated、rejected。

---

## 9. 两阶段 Director 与确定性检索

### 9.1 Phase A：无镜头答案的场景诊断

Director 只读剧本事实、连续性、资产职责、K1 和用户项目偏好索引，输出：

- 当前戏剧变化。
- 注意力起点、转移和落点。
- 空间/表演/可见性/切换/模型风险。
- 需要知识帮助的问题域。
- 不得由知识替代的创意决定。

### 9.2 检索器只做确定性工作

检索器负责：

1. 用显式诊断字段召回候选。
2. 检查 applies/non_applicability。
3. 检查 Capability 和画幅/时长/参考模式依赖。
4. 去除 v4/v5 和多胶囊重复。
5. 暴露冲突，不静默裁决创意。
6. 优先真实相关案例和用户确认偏好。
7. 在字符预算内选择互补问题卡。
8. 生成可重放 Knowledge Snapshot。

检索器不得：

- 从“对话”“追逐”“悬疑”等关键词直接选焦段、机位或运镜。
- 输出完整时间轴。
- 把最高分卡片当作必须执行答案。
- 在无匹配时回退到通用模板。

### 9.3 Phase B：同一个 Director 综合设计

同一个 Director 恢复会话，读取最小知识包，完成 Director Master。它必须对知识包进行综合、取舍或拒绝，而不是复制规则文本。

### 9.4 对当前 retriever 的具体修正

当前 `context_retriever.py` 的最终入选是 Director 显式传入的 `requested_capsules`；元数据相关性主要用于验证和报告。这一机制避免算法替 Director 创作，但没有实现问题驱动补位。

vNext 应改为：

- Director 提交 `knowledge_questions` 和 `decision_domains`，不提交最终胶囊路径。
- 算法根据条件匹配决策卡，并把选择原因与冲突返还给 Director。
- Director 保留拒绝卡片、请求另一问题域或无知识设计的权力。

---

## 10. 从原始知识到正式知识的离线链

~~~
K0原文
  → 原子Claim提取
  → 来源与版本绑定
  → 重复聚类
  → 适用/不适用条件补全
  → 冲突与反例标注
  → K2候选卡
  → 人工审查
  → active
  → 真实生成观察
  → repeated
  → 用户批准+跨场景回归
  → validated
~~~

硬约束：

- 大模型只能生成候选，不可直接修改 active/validated 知识。
- 任何自动摘要必须保留原始 source locator 和 hash。
- 旧 P0-P3 不直接继承为 vNext 权威等级。
- 一个来源被多份文档复制时只算一份证据。
- 能力声明到期或模型变更后自动降为待复验，不继续充当事实。
- rejected 内容保留原因，防止以后被重复引入。

---

## 11. 真实经验闭环升级

保留现有 candidate → repeated → validated → rejected 状态机，扩展 ExperienceCandidate：

- observation_type：attention、camera、editing、performance、visibility、reference、prompt、capability。
- storyboard_prediction：故事板预测了什么。
- actual_video_behavior：视频实际怎样执行。
- user_quality_label：用户认为优秀、可接受、失败或待定。
- invariant_preserved：哪些高层意图保留。
- deviation_class：优化、无害偏移、严重偏移。
- capability_profile_hash。
- affected_card_ids。
- regression_case_ids。

晋升 validated 的最低要求仍必须包含：

- 至少两个独立 RenderEvidence。
- 至少两个独立场景，而不是同一镜头重复生成。
- 明确的用户批准。
- 对应文本回归通过。
- 若声明模型能力，必须绑定同一目标模型版本或明确适用范围。
- 绑定 STORYBOARD_RUN_RECORD 或 RENDER_RUN_RECORD，证明实际提交文本、资产和输出的对应关系。

四组现有配对先进入 K3 Golden，不直接把所有观察晋升为 K1 通用铁律。

---

## 12. 单次知识包的生产预算

默认上限保持“小而相关”：

- K1：不超过 1,500 中文字符。
- K2：最多 8 张，合计不超过 2,400 中文字符。
- K3：最多 2 个案例摘要，合计不超过 1,000 中文字符。
- K4：不超过 600 中文字符。
- 总包：默认不超过 5,500 中文字符。

但预算裁剪不能只按相关分数截断。优先覆盖不同问题：

1. 剧情事实、空间可执行性和连续性冲突。
2. 表演与表面的可见性。
3. Generation Segment、内部切镜和起落幅。
4. 注意力、相机和构图。
5. 光影、材质、声音和细节。

重复解释同一问题的低证据卡先删除。

---

## 13. 必须建立的首批决策卡族

不是把旧九胶囊原样改名，而是优先覆盖真实样本暴露的问题：

1. Attention Path：注意力起点、转移、收缩、揭示、落点。
2. Generation Segment：连续镜头、内部切镜、段边界和连接自由度。
3. Camera Motivation：推、摇、绕、跟、移焦何时有动机。
4. Start/Process/End Frame：起幅、过程、落幅职责和可预测性。
5. Performance Visibility：动作通道与景别/朝向/占画比例。
6. Spatial Topology：轴线、入口、通道、擦肩距离和背景方向。
7. Composition Flow：视觉焦点、负空间、引导线、纵深和画幅重构。
8. Physical Lighting：光源锚点、光区、衰减、明暗连续性。
9. Editing Motivation：信息、动作、情绪、声音和空间切点。
10. Reference Responsibility：人物、场景、道具、故事板、音频各自职责。
11. Visibility Contract：屏幕、镜面、透明介质、孔洞、画外声源和背面。
12. Negative Routing：正向闭合、人类 QA、独立负向通道和 token leakage。
13. Capability Adaptation：在不改变导演意图的前提下降低模型复杂度。

---

## 14. 验收与回归测试

### 14.1 结构测试

- 24 个现有文件全部有 disposition，不存在“被默认加载”的未知来源。
- v4 不参与运行时召回。
- 同一来源复制条目不重复加权。
- 每张 active 卡有 applies、non_applicability、source_refs 和 evidence_tier。
- 能力卡有版本、验证日期和到期策略。
- 冲突卡能够共同进入冲突报告。

### 14.2 检索测试

- 枪管诊断召回注意力收缩、连续推进、起落幅和物件可见性，不召回通用动作模板。
- 观众席诊断召回内部三镜、群体注意力、对白表演可见性和 UI 空白闭合。
- 备赛区诊断召回擦肩空间、背影表演不可见和延迟入画，而不是“微笑=某心理”的固定表演卡。
- 窄巷诊断召回受控优化、仰摇、威胁落幅和画幅重构，不把旧切点当唯一答案。
- 手机背面、镜面、玻璃、画外声音、聊天空白和物体背面能召回 Visibility 卡。
- 同样含“对话”一词但导演问题不同的场景，知识包必须不同。
- 无匹配只返回 K1，不回退场景模板。

### 14.3 反漂移测试

运行时必须拒绝重新引入：

- “最多两个清晰主脸”等无目标模型证据的硬限制。
- “动作场景第一镜必须定场”等无适用条件硬规则。
- “固定颜色/线条/焦段等于固定情绪”的一键映射。
- 精确到毫米、毫秒、肌肉幅度但没有画面可验证性的伪精度。
- 把 narrative-only 或 audio-only 信息写入正向 Render Payload。
- 用算法分数自动选择当前镜头答案。

### 14.4 经验晋升测试

- 没有用户批准不能 validated。
- 单场重复生成不能冒充跨场景复现。
- 只有 Prompt 文本没有真实 RenderEvidence 不能晋升。
- Capability Profile 改变后，相关经验必须重新验证或缩小适用范围。
- 缺少外部运行记录的媒体不得作为 validated 因果证据。
- Calibration Set 不得同时充当唯一 Holdout；知识效果必须有消融对照。

---

## 15. 迁移顺序

1. 冻结当前 24 文件 hash，建立 K0 清单。
2. 将 v4 标为 superseded，不删除文件。
3. 从四个 Core 提取 K1 候选并压缩。
4. 将 9 个 Capsule 拆成单问题 K2 候选。
5. 对 v5、构图、运镜、表演、编剧和 Prompt 来源做 Claim 级提取与重复聚类。
6. 建立 Capability Candidate 与实际 Capability Profile 的人工验证闸门。
7. 把四组配对写成 K3 Golden Case，而不是理论卡。
8. 建立问题驱动检索器和 Knowledge Snapshot。
9. 跑文本回归、冲突回归、预算回归和 Golden Set 离线验收。
10. 用户批准后，才允许切换生产运行时。

---

## 16. 最终审计判断

在本次审计前，不能严谨地说 vNext 知识架构已经建立在完整项目知识库之上；当时只完成了运行时知识结构和关键规则的阅读。

本次审计后，可以明确回答：

- 设计已经覆盖并逐份处置项目现有 24 个知识文件。
- 保留了现有 Core、知识索引和经验闭环中正确的部分。
- 没有把旧大库的 P0-P3 直接继承为新系统权威。
- 新知识层的目标不是给 Director 更多格式文本，而是给它更少、更相关、更可质疑的判断材料。
- 真正决定 vNext 的最高权重仍然是你的真实 Storyboard-Video 配对和用户质量判断。

这份报告是 `MODE_P_VNEXT_LOOP_SPEC.md` 的知识设计依据。后续若 LOOP 的知识章节与本报告冲突，应先停止实现并重新审计，而不是由程序自行选择一个版本。
