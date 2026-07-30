# MODE:P 导演决策重构施工方案 v1.1

> 状态：`FROZEN_PRECONSTRUCTION_V1.1`（设计与验收权威；尚未授权 vNext 运行时或生产切换）  
> 适用项目：`D:\tsc\导演系统_v5`  
> 目标运行时：`mode_p_vnext` 的后续 Director vNext.1 队列  
> 保留基线：`DIRECTOR_DECISION_REFACTOR_CONSTRUCTION_PLAN.md`，SHA-256 `37e444e3c25e1e05d0c3f43fa5340631d159c4c69062aa3ca98cb20e5e00b2bc`  
> 设计变更来源：`DIRECTOR_DECISION_OPTIMIZATION_CHANGE_REQUEST_001.md`  
> 当前生产入口：v4 保持不变；本文件不删除旧文件、不切换入口、不授予视觉通过。

## 0. 权威、范围和变更纪律

本文件是 vNext.1 Director 施工的完整目标合同。它保留 v1.0 中仍有效的安全、同源、参考资产、媒体
验收和性能要求，并把“导演决策优化”从原则变成可失败、可回溯、可验证的链路。v1.0 作为 R0–R3
历史证据保留，不得覆盖或重写。

冲突优先级：用户最新明确要求 > 本文件与 v1.1 目标锁 > 当前有效的维修/运行控制器 > vNext 可复用
实现 > v4、旧交付物和历史提示词。任何改变 G-08 或 INV-DIR-* 的代码、Schema、Agent 契约、测试或
性能限制，必须同步更新本文件、v1.1 目标锁与变更记录；不能只改 Prompt 或测试使其静默漂移。

本文件不把“文字同源”伪装成视觉通过；不把 R0–R3 基础设施修复伪装成 Director 已实现；不保存私有
思维链。它只要求简短、可观察、可审计的理由、取舍、证据和影响字段。

## 1. 先决事实与施工顺序

当前 R3.2 尚未完成，原因必须原样保留并先受控解决：

1. 冻结基线写为 686 项，而当前 v4 收集 781 项；新增的 95 项来自一个后冻结的 EP35 历史场景套件，
   其中包含已废止的主板/固定图片槽位/像素级首帧规则，不能静默计入新 Director 语义。
2. R0.3 只完成 70 项的分类，不等于 70 项均有当前执行证据；59 项没有历史或修复证据标记，摘要还把
   “已勾选但无证据”错误命名为“所有无证据”。
3. R3.2 的 `local_ready_machine_generated` 与控制器终态 `V_TASK_REVALIDATION_REQUIRED` 的语义不一致。

因此顺序固定为：

```text
R3.2 基线/证据/终态契约受控复核
  → 生成真值化 R3.2 证据（而非改数字）
  → 冻结本 v1.1 设计锁与变更记录
  → 建立独立 DDO-0…DDO-6 队列
  → Shadow / Holdout / 真实媒体小样
  → 用户明确批准后才讨论 Pilot、Canary、Production
```

在 R3.2 真正结束前，本文件允许准备 Schema、Golden、Holdout 和测试设计，不允许把 DDO 工作包记为
完成，也不允许旧 EP35 的遗留规则进入新的运行时。

## 2. 最终目标与明确非目标

### 2.1 最终目标

- 一个持续的 Director 为整集形成统一但不模板化的导演意图。
- Director 先解释戏剧和人物调度，再决定相机、构图、运镜和转场；人物不能为了镜头无动机移动。
- 每一实质选择由同一份 `VisualExecutionContract`（VEC）投影为 Storyboard 与 Video Prompt；两者的
  差异仅是载体和 Adapter，不得重新猜镜头或改写事件。
- 知识库以小型、带来源和置信度的胶囊参与判断，而不是把整本理论塞入上下文或用关键词评分代替导演。
- 实际故事板和视频问题可归因到事实、意图、调度、决策、VEC 字段、参考、Adapter 或生成波动，并仅
  重做受影响范围。
- 用户能够在实际媒体上验收人物身份、服装、站位、视线、手机/道具持手与朝向、镜像、镜头拓扑、
  声音和节奏，而不是只看一段漂亮但不可复现的文字。

### G-08：可优化的导演决策链

每个实质创意选择必须经过下列完整、有界的链路：

