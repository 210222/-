# PLAN_案情室.md — 场景级Prompt骨架 + TIME_SKELETON

> **生产者:** Storyboard Planner v2.0 · MODE:P Step A2.5
> **场景:** 圣保罗刑警总部·案情室（日）·7镜·31秒
> **角色:** Miguel（刑警·主角）+ Vincent（鉴证科·仅门口出现）
> **合并来源:** Shot Architect §4-§5 YAML + Movement Designer §3-§4 YAML + Composition Designer §5-§6 YAML + ANCHOR_BASELINE
> **合并策略:** 机械合并·三Agent YAML逐行对照·冲突处标记[冲突]·不添加三Agent YAML中没有的数据
> **下游消费者:** prompt_composer（消费§A+§B展开为视频提示词）· storyboard_previewer（消费§B派生逐格线稿）· 审查专家（消费§B逐秒diff验证）

---

## §A: Prompt骨架 (场景内全7镜逐字复制·不可修改)

### A1: Character Anchor Block

```
Miguel: "Latin male, 30-40s, short black curly hair with greying temples,
         wide cheekbones, square jaw, vertical crease between brows,
         deep brown eyes with detective scrutiny, solid build,
         浅灰衬衫(纽扣领) + 深藏青警探夹克(哑光面料·拉链立领·前半段未穿搭椅背·后半段穿上)"

Vincent: "Male, 30-40s, dark brown short hair slightly disheveled, thin build,
          cold white skin tone from indoor lab work, 白色实验室外套(长款·及膝) + 内搭深色衬衫,
          黑框眼镜(黑色板材·矩形框·核心视觉识别物)"

⚠️ 此Character Anchor Block在本场景全部7镜中逐字复制·不可改一字。
如需变更角色状态(穿夹克·肤色变化)→必须有显式事件锚点(M3·M4)+已由Composition Designer逐帧记录。
```

**来源:** ANCHOR_BASELINE §A + Composition Designer global_anchors.character

---

### A2: Environment Anchor Block

```
"圣保罗刑警总部案情室·日间·全封闭室内(~6m深×~4m宽×~3m高)·无窗·纯人工照明·
 素灰色墙面·地面平整·强烈单点透视。
 北墙: 巨大白色白板(~3-4m宽·占满墙面·视觉重心)·人物照片+红线网络+建筑平面图(201红圈)+弹道分析报告。
 南侧: 合并办公桌×2·距白板~1-2m·堆满文件/笔记本/咖啡杯/签字笔/笔记本电脑。
 西墙: 灰色金属门(宽~1m·高~2.1m·不锈钢把手)·外连走廊(3500K暖黄光·推断·已标注物理属性)。
 东墙: 素灰墙面·无窗。
 天花板: 四个方形格栅发光顶灯(5000K冷白·均匀·无影灯设计)。"
```

**来源:** ANCHOR_BASELINE §C 场景A + Composition Designer global_anchors.environment

---

### A3: Style Spine

```
"shot on Arri Alexa 35, cold-white institutional 5000K, neutral-gray palette,
 blood-red accent as vascular metaphor, frame-within-frame composition motif,
 single-point perspective linear order, static-dominant camera language"
```

**Palette Anchors:** cold-white-5000K · neutral-gray · pure-white-whiteboard · blood-red-accent · warm-yellow-3500K-corridor · dark-navy-jacket · gold-badge-gleam

**来源:** Composition Designer global_anchors.style_spine + palette_anchors

---

### A4: Lighting Anchor

```
主光源: 天花板方形格栅发光顶灯×4, 5000K冷白, 柔光·大面积均匀扩散·无影灯设计,
        全室(~6m×4m)覆盖, 低光比约1:1至1:2, 锚定于参考图上排

第二光源a: 笔记本电脑屏幕, ~6500K冷蓝微光, 弱光·柔和扩散·桌面局部半径~0.3m,
            锚定于参考图下排

第二光源b: 门外走廊暖黄光(推断·已标注物理属性), 3500K暖黄, 软光·从门外走廊漫射·
           经门框切割为矩形光柱, 仅在镜#A4/#A7出现, 叙事功能: 打破冷白制度的均匀性·
           走廊=制度外空间
```

**来源:** Composition Designer global_anchors.lighting

---

### A5: Constraint Block

```
1. 所有光源描述基于物理锚点(格栅灯·笔记本屏幕·走廊暖黄光)·无凭空编造光源
2. 所有人物位置锚定空间地图人物可放置区域①-⑤·不悬空·不穿墙
3. 白板文字/名字/日期/弹道报告=后期叠加·不在Seko prompt中要求渲染文字(P-FAL-08规避)
4. 画面描述不含运镜语义(参照画布宪法第四条)
5. Miguel肤色作为'色温计'——冷白下偏灰偏蜡(分析者)→暖黄下回暖(行动者)
6. 跨镜色温一致: 同光源条件下色温锁定·无无理由的色温变化
7. 面部比例全程一致·五官不漂移
8. 光线色温全程锁定·无闪烁
9. 画面稳定无晃动·动作流畅自然
10. 无字幕·无Logo·无水印
```

**来源:** Composition Designer global_anchors.constraints + storyboard_planner §2E

---

## §B: TIME_SKELETON (统一时间轴·单帧=1秒)

