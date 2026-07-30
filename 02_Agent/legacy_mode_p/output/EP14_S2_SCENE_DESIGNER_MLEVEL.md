# EP14_S2_SCENE_DESIGNER_MLEVEL — 贫民窟巷道 · M-Level合并设计+台本初稿

> **Prompter:** Scene Designer v1.0 (M-Level)
> **场景:** EP14场景B · 山丘贫民窟巷道+轿车内部(午后·阴天) · 7镜·39秒
> **复杂度:** 🟡 M-Level · F1=2·F2=1+VO·F3=1+VO·F4≈57%·F5=true·F6=true(悬疑)
> **渲染目标:** Seko画布 · 动作悬疑镜头→海螺02优先
> **执行分支:** 3B M-Level路径M-B(悬疑/偷窥·三域合并含动作运镜展开)
> **格式规范:** s_level_script_format_v1.0.md (结构模板通用)
> **输出规模目标:** ≤1200行

---

## §3 Step 0: 空间坐标系（三域共享·只写一次）

```
📐 场景类型: 悬疑/偷窥混合格式
   角色数: 3(Pedro+Rico+金丝眼镜男) · complexity: M · KB: §2.3悬疑+§4构图+§6光影+§8视觉结构

═══════════ 空间A: 贫民窟窄巷 ═══════════
尺寸: 纵深~20m × 宽<2m × 高~6-8m(两侧墙面至一线天)
地面: 碎石+干泥·微坡向巷内倾斜·积水洼散布

关键建筑元素:
  巷口入口(格1): 外部道路与巷内碎石交界·两侧砖墙夹道·入口上方电线
  巷内纵深(格2): 全深~20m·宽度<2m·强烈单点透视
  巷内回看巷口(格3): 逆光视角·人物/车辆以剪影呈现
  左侧墙面(格4): 红砖裸露·水泥补丁·渗水痕迹·小窗铁栅栏·褪色涂鸦
  巷中段核心(格5): 最窄处·铸铁排水管贴墙·墙根青苔·碎石地面微坡
  右侧墙面(格6): 灰泥剥落·底层红砖显露·电表箱(距地~1.5m)·垃圾桶靠墙(~1m高·锈蚀·推断LEVEL-C)
  碎石地面(格7): 碎石子+干泥·积水洼反射天光·杂草墙根交界
  仰视天空(格8): 两侧墙面间一线天·电线+晾衣绳横跨·阴灰天空~5500K
  巷尾出口(格9): 通向外街·两侧墙面收束

人物可放置区域:
  ① 巷口入口(站姿·1人·外部道路与巷内交界)
  ② 巷中段车道(站姿·车辆停靠后两侧缝隙<0.3m禁入)
  ③ 巷中段垃圾桶后(蹲姿·Pedro躲藏·距地~0m·遮蔽物)
  ④ 巷尾出口(站姿·1人)

窄区约束: 宽度<2m→禁止横移(P-FAL-06)·仅限推近/拉远/固定
推断空间: 垃圾桶(金属·~1m高·锈蚀·参考图未覆盖→LEVEL-C)

光源物理锚点(巷道):
  L1-巷口逆光: 午后自然光·巷口方向·过曝1-2档·~4500K暖金·锚点格1+格3
  L2-阴天漫射: 头顶一线天·阴灰·漫射·~5500K冷灰·锚点格8
  L3-积水反射: 地面积水洼反射天光·微弱第二反射源·锚点格7

180度线: 关系线=Pedro(观察者)↔轿车(被观察者)·沿巷道纵深·A侧(右侧·电表箱侧)

═══════════ 空间B: 轿车内部 ═══════════
尺寸: 前排驾驶+副驾驶·~1.8m²可用面积
核心视觉: 旧黑色轿车·挡风玻璃布满沙尘+干涸水渍·皮质座椅极度老化(龟裂·褶皱·接缝积尘)
  方向盘皮质包浆·换挡杆油光·仪表台均匀灰尘·后视镜反射后排+车后街景

光源物理锚点(轿车内):
  L4-暖金侧逆光: 从驾驶座左侧/前方斜射·~3500K·硬光·明暗交界线锐利
    锚点: 轿车内部参考图(侧逆光+高反差)

三重色温系统:
  3500K(车内暖金·亲密·秘密) / 4500K(巷口暖金·外部·威胁) / 5500K(巷内冷灰·隐藏·观察)
```

---

## §7.1 机位域YAML

```yaml
scene:
  id: "EP14_S2"
  name: "贫民窟巷道+轿车内部"
  type: "悬疑/偷窥·双空间"
  total_duration_sec: 39
  complexity_level: "M"

segments_camera:
  - segment_id: "①"
    time_range: [0, 6]
    shot_type: "远景→中景"
    focal_length: "24mm"
    dof: "深景深f/8"
    angle: "超低角度30cm→眼平1.0m"
    kb_rule_ids: ["D-TRI-01", "A-SUS-02", "C-DEP-01"]

  - segment_id: "②"
    time_range: [6, 12]
    shot_type: "中全景(POV)"
    focal_length: "35mm"
    dof: "中景深f/5.6"
    angle: "眼平1.2m(Pedro眼高·POV)"
    kb_rule_ids: ["C-FI-17", "A-SUS-02", "C-FI-14"]

  - segment_id: "③"
    time_range: [12, 17]
    shot_type: "中景"
    focal_length: "35mm"
    dof: "中景深f/5.6"
    angle: "低角度微仰0.6m(桶侧)"
    kb_rule_ids: ["A-SUS-01", "A-SUS-09", "C-FI-17"]

  - segment_id: "④"
    time_range: [17, 23]
    shot_type: "中景(前景遮蔽POV)"
    focal_length: "50mm"
    dof: "浅景深f/2.8"
    angle: "微仰0.8m(桶后POV)"
    kb_rule_ids: ["C-FI-17", "C-AJS-03", "C-FI-16", "A-SUS-02"]

  - segment_id: "⑤"
    time_range: [23, 29]
    shot_type: "近景→POV中全景→极端特写(三设硬切)"
    focal_length: "50mm→35mm→85mm"
    dof: "浅f/2.8→中f/5.6→浅f/2.8"
    angle: "眼平(车内)→第一人称(POV)→微俯(影子)"
    kb_rule_ids: ["A-SUS-09", "A-SUS-02", "C-FI-17", "C-FI-06"]

  - segment_id: "⑥"
    time_range: [29, 34]
    shot_type: "极端特写(ECU)"
    focal_length: "85mm"
    dof: "极浅景深f/2.0"
    angle: "微仰拍0.6m(桶侧)"
    kb_rule_ids: ["A-SUS-01", "A-SUS-09", "C-KTZ-02"]

  - segment_id: "⑦"
    time_range: [34, 39]
    shot_type: "远景(OTS Pedro)"
    focal_length: "24mm"
    dof: "深景深f/8"
    angle: "低角度微仰0.5m(OTS Pedro)"
    kb_rule_ids: ["A-SUS-08", "C-FI-06", "C-DEP-01", "C-FI2-NS-26"]

frames_hard:
  - {sec: 0, global_sec: 0, camera_position: "①", shot_type: "远景", focal_length: "24mm"}
  - {sec: 6, global_sec: 6, camera_position: "②", shot_type: "中全景", focal_length: "35mm"}
  - {sec: 12, global_sec: 12, camera_position: "③", shot_type: "中景", focal_length: "35mm"}
  - {sec: 17, global_sec: 17, camera_position: "④", shot_type: "中景", focal_length: "50mm"}
  - {sec: 23, global_sec: 23, camera_position: "⑤", shot_type: "近景", focal_length: "50mm"}
  - {sec: 29, global_sec: 29, camera_position: "⑥", shot_type: "极端特写", focal_length: "85mm"}
  - {sec: 34, global_sec: 34, camera_position: "⑦", shot_type: "远景", focal_length: "24mm"}
```

