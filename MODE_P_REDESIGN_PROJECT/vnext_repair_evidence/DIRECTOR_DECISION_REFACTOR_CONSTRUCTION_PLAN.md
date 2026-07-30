# MODE:P 导演决策重构施工方案

> 文档状态：PRECONSTRUCTION BASELINE  
> 目标分支：`mode_p_vnext` 后续 Director vNext.1  
> 写入日期：2026-07-29  
> 适用项目：`D:\tsc\导演系统_v5`  
> 当前生产入口：保持 v4 不变；本方案不授权生产切换  
> 机器目标锁：`DIRECTOR_REFACTOR_GOAL_LOCK.json`

## 0. 本方案的权威与变更纪律

本文件用于阻止后续重构在局部修复中偏离最终目标。后续任何代码、Schema、Prompt、Agent
契约、知识整理、测试和性能优化，都必须引用本文件中的目标、不可变量和工作包编号。

冲突时按以下优先级裁决：

1. 用户最新明确要求。
2. 本施工方案与机器目标锁。
3. 当前 vNext LOOP 中仍与本方案一致的原则。
4. 当前 `mode_p_vnext` 可复用实现。
5. 旧 MODE:P、历史 Master、旧提示词和历史成功样本。

不得因旧文件已经存在、旧测试已经通过或迁移成本较高而降低本方案的目标。需要改变目标时，
必须同时：

- 写明改变原因和影响范围；
- 更新本文件和机器目标锁；
- 使受影响验收失效；
- 取得用户明确批准；
- 生成新的方案版本和变更记录。

禁止通过只改代码、不改目标锁的方式静默改变架构。

## 1. 输入证据与现状结论

### 1.1 本轮使用的高权重证据

- 用户在 Codex 中对故事板、视频提示词和实际视频的连续反馈。
- 已验收或已生成的真实配对链：
  `剧本 → 故事板提示词 → 故事板图 → 视频提示词 → 视频 → 用户评价`。
- 上一条 `D:\tsc\导演系统_v5` Codex 重构任务中的导演决策优化结论。
- 知识胶囊施工说明，SHA-256：
  `FDC4AAC84AEC6881EDA2370C329024A9C6A81EC07905C8D89B6AE3F3637E6340`。
- 当前 `mode_p_vnext` 的实际 Schema、编译器、Golden、控制器和测试，而不是文档声明。

### 1.2 已确认的根因

当前 vNext 已有大量生产控制与双输出骨架，但还不是完整的导演系统：

1. `SceneDiagnosis` 只保存问题列表，缺少场景职责、权力变化、观众信息差、视觉动词、
   节奏策略和避免项。
2. `DecisionCard` 主要是 Claim 与证据记录，缺少完整的触发条件、禁用条件、执行规则、
   预期效果、权衡、替代方案和反模式。
3. 检索仍偏向质量排序和关键词关系，没有真正完成
   “导演问题 → 决策卡 → 空间调度 → 执行知识”的两阶段检索。
4. `GenerationSegment` 与 `CinematicShot` 是有价值的结构骨架，但没有真实 Director
   将剧本诊断、知识选择、场面调度和镜头设计稳定地写入该结构。
5. 现有 Storyboard/Video 投影能从同一对象派生，但目前主要由 Golden 手工构建对象来证明；
   这不等于未知剧本上真实 Director 已能产出同等质量。
6. 现有同步检查仍有只比较数量、时间和 ID 的薄接口。R1.4 已补强 Golden 结构校验，
   但尚需把同样的字段级契约推广到非 Golden 运行。
7. 旧 `DIRECTOR_MASTER.md` 和“主连续性板/主故事板”概念耦合过重，容易让设计、排版、
   连续性、参考图和双输出再次混成一个长文档。
8. 参考图职责曾被硬编码为“本板首格、末格、上一段视频末帧”等槽位，导致注意力冲突、
   首帧融合、错误回退和对外部视频连续性的误解。
9. 正向提示词中出现全局时间、哈希、状态摘要、审查解释、不可见剧情和负向名词，会被生成
   模型当成需要呈现的内容。
10. 同源只能证明两个文本来自同一计划，不能自动保证生成模型不镜像、不换手、不拿反手机
    或不改变人物站位；实际媒体还缺少观察后验收层。
11. 旧实模运行曾约 68 分钟并包含多轮结构修订。主要耗时来自重复上下文、串行模型阶段、
    格式劳动、全量重检和非局部修订，而不是导演判断本身。

### 1.3 对“故事板即视频预览”的准确结论

最终可以达到的是“效果级、拓扑级、动作级可预测”，不是逐像素复制：

- 计划层：可以确定性保证故事板与视频提示词同源。
- 生成层：可以通过硬约束、参考职责和目标模型 Adapter 提高实现概率。
- 结果层：必须检查实际故事板图和实际视频后，才能宣称该次生成已经达到可验证的预览一致性。

