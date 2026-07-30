# MODE:P vNext LOOP — 最终目标与运行约束规范

> 状态：设计基线（经用户确认，尚未切换为生产实现）
>
> 适用范围：MODE:P vNext 的知识使用、导演决策、故事板提示词、视频提示词、审查、交付与 Golden Set 验收。
>
> 本文件用于约束最终目标，防止重构再次偏向格式工程、理论摄影规则或旧管道复刻。
>
> 高权重证据附件：GOLDEN_SET_EVIDENCE_REPORT.md
>
> 完整知识库审计附件：KNOWLEDGE_BASE_AUDIT.md
>
> 遗漏项与反向失效审计附件：MODE_P_VNEXT_OMISSION_AUDIT.md
>
> 生产审计附件：MODE_P_VNEXT_PRODUCTION_AUDIT.md

---

## 0. 规范权威与解释顺序

### 0.1 证据权重

出现设计冲突时，按以下顺序裁决：

1. 用户对真实生成结果的明确评价。
2. 已配对的真实数据：故事板提示词、实际故事板、视频提示词、实际视频。
3. 当前项目真实运行结果与可复现测试。
4. 当前 MODE:P 代码和运行约束。
5. 旧管道文件、历史模板和旧文档。
6. 通用电影理论与未经本项目验证的经验。

低权重资料不得推翻高权重生成证据。

### 0.2 当前高权重样本

本规范首批以四组数据为基线：

- 第八集枪管：连续注意力收缩与管内落幅。
- 第六集观众席：一个生成段内的三段内部切镜。
- 第六集贫民窟窄巷：忠实于叙事拓扑但优化连接方式。
- 第六集备赛区擦肩：构图成功、时序与人物行为偏移的诊断样本。

### 0.3 规范词义

- 必须：不满足即阻断或验收失败。
- 应当：默认执行；偏离必须有明确理由。
- 可以：允许但不要求。
- 禁止：任何实现不得执行。
- 运行时：从文本剧本进入 MODE:P，到交付故事板提示词和视频提示词。
- 离线：不属于 MODE:P 文本生成必需路径的知识整理、媒体分析和 Golden Set 验收。

---

## 1. 最终目标

MODE:P 的最终目标是：

> 让一个文本大模型成为真正承担导演判断的 Director。它在最小、可信、与当前问题相关的知识上下文中，设计运镜、构图、光影、表演、注意力和画面切换；确定性算法将同一导演设计编译成可直接使用的故事板提示词和视频提示词；故事板应能够预测视频的主要效果，同时允许模型在不改变叙事硬约束的范围内优化连接方式。

### 1.1 最重要的优化原则

1. 扩大离线知识源，缩小单次运行知识。
2. 增强导演判断，减少格式劳动。
3. 让算法负责确定性，让大模型负责创意。
4. 让故事板成为时间—构图—运动控制图，不是装饰性分镜清单。
5. 让视频提示词继承故事板的叙事拓扑和运动设计，而不是重新创作另一套镜头。
6. 用真实生成结果和用户评价校正系统，不用文档自洽代替实际效果。

### 1.2 非目标

本重构不以以下事项为目标：

- 恢复整套旧管道。
- 让最终提示词最短。
- 消除所有重复信息。
- 让算法自动创作镜头。
- 在单次运行中加载完整知识库。
- 强制所有场景使用逐秒或稀疏关键帧。
- 强制视频逐像素复制横版故事板。
- 用传统摄影理论否定已经被用户认可的 AI 运镜。
- 把 FFmpeg、图片解析或视频解析加入文本 Director 的必需运行路径。
- 仅凭测试通过、文档完成或格式正确宣布系统完成。

---

## 2. 不可突破的运行边界

### 2.1 MODE:P 必须是文本管道

MODE:P 的 Director 和 DP 使用文本大模型。运行时只允许读取：

- 剧本及其结构化文本事实。
- 项目 Visual Bible 和连续性文本。
- 人物、场景、道具、音频和故事板的文字资产卡。
- 素材 ID、路径、哈希、状态和职责。
- 经过检索的文本知识包。
- 用户提供的文字批准、纠正和评价。
- 当前 Master、派生文本和确定性检查报告。

运行时不得假装读取或理解：

- 图片像素。
- 视频画面。
- 音频波形。
- FFmpeg 联系表。
- 未转换成文字报告的多模态结果。

### 2.2 媒体只以引用身份进入

MODE:P 可以生成如下引用：

- @图片1
- @角色名
- @场景名
- @道具名
- @音频1

每个引用必须带有明确职责。视频生成平台读取真实媒体，MODE:P 只管理文字职责和绑定状态。

### 2.3 离线媒体分析不属于运行依赖

FFmpeg、图片对照和多模态评价可以用于：

- 研究历史样本。
- Golden Set 验收。
- 生成结构化文字反馈。
- 记录真实切点、时长、帧率和闪烁等机械证据。

MODE:P 在没有媒体解析器时仍必须完整生成故事板提示词和视频提示词。

### 2.4 可见性输出边界

剧本事实成立，不等于该事实可以进入当前镜头的视觉生成正文。MODE:P 必须把信息分成：

- 当前机位真实可见的表面、人物、动作、光线和空间。
- 被人物、道具、遮挡或取景完全挡住的状态。
- 只在叙事层成立、但当前画面不可见的信息。
- 只属于声音时间线的信息。

只有第一类和 Director 为其写出的正向物理闭合可以进入正向视觉正文。其余信息保留在 Master、声音时间线或审查字段中，不得因“帮助模型理解剧情”而泄漏进画面描述。

示例：人物正在手机上打游戏，但摄影机只看见手机背面。正向视觉正文应描述实心不透明后壳、镜头模组、手指的操作节奏和屏幕平面朝向，不描述游戏画面。游戏身份由可见动作、音轨、对白或另一个真正看见屏幕的镜头建立。

针对性禁止项只能作为第二层保险，不能替代可见性白名单和正向物理闭合。若模型会把否定句中的名词当作生成目标，负向内容不得进入该模型的正向 Render Payload。

---

## 3. 角色与职责

### 3.1 Orchestrator

Orchestrator 是确定性程序，负责：

- 剧本导入、行号、场景边界和事实骨架。
- 会话、版本、哈希、缓存和依赖失效。
- 触发同一持久 Director 的不同阶段。
- 构造知识检索请求。
- 加载已选择的小型知识包。
- 解析和验证 Master 的结构。
- 编译故事板提示词与视频提示词。
- 生成 DP Packet。
- 路由 DP 反馈。
- 管理用户批准状态。
- 交付和遥测。

Orchestrator 禁止：

- 选择机位、焦段、景别或运镜。
- 自动增删 Visual Beat。
- 自动选择 Storyboard Panel。
- 自动缩短保持时间。
- 改写导演文字。
- 删除括号、纠偏、距离、色温、时间或方向信息。
- 把一个内部切镜擅自改成多个生成文件。

### 3.2 Persistent Director

每个分集只使用一个持久 Director 身份。Director 负责：

- 场景诊断。
- 导演问题识别。
- 对知识包进行综合而不是复制。
- 全场调度。
- Generation Segment 规划。
- 内部 Cinematic Shot 设计。
- 运镜、构图、光影、表演、声音和切换。
- Visual Beat 和 Storyboard Panel 设计。
- Fidelity Contract。
- 用户文字纠正的吸收。
- DP 反馈修订。

Director 不负责：

- 编号和哈希。
- 最终格式重复排版。
- 生成 Manifest 技术字段。
- 解析图片或视频。
- 证明自己引用了哪个规则 ID。

### 3.3 DP

DP 是新的独立文本审查角色，只读取确定性生成的 `DP_VIEW`：

- 剧本事实。
- 空间和连续性事实。
- 能力配置。
- Master 中面向审查的 Fidelity、Visibility、Handoff 和时间状态投影。
- 双输出派生文本。
- 参考职责。

DP 检查：

- 戏剧职责是否清楚。
- 摄影路径在空间中是否成立。
- 内部镜头结构是否可执行。
- 微表演是否能被当前机位看见。
- 视线、身体朝向和禁止行为是否矛盾。
- 摄影机是否只能看到所描述物体的对应表面。
- 被遮挡、画外或只存在于叙事层的信息是否泄漏进视觉正文。
- 高风险物体是否有正向物理闭合，而不是只依赖否定句。
- 关键动作是否有足够时间。
- 起幅、过程、落幅是否完整。
- 故事板与视频是否来自同一导演设计。
- LOCKED、ELASTIC、OPTIMIZABLE 和 FORBIDDEN 是否分类合理。

DP 不加载 Knowledge Packet、Director 推理、历史 DP 反馈、未提交草稿或创作案例全文；不重新导演场景，不以个人口味否定导演选择。每轮 DP 使用新上下文，DP_VIEW 的字段白名单和 hash 写入 DP Packet Manifest。

### 3.4 User

用户拥有最终导演评价权，负责：

- 确认剧本和项目事实。
- 批准或退回实际故事板。
- 提供故事板纠正文字。
- 评价实际视频是否达到预期。
- 批准项目经验晋升。
- 批准生产切换和旧文件归档。

### 3.5 Offline Knowledge Curator

离线知识整理器负责：

- 读取大型原始知识源。
- 蒸馏微内核和决策卡候选。
- 建立适用与不适用条件。
- 关联真实案例。
- 运行迁移测试。
- 生成候选，不直接修改正式知识。

### 3.6 Optional Render Evaluator

可选的离线 Render Evaluator 可以使用 FFmpeg 或多模态模型，但只输出结构化文字证据。它不是 MODE:P 运行角色。

---

## 4. 核心产物

### 4.1 输入产物

- SCRIPT_STRUCTURE.json
- SCRIPT_FACTS.md
- EPISODE_VISUAL_BIBLE.md
- EPISODE_CONTINUITY_LEDGER.md
- ASSET_INDEX.json
- 文本资产卡
- SD2_CAPABILITY_PROFILE.json
- 用户视觉约束

### 4.2 运行时中间产物

- SCENE_DIAGNOSIS.json
- KNOWLEDGE_QUERY.json
- KNOWLEDGE_PACKET.md
- DIRECTOR_MASTER.md
- SEGMENT_MANIFEST.json
- DP_PACKET.md / DP_PACKET.json
- DP_FEEDBACK.md
- STORYBOARD_APPROVAL.md
- CORRECTION_IMPACT.json
- MODEL_INVOCATION_SNAPSHOT.json

### 4.3 最终产物

- STORYBOARD_PROMPT.md
- VIDEO_PROMPT.md
- RENDER_PAYLOAD.txt 或平台要求的等价载荷
- RENDER_PAYLOAD_MANIFEST.json
- DELIVERY_MANIFEST.json

### 4.4 离线证据产物

- RENDER_OBSERVATION.md
- RENDER_METADATA.json
- GOLDEN_EXPECTATION.json
- GOLDEN_RESULT.md
- EXPERIENCE_CANDIDATE.md
- STORYBOARD_RUN_RECORD.json
- RENDER_RUN_RECORD.json
- VIDEO_RESULT_REVIEW.md

离线证据产物不得成为文本 MODE:P 正常运行的强制输入。

---

## 5. 知识架构

### 5.1 K0 原始知识源

K0 存储全部离线来源：

- 导演教材。
- 运镜、构图、光影、剪辑、表演知识。
- 模型能力资料。
- 项目参考资料。
- 旧管道中仍有价值的判断。
- 真实故事板和视频配对案例。

K0 必须细分为：

- `source`：可提取原子 Claim 的原始来源。
- `archive`：被新版覆盖但为历史溯源保留的旧版。
- `capability_candidate`：尚未绑定目标模型实测的能力声明。
- `legacy_method`：旧蒸馏或旧管道方法。
- `quarantine`：已被反驳、来源不明、存在伪精度或容易造成伤害的内容。
- `golden_evidence`：真实 Storyboard-Video 配对与用户评价。

K0 只读，不在运行时直接加载。重复来源不得重复加权；当前 v4 作为 v5 的历史归档，不参与运行时召回。

### 5.2 K1 导演微内核

K1 始终加载，但总量必须严格控制。它只保留以下稳定判断顺序：

