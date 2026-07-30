# EP2 Cafe da Isa -- Director Script (assembler v2.0 draft)

> **Pipeline:** MODE:P | M-Level | deterministic assembly v2.0
> **Scene:** Rico工作室门口+室内 | 20s | 4 shots
> **Axis:** A侧(门轴对侧·锁孔侧)
> **Movement:** 2/4 static (50%)
> **Keyframe data:** YES | Dialogue map: YES
> **WARNING: Deterministic draft -- prose_smoother [Agent] needed for NL smoothing

---
## SA -- Global Anchors (verbatim from PLAN YAML)

### Character Anchors
**伊莎贝拉:**
  - Female, late 20s-early 30s, lean build, dark casual clothing, dark hair pulled back
  - Core props: 黄铜钥匙(红色标签·老旧·铜绿斑·约5cm)
  - Core: (I1) hand holding brass key at lock level—precise insertion
  - (I2) hand gripping door handle with whitened knuckles—tension
  - (I3) hand trembling after pulling key from lock—fear tremor
  - (I4) face half-lit by warm 2800K + cold 4000K—boundary between two worlds

### Environment Anchor
Soviet-style residential corridor, 4:30am. Corridor: ~15m×1.8m×2.8m, plain gray walls, terrazzo floor, circular ceiling fluorescent 4000K. Studio interior: ~5m×4m, industrial hanging lamp 2800K warm yellow, chiaroscuro. Wooden door 0.9m×2.1m with brass lock.
Spatial: Door = boundary between cold corridor(4000K) and warm studio(2800K)

### Lighting System
Dual color temperature system. CORRIDOR: L1-ceiling fluorescent 4000K cold white, soft diffused. STUDIO: L2-industrial hanging lamp 2800K warm yellow, hard light, ~45deg cone, outside cone pitch black. DOOR CRACK: L3-warm 2800K seeping through as thin line→widening rectangle when door opens

| Source | Kelvin | Direction | Reference Grid |
|--------|--------|-----------|----------------|
| L1-吸顶荧光灯 | 4000K | 天花板·垂直向下·圆形·声控 | 图2格6 |
| L2-工业吊灯 | 2800K | 天花板·垂直向下·光锥~45度·硬光 | 图1格1-6 |
| L3-门缝暖光 | 2800K | 门缝·水平漏出→门开时扩展为三角形光柱 | 图2格5 |

### Style Spine and Color Palette
shot on Arri Alexa 35, cold fluorescent 4000K corridor vs warm industrial 2800K studio, chiaroscuro single-source interior, blue-orange complementary color contrast, suspense single-character POV language, 1.85:1
  - cold-fluorescent-4000K
  - warm-industrial-2800K
  - dark-void-chiaroscuro
  - brass-key-gold
  - blood-stain-dark-red

### Global Constraints
  1. 1000K色温差贯穿全场景
  2. 伊莎贝拉肤色作为色温计
  3. 染血毛巾暗红是唯一非工业色
  4. 黄铜钥匙红色标签——唯一高饱和色点
  5. 面部比例全程一致
  6. 无画面文字(P-FAL-08)

---
## Shot #A1: ECU→MCU | 3s

### Camera Parameter Card
- Shot type: ECU→MCU
- Focal length: 85mm→35mm
- Aperture: 浅景深→中景深
- Angle: 正面微俯5度
- Camera type: ECU锁孔·门轴对侧
- Camera position: 楼道侧·门外0.5m·锁孔同高1.2m·门轴对侧·A侧
- Movement: 固定(S0) (S0)
- Axis side: A侧
- Model: Jimeng4.0 / Veo 3.1 (dialogue medium shot)
- KB rules: A-SUS-01, C-FI-17, A-SUS-02

### Reference Images
@scene_ref - Dual color temperature system. CORRIDOR: L1-ceiling fluorescent 4000K cold white
@伊莎贝拉_char - 伊莎贝拉 character reference

### Action Frames (structured -- prose_smoother expands to NL)
### Movement Trajectory (3 phases → 3s · video model interpolates)