```yaml
# TIME_SKELETON — 案情室 · 31秒 · 7镜
# 合并源: Shot Architect frames_hard + Movement Designer frames_movement
#          + Composition Designer frames_soft + global_anchors
# 冲突裁决: Shot Architect(机位) > Movement(运镜) > Composition(构图)
# 硬约束(hard): 运镜状态·景别·焦距 → 不可被消费者覆盖
# 软锚点(soft): action_anchor·composition·lighting·character_state → 消费者在锚点基础上展开

time_skeleton:
  scene: "圣保罗刑警总部·案情室"
  scene_time_of_day: "日间"
  total_duration_sec: 31

  global_anchors:
    character:
      Miguel:
        description: "Latin male, 30-40s, short black curly hair with greying temples, wide cheekbones, square jaw, vertical crease between brows, deep brown eyes with detective scrutiny, solid build"
        skin_tone_5000K: "棕褐色偏灰偏蜡 — 冷白制度光下的'分析者'状态"
        skin_tone_3500K: "棕褐色回暖·皮下散射深橙金 — 暖黄走廊光下的'行动者'状态"
        costume: "浅灰衬衫(纽扣领) + 深藏青警探夹克(哑光面料·拉链立领·前半段未穿搭椅背·后半段穿上)"
        key_identifiers: ["A19-金色警徽(左胸前·盾形·金属反光)", "A29-深色金属腕表(黑色表盘·秒针在走)", "A49-右手无名指旧伤疤(握物时形成枪柄弧度)"]
      Vincent:
        description: "Male, 30-40s, dark brown short hair slightly disheveled, thin build, cold white skin tone from indoor lab work"
        costume: "白色实验室外套(长款·及膝) + 内搭深色衬衫"
        key_identifiers: ["V1-黑框眼镜(黑色板材·矩形框)", "V2-深棕色眼睛(走廊暖黄光下镜片反射减少·眼睛可见)"]
        presence: "仅在门口探头说两句对白·不入室·不参与主线动作"
    environment:
      description: "圣保罗刑警总部案情室·日间·全封闭室内(~6m深×~4m宽×~3m高)·无窗·纯人工照明·素灰色墙面·强烈单点透视"
      key_elements:
        - "北墙: 巨大白色白板(~3-4m宽·占满墙面)·人物照片+红线网络+建筑平面图(201红圈)+弹道分析报告"
        - "南侧: 合并办公桌×2·距白板~1-2m·堆满文件/笔记本/咖啡杯/签字笔/笔记本电脑"
        - "西墙: 灰色金属门(宽~1m·高~2.1m)·外连走廊(3500K暖黄光·推断·已标注物理属性)"
        - "东墙: 素灰墙面·无窗"
        - "天花板: 四个方形格栅发光顶灯(5000K冷白·均匀·无影灯设计)"
    style_spine:
      description: "冷白制度凝视·灰色理性基调·红色冲撞血管隐喻·框中框构图·单点透视线性秩序·静态主导运镜"
      palette_anchors: ["cold-white-5000K", "neutral-gray", "pure-white-whiteboard", "blood-red-accent", "warm-yellow-3500K-corridor", "dark-navy-jacket", "gold-badge-gleam"]
    lighting:
      primary:
        source: "天花板方形格栅发光顶灯×4"
        color_temp: "5000K·冷白"
        quality: "柔光·大面积均匀扩散·无影灯设计"
        coverage: "全室(~6m×4m)·从天花板向下全覆盖"
        light_ratio: "低光比·约1:1至1:2"
      secondary:
        - source: "笔记本电脑屏幕"
          color_temp: "~6500K·冷蓝微光"
          quality: "弱光·柔和扩散·桌面局部半径~0.3m"
        - source: "门外走廊暖黄光(推断·已标注物理属性)"
          color_temp: "3500K·暖黄"
          quality: "软光·从门外走廊漫射·经门框切割为矩形光柱"
          narrative_function: "仅在镜#A4/#A7出现·打破冷白制度的均匀性"
    constraints:
      - "所有光源描述基于物理锚点·无凭空编造光源"
      - "所有人物位置锚定空间地图人物可放置区域①-⑤"
      - "白板文字=后期叠加·P-FAL-08规避"
      - "画面描述不含运镜语义·参照画布宪法第四条"
      - "Miguel肤色作为'色温计'——冷白下偏灰偏蜡→暖黄下回暖"
      - "面部比例全程一致·五官不漂移"
      - "光线色温全程锁定·无闪烁"
      - "画面稳定无晃动·动作流畅自然"
      - "无字幕·无Logo·无水印"

  segments:
    - segment_id: "A1"
      time_range: [0, 4]
      duration_sec: 5
      shot_type: "全景"
      focal_length: "24mm"
      dof: "深景深f/8"
      angle: "眼平·约1.6m高·正北朝向"
      camera_position: "房间中央·距白板~3m·人物可放置区域⑤"
      axis_side: "轴上·neutral"
      coverage_function: "建立·确立案情室完整空间和白板视觉重心"
      movement: "固定"
      movement_speed_tier: "S0"
      dof_vector: [0, 0, 0, 0, 0, 0, 0]
      static_exception: "信息密集——全室建立·24mm广角·深景深f/8·画面信息量大"
      kb_rule_ids:
        shot: ["D-TRI-03", "shared_agent_runtime.md §4·8机位模板-1·双人全景建立"]
        movement: ["M-MOT-01"]

    - segment_id: "A2"
      time_range: [5, 8]
      duration_sec: 4
      shot_type: "大特写"
      focal_length: "85mm"
      dof: "浅景深f/2.8"
      angle: "眼平·约1.5m高·正北朝向·与照片钉挂位置平齐"
      camera_position: "白板前偏左·距白板~0.4m→~0.2m·人物可放置区域①"
      axis_side: "轴上·neutral·插入镜头·天然中性过渡"
      coverage_function: "揭示·情绪锚点·Rico照片+红线缠颈"
      movement: "极慢前推(0.05x)"
      movement_speed_tier: "S1"
      movement_direction: "正北·推近·沿光轴·垂直于白板表面"
      movement_path: "直线·起点距白板0.4m·终点距白板0.2m·行程~20cm·匀速"
      push_distance_cm: 20
      push_duration_s: 4
      dof_vector: [0, 0, 0, 0, 0, 0.05, 0]
      kb_rule_ids:
        shot: ["D-TRI-05", "shared_agent_runtime.md §4·8机位模板-6·插入"]
        movement: ["M-MOT-02", "M-MOV-04"]

    - segment_id: "A3"
      time_range: [9, 13]
      duration_sec: 5
      shot_type: "中景"
      focal_length: "50mm"
      dof: "中等景深f/4"
      angle: "眼平·约1.6m高·东偏南朝向·面向Miguel"
      camera_position: "白板与桌之间西侧(A侧)·距白板~1.8m·人物可放置区域①"
      axis_side: "A侧·西侧·180度线同侧"
      coverage_function: "推进·Miguel从动作切换到审视状态·面部表情叙事"
      movement: "固定"
      movement_speed_tier: "S0"
      dof_vector: [0, 0, 0, 0, 0, 0, 0]
      static_exception: "信息密集——双重信息层(面部表情+背景红线网络)·5秒"
      kb_rule_ids:
        shot: ["D-TRI-02", "shared_agent_runtime.md §4·8机位模板-2·单人A"]
        movement: ["M-MOT-01"]

    - segment_id: "A4"
      time_range: [14, 17]
      duration_sec: 4
      shot_type: "中景"
      focal_length: "35mm"
      dof: "中等景深f/5.6"
      angle: "眼平·约1.6m高·正西朝向·面向门框"
      camera_position: "室内门框内侧偏南·距门~1.5m·人物可放置区域④"
      axis_side: "A侧·西侧·180度线同侧"
      coverage_function: "引入·Vincent门口探头·冷暖光交界建立角色功能"
      movement: "固定"
      movement_speed_tier: "S0"
      dof_vector: [0, 0, 0, 0, 0, 0, 0]
      static_exception: "空间受限——门框窄区·宽度不足2m·禁横移和大幅度摇镜"
      kb_rule_ids:
        shot: ["D-TRI-02", "shared_agent_runtime.md §4·8机位模板-3·单人B", "kb_index §1.1·门口相持调度变体"]
        movement: ["M-MOT-01"]

    - segment_id: "A5"
      time_range: [18, 22]
      duration_sec: 5
      shot_type: "近景"
      focal_length: "85mm"
      dof: "浅景深f/2.8"
      angle: "眼平·约1.65m高·微高于Miguel眼平·东偏北朝向·面向Miguel面部"
      camera_position: "白板与桌交界西侧(A侧)·距Miguel面部~1.5m·人物可放置区域①/②交界"
      axis_side: "A侧·西侧·180度线同侧"
      coverage_function: "反应·Miguel回应Vincent·揭示对Rico的了解"
      movement: "固定"
      movement_speed_tier: "S0"
      dof_vector: [0, 0, 0, 0, 0, 0, 0]
      static_exception: "信息密集——85mm CU·面部微表情+背景红线'光环'·5秒对白承载"
      kb_rule_ids:
        shot: ["D-TRI-02", "E-MTC-04", "shared_agent_runtime.md §4·8机位模板-7·反应"]
        movement: ["M-MOT-01"]

    - segment_id: "A6"
      time_range: [23, 25]
      duration_sec: 3
      shot_type: "中景"
      focal_length: "50mm"
      dof: "中等景深f/4"
      angle: "微俯·约1.3m高·略低于眼平·强调手部动作·东偏北朝向"
      camera_position: "办公桌西侧(A侧)·距桌~0.5m·人物可放置区域②"
      axis_side: "A侧·西侧·180度线同侧"
      coverage_function: "过渡·物理动作(拿外套+车钥匙)·分析者→行动者切换"
      movement: "固定"
      movement_speed_tier: "S0"
      dof_vector: [0, 0, 0, 0, 0, 0, 0]
      static_exception: "空间受限——桌面窄区·低机位1.3m·距桌0.5m·可推近空间<0.3m"
      kb_rule_ids:
        shot: ["D-TRI-02", "shared_agent_runtime.md §4·8机位模板-6·插入·过渡性"]
        movement: ["M-MOT-01"]

    - segment_id: "A7"
      time_range: [26, 30]
      duration_sec: 5
      shot_type: "中全景"
      focal_length: "35mm"
      dof: "深景深f/8"
      angle: "眼平·约1.6m高·正东朝向·从走廊穿过门框看向室内"
      camera_position: "门框外侧·走廊内·距门~0.8m·人物可放置区域④走廊侧·推断空间(已标注物理属性)"
      axis_side: "A侧·西侧·A侧自然延伸至走廊·空间连续·不越轴"
      coverage_function: "再交代+过渡·门框构图·场景封闭·冷暖交界+脸部遮挡=潜台词共振"
      movement: "固定"
      movement_speed_tier: "S0"
      dof_vector: [0, 0, 0, 0, 0, 0, 0]
      static_exception: "空间受限+信息密集——走廊窄区+框中框构图+冷暖交界+脸部遮挡+对白"
      kb_rule_ids:
        shot: ["D-TRI-02", "shared_agent_runtime.md §4·8机位模板-8·再交代", "kb_index §1.1·门口相持调度变体"]
        movement: ["M-MOT-01"]

  # 段间过渡: 全部硬切(6次)·无连续运镜过渡
  transitions:
    - transition_id: "A1→A2"
      type: "硬切"
      at_global_sec: 5
      visual_change: "从全室全景→Rico照片ECU·空间跳跃~2.6m·建立→情绪锚点"
    - transition_id: "A2→A3"
      type: "硬切"
      at_global_sec: 9
      visual_change: "从Rico照片ECU→Miguel MS·轴上→A侧西侧·从物件到人物"
    - transition_id: "A3→A4"
      type: "硬切"
      at_global_sec: 14
      visual_change: "从白板侧Miguel审视→门口Vincent探头·空间跳跃~3m·切换拍摄对象"
    - transition_id: "A4→A5"
      type: "硬切"
      at_global_sec: 18
      visual_change: "从Vincent门区→Miguel白板区·正反打·Vincent看右↔Miguel看左对视匹配"
    - transition_id: "A5→A6"
      type: "硬切"
      at_global_sec: 23
      visual_change: "从Miguel面部CU→手部动作MS·从'回应'到'行动'的节奏推进"
    - transition_id: "A6→A7"
      type: "硬切"
      at_global_sec: 26
      visual_change: "从室内桌侧→门外走廊·空间出口·制度内→外部世界·场景封闭"

  # ===== 逐秒冻结帧 (31秒=31帧) =====
  frames:

    # --- A1: 全景建立 (global_sec 0-4, 5秒) ---
    - global_sec: 0
      seg_ref: "A1"
      camera_position: "房间中央·距白板~3m·人物可放置区域⑤"
      is_transition_frame: false
      frame_label: "格1"
      hard:
        shot_type: "全景"
        focal_length: "24mm"
        camera_movement: "固定"
      soft:
        action_anchor: "Miguel背对镜头站在白板前·深藏青夹克搭在椅背上未穿·站姿距白板~0.5m·面向白板线索墙"
        spatial_anchor: "前景合并办公桌(文件堆叠·笔记本·咖啡杯·笔记本电脑屏幕亮着)→中景Miguel背影→后景巨大白色白板(人物照片·红线网络·建筑平面图201红圈·弹道分析报告·占画面后景水平中心)"
        composition:
          subject_position: "白板占据画面后景水平中心·前景桌面·中景Miguel背身"
          depth_layers: "3层: 前景(桌面·30%) + 中景(Miguel背影·25%) + 背景(白板·45%)"
          dominant_lines: "单点透视: 天花板灯带竖线+桌边横线+墙角线→汇聚至白板中央"
          negative_space: "天花板上方·格栅灯几何排列"
          composition_style: "封闭构图·深空间·制度秩序的几何化"
          kb_rule_ids: ["C-AJS-01", "C-DEP-01", "C-FI-03", "VS-LS-01", "VS-LS-02", "C-KTZ-01"]
        lighting:
          primary_source: "天花板格栅灯·5000K冷白·顶光均匀·全室覆盖·低光比1:1.5"
          secondary_source: "笔记本电脑屏幕~6500K冷蓝微光·桌面局部"
          shadow_quality: "极浅·几乎无可见阴影·无影灯设计"
          visual_focus: "白板(最亮·柔和反光)→视线路径: 前景桌面→Miguel背影→白板"
        color:
          base_palette: "冷酷基色(灰/白/黑白)~90% + 冲撞红(红线/红图钉/红圈)~5-10%"
          skin_tone_miguel: "无法观察(背身)"
          red_function: "白板上红线/红图钉/红圈=色彩冲撞·视觉锚点·'血管'引导线"
        character_state:
          - character: "Miguel"
            pose: "背对镜头·站姿·面向白板·距板~0.5m"
            position: "人物可放置区域①·白板前"
            expression: "面部不可见·背身"
            costume: "浅灰衬衫·深藏青夹克搭在椅背上(未穿)"
        on_screen: ["合并办公桌×2", "文件堆叠", "横线笔记本", "黑色签字笔", "黑色咖啡杯", "笔记本电脑(屏幕亮·弹壳对比图)", "Miguel(背身·浅灰衬衫)", "椅背(深藏青夹克搭着)", "巨大白色白板", "人物照片", "红线网络", "建筑平面图(201红圈)", "弹道分析报告", "天花板四个方形格栅发光顶灯"]
      audio:
        ambience: "低音量空调运行声·办公室底噪·远处打印机/复印机"
        events: []

    - global_sec: 1
      seg_ref: "A1"
      camera_position: "房间中央·距白板~3m·人物可放置区域⑤"
      is_transition_frame: false
      frame_label: "格2"
      hard:
        shot_type: "全景"
        focal_length: "24mm"
        camera_movement: "固定"
      soft:
        action_anchor: "画面同格1·Miguel背身站位稳定·观察白板线索墙"
        spatial_anchor: "同格1·全室透视不变·观众吸收空间信息"
        character_state:
          - character: "Miguel"
            pose: "同格1·背对镜头·站姿"
        on_screen: ["同格1"]
      audio:
        ambience: "低音量空调运行声·办公室底噪"

    - global_sec: 2
      seg_ref: "A1"
      camera_position: "房间中央·距白板~3m·人物可放置区域⑤"
      is_transition_frame: false
      frame_label: "格3"
      hard:
        shot_type: "全景"
        focal_length: "24mm"
        camera_movement: "固定"
      soft:
        action_anchor: "画面同格1·建立镜头持续·观众建立对案情室空间的完整认知"
        spatial_anchor: "同格1"
        character_state:
          - character: "Miguel"
            pose: "同格1"
        on_screen: ["同格1"]
      audio:
        ambience: "低音量空调运行声·办公室底噪"

    - global_sec: 3
      seg_ref: "A1"
      camera_position: "房间中央·距白板~3m·人物可放置区域⑤"
      is_transition_frame: false
      frame_label: "格4"
      hard:
        shot_type: "全景"
        focal_length: "24mm"
        camera_movement: "固定"
      soft:
        action_anchor: "画面同格1·建立镜头的最后时刻·观众已完成空间认知"
        spatial_anchor: "同格1"
        character_state:
          - character: "Miguel"
            pose: "同格1"
        on_screen: ["同格1"]
      audio:
        ambience: "低音量空调运行声·办公室底噪"

    - global_sec: 4
      seg_ref: "A1"
      camera_position: "房间中央·距白板~3m·人物可放置区域⑤"
      is_transition_frame: false
      frame_label: "格5"
      hard:
        shot_type: "全景"
        focal_length: "24mm"
        camera_movement: "固定"
      soft:
        action_anchor: "建立镜头结束·5秒全景中Miguel位置不变·即将切至ECU"
        spatial_anchor: "同格1·全室全景的最终凝视"
        character_state:
          - character: "Miguel"
            pose: "同格1·背对镜头·面向白板·5秒内位置不变"
        on_screen: ["同格1"]
      audio:
        ambience: "低音量空调运行声·办公室底噪"
        events:
          - second: 4
            type: "SFX"
            description: "轻微布料摩擦声(Miguel抬手准备钉照片)"
            duration: 0.5

    # --- A2: ECU Rico照片被钉上白板 (global_sec 5-8, 4秒·极慢推近0.05x) ---
    - global_sec: 5
      seg_ref: "A2"
      camera_position: "白板前偏左·距白板~0.4m·人物可放置区域①"
      is_transition_frame: false
      frame_label: "格6"
      hard:
        shot_type: "大特写"
        focal_length: "85mm"
        camera_movement: "极慢前推(0.05x)·起点·距白板0.4m"
      soft:
        action_anchor: "Miguel右手拇指指腹压紧红图钉·食指稳定照片边角·精准控制(M1锚点)·拇指正将红色图钉按入Rico照片上边缘"
        spatial_anchor: "Rico照片占据画面中心·ECU极特写·照片填满~60%面积·手指+图钉=前景层·照片面部=中景层·白板表面+红线=背景层·放射状红线从照片向外辐射·指向201红圈方向"
        composition:
          subject_position: "Rico照片占据画面中心·ECU极特写·照片填满~60%面积"
          depth_layers: "3层·微分层: 前景(手指+红图钉·25%) + 中景(照片面部·面无表情·举奖杯·60%) + 背景(白板表面·红线放射·旧钉眼凹陷·15%)"
          dominant_lines: "放射状红线从照片向外辐射·向右下方延伸→指向201红圈方向(画框外)"
          negative_space: "紧凑构图·无负空间·视觉压迫感=红线缠颈的窒息感"
          composition_style: "封闭构图·极浅空间·微观层级"
        lighting:
          primary_source: "天花板格栅灯·5000K冷白·从上方+后方均匀照明白板表面·白板柔反光"
          shadow_quality: "极浅·仅旧钉眼凹陷处有物理微影"
          visual_focus: "Rico照片面部(最亮)→手指动作→红图钉(红色焦点)→红线放射→回到照片面部(视觉循环)"
        color:
          red_accent: "红图钉+红线=唯一饱和色·白板表面=纯白背景·照片=黑白/低饱和旧色调"
          finger_skin: "Miguel右手拇指+食指·棕褐色在5000K冷白下偏灰偏蜡·'分析者'的手"
        character_state:
          - character: "Miguel"
            pose: "右手拇指指腹压紧红图钉·食指稳定照片边角·精准控制(M1锚点)"
            position: "人物可放置区域①·白板前·距板~0.5m"
            visible_part: "右手拇指+食指(其余身体和面部在画框外)"
            expression: "面部不可见"
        prop_state:
          - item: "红图钉"
            state: "Miguel右手拇指正在按入照片上边缘"
          - item: "Rico照片"
            state: "三年前·Rico站在颁奖台·举奖杯·面无表情·红线从照片颈部穿过"
          - item: "红线"
            state: "从照片向四周放射连接·向右下方延伸指向建筑平面图201红圈"
        on_screen: ["Rico照片(颁奖台上·举奖杯·面无表情)", "Miguel右手拇指(按红图钉)", "Miguel右手食指(稳定照片)", "红图钉", "红线(从照片向四周放射)", "白板表面(旧钉眼凹陷)", "五张死者照片(红线连接·手写标注)", "建筑平面图(201红圈·边缘可见)"]
      audio:
        ambience: "室内低频持续"
        events:
          - second: 5
            type: "SFX"
            description: "图钉入白板的细微'咔'声·清脆"
            duration: 0.2

    - global_sec: 6
      seg_ref: "A2"
      camera_position: "白板前偏左·距白板~0.33m·人物可放置区域①"
      is_transition_frame: false
      frame_label: "格7"
      hard:
        shot_type: "大特写"
        focal_length: "85mm"
        camera_movement: "极慢前推(0.05x)·匀速·距白板~0.33m"
      soft:
        action_anchor: "推近继续·图钉已按入·Miguel手指开始从照片边缘移开·红图钉稳固·照片紧贴白板表面"
        spatial_anchor: "极慢推近中·Rico照片面部在画面中缓慢变大·从~60%面积扩展·红线缠颈的视觉在逼近中逐步强化·白板表面旧钉眼凹陷开始更清晰"
        composition:
          subject_position: "推近中·Rico照片面部缓慢扩大"
          depth_layers: "前景层(手指)缓慢滑向画框边缘·中景层(照片面部)占比增大"
        character_state:
          - character: "Miguel"
            pose: "手指开始从照片边缘移开·红图钉已按入"
            visible_part: "右手拇指+食指·正在退出画框"
        prop_state:
          - item: "红图钉"
            state: "已按入·稳固·位于照片上边缘"
          - item: "Rico照片"
            state: "面部在推近中缓慢扩大·面无表情→向冷峻过渡"
        on_screen: ["Rico照片(面部扩大中)", "Miguel右手(手指从照片边缘移开)", "红图钉(已按入)", "红线(放射状·缠颈视觉强化)", "白板表面(旧钉眼凹陷更清晰)"]
      audio:
        ambience: "室内低频持续"

    - global_sec: 7
      seg_ref: "A2"
      camera_position: "白板前偏左·距白板~0.27m·人物可放置区域①"
      is_transition_frame: false
      frame_label: "格8"
      hard:
        shot_type: "大特写"
        focal_length: "85mm"
        camera_movement: "极慢前推(0.05x)·匀速·距白板~0.27m"
      soft:
        action_anchor: "推近继续·Miguel手指已完全退出画框·视觉焦点从手指+照片转移到照片面部+红线缠颈"
        spatial_anchor: "推近中·Rico照片面部占画面~70%·红线从颈侧穿过的细节清晰可见·旧钉眼凹陷在照片边缘白板表面愈发明显"
        character_state:
          - character: "Miguel"
            pose: "手指已退出画框"
            visible_part: "无(已退出画框)"
        prop_state:
          - item: "Rico照片"
            state: "面部占比~70%·在极近距下'面无表情'变为冷峻"
          - item: "红线"
            state: "从照片颈侧穿过·缠颈视觉清晰"
        on_screen: ["Rico照片(面部·冷峻)", "红线(缠颈·从颈侧穿过)", "白板表面(旧钉眼凹陷·线索反复调整的痕迹)"]
      audio:
        ambience: "室内低频持续"
        events:
          - second: 7
            type: "SFX"
            description: "手指离开照片·轻微摩擦声"
            duration: 0.3

    - global_sec: 8
      seg_ref: "A2"
      camera_position: "白板前偏左·距白板~0.2m·人物可放置区域①"
      is_transition_frame: false
      frame_label: "格9"
      hard:
        shot_type: "大特写"
        focal_length: "85mm"
        camera_movement: "极慢前推(0.05x)·落定·距白板~0.2m"
      soft:
        action_anchor: "推近落定·Rico照片面部成为画面绝对主体·占据~80%面积·'面无表情'在极度逼近下变为冷峻——这是全场景情绪锚点的顶峰"
        spatial_anchor: "推近落定距白板~0.2m·Rico面部绝对焦点·红线从颈侧穿过形成'缠颈'视觉·白板表面旧钉眼凹陷在边缘清晰可见·暗示线索被反复调整的历程·画面紧凑到无剩余空间·视觉压迫推到极致"
        composition:
          subject_position: "Rico面部成为画面绝对主体·填满~80%面积"
          depth_layers: "2层: 前景(照片面部·85%) + 背景(白板表面旧钉眼凹陷·15%)"
          dominant_lines: "红线从颈部侧方穿过·与照片颈部位置形成'缠颈'视觉"
          composition_style: "封闭构图·极浅空间·视觉焦点完全集中于照片+红线"
        lighting:
          primary_source: "天花板格栅灯·5000K冷白·白板极近距离柔反光"
          shadow_quality: "旧钉眼凹陷清晰可见·暗示线索被反复调整的历程"
          visual_focus: "Rico照片面部(绝对焦点·冷峻面无表情)+红线缠颈(红色)·手指已退出画框"
        color:
          red_accent: "红线缠颈与照片面部冷峻表情='被缠住的人'·红线的唯一饱和色在极近距下更为冲击"
        character_state:
          - character: "Miguel"
            pose: "手指已退出画框·仅留下拇指退出后的短暂残余触感(微痕·可忽略)"
            visible_part: "无(已退出画框)"
        prop_state:
          - item: "Rico照片"
            state: "面部成为绝对视觉焦点·'面无表情'变为冷峻·红线缠颈"
          - item: "红线"
            state: "从照片颈侧穿过·形成'缠颈'视觉·清晰可见"
          - item: "白板表面"
            state: "旧钉眼凹陷清晰可见·线索被反复调整的历史痕迹"
        on_screen: ["Rico照片(面部·冷峻·面无表情·红线缠颈)", "红线(从颈侧穿过)", "白板表面(旧钉眼凹陷)"]
      audio:
        ambience: "室内低频持续·极静"

    # --- A3: MS Miguel后退审视 (global_sec 9-13, 5秒) ---
    - global_sec: 9
      seg_ref: "A3"
      camera_position: "白板与桌之间西侧(A侧)·距白板~1.8m·人物可放置区域①·眼平1.6m·东偏南朝向"
      is_transition_frame: false
      frame_label: "格10"
      hard:
        shot_type: "中景"
        focal_length: "50mm"
        camera_movement: "固定"
      soft:
        action_anchor: "Miguel身体刚完成后移动作·重心后移·双臂垂放或微交叉·后退一步(M2锚点)——从'钉照片的动作'切换到'审视证据网的状态'"
        spatial_anchor: "Miguel上半身位于画面左三分线·视线方向(画右上方·看向白板线索网)留白·前景(衬衫领口+金色警徽·5%)→中景(Miguel上半身·面部是核心·70%)→背景(白板红线网络虚化为色块和线条·形成'红色血管网'在Miguel肩后·25%)"
        composition:
          subject_position: "Miguel上半身位于画面左三分线·视线方向(画右上方·看向白板线索网)留白"
          depth_layers: "3层: 前景(衬衫领口+警徽·5%) + 中景(Miguel面部+上半身·70%) + 背景(白板红线网络·25%)"
          dominant_lines: "垂直(Miguel站姿·刑警权威)+斜线(背景红线方向·案件动态)+水平(视线方向·理性审视)"
          negative_space: "画面右侧·Miguel视线方向·填充白板红线网络(信息接收区)"
          focal_length: "50mm等效·中等景深f/4(背景红线虚化为色块和线条·仍可辨识)"
          composition_style: "开放构图·中景空间·人物+信息环境的互动"
        lighting:
          primary_source: "天花板格栅灯·5000K冷白·上方均匀照明·面部顶光·缺乏方向性立体感"
          shadow_quality: "极浅·眼窝和下颌微暗(顶光自然遮挡)·面部扁平化=制度中人的'功能化'"
          visual_focus: "Miguel面部(额骨和颧骨最亮)→眼珠方向→红线网络(次亮·白板反光)→回到面部(循环视觉流)"
          secondary: "白板反光·非独立光源·从Miguel正面(北侧)微补光"
        color:
          skin_tone: "Miguel棕褐色在5000K冷白下偏灰偏蜡·'分析者'状态"
          background: "白板红线网络在Miguel肩后形成模糊的红色'血管网'"
          badge: "左胸金色警徽在冷白光下呈现制度光泽(A19锚点)"
          depth_color_reversal: "前景人物(中性棕褐·偏冷)+背景红线(暖红色块)=反转冷暖深度——案件比人物更有'温度'"
        character_state:
          - character: "Miguel"
            pose: "身体刚完成后移·重心后移·双臂垂放或微交叉·后退一步(M2锚点)"
            position: "人物可放置区域①·白板前·距板~0.8m·背对白板·面向东偏南"
            expression: "眉心间竖纹·深棕色眼珠从左向右移动·追踪白板上红线网络的逻辑路径·'分析者'审视状态"
            costume: "浅灰衬衫(纽扣领)·左胸金色警徽·深藏青夹克尚未穿(仍在椅背上)"
        on_screen: ["Miguel(上半身·浅灰衬衫)", "左胸金色警徽(制度光泽)", "白板红线网络(虚化·红色'血管网'·在Miguel肩后)", "建筑平面图201红圈(画右上方·隐约可见)"]
      audio:
        ambience: "低音量空调运行声·办公室底噪"

    - global_sec: 10
      seg_ref: "A3"
      camera_position: "白板与桌之间西侧(A侧)·距白板~1.8m·人物可放置区域①"
      is_transition_frame: false
      frame_label: "格11"
      hard:
        shot_type: "中景"
        focal_length: "50mm"
        camera_movement: "固定"
      soft:
        action_anchor: "审视继续·眼珠从左向右进一步移动·追踪红线的逻辑路径·眉心竖纹持续·表情专注"
        spatial_anchor: "同格10·固定机位保持稳定·背景红线网络在浅景深下持续虚化为色块和线条"
        character_state:
          - character: "Miguel"
            pose: "审视姿势稳定·重心后移保持"
            expression: "眼珠继续扫描·从中部红线追踪到右侧·'分析者'状态深入"
        on_screen: ["同格10"]
      audio:
        ambience: "低音量空调运行声·办公室底噪"

    - global_sec: 11
      seg_ref: "A3"
      camera_position: "白板与桌之间西侧(A侧)·距白板~1.8m·人物可放置区域①"
      is_transition_frame: false
      frame_label: "格12"
      hard:
        shot_type: "中景"
        focal_length: "50mm"
        camera_movement: "固定"
      soft:
        action_anchor: "审视深入·眼珠追踪到201房间红圈方向(画右上方)·眼神停顿在红圈处·微妙的'抓住关键'表情"
        spatial_anchor: "同格10·50mm中景保持·背景红线网络在Miguel肩后形成持续的红色'血管网'"
        character_state:
          - character: "Miguel"
            expression: "眼珠追踪至201房间红圈位置·短暂停顿·大脑正在连接线索"
        on_screen: ["同格10"]
      audio:
        ambience: "低音量空调运行声·办公室底噪"

    - global_sec: 12
      seg_ref: "A3"
      camera_position: "白板与桌之间西侧(A侧)·距白板~1.8m·人物可放置区域①"
      is_transition_frame: false
      frame_label: "格13"
      hard:
        shot_type: "中景"
        focal_length: "50mm"
        camera_movement: "固定"
      soft:
        action_anchor: "审视接近尾声·眼珠从红圈位置移开·眉心竖纹微微加深——'分析'正在转向'判断'"
        spatial_anchor: "同格10"
        character_state:
          - character: "Miguel"
            expression: "眉毛微动·嘴角微不可察的变化·大脑完成信息连接·审视即将结束"
        on_screen: ["同格10"]
      audio:
        ambience: "低音量空调运行声·办公室底噪"

    - global_sec: 13
      seg_ref: "A3"
      camera_position: "白板与桌之间西侧(A侧)·距白板~1.8m·人物可放置区域①"
      is_transition_frame: false
      frame_label: "格14"
      hard:
        shot_type: "中景"
        focal_length: "50mm"
        camera_movement: "固定"
      soft:
        action_anchor: "审视结束·Miguel的注意力即将被Vincent的声音(从门口·画左方向)打断——身体微倾向门口方向·即将切换至对话状态"
        spatial_anchor: "同格10·5秒中景保持·中景审视的最后凝视"
        character_state:
          - character: "Miguel"
            expression: "审视结束·即将把注意力转向门口(被Vincent声音打断·在下一镜)"
        on_screen: ["同格10"]
      audio:
        ambience: "低音量空调运行声·办公室底噪"
        events:
          - second: 13
            type: "SFX"
            description: "轻微脚步声从走廊方向传来(画左·门外)"
            duration: 0.5

    # --- A4: MS Vincent门口探头 (global_sec 14-17, 4秒) ---
    - global_sec: 14
      seg_ref: "A4"
      camera_position: "室内门框内侧偏南·距门~1.5m·人物可放置区域④·眼平1.6m·正西朝向·面向门框"
      is_transition_frame: false
      frame_label: "格15"
      hard:
        shot_type: "中景"
        focal_length: "35mm"
        camera_movement: "固定"
      soft:
        action_anchor: "Vincent从走廊探头进入门框——身体在走廊·头微倾探入案情室·一半脸在门框后·露出右半脸和黑框眼镜(V1锚点)"
        spatial_anchor: "门框作为天然画框占据画面边缘(框中框构图母题第一次出现)·前景(门框灰色金属边缘·15%)→中景(Vincent上半身·核心信息层·70%)→背景(室内白板模糊轮廓+办公桌边缘·浅景深f/5.6虚化·15%)"
        composition:
          subject_position: "Vincent位于门框中·半张脸(右半)在门框后·门框=天然画框(框中框构图母题第一次出现)"
          depth_layers: "3层: 前景(门框边缘·15%) + 中景(Vincent上半身·70%) + 背景(室内·白板模糊轮廓+桌边·15%)"
          dominant_lines: "竖线(门框垂直线=制度框架边界)+横线(门框上边缘=空间天花板限制)"
          negative_space: "门框左侧走廊区域·Vincent藏在门框后的左半脸+左肩在画面外走廊中"
          focal_length: "35mm等效·中等景深f/5.6(门框清晰·Vincent面部清晰·背景虚化)"
          composition_style: "框中框·门框作为制度画框(C-FI-14嵌套构图)"
        lighting:
          primary_source: "双光源·冷暖交界——光源A: 室内5000K冷白格栅灯(右上方·照明Vincent右半脸) + 光源B: 走廊3500K暖黄光(左后方·照明Vincent左半身)"
          color_temp_boundary: "冷暖交界线从门框垂直中线贯穿Vincent面部中央偏左——右半脸(室内侧)=5000K冷白·左半身(走廊侧)=3500K暖黄"
          shadow_quality: "柔光·双光源均为柔光·无锐利阴影"
          visual_focus: "Vincent右眼(深棕色·黑框眼镜后·5000K冷白下清晰可见)→镜片反光变化(冷白侧反光强/暖黄侧反光弱)"
        color:
          boundary_event: "冷暖交界是本镜的色彩核心——Vincent白色实验室外套右半(5000K冷白·纯白) vs 左半(3500K暖黄·微暖)"
          glasses: "黑框眼镜·冷白侧镜片反射格栅灯光斑·暖黄侧镜片反射减少·深棕色眼睛可见(V2锚点)"
          background: "白板模糊轮廓(室内冷白·灰白色块·浅景深虚化)"
        character_state:
          - character: "Vincent"
            pose: "身体在走廊·头微倾探入案情室·露出右半脸和黑框眼镜·一半脸在门框后(V1锚点)"
            position: "人物可放置区域④·门框区域·走廊侧·探头入室"
            expression: "信息传递者·深棕色眼睛可见"
            costume: "白色实验室外套(长款·及膝)·内搭深色衬衫"
            dialogue_sync: "'酒店监控没有拍到脸。没有指纹。没有DNA。他清理过。'（CV Vincent）"
        on_screen: ["门框(灰色金属·作为自然画框)", "Vincent(右半脸·黑框眼镜·深棕色眼睛)", "Vincent白色实验室外套(长款·及膝)", "室内白板模糊轮廓(虚化)", "办公桌边缘(虚化)", "冷暖交界线(门框垂直中线贯穿Vincent面部)"]
      audio:
        ambience: "低音量空调运行声·办公室底噪"
        events:
          - second: 14
            type: "CV"
            description: "Vincent: '酒店监控没有拍到脸。没有指纹。没有DNA。他清理过。'(语速中等·陈述语调)"
            duration: 3.0

    - global_sec: 15
      seg_ref: "A4"
      camera_position: "室内门框内侧偏南·距门~1.5m·人物可放置区域④"
      is_transition_frame: false
      frame_label: "格16"
      hard:
        shot_type: "中景"
        focal_length: "35mm"
        camera_movement: "固定"
      soft:
        action_anchor: "Vincent探头姿势稳定·黑框眼镜在冷暖光交界中镜片反射变化——冷白侧反射格栅灯光斑·暖黄侧反射减少·深棕色眼睛清晰可见(V2锚点)"
        spatial_anchor: "同格15·门框构图稳定·固定机位维持框中框的几何张力"
        character_state:
          - character: "Vincent"
            pose: "探头姿势稳定·一半脸在门框后"
        on_screen: ["同格15"]
      audio:
        ambience: "低音量空调运行声·办公室底噪"

    - global_sec: 16
      seg_ref: "A4"
      camera_position: "室内门框内侧偏南·距门~1.5m·人物可放置区域④"
      is_transition_frame: false
      frame_label: "格17"
      hard:
        shot_type: "中景"
        focal_length: "35mm"
        camera_movement: "固定"
      soft:
        action_anchor: "Vincent继续陈述·探头姿势不变·白色实验室外套在双光源下——右半(5000K冷白·纯白)左半(3500K暖黄·微暖)——冷暖交界在服装上同样明显"
        spatial_anchor: "同格15"
        character_state:
          - character: "Vincent"
            pose: "同格15·探头姿势稳定"
        on_screen: ["同格15"]
      audio:
        ambience: "低音量空调运行声·办公室底噪"

    - global_sec: 17
      seg_ref: "A4"
      camera_position: "室内门框内侧偏南·距门~1.5m·人物可放置区域④"
      is_transition_frame: false
      frame_label: "格18"
      hard:
        shot_type: "中景"
        focal_length: "35mm"
        camera_movement: "固定"
      soft:
        action_anchor: "Vincent对白完毕·探头姿势稳定·等待Miguel的回应·视线方向(看画右·室内东=看向Miguel方向)"
        spatial_anchor: "同格15·4秒内Vincent探头姿势稳定"
        character_state:
          - character: "Vincent"
            pose: "同格15·探头姿势稳定·对白完毕"
            expression: "等待回应·深棕色眼睛通过镜片看向Miguel方向"
        on_screen: ["同格15"]
      audio:
        ambience: "低音量空调运行声·办公室底噪"

    # --- A5: CU Miguel回应Vincent (global_sec 18-22, 5秒) ---
    - global_sec: 18
      seg_ref: "A5"
      camera_position: "白板与桌交界西侧(A侧)·距Miguel面部~1.5m·人物可放置区域①/②交界·眼平1.65m·微高于Miguel眼平·东偏北朝向"
      is_transition_frame: false
      frame_label: "格19"
      hard:
        shot_type: "近景"
        focal_length: "85mm"
        camera_movement: "固定"
      soft:
        action_anchor: "Miguel身体微转向门口一侧(西)·头微倾·目光投向画左(Vincent方向)·准备回应——与#A4 Vincent看画右(东)形成对视匹配"
        spatial_anchor: "Miguel面部占据画面~60%面积·中央偏左·眼睛在画面上三分线·视线方向(画左下方·看向Vincent)留白·前景=面部(85%)+背景=红线网络极度虚化→红色'光环'(15%)·浅景深f/2.8·85mm"
        composition:
          subject_position: "Miguel面部占据画面~60%面积·中央偏左·眼睛在画面上三分线·视线方向(画左下方·看向Vincent)留白"
          depth_layers: "2层·极浅空间: 中景(面部·85%) + 背景(红线网络极度虚化→红色'光环'·15%)"
          dominant_lines: "斜线(视线方向·画左下方·15度角·对话张力)+水平线(眼线·眉骨·唇线·表情的稳定基线)+竖线(眉心间竖纹·刑警审视烙印)"
          negative_space: "画面左下方·Miguel视线方向留白·看向Vincent但Vincent不在画面中——负空间承载隐性对话关系"
          composition_style: "封闭构图·浅空间·极度亲密·面部光影细节与背景虚化红线的视觉对话"
        lighting:
          primary_source: "天花板格栅灯·5000K冷白·上方均匀照明·面部顶光: 额骨颧骨最亮·眼窝微暗(眉弓遮挡·审视感增强)·下颌微暗(嘴唇抿在暗部)"
          shadow_quality: "极柔阴影·仅眼窝和下颌微暗·低光比1:1.5·控制感·非审讯高光比"
          visual_focus: "Miguel右眼(额骨颧骨三角区最亮·眼珠在微暗眼窝中)→视线方向→背景红线'光环'(模糊红色)→回到面部"
          secondary: "左胸金色警徽·画面左下角边缘·冷白光下微反光·制度光泽点缀"
        color:
          skin_tone: "Miguel棕褐色在5000K冷白下偏灰偏蜡·'我早就知道'的表情在冷灰肤色下=知情者的冷淡"
          background_halo: "背景红线网络极度虚化(浅景深f/2.8·85mm)·红色线条在Miguel头后方形成模糊红色'光环'——与#A2中缠住Rico照片颈部的红线形成视觉回响"
          visual_echo: "线缠住Rico(#A2)→线在Miguel头后方(#A5)→暗示Miguel也在'线的网络'中"
        character_state:
          - character: "Miguel"
            pose: "身体微转向门口一侧(西)·头微倾·目光投向画左(Vincent方向)"
            position: "人物可放置区域①·白板前·微转身面向西侧(门方向)"
            expression: "宽颧骨·方下颌在冷白光下棱角分明·眉心间竖纹微微加深·嘴角微抿——几乎不可察觉的'我早就知道'的表情"
            costume: "浅灰衬衫·左胸金色警徽·深藏青夹克尚未穿"
            dialogue_sync: "'他从来不需要清理——他从不碰不需要碰的东西。'——这句话的影像化: 背景红线'光环'与#A2'缠颈'红线形成视觉共振"
        on_screen: ["Miguel面部(中央偏左·宽颧骨·方下颌·眉心竖纹·深棕色眼珠)", "浅灰衬衫领口", "左胸金色警徽(左下角·微反光)", "背景白板红线网络(极度虚化·红色'光环')"]
      audio:
        ambience: "室内低频持续"
        events:
          - second: 18
            type: "CV"
            description: "Miguel: '他从来不需要清理——' (语速缓慢·强调'从来不需要')"
            duration: 2.0

    - global_sec: 19
      seg_ref: "A5"
      camera_position: "白板与桌交界西侧(A侧)·距Miguel面部~1.5m·人物可放置区域①/②交界"
      is_transition_frame: false
      frame_label: "格20"
      hard:
        shot_type: "近景"
        focal_length: "85mm"
        camera_movement: "固定"
      soft:
        action_anchor: "Miguel持续对白·视线保持在画左(Vincent方向)·嘴角微抿的表情在CU下极为清晰——一个几乎不可察觉的'我早就知道'"
        spatial_anchor: "同格19·85mm CU固定·浅景深f/2.8保持面部绝对焦点·背景红线'光环'持续存在"
        character_state:
          - character: "Miguel"
            expression: "眉心竖纹微加深·嘴角微抿·深棕色眼珠固定在画左方向·'我早就知道'的表情+冷静陈述"
        on_screen: ["同格19"]
      audio:
        ambience: "室内低频持续"
        events:
          - second: 19
            type: "CV"
            description: "Miguel: '——他从不碰不需要碰的东西。' (语速缓慢·强调'从不碰不需要碰')"
            duration: 2.5

    - global_sec: 20
      seg_ref: "A5"
      camera_position: "白板与桌交界西侧(A侧)·距Miguel面部~1.5m·人物可放置区域①/②交界"
      is_transition_frame: false
      frame_label: "格21"
      hard:
        shot_type: "近景"
        focal_length: "85mm"
        camera_movement: "固定"
      soft:
        action_anchor: "对白完毕的静默瞬间·Miguel的表情从'陈述'过渡到'判断完成'·嘴唇微抿后放松·眼珠微微移开——大脑已完成对Rico的危险性评估"
        spatial_anchor: "同格19·背景红线'光环'在这一刻与Miguel的沉默形成最强共振——'他从不碰不需要碰的东西·但他碰了'(潜台词)"
        character_state:
          - character: "Miguel"
            expression: "对白完毕后的短暂静默·嘴唇从抿紧状态微放松·眼珠微移·从'陈述事实'到'决定行动'的过渡"
        on_screen: ["同格19"]
      audio:
        ambience: "室内低频持续"

    - global_sec: 21
      seg_ref: "A5"
      camera_position: "白板与桌交界西侧(A侧)·距Miguel面部~1.5m·人物可放置区域①/②交界"
      is_transition_frame: false
      frame_label: "格22"
      hard:
        shot_type: "近景"
        focal_length: "85mm"
        camera_movement: "固定"
      soft:
        action_anchor: "Miguel的微表情完成·眼珠从画左(Vincent方向)移回中央偏下(桌面方向)——身体开始从'对话'转向'行动'·深棕色眼睛中的审视感转化为决心"
        spatial_anchor: "同格19·CU近景的最后一秒·面部微表情完成·即将切换至动作镜头"
        character_state:
          - character: "Miguel"
            pose: "身体开始微转·从面向门口(西)转向面向桌子方向·即将切换至行动"
        on_screen: ["同格19"]
      audio:
        ambience: "室内低频持续"

    - global_sec: 22
      seg_ref: "A5"
      camera_position: "白板与桌交界西侧(A侧)·距Miguel面部~1.5m·人物可放置区域①/②交界"
      is_transition_frame: false
      frame_label: "格23"
      hard:
        shot_type: "近景"
        focal_length: "85mm"
        camera_movement: "固定"
      soft:
        action_anchor: "回应完成·Miguel身体开始从面向门口转向办公桌方向——'分析者'→'行动者'的切换开始(M3锚点·在下一镜)"
        spatial_anchor: "同格19·5秒内面部微表情从审视到判断到决心·全过程完成·肤色持续偏灰偏蜡"
        character_state:
          - character: "Miguel"
            expression: "回应完成·即将切换至行动(M3锚点·在下一镜)"
        on_screen: ["同格19"]
      audio:
        ambience: "室内低频持续"

    # --- A6: MS Miguel拿外套+车钥匙 (global_sec 23-25, 3秒) ---
    - global_sec: 23
      seg_ref: "A6"
      camera_position: "办公桌西侧(A侧)·距桌~0.5m·人物可放置区域②·低机位1.3m·略低于眼平·东偏北朝向"
      is_transition_frame: false
      frame_label: "格24"
      hard:
        shot_type: "中景"
        focal_length: "50mm"
        camera_movement: "固定"
      soft:
        action_anchor: "Miguel右手从椅背拿起深藏青警探夹克(哑光面料·拉链立领)——动作果断·无犹豫(M3锚点)·左手同时从桌面抓起车钥匙——双手双轨并行"
        spatial_anchor: "Miguel上半身在画面右三分线·手部动作在画面中央偏下——'行动'在画面几何中心·前景(桌面·笔记本电脑+咖啡杯+笔记本+签字笔·15%)→中景(Miguel上半身+手部动作·65%)→背景(白板线索墙·适度虚化·20%)·双手斜线形成'X'型交叉='分析到行动的交叉点'"
        composition:
          subject_position: "Miguel上半身在画面右三分线·手部动作在画面中央偏下——'行动'在画面几何中心"
          depth_layers: "3层: 前景(桌面·笔记本+咖啡杯+签字笔·15%) + 中景(Miguel上半身+手部动作·65%) + 背景(白板线索墙·适度虚化·20%)"
          dominant_lines: "斜线(右手拿夹克从椅背→向上·左手拿钥匙从桌面→腰部·双手形成'X'型交叉)+水平线(桌面边缘=分析的物理界面)+垂直线(Miguel站姿=蓄势)"
          negative_space: "画面左上方·白板方向的留白·Miguel已经从它面前转身"
          focal_length: "50mm等效·中等景深f/4(手部动作+面部清晰·后景白板适度虚化)"
          composition_style: "开放构图·框取动作·双手双轨的视觉节奏"
        lighting:
          primary_source: "天花板格栅灯·5000K冷白·上方均匀照明·穿衣动作时手臂抬起·面部被手臂微遮挡→短暂暗化='分析者'到'行动者'的光影过渡"
          shadow_quality: "极浅·仅桌面底部与地面·椅背与地面的闭塞阴影(L-3PT-15)"
          visual_focus: "金属车钥匙的反光(冷白光下短暂闪烁·画面最亮)→深色腕表(同框)→右手无名指旧伤疤(淡色凹痕·形成枪柄弧度)→视觉因果链"
          secondary: "笔记本电脑屏幕(~6500K冷蓝微光)·桌面局部·咖啡杯边缘和笔记本纸面微冷蓝高光"
        color:
          color_transition: "从'分析者'色调(#A5: 灰+蜡+浅灰衬衫)过渡到'行动者'色调(深藏青夹克·蓝黑色·冷色行动装备·金属车钥匙冷白反光)"
          jacket_color: "深藏青警探夹克·哑光面料·在5000K冷白下=蓝黑色·近黑的蓝——'行动者'的颜色"
          skin_tone: "Miguel棕褐色在5000K冷白下持续偏灰偏蜡·但此时变化不来自光线·来自动作——'分析者'的最后2秒"
        character_state:
          - character: "Miguel"
            pose: "右手从椅背拿起深藏青警探夹克(哑光面料·拉链立领)·动作果断·无犹豫(M3锚点)·左手同时从桌面抓起车钥匙·双手双轨并行"
            position: "人物可放置区域②·办公桌前·站姿·距桌~0.3m"
            expression: "面部被手臂微遮挡·在穿衣动作中短暂暗化·从'分析'切换到'行动'"
            costume: "浅灰衬衫·左手车钥匙·正在穿上深藏青夹克"
            hand_detail: "右手无名指旧伤疤在握钥匙时形成枪柄弧度(A49锚点)——'从拿笔切换到握钥匙·手指记忆预演了将要发生的行动'"
        prop_state:
          - item: "深藏青警探夹克"
            state: "从椅背上被拿起·正在穿上·从背景物品变为身体一部分"
          - item: "车钥匙"
            state: "左手从桌面抓起·金属反光在冷白光下短暂闪烁"
          - item: "笔记本电脑"
            state: "屏幕亮·显示弹壳对比图(锚定于参考图下排)"
          - item: "深色腕表"
            state: "黑色表盘·秒针在走·与钥匙同框(A29锚点)"
        on_screen: ["办公桌(资料文件夹·横线笔记本·黑色签字笔·黑色咖啡杯)", "笔记本电脑(屏幕亮·弹壳对比图·~6500K冷蓝)", "Miguel(上半身·浅灰衬衫)", "右手(从椅背拿起深藏青夹克·哑光面料)", "左手(从桌面抓起车钥匙·金属反光)", "深色腕表(黑色表盘·秒针在走·与钥匙同框)", "右手无名指旧伤疤(形成枪柄弧度)", "椅背(夹克刚被拿走)", "后景白板(模糊·信息背景)"]
      audio:
        ambience: "室内低频持续"
        events:
          - second: 23
            type: "SFX"
            description: "车钥匙被拿起·金属碰撞轻微叮声"
            duration: 0.3

    - global_sec: 24
      seg_ref: "A6"
      camera_position: "办公桌西侧(A侧)·距桌~0.5m·人物可放置区域②"
      is_transition_frame: false
      frame_label: "格25"
      hard:
        shot_type: "中景"
        focal_length: "50mm"
        camera_movement: "固定"
      soft:
        action_anchor: "穿衣动作进行中·深藏青夹克从右手传递到肩部·左手同时将车钥匙收入手掌·动作流畅连贯·'从拿笔到握钥匙·手指记忆预演了将要发生的行动'"
        spatial_anchor: "同格24·固定机位框取动作的中段·夹克从手中过渡到肩上的动态清晰·钥匙在左手中反光持续"
        character_state:
          - character: "Miguel"
            pose: "穿衣动作进行中·夹克从手过渡到肩·左手握钥匙"
        prop_state:
          - item: "深藏青警探夹克"
            state: "从手部传递到肩部·正在穿上·哑光面料在冷白光下=蓝黑色"
          - item: "车钥匙"
            state: "左手紧握·金属反光在冷白光下闪烁"
        on_screen: ["同格24·夹克穿上过程中"]
      audio:
        ambience: "室内低频持续"
        events:
          - second: 24
            type: "SFX"
            description: "夹克面料摩擦声·穿外套的布料声"
            duration: 0.5

    - global_sec: 25
      seg_ref: "A6"
      camera_position: "办公桌西侧(A侧)·距桌~0.5m·人物可放置区域②"
      is_transition_frame: false
      frame_label: "格26"
      hard:
        shot_type: "中景"
        focal_length: "50mm"
        camera_movement: "固定"
      soft:
        action_anchor: "穿衣完成·深藏青夹克已穿上·拉链未拉·立领竖立·左手持车钥匙·右手自然垂放·准备离开——'行动者'的完整外观呈现·从'分析'到'行动'的物理切换完成"
        spatial_anchor: "同格24·3秒动作镜头结束·Miguel穿着深藏青夹克的完整外观呈现在50mm中景中·后景白板为模糊的信息背景·Miguel已经从它面前转身"
        character_state:
          - character: "Miguel"
            pose: "深藏青夹克已穿上·左手持车钥匙·右手自然垂放·准备离开"
            expression: "面部从手臂遮挡中恢复可见·表情='分析者'→'行动者'的转变完成·眉心竖纹仍在但嘴角放松"
            costume: "深藏青警探夹克已穿上(哑光面料·拉链立领·未拉)·浅灰衬衫内搭·金色警徽·深色腕表·左手车钥匙"
        prop_state:
          - item: "深藏青警探夹克"
            state: "已穿上·拉链未拉·立领竖立·'行动者'外观"
          - item: "车钥匙"
            state: "左手持握·金属反光在冷白光下闪烁"
        on_screen: ["Miguel(上半身·深藏青夹克已穿上·浅灰衬衫内搭·金色警徽)", "左手(持车钥匙·金属反光)", "深色腕表(黑色表盘)", "办公桌局部(笔记本·咖啡杯·签字笔)", "后景白板(模糊·信息背景)"]
      audio:
        ambience: "室内低频持续"

    # --- A7: MLS Miguel门口停顿 (global_sec 26-30, 5秒) ---
    - global_sec: 26
      seg_ref: "A7"
      camera_position: "门框外侧·走廊内·距门~0.8m·人物可放置区域④走廊侧·眼平1.6m·正东朝向·从走廊穿过门框看向室内"
      is_transition_frame: false
      frame_label: "格27"
      hard:
        shot_type: "中全景"
        focal_length: "35mm"
        camera_movement: "固定"
      soft:
        action_anchor: "Miguel站在门框中·身体大部分在室内·面朝走廊方向(画面前方)·停了一下——门框恰好挡住他的脸(M4锚点)·观众只能看到: 深藏青夹克的肩膀和衣领·金色警徽在冷白光一侧闪烁·左手持车钥匙·右手自然垂放"
        spatial_anchor: "全场景构图顶峰——框中框(门框构图·C-FI-14) + 冷暖分界(门框垂直中线贯穿身体) + 脸部遮挡(C-FI-16) + 全纵深透视(门框→Miguel→白板~6m纵深·C-DEP-01单点透视)·四种构图母题汇聚·4层最深纵深: 前景(门框边缘·10%) + 中景前(Miguel在门框中·50%) + 中景后(走廊·5%) + 背景(白板线索墙~6m纵深缩小为远处信息焦点·35%)·深景深f/8·35mm"
        composition:
          subject_position: "Miguel站在门框中·身体大部分在室内·面朝走廊方向(画面前方)·门框恰好挡住他的脸(M4锚点)"
          depth_layers: "4层·全场景最深纵深: 前景(门框边缘·10%) + 中景前(Miguel在门框中·50%) + 中景后(走廊·5%) + 背景(白板线索墙·6m纵深缩小为远处信息焦点·35%)"
          dominant_lines: "竖线(门框垂直线+冷暖交界线贯穿身体)+水平线(门框上下边缘)+透视引导线(天花板灯带·桌边·墙角线→汇聚至白板·C-DEP-01单点透视)"
          negative_space: "门框顶部·画面左右两侧(门框外走廊区域=画面边框外)·紧凑框取·门框本身就是'负空间'的创造者"
          focal_length: "35mm等效·深景深f/8(从门框→Miguel→后景白板·全室纵深清晰)"
          composition_style: "框中框·深空间·封闭型开放构图——全场景构图的总结与出口"
          motif_convergence: "框中有框(C-FI-14)+单点透视(C-DEP-01)+信息密度峰值+隐藏/揭示(C-FI-16)=所有构图母题汇聚"
          symmetry_note: "与#A4 Vincent门框构图形成场景级对称——Vincent=进门(信息进入)vs Miguel=出门(行动出发)"
        lighting:
          primary_source: "双光源·冷暖交界·制度分界线——光源A: 室内5000K冷白格栅灯(从画面后方室内向前照明·照亮Miguel右半身·肤色偏灰偏蜡·深藏青夹克右半偏蓝黑·金色警徽制度光泽) + 光源B: 走廊3500K暖黄光(从画面最前方机位后方涌入·照亮Miguel左半身·肤色回暖深橙金·深藏青夹克左半偏暖深蓝·车钥匙暖金反光)"
          color_temp_boundary: "冷暖交界线从门框垂直中线贯穿Miguel身体——右侧(室内·冷白)=制度内·左侧(走廊·暖黄)=制度外·'分界线上的人'"
          shadow_quality: "柔光·双光源均为柔光·低对比·冷暖交界为色温对比非亮暗对比"
          visual_focus: "双重焦点——右: 金色警徽(冷白侧·闪烁·制度锚点)+左: 车钥匙(暖黄侧·暖金反光·行动锚点)——视线在'制度'和'行动'之间往返"
          secondary: "走廊暖黄光柱从机位后方涌入画面·与室内冷白在门框处形成清晰色温交界线"
        color:
          four_color_states: "一个画面·四种色彩状态: 1)右半身=5000K冷白(深藏青偏蓝黑+肤色灰蜡+警徽制度光泽) 2)左半身=3500K暖黄(深藏青偏暖深蓝+肤色回暖深橙金+钥匙暖金反光) 3)后景白板=6m纵深·冷白·红线/红图钉/红圈缩小为远处信息焦点 4)走廊暖黄光柱=从画面最前方涌入·包裹Miguel左半身·'外部世界的召唤'"
          skin_tone_arc_end: "全场景肤色弧线终点——右半脸(室内冷白)=#A1-A6延续·偏灰偏蜡·分析者——左半脸(走廊暖黄)=新状态·肤色回暖·深橙金·行动者"
          visual_echo: "后景深处白板上的Rico照片(红色图钉)+红线网络+201红圈——与#A2缠颈红线形成跨镜视觉回响·Miguel正从它面前走开"
          dialogue_sync: "'我只是去——叙旧。'——在门框挡住脸的这一刻说出'叙旧'·脸的遮挡+暖光涌入+冷白制度在身后='叙旧'的不可信达到峰值"
        character_state:
          - character: "Miguel"
            pose: "站在门框中·身体大部分在室内·面朝走廊方向(画面前方)·停了一下——门框恰好挡住他的脸(M4锚点)"
            position: "人物可放置区域④·门框区域·室内侧·即将进入走廊"
            visible_part: "深藏青夹克的肩膀和衣领·左胸金色警徽在冷白光一侧闪烁·左手持车钥匙·右手自然垂放·门框挡住脸"
            expression: "面部不可见(被门框遮挡)——遮挡与潜台词'叙旧'的共振"
            costume: "深藏青警探夹克已穿上·浅灰衬衫内搭·金色警徽·深色腕表·左手车钥匙"
        prop_state:
          - item: "金色警徽"
            state: "冷白光侧闪烁·制度光泽·'我还是刑警'"
          - item: "车钥匙"
            state: "暖黄光侧暖金反光·'我正要去'"
          - item: "深藏青夹克"
            state: "左半身暖黄侧偏暖深蓝·右半身冷白侧偏蓝黑·服装的色彩分界线=身体的冷暖分界线"
        on_screen: ["门框(灰色金属·作为框中框画框)", "Miguel(站在门框中·深藏青夹克已穿·金色警徽·左手车钥匙·右手垂放·门框挡住脸)", "冷暖交界线(从门框垂直中线贯穿Miguel身体)", "走廊暖黄光柱(从机位后方涌入画面)", "后景白板(6m纵深透视·缩小为远处信息焦点·Rico照片·红线网络·201红圈)", "天花板格栅灯(室内·5000K冷白)", "室内办公桌边缘(远景)"]
      audio:
        ambience: "室内低频持续·走廊轻微脚步声余韵"
        events:
          - second: 26
            type: "CV"
            description: "Miguel: '我只是去——'(轻微停顿·门框遮挡脸的时刻)"
            duration: 2.0

    - global_sec: 27
      seg_ref: "A7"
      camera_position: "门框外侧·走廊内·距门~0.8m·人物可放置区域④走廊侧"
      is_transition_frame: false
      frame_label: "格28"
      hard:
        shot_type: "中全景"
        focal_length: "35mm"
        camera_movement: "固定"
      soft:
        action_anchor: "Miguel在门框中停留·冷暖交界线稳定贯穿身体·金色警徽在冷白侧持续闪烁·车钥匙在暖黄侧反光·脸上的门框遮挡保持"
        spatial_anchor: "同格27·固定机位维持框中框构图·后景白板在6m纵深透视中保持为远处信息焦点·走廊暖黄光柱持续涌入"
        character_state:
          - character: "Miguel"
            pose: "在门框中停留·冷暖交界保持·面部仍被门框遮挡"
        on_screen: ["同格27"]
      audio:
        ambience: "室内低频持续"
        events:
          - second: 27
            type: "CV"
            description: "Miguel: '——'叙旧'。' ('叙旧'一词在门框挡住脸的时刻说出·潜台词与视觉遮挡共振)"
            duration: 1.5

    - global_sec: 28
      seg_ref: "A7"
      camera_position: "门框外侧·走廊内·距门~0.8m·人物可放置区域④走廊侧"
      is_transition_frame: false
      frame_label: "格29"
      hard:
        shot_type: "中全景"
        focal_length: "35mm"
        camera_movement: "固定"
      soft:
        action_anchor: "对白完毕·静默的呼吸时刻·Miguel在门框中的停顿——冷暖分界·脸部遮挡·'叙旧'的余韵在画面中凝固"
        spatial_anchor: "同格27·构图的静态张力达到峰值——门框=制度框架·Miguel=正在离开框架的人·冷暖分界=两个世界的门槛·白板在远处=已被抛在身后的证据"
        character_state:
          - character: "Miguel"
            pose: "门框中停顿·对白完毕·准备开始走向走廊"
        on_screen: ["同格27"]
      audio:
        ambience: "室内低频持续·走廊暖黄光中微弱的室外底噪"

    - global_sec: 29
      seg_ref: "A7"
      camera_position: "门框外侧·走廊内·距门~0.8m·人物可放置区域④走廊侧"
      is_transition_frame: false
      frame_label: "格30"
      hard:
        shot_type: "中全景"
        focal_length: "35mm"
        camera_movement: "固定"
      soft:
        action_anchor: "Miguel开始从门框中移动——身体走入走廊·左半身暖黄占比逐渐增大·右半身的冷白制度光在减小·'分界线上的人'开始向外部世界倾斜"
        spatial_anchor: "同格27·Miguel在门框中开始移动·身体逐渐被走廊暖黄光完全包裹·后景白板在6m纵深中保持静止——'我已经把它留在身后'"
        character_state:
          - character: "Miguel"
            pose: "从门框中开始走入走廊·身体渐被暖黄光包裹"
        on_screen: ["门框(灰色金属·框中框保持)", "Miguel(开始走入走廊·左半身暖黄占比增大)", "走廊暖黄光柱(增强)", "后景白板(远处·静止)", "冷暖交界线(Miguel身体上的分界在移动)"]
      audio:
        ambience: "走廊暖黄光中微弱的室外底噪上升·室内低频渐退"

    - global_sec: 30
      seg_ref: "A7"
      camera_position: "门框外侧·走廊内·距门~0.8m·人物可放置区域④走廊侧"
      is_transition_frame: false
      frame_label: "格31"
      hard:
        shot_type: "中全景"
        focal_length: "35mm"
        camera_movement: "固定"
      soft:
        action_anchor: "Miguel从门框中走出·身体完全进入走廊·全被3500K暖黄光包裹——肤色全暖金·'行动者'的肤色弧线终点·延续至下个场景——走进走廊深处·最终消失在暖黄光中·门框画面留空·白板在远处6m纵深中静止·案情室空无一人"
        spatial_anchor: "门框空·Miguel已走入走廊深处·画面从'人在框中'过渡到'空框'——制度的框架还在·人已经走了·后景白板线索墙(冷白)在6m纵深中静止·Rico照片·红线网络·201红圈——所有证据留在制度中·行动者走向外部世界"
        composition:
          subject_position: "Miguel走出画框·门框构图的终点——空框是'制度框架中的人走后'的余像"
        lighting:
          migration_note: "Miguel走入走廊时·全身被3500K暖黄包裹→消失在暖黄光中·室内5000K冷白仅照明空室"
        color:
          skin_tone_migration: "Miguel肤色从半灰蜡半暖金→走向走廊时全被3500K暖黄包裹→纯暖金——'分析者'→'行动者'的肤色弧线终点·延续至下个场景"
        character_state:
          - character: "Miguel"
            pose: "从门框中走出·进入走廊·走向画面前方偏下(走廊方向)·最终走出画框·消失在走廊暖黄光中"
            visible_part: "身体渐被走廊暖黄光完全包裹·在走入走廊深处时消失在暖黄光中"
            expression: "面部在门框遮挡后始终不可见——'叙旧'的悬念保留至下一个场景"
        on_screen: ["空门框(灰色金属·框中框构图继续·但框中无人)", "走廊暖黄光柱(填满门框)", "后景白板(6m纵深·Rico照片·红线网络·201红圈·冷白·静止)", "办公楼·天花板格栅灯(5000K冷白·照在空房间里)", "案情室空无一人"]
      audio:
        ambience: "走廊脚步声(逐渐远去)·室外底噪·室内空调低频持续"
        events:
          - second: 30
            type: "SFX"
            description: "脚步声渐远·门框处空无一人·场景结束"
            duration: 1.0
```

