# DIRECTOR_MASTER — scene_003（夜行列车包厢，夜，室内）

## 0. 版本

```text
Master 版本：scene_003/v1.0
```

## 1. 场景设计

```text
场景前状态：独立情境，无跨场继承。夜行列车包厢：顾言与米娅隔窄桌对坐，列车行进，窗外城市灯光流动；存储卡藏在米娅扣在桌沿的右拳中，工作证在顾言大衣内袋。
戏剧变化：对等条件交换。顾言开价（交卡、下一站下车）；米娅举卡却按住交付、开出反条件（证人名单删名）；顾言以翻扣工作证作答；米娅把存储卡放到桌面中央——双方各让一步，交易落定。
信息策略：观众与两人同步知情。卡内容与证面信息全场保持背向镜头，删名承诺只以翻扣动作呈现，无语言确认。隧道是剧本给定的节奏器：谈判最硬的两句压进黑暗里说完，让步与交付发生在光回来之后的亮处。
场景后状态：存储卡在桌面正中央，工作证翻扣一旁，两人各自靠回椅背。静帧收束，硬切进入雨夜追逐（静转动，后期，雨声提前入点）。

场景空间：夜行列车软席包厢。西侧车窗，窗下窄桌沿东西向伸入包厢；桌两侧南北对坐：顾言北座面南，米娅南座面北；东侧是包厢门与走廊。列车向北行驶，窗外灯光在朝西视轴画面中自右向左流动；入隧道时窗外光消失，仅剩包厢顶灯弱暖光。
关系线：南北向对视线。全部机位在桌轴东侧（门侧）：顾言恒定占画面右、视线向左；米娅恒定占画面左、视线向右。终镜为桌轴东端的对称略俯构图，两张四分之三侧脸左右均衡。
人物路径：两人全场坐姿无走位。物件路径：存储卡自米娅右拳升至面前两指间、再落至桌面正中央；工作证自顾言大衣内袋到右手、翻面扣在桌面中央左侧。
摄影可用区域：包厢内桌轴东侧：东端轴向双人位（水平与略俯两档）、东南角过米娅肩的顾言单人位、东北角过顾言肩的米娅单人位、桌面东缘俯角特写位。机身随车体保持低频微晃，无操作性运动。

视觉策略：包厢顶灯弱暖光打底，窗外流动冷光作副光；入隧道后只剩顶灯，人物压成轮廓与半脸；驶出隧道的回光落在桌面上，交付在亮处完成。景别对称推进：双人—单人—单人—单人—桌面—双人，两人获得完全等量的景别与占画，构图上无任何一方取得优势。
镜头拆分理由：入隧道后的黑暗定场一拍切入开价单人；话音落切到举卡——以物作答；反条件话音落切到接收方脸上看他消化；他的手探向大衣内袋处切入桌面，让翻扣与放卡两只手在同一画面完成交换；双手撤回、桌面两物静止后切出到轴向双人静帧收束。
场间关系：自上一场清晨静帧硬切进入（亮转暗，后期）；终镜静帧硬切离场，雨声在切点前零点五秒由后期入点作声音桥。

场景蓝图：[D] 夜，行进中的列车软席包厢。窄桌两侧对坐：顾言（男，40岁上下，深色大衣）与米娅（女，30岁上下，便装外套）。窗外城市灯光自右向左流过，入隧道即黑，顶灯弱暖光恒亮。桌面上将先后出现翻扣的工作证与放在正中央的存储卡。本场变化：一次各让一步的等价交换。
声音基调：[D] 行进列车底噪：轨缝节拍、车体低频吱响；入隧道时风压声增厚变闷、出隧道时变薄变亮；对白近距干声；存储卡与桌面的轻磕、证件翻扣的闷响是关键音效。
```

## 2. 共享 Boundary

本场 6 个 Shot，共 7 个共享 Boundary（B0-B6），与 Shot 交错书写于下方序列：B0 -> Shot 1 -> B1 -> Shot 2 -> B2 -> Shot 3 -> B3 -> Shot 4 -> B4 -> Shot 5 -> B5 -> Shot 6 -> B6。

## 3. Shot Contract

## Boundary scene_003-B0 | SCENE_ENTRY -> scene_003-1

