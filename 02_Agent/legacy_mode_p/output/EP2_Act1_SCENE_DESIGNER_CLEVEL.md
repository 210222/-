# EP2_Act1_SCENE_DESIGNER — Rico工作室 · C-Level合并设计+台本

> **Prompter:** Scene Designer v1.0 (C-Level·三域合并含动作运镜)
> **场景:** 枪王 EP2第一幕 · Rico工作室门口楼道+室内 · 4镜·20秒
> **复杂度:** 🔴 C-Level · F1=2·F2=1·F3=0·F4≈50%·F5=true·F6=true(悬疑)
> **渲染目标:** Seko画布 · 悬疑/动作镜头→海螺02优先 · 静态→即梦4.0
> **核心:** 9个叙事节拍压缩为4镜 · 单人悬疑探索 · 冷暖双色温(楼道4000K↔室内2800K)

---

## §3 Step 0: 空间坐标系（三域共享·只写一次）

```
📐 场景类型: 悬疑·单人探索
   角色数: 1(伊莎贝拉·女性·单人主角) · complexity: C · KB: §2.3悬疑+§5运镜+§4构图+§6光影

═══════════ 空间A: 楼道(苏式居民楼走廊) ═══════════
尺寸: 纵深~15m × 宽~1.8m × 高~2.8m
特征: 素灰墙面·水磨石地面·圆形吸顶荧光灯(4000K冷白·声控·微老旧闪烁)
  走廊尽头: 楼梯口·半透明窗·外部凌晨微光(~6500K·极弱)
  门: 深色木质门(宽~0.9m·高~2.1m)·黄铜锁孔·不锈钢门把·门框密封条老化

人物可放置区域:
  ① 门外·锁孔前(站姿·1人·距门0.3-0.5m)
  ② 走廊中段(站姿·1人·从楼梯口走向门)
  ③ 走廊尽头·楼梯口(站姿·1人)

光源物理锚点(楼道):
  L1-吸顶荧光灯: 4000K冷白·圆形·声控·老旧微闪烁·锚定格2格6(顶灯特写)

═══════════ 空间B: Rico工作室室内 ═══════════
尺寸: ~5m×4m·工业风·高天花板(~3.5m)
特征: 工作台居中·枪械零件散布·工业吊灯(2800K暖黄·光锥锐利·chiaroscuro)
  墙上工具架·金属柜·洗手池(角落)·深色混凝土地面
  光锥外区域全暗(室内仅一盏吊灯·无环境补光)

人物可放置区域:
  ④ 门口内(站姿·1人·门框中线)
  ⑤ 工作台前(站姿·1人·距工作台~0.5m)

光源物理锚点(室内):
  L2-工业吊灯: 2800K暖黄·硬光·光锥锐利(chiaoscuro)·锚定格1格1-6(全景室)
  L3-门缝暖光: L2从门缝漏出·2800K·门框缝隙·走廊可见

180度线: 关系线=伊莎贝拉↔门(走廊↔室内的分界线)
  轴线方向: 垂直于门平面·走廊纵深方向
  轴线侧: A侧(门轴对侧·锁孔侧)
```

---

## §7.1 机位域YAML

```yaml
scene:
  id: "EP2_Act1"
  name: "Rico工作室·门口+室内"
  type: "悬疑·单人探索·双空间"
  total_duration_sec: 20
  complexity_level: "C"

segments_camera:
  - segment_id: "①"
    time_range: [0, 3]
    shot_type: "ECU→MCU"
    focal_length: "85mm→35mm"
    dof: "浅f/2.8→中f/5.6"
    angle: "锁孔同高1.2m·正面微俯5°"
    kb_rule_ids: ["A-SUS-01", "C-FI-17", "A-SUS-02"]

  - segment_id: "②"
    time_range: [3, 8]
    shot_type: "全景→MS→CU(POV)"
    focal_length: "35mm→50mm→85mm"
    dof: "中f/5.6→浅f/2.8"
    angle: "眼平1.55m(伊莎贝拉眼高·POV)→微俯(毛巾)"
    kb_rule_ids: ["C-FI-17", "C-FI-06", "A-SUS-02", "C-KTZ-02"]

  - segment_id: "③"
    time_range: [8, 12]
    shot_type: "ECU→甩镜→CU"
    focal_length: "135mm→模糊→85mm"
    dof: "极浅f/2.0→中f/5.6"
    angle: "门把高1.1m→甩镜28°/s→面部眼平"
    kb_rule_ids: ["A-SUS-09", "A-SUS-01", "C-FI-06"]

  - segment_id: "④"
    time_range: [12, 20]
    shot_type: "全景→中景→ECU"
    focal_length: "24mm→35mm→135mm"
    dof: "深f/8→中f/5.6→极浅f/2.0"
    angle: "门口分界线→dolly back至1.2m→门把高1.1m"
    kb_rule_ids: ["A-SUS-08", "C-FI-06", "C-DEP-01", "C-KTZ-02"]
```