因此本项目将区分：

- `PLANNED_PREVIEW`：双输出来自同一执行契约。
- `STORYBOARD_REALIZED`：实际故事板图通过视觉实现检查。
- `VERIFIED_PREDICTIVE_PREVIEW`：实际视频与已验收故事板在硬不变量和主要软指标上通过。

文本同源通过不得冒充实际媒体已一致。

## 2. 最终目标与非目标

### 2.1 最终目标

`G-01`：让一个持久 Director Agent 针对当前剧本完成真正的导演判断，包括戏剧职责、
注意力、场面调度、机位、镜头、运镜、构图、光影、表演、声音、切镜和优化走廊。

`G-02`：知识库以可执行决策胶囊进入 Director 判断，而不是把完整教材或摘要全文塞入单次运行。

`G-03`：Director 的最终执行选择只写一次，形成结构化、不可变的
`VisualExecutionContract`。故事板提示词和视频提示词都是该契约的确定性投影。

`G-04`：故事板覆盖每个会改变画面意义、构图、注意力、轴线、人物关系、道具状态或动作阶段
的关键状态，使其成为视频的时间—构图—运动预览。

`G-05`：视频提示词只展开同一契约的连续时间、声音、能力适配和必要物理闭合，不重新导演、
不补新镜头、不重复上一段已完成的台词。

`G-06`：实际生成结果可追溯到剧本、导演决策、知识快照、参考资产、Prompt Adapter、
故事板批准和视频 Payload，并可检测镜像、换手、道具反向、视线错误和段间重复。

`G-07`：运行时间显著降低；强模型注意力用于导演判断，确定性工作、格式展开、哈希、时间、
引用映射和结构检查由本地程序完成。

### 2.2 明确非目标

- 不恢复“主连续性板”。
- 不保留以主故事板为中心的父子故事板依赖。
- 不使用固定的 `@图片2 = 本板首格`、`@图片3 = 本板末格`、
  `@图片4 = 上一段已验收视频末帧` 机制。
- 不要求一个独立生成视频继承上一条视频的全局时间。
- 不要求故事板格数机械等于视频秒数。
- 不要求视频逐像素复制故事板。
- 不让算法替 Director 选择审美答案。
- 不让 Director 编号、计算哈希、重复排版或生成 Manifest。
- 不依赖 DeepSeek 识图；文本模型只负责文本计划和文本审查。
- 不以隐藏推理全文作为运行产物或验收证据。
- 不因提示词更长而认为控制更强。
- 不在本方案阶段切换生产入口或删除仍受保护的 v4。

## 3. 不可协商架构不变量

### 3.1 单一创意真源

`INV-SOURCE-01`：每个 Generation Segment 只有一个已提交的
`VisualExecutionContract`。

`INV-SOURCE-02`：Storyboard 与 Video Prompt 不互相派生；二者只能从同一契约投影。

`INV-SOURCE-03`：实际故事板图片是“实现结果和用户批准证据”，不是默认的第二创意真源。

`INV-SOURCE-04`：任何故事板纠正若改变可见内容，必须先回写契约、重新投影并重新批准，
不得只改视频提示词。

### 3.2 无主故事板与无固定跨段首帧

`INV-NOMASTER-01`：不再生成或依赖主连续性板、主故事板整图及其格子裁图。

`INV-NOMASTER-02`：旧 `DIRECTOR_MASTER.md` 不再作为新架构的运行时创意文件。
其可复用语义迁移到结构化契约；旧文件仅作迁移输入或历史证据。

`INV-NOMASTER-03`：跨段连续性由结构化 Handoff State 和明确硬切设计表达，不由上一段末帧
强制裁决下一段首帧。

`INV-NOMASTER-04`：若下一段为硬切，开场构图必须来自 incoming Shot 的导演选择。
不得为了“连续”回退到上一段构图。

### 3.3 时间

`INV-TIME-01`：每个独立视频 Payload 的显示时间从本段 `0s` 开始。

`INV-TIME-02`：全局分集时间只能存在于机器 Manifest，禁止进入故事板或视频正向提示词。

`INV-TIME-03`：机器事实使用整数 tick 和 `[start,end)`；显示秒数由编译器派生。

`INV-TIME-04`：台词、动作、切点、HOLD 和声音都有明确区间或瞬时节点，不能依靠自然语言顺序猜测。

### 3.4 空间、人物和道具

`INV-SPACE-01`：每个 Shot 必须绑定世界空间和银幕空间：
摄影机侧位、轴线、screen-left/right、人物槽位、朝向、视线目标、运动向量和景深层。

`INV-SPACE-02`：`mirror_flip_forbidden` 为默认硬约束；画幅重构不能用镜像翻转代替。