```text
EpisodeDirectionState → SceneIntent + DirectorProblemSet → K1 → BlockingCommit
→ K2 → Candidate/DecisionRecord → VEC → EditorialReview → 双投影/媒体归因
```

追溯记录只保存短理由、取舍、已批准约束、来源和影响字段；不得记录 provider 私有推理、scratchpad
或 chain of thought。该目标新增于 v1.1，并补充而不替代原 G-01…G-07 的单一真源、无旧主板、时间、
空间、参考、Prompt 纯净度和同源目标。

### 2.2 明确非目标

- 不恢复主连续性板、主故事板、`DIRECTOR_MASTER.md` 或 `@图片2/@图片3/@图片4` 的固定语义。
- 不强制上一段视频末帧像素匹配下一段首格；硬切允许改变取景，连续性来自身份、状态、空间和事实。
- 不设硬切率、长镜头率、景别比例、镜头数量或“必须多切镜”的配额。硬切、连续、匹配切和叠化都是
  Director 根据当前戏剧选择的合法结果。
- 不让 DP、检索评分、Golden 或低置信知识自动替代导演审美；不创建每场一个 Director 的 Agent 群。
- 不因文字模型通过而宣称故事板或视频已视觉通过；DeepSeek 只能获得 `TEXT_VALIDATED`。
- 不改 v4 运行时、历史交付、已完成视频或生产入口，除非用户另行明确授权。

## 3. 不可协商不变量

### 3.1 创意、时间与空间

- `INV-SOURCE-01`：VEC 是唯一机器可读创意真源；Storyboard 和 Video Prompt 均为确定性投影。
- `INV-SOURCE-02`：任何源于 Markdown、图片或视频的反向猜测都不能成为新真源。
- `INV-TIME-01`：机器时间使用整数 tick、区间 `[start,end)`；局部视频正文从 0 秒计时。
- `INV-TIME-02`：全局时间只在不可见 Manifest 中出现；禁止进入任何生成正文。
- `INV-SPACE-01`：人物 screen-left/right、朝向、视线、运动方向、轴线和镜像禁令是字段级不变量。
- `INV-PROP-01`：道具 holder、持手、握法、正反面、可见面、朝向和状态必须跨两种投影一致。
- `INV-AUDIO-01`：角色对白事件必须绑定角色音色资产；同一对白不得跨 Segment 重复。

### 3.2 无旧主板、参考和可见 Prompt 纯净度

- `INV-NOMASTER-01`：不存在运行时主连续性板或父子故事板依赖；上一段媒体帧只能在用户明确指定的
  AssetBinding 中作为连续性证据，绝不强制本段开场构图。
- `INV-REF-01`：参考按身份、服装、站位/调度、场景布局、道具几何、构图、运动、声音等职责绑定；
  同一资产可有多职责但不得因平台序号取得权威。
- `INV-REF-02`：整张 Storyboard 默认不作为视频参考；仅当单格 A/B 已证明对目标模型有效时，才可低
  优先级、受范围限制地绑定。
- `INV-LEAK-01`：哈希、全局时间、状态摘要、审查结论、下一段指令、内部 ID、文学旁注和“不要出现 X”
  一类高泄漏负向名词不得进入正向创意正文。

### 3.3 导演决策优化不变量

- `INV-DIR-01`：`EpisodeDirectionState` 和 `SceneIntentContract` 不含相机、焦段、机位、运镜或切点
  答案；下层若反驳上层，必须发出带范围的失效请求。
- `INV-DIR-02`：没有已验证的 `BlockingCommit`，任何 camera、composition、movement、edit 或 boundary
  决策都不得写入 VEC。
- `INV-DIR-03`：实质选择要么由事实/用户硬约束唯一锁定，要么具有最多两个真正不同的备选、拒绝码、
  证据、收益、代价、能力风险与自由度走廊；禁止伪候选和自动总分裁决艺术答案。
- `INV-DIR-04`：每张知识卡有主类型、字段级来源、触发/禁用条件、置信度和 `allowed_use`；低置信卡
  只能提出问题，不能独立决定高影响调度、镜头或转场。
- `INV-DIR-05`：每个边界有 `transition {mode, reason, decision_id, evidence_refs}`；没有默认硬切或默认
  连续。
- `INV-DIR-06`：`MUTE_VISUAL_LOGIC` 与 `DIALOGUE_REDUNDANCY` 只能提出 `DirectedQuestion` 或给出文本
  通过证据，不能开出焦段、推镜、硬切或镜头数处方。