---

## §C: 连续性检查清单

### C1: 主体描述词逐字一致?

```
Miguel:
  年龄: 30-40s ✅ 全7镜一致
  发色/发型: short black curly hair with greying temples ✅ 全7镜一致
  面部: wide cheekbones·square jaw·vertical crease between brows·deep brown eyes ✅ 全7镜一致(镜#A1/#A2/#A7面部不可见除外)
  服装: 浅灰衬衫(纽扣领) ✅ 全7镜一致
        深藏青警探夹克(哑光面料·拉链立领) ✅ 镜#A1-A5未穿·镜#A6开始穿上·镜#A7已穿——状态变化有显式事件锚点(M3·global_sec=23)
  金色警徽(A19) ✅ 全7镜一致(镜#A1-#A2不可见除外)
  深色腕表(A29) ✅ 镜#A6可见
  右手无名指旧伤疤(A49) ✅ 镜#A2手指+镜#A6握钥匙可见

Vincent:
  黑框眼镜(矩形框·黑色板材) ✅ 镜#A4一致
  白色实验室外套(长款·及膝) ✅ 镜#A4一致
  深棕色眼睛(V2) ✅ 镜#A4一致
  仅镜#A4出现·不入室·其余6镜不可见 ✅

逐字一致性: ✅ 通过。所有镜头中同一角色的核心外貌特征逐字一致。
```

