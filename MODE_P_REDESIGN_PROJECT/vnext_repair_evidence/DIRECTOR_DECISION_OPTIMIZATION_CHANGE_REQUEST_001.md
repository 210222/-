# 导演决策优化施工变更案 001（v1.1 提案）

> 状态：`PROPOSED — NOT YET FROZEN`  
> 适用项目：`D:\tsc\导演系统_v5`  
> 基线：`DIRECTOR_DECISION_REFACTOR_CONSTRUCTION_PLAN.md` SHA-256 `37e444e3c25e1e05d0c3f43fa5340631d159c4c69062aa3ca98cb20e5e00b2bc`  
> 目标锁：`DIRECTOR_REFACTOR_GOAL_LOCK.json` SHA-256 `71edcc7152e9268886a99723e00b707caa892fb5ef9feac0df750f965dcd1272`  
> 激活条件：用户批准后，作为 v1.1 同步写入施工方案、目标锁和变更记录；在此之前它不是运行时权威。

## 1. 变更原因与结论

现有方案已经提出了正确的原则：Phase A 场景解释、两阶段知识检索、`blocking-first`、候选比较、
反模式卡和唯一 `VisualExecutionContract`（VEC）。但这些仍主要是原则、字段清单和未来工作包，
没有形成不可跳过、可失败、可测试的导演决策优化链。

因此，当前问题不是“缺少更多镜头技巧”，也不是“硬切必须减少”。真正缺的是从整集意图到实际
镜头/切换选择的受控决策闭环：导演为何在当前戏剧与空间条件下选此方案、放弃何种可行替代、
知识如何影响字段、文本审查如何只提出问题，以及实际媒体失败应归因到哪里。

本变更不恢复主故事板、`DIRECTOR_MASTER.md` 或固定 `@图片2/3/4` 语义；不加载完整书籍；不创建
多个常驻创意 Agent；不保存私有思维链；不设硬切、长镜头、景别或镜头数量比例。

## 2. 新增最终目标与不变量

### G-08：可优化的导演决策链

同一持续 Director 必须按下列有界链路完成设计：

```text
EpisodeDirectionState
  → SceneIntent + DirectorProblemSet
  → K1 问题级知识
  → BlockingCommit
  → K2 执行级知识
  → Candidate/DecisionRecord
  → VEC
  → EditorialReview
  → 同源双编译与实际媒体归因
```

每一项实质创意选择都可追溯到剧本事实、已批准约束、知识卡或平台能力证据。追溯记录仅保存
简短可观察的理由、权衡和范围，绝不保存 provider 推理原文、scratchpad 或 chain of thought。

### INV-DIR-01：层级与输入隔离

- `EpisodeDirectionState` 与 `SceneIntentContract` 不得包含镜头、焦段、机位、运镜或切点答案。
- `BlockingCommit` 不得读取或输出摄影/剪辑模板；人物不能为了镜头而无动机移动。
- 相机、构图、运镜和转场只能在有效 `BlockingCommit` 之后选择。
- 下层若需要推翻上层意图、调度或事实，必须生成范围化问题并使上层节点失效，不能静默重写。

### INV-DIR-02：调度先提交

没有已验证 `blocking_commit_hash` 的 camera、composition、movement、edit 或 boundary 决策不得写入
VEC，也不得生成 Storyboard/Video Prompt。

### INV-DIR-03：有意义的候选比较

每个实质创意决策要么是 `constraint_locked=true`（由剧本或用户硬约束唯一锁定），要么记录：

- 选择方案；
- 最多两个真正不同的替代方案；
- 每个替代的拒绝码与证据；
- 选择的叙事收益、代价、能力风险与自由度走廊。

禁止为了填表而编造伪候选，也禁止用自动总分或模板替 Director 决定审美答案。

### INV-DIR-04：知识置信度与适用性门控

- 每张规范化卡必须有一个主类型、来源定位、字段级 provenance、适用条件、禁用条件、代价和
  `allowed_use`。
- `high/direct` 卡可支持最终选择；`medium/conservative_inference` 卡只能参与候选且需额外事实或
  高置信证据；`low/unknown` 卡仅能提出查询问题，不可单独决定调度、镜头或剪辑。