1. 当前戏剧变化是什么。
2. 观众注意力从哪里转移到哪里。
3. 人物和道具怎样在空间中调度。
4. 摄影机为什么停留、移动或切换。
5. 起幅和落幅分别承担什么信息。
6. 表演是否可见。
7. 光源是否有物理锚点。
8. 当前机位实际看见哪些表面，哪些信息被遮挡或只在叙事层成立。
9. 模型会不会把被提及但不可见的信息补进画面，如何用正向物理状态封闭自由度。
10. 哪些必须锁定，哪些可以优化。
11. 当前模型复杂度如何降低。

K1 不保存大段案例，不保存固定镜头答案。

K1 也不保存会随平台变化的具体能力上限。它只保存“先读取 Capability Profile 再裁决”的接口原则。

### 5.3 K2 导演决策卡

每张决策卡只解决一个导演问题。推荐字段：

- knowledge_id
- title
- decision_domain
- director_question
- applies_when
- non_applicability
- decision_relation
- linked_domains
- director_variables
- observable_failures
- model_adaptation
- visibility_risk_class
- positive_closure_requirements
- negative_routing_constraints
- source_refs
- source_kind
- claim_type
- evidence_tier
- evidence_records
- options_and_tradeoffs
- counterexamples
- must_not_decide
- contradicts
- supersedes
- status
- last_reviewed_at
- version

决策卡必须表达：

> 意图或问题 -> 成立条件 -> 联动判断 -> 需要 Director 决定的变量 -> 可观察失败

决策卡禁止直接规定当前场景必须使用某个镜头答案。

旧知识的 P0-P3 不直接继承为 vNext 的运行权威。所有条目必须先拆成原子 Claim，完成来源绑定、去重、适用/不适用条件、反例和冲突审查，才能成为 active 决策卡。

以下风险必须能够由 K2 决策卡覆盖，但卡片仍只提供判断条件，不代替 Director 设计：

- 手机、电脑、电视和仪表屏幕。
- 镜子、玻璃、金属反射和水面倒影。
- 透明、半透明或模型容易错误透明化的物体。
- 画内文字、UI、聊天状态和通知。
- 门窗、孔洞、通道和画外声源。
- 只在剧情中存在、但当前机位看不见的人物或事件。

### 5.4 K3 真实案例模式

每个案例必须包含：

- 剧本与场景条件。
- 原导演设计。
- 故事板提示词。
- 实际故事板。
- 视频提示词。
- 实际视频。
- 用户质量评价。
- 成功机制。
- 可接受偏移。
- 严重偏移。
- 不可直接迁移的偶然因素。

案例模式必须区分：

- invariants：可继承的不变量。
- variables：当前场景必须重新设计的变量。
- failure_signals：可观察失败。
- user_quality_label：用户主观评价。

### 5.5 K4 项目导演偏好

K4 只对当前项目生效，可以由用户一次确认后启用：

- 目标故事板格式。
- 目标视频提示词格式。
- 用户对 AI 运镜的审美判断。
- 可接受的偏移范围。
- 角色、场景和叙事连续性偏好。

K4 不自动晋升为通用核心知识。

### 5.6 知识证据等级与冲突裁决

SCRIPT_FACTS、Continuity、用户明确要求和已批准 Storyboard 是当前任务事实，不属于可被知识投票推翻的条目。知识与事实冲突时直接排除。

正式知识使用以下等级：

- `E5`：用户批准的真实 Storyboard-Video 配对案例，含质量评价。
- `E4`：目标模型/平台可复现能力测试或当前运行时可复现测试。
- `E3`：可追溯的一手电影、视觉、表演来源，尚未被本项目验证。
- `E2`：项目内人工综合、二手整理或跨来源归纳。
- `E1`：旧管道规则、社区声明或无上下文经验。
- `E0`：已被反驳、来源不明或危险伪精度；只能隔离。

高等级不等于当前场景必须采用。证据等级只影响可信度与召回次序，`applies_when`、`non_applicability` 和当前事实仍具有否决权。

证据等级不得替代适用性判断。召回前必须独立通过：

- `target_model_match`
- `generation_mode_match`
- `aspect_match`
- `reference_mode_match`
- `recency_status`
- `replication_scope`
- `project_relevance`

旧模型上的 E5 成功案例不能覆盖当前目标模型已经验证的不兼容能力；Capability 的目标匹配与时效属于硬过滤，不参与创意投票。

同等级知识冲突时，检索器不得静默选择胜者。它必须输出冲突字段、最多两个相关选项和需要 Director 裁决的问题。

### 5.7 知识状态与晋升

K2/K3 至少使用：`candidate → active → repeated → validated → deprecated/rejected`。

- 大模型只能生成 candidate。
- active 需要人工审查。
- repeated 需要多条独立 RenderEvidence。
- validated 需要跨场景证据、用户批准和回归通过。
- 模型能力变化后，依赖该能力的条目回到待复验或缩小适用范围。

现有 `render_evidence.py` 和 `knowledge_curator.py` 的证据、观察、候选和回滚机制应被迁移扩展，不另建无证据自动学习器。

---

## 6. 场景诊断与知识检索

### 6.1 诊断先于检索

Director 第一次调用只读取事实和 K1，输出 SCENE_DIAGNOSIS。此阶段禁止直接完成镜头设计。

SCENE_DIAGNOSIS 必须包含：

- dramatic_change
- attention_path
- spatial_topology
- performance_visibility_problems
- visibility_contract_problems
- generative_leakage_risks
- camera_problems
- composition_problems
- lighting_problems
- editing_problems
- generation_segment_problems
- reference_problems
- model_risks
- user_style_relevance
- knowledge_questions
- decision_domains
- creative_decisions_reserved_for_director

### 6.2 诊断必须是问题，不是答案

允许：

- 如何从人物视线转移到被看物体。
- 关键微表演在背影机位下是否可读。
- 手机背面机位是否会诱发模型补出被遮挡的屏幕内容。
- 这个内部切镜是否应留在同一生成段。

禁止：

- 必须使用 50mm。
- 必须使用三镜头。
- 直接写完整时间轴。

### 6.3 检索器职责

检索器只依据显式诊断字段：

1. 过滤不满足空间、人物、运动和模型条件的条目。
2. 按导演问题和决策域匹配。
3. 排除 non_applicability 命中的条目。
4. 优先项目偏好和用户认可案例。
5. 选择互补而非重复的知识卡。
6. 输出选择原因和冲突提示。
7. 对同源、版本继承和跨胶囊重复进行去重。
8. 检查能力卡版本、验证日期和到期条件。

检索器不得从剧本关键词直接猜镜头答案。

Director Phase A 提交的是 `knowledge_questions` 和 `decision_domains`，不是最终胶囊路径。检索器根据条件返回决策卡；Director Phase B 可以采用、综合或拒绝卡片。算法不得把最高分卡片变成镜头答案。

### 6.4 知识包预算

单场默认预算：

- K1 微内核：约 1000-1500 中文字符。
- K2 决策卡：最多 8 张，每张约 100-300 字。
- K3 案例摘要：最多 2 个，每个约 200-500 字。
- K4 项目偏好：只加载与当前问题相关的小节。

超过预算时按顺序保留：

1. 当前剧情硬约束相关知识。
2. 表演可见性和空间可执行性。
3. Generation Segment 与切换问题。
4. 相机、构图和注意力问题。
5. 光影、材质和细节。

### 6.5 无匹配处理

没有匹配不是错误。只加载 K1，让 Director 从当前剧本设计。禁止回退到通用面对面、通用追逐或其他历史模板。

### 6.6 知识应用

Director 不在最终提示词中引用知识 ID。系统通过以下方式确认知识被应用：

- Master 回答了检索提出的导演问题。
- DP 检查设计结果是否解决可见风险。
- 真实生成结果验证判断是否成立。

知识是判断能力，不是输出装饰。

### 6.7 无损来源与可重放

每个入选卡必须能追溯到 K0 source locator、source hash、Claim 版本和人工审查状态。一个来源被多份旧文档复制时只算一份证据。

Knowledge Snapshot 必须保存候选、排除、去重、冲突、入选原因和预算。历史重放使用原快照，不重新检索。

---

## 7. 核心数据模型

### 7.1 Scene

Scene 是剧本意义上的场景。一个 Scene 可以包含一个或多个 Generation Segment。

### 7.2 Generation Segment

Generation Segment 是一次提交给视频模型的完整生成单元。

必须字段：

- segment_id
- duration
- canonical_timebase
- target_duration_policy
- dramatic_function
- attention_start
- attention_end
- generation_mode
- aspect_target
- reference_bindings
- shared_visual_anchors
- cinematic_shots
- visual_timeline
- storyboard_panels
- sound_timeline
- fidelity_contract
- visibility_contracts
- final_handoff
- fact_bindings
- prompt_dialect_id
- capability_snapshot_id

一个 Generation Segment 可以：

- 只有一个连续 Cinematic Shot。
- 包含多个内部 Cinematic Shot。
- 包含模型在同一视频内完成的硬切。
- 包含连续运镜、移焦、遮挡或画面重构。

### 7.2a Canonical Timeline

所有时间结构使用有理数 timebase 与整数 tick。禁止以浮点秒作为唯一机器事实。

硬规则：

1. 持续区间统一为 `[start_tick,end_tick)`。
2. 瞬时状态使用 `at_tick`，不得同时伪装成持续区间。
3. 相邻 Shot 的 `previous.end_tick == next.start_tick`。
4. Boundary 发生在一个精确 tick；该 tick 起属于 incoming Shot。
5. HOLD 必须占据非零区间并声明保持对象。
6. Segment 最后一个 Shot 的 end_tick 必须等于 Segment duration_ticks。
7. 人类可读秒数由编译器从 tick 确定性派生。
8. 输出帧率只有在 Capability 已验证时才能用于帧号映射；未知时使用时间容差，禁止伪造逐帧精度。

Canonical Timeline 至少包含：

- `ticks_per_second`
- `duration_ticks`
- `display_precision`
- `boundary_ownership: incoming`
- `output_fps_status: verified | unknown`
- `rounding_policy`

### 7.3 Cinematic Shot

Cinematic Shot 是电影语言中的镜头，不自动等于生成文件。

必须字段：

- shot_id
- segment_id
- start_time
- end_time
- narrative_job
- camera_position
- shot_size
- focal_intent
- camera_motion
- composition
- lighting
- performance
- visibility_contract
- entry_state
- exit_state
- fact_ids
- visibility_state_timeline

### 7.4 Internal Boundary

同一 Segment 内的相邻 Cinematic Shot 使用 Internal Boundary。

Boundary 类型：

- hard_cut
- match_cut
- motivated_cut
- continuous_reframe
- camera_transition
- focus_transition
- occlusion_transition

每个 Boundary 必须声明：

- at_tick
- preferred_execution
- fidelity_class
- outgoing_anchor
- incoming_anchor
- outgoing_state_id
- incoming_state_id

### 7.5 Visual Beat

Visual Beat 是时间轴上的可见变化。

Beat 类型：

- OPEN
- HOLD
- ACTION
- CAMERA
- FOCUS
- REVEAL
- REACTION
- CUT
- LIGHT
- SOUND_SYNC
- LANDING

每个 Beat 必须包含：

- at_tick 或 `[start_tick,end_tick)`
- shot_id
- visibility_state_id
- visible_state
- change_from_previous
- fidelity_class

HOLD 必须明确保持什么，不能只写“同上”而没有受控对象。

### 7.6 Storyboard Panel

Panel 类型：

- FREEZE：决定性状态。
- HOLD：相同状态持续。
- TRANSITION：运动路径或构图变化。
- CUT_BOUNDARY：切镜两侧。
- INTERVAL：一个时间区间内的单一连续变化。

Panel 必须引用 Beat 或 Boundary。程序不得自行选择 Panel。

格数不要求等于秒数，但必须覆盖：

- 完整起幅。
- 每次关键注意力转移。
- 主要动作阶段。
- 内部切镜。
- 运镜路径。
- 最终落幅。

### 7.7 Reference Binding

每个引用必须包含：

- asset_id 或平台标签。
- media_type。
- responsibility。
- priority。
- status。
- user_approved。
- content_sha256。
- asset_version。
- readonly_path 或受控 asset locator。
- platform_alias_or_slot。
- orientation_and_crop。
- valid_time_range。
- rights_or_user_confirmation。

职责可以是：

- identity
- wardrobe
- scene_layout
- material
- prop_shape
- composition_timing
- camera_motion
- audio_performance

