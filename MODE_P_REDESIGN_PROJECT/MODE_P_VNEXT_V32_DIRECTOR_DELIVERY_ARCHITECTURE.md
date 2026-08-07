# Mode P vNext v3.2 — Director Delivery Architecture

状态：提案实现基线  
目标分支：`agent/director-delivery-contract-v32`  
适用范围：vNext Director、VEC、Projection、Storyboard Delivery、Video Prompt Delivery

## 1. 固定产品目标

项目最终交付由同一个导演执行合同派生：

```text
Director Draft
    ↓
Visual Execution Contract
    ↓
ProjectionAST
    ├── Storyboard Projection
    └── Video Prompt Projection
```

故事版与视频提示词不得由两个独立 Agent 分别创作。两种交付允许表达粒度不同，但不得在镜头、人物、动作、站位、左右手、道具、台词、音色、运镜、切镜、参考图和时间上产生冲突。

## 2. 当前问题

当前 v3.1 已具备精确 tick 时间轴、VEC、ProjectionAST 和两种派生视图，但仍存在以下产品缺口：

1. `cli.py` 同时承担组合根、工作流编排、事务提交、状态恢复和交付组装。
2. `pipeline/scene_nodes.py` 同时承担模型调用、解码、知识检索、Blocking、VEC、Projection、Gate 和 DP。
3. 工作流图在多个位置重复定义，缺少唯一图 authority。
4. Port 层直接依赖 prompt 实现类型。
5. Knowledge Retriever 暴露 legacy 类型，缺少反腐层。
6. Delivery 尚未形成正式 bounded context 与项目入口。
7. Storyboard 仍偏向稀疏 VisualBeat 视图，关键视觉变化没有成为一等领域对象。
8. Shot 级构图、机位、灯光、表演被复制到多个 Beat，导致相邻故事板画面缺少真实差异。
9. Prompt Renderer 会把节点拆成多个独立片段，不符合一次复制、一次生成的实际使用方式。

## 3. 目标分层

```text
mode_p_vnext/
├── domain/
│   ├── visual_state.py
│   ├── storyboard_moment.py
│   ├── camera_movement.py
│   ├── reference_binding.py
│   ├── dialogue_voice.py
│   └── delivery_manifest.py
├── application/
│   ├── workflows/
│   ├── stages/
│   ├── use_cases/
│   └── contracts/
├── ports/
├── adapters/
│   ├── providers/
│   ├── storage/
│   ├── knowledge/
│   └── delivery/
├── runtime/
└── bootstrap/
```

依赖方向：

```text
Domain
  ↑
Application + Ports
  ↑
Adapters + Runtime
  ↑
Bootstrap / CLI
```

CLI 只负责参数解析和调用 Application Use Case。Graph 只在 `application/workflows/` 定义一次。

## 4. 变化驱动故事板

故事板不按秒机械切片，也不只按抽象 VisualBeat 取样。任何足以让观众感知画面变化的事件，都必须形成可投影的 Storyboard Moment。

关键变化包括：

- 切镜；
- 景别、角度、构图或摄影机位置改变；
- 运镜开始、关键经过点、运镜落点；
- 人物起身、转身、停步、落座、靠近、远离；
- 人物站位、前后层级、左右关系改变；
- 身体朝向或视线对象改变；
- 左右手与道具关系改变；
- 人物进画、出画；
- 可见表演状态改变；
- 镜头首状态和镜头尾状态。

没有视觉变化的连续节点不得无意识复制。确需保持同一画面时，必须显式标记为 `HOLD`。

## 5. 核心领域对象

### 5.1 VisualState

描述一个可验证画面状态：

- 人物站位；
- 身体朝向；
- 视线；
- 左右手状态；
- 道具位置与方向；
- 画面内外状态；
- 摄影机位置、景别、轴线、焦点；
- 当前光线变化状态。

### 5.2 VisualChange

描述 `entering_state → resulting_state` 之间实际发生的变化，不重复完整静态描述。

### 5.3 CameraMovementArc

至少记录：

- 起始构图；
- 启动条件或启动时间；
- 运动方式与方向；
- 关键经过点；
- 结束构图；
- 停止条件或停止时间。

### 5.4 StoryboardMoment

建议角色：

```text
shot_open
action_start
action_contact
blocking_change
camera_move_start
camera_move_land
reaction_change
cut_point
shot_close
hold
```

每个 Moment 绑定：

- `shot_id`
- `source_node_id`
- `start_state_id`
- `end_state_id`
- `local_interval`
- `visual_change`
- `camera_state`
- `character_blocking`
- `prop_and_hand_state`
- `screen_direction`
- `continuity_handoff`

## 6. 单一源头一致性

Storyboard 与 Video Delivery 必须共同绑定：

- `generation_unit_id`
- `revision_id`
- `vec_digest`
- `projection_ast_digest`
- `reference_manifest_digest`
- `dialogue_voice_manifest_digest`
- `first_state_id`
- `last_state_id`

规则：

1. 视频提示词只能展开 ProjectionAST 已有内容。
2. 视频不得新增故事板和 AST 中不存在的镜头、动作、站位、左右手变化、道具变化、台词或音色。
3. 故事板必须包含所有关键切镜、运镜首尾、动作阶段、站位变化和镜头尾状态。
4. Storyboard 可以是合法稀疏视图；Video 必须完整覆盖本 Generation Unit 的所有可执行节点。
5. 任一冲突必须 fail closed，并返回限定范围的 RevisionRequest。

## 7. Generation Unit 本地时间

每个视频生成单元独立计时，最长 15 秒：

