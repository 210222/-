# MODE:P vNext 实施计划

> 状态真源：本文件的任务复选框、`MODE_P_VNEXT_PROGRESS.md` 和当前测试证据必须一致。
>
> 执行入口：`/mode-p-vnext-rebuild [task_id]`。
>
> 生产保护：本计划采用“隔离重写 → 原子替换”。施工期 v4 只作为只读黑盒基线；未经 Shadow、Pilot、Canary 和用户明确批准，不得替换 `/mode-p-pilot`。切换后只保留一个活动 MODE:P。

> **执行暂停（2026-07-22审计）**：旧 Markdown 驱动 LOOP 产生了提前勾选、证据缺失和状态分叉。本文件现有复选框只表示历史实现声称，统一按 `IMPLEMENTED_UNVERIFIED` 处理。在 `MODE_P_VNEXT_LOOP_REPAIR_PLAN.md` 全部完成并由机器控制器迁移证据前，禁止从本文件选择下一任务，禁止输出 `LOCAL_VNEXT_READY`。

---

## 1. 任务执行契约

每个任务均适用：

- 一轮只完成一个 task_id。
- 先验证 `depends_on`，再加失败测试，再实现最小完整行为。
- 默认允许路径：`01_调度器/mode_p_vnext/`、本计划、vNext Progress、vNext Lock 和明确列出的共享入口文档。
- 默认禁止路径：`01_调度器/legacy_mode_p/`、旧 Session、现有 delivery、Golden 原始媒体、当前 v4 Schema、编译器、知识索引、缓存和 fallback。
- 若任务确需修改共享入口，必须同时提供 v4 回归和回滚证据。
- `[x]` 只表示本地工程证据通过，不表示真实模型、真实故事板或真实视频质量通过。

任务证据至少记录：

~~~text
task_id
changed_paths
focused_test_command
focused_test_result
required_regression_command
required_regression_result
spec_refs
completed_at
~~~

---

## 2. Phase V0：基线、目录与隔离

目标：建立独立命名空间、冻结证据和防污染边界。

- [x] **V0.1 冻结基线清单**  
  `depends_on: none`  
  记录当前 v4 的公开入口/输出契约与 685 项黑盒回归；记录 24 个知识候选文件和四组 Golden 文本/媒体路径及内容 hash。不得把 v4 实现作为新设计来源；媒体只记录 hash 和元数据，不复制、不解析。  
  `spec_refs: LOOP §4, §15.1; Audit P0-12/P1-14`

- [x] **V0.2 建立 vNext 包骨架**  
  `depends_on: V0.1`  
  建立 `01_调度器/mode_p_vnext/`、私有测试目录、版本模块、Schema 目录和只读 fixture 目录；默认入口不得导入 v4 创意编译器。  
  `spec_refs: LOOP §15.1, §21`

- [x] **V0.3 Canonical Serialization 基础层**  
  `depends_on: V0.2`  
  实现 UTF-8、LF、Canonical JSON、稳定 hash 和跨 Windows 代码页测试。  
  `spec_refs: LOOP §21.2; Omission P1-15`

- [x] **V0.4 v4/vNext 污染扫描器**  
  `depends_on: V0.2`  
  拒绝 vNext 写入 v4 Session/delivery，拒绝 v4 活动入口引用未批准的 vNext 模块，允许显式只读基线 fixture。  
  `spec_refs: LOOP §15.1, §24, §27`

- [x] **V0.5 Golden Fixture Registry**  
  `depends_on: V0.1,V0.3`  
  为枪管、观众席、备赛区、窄巷建立文本、图片、视频、主观评价和证据角色索引；不得把媒体二进制送入文本 Director。  
  `spec_refs: LOOP §5, §13; Golden Evidence Report`

退出条件：独立包可测试；基线 hash 可复验；交叉污染被自动阻断。

---

## 3. Phase V1：Canonical Timeline、Fact 与 Handoff

目标：首先冻结最底层确定性数据契约。

- [x] **V1.1 Canonical Timeline Schema**  
  `depends_on: V0.3`  
  定义 rational timebase、integer tick、`[start,end)`、瞬时 `at`、显示秒数派生和未知帧率策略。  
  `spec_refs: LOOP §7.2a, §10.2; Omission P0-08`

- [x] **V1.2 Timeline Validator/Compiler**  
  `depends_on: V1.1`  
  校验单调、连续、总时长、Segment/Shot/Beat 包含关系，并生成稳定显示时间。  
  `spec_refs: LOOP §7.2a, §12.8`

