# EP14_S1_SCENE_DESIGNER_SLEVEL — 案情室 · S-Level合并设计+台本初稿

> **Prompter:** Scene Designer v1.0 (S-Level)
> **场景:** EP14场景A · 圣保罗刑警总部·案情室 · 7镜·31秒
> **复杂度:** 🟢 S-Level · F1=1·F2=2·F3=4·F4=86%·F5=false·F6=false·F7=3
> **渲染目标:** Seko画布 · Seedance 2.0
> **静态快速通道:** 激活 · 6/7镜固定 · 仅镜#A2含运镜(极慢前推0.05x·S1)
> **格式规范:** s_level_script_format_v1.0.md
> **输出规模目标:** ≤600行

---

## §3 Step 0: 空间坐标系（三域共享·只写一次）

```
📐 场景类型: 双人对话(2人·Vincent仅门口不入室)
   角色数: 2 · complexity: S · KB章节: §1.1-1.3双人对话·§4构图·§6光影

空间坐标系:
  尺寸: ~6m纵深 × ~4m宽 × ~3m高 · 面积~24m²
  北墙: 巨大白色白板(~3-4m宽·占满墙面·视觉重心·人物照片+红线+平面图+弹道报告)
  南侧: 合并办公桌×2·距白板~1-2m·文件/笔记本/咖啡杯/笔记本电脑堆叠
  西墙: 灰色金属门(宽~1m·高~2.1m·不锈钢把手)·外连走廊(3500K暖黄光·推断)
  东墙: 素灰墙面·无窗
  天花板: 四个方形格栅发光顶灯(5000K冷白·均匀·无影灯设计)

人物可放置区域:
  ① 白板前·距白板~0.5-1m (站姿·1人·可指认线索)
  ② 桌前工作位 (坐姿·1人)
  ③ 桌前·距白板~2-3m (站姿·1-2人)
  ④ 桌侧 (站姿·1人)
  ⑤ 房间中央·距白板~3m (站姿·1人·全景机位)

禁入区: 墙体内·桌下·白板与墙面间隙

180度线设定:
  关系线: Miguel↔白板(对话场景中Miguel与白板线索墙的"对话")
  轴线侧: 白板侧(北)·选择理由: 白板是场景视觉重心·机位全在北侧半圆
  过波镜: 无越轴需求·全场景维持同一侧

光源物理锚点:
  L1-主光源: 天花板格栅灯×4, 5000K, 冷白, 柔光·锚定于参考图上排
  L2-屏幕光: 笔记本电脑, ~6500K, 冷蓝微光, 桌面局部·锚定于参考图下排
  L3-走廊光: 门外走廊暖黄光, 3500K, 软光, 仅镜#A4/#A7·锚定于空间地图西墙门
```

---

## §7.1 机位域YAML（segments_camera + frames_hard）

```yaml
scene:
  id: "EP14_S1"
  name: "案情室"
  type: "室内·制度空间·双人对话"
  total_duration_sec: 31
  complexity_level: "S"

segments_camera:
  - segment_id: "①"
    time_range: [0, 4]
    shot_type: "全景"
    focal_length: "24mm"
    dof: "深景深f/8"
    angle: "眼平"
    kb_rule_ids: ["D-TRI-03", "C-FI-03", "C-DEP-01"]

  - segment_id: "②"
    time_range: [5, 9]
    shot_type: "大特写"
    focal_length: "100mm"
    dof: "浅景深f/2.8"
    angle: "眼平"
    kb_rule_ids: ["D-TRI-05", "C-FI2-NS-16"]

  - segment_id: "③"
    time_range: [10, 14]
    shot_type: "中景"
    focal_length: "35mm"
    dof: "中等景深f/5.6"
    angle: "眼平"
    kb_rule_ids: ["D-TRI-03", "C-KTZ-01"]

  - segment_id: "④"
    time_range: [15, 18]
    shot_type: "中近景"
    focal_length: "50mm"
    dof: "浅景深f/2.8"
    angle: "眼平"
    kb_rule_ids: ["D-TRI-05", "C-FI-14"]

  - segment_id: "⑤"
    time_range: [19, 22]
    shot_type: "近景"
    focal_length: "50mm"
    dof: "浅景深f/2.8"
    angle: "眼平"
    kb_rule_ids: ["D-TRI-05"]

  - segment_id: "⑥"
    time_range: [23, 28]
    shot_type: "中景"
    focal_length: "35mm"
    dof: "中等景深f/5.6"
    angle: "眼平"
    kb_rule_ids: ["D-TRI-03", "M-MOT-01"]

  - segment_id: "⑦"
    time_range: [29, 31]
    shot_type: "中全景"
    focal_length: "24mm"
    dof: "深景深f/8"
    angle: "眼平"
    kb_rule_ids: ["D-TRI-03"]

frames_hard:
  - {sec: 0, global_sec: 0, camera_position: "①", shot_type: "全景", focal_length: "24mm"}
  - {sec: 5, global_sec: 5, camera_position: "②", shot_type: "大特写", focal_length: "100mm"}
  - {sec: 10, global_sec: 10, camera_position: "③", shot_type: "中景", focal_length: "35mm"}
  - {sec: 15, global_sec: 15, camera_position: "④", shot_type: "中近景", focal_length: "50mm"}
  - {sec: 19, global_sec: 19, camera_position: "⑤", shot_type: "近景", focal_length: "50mm"}
  - {sec: 23, global_sec: 23, camera_position: "⑥", shot_type: "中景", focal_length: "35mm"}
  - {sec: 29, global_sec: 29, camera_position: "⑦", shot_type: "中全景", focal_length: "24mm"}
```

