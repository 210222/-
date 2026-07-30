<!-- template: director_master v2.0 -->

# DIRECTOR_MASTER.md — 场景 1

> 本文件是场景唯一设计源。所有修订必须先修改本文件，再从本文件派生 `STORYBOARD.md` 和 `VIDEO_PROMPT.md`。
> 本模板遵循 LOOP_SPEC v2.1 第 9、10 节。

---

## 0. 版本信息

```text
Master 版本：SCN1/v1.0
父版本：无
创建时间：2026-07-16T12:00:00+08:00
最后修改：2026-07-16T12:00:00+08:00
对应 LOOP_SPEC：v2.1
```
<!-- 机器检查：Major must be a non-negative integer; minor resets to 0 on major bump. -->

---

## 1. 场景层设计

### 1.1 戏剧变化与信息策略

```text
场景前状态：无前场。观众不知道人物身份和关系。
戏剧变化：林警探从主动审讯者变为被动方；许然从被动嫌疑人变为持有反制信息者。
信息策略：观众与林警探同步——先以为许然是嫌疑人，后通过警徽发现许然反制。
           警徽的出现颠覆前面对话的所有预设。
场景后状态：许然掌握主动，林警探撤回。权力完成转移。
```

### 1.2 空间调度

```text
场景空间：【inferred】约 3m x 4m 审讯室，中央一张金属桌，两把椅子分居两侧。
         一面单向镜镜墙（假设），门在右侧后方。
关系线：林警探与许然隔桌对视，距离约 1.2m。桌子是正式关系的边界。
人物路径：两人均已在座，无入场/出场。身体移动仅限于手部和上半身。
摄影可用区域：桌两侧、房间角落、过肩高度。机位可放置于人物身后或侧面，
              也可置于桌面高度拍摄道具。
```

### 1.3 视觉策略

```text
视觉强度：中（开场）→ 高（警徽出现时收紧景别）→ 中残留（末镜静默）。
色彩策略：主色调冷绿灰（墙壁/桌面），荧光白（头顶灯光），无强调色。
光比策略：整体 3:1（头顶主光+环境补光），关闭局部顶灯使许然面部略显阴影，
          权力反转后他进入更充分的照明。
稳定性策略：全固定/三脚架。无手持或移动。运动仅限镜内人物动作。
节奏曲线：6s → 7s → 5s。中间镜最长，给反转动作充分时间。
```

### 1.4 镜头拆分理由

```text
三镜拆分：建立权力关系（双人镜）→ 反转动作（单人镜，许然）→ 反应（单人镜，林警探）。
不需要更多镜：信息变化集中在一个动作（取警徽），无需交替切换。
第一镜让观众理解位置和权力；第二镜详细展示反转过程；第三镜给前权力方反应时间。
```

### 1.5 全场转场策略

```text
入场方式：首镜从审讯室内部直接建立空间——观众不知前情，与人物同时在场。
出场方式：末镜以林警探手收回、身体后倾的静态画面结束——权力已转，无需再给对白。
场间关系：独立场景。末镜画面硬切至场景 2 清晨厨房。
```

### 1.6 双视图共享上下文

```text
场景蓝图：[D] 审讯室，夜间，室内。头顶荧光灯照明。中央金属桌，两人隔桌坐在对面。
          林警探初始主动，许然初始被动。照片是第一个物品，警徽是第二个。
声音基调：[D] 空调低频持续声。密封空间的微量回响。对话声音清晰，无外部干扰。
          照片推出时有纸张摩擦声，警徽放置时有金属与桌面接触的声响。
```

---

## 2. 逐镜 Shot Contract

### 2.1 叙事与溯源 `[M: ID, duration; D: 叙事文本]`

## Shot SCN1-1 | 6s

叙事职责：[D] 建立审讯空间、两人位置和初始权力结构——林警探主动推照片发起讯问。
剧本事实：[D] 林警探与许然隔桌相对。林警探把一张模糊的停车场照片推到桌中央。
原文定位：[M] SCN1 L1-L13
场景表达：[M] <conversation_power>
时间控制：[M] <event_nodes>