- [x] **V1.3 Boundary Ownership 与 HOLD**  
  `depends_on: V1.2`  
  实现切点归入切入镜头、N Shot=N+1 Boundary、显式受控 HOLD 和越界失败。  
  `spec_refs: LOOP §7.4, §10.2`

- [x] **V1.4 Fact Registry Schema**  
  `depends_on: V0.3`  
  定义稳定 fact_id、来源行号、事实类型、关键度、可见/画外/声音分类和不确定状态；程序只验证，不创作事实。  
  `spec_refs: LOOP §7.9, §9 Step 1; Omission P0-10`

- [x] **V1.5 Fact Coverage Checker**  
  `depends_on: V1.2,V1.4`  
  要求每个剧情关键事实明确映射、声明画外/声音处理或由用户批准省略；禁止静默丢失。  
  `spec_refs: LOOP §7.9, §12.8`

- [x] **V1.6 Structured Handoff Contract**  
  `depends_on: V1.3,V1.4`  
  定义 Entry/Exit/Handoff 的人物、道具、空间、动作阶段、屏幕方向、光源和声音状态，并校验相邻冲突。  
  `spec_refs: LOOP §7.10a; Omission P0-10`

退出条件：所有显示秒数、切点、保持、事实覆盖和跨镜交接均可由确定性测试证明。

---

## 4. Phase V2：动态可见性、资产、画幅与声音

目标：阻止不可见叙事信息和错误表面进入视觉输出。

- [x] **V2.1 Visibility Contract Schema**  
  `depends_on: V1.1,V1.4`  
  定义 visible_whitelist、occluded_state、narrative_only、audio_only、positive_closure 和 forbidden_qa。  
  `spec_refs: LOOP §6, §7.10; Audit P0-06`

- [x] **V2.2 Dynamic Visibility State**  
  `depends_on: V1.2,V2.1`  
  让 Visibility State 绑定时间区间，Beat 只能引用其时间范围内状态；验证进入、退出、遮挡和表面朝向路径。  
  `spec_refs: LOOP §7.10, §9 Step 6; Omission P0-09`

- [x] **V2.3 Positive Closure 与负向路由**  
  `depends_on: V2.1`  
  高风险表面必须以正向物理闭合表达；negative_route 支持 inline、separate_channel、human_qa_only 和 token_leakage_risk。  
  `spec_refs: LOOP §11.4-§11.7`

- [x] **V2.4 Reference/Asset Binding**  
  `depends_on: V0.3`  
  绑定 asset_id、内容 hash、版本、平台槽位、裁切、时间范围、职责、授权和项目隔离；解决冲突职责。  
  `spec_refs: LOOP §7.7, §11.2, §28.7; Omission P0-12/P1-14`

- [x] **V2.5 Aspect Reframe Contract**  
  `depends_on: V2.4`  
  定义横版故事板到目标画幅的 protected relationships、允许裁切/重构范围和禁止镜像规则。  
  `spec_refs: LOOP §7.8; Omission P1-08`

- [x] **V2.6 Audio/Lipsync Contract**  
  `depends_on: V1.2,V1.4`  
  对话归属、口型可见性、画外对白、时间窗、声音桥和音频职责结构化。  
  `spec_refs: LOOP §11.8; Omission P1-09`

退出条件：六类可见性泄漏测试、资产职责、画幅重构和音频路由全部可验证。

---

## 5. Phase V3：知识治理与最小检索

目标：扩大可审计离线知识，缩小单次运行知识。

- [x] **V3.1 知识来源盘点器**  
  `depends_on: V0.1,V0.3`  
  将 24 个现有知识文件视为待审计候选，不视为 v4 权威；记录来源、hash、版本、disposition、许可、项目范围和 E0 隔离状态。未完成 disposition 的内容不得进入 vNext 运行包。  
  `spec_refs: LOOP §5; Knowledge Audit`

- [x] **V3.2 Atomic Claim/Decision Card Schema**  
  `depends_on: V3.1`  
  拆分 Claim，分别记录 source_quality、render_evidence、cross_scene_repeat、user_approval、applicability 和反例。  
  `spec_refs: LOOP §5.4-§5.8; Omission P1-10`

