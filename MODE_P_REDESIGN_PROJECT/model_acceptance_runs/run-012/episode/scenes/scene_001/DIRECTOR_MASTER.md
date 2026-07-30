# DIRECTOR_MASTER — scene_001（审讯室，夜，室内）

## 0. 版本

```text
Master 版本：scene_001/v1.0
```

## 1. 场景设计

```text
场景前状态：全片首场，无继承。冷开场直接进入进行中的夜间审讯：林警探与许然已隔桌相对，模糊的停车场照片在林警探手边桌沿，警徽藏在许然外套内袋。
戏剧变化：审讯权力反转。林警探以照片施压开局，许然拒接照片、以一枚警徽反将；林警探收回压在照片上的手——施压方变成被质问方。
信息策略：观众与两人同步知情。照片内容保持模糊，警徽归属全场不揭示；观众只看见两件物先后进入桌面中央与随后的收手，靠动作读出强弱交换。本场确立全片语法：物件入桌即筹码入局。
场景后状态：照片与警徽并列留在桌面中央，林警探的手静止在桌沿，质问悬置。静帧收束，交给下一场硬切（后期，冷夜转暖晨）。

场景空间：无窗审讯室。金属长桌南北向置于房间中央，桌面上方一盏罩式顶灯垂直下照，墙面沉入暗部。林警探坐桌北侧面向南，许然坐桌南侧面向北。门在西墙，全场闭合。
关系线：南北向对视线贯穿全场。全部机位位于桌轴东侧：林警探恒定占画面右侧、视线向左；许然恒定占画面左侧、视线向右。
人物路径：两人全场保持坐姿，无起立、无走位。全部调度发生在桌面：照片自北侧桌沿移至中央、警徽自外套内袋落至照片旁、林警探的手自照片收回桌沿。
摄影可用区域：桌轴东侧半区：正东侧面全景位（视轴向西）、东南角过许然肩位（视轴向西北）、东北角过林警探肩位（视轴向西南）、桌面东侧上方俯角特写位。全部固定三脚架机位，无运动。

视觉策略：单一顶灯高光比冷调，桌面是全场最亮平面，物件天然成为视觉中心。全场固定机位，权力反转全部由景别与占画比例承担：开局林警探在过肩镜中占画过半；警徽落桌后许然获得更近景别与稳定正面；终镜里两张脸全部退场，只剩桌面与一只收回的手。节奏为长镜静置，切点全部落在动作完成与话音落点。
镜头拆分理由：四个切点各承载一次信息交接：照片压定后进入林警探的施压单人；话音落点切入许然的接收与反击；许然话音落点切到被点名的那只手；收手完成后静帧收束。
场间关系：黑场硬切进入（全片开篇），终镜静帧硬切离场（后期），无声音桥。

场景蓝图：[D] 夜，无窗审讯室。一盏罩式顶灯垂直照亮金属桌面，墙面近黑。林警探（男，45岁上下，深色衬衫挽袖，无佩戴警徽）坐北侧；许然（男，35岁上下，深色外套内衬衬衫）坐南侧。桌面中央先后出现两件物：一张模糊的停车场照片、一枚警徽。本场变化：施压的手最终从照片上收回。
声音基调：[D] 全场只有通风管低鸣与灯具微弱电流声的房间底噪；对白干声无混响拖尾；纸张滑动与金属磕桌的接触声在静场中被放大。
```

## 2. 共享 Boundary

本场 4 个 Shot，共 5 个共享 Boundary（B0-B4），与 Shot 交错书写于下方序列：B0 -> Shot 1 -> B1 -> Shot 2 -> B2 -> Shot 3 -> B3 -> Shot 4 -> B4。

## 3. Shot Contract

## Boundary scene_001-B0 | SCENE_ENTRY -> scene_001-1

边界关系：[M] <scene_entry>
转场执行：[M] <post_production>
剪辑触发：[D] 黑场硬切，全片第一帧直接落在审讯室的静止对峙上。
交接描述：[D] 0 秒画面：顶灯下的金属桌，林警探坐北侧、指尖搭在桌沿前的模糊停车场照片上；许然坐南侧、双手叠放桌沿；两人对视静止。声音自房间底噪冷起，无音乐。
接入状态键：[M]
  - character:lin_jingtan position:interrogation_room|table_north_side|chair facing:south screen_direction:static posture:seated_upright_fingertips_on_photo wardrobe:dark_shirt_rolled_sleeves
  - character:xu_ran position:interrogation_room|table_south_side|chair facing:north screen_direction:static posture:seated_upright_hands_folded_on_table_edge wardrobe:dark_jacket_over_shirt
  - prop:parking_photo held_by:none location:table_north_edge_under_lin_fingertips
  - prop:police_badge held_by:xu_ran location:jacket_inner_pocket
  - light_main direction:top_down_overhead color_temp:4300K ratio:1:8
  - action_phase:static
  - story_time:night
  - environment:windowless_interrogation_room_quiet