### 2.2 状态键 `[M: 键名字面量]`

开场状态：[D] 审讯室夜间。林警探与许然隔桌相对。林警探右手压在照片上，准备推向桌面中央。两人均坐姿稳定。
开场状态键：[M]
- character:lin_detective position:table_west facing:east screen_direction:static posture:seated_forward
- character:xu_ran position:table_east facing:west screen_direction:static posture:seated_upright
- prop:photo held_by:lin_detective location:lin_detective_hand
- light_main direction:overhead color_temp:4500K ratio:1:3
- action_phase:prepare

动作时间轴：[D] 从 0 秒到结束。采用 event_nodes 模式，只在真实事件变化点标记节点。
[0.0s] 林警探手压照片，准备推移。许然静坐注视。
[1.5s] 照片被推到桌面中央，发出纸张摩擦声。林警探手停在照片上。
[3.0s] 林警探：你说九点前就离开了。
[6.0s] 许然未碰照片，目光从照片抬起看向林警探。镜头微推。

结束状态：[D] 照片在桌面中央。林警探手仍停在照片上。许然未碰，目光抬起。空间信息和初始权力结构已经建立。
结束状态键：[M]
- character:lin_detective position:table_west facing:east screen_direction:static posture:seated_forward
- character:xu_ran position:table_east facing:west screen_direction:static posture:seated_upright
- prop:photo held_by:none location:table_center
- light_main direction:overhead color_temp:4500K ratio:1:3
- action_phase:static

### 2.3 摄影与构图 `[D: 自然语言]`

摄影设计：[D] 过肩镜头从许然右肩上方拍摄林警探。中全景（Medium Full Shot），包含桌面、照片和两人上半身。焦段 35mm（审讯室空间小，广角过肩保留环境）。镜头开场静止，在照片推至中央后缓慢推近约 0.3m，从全景过渡到中景。
构图设计：[D] 视觉中心为桌面中心——照片的推送方向和最终位置引导视线。林警探在画面左 2/3，照片的运动从他手下发出。许然占据右侧 1/3 作为前景剪影。前景许然肩膀的虚化提供空间深度。负空间在画面右侧林警探方向——他从左向右施加压力。
光影设计：[D] 主光从头顶荧光灯垂直打落，产生上下分离。林警探面部受光较充分（3:1），许然面部的顶光被帽檐/眉骨遮挡稍多。桌面反射灯光。无镜内光变化。
表演设计：[D] 林警探推照片的动作不紧不慢——反映他对场面有控制权。许然在照片推向中央时不追视，等照片到位后才缓慢抬起目光，表明他未被照片内容影响。

### 2.4 边界 `[M: ID 配对; D: 自然语言]`

进入边界 ID：[M] SCENE_ENTRY
进入边界：[D] 无前镜。场景从审讯室内部直接开场——镜头已就位，人物已在座。观众直接进入已有空间。
剪辑触发：[D] 开场即切入——不需要外部触发。
交出边界 ID：[M] SCN1-2
交出边界：[D] 本镜结束时林警探手停在照片上，许然未碰照片、目光抬起看向林警探。下一镜从许然切开，进入他的单人画面。
边界连续性：[M] <continuous>
转场执行：[M] <post_production>

### 2.5 生成模式与参考 `[M: 模式值和职责枚举; D: 职责说明]`

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无

### 2.6 双视图源文本 `[D: 由 Director 在 Master 内一次写完]`

故事板关键帧：[D]
- [开场] 过肩镜头，林警探手压照片，许然坐直注视，冷绿灰色审讯室。
- [关键变化] 照片被推到桌面中央，林警探手随照片移动后停在中央。
- [结束] 许然目光从照片抬起，镜头微推，定格在两人对峙。