- [x] **V3.3 去重与 Conflict Graph**  
  `depends_on: V3.2`  
  检测同源重复、近义重复和互斥建议；算法暴露冲突，不替 Director 选择创意答案。  
  `spec_refs: LOOP §5.6, §5.9`

- [x] **V3.4 Scene Diagnosis 与 Knowledge Query Schema**  
  `depends_on: V3.2`  
  用注意力、空间、表演、运动、光影、切换和模型风险问题驱动检索，不用单一场景标签。  
  `spec_refs: LOOP §5.10, §9 Step 3-4`

- [x] **V3.5 最小检索与预算器**  
  `depends_on: V3.3,V3.4`  
  先做模型、模式、画幅、时效和项目硬过滤，再按问题选择最小 K2/K3/K4；无匹配不回退模板。  
  `spec_refs: LOOP §5.11, §9 Step 4`

- [x] **V3.6 Knowledge Snapshot 与可重放证据**  
  `depends_on: V3.5`  
  保存入选 Claim、冲突、未入选原因、预算和 hash；禁止声称可重现模型输出。  
  `spec_refs: LOOP §20, §22; Omission P0-13`

- [ ] **V3.7 Prompt Injection 与不可信文本隔离**  
  `depends_on: V3.5`  
  把知识、剧本、资产说明和外部反馈作为数据解析，拒绝其中伪装的系统/工具指令。  
  `spec_refs: LOOP §28.6; Omission P1-13`

退出条件：知识选择可追溯、可预算、可暴露冲突，且不存在全库默认加载和隐式模板回退。

---

## 6. Phase V4：Director 数据模型

目标：建立不被格式劳动稀释的唯一创意母版。

- [x] **V4.1 Scene Diagnosis Artifact**  
  `depends_on: V3.4`  
  定义 Director 在设计前必须回答的问题和用户视觉约束，不含镜头答案。  
  `spec_refs: LOOP §7.1, §9 Step 3`

- [x] **V4.2 Generation Segment/Shot/Beat Schema**  
  `depends_on: V1.2,V1.6,V2.2`  
  分离 Generation Segment 与内部 Cinematic Shot，绑定 Canonical Timeline、事实、可见性和 Boundary。  
  `spec_refs: LOOP §7, §8`

- [x] **V4.3 Fidelity Contract**  
  `depends_on: V4.2`  
  定义 LOCKED、ELASTIC、OPTIMIZABLE、FORBIDDEN，关键事实和用户批准项不可降级。  
  `spec_refs: LOOP §7.11`

- [x] **V4.4 Correction Impact Schema**  
  `depends_on: V2.2,V4.3`  
  定义 clarification_only、render_constraint_only、storyboard_visible_change、topology_or_fact_change 及批准失效。  
  `spec_refs: LOOP §9 Step 11-12; Omission P0-11`

- [x] **V4.5 Master Parser 与 Validator**  
  `depends_on: V4.1,V4.2,V4.3,V4.4`  
  解析并验证 vNext Master；失败关闭，不猜测自然语言；程序不得替 Director 修改镜头。  
  `spec_refs: LOOP §8, §12`

- [x] **V4.6 Schema 版本与迁移策略**  
  `depends_on: V4.5`  
  支持明确版本、兼容窗口和只读迁移；Major 变化使相关批准失效，不写回旧 Session。  
  `spec_refs: LOOP §24, §25`

退出条件：同一个 Master 足以机械派生双输出，且没有第二创意真源。

---

## 7. Phase V5：双输出与 Render Payload 编译器

目标：恢复用户成功样本格式，同时严格区分人类审计文本和模型提交载荷。

- [x] **V5.1 Storyboard Projection**  
  `depends_on: V4.5`  
  从 Master 纯复制 Panel、时间、箭头、构图、光线、保持与交接字段，不做语义改写。  
  `spec_refs: LOOP §10`

- [x] **V5.2 Storyboard 旧式格式 Renderer**  
  `depends_on: V5.1,V0.5`  
  输出已确认模板顺序和中文标签；用四组 Golden 文本做黄金测试。  
  `spec_refs: LOOP §10.1-§10.5; Gate C`

- [x] **V5.3 Video Prompt Projection**  
  `depends_on: V4.5,V2.3,V2.4,V2.5,V2.6`  
  保留参考职责、编号、阶段、完整时间线、音轨、禁止和转场；只输出一个首选执行。  
  `spec_refs: LOOP §11`