`INV-SPACE-03`：人物服装、身份、站位与运动方向分别建模，不压成一条模糊人物描述。

`INV-PROP-01`：高风险道具必须记录持有人、左右手、抓握方式、可见表面、正反方向、屏幕/开口
朝向和状态转换。

`INV-PROP-02`：手机等物体用正向物理描述闭合，例如“右手持机、屏幕平面朝向人物、
不透明后壳朝向摄影机”，不得主要依靠“不要拿反”等负向句。

`INV-GAZE-01`：视线目标是 LOCKED 关系。人物“目送离去者”允许背侧或三分之二背面机位，
不强制眼球必须清晰可见。

### 3.5 参考资产与音色

`INV-REF-01`：资产权威使用稳定 `asset_id + content_sha256 + role`，`@图片N` 只是在目标平台
Payload 中临时映射的槽位名。

`INV-REF-02`：引用职责分离为 identity、wardrobe、blocking_layout、scene_layout、
prop_geometry、composition、motion、voice。一个素材不得自动承担未声明职责。

`INV-REF-03`：Storyboard 与 Video Payload 使用同一份角色、服装、站位和道具责任绑定。

`INV-REF-04`：整张故事板图片默认不作为视频生成的高优先级视觉引用。只有目标平台实测证明
有收益且不造成线稿风格、重复构图或注意力冲突时，才可作为低优先级 composition 引用。

`INV-AUDIO-01`：每句需要人物声音的对白必须绑定 `character_id` 与 `voice_asset_id`，
并声明画内/画外、起止时间、重叠、口型同步和后期混音职责。

### 3.6 Prompt 纯净度

`INV-LEAK-01`：状态摘要哈希、合同哈希、global time、内部节点 ID、审查备注和链路说明只进
Manifest，不进创意正文。

`INV-LEAK-02`：不可见剧情、导演解释和文学评价不能进入可见画面描述。

`INV-LEAK-03`：禁止出现“眼球内极微反光角度变化”“戏剧反讽——该词此前被定义为……”
这类不可稳定执行、泄漏叙事解释或会抢占生成注意力的描述。

`INV-LEAK-04`：负向项目只进入独立 prohibition/negative route。若目标模型会从否定句提取名词，
该负向文本不得进入正向 Payload。

`INV-LEAK-05`：视频提示词不得出现“本段结束后由下一段连续续播”等面向下一个视频的模糊指令。
交接只写机器 Handoff；当前 Payload 只描述当前视频。

### 3.7 对白与段间去重

`INV-DIALOGUE-01`：对白事件拥有稳定 `dialogue_event_id` 和剧本来源范围。

`INV-DIALOGUE-02`：相邻 Segment 不得绑定同一对白事件，除非剧本明确要求重叠或重复。

`INV-DIALOGUE-03`：已经生成完成的 Segment 默认冻结；后续修复只能修改未完成 Segment，
除非用户明确授权回改。

## 4. 目标架构

```text
Episode Script + Project Facts + User Constraints + Asset Registry
    ↓
Fact Extractor（确定性骨架，不做镜头）
    ↓
Director Phase A：Scene Interpretation
    ├─ SceneIntentContract
    └─ DirectorProblemSet
           ↓
    Knowledge Planner：问题级检索、过滤、冲突暴露
           ↓
    DecisionPacket（最小知识包）
           ↓
Director Phase B：Blocking First, Then Shot Design
    ├─ DirectorDecisionRecord
    └─ VisualExecutionContract（唯一创意真源）
           ↓
Deterministic Compilers
    ├─ StoryboardProjection → Storyboard Prompt/Payload
    ├─ VideoProjection → Human Video Prompt
    ├─ Target Adapter → Actual Render Payload
    └─ DPViewProjection
           ↓
Text Structural Gates
           ↓
Storyboard Generation + Observed Storyboard Gate
           ↓
User Approval / Typed Correction
           ↓
Video Generation + Observed Video Gate
           ↓
PreviewFidelityReport + RenderEvidence
```

依赖方向只能向下。知识层不能导入编译器，编译器不能导入 Director Provider，视觉验收层不能
回写已提交契约，只能产生问题报告或新的修订请求。

## 5. Director Agent 施工设计

### 5.1 一个 Director、两个显式阶段

同一分集保持一个 Director 身份，场景内分两阶段：

#### Phase A：解释与问题建模

只回答：

- 场景在本集中的功能是什么；
- 开始和结束时权力、关系、风险或信息发生什么变化；
- 观众已知、角色已知和隐藏信息分别是什么；
- 注意力从哪里转移到哪里；
- 核心空间问题、表演问题、节奏问题和生成风险是什么；
- 当前场景的视觉动词、节奏策略、必须保留和必须避免是什么；
- 哪些问题需要知识支持。

Phase A 禁止输出具体焦段、镜头时间线和最终运镜答案。