同一职责存在多个素材时必须明确优先级。

同一职责存在视觉冲突时必须记录 `conflict_resolution`，不得仅按引用顺序猜测。实际 Render Payload 必须绑定平台别名/槽位与内容 hash，不能只保留 `@图片1` 之类人类标签。

### 7.8 Fidelity Contract

每个 Segment 必须同时包含四类：

#### LOCKED

改变即失败：

- 剧情事实。
- 事件顺序。
- 人物是否看向某人。
- 入画和离画条件。
- 道具归属。
- 运动方向。
- 必须出现的内部镜头。
- 最终揭示和落幅。

每条 LOCKED 必须引用 `fact_id`、用户约束 ID 或已批准 Storyboard 元素 ID。所有剧情关键事实必须出现在 `fact_bindings` 中，并声明：

- visible
- audio_only
- narrative_only
- not_in_segment
- locked_execution

行为、方向、是否看向、道具归属和事件顺序不得降级为 ELASTIC 或 OPTIMIZABLE。

#### ELASTIC

允许小幅变化：

- 非关键切点时间。
- 人物大小和位置的小幅变化。
- 精确焦段的视觉近似。
- 横版到竖版的语义重排。
- 自然微动。

#### OPTIMIZABLE

允许模型优化连接：

- 中间摄影路径曲线。
- 连续重构替代非必要硬切。
- 不改变节点的遮挡或移焦。
- 不改变落幅的节奏调整。

#### FORBIDDEN

可逐帧核验的失败事件。每条必须具体、单义、与正向设计不冲突。

### 7.9 画幅语义不变量

故事板与视频画幅不同时，必须锁定：

- 主体关系。
- 银幕运动方向。
- 前中后景层次。
- 注意力中心。
- 起幅和落幅对象。
- 关键负空间的叙事功能。

不得要求像素坐标完全相同。

每个跨画幅 Segment 还必须声明 `reframe_strategy`：

- protected_subjects
- protected_screen_order
- protected_eyelines
- protected_movement_direction
- protected_depth_layers
- protected_negative_space_function
- crop_safe_relationships
- mirror_flip_forbidden

画幅重构允许重新分配上下左右空间，不允许用镜像翻转破坏银幕方向。

### 7.10 Visibility Contract：可见性与生成泄漏契约

每个 Cinematic Shot 必须包含一个 Visibility Contract。低风险镜头可以填写 `not_applicable`，但必须说明不存在屏幕、反射、透明结构、画外叙事泄漏或其他高风险表面。

必须字段：

- visible_whitelist：当前机位允许进入视觉正文的实体、表面、动作、光线和空间。
- occluded_state：确实存在但被遮挡、背向摄影机或位于画框外的状态。
- narrative_only：剧本成立但当前画面不应直接可视化的信息。
- audio_only：只允许进入声音时间线的信息。
- positive_closure：Director 写出的正向、可见、可逐帧核验的物理闭合。
- leakage_risks：模型可能错误补出的实体、界面、倒影、文字、透明结构或画外事件。
- forbidden_qa：用于 DP、用户和离线验收的具体失败事件。
- negative_route：`inline_supported`、`separate_negative_channel`、`human_qa_only` 三者之一。
- visibility_states：按 Canonical Timeline 分段的动态可见状态。

硬规则：

1. 正向视觉正文只能从 visible_whitelist、positive_closure 和对应 Visual Beat 派生。
2. occluded_state、narrative_only 和 audio_only 不得映射到正向视觉正文。
3. positive_closure 必须描述镜头真实看见的物理状态，避免重复命名隐藏内容。
4. forbidden_qa 不能成为唯一防线；存在 leakage_risks 时必须同时存在 positive_closure。
5. negative_route 必须与 Capability Snapshot 的负向指令能力一致。
6. 镜面、屏幕、玻璃、文字、UI、门窗和画外事件未声明 Visibility Contract 时阻断。
7. 当前机位若只看见物体背面，不得同时描述其正面内容，除非设计中存在可验证的镜面、透明或中介成像路径。
8. 每个 Visibility State 必须有 `valid_time_range`，并由对应 Visual Beat 引用。
9. 揭示、遮挡、反射路径建立/断开或物体翻转必须建立 Visibility Boundary。
10. 后一状态允许出现的信息不得提前进入前一状态的正向正文。
11. 摄影机运动的中间路径也必须满足可见性契约，不能只检查起幅和落幅。

### 7.10a Structured Handoff Contract

每个 Shot 的 entry_state、exit_state 以及 Segment 的 final_handoff 至少保存：

- 人物位置、身体朝向、视线和动作阶段。
- 道具归属、位置、朝向和状态。
- 摄影机侧位、运动阶段和焦点目标。
- 主光位置、方向和连续状态。
- 当前可见表面与 Visibility State ID。
- 声音是否延续、提前进入或硬切。

这些状态由 Director 创作；算法只检查相邻 ID、枚举和明确字段是否连续，不替 Director 设计交接。

典型手机背面镜头：

~~~yaml
visible_whitelist:
  - 实心哑光深色手机后壳
  - 镜头模组
  - 握持手机的双手
  - 双拇指不规则交替轻触和短距离滑动
occluded_state:
  - 手机正面始终朝向人物并由机身完全遮挡
narrative_only:
  - 人物正在进行的具体游戏内容
positive_closure:
  - 后壳在整个镜头中保持完整、不透明、无反射的实体表面
leakage_risks:
  - 后壳被错误透明化
  - 界面被错误叠加到后壳或画面
forbidden_qa:
  - 当前镜头出现任何未经设计的界面或游戏内容
negative_route: human_qa_only
~~~

---

## 8. DIRECTOR_MASTER vNext

### 8.1 单一创作源

Master 是唯一导演设计源。所有创造性句子由 Director 写入 Master。

派生器只能：

- 复制。
- 排序。
- 编号。
- 映射。
- 排版。

### 8.2 推荐结构

~~~
# DIRECTOR_MASTER vNext

## 场景职责
戏剧变化：
注意力路径：
段末结果：

## Generation Segment G01
时长：
生成模式：
画幅目标：

### 参考职责

### 共享视觉锚

### Fidelity Contract
LOCKED:
ELASTIC:
OPTIMIZABLE:
FORBIDDEN:

### Fact Bindings
FACT_ID:
RENDER_POLICY:

### Canonical Timeline
TIMEBASE:
DURATION_TICKS:
BOUNDARY_TICKS:

### Shot Visibility Contracts
SHOT_ID:
VISIBLE_WHITELIST:
OCCLUDED_STATE:
NARRATIVE_ONLY:
AUDIO_ONLY:
POSITIVE_CLOSURE:
LEAKAGE_RISKS:
FORBIDDEN_QA:
NEGATIVE_ROUTE:

### Dynamic Visibility States
STATE_ID:
VALID_TIME_RANGE:
VISIBLE_SURFACES:
OCCLUSION_OR_REFLECTION_PATH:
BEAT_IDS:

### 内部镜头拓扑

### 统一视觉时间线

### 故事板格计划

### 声音时间线

### 段末交接
[人物/道具/摄影机/焦点/光源/可见表面/声音状态]

## 故事板批准
素材：
状态：
用户纠正：
~~~

### 8.3 创意只写一次

Director 在视觉时间线写 visible_state。Storyboard Panel 只补充：

- 取用哪个状态。
- Panel 类型。
- 红、蓝、绿、橙标注内容。

视频编译器读取完整时间线。故事板编译器读取显式 Panel 计划。二者不得各自重新创作。

### 8.4 有效冗余由编译器生成

编译器可以把同一信息重复输出为：

- 编号含义。
- 阶段标题。
- 每秒状态。
- 箭头说明。
- 段末交接。

这种重复是控制信号，不视为无效冗余。

---

## 9. 主运行 LOOP

### Step 0：启动与锁定

Orchestrator：

1. 创建或恢复分集会话。
2. 锁定唯一 Director 身份。
3. 验证剧本、项目和能力配置。
4. 记录版本与哈希。
5. 确认用户视觉约束。
6. 验证 Prompt Dialect、Capability 必填字段和复验状态。
7. 计算完整请求上下文预算并预留模型输出空间。

阻断条件：

- 剧本文件缺失。
- 场景边界不可确定。
- 运行时能力配置自相矛盾。
- 会改变剧情事实的关键输入缺失。
- 目标平台 Adapter 或关键 Capability 字段未知。
- 任何阶段只能通过静默截断才能装入上下文。

### Step 1：剧本事实

同一 Director 填写 SCRIPT_FACTS：

- 事件。
- 对白。
- 连续性入口。
- 角色和道具事实。
- 未确定项。
- 每条事实的稳定 fact_id、原文行号和事实类型。

本阶段禁止镜头设计。

### Step 2：分集视觉基线

Director 建立或更新：

- EPISODE_VISUAL_BIBLE。
- EPISODE_CONTINUITY_LEDGER。

分集基线只定义跨场稳定关系，不预先规定每场镜头。

### Step 3：场景诊断

Director 读取当前场景事实和 K1，输出 SCENE_DIAGNOSIS。

必须提出：

- 当前注意力路径。
- 空间与视线问题。
- 表演可见性问题。
- 运镜、构图、光影和剪辑问题。
- Generation Segment 结构问题。
- 模型风险。
- 可见性契约问题与生成泄漏风险。

### Step 4：知识检索

Orchestrator：

1. 将诊断字段转换为 KNOWLEDGE_QUERY。
2. 检索 K2、K3 和相关 K4。
3. 过滤不适用知识。
4. 控制预算。
5. 生成 KNOWLEDGE_PACKET。
6. 在证据等级排序前执行目标模型、生成模式、画幅、时效和项目适用性硬过滤。

### Step 5：Director 设计

恢复同一 Director，输入：

- 场景事实。
- Visual Bible 和连续性。
- 资产文字卡。
- KNOWLEDGE_PACKET。
- 用户视觉约束。

Director 输出完整 DIRECTOR_MASTER。

设计顺序必须是：

1. 戏剧变化。
2. 注意力路径。
3. 空间调度。
4. Generation Segment。
5. 内部 Cinematic Shot。
6. 起幅、过程、落幅。
7. 运镜、构图、光影、表演和声音联动。
8. 每个 Shot 的 Visibility Contract。
9. 动态 Visibility State 与 Canonical Timeline 绑定。
10. Fact Bindings 和结构化 Handoff。
11. Storyboard Panel。
12. Fidelity Contract。
13. 负向内容路由。

### Step 6：确定性预检

程序检查：

- Segment 时长与时间范围。
- Shot 归属和内部 Boundary。
- Beat 单调递增。
- tick 区间为半开区间且连续，Boundary 归属单义。
- 起幅与尾节点。
- HOLD 的受控对象。
- Panel 引用存在。
- 参考职责完整。
- 每个 Shot 的 Visibility Contract 存在。
- 高风险表面具有 positive_closure。
- narrative_only 和 audio_only 未映射到正向视觉正文。
- negative_route 与能力配置一致。
- 每个剧情关键 fact_id 已分类并绑定。
- 相邻 Entry/Exit/Handoff 状态完整且无确定性冲突。
- 每个 Beat 引用有效时间范围内的 Visibility State。
- 参考资产 hash、平台槽位和职责完整。
- 完整模型请求未发生静默截断。
- LOCKED、ELASTIC、OPTIMIZABLE、FORBIDDEN 不为空且不重复。
- 未裁决分支。
- 占位符。
- 双输出可派生性。

程序不得检查“镜头是否有导演感”。

### Step 7：双输出草案

编译器生成：

- STORYBOARD_PROMPT 草案。
- VIDEO_PROMPT 草案。

视频草案此时可以缺少实际故事板素材绑定，不得作为最终交付。

### Step 8：DP 审查

DP 审查：

- 叙事。
- 空间。
- 摄影路径。
- 构图与注意力。
- 光源。
- 表演可见性。
- 表面朝向、遮挡关系和可见性白名单。
- 叙事信息、画外信息和声音信息是否泄漏进画面。
- 生成泄漏风险是否由正向物理闭合控制。
- 内部切镜。
- 时间可读性。
- Fidelity 分类。
- 双输出一致性。

输出只能是：

- READY。
- 定向问题。
- 输入阻断。

### Step 9：定向修订

同一 Director 只修改：