---

## §7.2 运镜域YAML

```yaml
segments_movement:
  - segment_id: "①"
    movement: "固定(S0)·门开=被动景别变化(ECU→MCU非变焦·门物理运动)"
    movement_speed_tier: "S0"
    kb_rule_ids: ["M-MOT-01", "M-MOT-03"]

  - segment_id: "②"
    movement: "间歇摇摄POV(揭示式)·极慢摇摄约1.5-2.0°/s·有停顿(0.5s枪械零件)"
    movement_speed_tier: "S1"
    kb_rule_ids: ["M-MOT-02", "M-MOV-05", "M-PAN-01"]

  - segment_id: "③"
    movement: "固定(2s·ECU手)→甩镜(0.5s·极慢摇摄约28°/s·惊吓反应)→固定(1.5s·CU面部)"
    movement_speed_tier: "S0→S8→S0"
    kb_rule_ids: ["M-MOT-01", "A-SUS-10", "M-MOT-02"]

  - segment_id: "④"
    movement: "固定(POV空镜2s)→dolly back(3s·v_dolly=-0.3m/s·沿走廊纵深后退)→固定(ECU手抖3s)"
    movement_speed_tier: "S0→S3→S0"
    kb_rule_ids: ["M-MOV-04", "M-MOT-02", "M-MOT-03"]

segments_transitions:
  - {transition_id: "①→②", from_segment: "①", to_segment: "②", transition_type: "硬切", time_range: [3, 3], visual_change: "门开·暖光涌出→硬切至POV室内·门外→门内·冷→暖"}
  - {transition_id: "②→③", from_segment: "②", to_segment: "③", transition_type: "硬切", time_range: [8, 8], visual_change: "染血毛巾特写→硬切至ECU手部紧握门把·探索→反应"}
  - {transition_id: "③→④", from_segment: "③", to_segment: "④", transition_type: "甩镜过渡", time_range: [12, 12], visual_change: "伊莎贝拉面部→转头140°→甩镜过渡→走廊空镜·室内→楼道"}
```

---

## §7.3 构图光影域YAML

```yaml
global_anchors:
  character:
    伊莎贝拉: "Female, late 20s-early 30s, lean build, dark casual clothing (深色便装·夹克或长外套), dark hair pulled back or shoulder-length, pale skin tone sensitive to color temperature shifts. Core props: 黄铜钥匙(红色标签·老旧·铜绿斑). Core visual signatures: (I1) hand holding brass key with red tag at lock level — precise insertion; (I2) hand gripping door handle with whitened knuckles — tension; (I3) hand trembling after pulling key from lock — fear tremor; (I4) face half-lit by warm 2800K from door crack + cold 4000K corridor — standing on the boundary between two worlds"

  environment:
    description: "Soviet-style residential building corridor, 4:30am. Corridor: ~15m deep × ~1.8m wide × ~2.8m high, plain gray walls, terrazzo floor, circular ceiling fluorescent light (4000K cold white, voice-activated, slight old flicker), corridor end with stairwell and semi-transparent window (weak 6500K pre-dawn light). Wooden door (~0.9m×2.1m) with brass lock and stainless steel handle, aged doorframe seal. Studio interior (~5m×4m): industrial high ceiling (~3.5m), central workbench with disassembled gun parts, industrial hanging lamp (2800K warm yellow, hard light, sharp cone, chiaroscuro), tool shelves on walls, metal cabinets, corner washbasin, dark concrete floor. Light cone periphery completely dark — single hanging lamp, no ambient fill."

  style_spine:
    description: "shot on Arri Alexa 35, cold fluorescent 4000K corridor vs warm industrial 2800K studio, chiaroscuro single-source interior, blue-orange complementary color contrast, suspense single-character POV language, 1.85:1 aspect ratio"
    palette_anchors: ["cold-fluorescent-4000K", "warm-industrial-2800K", "dark-void-chiaroscuro", "brass-key-gold", "blood-stain-dark-red", "pre-dawn-blue-6500K"]

  lighting:
    description: "Dual color temperature system with 1000K difference. CORRIDOR: L1-ceiling fluorescent 4000K cold white, circular, voice-activated, slight flicker, soft diffused. STUDIO: L2-industrial hanging lamp 2800K warm yellow, hard light, sharp cone ~45°, chiaroscuro — light cone = illuminated, outside cone = pitch black. DOOR CRACK: L3-warm 2800K seeping through door crack as thin vertical line before door opens, then flooding corridor as widening warm rectangle. COLOR ARC: cold(4000K·corridor·closed)→cold+warm sliver(door crack)→warm flood(door opens·2800K dominates)→warm(CU interior·pure 2800K)→mix(CU face·half 2800K warm edge + half 4000K cold front)→transition(dolly back·warm rectangle shrinks)→cold(ECU·4000K only·door closed)"
    anchor_in_reference: "Corridor: Grid2-Grid6(ceiling light closeup). Studio: Grid1-Grid1-6(panoramic room with hanging lamp + light cone). Door: Grid2-Grid4(front door) + Grid2-Grid7(lock hole) + Grid2-Grid5(half-open door)"

  constraints:
    - "1000K色温差贯穿全场景——2800K室内暖黄 vs 4000K楼道冷白·冷暖交界线=两个世界的分界"
    - "伊莎贝拉肤色作为色温计——冷白下偏冷偏白·暖黄下回暖·冷暖交界时面部呈现双色温"
    - "染血毛巾的暗红色是画面中唯一非工业色——2800K暖黄下血迹偏深红·视觉冲击"
    - "黄铜钥匙红色标签——唯一高饱和色点·跨镜视觉锚点"
    - "面部比例全程一致·五官不漂移"
    - "无画面文字(P-FAL-08)"
    - "光源必须有物理锚点·无凭空编造"
```