---

## §7.2 运镜域YAML（segments_movement + transitions）

```yaml
segments_movement:
  - segment_id: "①"
    movement: "固定"
    movement_speed_tier: "S0"
    kb_rule_ids: ["M-MOT-01"]

  - segment_id: "②"
    movement: "固定→极慢前推0.05x·匀速·沿光轴·行程约20cm·4秒"
    movement_speed_tier: "S1"
    kb_rule_ids: ["M-MOT-01", "M-MOT-04"]

  - segment_id: "③"
    movement: "固定"
    movement_speed_tier: "S0"
    kb_rule_ids: ["M-MOT-01"]

  - segment_id: "④"
    movement: "固定"
    movement_speed_tier: "S0"
    kb_rule_ids: ["M-MOT-01"]

  - segment_id: "⑤"
    movement: "固定"
    movement_speed_tier: "S0"
    kb_rule_ids: ["M-MOT-01"]

  - segment_id: "⑥"
    movement: "固定"
    movement_speed_tier: "S0"
    kb_rule_ids: ["M-MOT-01"]

  - segment_id: "⑦"
    movement: "固定"
    movement_speed_tier: "S0"
    kb_rule_ids: ["M-MOT-01"]

segments_transitions:
  - {transition_id: "①→②", from_segment: "①", to_segment: "②", transition_type: "硬切", time_range: [4, 5], path: "—", speed: "瞬时", visual_change: "全景建立→ECU红图钉·景别跳变4级·视觉冲击"}
  - {transition_id: "②→③", from_segment: "②", to_segment: "③", transition_type: "硬切", time_range: [9, 10], path: "—", speed: "瞬时", visual_change: "ECU→中景·空间扩展·Miguel后退一步·角色从微观进入空间"}
  - {transition_id: "③→④", from_segment: "③", to_segment: "④", transition_type: "硬切", time_range: [14, 15], path: "—", speed: "瞬时", visual_change: "中景→中近景·Vincent探头·新角色引入"}
  - {transition_id: "④→⑤", from_segment: "④", to_segment: "⑤", transition_type: "硬切", time_range: [18, 19], path: "—", speed: "瞬时", visual_change: "中近景→近景·Miguel面部反应·情绪聚焦"}
  - {transition_id: "⑤→⑥", from_segment: "⑤", to_segment: "⑥", transition_type: "硬切", time_range: [22, 23], path: "—", speed: "瞬时", visual_change: "近景→中景·Miguel拿起夹克和车钥匙·动作转折"}
  - {transition_id: "⑥→⑦", from_segment: "⑥", to_segment: "⑦", transition_type: "硬切", time_range: [28, 29], path: "—", speed: "瞬时", visual_change: "中景→中全景·Miguel走向门口·空间扩展"}
```

---

## §7.3 构图光影域YAML（global_anchors + frames_soft）

