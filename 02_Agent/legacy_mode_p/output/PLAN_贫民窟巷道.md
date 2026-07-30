# PLAN — EP14 S2: 贫民窟巷道

> **合并来源:**
> - `EP14_S2_SCENE_DESIGNER.md` — §4(机位域YAML) + §6(构图光影域YAML)
> - `EP14_S2_MOVEMENT_DESIGNER.md` — §5(运镜域YAML) + 过渡YAML
> **场景:** 贫民窟窄巷+轿车内部(午后·阴天) · 7镜 · 39秒 · 悬疑/偷窥 · complexity=M
> **三重色温系统:** 3500K(车内暖金) / 4500K(巷口暖金) / 5500K(巷内冷灰)

---

# §A — GLOBAL ANCHORS (三域共享·Scene Designer §6)

```yaml
global_anchors:
  character:
    Pedro: "Boy, 10 years old, male, thin small malnourished build, ~1.2m height, dark black unkempt hair, deep-set brown eyes large and alert, sun-tanned skin from outdoor favela life, narrow face with slightly protruding cheekbones, small hands with dirt under fingernails. Costume: faded old light-colored T-shirt (may have small holes), dark shorts or old trousers (knees worn), barefoot or old flip-flops. Core visual signatures: (P1) half-face one-eye peeking from behind trash can rim — only right half of face visible, left half obscured by can; (P2) fingers gripping rusty can rim with whitened knuckles from tension; (P3) crouched low posture at approximately 0.8m eye height when squatting behind trash can."
    Rico: "Latin male, 30-35 years old, lean build with controlled precise presence, short dark brown hair neatly kept (not favela style), tan-brown skin, angular face with calm expressionless default look, deep-set dark eyes with slow scanning gaze, no unnecessary movements. Costume: dark casual jacket or coat (not police style), dark shirt or t-shirt, dark trousers (inside car, shadowy interior obscures details). Core visual signatures: (R1) side profile silhouette through dusty windshield — half face lit by warm gold side-light, other half in deep shadow; (R2) quick mechanical hand movements for envelope/phone exchange — no wasted motion; (R3) sudden head turn with visible neck muscle tension — the moment of near-discovery."
    GoldRimmedGlassesDriver: "Male, 40-50 years old, medium build, seated in driver seat behind steering wheel. Gold-rimmed glasses (thin gold metal frame, round or oval lenses) are PRIMARY visual identifier — rest of facial features obscured by glasses reflection and dark car interior shadow. Costume: dark top (shirt or jacket, details indistinct in deep shadow). Core visual signatures: (G1) gold-rim glasses reflecting warm side-backlight as tiny bright points in dark car interior; (G2) hands moving from steering wheel to center console for exchange; (G3) side face partially lit by warm gold light on cheekbone and glasses frame edge only — maintain mysterious aura through visual concealment."

  environment:
    description: "Favela narrow alleyway in Sao Paulo hills, afternoon, overcast sky. Alley dimensions: approximately 20m deep, less than 2m wide, open-air corridor between two brick walls. Left wall: exposed red brick, cement patches, water seepage dark stains, small iron-barred window, faded graffiti remnants. Right wall: peeling gray plaster revealing underlying red brick, electric meter box at approximately 1.5m height. Floor: gravel and dry mud with slight slope inward, scattered puddles reflecting sky light, weeds at wall-gravel junction. Overhead: narrow strip of gray overcast sky with crisscrossing electrical wires and clothesline. Two exits: alley entrance (connects to external road via stone steps, bright afternoon backlight overexposed 1-2 stops, approximately 4500K warm gold) and alley rear exit (connects to another street, darker). Mid-alley: rusted cast iron drainpipe along left wall, moss at wall base, metal trash can (approximately 1m tall, rusted surface, inferred physical property — reference image does not directly cover, marked LEVEL-C) positioned against right wall. Secondary space: dark sedan interior (front seats only) — old black sedan, dusty windshield with dried water stain patterns, aged cracked black leather seats with deep creases and seam dust, dust-covered dashboard and center console, gear shift knob with oily patina and fine scratches, rearview mirror reflecting backseat and street behind, warm gold side-backlight (approximately 3500K) entering from driver side window creating high-contrast chiaroscuro light slices on leather, hands, and dashboard surfaces."

  style_spine:
    description: "shot on Arri Alexa 35, Kodak Vision3 250D, desaturated cool slate gray alley interior with warm amber gold overexposed entrance, vintage warm gold high-contrast car interior like 1970s crime cinema, subtle film grain, 2.35:1 widescreen aspect ratio for lateral compression of narrow alley depth"
    palette_anchors:
      - "cool slate gray (alley interior, 5500K overcast)"
      - "warm amber gold (alley entrance backlight, 4500K)"
      - "vintage warm gold/amber (car interior side-backlight, 3500K)"
      - "deep black (car interior shadows, chiaroscuro voids)"
      - "rust orange-brown (trash can, drainpipe, iron oxidation details)"

  lighting:
    description: "Triple light source system spanning two interconnected spaces. ALLEY: Source1 — alley entrance afternoon backlight, 4500K, hard light, overexposed 1-2 stops, anchored in reference Grid1 (alley entrance looking in) and Grid3 (looking back at entrance from inside alley). Source2 — overcast diffused sky light, 5500-6500K, soft light, from narrow sky strip above alley between walls, anchored in reference Grid8 (looking up at sky strip with wires). Source3 — weak puddle reflection light from gravel floor water puddles, anchored in reference Grid7 (gravel micro-detail). CAR INTERIOR: Source4 — warm gold side-backlight, 3200-4000K, hard light, entering from driver side left/front window, creating sharp chiaroscuro contrast with light slices on leather seats, steering wheel top, dashboard surfaces, and hands during exchange, anchored in car interior reference images (center-top and right-center grid positions showing side-backlight and strong contrast). KEY COLOR TEMPERATURE SYSTEM: alley entrance warm-bright (4500K) versus alley interior cool-gray (5500K) versus car interior warm-gold intimate (3500K). Each space has a distinct color temperature identity — the warm car interior (3500K) reads as a 'warm pocket of secrecy' embedded within the cold gray alley environment. Earthy texture tones throughout: red brick warm brown, gray plaster mid-gray, gravel neutral gray, rusted iron orange-brown."
    anchor_in_reference: "Alley: Grid1 (entrance backlight) + Grid3 (looking back at entrance) + Grid5 (alley mid-section core) + Grid7 (gravel micro-detail with puddle reflection) + Grid8 (looking up at sky strip with wires). Car interior: side-backlight and strong contrast descriptions + warm color tone base + external view through windshield."

  constraints:
    - "Pedro half-face one-eye visual signature consistent across shots #3, #4, #6 — same angle, same trash can rim position, same eye-to-rim relationship"
    - "Rico expressionless angular face matches EP14 Scene A award photo of Rico for cross-scene anchor continuity"
    - "Gold-rimmed glasses reflection is car interior only highlight point — maintain consistent reflection angle and brightness in shots #2 and #5"
    - "Alley triple color temperature contrast ratio consistent: warm 4500K entrance vs cool 5500K interior vs warm 3500K car interior"
    - "Football shadow on gravel floor: semi-penumbra edge transition, not pure black — gravel gaps transmit both alley entrance light (4500K) and sky light (5500K) creating subtle bright speckles within shadow"
    - "Trash can: metal cylinder approximately 1m tall, rusted surface, positioned against right wall in alley mid-section — inferred physical property (reference image does not directly cover), marked as LEVEL-C for Object Existence Verifier"
    - "All characters maintain consistent facial proportions across shots — no facial feature drift"
    - "No flickering in light color temperature across shots within same light source"
    - "No subtitles, no logos, no watermarks"
    - "No on-screen text — any required text marked as 'post-production overlay' (P-FAL-08)"
```