边界关系：[M] <scene_entry>
转场执行：[M] <post_production>
剪辑触发：[D] 自上一场清晨静帧硬切，第一帧落在夜行包厢的流动灯光双人全景上。
交接描述：[D] 0 秒画面：行进列车包厢，顾言与米娅隔窄桌对坐对视，窗外城市灯光自右向左流动扫过两人侧脸，米娅右拳扣在桌沿。声音自轨缝节拍底噪冷起。
接入状态键：[M]
  - character:gu_yan position:train_compartment|table_north_seat|seated facing:south screen_direction:static posture:seated_forearms_on_table wardrobe:dark_overcoat
  - character:mi_ya position:train_compartment|table_south_seat|seated facing:north screen_direction:static posture:seated_right_fist_on_table_edge wardrobe:plain_casual_jacket
  - prop:memory_card held_by:mi_ya location:inside_right_fist_on_table_edge
  - prop:work_id held_by:gu_yan location:coat_inner_pocket
  - light_main direction:overhead_cabin_lamp color_temp:3200K ratio:1:4
  - action_phase:static
  - story_time:night
  - environment:train_moving_open_night_city_lights_streaking

## Shot scene_003-1 | 12s

叙事职责：[D] 建立对坐关系与列车节奏，并让隧道在镜内吞掉光线——谈判被送进黑暗。
剧本事实：[D] L30——顾言与证人米娅隔着窄桌坐着；列车经过隧道，窗外的城市灯光短暂消失。
原文定位：[M] scene_003 L30-L30
生成单元：[M] 一个独立 SD2.0 视频段，时长从 0 秒到 12 秒。
场景表达：[M] <conversation_power>
时间控制：[M] <event_nodes>

摄影设计：[D] 桌轴东端水平双人位，视轴向西；40mm；机身随车体低频微晃，无操作性运动；起止构图稳定。
构图设计：[D] 对称双人侧构图：顾言居画面右半、米娅居画面左半，窄桌横贯画面下部，车窗光带横贯背景；城市灯光的光斑自右向左连续拉线；两人视线在画面中线相接。
光影设计：[D] 包厢顶灯弱暖光为主，色温3200K，光比1:4；窗外流动冷光在两人侧脸上扫出移动光斑；入隧道瞬间窗光消失，光比收紧，只剩顶灯窄光池。
表演设计：[D] 两人对视静止，米娅右拳扣在桌沿，拇指压住食指；顾言前臂搭桌、十指交叉；入黑后两人轮廓保持原位，呼吸节奏可见。

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无

视觉时间线：[D] [0.0s][SB] 夜行列车包厢对称双人全景：顾言居画面右、米娅居画面左，隔窄桌对视；背景车窗光带里城市灯光自右向左流动，光斑扫过两人侧脸；米娅右拳扣在桌沿；画面带列车低频微晃。
  [3.0s] 一串密集灯点扫过窗面，亮斑依次滑过两张侧脸。
  [6.5s][SB] 窗外光骤然消失——列车进入隧道；包厢只剩顶灯弱暖光，两人压成轮廓与半脸，桌面只余一小片光池；风压声变厚。
  [9.5s] 黑暗持续，两人轮廓静止，光池里的桌面空无一物。
  [12.0s][SB] 定格：隧道黑暗中的双人轮廓对坐，窗面全黑，顶灯光池落在空桌面中央。
声音设计：[D] 轨缝节拍与车体低频吱响贯穿；6.5 秒入隧道，风压声增厚、音色变闷并持续到镜末；无对白。

## Boundary scene_003-B1 | scene_003-1 -> scene_003-2

边界关系：[M] <continuous>
转场执行：[M] <post_production>
剪辑触发：[D] 入隧道后的黑暗定场保持一拍、画面完全静止的时刻切出。
交接描述：[D] 隧道内：两人轮廓对坐、桌面光池空置、米娅右拳仍扣桌沿；该状态为前镜结束帧与后镜 0 秒画面共用。
交出状态键：[M]
  - character:gu_yan position:train_compartment|table_north_seat|seated facing:south screen_direction:static posture:seated_forearms_on_table
  - character:mi_ya position:train_compartment|table_south_seat|seated facing:north screen_direction:static posture:seated_right_fist_on_table_edge
  - prop:memory_card held_by:mi_ya location:inside_right_fist_on_table_edge
  - prop:work_id held_by:gu_yan location:coat_inner_pocket
  - light_main direction:overhead_cabin_lamp color_temp:3200K ratio:1:8
  - action_phase:static
  - environment:tunnel_inside_window_black