### C2: 场景空间描述逐字一致?

```
案情室(~6m深×~4m宽×~3m高) ✅ 全7镜一致
北墙白板(~3-4m宽·占满墙面) ✅ 镜#A1-#A3·#A5-#A7可见·一致
南侧合并办公桌×2 ✅ 镜#A1·#A6·#A7可见·一致
西墙灰色金属门(宽~1m·高~2.1m) ✅ 镜#A4·#A7可见·一致
东墙素灰墙面·无窗 ✅ 全镜一致(镜#A1-#A3能看到东墙侧)
天花板四个方形格栅发光顶灯(5000K冷白) ✅ 镜#A1·#A3·#A7可见·一致
走廊3500K暖黄光(推断·已标注物理属性) ✅ 镜#A4·#A7一致

逐字一致性: ✅ 通过。空间元素在可观察镜头中描述一致。
```

### C3: 光源色温+方向跨镜一致?

```
主光源·室内5000K冷白格栅灯:
  ✅ 镜#A1: 天花板格栅灯·5000K冷白·顶光均匀·全室覆盖
  ✅ 镜#A2: 天花板格栅灯·5000K冷白·从上方+后方照明白板
  ✅ 镜#A3: 天花板格栅灯·5000K冷白·上方均匀照明
  ✅ 镜#A4: 室内侧5000K冷白格栅灯·右上方照明Vincent右半脸
  ✅ 镜#A5: 天花板格栅灯·5000K冷白·上方均匀照明
  ✅ 镜#A6: 天花板格栅灯·5000K冷白·上方均匀照明
  ✅ 镜#A7: 室内侧5000K冷白格栅灯·从画面后方室内向前照明Miguel右半身

走廊3500K暖黄光(推断·已标注):
  ✅ 镜#A4: 走廊3500K暖黄·左后方照明Vincent左半身
  ✅ 镜#A7: 走廊3500K暖黄·从画面最前方涌入·照明Miguel左半身
  ✅ 镜#A1-#A3·#A5-#A6: 不出现在画面中(门未入镜或不在画框内)

笔记本电脑屏幕~6500K冷蓝微光:
  ✅ 镜#A1: 桌面局部·微弱
  ✅ 镜#A6: 桌面局部·微弱
  ✅ 其余镜: 不在画框内或被遮挡

色温一致性: ✅ 通过。同光源条件下色温锁定·冷暖混合均有叙事理由(门口=制度交界处)。
```

