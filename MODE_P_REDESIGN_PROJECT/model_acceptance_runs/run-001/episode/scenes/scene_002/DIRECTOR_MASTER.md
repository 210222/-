<!-- template: director_master v2.0 -->

# DIRECTOR_MASTER.md — 场景 2

> 本文件是场景唯一设计源。所有修订必须先修改本文件，再从本文件派生 `STORYBOARD.md` 和 `VIDEO_PROMPT.md`。
> 本模板遵循 LOOP_SPEC v2.1 第 9、10 节。

---

## 0. 版本信息

```text
Master 版本：SCN2/v1.0
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
场景前状态：无前场继承。全新场景。观众不知人物关系和前史。
戏剧变化：周岚直接质问"你早就知道她还活着"——周成用钥匙而非语言回答。
          沉默本身是一个回答，钥匙则是一个选择：是否去追寻。
信息策略：观众与周岚信息同步——都看到信已拆封，都听到质问，都等到一把钥匙作为回应。
          信的内容未被告知观众（与周岚一致），钥匙指向未知地点。
场景后状态：周岚拿到了钥匙但留下信。她面临选择，但已向行动方向迈出一步。
```

### 1.2 空间调度

```text
场景空间：【inferred】老旧厨房约 4m x 5m。水槽位于左侧窗台下。灶台在水槽旁（含旧式水壶）。
          小餐桌靠近右侧墙壁，铺着旧桌布。一扇小窗在餐桌上方，透入清晨微光。
关系线：周岚站水槽旁，面朝右侧餐桌方向的周成。周成坐餐桌前，面向左侧周岚。
         两人视线方向在房间中部交叉，距离约 2.5m。
人物路径：周岚开场已站在水槽旁，无入场。周成已坐在桌旁。
         周成在关火时起身（短程——从餐桌走到灶台再返回），推钥匙时已坐回。
         周岚从水槽旁走到餐桌处取钥匙，然后停下。
摄影可用区域：水槽一侧（拍周成），餐桌一侧（拍周岚），房间中部（双人镜），
             厨房门口处（广角建立镜）。灶台附近（拍水壶动作）。
```

### 1.3 视觉策略

```text
视觉强度：低（开场静默）→ 中（水壶鸣叫、对话、推钥匙）→ 低（末镜静默）。
色彩策略：主色调暖琥珀色（老旧厨房的黄色墙壁、晨光），蒸汽白，深棕木色家具。
光比策略：整体 2:1 柔和对比。清晨窗光从左侧窗射入（主光），灶台火为补充暖光。
稳定性策略：全固定。三脚架。镜内运动仅限于人物动作（周成起身/坐下，周岚走动）。
节奏曲线：6s → 8s → 5s。第二镜最长，容纳从水壶鸣叫到推钥匙的整条动作链。
```

### 1.4 镜头拆分理由

```text
三镜拆分：建立空间与沉默（双人宽镜）→ 动作与真相（中景，周成）→ 决定（中景，周岚）。
中间镜覆盖了从水壶鸣叫到推钥匙的全过程——这是本场最复杂的动作链，需要一个足够长的镜头承载。
首末镜让观众感受沉默的张力前后对称。
```

### 1.5 全场转场策略

```text
入场方式：从厨房空间宽景开始——清晨窗外微光，蒸汽缓缓上升，建立时间与氛围。
出场方式：末镜结束于周岚拿起钥匙停住——选择已做出，但去向未知。
场间关系：独立场景。前场（审讯室）的冷绿灰与末镜定格，硬切至暖琥珀色的清晨厨房。
```

### 1.6 双视图共享上下文

```text
场景蓝图：[D] 老旧厨房，清晨。窗外透入柔和晨光。水槽在左侧，灶台上水壶微微冒蒸汽。
          小餐桌在右侧，椅上周成坐。桌上一封已拆的信。周岚站在水槽旁面朝周成。
声音基调：[D] 清晨的安静——远处偶有鸟鸣。水壶的微弱嘶声逐渐升高。灶台火的低响。
          周岚开场对白打破沉默。水壶鸣叫是环境中的关键声音事件。
```

---

## 2. 逐镜 Shot Contract

### 2.1 叙事与溯源 `[M: ID, duration; D: 叙事文本]`

## Shot SCN2-1 | 6s