- `INV-DIR-07`：媒体失败必须记录 `OutcomeAttribution`；不得无归因重抽、单次波动升格为知识，或改写
  已冻结的无关 Segment。

## 4. 唯一导演决策链

同一持续 Director 在同一场景内按以下逻辑阶段工作。它们是有界的数据阶段，不是六个常驻 Agent，
也不等于六次模型调用：

```text
E0 Episode Interpreter
  → EpisodeDirectionState（每集一次、内容寻址缓存）
S1 Scene Interpreter
  → SceneIntentContract + DirectorProblemSet
K1 Knowledge Planner
  → 问题级 DecisionPacket
B0 Blocking Designer
  → BlockingProposal → BlockingCommit
K2 Execution Knowledge
  → 执行级 DecisionPacket
B1 Shot + Edit Designer
  → SceneVisualCurve + CandidateSet + DirectorDecisionRecord + VEC
R1 Editorial Critic
  → EditorialReviewRecord → 范围化修订或通过
```

常态性能契约：E0 每集最多一次强语义调用；每场最多 S1、B0、B1 三次强语义调用；K1/K2 是确定性检索；
R1 是结构化自检与确定性投影，不新增常驻 Critic 调用。DP 始终新鲜、只读、问题式审查。

## 5. 数据契约和失效图

### 5.1 Episode 与 Scene 意图

`EpisodeDirectionState` 仅保存整集主题、角色弧线约束、信息地图、关键转折、场景优先级、视觉发展、
克制区与强调区。它的缓存键由剧本事实、项目创作约束和批准资产事实组成；Adapter 改动不能使其失效。

`SceneIntentContract` 至少包含：

```text
scene_objective, dramatic_action, entry_state, exit_state, power_curve,
character_actions, beats, attention_trajectory, audience_knowledge_delta,
character_knowledge_delta, risk_flags, must_preserve, avoid_list
```

每个 beat 必须有 `beat_id`、事实来源和戏剧作用，且不含镜头答案。

### 5.2 BlockingCommit 与视觉曲线

每个 beat 的 `BlockingCommit` 至少包含：

```text
positions, facing_and_gaze, action_paths, prop_interactions, space_control,
entry_state, exit_state, dramatic_reason, constraint_refs
```

它是 VEC 前不可变边界。修改它会使依赖的候选、Shot、Boundary 和投影失效；修改 Adapter 不会使它失效。

`SceneVisualCurve` 由 `beat_id → attention_change / information_release / spatial_pressure /
visual_density / restraint_or_emphasis / permitted_transition_intent` 组成。它用于检验节奏与发展，不能暗中
规定固定镜头模板、时长或切镜比率。

### 5.3 决策、知识和审查记录

`DirectorDecisionRecord` 必须在 VEC freeze 前写入，最低字段：

```text
decision_id, scope, decision_kind, problem_ids, blocking_commit_hash,
selected_option_id, constraint_locked, selected_capsule_ids, evidence_refs,
decision_summary, tradeoff_summary, rejected_options, risk_flags,
freedom_corridor, influenced_vec_field_ids
```

`rejected_options` 最多两项，必须在决策轴上真正不同，并使用可审查的拒绝码，例如：
`BREAKS_BLOCKING`、`REVEALS_HIDDEN_INFORMATION`、`REPEATS_PATTERN`、`EXCEEDS_TARGET_CAPABILITY`、
`WRONG_PACE`、`CONFLICTS_WITH_APPROVED_FACTS`。

`CapsuleApplicabilityRecord` 保存触发证据、禁用条件检查、置信度、允许用途和实际影响字段；
`ConflictDecisionRecord` 保存冲突卡、优先级来源和 Director 的选择/排除原因；
`EditorialReviewRecord` 保存审查模式、范围、可观察契约引用、问题和 `TEXT_VALIDATED` 上限。

## 6. 知识胶囊与两阶段检索

完整书籍和旧知识仅用于离线原子化。每张卡必须包含：

```text
parent_capsule_id, primary_type, secondary_tags, decision_level,
director_problem, trigger_conditions, contraindications, required_context,
execution_rules, expected_effect, tradeoffs, alternatives, source_location,
source_hash, field_provenance, inference_fields, confidence_level,
allowed_use, review_status
```

