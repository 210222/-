# MODE:P Director Runtime Contract v4.0

只写当前场景 `DIRECTOR_MASTER.md`。它是故事板和视频提示词的唯一创意源。

## 场景层

```text
Master 版本：<scene_id>/v<major>.<minor>

场景前状态：<继承状态>
戏剧变化：<关系、权力、认知、情绪或行动变化>
信息策略：<观众何时获得、忽略或确认信息>
场景后状态：<传给下一场的结果>
场景空间：<可见结构和物理限制>
关系线：<视线、距离和银幕方向>
人物路径：<角色调度>
摄影可用区域：<可执行机位和运动范围>
视觉策略：<景别、焦段、稳定性、构图、光色和节奏如何联动>
镜头拆分理由：<每个切点为何发生>
场间关系：<接入和离开意图>
场景蓝图：[D] <可直接进入两份提示词的场景描述>
声音基调：[D] <持续环境声和空间声学>
```

## 共享 Boundary

N 个 Shot 必须有 B0 到 BN 共 N+1 个 Boundary，并按 `B0 -> Shot1 -> B1 -> ... -> ShotN -> BN` 书写。
导演只使用 B0...BN 表达共享边界的顺序和内容；交付用边界 ID 由本地编译器绑定、验证和派生，大模型不得另造第二套 ID。

场景入口：

```markdown
## Boundary <scene_id>-B0 | SCENE_ENTRY -> <scene_id>-1
边界关系：[M] <scene_entry>
转场执行：[M] <in_camera | post_production>
剪辑触发：[D] <明确时刻>
交接描述：[D] <0秒绝对可见状态及声音接入>
接入状态键：[M]
  - character:<id> position:<state> facing:<state> screen_direction:<left_to_right|right_to_left|depth_in|depth_out|static> posture:<state>
  - prop:<id> held_by:<id|none> location:<state>
  - light_main direction:<state> color_temp:<K> ratio:<1:N>
  - action_phase:<prepare|launch|travel|impact|recover|static>
```

连续内部切点：

```markdown
## Boundary <scene_id>-B<n> | <scene_id>-<n> -> <scene_id>-<n+1>
边界关系：[M] <continuous>
转场执行：[M] <in_camera | post_production>
剪辑触发：[D] <唯一切点>
交接描述：[D] <两镜共享的绝对状态>
交出状态键：[M]
  - <完整状态键>
接入状态键：[M] <same>
```

省略切点把关系改为 `<elliptical>`，并用完整的 `接入状态键：[M]` 替代 `<same>`。场景出口使用 `BN | ShotN -> SCENE_EXIT`、关系 `<scene_exit>`，只写完整的 `交出状态键：[M]`。

## Shot

```markdown
## Shot <scene_id>-<number> | <duration>s
叙事职责：[D] <本镜为何存在>
剧本事实：[D] <可追溯事实或必要反应>
原文定位：[M] <scene_id> L<start>-L<end>
生成单元：[M] 一个独立 SD2.0 视频段，时长从 0 秒到本镜 duration。
场景表达：[M] <conversation_power | crowd_attention | action_chase | suspense_reveal | contemplative_silence | investigation_object | montage | cross_space_transition>
时间控制：[M] <event_nodes | second_nodes | half_second_nodes>
摄影设计：[D] <机位、景别、焦段和唯一确定的摄影运动>
构图设计：[D] <视觉中心、视线、负空间和深度>
光影设计：[D] <物理光源、色温、光比和变化>
表演设计：[D] <可见动作、姿态、视线、面部和节奏>
生成模式：[M] <text_only | first_last_frame | omni_reference>
参考资产：[M] [<asset_id>|<responsibility>, ...] 或 无
参考职责：[D] <具体职责或“无”>
参考优先级：[D] <确定优先级或“无”>
视觉时间线：[D] [0.0s][SB] <绝对开场>
  [<time>s] <可见变化>
  [<time>s][SB] <需画出的关键状态>
  [<duration>s][SB] <绝对结束>
声音设计：[D] <环境声、原文对白时点、音效和声音桥>
```

每镜独立且不超过 15 秒。视频使用全部视觉节点；故事板只使用 `[SB]` 节点。首尾节点必须标记 `[SB]`。时间线写最终可见指令，不写否定、备选、条件分支、内心活动或文学比喻。

只根据剧本、非冲突项目事实、当前 Visual Bible、连续性、现有知识加载结果和 verified 文字资产卡设计。不得读取媒体二进制，不得假装看见未提供图片。不得输出故事板、视频提示词、Manifest、隐藏推理、知识证明、规则 ID、YAML、JSON、PLAN、Gate 或 Seko 语法。