```yaml
global_anchors:
  character:
    Miguel: "Latin male, 30-40s, short black curly hair with greying temples, wide cheekbones, square jaw, vertical crease between brows, deep brown eyes with detective scrutiny, solid build, 浅灰衬衫(纽扣领), 深藏青警探夹克(哑光面料·拉链立领·镜#A1-A5未穿·镜#A6穿上)"
    Vincent: "Male, 30-40s, dark brown short hair slightly disheveled, thin build, cold white skin tone, 白色实验室外套(长款·及膝)+内搭深色衬衫, 黑框眼镜(黑色板材·矩形框·核心视觉识别物)"

  environment:
    description: "圣保罗刑警总部案情室·日间·全封闭室内(~6m×4m×3m)·无窗·纯人工照明·素灰色墙面·强烈单点透视。北墙巨大白板(~3-4m宽·占满)·人物照片+红线网络+建筑平面图(201红圈)+弹道报告。南侧合并办公桌×2·距白板~1-2m。西墙灰色金属门(宽~1m·高~2.1m)·外连走廊(3500K暖黄)。天花板四个方形格栅发光顶灯(5000K冷白·均匀·无影灯设计)"

  style_spine:
    description: "shot on Arri Alexa 35, cold-white institutional 5000K, neutral-gray palette, blood-red accent as vascular metaphor, frame-within-frame composition motif, single-point perspective, static-dominant camera language"
    palette_anchors: ["cold-white-5000K", "neutral-gray", "pure-white-whiteboard", "blood-red-accent", "warm-yellow-3500K-corridor", "dark-navy-jacket", "gold-badge-gleam"]

  lighting:
    description: "主光源: 天花板格栅灯×4, 5000K冷白, 柔光·均匀扩散·无影灯·全室覆盖·低光比1:1~1:2。第二光源: 笔记本电脑屏幕~6500K冷蓝微光·桌面局部。第三光源: 门外走廊暖黄光3500K·仅镜#A4/#A7出现"
    anchor_in_reference: "参考图上排·天花板正中格栅灯"

  constraints:
    - "白板文字=后期叠加·画面中仅呈现照片色块和红线网络(P-FAL-08)"
    - "面部比例全程一致·五官不漂移"
    - "Miguel肤色作为色温计——冷白下偏灰偏蜡→暖黄下回暖"
    - "跨镜色温一致: 同光源条件下色温锁定"

frames_soft:
  - {sec: 0, global_sec: 0, camera_position: "①", action_anchor: "Miguel背对镜头站立在白板前·距白板约0.5m·面向白板线索墙凝视。深藏青夹克搭在椅背上。三层纵深:前景桌面(30%)→中景Miguel背影(25%)→后景白板(45%)。单点透视汇聚至白板中央", spatial_anchor: "全室5000K冷白均匀照明·低光比1:1.5·灰色调90%+红色5-10%", prop_state: [{item: "白板", state: "人物照片+红线+平面图+弹道报告(文字后期叠加)"}, {item: "夹克", state: "搭在椅背·未穿"}, {item: "笔记本电脑", state: "屏幕亮·弹壳对比图(~6500K冷蓝微光)"}], character_state: [{character: "Miguel", pose: "背对镜头站立·距白板0.5m", position: "白板前·区域①", expression: null}], audio: {ambience: "低音量空调运行声·办公室底噪", events: []}}
  
  - {sec: 1, global_sec: 1, camera_position: "①", action_anchor: "Miguel背身站位稳定·面向白板观察·全室透视不变", spatial_anchor: "同t=0s", prop_state: [], character_state: [{character: "Miguel", pose: "稳定站立·观察白板", position: "白板前·区域①", expression: null}], audio: {ambience: "持续", events: []}}

  - {sec: 5, global_sec: 5, camera_position: "②", action_anchor: "ECU·Miguel右手拇指按压红图钉·食指稳定照片·图钉刺入白板表面·照片边框压住下层面孔·红线从图钉帽下绷直延伸至'201'红圈", spatial_anchor: "极浅景深·背景完全虚化·红图钉+红线为画面唯一焦点·5000K冷白光下图钉金属帽微反光", prop_state: [{item: "红图钉", state: "被拇指压入白板·钉帽微反光"}, {item: "红线", state: "绷直·从图钉延伸至201红圈"}], character_state: [{character: "Miguel", pose: "右手按压图钉·拇指+食指精准控制", position: "白板前·距白板~0.5m", expression: "眼睑微垂·视线聚焦图钉位置"}], audio: {ambience: "持续底噪", events: ["t=5s: 图钉刺入白板·轻微噗声"]}}

  - {sec: 10, global_sec: 10, camera_position: "③", action_anchor: "Miguel后退一步·身体重心后移·双臂微垂·从白板前后退至距白板约1.5m·审视红线网络全貌。夹克仍在椅背上", spatial_anchor: "中景·Miguel全身+白板局部·5000K冷白均匀照明·白板占背景", prop_state: [{item: "白板", state: "红线网络全貌可见"}], character_state: [{character: "Miguel", pose: "站立·重心后移·双臂微垂·审视姿态", position: "白板前·距白板~1.5m·区域③", expression: "眉心微皱·深棕色眼睛审视红线连接逻辑"}], audio: {ambience: "持续", events: ["t=10-11s: 后退一步·鞋底与地面轻微摩擦声"]}}

  - {sec: 15, global_sec: 15, camera_position: "④", action_anchor: "门框构图·Vincent从走廊探头·身体在走廊·头微倾探入案情室·一半脸在门框后·黑框眼镜在3500K暖黄光下镜片反射减少", spatial_anchor: "西墙门框为自然画框·门内5000K冷白 vs 门外3500K暖黄冷暖交界·门框切割光柱", prop_state: [{item: "门", state: "半开·不锈钢把手"}, {item: "黑框眼镜", state: "镜片反射减少·眼睛可见"}], character_state: [{character: "Vincent", pose: "身体在走廊·头微倾探入·一半脸在门框后", position: "门口·西墙门外", expression: "透过镜片看向Miguel"}], audio: {ambience: "走廊轻微回声", events: ["t=15s: 门把手转动声", "t=15.5s: Vincent: 'Miguel. A Clara pediu para avisar——'"]}}

  - {sec: 19, global_sec: 19, camera_position: "⑤", action_anchor: "Miguel近景·面部占据画面·冷白5000K下肤色偏灰偏蜡·眉心间竖纹深刻·深棕色眼睛呈现刑警的审视感·对Vincent的话语做出微反应", spatial_anchor: "近景浅景深·Miguel面部为焦点·5000K冷白制度光·背景虚化", prop_state: [], character_state: [{character: "Miguel", pose: "站立·面向门方向", position: "白板前·区域③", expression: "眉心微皱加深·唇线微收·听到Clara名字时眼睑微动"}], audio: {ambience: "持续", events: ["t=19s: Vincent继续: '——que o relatório preliminar já está pronto.'"]}}

  - {sec: 23, global_sec: 23, camera_position: "⑥", action_anchor: "Miguel果断拿起搭在椅背的深藏青夹克+桌上车钥匙·从'分析者'切换到'行动者'·哑光面料在冷白光下呈现制度质感·金色警徽金属反光", spatial_anchor: "中景·Miguel+办公桌+椅背·5000K冷白·桌面局部~6500K屏幕光", prop_state: [{item: "夹克", state: "从椅背被拿起→穿上"}, {item: "车钥匙", state: "从桌面被拿起"}, {item: "警徽", state: "金色·冷白光下制度光泽"}], character_state: [{character: "Miguel", pose: "拿起夹克穿上·拿起车钥匙·动作果断", position: "桌前·区域②", expression: "眉心竖纹仍在·表情从审视转为决断"}], audio: {ambience: "持续", events: ["t=23s: 夹克面料摩擦声", "t=24s: 车钥匙金属碰撞声"]}}

  - {sec: 29, global_sec: 29, camera_position: "⑦", action_anchor: "Miguel走向门口·身体一半面光(室内5000K冷白)·一半阴影(走廊3500K暖黄)·框在门框中·走廊暖黄光在Miguel面部形成冷暖过渡", spatial_anchor: "中全景·门框构图·冷暖交界线·门外走廊暖黄光漫射入室·矩形光柱", prop_state: [], character_state: [{character: "Miguel", pose: "走向门口·身体框在门框中·一半冷白一半暖黄", position: "门口·西墙", expression: "面部冷暖过渡·冷白侧=制度·暖黄侧=行动"}], audio: {ambience: "走廊回声·门框声学变化", events: ["t=29s: 脚步声·从室内地板过渡到走廊"]}}
```