- 被引用的 Segment、Shot、Beat、Panel 或 Fidelity 条目。
- 受影响的相邻 Boundary。

修改后重新运行预检、派生和新一轮 DP。

禁止用整个场景重写掩盖局部问题。

### Step 10：故事板提示词交付

DP READY 后交付 STORYBOARD_PROMPT。

用户在外部图像模型生成故事板。

### Step 11：用户故事板批准

用户提供：

- 故事板素材 ID 或路径。
- approved 或 revise。
- 可选文字纠正。
- 纠正影响级别确认。

示例：

~~~
状态：approved
素材：@图片1
纠正：
- 格11-13不能解释为漩涡，视频必须是金属内壁。
~~~

MODE:P 不解析故事板图片。

批准状态：

- `approved`：无纠正。
- `approved_with_clarification`：纠正只解释已存在画面。
- `revise`：纠正改变可见画面或镜头设计。

Director 提出 `correction_impact`，DP 核对，用户最终确认。新增可见实体、动作、方向、表面、切镜或时间节点不得归为 clarification。

### Step 12：视频纠偏

若用户提供纠正，恢复同一 Director，只允许更新：

- 故事板绑定。
- 视频纠正。
- 对应 FORBIDDEN 或正向物理说明。
- 对应 Shot 的 Visibility Contract。

不得因此擅自改变剧本或已批准的镜头拓扑。

纠正路由：

- `clarification_only`：可进入视频纠偏。
- `render_constraint_only`：只更新 Visibility/Capability 路由与 Render Payload。
- `storyboard_visible_change`：批准失效，回到 STORYBOARD_REVISION_REQUIRED。
- `topology_or_fact_change`：回到 MASTER_REQUIRED，重新预检、DP 和故事板批准。

### Step 13：最终视频提示词编译

只有以下条件满足才允许最终编译：

- DP READY。
- 故事板状态 approved。
- 故事板引用已绑定。
- 用户纠正已吸收。
- 引用职责可解析。
- Capability Snapshot 已声明负向指令路由。
- Prompt Dialect Adapter 已锁定。
- 所有参考资产平台槽位与 hash 已绑定。

编译必须同时生成：

- 人类审计用 VIDEO_PROMPT。
- 实际提交用 RENDER_PAYLOAD。
- RENDER_PAYLOAD_MANIFEST。

只有三者 hash 和字段路由一致时才能进入 RENDER_PAYLOAD_READY。

### Step 14：分集审查与交付

Episode Review 检查：

- 场景间连续性。
- 角色、道具和空间状态。
- Segment 交接。
- 声音桥和段末状态。
- 故事板与视频提示词格式一致。

通过后写 DELIVERY_MANIFEST。

### Step 15：离线真实结果反馈

用户生成视频后，可以选择：

- 只提交人工文字评价。
- 使用 FFmpeg 生成机械证据。
- 使用独立多模态审查生成文字报告。

反馈进入项目案例或经验候选，不自动修改正式知识。

若反馈用于 K3 或能力验证，必须同时提供 STORYBOARD_RUN_RECORD 或 RENDER_RUN_RECORD，绑定实际提交文本、资产、平台参数、任务ID、模型/产品版本和输出 hash。缺少运行记录的媒体只允许人工评价，不得晋升为 validated。

---

## 10. 故事板提示词编译契约

### 10.1 固定输出顺序

1. 场景标题和时长。
2. @人物、@场景、@道具参考。
3. 黑白线稿风格。
4. 标注颜色系统。
5. 共享视觉锚。
6. 编号含义。
7. 按阶段分隔的格描述。
8. 每格时间、景别、焦段和运镜。
9. 红、蓝、绿、橙标注。
10. 段末保持和交接。
11. 故事板禁止项。

Profile 不得改变这一外部格式。

### 10.2 时间规则

- 机器事实来自 Canonical Timeline 的整数 tick；正文秒数只是确定性显示值。
- 持续区间统一采用 `[start,end)`；瞬时状态使用 `at`。
- 切点 tick 起属于切入镜头，禁止前后镜同时占有同一持续帧。
- Panel 可以对应时间点或时间区间。
- Panel 数不必等于秒数。
- 保持状态必须显式存在。
- 关键入画延迟必须显示空区保持。
- 运镜必须至少显示起点、路径或中间状态、落点。
- 内部切镜必须显示切镜两侧。
- 平台帧率未知时不输出“精确第N帧”承诺，只输出经过能力配置允许的时间容差。

### 10.3 视觉规则

- 内容画面黑白。
- 彩色只用于导演箭头和标注。
- 箭头方向必须与文字一致。
- 编号必须与机位阶段一致。
- 不使用像素坐标锁定横竖画幅。
- 每格画面正文只能使用对应 Shot 的 visible_whitelist、positive_closure 和 Visual Beat。

### 10.4 禁止派生行为

- 不得删除括号。
- 不得删除“不是笑”“不是漩涡”等物理纠偏。
- 不得删除相同状态的保持格。
- 不得把时间区间强制展开成机械逐秒。
- 不得把逐秒设计强制压缩成少量关键帧。

### 10.5 故事板可见性派生

故事板模型同样可能把被提及但不可见的信息画出来。故事板编译器必须：

- 不把 narrative_only、occluded_state 的隐藏内容和 audio_only 复制进画格视觉正文。
- 保留必要的正向遮挡、表面朝向和实体材质说明。
- 把声音标注放在画格外的导演注释区，不把声源实体自动画进画面。
- 保留用户明确要求的可见性纠偏和可逐帧验收项。

故事板中若已经出现泄漏，用户纠正必须进入对应 Shot 的 Visibility Contract，并使旧批准失效。

---

## 11. 视频提示词编译契约

### 11.1 固定输出顺序

1. @上传参考图。
2. 每份参考的职责。
3. 编号含义。
4. 故事板箭头解释。
5. 故事板参考优先级。
6. 真人实拍或目标风格。
7. 共享光影和稳定性要求。
8. 按内部镜头和运动阶段分隔。
9. 完整时间线。
10. @音轨。
11. @禁止。
12. @转场。

### 11.2 参考职责

- 故事板：构图、机位、人物位置、运动方向、内部切镜、落幅。
- 角色：身份、面部、发型、服装。
- 场景：空间结构、材质、光源。
- 道具：形状、尺度、朝向和操作方式。
- 音频：对白、语气、节奏和环境声音。

人类可读标签必须经 Reference Binding 解析为内容 hash 和实际平台槽位。目标平台的 Prompt Dialect Adapter 只负责标签语法、字段位置、转义和通道路由，不得改写 Director 语义。

### 11.3 提示词必须只有一个首选执行

视频提示词不得输出多个备选镜头。OPTIMIZABLE 不转成“可以 A 或 B”，只用于结果验收。

### 11.4 允许针对性禁止项

允许 @禁止 区块。每条必须：

- 可逐帧核验。
- 对应剧情、身份、方向、空间或高风险生成失败。
- 不与正向画面冲突。
- 不只是“自然”“好看”“稳定”等模糊要求。

针对性禁止项是验收边界，不是第一层生成控制。每条高风险禁止必须能够追溯到 positive_closure；不能只写“禁止出现 X”而在正向正文中继续描述 X。

正文中的未裁决分支继续阻断。

### 11.5 故事板纠偏

用户纠正可以进入：

- 正向物理描述。
- 时间状态。
- @禁止。

例如：

- 内壁为钢本色螺旋加工纹，不发光。
- 那不是漩涡或幻觉。

### 11.6 正向可见性闭合

视频正向画面正文的来源被限定为：

- visible_whitelist。
- positive_closure。
- 对应 Visual Beat 的可见状态。
- 机位、构图、运镜、光影和可见表演。

以下字段不进入正向画面正文：

- narrative_only。
- occluded_state 中被遮挡内容的语义细节。
- audio_only。
- leakage_risks。
- human_qa_only 的 forbidden_qa。

遮挡本身、物体朝向、可见表面和实体材质可以进入正文，因为它们是当前画面可见的正向物理状态。

### 11.7 模型负向能力分流

Capability Profile 必须声明 `negative_instruction_policy`：

- `inline_supported`：精确 forbidden_qa 可以进入 `@禁止`，并随正向正文一同提交。
- `separate_negative_channel`：`@禁止` 保留在人类交付文档，同时逐字路由到平台独立负向通道。
- `token_leakage_risk`：模型可能把否定句中的对象当成生成目标；Render Payload 只提交正向闭合，不提交 forbidden_qa。
- `unsupported_or_unknown`：按 `token_leakage_risk` 处理，直到真实测试证明可内联。

Capability policy 与每个 Visibility Contract 的 `negative_route` 必须按以下确定性映射：

| negative_instruction_policy | negative_route | 实际提交 |
|---|---|---|
| `inline_supported` | `inline_supported` | 正向正文 + 经批准的精确 forbidden_qa |
| `separate_negative_channel` | `separate_negative_channel` | 正向正文进正向通道；forbidden_qa 逐字进独立负向通道 |
| `token_leakage_risk` | `human_qa_only` | 只提交正向闭合；forbidden_qa 仅供人类审计 |
| `unsupported_or_unknown` | `human_qa_only` | 按最保守策略处理，直到实测更新 profile |

任何其他组合都属于结构错误，不能生成 Render Payload。

Director 必须先写完整 Visibility Contract；编译器只按照 profile 选择已存在字段的去向，不改写、不摘要、不把负向句自动改成正向句。

人类可读的 VIDEO_PROMPT 仍保留 `@禁止` 审计区和路由标记。实际提交给模型的 Render Payload 必须单独记录 included field IDs，避免用户误把 human_qa_only 内容复制进模型输入。

### 11.8 声音与对白执行契约

每个声音节点至少声明：

- start_tick 与 end_tick。
- speaker 或 sound_source_id。
- onscreen / offscreen / non_diegetic。
- generated、reference_audio 或 post_mix 职责。
- reference_offset（使用外部音频时）。
- overlap_group。
- sync_class：LOCKED、ELASTIC 或 descriptive_only。
- lip_sync_requirement 与 Capability 状态。

对白时长超出分配区间、说话人可见但平台不支持所需口型同步、或 audio_only 声源泄漏到视觉正文时必须阻断或要求 Director 改变执行方案。

---

## 12. 确定性检查器

### 12.1 Structural Precheck

检查：

- 必填标题。
- Segment、Shot、Beat、Panel ID。
- 时长。
- 时间覆盖。
- 内部 Boundary。
- 用户批准状态。

### 12.2 Segment Topology Check

检查：

- 每个 Shot 位于一个 Segment。
- Shot 时间不重叠且顺序明确。
- 内部切镜位于 Segment 时长内。
- 一个 Segment 可以有多个 Shot。
- 生成段间 Boundary 与内部 Boundary 不混用。

### 12.3 Fidelity Check

检查：

- 四类 Fidelity 均存在。
- 同一事实不能同时 LOCKED 和 OPTIMIZABLE。
- FORBIDDEN 不能与正向 Beat 冲突。
- ELASTIC 必须有允许范围或语义边界。

### 12.4 Storyboard Mapping Check

检查：

- 每个 Panel 引用真实 Beat 或 Boundary。
- 首尾 Panel 存在。
- 所有 LOCKED 注意力转移至少有一个 Panel。
- 保持时间没有被丢弃。

### 12.5 Prompt Preflight

阻断：

- 占位符。
- 未裁决的甲或乙。
- 条件分支。
- 时间越界。
- 引用不存在。
- 段内 Shot 顺序冲突。
- 格编号和时间顺序冲突。

不得阻断：

- 独立 @禁止 区块中的精确禁止。
- 距离、焦段、色温、百分比和时间范围。
- 物理纠偏中的“不是”。

### 12.6 No Semantic Mutation

同源检查必须证明：

- visible_state 在输出中逐字存在。
- 程序未删除括号。
- 程序未选择斜杠一侧。
- 程序未重写导演句子。
- 程序只添加固定标题、编号和派生标签。

### 12.7 Visibility Contract Check

确定性检查：

- 每个 Shot 有 Visibility Contract 或带理由的 `not_applicable`。
- 高风险物体存在 leakage_risks 时同时存在 positive_closure。
- 正向 Render Payload 的字段来源只属于允许集合。
- narrative_only、audio_only 和 human_qa_only 字段 ID 未进入正向 Render Payload。
- negative_route 与 Capability Snapshot 一致。
- VIDEO_PROMPT、Render Payload 和 Commit Manifest 的字段路由可追溯。
- 每个 Beat 的 visibility_state_id 在其 tick 范围内有效。
- Visibility Boundary 覆盖表面揭示、遮挡、反射路径和物体翻转。