---

# §B — TIME_SKELETON (三域合并·逐镜逐秒)

## SEGMENTS OVERVIEW

```yaml
segments:
  - seg_id: "1"
    time_range: [0, 6]
    narrative_beat: "追球入巷·巷口猛停"
    location: "巷口->巷中段"
    camera:
      shot_type: "远景->中景"
      focal_length: "24mm"
      dof: "深景深f/8"
      angle: "超低角度(30cm)->眼平(1.0m)"
      axis_side: "A侧(巷道右侧)"
      coverage_function: "建立+推进+揭示"
      kb_rule_ids: ["D-TRI-01", "A-SUS-02", "C-DEP-01"]
    movement:
      type: "低角度前跟拍(0.3x)+缓升(30cm→100cm)"
      speed_tier: "S3→S1"
      direction: "巷口→巷中段·沿巷道中轴线·正前"
      path: "直线·起点巷口入口(距地30cm)·终点巷中段(距地100cm·Pedro身后~2m)·行程~12m"
      composite: "前跟拍4s(0.3x)+微推落定1s(0.05x)+缓升70cm(30→100cm·第2-5s)"
      dof_vector: [0, 0, 0, 0, 70, 12, 0]
      kb_rule_ids: ["M-MOT-02", "M-MOV-05", "M-MOV-04", "M-MOT-03"]

  - seg_id: "2"
    time_range: [6, 12]
    narrative_beat: "Pedro POV·发现轿车·目击交易"
    location: "巷中段(POV虚拟)"
    camera:
      shot_type: "中全景"
      focal_length: "35mm"
      dof: "中景深f/5.6"
      angle: "眼平(1.2m·Pedro眼高·POV)"
      axis_side: "A侧(继承Pedro位置)"
      coverage_function: "揭示+人物引入·信息差制造"
      kb_rule_ids: ["C-FI-17", "A-SUS-02", "C-FI-14"]
    movement:
      type: "固定"
      speed_tier: "S0"
      dof_vector: [0, 0, 0, 0, 0, 0, 0]
      static_exception: "信息密集——POV主观+嵌套构图+三重色温+车内双人物·6秒吸收"
      kb_rule_ids: ["M-MOT-01"]

  - seg_id: "3"
    time_range: [12, 17]
    narrative_beat: "躲藏·垃圾桶后探头"
    location: "巷中段·垃圾桶侧方"
    camera:
      shot_type: "中景"
      focal_length: "35mm"
      dof: "中景深f/5.6"
      angle: "低角度微仰(0.6m·桶侧)"
      axis_side: "A侧"
      coverage_function: "反应+过渡·躲藏动作"
      kb_rule_ids: ["A-SUS-01", "A-SUS-09", "C-FI-17"]
    movement:
      type: "固定"
      speed_tier: "S0"
      dof_vector: [0, 0, 0, 0, 0, 0, 0]
      static_exception: "信息密集——躲藏4子节拍(急跑+蹲下+紧缩+极慢探头)·角色身体运动承载节奏"
      kb_rule_ids: ["M-MOT-01"]

  - seg_id: "4"
    time_range: [17, 23]
    narrative_beat: "偷看POV·交易细节"
    location: "垃圾桶后方(POV虚拟)"
    camera:
      shot_type: "中景(前景遮蔽POV)"
      focal_length: "50mm"
      dof: "浅景深f/2.8"
      angle: "微仰(0.8m·桶后POV)"
      axis_side: "A侧"
      coverage_function: "揭示+代入·交易细节"
      kb_rule_ids: ["C-FI-17", "C-AJS-03", "C-FI-16", "A-SUS-02"]
    movement:
      type: "固定"
      speed_tier: "S0"
      dof_vector: [0, 0, 0, 0, 0, 0, 0]
      static_exception: "信息密集——遮蔽POV(>30%遮挡)+小窗口法(C-AJS-03)·固定维持视野限制=悬念"
      kb_rule_ids: ["M-MOT-01"]

  - seg_id: "5"
    time_range: [23, 29]
    narrative_beat: "Rico转头·差点发现"
    location: "轿车内->巷口POV->碎石地面"
    camera:
      shot_type: "近景->POV中全景->极端特写"
      focal_length: "50mm->35mm->85mm"
      dof: "浅f/2.8->中f/5.6->浅f/2.8"
      angle: "眼平(车内)->第一人称(POV)->微俯(影子)"
      axis_side: "车外侧->无(POV)->A侧"
      coverage_function: "威胁识别·全场景情绪峰值"
      kb_rule_ids: ["A-SUS-09", "A-SUS-02", "C-FI-17", "C-FI-06"]
    movement:
      type: "固定(三设硬切)"
      speed_tier: "S0"
      dof_vector: [0, 0, 0, 0, 0, 0, 0]
      movement_note: "三段子机位均固定: 23-25s车内Rico CU/25-27s巷口POV/27-28s影子ECU·硬切切换·无连续运镜"
      static_exception: "复合——车内段(空间受限·1.8m²)+POV段(信息密集·扫描)+影子ECU(情感沉浸·悬念悬停)"
      kb_rule_ids: ["M-MOT-01"]

  - seg_id: "6"
    time_range: [29, 34]
    narrative_beat: "Pedro反应·缩回·恐惧"
    location: "巷中段·垃圾桶侧前"
    camera:
      shot_type: "极端特写"
      focal_length: "85mm"
      dof: "极浅景深f/2.0"
      angle: "微仰拍(0.6m·桶侧)"
      axis_side: "A侧"
      coverage_function: "情绪峰值反应·恐惧视觉化"
      kb_rule_ids: ["A-SUS-01", "A-SUS-09", "C-KTZ-02"]
    movement:
      type: "固定"
      speed_tier: "S0"
      dof_vector: [0, 0, 0, 0, 0, 0, 0]
      static_exception: "情感沉浸——ECU恐惧峰值·缩回避让+极慢探头·静止=窒息感·运动稀释情绪"
      kb_rule_ids: ["M-MOT-01"]

  - seg_id: "7"
    time_range: [34, 39]
    narrative_beat: "轿车驶离·Pedro前景锚点"
    location: "巷中段·OTS Pedro身后"
    camera:
      shot_type: "远景"
      focal_length: "24mm"
      dof: "深景深f/8"
      angle: "低角度微仰(0.5m·OTS Pedro)"
      axis_side: "A侧"
      coverage_function: "收束+情绪余韵+空间释放"
      kb_rule_ids: ["A-SUS-08", "C-FI-06", "C-DEP-01", "C-FI2-NS-26"]
    movement:
      type: "极慢前推(0.03x)"
      speed_tier: "S1"
      direction: "巷中段→Pedro方向·沿巷道中轴偏右·微朝垃圾桶"
      path: "直线·起点Pedro身后~1m(距地50cm)·终点~0.85m·行程~15cm·匀速5s"
      dof_vector: [0, 0, 0, 0, 0, 0.03, 0]
      push_distance_cm: 15
      push_duration_s: 5
      kb_rule_ids: ["M-MOV-04", "M-MOT-02", "M-MOT-03"]

# ══════════════════════════════════════════
# TRANSITIONS (Movement Designer)
# ══════════════════════════════════════════
transitions:
  - id: "1→2"
    from_segment: "1"
    to_segment: "2"
    type: "硬切"
    time_range: [6, 6]
    visual_change: "从Pedro背影停步+巷口轿车剪影→硬切至Pedro POV看轿车·观察者→所见·经典POV切"

  - id: "2→3"
    from_segment: "2"
    to_segment: "3"
    type: "硬切"
    time_range: [12, 12]
    visual_change: "从POV看车内交易→硬切回巷道Pedro跑向垃圾桶·所见→反应·信息差闭合"

  - id: "3→4"
    from_segment: "3"
    to_segment: "4"
    type: "硬切"
    time_range: [17, 17]
    visual_change: "从桶侧看Pedro探头→硬切至桶后偷窥POV·观察者→所见(更受限视角)·嵌套信息差"

  - id: "4→5"
    from_segment: "4"
    to_segment: "5"
    type: "硬切"
    time_range: [23, 23]
    visual_change: "从偷窥POV看车内→硬切至车内Rico近景·空间跳跃(巷道→轿车内)·威胁源突然拉近·悬念引爆"

  - id: "5→6"
    from_segment: "5"
    to_segment: "6"
    type: "硬切"
    time_range: [29, 29]
    visual_change: "从Rico视角影子ECU→硬切至Pedro恐惧ECU·威胁扫描→恐惧反应·正反打恐惧释放"

  - id: "6→7"
    from_segment: "6"
    to_segment: "7"
    type: "硬切"
    time_range: [34, 34]
    visual_change: "从Pedro右眼ECU→硬切至巷道远景OTS·极度压缩→全纵深展开·空间释放·恐惧余韵落地"
```

