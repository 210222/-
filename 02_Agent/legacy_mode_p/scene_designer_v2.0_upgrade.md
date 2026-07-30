# Scene Designer v2.0 Upgrade — Keyframe 输出 + dialogue_map

> **定位:** scene_designer_v1.0.md 的增量补丁。基础设计流程不变，仅增加两个新的 YAML 输出域。
> **适用:** 所有 complexity_level (S/M/C)
> **版本:** v2.0 · 2026-07-08

---

## 新增 §7.4: segment_frames YAML 输出

### 为什么需要

v1.0 的 Scene Designer 产出逐镜 prose 描述（.md 报告中的自由文本），但没有产出机器可读的逐秒描述数据。下游的 script_assembler 无法从 v1.0 YAML 生成帧级台本描述。

v2.0 新增 `segment_frames` 域——为每个镜头提供关键帧（keyframe）级别的结构化描述。

### 什么是关键帧

关键帧是镜头内**状态发生变化的时刻**。不需要每秒都描述——只描述变化点。

```
一个 8 秒的擦杯子镜头：
  第 0 秒: 开始擦 (hold · 重复到第 6 秒)
  第 7 秒: 手机亮 (event · 单一时刻)
  → 2 个关键帧覆盖 8 秒

一个 10 秒的走向吧台镜头：
  第 0 秒: 起身离开窗边 (transition · 过渡到第 4 秒)
  → 1 个 transition 关键帧覆盖完整运动
```

### 输出格式

```yaml
segment_frames:
  - segment_id: "②"           # 必须匹配 segments_camera 的 segment_id
    shot_id: "#2"
    characters_in_frame: ["Isabela"]   # ← 新增字段
    keyframes:
      - kf_id: "②-1"
        sec_offset: 0          # 段内偏移秒 (0 = 镜头第一秒)
        global_sec: 6          # 场景绝对秒 (必须 = segment.time_range[0] + sec_offset)
        type: hold             # hold | event | transition
        hold_until: 12         # type=hold 或 type=transition 时必须
        action_anchor: "Isabela擦杯子·白布顺时针擦拭杯口·动作机械重复"
        performance:           # ← NEW v2.1: 表演细节
          facial:
            eyes: "眼睑半垂·视线落在杯口"
            brow: "眉位不变·无表情"
            mouth: "唇自然闭合"
          body:
            posture: "吧台后站立·重心均匀·上半身微前倾"
            hands: "左手持杯·右手白布·手腕匀速旋转"
        lighting: "L3(3000K)·伦勃朗三角光斑·鼻侧阴影柔和"
        spatial: "吧台大理石台面·杯架背景"
        audio: "咖啡机蒸汽嘶嘶声·冷藏柜嗡嗡声"

      - kf_id: "②-2"
        sec_offset: 7
        global_sec: 13
        type: event            # event 不需要 hold_until
        action_anchor: "手机亮·手停·目光移向屏幕"
        performance:
          facial:
            eyes: "视线从杯子骤然移向手机·瞳孔适应屏幕亮度"
            brow: "眉间微皱·眉心出现浅纵纹"
            mouth: "下唇微收·唇线变平"
          body:
            posture: "身体微前倾·重心移向前"
            hands: "右手擦拭动作骤停·左手伸向手机"
        lighting: "L3(3000K)暖黄面部+手机冷白(~6500K)从下方补光"
        spatial: "吧台大理石台面·手机平放"
        audio: "手机振动嗡鸣声·擦拭声停止"

  - segment_id: "⑭"
    shot_id: "#14"
    characters_in_frame: ["Rico"]
    keyframes:
      - kf_id: "⑭-1"
        sec_offset: 0
        global_sec: 122
        type: transition       # transition 需要 transition_target
        hold_until: 126        # 过渡终点秒 (必须 < segment.time_range[1])
        action_anchor: "Rico从窗边桌起身·离开座位·开始走向吧台"
        character_state:
          - {character: "Rico", pose: "从坐姿起身·右手撑桌面", gaze: "向右看Isabela方向"}
        lighting: "L2(6000K)·冷蓝晨光"
        spatial: "窗边双人桌·画面左1/3"
        audio: "椅子腿与红砖地面摩擦声"
        transition_target:     # type=transition 时必须
          action_anchor: "Rico步行至吧台前·Isabela对面·两人隔吧台站立"
          lighting: "L3(3000K)·暖黄吊灯主光"
          character_state:
            - {character: "Rico", pose: "站立·吧台前·与Isabela面对面", gaze: "直视Isabela眼睛"}
          spatial: "吧台前·画面右1/3"
        transition_params:     # 可选·可量化参数 (供 assembler 插值)
          color_temp_kelvin: {start: 6000, end: 3000}
          position_in_frame: {start: "左1/3", end: "右1/3"}
          gait_phase: {start: "起步", end: "停止"}
```