---

## ═══════════ S-Level 导演台本初稿 ═══════════

> **Prompter:** Scene Designer v1.0 (S-Level)
> **场景:** EP14场景A · 圣保罗刑警总部·案情室 · 7镜·31秒
> **复杂度:** 🟢 S-Level · F1=1·F2=2·F3=4·F4=86%·F5=false·F6=false
> **渲染目标:** Seko画布 · Seedance 2.0
> **静态快速通道:** 激活 · 6/7镜固定 · 仅镜#A2含运镜(极慢前推0.05x·S1)

---

## 【场景级共享锚点】

### @参考图声明
@图片1: [[案情室_上排]] — 用途: 全室空间布局锚定·双桌合并·白板后墙·格栅顶灯·单点透视
@图片2: [[案情室_中排]] — 用途: 白板线索墙信息密度锚定·人物照片·红线网络·建筑平面图
@图片3: [[案情室_下排]] — 用途: 桌面工作细节确认·笔记本·咖啡杯·签字笔·图钉特写

### C1 Character Anchor（逐字锁定）
Miguel: "Latin male, 30-40s, short black curly hair with greying temples, wide cheekbones, square jaw, vertical crease between brows, deep brown eyes with detective scrutiny, solid build, 浅灰衬衫(纽扣领), 深藏青警探夹克(哑光面料·拉链立领·镜#A1-A5未穿·镜#A6穿上), 金色警徽左胸前(盾形·浮雕鹰+星环), 深色金属腕表(黑色表盘)"

Vincent: "Male, 30-40s, dark brown short hair slightly disheveled, thin build, cold white skin tone, 白色实验室外套(长款·及膝)+内搭深色衬衫, 黑框眼镜(黑色板材·矩形框·核心视觉识别物)"

### C2 Environment Anchor（逐字锁定·五要素）
日间 · 圣保罗刑警总部案情室 · 全封闭室内(~6m×4m×3m)·无窗·纯人工照明 · 天花板格栅灯5000K冷白 · 北墙巨大白板(~3-4m宽·占满·人物照片+红线网络+建筑平面图+弹道报告)·南侧合并办公桌×2·西墙灰色金属门(外连走廊3500K暖黄)·东墙素灰·强烈单点透视

### C3 Lighting Anchor（逐字锁定·锚点可追溯）
主光源: 天花板方形格栅发光顶灯×4 · 5000K冷白 · 柔光·大面积均匀扩散·无影灯设计 · 全室覆盖·低光比1:1~1:2 · 锚定于参考图上排
第二光源a: 笔记本电脑屏幕 · ~6500K冷蓝微光 · 桌面局部半径~0.3m · 锚定于参考图下排
第二光源b: 门外走廊暖黄光 · 3500K · 软光·矩形光柱 · 仅镜#A4/#A7出现 · 锚定于空间地图西墙门