---

## ═══════════ C-Level 导演台本 ═══════════

> **Prompter:** Scene Designer v1.0 (C-Level·三域合并)
> **场景:** EP2第一幕 · Rico工作室门口+室内 · 4镜·20秒
> **角色:** 伊莎贝拉(单人悬疑主角)
> **叙事:** 9拍→4镜: 钥匙入锁→转动→门开→扫视室内→发现染血毛巾→松手→脚步声→转头→退出锁门+手抖
> **色温弧线:** 冷(4000K)→冷暖交界→暖涌入→暖主导(2800K)→冷暖混合→暖收缩→冷闭合(4000K)

---

## 【场景级共享锚点】

### @参考图声明
@图1格1-6: [[Rico工作室_全景]] — 用途: 室内全景·工作台·工业吊灯光锥·枪械零件·洗手池
@图2格1-3: [[楼道_走廊+楼梯口]] — 用途: 走廊纵深·楼梯口半透明窗·凌晨微光
@图2格4: [[楼道_正门]] — 用途: 深色木质门全貌·门框·黄铜锁孔位置
@图2格5: [[楼道_半开门]] — 用途: 门半开状态·暖光涌出·门缝光柱
@图2格6: [[楼道_顶灯]] — 用途: 圆形吸顶荧光灯·4000K冷白·声控
@图2格7: [[楼道_锁孔]] — 用途: 黄铜锁孔特写·钥匙插入·门把
@图8: [[钥匙_手部]] — 用途: 黄铜钥匙红色标签·手持钥匙·手部微动作
@图-R4: [[染血毛巾]] — 用途: 工作台上染血毛巾·暗红血迹·织物纹理

### C1 Character Anchor（逐字锁定）
伊莎贝拉: "Female, late 20s-early 30s, lean build, dark casual clothing (深色便装·夹克或长外套), dark hair pulled back or shoulder-length, pale skin tone sensitive to color temperature shifts. Core props: 黄铜钥匙(红色标签·老旧·铜绿斑·~5cm). Core visual signatures: (I1) hand holding brass key at lock level — precise insertion; (I2) hand gripping door handle with whitened knuckles — tension; (I3) hand trembling after pulling key from lock — fear tremor; (I4) face half-lit by warm 2800K edge + cold 4000K front — standing on the boundary between two worlds"

### C2 Environment Anchor（逐字锁定·五要素）
凌晨4:30 · 苏式居民楼走廊+Rico工作室室内 · 无窗楼道·水磨石地面·吸顶荧光灯 · 走廊冷白4000K·室内暖黄2800K·1000K色温差 · 深色木质门·黄铜锁孔·工业吊灯光锥·工作台枪械零件散落·染血毛巾

