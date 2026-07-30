# MODE:P v4.0 - 精简导演循环规范

> 本文件是 MODE:P 正式创作运行的唯一权威。目标不是生成审计材料，而是让一个
> Director 在最小、可信的上下文中完成统一视觉设计，并从同一 Master 派生故事板和
> 即梦 SD2.0 视频提示词。

> 本轮知识架构冻结。不修改原始资料、Core/Capsules、知识选择、覆盖矩阵、
> 蒸馏或经验晋升；冻结边界见 `KNOWLEDGE_ARCHITECTURE_FROZEN_NOTE.md`。

## 1. 用户体验

### 1.1 唯一创作入口

```text
/mode-p-pilot <当前分集剧本路径>
```

用户不填写项目名、集号、场景范围、Agent 名、模型名或本地脚本参数。

- 分集 ID 优先读取剧本标题，其次使用文件名。
- 同一分集内容变化时，以内容哈希建立新版本。
- 当前工作区只有一个活动项目时自动绑定。
- 没有活动项目时按独立分集运行。
- 只有多个项目同时可用且无法确定归属时才询问用户。

### 1.2 完整剧本作为项目背景

用户用自然语言说明“将这个完整剧本设为 MODE:P 项目背景”时，Claude Code 自动运行
本地登记程序。用户不需要执行另一个斜杠命令。

登记只做文件哈希、结构索引和持久化，不调用模型。完整剧本与后续分集不要求存在
包含关系；后续分集可以是改写、扩写或新版本。

## 2. 真源优先级

每次分集设计按以下顺序裁决：

1. 当前上传的分集剧本：本集唯一叙事真源。
2. 已提交分集形成的连续性事实。
3. 完整剧本中与当前分集不冲突的世界、人物和长期弧线背景。
4. 项目视觉圣经中的稳定导演设定。
5. 当前核心知识、相关场景胶囊和已验证经验。
6. Director 为完成拍摄补充的视觉选择。

冲突时当前分集优先。Director 不得把完整剧本中的旧事件重新写回分集。影响未来分集
的变化记录到项目连续性账本；不静默改写完整剧本。

所有视觉信息必须标明其性质：

- `script_fact`：剧本明确事实。
- `project_fact`：已提交的项目事实。
- `director_choice`：Director 补充的稳定设计。
- `unknown`：当前证据无法确定，不得伪装成图片事实。

## 3. 架构边界

### 3.1 两个模型角色

- **Director**：唯一创作角色，统一决定镜头、运镜、构图、光影、表演、声音、切换和
  SD2.0 生成模式。
- **DP**：每轮全新、只读、独立审查；只指出可观察问题，不重新设计。

当前 Claude Code 任务只负责调度。本地程序只负责解析、选择、哈希、编译、派生、
结构检查、缓存、恢复和原子提交。不得增加摄影、运镜、构图、光影、剪辑、资产选择、
验证或包装模型角色。

### 3.2 模型继承

正式创作继承用户在 Claude Code 中选择的模型并记录 Agent 工具实际
`resolvedModel`。生产运行没有模型名称白名单。只有显式 `/mode-p-accept` 固定验收
强制其协议指定的模型。

### 3.3 唯一设计源

```text
DIRECTOR_MASTER.md
    -> SHOT_MANIFEST.json   机器投影，不拥有设计权
    -> STORYBOARD.md        情境化故事板视图
    -> VIDEO_PROMPT.md      情境化 SD2.0 视频视图
```

Director 只修改 Master。派生器不得增加镜头、改写导演意图或分别创作两个视图。

### 3.4 推理模型执行纪律

正式 Pilot 继承 Claude Code 父任务选择的模型，包括用户选择的 DeepSeek V4 Pro。
Director 使用 `effort: max`、DP 使用 `effort: high` 作为宿主提示，但流程不依赖供应商
是否实现该字段。任务包必须给出当前阶段、输入白名单、授权输出和完成条件；不得额外
要求输出思维链，也不得用整仓库、整份 Loop 或工程日志来换取所谓“更深思考”。

Director 在内部按“事实与戏剧变化 -> 空间调度 -> Profile/生成模式 -> Shot 跨域设计 ->
连续性自检”完成后直接写 Master。DP 只按当前证据审双视图。模型能力用于导演判断，
机械一致性继续由本地程序承担。

## 4. 项目记忆

工作区最多有一个默认活动项目。活动项目保存：