- [x] **V5.4 Video Prompt 旧式格式 Renderer**  
  `depends_on: V5.3,V0.5`  
  对齐用户提供的成功样本格式，不把 Profile 变成八套模板。  
  `spec_refs: LOOP §11.1-§11.9; Gate D`

- [x] **V5.5 Capability Profile 与 Prompt Adapter**  
  `depends_on: V2.3,V2.4`  
  Adapter 只处理标签、槽位、转义和通道路由，不改变 Director 语义；未知能力保守失败。  
  `spec_refs: LOOP §22.3; Omission P0-14`

- [x] **V5.6 Render Payload Compiler**  
  `depends_on: V5.3,V5.5`  
  从允许字段生成实际正向载荷；排除 narrative_only、audio_only、human_qa_only 和 token-leakage 内容。  
  `spec_refs: LOOP §9 Step 13, §11.7`

- [x] **V5.7 Render Payload Manifest**  
  `depends_on: V5.6,V0.3`  
  记录 included/excluded field IDs、negative route、资产槽位、能力快照、序列化版本和 hash。  
  `spec_refs: LOOP §21.4a`

- [x] **V5.8 双输出同步与 Fact/Handoff 检查**  
  `depends_on: V5.2,V5.4,V5.7`  
  验证两个视图来自同一 Master、时间/事实/交接一致，禁止逐字段自然语言相似度代替源绑定。  
  `spec_refs: LOOP §12.8-§12.9`

退出条件：四组格式黄金测试通过；VIDEO_PROMPT 与 Payload 可逐字段追溯；算法没有创意改写。

---

## 8. Phase V6：会话、批准、恢复与调用证据

目标：让完整流程在崩溃、修订和能力变化时可安全恢复。

- [x] **V6.1 vNext Session State Machine**  
  `depends_on: V4.6,V5.8`  
  实现 LOOP 状态，包括 STORYBOARD_APPROVAL_REQUIRED、RENDER_PAYLOAD_READY 和局部回退。  
  `spec_refs: LOOP §17, §21`

- [x] **V6.2 事务、staging 与原子提交**  
  `depends_on: V6.1,V0.3`  
  每个阶段写 staging、校验 Manifest 后原子更新 current/delivery；失败不暴露半提交。  
  `spec_refs: LOOP §21.1-§21.3; Audit P0-02`

- [x] **V6.3 Dependency Invalidation**  
  `depends_on: V4.4,V5.7,V6.1`  
  按事实、时间、故事板纠正、能力、资产、Adapter 和字段路由计算最小批准失效范围。  
  `spec_refs: LOOP §23-§25`

- [x] **V6.4 用户故事板批准闸门**  
  `depends_on: V4.4,V6.3`  
  保存 approved/clarification/revise、素材绑定、用户纠正和最终影响确认；未批准不能生成最终 Payload。  
  `spec_refs: LOOP §9 Step 10-13`

- [x] **V6.5 Model Invocation Snapshot**  
  `depends_on: V3.6,V5.7`  
  保存模型/产品版本、参数、完整输入 hash、输出 hash、调用 ID、重试和 replay_compile/reinvoke/regenerate 语义。  
  `spec_refs: LOOP §21.5, §22; Omission P0-13`

- [x] **V6.6 完整上下文预算与截断失败**  
  `depends_on: V3.5,V6.5`  
  分别预算事实、知识、资产、纠正、调用协议和输出；任何静默截断都阻断。  
  `spec_refs: LOOP §26; Omission P0-15`

- [x] **V6.7 并发锁、幂等与崩溃恢复**  
  `depends_on: V6.2,V6.3`  
  实现 lease、重复提交、陈旧锁、崩溃恢复和 Commit Manifest 验证。  
  `spec_refs: LOOP §21, §27; Audit P0-01/P0-04/P1-01`

- [ ] **V6.8 vNext 工程 CLI（非生产）**  
  `depends_on: V6.1,V6.2,V6.3,V6.4,V6.5,V6.6,V6.7`  
  提供 init/status/precheck/compile/approve/recover 命令；默认 `shadow_only`，不能替换 `/mode-p-pilot`。  
  `spec_refs: LOOP §27`

退出条件：批准、失效、调用证据、上下文和恢复路径全部通过故障注入测试。

---

## 9. Phase V7：DP Evidence View 与定向修订

目标：DP 只看可观察证据，不接管导演设计。