### C4 Style Spine & Palette
风格: "shot on Arri Alexa 35, cold-white institutional 5000K, neutral-gray palette, blood-red accent as vascular metaphor, frame-within-frame composition motif, single-point perspective, static-dominant camera language"
调色板: cold-white-5000K · neutral-gray · pure-white-whiteboard · blood-red-accent · warm-yellow-3500K-corridor · dark-navy-jacket · gold-badge-gleam

### 场景级禁止
1. 白板文字(名字/日期/弹道报告)=后期叠加·画面中仅呈现照片色块和红线网络(P-FAL-08)
2. 面部比例全程一致·五官不漂移
3. Miguel肤色作为色温计——冷白下偏灰偏蜡(分析者)→暖黄下回暖(行动者)
4. 跨镜色温一致: 同光源条件下色温锁定·无闪烁
5. 画面稳定无晃动·动作流畅自然

---

━━━ 镜#A1: 全景 · 5秒 ━━━

### 【镜头参数卡】
- 景别: 全景(LS)
- 焦距: 24mm
- 机位: 房间中央·距白板~3m·区域⑤ · 锚定于参考图上排
- 运镜: 固定(S0)
- 角度: 眼平·高度1.6m
- 时长: 5秒 (场景内t=0~4)
- KB: D-TRI-03 M-MOT-01

### 【传入参考图】
@图片1: [[案情室_上排]] — 用途: 全室空间布局·双桌·白板·格栅灯·单点透视锚定
@图片2: [[案情室_中排]] — 用途: 白板线索墙信息密度确认
@图片3: [[案情室_下排]] — 用途: 桌面工作细节确认

### 【生成指令】
Subject: Miguel · 白板前站姿·背对镜头
Action:
  t=0s: Miguel背对镜头站立在白板前·距白板约0.5m·面向白板线索墙凝视。深藏青夹克搭在椅背上(画面前景·椅背可见夹克轮廓和哑光面料质感)。白板上人物照片色块+红线血管状网络+建筑平面图(红色201圈注)+弹道报告色块——文字为后期叠加。前景合并办公桌×2——文件堆叠·翻开横线笔记本·黑色签字笔·黑色咖啡杯·笔记本电脑屏幕亮(弹壳对比图·~6500K冷蓝微光)。三层纵深:前景桌面(30%)→中景Miguel背影(25%)→后景白板(45%)。单点透视汇聚至白板中央。四个方形格栅顶灯·5000K冷白·全室均匀照明·低光比1:1.5。基调:灰色90%+红色5-10%。Miguel肤色不可见(背身)
  t=1s: 画面同t=0s。Miguel背身站位稳定·面向白板观察·全室透视不变
  t=2s: 画面同t=0s。白板上红线网络在冷白光下为唯一饱和色·形成视觉引导路径
  t=3s: 画面同t=0s。全室制度秩序的几何化构图——封闭构图·深空间
  t=4s: 画面同t=0s。轻微布料摩擦声——Miguel抬手准备钉照片的动作前兆
Camera: Shot Type: 全景 · Focal: 24mm · DoF: 深景深f/8 · Angle: 眼平
Style: cold-white institutional · neutral-gray palette
  调色板: cold-white-5000K · neutral-gray · pure-white-whiteboard · blood-red-accent · dark-navy-jacket
Constraints: 白板文字=后期叠加·画面中仅呈现照片色块和红线网络

### 【音轨】
底噪: 低音量空调运行声·办公室底噪·远处打印机微弱运转声
  t=0-3s: 持续底噪
  t=4s: 轻微布料摩擦声——Miguel抬手准备钉照片·0.5秒

### 【段末转场设计】
本镜→镜#A2: 硬切
转场时长: 0秒
视觉衔接: 全景建立→ECU红图钉·景别跳变4级(全景→大特写)·视觉冲击·红图钉成为跨镜色彩锚点(延续红线/红圈注的血红色调)

### 【禁止】
1. Miguel面部不可见(背身)·不描述面部表情
2. 白板文字仅呈现色块和线条·不可要求渲染具体文字


━━━ 镜#A2: 大特写 · 5秒 ━━━

### 【镜头参数卡】
- 景别: 大特写(ECU)
- 焦距: 100mm
- 机位: 白板前·距白板~0.3m·区域① · 锚定于参考图中排
- 运镜: 极慢前推0.05x·匀速·沿光轴·行程约20cm·4秒(S1)
- 角度: 眼平·高度1.5m
- 时长: 5秒 (场景内t=5~9)
- KB: D-TRI-05 M-MOT-01 M-MOT-04

