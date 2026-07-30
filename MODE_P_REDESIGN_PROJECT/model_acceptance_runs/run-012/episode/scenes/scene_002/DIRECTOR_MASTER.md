# DIRECTOR_MASTER — scene_002（老旧厨房，清晨，室内）

## 0. 版本

```text
Master 版本：scene_002/v1.0
```

## 1. 场景设计

```text
场景前状态：独立情境，无跨场继承。清晨老旧厨房：周岚站在水槽旁，周成坐在小餐桌前，桌上放着一封已拆开的信，炉灶上水壶冒着蒸汽。
戏剧变化：沉默的承认与交接。周岚说出「你早就知道她还活着」；周成以沉默完成承认，用一把储物柜钥匙代替解释；周岚拿起钥匙、把信留在桌上——接下寻找，留下旧物。
信息策略：观众与周岚同步知情。信面文字全场保持折叠向上无字迹可见，「她」全场只存在于对白；周成的承认仅由两个可见行为成立：看着蒸汽的沉默、推出钥匙。钥匙是本场唯一移动的小物，视觉权重全部让给它。
场景后状态：钥匙在周岚握紧的手中，信留在桌面中央，周成坐回桌前低头。静帧收束，硬切进入下一场夜景（后期，亮转暗）。

场景空间：老旧厨房。东墙窗下是水槽，低角度晨光自东窗射入；小餐桌在窗西侧约两米，周成坐桌西端座椅面向东；炉灶在北墙、紧邻餐桌一步之内，水壶在灶上；信平放桌面中央。周岚立于水槽旁窗光中。
关系线：东西纵深轴：东窗—水槽—餐桌。周岚在东端高位（站姿），周成在西端低位（坐姿）。全部机位在轴南侧，晨光恒定为画面右侧来光；周岚恒定占画面右／后景并视线向左，周成恒定占画面左／中景并视线向右。
人物路径：周岚：水槽旁站立 → 场末走到餐桌东端取钥匙。周成：坐姿 → 起身一步关火 → 坐回 → 推出钥匙。钥匙路径：周成开衫口袋 → 握拳落桌西沿 → 推过桌面停在桌东区 → 周岚手中。
摄影可用区域：轴南侧半区：西南角纵深全景位（可沿轴向北缓推二十厘米）、水槽南侧的周岚中景位、餐桌南侧的周成中近景位、桌面南缘俯角特写位、餐桌东南收束中景位。除全景位缓推外全部固定。

视觉策略：全片最低光比与最暖色调；晨光把蒸汽照成体积，柔化一切边缘。前段两人互不同框对视——周岚望着周成的背与侧脸，周成望着蒸汽；钥匙推出是两只手唯一一次进入同一画面。全场唯一光变化是关火：炉焰在水壶与周成侧面上的暖反光熄灭。节奏缓慢，停顿长于台词。
镜头拆分理由：头部转向完成处切入周岚的质问单人；话音落在无回答的静默上，切到周成与蒸汽；握钥匙的拳落上桌沿后切入桌面特写完成交接；周岚指尖停在钥匙旁的悬停一拍切出到全身，让拿起钥匙的决定在带着周成背景的画面里完成。
场间关系：自上一场夜景静帧硬切进入（冷转暖，后期）；终镜静帧硬切离场（亮转暗，后期），无声音桥。

场景蓝图：[D] 清晨，老旧厨房。东窗低角度暖晨光，水槽旁立着周岚（女，30岁上下，薄外套便装）；小餐桌前坐着她的父亲周成（男，60岁上下，旧开衫毛衣）。桌面中央一封已拆开的信（信纸折面向上，无字迹可见），炉灶上水壶冒蒸汽。本场变化：一把黄铜储物柜钥匙从父亲口袋经桌面到女儿手中，信留在原处。
声音基调：[D] 清晨底噪：水壶沸腾声由细密渐强至鸣叫，关火后归于水槽滴水与老屋木质轻响；对白稀少、置于长停顿之间；钥匙与木桌面的刮擦声是本场最重要的音效。
```

