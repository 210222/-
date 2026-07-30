# YAML-only Agent间通信协议 v1.0

> **版本:** v1.0 · 2026-07-07
> **设计依据:** EP14架构浪费分析——审计Agent读取设计Agent完整输出(含推理·自检·设计依据)而非仅读结构化YAML。信息生命周期追踪显示同一空间描述在9次产生/复制中累积消耗~130-180K tokens·其中~50%为纯重复。
> **宪法依据:** 画布第七条(独立验证优先于自我审查)·独立验证=推理隔离·非文件加载隔离
> **核心原则:** 设计Agent产出"两部分"——自由文本(人类审核) + 结构化YAML(机器消费)。审计Agent只读YAML。
> **预期效果:** 每审计Agent节省40-60%输入token·消除推理过程/自检/设计依据的Agent间传输

---

# §1 原则

## 1.1 通信边界

```
┌─────────────────────────────────────────────────────────────────────┐
│                Agent间通信 = 结构化数据管道                            │
│                                                                      │
│  设计Agent产出两部分:                                                 │
│    A. §6 YAML块 (结构化·参数化·被下游消费)                            │
│    B. 自由文本 (推理·自检·设计依据·仅供人类审核)                       │
│                                                                      │
│  下游Agent(审计·规划·合成)只读A·不读B。                               │
│                                                                      │
│  人类审核可在任何时间读取A+B。                                        │
│                                                                      │
│  Agent <─ YAML ─> Agent    (机器对机器·结构化)                       │
│  Human <─ MD+YAML ─ Agent  (人类审核·完整阅读)                       │
└─────────────────────────────────────────────────────────────────────┘
```

## 1.2 通信规则

```
YC-01: 设计Agent的输出必须分成两个物理文件——.md(自由文本) + .yml(结构化数据)
YC-02: 下游Agent的输入只能是.yml文件·不得读取.md自由文本
YC-03: 下游Agent的SW-C02上下文隔离声明中·只列出.yml文件·不列.md文件
YC-04: 自由文本.md中包含YAML副本·供人类在单一视图中阅读(便利性)
        但Agent不读这个副本——Agent从.yml独立文件读取
YC-05: 调度器负责传递.yml文件路径给下游Agent·不传递.md文件路径
        或传递完整输出目录·但下游Agent指令中明确"只Read .yml文件"

🆕 YC-06 (§-4性能协议·v1.1): 下游Agent的公共文件加载
  ├─ agent_quick_ref_v1.0.md (宪法/P-FAL/渲染边界/核心KB/Gate 0速查)
  ├─ CONTEXT_PACKAGE_[剧本名].md (场景/空间/角色/参考图/P-STATE活跃条目)
  ├─ KB_SUMMARY_[剧本名].md (L1_CORE+L2_SCENE规则全文)
  └─ GATE0_PRE_REPORT.md (调度器前置正则扫描结果·仅审计Agent)
  禁止加载: P-CONSTITUTION.md · P-STATE.md · canvas_runtime.md · kb_index_v2.0.md · 完整KB文件
```

## 1.3 为什么不是单一文件+块标记

```
方案A(当前): 单一文件 = 自由文本 + 【块】标记
  问题: Agent仍需Read整个文件才能"跳过"自由文本部分
  即使不处理自由文本·token已消耗在文件加载中

方案B(YAML-only): 两个文件·.md + .yml
  优势: 下游Agent只Read .yml → 自由文本完全不进入Agent上下文
  成本: 增加一个文件·调度器需同时传递两个文件
  权衡: 1个额外文件 vs 40-60% token节省 → 节省明确压倒成本

结论: 物理文件拆分是实现"不读自由文本"的唯一可靠手段。
      "在上下文中跳过"仍然消耗了文件读取token。
```

---

# §2 文件拆分规范

## 2.1 旧格式 (v1.0 · 一个文件)

```
EP14_S1_SHOT_ARCHITECT.md:
  ├── 元数据·Agent签名(5-10行)
  ├── 推理过程·场景分析(~200-400行)
  ├── 逐镜设计决策·KB引用(~300-500行)
  ├── 自检清单·合规矩阵(~100-200行)
  └── §6 YAML块(~100-200行)
  
  总: ~700-1300行
  其中YAML: ~14-25% → 86-75%是Agent间不需要的文本
```

## 2.2 新格式 (v1.1 · 两个文件)