---

## FRAMES (逐秒合并·39帧)

```yaml
frames:
  # ═══════════════════════════════════════
  # 镜#1: 追球入巷·巷口猛停 [0-5s] seg_id=1
  # ═══════════════════════════════════════

  - sec: 0
    global_sec: 0
    camera_position: "1"
    shot_type: "远景"
    focal_length: "24mm"
    dof: "深景深f/8"
    movement: "前跟拍(0.3x)·起幅·距地30cm"
    action_anchor: "旧足球从石阶上方向画面滚入·球体占画面下三分之一中央·足球表面旧皮革磨损纹理可见·球在碎石地面上弹跳·碎石飞溅微尘"
    spatial_anchor: "超低角度贴近地面·碎石占据前景2/3·石阶从画面外延伸入画·巷内纵深空间向远处收窄·巷口方向暖亮逆光过曝"
    prop_state:
      - item: "旧足球(O-032)"
        state: "沿石阶滚下·刚进入画面·弹跳中"
      - item: "碎石地面(O-021)"
        state: "碎石子+干泥·微坡向巷内·画面主体"
    character_state: []
    audio:
      ambience: "贫民窟远底噪(远处人声·狗吠·电视声从窗内传出)"
      events:
        - "足球在碎石上弹跳: 喀嗒-喀嗒 节奏"

  - sec: 1
    global_sec: 1
    camera_position: "1"
    shot_type: "远景"
    focal_length: "24mm"
    dof: "深景深f/8"
    movement: "前跟拍(0.3x)·匀速·距地30cm"
    action_anchor: "足球继续沿碎石地面滚落·速度微减·球体影子在前方碎石上拉长·狭窄巷内足球撞击左侧墙根碎石后方向微偏"
    spatial_anchor: "两侧砖墙进入画面边缘·左侧墙面红砖水泥补丁纹理渐显·头顶一线天窄条开始可见·巷口暖亮过曝区在远景中央"
    prop_state:
      - item: "旧足球(O-032)"
        state: "滚动中·速度微减·方向微偏"
    character_state: []
    audio:
      ambience: "贫民窟远底噪持续"
      events:
        - "足球滚动声: 咕噜噜持续·节奏放缓"

  - sec: 2
    global_sec: 2
    camera_position: "1"
    shot_type: "远景"
    focal_length: "24mm"
    dof: "深景深f/8"
    movement: "前跟拍(0.3x)+缓升始·距地30→45cm"
    action_anchor: "足球继续向巷内滚落·Pedro的赤脚从石阶上方进入画面后景·小跑追逐球·瘦小身形剪影在巷口暖亮逆光中"
    spatial_anchor: "两侧砖墙更清晰·墙面渗水痕迹深灰蔓延可见·头顶电线进入画面顶部·巷口暖亮过曝在画面远景中央"
    prop_state:
      - item: "旧足球(O-032)"
        state: "继续滚动·速度进一步减慢"
    character_state:
      - character: "Pedro"
        pose: "小跑追逐·手臂摆动·身体前倾"
        position: "画面后景上方·石阶中段·距球约2m"
        expression: "未可见(逆光剪影)"
    audio:
      ambience: "贫民窟远底噪持续"
      events:
        - "足球滚动声继续·伴随Pedro小跑脚步声"

  - sec: 3
    global_sec: 3
    camera_position: "1"
    shot_type: "中全景"
    focal_length: "24mm"
    dof: "深景深f/8"
    movement: "前跟拍(0.3x)+缓升·距地45→65cm"
    action_anchor: "Pedro追近足球·距离缩短至约1m·右手前伸准备捡球·足球即将停止滚动"
    spatial_anchor: "两侧墙面压迫感增强·墙根青苔沿墙角可见·铸铁排水管贴左侧墙面进入画面·巷口暖亮逆光中隐约可见外部道路"
    prop_state:
      - item: "旧足球(O-032)"
        state: "即将停止·在碎石地上最后滚动"
    character_state:
      - character: "Pedro"
        pose: "追近至球旁·右手前伸·身体仍然前倾"
        position: "画面中景·距球约1m"
        expression: "未可见(身体朝向球·背向镜头侧)"
    audio:
      ambience: "贫民窟远底噪"
      events:
        - "足球滚动声即将停止·最后几下碎石摩擦声"

  - sec: 4
    global_sec: 4
    camera_position: "1"
    shot_type: "中全景"
    focal_length: "24mm"
    dof: "深景深f/8"
    movement: "前跟拍(0.2x)+缓升·距地65→85cm"
    action_anchor: "Pedro突然猛停·双脚钉在碎石上·身体惯性前倾后急刹·右腿在前左腿在后形成支撑·足球在前方约1m处静止"
    spatial_anchor: "相机升至Pedro眼高约1.0m·巷口全景展开:暖亮过曝逆光中一辆黑色轿车暗色剪影停在巷口外部道路·车身挡住部分巷口暖光·形成不祥的暗色块"
    prop_state:
      - item: "旧足球(O-032)"
        state: "静止在碎石地上·球体影子在地上"
      - item: "黑色轿车(O-033)"
        state: "停在巷口外部道路·暗色剪影·全新出现在画面中"
    character_state:
      - character: "Pedro"
        pose: "猛停·双脚钉地·身体前倾后急刹·重心后移"
        position: "画面中景中央偏右·背对镜头"
        expression: "不可见(背对)·但身体语言传达震惊"
    audio:
      ambience: "贫民窟远底噪"
      events:
        - "足球静止:碎石摩擦声停止"
        - "Pedro急停:碎石上急促摩擦声"

  - sec: 5
    global_sec: 5
    camera_position: "1"
    shot_type: "中景"
    focal_length: "24mm"
    dof: "深景深f/8"
    movement: "极慢前推(0.05x)落定·距地100cm"
    action_anchor: "Pedro身体完全静止·手臂垂放·背部僵硬·面向巷口方向凝视轿车·瘦小背影在巷道中央形成中间调剪影·边缘被巷口暖逆光勾勒极细暖色轮廓光"
    spatial_anchor: "固定画面:两侧墙面收窄至巷口·碎石地面向前延伸至外部道路交界·轿车暗色剪影在巷口暖亮逆光中占据中心远景·天空一线天在上方窄条可见"
    prop_state:
      - item: "旧足球(O-032)"
        state: "静止在碎石地上·球的影子在地上·距Pedro约1m"
      - item: "黑色轿车(O-033)"
        state: "静止停在巷口外部道路·暗色剪影·引擎怠速"
    character_state:
      - character: "Pedro"
        pose: "完全静止站立·背对镜头·凝视巷口轿车"
        position: "画面中景中央·距轿车远景约15m"
        expression: "不可见(背影)"
    audio:
      ambience: "贫民窟远底噪持续"
      events:
        - "轿车引擎声:低沉怠速声从巷口方向传来·持续"

  # ═══════════════════════════════════════
  # 镜#2: Pedro POV·发现轿车·目击交易 [6-11s] seg_id=2
  # ═══════════════════════════════════════

  - sec: 6
    global_sec: 6
    camera_position: "2"
    shot_type: "中全景"
    focal_length: "35mm"
    dof: "中景深f/5.6"
    movement: "固定"
    action_anchor: "硬切至Pedro主观视角。从他眼高(~1.2m)看巷口方向。黑色轿车停在巷口外道路。透过布满沙尘和干涸水渍的挡风玻璃看入车内前排。Rico(右·副驾驶)和金丝眼镜司机(左·驾驶座)坐姿·两人上半身可见·挡风玻璃沙尘层在暖金逆光中散射形成柔和空气质感"
    spatial_anchor: "挡风玻璃作为天然画框·沙尘纹理和水渍斑痕在前景半透明·后视镜反射后排空间和车后街景·中控台灰尘均匀覆盖·方向盘老化皮质龟裂纹理在司机手中隐约可见·车内暖金侧逆光与巷内冷灰形成冷暖视觉分离"
    prop_state:
      - item: "挡风玻璃(O-030)"
        state: "沙尘覆盖·干涸水渍斑痕·散射暖金光"
      - item: "皮质座椅(O-029)"
        state: "黑色皮革极度老化·龟裂褶皱"
      - item: "方向盘(O-026)"
        state: "老化皮质龟裂·司机双手握持"
    character_state:
      - character: "Rico"
        pose: "坐姿·副驾驶·身体微微转向司机侧"
        position: "挡风玻璃框内·画面右侧"
        expression: "棱角分明·面无表情·冷静"
      - character: "GoldRimmedGlassesDriver"
        pose: "坐姿·驾驶座·双手在方向盘上"
        position: "挡风玻璃框内·画面左侧"
        expression: "不可辨(车内暗部+眼镜反光模糊)"
    audio:
      ambience: "轿车引擎低沉怠速声(从巷口方向传来·略远)"
      events: []

  - sec: 7
    global_sec: 7
    camera_position: "2"
    shot_type: "中全景"
    focal_length: "35mm"
    dof: "中景深f/5.6"
    movement: "固定"
    action_anchor: "Rico右手从身侧取出信封(深色/牛皮纸色)·动作快而精准·无多余手指动作。司机左手从方向盘移至中控区上方"
    spatial_anchor: "挡风玻璃沙尘纹理持续在前景·车内空间焦点收至两人之间的中控区上方·暖金侧逆光在仪表台边缘形成清晰光切面"
    prop_state:
      - item: "信封(O-034)"
        state: "Rico右手握持·刚从身侧取出·出现在画面中"
    character_state:
      - character: "Rico"
        pose: "右手持信封向司机方向递出·动作快而精准"
        position: "挡风玻璃框内右侧"
        expression: "面无表情·眼神锁定交换物"
      - character: "GoldRimmedGlassesDriver"
        pose: "左手从方向盘移向中控区·准备交换"
        position: "挡风玻璃框内左侧"
    audio:
      ambience: "引擎怠速声持续"
      events:
        - "信封轻微摩擦声"

  - sec: 8
    global_sec: 8
    camera_position: "2"
    shot_type: "中全景"
    focal_length: "35mm"
    dof: "中景深f/5.6"
    movement: "固定"
    action_anchor: "Rico将信封递至中控区上方中央。司机右手从身侧取出一部深色手机·动作同样快而机械。两只手在中控区上方交汇·信封和手机在暖金侧逆光的光切面中"
    spatial_anchor: "画面焦点收至中控区上方·暖金侧逆光在信封表面和手机屏幕边缘形成清晰光切面·仪表台灰尘在暖光下可见颗粒"
    prop_state:
      - item: "信封(O-034)"
        state: "Rico递至中控区上方中央·暖金光切面照亮"
      - item: "手机(O-035)"
        state: "司机右手取出·深色·即将递出"
    character_state:
      - character: "Rico"
        pose: "右手持信封在中控区上方·等待交换"
        expression: "面无表情"
      - character: "GoldRimmedGlassesDriver"
        pose: "右手持手机递出·左手从方向盘移至中控区"
    audio:
      ambience: "引擎怠速声持续"
      events: []

  - sec: 9
    global_sec: 9
    camera_position: "2"
    shot_type: "中全景"
    focal_length: "35mm"
    dof: "中景深f/5.6"
    movement: "固定"
    action_anchor: "交换完成。Rico接过手机收入身侧口袋·司机接过信封放在中控台或身侧。手指接触即分离·无多余停留"
    spatial_anchor: "画面紧致:中控区上方·两只手占据画面中央·交换后的静止·仪表台灰尘和换挡杆球头油光包浆清晰·暖金光照亮手部皮肤纹理"
    prop_state:
      - item: "信封(O-034)"
        state: "司机已接收·放置中控台或身侧"
      - item: "手机(O-035)"
        state: "Rico已接收·收入身侧"
    character_state:
      - character: "Rico"
        pose: "交换完成·手收回身侧"
      - character: "GoldRimmedGlassesDriver"
        pose: "交换完成·左手回到方向盘"
    audio:
      ambience: "引擎怠速声持续"
      events:
        - "手机轻放声"

  - sec: 10
    global_sec: 10
    camera_position: "2"
    shot_type: "中全景"
    focal_length: "35mm"
    dof: "中景深f/5.6"
    movement: "固定"
    action_anchor: "交换后静止片刻。Rico手放在腿上·司机双手回到方向盘。车内恢复到交换前的静态·但信封和手机已交换位置。Rico侧脸在暖金侧逆光中半明半暗"
    spatial_anchor: "中控区+两只手(静止)+两人下半面部(暗部)·暖金光照亮方向盘顶部老化龟裂·司机金丝眼镜框边缘微光反射·车内暗部深邃黑色"
    prop_state:
      - item: "信封(O-034)"
        state: "在司机侧·已放置"
      - item: "手机(O-035)"
        state: "在Rico侧·已放置"
      - item: "金丝眼镜(O-036)"
        state: "司机佩戴·金色细框·镜片在侧逆光下反光"
    character_state:
      - character: "Rico"
        pose: "坐姿静止·手在腿上·侧脸半明半暗"
      - character: "GoldRimmedGlassesDriver"
        pose: "坐姿静止·双手在方向盘"
    audio:
      ambience: "引擎怠速声持续·车内安静"
      events: []

  - sec: 11
    global_sec: 11
    camera_position: "2"
    shot_type: "中全景"
    focal_length: "35mm"
    dof: "中景深f/5.6"
    movement: "固定"
    action_anchor: "静止延续。车内暗部深邃·暖金光照区域稳定·交换已完成的静止瞬间——暴风雨前的平静"
    spatial_anchor: "挡风玻璃沙尘纹理静止·仪表台暖金光切面稳定·后视镜反射后排暗部空间"
    prop_state: []
    character_state: []
    audio:
      ambience: "引擎怠速声持续"
      events: []

  # ═══════════════════════════════════════
  # 镜#3: 躲藏·垃圾桶后探头 [12-16s] seg_id=3
  # ═══════════════════════════════════════

  - sec: 12
    global_sec: 12
    camera_position: "3"
    shot_type: "中景"
    focal_length: "35mm"
    dof: "中景深f/5.6"
    movement: "固定"
    action_anchor: "硬切回巷道。Pedro在巷口中央猛停位置·身体快速转向后跑向巷中段靠墙的垃圾桶·动作急促·手臂摆动·身体前倾跑步姿态"
    spatial_anchor: "低角度微仰视角从Pedro身侧~1.5m处·巷口暖亮逆光在远景(轿车暗色剪影仍在)·巷中段墙面在散射光中呈冷灰色调·垃圾桶(金属圆桶·锈蚀)靠右侧墙面"
    prop_state:
      - item: "垃圾桶(O-037)"
        state: "靠右侧墙面·金属圆桶·高约1m·表面锈蚀·静止"
      - item: "黑色轿车(O-033)"
        state: "远景巷口·暗色剪影·仍在"
    character_state:
      - character: "Pedro"
        pose: "从巷口快速跑向垃圾桶方向·身体前倾"
        position: "画面中景·向画面右侧移动"
        expression: "不可见(侧身+运动模糊)"
    audio:
      ambience: "贫民窟远底噪+引擎怠速声从巷口传来"
      events:
        - "Pedro急促跑步声在碎石上"

  - sec: 13
    global_sec: 13
    camera_position: "3"
    shot_type: "中景"
    focal_length: "35mm"
    dof: "中景深f/5.6"
    movement: "固定"
    action_anchor: "Pedro到达垃圾桶后方·快速蹲下·膝盖抵胸·全身缩成一团·身体完全被垃圾桶遮挡·仅头顶和部分肩膀从桶沿上方微露"
    spatial_anchor: "巷中段·垃圾桶占据画面右侧·Pedro缩入桶后过程可见其身体从右侧边缘消失·巷中段墙面冷灰散射光均匀·左侧排水管锈蚀纹理可见"
    prop_state:
      - item: "垃圾桶(O-037)"
        state: "原位·遮挡Pedro·桶沿在画面中右区域"
    character_state:
      - character: "Pedro"
        pose: "快速蹲下·膝盖抵胸·缩成一团"
        position: "垃圾桶后方·身体被桶遮挡·仅头顶微露"
    audio:
      ambience: "引擎怠速声持续"
      events:
        - "Pedro蹲下:碎石上急促摩擦+身体撞击桶壁闷响"

  - sec: 14
    global_sec: 14
    camera_position: "3"
    shot_type: "中景"
    focal_length: "35mm"
    dof: "中景深f/5.6"
    movement: "固定"
    action_anchor: "Pedro完全静止在垃圾桶后·身体紧缩·双手扶桶·头顶在桶沿下方·从外看不到面部。垃圾桶在散射光下呈冷灰锈蚀质感"
    spatial_anchor: "静止画面:巷中段全貌·排水管·墙根青苔·碎石地面·垃圾桶靠右墙·巷口方向暖亮逆光中轿车剪影仍在·形成静态的威胁存在"
    prop_state:
      - item: "垃圾桶(O-037)"
        state: "静止靠墙·遮挡Pedro"
    character_state:
      - character: "Pedro"
        pose: "完全静止蹲姿·身体紧缩·被垃圾桶遮挡"
        position: "垃圾桶后方·不可见"
    audio:
      ambience: "引擎怠速声持续·贫民窟远底噪"
      events: []

  - sec: 15
    global_sec: 15
    camera_position: "3"
    shot_type: "中景"
    focal_length: "35mm"
    dof: "中景深f/5.6"
    movement: "固定"
    action_anchor: "Pedro极缓慢地从桶沿上方探出头·动作极其谨慎·先露出发际线·再额头·最后停在半张脸——右半脸和右眼从桶沿上方露出·手指扒着桶沿·指关节紧抓"
    spatial_anchor: "画面焦点转移至垃圾桶上方·Pedro半张脸从桶沿后浮现·巷口暖亮逆光在远景提供微弱轮廓照明"
    prop_state:
      - item: "垃圾桶(O-037)"
        state: "桶沿被Pedro手指扒住·指关节紧抓桶沿金属边"
    character_state:
      - character: "Pedro"
        pose: "极缓慢探头·手指扒桶沿·右半脸+右眼露出"
        position: "垃圾桶后方·桶沿上方"
        expression: "右眼大睁·警觉·瞳孔在暗处"
    audio:
      ambience: "引擎怠速声持续"
      events:
        - "Pedro气息声:微弱·几乎只在嘴唇间流动"

  - sec: 16
    global_sec: 16
    camera_position: "3"
    shot_type: "中景"
    focal_length: "35mm"
    dof: "中景深f/5.6"
    movement: "固定"
    action_anchor: "Pedro保持探头姿势·右半脸+右眼静止在桶沿上方·眼睛不眨·锁定巷口方向(轿车)·身体其余部分完全被桶遮挡"
    spatial_anchor: "静止·桶沿水平线分割画面·上方=Pedro半脸(冷灰散射光)·下方=桶身暗部·远景巷口暖亮+轿车剪影"
    character_state:
      - character: "Pedro"
        pose: "探头静止·手指扒桶沿·半脸露出"
        position: "垃圾桶后方·桶沿上方"
        expression: "右眼大睁·警觉注视·嘴唇紧闭"
    audio:
      ambience: "引擎怠速声·贫民窟远底噪"
      events: []

  # ═══════════════════════════════════════
  # 镜#4: 偷看POV·交易细节 [17-22s] seg_id=4
  # ═══════════════════════════════════════

  - sec: 17
    global_sec: 17
    camera_position: "4"
    shot_type: "中景(遮蔽POV)"
    focal_length: "50mm"
    dof: "浅景深f/2.8"
    movement: "固定"
    action_anchor: "切换至偷窥POV。前景:垃圾桶沿(极度虚化·深色块占据画面下方1/4)。中景:透过桶与墙壁间隙/桶沿上方看轿车挡风玻璃。车内:Rico和金丝眼镜男·暖金侧逆光中·交换刚完成后的静止"
    spatial_anchor: "极度遮蔽POV:桶沿深色虚化块在下方·桶与墙间隙形成狭窄视窗·巷中段碎石地面虚化过渡·轿车挡风玻璃框在画面中上部·沙尘纹理过滤车内画面·巷口暖亮在挡风玻璃框外过曝"
    prop_state:
      - item: "垃圾桶(O-037)"
        state: "桶沿在画面下1/4·极度虚化深色块·遮挡视野"
      - item: "挡风玻璃(O-030)"
        state: "沙尘+水渍纹理·天然画框·散射暖金光"
    character_state:
      - character: "Rico"
        pose: "坐姿静止·副驾驶·侧脸在暖金半面光中"
        position: "挡风玻璃框内右侧"
        expression: "棱角分明·面无表情"
      - character: "GoldRimmedGlassesDriver"
        pose: "坐姿静止·驾驶座·双手在方向盘"
        position: "挡风玻璃框内左侧·暗部"
    audio:
      ambience: "引擎怠速声(从巷口方向·略远)"
      events: []

  - sec: 18
    global_sec: 18
    camera_position: "4"
    shot_type: "中景(遮蔽POV)"
    focal_length: "50mm"
    dof: "浅景深f/2.8"
    movement: "固定"
    action_anchor: "偷窥视角延续。车内两人保持静止·交换已完成·暖金侧逆光照亮中控区上方·方向盘顶部皮质龟裂在暖光中纹理清晰"
    spatial_anchor: "桶沿深色虚化块静止·视觉窗口(间隙/桶沿上方)窄小·观众与Pedro共享视野限制·信息受限制造悬念"
    prop_state: []
    character_state: []
    audio:
      ambience: "引擎怠速声持续"
      events: []

  - sec: 19
    global_sec: 19
    camera_position: "4"
    shot_type: "中景(遮蔽POV)"
    focal_length: "50mm"
    dof: "浅景深f/2.8"
    movement: "固定"
    action_anchor: "车内·Rico右手微动——检查手机(翻看屏幕或放入口袋)·动作细微但可见。金丝眼镜男转头微瞥Rico方向·然后回正"
    spatial_anchor: "挡风玻璃框内·暖金侧逆光中Rico手部微动是画面唯一动态·眼镜反光微闪(司机转头时)"
    character_state:
      - character: "Rico"
        pose: "右手微动·检查手机·动作细微"
        expression: "面无表情·视线在手机上"
      - character: "GoldRimmedGlassesDriver"
        pose: "微转头瞥Rico·回正"
    audio:
      ambience: "引擎怠速声·车内极静"
      events: []

  - sec: 20
    global_sec: 20
    camera_position: "4"
    shot_type: "中景(遮蔽POV)"
    focal_length: "50mm"
    dof: "浅景深f/2.8"
    movement: "固定"
    action_anchor: "车内恢复静止。Rico手机已收好·司机双手在方向盘·暖金侧逆光在仪表台灰尘上形成稳定光切面·车内暗部深邃"
    spatial_anchor: "偷窥视角静止·桶沿深色块不变·挡风玻璃沙尘纹理不变·巷口暖亮过曝不变——时间在静止中累积紧张"
    prop_state: []
    character_state: []
    audio:
      ambience: "引擎怠速声持续"
      events: []

  - sec: 21
    global_sec: 21
    camera_position: "4"
    shot_type: "中景(遮蔽POV)"
    focal_length: "50mm"
    dof: "浅景深f/2.8"
    movement: "固定"
    action_anchor: "静止延续。车内暖金光切面无变化·暗部深黑·挡风玻璃沙尘纹理过滤使画面呈现胶片颗粒质感"
    spatial_anchor: "偷窥视角静止·观众等待·Pedro在等待·悬念在累积"
    prop_state: []
    character_state: []
    audio:
      ambience: "引擎怠速声·此刻格外清晰(视觉静默强化听觉)"
      events: []

  - sec: 22
    global_sec: 22
    camera_position: "4"
    shot_type: "中景(遮蔽POV)"
    focal_length: "50mm"
    dof: "浅景深f/2.8"
    movement: "固定"
    action_anchor: "静止延续。最后一秒的平静。车内一切如常——但观众知道Pedro在看·信息差制造双重悬念:Rico会发现Pedro吗?"
    spatial_anchor: "桶沿深色块·间隙视窗·挡风玻璃框·车内暖金+暗部·巷口暖亮——全部静止·等待打破"
    prop_state: []
    character_state: []
    audio:
      ambience: "引擎怠速声持续"
      events: []

  # ═══════════════════════════════════════
  # 镜#5: Rico转头·差点发现 [23-28s] seg_id=5
  # ═══════════════════════════════════════

  - sec: 23
    global_sec: 23
    camera_position: "5"
    shot_type: "近景"
    focal_length: "50mm"
    dof: "浅f/2.8"
    movement: "固定(Rico CU·车内)"
    action_anchor: "硬切至轿车内近景。Rico侧脸·副驾驶位。他突然转头——颈肌紧绷·头部快速转向左侧车窗外(巷口方向)·动作果断无犹豫·暖金侧逆光照亮他左半脸(颧骨·眼窝·下颌线)·右半脸在深黑阴影中"
    spatial_anchor: "车内空间紧致·Rico面部占画面左三分线·暖金侧逆光(~3500K)形成清晰明暗交界线沿鼻梁和下颌·挡风玻璃边缘在前景右侧虚化暗框·车内暗部深邃黑色"
    prop_state:
      - item: "挡风玻璃(O-030)"
        state: "前挡边缘在画面右侧虚化暗框"
    character_state:
      - character: "Rico"
        pose: "突然转头向左(巷口方向)·颈肌紧绷·动作果断"
        position: "副驾驶·画面左三分线"
        expression: "棱角分明·面无表情但眼中有警觉·扫描式视线"
    audio:
      ambience: "引擎怠速声(车内·近)"
      events: []

  - sec: 24
    global_sec: 24
    camera_position: "5"
    shot_type: "近景"
    focal_length: "50mm"
    dof: "浅f/2.8"
    movement: "固定(Rico CU·车内)"
    action_anchor: "Rico侧脸静止·目光穿过挡风玻璃看向巷口方向·扫描式视线从左向右缓慢移动。暖金光照亮颧骨和眼窝·另半脸在深黑阴影中"
    spatial_anchor: "画面紧致:挡风玻璃在前景右上方形成暗框·透过玻璃隐约可见巷口暖亮区·Rico面部暖金+深黑chiaroscuro效果"
    character_state:
      - character: "Rico"
        pose: "转头后静止·目光锁定巷口方向·视线扫描"
        expression: "扫描式视线·警觉·面无表情"
    audio:
      ambience: "引擎怠速声持续"
      events: []

  - sec: 25
    global_sec: 25
    camera_position: "5"
    shot_type: "中全景"
    focal_length: "35mm"
    dof: "中f/5.6"
    movement: "固定(POV扫描·巷口)"
    action_anchor: "POV开始:画面过渡至Rico第一人称视角·透过挡风玻璃看巷口。沙尘+水渍纹理成为前景滤镜。巷口暖亮逆光(~4500K过曝)从画面右方入画·碎石地面占据画面下方·巷口两侧墙面收束·垃圾桶暗色块靠右墙"
    spatial_anchor: "POV视角:挡风玻璃沙尘层在前景形成柔焦纹理过滤·巷口暖亮过曝区在画面右上·碎石地面向巷外延伸·垃圾桶+墙面在中景左方·Pedro身体被桶完全遮挡·只有桶的暗色轮廓"
    prop_state:
      - item: "挡风玻璃(O-030)"
        state: "POV前景·沙尘+水渍纹理过滤视线"
      - item: "垃圾桶(O-037)"
        state: "靠右墙·暗色剪影在巷口暖亮背景中·Pedro在其后不可见"
    character_state: []
    audio:
      ambience: "引擎怠速声(车内)"
      events: []

  - sec: 26
    global_sec: 26
    camera_position: "5"
    shot_type: "中全景"
    focal_length: "35mm"
    dof: "中f/5.6"
    movement: "固定(POV扫描·巷口)"
    action_anchor: "POV扫描继续:视线从左向右水平扫过巷口。扫过碎石地面纹理·积水洼反射天光·墙面灰泥剥落处·垃圾桶轮廓——在Pedro躲藏位置没有停留·Rico没有发现Pedro"
    spatial_anchor: "POV扫描中·挡风玻璃沙尘纹理在前景静态·巷口全景在背景缓慢右移——碎石→墙面→垃圾桶依次入画·扫描经过垃圾桶区域"
    prop_state: []
    character_state: []
    audio:
      ambience: "引擎怠速声持续"
      events: []

  - sec: 27
    global_sec: 27
    camera_position: "5"
    shot_type: "极端特写"
    focal_length: "85mm"
    dof: "浅f/2.8"
    movement: "固定(影子ECU·碎石)"
    action_anchor: "POV扫描结束·视线停在碎石地面上。足球的影子——一个深色椭圆在碎石上·边缘有半影过渡带·影子内部非纯黑(碎石间隙透射巷口暖光和天空光形成细小亮斑镶嵌)"
    spatial_anchor: "画面定格:碎石地面近景·球的影子深色椭圆占据画面下三分之一·碎石粒径不一·干泥填隙·球的影子是画面中唯一的不规则元素"
    prop_state:
      - item: "旧足球(O-032)"
        state: "球体在画面外(上方或侧方)·仅影子可见在碎石上"
    character_state: []
    audio:
      ambience: "引擎怠速声持续"
      events: []

  - sec: 28
    global_sec: 28
    camera_position: "5"
    shot_type: "极端特写"
    focal_length: "85mm"
    dof: "浅f/2.8"
    movement: "固定(影子ECU·碎石)"
    action_anchor: "球的影子静止在碎石上。Rico的目光在此停留——一段静默。碎石地面微坡·球的影子在散射光中呈深灰·半影边缘过渡柔和·碎石间隙透光形成亮斑镶嵌"
    spatial_anchor: "固定ECU画面:碎石微距·球的影子深色椭圆占据画面下三分之一·碎石间隙中的细小亮斑散布在影子内部和外部·自然光影纹理"
    prop_state: []
    character_state: []
    audio:
      ambience: "引擎怠速声·格外清晰(视觉静默强化听觉)"
      events: []

  # ═══════════════════════════════════════
  # 镜#6: Pedro反应·缩回·恐惧 [29-33s] seg_id=6
  # ═══════════════════════════════════════

  - sec: 29
    global_sec: 29
    camera_position: "6"
    shot_type: "极端特写"
    focal_length: "85mm"
    dof: "极浅景深f/2.0"
    movement: "固定"
    action_anchor: "硬切回垃圾桶后。Pedro右半脸+右眼ECU·桶沿在画面下1/3(极度虚化深色块)。Pedro眼睛瞬间瞪大——看到Rico转头·瞳孔中暖色高光点如针尖·眼白可见血丝。然后面部急速向下沉——缩回避让·右眼从桶沿上方消失·画面只剩桶沿深色虚化块和暗部背景"
    spatial_anchor: "画面紧缩:桶沿深色块占据下方·Pedro面部从存在到消失·背景巷内墙面在极浅景深下完全虚化为冷灰色调"
    prop_state:
      - item: "垃圾桶(O-037)"
        state: "桶沿在画面下1/3·极度虚化·Pedro缩回后桶沿上方无面部"
    character_state:
      - character: "Pedro"
        pose: "眼睛瞪大->身体后缩·面部急速下沉消失·背部撞墙"
        position: "垃圾桶后方·缩回避让·不可见"
        expression: "恐惧·眼睛瞪大·瞳孔暖色高光点(缩回前瞬间)"
    audio:
      ambience: "引擎怠速声持续(从巷口方向·略远)"
      events:
        - "Pedro气息声:急促·几乎听清 CV:又是他——"

  - sec: 30
    global_sec: 30
    camera_position: "6"
    shot_type: "极端特写"
    focal_length: "85mm"
    dof: "极浅景深f/2.0"
    movement: "固定"
    action_anchor: "桶沿上方为空——Pedro已完全缩回桶后。画面仅剩桶沿深色虚化块+背景冷灰虚化·巷口暖色远光在背景微渗透·Pedro呼吸声可闻"
    spatial_anchor: "ECU固定:桶沿虚化深色块占据画面下1/3·背景为巷内墙面(完全虚化冷灰)·巷口方向微弱的暖色渗透在画面右上角"
    character_state:
      - character: "Pedro"
        pose: "缩在桶后·背部贴墙·完全不可见"
        position: "垃圾桶后方·完全遮蔽"
        expression: "不可见"
    audio:
      ambience: "引擎怠速声"
      events:
        - "Pedro急促呼吸声(桶后·微弱)"

  - sec: 31
    global_sec: 31
    camera_position: "6"
    shot_type: "极端特写"
    focal_length: "85mm"
    dof: "极浅景深f/2.0"
    movement: "固定"
    action_anchor: "桶沿上方仍为空。静止。Pedro在桶后的呼吸声渐缓。巷口引擎声仍在·Rico还在扫描——悬念未解"
    spatial_anchor: "固定ECU:桶沿虚化+背景冷灰·画面几乎静止·仅有微弱的光线微动(巷口暖光在墙面上的微偏移)"
    prop_state: []
    character_state: []
    audio:
      ambience: "引擎怠速声"
      events:
        - "Pedro呼吸声:渐缓·但仍有紧张"

  - sec: 32
    global_sec: 32
    camera_position: "6"
    shot_type: "极端特写"
    focal_length: "85mm"
    dof: "极浅景深f/2.0"
    movement: "固定"
    action_anchor: "极缓慢地·Pedro右眼重新从桶沿上方浮现——先睫毛·再眼睑·最后眼睛完全露出。右眼大睁·瞳孔中暖色高光点(巷口远光反射)重新出现·他还在确认:Rico是否还在看?"
    spatial_anchor: "桶沿上方·Pedro右眼重新出现·眼睫毛清晰·瞳孔暖色高光点如针尖·桶沿深色虚化块不变·背景冷灰虚化不变·Pedro面部其余部分仍在桶后暗部"
    character_state:
      - character: "Pedro"
        pose: "极缓慢重新探头·右眼从桶沿上方浮现"
        position: "垃圾桶后方·桶沿上方·仅右眼露出"
        expression: "恐惧未消·右眼大睁·确认威胁是否仍在"
    audio:
      ambience: "引擎怠速声·然后引擎声微变——Rico转回头·轿车准备驶离"
      events:
        - "Pedro气息声:极微弱·近乎无声"

  - sec: 33
    global_sec: 33
    camera_position: "6"
    shot_type: "极端特写"
    focal_length: "85mm"
    dof: "极浅景深f/2.0"
    movement: "固定"
    action_anchor: "Pedro右眼保持静止在桶沿上方·瞳孔中暖色高光点稳定·恐惧未消但未再缩回——他确认了:轿车还在·但Rico已转回头"
    spatial_anchor: "ECU:右眼+桶沿虚化+冷灰背景·画面结构与29秒相似但情绪不同——从恐惧峰值过渡到恐惧余波·Pedro的身体仍紧绷但不再逃离"
    character_state:
      - character: "Pedro"
        pose: "探头静止·右眼锁定巷口"
        expression: "恐惧未消·瞳孔暖色高光点·嘴唇紧闭"
    audio:
      ambience: "引擎声从怠速转为启动驶离的低沉轰鸣·音调变化"
      events: []

  # ═══════════════════════════════════════
  # 镜#7: 轿车驶离·Pedro前景锚点 [34-38s] seg_id=7
  # ═══════════════════════════════════════

  - sec: 34
    global_sec: 34
    camera_position: "7"
    shot_type: "远景"
    focal_length: "24mm"
    dof: "深景深f/8"
    movement: "极慢前推(0.03x)·起幅·距Pedro~1.00m"
    action_anchor: "硬切至巷道远景。低角度·OTS Pedro。Pedro头部/肩膀剪影(暗色块·画面右下·略微虚化)。中远景:轿车从巷口位置发动·车身暗色块在暖亮逆光中开始移动·向巷尾方向驶离"
    spatial_anchor: "低角度远景(~0.5m·Pedro蹲姿肩高):两侧砖墙向巷口收窄·碎石地面从画面下方向巷口延伸·Pedro前景剪影在右下锚定画面·轿车在巷口暖亮区中央·开始横向移动"
    prop_state:
      - item: "黑色轿车(O-033)"
        state: "发动·开始从巷口驶离·暗色块在暖亮中移动"
      - item: "旧足球(O-032)"
        state: "球体在碎石地面某处(画面外)·球的影子仍可见"
    character_state:
      - character: "Pedro"
        pose: "蹲姿静止·头部/肩膀在画面右下·剪影/暗色块"
        position: "垃圾桶后方·画面右下前景锚点"
        expression: "不可见(背对镜头·剪影)"
    audio:
      ambience: "轿车引擎加速声·由近渐远"
      events: []

  - sec: 35
    global_sec: 35
    camera_position: "7"
    shot_type: "远景"
    focal_length: "24mm"
    dof: "深景深f/8"
    movement: "极慢前推(0.03x)·匀速·距Pedro~0.97m"
    action_anchor: "轿车继续驶离·暗色块在画面中向巷口侧方缩小·车身在暖亮逆光中从完整剪影变为渐小暗块·尾灯红色点光源在暖金背景中微亮"
    spatial_anchor: "固定远景:Pedro前景剪影不变·碎石地面纵深·巷道墙面透视·轿车从巷口中央移至侧方·体积缩小·巷口暖亮开始恢复完整(不再被轿车遮挡)"
    prop_state: []
    character_state: []
    audio:
      ambience: "轿车引擎声渐远"
      events: []

  - sec: 36
    global_sec: 36
    camera_position: "7"
    shot_type: "远景"
    focal_length: "24mm"
    dof: "深景深f/8"
    movement: "极慢前推(0.03x)·匀速·距Pedro~0.94m"
    action_anchor: "轿车逐渐消失在巷口侧方·暖亮过曝区恢复完整——午后的日常光线重新填满巷口。Pedro前景剪影保持不变·没有起身"
    spatial_anchor: "空巷远景:无车辆·暖亮巷口完整恢复·碎石地面·两侧墙面·头顶一线天·Pedro前景剪影右下——故事未结束·Pedro仍未动"
    prop_state:
      - item: "黑色轿车(O-033)"
        state: "驶离·消失在巷口侧方/巷尾方向·不再可见"
    character_state: []
    audio:
      ambience: "轿车引擎声远去至消失·贫民窟远底噪恢复"
      events: []

  - sec: 37
    global_sec: 37
    camera_position: "7"
    shot_type: "远景"
    focal_length: "24mm"
    dof: "深景深f/8"
    movement: "极慢前推(0.03x)·匀速·距Pedro~0.91m"
    action_anchor: "巷口空荡·暖亮逆光完整。碎石地面上球的影子仍在。Pedro前景剪影静止。巷道恢复日常——但紧张感残留在画面中·Pedro的身体语言传递着恐惧未消"
    spatial_anchor: "固定远景:低角度·Pedro剪影右下·碎石地面纵深·巷口暖亮·头顶一线天·排水管·垃圾桶·全部静止·日常恢复但记忆残留"
    character_state:
      - character: "Pedro"
        pose: "蹲姿静止·未起身·身体仍紧缩"
        position: "垃圾桶后方·画面右下前景剪影"
    audio:
      ambience: "贫民窟远底噪(远处人声·狗吠·电视声恢复)"
      events: []

  - sec: 38
    global_sec: 38
    camera_position: "7"
    shot_type: "远景"
    focal_length: "24mm"
    dof: "深景深f/8"
    movement: "极慢前推(0.03x)·落幅·距Pedro~0.85m"
    action_anchor: "最后一个画面静持。Pedro前景剪影·空巷口暖亮·球的影子·冷灰墙面。Pedro没有起身——刚才看到的一切已经改变了他。贫民窟午后的日常恢复了·但在这个男孩的眼睛里·世界已经不同"
    spatial_anchor: "固定远景:全纵深清晰·无运动元素·仅有光影——巷口暖亮渐变至巷内冷灰·Pedro剪影=叙事锚点·静止的时间·等待下一场景"
    prop_state: []
    character_state:
      - character: "Pedro"
        pose: "蹲姿静止·未起身·身体紧缩"
        position: "垃圾桶后方·画面右下前景剪影"
    audio:
      ambience: "贫民窟远底噪持续·渐渐过渡至下一场景环境声"
      events: []
```

