# MODE:P vNext LOOP 生产审计报告

> 审计对象：MODE_P_VNEXT_LOOP_SPEC.md
>
> 证据附件：GOLDEN_SET_EVIDENCE_REPORT.md
>
> 知识审计附件：KNOWLEDGE_BASE_AUDIT.md
>
> 遗漏项审计附件：MODE_P_VNEXT_OMISSION_AUDIT.md
>
> 审计日期：2026-07-22
>
> 状态：生产补强前审计；本报告中的缺口由 LOOP 新增生产章节关闭。
>
> 补充审计：2026-07-22，加入“可见性与生成泄漏契约”专项审计。
>
> 补充审计：2026-07-22，加入完整 24 文件知识库语义、重复、冲突与可编译性审计。
>
> 补充审计：2026-07-22，加入 Canonical Timeline、动态可见性、事实覆盖、纠正影响、外部运行证据、调用快照、Prompt Adapter 和完整上下文专项审计。

---

## 1. 审计结论

现有 vNext LOOP 已经完整描述：

- 最终目标。
- 文本模型边界。
- 知识使用方向。
- Director与算法职责。
- Generation Segment数据模型。
- 双输出格式。
- Golden Set和防偏移原则。
- 当前机位可见性、生成补全泄漏和模型负向指令分流。

但它仍属于“架构与创作流程规范”，尚缺少生产系统必须明确的运行状态、事务提交、幂等恢复、失败代码、并发锁、版本兼容、观测指标、回滚和发布治理。

审计结论：

> 创作架构可进入实现设计；在补齐生产控制面之前，不得替换当前 MODE:P 生产入口。

补充审计结论：原 vNext 虽已有 FORBIDDEN、物理纠偏和 DP 表演可见性检查，但不足以阻止模型把被遮挡或只在叙事层存在的信息生成到画面。新增 Visibility Contract 后，该缺口已在规范层关闭；运行实现仍须通过专项回归测试。

知识补充审计结论：原 vNext 的 K0-K4 方向正确，但在完整知识库审计前证据不足。审计确认旧大库存在高重复、硬规则升级、库内冲突、能力声明时效和场景胶囊粒度过粗问题。新增来源分级、证据等级、冲突暴露、Claim 级蒸馏和问题驱动检索后，该缺口已在规范层关闭；当前运行时仍未实现。

---

## 2. 审计范围

### 2.1 创作正确性

- 知识是否真正参与导演判断。
- Director是否拥有完整创作权。
- 故事板和视频是否同源。
- 内部镜头是否可在单一生成段表达。
- 有价值偏移是否能被接受。
- 剧本事实是否与当前机位可见内容分离。
- 屏幕、镜面、玻璃、文字、UI 和画外事件是否存在生成泄漏控制。

### 2.2 运行正确性

- 状态是否单义。
- 中断后是否可恢复。
- 重试是否幂等。
- 并发是否安全。
- 交付是否原子化。

### 2.3 可追溯性

- 输入、知识、能力、Master、编译器和交付版本是否可追溯。
- 用户批准是否绑定准确产物。
- 旧结果是否能重放。

### 2.4 可运营性

- 是否有日志、指标、错误代码和停止条件。
- 是否能回滚。
- 是否能灰度切换。
- 是否有维护和兼容策略。

### 2.5 安全与数据治理

- 文件路径是否受限。
- 临时文件是否隔离。
- 是否避免覆盖用户文件。
- 媒体和项目数据是否被意外上传。

---

## 3. 已满足项

### A01 文本模型边界

状态：满足。

MODE:P运行时不依赖图片、视频或音频解析。媒体只通过文字资产卡和引用职责进入。

### A02 证据权重

状态：满足。

用户真实评价和四组配对样本优先于旧文档和理论规则。

### A03 知识方向

状态：完整知识审计补充后满足。

已定义场景诊断、问题驱动检索、最小知识包和同一Director恢复设计；并已逐份处置现有 24 个知识文件。旧 P0-P3 不直接继承，v4 不参与召回，能力声明必须实测，冲突知识不得由分数静默裁决。