叙事职责：[D] 建立厨房空间、人物位置和初始沉默——周岚站、周成坐、信在桌上，以及周岚打破沉默的质问。
剧本事实：[D] 周岚站在水槽旁，父亲周成坐在小餐桌前。桌上放着一封已经拆开的信。
原文定位：[M] SCN2 L15-L27
场景表达：[M] <conversation_power>
时间控制：[M] <event_nodes>

### 2.2 状态键 `[M: 键名字面量]`

开场状态：[D] 清晨，老旧厨房。窗光透过小窗。周岚站于水槽旁，身体微侧向周成方向。周成坐于小餐桌前。桌上一封已拆信。水壶在灶台上开始冒出细蒸汽。
开场状态键：[M]
- character:zhou_lan position:sink_west facing:east screen_direction:static posture:standing_turned
- character:zhou_cheng position:table_east facing:west screen_direction:static posture:seated_forward
- prop:letter held_by:none location:table_top
- prop:kettle held_by:none location:stove
- light_main direction:window_west color_temp:3200K ratio:1:2
- action_phase:static

动作时间轴：[D]
[0.0s] 清晨厨房。周岚站在水槽旁，面朝周成。周成坐在餐桌前，看水壶蒸汽。蒸汽在光中可见。
[1.5s] 周岚：你早就知道她还活着。
[3.0s] 周成没有回答。他持续看着水壶蒸汽的方向。蒸汽的嘶声轻微增大。
[6.0s] 水壶鸣叫即将开始。周成未移开目光。

结束状态：[D] 清晨厨房。周岚已问出问题。周成以沉默回应，仍在看水壶蒸汽。水壶的嘶声已升高至即将鸣叫。
结束状态键：[M]
- character:zhou_lan position:sink_west facing:east screen_direction:static posture:standing_turned
- character:zhou_cheng position:table_east facing:west screen_direction:static posture:seated_forward
- prop:letter held_by:none location:table_top
- prop:kettle held_by:none location:stove
- light_main direction:window_west color_temp:3200K ratio:1:2
- action_phase:prepare

### 2.3 摄影与构图 `[D: 自然语言]`

摄影设计：[D] 广角建立镜。从厨房门口区域拍摄，包含水槽、灶台、餐桌和两人。焦段 28mm。镜头固定，让清晨阳光中的蒸汽、人物位置和空间关系一次性建立。景深足够使全空间清晰。
构图设计：[D] 画面从左到右分为三个区域：左区水槽（周岚站立），中区灶台水壶（蒸汽上升），右区餐桌（周成坐着，信在桌上）。三人物的空间关系形成从站到坐、从西到东的水平布局。蒸汽在中区的上升路径连接两侧，暗示未出口的话语。
光影设计：[D] 清晨窗光从左侧射入（主光），暖色 3200K。光在蒸汽中形成可见的光束效果。灶台火焰提供辅助暖光。光比柔和约 2:1。周岚站在窗光中受光更充分，周成面向光源但处于更远处，亮度稍低。
表演设计：[D] 周岚的站姿有一个明确的朝向：身体微向右转，视线从水槽方向望向周成方向，态度直接。周成则以完全的静态回应——不看周岚，而是凝视水壶蒸汽。不看人本身就是一种回避回答的姿态。

### 2.4 边界 `[M: ID 配对; D: 自然语言]`

进入边界 ID：[M] SCENE_ENTRY
进入边界：[D] 无前镜。场景直接以厨房建立镜头开场。观众与新人物、新空间同时接触。
剪辑触发：[D] 开场即切入。
交出边界 ID：[M] SCN2-2
交出边界：[D] 本镜结束时蒸汽嘶声已经升高，水壶即将鸣叫。下一镜从中景展示周成起身处理水壶——动作被声音触发。
边界连续性：[M] <continuous>
转场执行：[M] <post_production>

### 2.5 生成模式与参考 `[M: 模式值和职责枚举; D: 职责说明]`

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无

### 2.6 双视图源文本 `[D: 由 Director 在 Master 内一次写完]`

故事板关键帧：[D]
- [开场] 厨房全景：周岚站水槽旁，周成坐餐桌前，蒸汽从水壶升起，晨光从窗口射入。
- [关键变化] 周岚质问后，周成沉默看向蒸汽方向——蒸汽成为画面对话的替代。
- [结束] 蒸汽嘶声升高，水壶准备鸣叫，周成未动。