### C3 Lighting Anchor（逐字锁定·锚点可追溯）
L1-楼道荧光灯: 圆形吸顶·4000K冷白·声控·微老旧闪烁·柔光漫射·锚定格2格6
L2-工业吊灯: 室内单光源·2800K暖黄·硬光·光锥锐利~45°·光锥外全暗·锚定格1格1-6
L3-门缝暖光: L2从门缝漏出·2800K·门框缝隙·开启后涌出为矩形光柱·锚定格2格5
L4-凌晨微光: 走廊尽头楼梯口·半透明窗·6500K极弱·仅提供楼梯口轮廓光·锚定格2格1-3

### C4 Style Spine & Palette
风格: "shot on Arri Alexa 35, cold fluorescent 4000K corridor vs warm industrial 2800K studio, chiaroscuro single-source interior, blue-orange complementary color contrast, suspense single-character POV language, 1.85:1"
调色板: cold-fluorescent-4000K · warm-industrial-2800K · dark-void-chiaroscuro · brass-key-gold · blood-stain-dark-red · pre-dawn-blue-6500K

### 场景级禁止
1. 1000K色温差跨镜一致: 2800K室内/4000K楼道全幕保持·色温不无故漂移
2. 光源必须有物理锚点(吸顶灯/吊灯/门缝漏光/凌晨窗光)·无凭空编造
3. 面部比例全程一致·五官不漂移
4. 黄铜钥匙红色标签在镜#A1/#A3/#A4中保持一致外观
5. 染血毛巾仅在镜#A2中出现·镜#A3后已松手(不再握毛巾)
6. 无画面文字(P-FAL-08)


━━━ 镜#A1: ECU→MCU · 3秒 ━━━

### 【镜头参数卡】
- 景别: ECU(锁孔)→MCU(门框半开)
- 焦距: 85mm→35mm
- 机位: 楼道侧·门外0.5m·锁孔同高1.2m·门轴对侧 · 锚定格2格7+格4+格5
- 运镜: 固定(S0)·门开=被动景别变化(非变焦·门物理运动展开空间)
- 角度: 正面微俯5°
- 时长: 3秒 (场景内t=0~3)
- KB: A-SUS-01 C-FI-17 A-SUS-02 M-MOT-01 M-MOT-03

### 【传入参考图】
@图2格7: [[楼道_锁孔]] — 用途: 黄铜锁孔·钥匙插入位置·门表面木纹
@图8: [[钥匙_手部]] — 用途: 伊莎贝拉手持黄铜钥匙·红色标签·手部微动作
@图2格4: [[楼道_正门]] — 用途: 深色木质门全貌·门框密封条·不锈钢门把
@图2格5: [[楼道_半开门]] — 用途: 门半开·暖光涌出·光柱形态

### 【生成指令】
Subject: 伊莎贝拉右手+黄铜钥匙 · 锁孔 · ECU→MCU
Action:
  t=0s: ECU·黄铜锁孔居中·深色木门表面·木纹微细纹理。伊莎贝拉右手持黄铜钥匙入画——钥匙尖端对准锁孔·红色标签(~5cm·老旧纸质·褪色·"RICO"手写字迹半褪)从钥匙环垂下。手指稳定·指甲整洁·无名指无戒指。锁孔周围黄铜微磨损——多次开锁痕迹。楼道吸顶荧光灯4000K冷白·锁孔区域均匀照明·木门表面冷色调
  t=1s: 钥匙插入锁孔——黄铜与黄铜的接触·钥匙齿与锁芯销钉的机械配合。伊莎贝拉手腕旋转——钥匙顺时针转动约70°·红色标签随之微晃。锁芯内部机械声(音轨)。手指稳定·无颤抖·动作熟练——她来过这里
  t=2s: 锁芯弹开——咔嗒声。伊莎贝拉左手出现在画面·握住不锈钢门把·向下按压·门把转动。右手从锁孔拔出钥匙·钥匙+红色标签回至身侧
  t=3s: 门被推开——门框密封条分离·门缝从0变为~2cm→5cm→15cm。2800K暖黄光从门缝涌出——先是极细的垂直线·然后扩展为楔形光柱·投射在走廊水磨石地面上。门框边缘形成1000K色温差冷暖交界线——暖黄光在走廊冷白中如火焰。ECU自然过渡为MCU——门半开·伊莎贝拉深色背影在门前·暖黄光勾勒身体轮廓
Camera: Shot Type: ECU→MCU · Focal: 85mm→35mm · DoF: 浅f/2.8→中f/5.6 · Angle: 正面微俯5°
Style: cold fluorescent corridor · warm light invasion begins
  调色板: cold-fluorescent-4000K · warm-industrial-2800K · brass-key-gold