```
EP14_S1_SHOT_ARCHITECT.md       自由文本(人类审核·Agent不读)
  ├── 元数据·Agent签名(5-10行)
  ├── 推理过程·场景分析(~200-400行)
  ├── 逐镜设计决策·KB引用(~300-500行)
  ├── 自检清单·合规矩阵(~100-200行)
  └── [底部] §6 YAML副本(仅供人类·与.yml内容一致·行首#注释)

EP14_S1_SHOT_ARCHITECT.yml      结构化数据(下游Agent消费·机器可解析)
  └── §6 YAML块(~100-200行·纯YAML·无注释·可直接解析)
```

## 2.3 .yml文件格式规范

```yaml
# ⚠️ 废弃警告: 以下示例使用旧版flat shots[]结构(shot_id: "A1")·已被v1.1 Schema废弃。
# 新版Schema见§4.1——使用segments_camera + frames_hard + frames_soft等segment+frame结构。
# 此处保留仅供历史参考·新Agent实现请参见§4.1。
#
# EP14_S1_SHOT_ARCHITECT.yml
# 格式: YAML 1.2
# 编码: UTF-8
# 生产者: Shot Architect v1.0
# 消费者: Scene Auditor · Storyboard Planner · Prompt Composer

scene:
  id: "EP14_S1"
  name: "案情室"
  total_shots: 7
  total_duration_sec: 31
  complexity_level: "C"  # C | M | S

shots:
  - shot_id: "A1"
    shot_label: "镜#A1"
    function: "建立"
    duration_sec: 5
    global_sec_range: [0, 4]
    camera:
      position: "房间中央·距白板~3m"
      position_zone: "人物可放置区域⑤"
      height_m: 1.6
      angle: "眼平·正北朝向"
      shot_type: "全景"
      focal_length_mm: 24
      depth_of_field: "深景深f/8"
      movement: "固定(S0)"
      axis: "轴上·neutral"
    kb_references:
      camera_position: ["D-TRI-03"]
      movement: ["M-MOT-01"]
    anchor_references:
      reference_image: "@图片1"
      image_grid_position: ["上排", "中排", "下排"]
    composition_hints:
      perspective: "单点透视"
      depth_layers: 3
      dominant_lines: "垂直+水平"
      color_zones:
        gray: "~90%"
        red: "~5-10%"

  - shot_id: "A2"
    # ... 逐镜重复上述结构 ...

global_anchors:
  # 如果设计Agent负责锚点定义·在此声明
  # 否则引用ANCHOR_BASELINE中的锚点ID
  character_anchor_ref: "ANCHOR_BASELINE:§A"
  environment_anchor_ref: "ANCHOR_BASELINE:§C"
  lighting_anchor_ref: "ANCHOR_BASELINE:§D"
  style_spine_ref: "PLAN:§A3"

constraints:
  global:
    - id: "GLOBAL-01"
      description: "白板文字=后期叠加"
      p_fal_ref: "P-FAL-08"
    - id: "GLOBAL-02"
      description: "面部比例全程一致·五官不漂移"
      p_fal_ref: null
  per_shot:
    A1:
      - id: "A1-C01"
        description: "白板文字仅呈现色块和线条"
      - id: "A1-C02"
        description: "Miguel在5秒内不改变站姿或位置"
    # ... 逐镜约束 ...
```

## 2.4 .md文件中的YAML副本 (仅供人类便利)

```markdown
# EP14_S1 Shot Architect — 设计报告

> **Agent:** Shot Architect v1.0
> **场景:** EP14场景A·案情室·7镜·31秒
> **输出文件:** EP14_S1_SHOT_ARCHITECT.yml (下游Agent消费文件)
> **本文件:** 自由文本推理·仅供人类审核·Agent不读取本文件

---

[... 推理过程 · 场景分析 · 设计决策 · 自检清单 ...]

---

## §6 YAML结构化数据 (副本·与.yml内容一致)

> 以下YAML内容与 EP14_S1_SHOT_ARCHITECT.yml 完全一致。
> 此处提供副本供人类在单一视图中阅读。
> 下游Agent应读取 .yml 文件而非本副本。

```yaml
# [YAML内容·与.yml完全一致]
```

---
```

---

# §3 下游Agent加载清单