DP 语义检查：

- 当前机位是否真的看得见 visible_whitelist 中的表面和动作。
- 背面机位是否错误描述正面内容。
- 镜面、玻璃、屏幕和反射是否存在未经设计的信息通路。
- 剧情事实是否被模型诱导成画内实体、UI、文字、倒影或额外人物。
- positive_closure 是否足以表达画面，而不是靠否定句维持。

任何隐藏剧情信息进入正向视觉正文、任何背面/遮挡几何矛盾、或任何负向路由违反模型能力配置，均为阻断错误。

### 12.8 Timeline、Fact Coverage 与 Handoff Check

确定性检查：

- timebase、duration_ticks、半开区间和 Boundary ownership 单义。
- Shot/Beat/Panel/Sound 的 tick 不越界、不重叠、不留未声明空洞。
- 每个剧情关键 fact_id 有 render policy 和 Fidelity 绑定。
- LOCKED 行为事实未被降级。
- 相邻 Entry/Exit/Handoff 的人物、道具、摄影机、焦点、光源、可见表面和声音字段齐全。

DP 只判断这些状态在导演语义上是否连续；程序不替 Director 选择状态。

### 12.9 Asset、Capability、Context 与 Invocation Check

阻断：

- 参考资产缺少 hash、平台槽位、职责、优先级或冲突裁决。
- Prompt Dialect Adapter 与目标平台/profile 不匹配。
- Capability 的负向、时长、画幅、参考、文字、音频或切镜关键字段未知且当前设计依赖该字段。
- 完整请求或预留输出超过上下文预算。
- 模型 finish reason 表示截断，或最终尾节点/必填结构缺失。

禁止通过静默删减事实、用户纠正、Visibility、Fidelity 或 Handoff 解决预算问题。

---

## 13. Golden Set

### 13.1 Golden Set 目的

Golden Set 用于验证：

- 知识是否改善导演判断。
- Master 是否能表达成功结构。
- 编译器是否保留控制信号。
- 验收是否能区分有价值偏移和严重偏移。

### 13.2 枪管

必须：

- 单一 Segment。
- 单一连续 Shot。
- 无切镜。
- 背影到右侧到管口到管内。
- 注意力持续收缩。
- 最终金属内壁填满画面。
- 不出现魔幻漩涡。

知识问题：

- 环境到物体内部的注意力收缩。
- 连续运镜的起幅、路径和落幅。
- 故事板视觉歧义的物理纠正。

### 13.3 观众席

必须：

- 一个 Segment 内三个 Cinematic Shot。
- WS 到双人 MCU 到手机 ECU。
- 内部两次切镜。
- 伊莎贝拉左、乔右。
- 手机无回复、无已读、无正在输入。
- 手机画面只包含设计中明确存在的对话气泡和空白负空间，不自动补充回复、通知或状态符号。

允许：

- 切点小幅偏移。
- 横版构图到竖版重新排布。

知识问题：

- 空间、关系、证据的信息尺度递进。
- 内部切镜作为同一生成段拓扑。
- AI 文字和 UI 风险。
- 信息缺失如何通过可见负空间表达，而不是依赖否定句。
- 屏幕参考、后期合成和生成模型之间的职责选择。

### 13.4 窄巷

必须：

- Pedro 追球、抬头、直升机、轿车的顺序。
- 直升机画右到画左。
- 轿车静止、熄灯、无人。
- 最终轿车成为绝对焦点。
- 阴灰天气。

可以优化：

- 直升机是否独立切镜。
- 9 秒处是否硬切。
- Pedro 如何退出画面。

知识问题：

- 锁定叙事节点与弹性连接。
- 注意力交接。
- 横竖画幅语义重构。

### 13.5 备赛区

必须：

- 单一固定 Shot。
- Rico 低头。
- 伊乌里在规定时间前不入画。
- 伊乌里不看 Rico。
- 擦肩距离成立。
- Rico 停顿可读。
- 伊乌里走向亮区。

当前历史视频应因提前入画和回看 Rico 被判为失败，但其构图关系可记录为成功。

知识问题：

- 微表演可见性。
- 背影与嘴角动作冲突。
- 长保持被模型压缩。
- 空区与首次入画锁定。

### 13.6 验收方式

第一层硬门槛：

- 任何 LOCKED 或 FORBIDDEN 违规直接失败。
- 任何 narrative_only、audio_only 或被遮挡信息泄漏到画面直接失败。
- 任何未经设计的 UI、倒影、透明结构、文字、人物或画外事件直接失败。

第二层软评分：

| 维度 | 权重 |
|---|---:|
| 事件与注意力拓扑 | 25 |
| 内部镜头与切换 | 20 |
| 运镜方向与路径 | 15 |
| 起幅、关键状态与落幅 | 15 |
| 人物身份与行为 | 15 |
| 光影与空间 | 5 |
| 材质、声音与微细节 | 5 |

用户评价拥有最终裁决权。用户认可的非字面偏移可以成为 OPTIMIZABLE 候选，但不能覆盖剧情硬约束。

### 13.7 Visibility Contract 文本回归组

除四组媒体 Golden 外，必须维护不依赖媒体解析的文本回归场景：

1. 手机背面：人物操作手机，画面只见不透明后壳和双手，不生成屏幕内容。
2. 镜面边界：镜子只反射物理反射路径内的对象，不补出画外人物。
3. 玻璃与窗户：除非剧本和构图明确要求，不自动增加窗外车辆、行人或事件。
4. 画外声音：声源只进入 audio_only，不因声音描述自动在画面中出现。
5. 聊天界面：只保留明确给出的消息和状态，空白区域不补全对话。
6. 物体背面：当前机位只看见背面时，不生成正面文字、标识、显示内容或结构。

每个回归场景至少测试两种 Capability Profile：`inline_supported` 与 `token_leakage_risk`。两者的人类审计契约相同，实际 Render Payload 路由不同。

### 13.8 Calibration、Holdout 与知识消融

当前四组样本属于 calibration set，用于发现机制和建立格式，不得同时充当唯一的无偏发布证明。

生产发布还必须维护：

- 不参与决策卡设计的 holdout scenes。
- 动态可见性、跨画幅、对白同步、跨Segment交接和精确UI文字风险场景。
- `no_knowledge`、`K1_only`、`K1_K2`、`K1_K2_K3` 消融对照。

消融用于判断知识是否改善导演判断，而不是增加字数。Soft Score 只作诊断，不得绕过硬门槛或替代用户评价。

---

## 14. 经验学习

### 14.1 经验状态

- candidate：一次真实观察。
- active：已经人工审查，可作为有条件候选知识使用。
- project_approved：用户批准，可在当前项目加载。
- repeated：至少两个不同场景出现。
- validated：跨场景修订有效且人工批准。
- core_candidate：多项目稳定，等待人工批准。
- deprecated：曾经有效，但因来源、能力或适用范围变化停止新召回。
- rejected：复测不成立。

### 14.2 晋升规则

项目偏好可以一次批准后进入 K4。

通用知识必须满足：

- 至少两个不同场景。
- 有真实生成证据。
- 有修订前后对比。
- 有用户或人工批准。
- 通过 Golden 回归。
- 绑定可验证的 STORYBOARD_RUN_RECORD 或 RENDER_RUN_RECORD。

同一场景的多次生成不能冒充“两个不同场景”。声明目标模型能力的经验还必须绑定 Capability Profile hash；profile 改变时重新验证或缩小适用范围。

模型自我评价不得作为验证证据。

### 14.3 学习内容

经验应记录：

- observation_type：attention、camera、editing、performance、visibility、reference、prompt 或 capability。
- storyboard_prediction。
- actual_video_behavior。
- user_quality_label。
- invariant_preserved。
- deviation_class：优化、无害偏移或严重偏移。
- 哪个判断成立。
- 在什么条件下成立。
- 哪些变量没有被验证。
- 哪个偏移改善了结果。
- 哪个偏移破坏了剧情。
- 素材、模型和提示词版本。
- capability_profile_hash。
- affected_card_ids 与 regression_case_ids。

禁止把完整历史提示词直接当模板加载。

---

## 15. 迁移策略

### 15.1 隔离重写与原子接管

施工和验收期间 vNext 与当前 MODE:P 只允许在文件系统中隔离共存，用于黑盒回归、对照和回滚；不得在同一次创作运行中共同工作：

- 不覆盖当前 LOOP_SPEC。
- 不删除当前 Director 文件。
- 不立即替换 view_deriver。
- 不修改旧 session 产物。
- 不导入 v4 模块、知识索引、缓存或 fallback。
- 不把 v4 实现细节当作 vNext 的设计权威。

最终生产形态不是长期双系统：通过 Shadow、Pilot、Canary 和用户批准后，vNext 原子接管唯一 `mode_p` 与 `/mode-p-pilot` 活动入口；v4 转入只读归档包，仅保留受控回滚能力。

### 15.2 实施顺序

1. 冻结当前运行基线、24 个知识文件 hash 和四组样本。
2. 将 v4 标为归档；建立同源去重、E0 隔离和 Capability Candidate 复验规则。
3. 从四个 Core 精简 K1；将九个 Capsule 拆为单问题 K2 候选。
4. 建立 Claim、Decision Card、Conflict Graph、Evidence Tier 和 Knowledge Snapshot Schema。
5. 建立 Scene Diagnosis、Knowledge Query 和最小检索闭环。
6. 把四组配对建立为 K3 Golden Case；扩展 RenderEvidence 经验晋升链。
7. 建立 Generation Segment 与 Visibility Contract 数据模型。
8. 重写 Director Master 和契约。
9. 实现纯复制的故事板编译器。
10. 实现人类 VIDEO_PROMPT 与实际 Render Payload 的分域编译器。
11. 重写预检和 DP。
12. 建立用户故事板批准、字段路由审计和批准失效。
13. 建立 Golden Set Runner 与知识反漂移测试。
14. 四组验收通过后再考虑切换生产入口。

### 15.3 旧文件处理

任何删除或归档必须满足：

- 新入口已通过 Golden Set。
- 当前测试无新增严重失败。
- 旧文件没有仍被活动入口引用。
- 用户明确批准。

---

## 16. 最终验收门

### Gate A：知识使用

- 当前知识来源清单、hash、disposition 和重复关系可追溯。
- v4、E0、未验证 Capability 和过期能力不进入运行时知识包。
- 场景诊断先于知识检索。
- 检索基于导演问题，不基于场景类型单标签。
- 冲突知识被暴露给 Director，算法未静默选择创意答案。
- 单次知识包符合预算。
- 无匹配时不回退模板。
- Director 的设计回答了诊断问题。

### Gate B：导演能力

- Master 包含明确注意力路径。
- 运镜、构图、光影、表演和剪辑服务同一戏剧变化。
- 微表演在机位中可见。
- Generation Segment 与 Cinematic Shot 分离。

### Gate C：故事板

- 输出格式符合已确认旧式模板。
- Panel 覆盖起幅、路径、切换和落幅。
- 保持格未被删除。
- 箭头、编号和自然语言一致。

### Gate D：视频提示词

- 实际故事板引用职责明确。
- 内部切镜完整保留。
- 起幅、过程和落幅完整。
- @音轨、@禁止、@转场存在。
- 用户纠正已吸收。
- VIDEO_PROMPT 与 Render Payload 分域，included/excluded 字段和 negative route 可追溯。

### Gate E：确定性

- 算法没有语义改写。
- 相同输入产生相同输出。
- ID、时间、引用和版本可追溯。
- 依赖改变只使相关产物失效。

### Gate F：Golden Set

- 枪管连续收缩可表达。
- 观众席三段内部切镜可表达。
- 窄巷受控优化可被接受。
- 备赛区行为和时序失败可被识别。

### Gate G：用户评价

- 用户确认故事板能够基本推断视频效果。
- 用户确认提示词格式可直接使用。
- 用户确认导演判断优于当前管道。
- 用户明确批准生产切换。

只有 A-G 全部通过，MODE:P vNext 才算达到最终目标。

---

## 17. 永久防偏移条款

以下任一现象出现，视为架构重新偏移：