### C4: 运镜递进是否合理?

```
运镜序列: S0→S1→S0→S0→S0→S0→S0

 镜#A1: S0(固定) ──── 建立·呼吸
 镜#A2: S1(极慢推近0.05x) ──── 全场景唯一运镜·情绪锚点
 镜#A3-A7: S0(固定) ──── 制度空间的静态凝视

递进评估:
  ✅ S0→S1→S0: 建立→情绪锚点(唯一运镜鼓起)→回到静态凝视
  ✅ 速度跳跃: 最大差1档(S0↔S1)·无极端跳跃
  ✅ 运镜配比: S0=86%(6/7镜)·S1=14%(1/7镜)
  ✅ 所有静态镜均有例外理由(信息密集/空间受限)·无惰性静态

递进: ✅ 通过。制度空间的"冷静态凝视"策略·静态主导符合叙事属性。
```

### C5: 动作方向有跨镜连续性?

```
Miguel动作弧线:
  镜#A1(0-4s): 背身站姿·面向白板·建立
  镜#A2(5-8s): 右手钉照片(拇指按红图钉·食指稳定)→手指退出——M1锚点
  镜#A3(9-13s): 后退一步·重心后移·双臂垂放或微交叉——M2锚点
  镜#A4(14-17s): [不在画面中·Vincent门外出现]
  镜#A5(18-22s): 身体微转向门口(西)·头微倾·看向Vincent——对话状态
  镜#A6(23-25s): 右手拿夹克·左手抓钥匙——M3锚点·从分析切换到行动
  镜#A7(26-30s): 站在门框中→停→门框挡脸→走入走廊→走出画框——M4锚点

因果关系链:
  ✅ 钉照片(M1)→后退审视(M2)→对话回应(#A5)→拿外套+钥匙(M3)→门口停顿并离开(M4)
  ✅ 动作因果链完整·无跳跃·无缺失
  ✅ Miguel从"分析者"(灰蜡肤色·冷白制度内)→"分界线上的人"(半灰蜡半暖金·门框)→"行动者"(全暖金·走廊·延续至下场景)

Vincent动作:
  镜#A4(14-17s): 探头入门框·一半脸在门框后→姿势稳定·对白完毕
  ✅ Vincent仅在镜#A4出现·动作弧线自足·无跨镜连续性需求

视线匹配:
  ✅ 镜#A4 Vincent看画右(东·看向Miguel) ↔ 镜#A5 Miguel看画左(西·看向Vincent) = 对视方向相反 = 正确匹配
  ✅ 参照E-MTC-04视线匹配铁律

跨镜连续性: ✅ 通过。
```

