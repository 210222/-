# TIME_SKELETON v1.0 — 统一时间骨架规范

> **定位:** 场景级逐秒时间轴数据结构——故事板、视频提示词、审查报告三者的单一真源（Single Source of Truth）。
> **设计依据:** 方案二/v3.0架构 · storyboard_planner §2E.4 + prompt_composer §3.3d 编号系统同构
> **版本:** v1.0 · 2026-07-07
> **维护者:** storyboard_planner (生产者) · prompt_composer + 审查专家 (消费者)
> **存储:** 每个场景一个 TIME_SKELETON · 随 PLAN_[场景名].md 一起输出

---

## §1 核心原则

```
┌──────────────────────────────────────────────────────────────────┐
│                    TIME_SKELETON 三原则                           │
│                                                                  │
│  原则1: 单一定义 · 多处引用                                       │
│    时间信息在 TIME_SKELETON 中定义一次。                           │
│    故事板、视频提示词、审查报告都引用它——不各自重复定义时间。       │
│                                                                  │
│  原则2: 骨架是源 · 产出物是视图                                    │
│    TIME_SKELETON = 数据库                                         │
│    故事板线稿    = TIME_SKELETON 的视觉视图（空间层）              │
│    视频提示词    = TIME_SKELETON 的文本视图（时间层）              │
│    审查报告      = TIME_SKELETON 的 diff 视图（验证层）            │
│                                                                  │
│  原则3: 硬约束锁定 · 软锚点展开                                    │
│    运镜状态、摄影机位置、段时长 → 硬约束·不可被覆盖                │
│    action_anchor、画面描述细节   → 软锚点·消费者可在锚点基础上展开  │
└──────────────────────────────────────────────────────────────────┘
```

---

## §2 数据结构

### 2.0 顶层结构

```yaml
TIME_SKELETON:
  # === 场景级元数据 (从PLAN骨架§A继承·不可变) ===
  scene_id: "Rico工作室"
  scene_time_of_day: "凌晨4:30"            # 场景内时间·氛围锚点
  total_duration_sec: 14                    # 场景总时长(秒)
  
  # === 全局锚点 (从PLAN骨架§A继承·逐字锁定) ===
  global_anchors:
    character:                              # A1: Character Anchor Block
      Rico: "Latin male, mid-30s, short dark brown hair slicked back, stubble beard, deep-set brown eyes, scar on right eyebrow, worn black leather jacket over grey henley"
    environment:                            # A2: Environment Anchor Block
      description: "凌晨4:30的Rico工作室·工作台靠左墙·洞洞板工具墙居中·洗手池在右"
    style_spine:                            # A3: Style Spine
      description: "shot on Arri Alexa 35, Kodak Vision3 500T, desaturated warm amber grade, subtle film grain"
    lighting:                               # A4: Lighting Anchor
      description: "single tungsten pendant lamp, 2800K, centered above workbench, soft shadows on workbench surface, hard shadows on back wall"
    constraints:                            # A5: Constraint Block
      - "面部比例全程一致·五官不漂移"
      - "光线色温全程锁定2800K无闪烁"
      - "画面稳定无晃动·动作流畅自然"
      - "无字幕·无Logo·无水印"

  # === 逐秒时间轴 (核心数据结构) ===
  segments: []                              # 每段一个segment·段=摄影机位置连续区间
```

### 2.1 Segment 结构 (摄影机位置段)

```yaml
segments:
  - segment_id: "①"
    time_range: [0, 5]                      # [起始秒, 结束秒]·闭区间
    duration_sec: 5
    camera:
      shot_type: "全景"                     # 全景/中全景/中景/中近景/近景/特写/大特写
      focal_length: "24mm"                  # 35mm等效焦距
      dof: "深景深f/8"                      # 景深描述
      movement: "固定→极慢前推(0.02x)"       # 运镜类型+速度
      angle: "眼平"                         # 拍摄角度
    transition:                             # 段末转场 (如果是最后一段)
      type: "①→②"
      to_segment: "②"
      
  - segment_id: "①→②"
    time_range: [5, 6]                      # 过渡秒
    duration_sec: 1
    transition_type: "极慢前推"              # 运镜过渡类型
    path: "直线·沿房间中轴线"               # 摄影机运动路径
    speed: "匀速·1s"                        # 速度描述
    visual_change: "门框边缘缓慢滑出·Rico背影变大·光区扩展"
    from_segment: "①"
    to_segment: "②"
    
  - segment_id: "②"
    time_range: [6, 14]
    duration_sec: 8
    camera:
      shot_type: "中近景"
      focal_length: "50mm"
      dof: "浅景深f/2.8"
      movement: "固定"
      angle: "低角度(约20cm高)"
    transition: null                        # 场景末段·无转场
```