视频时间轴：[D]
[0.0s] 清晨厨房广角。晨光从左侧窗口射入。周岚站水槽旁微侧向餐桌。周成坐餐桌前看向水壶方向。信在桌上。水壶蒸汽上升。
[1.5s] 周岚：你早就知道她还活着。
[3.0s] 周成没有回答。他的目光持续看着蒸汽方向。蒸汽嘶声增大。
[6.0s] 蒸汽嘶声升到即将鸣叫的程度。周成仍未移开目光。画面保持在建立镜。

声音设计：[D] 清晨环境声——远处鸟鸣（在 0.0s 起，微弱）。水壶蒸汽嘶声（持续上升，0.0s 起从轻微到明显）。灶台火低响。周岚对白（1.5s-2.5s）。之后沉默继续，蒸汽嘶声升高。环境声床持续至结束。

---

## Shot SCN2-2 | 8s

叙事职责：[D] 展示周成的动作反应链——水壶鸣叫触发他关火、返回餐桌、推钥匙。这是他用行动替代语言的回答。
剧本事实：[D] 水壶鸣叫后，他关掉火，把一把储物柜钥匙推向周岚。
原文定位：[M] SCN2 L15-L27
场景表达：[M] <suspense_reveal>
时间控制：[M] <second_nodes>

### 2.2 状态键 `[M: 键名字面量]`

开场状态：[D] 周成坐于餐桌前，水壶在灶台上鸣叫，蒸汽剧烈上升。他把手伸向水壶方向准备起身。周岚站在水槽旁，目光跟随周成。
开场状态键：[M]
- character:zhou_cheng position:table_east facing:west screen_direction:static posture:seated_starting_rise
- character:zhou_lan position:sink_west facing:east screen_direction:static posture:standing_watching
- prop:kettle held_by:none location:stove state:whistling
- prop:key held_by:zhou_cheng location:zhou_cheng_pocket
- prop:letter held_by:none location:table_top
- light_main direction:window_west color_temp:3200K ratio:1:2
- action_phase:prepare

动作时间轴：[D]
[0.0s] 水壶鸣叫。周成从桌边站起，走向灶台。
[1.5s] 周成到灶台，伸手关火。水壶鸣叫停止，余汽嘶一声。
[3.0s] 周成停顿片刻，看了一下水壶，然后转身走回餐桌。
[4.5s] 周成重新坐下。他手伸进口袋，取出储物柜钥匙。
[5.5s] 周成将钥匙放在桌上，沿桌面推向周岚方向——推过信的位置。
[7.0s] 周成：信里没有地址。钥匙会带你找到她留下的东西。
[8.0s] 钥匙停在周岚一侧的桌面上。周成手收回。

结束状态：[D] 周成已坐回，钥匙停在靠近周岚一侧的桌面上。信仍在原位。周成对白已说完。
结束状态键：[M]
- character:zhou_cheng position:table_east facing:west screen_direction:static posture:seated_back
- character:zhou_lan position:sink_west facing:east screen_direction:static posture:standing_watching
- prop:key held_by:none location:table_near_zhoulan
- prop:letter held_by:none location:table_top
- prop:kettle held_by:none location:stove state:off
- light_main direction:window_west color_temp:3200K ratio:1:2
- action_phase:recover

### 2.3 摄影与构图 `[D: 自然语言]`

摄影设计：[D] 中景跟随周成的动作。机位在餐桌与灶台之间的侧面，可以捕捉周成从桌到灶台再返回的全程。焦段 35mm。镜头随着周成起身向右摇摄到灶台，然后随他返回向左摇回餐桌。摇摄速度平缓，匹配老人动作节奏。
构图设计：[D] 开场画框中周成起身打破之前的静态构图。在灶台处，画面以水壶和周成的侧面为主。返回餐桌后，桌面上的信和即将出现的钥匙成为视觉中心。推钥匙时，钥匙沿桌面运动的路径是构图中的主要视线引导。
光影设计：[D] 晨光从左侧窗持续射入，在周成走向灶台时他逆光，面部略显暗。返回餐桌时他重新面向窗光，面部变亮——与他从回避转向面对的戏剧动作同步。水壶蒸汽在晨光中形成可见的柔光散射。
表演设计：[D] 周成的动作节奏是本镜的关键——他走得不快不慢，关火的标准动作熟练（是做了很多年的家庭动作），取钥匙时的停顿透露出这是一个有意识的决定而不是随手动作。推钥匙时他的视线第一次转向周岚，这是全镜中他第一次看女儿。