### 【传入参考图】
@图片2: [[案情室_中排]] — 用途: 白板线索墙·红图钉+红线+照片细节锚定
@图片3: [[案情室_下排]] — 用途: 图钉微距特写·旧钉眼凹陷·钉帽质感

### 【生成指令】
Subject: Miguel右手 · 拇指+食指·精准按压红图钉
Action:
  t=5s: ECU·Miguel右手拇指按压红图钉·食指稳定照片·图钉尖端刺入白板表面·照片边框压住下层面孔·红线从图钉帽下绷直延伸至白板'201'红圈(红圈为色块·文字后期叠加)。极浅景深·背景完全虚化为白色模糊·红图钉+红线为画面唯一焦点。5000K冷白光下图钉金属帽微反光·白板表面微纹理。Miguel拇指指纹和指甲细节清晰
  t=6s: 极慢前推0.05x继续·图钉占据画面更大比例·钉帽金属质感增强·红线张力视觉化
  t=7s: 前推继续·旧钉眼凹陷(旁边两个)进入画面边缘·白板使用痕迹可见
  t=8s: 前推继续·图钉帽几乎占满画面·金属表面微细划痕可见·红线如血管从钉帽下延伸
  t=9s: 前推落定·图钉完全刺入·照片固定完成·红线绷直至'201'红圈·前推结束
Camera: Shot Type: 大特写 · Focal: 100mm · DoF: 浅景深f/2.8 · Angle: 眼平
Style: cold-white institutional · blood-red accent dominant
  调色板: blood-red-accent · cold-white-5000K · pure-white-whiteboard
Constraints: 红图钉+红线为画面唯一焦点·文字为后期叠加·手指不遮挡红线延伸方向

### 【音轨】
底噪: 持续底噪
  t=5s: 图钉刺入白板·轻微噗声·0.3秒
  t=5-9s: 持续底噪

### 【段末转场设计】
本镜→镜#A3: 硬切
转场时长: 0秒
视觉衔接: ECU红图钉→中景Miguel后退·空间骤然扩展·红图钉成为跨镜记忆锚点·观众从微观回到空间


━━━ 镜#A3: 中景 · 5秒 ━━━

### 【镜头参数卡】
- 景别: 中景(MS)
- 焦距: 35mm
- 机位: 白板前·距白板~2m·区域③ · 锚定于参考图上排
- 运镜: 固定(S0)
- 角度: 眼平·高度1.6m
- 时长: 5秒 (场景内t=10~14)
- KB: D-TRI-03 C-KTZ-01

### 【传入参考图】
@图片1: [[案情室_上排]] — 用途: 白板+办公桌空间关系锚定
@图片2: [[案情室_中排]] — 用途: 白板红线网络全貌

### 【生成指令】
Subject: Miguel · 白板前站立·后退一步后审视姿态
Action:
  t=10s: Miguel后退一步完成·身体重心后移·双臂微垂·距白板约1.5m。夹克仍在椅背上(画面中可见)。白板红线网络全貌——从ECU中的单个图钉扩展到完整的红线血管状网络·多条红线汇聚至'201'红圈。Miguel中景全身·5000K冷白均匀照明·肤色偏灰偏蜡(制度光下棕褐的冷调)
  t=11s: Miguel静止审视·眉心微皱·深棕色眼睛扫视红线连接逻辑·从一张照片到另一张照片
  t=12s: Miguel视线停留在'201'红圈(建筑平面图中心)·审视姿态稳定
  t=13s: 画面同t=12s。Miguel审视中·身体微前倾·目光从红圈移向上方弹道报告色块区域
  t=14s: 画面同t=13s。西墙门外传来轻微脚步声(画外音·音轨标注)·Miguel未察觉
Camera: Shot Type: 中景 · Focal: 35mm · DoF: 中等景深f/5.6 · Angle: 眼平
Style: cold-white institutional · neutral-gray dominant
  调色板: cold-white-5000K · neutral-gray · blood-red-accent
Constraints: Miguel肤色冷白下偏灰偏蜡·不擅自回暖

### 【音轨】
底噪: 持续底噪
  t=10-11s: 后退一步·鞋底与地面轻微摩擦声
  t=14s: 门外走廊传来轻微脚步声(画外音·Vincent接近中)
  t=10-14s: 持续底噪

### 【段末转场设计】
本镜→镜#A4: 硬切
转场时长: 0秒
视觉衔接: Miguel中景→门口Vincent中近景·视线方向从白板转向门·新角色引入·空间轴线从北(白板)转向西(门)


━━━ 镜#A4: 中近景 · 4秒 ━━━

### 【镜头参数卡】
- 景别: 中近景(MCU)
- 焦距: 50mm
- 机位: 门口·面向西墙门·距门~2m · 锚定于空间地图西墙
- 运镜: 固定(S0)
- 角度: 眼平·高度1.6m
- 时长: 4秒 (场景内t=15~18)
- KB: D-TRI-05 C-FI-14