接入状态键：[M] <same>

## Shot scene_003-2 | 8s

叙事职责：[D] 开价：顾言在黑暗中说出条件，半脸窄光让这句话只剩内容、无表情余地。
剧本事实：[D] L32——顾言：「存储卡给我，你下一站下车。」
原文定位：[M] scene_003 L32-L32
生成单元：[M] 一个独立 SD2.0 视频段，时长从 0 秒到 8 秒。
场景表达：[M] <conversation_power>
时间控制：[M] <event_nodes>

摄影设计：[D] 东南角过米娅肩的顾言单人位，视轴向西北，与顾言视线齐平；50mm 中近景；机身低频微晃；无操作性运动。
构图设计：[D] 顾言占画面右侧，顶灯只照出眉骨、鼻梁与颧骨窄亮区；背景窗面全黑；前景左下角是米娅虚化的肩线与后脑轮廓。
光影设计：[D] 顶灯自上直落，色温3200K，光比1:8；面部大半沉入暗部，唯亮区随微晃轻移；全镜无窗光。
表演设计：[D] 开口前静止一拍；说话语速平、字字等重、无手势；话音落后合唇，视线在黑暗中持续压向对面。

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无

视觉时间线：[D] [0.0s][SB] 隧道黑暗中的顾言中近景：他占画面右侧，顶灯照出眉骨与鼻梁的窄亮区，其余面部沉入暗部；背景窗面全黑，前景左下角是米娅虚化的肩线。
  [1.5s] 顾言开口说话，语速平，头部静止。
  [4.5s][SB] 话音落，嘴唇合拢，窄光区里的双眼持续压向画外的米娅。
  [8.0s][SB] 静帧：半脸窄光中的凝视，画面随车体低频微晃。
声音设计：[D] 隧道内闷底噪贯穿；1.5-4.2 秒对白（顾言）：「存储卡给我，你下一站下车。」近距干声；随后静场。

## Boundary scene_003-B2 | scene_003-2 -> scene_003-3

边界关系：[M] <continuous>
转场执行：[M] <post_production>
剪辑触发：[D] 开价话音落、静止一拍后切出，转向被开价的一方。
交接描述：[D] 隧道内状态延续：两人坐姿未变、卡仍在米娅拳中；该静止状态为前镜结束帧与后镜 0 秒画面共用。
交出状态键：[M]
  - character:gu_yan position:train_compartment|table_north_seat|seated facing:south screen_direction:static posture:seated_forearms_on_table
  - character:mi_ya position:train_compartment|table_south_seat|seated facing:north screen_direction:static posture:seated_right_fist_on_table_edge
  - prop:memory_card held_by:mi_ya location:inside_right_fist_on_table_edge
  - prop:work_id held_by:gu_yan location:coat_inner_pocket
  - light_main direction:overhead_cabin_lamp color_temp:3200K ratio:1:8
  - action_phase:static
  - environment:tunnel_inside_window_black
接入状态键：[M] <same>

## Shot scene_003-3 | 10s

叙事职责：[D] 以物作答再加价：米娅把卡举到脸前展示又按住交付，随后说出反条件——筹码可见、交付冻结。
剧本事实：[D] L34——米娅把存储卡夹在两指之间，却没有递出；L36——米娅：「先把我的名字从证人名单里删掉。」
原文定位：[M] scene_003 L34-L36
生成单元：[M] 一个独立 SD2.0 视频段，时长从 0 秒到 10 秒。
场景表达：[M] <conversation_power>
时间控制：[M] <event_nodes>