## 3.1 各Agent的YAML消费模式

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       YAML-only 通信矩阵                                     │
│                                                                              │
│  生产者Agent              输出的.yml            消费者Agent    消费方式       │
│  ───────────────────────────────────────────────────────────────────────     │
│  Shot Architect           [场景]_SHOT.yml        Scene Auditor   Read YAML   │
│                                                  SBoard Planner  Read YAML   │
│                                                  Prompt Composer Read YAML   │
│                                                                              │
│  Movement Designer        [场景]_MOVEMENT.yml    Scene Auditor   Read YAML   │
│                             (如独立Agent)        SBoard Planner  Read YAML   │
│                                                  Prompt Composer Read YAML   │
│                                                                              │
│  Composition Designer     [场景]_COMPOSITION.yml Scene Auditor   Read YAML   │
│                             (如独立Agent)        SBoard Planner  Read YAML   │
│                                                  Prompt Composer Read YAML   │
│                                                                              │
│  Scene Designer (合并)    [场景]_DESIGN.yml      Scene Auditor   Read YAML   │
│                             (S/M-Level)          SBoard Planner  Read YAML   │
│                             §4+§5+§6            Prompt Composer Read YAML   │
│                             三个YAML块                                    │
│                                                                              │
│  Storyboard Planner       [场景]_PLAN.yml        Scene Auditor   Read YAML   │
│                             §A anchors          Prompt Composer Read YAML   │
│                             §B TIME_SKELETON                                │
│                                                                              │
│  Prompt Composer          [场景]_台本.yml        Scene Auditor   Read YAML   │
│                             §镜头参数卡                                  │
│                             §生成指令(结构化)                             │
│                                                                              │
│  调度器(自执行)           OBJECT_TIMELINE.yml    Obj Verifier    Read YAML   │
│                             (如生成此文件)                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 3.2 Scene Auditor 的具体加载模式

```
旧模式 (v1.0):
  Scene Auditor Read:
    ✗ EP14_S1_SHOT_ARCHITECT.md (857行·含推理+自检+设计依据)
    ✗ EP14_S1_MOVEMENT_DESIGNER.md (978行·含静态辩护段落)
    ✗ EP14_S1_COMPOSITION_DESIGNER.md (1631行·含光影推理)
    ✗ PLAN_案情室.md (1516行·含推理)
    ✗ EP14_S1_导演台本.md (984行·含设计依据)
    = 5,966行自由文本(含设计依据+推理+自检) + YAML数据

新模式 (v1.1):
  Scene Auditor Read:
    ✅ EP14_S1_SHOT_ARCHITECT.yml (~180行·纯YAML)
    ✅ EP14_S1_MOVEMENT_DESIGNER.yml (~120行·纯YAML)
    ✅ EP14_S1_COMPOSITION_DESIGNER.yml (~200行·纯YAML)
    ✅ PLAN_案情室.yml (~300行·纯YAML·§A+§B)
    ✅ EP14_S1_导演台本.md (984行·台本本体·无法YAML化)
      但其中【设计依据】块在加载后移除·只保留【生成指令】等可执行块
    = ~1,784行·其中~800行是台本本体(无法YAML化的逐秒画面描述)
      自由文本YAML部分: ~800行→~800行台本+500行YAML=~1300行(节省~78%)

  注意: 台本本体(【生成指令】逐秒描述)无法进一步YAML化——
        逐秒画面描述是自由文本的核心存在形式。
        但设计Agent的推理/自检/设计依据部分完全可YAML化。
```

## 3.3 Storyboard Planner 的具体加载模式

```
旧模式:
  SBoard Planner Read:
    ✗ 三份设计报告完整MD (3,466行)
    ✗ ANCHOR_BASELINE.md (404行)
    = 3,870行

新模式:
  SBoard Planner Read:
    ✅ EP14_S1_SHOT_ARCHITECT.yml (~180行)
    ✅ EP14_S1_MOVEMENT_DESIGNER.yml (~120行)
    ✅ EP14_S1_COMPOSITION_DESIGNER.yml (~200行)
    ✅ ANCHOR_BASELINE (仍为MD·但已经是结构化表格·~404行)
    = ~904行 (节省~77%)
```

## 3.4 Prompt Composer 的具体加载模式