`primary_type` 仅可为 `dramatic`、`blocking_performance`、`camera_shot`、`editing_validation`；反模式为跨层标签。
不能由来源支持的字段必须标注 `unknown` 并降低允许用途。

K1 只接受 `DirectorProblemSet`，可取 0–3 张主卡、1 张冲突卡和 1 张反模式卡，禁止提供 camera/edit
答案。K2 只能在 `BlockingCommit` 通过后，以空间、行为、注意力和隐藏信息问题检索最小执行卡。无匹配是
合法结果，不能退化为“对白 → 正反打”模板。

优先级：用户/项目事实 > 批准人物/空间/声音资产 > Episode/Scene 意图 > 目标能力证据 > 已验证生成
证据 > 高置信知识 > 中低置信知识与美化偏好。算法暴露冲突，不自动裁决艺术赢家。

## 7. VEC、Storyboard 与 Video 同源编译

VEC 保存 canonical timeline、segments、shots、boundaries、visual beats、blocking/camera/visibility/light/
performance/prop/audio/reference 状态、fidelity class、freedom corridor 和 handoff。每个 Shot 至少绑定：

```text
dramatic_function, attention_target, information_action, blocking_state_id,
axis_id, camera_side, screen_order, shot_size, focal_intent, camera_pose,
camera_motion, composition, lighting, performance, gaze_target, prop_state_ids,
dialogue_event_ids, start_state_id, end_state_id, transition_in, transition_out,
decision_ids, selected_capsule_ids, freedom_corridor
```

Storyboard 是 Visual Beat/Boundary 的选择性视图：起幅、新 Shot 入场状态、注意力/位置/视线/持手/朝向变化、
运镜中的构图意义阶段、内部切镜两侧、关键表演和落幅都必须有来源。它不是逐秒截图，格数既不等于秒数也
不受“只能两格”限制。

Video Prompt 由同一 Timeline、Shot、Beat、Boundary、AudioEvent、ReferenceBinding 编译。它只描述本段的
局部时间、动作相位、摄影路径、切换、对白、声音与音色、可执行引用职责和正向物理闭合；不得从故事板图片
重猜镜头、为流畅而新增动作/切镜、重复已说台词，或泄漏 global/state/hash/review 文字。

两份 Manifest 必须共同记录 `contract_fingerprint`、`blocking_commit_hashes`、`decision_ids`、
`source_node_ids`、编译器/Adapter 版本、reference/audio fingerprint。AST 比较必须覆盖拓扑、tick、phase、
景别、运动、构图、注意力、人物槽位/轴线/方向/视线、道具、参考、音频、起落幅和 freedom corridor。

## 8. 参考资产、连续性与声音

每次生成使用“最小职责包”，优先级为：人物身份与服装 > blocking/layout > 高风险道具几何 > 必要场景布局
> 经 A/B 验证有效的构图或运动辅助。相同资产可以在 Storyboard 和 Video 使用相同 role binding，但可由
Adapter 去重上传；绝不由图片编号赋权。

人物服装、站位、视线和道具状态必须在 VEC 结构字段中绑定。上一段结束状态可作为事实连续性证据，不是
强制首帧模板；若边界模式为 `hard_cut`，下一段的开场取景可以不同，但人物身份、服装、空间关系、道具
和叙事状态仍必须连续。每段角色对白必须绑定对应音色 AssetBinding。

## 9. 双模式审查、媒体验收与归因

`MUTE_VISUAL_LOGIC` 在去除对白/音色/旁白的状态投影中提问：权力、空间控制、注意力和关系变化是否可见；
是否只能由台词解释；是否过早泄露隐藏信息。

`DIALOGUE_REDUNDANCY` 在对白事件和去镜头术语的视觉 beat 摘要中提问：是否逐句复读、镜头是否只跟随
说话者、是否存在无意义反应/插入或重复对白。两种模式都允许停顿、持镜和硬切，只要求它们服务当前戏剧。

文本审查只能到 `TEXT_VALIDATED`。实际故事板需要检查 panel 对应、身份/服装/数量、空间、视线、持手、
可见面、构图、注意力、镜头路径和泄漏；视频需要用 FFmpeg 提取开场、beat、边界两侧和落幅帧，检查相同
硬不变量、切镜顺序、动作相位、运镜、声音/音色与未计划可见事件。