```text
MODE_P_PROJECT.json
PROJECT_SOURCE_INDEX.json
PROJECT_VISUAL_BIBLE.md
PROJECT_CONTINUITY_LEDGER.md
ASSET_REQUIREMENTS.md
```

- `MODE_P_PROJECT.json`：项目 ID、完整剧本路径/哈希、项目目录和状态。
- `PROJECT_SOURCE_INDEX.json`：确定性结构索引，不做语义创作。
- `PROJECT_VISUAL_BIBLE.md`：Director 的稳定视觉设定。
- `PROJECT_CONTINUITY_LEDGER.md`：已提交分集的实际连续性。
- `ASSET_REQUIREMENTS.md`：尚未生成或尚未绑定的资产槽位。

每个分集独立保存当前剧本哈希、版本、事实、Master、派生视图和运行状态。项目背景
改变不会静默重写旧分集；依赖失效器只标记受影响版本。

## 5. 无资产优先运行

没有传入图片或文本资产卡是正常状态，不得阻断 MODE:P。

Director 此时依据当前分集剧本、非冲突项目背景、视觉圣经和知识库设计：

```text
生成模式：text_only
参考资产：无
```

剧本未描述的必要外观或空间可以成为 `director_choice` 并写入视觉圣经。Director 同时
可声明未来资产槽位、用途和目标，但不能声称已经看见不存在的图片。

## 6. 无多模态文本资产卡

MODE:P 运行时不调用视觉模型，Director 与 DP 不读取图片、视频或音频二进制。真实
媒体仍可在最终生成阶段由即梦 SD2.0 通过 `asset_id` 使用。

每份可供模型理解的媒体必须绑定一张文字资产卡：

```text
asset_id
媒体内容 SHA-256
资产卡 SHA-256
状态：verified | stale | unverified
来源：用户描述 | 既有详细解析 | 生成规格并经用户确认
摘要
可确认视觉事实
空间/人物/光影/摄影事实
不确定区域
允许职责
```

规则：

- 只有 `verified` 卡可作为视觉事实。
- 媒体哈希变化时卡片自动 `stale`。
- 历史 IMAGE_AUDIT 只有在确认对应原媒体后才能晋升为 `verified`。
- 没有卡的媒体可以保存，但 Director 不得选择它承担视觉职责。
- 资产卡属于项目视觉事实，不进入导演知识库。

### 6.1 成本预算

- 不新增模型调用或视觉调用。
- Director 资产上下文默认不超过 6,000 tokens/批次，硬上限 10,000。
- DP 资产证据默认不超过 2,000 tokens/轮。
- 同一资产在一个持续 Director 中只加载一次。
- 按实际职责裁剪卡片章节；不把所有卡片发给模型。

## 7. Director 最小上下文

调度器为整个分集只启动一个持续 `mode-p-director`。所有批次、修订和 Episode Review
必须恢复同一 Agent ID 和实际模型；`director_session.py` 负责确定性绑定。无法恢复时
阻断，不得新建替代 Director 或由调度器接管创作。
Director 只读取：

1. 当前分集的精确剧本文本和行号。
2. 不冲突的项目背景摘要和连续性快照。
3. 当前 Visual Bible。
4. 四份 Core。
5. 胶囊候选文件名，以及 Director 从中选择的每批 0-3 份胶囊正文。程序只校验路径、
   数量和版本，不按关键词替 Director 判定场景类型或创作方向。
6. 每场 0-3 条 validated 经验。
7. 当前 SD2.0 能力摘要。
8. 实际相关的 verified 文本资产卡章节。
9. 精简 Master 创作契约和明确输出路径。

Director 不读取：

- LOOP_SPEC 全文、测试、运行时代码或哈希表。
- BATCH_MANIFEST、SCENE_SESSIONS、缓存记录和遥测。
- 旧 Agent 输出、旧审计、历史 PLAN、TIME_SKELETON 或 Seko 资料。
- 未选知识、未选资产卡或 DP 历史推理。

## 8. Master 创作内容

每场 Master 只保留创作和连续性真正需要的信息：

### 场景层

- 戏剧变化、信息策略和场景后状态。
- 空间调度、关系线和人物路径。
- 视觉、光影、稳定性和节奏曲线。
- 镜头拆分和全场转场策略。
- 可直接进入双视图的场景蓝图和声音基调。

### 逐镜层

- Shot ID、时长和剧本事实定位。
- 场景表达 Profile 与时间控制模式。
- 摄影、构图、光影和表演设计。
- 一条统一视觉时间线；首尾和需画出的关键状态标记 `[SB]`。
- 生成模式、参考职责和资产槽位。
- 声音设计。