视频时间轴：[D]
[0.0s] 过肩镜头：林警探手压在照片上，许然坐直注视。审讯室冷绿灰墙壁，头顶荧光灯。
[1.5s] 照片被推到桌面中央，发出纸张声。林警探手停在照片上缘，许然视线追随照片。
[3.0s] 林警探：你说九点前就离开了。
[6.0s] 许然没有碰照片，目光从照片抬起，直看向林警探。镜头缓慢推近结束。

声音设计：[D] 空调低频持续环境声。照片与桌面摩擦声（1.5s起）。林警探对白（3.0s起）。结束后保持安静环境声床。

---

## Shot SCN1-2 | 7s

叙事职责：[D] 展示许然的冷静和反转——他不碰照片，而是从外套取警徽，权力开始转移。
剧本事实：[D] 许然没有碰照片。他从外套内袋取出一枚警徽，放在照片旁。
原文定位：[M] SCN1 L1-L13
场景表达：[M] <suspense_reveal>
时间控制：[M] <second_nodes>

### 2.2 状态键 `[M: 键名字面量]`

开场状态：[D] 两人隔桌。照片在桌面中央。许然手未碰照片，身体微微调整坐姿。林警探手仍停在照片上缘。
开场状态键：[M]
- character:xu_ran position:table_east facing:west screen_direction:static posture:seated_upright
- character:lin_detective position:table_west facing:east screen_direction:static posture:seated_forward
- prop:photo held_by:none location:table_center
- prop:badge held_by:xu_ran location:inside_coat_pocket
- light_main direction:overhead color_temp:4500K ratio:1:3
- action_phase:prepare

动作时间轴：[D]
[0.0s] 许然坐直，目光从林警探移开。右手缓缓伸入外套内袋。
[1.5s] 手在内袋中接触到警徽金属表面，发出轻微金属触响。
[3.0s] 手取出警徽，捏在两指间。画面焦点从面部转移到手与警徽。
[4.5s] 许然手臂越过照片上方，将警徽放在照片旁——放在自己一侧桌面上。
[5.5s] 警徽与桌面接触发出清晰的金属撞击声。手收回。
[6.5s] 许然：先问问这枚警徽昨晚为什么在你的车里。
[7.0s] 镜头保持在许然，警徽在画面下方可见。

结束状态：[D] 许然手已收回。警徽放置在照片旁边的桌面上。两人隔着警徽和照片对视。权力结构已经变化——警徽表明许然身份不同寻常。
结束状态键：[M]
- character:xu_ran position:table_east facing:west screen_direction:static posture:seated_back
- character:lin_detective position:table_west facing:east screen_direction:static posture:seated_forward
- prop:photo held_by:none location:table_center
- prop:badge held_by:none location:table_adjacent_to_photo
- light_main direction:overhead color_temp:4500K ratio:1:3
- action_phase:recover

### 2.3 摄影与构图 `[D: 自然语言]`

摄影设计：[D] 内反拍镜头，从林警探左肩后方拍摄许然。中近景（Medium Close-Up），画面从许然齐胸至头顶。焦段 50mm，压缩背景深度，集中注意力在许然面部和手部动作。镜头完全固定，不跟随手运动——手出入画框，让观众期待手带回什么。
构图设计：[D] 画面以许然为中心，略微偏右（为左侧留出视线空间）。背景是模糊的审讯室墙壁。手入画取警徽时，画面重心短暂转移到画框左下角。警徽放置后，前景桌面上的警徽与许然面部构成上下视觉线。
光影设计：[D] 头顶荧光灯打亮许然头顶和肩膀。他的眼窝在顶光下有一定阴影，使表情不那么易读，增加神秘感。手部动作进入桌面区域时，桌面反射光补充手部照明。
表演设计：[D] 许然动作缓慢而精确——手伸入内袋、触到警徽、取出、放下的整个过程不紧不慢。这表明他是刻意控制节奏，而非冲动。放完后他微微后靠，增加姿态上的距离感。对白语气平稳，不带挑衅——他只是陈述事实，这比挑衅更有力。