### 2.2 Frame 结构 (逐秒冻结帧)

```yaml
frames:                                     # 逐秒条目·N秒=N条
  - sec: 0                                  # 秒偏移(段内从0开始)
    global_sec: 0                           # 场景内全局秒偏移
    camera_position: "①"                    # 引用 segment_id
    is_transition_frame: false
    frame_label: "格1"                      # 对应故事板格号
    
    # === 硬约束 (不可被消费者覆盖) ===
    hard:
      shot_type: "全景"
      focal_length: "24mm"
      camera_movement: "固定"               # 该秒的运镜状态
    
    # === 软锚点 (消费者可在锚点基础上展开) ===
    soft:
      action_anchor: "Rico背对镜头坐在台灯后——身体剪影·仅肩膀和头顶极细暖黄边缘光"
      spatial_anchor: "台面暖黄光区照亮木纹和散落小物件·光区外全黑"
      prop_state:                           # 该秒关键道具状态
        - item: "台灯"
          state: "亮·2800K暖黄"
        - item: "工作台"
          state: "散落小物件(未辨识)"
      character_state:
        - character: "Rico"
          pose: "背对镜头坐"
          position: "工作台后·画面中央"
          expression: null                 # 该秒无面部可见
    
    # === 音频锚点 ===
    audio:
      ambience: "室内低频持续"
      events: []                           # 该秒的声音事件

  - sec: 1
    global_sec: 1
    camera_position: "①"
    is_transition_frame: false
    frame_label: "格2"
    hard:
      shot_type: "全景"
      focal_length: "24mm"
      camera_movement: "极慢前推中"
    soft:
      action_anchor: "推进继续·门框已滑出画面·Rico背影占画面约1/3"
      spatial_anchor: "台面木纹年轮从模糊弧线向清晰纹理过渡·光区扩展"
      prop_state:
        - item: "台灯"
          state: "亮·2800K暖黄"
        - item: "工作台"
          state: "更多散落物件轮廓浮现"
      character_state:
        - character: "Rico"
          pose: "背对镜头坐·背影变大"
          position: "画面中央约1/3"
          expression: null
    audio:
      ambience: "室内低频持续"
      events: []

  # ... 每秒一个 frame 条目 ...

  - sec: 5
    global_sec: 5
    camera_position: "①→②"
    is_transition_frame: true
    frame_label: "格5→格6 运镜过渡"
    hard:
      shot_type: "全景→中近景过渡"
      focal_length: "24mm→50mm过渡"
      camera_movement: "极慢前推·匀速"
    soft:
      action_anchor: "摄影机沿中轴线前移·Rico背影从中景变为中近景"
      spatial_anchor: "两侧墙壁滑出·台面占画面比例增大"
      prop_state:
        - item: "台灯"
          state: "亮·2800K暖黄·光区在画面中扩大"
      character_state:
        - character: "Rico"
          pose: "背影·过渡中"
          position: "画面中央·占比增大"
          expression: null
    audio:
      ambience: "室内低频持续"
      events: []

  - sec: 6
    global_sec: 6
    camera_position: "②"
    is_transition_frame: false
    frame_label: "格7"
    hard:
      shot_type: "中近景"
      focal_length: "50mm"
      camera_movement: "固定(落定)"
    soft:
      action_anchor: "Rico右手从暗处伸入光区——暖黄光先在指尖亮起·沿手指向后蔓延"
      spatial_anchor: "指尖轻触台面深色小物(约3cm)·光区集中在手部周围"
      prop_state:
        - item: "深色小物"
          state: "被指尖轻触·未辨识"
        - item: "台灯"
          state: "亮·2800K暖黄"
      character_state:
        - character: "Rico"
          pose: "右手伸出·指尖在光区中"
          position: "画面右1/3"
          expression: null
    audio:
      ambience: "室内低频持续"
      events:
        - second: 6
          type: "SFX"
          description: "指尖轻触金属·微弱叮声"
          duration: 0.3

  # ... 每秒持续到场景结束 ...
```

---

## 🆕 §2.3 M-Level 精简骨架 (段级·无 frames)