- [x] **V7.1 DP_VIEW 白名单编译器**  
  `depends_on: V5.8`  
  仅包含剧本事实、必要连续性、两个视图、使用能力和资产文字证据；排除 Master、知识、历史反馈和推理。  
  `spec_refs: LOOP §3, §12.4; Omission P1-12`

- [x] **V7.2 DP Packet Manifest**  
  `depends_on: V7.1,V0.3`  
  保存白名单字段、文件 hash、fresh context ID 和调用边界。  
  `spec_refs: LOOP §3, §21`

- [x] **V7.3 DP Response Contract**  
  `depends_on: V7.1`  
  只允许 READY、定向问题或输入阻断；每个问题绑定 Segment/Shot/Beat/Panel/Fidelity。  
  `spec_refs: LOOP §9 Step 8`

- [x] **V7.4 定向修订与受影响边界**  
  `depends_on: V6.3,V7.3`  
  只返回同一 Director 修改被引用对象和真正受影响 Boundary；新 DP 必须是新上下文。  
  `spec_refs: LOOP §9 Step 9`

- [x] **V7.5 DP 缓存与防空转**  
  `depends_on: V7.2,V7.4`  
  缓存键包含完整 DP_VIEW/能力/资产/实现版本；相同问题对未变 Master 重复出现时阻断。  
  `spec_refs: LOOP §17, §22`

- [ ] **V7.6 DP 对抗与可见性专项测试**  
  `depends_on: V7.1,V7.2,V7.3,V7.4,V7.5`  
  覆盖手机背面泄漏、遮挡角色、画外声源、反射、透视面、否定词诱导和越权重导演。  
  `spec_refs: LOOP §6, §12, §29`

退出条件：DP 证据边界、freshness、定向反馈和六类生成泄漏风险都有自动回归。

---

## 10. Phase V8：Golden、留出集、消融与外部记录

目标：用用户真实成功数据检验可预测性，而不是用旧理论自证。

- [x] **V8.1 四组 Golden Case 结构化登记**  
  `depends_on: V0.5,V5.8`  
  登记枪管、观众席、备赛区、窄巷的提示词、故事板、视频、职责和用户质量评价。  
  `spec_refs: LOOP §13; Golden Evidence Report`

- [x] **V8.2 多轴 Fidelity 评分器**  
  `depends_on: V8.1`  
  分开评价起幅、路径、切点、人物位置、可见性、落幅和允许优化；不压缩成单一相似度。  
  `spec_refs: LOOP §13.2-§13.7`

- [x] **V8.3 Golden Structural Runner**  
  `depends_on: V8.2`  
  在不调用模型的情况下验证格式、时间、切镜、职责、禁止路由和同源性。  
  `spec_refs: LOOP §13, §29`

- [x] **V8.4 Holdout Set**  
  `depends_on: V8.3`  
  建立不参与模板设计的新场景留出集，防止只复现四个成功样本。  
  `spec_refs: LOOP §13.8; Omission P1-11`

- [x] **V8.5 Knowledge/Constraint Ablation**  
  `depends_on: V3.6,V8.3`  
  对最小知识、去除单类约束和无 Golden 经验条件做消融，识别真正贡献。  
  `spec_refs: LOOP §13.8`

- [x] **V8.6 Storyboard/Render Run Record**  
  `depends_on: V5.7,V6.5,V8.1`  
  绑定实际提交文本、资产、平台参数、任务 ID、版本和输出 hash；缺记录不得晋升 validated。  
  `spec_refs: LOOP §9 Step 15, §21.7; Omission P0-12`

退出条件：校准集、留出集、消融和外部运行证据相互区分，不把历史媒体误称为可重放实验证据。

---

## 11. Phase V9：垂直集成、安全和观测

目标：形成可运行但仍不替换生产的完全隔离候选系统。

- [ ] **V9.1 无模型垂直集成 fixture**  
  `depends_on: V6.8,V7.6,V8.3`  
  覆盖 Facts→Diagnosis→Knowledge→Master→双输出→DP→批准→Payload→Delivery Manifest。  
  `spec_refs: LOOP §9, §29`

- [x] **V9.2 人工故事板暂停与恢复测试**  
  `depends_on: V6.4,V9.1`  
  验证 approved、clarification、visible change、topology change 四条路由和恢复幂等。  
  `spec_refs: LOOP §9 Step 10-13`

- [x] **V9.3 外部反馈接入测试**  
  `depends_on: V8.6,V9.1`  
  接收人工评价、FFmpeg 机械证据或独立多模态报告，但不自动修改知识。  
  `spec_refs: LOOP §9 Step 15`

