# DIRECTOR_MASTER.md 参考模板 v4.0

> 场景唯一设计源。Director 只在这里创作；本地程序从同一条视觉时间线派生故事板和视频提示词。
> `[M]` 是确定性字段，`[D]` 是 Director 决策。不得输出 YAML、JSON、规则 ID、审计报告或平台包装。

## 0. 版本

```text
Master 版本：<scene_id>/v<major>.<minor>
```

## 1. 场景设计

```text
场景前状态：（从已提交连续性继承）
戏剧变化：（本场改变的权力、关系、认知、情绪或行动）
信息策略：（观众何时看见、忽略、误判或确认什么）
场景后状态：（传给下一场的结果）

场景空间：（可见结构、人物初始位置、物理限制）
关系线：（人物视线、距离和银幕方向）
人物路径：（角色调度及其变化）
摄影可用区域：（可放置机位和可执行运动范围）

视觉策略：（景别、焦段、稳定性、色彩、光比和节奏如何共同表达戏剧变化）
镜头拆分理由：（每个切点为什么发生）
场间关系：（如何接入本场、如何离开本场）

场景蓝图：[D] 可直接进入两份提示词的空间、人物、视觉基调和本场变化。
声音基调：[D] 持续环境声、空间声学和全场声音关系。
```

## 2. 共享 Boundary

Boundary 是相邻镜头唯一的交接源。一个 N 镜场景必须有 `B0...BN` 共 N+1 个 Boundary，按以下顺序与 Shot 交错书写：

```text
Boundary B0 -> Shot 1 -> Boundary B1 -> Shot 2 -> ... -> Shot N -> Boundary BN
```

### 2.1 场景入口

```markdown
## Boundary <scene_id>-B0 | SCENE_ENTRY -> <scene_id>-1

边界关系：[M] <scene_entry>
转场执行：[M] <in_camera | post_production>
剪辑触发：[D] 上一场或黑场在什么可观察时刻交入。
交接描述：[D] 本镜 0 秒的绝对可见状态及声音接入关系。
接入状态键：[M]
  - character:<entity_id> position:<x|y|z> facing:<world_direction> screen_direction:<left_to_right|right_to_left|depth_in|depth_out|static> posture:<state> wardrobe:<state，可选> injury:<state，可选>
  - prop:<prop_id> held_by:<entity_id|none> location:<x|y|z>
  - light_main direction:<direction> color_temp:<K> ratio:<1:N>
  - action_phase:<prepare|launch|travel|impact|recover|static>
  - story_time:<state，可选>
  - weather:<state，可选>
  - environment:<state，可选>
```

### 2.2 连续切点

连续 Boundary 的状态只写一次。下一镜开场直接复用它：

```markdown
## Boundary <scene_id>-B1 | <scene_id>-1 -> <scene_id>-2

边界关系：[M] <continuous>
转场执行：[M] <in_camera | post_production>
剪辑触发：[D] 唯一确定的动作、视线、声音、遮挡或图形切点。
交接描述：[D] 前镜交出、后镜接入的同一个绝对可见状态。
交出状态键：[M]
  - character:...
  - light_main ...
  - action_phase:...
接入状态键：[M] <same>
```

### 2.3 省略切点

只有 `elliptical` 允许边界两侧状态不同，两侧都必须明确：

```markdown
## Boundary <scene_id>-B2 | <scene_id>-2 -> <scene_id>-3

边界关系：[M] <elliptical>
转场执行：[M] <in_camera | post_production>
剪辑触发：[D] 省略发生的明确依据。
交接描述：[D] 被省略的时间、空间或动作，以及后镜接入的确定状态。
交出状态键：[M]
  - character:...
  - light_main ...
  - action_phase:...
接入状态键：[M]
  - character:...
  - light_main ...
  - action_phase:...
```

### 2.4 场景出口