Constraints: 钥匙红色标签颜色饱和·锁孔周围黄铜磨损可见·门开时暖光涌出的光柱形态与格5参考图一致

### 【音轨】
底噪: 凌晨居民楼·极度安静·远处冰箱压缩机低鸣
  t=0-1s: 钥匙插入锁孔·金属微声
  t=2s: 锁芯弹开·咔嗒·清脆金属声。门把转动·机械微声
  t=3s: 门框密封条分离·轻微橡胶撕裂声。门轴铰链微声

### 【段末转场设计】
本镜→镜#A2: 硬切
转场时长: 0秒
视觉衔接: 伊莎贝拉门前背影·暖光涌出→硬切至POV室内·从第三人称切到第一人称·门外→门内·冷→暖


━━━ 镜#A2: 全景→MS→CU(POV) · 5秒 ━━━

### 【镜头参数卡】
- 景别: 全景→中景→近景(POV主观)
- 焦距: 35mm→50mm→85mm
- 机位: 门口内·距门0.3m·伊莎贝拉眼高1.55m·门框中线 · 锚定格1格1-6
- 运镜: 间歇摇摄POV(揭示式)·极慢摇摄约1.5-2.0°/s·停顿0.5s·5s
- 角度: 眼平1.55m(伊莎贝拉眼高·第一人称POV)
- 时长: 5秒 (场景内t=3~8)
- KB: C-FI-17 C-FI-06 A-SUS-02 C-KTZ-02 M-MOT-02 M-MOV-05

### 【传入参考图】
@图1格1-6: [[Rico工作室_全景]] — 用途: 室内全景·工作台·工业吊灯光锥·枪械零件·工具架
@图-R4: [[染血毛巾]] — 用途: 工作台上染血毛巾·暗红血迹·织物纹理

### 【生成指令】
Subject: 伊莎贝拉POV · 室内探索 · 间歇摇摄
Action:
  t=3s: 全景·POV从门口看向室内。工业吊灯(2800K暖黄·硬光·光锥锐利~45°)从天花板垂下·光锥内:工作台居中·散落拆卸中的枪械零件(金属反光·机油微光)·工具架墙上·金属柜·角落洗手池。光锥外:完全黑暗——室内只有这一盏灯。强烈的chiaroscuro——亮部极亮·暗部极暗·无中间调。光锥边缘锐利如刀割。暖黄2800K充满画面——与镜#A1的冷白4000K形成彻底的色温断裂。起幅静态1s——让观众吸收室内信息
  t=4s: 第一段摇摄开始·摄影机以极慢速度向右摇摄·每秒约1.5度。POV从工作台全貌向右缓慢平移——视线扫过枪械零件(枪管·弹簧·扳机组件散落)·金属表面在2800K下呈现暖金反光。工具架——扳手·螺丝刀·油壶。摇摄速度匹配伊莎贝拉的审视节奏——她在评估·在寻找
  t=5s: 摇摄停顿0.5s——视线停在工作台右侧·一把拆卸到一半的手枪·弹匣退出·枪膛打开。枪械零件的机械美感——金属与机油·秩序与暴力
  t=6s: 第二段摇摄开始·摄影机以慢速向右摇摄·每秒约2度·速度微增——伊莎贝拉的呼吸加速。POV从手枪移向工作台左前方。光锥边缘——在半明半暗中·一块白色织物。摇摄落定——POV停在毛巾上。白色毛巾·但上面有暗红色污渍——血迹。血迹已干涸·呈暗红褐色·渗透织物纹理。毛巾边缘微卷·随意丢在工作台上。POV静止——伊莎贝拉盯着毛巾
  t=7s: 镜头从全景推至CU(模拟伊莎贝拉俯身)——毛巾占满画面。暗红血迹细节——边缘不规则·中心深色·边缘扩散。织物白色与血暗红的对比在2800K暖黄下——血迹偏深红·不祥。浅景深·背景完全虚化为暖黄光斑
  t=8s: CU定格在染血毛巾·2秒凝视。伊莎贝拉呼吸声(画外·音轨)——从稳定变为微急促
Camera: Shot Type: 全景→MS→CU(POV) · Focal: 35mm→50mm→85mm · DoF: 中f/5.6→浅f/2.8 · Angle: 眼平1.55m(POV)
Style: warm industrial chiaroscuro · POV exploration · single-source hard light
  调色板: warm-industrial-2800K · dark-void-chiaroscuro · blood-stain-dark-red