#### Phase B：调度与镜头

输入只包含剧本事实、Phase A、最小知识包、资产职责、目标能力和用户约束。

固定判断顺序：

1. 场面调度和空间关系。
2. 人物位置、朝向、视线、动作路径和道具状态。
3. 注意力与信息释放阶段。
4. 候选镜头/切换拓扑比较。
5. 机位、景别、焦段意图、运镜、构图和光影。
6. 表演、对白、声音和落幅。
7. 目标模型复杂度压缩与自由度走廊。

Director 必须输出一个已选择方案。允许在决策记录中简述：

- 采用方案；
- 采用理由；
- 使用了哪些决策胶囊及其作用字段；
- 被拒绝的最多两个替代方案及拒绝原因；
- 风险和允许优化范围。

不要求、也不保存模型的私有思维链全文。高推理强度通过 Provider 配置启用，工程验收依赖结构化
决策、证据、候选比较和可观察结果，而不是依赖模型暴露隐藏推理。

### 5.2 Director 不承担格式劳动

Director 不生成：

- `@图片N` 顺序；
- 哈希和时间显示格式；
- Markdown 重复章节；
- 编号含义、固定提示前缀和路由标记；
- Payload Manifest；
- Golden 对比表。

这些均由确定性编译器完成。

## 6. 知识胶囊重构

### 6.1 离线标准化

完整书籍、理论摘要和旧知识只作为离线来源，不直接进入运行时。每条知识拆成单问题胶囊，至少包含：

- `capsule_id`
- `source`、bibliographic locator、source hash、授权状态
- `type`：dramatic / blocking_performance / camera_shot / editing_validation / anti_pattern
- `tags`
- `decision_level`
- `director_problem`
- `dramatic_function`
- `triggers`
- `contraindications`
- `required_context`
- `execution_rules`
- `expected_effect`
- `tradeoffs`
- `alternatives`
- `related_capsules`
- `conflicting_capsules`
- `inference_required`
- `inference_prompts`
- `confidence_level`
- `review_status`

### 6.2 两阶段检索

第一阶段按 `DirectorProblemSet` 检索问题卡，只帮助确定“要判断什么”。人物调度尚未固定前，
不得过早注入焦段、运镜和切镜答案。

第二阶段在 blocking 已确定后，按具体执行问题检索 camera/edit/performance 卡。

每个场景正常预算：

- 0–3 张主要相关卡；
- 最多 1 张冲突卡；
- 最多 1 张反模式卡；
- 无匹配时返回 K1，不回退通用镜头模板。

### 6.3 冲突和优先级

优先级：

1. 当前剧本与用户明确约束。
2. 已批准人物、服装、空间、道具和声音事实。
3. 当前场景的戏剧职责与角色动机。
4. 当前目标平台已验证能力。
5. 高适用性的真实生成证据。
6. 理论与教材。

算法只暴露冲突，Director 选择；不得用总分静默决定创意答案。

### 6.4 证明知识真正被使用

`DirectorDecisionRecord` 记录：

- `selected_capsule_ids`
- `decision_fields_influenced`
- `application_summary`
- `rejected_capsule_ids`
- `rejection_reason`

验收同时进行 no-knowledge、K1-only、K1+K2、K1+K2+K3 消融。只有结果改善而不是文本变长，
才证明知识有效。

## 7. 唯一视觉执行契约

### 7.1 契约分层

#### SceneIntentContract

保存场景解释，不含最终镜头答案：

- scene_function
- dramatic_change
- power_change
- audience_knowledge
- character_knowledge
- hidden_information
- attention_start / attention_end
- visual_verb
- tempo_strategy
- must_preserve
- avoid_list
- director_problems

#### VisualExecutionContract

保存唯一最终导演选择：

- contract_id / schema_version / source hashes
- local canonical timeline
- generation segments
- cinematic shots
- internal boundaries
- visual beats
- storyboard panel references
- blocking states
- camera states
- visibility states
- lighting states
- performance states
- prop states
- dialogue and sound events
- reference bindings
- fidelity classes
- freedom corridors
- final handoff

### 7.2 每个 Shot 的最低字段

- dramatic_function
- attention_target
- information_action
- blocking_state_id
- axis_id / camera_side / screen_order
- shot_size / focal_intent
- camera_pose / camera_motion
- composition
- lighting
- performance
- gaze_target
- prop_state_ids
- dialogue_event_ids
- start_state_id / end_state_id
- cut_in_reason / cut_out_reason
- selected_capsule_ids
- freedom_corridor

### 7.3 人物、手机和镜像的结构化字段

人物状态：

- world_position
- screen_position
- body_facing
- head_facing
- gaze_target
- movement_vector
- visible_body_parts
- wardrobe_state_id

道具状态：