### 2.4 边界 `[M: ID 配对; D: 自然语言]`

进入边界 ID：[M] SCN2-1
进入边界：[D] 上一镜结束于水壶嘶声升高到即将鸣叫。本镜以水壶鸣叫和周成起身为开始，动作被声音触发。
剪辑触发：[D] 水壶鸣叫的第一个音起切入——声音作为剪辑触发点。
交出边界 ID：[M] SCN2-3
交出边界：[D] 本镜结束时钥匙已推至桌面上靠近周岚的一侧，周成对白说完。下一镜从周岚的反应开始——她将走向桌子取钥匙。
边界连续性：[M] <continuous>
转场执行：[M] <post_production>

### 2.5 生成模式与参考 `[M: 模式值和职责枚举; D: 职责说明]`

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无

### 2.6 双视图源文本 `[D: 由 Director 在 Master 内一次写完]`

故事板关键帧：[D]
- [开场] 水壶鸣叫，周成从餐桌起身走向灶台，蒸汽在晨光中可见。
- [关键变化] 周成关火，转身回桌，手伸入口袋取钥匙（动作转折点）。
- [结束] 钥匙沿桌面被推向周岚方向，越过信的位置，停在她那一侧。

视频时间轴：[D]
[0.0s] 水壶鸣叫，尖锐的声音打破寂静。周成从餐桌边站起身，走向灶台。
[1.5s] 周成到达灶台，伸手旋转旋钮关火。鸣叫停止，最后一股汽嘶声。
[3.0s] 周成站定片刻，看了看水壶。然后转身走回餐桌。
[4.5s] 周成重新坐下。手伸入衣袋，取出金属钥匙。晨光在钥匙上反光。
[5.5s] 周成将钥匙放在桌上，用手沿桌面推向周岚方向——钥匙滑动越过信的位置。
[7.0s] 周成：信里没有地址。钥匙会带你找到她留下的东西。
[8.0s] 钥匙停在桌面靠近周岚一侧。周成手收回，画面停留。

声音设计：[D] 环境声床持续。水壶鸣叫（0.0s 起）——尖锐但老式金属哨音。关火声（1.5s）。水壶蒸汽余嘶（1.5s-2.0s）。脚步——木板地面（0.5s-1.5s, 3.0s-4.0s）。钥匙取出时金属碰撞声（4.5s-5.0s）。钥匙在桌面滑动的摩擦声（5.5s-6.0s）。周成对白（7.0s-7.8s）。环境恢复安静。

---

## Shot SCN2-3 | 5s

叙事职责：[D] 周岚的决定时刻——她走向桌边拿起钥匙，但把信留在桌上。用行动而非语言回应了父亲的回答。
剧本事实：[D] 周岚拿起钥匙，仍把信留在桌上。
原文定位：[M] SCN2 L15-L27
场景表达：[M] <contemplative_silence>
时间控制：[M] <event_nodes>

### 2.2 状态键 `[M: 键名字面量]`

开场状态：[D] 周岚仍站在水槽旁。钥匙停在桌面靠近她的一侧。信仍在原处。周成已坐回，手收回。
开场状态键：[M]
- character:zhou_lan position:sink_west facing:east screen_direction:static posture:standing_turned
- character:zhou_cheng position:table_east facing:west screen_direction:static posture:seated_back
- prop:key held_by:none location:table_near_zhoulan
- prop:letter held_by:none location:table_top
- light_main direction:window_west color_temp:3200K ratio:1:2
- action_phase:static

动作时间轴：[D]
[0.0s] 周岚站立片刻，看向桌上的钥匙。
[1.0s] 周岚从水槽旁迈步，走向餐桌。
[2.5s] 到达桌边，手伸向钥匙——短暂停顿，指尖触到钥匙。
[3.5s] 拿起钥匙，握在手中。没有看信。
[5.0s] 拿着钥匙站定。信留在桌上。

结束状态：[D] 周岚已拿起钥匙握在手里，站在餐桌旁。信留在桌上未被触碰。周成坐着。选择完成。
结束状态键：[M]
- character:zhou_lan position:table_west facing:east screen_direction:static posture:standing_by_table
- character:zhou_cheng position:table_east facing:west screen_direction:static posture:seated_back
- prop:key held_by:zhou_lan location:zhou_lan_hand
- prop:letter held_by:none location:table_top
- light_main direction:window_west color_temp:3200K ratio:1:2
- action_phase:static