Constraints: 光锥外=纯黑·无任何可见物·无环境补光·这是单光源chiaroscuro的核心视觉特征

### 【音轨】
底噪: 室内极度安静·吊灯电流微嗡(2800K工业吊灯·老式变压器)
  t=3-4s: 伊莎贝拉呼吸·稳定·通过鼻腔
  t=5-6s: 摇摄过程·衣物微声(身体微转)
  t=7-8s: 呼吸微加速——从稳定到微急促·发现毛巾的反应。极度安静中呼吸声放大

### 【段末转场设计】
本镜→镜#A3: 硬切
转场时长: 0秒
视觉衔接: 染血毛巾特写→硬切至ECU手部紧握门把·探索→反应·从暖黄室内切到冷白走廊


━━━ 镜#A3: ECU→甩镜→CU · 4秒 ━━━

### 【镜头参数卡】
- 景别: ECU(手·135mm)→甩镜(模糊)→CU(面部·85mm)
- 焦距: 135mm→模糊→85mm
- 机位: 楼道侧·门外0.4m·门把高1.1m→甩镜至面部 · 锚定格2格4/7+格1/2/3
- 运镜: 固定(2s·ECU手)→甩镜(0.5s·极慢摇摄约28°/s·惊吓反应)→固定(1.5s·CU面部)
- 角度: 门把同高1.1m→面部眼平1.55m
- 时长: 4秒 (场景内t=8~12)
- KB: A-SUS-09 A-SUS-01 C-FI-06 M-MOT-01 A-SUS-10 M-MOT-02

### 【传入参考图】
@图2格4: [[楼道_正门]] — 用途: 门把位置·门框·走廊纵深
@图8: [[钥匙_手部]] — 用途: 伊莎贝拉手部微动作·指关节·钥匙
@图2格1-3: [[楼道_走廊+楼梯口]] — 用途: 走廊纵深·楼梯口半透明窗·转头方向

### 【生成指令】
Subject: 伊莎贝拉 · ECU手→甩镜→CU面部
Action:
  ---[子设A: t=8-10s·ECU手部·135mm·极浅f/2.0]---
  t=8s: ECU·伊莎贝拉右手紧握门把——不锈钢门把·手掌包握·指关节因用力发白(I2视觉签名)。门把表面微细划痕·手指皮肤纹理·无名指无戒指。楼道吸顶荧光灯4000K冷白·手部均匀照明·冷色调。手在微微颤抖——不是寒冷·是恐惧的生理反应
  t=9s: 手从紧握到松开——指关节血色恢复·手掌从门把上脱离·手指仍微屈·在空中悬停。门把上留下微细手汗痕迹。伊莎贝拉VO气息声(音轨):"Rico..."——独白·低语·气息多于声音
  t=10s: 走廊尽头传来脚步声(画外·音轨)——沉重的皮靴声·从楼梯口方向·由远及近·每一步都在水磨石地面上清晰回响。伊莎贝拉手猛地一颤——手指收紧·悬空的手无处可放
  ---[子设B: t=10-10.5s·甩镜·每秒约28度]---
  t=10s: 甩镜——摄影机急速左转·画面模糊·走廊墙面+门+光线拖尾成水平条纹。4000K冷白+门缝2800K暖黄在甩镜中混合为暖冷光带。持续0.5秒——模拟伊莎贝拉听到脚步声后骤然转头·约140至160度的生理反应
  ---[子设C: t=10.5-12s·CU面部·85mm·中f/5.6]---
  t=10.5s: 甩镜落定·CU伊莎贝拉面部。她转头看向走廊尽头(楼梯口方向)·面部处于门框分界线——左半脸(面向室内)被门缝2800K暖黄光勾勒边缘·暖色轮廓光(I4);右半脸(面向楼道)被吸顶灯4000K冷白正面照亮·冷色调。1000K色温差同时出现在一张脸上——她站在两个世界的分界线上。面部三区色彩:冷额头·过渡脸颊·冷下巴。深色眼睛睁大·瞳孔放大·眼白微血管可见。嘴唇微张·呼出白气(凌晨低温·楼道无暖气)
  t=11s: 伊莎贝拉面部僵持——眼睛死盯走廊尽头方向·不眨眼。脚步声继续·越来越近。暖黄边缘光在她左脸轮廓上微动(门缝光因门微动而闪烁)。冷白光在右脸稳定。肤色双色温——左脸偏暖·右脸偏冷·中线沿鼻梁
  t=12s: 伊莎贝拉保持凝视。脚步声突然停止(在走廊中段·距她约5m·不可见)。沉默重压。她的喉结微动——吞咽。即将决定退出