### 关键帧类型说明

| type | 何时使用 | 必填字段 | 插值方式 |
|------|---------|---------|---------|
| `hold` | 状态长时间持续 (≥2秒无变化) | action_anchor, hold_until | 轮转模板·轻微措辞变化 |
| `event` | 单一时刻的离散变化 | action_anchor | 精确描述·不插值 |
| `transition` | 位置/色温/表情的连续变化 | action_anchor, hold_until, transition_target | 线性插值 start→end |

### 🆕 v2.1: performance 字段 — 表演指令

剧本中有大量表演注释 ("瞬间挂上笑容，但眼睛没笑" / "声音压得极低" / "没有抽手")。
这些不是"情绪"——是**可渲染的解剖学指令**。performance 字段将它们翻译为 Seko 可以执行的描述。

**结构:**

```yaml
performance:                # 可选·含对白或表情变化的关键帧建议填写
  facial:                   # 面部微表情
    eyes: "描述眼睑/瞳孔/视线方向的精确状态"
    brow: "描述眉位/眉心/眉形的精确状态"
    mouth: "描述唇形/嘴角/唇间距离的精确状态"
  body:                     # 身体语言
    posture: "描述重心/脊柱/肩位"
    hands: "描述手部位置/动作/力度"
    head: "描述头位/颈部角度(可选)"
  voice:                    # 声音表演·仅对白关键帧填写
    quality: "音色/音量/气息"
    speed: "语速·字/秒"
    subtext: "台词下面的真实意思"
```

**剧本→performance 翻译规则:**

```
剧本写:                     performance 字段:
─────────────────────────────────────────────────
"瞬间挂上笑容，但眼睛没笑"    facial.mouth: "嘴角提肌收紧·上唇微升"
                            facial.eyes: "眼轮匝肌静默·下眼睑无皱褶"
                            facial.brow: "眉位不变"
                            voice.subtext: "热情但不亲近"

"声音压得极低"              voice.quality: "气声主导·喉部收紧·音量降至耳语级"
                            voice.speed: "≤3字/秒"

"没有抽手，看着他眼睛"      body.hands: "手腕被握·不抽回·手指放松"
                            facial.eyes: "视线锁定对方瞳孔·不闪躲"
                            facial.brow: "眉位微降·上眼睑微抬"

"他的手停在桌面上——一瞬间"  body.hands: "右手五指伸展·静止·指关节无动作"
                            facial.eyes: "视线焦点从远处收回到自己的手"

"不是问句"                  voice.quality: "句尾不下沉不上扬·平直"
                            facial.mouth: "句末唇形不回缩·保持开启"
```

**为什么是解剖学描述而非情绪标签:**

```
❌ "她悲伤地看着他"           → Seko 无法渲染"悲伤"
✅ facial.eyes: "下眼睑微红·泪膜增厚反光增强·视线固定在对方左眼"
   facial.mouth: "下唇微颤·嘴角下降约2mm"
   facial.brow: "眉心纵纹加深·眉头微抬(内侧上扬)"
   → 每一条都是视觉指令·Seko 可以逐条执行
```

### 覆盖规则