### 【传入参考图】
@图片1: [[案情室_上排]] — 用途: 西墙门框位置锚定

### 【生成指令】
Subject: Vincent · 门口探头·一半脸在门框后
Action:
  t=15s: 门框构图。西墙灰色金属门(宽~1m·高~2.1m·不锈钢把手)半开。Vincent从走廊探头·身体在走廊·头微倾探入案情室·一半脸在门框后。黑框眼镜(黑色板材·矩形框)在3500K暖黄走廊光下镜片反射减少·眼睛可见。门框为自然画框——门内5000K冷白 vs 门外3500K暖黄·冷暖交界线沿门框切割·矩形光柱投射在地面。Vincent冷白肤色与Miguel形成冷暖对照
  t=16s: Vincent开口说话·嘴唇微动·黑框眼镜稳定·镜片在暖黄光下半透明
  t=17s: 画面同t=16s。Vincent说完第一句·等待Miguel反应
  t=18s: 画面同t=17s。Vincent微微点头确认信息传达·准备退出门框
Camera: Shot Type: 中近景 · Focal: 50mm · DoF: 浅景深f/2.8 · Angle: 眼平
Style: frame-within-frame composition · warm-cool contrast
  调色板: warm-yellow-3500K-corridor · cold-white-5000K · neutral-gray
Constraints: Vincent面部不越出门框·保持一半在画框外的构图

### 【音轨】
底噪: 走廊轻微回声·门框声学变化
  t=15s: 门把手转动声
  t=15.5s: Vincent(CV): "Miguel. A Clara pediu para avisar——"
  t=17s: Vincent继续: "——que o relatório preliminar já está pronto."
  t=18s: Vincent轻微气息声·准备退后