Camera: Shot Type: ECU→甩镜→CU · Focal: 135mm→模糊→85mm · DoF: 极浅f/2.0→中f/5.6 · Angle: 门把高1.1m→面部眼平
Style: cold fluorescent corridor · warm edge light on face · fear physiology
  调色板: cold-fluorescent-4000K · warm-industrial-2800K · brass-key-gold
Constraints: 甩镜速度28°/s对应140-160°转头·面部双色温(I4签名)必须清晰可见·手抖是微细生理反应非夸张表演

### 【音轨】
底噪: 楼道吸顶灯电流微嗡·极度安静
  t=8-9s: 手从门把松开·微声。伊莎贝拉VO(低语·气息声):"Rico..."
  t=10s: 走廊尽头脚步声——沉重皮靴·水磨石地面·由远及近·每一步清晰·间隔约0.8秒
  t=10-10.5s: 甩镜——衣物急速摩擦声(转头)
  t=11-12s: 脚步声持续接近·然后停止(走廊中段)。沉默。伊莎贝拉微促呼吸

### 【段末转场设计】
本镜→镜#A4: 甩镜过渡
转场时长: 0秒(甩镜自然过渡)
视觉衔接: 伊莎贝拉面部CU→甩镜过渡→走廊空镜·从面部表情切到空间·从室内侧切到楼道侧


━━━ 镜#A4: 全景→中景→ECU · 8秒 ━━━

### 【镜头参数卡】
- 景别: 全景→中景→ECU(手+锁孔)
- 焦距: 24mm→35mm→135mm
- 机位: 门口分界线→dolly back至楼道侧1.2m→门把高1.1m · 锚定格2格1/2+格5+格4+格7
- 运镜: 固定(POV空镜2s)→dolly back(3s·v_dolly=-0.3m/s)→固定(ECU手抖3s)
- 角度: 门口→后退至走廊·锁孔同高
- 时长: 8秒 (场景内t=12~20)
- KB: A-SUS-08 C-FI-06 C-DEP-01 C-KTZ-02 M-MOV-04 M-MOT-02 M-MOT-03

### 【传入参考图】
@图2格1-3: [[楼道_走廊+楼梯口]] — 用途: 走廊纵深·空镜·楼梯口半透明窗
@图2格5: [[楼道_半开门]] — 用途: 门半开·暖光矩形·门闭合过程
@图2格4: [[楼道_正门]] — 用途: 门全貌·闭合状态·锁孔位置
@图2格7: [[楼道_锁孔]] — 用途: 锁孔·拔钥匙·手抖
@图8: [[钥匙_手部]] — 用途: 手抖·钥匙红色标签晃动