- 每张实际使用的卡必须产生 `CapsuleApplicabilityRecord`，证明触发条件、禁用条件与影响字段；
  只有 `selected_capsule_ids` 而没有字段影响属于失败。

### INV-DIR-05：转场是导演选择，不是默认硬切

每个 Boundary 用 `transition_in/out {mode, reason}` 表示，而非默认 `cut`：

- `mode` 可以是 `hard_cut`、`continuous`、`match_cut`、`dissolve` 或平台允许的其他明确方式；
- `reason` 连接当前的戏剧、信息、节奏和执行约束；
- `hard_cut` 是有效结果，绝无比例限制；`continuous` 也不是默认优先级。

### INV-DIR-06：双模式导演审查不夺权

`MUTE_VISUAL_LOGIC` 与 `DIALOGUE_REDUNDANCY` 审查只给出带范围的 `DirectedQuestion` 或通过证据，
不能给出“改用某焦段/推镜/硬切/三镜头”等镜头处方。其状态上限是 `TEXT_VALIDATED`。

### INV-DIR-07：结果归因与反模板

实际故事板/视频失败必须标注为 `fact`、`episode_intent`、`scene_intent`、`blocking`、`decision`、
`VEC_field`、`reference`、`adapter` 或 `generation_variance`。不得因一次抽卡失败自动否定导演，
也不得无归因重抽。经验卡只能在多次、已审阅结果后提升证据等级。

## 3. 一个 Director、六个逻辑阶段

以下是同一持久 Director 下的数据阶段，不是六个独立 Agent 或六次模型调用：

```text
E0  Episode Interpreter        → EpisodeDirectionState（每集一次、可缓存）
S1  Scene Interpretation       → SceneIntentContract + DirectorProblemSet
K1  Knowledge Planner           → 戏剧/调度问题级 DecisionPacket
B0  Blocking Designer           → BlockingProposal → BlockingCommit
K2  Execution Knowledge         → 摄影/剪辑/表演的最小 DecisionPacket
B1  Shot + Edit Designer        → CandidateSet + DecisionRecord + VEC
R1  Editorial Critic            → 双模式 EditorialReviewRecord
```

常态性能策略：E0 每集一次；每场最多三次强模型语义调用（S1、B0、B1）；R1 由确定性投影和 B1 的
结构化自检完成，不能新增常驻 Critic 调用。DP 仍是新鲜、只读、问题式审查，不能接管导演。

## 4. 新增与扩展的数据契约

### 4.1 EpisodeDirectionState

每集一次的压缩导演状态，禁止任何镜头答案：

```json
{
  "episode_id": "",
  "source_hashes": [],
  "episode_thesis": "",
  "character_arc_constraints": [],
  "information_map": [],
  "key_turns": [],
  "scene_priorities": {},
  "visual_progression": "",
  "restraint_zones": [],
  "emphasis_zones": []
}
```

它不是主故事板，不支配单场镜头；它只防止每场根据局部对白孤立设计。其缓存键由剧本事实、项目创作
约束、已批准角色/世界事实组成。改变 adapter 不使它失效。

### 4.2 扩展 SceneIntentContract

保留既有场景功能、权力、信息、注意力、视觉动词与节奏，并新增：

```text
scene_objective, dramatic_action, entry_state, exit_state,
power_curve, character_actions, beats, attention_trajectory,
audience_knowledge_delta, character_knowledge_delta, risk_flags
```

每个 `beat` 都必须有 `beat_id`、事实来源和戏剧作用；仍不得包含相机/剪辑答案。

### 4.3 BlockingCommit

`BlockingCommit` 是镜头设计前的不可变空间/行为边界。每个 beat 至少包括：

```text
positions, facing_and_gaze, action_paths, prop_interactions,
space_control, entry_state, exit_state, dramatic_reason, constraint_refs
```

镜头层只能引用其 hash 与 beat id，不能事后悄悄修改。若修订 blocking，所有依赖它的候选、Shot、
Boundary 和双输出投影必须按依赖图失效。

### 4.4 SceneVisualCurve

在 BlockingCommit 后、Shot 拓扑前形成全场视觉发展曲线：

```text
beat_id → attention change / information release / spatial pressure /
visual density / restraint-or-emphasis / permitted transition intent
```