```
旧模式:
  Prompt Composer Read:
    ✗ PLAN_案情室.md (1516行·含推理)
    ✗ 三份设计报告完整MD (3,466行·含推理)
    = 4,982行

新模式:
  Prompt Composer Read:
    ✅ PLAN_案情室.yml (~300行·§A+§B)
    ✅ EP14_S1_SHOT_ARCHITECT.yml (~180行)
    ✅ EP14_S1_MOVEMENT_DESIGNER.yml (~120行)
    ✅ EP14_S1_COMPOSITION_DESIGNER.yml (~200行)
    = ~800行 (节省~84%)
```

---

# §4 YAML Schema定义

## 4.1 Scene Designer合并输出YAML Schema (M/S-Level) — v1.1

> **此Schema与scene_designer_v1.0.md §7输出格式·storyboard_planner §2G消费格式完全一致——三者在TIME_SKELETON层级是同构的。**
> **v1.1变更:** 废弃flat `shots[]`数组(`shot_id: "A1"`)·改用scene_designer §7的三段式segment+frame结构(`segment_id: "①"` + `frames[]` + `segments_camera/movement`)。
> **权威源:** scene_designer_v1.0.md §7.1-§7.3 —— 本节字段名和结构与§7完全一致·不自行发明。

```yaml
# SCENE_DESIGN_YAML.yml — Scene Designer合并输出
# Schema版本: v1.1
# 对齐: scene_designer_v1.0.md §7.1-§7.3（三块YAML·一次推理产出）
# 消费: storyboard_planner (§2G TIME_SKELETON组装) · scene_auditor · prompt_composer

scene:
  id: string              # "EP14_S1"
  name: string            # "案情室"
  type: string            # "室内·制度空间" — 场景类型路由键
  total_duration_sec: integer  # 31
  complexity_level: string     # "C" | "M" | "S"

# ═══════════════════════════════════════
# §4 机位域YAML（scene_designer §7.1）
# 映射目标: TIME_SKELETON.segments[].camera + frames[].hard
# ═══════════════════════════════════════

segments_camera:
  - segment_id: "①"              # 摄影机位置编号（①②③④·非shot_id）
    time_range: [integer, integer]  # [起始秒, 结束秒] 闭区间
    shot_type: string             # 全景/中全景/中景/中近景/近景/特写/大特写
    focal_length: string          # "24mm" 35mm等效焦距
    dof: string                   # "深景深f/8" / "浅景深f/2.8" / "中等景深f/4"
    angle: string                 # "眼平" / "俯拍" / "仰拍" / "低角度"
    kb_rule_ids:                  # 设计依据（不进入渲染·供审计）
      - string

frames_hard:                      # 逐秒硬约束·景别+焦距
  - sec: integer                  # 镜头内秒序（从0开始）
    global_sec: integer           # 场景内绝对秒
    camera_position: string       # 引用segment_id（"①"/"②"）或过渡（"①→②"）
    shot_type: string
    focal_length: string

# ═══════════════════════════════════════
# §5 运镜域YAML（scene_designer §7.2）
# 映射目标: TIME_SKELETON segments[].camera.movement + transition + frames[].hard.camera_movement
# ═══════════════════════════════════════

segments_movement:
  - segment_id: "①"              # 引用§4 segments_camera的segment_id
    movement: string              # "固定" / "固定→极慢前推(0.02x)" / ...
    movement_speed_tier: string   # "S0"（静止）~ "S8"（极快）
    kb_rule_ids:
      - string

frames_movement:                   # 逐秒运镜状态
  - sec: integer
    global_sec: integer
    camera_position: string       # 引用segment_id或过渡标记"①→②"
    movement: string              # "固定" / "极慢前推中" / "固定(落定)" / ...
    is_transition_frame: boolean  # 可选·标记该秒是否为段间过渡帧

segments_transitions:              # 段间运镜过渡（非硬切时存在）
  - transition_id: string         # "①→②"
    from_segment: string          # "①"
    to_segment: string            # "②"
    transition_type: string       # "切"（硬切）/ "极慢前推" / "慢摇" / ...
    time_range: [integer, integer]  # 过渡跨越的秒范围
    path: string                  # "直线·沿房间中轴线" — 摄影机运动路径
    speed: string                 # "匀速·1s"
    visual_change: string         # 过渡过程的视觉变化描述
    kb_rule_ids:
      - string

# ═══════════════════════════════════════
# §6 构图光影域YAML（scene_designer §7.3）
# 映射目标: TIME_SKELETON.global_anchors + frames[].soft
# ═══════════════════════════════════════

global_anchors:
  character:                      # A1: Character Anchor Block
    # key=角色名·value=完整外观描述（逐字锁定·全场景复用）
    <角色名>: string              # "Latin male, mid-30s, short dark brown hair..."

  environment:                    # A2: Environment Anchor Block
    description: string           # 五要素: 地点+时间+天气+光源方向+关键背景元素

  style_spine:                    # A3: Style Spine（15-25字风格锚短语）
    description: string           # "shot on Arri Alexa 35, Kodak Vision3 500T..."
    palette_anchors:              # 3-5个颜色锚点词
      - string

  lighting:                       # A4: Lighting Anchor
    description: string           # 光源完整描述·含色温·质量·方向
    anchor_in_reference: string   # "参考图格5·天花板正中吊灯" — 物理锚点可追溯

  constraints:                    # A5: Constraint Block（3-5条正向约束）
    - string                      # "面部比例全程一致·五官不漂移"

frames_soft:                      # 逐秒软锚点·prompt_composer在此基础上展开
  - sec: integer                  # 镜头内秒序（从0开始）
    global_sec: integer           # 场景内绝对秒
    camera_position: string       # 引用segment_id
    action_anchor: string         # 该秒的核心动作/画面描述（不含运镜语义·宪法第四条）
    spatial_anchor: string        # 该秒的空间锚点描述（光区·深度·背景）
    prop_state:                   # 物体状态（与OBJECT_TIMELINE对齐）
      - item: string              # "台灯"
        state: string             # "亮·2800K暖黄"
    character_state:              # 角色状态
      - character: string         # "Rico"
        pose: string              # "背对镜头坐"
        position: string          # "工作台后·画面中央"
        expression: string | null # null=该秒面部不可见
    audio:                        # 音频锚点（画外音·不混入action_anchor·宪法第一条）
      ambience: string            # "室内低频持续"
      events: list[string]        # 离散音效事件

# ═══════════════════════════════════════
# 废弃字段（旧版v1.0·与scene_designer §7不兼容）
# ═══════════════════════════════════════
# shots[] (flat数组·shot_id: "A1")          → 已替换为 segments_camera + frames 结构
# shots[].camera.position / position_zone   → 已整合入 global_anchors.environment + frames_soft.spatial_anchor
# shots[].camera.height_m / axis            → 待scene_designer §7补充（如需逐segment标注）
# shots[].kb_references                     → 已替换为 segments_*.kb_rule_ids
# shots[].anchor_references                 → 已替换为 global_anchors.lighting.anchor_in_reference
# shots[].composition_hints                 → 已整合入 frames_soft（spatial_anchor中描述）
# shots[].duration_breakdown                → 已替换为 frames_hard/frames_soft 逐秒结构
# shots[].constraints                       → 已替换为 global_anchors.constraints
# cross_shot_continuity.transitions         → 已替换为 segments_transitions
# cross_shot_continuity.axis_continuity     → 待scene_designer §7补充
# cross_shot_continuity.prop_chain          → 待scene_designer §7补充
# global_anchors.character[].state_changes  → 已替换为 frames_soft.character_state（逐秒）
# global_anchors.lighting.sources[]         → 待scene_designer §7补充（结构化光源列表）
# scene.total_shots                         → 废弃（segment ≠ shot·不再有flat shot计数）
```

