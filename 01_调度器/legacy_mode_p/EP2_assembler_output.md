# EP2 Cafe da Isa -- Director Script (assembler v2.0 draft)

> **Pipeline:** MODE:P | M-Level | deterministic assembly v2.0
> **Scene:** Rico工作室门口+室内 | 20s | 4 shots
> **Axis:** A侧(门轴对侧·锁孔侧)
> **Movement:** 2/4 static (50%)
> **Keyframe data:** NO (fallback mode) | Dialogue map: NO (heuristic)
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
# CAM: 正面微俯5度 | ECU锁孔·门轴对侧 | camera static
# ZONE: D | LIGHT: L1-吸顶荧光灯 + L2-工业吊灯 + L3-门缝暖光
# CHARS: 伊莎贝拉

0-2s: [ECU→MCU] cam static | 85mm→35mm 浅景深→中景深 | light:L1-吸顶荧光灯 + L2-工业吊灯 + L3-门缝暖光

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
# CAM: 眼平1.55m(伊莎贝拉眼高·POV) | POV主观·门框中线 | camera 间歇摇摄POV·极慢→停顿→慢→落定
# ZONE: D | LIGHT: L1-吸顶荧光灯 + L2-工业吊灯 + L3-门缝暖光
# DIALOGUE timing:
#   [VO] @ ~4s (2s): Rico...

3-7s: [全景→MS→CU(POV)] cam 间歇摇摄POV·极慢→停顿→慢→落定 | 35mm→50mm→85mm 中景深→浅景深 | light:L1-吸顶荧光灯 + L2-工业吊灯 + L3-门缝暖光
    CV [VO]: Rico...

### Audio Track
Ambience: fridge compressor low hum (continuous)
  @4s | VO (narrative): Rico... [~1.6 chars/s, ~2s]

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
# CAM: 门把高1.1m→面部眼平1.55m | ECU手→甩镜→CU面·门把侧 | camera 固定(2s)→甩镜(0.5s·约28度/秒)→固定(1.5s)
# ZONE: D | LIGHT: L1-吸顶荧光灯 + L2-工业吊灯 + L3-门缝暖光
# CHARS: 伊莎贝拉

8-11s: [ECU→甩镜→CU] cam 固定(2s)→甩镜(0.5s·约28度/秒)→固定(1.5s) | 135mm→85mm 极浅景深→中景深 | light:L1-吸顶荧光灯 + L2-工业吊灯 + L3-门缝暖光

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
# CAM: 门口分界线→dolly back至1.2m→门把高1.1m | 全景走廊→dolly back→ECU锁孔 | camera 固定(2s)→dolly back(3s·约0.3m/s)→固定(3s)
# ZONE: D | LIGHT: L1-吸顶荧光灯 + L2-工业吊灯 + L3-门缝暖光
# CHARS: 伊莎贝拉

12-15s: [全景→中景→ECU] cam 固定(2s)→dolly back(3s·约0.3m/s)→固定(3s) | 24mm→35mm→135mm 深景深→中景深→极浅景深 | light:L1-吸顶荧光灯 + L2-工业吊灯 + L3-门缝暖光

16-19s: [全景→中景→ECU] cam 固定(2s)→dolly back(3s·约0.3m/s)→固定(3s) | 24mm→35mm→135mm 深景深→中景深→极浅景深 | light:L1-吸顶荧光灯 + L2-工业吊灯 + L3-门缝暖光

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