### A04 创作权边界

状态：满足。

算法只复制、编号、校验和排版，禁止创作或清洗导演文字。

### A05 数据模型

状态：满足。

Generation Segment、Cinematic Shot、Visual Beat、Storyboard Panel和Fidelity Contract已分离。

### A06 输出格式

状态：满足。

故事板和视频提示词固定采用真实成功样本的外部格式。

### A07 Golden Set语义

状态：满足。

四组样本能够区分连续复现、内部切镜、受控优化和行为失败。

### A08 可见性与生成泄漏

状态：补充后满足。

LOOP 已定义 Visibility Contract、正向可见性闭合、模型负向能力分流和对应文本回归组。观众席额外回复气泡作为实际失败证据，手机背面游戏画面作为用户确认的项目级风险，两者没有被混为同一证据等级。

---

## 4. 生产缺口

### P0-01 缺少正式运行状态机

风险：

- 同一场景可能在未完成DP时进入故事板批准。
- 故事板批准后Master被修改，旧批准仍被错误沿用。
- 视频提示词可能在素材未绑定时被误交付。

要求：

- 定义Episode、Scene、Segment和Approval状态。
- 明确合法状态迁移。
- 非法迁移必须阻断并输出错误代码。

关闭方式：LOOP §20。

### P0-02 缺少事务与原子提交

风险：

- 编译中断后只写出一半文件。
- Manifest与提示词版本不一致。
- working和delivery目录混用。

要求：

- 所有产物先写临时目录。
- 全部校验通过后原子提交。
- 提交必须生成Commit Manifest。

关闭方式：LOOP §21。

### P0-03 缺少批准失效规则

风险：

- 用户批准的故事板对应Master v1，但视频编译使用Master v2。
- 素材文件被替换但路径不变。

要求：

- 批准绑定Master哈希、故事板素材哈希和提示词哈希。
- 任一绑定项变化，批准自动失效。

关闭方式：LOOP §22。

### P0-04 缺少幂等与崩溃恢复

风险：

- 重试重复调用Director。
- 相同阶段产生不同版本覆盖。
- 崩溃后无法判断最后一次成功提交。

要求：

- 每个阶段具有idempotency key。
- 模型调用和编译结果分开提交。
- 恢复只从最后一个已提交状态继续。

关闭方式：LOOP §21、§23。

### P0-05 缺少错误分类和停止条件

风险：

- 所有失败都表现为通用异常。
- 创意问题与程序错误混在一起。
- 无限制修订循环。

要求：

- 定义INPUT、KNOWLEDGE、DIRECTOR、STRUCTURE、DP、APPROVAL、COMPILE、DELIVERY和SYSTEM错误。
- 定义可重试、需Director修订、需用户输入和不可恢复。
- 限制自动循环次数。

关闭方式：LOOP §24。

### P0-06 缺少可见性与生成泄漏契约

风险：

- 剧本写“人物在打游戏”，背面机位仍把游戏画面生成到手机后壳。
- 画外声音诱发模型把声源人物或物体加入画面。
- 镜子、玻璃、屏幕和反射自动补出未经设计的信息。
- 只写“禁止出现”仍把高风险名词送入会发生 token leakage 的模型。
- 人类 VIDEO_PROMPT 与实际提交给模型的字段范围不一致且不可追溯。

要求：

- 每个 Cinematic Shot 声明 visible_whitelist、occluded_state、narrative_only、audio_only、positive_closure、leakage_risks、forbidden_qa 和 negative_route。
- Director 负责可见性设计，DP 负责几何与语义审查，算法只负责字段来源校验和路由。
- targeted @禁止只能作为第二层保险；第一层必须是正向可见性闭合。
- Capability Snapshot 明确 inline、独立负向通道或 token leakage 风险。
- 建立手机背面、镜面、玻璃、画外声音、聊天空白和物体背面文本回归。