- holder_character_id
- holder_hand: left / right / both / none
- grip
- visible_surface
- front_vector
- screen_plane_normal
- target_facing
- open_closed_state
- continuity_owner

摄影机状态：

- axis_id
- axis_side
- position_relation
- view_direction
- lens_intent
- movement_path
- mirror_flip_forbidden

这些字段必须同时进入 Storyboard 与 Video 的相应投影，避免只在一边声明。

## 8. Storyboard 与 Video 双编译

### 8.1 Storyboard 编译

Storyboard Panel 不是“每秒截图”，而是对 Visual Beat/Boundary 的显式选择。

必须成格的事件：

- 起幅；
- 新 Shot 的 incoming 状态；
- 注意力目标变化；
- 人物槽位、朝向、视线或运动方向变化；
- 道具持手、正反面、状态或归属变化；
- 运镜路径中构图意义发生变化的阶段；
- 内部切镜两侧；
- 关键表演可见状态；
- 最终落幅。

连续 HOLD 且画面关系未变时不强制重复格。一个 10 秒视频可以合法拥有多于或少于 10 格，
但每格必须引用不同 Beat/Boundary 或明确 HOLD 区间；无来源的装饰格失败。

### 8.2 Video Prompt 编译

Video Prompt 使用同一 Shot、Beat、Boundary、AudioEvent 和 ReferenceBinding：

- 展开连续时间；
- 描述动作相位和摄影路径；
- 写入对白、声音和音色绑定；
- 写入目标平台可执行的参考职责；
- 写入必要的正向物理闭合；
- 按 Adapter 路由负向项；
- 保留同一开场、关键阶段、切镜和落幅。

禁止：

- 从故事板图片重新猜镜头；
- 为了“更流畅”增加新动作或新切镜；
- 重复上一 Segment 已说完的台词；
- 把 global 时间当本段时间；
- 把机器元数据写入正文。

### 8.3 同源证明

两份投影 Manifest 都保存：

- `contract_fingerprint`
- `source_node_ids`
- `compiler_version`
- `adapter_version`
- `reference_binding_fingerprint`
- `audio_binding_fingerprint`

这些字段不进入用户创意正文。

验证比较结构化 AST：

- Segment/Shot/Boundary 拓扑；
- tick；
- phase；
- 景别、运镜、构图和注意力；
- 人物槽位、轴线、方向、视线；
- 道具持手和朝向；
- ReferenceBinding；
- AudioEvent；
- 起幅、落幅和 Handoff；
- Freedom Corridor。

不得用自然语言相似度替代来源绑定。

## 9. 实际媒体的预览一致性

### 9.1 文本模型的边界

DeepSeek 可以审查：

- 剧本—诊断—决策—契约逻辑；
- Storyboard Prompt 与 Video Prompt 的同源结构；
- 重复对白、泄漏、时间、引用职责和可执行性。

DeepSeek 不能识图，因此不能裁决：

- 实际人物是否换脸或换衣；
- 实际画面是否镜像；
- 手是否切换；
- 手机是否拿反；
- 视线是否真正指向离去者；
- 实际构图与故事板是否一致。

视觉结果由用户、具备视觉能力的离线评估器或两者共同验收。

### 9.2 Storyboard 实现检查

实际故事板图生成后，对每格检查：

- panel_id 与 Beat/Boundary 对应；
- 人物身份、服装和数量；
- screen-left/right 与轴线；
- 站位、朝向、视线目标；
- 道具持手、正反面和可见表面；
- 景别、构图、注意力中心；
- 运镜箭头和切镜标记；
- 光源角色；
- 无额外文字、哈希、时间元数据或叙事解释。

失败必须回到对应契约字段或生成执行约束，不能只在 Video Prompt 里补救。

### 9.3 Video 实现检查

实际视频用 FFmpeg 提取：

- 起幅；
- 每个 Storyboard Panel 对应 tick 的最近可用帧；
- 每个 Boundary 前后帧；
- 落幅。

视觉检查比较相同不变量，并额外检查：

- 切镜数量和顺序；
- 动作阶段与运动方向；
- 摄影机运动；
- 人物/道具连续性；
- 对白事件和音色；
- Storyboard 未展示的新可见事件。

### 9.4 预览等级验收

硬指标必须 100%：

- 剧情事实与事件顺序；
- Shot/Boundary 拓扑；
- 人物身份、服装和数量；
- 镜像禁令、轴线和运动方向；
- 视线目标；
- 道具归属、持手和正反方向；
- 起幅与落幅职责；
- 对白不重复、声音身份正确。

软指标初始目标：

- Storyboard 实现综合相似度不低于 0.90；
- Video 对已批准 Storyboard 的综合预测一致性不低于 0.85；
- 构图、注意力、景别、摄影运动、表演和光影任一维度不得低于 0.80。

阈值在首批已批准真实媒体校准后冻结；冻结前不得进入 Production。