它检验节奏和发展，不规定镜头模板、时长或硬切比例。

### 4.5 DecisionOption 与 DirectorDecisionRecord

`DecisionOption` 是候选而不是隐藏思维过程。`DirectorDecisionRecord` 最低要求：

```text
decision_id, scope(scene|beat|shot|boundary), decision_kind,
problem_ids, blocking_commit_hash, selected_option_id, constraint_locked,
selected_capsule_ids, evidence_refs, decision_summary, tradeoff_summary,
rejected_options[{decision_axis_difference,rejection_code,evidence_refs}],
risk_flags, freedom_corridor, influenced_vec_field_ids
```

`rejection_code` 必须是可审查枚举，例如 `BREAKS_BLOCKING`、`REVEALS_HIDDEN_INFORMATION`、
`REPEATS_PATTERN`、`EXCEEDS_TARGET_CAPABILITY`、`WRONG_PACE`、`CONFLICTS_WITH_APPROVED_FACTS`。
记录必须先于 VEC freeze 生成；VEC 提交后不得补写理由。

### 4.6 CapsuleApplicabilityRecord 与 ConflictDecisionRecord

`CapsuleApplicabilityRecord` 保存卡的 `trigger_evidence`、`contraindication_check`、`confidence`、
`allowed_use` 与实际影响字段。`ConflictDecisionRecord` 保存冲突卡、优先级来源、Director 选择或排除
原因。算法只能验证完整性，不能裁定艺术胜者。

### 4.7 EditorialReviewRecord

```text
review_mode(MUTE_VISUAL_LOGIC|DIALOGUE_REDUNDANCY), contract_hash,
verdict(PASS|REVISE|ESCALATE), findings[{finding_type,scope_refs,
observed_contract_refs,question_to_director,severity}], TEXT_VALIDATED
```

## 5. 知识规范化与阶段检索

### 5.1 离线规范化

旧胶囊只能离线拆成单一主要原则；每条需要：

```text
parent_capsule_id, primary_type, secondary_tags, decision_level,
director_problem, trigger_conditions, contraindications, required_context,
execution_rules, expected_effect, tradeoffs, alternatives,
source_location, source_hash, field_provenance, inference_fields,
confidence_level, allowed_use, review_status
```

`primary_type` 只能是以下四类之一：`dramatic`、`blocking_performance`、`camera_shot`、
`editing_validation`；`anti_pattern` 是跨层标记。无法从来源支持的字段必须写 `unknown` 并降低
`allowed_use`，不能伪装为书籍原意。

### 5.2 K1 / K2 阶段边界与预算

- K1 由 `DirectorProblemSet` 取得戏剧/调度问题卡，禁止 camera/edit 的执行答案。
- `BlockingCommit` 通过后，K2 才能以空间、行为、注意力和隐藏信息取得执行卡。
- 每次调用仍保持 0–3 主卡、最多 1 冲突卡、最多 1 反模式卡；不同阶段传递快照和摘要，不把所有卡
  累积进同一上下文。
- 无匹配是可接受结果，Director 依据剧本约束设计；不得回退“对白→正反打”或场景标签模板。

冲突优先级：用户/项目事实 > 已批准角色资产空间声音 > Episode/Scene Intent > 目标能力 > 已验证
生成证据 > 高置信知识 > 中低置信知识与美化偏好。

## 6. 两种导演审查

### MUTE_VISUAL_LOGIC

输入为移除对白、音色、旁白后的可见状态投影。检查：权力、空间控制、注意力和关系变化是否存在可见
状态证据；是否仅由台词宣告变化；是否提前泄露隐藏信息。停顿与持镜可以通过，前提是它们服务当前
戏剧状态。

### DIALOGUE_REDUNDANCY

输入为对白事件与去镜头术语的视觉 beat 摘要。检查：是否逐句复读台词；是否所有镜头只跟随说话者；
是否出现无意义反应/插入；是否有重复对白事件。它不要求每镜都有动作，只在整体退化为覆盖拍法时提问。

## 7. 决策优化验收矩阵

### Fail-closed 自动门