关闭方式：LOOP §2.4、§7.10、§10.5、§11.6、§11.7、§12.7、§13.7、§22.3、§30。

### P0-07 缺少完整知识来源、冲突和晋升契约

风险：

- 旧 v4 与 v5 大量重复，被当作两份证据重复加权。
- 书本候选被写成“所有场景必须”的运行硬规则。
- 构图、颜色、线条、焦段和情绪被一键映射，压制 Director 判断。
- 当前 retriever 只验证 Director 显式点名的 Capsule，无法根据诊断问题主动补位。
- 9 个 Capsule 的 verified_count 全为 0，却可能被误解为真实生成经验。
- 历史模型能力声明没有版本、实测和到期条件。

要求：

- 为现有 24 个知识文件建立只读清单、hash、来源类型和 disposition。
- v4 进入 archive；v5 等大库只作 Claim 候选提取。
- 决策卡必须有适用、不适用、反例、权衡、冲突、来源与证据等级。
- Director Phase A 提交知识问题和决策域；算法匹配、去重、过滤、暴露冲突和控制预算，但不输出镜头答案。
- 真实案例 K3 与理论卡 K2 分层；没有 RenderEvidence、跨场景证据和用户批准不得 validated。
- 能力知识必须绑定 Capability Profile hash、验证日期和复验条件。

关闭方式：`KNOWLEDGE_BASE_AUDIT.md` 全文；LOOP §5、§6、§14、§22.2、§30.7。

### P0-08 Canonical Timeline 缺失

风险：秒数端点、切点归属、保持区间和平台帧率歧义会让故事板与视频时间结构漂移。

要求：有理数 timebase、整数 tick、`[start,end)`、incoming Boundary ownership、确定性显示秒数和未知帧率容差。

关闭方式：LOOP §7.2a、§10.2、§12.8、§30。

### P0-09 动态可见性缺失

风险：Shot 内绕行、推近、物体翻转和反射路径变化时，后一阶段信息提前泄漏。

要求：Visibility State 具有 valid_time_range；Beat 引用状态；揭示/遮挡/反射变化建立 Boundary；DP 检查完整运动路径。

关闭方式：LOOP §7.10、§12.7。

### P0-10 Fact Coverage 与 Handoff 不完整

风险：关键事实漏绑定或被降级；跨镜人物、道具、摄影机、焦点、光源和可见表面状态断裂。

要求：稳定 fact_id、fact_render_policy、不可降级事实和 Structured Handoff 最低字段。

关闭方式：LOOP §7.8、§7.10a、§12.8。

### P0-11 故事板纠正影响未分级

风险：approved + correction 绕过重新批准，向视频提示词加入故事板未批准的新画面。

要求：clarification、render constraint、storyboard visible change、topology/fact change 四级路由；Director提议、DP核对、用户确认。

关闭方式：LOOP Step 11-13、§20、§22.4-22.5。

### P0-12 资产槽位和外部运行证据断链

风险：`@图片1` 无法证明实际提交的是哪份素材；实际视频无法证明来自哪份 Payload。

要求：资产 hash/版本/槽位/职责/冲突；Storyboard/Render Run Record 绑定平台任务和输出 hash。

关闭方式：LOOP §7.7、§21.7。

### P0-13 模型调用不可真正重现

风险：重新调用非确定性模型被错误称为 reproduce；system、采样或截断状态无法追溯。

要求：Model Invocation Snapshot；区分 replay_compile、reinvoke 和 regenerate。

关闭方式：LOOP §21.6、§23.6。

### P0-14 Capability 与 Prompt Adapter 不完整

风险：负向、时长、画幅、帧率、切镜、文字、参考、音频和口型能力未知，Render Payload 仍被生成。

要求：版本化 Prompt Dialect Adapter 和完整 Capability Snapshot；未知关键字段保守阻断。

关闭方式：LOOP §11.2、§12.9、§22.3。

### P0-15 完整上下文与截断处理缺失

风险：只计算知识字符数，事实、资产卡、纠正和输出可能被静默截断。