- 重新把 Shot 等同于生成单元。
- 故事板重新变成默认稀疏投影。
- Profile 改变最终输出结构。
- 编译器开始摘要或清洗导演文本。
- 再次全面禁止否定句。
- 内部切镜被统一推给后期。
- 知识检索重新退化为单一场景类型胶囊。
- 运行时开始加载完整知识库。
- Director 需要手写大量重复格式。
- 算法自动决定镜头。
- 文本 Director 假装看过图片或视频。
- 没有真实生成结果却宣布经验有效。
- 用传统摄影规则否定用户认可的 AI 结果。
- 只验证文本同源，不验证故事板是否具备视频预判能力。
- 用更长的 @禁止 代替 visible_whitelist 和 positive_closure。
- 把剧本成立但当前机位不可见的信息直接放进正向视觉正文。
- 不依据模型能力配置就把所有负向词提交给视频模型。
- 只在最终 Prompt 检查泄漏，而不在 Director 设计和 DP 审查阶段处理。

检测到偏移后必须：

1. 停止扩大实现范围。
2. 指出违反的本文件条款。
3. 回到四组 Golden Set。
4. 用用户评价和真实生成证据重新裁决。

---

## 18. 最终交付检查表

### 文本运行边界

- [ ] Director 与 DP 全程只读取文本。
- [ ] 媒体解析不属于运行依赖。
- [ ] 所有素材只通过文字卡和职责进入 MODE:P。

### 知识

- [ ] 有 Scene Diagnosis。
- [ ] 有问题驱动的 Knowledge Query。
- [ ] 只加载最小知识包。
- [ ] 知识卡包含适用与不适用条件。
- [ ] 真实案例与理论知识分层。

### 导演设计

- [ ] Generation Segment 与 Cinematic Shot 分离。
- [ ] 注意力路径明确。
- [ ] 起幅、过程和落幅完整。
- [ ] 关键表演在镜头中可见。
- [ ] Fidelity Contract 完整。
- [ ] 每个 Shot 有 Visibility Contract 或带理由的 not_applicable。
- [ ] 高风险表面具有 visible_whitelist、positive_closure 和 leakage_risks。

### 故事板

- [ ] 采用固定旧式格式。
- [ ] 共享锚、编号、箭头和分段齐全。
- [ ] 保持格和过渡格按导演设计保留。
- [ ] 格数由设计决定，不机械等于秒数。

### 视频提示词

- [ ] 有实际故事板引用。
- [ ] 参考职责分离。
- [ ] 内部切镜可在单一 Segment 中表达。
- [ ] 有完整时间线。
- [ ] 有针对性 @禁止。
- [ ] 正向画面正文没有 narrative_only、audio_only 或隐藏内容。
- [ ] negative_route 与目标模型能力一致。
- [ ] 人类 VIDEO_PROMPT 与实际 Render Payload 的字段范围可追溯。
- [ ] 有音轨和转场。

### 编译

- [ ] 不删除括号。
- [ ] 不删除纠偏文字。
- [ ] 不擅自选择或删掉 Beat/Panel。
- [ ] 不产生未裁决分支。
- [ ] 同输入同输出。
- [ ] 编译器只路由 Visibility Contract 字段，不重写正负向语义。

### 验收

- [ ] 四组 Golden Set 按预期通过或失败。
- [ ] Visibility Contract 文本回归组全部通过。
- [ ] 用户主观评价被记录。
- [ ] 没有以格式正确代替导演质量。
- [ ] 生产切换得到用户明确批准。

---

## 19. 设计基线结论

MODE:P vNext 的成功标准不是“生成了一份更规整的提示词”，而是：

> 文本 Director 能利用最小而相关的知识，针对当前剧本完成真实的导演判断；故事板清楚呈现时间、构图、运镜、光影和切换；视频提示词继承同一设计；实际视频可以在受控范围内优化连接，但不能改变剧情事实、人物行为、运动方向和最终注意力落点。

本文件是后续实现、审查、测试和生产切换的最终目标约束。任何局部代码、模板、优化或旧文档与本文件冲突时，必须回到第 0 节的证据权重重新裁决。

---

## 20. 生产状态机

### 20.1 状态机原则

所有运行状态必须：

- 单义。
- 持久化。
- 可恢复。
- 可审计。
- 只允许显式迁移。
- 与当前产物哈希绑定。

不得通过“某文件存在”猜测业务状态。状态文件是唯一运行状态来源，文件存在性只作为一致性检查。

### 20.2 Episode 状态

Episode 状态枚举：

- INITIALIZED
- FACTS_READY
- VISUAL_BASELINE_READY
- SCENES_IN_PROGRESS
- EPISODE_REVIEW_REQUIRED
- EPISODE_REVISION_REQUIRED
- READY_FOR_DELIVERY
- DELIVERED
- BLOCKED
- FAILED

合法主路径：

~~~
INITIALIZED
→ FACTS_READY
→ VISUAL_BASELINE_READY
→ SCENES_IN_PROGRESS
→ EPISODE_REVIEW_REQUIRED
→ READY_FOR_DELIVERY
→ DELIVERED
~~~

EPISODE_REVISION_REQUIRED 只能回到受影响场景的已提交前状态。BLOCKED 需要用户或外部状态变化才能恢复。FAILED 表示系统错误，不等同于创意未通过。

### 20.3 Scene 状态

Scene 状态枚举：

- NEW
- FACTS_BOUND
- DIAGNOSIS_REQUIRED
- DIAGNOSIS_READY
- KNOWLEDGE_REQUIRED
- KNOWLEDGE_READY
- MASTER_REQUIRED
- MASTER_DRAFTED
- PRECHECK_REQUIRED
- PRECHECK_FAILED
- DP_REQUIRED
- DP_IN_REVIEW
- DIRECTOR_REVISION_REQUIRED
- STORYBOARD_READY
- AWAITING_STORYBOARD_APPROVAL
- STORYBOARD_REVISION_REQUIRED
- STORYBOARD_APPROVED
- VIDEO_CORRECTION_REQUIRED
- VIDEO_PROMPT_READY
- RENDER_PAYLOAD_REQUIRED
- RENDER_PAYLOAD_READY
- READY_FOR_EPISODE_REVIEW
- COMMITTED
- BLOCKED
- FAILED

合法主路径：

~~~
NEW
→ FACTS_BOUND
→ DIAGNOSIS_REQUIRED
→ DIAGNOSIS_READY
→ KNOWLEDGE_REQUIRED
→ KNOWLEDGE_READY
→ MASTER_REQUIRED
→ MASTER_DRAFTED
→ PRECHECK_REQUIRED
→ DP_REQUIRED
→ DP_IN_REVIEW
→ STORYBOARD_READY
→ AWAITING_STORYBOARD_APPROVAL
→ STORYBOARD_APPROVED
→ VIDEO_PROMPT_READY
→ RENDER_PAYLOAD_REQUIRED
→ RENDER_PAYLOAD_READY
→ READY_FOR_EPISODE_REVIEW
→ COMMITTED
~~~

### 20.4 修订迁移

- PRECHECK_FAILED → MASTER_REQUIRED。
- DP_IN_REVIEW → DIRECTOR_REVISION_REQUIRED → MASTER_DRAFTED。
- AWAITING_STORYBOARD_APPROVAL → STORYBOARD_REVISION_REQUIRED → MASTER_REQUIRED。
- STORYBOARD_APPROVED + clarification_only → VIDEO_CORRECTION_REQUIRED → MASTER_DRAFTED。
- STORYBOARD_APPROVED + render_constraint_only → RENDER_PAYLOAD_REQUIRED。
- STORYBOARD_APPROVED + storyboard_visible_change → STORYBOARD_REVISION_REQUIRED。
- STORYBOARD_APPROVED + topology_or_fact_change → MASTER_REQUIRED。
- Episode Review发现问题 → 受影响Scene的DIRECTOR_REVISION_REQUIRED。

修订不得跳过重新预检、派生和DP。

### 20.5 用户等待状态

以下状态必须停止自动创作：

- AWAITING_STORYBOARD_APPROVAL
- BLOCKED

处于用户等待状态时允许：

- 读取状态。
- 显示待办。
- 校验用户输入。

禁止：

- 后台重写Master。
- 自动重新检索知识。
- 自动生成新版本故事板。
- 使当前待批准产物失效。

### 20.6 状态迁移记录

每次迁移必须写事件：

- event_id
- timestamp_utc
- episode_id
- scene_id
- from_state
- to_state
- actor
- reason_code
- input_commit_id
- output_commit_id
- correlation_id

事件写入后不得修改，只允许追加补偿事件。

---

## 21. 产物封装、幂等与原子提交

### 21.1 Artifact Envelope

所有机器可读产物必须包含：

- schema_name
- schema_version
- artifact_type
- artifact_id
- episode_id
- scene_id
- generation_id
- created_at_utc
- created_by
- source_commit_ids
- source_hashes
- capability_profile_hash
- knowledge_snapshot_id
- content_sha256

Markdown产物的Envelope可以存入同名Manifest，不强制污染用户可读正文。

`VIDEO_PROMPT` 与 `RENDER_PAYLOAD` 是两个不同的一等产物：前者是包含完整 `@禁止` 和路由说明的人类审计文档；后者是实际提交给目标模型的字段集合。两者不得共用一个模糊的“最终提示词”文件名或 hash。

文本统一使用 UTF-8 与 LF。机器 JSON 在 hash 前必须使用项目规定的 Canonical JSON 序列化；禁止因键顺序、缩进或 Windows 换行产生语义相同但 hash 不同的产物。

### 21.2 目录分层

每个Scene至少分为：

~~~
scene/
├── working/
├── staging/
├── commits/
├── delivery/
├── reports/
└── telemetry/
~~~

- working：当前可修改草稿。
- staging：待提交的完整候选。
- commits：不可变提交记录和Manifest。
- delivery：最后一个已批准提交的只读镜像。
- reports：检查和审查报告。
- telemetry：事件和指标。

### 21.3 原子提交

提交顺序：

1. 为本次操作创建唯一 generation_id。
2. 在staging/generation_id写全部候选产物。
3. 计算每个文件哈希。
4. 运行全部确定性检查。
5. 写COMMIT_MANIFEST候选。
6. 对staging目录执行最终完整性检查。
7. 原子更新current commit pointer。
8. 将交付镜像更新到delivery。
9. 写状态迁移事件。

任一步失败：

- current commit pointer不得改变。
- delivery不得出现部分新文件。
- staging保留用于诊断或按策略清理。

### 21.4 Commit Manifest

必须包含：

- commit_id
- parent_commit_id
- generation_id
- artifact列表
- 每个artifact的相对路径、schema、hash
- Master版本
- 知识快照
- 能力快照
- 编译器版本
- 检查结果
- DP结果
- 用户批准引用
- 提交状态

若提交含 Render Payload，Manifest 还必须保存：

- render_payload_hash
- positive_channel_included_field_ids
- negative_channel_included_field_ids
- human_qa_only_field_ids
- negative_instruction_policy
- negative_route
- capability_snapshot_id

### 21.4a Render Payload Manifest

每个实际 Render Payload 必须有独立 Manifest，至少包含：

- target_model与profile版本。
- Segment ID。
- 来源 VIDEO_PROMPT hash 与 Director Master hash。
- 正向通道逐字段来源 ID。
- 独立负向通道逐字段来源 ID。
- 被排除的 narrative_only、audio_only、occluded semantic detail 和 human_qa_only 字段 ID。
- 编译器版本与内容 hash。

Render Payload 只能由确定性编译器生成，不允许用户可读 VIDEO_PROMPT 在提交前再经过不可追溯的大模型改写。

### 21.5 幂等键

每个阶段必须计算idempotency_key：

~~~
stage_name
+ source commit
+ relevant input hashes
+ model identity or compiler version
+ normalized options
~~~

相同幂等键已经成功提交时：

- 默认复用结果。
- 不重复调用模型。
- 不创建语义等价的新版本。

用户显式要求重新生成时必须产生新的request_nonce并记录原因。

### 21.6 模型调用提交

模型原始响应和解析后的产物分开处理：

1. 保存不可变原始响应。
2. 解析到staging。
3. 结构检查。
4. 只有解析成功才允许提交。

解析失败不得覆盖上一个有效Master。

每次模型调用必须额外保存 Model Invocation Snapshot：