## 10. Prompt 注意力与参考图策略

### 10.1 最小责任包

每个 Payload 只携带当前 Shot/Segment 需要的引用，不把整套资产和整张主板一起上传。

优先级：

1. 人物 identity + wardrobe。
2. blocking/layout。
3. 高风险 prop geometry。
4. 必要 scene layout。
5. 经实测有效的 composition/motion 辅助。

同一张图片承担多个职责时仍需分别声明，编译器可去重上传但不能合并职责。

### 10.2 故事板图片是否绑定视频

默认不绑定整张故事板图，原因：

- 容易吸收线稿风格而不是目标实拍风格；
- 多格画面会竞争注意力；
- 可能把多个时间节点融合到一帧；
- 与人物、站位和道具参考冲突；
- 不能代替结构化时间线。

只有 A/B 实测证明目标模型在单格 composition reference 下稳定受益时，才允许：

- 只上传当前 Shot 相关单格；
- 低于 identity/wardrobe/blocking 引用优先级；
- 不承担时间、身份、服装或道具职责；
- 记录目标模型、模式、画幅和验证日期。

## 11. 降耦合施工

### 11.1 模块边界

- `facts`：剧本事实和连续性，不依赖知识与生成。
- `director_intent`：Phase A Schema，不依赖编译器。
- `knowledge`：胶囊、检索、冲突和快照，不依赖 Shot Schema。
- `director_execution`：Phase B 输出和执行契约。
- `projection`：纯函数投影，不调用模型、不检索知识。
- `adapter`：目标平台能力与字段路由，不改变导演语义。
- `validation`：结构、可见性、同源、媒体观测。
- `runtime`：状态、锁、事务、缓存、恢复。
- `evidence`：调用、运行、用户评价和晋升。

禁止通过 Markdown 解析把上游创意重新变成机器真源。机器契约先存在，Markdown 只是视图。

### 11.2 可复用设施

保留并扩展：

- Canonical Timeline 与 tick。
- Generation Segment / Cinematic Shot 分层。
- SourceSpan、canonical serialization 和 fingerprint。
- Storyboard/Video Projection 与 Renderer 的纯函数思路。
- Knowledge inventory、snapshot、retrieval budget。
- ConflictGraph 的接口，但替换仅关键词的冲突判断。
- Fidelity Contract、Visibility、Handoff。
- Structural Runner 与 mutation gate。
- Atomic Commit、Concurrency Lock、Session State、Feature Gate、Rollback。

### 11.3 退役或隔离

- 主连续性板和父子故事板依赖。
- `@图片2/@图片3/@图片4` 固定语义。
- `DIRECTOR_MASTER.md` 作为新运行时机器真源。
- Storyboard 输出反向生成 Video Prompt。
- 全局时间进入局部 Payload。
- 把全文教材作为单次 Director 上下文。
- 用关键词分数直接决定导演答案。
- 正向正文中的负向名词堆叠。
- 可见画面中的审查解释、哈希和状态说明。

旧产物只读保留，迁移不原地覆盖。

## 12. 性能优化目标

### 12.1 当前耗时根因

- 固定长 system/contract 在每轮重复。
- Director 被迫输出大量格式字段。
- 检索加载候选过多或多次重复。
- 一个局部错误触发整场重做。
- Director 与 DP 多轮串行。
- 每次重跑全量文件、全量知识和全量测试。
- 缓存键与依赖失效粒度过粗。

### 12.2 优化措施

1. 知识离线标准化、索引、去重和 hash；运行时只取最小卡片。
2. Episode facts、项目视觉事实和资产卡内容寻址缓存。
3. Phase A、Knowledge Packet、Phase B 和 Projection 分别缓存。
4. 只有依赖字段变化才使下游缓存失效。
5. Director 只输出结构化决策；Markdown 由本地编译。
6. 同一场景正常路径限制为 Phase A 1 次、Phase B 1 次、DP 1 次。
7. 定向修订只发送问题 Shot、相邻 Boundary 和相关状态，不重发整集。
8. 无冲突知识、资产解析和独立场景预处理可并行。
9. 快速模型/确定性程序用于事实格式检查；强模型只用于导演选择与必要语义审查。
10. 本地 Gate 分层运行：改哪个模块只先跑对应单测，提交前再跑集成和 Golden。
11. 输出内容与 Provider 缓存前缀稳定化，避免无意义时间戳破坏缓存。
12. 不把隐藏思维链保存和反复传回模型；保存精炼决策记录。

### 12.3 性能验收

先记录当前基线，再冻结目标：