## 2. 共享 Boundary

本场 5 个 Shot，共 6 个共享 Boundary（B0-B5），与 Shot 交错书写于下方序列：B0 -> Shot 1 -> B1 -> Shot 2 -> B2 -> Shot 3 -> B3 -> Shot 4 -> B4 -> Shot 5 -> B5。

## 3. Shot Contract

## Boundary scene_002-B0 | SCENE_ENTRY -> scene_002-1

边界关系：[M] <scene_entry>
转场执行：[M] <post_production>
剪辑触发：[D] 自上一场夜景静帧硬切，第一帧落在暖晨光的厨房纵深全景上。
交接描述：[D] 0 秒画面：晨光斜射的老旧厨房，前景桌面中央放着拆开的信，中景周成坐在桌西端，背景周岚立在水槽旁面向东窗；炉灶上水壶蒸汽升入窗光。声音自水壶细密沸腾声与滴水底噪冷起。
接入状态键：[M]
  - character:zhou_lan position:kitchen|sink_east_window|standing facing:east screen_direction:static posture:standing_hands_on_sink_edge wardrobe:light_jacket_casual
  - character:zhou_cheng position:kitchen|table_west_seat|seated facing:east screen_direction:static posture:seated_forearms_on_table_eyes_down wardrobe:old_cardigan_sweater
  - prop:opened_letter held_by:none location:table_center
  - prop:locker_key held_by:zhou_cheng location:cardigan_pocket
  - prop:kettle held_by:none location:stove_north_burner_steaming
  - light_main direction:east_window_low_dawn color_temp:3000K ratio:1:2
  - action_phase:static
  - story_time:early_morning
  - environment:old_kitchen_steam_in_window_light

## Shot scene_002-1 | 12s

叙事职责：[D] 建立空间与三角关系：信在前景、父亲在中景、女儿在窗光里，沉默先于一切话语。
剧本事实：[D] L17——周岚站在水槽旁，父亲周成坐在小餐桌前；桌上放着一封已经拆开的信。
原文定位：[M] scene_002 L17-L17
生成单元：[M] 一个独立 SD2.0 视频段，时长从 0 秒到 12 秒。
场景表达：[M] <contemplative_silence>
时间控制：[M] <event_nodes>

摄影设计：[D] 西南角纵深全景位，视轴向东北，高度与桌面齐平略高；32mm；全镜做一次二十厘米匀速缓推，起止构图均稳定。
构图设计：[D] 纵深三层：前景桌面中央的信占画面左下，中景周成侧坐居左，背景周岚立于画面右侧窗光中；蒸汽柱在右上窗光里升起；窗外过曝成柔白负空间。
光影设计：[D] 东窗低角度晨光为唯一主光，色温3000K，光比1:2；蒸汽接光成体积；炉灶蓝色小火苗在水壶底沿留一线反光；全镜光线恒定。
表演设计：[D] 周成低头静坐，前臂搭桌，拇指缓慢摩挲另一只手背；周岚背对房间望着窗外，双手扶住水槽沿，肩线随呼吸缓慢起伏；镜末她的手指收紧、头部转向周成。

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无

视觉时间线：[D] [0.0s][SB] 清晨老旧厨房纵深全景：东窗低角度暖晨光斜射，前景桌面中央平放一封拆开的信，中景周成穿旧开衫坐在桌西端低头静坐，背景周岚穿薄外套立在水槽旁面向窗外，炉灶上水壶蒸汽升入窗光。画面在极缓推近中。
  [3.0s] 蒸汽柱变浓，缓慢穿过窗光，窗外亮部微微晃动。
  [6.0s] 周岚扶在水槽沿的手指收紧，指节抵住陶瓷边。
  [9.0s][SB] 周岚的头从窗外转向周成方向，侧脸进入晨光，视线落在他背上。
  [12.0s][SB] 定格：周岚侧脸望向周成，周成保持低头，信在前景桌面中央，蒸汽持续上升。