### 2.4 边界 `[M: ID 配对; D: 自然语言]`

进入边界 ID：[M] SCN1-1
进入边界：[D] 上一镜结束于许然目光抬起看向林警探。本镜从许然单人近景开始，动作从"看"变为"行动"——他开始伸手取物。
剪辑触发：[D] 在许然目光从林警探移开的瞬间切入——动作动机的起始。
交出边界 ID：[M] SCN1-3
交出边界：[D] 本镜结束时许然后靠、说完对白。下一镜切至林警探反应——他的手还停在桌上，刚刚听完许然的反问。
边界连续性：[M] <continuous>
转场执行：[M] <post_production>

### 2.5 生成模式与参考 `[M: 模式值和职责枚举; D: 职责说明]`

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无

### 2.6 双视图源文本 `[D: 由 Director 在 Master 内一次写完]`

故事板关键帧：[D]
- [开场] 许然中近景，手开始伸入外套内袋，照片在画外下方。
- [关键变化] 手取出警徽，金属在荧光灯下反射，悬停在照片上方。
- [结束] 警徽放在照片旁桌面，手收回，许然后靠说完对白。

视频时间轴：[D]
[0.0s] 许然中近景。他坐直，目光从前方移开。右手伸入外套内袋。
[1.5s] 手在内袋中碰到警徽，发出轻微金属摩擦声。
[3.0s] 手取出警徽，两指捏住。焦点在警徽上——金属表面反射冷光。
[4.5s] 手臂越过照片上方，将警徽放置在照片旁（放在自己一侧）。
[5.5s] 警徽接触桌面——清晰的"嗒"声。手收回。
[6.5s] 许然：先问问这枚警徽昨晚为什么在你的车里。
[7.0s] 许然后靠，画面凝固。

声音设计：[D] 环境声床（空调持续声）贯穿。手与外套摩擦声（1.0s起）。金属摩擦（2.5s起）。警徽放桌面的金属撞击声（5.5s）。许然对白（6.5s起）。对白后保持环境静默床。

---

## Shot SCN1-3 | 5s

叙事职责：[D] 林警探的权力反应——他从主动位置被动摇，手收回，身体后倾。权力反转在画面中完成。
剧本事实：[D] 林警探停住，收回压在照片上的手。
原文定位：[M] SCN1 L1-L13
场景表达：[M] <contemplative_silence>
时间控制：[M] <event_nodes>

### 2.2 状态键 `[M: 键名字面量]`

开场状态：[D] 林警探坐在原位，右手仍然停在照片边缘。警徽已在桌面上许然一侧，与照片并列。
开场状态键：[M]
- character:lin_detective position:table_west facing:east screen_direction:static posture:seated_forward
- prop:photo held_by:none location:table_center
- prop:badge held_by:none location:table_adjacent_to_photo
- light_main direction:overhead color_temp:4500K ratio:1:3
- action_phase:static

动作时间轴：[D]
[0.0s] 林警探手停在照片上缘，身体微微前倾姿态。
[1.0s] 许然对白的冲击在脸上显现——细微的停顿、眼神变化。
[2.5s] 手开始从照片上缓慢收回——不是快速抽离，而是有意识的撤回。
[4.0s] 手完全撤回至桌面自己一侧。身体微微后倾。
[5.0s] 画面固定在新姿态上——权力平衡已完成转移。

结束状态：[D] 林警探手已完全收回，身体后倾。桌面上的照片和警徽成为新的视觉焦点——谁的东西在桌上，谁控制局面。许然（警徽主）占据主动。
结束状态键：[M]
- character:lin_detective position:table_west facing:east screen_direction:static posture:seated_back
- prop:photo held_by:none location:table_center
- prop:badge held_by:none location:table_adjacent_to_photo
- light_main direction:overhead color_temp:4500K ratio:1:3
- action_phase:recover

### 2.3 摄影与构图 `[D: 自然语言]`