---

## §7.2 运镜域YAML

```yaml
segments_movement:
  - segment_id: "①"
    movement: "低角度前跟拍0.3x(4s)+微推落定0.05x(1s)+缓升70cm(30→100cm·第2-5s)·复合运镜"
    movement_speed_tier: "S3→S1"
    kb_rule_ids: ["M-MOT-02", "M-MOV-05", "M-MOV-04", "M-MOT-03"]

  - segment_id: "②"
    movement: "固定"
    movement_speed_tier: "S0"
    kb_rule_ids: ["M-MOT-01"]

  - segment_id: "③"
    movement: "固定"
    movement_speed_tier: "S0"
    kb_rule_ids: ["M-MOT-01"]

  - segment_id: "④"
    movement: "固定"
    movement_speed_tier: "S0"
    kb_rule_ids: ["M-MOT-01"]

  - segment_id: "⑤"
    movement: "固定(三设硬切)"
    movement_speed_tier: "S0"
    kb_rule_ids: ["M-MOT-01"]

  - segment_id: "⑥"
    movement: "固定"
    movement_speed_tier: "S0"
    kb_rule_ids: ["M-MOT-01"]

  - segment_id: "⑦"
    movement: "极慢前推0.03x·匀速5s·行程~15cm·沿巷道中轴偏右"
    movement_speed_tier: "S1"
    kb_rule_ids: ["M-MOV-04", "M-MOT-02", "M-MOT-03"]

segments_transitions:
  - {transition_id: "①→②", from_segment: "①", to_segment: "②", transition_type: "硬切", time_range: [6, 6], visual_change: "Pedro背影停步+巷口轿车剪影→硬切至Pedro POV看轿车·观察者→所见·经典POV切"}
  - {transition_id: "②→③", from_segment: "②", to_segment: "③", transition_type: "硬切", time_range: [12, 12], visual_change: "POV车内交易→硬切回巷道Pedro跑向垃圾桶·所见→反应"}
  - {transition_id: "③→④", from_segment: "③", to_segment: "④", transition_type: "硬切", time_range: [17, 17], visual_change: "Pedro蹲下缩身→硬切至垃圾桶后POV看车内·躲藏→偷窥"}
  - {transition_id: "④→⑤", from_segment: "④", to_segment: "⑤", transition_type: "硬切", time_range: [23, 23], visual_change: "交易完成信封交接→硬切至Rico近景·POV→被观察者"}
  - {transition_id: "⑤→⑥", from_segment: "⑤", to_segment: "⑥", transition_type: "硬切", time_range: [29, 29], visual_change: "足球影子ECU→硬切至Pedro恐惧ECU·威胁→反应·情绪峰值"}
  - {transition_id: "⑥→⑦", from_segment: "⑥", to_segment: "⑦", transition_type: "硬切", time_range: [34, 34], visual_change: "Pedro缩回→硬切至OTS Pedro远景·恐惧→空间释放"}
```

---

## §7.3 构图光影域YAML

```yaml
global_anchors:
  character:
    Pedro: "Boy, 10yo, thin small malnourished build, ~1.2m height, dark black unkempt hair, deep-set brown eyes large and alert, sun-tanned skin, narrow face with slightly protruding cheekbones, small hands with dirt under fingernails. Faded old light-colored T-shirt, dark shorts, barefoot. Core: (P1) half-face one-eye peeking from behind trash can rim; (P2) fingers gripping rusty can rim with whitened knuckles; (P3) crouched low posture at ~0.8m eye height"
    Rico: "Latin male, 30-35yo, lean build with controlled precise presence, short dark brown hair neatly kept, tan-brown skin, angular face with calm expressionless default look, deep-set dark eyes with slow scanning gaze. Dark casual jacket, dark shirt, dark trousers. Core: (R1) side profile silhouette through dusty windshield; (R2) quick mechanical hand movements for envelope/phone exchange; (R3) sudden head turn with visible neck muscle tension"
    GoldRimmedGlassesDriver: "Male, 40-50yo, medium build, seated in driver seat. Gold-rimmed glasses (thin gold metal frame, round/oval lenses) are PRIMARY visual identifier — rest of facial features obscured by glasses reflection and dark car interior shadow. Dark top. Core: (G1) gold-rim glasses reflecting warm side-backlight as tiny bright points in dark car interior; (G2) hands moving from steering wheel to center console"

  environment:
    description: "Favela narrow alleyway in Sao Paulo hills, afternoon, overcast sky. Alley: ~20m deep, <2m wide, open-air corridor between two brick walls. Left wall: exposed red brick, cement patches, water seepage dark stains, small iron-barred window, faded graffiti. Right wall: peeling gray plaster revealing red brick, electric meter box at ~1.5m height, rusted metal trash can (~1m tall, LEVEL-C). Floor: gravel and dry mud with slight slope inward, scattered puddles reflecting sky light. Overhead: narrow strip of gray overcast sky, crisscrossing electrical wires and clothesline. Alley entrance: bright afternoon backlight overexposed 1-2 stops, ~4500K warm gold. Car interior: old black sedan front seats, dusty windshield with dried water stains, aged cracked black leather, warm gold side-backlight ~3500K from driver side window creating high-contrast chiaroscuro"

  style_spine:
    description: "shot on Arri Alexa 35, Kodak Vision3 250D, desaturated cool slate gray alley interior with warm amber gold overexposed entrance, vintage warm gold high-contrast car interior like 1970s crime cinema, subtle film grain, 2.35:1 widescreen"
    palette_anchors: ["cool-slate-gray-5500K", "warm-amber-gold-4500K", "vintage-warm-gold-3500K", "deep-black-chiaroscuro", "rust-orange-brown", "faded-graffiti-blue"]

  lighting:
    description: "Triple color temperature system. ALLEY: L1-alley entrance backlight 4500K hard overexposed 1-2stops (Grid1+3), L2-overcast sky diffused 5500K soft from narrow sky strip (Grid8), L3-puddle reflection weak (Grid7). CAR: L4-warm gold side-backlight 3500K hard entering driver side window, sharp chiaroscuro contrast on leather/hands/dashboard. Each space has distinct color temperature identity — warm car interior reads as 'warm pocket of secrecy' within cold gray alley"
    anchor_in_reference: "Alley: Grid1+3(entrance backlight) Grid5(mid-section core) Grid7(gravel+puddle) Grid8(sky strip). Car: side-backlight+strong contrast reference images"

  constraints:
    - "Pedro half-face one-eye visual signature consistent across shots #3, #4, #6"
    - "Rico expressionless angular face matches EP14 Scene A for cross-scene anchor continuity"
    - "Gold-rimmed glasses reflection is car interior only highlight point"
    - "Triple color temperature contrast ratio consistent: 4500K vs 5500K vs 3500K"
    - "Football shadow on gravel: semi-penumbra edge, not pure black — gravel gaps transmit both 4500K and 5500K"
    - "Trash can: metal ~1m tall, rusted, LEVEL-C for Object Existence Verifier"
    - "All facial proportions consistent across shots — no drift"
    - "No on-screen text — any text marked post-production overlay (P-FAL-08)"
```