每个媒体失败需要一个 `OutcomeAttribution`：`fact`、`episode_intent`、`scene_intent`、`blocking`、
`decision`、`VEC_field`、`reference`、`adapter` 或 `generation_variance`。一次抽卡失败不能自动否定导演，
也不得重写冻结的无关 Segment。

## 10. 模块边界、低耦合与性能

模块依赖固定为：

```text
facts → episode_direction → scene_intent → knowledge → blocking → decisions/VEC
     → projection → adapter → validation → evidence
runtime（事务、缓存、锁、恢复）只编排，不能选择镜头或审美。
```

投影、Markdown、哈希、Adapter 路由、结构 Gate 和依赖失效均为本地确定性工作。缓存以 Episode facts、
SceneIntent、BlockingCommit、DecisionPacket、VEC 和投影的内容 hash 为键；只修改一个 beat/shot/boundary 时
只失效其下游。正常单场不超过 3 次强模型调用；本地 Schema/编译/同源 P95 各小于 5 秒；热缓存重编译不
调用 Director；Adapter-only 改动不得使 Director、知识或 Storyboard 失效。

## 11. R3.2 受控协调与 DDO 工作包

### 11.1 R3.2 必须先完成的真值化任务

- `BCR-01`：保留冻结 686 为历史数；建立版本化 cohort ledger，证明当前 781 = reconstructed candidate
  generic 686 + 已登记历史 EP35 95，且无未解释第三集合。不得声称 reconstructed cohort 就是冻结日的
  精确 ID 集合。
- `ECR-01`：建立 70 行逐项 evidence ledger。每行有 `disposition`、依赖闭合、当前证据或经批准 waiver；
  `all_70_reconciled` 与 `all_70_evidenced` 必须是两个不同的 Gate。
- `ACC-01`：明确控制器可机器生成的本地终态及其证据，不得把未实现的 `LOCAL_VNEXT_READY` 写成已通过。

以上三项可揭示未完成，不能用 waiver 或历史 checkbox 伪装实现。只有它们使 R3.2 所有既定检查可诚实
满足后，才可结束 R0–R3。

### 11.2 受 R3.2 之后控制的 DDO 队列

```text
DDO-0 / WP-0：同步 v1.1 锁、冻结决策 Golden/Holdout/验收合同
DDO-1 / WP-2：离线知识原子化、来源、置信度、禁用条件与反模式
DDO-2 / WP-2：EpisodeDirectionState、SceneIntent、K1 与缓存
DDO-3 / WP-3：BlockingCommit、SceneVisualCurve、K2、候选/决策/VEC 绑定
DDO-4 / WP-5：双模式 EditorialReview、DP 安全投影和范围化回流
DDO-5 / WP-4/6：双编译、字段依赖失效、性能、泄漏与媒体归因
DDO-6 / WP-7：Shadow、Holdout、真实媒体小样与用户批准门
```

DDO 队列必须以独立、严格 JSON 的任务表创建；不得把它塞回历史 R0–R3 表或篡改已完成证据。

## 12. 验收与完成定义

自动硬门：Schema fail-closed；BlockingCommit 前置；决策/知识/冲突/VEC 字段回指；Storyboard/Video AST
同源；参考和音色绑定；时间/Hash/状态/文学泄漏扫描；对白去重；轴线/镜像/方向/视线/道具字段一致；
确定性编译和范围化失效。

Golden 与 Holdout 必须分离：Golden 校准已验证控制信号，Holdout 在胶囊/模板完成前冻结，检验不同权力、
空间、隐藏信息下不会复制同一覆盖模板。消融测试比较 no-knowledge、K1-only、K1+K2，不接受“文本更长”
作为改善证据。媒体样本至少覆盖双人离场目送、手机/屏幕/持手、内部硬切、连续运镜、画幅重构、画外声音
与道具表面揭示。

重构仅在以下全部为真时完成：真实 Director 在未知剧本上产生 E0–B1 链和 VEC；知识有选择、适用性和
冲突证据；所有历史回归通过；Golden、Holdout、消融、变异和性能目标通过；实际 Storyboard/Video 的
硬不变量通过且预览阈值经真实媒体校准；崩溃恢复/并发/回滚通过；用户明确批准生产切换。

在实际媒体验收前，最高可用表述始终是 `PLANNED_PREVIEW`。