- [x] **V9.4 v4 兼容与旧 Session 隔离**  
  `depends_on: V9.1`  
  以公开命令和产物做黑盒验证：证明切换前 v4 入口、685 测试和旧 Session 行为不变，同时证明 vNext 不导入 v4 模块、知识索引、缓存或 fallback。  
  `spec_refs: LOOP §15, §24`

- [ ] **V9.5 安全、授权与项目隔离回归**  
  `depends_on: V2.4,V3.7,V9.1`  
  覆盖路径逃逸、跨项目资产、未授权素材、提示注入、敏感元数据和日志泄漏。  
  `spec_refs: LOOP §28; Omission P1-13/P1-14`

- [ ] **V9.6 遥测、SLO 与错误分类**  
  `depends_on: V6.8,V9.1`  
  记录阶段耗时、预算、缓存、失败类型、批准状态和恢复结果；不记录私密推理和媒体内容。  
  `spec_refs: LOOP §26-§28; Audit P0-05/P1-05`

退出条件：隔离候选系统可恢复、可审计、可观测，且当前生产行为不变。

---

## 12. Phase V10：Shadow 与本地完成门

目标：只准备受控发布能力，不自动进入真实模型或生产。

- [x] **V10.1 vnext_shadow 入口**  
  `depends_on: V9.1,V9.2,V9.3,V9.4,V9.5,V9.6`  
  同一输入在完全隔离的 Session 中生成 vNext 对照产物；不调用 v4 生成链、不进入 v4 delivery、不共享缓存，也不影响当前批准。Shadow 只做候选结果对照，不构成双系统协同运行。  
  `spec_refs: LOOP §27.1`

- [x] **V10.2 v4/vNext 对照报告**  
  `depends_on: V10.1,V8.2`  
  比较结构、时间、切镜、可见性、知识使用和格式，不用单一文本相似度裁决质量。  
  `spec_refs: LOOP §13, §27`

- [x] **V10.3 Pilot/Canary Feature Gate**  
  `depends_on: V10.1`  
  实现默认关闭、显式场景/分集选择、隔离 Session 和批准记录；不在 Rebuild 中启用。  
  `spec_refs: LOOP §27.1-§27.3`

- [ ] **V10.4 回滚与 Kill Switch**  
  `depends_on: V10.3`  
  切换失败时可用封存包恢复 v4；正常切换后 v4 不作为第二活动入口。保留 vNext commit/证据，不把 vNext Schema 写回旧 Session。  
  `spec_refs: LOOP §27.4; Audit P1-06`

- [ ] **V10.5 操作文档与迁移说明**  
  `depends_on: V10.1,V10.2,V10.3,V10.4`  
  记录 Shadow、批准暂停、外部资产绑定、运行记录、恢复和回滚；清楚标注未获生产批准。  
  `spec_refs: LOOP §15, §27`

- [ ] **V10.6 Local Completion Audit**  
  `depends_on: all engineering tasks`  
  执行 vNext 全量、v4 完整回归、污染扫描、Schema/Manifest 版本检查和 Golden 结构验收。通过后状态只能是 `LOCAL_VNEXT_READY`。  
  `spec_refs: VNext Rebuild Loop §12`

退出条件：输出 `LOCAL_VNEXT_READY`、`PRODUCTION_ENTRY_UNCHANGED`，等待用户显式授权 Shadow 验收。

---

## 13. 非自动任务：语义与发布门

以下不由 `/mode-p-vnext-rebuild` 或 `/loop` 自动执行：

1. 四组 Golden 的新模型调用验收。
2. Holdout 真实生成。
3. 实际故事板图片批准。
4. 实际视频模型提交。
5. Shadow 质量结论。
6. Pilot、Canary 或 Production 开关。
7. 删除、归档或替换当前 v4 文件。

推进顺序固定：

~~~text
LOCAL_VNEXT_READY
  -> 用户授权 Shadow
  -> Shadow 证据审查
  -> 用户授权 Pilot
  -> Pilot 验收
  -> 用户授权 Canary
  -> Canary 与回滚演练
  -> PRODUCTION_APPROVAL_REQUIRED
  -> 用户明确批准
  -> 原子切换唯一 mode_p 与 /mode-p-pilot
  -> v4 转入只读归档包，仅用于授权回滚
~~~
