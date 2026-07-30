# MODE:P 重构实施计划

## 1. Build Loop 规则

每个任务都有唯一 ID。`IMPLEMENTATION_PLAN.md` 的复选框是实施状态真源；整个
项目是否完成，必须由当前测试、验收矩阵和活动文件共同证明。`PROGRESS.md`
记录当前任务与可复验的证据。

```text
读取 PROGRESS
  -> 选择计划中第一个 [ ] 任务
  -> 读取该任务相关规范与活动文件
  -> 标记 in_progress
  -> 实现一个最小完整变更
  -> 运行聚焦测试和必要回归
  -> 同时更新计划复选框与 PROGRESS 证据
  -> 仍有 [ ]：停止本轮
  -> 全部 [x]：下一轮进入 Completion Audit Mode
```

如果计划与进度冲突，先根据测试证据修复状态，不得重新实现已经有通过证据的任务。
全部旧阶段项目 `[x]` 不是“无工作可做”：仍须执行当前 v3.0 阶段并检查验收矩阵、全量测试、活动入口、
残留扫描、并发锁和状态文档。证据失效时，对应已完成项重新进入监督修复；证据全部
成立时只报告 `LOCAL_REBUILD_READY`。B1-B5、D4 和最终语义通过只能由用户显式
调用 `/mode-p-accept <new-run-id>` 后报告；Rebuild 不得自动启动 Director/DP。

禁止：

- 创建新的原型版本目录而不迁移活动入口。
- 一次重写全部运行文件后才测试。
- 恢复 legacy Agent、Seko、YAML Agent 协议或规则证明链。
- 用文档完成代替可执行测试。
- 在数据契约尚未冻结前实现依赖它的缓存。
- 未满足退出条件就勾选任务或阶段。

## 2. Phase 0：活动基线修复

目标：保证当前入口和重构命令真实可运行，建立可信基线。

- [x] **P0.1** 保存 EP14 S1 回归和原五项测试证据。
- [x] **P0.2** 修复 `.claude/settings.json` Hook 命令，调用项目内 `kb-guard.py`。
- [x] **P0.3** 扩展 Guard 到 `STORYBOARD.md`、`VIDEO_PROMPT.md` 和 Edit `new_string`，同时允许内部 Master。
- [x] **P0.4** 修复真实 `working/` 路径提交的同文件复制异常；增加缺失 Shot、非法时长、越界时间节点和真实入口测试。
- [x] **P0.5** 删除 `decision_patterns` 的通用面对面对话回退。

退出条件：活动测试全部通过；真实 Claude 命令使用的提交路径可交付；Hook 可执行；计划与进度状态一致。

## 3. Phase 1：数据契约与单场垂直切片

目标：先建立机器可验证但不污染最终提示词的内部数据契约。

- [x] **P1.1** 定义剧本输入契约：支持格式、场景标题规则、编码、原文行号和无法确定时的处理方式。
- [x] **P1.2** 定义 `DIRECTOR_MASTER.md` 模板，包含独立 `story_fact`、源文定位、Shot ID、时长、时间轴、边界和参考资产 ID。
- [x] **P1.3** 定义内部 `SHOT_MANIFEST.json` 与版本字段；它是 Master 的机械投影，不是第二设计源，也不进入交付。
- [x] **P1.4** 实现 Master 解析器和 Manifest 编译器；无法解析时失败关闭，不猜测自然语言语义。
- [x] **P1.5** 实现 Storyboard/Video 派生契约，规范化字段由本地模板复制，创作文本由 Director 提供。
- [x] **P1.6** 实现 `master_sync_check.py`，只检查 ID、版本、哈希、时长、字段存在和规范值；语义质量留给 DP。
- [x] **P1.7** 实现 `boundary_check.py`，检查边界 ID、人物/道具状态键、动作阶段、银幕方向和相邻配对。
- [x] **P1.8** 实现增强版 `reference_plan_check.py`，检查模式、asset_id、文件存在、职责和能力配置，不判断审美选择。
- [x] **P1.9** 将结构预检移动到 DP 之前，并在 DP READY 后执行最终哈希/交付校验。
- [x] **P1.10** 建立单场垂直集成测试：Master -> Manifest -> 两个视图 -> 预检 -> DP状态 -> 两文件交付。

退出条件：修改任一规范字段必然导致结构检查失败；改写创作措辞但保持规范字段时不会被错误判定为语义冲突；单场真实入口测试通过。

## 4. Phase 2：当前分集与导演批次

目标：当前独立分集默认一次处理，并保持事实追溯与跨场导演统一。