```
每个镜头的 keyframes 必须覆盖该镜头的所有秒。

验证方法 (写完后自检):
  for seg in segment_frames:
      covered = [False] * seg.duration
      for kf in seg.keyframes:
          if kf.type in (hold, transition):
              end = kf.hold_until - seg.start_sec
              covered[kf.sec_offset : end] = True
          else:  # event
              covered[kf.sec_offset] = True
      assert all(covered), f"Segment {seg.segment_id} 有未覆盖秒!"

如果发现空白秒:
  → 添加一个 type=hold 的 keyframe 覆盖空白区域
  → 或扩展相邻 keyframe 的 hold_until
```

### 🛑 action_anchor 文本禁令 (Gate 0 R02·违反=打回)

以下词绝对禁止出现在 action_anchor 中。这些是画布宪法第五条 + Gate 0 R02 的阻断项——不是建议：

```
禁止: 开始 | 正在 | 刚 | 已 | 持续 | 继续 | 一直 | 仍 | 缓缓 | 渐渐 | 慢慢 | 逐渐
原因: Seko 将这些词理解为过程动词·首帧渲染为"动作未完成"状态·与预期静态帧矛盾

替代:
  "开始走向吧台"        → "起身·走向吧台"
  "持续嗡嗡声"          → "嗡嗡声保持"
  "继续擦杯子"          → "重复擦拭动作"
  "正在擦杯子"          → "擦杯子·动作进行中" → "手持杯与布·擦拭姿态"
  "缓缓抬起头"          → "头以慢速抬起·约3秒完成"
```

### 🛑 performance 文本禁令 (Gate 0 R16·违反=打回)

以下词绝对禁止出现在 performance 的任何子字段中。PERFORMANCE_KB 使用它们作为**状态标识符**（章节标题），不是可渲染的解剖学描述：

```
禁止(状态名): 悲伤 | 愤怒 | 恐惧 | 紧张 | 焦虑 | 压抑 | 绝望 | 兴奋 | 厌恶 | 震惊
原因: Seko 无法渲染情绪标签·只能执行解剖学指令

正确做法:
  PERFORMANCE_KB 中 "紧张" 章节的内容是:
    facial.eyes: "眼睑微紧·眨眼频率增加·视线不稳定"
    body.hands: "手部动作增加·手指抖动·握拳或抓握衣物"
  → 使用这些解剖学描述·不使用"紧张"这个词本身
  → 如果必须引用状态名·标注为 "PERF_KB:tension" (内部标签·不进台本)
```

### 关键帧数量指南

| 镜头时长 | 建议 keyframe 数 | 最少 | 最多 |
|:---:|:---:|:---:|:---:|
| 3-6s | 1-2 | 1 | 3 |
| 7-10s | 2-3 | 1 | 5 |
| 11-15s | 3-5 | 2 | 7 |

全场景 (18 镜·168s) 建议总 keyframe 数: 35-55 个。

---

## 新增 §7.5: dialogue_map YAML 输出

### 为什么需要

v1.0 的对白信息嵌入在 .md 设计的 prose 中，无法被机器可靠提取。v2.0 需要结构化的对白→镜号×时序映射，供 script_assembler 生成精确的音轨。

### 输出格式

```yaml
dialogue_map:
  - shot_id: "#6"
    entries:
      - speaker: "Isabela"
        text_pt: "早啊，塞拉。老样子？"
        global_sec_start: 38    # 场景绝对秒·对白开始的时刻
        duration_s: 3.0          # 预估对白时长 (基于字数÷语速)
        direction: "瞬间挂上笑容，但眼睛没笑"

      - speaker: "Sera"
        text_pt: "你今天开门比平时早。"
        global_sec_start: 43
        duration_s: 2.5
        direction: "略带意外"

  - shot_id: "#13"
    entries:
      - speaker: "Isabela"
        text_pt: "我昨晚去工作室找你了。"
        global_sec_start: 106
        duration_s: 3.5
        direction: "声音压得极低"
      # ... 更多条目
```

### duration_s 计算规则

```
duration_s = max(2.0, min(6.0, len(text) × 0.25))

原理:
  - 中文对白语速 ~3-4字/秒
  - 以 4字/秒 为上限 (P-FAL-05)
  - 最短 2 秒·最长 6 秒 (更长的对白拆分为多个 entry)
```

