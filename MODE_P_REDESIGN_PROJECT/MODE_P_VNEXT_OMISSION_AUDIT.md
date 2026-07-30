# MODE:P vNext 遗漏项与反向失效审计

> 审计日期：2026-07-22
>
> 审计对象：`MODE_P_VNEXT_LOOP_SPEC.md`、知识审计、Golden 证据、当前 MODE:P 代码与测试基线。
>
> 状态：用户已批准修复；本报告中的 P0/P1 已作为 LOOP 的生产阻断条件。

---

## 1. 审计方法

本轮不再证明既有方案正确，而是假设系统会在生产中失败，并从以下方向反查：

1. 知识证据与目标模型适用性。
2. 剧本事实到画面约束的覆盖。
3. 时间、切点、保持和音频同步。
4. 摄影机运动中的动态可见性。
5. 横竖画幅重构和跨镜交接。
6. 参考资产、平台槽位和实际提交载荷。
7. 用户批准、纠正影响和失效边界。
8. 外部故事板/视频运行的证据链。
9. 大模型调用、上下文截断和可重放性。
10. Windows 编码、Canonical Serialization 和全量测试健康度。

---

## 2. 审计结论

原设计已经正确解决了“知识过载、算法越权、故事板/视频双源、可见性泄漏、负向路由和生产状态”问题，但仍漏掉了八个会直接破坏故事板预测能力或生产可追溯性的 P0，以及八个会造成质量漂移的 P1。

最关键的新结论：

> 可见性、时间和连续性都不是 Shot 级静态属性；它们必须在 Canonical Timeline 上随 Beat 变化。故事板批准也不是一个布尔值；纠正必须先判定是否改变已批准的可见画面。

---

## 3. P0 生产阻断项

### P0-08 Canonical Timeline 缺失

问题：

- “0-3s”可能被理解为三秒区间，也可能被理解为包含 0、1、2、3 四个状态。
- 切点属于前镜还是后镜没有定义。
- 10 秒镜头写出 0-10s 共 11 个状态时无法判定是否越界。
- 视频模型输出帧率未知时，文本中的逐帧精度可能是伪精度。

关闭要求：

- Master 使用有理数 timebase 和整数 tick。
- 所有持续区间采用 `[start,end)`。
- 瞬时状态使用 `at`，不能伪装成时长。
- Boundary 在一个精确 tick 上发生；该 tick 起属于 incoming Shot。
- 平台输出帧率未验证时只承诺时间容差，不承诺帧号。
- 显示秒数由编译器确定性派生。

### P0-09 动态 Visibility State 缺失

问题：每个 Shot 只有一份 Visibility Contract，但推、绕、摇、旋转和反射路径会在镜头内部改变可见表面。

关闭要求：

- 每个 Visibility State 具有 `valid_time_range`。
- Visual Beat 引用 `visibility_state_id`。
- 表面揭示、遮挡、反射路径建立或断开必须产生 Visibility Boundary。
- 后段允许看见的信息不得提前进入前段正向正文。
- DP 审查整条摄影路径，而不只审查起幅和落幅。

### P0-10 剧本事实覆盖与交接状态不足

问题：Fidelity 虽声明剧情事实 LOCKED，但没有证明所有关键事实都已被覆盖；`entry_state`、`exit_state` 也缺少最低结构。

关闭要求：

- 每条场景事实有稳定 `fact_id` 和原文定位。
- Segment 声明 `fact_bindings` 与 `fact_render_policy`。
- 每条事实明确为 visible、audio_only、narrative_only、not_in_segment 或 locked_execution。
- Director 不能把行为、方向、是否看向、道具归属和事件顺序降级为 ELASTIC。
- Entry/Exit/Handoff 至少保存人物位置与朝向、动作阶段、道具状态、摄影机侧位、焦点、主光状态、可见表面和声音延续。

### P0-11 故事板批准纠正缺少影响分级

问题：`approved + correction` 可能被直接写入视频提示词，从而产生故事板没有批准过的新画面。

关闭要求：

- `clarification_only`：只解释已存在画面。
- `render_constraint_only`：只改变生成执行，不改变可见构图。
- `storyboard_visible_change`：批准失效，重新生成故事板。
- `topology_or_fact_change`：回到 Master 和 DP。
- Director 提议影响级别，DP核对，用户最终确认。
- 新增可见实体、动作、切镜、方向、表面或时间节点一律不得归为 clarification。

### P0-12 参考资产与外部运行证据未闭环

问题：`@图片1` 之类人类标签没有绑定实际平台槽位；外部生成的视频也没有证明来自哪份 Render Payload。

关闭要求：

- Reference Binding 记录内容 hash、版本、只读路径、平台别名/槽位、方向/裁切、有效时间范围、职责和优先级。
- 同一职责多个素材必须声明冲突裁决。
- 新增 STORYBOARD_RUN_RECORD 与 RENDER_RUN_RECORD。
- 运行记录绑定提交文本、实际资产、平台参数、任务ID、输出hash和模型/产品版本。
- 没有运行记录的媒体可以人工评价，但不得晋升为 K3 validated 证据。

### P0-13 大模型可重放语义不准确

问题：相同输入再次调用非确定性模型不能保证得到相同 Master；现有 `reproduce` 容易被误解为重新调用模型后字节相同。

关闭要求：

- `replay_compile`：从已保存原始响应或 Master 重新确定性编译。
- `reinvoke`：相同输入重新调用模型，必须新建分支。
- Model Invocation Snapshot 保存完整请求 hash、system/contract hash、resolved model、provider revision、采样参数、finish reason、截断状态、原始响应 hash 和调用ID。
- 上下文压缩或模型切换视为调用输入变化。