- [x] **P2.1** 实现场景边界解析器，只确定分场和原文范围，不自行解释剧情。
- [x] **P2.2** 由同一 Director 批次提取 `SCRIPT_FACTS.md`，每项事实携带原文位置；本地程序验证引用范围存在。
- [x] **P2.3** 生成 `EPISODE_VISUAL_BIBLE.md` 和 `EPISODE_CONTINUITY_LEDGER.md`。
- [x] **P2.4** 定义小型全片批次和长剧本多批次两种上下文策略，禁止声称持久会话可以卸载旧上下文。
- [x] **P2.5** `/mode-p-pilot` 默认处理当前分集全部场景；生产入口不暴露范围参数，局部重算由内部失效器决定。
- [x] **P2.6** 实现场间边界和 Ledger 更新，后批次读取前批次已提交状态。
- [x] **P2.7** 实现全片回看闭环：修订后必须重新进入 Episode Review，直到通过或明确阻断。
- [x] **P2.8** 建立多场剧本回归：顺序、事实、服装、伤势、道具、时间和场间转场。

退出条件：多场剧本一次调用完成；每项剧情事实可追溯；全片修订后重新回看；局部运行不会破坏跨场连续性。

## 5. Phase 3：知识、能力与参考资产

目标：在缓存实现之前建立稳定可索引的数据来源。

- [x] **P3.1** 重组 `knowledge/core` 与 `knowledge/capsules`，新增 Editing/Transition、多人、调查、蒙太奇、多空间和全能参考知识。
- [x] **P3.2** 生成版本化 `knowledge_index.json`，记录适用条件、文件哈希和经验状态。
- [x] **P3.3** 实现 `context_retriever`，校验 Director 显式选择的 0-3 胶囊并筛选 0-3 validated 经验；无选择/匹配时只用 Core，不回退历史 Pattern。
- [x] **P3.4** 建立版本化 `SD2_CAPABILITY_PROFILE.json`，记录首尾帧、全能参考、素材类型、互斥关系和当前画布限制。
- [x] **P3.5** 建立 `ASSET_INDEX.json`，使用稳定 asset_id、路径、媒体类型、内容哈希、可用状态和可承担职责。
- [x] **P3.6** 改造历史 Pattern 为条件化案例，补充 applicability、non_applicability、evidence、invariants 和 variables。
- [x] **P3.7** 建立知识与参考选择测试：对话、动作、悬疑、多人、多空间、无匹配、首尾帧、全能参考和冲突素材。

退出条件：最终提示词无规则 ID；无匹配不加载历史 Pattern；能力或素材变化可被索引发现；参考计划可以解析到实际素材。

## 6. Phase 4：批次状态机、缓存与 Claude Code Loop

目标：用户只发一条命令；本地算法负责状态、缓存和恢复，LLM 只负责导演与 DP 工作。

- [x] **P4.1** 实现批次状态机：BOOTSTRAP -> SCRIPT_PARSE -> DIRECTOR_BATCH -> STRUCTURAL_PRECHECK -> DP_BATCH -> FINAL_CHECK -> BATCH_COMMIT -> EPISODE_REVIEW -> DELIVERY。
- [x] **P4.2** 实现会话锁、staging 目录、提交清单和两阶段提交；崩溃时不暴露半写入 delivery。
- [x] **P4.3** 实现 `bootstrap_loader`，加载版本指纹和索引元数据，不加载全量知识正文或媒体内容。
- [x] **P4.4** 实现包含全部真实输入与实现版本的缓存键，包括能力配置、资产内容哈希和 DP 实际上下文。
- [x] **P4.5** 实现 `dependency_invalidator`，按剧本、知识、能力、素材、Master、视图、DP和检查器变化计算最小失效范围。
- [x] **P4.6** 实现 `batch_scheduler`，按检测到的上下文/输出预算拆批，不调用复杂度 Agent。
- [x] **P4.7** 小型先导篇使用一个 Director 批次和一个全新 DP 批次；长剧本批次共享 Visual Bible 与已提交 Ledger。
- [x] **P4.8** 定义 DP 自然语言问题契约：稳定 Shot ID、问题字段和简短说明；据此计算防空转指纹。
- [x] **P4.9** 重写 `/mode-p-pilot`、Director、DP 和根 `CLAUDE.md`，执行完整 L0-L6。
- [x] **P4.10** 增加调用次数、输入/输出量、本地耗时、缓存命中和失效范围遥测。
- [x] **P4.11** 建立冷启动、热恢复、缓存损坏、并发启动、子 Agent 中断和实现版本升级测试。
- [x] **P4.12** 基准测试 Director/DP 模型分配；Director 优先质量，DP 仅在固定回归无下降时切换更快模型。

退出条件：3-5 场无修订先导篇在预算允许时为一次 Director + 一次新 DP；缓存命中不调用模型；并发和崩溃不会损坏状态；用户无需运行脚本或转发反馈。

## 7. Phase 5：真实渲染反馈学习（MODE:P 不负责渲染）