```text
GU-A storyboard: 0.0s–15.0s
GU-A video:      0.0s–15.0s

GU-B storyboard: 0.0s–15.0s
GU-B video:      0.0s–15.0s
```

不同 Generation Unit 不承接时间数字。内部可保留 Scene Placement，但交付和视频模型只使用 Generation Unit Local Time。

```text
scene_time                 内部排序坐标
generation_unit_local_time 正式交付坐标
```

不同视频通常通过剪辑跳转衔接，不要求传入上一视频末帧或目标尾帧。不得把末帧接力设为默认能力。

## 8. 参考输入合同

### 8.1 故事板生成

默认输入：

```text
@图片1 = 角色A身份与服装参考
@图片2 = 角色B身份与服装参考
@图片3 = 场景空间参考
@图片4 = 重要道具参考，可选
```

### 8.2 视频生成

默认输入：

```text
@图片1 = 本 Generation Unit 完整故事板
@图片2 = 角色A身份与服装参考
@图片3 = 角色B身份与服装参考
@图片4 = 场景空间参考
@图片5 = 重要道具参考，可选

@音频1 = 角色A音色参考
@音频2 = 角色B音色参考
```

视频必须把完整故事板作为镜头顺序、构图、人物位置、动作阶段、运镜和切镜的主要视觉依据。

## 9. 台词与音色

每句台词绑定：

- `dialogue_fact_id`
- `speaker_id`
- `dialogue_text`
- `local_start_time`
- `local_end_time`
- `voice_reference_id`
- `delivery_intent`
- `source_node_id`

故事板显示说话人、台词和落点。视频提示词使用完全相同的台词，并绑定人物音色参考。不得交换音色、改写台词、增加旁白或让未说话角色出现说话口型。

## 10. Prompt 纯净边界

正式生成提示词只保留模型可直接执行的内容：

- 参考图和音色分配；
- 画面规格；
- 全程固定画面与光线；
- 镜头时间；
- 构图、机位、人物站位；
- 动作、台词、音色、口型；
- 运镜；
- 环境声；
- 必要的负面限制。

以下内容不得进入生成提示词：

- 推理过程；
- 设计依据；
- 架构说明；
- 节点、哈希、Digest；
- 一致性验证文字；
- Gate 名称；
- 面向人的验收解释；
- 无法被模型直接执行的标签，例如“剪辑硬锁”。

这些信息保存在机器侧车 Manifest 和验证报告中。

## 11. 连续提示词交付

一个 Generation Unit 只交付：

```text
一份连续故事板提示词
一份连续视频提示词
一份共同的机器侧车 Manifest
```

机器内部可保留节点，但 Renderer 必须把节点合并为一次复制、一次生成的连续提示词。不得要求用户逐节点单独复制。

## 12. 光线规则

光线、时间、天气、色温、曝光和白平衡在提示词开头定义一次，默认贯穿整个 Generation Unit。

普通镜头段落不得机械重复光线字段。只有画面中的实际光源或导演设定发生变化时，才在对应时间点描述变化，例如：

```text
10.5s，手机屏幕亮起，冷蓝色屏幕光照亮人物下半张脸；原有环境光和曝光保持不变。
```

若变化结束，明确恢复开头定义的基础光线；否则保持新状态至本单元结束。

## 13. Delivery Gate

至少验证：

1. Storyboard 与 Video 绑定同一 ProjectionAST 和参考 Manifest。
2. 同一 Generation Unit 的 Storyboard 与 Video 都从 0.0 秒开始。
3. 时间区间完整、无重叠、无越界，最大 15 秒。
4. 每个关键 VisualChange 至少有一个 Storyboard Moment。
5. 相邻 Storyboard Moment 必须存在可验证视觉差异，或显式为 HOLD。
6. Shot 首尾、运镜首尾、切镜位置完整。
7. 人物站位、身体朝向、左右手和道具状态连续。
8. Video 覆盖所有可执行节点且顺序唯一。
9. Storyboard 与 Video 的台词、说话人、音色参考一致。
10. 视频提示词包含完整故事板输入要求。
11. 生成提示词中不得出现架构、推理、Digest、Gate 或验收解释。
12. 光线只在开头定义，除非对应时间点确有变化。

## 14. 迁移顺序

1. 将唯一工作流图移至 `application/workflows/`。
2. 将 `run_text_shadow` 下沉为 Application Use Case。
3. 拆分 `scene_nodes.py` 为各 Stage Use Case、Decoder 和 Adapter。
4. 引入 KnowledgeCatalogPort 与 legacy 反腐 Adapter。
5. 新增 VisualState、VisualChange、CameraMovementArc、StoryboardMoment。
6. 新增 ReferenceBindingManifest 和 DialogueVoiceManifest。
7. 新增连续 Storyboard Prompt Renderer。
8. 新增连续 Video Prompt Renderer。
9. 新增正式 run-artifact-to-delivery CLI。
10. 新增同源、时间、参考、台词、音色、光线和 Prompt Purity 测试。

## 15. 完成定义

只有同时满足以下条件，v3.2 Delivery 才可视为完成：

- 用户一次复制即可生成完整故事板；
- 用户一次复制即可生成完整 15 秒视频；
- 视频输入明确要求绑定本单元完整故事板；
- Storyboard 与 Video 同源且可机器验证；
- 每个生成单元独立使用 0.0s–15.0s 本地时间；
- 关键切镜、运镜首尾、人物动作、站位和道具变化完整进入故事板；
- 台词、说话人和音色参考完整进入视频提示词；
- 光线只在开头定义，变化时才补充；
- 生成提示词不包含推理和架构解释；
- 项目具有正式 Delivery CLI、Renderer 和真实运行验收测试。