要求：完整请求+输出预留预算；finish_reason与尾节点检查；禁止静默截断。

关闭方式：LOOP Step 0、§12.9、§21.6、§29.4。

### P1-01 缺少并发与锁语义

风险：

- 同一Scene两个运行同时修改Master。
- Episode Review与场景修订竞争。
- 用户批准期间后台任务继续更新。

要求：

- Episode读锁、Scene写锁。
- 用户等待状态禁止创作性后台更新。
- 锁必须有所有者、租约和安全恢复。

关闭方式：LOOP §23。

### P1-02 缺少知识快照与可重放

风险：

- 相同Master无法重现，因为知识卡已更新。
- 检索结果发生变化但缓存未失效。

要求：

- 保存Knowledge Query、选择结果、内容哈希、索引哈希和排序版本。
- 生产重放使用原快照，不重新检索。

关闭方式：LOOP §22。

### P1-03 缺少能力配置快照

风险：

- 模型能力或平台限制更新后，旧结果无法解释。
- 生成模式选择与当前能力不一致。

要求：

- 每次设计绑定能力配置版本和哈希。
- 能力改变只使相关Segment失效。

关闭方式：LOOP §22。

### P1-04 缺少Schema兼容策略

风险：

- Master升级后旧Session无法读取。
- 编译器升级静默改变旧输出。

要求：

- 所有机器产物带schema_version。
- 只允许显式迁移。
- 禁止原地静默升级。

关闭方式：LOOP §25。

### P1-05 缺少观测和SLO

风险：

- 无法定位时间花在哪个阶段。
- 不知道上下文预算是否扩大。
- 失败率和修订次数不可见。

要求：

- 阶段事件、耗时、字符量、模型调用次数、缓存命中、修订次数和错误码。
- 定义本地确定性阶段SLO。
- 外部模型耗时只记录，不伪造稳定SLO。

关闭方式：LOOP §26。

### P1-06 缺少发布与回滚

风险：

- vNext直接替换现有入口。
- Golden Set通过但真实项目失败时无法回退。

要求：

- feature flag。
- shadow、pilot、canary、production四阶段。
- 保留旧入口和回滚点。

关闭方式：LOOP §27。

### P1-07 缺少数据安全约束

风险：

- 路径逃逸。
- 临时文件覆盖用户资料。
- 日志泄漏剧本或素材内容。

要求：

- 限制写入工作区和会话目录。
- 路径规范化。
- 临时目录隔离。
- 遥测默认记录哈希和计数，不记录完整敏感内容。

关闭方式：LOOP §28。

### P1-08 至 P1-15 补充质量与治理缺口

以下缺口在 `MODE_P_VNEXT_OMISSION_AUDIT.md` 中逐项定义，并已进入 LOOP：

- P1-08：跨画幅 reframe strategy 与保护关系。
- P1-09：对白、音频偏移、重叠、口型与混音职责。
- P1-10：证据等级之外的目标模型、模式、画幅、时效和项目适用性硬过滤。
- P1-11：Calibration/Holdout 分离和知识消融。
- P1-12：DP_VIEW 字段白名单与独立审查上下文。
- P1-13：剧本、知识、资产卡和用户纠正中的提示注入。
- P1-14：知识来源授权、媒体使用确认和项目隔离。
- P1-15：UTF-8/LF、Canonical JSON 与 Windows 子进程编码。

关闭方式：LOOP §3.3、§5.6、§7.9、§11.8、§13.8、§28.6-28.7、§30。

### P2-01 缺少资源预算

风险：

- 知识包逐渐膨胀。
- Director阶段数量失控。
- 单场修订成本不可预测。

要求：

- 知识字符预算。
- 模型调用预算。
- 修订轮次预算。
- 超预算需显式用户批准。

关闭方式：LOOP §29。

### P2-02 缺少测试分层

风险：

- 只有端到端测试，定位困难。
- 只有格式测试，无法证明导演目标。

要求：