- [x] **P5.1** 建立 `05_项目经验` 的 candidates、repeated、validated、rejected 和 render_cases 目录。
- [x] **P5.2** 新增非运行时 Knowledge Curator 与 `/mode-p-learn`；只整理外部真实渲染证据，不调用渲染。
- [x] **P5.3** 实现真实渲染证据、用户观察和 Master/素材版本关联。
- [x] **P5.4** 实现状态晋升、回归测试和 `/mode-p-promote` 人工批准流程。

退出条件：无真实渲染证据不能创建有效经验；单次观察不能进入 validated；知识更新可回退且回归通过。

## 8. Phase 6：迁移与收口

- [x] **P6.1** 更新 dispatcher、README、CLAUDE.md、活动 Agent 和迁移映射。
- [x] **P6.2** 实现并运行 `legacy_residue_check`，扫描活动入口中的旧 Agent、Seko、TIME_SKELETON、Gate 和 YAML 协议引用。
- [x] **P6.3** 运行全部单元、集成、真实命令和剧本回归测试。
- [x] **P6.4** 将新 Loop 切换为唯一活动入口，更新实现状态并保留只读归档。

退出条件：活动路径只有新 Loop；所有强制验收通过；文档状态与实际运行能力一致。

## 9. Phase 7：v3.0 注意力收敛与独立分集

目标：删除不参与导演设计的模型上下文，支持可选项目背景、无图片运行和真正情境化双视图。

- [x] **P7.1** 实现自然语言登记项目背景、自动绑定、独立分集版本和无项目 standalone。
- [x] **P7.2** 重写 Loop、Pilot、Director/DP 契约；Director 使用精简运行契约，当前分集冲突优先。
- [x] **P7.3** 实现八类场景 Profile 与三类时间模式；Storyboard/Video 从同一 Master 改变字段关注顺序。
- [x] **P7.4** 将 DP 模型可见 Packet 限定为干净剧本证据、连续性、双视图、实际能力和实际资产卡。
- [x] **P7.5** 实现无多模态文字资产卡、媒体哈希绑定、stale 失效、职责限制和 Director/DP 预算。
- [x] **P7.6** 统一根文档、dispatcher、运行 README、Claude Code Runbook、验收矩阵与活动入口测试。
- [x] **P7.7** 运行活动入口、残留扫描和本地全量回归，记录当前证据。

退出条件：用户只需 `/mode-p-pilot <当前分集剧本>`；无项目、无资产正常；DP 不看到
Master/Manifest/知识/源码/哈希；八类 Profile 与三种生成模式有可执行测试；全量回归与
残留扫描通过。实模导演质量仍由用户显式 `/mode-p-accept` 验收。

## 10. Phase 8：v4.0 视觉真源与有效审查

目标：消除 Master 内最后的双时间源和双份边界，让同一 Director 贯穿整集，并用
全文预检与可观察 DP 证据阻止不可执行提示词。

- [x] **P8.1** 每镜收口为一条视觉时间线；Video 投影全部节点，Storyboard 只投影 `[SB]` 节点。
- [x] **P8.2** 建立 N+1 共享 Boundary，区分 continuous/elliptical，去除每镜重复的进入/交出设计。
- [x] **P8.3** 最终提示词预检扩展至全文、时间尾节点、占位符、否定、条件/备选分支、不可见语言和 `[SB]` 泄漏。
- [x] **P8.4** DP 通过需要每场引用当前 Shot 的具体证据；实现 `DP_INPUT_BLOCKED` 和验收专用五类对抗检查。
- [x] **P8.5** 分集绑定唯一 Director Agent ID/实际模型，批次、修订和 Episode Review 只恢复同一 Director。
- [x] **P8.6** 运行聚焦测试、全量回归、活动入口检查和 legacy residue 扫描，固化当前 v4.0 证据。
- [ ] **P8.7** 在 Claude Code 中用当前 DeepSeek V4 Pro 执行新 run 实模验收，包括对抗 DP Gate。
- [ ] **P8.8** 在外部即梦画布分别完成 text-only、首尾帧、全能参考真实生成对比；需用户账号/素材，MODE:P 不自行渲染。

知识源、Core/Capsules、知识选择、覆盖矩阵、蒸馏与经验晋升在本 Phase 全部
暂停，不得为了完成 P8 而修改。

退出条件：P8.1-P8.7 通过才能声称当前契约的实模导演能力已验收；P8.8 通过前不得声称真实渲染质量已证明。

## 11. PROGRESS.md 状态格式

```markdown
# MODE:P Rebuild Progress

当前阶段：Phase N
当前任务：PN.M 任务名称
状态：pending | in_progress | passed | blocked

## 已完成
- PN.M：变更文件、测试命令、结果和验收编号

## 当前问题
- 可复现问题和下一动作

## 不得回归
- 已验证不变量
```

计划复选框与进度状态必须在同一提交步骤更新。不得记录模型隐藏推理。
