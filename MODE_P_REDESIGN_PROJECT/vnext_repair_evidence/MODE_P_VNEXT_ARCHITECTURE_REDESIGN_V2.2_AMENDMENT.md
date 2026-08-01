# MODE:P vNext 架构重构 v2.2 修订案

> 状态：NORMATIVE AMENDMENT
>
> 基线：`MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.0.md`
>
> 前序修订：`MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V2.1_AMENDMENT.md`
>
> 触发证据：`A8_ARCHITECTURE_BLOCKER_001.json`
>
> 生产边界：本修订不授权生产切换；v4 继续保持唯一生产入口。

## 1. 修订目的

v2.1 首次真实 A8 Shadow 审查证明两个问题无法由 A8 局部补丁解决：

1. 任意剧本文本只被登记为无语义的行事实，而 A5 又从 `fact_id` 字符串前缀猜测人物、服装、道具、场景和对白，导致 VEC 引用与音频职责无法可靠生成；
2. A6 在服务层和适配层重新定义了 A1 已冻结的 `ProjectionAST`、`ProjectionManifest`、`ProjectionNode` 与 `CapabilityAdaptationRecord`，导致持久化 Artifact 无法满足唯一类型权威。

本修订冻结两项根因合同，并加强 A8 的端到端、恢复与验收边界。本文只修订与下列条款直接相关的内容；v2.0 与 v2.1 的其他条款继续有效。冲突时按 v2.2 执行。

## 2. ADR-021：脚本摄取采用“可溯源抽取草稿 + 本地事实装配”

### 2.1 权威输入与阶段边界

用户上传的当前集剧本始终是叙事权威。`INGEST` 不得把剧本改写成新的叙事，也不得从文件名、Golden、历史产物或模型记忆补充事实。

任意 UTF-8 剧本文本进入以下固定流程：

```text
raw script bytes
  -> normalized source document
  -> I0 FactExtractionDraft（结构化文本模型，可失败）
  -> FactAssembler（本地、确定性、可验证）
  -> ArtifactEnvelope[FactRegistry]
```

`I0` 是 INGEST 内部的声明式 Signature，不是新的持久状态节点。它必须通过 A4 的同一结构化生成端口、预算、Schema 分通道和一次受控纠错机制运行。

### 2.2 规范化源文档

本地摄取器必须：

- 以 UTF-8 严格解码；允许 UTF-8 BOM，但摘要前移除 BOM；
- 将 CRLF 和裸 CR 规范化为 LF；
- 保留规范化文本、逐行序号、字符起止偏移和源文件 SHA-256；
- 使用完整 256-bit 摘要参与默认 `run_id`，不得只以截断摘要作为唯一身份；
- 对空文件、无法解码、路径逃逸、符号链接和摘要冲突 fail-closed。

### 2.3 `FactExtractionDraft`

I0 只能返回创意之外的事实抽取草稿：

```text
facts[]
  source_start
  source_end
  semantic_type:
    narrative | character | wardrobe | prop | setting | dialogue | continuity | asset
  statement
  subject_id?        # 规范实体键；对白时为说话人
  spoken_text?       # 仅 dialogue 必填
  scene_hint?
```

禁止 I0 输出：

- `fact_id`、Artifact ID、摘要或验证状态；
- 未被 `[source_start, source_end)` 原文支持的事实；
- 摄影机、构图、运镜、表演或剪辑决策；
- 引用编号、音色文件、VEC、Projection 或交付提示词；
- Golden、Holdout、旧输出或历史任务内容。

### 2.4 规范 `ScriptFact`

A1 必须把事实来源可信度与事实语义分离。规范领域模型至少包含：

```text
FactKind           # script | continuity | asset | user_approved，表示来源/权威
FactSemantic       # narrative | character | wardrobe | prop | setting | dialogue | continuity | asset

ScriptFact
  fact_id          # 本地稳定生成；语义不编码在 ID 中
  scene_id
  kind: FactKind
  semantic: FactSemantic
  statement
  source_ref
  source_start
  source_end
  ordinal
  subject_id?
  spoken_text?
```

不变量：

- `fact_id` 是不透明身份，消费者不得解析前缀获得语义；
- `source_start/source_end` 必须指向规范化源文档中的精确非空跨度；
- `statement` 必须能由该跨度直接支持；本地装配器拒绝无原文支持的新增事实；
- `dialogue` 必须同时具有非空 `subject_id` 与 `spoken_text`，且 `spoken_text` 必须出现在源跨度内；
- `character/wardrobe/prop/setting/asset` 必须具有非空 `subject_id`；
- ordinal 在同一源文档内严格递增且唯一；
- `FactRegistry` 必须至少包含一个事实，但并非每个剧本都必须包含对白或所有引用类型。

旧 `ScriptFact` 只能经显式兼容读取器导入；兼容读取器不得通过 ID 前缀猜测新语义，缺少语义时标记为 `narrative`，需要引用或对白的运行必须重新 INGEST。

### 2.5 A5 消费合同

`VECAssembler` 必须：

- 只从 `ScriptFact.semantic` 推导引用与 AudioEvent；
- 从 `character/wardrobe/prop/setting/asset` 事实生成 ReferenceRequirement；
- 从 `dialogue` 的 `subject_id + spoken_text` 生成 AudioEvent 与 VoiceRequirement；
- 不解析 `fact_id`、`statement` 或自然语言意图来猜测类别；
- 保留每个 Requirement/AudioEvent 到源 Fact 的可追踪映射；
- 当画面设计引用了没有对应事实的实体，或对白设计无法绑定唯一对白事实时 fail-closed；
- 无对白场景允许没有 AudioEvent；纯环境或抽象场景仍必须由显式 setting/asset 事实满足所需引用。