---

## ═══════════ M-Level 导演台本 ═══════════

> **Prompter:** Scene Designer v1.0 (M-Level·路径M-B)
> **场景:** EP14场景B · 贫民窟巷道+轿车内部 · 7镜·39秒
> **复杂度:** 🟡 M-Level · 悬疑/偷窥 · 三重色温系统
> **渲染目标:** Seko画布 · 动作悬疑镜头→海螺02优先
> **运镜:** 2/7镜含运镜(镜#A1复合跟拍+缓升·镜#A7极慢前推)

---

## 【场景级共享锚点】

### @参考图声明
@图片1: [[贫民窟窄巷_格1]] — 用途: 巷口入口锚定·外部道路与巷内碎石交界·逆光基准
@图片2: [[贫民窟窄巷_格2]] — 用途: 巷内纵深全貌·强烈单点透视·宽度<2m空间约束
@图片3: [[贫民窟窄巷_格3]] — 用途: 巷内回看巷口·逆光剪影视角·车辆进入锚定
@图片4: [[贫民窟窄巷_格5]] — 用途: 巷中段核心·最窄处·排水管·垃圾桶位置
@图片5: [[贫民窟窄巷_格7]] — 用途: 碎石地面微距·积水洼反射·足球影子地面材质
@图片6: [[贫民窟窄巷_格8]] — 用途: 仰视天空·一线天+电线·阴天5500K漫射光基准
@图片7: [[轿车内部]] — 用途: 挡风玻璃+皮质座椅+方向盘+仪表台·暖金3500K侧逆光

### C1 Character Anchor（逐字锁定）
Pedro: "Boy, 10yo, thin small malnourished build, ~1.2m, dark black unkempt hair, deep-set brown eyes large and alert, sun-tanned skin, narrow face protruding cheekbones, small hands with dirt under fingernails. Faded old light-colored T-shirt, dark shorts, barefoot. Core: half-face one-eye peeking(P1), fingers gripping rusty can rim with whitened knuckles(P2), crouched at ~0.8m eye height(P3)"

Rico: "Latin male, 30-35yo, lean build controlled precise presence, short dark brown hair neatly kept, tan-brown skin, angular face calm expressionless default look, deep-set dark eyes slow scanning gaze. Dark casual jacket, dark shirt, dark trousers. Core: side profile silhouette through dusty windshield(R1), quick mechanical hand movements(R2), sudden head turn with neck muscle tension(R3)"

GoldRimmedGlassesDriver: "Male, 40-50yo, medium build, seated driver seat. Gold-rimmed glasses(thin gold metal frame, round/oval lenses) PRIMARY visual identifier — rest of facial features obscured by glasses reflection and dark car interior shadow. Dark top. Core: glasses reflecting warm side-backlight as tiny bright points(G1), hands steering wheel to center console(G2)"

### C2 Environment Anchor（逐字锁定·五要素）
午后 · 圣保罗山丘贫民窟窄巷+旧轿车内部 · 阴天·无直射阳光 · 巷口逆光4500K+一线天漫射5500K+车内暖金3500K · 窄巷~20m深×<2m宽·两侧砖墙·碎石地面·头顶电线·铸铁排水管·锈蚀垃圾桶·旧黑色轿车前排·挡风玻璃沙尘·龟裂黑皮革座椅

### C3 Lighting Anchor（逐字锁定·锚点可追溯）
L1-巷口逆光: 午后自然光·4500K暖金·硬光·过曝1-2档·锚定格1+格3
L2-阴天漫射: 头顶一线天·5500K冷灰·柔光漫射·锚定格8
L3-积水反射: 地面积水洼·微弱反射·锚定格7
L4-车内暖金: 驾驶座左侧/前方斜射·3500K·硬光·明暗交界线锐利·锚定轿车内部参考图

### C4 Style Spine & Palette
风格: "shot on Arri Alexa 35, Kodak Vision3 250D, desaturated cool slate gray alley + warm amber gold overexposed entrance, vintage warm gold chiaroscuro car interior like 1970s crime cinema, subtle film grain, 2.35:1 widescreen"
调色板: cool-slate-gray-5500K · warm-amber-gold-4500K · vintage-warm-gold-3500K · deep-black-chiaroscuro · rust-orange-brown · faded-graffiti-blue

### 场景级禁止
1. 窄巷宽度<2m→禁止横移运镜(P-FAL-06)·仅限推近/拉远/固定/跟拍
2. 三重色温系统跨镜一致: 同光源条件下色温锁定·无闪烁
3. Pedro半脸单眼视觉签名(P1)在镜#A3/#A4/#A6中保持一致角度和位置
4. 垃圾桶为推断空间(LEVEL-C)·位置和外观在镜#A3-#A7中保持一致
5. 面部比例全程一致·五官不漂移
6. 无画面文字——任何需要的文字标记为后期叠加(P-FAL-08)


━━━ 镜#A1: 远景→中景 · 6秒 ━━━

### 【镜头参数卡】
- 景别: 远景→中景(复合)
- 焦距: 24mm
- 机位: 巷口入口→巷中段·距地30cm→100cm · 锚定格1+格2
- 运镜: 低角度前跟拍0.3x(4s)+微推落定0.05x(1s)+缓升70cm(30→100cm·第2-5s)·S3→S1
- 角度: 超低角度30cm→眼平1.0m
- 时长: 6秒 (场景内t=0~6)
- KB: D-TRI-01 A-SUS-02 C-DEP-01 M-MOT-02 M-MOV-05 M-MOV-04

### 【传入参考图】
@图片1: [[贫民窟窄巷_格1]] — 用途: 巷口入口·逆光初始位置·碎石与外部道路交界
@图片2: [[贫民窟窄巷_格2]] — 用途: 巷内纵深·单点透视运动路径·终点位置

### 【生成指令】
Subject: 足球 · Pedro(远景·背影·不可辨认面部)
Action:
  t=0s: 超低角度30cm·碎石地面占画面下2/3·足球从巷口外滚入画面——旧足球·黑白拼块褪色·滚过碎石与外部道路交界·微坡向巷内倾斜引导滚动方向。巷口逆光4500K暖金过曝1-2档·入口外部道路明亮·巷内渐暗形成强烈明暗过渡。足球在碎石上轻微弹跳·小石子被撞开
  t=1s: 前跟拍0.3x·摄影机跟随足球沿巷道中轴线向前移动·距地30cm。足球滚入巷内暗部·从巷口暖金4500K过渡到巷内冷灰5500K。两侧砖墙在画面边缘急剧收窄·单点透视将视线引向巷尾。足球影子在碎石地面上拉长
  t=2s: 前跟拍继续·缓升开始(30cm→)。一双赤脚出现在画面——Pedro从巷口追球跑入·脚踩碎石·脚底泥垢·脚踝细小。镜头高度升至约50cm·Pedro小腿+赤脚+前方足球。巷口逆光在Pedro身体周围形成轮廓光
  t=3s: 前跟拍继续·缓升至约70cm·Pedro瘦小背影——褪色旧T恤·深色短裤·黑发微乱。Pedro追球小跑·手臂微摆。足球滚至巷中段·碎石地面上积水洼反射天光(格7·~5500K冷灰)。头顶一线天(格8)·电线横斜
  t=4s: 前跟拍0.3x结束·微推0.05x开始。缓升至约90cm。足球滚至巷中段核心(格5)——铸铁排水管贴左墙·墙根青苔。足球撞到碎石减速。Pedro在球后~2m·身体微前倾伸手准备捡球
  t=5s: 微推落定。缓升至100cm(眼平)。Pedro弯腰捡球——手触碰足球·手指细小·指甲泥垢。Pedro起身·面向巷口·突然僵住——身体冻结·手臂微垂·足球从手中滑落。巷口方向:旧黑色轿车剪影停在巷口入口(格1)·逆光4500K在轿车边缘形成过曝轮廓。车内隐约两个人影——驾驶座金丝眼镜微反光(车外不可见)·副驾驶座深色轮廓
  t=6s: Pedro静止站立·背对镜头·面向巷口轿车·身体微僵
Camera: Shot Type: 远景→中景 · Focal: 24mm · DoF: 深景深f/8 · Angle: 超低30cm→眼平1.0m
Style: desaturated cool slate gray alley · warm amber gold overexposed entrance
  调色板: cool-slate-gray-5500K · warm-amber-gold-4500K · rust-orange-brown
Constraints: Pedro面部在镜#A1中不可辨认(远景·背影·面部尺寸<画面1%)·后续镜#A3人脸特征出现

### 【音轨】
底噪: 贫民窟环境·远处狗吠·风吹电线微鸣·碎石地面脚步声
  t=0-2s: 足球滚过碎石·持续摩擦声
  t=2-5s: Pedro赤脚跑过碎石·轻快步声
  t=5s: 足球从手中滑落·触地闷响。Pedro气息声——轻微喘息转为突然屏息(t=5s僵住时)
  t=6s: 屏息·安静·远处狗吠回荡

### 【段末转场设计】
本镜→镜#A2: 硬切
转场时长: 0秒
视觉衔接: Pedro背影停步+巷口轿车剪影→硬切至Pedro POV看轿车内部·观察者→所见·经典悬疑POV切

### 【禁止】
1. Pedro面部在镜#A1中不可辨认(远景·保持神秘·镜#A3首次揭示面部)
2. 轿车内人物细节在此镜不可见(仅剪影·车内细节留给镜#A2)


━━━ 镜#A2: 中全景(POV) · 6秒 ━━━

### 【镜头参数卡】
- 景别: 中全景(MS·POV)
- 焦距: 35mm
- 机位: 虚拟POV·Pedro眼高1.2m·巷中段看巷口 · 锚定格3(巷内回看巷口)
- 运镜: 固定(S0)·信息密集——POV主观+嵌套构图+三重色温+车内双人物·6秒吸收
- 角度: 眼平1.2m(Pedro眼高·第一人称POV)
- 时长: 6秒 (场景内t=6~12)
- KB: C-FI-17 A-SUS-02 C-FI-14 M-MOT-01

### 【传入参考图】
@图片3: [[贫民窟窄巷_格3]] — 用途: 巷内回看巷口·逆光剪影视角·轿车挡风玻璃位置
@图片7: [[轿车内部]] — 用途: 挡风玻璃+仪表台+方向盘·车内暖金3500K侧逆光

### 【生成指令】
Subject: Rico+金丝眼镜男 · 轿车前排·挡风玻璃后 · Pedro POV
Action:
  t=6s: Pedro POV·从巷内暗部(~5500K冷灰)看向巷口轿车。挡风玻璃+后视镜+侧窗构成嵌套画框——巷口逆光4500K在玻璃上形成沙尘纹理可见(挡风玻璃有干涸水渍痕迹·沙尘散射逆光)。驾驶座:金丝眼镜男——金色细金属圆框眼镜是唯一清晰面部元素·镜片反射暖金侧背光为微小亮点·其余面部特征被车内暗影遮蔽。副驾驶座:Rico侧脸剪影——深色夹克·黑色短发整齐·面部半明半暗(暖金3500K侧逆光照亮颧骨和下颌线·另一半在深黑阴影中·明暗交界线锐利)。仪表台均匀灰尘·方向盘皮质包浆·后视镜反射后排+车后街景(叠加·模糊)
  t=7s: Rico右手从阴影中伸出——机械般精准的动作·手中棕色信封。Rico将信封递给金丝眼镜男·动作无多余颤抖·无迟疑。挡风玻璃沙尘散射逆光形成柔化效果·车内人物如隔雾观看
  t=8s: 金丝眼镜男右手从方向盘移开·接信封——手背可见皮肤纹理和微细汗毛·暖金侧逆光在手指边缘形成高光切面。信封在两双手之间短暂的悬停时刻——仪式感
  t=9s: 信封交接完成。金丝眼镜男将信封放入中控台储物格。Rico右手收回阴影中。一切在沉默中完成——无对白·只有动作
  t=10s: Rico从怀中取出手机——屏幕在黑暗车内为唯一冷光源(~6500K·打破暖金基调)。Rico低头看屏幕·面部被手机冷光照亮下半部分——下颌线·嘴唇·鼻梁下部。上半脸仍在暖金逆光中。色温冲突——3500K暖金vs 6500K冷蓝=两个世界
  t=11s: Rico拇指滑动屏幕·动作精准·无情绪。手机光在Rico脸上微动。金丝眼镜男目视前方·眼镜反射不变。车内静默·只有细微皮革摩擦声
  t=12s: Rico将手机放回怀中·车内恢复单一暖金3500K光源。Rico侧脸回到半明半暗状态。金丝眼镜男手放回方向盘
Camera: Shot Type: 中全景(POV) · Focal: 35mm · DoF: 中景深f/5.6 · Angle: 眼平1.2m(POV)
Style: vintage warm gold chiaroscuro · 1970s crime cinema · Pedro subjective gaze
  调色板: vintage-warm-gold-3500K · warm-amber-gold-4500K · deep-black-chiaroscuro
Constraints: 车内人物面部特征保持在挡风玻璃后——沙尘+水渍+逆光散射=自然的视觉遮蔽·不追求面部清晰

### 【音轨】
底噪: 巷内风穿过电线的微鸣·远处贫民窟环境
  t=6-12s: 持续巷内环境音。车内细微皮革摩擦声(t=7s·信封交接·t=11s·手机滑动)
  t=7s: 信封纸面微声·手指触碰
  t=12s: 手机放回衣物·微声

### 【段末转场设计】
本镜→镜#A3: 硬切
转场时长: 0秒
视觉衔接: POV车内交易→硬切回巷道Pedro跑向垃圾桶·所见→反应·信息差闭合·从静止观察切到慌乱躲藏


━━━ 镜#A3: 中景 · 5秒 ━━━

### 【镜头参数卡】
- 景别: 中景(MS)
- 焦距: 35mm
- 机位: 巷中段·垃圾桶侧方·距地0.6m · 锚定格5(巷中段核心)
- 运镜: 固定(S0)·角色身体运动承载节奏(急跑+蹲下+紧缩+极慢探头)
- 角度: 低角度微仰0.6m(桶侧)
- 时长: 5秒 (场景内t=12~17)
- KB: A-SUS-01 A-SUS-09 C-FI-17 M-MOT-01

### 【传入参考图】
@图片4: [[贫民窟窄巷_格5]] — 用途: 巷中段核心·排水管·墙根青苔·垃圾桶位置锚定

### 【生成指令】
Subject: Pedro · 跑向垃圾桶·躲藏动作
Action:
  t=12s: Pedro从观看位置转身急跑——向巷中段右侧垃圾桶方向。低角度0.6m微仰·Pedro瘦小身形在窄巷中·赤脚跑过碎石·手臂摆动。巷内5500K冷灰散射光·Pedro肤色偏深·旧T恤在身体上晃动。锈蚀金属垃圾桶(~1m高·靠在右侧墙·电表箱下方)在前方
  t=13s: Pedro急蹲——膝盖弯曲·身体缩至垃圾桶后·瘦小身形完全被桶遮蔽。只有头顶黑发和手指在桶沿上方微露。赤脚在碎石地面上找到落脚点·脚趾紧扣碎石
  t=14s: Pedro紧缩身体·膝盖抱在胸前·背部贴墙·手指抓住垃圾桶锈蚀边缘——指甲掐进铁锈·指节因紧张发白(P2视觉签名)。巷内冷灰5500K·身体缩在桶后阴影中·阴影覆盖Pedro全身
  t=15s: Pedro极慢地从垃圾桶右侧边缘探出半张脸——右眼+右半边面部·左半边被桶遮蔽(P1视觉签名·首次出现)。深棕色大眼睛警觉·瞳孔在暗处放大·视线锁定巷口轿车方向。动作极致谨慎·头部移动速度几乎不可察觉·如小动物
  t=16s: Pedro半脸单眼继续观察巷口·眼睑不眨·眼球微动扫描轿车内动静。桶沿铁锈在Pedro脸颊旁·冷灰光下铁锈橙褐色与肤色形成暖冷对比。手指仍紧抓桶沿·指节发白。远处巷口逆光4500K暖金过曝——制度外的暖色威胁
  t=17s: Pedro维持观察·准备切换至镜#A4的桶后POV偷看视角
Camera: Shot Type: 中景 · Focal: 35mm · DoF: 中景深f/5.6 · Angle: 低角度微仰0.6m
Style: desaturated cool slate gray · hiding-in-shadows
  调色板: cool-slate-gray-5500K · rust-orange-brown · warm-amber-gold-4500K(远处巷口·小面积)
Constraints: P1半脸单眼签名——右眼+右脸·左脸被桶沿遮蔽·角度与镜#A4/#A6一致·桶沿位置固定

### 【音轨】
底噪: 持续巷内环境音
  t=12s: Pedro急跑·赤脚碎石脚步声
  t=13s: 蹲下·碎石摩擦·衣物摩擦
  t=14s: 紧缩·手指抓住桶沿·铁锈微声
  t=15-17s: 屏息·极度安静·远处狗吠

### 【段末转场设计】
本镜→镜#A4: 硬切
转场时长: 0秒
视觉衔接: Pedro半脸单眼在桶后→硬切至桶后POV看车内交易细节·躲藏→偷窥·主观代入


━━━ 镜#A4: 中景(前景遮蔽POV) · 6秒 ━━━

### 【镜头参数卡】
- 景别: 中景(前景遮蔽POV)
- 焦距: 50mm
- 机位: 虚拟POV·垃圾桶后方·距地0.8m(Pedro眼高·蹲姿) · 锚定格5(巷中段)
- 运镜: 固定(S0)·遮蔽POV>30%遮挡+小窗口法·固定维持视野限制=悬念
- 角度: 微仰0.8m(桶后POV)
- 时长: 6秒 (场景内t=17~23)
- KB: C-FI-17 C-AJS-03 C-FI-16 A-SUS-02 M-MOT-01

### 【传入参考图】
@图片3: [[贫民窟窄巷_格3]] — 用途: 巷内回看巷口·POV视线方向锚定
@图片7: [[轿车内部]] — 用途: 车内交易细节·挡风玻璃+仪表台

### 【生成指令】
Subject: Rico+金丝眼镜男(车内) · Pedro桶后POV · 前景垃圾桶边缘虚化遮蔽
Action:
  t=17s: Pedro桶后POV。前景:垃圾桶锈蚀边缘·占画面左侧>30%·虚化(浅景深f/2.8·焦点在巷口轿车)。桶沿铁锈纹理·橙褐色锈斑·旧钉眼。中景:巷口轿车——挡风玻璃沙尘+水渍散射逆光。驾驶座:金丝眼镜男·金色镜框反射暖金侧背光·镜片后眼不可见。副驾驶座:Rico侧脸剪影·暖金3500K明暗交界线在颧骨和下颌。后景:巷口外部道路·4500K暖金过曝。嵌套画框:桶沿(前景框)→挡风玻璃+车窗(中景框)→巷口外(后景光)——三层框内框(小窗口法·C-AJS-03)
  t=18s: Rico从怀中取出手机——动作同镜#A2但视角不同。手机屏幕冷蓝光(~6500K)在Rico脸上形成下半脸冷光照亮——与暖金3500K上半脸形成色温冲突。Rico拇指滑动屏幕·阅读信息
  t=19s: 金丝眼镜男从方向盘移开右手·从中控台储物格取出一个黑色小物件(手机大小·不可辨认)——交换的另一半。Rico接过·放入夹克内袋·动作流畅无停顿。两个人物之间没有眼神接触——一切如仪式
  t=20s: Rico突然转头——颈部肌肉绷紧(R3视觉签名)·目光扫向巷内方向——几乎直视镜头(Pedro位置)。Rico深色眼睛在暖金逆光中·瞳仁微缩。Pedro(画外·POV主体)猛地缩回——画面微晃(模拟Pedro后撤)·垃圾桶边缘在画面中移动·视野暂时被桶身遮蔽
  t=21s: 画面静止——桶身占画面>80%·只在桶与墙之间缝隙中透出一线巷口光(4500K暖金·光缝宽~5cm)。Pedro屏息声(画外·音轨)。极度紧张——Rico是否看到了他？
  t=22s: 画面从桶后极慢探出——桶沿重新进入前景>30%遮蔽构图。巷口轿车仍在·Rico已转回面向前方·似乎未发现。金丝眼镜男发动引擎——右手转动钥匙·仪表盘亮起微弱暖光
  t=23s: 轿车引擎声(画外·音轨)。Pedro维持桶后POV观察·手指紧抓桶沿·指节发白(P2)·前景桶沿稳定
Camera: Shot Type: 中景(前景遮蔽POV) · Focal: 50mm · DoF: 浅景深f/2.8 · Angle: 微仰0.8m(POV)
Style: frame-within-frame · foreground occlusion suspense · 1970s crime cinema
  调色板: vintage-warm-gold-3500K · rust-orange-brown(前景桶) · warm-amber-gold-4500K · deep-black-chiaroscuro
Constraints: 前景桶沿>30%画面·浅景深虚化·桶沿位置与镜#A3的P1签名一致(t=15-17s桶沿在Pedro脸颊旁)

### 【音轨】
底噪: 巷内持续环境音
  t=17-19s: 车内细微动作声(挡风玻璃后·微弱)
  t=20s: Rico转头——衣物摩擦·颈部微声。Pedro猛地缩回——碎石摩擦·衣物急速摩擦·桶沿微晃
  t=20-21s: Pedro屏息·极度安静·心跳声(可选·后期混音)
  t=22s: Pedro极慢探出·衣物微声
  t=23s: 轿车引擎发动·低沉的旧引擎启动声·回荡窄巷

### 【段末转场设计】
本镜→镜#A5: 硬切
转场时长: 0秒
视觉衔接: 桶后POV交易完成→硬切至车内Rico近景·从偷窥者视角切换到被观察者·威胁升级


━━━ 镜#A5: 近景→POV中全景→极端特写(三设硬切) · 6秒 ━━━

### 【镜头参数卡】
- 景别: 近景→POV中全景→极端特写(三设硬切)
- 焦距: 50mm→35mm→85mm
- 机位: 车内(眼平)→巷口POV(第一人称)→碎石地面(微俯) · 三设硬切
- 运镜: 固定(S0)·三段子机位均为固定·硬切切换·无连续运镜
- 角度: 眼平(车内)→第一人称(POV)→微俯(影子)
- 时长: 6秒 (场景内t=23~29)
- KB: A-SUS-09 A-SUS-02 C-FI-17 C-FI-06 M-MOT-01

### 【传入参考图】
@图片7: [[轿车内部]] — 用途: Rico面部近景·暖金3500K侧逆光·明暗交界线
@图片3: [[贫民窟窄巷_格3]] — 用途: 巷口POV·轿车位置·巷口外道路
@图片5: [[贫民窟窄巷_格7]] — 用途: 碎石地面材质·积水洼·足球影子

### 【生成指令】
Subject: Rico(车内近景·23-25s) → 巷口POV(25-27s) → 足球影子ECU(27-28s)
Action:
  ---[子设A: t=23-25s·车内Rico近景·50mm·浅f/2.8]---
  t=23s: 硬切至车内。Rico近景——面部占据画面·暖金3500K侧逆光从左侧斜射·明暗交界线沿鼻梁和下颌线切割。右侧脸在深黑阴影中。Rico深色眼睛在阴影中几乎不可见·只有颧骨和眉骨的高光线。Rico表情——无表情·角形脸·冷静的默认面容。黑色夹克领口·深色衬衫·背景完全虚化(浅景深·黑色)
  t=24s: Rico目光缓慢扫过巷内方向——不是紧张的扫描·是冷静的评估。眼球移动精准·无多余动作。颈部肌肉微绷(R3·这次在近景中清晰可见)。暖金侧逆光在Rico皮肤上呈现tan-brown色调·毛孔和微细纹理可见
  t=25s: Rico收回目光·面向前方·微不可察地点头(给金丝眼镜男的信号·确认安全/可以离开)
  ---[子设B: t=25-27s·巷口POV·35mm·中f/5.6·第一人称]---
  t=25s: 硬切至Rico POV——从车内通过挡风玻璃看巷内。挡风玻璃沙尘+水渍散射·巷内暗部(~5500K冷灰)·垃圾桶位置不可见(Pedro已缩回桶后)。巷内无人。挡风玻璃如脏滤镜·模糊了巷内细节
  t=26s: Rico视线扫描巷内——从巷口到巷尾·缓慢平移。碎石地面·积水洼反光·墙根青苔。一切静止。Rico的视角确认了"无人看到我们"
  t=27s: Rico视线收回·看向前方巷口外道路。挡风玻璃上的沙尘在巷口逆光4500K下形成散射光斑
  ---[子设C: t=27-28s·足球影子ECU·85mm·浅f/2.8·微俯]---
  t=27s: 硬切至碎石地面ECU。足球躺在碎石上·停在巷中段·不再滚动。足球黑白拼块褪色·皮革磨损。足球影子投射在碎石地面——半影边缘·非纯黑·碎石缝隙透射巷口4500K暖金和天空5500K冷灰·影子内可见微细亮斑
  t=28s: 足球静止。巷内冷灰5500K均匀光照·影子边缘柔和。画面极简——只有足球+碎石+影子
  t=29s: 硬切至镜#A6
Camera: 近景(CU·50mm·f/2.8)→中全景(POV·35mm·f/5.6)→ECU(85mm·f/2.8) · 三设硬切
Style: vintage warm gold chiaroscuro → desaturated cool slate gray → minimal gravel texture
  调色板: vintage-warm-gold-3500K · deep-black-chiaroscuro · cool-slate-gray-5500K · warm-amber-gold-4500K
Constraints: Rico近景面部特征与EP14场景A的Rico照片一致·跨场景锚点连续

### 【音轨】
底噪: 车内引擎怠速(镜#A5子设A/B)·巷内持续环境音(子设C)
  t=23-25s: 车内细微呼吸声·引擎怠速低鸣
  t=25s: Rico点头·衣物微声
  t=25-27s: 车内引擎怠速·挡风玻璃外巷内环境音(远处·经玻璃衰减)
  t=27-28s: 切换至巷内·引擎怠速从车内方向传来·碎石地面静默

### 【段末转场设计】
本镜→镜#A6: 硬切
转场时长: 0秒
视觉衔接: 足球影子ECU→硬切至Pedro恐惧ECU·足球(静止·被遗忘)→Pedro(恐惧·被发现)·情绪从静物转移到人物


━━━ 镜#A6: 极端特写(ECU) · 5秒 ━━━

### 【镜头参数卡】
- 景别: 极端特写(ECU)
- 焦距: 85mm
- 机位: 巷中段·垃圾桶侧前·距地0.6m · 锚定格5(巷中段核心)
- 运镜: 固定(S0)·ECU恐惧峰值——静止=窒息感·运动稀释情绪
- 角度: 微仰拍0.6m(桶侧)
- 时长: 5秒 (场景内t=29~34)
- KB: A-SUS-01 A-SUS-09 C-KTZ-02 M-MOT-01

### 【传入参考图】
@图片4: [[贫民窟窄巷_格5]] — 用途: 垃圾桶侧前·Pedro躲藏位置·桶沿+墙面关系

### 【生成指令】
Subject: Pedro · 极端特写面部·恐惧反应
Action:
  t=29s: ECU·Pedro面部。右眼占据画面中心——深棕色瞳仁放大(恐惧·肾上腺素)·巩膜微血管可见·眼睑紧绷不眨。右半边面部——窄脸·颧骨微凸·日晒肤色在巷内冷灰5500K下偏深偏灰·额头微细汗珠。左半边面部被垃圾桶边缘遮蔽(P1视觉签名·ECU版)。桶沿锈蚀铁锈在Pedro脸颊旁·离皮肤仅~2cm·橙褐色铁锈与肤色形成暖冷对比。极浅景深f/2.0——眼睫毛细微·瞳孔纹理可见·背景完全虚化为灰色模糊
  t=30s: Pedro眼球微动——从巷口方向(镜#A5中Rico视线)收回·看向前方桶身。瞳孔仍放大。眉心微皱——眉间皮肤微褶·眉毛下沉。嘴唇紧闭·嘴角下拉·牙关咬紧——恐惧但不发出声音
  t=31s: Pedro极慢地将头缩回桶后——右眼从桶沿露出→桶沿遮蔽全脸→只有头顶黑发在桶沿上方微露。动作速度约0.5cm/s·极致控制·如小动物试图不被捕食者发现。手指仍紧抓桶沿·指节发白(P2·画面下方可见手指+桶沿铁锈)
  t=32s: Pedro完全缩回桶后——面部不可见·只有桶身锈蚀金属表面+头顶黑发。桶沿铁锈·旧钉眼·凹陷。巷内安静——引擎怠速持续(画外·轿车未驶离)
  t=33s: 极慢——Pedro右眼再次从桶沿探出(P1签名重现)·位置与t=29s完全一致。瞳孔仍放大·眼睑仍紧绷·但眼球停止扫动——凝视巷口方向。轿车引擎声变化(准备驶离)
  t=34s: Pedro维持凝视·单眼在桶沿后·静止
Camera: Shot Type: ECU · Focal: 85mm · DoF: 极浅景深f/2.0 · Angle: 微仰0.6m
Style: intimate fear · extreme close-up suspense · cool gray skin tone
  调色板: cool-slate-gray-5500K · rust-orange-brown · deep-black
Constraints: P1半脸单眼签名角度和桶沿位置与镜#A3(t=15-17s)和镜#A4(前景桶沿)一致·瞳孔放大和微细汗珠是恐惧的可见生理反应

### 【音轨】
底噪: 巷内极度安静·远处轿车引擎怠速
  t=29-31s: Pedro屏息·极度安静。衣物微声(缩回时)
  t=32s: 静止·无声
  t=33s: Pedro探出·衣物微声。轿车引擎转速变化——准备驶离
  t=34s: 轿车引擎声渐强·即将移动

### 【段末转场设计】
本镜→镜#A7: 硬切
转场时长: 0秒
视觉衔接: Pedro恐惧ECU→硬切至OTS Pedro远景·恐惧→空间释放·从微观情感切到宏观空间


━━━ 镜#A7: 远景(OTS Pedro) · 5秒 ━━━

### 【镜头参数卡】
- 景别: 远景(LS·OTS Pedro)
- 焦距: 24mm
- 机位: Pedro身后~1m·距地50cm·OTS垃圾桶右侧 · 锚定格5(巷中段)
- 运镜: 极慢前推0.03x·匀速5s·行程~15cm·沿巷道中轴偏右(S1)
- 角度: 低角度微仰0.5m(OTS Pedro)
- 时长: 5秒 (场景内t=34~39)
- KB: A-SUS-08 C-FI-06 C-DEP-01 C-FI2-NS-26 M-MOV-04 M-MOT-02 M-MOT-03

### 【传入参考图】
@图片3: [[贫民窟窄巷_格3]] — 用途: 巷内回看巷口·轿车驶离方向·逆光
@图片2: [[贫民窟窄巷_格2]] — 用途: 巷内纵深全貌·单点透视收束

### 【生成指令】
Subject: Pedro(前景·背影·OTS) + 轿车(巷口·驶离)
Action:
  t=34s: OTS Pedro·低角度0.5m微仰。前景:Pedro蹲在垃圾桶后·瘦小背影·旧T恤·黑发微乱·右肩和头部在桶右侧微露。垃圾桶锈蚀金属表面·橙褐色铁锈·旧钉眼。Pedro手指仍抓桶沿·指节白(P2·前景可见)。中景:窄巷纵深~15m·两侧砖墙收窄·单点透视·碎石地面·头顶一线天。后景:巷口轿车——旧黑色轿车剪影·逆光4500K暖金在车身边缘形成过曝轮廓·巷口外部道路明亮。冷灰5500K巷内与暖金4500K巷口的色温对比——Pedro在冷灰阴影中·轿车在暖金亮光中
  t=35s: 极慢前推0.03x开始·沿巷道中轴偏右·微朝垃圾桶。轿车开始移动——从巷口驶离·车身从逆光剪影过渡到侧影·车尾灯红色微光(唯一暖色元素·在冷灰巷内如两滴血)。Pedro身体微动——头部微转追踪轿车移动方向·但身体仍躲在桶后
  t=36s: 前推继续。轿车驶出巷口外道路·车身被巷口外建筑遮蔽·红色尾灯最后消失。巷口恢复为空的逆光矩形——4500K暖金过曝·外部道路空荡。Pedro维持蹲姿·手指从桶沿松开——指节恢复血色·手垂至身侧
  t=37s: 前推继续。巷内恢复安静——只有Pedro瘦小背影在桶旁。碎石地面上足球仍在·停在巷中段。冷灰5500K均匀照明·一切回到静止。Pedro从桶后站起——身体从蹲姿0.8m升至站姿1.2m·赤脚在碎石上·旧T恤下垂。Pedro看向巷口——空荡·轿车已消失
  t=38s: 前推落定·终点距Pedro~0.85m。Pedro站在垃圾桶旁·瘦小身形在窄巷中·冷灰光照·皮肤偏深·赤脚。Pedro转身·走向足球·弯腰捡起。足球在手中·黑白拼块褪色·皮革磨损。Pedro把足球抱在胸前——足球几乎和他上半身一样大
  t=39s: Pedro抱球站在巷中段·面向巷口空荡逆光·静止。前景桶身·中景Pedro背影+足球·后景巷口逆光过曝。窄巷冷灰·巷口暖金·人物在中间——一个夹在两个世界之间的小身影
Camera: Shot Type: 远景(OTS) · Focal: 24mm · DoF: 深景深f/8 · Angle: 低角度微仰0.5m
Style: desaturated cool slate gray · warm amber gold exit · emotional closure · 2.35:1 widescreen
  调色板: cool-slate-gray-5500K · warm-amber-gold-4500K · rust-orange-brown · red-taillight-glow
Constraints: Pedro身体尺寸在24mm远景中小(<画面5%)·不追求面部细节·气质通过身体语言传达

### 【音轨】
底噪: 巷内环境音·轿车引擎
  t=34s: 轿车引擎启动移动
  t=35s: 轿车驶离·引擎声渐远·碎石在轮胎下微声
  t=36s: 轿车驶出巷口·引擎声在外部道路上·被建筑遮挡·声音变远
  t=37-39s: 巷内恢复安静·远处狗吠·风吹电线微鸣。Pedro站起·赤脚碎石微声·足球捡起·皮革微声
  t=39s: 安静·结束

### 【段末转场设计】
本镜→场景结束: 黑屏
转场时长: 2秒(淡出)
视觉衔接: Pedro抱球·面向巷口逆光→淡出黑屏。制度空间的逃离(镜#A7轿车暖金)→外部世界(场景C·未知)。Pedro在垃圾桶后的躲藏成为EP14的视觉签名——下一个场景中他是否会再出现？

### 【禁止】
1. Pedro面部在远景中不可见·不描述表情·气质通过身体语言传达
2. 轿车驶离后巷口必须恢复为空荡——无人物·无车辆·只有逆光


━━━ 全场景收尾 ━━━
色彩弧线: 巷口暖金(镜#A1-A2建立)→巷内冷灰(镜#A3-A6躲藏·观察)→冷暖对比(镜#A5色温冲突)→暖金驶离+冷灰留守(镜#A7收束)
运镜统计: 5/7镜固定(71%) · 镜#A1复合跟拍+缓升(S3→S1)·镜#A7极慢前推(S1)
悬疑节奏: 建立(镜#A1)→观察(镜#A2)→躲藏(镜#A3)→偷窥(镜#A4)→威胁(镜#A5)→恐惧(镜#A6)→释放(镜#A7)
三重色温: 3500K车内暖金(秘密·亲密)/4500K巷口暖金(外部·威胁)/5500K巷内冷灰(隐藏·观察)
硬切统计: 7镜·6次硬切+1次淡出
宪法合规: 画布七条铁律全部✅ · P-FAL-06规避(窄巷<2m禁横移) · P-FAL-08规避(无画面文字)
场景末状态快照: Pedro抱足球·站在巷中段·面向空荡巷口·轿车已驶离