- Schema单测。
- Compiler黄金文本测试。
- State Machine测试。
- 恢复和故障注入。
- Golden Set语义验收。
- 用户最终验收。

关闭方式：LOOP §30。

### P2-03 缺少删除和保留策略

风险：

- Session、缓存和证据无限增长。
- 用户文件被误当临时文件删除。

要求：

- 用户源文件永不自动删除。
- working、cache、telemetry和delivery分别定义保留策略。
- 清理操作必须限定明确目录。

关闭方式：LOOP §28。

---

## 5. 生产状态目标

补强后的LOOP必须实现：

~~~
可恢复
+ 可重放
+ 可审计
+ 可回滚
+ 可灰度
+ 可限制预算
+ 可区分创意失败与系统失败
+ 不突破文本模型边界
+ 可区分叙事事实、可见内容、声音信息与审查禁止项
+ 可追溯实际 Render Payload 的字段来源
~~~

---

## 6. 审计后的实施优先级

### 第一阶段：生产控制面

- State Machine。
- Artifact Envelope。
- Commit Protocol。
- Lock和Recovery。
- Error Taxonomy。

在这些完成前，不接真实生产入口。

### 第二阶段：知识闭环

- 冻结 24 文件 K0 清单和 hash。
- v4 归档、同源去重和危险规则隔离。
- Core 精简为 K1；9 个 Capsule 拆成单问题 K2 候选。
- Scene Diagnosis。
- Decision Card Schema。
- Evidence Tier、Conflict Graph 和 Capability 到期策略。
- Knowledge Query和Snapshot。
- 最小知识包。
- RenderEvidence、用户评价和经验晋升状态机。

### 第三阶段：导演与编译

- Generation Segment Master。
- Storyboard Compiler。
- Video Prompt Compiler。
- Fidelity和DP。
- Visibility Contract。
- Positive Closure 和 Negative Route。
- VIDEO_PROMPT 与 Render Payload 分域编译。

### 第四阶段：用户闸门

- Storyboard Approval。
- 批准失效。
- 用户纠正。
- Delivery Commit。

### 第五阶段：Golden与灰度

- 四组Golden。
- Visibility Contract 文本回归组。
- Shadow运行。
- 单场Pilot。
- 分集Canary。
- 用户批准Production。

---

## 7. 生产就绪判定

当前基线状态（2026-07-22）：现有 MODE:P 完整回归 `685/685` 通过，旧管道可继续作为受保护基线；以下 vNext 条件仍须逐项实现和验收，不能因基线绿色而跳过。

以下条件全部满足才允许生产切换：

- 所有P0关闭。
- 所有P1关闭或有用户批准的限时豁免。
- 24 个知识文件 disposition、hash 和来源类型通过结构测试。
- v4、重复来源、E0 隔离内容和过期 Capability 不进入运行时知识包。
- 问题驱动检索、冲突暴露、无匹配和知识预算回归全部通过。
- 没有 RenderEvidence、跨场景证据和用户批准的条目未被标记为 validated。
- 四组Golden按预期通过或失败。
- Visibility Contract 六类文本回归全部通过。
- 每个目标模型的 negative_instruction_policy 有真实测试或按 token_leakage_risk 保守运行。
- VIDEO_PROMPT、Render Payload 和 Manifest 的字段路由可审计。
- 崩溃恢复和重复提交测试通过。
- 旧Session兼容策略通过。
- 回滚演练通过。
- 用户批准当前输出格式和实际质量。

---

## 8. 审计结语

MODE:P vNext 的生产化不能只增加更多检查器。正确方向是：

> 用明确状态、版本、事务和用户闸门保护Director的创意过程；让完整离线知识先经过来源、重复、冲突和证据审计，再以最小问题包进入 Director；用知识快照保证判断可重放；用 Visibility Contract 阻止不可见叙事信息泄漏成画面；用纯复制与确定性路由保证导演语义不被程序改变；用Golden Set和用户评价判断最终效果。

本审计不授权修改生产入口。生产切换仍需用户单独明确批准。