## 3. ADR-022：规范领域类型具有进程内唯一身份

### 3.1 唯一投影权威

以下持久化类型只能在 `mode_p_vnext.domain.projection` 定义：

- `ProjectionNode`
- `ProjectionAST`
- `ProjectionManifest`
- `CapabilityAdaptationRecord`

服务层、pipeline、port 和 adapter：

- 必须直接导入并构造上述规范类型；
- 不得重新定义同名或语义等价的持久化 dataclass；
- 不得先生成私有 AST 再以未记录转换伪装成规范 AST；
- 可以定义纯交付 DTO，但其名称、字段和用途必须明确为非 Artifact，且只能由规范 ProjectionAST 派生。

`ArtifactEnvelope(artifact_kind=PROJECTION_AST)` 的 payload 必须满足：

```text
type(payload) is mode_p_vnext.domain.projection.ProjectionAST
```

`CAPABILITY_ADAPTATION` 与 `PROJECTION_MANIFEST` 同样执行精确类型身份检查。

### 3.2 A6 验收补强

A6 完成 Evidence 必须证明：

1. 非 domain 模块不存在上述四个重复类定义；
2. 编译器返回规范 `ProjectionAST`；
3. AST 可进入规范 ArtifactEnvelope 并完成 canonical round-trip；
4. Storyboard 和 Video 从同一个 AST 实例/摘要派生；
5. Storyboard 只选择规定 VisualBeat，Video 使用全部节点；
6. capability 降级只产生规范 `CapabilityAdaptationRecord`，且不发明事件；
7. A5、A7 与 v4 隔离回归通过。

### 3.3 A7 消费边界

Gate 0、ReviewPacket、DP、Revision、Media 与 Visual Verification 必须消费 A1/A6 的规范领域类型。A7 不得定义 A1 已拥有的 Evidence 或 Revision 类型，也不得接受服务层影子 AST。

## 4. ADR-023：A8 必须是单入口、单会话、完整状态图

A8 顶层 CLI 的一次真实 Text Shadow 必须执行并持久化：

```text
INGEST(I0 + FactAssembler)
  -> E0 -> S1 -> K1 -> B0 -> ASSEMBLE_B0
  -> K2 -> B1 -> ASSEMBLE_VEC
  -> GATE0 -> independent DP -> PROJECT
```

要求：

- 顶层 CLI 是唯一运行入口；不得继续调用只写结构清单的旧 Shadow 作为 A8 成功路径；
- 每个模型阶段使用 A4 冻结的 `stage_signatures()`，不得在 A8 重建 Signature；
- K1 与 K2 必须调用 A3 唯一检索实现，K2 绑定已验收 BlockingCommit；
- 所有持久输出使用 A1 ArtifactEnvelope、A2 RunSession/NodeRunner/ArtifactStore/Checkpoint/Atomic Commit；
- 恢复时只重跑输入摘要、节点版本或依赖摘要不匹配的节点；已接受且依赖不变的模型节点不得再次调用；
- `RUN.json` 与 run record 的自摘要读取时必须验证；损坏、截断、碰撞和双写一律 fail-closed；
- 默认 run identity 使用完整规范化源摘要；展示可缩写，但目录冲突检查必须比较完整摘要；
- Golden/Holdout 只能进入 A9 离线评估，不能作为 A8 VEC 或 Draft 输入；
- Text Shadow 的最高声明为 `TEXT_VALIDATED`，不得声明视觉通过、用户批准或生产可用；
- v4 缓存、v4 生成链和 v4 delivery 不得被读取、写入或调用。

## 5. ADR-024：受影响任务与注册验证

本修订改变规范领域事实、I0 Signature、VEC 消费、Projection 编译、Gate/DP 消费和 A8 运行路径，因此 A0–A8 的旧完成记录全部失效，必须依次重验。

任务表必须至少加入以下硬检查：

- A0：锁定完整 v2.0 + v2.1 + v2.2 权威包；任务路径仍两两不重叠；
- A1：typed fact semantics、opaque fact IDs、source-span invariants、canonical type uniqueness；
- A4：I0 Signature、schema budget、source-span repair ceiling；
- A5：typed reference binding、typed dialogue/audio binding、no fact-id semantics；
- A6：canonical type identity、ArtifactEnvelope round-trip、no duplicate projection authority；
- A7：canonical projection/evidence consumption，并注册 v4 隔离回归；
- A8：完整状态图、真实未知剧本、断点恢复不重复调用、记录摘要篡改拒绝、无 Golden 注入、TEXT_VALIDATED 上限、v4 隔离。

每个任务的 Evidence 只能由 ReleaseLedger 注册命令的真实执行结果授予。手写 `exit_code: 0`、仅导入测试、占位测试或结构扫描都不能代替行为验收。

## 6. 架构重基与生产不变量

按 v2.1 架构变更协议：

1. A8 先失败关闭并绑定根因 Evidence；
2. 既有 A7→A0 按依赖逆序受控失效；
3. 更新任务表以锁定三个权威文件及其规范化 SHA-256；
4. 在无锁、无已完成 A 任务时调用 `release_control rebase-architecture --version 2.2`；
5. 从 A0 重新施工，每轮只领取 `next` 返回的唯一任务；
6. 在 A10 的媒体证据与用户批准之前，`production_entry=v4_unchanged`、`production_switch_authorized=false`。

本修订不授予模型替用户记录媒体验收或 owner approval 的权限。