## Shot scene_001-1 | 10s

叙事职责：[D] 建立对峙空间与第一次施压：照片被推到桌面中央，观众看清两人位置、桌面与顶灯构成的权力场。
剧本事实：[D] L5——林警探与许然隔桌相对；林警探把一张模糊的停车场照片推到桌中央。
原文定位：[M] scene_001 L5-L5
生成单元：[M] 一个独立 SD2.0 视频段，时长从 0 秒到 10 秒。
场景表达：[M] <conversation_power>
时间控制：[M] <event_nodes>

摄影设计：[D] 固定三脚架，正东侧面机位，视轴向西，高度比桌面高三十厘米；35mm 侧面全景收入全桌与两人坐姿全身；起止均为静止构图，无运动。
构图设计：[D] 对称侧面构图：林警探居画面右、许然居画面左，桌面横贯画面下三分之一；顶灯灯罩压画面上缘中央；视觉中心随照片从右侧桌沿滑到正中最亮点；两侧墙面黑负空间对称压边。
光影设计：[D] 罩式顶灯垂直下照，色温4300K，光比1:8；桌面为最亮平面，两人面部半亮半暗，墙面近黑；全镜光线恒定。
表演设计：[D] 林警探手臂平稳前伸推照片，推定后五指留在照片一角，上身前压两厘米；许然全程静止，双手叠放桌沿，视线钉在林警探脸上，双眼避开照片。

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无

视觉时间线：[D] [0.0s][SB] 夜间无窗审讯室，罩式顶灯垂直照亮金属桌面，墙面沉入暗部。侧面全景：林警探坐桌北侧（画面右），指尖搭在桌沿前的模糊停车场照片上；许然坐桌南侧（画面左），双手叠放桌沿，背脊直立。两人隔桌对视，全画面静止。
  [2.0s] 林警探手臂前伸，照片贴着桌面滑向桌面中央，纸边与金属桌面摩擦。
  [4.5s][SB] 照片停在桌面中央顶灯最亮处，林警探五指压住照片一角，手臂悬在桌面上方，上身前压。
  [7.0s] 许然保持原姿，双手与视线静止，房间只余底噪。
  [10.0s][SB] 定格侧面全景：照片在桌面中央被林警探的手压住一角，许然静止，两人对视。
声音设计：[D] 通风管低鸣与灯具电流声底噪贯穿；2.0-4.5 秒纸张滑过金属桌面的摩擦声；无对白，无音乐。

## Boundary scene_001-B1 | scene_001-1 -> scene_001-2

边界关系：[M] <continuous>
转场执行：[M] <post_production>
剪辑触发：[D] 照片压定后静置完成、画面完全静止的时刻切出。
交接描述：[D] 照片停在桌面中央、林警探五指压角、上身前压，许然叠手静坐；该静止状态为前镜结束帧与后镜 0 秒画面共用。
交出状态键：[M]
  - character:lin_jingtan position:interrogation_room|table_north_side|chair facing:south screen_direction:static posture:seated_lean_forward_fingers_pinning_photo
  - character:xu_ran position:interrogation_room|table_south_side|chair facing:north screen_direction:static posture:seated_upright_hands_folded_on_table_edge
  - prop:parking_photo held_by:none location:table_center_pinned_by_lin_fingers
  - prop:police_badge held_by:xu_ran location:jacket_inner_pocket
  - light_main direction:top_down_overhead color_temp:4300K ratio:1:8
  - action_phase:static
接入状态键：[M] <same>

## Shot scene_001-2 | 8s

叙事职责：[D] 施压方的正面陈词：林警探以最大占画比例说出指控，确立此刻的强势位。
剧本事实：[D] L7——林警探：「你说九点前就离开了。」
原文定位：[M] scene_001 L7-L7
生成单元：[M] 一个独立 SD2.0 视频段，时长从 0 秒到 8 秒。
场景表达：[M] <conversation_power>
时间控制：[M] <event_nodes>