摄影设计：[D] 东北角过顾言肩的米娅单人位，视轴向西南，与米娅视线齐平；50mm 中近景，与前镜同档景别保持对等；机身低频微晃；无操作性运动。
构图设计：[D] 米娅占画面左侧，半脸窄光与顾言前镜完全对称；右拳自画面下缘升入画面中带；卡面背向镜头，卡沿在顶灯下亮出一线；前景右下角是顾言虚化的肩线。
光影设计：[D] 顶灯直落，色温3200K，光比1:8；存储卡上升入光池时卡沿闪出一线反光；全镜无窗光。
表演设计：[D] 拳匀速上升到下颌高度，食指与中指伸出夹出存储卡，手腕随即锁定悬停；说话时字距拉开、音量与顾言等平；话音落后两指与卡保持静止，视线越过卡沿钉住对面。

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无

视觉时间线：[D] [0.0s][SB] 隧道黑暗中的米娅中近景：她占画面左侧，顶灯照出半脸窄亮区，右拳扣在画面下缘桌沿处；背景窗面全黑，前景右下角是顾言虚化的肩线。
  [2.0s] 右拳匀速升至下颌高度，食指与中指伸出，两指间夹出一枚存储卡，卡沿在顶灯下亮出一线反光。
  [4.0s][SB] 存储卡停在她面前两指间，手腕悬定静止，卡面背向镜头。
  [5.5s] 米娅开口说话，音量平，卡在指间保持静止。
  [8.5s] 话音落，两指与卡静止，视线越过卡沿钉住画外的顾言。
  [10.0s][SB] 静帧：两指夹卡立在黑暗前景，米娅半脸在卡后，窄光区里双眼直视。
声音设计：[D] 隧道内闷底噪贯穿；5.5-8.2 秒对白（米娅）：「先把我的名字从证人名单里删掉。」近距干声；随后静场。

## Boundary scene_003-B3 | scene_003-3 -> scene_003-4

边界关系：[M] <continuous>
转场执行：[M] <post_production>
剪辑触发：[D] 反条件话音落、持卡悬停静止一拍后切出，落到接收条件的顾言脸上。
交接描述：[D] 隧道内：米娅两指夹卡悬于面前，顾言坐姿未变；该状态为前镜结束帧与后镜 0 秒画面共用。
交出状态键：[M]
  - character:gu_yan position:train_compartment|table_north_seat|seated facing:south screen_direction:static posture:seated_forearms_on_table
  - character:mi_ya position:train_compartment|table_south_seat|seated facing:north screen_direction:static posture:seated_card_between_two_fingers_at_face_level
  - prop:memory_card held_by:mi_ya location:between_two_fingers_at_face_level
  - prop:work_id held_by:gu_yan location:coat_inner_pocket
  - light_main direction:overhead_cabin_lamp color_temp:3200K ratio:1:8
  - action_phase:static
  - environment:tunnel_inside_window_black
接入状态键：[M] <same>

## Shot scene_003-4 | 8s

叙事职责：[D] 消化与决定：顾言在黑暗中接住反条件，视线从人到卡再回到人，手伸向大衣内袋——让步开始成形。
剧本事实：[D] L36 之后、L38 之前的必要反应：顾言接收条件并取出工作证的过渡动作。
原文定位：[M] scene_003 L36-L38
生成单元：[M] 一个独立 SD2.0 视频段，时长从 0 秒到 8 秒。
场景表达：[M] <conversation_power>
时间控制：[M] <event_nodes>

摄影设计：[D] 东南角过米娅肩的顾言单人位（与本场 Shot 2 同机位），视轴向西北；50mm 中近景；机身低频微晃；无操作性运动。
构图设计：[D] 顾言占画面右侧半脸窄光；前景左缘是米娅持卡手指的虚化剪影，卡沿一线反光作为前景锚点；背景窗面全黑。
光影设计：[D] 顶灯直落，色温3200K，光比1:8；取证动作在暗部完成，证件入光池上方时露出硬质卡片轮廓；全镜无窗光。
表演设计：[D] 视线先从她的眼睛降到卡上，再抬回眼睛——两段清晰的眼动；右手离开桌沿探入大衣内襟，动作缓慢无声张；手回到桌面上方时指间捏着工作证，悬停不落。

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无