### 2.3 摄影与构图 `[D: 自然语言]`

摄影设计：[D] 中景从餐桌侧面拍周岚走近桌子。焦段 35mm。镜头固定，周岚走入画框、完成动作、停住。画框包含桌面上信和钥匙的位置，以及周成在画面边缘的存在。
构图设计：[D] 开场画面预留左侧空间——周岚将从左侧入画。她走近后，画框以她和桌面上的物品为中心。钥匙和信在画面下方形成物品之间的对比：拿起的 vs 留下的。周成在画面右边缘的焦外——他已完成动作，退为背景。
光影设计：[D] 周岚走向餐桌时她从窗光中走入室内较暗区域，面部亮度降低，但手部触及桌面时钥匙在晨光中闪光。信处在桌面阴影一侧，视觉上被"冷落"。
表演设计：[D] 周岚的走近不是立即而是短暂的停顿后才行动——说明这个决定不是本能的而是有意识的。她的手触到钥匙时有一个微小停顿（约 0.5s），然后才拿起。拿起后她没有立即看周成，而是看着手中的钥匙——未来在她手上。不碰信是另一个有意识的选择：她接受线索但不接受过去。

### 2.4 边界 `[M: ID 配对; D: 自然语言]`

进入边界 ID：[M] SCN2-2
进入边界：[D] 上一镜结束于钥匙停在桌面靠近周岚一侧。本镜从周岚的反应开始——她站立片刻后决定走近桌子。
剪辑触发：[D] 在上一镜结束的后半秒静默中切入——观众等待周岚的反应，这个等待本身就是触发。
交出边界 ID：[M] SCENE_EXIT
交出边界：[D] 本镜结束于周岚拿起钥匙站定，信留在桌上。她有了线索但选择的方向未知。场景在此状态中结束，硬切至场景 3。
边界连续性：[M] <scene_exit>
转场执行：[M] <post_production>

### 2.5 生成模式与参考 `[M: 模式值和职责枚举; D: 职责说明]`

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无

### 2.6 双视图源文本 `[D: 由 Director 在 Master 内一次写完]`

故事板关键帧：[D]
- [开场] 周岚站水槽旁看向桌上钥匙，远处周成坐着。
- [关键变化] 周岚走近餐桌，手伸向钥匙，短暂停顿后拿起。
- [结束] 钥匙握在手中，信留在桌上。周岚拿着钥匙站立。

视频时间轴：[D]
[0.0s] 周岚站在原地看着桌上钥匙。窗外晨光照亮桌面局部。
[1.0s] 周岚迈步，从左向右走入餐桌区域。身影遮挡部分光线。
[2.5s] 到达桌边。手伸向金属钥匙——指尖触到钥匙表面。短暂停顿。
[3.5s] 拿起钥匙，握入掌心。
[5.0s] 拿着钥匙站定。信留在桌面未被触碰。画面凝固。

声音设计：[D] 清晨环境声持续——远处鸟鸣微弱。脚步声（1.0s-2.0s）——老旧木地板。钥匙拿起时与桌面的轻微金属摩擦（3.5s-4.0s）。之后安静，无对白。环境声床持续至结束，然后硬切至场景 3。

---

## 3. 机器可检查字段汇总

| 字段 | Shot 1 | Shot 2 | Shot 3 |
|---|---|---|---|
| Shot ID | SCN2-1 | SCN2-2 | SCN2-3 |
| duration | 6s | 8s | 5s |
| scene_expression | conversation_power | suspense_reveal | contemplative_silence |
| timing_mode | event_nodes | second_nodes | event_nodes |
| 原文定位 | SCN2 L17 | SCN2 L21-L22 | SCN2 L26 |
| 进入边界 ID | SCENE_ENTRY | SCN2-1 | SCN2-2 |
| 交出边界 ID | SCN2-2 | SCN2-3 | SCENE_EXIT |
| 边界连续性 | continuous | continuous | scene_exit |
| 转场执行 | post_production | post_production | post_production |
| 生成模式 | text_only | text_only | text_only |
| 参考资产 | 无 | 无 | 无 |

<!-- M: 所有 ID 链正确；duration ∈ (0,15]；scene_expression/timing_mode 为枚举值 -->