摄影设计：[D] 固定三脚架，东南角过许然右肩机位，视轴向西北，机位比林警探视线低五厘米形成微仰；50mm 中景；无运动。
构图设计：[D] 林警探上身占画面右侧过半，面部近上三分之一线；前景左下角是许然虚化的后脑与肩线；压照片的手臂斜穿画面下缘；背景墙面全黑。
光影设计：[D] 顶灯自头顶直落，眉骨与鼻下投硬影，色温4300K，光比1:8；许然后脑仅存轮廓亮线；全镜光线恒定。
表演设计：[D] 开口前先有一次缓慢吸气；说话语速慢、音量低、字距拉开，双眼圆睁少眨，下颌随尾字微收；话音落后视线继续钉在许然脸上，手指在照片上保持压力。

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无

视觉时间线：[D] [0.0s][SB] 过许然右肩的中景：林警探占画面右侧过半，顶灯在眉骨下投出硬阴影，压在照片上的手臂斜入画面下缘；前景左下角是许然虚化的肩与后脑；背景全黑。
  [1.5s] 林警探胸腔缓慢吸气，嘴唇张开。
  [2.0s] 林警探开口说话，头部静止，双眼直视。
  [4.5s][SB] 话音落，嘴唇合拢，下颌微收，视线钉住对面，手指仍压在照片上。
  [8.0s][SB] 静帧：林警探保持凝视，画面内唯一运动是他极缓的呼吸起伏。
声音设计：[D] 底噪延续；2.0-4.5 秒对白（林警探）：「你说九点前就离开了。」近距干声；话音落后静场至镜末。

## Boundary scene_001-B2 | scene_001-2 -> scene_001-3

边界关系：[M] <continuous>
转场执行：[M] <post_production>
剪辑触发：[D] 对白尾字消散、静场持续一拍后，在林警探的凝视静止中切出，转向接收方。
交接描述：[D] 桌面与两人状态与上一边界一致：照片在中央被压、警徽仍在内袋；切点两侧共用该静止状态，后镜转到许然一侧接收这句话。
交出状态键：[M]
  - character:lin_jingtan position:interrogation_room|table_north_side|chair facing:south screen_direction:static posture:seated_lean_forward_fingers_pinning_photo
  - character:xu_ran position:interrogation_room|table_south_side|chair facing:north screen_direction:static posture:seated_upright_hands_folded_on_table_edge
  - prop:parking_photo held_by:none location:table_center_pinned_by_lin_fingers
  - prop:police_badge held_by:xu_ran location:jacket_inner_pocket
  - light_main direction:top_down_overhead color_temp:4300K ratio:1:8
  - action_phase:static
接入状态键：[M] <same>

## Shot scene_001-3 | 12s

叙事职责：[D] 反击：许然拒接照片，让警徽落桌并说出反问，权力在本镜内完成换手。
剧本事实：[D] L9——许然没有碰照片，从外套内袋取出一枚警徽放在照片旁；L11——许然：「先问问这枚警徽昨晚为什么在你的车里。」
原文定位：[M] scene_001 L9-L11
生成单元：[M] 一个独立 SD2.0 视频段，时长从 0 秒到 12 秒。
场景表达：[M] <conversation_power>
时间控制：[M] <event_nodes>

摄影设计：[D] 固定三脚架，东北角过林警探左肩机位，视轴向西南，机位与许然视线齐平；50mm 中近景，比前镜近半档；无运动。
构图设计：[D] 许然占画面左侧，面部与胸口清晰；前景右下角是林警探虚化的肩线与压照片的手；照片一角入画面下部；外套翻开与警徽落桌的动作在画面中部完成。
光影设计：[D] 顶灯直落，许然面部高反差半亮；警徽出袋后在顶光下闪出一次金属高光；色温4300K，光比1:8，光线恒定。
表演设计：[D] 先低头看一眼照片再抬眼——确认后拒触；右手翻开外套左襟取警徽，动作匀速无停顿；放徽时手腕下沉让金属轻磕桌面；说话音量低于林警探、语尾平直；说完保持直视，双手回到桌沿。

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无

视觉时间线：[D] [0.0s][SB] 过林警探左肩的中近景：许然占画面左侧，顶灯照出高反差面部，视线落在画面下部桌面中央的照片上；前景右下角是林警探虚化的肩与压在照片上的手。
  [1.5s] 许然视线从照片抬回林警探的眼睛，双手离开桌沿。
  [3.0s] 许然右手翻开外套左襟，从内袋取出一枚警徽，金属面接住顶光闪出一点高光。
  [5.5s][SB] 警徽底面轻磕桌面，被平放在照片右侧；许然的手离开警徽收回桌沿。
  [7.5s] 许然开口说话，语速平稳，头部静止。
  [11.0s] 话音落，许然合唇直视，肩线静止。
  [12.0s][SB] 静帧：警徽与照片并列于画面下部，许然直视前方，前景中林警探压照片的手保持原位。