### 【段末转场设计】
本镜→镜#A5: 硬切
转场时长: 0秒
视觉衔接: Vincent门口→Miguel面部近景·反应镜头·对话的视觉回答·冷暖光对比(镜#A4暖黄门口→镜#A5冷白面部)


━━━ 镜#A5: 近景 · 4秒 ━━━

### 【镜头参数卡】
- 景别: 近景(CU)
- 焦距: 50mm
- 机位: 白板前·距Miguel~1.5m·区域③ · 锚定于参考图上排
- 运镜: 固定(S0)
- 角度: 眼平·高度1.6m
- 时长: 4秒 (场景内t=19~22)
- KB: D-TRI-05

### 【传入参考图】
@图片1: [[案情室_上排]] — 用途: Miguel面部+白板背景空间锚定

### 【生成指令】
Subject: Miguel · 近景面部·对Vincent话语的微反应
Action:
  t=19s: Miguel近景·面部占据画面。5000K冷白制度光下肤色偏灰偏蜡。眉心间竖纹深刻·深棕色眼睛呈现刑警的审视感。听到Vincent说"Clara"——Miguel眼睑微动·瞳孔微缩。浅景深·背景白板红线网络虚化为色块
  t=20s: Miguel眉心微皱加深·唇线微收。听到"relatório preliminar já está pronto"(初步报告已准备好)——Miguel的表情从纯粹审视过渡到决断的前兆。金色警徽在胸前冷白光下制度光泽
  t=21s: Miguel微微点头·确认信息·眼睑半垂·内心计算下一步行动
  t=22s: Miguel抬起头·目光从虚空中收回·转向门方向·表情已从分析者切换为行动者。面部冷白光下偏灰偏蜡·即将转向暖黄
Camera: Shot Type: 近景 · Focal: 50mm · DoF: 浅景深f/2.8 · Angle: 眼平
Style: cold-white institutional · intimate
  调色板: cold-white-5000K · neutral-gray · gold-badge-gleam
Constraints: Miguel肤色5000K冷白下偏灰偏蜡·不可回暖·面部比例与镜#A1-3一致

### 【音轨】
底噪: 持续底噪
  t=19-22s: 持续底噪

### 【段末转场设计】
本镜→镜#A6: 硬切
转场时长: 0秒
视觉衔接: Miguel面部近景→Miguel中景拿夹克·动作转折·从"审视"到"行动"


━━━ 镜#A6: 中景 · 6秒 ━━━

### 【镜头参数卡】
- 景别: 中景(MS)
- 焦距: 35mm
- 机位: 桌前·距Miguel~2m·区域③ · 锚定于参考图上排
- 运镜: 固定(S0)
- 角度: 眼平·高度1.6m
- 时长: 6秒 (场景内t=23~28)
- KB: D-TRI-03 M-MOT-01

### 【传入参考图】
@图片1: [[案情室_上排]] — 用途: 办公桌+椅背+夹克空间位置锚定
@图片3: [[案情室_下排]] — 用途: 桌面细节·车钥匙位置·笔记本电脑

### 【生成指令】
Subject: Miguel · 桌前·拿起夹克和车钥匙·动作转折
Action:
  t=23s: Miguel转身走向办公桌·果断拿起搭在椅背的深藏青警探夹克。哑光面料在5000K冷白光下呈现制度质感·面料微反光。金色警徽(盾形·浮雕鹰+星环)在左胸前随动作微晃动·金属反光。Miguel手臂穿过袖管·夹克上身
  t=24s: Miguel拉上夹克拉链·立领包裹颈部。右手伸向桌面·拿起车钥匙。车钥匙金属环碰撞·银色光泽
  t=25s: Miguel穿上夹克后身材轮廓变化——宽阔肩膀被夹克强化·深藏青色与浅灰衬衫形成层次。右手握车钥匙·钥匙齿可见。身体语言从"分析者"(微前倾·手臂微垂)切换为"行动者"(直立·肩膀展开·握钥匙手微抬)
  t=26s: Miguel面向门方向·准备出发。夹克哑光面料在制度光下纹理清晰·金色警徽为胸前唯一高光点
  t=27s: Miguel迈出第一步·身体开始移向门口
  t=28s: Miguel走向门口·即将进入镜#A7的门框构图
Camera: Shot Type: 中景 · Focal: 35mm · DoF: 中等景深f/5.6 · Angle: 眼平
Style: cold-white institutional · action-transition moment
  调色板: dark-navy-jacket · gold-badge-gleam · cold-white-5000K · neutral-gray
Constraints: 夹克哑光面料质感准确·警徽金属反光与格栅灯光源方向一致

### 【音轨】
底噪: 持续底噪
  t=23s: 夹克从椅背拿起·面料摩擦声
  t=24s: 拉链声·车钥匙金属碰撞声
  t=27s: Miguel脚步声开始
  t=23-28s: 持续底噪

### 【段末转场设计】
本镜→镜#A7: 硬切
转场时长: 0秒
视觉衔接: Miguel走向门→门框中全景·镜#A4门框构图的回响·冷暖交界再现·Miguel从冷白进入暖黄


━━━ 镜#A7: 中全景 · 3秒 ━━━

### 【镜头参数卡】
- 景别: 中全景(MFS)
- 焦距: 24mm
- 机位: 房间中央·面向西墙门·区域⑤ · 锚定于参考图上排
- 运镜: 固定(S0)
- 角度: 眼平·高度1.6m
- 时长: 3秒 (场景内t=29~31)
- KB: D-TRI-03

### 【传入参考图】
@图片1: [[案情室_上排]] — 用途: 门框+室内空间关系锚定

### 【生成指令】
Subject: Miguel · 门框中·一半室内冷白一半走廊暖黄
Action:
  t=29s: Miguel身体框在门框中·一半面光(室内5000K冷白)·一半阴影(走廊3500K暖黄)。门框为自然画框——与镜#A4对称·但此时框中人是主角而非访客。Miguel面部呈现冷暖过渡:冷白侧肤色偏灰偏蜡(制度·分析)·暖黄侧肤色回暖(行动·出发)。走廊暖黄光从门外漫射·经门框切割为矩形光柱投射在室内地面
  t=30s: Miguel跨出门框·身体从制度空间(冷白)完全进入走廊(暖黄)·面部肤色从偏灰过渡到皮下散射深橙金。门框构图完整·镜#A4的视觉回响
  t=31s: Miguel背影在走廊暖黄光中模糊·门开始关闭·冷白矩形光柱缩小·制度空间回到宁静
Camera: Shot Type: 中全景 · Focal: 24mm · DoF: 深景深f/8 · Angle: 眼平
Style: frame-within-frame · warm-cool transition · closure
  调色板: warm-yellow-3500K-corridor · cold-white-5000K · dark-navy-jacket · gold-badge-gleam
Constraints: 冷暖过渡自然·门框构图与镜#A4对称·肤色从冷白→暖黄过渡准确

### 【音轨】
底噪: 走廊回声·门框声学过渡
  t=29s: 脚步声从室内地板过渡到走廊
  t=31s: 门开始关闭·铰链声

### 【段末转场设计】
本镜→场景结束: 门关闭·黑屏
转场时长: 1秒(门关闭)
视觉衔接: 场景结束·冷暖过渡完成·制度空间恢复宁静·为场景B(贫民窟巷道·暖色调)做视觉铺垫

### 【禁止】
1. 门框构图必须与镜#A4对称(门内→门外·主角vs访客)
2. Miguel面部冷暖过渡必须自然·从冷白到暖黄的色温变化与肤色描述一致


━━━ 全场景收尾 ━━━
色彩弧线: 冷白制度(镜#A1-A5)→冷暖过渡(镜#A6-A7)→暖黄行动(镜#A7结尾·为场景B铺垫)
运镜统计: 6/7镜固定(86%) · 仅镜#A2极慢前推0.05x(S1)
硬切统计: 7镜·6次硬切
宪法合规: 画布七条铁律全部✅ · P-FAL-08规避(白板文字后期叠加) · 静态快速通道激活
场景末状态快照: Miguel离开案情室·夹克已穿·车钥匙在手·门关闭中