### C6: 景别递进曲线是否合理?

```
景别递进: LS→ECU→MS→MS→CU→MS→MLS

 镜#A1: LS/MLS (宽) ───── 建立·呼吸·全室信息
 镜#A2: ECU (极紧) ───── 突入·锚点·视觉冲击·全场景情绪核心
 镜#A3: MS (中) ──────── 回中·角色状态审视
 镜#A4: MS (中) ──────── 平行·新角色引入(景别平行=角色对等)
 镜#A5: CU (紧) ──────── 收紧·对话强度提升·面部微表情
 镜#A6: MS (中) ──────── 过渡·动作容纳
 镜#A7: MLS (中宽) ──── 释放·场景出口·全室纵深最后回望

节奏特征: LS → ECU(冲击) → MS(回中) → MS(hold) → CU(收紧) → MS(过渡) → MLS(释放)
视觉呼吸: 宽→极紧→中→中→紧→中→宽 = 有张弛的V形曲线

景别递进: ✅ 通过。V形曲线符合建立→锚点→释放→出口的叙事需求。
```

### C7: 信息密度波形是否合理?

```
信息密度曲线(7镜):
  极高(#A1: LS·深景深·全室)→极低(#A2: ECU·浅景深·单一元素·冲击)→
  中(#A3: MS·面部+背景双重信息)→中高(#A4: MS·新角色+门框构图+冷暖交界)→
  中低(#A5: CU·面部绝对焦点)→中(#A6: MS·手部动作+桌面)→
  极高(#A7: MLS·门框构图+冷暖交界+脸部遮挡+全纵深·全场景最高)

信息密度波形: ✅ 通过。类似"呼吸"的V形——建立镜和出口镜为信息峰值·ECU为最低点的"心跳"。
```