```markdown
## Boundary <scene_id>-BN | <scene_id>-N -> SCENE_EXIT

边界关系：[M] <scene_exit>
转场执行：[M] <in_camera | post_production>
剪辑触发：[D] 本场结束的唯一可观察时刻。
交接描述：[D] 交给下一场的画面、动作和声音绝对状态。
交出状态键：[M]
  - character:...
  - light_main ...
  - action_phase:...
```

## 3. Shot Contract

每个 Shot 是一个独立的即梦 SD2.0 视频段，`0 < duration <= 15s`。相邻镜头状态从共享 Boundary 继承，Shot 内不重复填写开场/结束状态。

```markdown
## Shot <scene_id>-<number> | <duration>s

叙事职责：[D] 本镜为何存在，观众在本镜获得什么。
剧本事实：[D] 可追溯事实或必要反应。
原文定位：[M] <scene_id> L<start>-L<end>
生成单元：[M] 一个独立 SD2.0 视频段，时长从 0 秒到本镜 duration。
场景表达：[M] <conversation_power | crowd_attention | action_chase | suspense_reveal | contemplative_silence | investigation_object | montage | cross_space_transition>
时间控制：[M] <event_nodes | second_nodes | half_second_nodes>

摄影设计：[D] 唯一确定的机位、景别、角度、焦段、摄影运动、速度、路径和起止稳定性。
构图设计：[D] 视觉中心、人物关系、视线、负空间和前中后景。
光影设计：[D] 物理光源、方向、色温、光比及镜内变化。
表演设计：[D] 动作、姿态、视线、面部和节奏的可见表达。

生成模式：[M] <text_only | first_last_frame | omni_reference>
参考资产：[M] [<asset_id>|<responsibility>, ...] 或 无
参考职责：[D] 每份素材具体约束什么；无素材写“无”。
参考优先级：[D] 冲突时保留什么；无素材写“无”。

视觉时间线：[D] [0.0s][SB] <绝对开场的可见状态>
  [<time>s] <这一节点发生的可见变化>
  [<time>s][SB] <真正需要画出的关键状态>
  [<duration>s][SB] <绝对结束状态>
声音设计：[D] 环境声、原文对白时点、必要音效、声音桥或静音关系。
```

## 4. 视觉时间线规则

1. 视觉时间线是故事板与视频提示词唯一的逐时创意源。
2. 视频提示词复制全部节点；故事板只提取带 `[SB]` 的节点，文字不改写。
3. 首节点必须是 `[0.0s][SB]`，末节点必须是 `[duration][SB]`。
4. 每镜至少两个 `[SB]` 节点；其余关键帧数量由动作和信息变化决定，不为凑数量添加。
5. `event_nodes` 只写真实变化点；`second_nodes` 相邻节点不超过 1 秒；`half_second_nodes` 相邻节点不超过 0.5 秒。
6. 时间线只能写最终可见状态，不写备选方案、否定指令、内心活动或文学比喻。

## 5. 生成模式

- `text_only`：参考资产写“无”，从剧本、连续性和文字资产事实完成设计。
- `first_last_frame`：恰好绑定 `first_frame` 与 `last_frame` 两个图像职责。
- `omni_reference`：每份素材只承担明确职责，并写清冲突优先级。

模式是 Director 的场景决策。本地程序只检查枚举、资产绑定和已声明能力，不替 Director 选择。

## 6. 派生边界

本地程序只允许：

- 从统一视觉时间线复制全部视频节点。
- 从同一时间线筛选 `[SB]` 节点形成故事板。
- 从共享 Boundary 复制一次交接描述和剪辑触发。
- 复制 Director 已写的摄影、构图、光影、表演、声音和参考职责。
- 标注 Shot ID、时长、生成模式和素材职责。

本地程序不得补写画面、选择关键帧、解释情绪、生成镜头运动、改写切点或制造新的创意句子。

## 7. 兼容性

- 活跃模板版本：v4.0。
- 编译器可以只读历史 v3 Master，以保留旧验收证据。
- 新创作、修订和重新验收必须使用统一视觉时间线与共享 Boundary，不得继续输出“故事板关键帧 + 视频时间轴”双源结构。