### 必须覆盖

全部对话必须出现在 dialogue_map 中。包括:
- 所有 CV 对白
- 所有 VO 旁白
- 14 句对白 (EP2 实测)
- 对白必须与 keyframes 中的时间标注一致 (global_sec_start 必须在对应镜头的 time_range 内)

---

## §8.4 更新: 输出前自检新增

在原有 6 项自检基础上增加:

```
⚠️ 自检七: Keyframe 覆盖完整性
  对每镜的 segment_frames.keyframes:
    □ 首帧被覆盖? (必须有 sec_offset=0 的 keyframe)
    □ 尾帧被覆盖? (最后一个 keyframe 的 hold_until ≥ segment_end-1)
    □ 无空白秒? (相邻 keyframe 之间无间隙)
    □ type=hold/transition 有 hold_until?
    □ type=transition 有 transition_target?
  不通过 → 补充缺失的 keyframe

⚠️ 自检八: dialogue_map 覆盖完整性
  遍历剧本所有对白:
    □ 每句 CV 有对应 dialogue_map entry?
    □ 每句 VO 有对应 dialogue_map entry?
    □ 每个 entry 的 global_sec_start 在对应镜头的 time_range 内?
    □ 每个 entry 的 duration_s ≥ 2.0 且 ≤ 6.0?
  不通过 → 补充缺失的对白条目

⚠️ 自检九: Keyframe 与 dialogue_map 时间一致性
  对于既有对白又有关键帧的镜头:
    □ 对白的 global_sec_start 有对应的 keyframe (±2秒内有 event)?
    □ 说话角色在 characters_in_frame 中?
  不通过 → 调整 keyframe 时间或添加 event keyframe
```

⚠️ 自检十: action_anchor 文本合规 (🛑阻断·不可跳过)
  对全部 keyframe 的 action_anchor 字段执行正则扫描:
    □ 禁止词: /开始|正在|刚|已|持续|继续|一直|仍|缓缓|渐渐|慢慢|逐渐/
    命中 → 替换为静态替代词·重新输出
    □ 首字符检查: action_anchor 不以过程动词开头
  全部通过 → ✅通过

⚠️ 自检十一: performance 文本合规 (🛑阻断·不可跳过)
  对全部 keyframe 的 performance.* 子字段执行正则扫描:
    □ 禁止情绪词: /悲伤|愤怒|恐惧|紧张|焦虑|压抑|绝望|兴奋|厌恶|震惊/
    命中 → 替换为 PERFORMANCE_KB 中的解剖学描述·不输出状态名
    □ 禁止文学修饰: /像|如|仿佛|似乎|宛若|犹如/
    命中 → 替换为精确参数
  全部通过 → ✅通过

---

> **v2.1 · 2026-07-08**
> **变更:** §8.4 新增自检十(action_anchor文本禁令) + 自检十一(performance文本禁令)
> **核心:** 关键帧文本质量 → Gate 0 零阻断·从源头消除 R02/R16 违规
> **根因:** EP2 实测发现 Scene Designer 在 action_anchor 中自然使用 "开始/持续/继续"·在 performance 中混淆 KB 状态名与解剖描述
> **下游:** script_assembler v2.1 同步增加消毒层(安全网)
> **兼容:** v2.0 .yml 格式不变

---

## 🆕 §7.6: description_visual — 故事板专用画面描述 (v2.2)

### 为什么需要

`action_anchor` 是为视频渲染引擎设计的精确技术描述——含测量值、解剖术语、色温参数。这些是 `script_assembler` 和 Seko 视频生成所需的精度。

但故事板生成需要的是**手绘线稿画面描述**——简洁、视觉化、只写"画面上能看到什么"。`action_anchor` 中的 `约15度` `约3cm` `6000K` `口轮匝肌` 在手绘稿中没有意义。

v2.2 新增 `description_visual` 字段——同一帧，两份描述，两个用途：