### 共享 Boundary

N 个 Shot 只有 B0...BN 共 N+1 个 Boundary，并按
`B0 -> Shot1 -> B1 -> ... -> ShotN -> BN` 排列。B0 是场景入口，BN 是场景出口。
每个内部 Boundary 只拥有一份剪辑触发、交接描述和转场执行位置。

- `continuous`：交出状态与接入状态完全相同，接入用 `<same>`。
- `elliptical`：显式写出省略前后两份状态，DP 审查跳变动机。
- 不再为每镜重复写开场/结束及进入/交出文案。

每镜仍为独立生成单元，Boundary 只确保可见的镜间衔接。

### 同源派生

- Video Prompt 机械复制视觉时间线的全部节点。
- Storyboard 机械复制同一时间线中 Director 标记的 `[SB]` 节点。

ID 链接、哈希、版本时间、可推导边界 ID 和摘要表由本地程序生成；不得要求 Director
重复填写已能机械得到的技术字段。
最终双视图不得暴露哈希、边界 ID、Profile、时间模式或 `[SB]`，也不得由程序
合成画面、动作、光影、声音或转场文案。脚本只复制 Director 源文本、组织字段和
标注 Shot/时长/生成模式/参考职责。

## 9. 情境 Profile

Master 使用一个核心 Shot Contract，加一个轻量 Profile。Profile 只改变关注重点、
字段排序和时间密度，不复制八份完整模板。

| Profile | 故事板关注 | 视频关注 | 默认时间建议 |
|---|---|---|---|
| conversation_power | 关系线、景别、视线、反应帧 | 停顿、视线和权力变化切点 | event/second |
| crowd_attention | 注意力层级、群体调度 | 主要注意力转移和遮挡 | second |
| action_chase | 起势、运动方向、撞击、恢复 | 连续轨迹、速度和动作阶段 | half-second |
| suspense_reveal | 遮挡、信息缺口、揭示帧 | 揭示时点前后的密度变化 | event/second |
| contemplative_silence | 构图、微表演、环境变化 | 稀疏但有意义的变化 | event |
| investigation_object | 物体尺度、视线链、信息层级 | 接近、发现和反应节点 | event/second |
| montage | 图形/动作/声音匹配 | 短节拍和剪辑锚点 | event |
| cross_space_transition | 两端空间和交接元素 | 声音桥、匹配元素和切换状态 | event/second |

建议不是硬绑定。Director 可根据当前镜头选择更精细或更稀疏的时间模式，但必须说明
真实可见变化，不能为了填格制造动作。

## 10. 故事板视图

每个 Shot 独立且 `0 < duration <= 15s`。故事板是统一视觉时间线的稀疏投影：

- 对话/沉思通常使用 2-3 个关键状态。
- 悬疑/调查覆盖信息隐藏、发现和结果。
- 动作覆盖起势、关键路径、峰值和恢复，通常 3-5 个状态。
- 蒙太奇按真正视觉节拍呈现。
- 多空间必须显示两端空间的交接依据。

视图根据 Profile 调整字段顺序和标题。例如动作镜显示 `Action Beats`，对话镜优先显示
构图与表演，悬疑镜显示 `Reveal Focus`。不相关模块不输出空字段。
`[SB]` 只是 Master 内部派生标记，不出现在最终故事板。

## 11. 视频提示词视图

每个 Shot 是可独立提交给 SD2.0 的完整段落，不能写“承接上一镜”。必须包含绝对
开场、可见过程和绝对结束。
所有可见节点均来自 Master 的同一条视觉时间线；派生器只去掉 `[SB]` 内部标记，
不改写画面。

时间模式：

- `event_nodes`：只在真实变化点写节点。
- `second_nodes`：相邻节点不超过 1 秒。
- `half_second_nodes`：相邻节点不超过 0.5 秒。

生成模式 Profile：

- `text_only`：完整写出本镜需要的可见事实。
- `first_last_frame`：明确首帧职责、尾帧职责和中间变化路径。
- `omni_reference`：只继承资产卡声明的职责，同时明确本镜允许变化的内容。

硬切、叠化和声音桥标记为后期；遮挡过镜、甩镜等真实镜内事件才标记镜内完成。

## 12. 确定性预检

Director 完成 Master 后，本地程序执行：

1. 编译 Manifest。
2. 从同一 Master 派生两个 Profile 视图。
3. 检查剧本定位、ID、时长、单一时间线、`[SB]`、N+1 共享 Boundary、引用、
   能力兼容和禁止残留。