声音设计：[D] 水壶细密沸腾声与水槽滴水底噪贯穿；老屋木质偶发轻响；无对白，无音乐。

## Boundary scene_002-B1 | scene_002-1 -> scene_002-2

边界关系：[M] <continuous>
转场执行：[M] <post_production>
剪辑触发：[D] 周岚头部转向完成、视线落定在周成身上的静止一拍切出。
交接描述：[D] 周岚立于水槽旁、侧脸转向周成，周成低头静坐，信与水壶状态未变；该状态为前镜结束帧与后镜 0 秒画面共用。
交出状态键：[M]
  - character:zhou_lan position:kitchen|sink_east_window|standing facing:west screen_direction:static posture:standing_head_turned_toward_father
  - character:zhou_cheng position:kitchen|table_west_seat|seated facing:east screen_direction:static posture:seated_forearms_on_table_eyes_down
  - prop:opened_letter held_by:none location:table_center
  - prop:locker_key held_by:zhou_cheng location:cardigan_pocket
  - prop:kettle held_by:none location:stove_north_burner_steaming
  - light_main direction:east_window_low_dawn color_temp:3000K ratio:1:2
  - action_phase:static
接入状态键：[M] <same>

## Shot scene_002-2 | 8s

叙事职责：[D] 质问出口：女儿说出全场唯一的指控句，逆光站位让这句话带着窗光的重量压向父亲。
剧本事实：[D] L19——周岚：「你早就知道她还活着。」
原文定位：[M] scene_002 L19-L19
生成单元：[M] 一个独立 SD2.0 视频段，时长从 0 秒到 8 秒。
场景表达：[M] <conversation_power>
时间控制：[M] <event_nodes>

摄影设计：[D] 水槽南侧固定机位，视轴向北偏东，与周岚视线齐平；50mm 中景；无运动。
构图设计：[D] 周岚居画面右侧，身后东窗在画面右缘过曝成柔白，轮廓光勾出发丝与肩线；画面左侧留出她视线方向的负空间，指向画外的周成；蒸汽边缘从右上飘入。
光影设计：[D] 东窗逆光为主，面部由室内反射光补起，色温3000K，光比1:2；发丝与肩线带亮边；全镜光线恒定。
表演设计：[D] 开口前喉部先动一次咽下；说话音量低、语速慢，每个字落地；说完嘴唇合拢，视线持续压在画外周成方向，身体保持扶槽站姿。

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无

视觉时间线：[D] [0.0s][SB] 周岚中景：她立于水槽旁，身后东窗过曝成柔白，轮廓光勾出发丝与肩线，侧身面向画面左侧，视线投向画外的周成；一缕蒸汽边缘从画面右上飘入。
  [1.5s] 她的喉部滚动一次，嘴唇张开。
  [2.0s] 周岚开口说话，音量低，字距拉开，视线钉住画外。
  [5.0s][SB] 话音落，嘴唇合拢，视线保持原处，胸口一次深呼吸。
  [8.0s][SB] 静帧：周岚逆光站姿静止，窗光里蒸汽缓慢飘动。
声音设计：[D] 底噪延续，水壶沸腾声比前镜略强；2.0-4.5 秒对白（周岚）：「你早就知道她还活着。」干声近距；话音落后静场，只余沸腾声继续攀升。

## Boundary scene_002-B2 | scene_002-2 -> scene_002-3