1. Phase A 出现最终镜头答案、K2 在 BlockingCommit 前调用、或 shot 未引用 BlockingCommit，均失败。
2. 实质决策缺 decision/problem/evidence/VEC 字段绑定，或非约束锁定决策没有真实替代证据，均失败。
3. 低置信卡单独决定高影响选择、卡的禁用条件命中、冲突静默覆盖，均失败。
4. DecisionRecord 事后篡改、VEC 未回指决定、Storyboard/Video AST 字段无法回溯 VEC/decision，均失败。
5. DP/EditorialReview 给出镜头处方、跨越范围或宣称图像/视频通过，均失败。
6. 视觉失败没有归因而触发整场/整集重做，或冻结 Segment 被改写，均失败。

### Holdout、消融与变异测试

- 同样的对白、不同权力/空间/隐藏信息，不能自动生成同一覆盖模板；相同拓扑需有相同约束证据。
- "低机位表现强大" 这类低置信概念卡不能单独生成低机位决定。
- 逐句正反打、无理由推镜、过肩重复、角色为镜头无理由移动、景别变化冒充升级均可定位到 scope。
- Mute fixture 捕获“台词可懂但视觉不可读”；Dialogue fixture 捕获“画面只复读台词”。
- 修改空间事实只失效相关 Blocking/Beat/Shot/Boundary；修改 adapter 不失效意图、知识与调度。
- 未知剧本中真实 Director 必须产出 DecisionRecord + VEC；Golden 只能校准规则，不能成为模板。

### 实际媒体与结果归因

文本同源仍仅为 `PLANNED_PREVIEW`。只有已观察的故事板/视频可提升预览等级。媒体问题必须按
`OutcomeAttribution` 记录，且单次生成波动不得自动形成知识或改变导演意图。

## 8. 工作包与顺序

```text
DDO-0 / WP-0  批准 v1.1、同步目标锁、冻结决策 Golden 与 Holdout
DDO-1 / WP-2  离线知识原子化、主类型、provenance、置信度和反模式
DDO-2 / WP-2  EpisodeDirectionState、扩展 SceneIntent、K1
DDO-3 / WP-3  BlockingCommit、SceneVisualCurve、K2、Candidate/DecisionRecord、VEC 绑定
DDO-4 / WP-5  双模式 EditorialReview、DP 安全审查投影、范围化回流
DDO-5 / WP-4/6 同源投影、依赖失效、缓存、性能、泄漏和归因
DDO-6 / WP-7  Shadow、Holdout、小样媒体验收、用户批准后才讨论生产
```

R0–R3 维修队列只提供基础设施与安全；即使其全部完成，也不能宣称 DDO-0 至 DDO-6 或真实
Director 决策优化已经完成。

## 9. 性能、耦合与安全边界

- 一集一次 `EpisodeDirectionState` 内容寻址缓存；单场不超过三次强模型调用。
- 适配器、Markdown、哈希、审查投影和结构 gate 均为本地确定性工作。
- DecisionRecord 与 VEC 使用字段级依赖；只改一个 beat/shot/boundary 时只重新 DP 受影响范围。
- 遥测需记录每阶段 token、调用数、检索卡数、缓存命中、审查发现、修订范围和 OutcomeAttribution，
  不记录私有推理。
- 新运行时不得导入 v4 `mode_p`、`legacy_mode_p`、旧知识索引/缓存/历史交付物；旧胶囊只可离线
  规范化为审阅后的 metadata 卡。

## 10. 激活与影响范围

此提案一旦批准，必须同时：

1. 将 `G-08` 与 `INV-DIR-01` 至 `INV-DIR-07` 写入施工方案和目标锁；
2. 在 `completion_requires` 中加入决策链、BlockingCommit、候选证据、双审查和低置信门控；
3. 以版本化 changelog 记录本基线 hash、批准原因、受影响工作包和新的 hash；
4. 仅使受影响的 vNext.1 Director 工作包验收失效或重建，不将已经通过的 R2.1–R2.4 安全基础
   设施误称为创意实现；
5. 在当前 R0–R3 受控维修队列结束后、创建 vNext.1 Director 队列前，执行上述同步冻结。

在这些步骤完成前，当前基础设施仍可继续修复，但不得把它宣传为“导演决策优化已实现”。