声音设计：[D] 底噪延续；3.0 秒衣料摩擦声；5.5 秒金属磕桌短促闷响；7.5-11.0 秒对白（许然）：「先问问这枚警徽昨晚为什么在你的车里。」音量低于前镜对白；随后静场。

## Boundary scene_001-B3 | scene_001-3 -> scene_001-4

边界关系：[M] <continuous>
转场执行：[M] <post_production>
剪辑触发：[D] 许然话音落、静止一拍后，在他稳定的直视中切出，落点是被点名的那只手。
交接描述：[D] 桌面中央：照片被林警探五指压角，警徽平放照片右侧；两人坐姿未变。该状态为前镜结束帧与后镜 0 秒俯角特写共用。
交出状态键：[M]
  - character:lin_jingtan position:interrogation_room|table_north_side|chair facing:south screen_direction:static posture:seated_lean_forward_fingers_pinning_photo
  - character:xu_ran position:interrogation_room|table_south_side|chair facing:north screen_direction:static posture:seated_upright_gaze_on_lin_hands_on_table_edge
  - prop:parking_photo held_by:none location:table_center_pinned_by_lin_fingers
  - prop:police_badge held_by:none location:table_center_right_of_photo
  - light_main direction:top_down_overhead color_temp:4300K ratio:1:8
  - action_phase:static
接入状态键：[M] <same>

## Shot scene_001-4 | 10s

叙事职责：[D] 后果落地：被质问的手从照片上收回，本场的权力反转以一次收手完成并静帧收束全场。
剧本事实：[D] L13——林警探停住，收回压在照片上的手。
原文定位：[M] scene_001 L13-L13
生成单元：[M] 一个独立 SD2.0 视频段，时长从 0 秒到 10 秒。
场景表达：[M] <conversation_power>
时间控制：[M] <event_nodes>

摄影设计：[D] 固定三脚架，桌面东侧上方俯角特写机位，视轴向下偏西约六十度俯角；85mm 特写覆盖桌面中央与北侧桌沿；无运动。
构图设计：[D] 照片与警徽并列于画面中央偏上，林警探的手压住照片一角自画面下缘伸入；顶光在两件物边缘投出短影；画面上部留出金属桌面的空负区。
光影设计：[D] 顶灯垂直照明桌面，色温4300K，光比1:8；金属桌面反光勾出手的轮廓；全镜光线恒定。
表演设计：[D] 手部表演：五指压力先维持一拍，再逐指抬起离开纸面，手掌贴桌面匀速缩回至桌沿停住；整个撤回一气呵成，中途无停顿。

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无

视觉时间线：[D] [0.0s][SB] 俯角特写：金属桌面中央，模糊的停车场照片被林警探五指压住一角，警徽平躺在照片右侧，顶光直落，两件物边缘投出短影。
  [2.5s] 五指逐一离开纸面，指尖抬起，照片彻底松开。
  [5.0s][SB] 手掌贴着桌面匀速缩回，退到画面下缘的桌沿处停住。
  [7.5s] 画面内再无运动，照片与警徽并列于灯光中心。
  [10.0s][SB] 定格：桌面中央照片与警徽并列，林警探的手静止在画面下缘桌沿。
声音设计：[D] 底噪延续；2.5 秒指尖离开纸面的极轻粘离声；5.0 秒手掌与桌面的缓慢摩擦声；7.5 秒后完全静场收束。

## Boundary scene_001-B4 | scene_001-4 -> SCENE_EXIT

边界关系：[M] <scene_exit>
转场执行：[M] <post_production>
剪辑触发：[D] 收手停定、静帧保持两秒后切出，本场结束。
交接描述：[D] 交出终局画面：照片与警徽并列于顶灯下的桌面中央，林警探的手静止在桌沿，许然坐姿未变；声音为房间底噪静场，无延续声。下一场以清晨厨房独立开场，硬切（后期，冷转暖）。
交出状态键：[M]
  - character:lin_jingtan position:interrogation_room|table_north_side|chair facing:south screen_direction:static posture:seated_hand_resting_at_table_edge
  - character:xu_ran position:interrogation_room|table_south_side|chair facing:north screen_direction:static posture:seated_upright_hands_folded_on_table_edge
  - prop:parking_photo held_by:none location:table_center
  - prop:police_badge held_by:none location:table_center_right_of_photo
  - light_main direction:top_down_overhead color_temp:4300K ratio:1:8
  - action_phase:static