边界关系：[M] <continuous>
转场执行：[M] <post_production>
剪辑触发：[D] 话音落进无人应答的静默、沸腾声继续攀升的一拍切出，落到被质问的父亲身上。
交接描述：[D] 周岚保持逆光站姿，周成仍低头坐在桌前，水壶沸腾声渐强逼近鸣叫；该状态为前镜结束帧与后镜 0 秒画面共用。
交出状态键：[M]
  - character:zhou_lan position:kitchen|sink_east_window|standing facing:west screen_direction:static posture:standing_gaze_on_father
  - character:zhou_cheng position:kitchen|table_west_seat|seated facing:east screen_direction:static posture:seated_forearms_on_table_eyes_down
  - prop:opened_letter held_by:none location:table_center
  - prop:locker_key held_by:zhou_cheng location:cardigan_pocket
  - prop:kettle held_by:none location:stove_north_burner_near_boiling
  - light_main direction:east_window_low_dawn color_temp:3000K ratio:1:2
  - action_phase:static
接入状态键：[M] <same>

## Shot scene_002-3 | 13s

叙事职责：[D] 沉默的承认：父亲以看蒸汽代替回答，水壶鸣叫替他喊出压力；关火与取钥匙把回答变成行动。
剧本事实：[D] L21——周成看着水壶冒出的蒸汽，没有回答；水壶鸣叫后，他关掉火。
原文定位：[M] scene_002 L21-L21
生成单元：[M] 一个独立 SD2.0 视频段，时长从 0 秒到 13 秒。
场景表达：[M] <conversation_power>
时间控制：[M] <event_nodes>

摄影设计：[D] 餐桌南侧固定机位，视轴向北，与周成坐姿视线齐平；50mm 中近景，画面同时收入他与背景炉灶上的水壶；无运动。
构图设计：[D] 周成占画面左侧，四分之三侧脸朝向画面右；背景右上是炉灶与冒汽的水壶，蒸汽接窗光；画面右侧负空间由蒸汽与窗光填充，他的视线落在水壶上。
光影设计：[D] 东窗晨光自画面右侧入，色温3000K，光比1:2；炉灶火苗在水壶底沿与周成侧脸下缘留一线暖反光；关火瞬间该反光熄灭——本场唯一光变化。
表演设计：[D] 周成抬眼望向水壶，喉部滚动，嘴唇闭紧；鸣叫响起后他撑桌起身，一步到灶前拧阀，动作缓慢无迟滞；坐回时右手先入开衫口袋，出来时已握成拳，拳背落在桌沿。

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无

视觉时间线：[D] [0.0s][SB] 周成中近景：他坐在桌西端，四分之三侧脸朝画面右，视线抬起落在背景炉灶冒汽的水壶上，晨光自右侧照亮半脸，火苗反光在侧脸下缘微微跳动；嘴唇闭紧。
  [2.5s] 水壶鸣叫声响起，音调由细转尖；周成的视线停在蒸汽上，睫毛低垂一次。
  [4.5s] 他双手撑桌，缓慢起身，椅腿在地面刮出一声。
  [6.0s][SB] 他站到灶前拧下燃气阀：火苗熄灭，鸣叫塌落成嘶声再归于寂静，蒸汽柱开始下沉，他侧脸上的暖反光消失。
  [8.0s] 他转身坐回椅子，坐定后右手探入开衫口袋。
  [10.0s][SB] 右手从口袋出来握成拳，拳背轻落在桌西沿，停住。
  [13.0s][SB] 定格：周成低头坐在桌前，握拳的手抵在桌沿，身后水壶蒸汽散尽，厨房重归滴水底噪。
声音设计：[D] 沸腾声在 2.5 秒升为尖锐鸣叫并持续；6.0 秒拧阀轻响后鸣叫塌落归寂；4.5 秒椅腿刮地声；10.0 秒拳落桌沿的轻叩；无对白。

## Boundary scene_002-B3 | scene_002-3 -> scene_002-4