- 本地 Schema/编译/同源检查 P95 各小于 5 秒。
- 热缓存场景重编译不调用 Director。
- 只改 Video Adapter 不使 Director、知识检索和 Storyboard 失效。
- 只改一个 Shot 的 Director 修订不重做无关 Shot。
- 正常单场模型调用不超过 3 次。
- 自动 Director 修订最多 2 轮，超出后停止并给用户证据。
- 相对当前同规模冷运行，外部模型调用数至少下降 40%。
- 相对当前同规模热修订，墙钟时间至少下降 70%。

外部模型排队不作为本地 SLO，但必须记录。

## 13. 施工工作包与顺序

### WP-0：目标冻结与证据集

产物：

- 本施工方案。
- 机器目标锁。
- 历史用户问题回归清单。
- Calibration/Golden 与未知剧本 Holdout 分离。

退出条件：

- 每个后续任务映射至少一个目标和验收项。
- 无“主故事板/固定图片2-4”依赖。

### WP-1：受控运行底座

完成当前控制器 R2.1、R2.2：

- 原子写入、跨进程锁、崩溃恢复。
- CLI、状态持久化、Shadow 隔离。

该阶段不得改变 Director 创意语义。

### WP-2：知识卡与 Phase A

完成并扩展当前 R2.3：

- 知识来源清单与隔离。
- 决策胶囊 Schema。
- 两阶段检索、冲突、预算、快照。
- SceneIntentContract 与 DirectorProblemSet。
- 提示注入和不可信文本边界。

退出条件：

- 不同导演问题获得不同最小知识包。
- 无匹配不回退模板。
- Phase A 不输出镜头答案。

### WP-3：Director Phase B 与唯一执行契约

新增 vNext.1 受控任务，不应被现有修复队列省略：

- Director Provider 接口与持久身份。
- blocking-first 决策流程。
- VisualExecutionContract。
- 人物、道具、视线、轴线、声音和 ReferenceBinding。
- 候选比较与决策记录。

退出条件：

- 未知剧本可由真实 Director 生成合法契约。
- 无手工构造 GenerationSegment 才能通过的依赖。

### WP-4：双编译与目标平台 Adapter

- StoryboardProjection vNext.1。
- VideoProjection vNext.1。
- Human Prompt 与 Render Payload 分离。
- 本段局部时间。
- Voice binding。
- 正向可见性闭合与负向路由。
- 无内部元数据泄漏。

退出条件：

- 两份输出共享同一 contract fingerprint 和 node provenance。
- 编译器零创意改写。

### WP-5：文本与媒体验收

- 字段级同源校验。
- Prompt 泄漏扫描。
- 对白去重。
- 镜像/轴线/持手/视线/道具方向硬门。
- Storyboard Run Record。
- Video Run Record。
- FFmpeg 关键帧抽取。
- PreviewFidelityReport。

退出条件：

- 文本同源、实际故事板实现和实际视频预测三个等级可区分。

### WP-6：性能与局部修订

- 内容寻址缓存。
- 依赖图与增量失效。
- Shot 级 Targeted Revision。
- 并行只读预处理。
- 调用/字符/耗时遥测。

退出条件：

- 达到第 12.3 节性能目标。

### WP-7：Shadow、Pilot、Canary 与切换

- Golden 反向回放。
- 未知剧本盲测。
- Knowledge ablation。
- 实际故事板和视频小样。
- 回滚演练。
- 用户明确批准 Production。

未经用户批准不得删除 v4 或切换入口。

## 14. 必须覆盖的历史问题回归

`REG-01`：故事板第 3 格的镜头职责错误。  
`REG-02`：相邻格人物手部切换。  
`REG-03`：目送离去者却错误强制眼睛正面可见。  
`REG-04`：局部视频提示词泄漏 global 时间。  
`REG-05`：状态摘要 SHA-256 泄漏。  
`REG-06`：视频位置相对故事板镜面翻转。  
`REG-07`：手机换手、正反面或朝向错误。  
`REG-08`：正向正文出现不可执行微细节、文学解释和剧情旁注。  
`REG-09`：相邻 N/O Segment 重复内心对白或台词。  
`REG-10`：视频提示词遗漏人物音色绑定。  
`REG-11`：Storyboard/Video 提示词不是同一镜头计划。  
`REG-12`：故事板格数被机械限制为 2 格或机械等于秒数。  
`REG-13`：旧首帧连续性规则造成硬切回退。  
`REG-14`：引用整张故事板导致多时间节点融合和注意力不足。  
`REG-15`：未使用知识库导致对话场景平淡、节奏缓慢。  
`REG-16`：写入禁止物体名称反而诱导模型生成该物体。  
`REG-17`：视频 Prompt 写“交给下一段续播”造成职责不清。  
`REG-18`：已经完成的视频被后续修复意外改动。  

每项必须至少有：

- 单元或 mutation 测试；
- Golden/fixture；
- 失败诊断码；
- 对应修复层；
- 若依赖视觉结果，则有实际媒体或人工验收记录。

## 15. 验收矩阵