| 字段 | 用途 | 消费者 |
|------|------|--------|
| `action_anchor` | 视频渲染引擎 | script_assembler · Seko 图生视频 |
| `description_visual` | 故事板画面生成 | STORYBOARD prompt · Seko 图生图 |

### 输出格式

每个 keyframe 新增可选字段（**S-Level 强制·M/C-Level 建议**）：

```yaml
keyframes:
  - kf_id: "①-1"
    sec_offset: 0
    type: hold
    action_anchor: "门板夹角约15度·铃舌偏转约3cm·6000K冷光在红砖地面割出约3cm宽锐利条形光斑"
    description_visual: "Isabela推开门——门铃轻响·冷蓝晨光铺在红砖地面"
    
    performance:
      facial:
        eyes: "眼轮匝肌静默·下眼睑无皱褶"
    # performance 不重复——description_visual 是独立的画面速写
```

### 写作规则

```
✅ 写"看到什么"          ❌ 不写"参数是多少"
✅ 人物动作+环境细节      ❌ 角度值·mm·cm·K值
✅ 光影效果·空间关系      ❌ 解剖术语(口轮匝肌等)
✅ 30-60字·一句话·画面感   ❌ 过程动词(开始/正在/持续)
```

### 对比示例

```
❌ action_anchor:    "门板夹角约15度·铃舌偏转约3cm·6000K冷光在红砖地面割出约3cm光斑"
✅ description_visual: "门推开一道缝·门铃轻响·冷蓝晨光铺在红砖地面"

❌ action_anchor:    "口轮匝肌收缩·嘴角对称上提约1.2mm·眼轮匝肌无激活"
✅ description_visual: "嘴角上扬·眼睛没笑——标准的社交微笑"

❌ action_anchor:    "上眼睑抬高约2mm·下眼睑收紧约1mm·巩膜暴露约3mm²"
✅ description_visual: "眼睛微微睁大·盯着对方"

❌ action_anchor:    "右手棉布绕示指一周·布面在杯口内壁顺时针画圈擦拭"
✅ description_visual: "手拿抹布在杯口内壁打圈擦拭"

❌ action_anchor:    "身体顺时针旋转约25度·右臂上抬肘角约120度·右手伸向冲煮头金属手柄"
✅ description_visual: "她转身·伸手去够咖啡机的手柄"
```

### 参考模板风格

```
模板帧描述 (人手写/Agent写的画面语言):
  "低角度。窄巷中段——两侧墙面挤压·宽不足两米。碎石地面·积水洼·青苔。"
  "Pedro踩住足球——光脚踩在球上。弯腰——双手捡球。"
  "直升机低空掠过画面→远去·航向摩天楼群方向。"

特点: 短句·逗号分隔·画面速写·偶尔保留方向性量词(不足两米)但不堆砌数字
```

### 覆盖规则

```
description_visual 覆盖 keyframe 的 hold 区间——hold 类型的所有秒共享同一描述。
event 类型仅覆盖该秒。
transition 类型覆盖 transition 区间。

无 description_visual 的秒 → 下游脚本自动从 action_anchor 提取画面摘要(降级·质量下降)
```

### 🆕 自检十二: description_visual 文本质量

```
对全部 keyframe 执行:
  □ 有 description_visual? (S-Level 必须全部有·M/C-Level 至少首尾帧有)
  □ 不含测量值? /[约]?\d+[\.\d]*\s*[度mmcmK]/
  □ 不含解剖术语? /口轮匝肌|眼轮匝肌|颧大肌|胸锁乳突肌|肱三头肌|掌指关节/
  □ 不含过程动词? /开始|正在|刚(?!好)|已(?!经)|持续|继续/
  □ 字数 20-70? (太短信息不足·太长失去速写感)
  □ 读起来像手绘稿标注而非技术手册?
不通过 → 重写该字段
```

---

## 🆕 §7.7: 故事板标注三字段 — composition_note / lighting_note / motion_note (v2.3)

### 为什么需要

v2.2 的 `description_visual` 解决了故事板的**画面描述**问题。但故事板还有三个标注维度——🟢构图、🟠光线、🔴运动——当前是由下游脚本 `_gen_sb_sparse.py` 用硬编码规则生成的：