视觉时间线：[D] [0.0s][SB] 隧道黑暗中的顾言中近景：半脸窄光静止，前景左缘悬着米娅持卡手指的虚化剪影，卡沿亮出一线。
  [2.0s] 顾言的视线从她的眼睛降到存储卡上，再抬回她的眼睛。
  [4.0s] 右手离开桌沿，探入大衣内襟，肩线随之微沉。
  [6.0s][SB] 手回到桌面上方，指间捏着一张硬质工作证，悬停在光池边缘。
  [8.0s][SB] 静帧：证件悬在桌面上方，顾言凝视对面，窗面仍黑。
声音设计：[D] 隧道内闷底噪贯穿；4.0 秒大衣衣料摩擦声；无对白；镜末静场。

## Boundary scene_003-B4 | scene_003-4 -> scene_003-5

边界关系：[M] <continuous>
转场执行：[M] <post_production>
剪辑触发：[D] 证件悬停在桌面上方、下落开始前的一拍切出，落到桌面。
交接描述：[D] 隧道内最后状态：顾言右手捏工作证悬于桌面上方，米娅两指夹卡悬于面前；桌面空置。该状态为前镜结束帧与后镜 0 秒俯角特写共用。
交出状态键：[M]
  - character:gu_yan position:train_compartment|table_north_seat|seated facing:south screen_direction:static posture:seated_right_hand_holding_work_id_above_table
  - character:mi_ya position:train_compartment|table_south_seat|seated facing:north screen_direction:static posture:seated_card_between_two_fingers_at_face_level
  - prop:memory_card held_by:mi_ya location:between_two_fingers_at_face_level
  - prop:work_id held_by:gu_yan location:in_right_hand_above_table
  - light_main direction:overhead_cabin_lamp color_temp:3200K ratio:1:8
  - action_phase:prepare
  - environment:tunnel_inside_window_black
接入状态键：[M] <same>

## Shot scene_003-5 | 9s

叙事职责：[D] 交换落定：出隧道的回光铺上桌面，工作证翻扣、存储卡入正中央——两只手在同一画面完成各让一步。
剧本事实：[D] L38——列车驶出隧道；顾言把自己的工作证翻面扣在桌上，米娅才把存储卡放到桌面中央。
原文定位：[M] scene_003 L38-L38
生成单元：[M] 一个独立 SD2.0 视频段，时长从 0 秒到 9 秒。
场景表达：[M] <investigation_object>
时间控制：[M] <event_nodes>

摄影设计：[D] 桌面东缘俯角特写位，固定基座随车体微晃，视轴向西下俯约六十度；60mm；覆盖整张窄桌桌面；无操作性运动。
构图设计：[D] 窄桌桌面充满画面：画面右侧为顾言一方、左侧为米娅一方；顶灯光池居中；顾言的手自画面右上入，米娅的手自画面左下入；卡与证的终点分居中央与中央偏右，物件位置构成对等图形。
光影设计：[D] 顶灯光池打底，色温3200K；出隧道瞬间窗侧回光扫入，流动光带开始在桌面上掠过，光比自1:8放宽到1:4；此后光带持续流动。
表演设计：[D] 手部表演：顾言的手匀速下落，手腕翻转让证件印刷面朝下扣上桌面，掌心压平一次后撤离；米娅两指携卡入画，把卡端正放在桌面正中央，指尖停半拍再松开撤回。

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无

视觉时间线：[D] [0.0s][SB] 俯角桌面特写：窄桌木面与固定杯槽，顶灯光池居中，画面右上缘顾言的手捏着工作证悬停，四周沉在隧道黑暗里。
  [1.0s] 窗侧回光扫入——列车驶出隧道，一道道流动光带开始掠过桌面，画面整体转亮。
  [2.5s] 顾言的手匀速下落，手腕翻转，工作证印刷面朝下扣在桌面中央偏右，掌心压平一次。
  [4.0s][SB] 手指撤离出画，工作证翻扣静止，空白背面朝上。
  [5.5s] 画面左下缘米娅的两指携存储卡入画，向桌面正中央推进。
  [7.0s][SB] 存储卡被端正放在桌面正中央，两指停半拍后松开撤回出画。
  [9.0s][SB] 定格：翻扣的工作证与正中央的存储卡同在流动光带里，桌面再无手。
声音设计：[D] 1.0 秒风压声变薄、轨缝节拍转亮；2.5 秒证件翻扣闷响；7.0 秒存储卡与桌面轻磕；无对白。

## Boundary scene_003-B5 | scene_003-5 -> scene_003-6