4. 扫描最终可执行提示词全文：未解析占位符、否定指令、未裁决备选/条件分支、
   不可见心理/文学语言、时间越界、缺少尾节点和泄漏的 `[SB]`。
5. 对 working 树做原子提交。

结构失败回同一 Director；纯机械错误由本地程序修复。预检不判断审美质量。

## 13. Fresh DP 最小审查

每轮启动一个全新 `mode-p-dp`。DP 模型可见内容只包括：

1. 当前分集的相关剧本摘录。
2. 当前项目连续性摘要。
3. `STORYBOARD.md`。
4. `VIDEO_PROMPT.md`。
5. 本批实际使用的 SD2.0 能力摘要。
6. 本批实际使用的 verified 资产卡摘要。

DP 不读取 Master、Manifest、知识库、Agent 定义、解析器源码、哈希实现、缓存、遥测或
以前的 DP 反馈。这些文件可以参与本地 provenance 哈希，但不得出现在模型可见 Packet。

DP 只输出下列三种互斥结果之一。通过时必须每场一行、引用当前 Shot 并给出
一条可观察理由：

```text
READY <scene_id>: <Shot ID 与具体观察证据>
```

发现问题时：

```text
<ShotID>: <field> - <短而具体的问题>
```

必需当前输入缺失时：

```text
DP_INPUT_BLOCKED: <缺少的具体输入>
```

问题只回传引用 Shot 和必要相邻边界给同一 Director。重新派生、预检后启动新的 DP。
没有固定轮数；相同 Master 哈希下同一问题重复才视为真实阻塞。

## 14. 状态机

```text
PROJECT_RESOLVE
  -> EPISODE_INGEST
  -> CONTEXT_SELECT
  -> DIRECTOR_BATCH
  -> MASTER_COMPILE
  -> PROFILE_DERIVE
  -> STRUCTURAL_PRECHECK
  -> FRESH_DP
  -> DIRECTOR_REVISE (有问题)
  -> FINAL_HASH_CHECK
  -> ATOMIC_BATCH_COMMIT
  -> EPISODE_REVIEW
  -> ATOMIC_DELIVERY
```

恢复依据状态文件和内容哈希，不依据聊天记忆或文件名猜测。缓存只在剧本、项目背景、
知识、能力、资产卡、模型分配和输出契约均未变化时命中。
`DIRECTOR_SESSION.json` 另外绑定集级 Director Agent ID 和实际模型，批次恢复不得更换。

## 15. 后续资产绑定

无资产设计可以声明未来资产槽位和绑定后首选模式。生成媒体后：

1. 本地程序记录媒体哈希。
2. 用户提供/确认文字资产卡。
3. verified 卡绑定到原槽位。
4. 只重新派生受影响 Shot。
5. 生成模式或视觉事实改变时，只对受影响 Shot 运行 fresh DP；只有设计冲突才恢复
   Director 局部修订。

资产绑定不重新运行整集，也不调用视觉模型。

## 16. 交付

最终目录只包含：

```text
delivery/STORYBOARD.md
delivery/VIDEO_PROMPT.md
```

Master、Manifest、项目记忆、资产需求、DP 反馈、遥测和审计证据都是内部文件，不进入
交付目录。

## 17. 三种 Loop 严格分离

- `/mode-p-pilot`：正式创作，可启动 Director 和 fresh DP。
- `/mode-p-rebuild`：确定性工程修改与测试，不启动创作 Agent。
- `/mode-p-accept`：用户显式启动的固定实模验收，不得放入 `/loop`。

任何入口都不得自动切换到另一入口。

## 18. 完成标准

重构只有同时满足以下条件才算本地完成：

- 用户正式创作只需 `/mode-p-pilot <分集剧本>`。
- 完整剧本通过自然语言登记，后续分集自动绑定。
- 无项目、无资产都可运行。
- Director/DP 不读取媒体二进制。
- Director 模型可见内容符合第 7 节。
- DP Packet 不暴露 Master、Manifest、运行时代码或知识库。
- Storyboard/Video 根据 Profile 和生成模式改变输出组织。
- 两个视图来自同一条视觉时间线，Storyboard 仅投影 `[SB]` 节点。
- N 个 Shot 只有 N+1 个共享 Boundary，无双份交接设计。
- 同一分集的批次、修订和 Episode Review 使用同一 Director Agent。
- 每镜独立且不超过 15 秒。
- 本地全量测试和遗留扫描通过。

这些结构测试不能代替真实 Director/DP 的语义质量验收。