| 标注 | 当前脚本做法 | 问题 |
|------|------------|------|
| 🟢绿色构图 | `if '全景' in st: '纵深空间·环境为主'` | 通用标签·换场景也输出同样文本 |
| 🟠橙色光线 | 从 `description` 抠 `6000K`/`暖光` 关键词 | 碎片拼凑·无场景整体理解 |
| 🔴红色运动 | 180行 `if-elif` 链解析 `action_anchor` | 脆弱·Agent 措辞变化即失效 |

参考模板（场景D 贫民窟窄巷）的标注是**场景特定的**：
```
🟢绿:巷宽不足2m=画面自然框·两侧墙面=垂直引导线·一线天=画面上方1/5天空带
🟠橙:阴灰散射光~6000-6500K·顶光漫反射·无方向性阴影·巷内减光1-2档
🔴红→:Pedro向前跑(纵深方向·实线箭头)
```

这些不是通用模板——是这个场景独有的空间和光线逻辑。只有 Agent 在理解这个场景后才能写出。

v2.3 新增三个字段，让 Agent 在产出 `action_anchor` 和 `description_visual` 时，同步产出标注文本。**不需要新知识库**——Agent 已有 `camera_position`、`shot_type`、`global_anchors.lighting`、`action_anchor` 全部所需数据。

### 输出格式

```yaml
keyframes:
  - kf_id: "⑥-1"
    sec_offset: 0
    type: hold
    action_anchor: "门板夹角约15度·铃舌偏转约3cm·6000K冷光在红砖地面割出锐利条形光斑"
    description_visual: "一只手握住黄铜门把·门推开一道缝·门铃轻晃·冷蓝晨光铺进门内红砖地面"

    # ↓ v2.3 新增——故事板四色标注 ↓
    composition_note: "门口=画面框架·门口→吧台=纵深引导线·纵深空间·环境为主"
    lighting_note: "门口6000K冷蓝晨光·吧台3000K暖黄吊灯"
    motion_note: "推门·门铃晃·冷光铺入"
```

### 字段写作规则

#### 🟢 composition_note（构图标注·绿色）

```
规则:
  ✅ 场景特定的空间逻辑——这个镜头的机位+景别组合产生什么构图效果
  ✅ 参考 camera_position + shot_type + focal_length + 九宫格理解
  ✅ 格式: "空间锚点=构图效果·引导线方向·景别功能"
  ✅ 字数: 15-40字
  ❌ 禁止纯通用标签——不能只写"纵深空间·环境为主"（那是脚本的 fallback）

示例:
  shot #1·全景·24mm·A区门口内侧 → "门口=画面框架·门口→吧台=纵深引导线·纵深空间·环境为主"
  shot #8·特写·85mm·D区左墙前    → "墙面=人物背景·局部聚焦·背景虚化"
  shot #11·全景·24mm·C区红砖墙侧  → "红砖墙=垂直引导·吧台=画面分割线·纵深空间·环境为主"
  shot #16·近景·85mm·C区透过窗    → "窗框=内外空间分界·人物为主·环境压缩"
```

#### 🟠 lighting_note（光线标注·橙色）

```
规则:
  ✅ 本镜头实际出现的光源·色温·光质
  ✅ 参考 keyframe.description + global_anchors.lighting
  ✅ 格式: "光源+色温+光质·按重要性排列"
  ✅ 字数: 12-30字
  ✅ 同一场景的光源组合只在这个镜头确实有变化时才不同
  ❌ 禁止写不在此镜头画面中出现的光源

示例:
  门口镜头·冷光为主       → "门口6000K冷蓝晨光·吧台3000K暖黄吊灯"
  吧台特写·暖光为主       → "吧台3000K暖黄吊灯·伦勃朗三角光斑右颧骨"
  室外镜头·阴灰散射       → "阴灰散射光~6000-6500K·顶光漫反射·无方向性阴影"
  纯黑画面               → "无光源·纯黑帧"
  手机屏幕光              → "手机屏幕冷白光~6500K补光·吧台3000K暖黄吊灯"
```