## 4.2 PLAN YAML Schema

```yaml
# PLAN_SCENE.yml — Storyboard Planner输出
# Schema版本: v1.0

plan:
  scene_id: string
  scene_name: string
  created_by: string    # "Storyboard Planner v1.0"

global_anchors:  # §A
  character: string     # 完整C1文本(逐字锁定)
  environment: string   # 完整C2文本(逐字锁定)
  lighting: string      # 完整C3文本(逐字锁定)
  style_spine: string   # 完整C4文本(逐字锁定)
  constraints:
    - text: string
      category: string  # "平台约束" | "P-FAL规避" | "跨镜一致性"

time_skeleton:  # §B
  total_duration_sec: integer
  frames:
    - global_sec: integer
      hard:
        shot_type: string
        camera_movement: string
        focal_length: string
      soft:
        action_anchor: string
        spatial_anchor: string
        character_state: string
        prop_state: object  # {prop_id: state, ...}
  segments:
    - segment_id: string     # "①" | "①→②"
      shot_label: string
      time_range: [integer, integer]
      transition:
        type: string         # "硬切" | "淡入" | ...
        at_global_sec: integer
```

---

# §5 预期节省

## 5.1 单Auditor节省(Scene Auditor为例·EP14场景A·C-Level)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    EP14场景A · Scene Auditor token节省               │
│                                                                      │
│  输入文件          旧模式(token)  新模式(token)  节省                │
│  ──────────────────────────────────────────────────────────────     │
│  Shot Architect      ~20K (857行)  ~4K (180行YAML)  -80%            │
│  Movement Designer   ~22K (978行)  ~3K (120行YAML)  -86%            │
│  Composition Des.    ~35K (1631行) ~5K (200行YAML)  -86%            │
│  PLAN                 ~35K (1516行) ~8K (300行YAML)  -77%            │
│  导演台本              ~30K (984行)  ~25K (去设计依据块)  -17%       │
│  ──────────────────────────────────────────────────────────────     │
│  设计报告合计          ~112K         ~20K              -82%          │
│  台本本体              ~30K          ~25K              -17%          │
│  总计                  ~142K         ~45K              -68%          │
│                                                                      │
│  其中台本本体(984行)无法YAML化——逐秒画面描述是自由文本的              │
│  核心存在形式。节省仅限于"去设计依据块"和"去元数据头"。              │
│  设计报告YAML化是主要节省来源(112K→20K)。                           │
└─────────────────────────────────────────────────────────────────────┘
```

## 5.2 全管道累计节省(EP14场景A·C-Level·3设计Agent)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    YAML-only协议 · 全管道节省                         │
│                                                                      │
│  Scene Auditor:         ~142K → ~45K  (节省 ~97K · -68%)            │
│  Storyboard Planner:    ~95K  → ~25K  (节省 ~70K · -74%)            │
│  Prompt Composer:       ~120K → ~45K  (节省 ~75K · -63%)            │
│  SDA (如独立):          ~144K → ~25K  (节省 ~119K · -83%)           │
│  SSA (如独立):          ~177K → ~80K  (节省 ~97K · -55%)            │
│  ──────────────────────────────────────────────────────────────     │
│  累计Agent间传输:       ~678K → ~220K (节省 ~458K · -68%)           │
│                                                                      │
│  注: 以上为"Agent间通信"token节省·不含Agent自身推理消耗。            │
│      每个Agent仍需执行自己的LLM推理·但输入token大幅减少。            │
│                                                                      │
│  实际LLM调用token节省(含推理):                                       │
│    输入节省: ~458K tokens                                            │
│    推理不变: 各Agent仍需执行相同深度的推理                            │
│    净节省: ~458K tokens/场景 (输入侧·全管道)                         │
└─────────────────────────────────────────────────────────────────────┘
```