[0s 黄铜锁孔居中偏下。右手从上方伸入——拇指食指捏黄铜钥匙·红色标签垂下。钥匙尖对准锁孔·即将插入
  视觉状态: 深棕色木门板·木纹清晰。锁孔周围铜绿斑点·微磨损。冷白4000K均匀照明·木门冷色调

[1s 钥匙完全插入锁孔。拇指向右扭动——顺时针方向·手腕外旋·红色标签微晃
  视觉状态: 锁芯内部机械咬合。手指稳定·动作熟练——她来过这里

[2s·事件] 锁芯弹开。左手握门把下压。右手拔钥匙。门缝从零变为细线——暖黄光涌入
  视觉细节: 门板绕右边缘门轴旋转·左边缘离开门框向深处移动。缝隙从细线变成一掌宽再变成一半门宽。暖黄三角形亮区投射地面。L形构图完成

### Audio Track
Ambience: fridge compressor low hum (continuous)

### Prohibit List (P-FAL rule table)
1. no frame text(P8)
2. no mm precision(P2)
3. no pupil change(P1)
4. no sub-sec timing(P3)

### Segment Transition
HARD CUT. . (Not counted in segment duration.)

---

## Shot #A2: 全景→MS→CU(POV) | 5s

### Camera Parameter Card
- Shot type: 全景→MS→CU(POV)
- Focal length: 35mm→50mm→85mm
- Aperture: 中景深→浅景深
- Angle: 眼平1.55m(伊莎贝拉眼高·POV)
- Camera type: POV主观·门框中线
- Camera position: 门口内·距门0.3m·伊莎贝拉眼高1.55m·门框中线
- Movement: 间歇摇摄POV·极慢→停顿→慢→落定 (S1)
- Axis side: A侧
- Model: Jimeng4.0 / Veo 3.1 (dialogue medium shot)
- KB rules: C-FI-17, C-FI-06, A-SUS-02, C-KTZ-02

### Reference Images
@scene_ref - Dual color temperature system. CORRIDOR: L1-ceiling fluorescent 4000K cold white

### Action Frames (structured -- prose_smoother expands to NL)
### Movement Trajectory (5 phases → 5s · video model interpolates)

[3s POV全景·从门口看向室内。门框为暗色前景框。工业吊灯2800K暖黄·硬光·光锥向下·光锥外全黑
  视觉状态: 工作台居中·金属零件散落·工具架后墙。光和暗硬的分界线。前1秒完全静止

[4s 摄影机以极慢速度向右摇摄·每秒约1.5度。POV扫过工作台面——枪管哑光·弹簧暗银·螺丝散布。金属表面在暖黄下暖金反光
  视觉状态: 工具架——扳手·螺丝刀·油壶。摇摄速度匹配审视节奏

[5s·事件] 摇摄短暂停住。视线落在手枪扳机一道细微划痕上——金属表面的浅线
  视觉细节: 弹匣退出·枪膛打开。机械美感——金属与机油·秩序与暴力

[6s 摄影机以慢速重复向右摇摄·每秒约2度。POV离开光锥最亮区域·画面变暗。白色织物进入视线边缘——灰色毛巾搭在洗手池边
  视觉状态: 半明半暗中·毛巾轮廓渐显

[7s 摇摄落定。特写。灰色毛巾搭在池边·中央暗红血迹·手掌大小·中心深红发黑·边缘浅红褐。棉质纹理清晰。背景全虚。2秒凝视
  视觉状态: 血迹中心深色发黑·向外扩散变浅。织物白色与血暗红对比在暖黄下偏深红褐

  ⚡对白时序:
    VO (low whisper, breath more than voice): Rico...

### Audio Track
Ambience: fridge compressor low hum (continuous)
  @9s | VO (low whisper, breath more than voice): Rico... [~2.7 chars/s, ~2s]

### Prohibit List (P-FAL rule table)
1. no frame text(P8)
2. no mm precision(P2)
3. no pupil change(P1)
4. no sub-sec timing(P3)

### Segment Transition
HARD CUT. . (Not counted in segment duration.)

---

## Shot #A3: ECU→甩镜→CU | 4s

### Camera Parameter Card
- Shot type: ECU→甩镜→CU
- Focal length: 135mm→85mm
- Aperture: 极浅景深→中景深
- Angle: 门把高1.1m→面部眼平1.55m
- Camera type: ECU手→甩镜→CU面·门把侧
- Camera position: 楼道侧·门外0.4m·门把高1.1m→面部眼平
- Movement: 固定(2s)→甩镜(0.5s·约28度/秒)→固定(1.5s) (S0→S8→S0)
- Axis side: A侧
- Model: Hailuo02 (motion scene, color temp transition)
- KB rules: A-SUS-09, A-SUS-01, C-FI-06

### Reference Images
@scene_ref - Dual color temperature system. CORRIDOR: L1-ceiling fluorescent 4000K cold white
@伊莎贝拉_char - 伊莎贝拉 character reference

### Action Frames (structured -- prose_smoother expands to NL)
### Movement Trajectory (4 phases → 4s · video model interpolates)

[8s ECU·右手紧握门把——手掌包握·指关节发白。钥匙插在锁孔中·红色标签微晃。手在微微颤抖
  视觉状态: 不锈钢门把表面微细划痕。手背被冷白4000K照亮·手心在暗处

[9s·事件] 手指一根一根松开——指关节血色恢复。手掌从门把上离开·手指微屈悬停。VO低语Rico
  视觉细节: 门把上留下微细手汗痕迹。手指依旧微颤

[10s·事件] 身后脚步声——皮靴踩水磨石地面·由远及近。手突然弹开。甩镜——摄影机急速右转·0.5秒内所有东西变成水平模糊条纹
  视觉细节: 冷白4000K和暖黄2800K在甩镜中混合为暖冷光带。保持0.5秒——模拟听到脚步声后骤然转头

[10.5-11.0s·1.5s hold] 甩镜落定。CU面部·第一次看到她的脸。左脸暖黄2800K边缘光+右脸冷白4000K正面光·分界线沿鼻梁。眼睛睁大·瞳孔定住·嘴唇微张·下巴微抖。头右后转·回看走廊
  视觉状态: 走廊空无一人。日光灯微闪。脚步声停了。她全程不出声
  微运动: 呼吸可见于肩线微幅起伏·尘埃在光柱交汇区缓慢漂移·光影位置稳定·衣物纤维微幅沉降

### Audio Track
Ambience: fridge compressor low hum (continuous)

### Prohibit List (P-FAL rule table)
1. no frame text(P8)
2. no mm precision(P2)
3. no pupil change(P1)
4. no sub-sec timing(P3)
5. no limb deformation from fast motion(P9)

### Segment Transition
HARD CUT. . (Not counted in segment duration.)

---

## Shot #A4: 全景→中景→ECU | 8s

### Camera Parameter Card
- Shot type: 全景→中景→ECU
- Focal length: 24mm→35mm→135mm
- Aperture: 深景深→中景深→极浅景深
- Angle: 门口分界线→dolly back至1.2m→门把高1.1m
- Camera type: 全景走廊→dolly back→ECU锁孔
- Camera position: 门口分界线→dolly back至走廊侧1.2m→门把高1.1m
- Movement: 固定(2s)→dolly back(3s·约0.3m/s)→固定(3s) (S0→S3→S0)
- Axis side: A侧
- Model: Hailuo02 (motion scene, color temp transition)
- KB rules: A-SUS-08, C-FI-06, C-DEP-01

### Reference Images
@scene_ref - Dual color temperature system. CORRIDOR: L1-ceiling fluorescent 4000K cold white
@伊莎贝拉_char - 伊莎贝拉 character reference

### Action Frames (structured -- prose_smoother expands to NL)
### Movement Trajectory (4 phases → 8s · video model interpolates)

[12-13s·2s hold] 全景·空旷走廊。从近到远延伸·日光灯4000K微闪。空无一人。门框在前景底部·半开门·暖黄2800K矩形光柱投射地面。静止2秒
  视觉状态: 伊莎贝拉从门框中退出——深色背影从暖黄退入冷白。肤色从暖调回冷
  微运动: 呼吸可见于肩线微幅起伏·尘埃在光柱交汇区缓慢漂移·光影位置稳定·衣物纤维微幅沉降

[14-16s·3s过渡] 伊莎贝拉背影·右手拉门把向身体方向回收。门缝从半开变窄·暖黄矩形缩小。摄影机同时极慢后退·每秒约0.3米
  → 门完全闭合——锁舌入位。暖黄光彻底消失。走廊回到纯冷4000K。伊莎贝拉静止1秒
  运动过程: 门将合未合——缝隙只剩约5厘米。暖黄光只剩极细垂直线·如激光。面部最后一丝暖色边缘光消失——全脸进入4000K冷白。暖黄光彻底消失
  色温渐变: 2800K→4000K
  画面位移: 近景·门前→中景·退后

[17s·事件] 门完全闭合。ECU·右手掏钥匙·插入锁孔·手指一扭——锁芯弹响。手保持微抖。虎口微红痕
  视觉细节: 门闭合。深棕色木门·冷白4000K下门板颜色偏灰

[18-19s·2s hold] 钥匙拔出——水平滑出。手依旧抖。虎口压红痕。红色标签在手心微晃。手悬停半空——最后1秒淡出全黑
  视觉状态: 冷暖弧线完整闭环——冷白→暖涌入→暖主导→暖收缩→冷闭合
  微运动: 呼吸可见于肩线微幅起伏·尘埃在光柱交汇区缓慢漂移·光影位置稳定·衣物纤维微幅沉降

### Audio Track
Ambience: fridge compressor low hum (continuous)

### Prohibit List (P-FAL rule table)
1. no frame text(P8)
2. no mm precision(P2)
3. no pupil change(P1)
4. no sub-sec timing(P3)
5. no limb deformation from fast motion(P9)

### Segment Transition
BLACK SCREEN. Scene end.

---

> **script_assembler v2.0** | deterministic | 0 LLM tokens | 0 Agent calls
> **Total:** 4 shots | 20s
> **Next:** prose_smoother [Agent] reads ONLY this file -> NL smoothing -> final script