> **v1.1 新增:** M-Level 场景不需要逐秒冻结帧。segments 段级数据足够 prompt_composer 展开为逐秒描述。
> **触发条件:** complexity_level = "M" · 静态比例 < 80% · 运镜为段级参数
> **S-Level / C-Level 不受影响:** S-Level 台本嵌入式·C-Level 仍需完整 frames

```yaml
TIME_SKELETON (M-Level):
  scene_id: "鉴证科实验室"
  complexity: "M"
  
  global_anchors:        # 同标准格式·不变
    character: ...
    environment: ...
    style_spine: ...
    lighting: ...
    constraints: ...
  
  segments: []           # 段级数据·只需定义每段
    - segment_id: "①"
      time_range: [0, 4]       # [起始秒, 结束秒]
      duration_sec: 4
      camera:
        shot_type: "ECU"
        focal_length: "100mm"
        dof: "极浅f/1.4"
        movement: "固定"
        angle: "水平"
      action_anchor: "弹头在显微镜载物台上·环形LED 3200K侧光掠过膛线纹路"
      spatial_anchor: "弹头占画面~5%·其余纯黑负空间"
      lighting: "3200K暖黄侧光·15°掠射角"
      audio:
        ambience: "室内低频·空调运转音"
        events: []
    
    - segment_id: "②"
      time_range: [4, 7]
      duration_sec: 3
      camera:
        shot_type: "近景"
        focal_length: "50mm"
        dof: "中浅f/2.8"
        movement: "固定"
        angle: "眼平"
      action_anchor: "Vincent直起腰·摘下黑框眼镜·揉鼻梁"
      spatial_anchor: "Vincent在画面右2/3·显微镜前景左侧虚化"
      lighting: "底光3200K(显微镜反弹)+顶光5000K·倒置阴影"
      audio:
        ambience: "室内低频"
        events: []

  # frames: []           # ← M-Level 不输出 frames 数组
                          # prompt_composer 从 segments 的 time_range + action_anchor 展开逐秒描述
```

**M-Level 与 C-Level 的区别:**

| 字段 | C-Level | M-Level |
|------|:---:|:---:|
| segments[] | ✅ | ✅ |
| frames[] | ✅ 逐秒·N秒=N条 | ❌ 不输出 |
| action_anchor | 在 frames[].soft 中 | 在 segments[] 中 |
| prompt_composer 如何展开 | 从 frames[].soft 逐秒复制 | 从 segments[].action_anchor + time_range 自动展开 |

**预期节省:** 58帧→17段(-71% YAML行数)·Scene Designer 输出 ~400行 → ~300行

---

三个消费者各自从 TIME_SKELETON 派生自己的产出物：

### 3.1 故事板线稿 (视觉视图)

```
从 TIME_SKELETON 派生:
  global_anchors → 共享视觉锚块 (场景空间/固定光源/固定道具/贯穿人物/空间关键)
  frames[].sec   → 格N 的 [Ns·景别·焦距·运镜]
  frames[].soft.action_anchor  → 格N 的画面描述(只取空间/姿态部分)
  frames[].soft.spatial_anchor → 格N 的空间结构
  segments[].camera             → 格N 的标注文本
  segments[].transition         → 运镜过渡标记

不取自 TIME_SKELETON (故事板生成器自行补充):
  箭头标注 (红/蓝/绿/橙)
  构图标记 (三分法/引导线)
  透视关系 (一点/两点/三点)
  
原因: 这些是视觉语法层面的信息——TIME_SKELETON 只说"是什么"，
      故事板说"怎么画"。
```

### 3.2 视频提示词 (文本视图)

```
从 TIME_SKELETON 派生:
  global_anchors     → Subject / Style / Constraints (逐字复制)
  segments[].camera  → Camera 汇总段
  frames[].sec       → Action 逐秒描述的时间轴
  frames[].soft.*    → Action 逐秒画面描述(展开为完整文本)
  frames[].audio     → 时序描述 (音效/CV/VO)
  frames[].hard.*    → 每秒运镜状态(不重复·已在Camera中)

不取自 TIME_SKELETON (prompt_composer 自行补充):
  @声明区 (从 IMAGE_AUDIT 提取)
  线稿专用声明
  材质/纹理/色彩的具体描述
  【禁止】块

原因: 信息分工铁律——TIME_SKELETON 有空间骨架，
      prompt_composer 填血肉(材质/光影/色彩)。
```