---

# 场景末状态快照

```yaml
scene_end_snapshot:
  time: "午后·阴天·场景结束"
  location:
    alley: "空无一人·碎石地面·球的影子仍在·垃圾桶靠右墙·巷口暖光完整"
    car: "已驶离·去向不明"
  characters:
    Pedro: "蹲在垃圾桶后·未起身·恐惧未消·刚目睹了一场秘密交易"
    Rico: "在驶离的轿车内·已接收手机·信封已交给司机"
    GoldRimmedGlassesDriver: "驾驶轿车离开·已接收信封"
  props:
    旧足球O-032: "在巷口碎石地上·球的影子在碎石上"
    黑色轿车O-033: "已驶离·去向不明"
  unresolved_tension:
    - "Rico是否看到了足球影子? 他停留的几秒意味着什么?"
    - "Pedro看到了什么? 他理解了多少?"
    - "轿车驶向何处? Rico的下一个目的地?"
```

---

## 三域合并来源签注

```
┌────────────────────────────────────────────────────┐
│  TIME_SKELETON 合并签注                              │
│                                                      │
│  §A Global Anchors:                                  │
│    → EP14_S2_SCENE_DESIGNER.md  §6 构图光影域YAML    │
│    → global_anchors (character + environment          │
│        + style_spine + lighting + constraints)       │
│                                                      │
│  §B TIME_SKELETON:                                   │
│    segments[].camera:                                  │
│      → SCENE_DESIGNER §4 机位域YAML                   │
│    segments[].movement:                               │
│      → MOVEMENT_DESIGNER §5 运镜域YAML                │
│    transitions:                                       │
│      → MOVEMENT_DESIGNER segments_transitions        │
│    frames[].hard (camera_position/shot_type/          │
│                   focal_length/dof):                 │
│      → SCENE_DESIGNER frames_hard                    │
│    frames[].movement:                                 │
│      → MOVEMENT_DESIGNER frames_movement              │
│    frames[].soft (action_anchor/spatial_anchor/       │
│                   prop_state/character_state/audio):  │
│      → SCENE_DESIGNER frames_soft                     │
│                                                      │
│  合并日期: 2026-07-07                                │
│  场景ID: EP14 S2 · 贫民窟巷道                         │
│  7镜 · 39秒 · 39帧 · 6过渡                            │
│  下游: storyboard_planner(Step A2.5) ·                │
│        prompt_composer(Step A3)                       │
└────────────────────────────────────────────────────┘
```