摄影设计：[D] 内反拍对切镜头，从许然一侧拍林警探。中近景（Medium Close-Up），景别与上一镜对称。焦段 50mm。镜头完全固定，让表演成为唯一变化。结束画面停留约 1 秒再切。
构图设计：[D] 画面以林警探为中心。前景左侧可见警徽的一部分（在焦外），提醒观众权力来源。林警探的手收回动作穿越画面中心，手的运动路径从画面下缘的桌面撤回他身体一侧。手收回后，警徽在画面左下角的视觉权重上升。
光影设计：[D] 林警探面部在头顶光下比许然稍亮（之前 3:1，此时因他前倾变回稍微受光充分）。收回手时，手部从桌面反射光区移到暗区。无镜内光变化。
表演设计：[D] 林警探的关键变化在手收回的方式——不是被烫到似的快收，而是一个有意识的、承认失败的慢收。面部在听到对白时有一个可读的停滞（在原本流畅的审讯节奏中被外力打断）。身体后倾后视线没有离开许然，但凝视的性质从审讯变成了重新评估。

### 2.4 边界 `[M: ID 配对; D: 自然语言]`

进入边界 ID：[M] SCN1-2
进入边界：[D] 上一镜结束于许然后靠说完对白。本镜从林警探的反应开始——他刚听完那句反转性的问题。
剪辑触发：[D] 在许然最后一句词的余音中切入，让观众看林警探如何接住这句话。
交出边界 ID：[M] SCENE_EXIT
交出边界：[D] 本镜结束于林警探手收回、身体后倾的新姿态。桌面上的照片和警徽构成新的权力图景。场景在此状态中结束。
边界连续性：[M] <scene_exit>
转场执行：[M] <post_production>

### 2.5 生成模式与参考 `[M: 模式值和职责枚举; D: 职责说明]`

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无

### 2.6 双视图源文本 `[D: 由 Director 在 Master 内一次写完]`

故事板关键帧：[D]
- [开场] 林警探中近景，手停在照片上缘，表情从审讯状态开始变化。
- [关键变化] 手缓慢从桌面收回，身体后倾，视线模式改变。
- [结束] 手收回到自己一侧，身体后靠定住，权力姿态从主动变为被动。

视频时间轴：[D]
[0.0s] 林警探中近景。他手还停在照片上缘，身体微微前倾。
[1.0s] 许然话语的冲击到达——林警探眼神中出现顿挫，动作停止。
[2.5s] 右手从照片上缘缓慢收回——沿桌面往回滑移，不是快速抽手。
[4.0s] 手完全回到林警探一侧桌面。身体微微后倾。
[5.0s] 画面固定。警徽与照片并置的桌面构图成为最后信息。

声音设计：[D] 环境声床持续。许然对白的余音在第 0 秒尾声部延续（对白桥提前约 0.5s 或切齐——后期处理）。第 2.5s 起只有环境寂静。手收回时细微的衣袖与桌面摩擦声。结束无音乐。

---

## 3. 机器可检查字段汇总

| 字段 | Shot 1 | Shot 2 | Shot 3 |
|---|---|---|---|
| Shot ID | SCN1-1 | SCN1-2 | SCN1-3 |
| duration | 6s | 7s | 5s |
| scene_expression | conversation_power | suspense_reveal | contemplative_silence |
| timing_mode | event_nodes | second_nodes | event_nodes |
| 原文定位 | SCN1 L5 | SCN1 L9 | SCN1 L13 |
| 进入边界 ID | SCENE_ENTRY | SCN1-1 | SCN1-2 |
| 交出边界 ID | SCN1-2 | SCN1-3 | SCENE_EXIT |
| 边界连续性 | continuous | continuous | scene_exit |
| 转场执行 | post_production | post_production | post_production |
| 生成模式 | text_only | text_only | text_only |
| 参考资产 | 无 | 无 | 无 |

<!-- M: 所有 ID 链正确；duration ∈ (0,15]；scene_expression/timing_mode 为枚举值 -->