### 3.3 审查报告 (diff 视图)

```
审查专家不重新描述时间——他们对 TIME_SKELETON 做 diff:

检查项:
  □ 故事板格N 的构图 = TIME_SKELETON.frames[N].hard 的景别+运镜?
  □ 视频提示词第N秒 = TIME_SKELETON.frames[N].soft.action_anchor 展开?
  □ 格N→格N+1 运镜过渡 = TIME_SKELETON.segments 的 transition?
  □ 全局锚点逐字一致? (故事板共享锚点 = 提示词Subject/Style = 骨架原文?)
  □ 道具状态: frames[N].prop_state → frames[N+1].prop_state 变化有中间帧?

输出: 仅输出差异项·不通过则标注骨架偏移量
```

---

## §4 生产者与消费者契约

```
┌──────────────────────────────────────────────────────────────────┐
│                     TIME_SKELETON 数据流                           │
│                                                                  │
│  Step A2.5: storyboard_planner                                   │
│    输入: 三Agent设计报告 + 空间地图 + 参考图 + ANCHOR_BASELINE    │
│    输出: PLAN_[场景名].md                                         │
│           ├─ §A 全局锚点 (global_anchors)                         │
│           ├─ §B TIME_SKELETON (segments + frames·YAML块)          │
│           └─ §C 连续性检查清单                                    │
│                                                                  │
│  Step A3: prompt_composer                                        │
│    输入: PLAN_[场景名].md → Read §A + §B                          │
│    继承: §A 逐字复制到 Subject/Style/Constraints                  │
│    展开: §B frames[].soft 展开为逐秒画面描述                       │
│    输出: VIDEO_PROMPT_[场景名].md                                 │
│                                                                  │
│  Step A4: 故事板生成器 (GPT Image / DALL·E)                       │
│    输入: PLAN_[场景名].md §A + §B                                 │
│    派生: 共享视觉锚 + 逐格画面描述                                  │
│    输出: STORYBOARD_[场景名].md (线稿prompt)                      │
│                                                                  │
│  审查层 (方案二·独立专项专家):                                     │
│    输入: TIME_SKELETON + 故事板 + 视频提示词                       │
│    验证: 逐秒对照·只输出差异                                       │
│    输出: AUDIT_[场景名].md (骨架偏移量报告)                        │
└──────────────────────────────────────────────────────────────────┘
```

---

## §5 与现有编号系统的兼容

TIME_SKELETON 完全兼容现有的 storyboard_planner §2E.4f 编号系统：

```
现有映射 (手动维护)                  TIME_SKELETON (自动保证)
─────────────────────────────       ─────────────────────────
格1 [0s·...]: ①位置                  frames[sec:0].camera_position = "①"
格2 [1s·...]: ①位置                  frames[sec:1].camera_position = "①"
格N→格N+1 [运镜过渡]                 segments[id:"①→②"].time_range
格N+1 [...]: ②位置                   frames[sec:N+1].camera_position = "②"

编号含义 (两处各写一遍)               编号含义 (只在 TIME_SKELETON 定义一次)
故事板格 = 提示词秒 (人工对照)        故事板格 ← sec → 提示词秒 (结构保证)
```

---

## §6 文件产出规范

每个场景输出以下文件——不再有冗余：

| 文件 | 内容 | 引用 TIME_SKELETON? |
|------|------|:--:|
| `PLAN_[场景].md` | §A全局锚点 + §B TIME_SKELETON + §C检查清单 | 定义者 |
| `VIDEO_PROMPT_[场景].md` | @声明区 + 五段式提示词 (从骨架展开) | 消费者 |
| `STORYBOARD_[场景].md` | 故事板线稿prompt (从骨架派生) | 消费者 |
| `AUDIT_[场景].md` | 骨架偏移量报告 (diff格式·仅差异) | 验证者 |

**删除的文件类型：**
- `STORYBOARD_叙事_*.md` — 叙事版本·与完整故事板冗余
- `STORYBOARD_*_审查报告.md` — 一次性审查产物·不再独立输出
- `*_scene_level_v*.md` — 中间设计产物·内容已在PLAN中

---

> **v1.0 · 2026-07-07**
> **创建:** 方案二/v3.0架构 · 统一时间骨架
> **关联:** storyboard_planner_v2.0.md · prompt_composer_v2.0.md · P-CONSTITUTION.md
> **下一步:** storyboard_planner 升级为 TIME_SKELETON 生产者