### C8: TIME_SKELETON.frames 逐秒格号是否连续?

```
逐秒检测:
  global_sec 0 → 格1 ✅
  global_sec 1 → 格2 ✅
  global_sec 2 → 格3 ✅
  ... (逐秒递增)
  global_sec 30 → 格31 ✅

跳秒: 🈚 无。31秒=31帧·每秒必有帧·格号连续·无跳秒。
```

### C9: 180度线跨镜一致性

```
关系线: Miguel ↔ 白板中心(南北向)
A侧: 西侧(门所在侧)

逐镜轴线验证:
  镜#A1: 轴上(neutral) ✅
  镜#A2: 轴上(neutral·插入镜头·天然中性) ✅
  镜#A3: A侧(西侧) ✅
  镜#A4: A侧(西侧) ✅
  镜#A5: A侧(西侧) ✅
  镜#A6: A侧(西侧) ✅
  镜#A7: A侧(西侧·A侧自然延伸至走廊·空间连续) ✅

跨镜越轴: 🈚 零次越轴
180度线: ✅ 通过。全场景7镜均在A侧(西侧)或轴上。
```

### C10: 空间连续性 (机位不穿墙·不越轴)

```
逐镜空间验证:
  镜#A1机位: 区域⑤·房间中央·距白板3m → ✅ 不穿墙·不悬空
  镜#A2机位: 区域①·白板前·距板0.4m→0.2m(推近) → ✅ 全路径在区域①内
  镜#A3机位: 区域①·白板前西侧·距板1.8m → ✅ 不穿墙·不悬空
  镜#A4机位: 区域④·门内侧·距门1.5m → ✅ 不穿墙·不悬空
  镜#A5机位: 区域①/②交界·距Miguel面部1.5m → ✅ 不穿墙·不悬空
  镜#A6机位: 区域②·办公桌西侧·距桌0.5m·1.3m低机位 → ✅ 不穿墙·不悬空
  镜#A7机位: 区域④走廊侧·距门0.8m·推断空间(已标注物理属性) → ✅ 不穿墙·不悬空

空间连续性: ✅ 通过。全部7个机位在人物可放置区域①-⑤内·不穿墙不悬空。
```