- invocation_id 与 provider request ID。
- 完整请求 content hash。
- system prompt、Director contract 和 template hash。
- resolved model 与 provider revision。
- sampling parameters、seed（若平台支持）和 normalized options。
- 完整上下文 token 预算与预留输出。
- finish_reason、truncated 和 parse_status。
- 原始响应 hash 与提交后的 artifact hash。

上下文压缩、system prompt 变化、模型切换或采样参数变化必须产生新的幂等输入；不得继续声称是同一次可重放调用。

### 21.7 外部生成运行记录

STORYBOARD_RUN_RECORD 与 RENDER_RUN_RECORD 至少包含：

- source prompt/payload hash。
- 实际绑定的资产 ID、hash 与平台槽位。
- 平台、产品、模型/模式和任务ID。
- 用户可见生成参数。
- submitted_at 与 completed_at。
- 输出文件 hash。
- 用户评价或后续 review ID。

外部平台未提供某字段时明确写 unknown，不得猜测。

---

## 22. 来源、快照与批准失效

### 22.1 Provenance Snapshot

每个Master提交必须绑定：

- 剧本哈希。
- SCRIPT_FACTS哈希。
- Visual Bible哈希。
- Continuity Ledger哈希。
- 资产卡哈希。
- 能力配置哈希。
- Knowledge Query哈希。
- Knowledge Index哈希。
- 被选知识内容哈希。
- 项目偏好哈希。
- Director契约版本。

### 22.2 Knowledge Snapshot

知识快照必须保存：

- query。
- 检索器版本。
- 排序算法版本。
- 候选集ID。
- 入选卡ID和版本。
- 入选内容hash。
- 选择原因。
- 排除的冲突条目。
- 字符预算。

重放历史提交时使用原快照，不重新运行实时检索。

### 22.3 Capability Snapshot

每个Segment绑定：

- 平台或模型能力profile。
- profile版本。
- profile hash。
- 验证日期。
- 影响该Segment的能力字段。
- negative_instruction_policy。
- 是否支持独立负向通道。
- 是否存在否定词 token leakage 的真实测试证据。
- Render Payload 允许包含的 Visibility Contract 字段。
- prompt_dialect_id 与 adapter版本。
- duration_quantization 与允许时长。
- supported_aspect_ratios、resolutions 和 output_fps_status。
- internal_cut_support。
- reference slot/alias/order contract。
- readable_text_and_ui_policy。
- audio_generation、reference_audio 和 lip_sync capability。
- prompt/context limit。
- expires_at 或 next_revalidation_at。

能力配置变化时只使实际依赖该字段的Segment失效。

负向能力未知时不得乐观推断，必须按 `token_leakage_risk` 路由。Capability Snapshot 的该字段变化会使对应 Segment 的 Render Payload 和视频提示词批准失效，但不自动改变 Director Master 中的创意设计。

### 22.4 Storyboard Approval Record

批准记录必须包含：

- approval_id
- user identity或本地批准标识
- approved_at
- scene_id
- storyboard_prompt_hash
- director_master_hash
- storyboard_asset_id
- storyboard_asset_hash（可用时）
- user_status
- user_corrections
- correction_hash
- correction_impact
- correction_impact_confirmed_by_user
- approved_visible_scope

### 22.5 批准自动失效

以下任一变化使批准失效：

- Master中影响故事板的Beat、Panel、镜头拓扑或Fidelity改变。
- 故事板提示词hash改变。
- 故事板素材hash改变。
- 用户纠正被修改。
- 场景事实或连续性发生相关变化。
- 纠正新增或改变可见实体、动作、表面、方向、切镜或时间节点。
- correction_impact 从 clarification/render constraint 升级为 storyboard_visible_change 或 topology_or_fact_change。

以下变化不必失效：

- 不影响内容的遥测。
- 报告路径变化。
- 纯显示层且保证字节内容不变的交付复制。

批准失效后状态回到AWAITING_STORYBOARD_APPROVAL或STORYBOARD_REVISION_REQUIRED。

### 22.6 视频交付绑定

最终VIDEO_PROMPT必须绑定：

- 有效approval_id。
- approved storyboard asset。
- 对应Master hash。
- 用户纠正hash。
- Video Compiler版本。

最终 Render Payload 还必须绑定：

- VIDEO_PROMPT hash。
- Capability Snapshot ID 与 hash。
- Render Payload Manifest hash。
- negative_instruction_policy 与 negative_route。
- 所有 included/excluded field IDs。

任何绑定缺失不得进入delivery。

Capability Profile、Visibility Contract、negative route 或字段路由变化时，只使依赖它们的 VIDEO_PROMPT/Render Payload 批准和交付绑定失效；不自动推翻已批准 Storyboard 的构图事实，也不让编译器修改 Director Master 的创意设计。

---

## 23. 并发、锁与恢复

### 23.1 锁粒度

- Episode级共享读锁：场景读取分集基线。
- Episode级独占写锁：修改Visual Bible、Continuity Ledger或Episode Delivery。
- Scene级独占写锁：修改Master、状态、批准和交付。
- Scene级共享读锁：审查或读取已提交产物。

### 23.2 锁内容

锁必须记录：

- lock_id
- resource_id
- owner_id
- process_id
- acquired_at
- lease_expires_at
- operation
- correlation_id

### 23.3 租约与恢复

- 锁必须有有限租约。
- 活动进程定期续约。
- 租约过期不代表可以立即覆盖；恢复程序必须确认没有有效提交正在进行。
- 接管过期锁必须写审计事件。

### 23.4 并发禁止

禁止：

- 同一Scene同时存在两个Director写操作。
- DP审查未提交Master草稿。
- 用户等待批准时后台修改待批准内容。
- Episode Review和Scene修订同时写连续性账本。

### 23.5 崩溃恢复

恢复顺序：

1. 读取最后一个有效Commit Manifest。
2. 校验current pointer和delivery hash。
3. 检查未完成staging。
4. 若staging完整但未提交，重新运行最终检查。
5. 若staging不完整，标记abandoned，不拼接部分文件。
6. 恢复业务状态到最后一个已提交状态。
7. 记录RECOVERY事件。

### 23.6 重放

重放必须区分：

- replay_compile：使用已保存原始响应或 Master、原知识快照、原能力快照和原编译器版本，确定性重建派生产物。
- reinvoke：使用相同请求再次调用非确定性模型，必须创建新分支提交，不保证字节或语义相同。
- regenerate：使用当前版本和当前输入重新生成，必须创建新分支提交。

禁止用regenerate覆盖历史commit。

---

## 24. 错误分类、重试与停止条件

### 24.1 错误域

错误代码前缀：

- INPUT：输入和剧本事实。
- ASSET：素材卡和引用。
- KNOWLEDGE：诊断、检索和知识快照。
- DIRECTOR：模型响应和Master。
- STRUCTURE：Schema、时间和映射。
- DP：审查输入与输出。
- APPROVAL：用户批准和失效。
- COMPILE：故事板或视频编译。
- DELIVERY：提交和交付。
- LOCK：并发和租约。
- RECOVERY：崩溃恢复。
- SYSTEM：文件系统、进程和未知错误。

### 24.2 错误处理类型

- RETRYABLE：相同输入可以安全重试。
- REVISION_REQUIRED：同一Director需要定向修订。
- USER_REQUIRED：必须等待用户。
- CONFIG_REQUIRED：需要能力或项目配置。
- FATAL：不能安全继续。

### 24.3 自动重试

只允许对以下情况自动重试：

- 临时模型传输失败。
- 短暂文件锁竞争。
- 可证明没有副作用的读取失败。
- 原子提交前的临时I/O失败。

自动重试必须：

- 使用相同幂等键。
- 指数退避。
- 有最大次数。
- 记录每次尝试。

### 24.4 禁止自动重试

- Director语义不合格。
- DP指出创意或空间问题。
- 用户拒绝故事板。
- 批准失效。
- Schema版本不兼容。
- 哈希不一致。

### 24.5 修订轮次

默认单场自动流程：

- Director初稿：1次。
- DP定向修订：最多3轮。
- 用户故事板纠正后的Director修订：最多1轮自动恢复。

超过预算时：

- 状态转为BLOCKED。
- 输出已经完成的证据。
- 请求用户决定继续、改变范围或人工接管。

禁止无限修订。

### 24.6 失败保存

失败时必须保存：

- 错误代码。
- 所处状态。
- 输入commit。
- staging位置。
- 已通过检查。
- 未通过检查。
- 是否可重试。
- 推荐恢复入口。

不得以通用“生成失败”覆盖具体原因。

---

## 25. Schema、版本与兼容

### 25.1 版本规则

所有Schema使用语义版本：

- Major：不兼容字段或语义变化。
- Minor：向后兼容新增。
- Patch：校验或说明修正，不改变语义。

新增或改变 Visibility Contract 必填字段、negative_route 语义、Render Payload 字段范围，均属于 Major 变更。新增风险类别但不改变现有路由语义，可以是 Minor 变更。

### 25.2 读取策略

- 当前程序必须声明支持的Schema范围。
- 遇到未知Major立即阻断。
- 遇到较新Minor可以只在明确向后兼容时读取。
- 禁止忽略未知关键字段继续运行。

### 25.3 迁移

Schema迁移必须：

- 读取旧artifact。
- 生成新artifact和迁移报告。
- 保留旧artifact。
- 记录字段映射。
- 运行迁移前后语义检查。
- 产生新commit。

禁止原地静默修改历史文件。

### 25.4 编译器版本

Storyboard Compiler和Video Compiler独立版本化。

编译器升级必须运行：

- 字节级黄金文本测试。
- No Semantic Mutation测试。
- 四组Golden输出结构测试。
- 旧Master兼容测试。

### 25.5 Director契约版本

Director Agent、Runtime Contract和Master Template共享一个contract_version。任一语义变化必须同步升级并使相关模型缓存失效。

---

## 26. 观测、遥测与SLO

### 26.1 事件

每个阶段至少记录：

- stage_started
- stage_completed
- stage_failed
- state_transition
- model_call_started
- model_call_completed
- cache_hit
- cache_miss
- validation_failed
- approval_received
- approval_invalidated
- commit_created
- recovery_started
- recovery_completed

### 26.2 指标

按Episode、Scene和Stage记录：

- 输入字符数。
- 知识包字符数。
- Director输出字符数。
- 模型调用次数。
- 模型调用耗时。
- 确定性阶段耗时。
- 缓存命中率。
- DP修订次数。
- 用户等待时间。
- 错误域和错误码。
- 交付成功率。

### 26.3 本地确定性SLO

在标准Golden测试机和固定语料上：

- 单场Schema与结构预检P95应小于5秒。
- 单场双编译P95应小于5秒。
- 状态读取和迁移P95应小于1秒。
- 原子提交P95应小于5秒。

SLO必须通过基准测试确认后才能写入生产告警。外部模型排队和推理时间只记录，不承诺不受控制的墙钟SLO。

### 26.4 质量指标

必须跟踪：

- Storyboard Approval一次通过率。
- DP一次通过率。
- Golden硬约束通过率。
- 用户可交付率。
- 平均修订轮次。
- 知识卡命中后改善或恶化的案例数。

### 26.5 遥测隐私

默认遥测只记录：

- ID。
- 哈希。
- 字符数。
- 耗时。
- 状态。
- 错误码。

不得默认记录完整剧本、完整提示词、人物隐私资料或媒体内容。需要保存内容时必须位于项目会话目录并遵循保留策略。

---

## 27. 发布、灰度与回滚

### 27.1 Feature Flag

生产入口必须支持：

- current：现有MODE:P。
- vnext_shadow：vNext只生成对照产物，不进入交付。
- vnext_pilot：指定场景使用vNext。
- vnext_canary：指定分集使用vNext。
- vnext_production：vNext作为默认。

### 27.2 Shadow

Shadow阶段：

- 读取相同文本输入。
- 不修改现有交付。
- 输出到独立目录。
- 比较Master、格式、预算和检查结果。
- 不自动发送到外部生成平台。

### 27.3 Pilot

Pilot阶段：

- 每次只选择一个场景。
- 必须经过用户故事板批准。
- 必须记录实际生成评价。
- 不自动晋升到Canary。

### 27.4 Canary

Canary阶段：