边界关系：[M] <continuous>
转场执行：[M] <post_production>
剪辑触发：[D] 握钥匙的拳落上桌沿、轻叩声落定的瞬间切出，落到桌面。
交接描述：[D] 周成坐回桌前、握拳抵在桌西沿，钥匙在拳中；水壶已关、蒸汽散尽；周岚仍立于水槽旁注视。该状态为前镜结束帧与后镜 0 秒俯角特写共用。
交出状态键：[M]
  - character:zhou_lan position:kitchen|sink_east_window|standing facing:west screen_direction:static posture:standing_gaze_on_father
  - character:zhou_cheng position:kitchen|table_west_seat|seated facing:east screen_direction:static posture:seated_fist_on_table_west_edge
  - prop:opened_letter held_by:none location:table_center
  - prop:locker_key held_by:zhou_cheng location:inside_right_fist_on_table_west_edge
  - prop:kettle held_by:none location:stove_north_burner_off_silent
  - light_main direction:east_window_low_dawn color_temp:3000K ratio:1:2
  - action_phase:prepare
接入状态键：[M] <same>

## Shot scene_002-4 | 10s

叙事职责：[D] 桌面交接：钥匙从父亲拳中推过桌面，台词在物件行进后落下；女儿的指尖抵达钥匙旁——两只手唯一一次同框。
剧本事实：[D] L21-L22——他把一把储物柜钥匙推向周岚；L24——周成：「信里没有地址。钥匙会带你找到她留下的东西。」
原文定位：[M] scene_002 L21-L24
生成单元：[M] 一个独立 SD2.0 视频段，时长从 0 秒到 10 秒。
场景表达：[M] <investigation_object>
时间控制：[M] <event_nodes>

摄影设计：[D] 桌面南缘俯角特写位，固定，视轴向北下俯约六十度；60mm；覆盖桌面自西沿到东区的横条带；无运动。
构图设计：[D] 木质桌面纹理横贯画面：左侧是周成布满皱纹的拳，右上角入画信的一角（信纸折面向上，无字迹可见）；钥匙行进路线自左向右穿过画面中带，晨光自画面右上打来，钥匙投出细长影子。
光影设计：[D] 东窗晨光低角度掠过桌面，色温3000K，光比1:2；木纹与黄铜钥匙的高光清晰；全镜光线恒定。
表演设计：[D] 拳翻转摊开的速度极慢，掌心先停一拍再推；食指与中指压住钥匙匀速推行，到位后手指松开、手缓慢撤回出画；周岚的脚步声两下由远及近，指尖入画后悬停在钥匙旁一指宽处。

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无

视觉时间线：[D] [0.0s][SB] 俯角桌面特写：木纹横贯，画面左侧周成的右拳扣在桌西沿，右上角入画信的一角，晨光自右上掠过桌面。
  [1.5s] 拳缓慢翻转摊开，掌心里躺着一把黄铜储物柜钥匙。
  [3.0s] 食指与中指压住钥匙，沿木纹向画面右侧匀速推行，金属与木面刮出连续轻响。
  [4.5s][SB] 钥匙停在桌面东区、信旁一掌宽处；周成的手松开钥匙，缓慢撤回出画。
  [5.5s] 画外周成开口说话，声音低而平。
  [8.3s] 话音落；木地板上传来两声渐近的脚步。
  [9.3s] 周岚的指尖自画面右缘入画，停在钥匙旁一指宽处，悬停。
  [10.0s][SB] 定格：指尖悬在钥匙旁，钥匙与信同在晨光里，桌面再无运动。
声音设计：[D] 滴水底噪；3.0-4.5 秒钥匙刮过木面的连续轻响；5.5-8.3 秒对白（周成，画外）：「信里没有地址。钥匙会带你找到她留下的东西。」；8.6 秒起两声脚步渐近；镜末静场。

## Boundary scene_002-B4 | scene_002-4 -> scene_002-5