### C11: 光影连续性 (同一光源跨镜一致)

```
天花板格栅灯5000K冷白:
  ✅ 镜#A1: 全室覆盖·低光比1:1.5
  ✅ 镜#A2: 白板柔反光·从上方+后方
  ✅ 镜#A3: 上方均匀·面部扁平
  ✅ 镜#A4: 右上方·照明Vincent右半脸
  ✅ 镜#A5: 上方均匀·额骨颧骨最亮·眼窝下颌微暗
  ✅ 镜#A6: 上方均匀·手臂遮挡面部时短暂暗化
  ✅ 镜#A7: 画面后方室内向前·照亮Miguel右半身

  一致性: ✅ 5000K冷白格栅灯在7/7镜中作为主光源出现·色温·方向·质量逐镜一致

走廊3500K暖黄光:
  ✅ 镜#A4: 左后方·照明Vincent左半身·仅此镜和#A7出现
  ✅ 镜#A7: 画面最前方·涌入门框·照明Miguel左半身

  一致性: ✅ 走廊暖黄光仅在门框相关镜(#A4·#A7)中出现·色温·方向一致

光影连续性: ✅ 通过。同光源跨镜一致·冷暖混合均有叙事理由(门框=制度交界处)。
```

### C12: 道具连续性 (基于ANCHOR_BASELINE+Composition Designer prop_state)

```
关键道具跨镜状态追踪:

深藏青警探夹克:
  镜#A1-A5: 搭在椅背上·未穿
  镜#A6 global_sec=23: 从椅背拿起→正在穿上
  镜#A6 global_sec=25: 已穿上·拉链未拉·立领竖立
  镜#A7: 已穿上·左半暖黄偏暖深蓝·右半冷白偏蓝黑
  ✅ 状态变化有显式事件锚点(M3·镜#A6)·无状态跳跃

车钥匙:
  镜#A1-A5: 不在画面中(在桌面或口袋·具体位置不可见)
  镜#A6 global_sec=23: 左手从桌面抓起→金属反光在冷白光下闪烁
  镜#A6 global_sec=25: 左手紧握
  镜#A7: 左手持·暖黄侧反光偏暖金色
  ✅ 引入有明确事件(从桌面抓起·镜#A6)·无凭空出现

金色警徽:
  镜#A1-A2: 不可见(背身/手部特写)
  镜#A3: 可见·冷白光下制度光泽
  镜#A4: 不可见(Miguel不在画面中)
  镜#A5: 画面左下角边缘·微反光
  镜#A6: 可见·冷白光下制度光泽
  镜#A7: 冷白光侧闪烁·'制度锚点'
  ✅ 随身物品·随角色进出画面自动延续

Rico照片:
  镜#A1: 在白板上·全貌中
  镜#A2: ECU·红图钉钉入→推近至面部+红线缠颈
  镜#A3: 在白板上·背景虚化中
  镜#A5: 在白板上·极度虚化·红线'光环'
  镜#A7: 在白板上·6m纵深远处·缩小为信息焦点
  ✅ 位置在白板上不变·状态变化(钉入→推近特写→回到背景)有跨镜递进

红线网络:
  镜#A1: 全貌·从照片向四周放射·连接死者照片→汇聚201红圈
  镜#A2: 一根红线从Rico照片颈侧穿过·缠颈视觉
  镜#A3: 背景虚化·'红色血管网'
  镜#A5: 极度虚化·红色'光环'
  镜#A7: 6m纵深远处·缩小·红图钉·红线·红圈注
  ✅ 全场景循序渐进呈现·构成'红线网络视角'构图母题

道具连续性: ✅ 通过。所有关键道具跨镜状态变化有显式事件锚点或构图母题递进。无状态跳跃·无凭空出现·无消失后无解释重现。
```

---

## 合并冲突记录

```
三Agent YAML机械合并·冲突检测:

字段冲突扫描:
  seg_ref: Shot Architect=A1·Movement Designer=A1·Composition Designer=A1 → ✅ 一致
  global_sec: 三Agent逐帧sec值和global_sec值完全一致 → ✅ 一致
  camera_position: Shot Architect≈Movement Designer≈Composition Designer → ✅ 一致(语义等价·措辞微异)
  shot_type: 仅Shot Architect定义 → ✅ 无冲突(Movement/Composition不定义此字段)
  focal_length: 仅Shot Architect定义 → ✅ 无冲突
  movement: 仅Movement Designer定义 → ✅ 无冲突(Shot Architect留空留给Movement填充)
  composition/layout: 仅Composition Designer定义 → ✅ 无冲突
  lighting: 仅Composition Designer定义 → ✅ 无冲突
  character_state: 仅Composition Designer定义(frames_soft中) → ✅ 无冲突

裁决: 🈚 无可检测冲突。三Agent的YAML字段分工明确——Shot Architect定义机位/景别/焦距·Movement Designer定义运镜·Composition Designer定义构图/光影/角色状态。字段不重叠·无需裁决。

冲突裁决规则应用:
  Shot Architect(机位) > Movement(运镜) > Composition(构图) — 未触发·字段无重叠
  global_anchors仅由Composition Designer定义·其他Agent不可覆盖 — ✅ 已遵守
```

---

## 画布宪法合规声明

```
参照画布宪法第四条·运镜-画面分离:
  ✅ §A骨架和§B TIME_SKELETON中画面描述不含运镜语义
  ✅ 运镜参数在segments和frames[].hard中独立存储
  ✅ 跨镜零引用·每镜/每帧独立完整描述

参照画布宪法第三条·空间锚定:
  ✅ 全部机位锚定于ANCHOR_BASELINE §C空间地图人物可放置区域①-⑤
  ✅ 光源全部有物理锚点(格栅灯·笔记本屏幕·走廊暖黄光)
  ✅ 走廊推断空间已标注物理属性

参照画布宪法第五条·确定性优先:
  ✅ 所有描述基于三Agent YAML中的可量化数据·无新增模糊描述
  ✅ 机位坐标·色温K值·光比·深度层次百分比均量化

本planner为机械合并器——不添加三Agent YAML中没有的数据·不修改三Agent的设计决策·冲突处已标记。
```

---

> **Storyboard Planner 签名:** v2.0 · 机械合并器 · 独立上下文
> **输入:** Shot Architect YAML + Movement Designer YAML + Composition Designer YAML + ANCHOR_BASELINE
> **输出:** §A锁定骨架 + §B TIME_SKELETON(31帧) + §C连续性检查清单(12项)
> **冲突:** 🈚 无可检测冲突(三Agent字段不重叠)
> **合并模式:** 逐帧机械合并·Shot Architect hard字段 + Movement Designer movement字段 + Composition Designer soft字段
> **下游交付:** prompt_composer(消费§A+§B展开视频提示词) · storyboard_previewer(消费§B派生逐格线稿) · 审查专家(消费§B逐秒diff验证)
> **TIME_SKELETON spec:** 04_共享/TIME_SKELETON_spec.md v1.0 · 格式完全合规