## 5.3 S-Level场景节省(2 Agent·Scene Designer + Scene Auditor)

```
S-Level (MVP管道·EP14场景复杂度):
  Scene Auditor:
    旧: ~45K 输入 (Scene Designer完整MD + 台本)
    新: ~12K 输入 (Scene Designer YAML + 台本去设计依据)
    节省: -73%

  全管道(S-Level·2 Agent):
    旧: ~60-80K tokens (MVP基线)
    新: ~35-45K tokens (YAML-only后)
    进一步节省: ~40%
    累计MVP+YAML-only: 875K → 60K → 35K = 节省96% vs 旧C-Level管道
```

---

# §6 实施步骤

## 6.1 实施优先级

```
Phase 1 (本周·指令修改·零代码):
  □ 1. scene_designer_v1.0.md: 新增输出格式——产出两个文件(.md + .yml)
  □ 2. scene_auditor_v1.0.md: 更新输入清单——.yml替代.md(设计报告部分)
  □ 3. storyboard_planner_v1.0.md: 更新输入清单——.yml替代.md
  □ 4. prompt_composer_v2.0.md: 更新输入清单——.yml替代.md(设计报告部分)

Phase 2 (本周·调度器修改):
  □ 5. dispatcher_v5.0.md: 更新Agent调用参数·传递.yml路径
  □ 6. 独立旧版Agent(Shot/Movement/Composition): 更新输出格式
  □ 7. Scene Designer合并版: 确保§4+§5+§6三个YAML块完整

Phase 3 (优化·后续):
  □ 8. 台本部分YAML化: 提取镜头参数卡为独立.yml
  □ 9. OBJECT_TIMELINE YAML化: 改为结构化.yml·便于Obj Verifier消费
  □ 10. 建立.yml schema版本管理·防止跨版本不兼容
```