### 15.1 自动硬门

- Schema fail-closed。
- Canonical Timeline 无越界、重复、空洞和端点歧义。
- Storyboard/Video AST 同源。
- Reference/Voice binding 完整。
- Prompt 无 global、hash、内部 ID 和审查说明泄漏。
- DialogueEvent 不跨 Segment 重复。
- 轴线、screen order、movement direction 和 mirror flag 一致。
- PropState 的 holder hand、visible surface 和 orientation 一致。
- Storyboard 可见纠正不会绕过重新批准。
- 编译器同输入字节级稳定。

### 15.2 Golden 反向回放

从已认可的故事板与视频结果反推执行契约，再重新编译，检查：

- 成功结构是否能被契约完整表达；
- 两份提示词是否保留原有有效控制信号；
- 是否去掉历史泄漏与多余格式；
- 不把 Golden 的具体答案硬编码为未知场景模板。

### 15.3 未知剧本 Holdout

Holdout 在胶囊和模板设计完成前冻结。验证：

- Phase A 问题是否合理；
- 知识包是否因问题而异；
- Blocking 是否先于镜头；
- 是否产生单一可执行方案；
- Storyboard 是否真正预示 Video；
- 是否复制 Golden 镜头套路。

### 15.4 真实媒体

至少覆盖：

- 双人对话与离场目送；
- 手机/屏幕与持手；
- 内部硬切；
- 连续运镜；
- 画幅重构；
- 画外声音与音色；
- 道具翻转或表面揭示。

只有实际媒体硬不变量通过、用户接受主要效果且 Render Run Record 完整，才能晋升为 validated。

## 16. 失败策略与风险压力测试

### 16.1 同源但生成仍偏移

原因：生成模型并不严格执行文本或参考。  
处理：文本同源只授予 `PLANNED_PREVIEW`；视觉失败触发具体字段修订或重新生成，不修改无关设计。

### 16.2 参考过多导致注意力稀释

处理：按职责和时间范围裁剪；默认不上传整张故事板；超过引用预算时阻断而不是任意丢弃。

### 16.3 约束过多导致画面僵硬

处理：硬不变量与 Freedom Corridor 分离。中间运动、自然微表演、布料和光影微变化可在不改变
节点和落幅的范围内优化。

### 16.4 知识使场景模板化

处理：胶囊只回答问题和条件；Director 必须记录当前适用原因和被拒绝替代；Holdout 与消融检测
重复方案。

### 16.5 修订循环重新变慢

处理：错误必须定位到 fact/shot/beat/reference/audio/adapter；只使依赖节点失效。两轮后停止自动修订。

### 16.6 文本审查误称视觉通过

处理：DeepSeek/文本 DP 的输出只能标记 `TEXT_VALIDATED`，不能标记
`STORYBOARD_REALIZED` 或 `VERIFIED_PREDICTIVE_PREVIEW`。

### 16.7 旧队列未包含真正 Director 运行

当前 R0–R3 修复队列主要完成基础设施和安全，不足以单独证明真实 Director 已接通。完成当前修复队列后，
必须新建受控 vNext.1 Director 工作包 WP-3 至 WP-7；不得因旧队列显示 COMPLETE 而宣布最终目标完成。

## 17. 完成定义

只有以下全部成立，才可称本次重构完成：

1. 真实 Director 在未知剧本上完成 Phase A 和 Phase B。
2. 知识使用有选择、有冲突裁决、有适用性证据，不是加载全文或引用标签。
3. `VisualExecutionContract` 是唯一创意真源。
4. 无主故事板、无固定图片2/3/4、无上一段末帧强制首帧。
5. Storyboard 与 Video Prompt 从同一契约机械编译且字段级通过。
6. 局部时间、引用、音色、人物服装、站位、视线、道具持手和朝向完整。
7. 所有历史问题回归通过。
8. Golden 与未知 Holdout 都通过，且知识消融证明有实际提升。
9. 实际故事板图和视频在硬不变量上通过，并达到冻结后的预览一致性阈值。
10. 性能目标达成，崩溃恢复、并发、回滚和生产隔离通过。
11. 用户明确批准生产切换。

在第 9 项之前，只能说“计划同源”；不能说“实际视频一定与故事板一致”。

## 18. 立即施工顺序

1. 冻结本文件和机器目标锁。
2. 完成当前 R2.1 事务/锁，保证后续产物不会部分写入。
3. 完成 R2.2 Runtime/Shadow。
4. 按本方案改造 R2.3 知识与 Phase A。
5. 完成现有安全修复队列，但不误宣称 Director 已完成。
6. 建立 vNext.1 受控队列，实施 WP-3 至 WP-7。
7. 在任何 Prompt 模板施工前先写对应 Contract Schema 和失败测试。
8. 在任何生产切换前完成真实故事板与视频小样验收。