- 选择一个完整分集。
- 新旧入口同时可用。
- Episode Review和回滚演练通过。
- 用户明确批准后才能扩大。

### 27.5 Production

进入Production前必须：

- 审计P0、P1关闭。
- 四组Golden通过预期。
- 当前回归测试通过。
- 故障恢复测试通过。
- 用户明确批准。

### 27.6 回滚

回滚必须：

- 切换feature flag。
- 保留vNext所有commit和证据。
- 不修改旧入口产物。
- 不把vNext Schema写回旧Session。
- 记录回滚原因和受影响范围。

---

## 28. 数据安全、路径与保留

### 28.1 路径边界

写操作只允许：

- 当前项目定义的Session目录。
- 明确的vNext工作目录。
- 系统临时目录中的本次任务子目录。

禁止：

- 对工作区根目录递归删除。
- 使用HOME或未解析环境变量作为删除目标。
- 路径逃逸。
- 跟随符号链接写出允许目录。

### 28.2 用户源文件

剧本、图片、视频、音频和用户资产：

- 永不自动删除。
- 永不自动覆盖。
- 默认只读。
- 只记录路径、hash和职责。

### 28.3 临时文件

临时目录必须：

- 每次任务独立。
- 包含任务ID。
- 不与delivery共用。
- 清理前验证绝对路径。
- 只清理明确归属本任务的文件。

### 28.4 保留策略

- delivery：永久保留，直到用户明确归档或删除。
- commits：默认永久保留。
- approvals：永久保留。
- reports：随commit保留。
- staging成功提交后：保留短期诊断窗口后可清理。
- abandoned staging：记录后按配置清理。
- cache：可重建，按容量和最近使用清理。
- telemetry：按项目策略归档。

### 28.5 敏感信息

- 日志不得输出凭据。
- 资产卡不得存储不必要的个人信息。
- 外部调用前必须明确当前允许发送的文本范围。
- MODE:P不得自动上传本地媒体。

### 28.6 不可信文本与提示注入

剧本、对白、知识原文、资产卡、外部元数据和用户纠正都属于数据载荷，不属于系统指令。运行时必须：

- 使用明确的 role/envelope 和来源 ID 分隔各类文本。
- 不执行载荷中“忽略以上规则”“读取其他文件”“调用工具”等指令式内容。
- 不允许知识候选直接写入 system prompt 或 active K1/K2。
- 对候选知识执行来源、指令污染和跨项目数据审查。
- 将疑似注入记录为 INPUT/KNOWLEDGE 安全事件并等待人工裁决。

### 28.7 来源授权与项目隔离

- K0 来源记录 bibliographic locator、摘录 hash 和许可/内部使用状态。
- 人物、声音和媒体资产记录用户确认或允许使用范围。
- K3/K4 默认只在当前项目可见，不跨项目自动共享。
- 未授权素材不进入外部 Render Payload，也不得晋升为共享案例。

---

## 29. 上下文、调用与修订预算

### 29.1 知识预算

默认单场上限：

- K1：1500中文字符。
- K2：最多8张，合计不超过2400中文字符。
- K3：最多2个案例摘要，合计不超过1000中文字符。
- K4：不超过600中文字符。

默认知识总包不超过5500中文字符。项目可以配置更低值。

### 29.2 Director调用预算

默认单场：

- Scene Diagnosis：1次。
- Master Design：1次。
- 每轮DP定向修订：1次。
- 用户故事板纠正：最多1次。

### 29.3 DP调用预算

默认最多：

- 初审1次。
- 定向复审3次。

Episode Review另计，但不得重复审查未变化场景。

### 29.4 预算超限

任何预算超限必须：

- 指明超限原因。
- 显示已经使用和预计增加。
- 说明是否有可安全缩小的上下文。
- 请求用户批准后继续。

禁止为了预算：

- 截断剧本事实。
- 删除LOCKED或FORBIDDEN。
- 删除有效Panel。
- 用算法摘要导演文字。

完整请求预算必须覆盖 system/contract、剧本事实、连续性、资产卡、K1-K4、当前 Master 片段、用户纠正和 DP 反馈，并为输出保留安全余量。优先使用目标模型 tokenizer；不可用时使用经回归校准的保守估计。

任何输入或输出截断必须阻断：

- 输入超限进入 CONFIG_REQUIRED 或 BLOCKED。
- finish_reason/truncated 异常进入 DIRECTOR 错误域。
- 缺少最终 Shot、LANDING、Handoff 或必填尾字段视为截断，不允许解析提交。

### 29.5 缓存

可以缓存：

- 脚本结构。
- 事实骨架。
- 知识快照。
- 确定性编译结果。
- 未变化Master的DP结果。

缓存键必须包含全部相关hash。任何相关输入变化必须失效。

---

## 30. 生产测试矩阵

### 30.1 Schema单元测试

覆盖：

- Generation Segment多个Shot。
- Beat时间与范围。
- Panel引用。
- Fidelity互斥。
- Reference Binding。
- Approval Record。
- Artifact Envelope。
- Render Payload Manifest 与 included/excluded field IDs。
- Visibility Contract 必填字段。
- 高风险对象不得使用无理由的 not_applicable。
- negative_route 枚举和 Capability Profile 对应关系。
- Canonical Timeline、半开区间、Boundary ownership 和显示秒数派生。
- Fact Bindings 全覆盖与不可降级事实。
- Dynamic Visibility State 的时间范围和 Beat 引用。
- Structured Handoff 最低字段。
- Correction Impact 枚举与批准失效。
- Reference Binding hash、平台槽位和冲突裁决。
- Model Invocation、Storyboard Run 与 Render Run Record。

### 30.2 状态机测试

覆盖：

- 每条合法迁移。
- 每条非法迁移。
- 用户等待冻结。
- 批准失效。
- clarification、render constraint、visible change 和 topology/fact change 四类纠正迁移。
- VIDEO_PROMPT_READY → RENDER_PAYLOAD_REQUIRED → RENDER_PAYLOAD_READY。
- Episode Review回流。
- BLOCKED恢复。

### 30.3 编译器黄金测试

覆盖：

- 固定标题和字段顺序。
- 有效冗余。
- 括号保留。
- 纠偏保留。
- @禁止保留。
- 相同输入字节级相同输出。
- Profile不改变外部格式。
- narrative_only、audio_only 和 human_qa_only 不进入正向 Render Payload。
- inline_supported 与 separate_negative_channel 的字段路由正确。
- token_leakage_risk 只提交 Director 已写出的正向闭合，不调用算法改写。
- VIDEO_PROMPT、Render Payload 和 Manifest 的字段 ID 可追溯。
- Prompt Dialect Adapter 只改变语法和路由，不改变语义。
- UTF-8/LF 与 Canonical JSON 的字节黄金结果稳定。

### 30.4 No Semantic Mutation测试

注入：

- 括号。
- 斜杠。
- 距离。
- 色温。
- “不是笑”。
- “不是漩涡”。
- 多秒HOLD。

验证编译后逐字存在且未被择一。

### 30.5 事务测试

故障注入点：

- 写第一个文件后崩溃。
- 写Manifest前崩溃。
- 检查后提交前崩溃。
- current pointer更新失败。
- delivery复制失败。

验证：

- 上一个commit仍有效。
- 不出现部分delivery。
- 恢复路径单义。

### 30.6 幂等与并发测试

- 相同请求重复执行只产生一个有效commit。
- 相同Scene两个写者只有一个获得锁。
- 过期锁安全接管。
- 用户等待期间后台写被拒绝。

### 30.7 知识测试

- 诊断问题能够检索相关决策卡。
- non_applicability有效排除。
- 无匹配不回退模板。
- 知识包不超过预算。
- 历史重放使用原快照。
- 当前 24 个知识文件全部有 disposition，未知来源不得默认加载。
- v4 归档不得参与运行时召回或重复加权。
- 同一来源在多文档中的复制条目必须去重。
- active 决策卡必须包含适用、不适用、来源、证据等级、反例或权衡。
- 互相冲突的相关卡必须进入冲突报告，不得由分数静默裁决。
- Director 提交问题域而不是最终胶囊路径；算法不得输出焦段、机位、运镜或时间轴答案。
- 模型能力卡必须检查 profile 版本、验证日期和到期条件。
- 没有真实 RenderEvidence 和用户批准的条目不得标为 validated。
- 枪管、观众席、备赛区和窄巷的诊断必须召回不同的最小知识包。
- 两个同为“对话”但导演问题不同的场景不得得到相同模板包。
- 反漂移扫描拒绝无证据人物上限、固定情绪映射、伪精度和“所有场景必须”类旧规则。

### 30.8 DP测试

- 背影机位要求嘴角动作必须被指出。
- 延迟入画没有空区锁定必须被指出。
- 一个Segment三个内部Shot不得被错误拆分。
- OPTIMIZABLE连接不得因非字面执行被自动否定。
- 手机背面镜头描述游戏界面必须被指出。
- 只写“禁止出现界面”但没有正向不透明后壳闭合必须被指出。
- 镜面、玻璃和屏幕存在未经设计的信息路径必须被指出。
- 画外声音导致声源实体进入画面必须被指出。
- 摄影机运动中 Visibility State 提前/延后切换必须被指出。
- Storyboard 新增可见内容却标成 clarification 必须被指出。
- 对白时长、画内说话人和 lip-sync capability 冲突必须被指出。

### 30.9 Golden Set测试

- 枪管：连续注意力收缩。
- 观众席：内部三镜。
- 窄巷：受控优化。
- 备赛区：行为与时序失败。
- Visibility Contract：手机背面、镜面、玻璃、画外声音、聊天空白和物体背面文本回归。
- Holdout：动态可见性、跨画幅、音频同步、跨Segment交接和精确UI文字。
- Knowledge Ablation：no_knowledge、K1_only、K1_K2、K1_K2_K3。

Golden文本测试属于自动化。实际媒体语义仍由用户或独立离线审查评价。

### 30.10 安全测试

- 路径逃逸。
- 符号链接逃逸。
- 宽泛删除目标。
- 日志敏感内容。
- 未批准媒体上传。
- 剧本、知识、资产卡和用户纠正中的提示注入。
- 未授权资产进入外部 Payload。
- K3/K4 跨项目泄漏。

### 30.11 性能测试

- 小场景。
- 长场景。
- 多Segment场景。
- 多场分集。
- 缓存冷启动和热启动。
- 完整上下文预算临界值、输入超限和输出截断。
- Windows 活动代码页与 UTF-8 子进程互操作。

记录本地耗时、字符量、调用次数和缓存命中，不把外部模型延迟当本地确定性性能。

### 30.12 发布验收

发布必须依次通过：

1. Unit。
2. Integration。
3. Fault Injection。
4. Golden Text。
5. Golden Semantic人工确认。
6. Shadow。
7. Pilot。
8. Canary。
9. 用户Production批准。

任何阶段不得自动升级到下一阶段。

---

## 31. 生产级最终结论

MODE:P vNext 的生产级 LOOP 必须同时成立：

1. 文本 Director 在问题驱动的最小知识包中完成真实导演判断。
2. Generation Segment、内部 Cinematic Shot、Beat 和 Panel 清楚分层。
3. 故事板和视频提示词由纯复制编译器生成，导演语义不被程序改写。
4. 用户故事板批准与准确的Master、提示词和素材版本绑定。
5. 状态、提交、锁、恢复、错误和版本行为可重放、可审计、可回滚。
6. 四组Golden能够分别验证连续复现、内部切镜、受控优化和行为失败。
7. 实际生产切换必须经过Shadow、Pilot、Canary和用户明确批准。
8. Canonical Timeline、Fact Coverage、Dynamic Visibility 和 Structured Handoff 在同一时间轴闭环。
9. 故事板纠正不会绕过重新批准而改变可见画面。
10. 实际 Render Payload、参考资产、外部运行结果和模型调用可以逐字段追溯。
11. 完整上下文没有静默截断，目标 Capability 与 Prompt Adapter 已验证。

生产完成的定义不是“代码已经接通”，而是：

> 在真实文本模型运行边界内，导演知识被有效使用，创意设计得到完整保留，任何中断都不会破坏有效交付，任何结果都能追溯到输入、知识、能力、Master、编译器、用户批准和版本，且故事板仍能作为视频效果的可靠预判。

本文件连同证据报告和生产审计报告共同构成 MODE:P vNext 的设计、实现和验收基线。