## 6.2 向后兼容策略

```
兼容旧Agent(尚未YAML化):
  调度器检测逻辑:
    IF [场景]_SHOT.yml 存在 THEN
      传递 .yml 路径给下游Agent
    ELSE
      回退: 传递 .md 路径给下游Agent
      并在日志中标记 "⚠️ YAML-only回退·旧Agent仍在产生MD-only输出"

  过渡期: 新旧格式共存·调度器自适应
  目标: 3个场景(EP14-16)运行后·全部Agent迁移到YAML+MD双输出格式
```

## 6.3 人类审核不中断保证

```
关键保证: YAML+MD双输出 = 人类审核体验不降级

  .md文件中包含YAML副本——人类在单一视图中看到:
    推理过程(自由文本) → YAML数据(副本) → 自检清单(自由文本)
    不需要打开两个文件

  .yml文件独立存在——供机器解析:
    调度器传递.yml路径给下游Agent
    Agent直接Read .yml

  两个文件内容(就YAML部分而言)完全一致·通过文件头注释声明版本同步
```

---

# §7 边界情况与例外

## 7.1 台本本体的YAML化限制

```
问题: 导演台本的【生成指令】包含逐秒画面描述("t=0s: Miguel背对镜头站立..." )
      这是自由文本的核心形式·无法完全结构化。
      
处理: 台本保持.md格式·但做以下优化:
  1. 【设计依据】块从台本中移除·移至独立的_DESIGN_NOTES.md
  2. 【镜头参数卡】可提取为独立.yml(可选·Phase 3)
  3. 【生成指令】逐秒描述保留在.md中·这是Seko的直接输入
  4. 【音轨】保留在.md中
  5. 【禁止】保留在.md中
  
审计Agent读取台本.md时:
  → 不读取已移除的【设计依据】块(它不在台本.md中了)
  → 台本.md从984行缩减至~700行
```

## 7.2 多文件同步一致性

```
问题: .md中的YAML副本与.yml可能出现版本不同步。
      
保证机制:
  1. .md和.yml文件头均包含版本时间和MD5哈希
  2. 调度器验证: .md中声明的.yml哈希 == 实际.yml文件哈希
     不一致 → 调度器报错·重新生成
  3. Agent指令: "只读取.yml文件·忽略.md中的YAML副本"
     避免Agent两端读取导致混淆
  4. 格式: 
     .md文件头: "> **YAML同步:** EP14_S1_SHOT.yml · MD5=abc123"
     .yml文件头: "# SYNC: EP14_S1_SHOT_ARCHITECT.md · MD5=cba321"
```

## 7.3 纯骨架场景(无设计Agent)

```
场景: S-Level·跳过设计Agent·Scene Designer直接输出台本

处理: 无设计报告·无.yml文件·Scene Auditor加载:
  → PLAN.yml (如PLAN存在)
  → 台本.md (去除设计依据后)
  → Phase 1(设计域)跳过·因"无设计报告"
  
  此时YAML-only协议无适用设计Agent·但PLAN的YAML化仍然生效。
```

## 7.4 复杂C-Level场景(三Agent全量)

```
场景: 三Agent(Shot/Movement/Composition)全部存在的复杂场景

处理: 三个独立.yml文件 + 1个PLAN.yml + 1个台本.md
  Scene Auditor加载:
    ✅ SHOT.yml + MOVEMENT.yml + COMPOSITION.yml
    ✅ PLAN.yml
    ✅ 台本.md(去设计依据)
    = 5个文件·全部为结构化+必要自由文本
  
  三Agent间YAML字段级一致性由Scene Auditor Phase 1·C-Level检查验证。
  YAML格式使字段比对更加精确(不再是"逐行匹配自由文本"而是"逐字段值比对")
```

---

> **YAML-only Agent间通信协议 v1.0 · 2026-07-07**
> **核心原则:** 设计Agent产出.md(人类)+.yml(机器)双文件·审计Agent只读.yml
> **预期效果:** Agent间通信token节省68%·Scene Auditor输入节省82%(设计报告部分)
> **宪法依据:** 画布第七条(独立验证>自审)·独立验证=推理隔离·非文件加载隔离
> **实施:** Phase 1(指令修改·本周)→Phase 2(调度器集成·本周)→Phase 3(YAML化深化·后续)
> **不退化保证:** .md中包含YAML副本·人类审核体验不降级