### 【生成指令】
Subject: 走廊空镜 → 伊莎贝拉退出锁门 → ECU手抖拔钥匙
Action:
  ---[子设A: t=12-14s·全景·24mm·深f/8·POV空镜]---
  t=12s: 走廊空镜——从门口看向走廊尽头(楼梯口方向)。全景·超广24mm·走廊纵深透视——素灰墙面夹道·水磨石地面·圆形吸顶荧光灯4000K冷白·半透明窗凌晨6500K微光在走廊尽头形成极弱蓝灰光斑。无人——脚步声已停·但无人在走廊中。空荡的压迫感。门框在前景(画面底部·占~15%)——半开的门·门缝2800K暖黄光投射在走廊地面上·矩形光柱
  t=13s: 伊莎贝拉从门框中退出——深色背影从暖黄光中退入走廊冷白。她的身体从2800K暖黄过渡到4000K冷白——肤色从暖调回冷。后退一步·两步·离开门框
  ---[子设B: t=14-17s·dolly back·35mm·中f/5.6]---
  t=14s: 摄影机沿走廊中轴线匀速后退·每秒约0.3米。伊莎贝拉右手拉门——深色木质门开始闭合。门缝暖黄光矩形缩小——从30cm宽→20cm→10cm→细线。2800K暖黄光在走廊地面上缩小为一条光带→消失。冷暖交界线收缩。伊莎贝拉左手仍握黄铜钥匙(红色标签)·右手推门闭合
  t=15s: Dolly back继续。门合至5cm缝隙——暖黄光只剩极细的垂直线·如激光。伊莎贝拉面部最后一丝暖色边缘光消失——全脸进入4000K冷白。肤色彻底偏冷。门铰链微声
  t=16s: Dolly back继续。门完全闭合——咔嗒·锁舌入位。暖黄光彻底消失。走廊回到纯粹的4000K冷白——均匀·冷·制度。伊莎贝拉后退·距门约1m·深色背影在走廊中·面向门
  t=17s: Dolly back落定·终点距门1.2m。伊莎贝拉静止1秒·面对关闭的门
  ---[子设C: t=17-20s·ECU·135mm·极浅f/2.0·手+锁孔]---
  t=17s: ECU·伊莎贝拉右手持黄铜钥匙·对准锁孔。手在剧烈颤抖(I3视觉签名)——不是微颤·是可见的抖动·手指难以稳定·钥匙尖端在锁孔周围磕碰·金属微声。红色标签随之晃动——红点在冷白画面中如血滴
  t=18s: 手仍在颤抖——伊莎贝拉用左手握住右手腕·试图稳定·但仍无法控制抖动。钥匙终于插入锁孔——锁芯转动·锁舌弹回。咔嗒声在空荡走廊中回响
  t=19s: 伊莎贝拉拔出钥匙——手指紧握钥匙·红色标签在手心·指关节发白。手从锁孔收回·钥匙+标签悬在身侧·仍在微颤。门已锁闭——深色木门·黄铜锁孔·不锈钢门把·一切如镜#A1的起始状态
  t=20s: ECU定格·锁孔+闭合的门。走廊4000K冷白·均匀·安静。门缝不再漏光。暖色弧线完成闭环——冷→暖涌入→暖主导→冷暖混合→暖收缩→冷闭合。伊莎贝拉呼吸声(画外·音轨)·微促·然后开始平复
Camera: Shot Type: 全景→中景→ECU · Focal: 24mm→35mm→135mm · DoF: 深f/8→中f/5.6→极浅f/2.0 · Angle: 门口→后退·锁孔同高
Style: cold fluorescent corridor · warm light extinction · color arc closure
  调色板: cold-fluorescent-4000K · warm-industrial-2800K(消失中) · brass-key-gold · pre-dawn-blue-6500K
Constraints: 暖光从门缝消失的过程是色温弧线的关键闭合——从矩形→细线→消失·每一个阶段都必须在画面中清晰可见·伊莎贝拉手抖是生理恐惧反应·不是表演夸张

### 【音轨】
底噪: 走廊吸顶灯电流微嗡·凌晨极度安静
  t=12-13s: 伊莎贝拉后退·脚步在走廊水磨石地面上·轻微回声
  t=14-16s: 门闭合·铰链微声。dolly back过程·摄影机后退轮声(可选·后期混音)
  t=16s: 锁舌入位·咔嗒·在走廊中回响
  t=17-18s: 钥匙在锁孔周围磕碰·金属微声·手抖导致的不稳定接触。伊莎贝拉呼吸·微促·恐惧未散
  t=18s: 锁芯转动·锁舌弹回·第二声咔嗒
  t=19-20s: 钥匙拔出·金属微声。伊莎贝拉呼吸从微促开始平复——深呼一口气。安静。走廊空荡

### 【段末转场设计】
本镜→场景结束: 黑屏
转场时长: 2秒(淡出)
视觉衔接: ECU锁孔+闭合的门→淡出黑屏。冷暖弧线完整闭环——从冷(镜#A1起始)到暖到冷(镜#A4结束)。门已锁·钥匙在手·但Rico工作室的秘密(染血毛巾)已被发现


━━━ 全场景收尾 ━━━
色彩弧线: 冷4000K(镜#A1起始)→冷暖交界→暖2800K涌入→暖主导(镜#A2)→冷暖混合(镜#A3面部)→暖收缩→冷闭合4000K(镜#A4结束)
运镜统计: 2/4镜含运镜(镜#A2间歇摇摄POV·镜#A4 dolly back) · 甩镜1次(镜#A3·28°/s)
悬疑节奏: 进入(镜#A1)→探索(镜#A2·POV)→发现+反应(镜#A3·手松+转头)→退出+锁闭(镜#A4)
色温闭合: 1000K色温差贯穿·冷暖弧线完整闭环·门=冷暖世界的物理开关
硬切统计: 3次硬切+1次甩镜过渡+1次淡出
宪法合规: 画布七条铁律全部✅ · P-FAL-06规避·色温锁定·光源锚点全追溯
场景末状态快照: 门已锁·伊莎贝拉在走廊·手握钥匙·呼吸平复·面向闭合的门