边界关系：[M] <continuous>
转场执行：[M] <post_production>
剪辑触发：[D] 指尖在钥匙旁悬停的一拍切出，把拿起的决定交给全身画面。
交接描述：[D] 周岚已立于餐桌东端，指尖悬在桌面钥匙旁；周成坐在西端，双手回到桌沿；信在桌面中央。该状态为前镜结束帧与后镜 0 秒画面共用。
交出状态键：[M]
  - character:zhou_lan position:kitchen|table_east_end|standing facing:west screen_direction:static posture:standing_fingertips_above_key
  - character:zhou_cheng position:kitchen|table_west_seat|seated facing:east screen_direction:static posture:seated_hands_folded_on_table_edge
  - prop:opened_letter held_by:none location:table_center
  - prop:locker_key held_by:none location:table_east_area_beside_letter
  - prop:kettle held_by:none location:stove_north_burner_off_silent
  - light_main direction:east_window_low_dawn color_temp:3000K ratio:1:2
  - action_phase:static
接入状态键：[M] <same>

## Shot scene_002-5 | 10s

叙事职责：[D] 决定与收束：周岚当着父亲拿起钥匙、留下信；父女与两件物的最终关系在一个画面里静帧定案。
剧本事实：[D] L26——周岚拿起钥匙，仍把信留在桌上。
原文定位：[M] scene_002 L26-L26
生成单元：[M] 一个独立 SD2.0 视频段，时长从 0 秒到 10 秒。
场景表达：[M] <conversation_power>
时间控制：[M] <event_nodes>

摄影设计：[D] 餐桌东南收束中景位，固定，视轴向西北，高度在周岚肩下；40mm 中景带全桌；无运动。
构图设计：[D] 周岚站姿居画面右前，占画高于坐着的周成；周成居画面左后中景低位；信在两人之间的桌面中央，钥匙在画面右下桌东区；东窗光自画面右缘入，铺过桌面。
光影设计：[D] 东窗晨光自右侧低角度入画，色温3000K，光比1:2；周岚半身亮、周成半身处于柔和暗部；全镜光线恒定。
表演设计：[D] 指尖合拢捏起钥匙，动作干脆；钥匙在指间翻转一次后握入掌心成拳垂于身侧；她低头看一眼桌面中央的信，随后抬眼望向窗光方向；周成全程低头，双手叠放，肩线一次缓慢起伏。

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无

视觉时间线：[D] [0.0s][SB] 餐桌中景：周岚站在桌东端居画面右前，指尖悬在桌面钥匙上方；周成坐在桌西端居画面左后低位，双手叠放低头；信平放两人之间的桌面中央，晨光自右铺过桌面。
  [2.0s] 周岚指尖合拢捏起钥匙，提离桌面。
  [4.0s][SB] 钥匙在她指间翻转一次，被握入掌心成拳，垂落身侧。
  [6.5s] 她低头看一眼桌面中央的信，随后抬眼望向画面右侧窗光方向；周成保持低头。
  [10.0s][SB] 定格：周岚握钥匙立于桌旁，信仍在桌面中央，周成坐在原位低头，背景炉灶上的水壶安静无汽。
声音设计：[D] 滴水与老屋木质轻响底噪；2.0 秒钥匙离开桌面的轻响；4.0 秒掌心合拢的闷声；无对白；镜末静场收束。

## Boundary scene_002-B5 | scene_002-5 -> SCENE_EXIT

边界关系：[M] <scene_exit>
转场执行：[M] <post_production>
剪辑触发：[D] 静帧保持两秒后切出，本场结束。
交接描述：[D] 交出终局画面：周岚握钥匙立于桌旁望向窗光，信留在桌面中央，周成低头坐在原位，厨房只余滴水底噪。下一场以夜行列车包厢独立开场，硬切（后期，亮转暗）。
交出状态键：[M]
  - character:zhou_lan position:kitchen|table_east_end|standing facing:east screen_direction:static posture:standing_key_in_closed_fist_at_side
  - character:zhou_cheng position:kitchen|table_west_seat|seated facing:east screen_direction:static posture:seated_hands_folded_eyes_down
  - prop:opened_letter held_by:none location:table_center
  - prop:locker_key held_by:zhou_lan location:inside_closed_fist_at_side
  - prop:kettle held_by:none location:stove_north_burner_off_silent
  - light_main direction:east_window_low_dawn color_temp:3000K ratio:1:2
  - action_phase:static