#### 🔴 motion_note（运动标注·红色）

```
规则:
  ✅ PURE action——只写身体/物体怎么动·不写画面有什么
  ✅ 从 action_anchor 或 description_visual 浓缩出最核心的动作
  ✅ 格式: "动作动词+对象·动作动词+方向"（逗号分隔·不用连接词）
  ✅ 字数: 5-15字（严格）
  ✅ 静态画面填空字符串 "" 或不填
  ❌ 禁止包含测量值/解剖术语/色温/画面描述
  ❌ 禁止超过 15 字
  ❌ 禁止写身体部位作为主语（"一只手""右手"等）

对比:
  description_visual (画面描述):  "一只手握住黄铜门把·门推开一道缝·门铃轻晃·冷蓝晨光铺进门内红砖地面"
  motion_note (运动标注):        "推门·门铃晃"                                      ← 7字

  description_visual:  "Isabela走入吧台后·手指按下咖啡机拨杆·蒸汽柱从冲煮头喷涌而出"
  motion_note:         "走入吧台·按下拨杆"                                          ← 9字

  description_visual:  "微笑从脸上一瞬消失·嘴角垂落·嘴唇合拢·面部回到毫无表情的状态"
  motion_note:         "微笑消失·嘴角垂落"                                          ← 9字

  description_visual:  "Rico大步穿过咖啡馆纵深·从窗边走向吧台·大理石台面横在两人之间"
  motion_note:         "穿过纵深·走向吧台"                                          ← 9字

  description_visual:  "Rico转过身去·后背朝向镜头·双肩齐平·朝门口走去·不回头"
  motion_note:         "转身·走向门口"                                              ← 7字

  description_visual:  "咖啡馆全景·两人静止不动·咖啡机嘶鸣停歇·唯有冷藏柜嗡嗡声回荡"
  motion_note:         ""                                                            ← 静态·无运动
```

### 覆盖规则

```
composition_note / lighting_note:
  hold + transition 类型: 整个 hold/transition 区间共享同一值
  event 类型: 仅该秒
  同镜内 keyframe 之间通常不变·变化时才更新

motion_note:
  hold 类型: 覆盖整个 hold 区间
  event 类型: 仅该秒
  transition 类型: 覆盖整个 transition 区间
  每镜至少第一个 keyframe 有值（除非全镜静态）
```

### 🆕 自检十三: 标注三字段质量

```
对全部 keyframe 执行:
  □ composition_note 有值? (S-Level 必须全部有·M/C-Level 至少首帧有)
    □ 包含 camera_position 的场景锚点? (门口/吧台/窗/墙 至少一个)
    □ 不是纯通用标签? (不能只写"纵深空间·环境为主")
    □ 字数 15-40?
  □ lighting_note 有值? (S-Level 必须全部有·M/C-Level 至少首帧有)
    □ 包含至少一个光源+色温?
    □ 字数 12-30?
  □ motion_note 考虑了? (无身体运动的帧可空)
    □ 有值则字数 5-15?
    □ 不含测量值? /[约]?\d+[\.\d]*\s*[度mmcmK]/
    □ 不含画面描述·不含身体部位主语?
    □ 读起来像箭头标注而非画面描述?
不通过 → 重写该字段
```

---

> **v2.3 · 2026-07-09**
> **变更:** §7.7 新增 composition_note / lighting_note / motion_note 三字段 + 自检十三
> **核心:** 故事板四色标注从脚本硬编码迁移到 Agent 场景理解——每个标注都是**这个场景独有的**
> **根因:** EP2 实测——脚本生成的构图/光线/运动标注为通用标签·质量远低于 Agent 场景理解可达到的水平
> **下游:** _gen_sb_sparse.py 优先读取三字段·不可用时降级为现有硬编码逻辑(兼容)
> **知识库:** 不需要新KB·Agent 已有 camera_position/shot_type/global_anchors/action_anchor 全部所需数据
> **兼容:** v2.0/v2.1/v2.2 .yml 格式不变·三字段均为可选字段