### P0-14 Capability 与 Prompt Adapter 不完整

问题：当前能力配置没有负向策略、提示词方言、画幅/帧率、内部切镜、文字、音频和口型字段。

关闭要求：

- 每个目标平台必须有版本化 Prompt Dialect Adapter。
- Capability Profile 必须声明负向策略、时长量化、画幅/分辨率/帧率、内部切镜、参考槽位、文字/UI、音频/口型、提示词长度和复验日期。
- 未知字段保守阻断或降级，不得乐观推断。
- 人类 VIDEO_PROMPT 格式保持项目模板；实际 Render Payload 由目标平台 Adapter 路由。

### P0-15 完整上下文预算与截断处理缺失

问题：只限制知识字符数，没有限制 system、事实、资产卡、历史 Master、纠正和 DP 反馈的总上下文。

关闭要求：

- 预算计算覆盖完整请求和预留输出。
- 使用目标模型 tokenizer；不可用时使用保守估计并留安全余量。
- 禁止静默截断事实、连续性、Visibility、Fidelity 或用户纠正。
- 输入超限进入 BLOCKED/CONFIG_REQUIRED。
- 输出必须检查 finish reason、必填尾节点和结构完整性。

---

## 4. P1 质量与治理项

### P1-08 画幅重构缺少执行契约

增加 `reframe_strategy`、protected subjects、screen order、eyeline、movement direction、negative-space function 和 crop-safe relationships。禁止镜像翻转代替重构。

### P1-09 音频与对白同步缺少结构

声音节点应记录 speaker、on/offscreen、start/end、reference offset、overlap、sync class、lip-sync requirement 和生成/参考/后期混音职责。

### P1-10 知识证据等级混合了多个维度

E0-E5 只表示来源可信等级。运行召回前还必须独立检查 target_model_match、mode_match、aspect_match、recency、replication 和 project relevance。旧模型的 E5 成功案例不能覆盖当前模型不支持的能力。

### P1-11 Golden Set 缺少留出集与消融

四组案例作为 calibration set；另建不参与卡片设计的 holdout set。发布时增加无知识、仅K1、K1+K2、K1+K2+K3 消融，验证知识确实改善而不是增加格式文本。

### P1-12 DP Evidence View 边界不够严格

DP 只读取确定性生成的 `DP_VIEW`：事实、连续性、Capability、Fidelity、Visibility、Handoff 和双输出。禁止读取 Knowledge Packet、Director 推理、历史反馈和未提交草稿。

### P1-13 不可信文本与提示注入

剧本、对白、知识原文、资产卡和用户纠正均作为带边界的数据载荷；其中类似“忽略以上规则”的内容不得成为系统指令。知识候选激活前执行来源与指令污染审查。

### P1-14 来源授权、隐私与项目隔离

知识来源记录 bibliographic locator、许可/内部使用状态和摘录 hash；人物与媒体资产记录使用授权或用户确认。K3/K4 不跨项目自动共享。

### P1-15 Canonical Serialization 与 Windows 编码

- Markdown/文本统一 UTF-8、LF。
- JSON 使用 Canonical JSON 后计算 hash。
- CLI stdout/stderr 明确 UTF-8。
- 子进程显式声明编码，禁止依赖 Windows 活动代码页。

---

## 5. 当前代码基线验证

修复前完整测试：

- 685 tests。
- 39 failures。
- 4 errors。

主要根因链：

1. Manifest v1.2 的带时间 Storyboard Frame 要求被错误应用到仍受支持的 v1.1 历史 Master，导致 precheck、DP、delivery 和 recovery 连锁失败。
2. Windows 子进程使用活动代码页输出，而部分测试按 UTF-8 解码，产生 UnicodeDecodeError。
3. 多个同步测试仍用旧英文派生标签修改文本，实际派生格式已经是中文，因此测试没有真正篡改目标字段。

修复原则：

- v1.2 继续严格要求至少两个带时间帧。
- v1.1 只兼容至少两个明确标签的旧式帧，不放松为任意文本。
- CLI 和内部子进程统一 UTF-8。
- 测试按当前中文交付契约篡改真实字段。

修复后完整验证（2026-07-22）：

- `python -m unittest discover -q`：685 tests，全部通过。
- Manifest v1.1 兼容路径与 v1.2 严格时间帧路径同时保留。
- MODE:P CLI、结构预检子进程与测试捕获端统一使用 UTF-8；复跑日志中无隐藏解码线程异常。
- 集成链验证覆盖 Master → Manifest → 派生视图 → precheck → DP 状态 → delivery。

该结果只说明**当前 MODE:P 基线已恢复为绿色**。本报告新增的 vNext Schema、Render Payload、外部运行记录和其他生产控制面仍处于规范阶段，不能据此宣称已经实现。

---

## 6. 生产切换新增阻断门

以下任一未完成，不得从 shadow 进入 pilot：

- Canonical Timeline 和动态 Visibility State Schema 未实现。
- Fact Coverage 或 Handoff Check 未实现。
- Storyboard Correction Impact 没有用户确认流程。
- Capability Profile 缺少目标平台所需字段。
- Render Payload 没有准确资产槽位和 Manifest。
- 完整上下文可能被静默截断。
- 外部运行结果无法绑定到确切 Payload。
- 全量测试不是绿色。

---

## 7. 最终判断

遗漏项不是要让算法替 Director 创作。它们全部属于确定性边界：

> 算法负责时间、ID、覆盖、路由、版本、资产、状态、编码和证据；Director 仍负责注意力、调度、机位、运镜、构图、光影、表演、声音和切换的创意判断。

完成这些补强后，MODE:P vNext 才同时具备“导演判断不被格式劳动稀释”和“故事板能够可靠预测视频”的生产基础。