边界关系：[M] <continuous>
转场执行：[M] <post_production>
剪辑触发：[D] 双手撤回、桌面两物静止的一拍切出，退回双人确认交易。
交接描述：[D] 出隧道后的亮态：存储卡在桌面正中央、工作证翻扣中央偏右，两人双手收回坐姿；该状态为前镜结束帧与后镜 0 秒画面共用。
交出状态键：[M]
  - character:gu_yan position:train_compartment|table_north_seat|seated facing:south screen_direction:static posture:seated_hands_withdrawn_to_table_edge
  - character:mi_ya position:train_compartment|table_south_seat|seated facing:north screen_direction:static posture:seated_hands_withdrawn_to_table_edge
  - prop:memory_card held_by:none location:table_center
  - prop:work_id held_by:none location:table_center_right_face_down
  - light_main direction:overhead_cabin_lamp color_temp:3200K ratio:1:4
  - action_phase:static
  - environment:train_moving_open_night_city_lights_streaking
接入状态键：[M] <same>

## Shot scene_003-6 | 10s

叙事职责：[D] 对等达成的视觉宣告：轴向对称双人静帧，卡在两人正中间，流动灯光恢复——交易成立，各自归位。
剧本事实：[D] L38 之后的场面结果：交换完成后的对坐状态。
原文定位：[M] scene_003 L38-L38
生成单元：[M] 一个独立 SD2.0 视频段，时长从 0 秒到 10 秒。
场景表达：[M] <conversation_power>
时间控制：[M] <event_nodes>

摄影设计：[D] 桌轴东端略俯对称机位，比水平位抬高四十厘米俯视桌面与两人；32mm；机身低频微晃；无操作性运动。
构图设计：[D] 对称构图：顾言居画面右、米娅居画面左，两张四分之三侧脸左右均衡；窄桌自画面下缘中央伸向背景车窗；存储卡在画面下部正中，工作证翻扣其右；背景窗面流动光带自右向左。
光影设计：[D] 顶灯弱暖光加窗外流动冷光，色温3200K，光比1:4；光带周期性掠过两张侧脸与桌面；全镜节奏恒定。
表演设计：[D] 两人同时靠回椅背，肩线下沉；视线各自从桌面中央的卡抬起，在画面中线相接一次，随后各自转向窗面；呼吸放缓，双手静置。

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无

视觉时间线：[D] [0.0s][SB] 桌轴东端略俯对称双人构图：顾言居右、米娅居左，四分之三侧脸相对；存储卡在画面下部桌面正中，工作证翻扣其右；背景车窗流动光带自右向左掠过。
  [2.5s] 两人同时靠回椅背，肩线沉下，双手收回身前。
  [5.0s][SB] 两人的视线从桌面中央的卡同时抬起，在画面中线相接一次。
  [7.5s] 一串灯点扫过窗面，亮斑先后滑过两张侧脸，两人各自转向窗面。
  [10.0s][SB] 定格：对称双人静坐，存储卡在两人之间的桌面正中央，工作证翻扣一旁，窗外灯光持续流动。
声音设计：[D] 开阔的轨缝节拍与车体低频吱响贯穿；无对白；镜末保持行车底噪静场。

## Boundary scene_003-B6 | scene_003-6 -> SCENE_EXIT

边界关系：[M] <scene_exit>
转场执行：[M] <post_production>
剪辑触发：[D] 静帧保持两秒后切出，本场结束。
交接描述：[D] 交出终局画面：对称双人静坐，存储卡在桌面正中央、工作证翻扣一旁，窗外灯光流动，行车底噪延续。后期在切点前零点五秒引入雨声作声音桥，硬切进入雨夜停车楼（静转动）。
交出状态键：[M]
  - character:gu_yan position:train_compartment|table_north_seat|seated facing:south screen_direction:static posture:seated_back_against_seat
  - character:mi_ya position:train_compartment|table_south_seat|seated facing:north screen_direction:static posture:seated_back_against_seat
  - prop:memory_card held_by:none location:table_center
  - prop:work_id held_by:none location:table_center_right_face_down
  - light_main direction:overhead_cabin_lamp color_temp:3200K ratio:1:4
  - action_phase:static
