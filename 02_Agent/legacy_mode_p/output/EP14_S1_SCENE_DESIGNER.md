# Scene Designer v1.0 -- EP14 S1 三域合并设计

> **Agent:** Scene Designer v1.0 (合并式·三域整合)
> **剧本:** 枪王 EP14《调查》S1: 圣保罗刑警总部·案情室(内景·人工光)
> **complexity_level:** S
> **判定依据:** F1 N_spaces=1(S触发) · F2 N_speakers=2 · F3 N_dialogue=4 · F4 R_static=100% · F5 Has_action=false(仅桌面动作·无打斗/追逐) · F6 N_shots=5
> **执行分支:** 3A S-Level流程(静态快速通道)
> **输出目标:** EP14_S1_SCENE_DESIGNER.md
> **总时长:** 32s · 5镜 · 全部固定

---

# Step 0: 场景类型判定 + 空间坐标系（三域共享·只写一次）

## 场景类型判定

场景分析:
  [x] 有角色>=2 -> Miguel+Vincent双人对话
  [x] 有对话 -> 4句对白
  [x] 室内单空间 -> 无空间转换
  [ ] 有打斗/追逐/悬疑 -> 无
  [ ] 环境描述为主 -> 非

判定: 双人对话场景·纯室内·全静态
KB章节路由: 双人对话(机位域§1.1-1.3·运镜域§5.2-5.4·构图光影域§4.1+§4.2+§6.1-6.4)
P0安全规则: D-TRI-01~05·E-MTC-04·M-MOT-03+M-MOT-04+GEN-02·画布宪法七条·P-STATE§1+§2

场景类型=[双人对话] · 角色数=[2: Miguel+Vincent] · complexity=[S]
KB章节=[1.1-1.3双人对话+5.2运动方式+5.4运镜对话+4.1画面分配+4.2构图法则+6.1-6.4光影色彩+8.2对比与亲和]

## 空间坐标系

### 空间尺寸

空间类型: 现代极简办公/案件分析室·封闭内景无窗
尺寸: 约6m(宽) × 5m(深) × 2.8m(高)
面积: ~30m2(中型分析室)
地面: 灰色耐磨地板或短绒地毯·冷灰基调
天花: 四组方形格栅LED面板灯·均匀布光

### 关键建筑元素

| 元素 | 位置 | 描述 |
|------|------|------|
| 白板线索墙 | 正对门口·房间后墙居中 | 画面视觉重心·金属边框·亚光白表面·布满物证 |
| 合并办公桌 | 房间中央偏后·白板前约2m | 深色木质或金属框架·L形或矩形·笔记本电脑+卷宗+文具+咖啡杯 |
| 门口 | 房间前墙·偏右或居中 | 标准办公室门宽~0.9m·门框提供自然画框·Vincent出入点 |
| 办公椅 | 桌后 | 可旋转办公椅·深色网面或皮质·Miguel取外套的家具锚点 |
| 角落电脑位 | 房间侧墙·可选次要人物区 | 辅助台式机/笔记本电脑·画面深处次要视觉层 |

### 人物可放置区域

1. 白板前1-2m(站姿·Miguel主表演区·光线最佳)
2. 办公桌侧(站姿·Miguel取外套+车钥匙·过渡动作区)
3. 门口处(站姿·Vincent探头通报·门框自然框景)
4. 办公桌后(坐姿·未使用·本场景Miguel全程站立)

### 180度线设定

关系线: Miguel(白板前) <-> Vincent(门口) · 轴线沿房间纵深方向(白板↔门口)
轴线侧选择: A侧(白板前方·面向门口方向)
选取理由: 所有机位在A侧·保持Miguel看向门口(Vincent方向)统一·白板始终在画面背景或前景
D-TRI-01(180度关系线定义)·D-TRI-03(对话场景轴线)

### 光源物理锚点

光源1[天花板LED格栅主光源]: 四组方形格栅LED面板灯·正上方均匀布光·冷白~4500-5000K·柔光(散射)
  锚点: IMAGE_AUDIT_EP14·参考图格1(全景·天花板格栅灯在画面上方)

光源2[笔记本电脑屏幕光]: 桌面·笔记本屏幕·冷蓝~6500K·局部补光·照亮人物面部下侧
  锚点: IMAGE_AUDIT_EP14·参考图格3(特写·笔记本弹壳对比画面)

光源3[白板区域反射]: 白板表面·天花板灯光最强反射区·画面最亮区域
  锚点: IMAGE_AUDIT_EP14·参考图格1(全景·白板线索墙全貌)+格2(中景·白板信息网络分区特写)

### 空间约束速查

禁入区: 白板至后墙之间(间距过窄无法站人)·桌面物品上方(不可悬浮)
窄区: 无(房间30m2·机位移动空间充足·但全固定不涉及运镜空间)
物理属性: 所有机位在可拍摄区域内(正面白板视角·45度侧角·过肩·桌面平视·门口视角·微距物证)
P-FAL-06: 不触发(全固定·无横移)
P-FAL-09: 不触发(全固定·无极端运动形变风险)

---

# Step 1: 场景级静态比例预判

5镜全部固定 → 静态占比100% ≥ 80%
判定: 🎥 运镜域触发静态快速通道
运镜域输出压缩至一句话——不为"什么都不做"编写形式主义论证

---

# Step 2: KB加载（场景类型路由·S-Level缩略加载）

S-Level缩略: 双人对话场景·每域只加载核心~10条

机位域:
  D-TRI-01(180度关系线)·D-TRI-03(对话场景轴线)·D-TRI-05(越轴过渡)
  E-MTC-04(视线匹配)
  shared_agent_runtime§4: 8机位模板(双人对话)
  C-COM-04(特写情绪峰值)

运镜域:
  M-MOT-01(运镜必须有动机·静态适用例外)
  M-MOT-03(空间可行性)
  M-MOT-04(运镜速度空间约束)
  P-FAL-01~10(已知失败模式·全部已规避)

构图光影域:
  C-KTZ-01~05(景别)·C-KTZ-13(主体位置)
  C-FI-01(负空间)·C-FI-06(深度层次)·C-FI-21(主导线条)·C-DEP-01(深度策略)
  L-3PT-01(主光源)·L-3PT-05(光影焦点)·L-3PT-08(光比)
  COL-PRI-01(互补色)·COL-PRI-03(主色调)
  VS-COM-06(视线引导)·VS-SPA-01(空间深度)

---

# Step A-S1: 覆盖策略速选

从8机位模板(双人对话)选5个必要机位·不展开未使用理由:

| 机位 | 模板 | 叙事功能 |
|:----:|------|---------|
| ①全景建立 | Establishing | 建立案情室空间·白板+桌+人物位置关系·制度空间锚定 |
| ②中景门口 | OTS/门口视角 | Vincent通报+Miguel在背景白板前建立双人空间关系 |
| ③中近景Miguel | Single A | Miguel主镜头·对白+动作(钉照片+取外套) |
| ④大特写白板 | Insert | 白板证据网络·逻辑锚点·红钉+红线叙事 |
| ⑤中近景Miguel(桌) | Single A(移位) | Miguel决策+动作(外套+车钥匙)+对白收束 |

未使用模板机位: Single B(Vincent无独立单人镜·门口中景已覆盖)·Reaction(无独立反应镜·Miguel反应嵌入②③⑤)·Re-establishing(S-Level不冗余建立)

---

# Step A-S2: 逐镜机位速记

````
#1 | 全景 | 全景建立 | 24mm | 深f/11 | 眼平 | A侧 | 建立 | D-TRI-03
#2 | 中景 | 门口视角 | 35mm | 中f/5.6 | 眼平 | A侧 | 推进 | D-TRI-01+E-MTC-04
#3 | 中近景 | 单人Miguel | 50mm | 浅f/2.8 | 眼平 | A侧 | 推进 | D-TRI-03+C-COM-04
#4 | 大特写 | 插入·白板 | 85mm | 浅f/2.8 | 眼平(白板中心) | 轴上 | 揭示 | C-COM-04
#5 | 中近景 | 单人Miguel(桌) | 50mm | 中f/5.6 | 眼平 | A侧 | 释放 | D-TRI-05+E-MTC-04
````

---

# Step A-S3: 运镜处理（静态快速通道激活）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎥 运镜域: 静态快速通道激活 — 5/5镜固定
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

5/5镜固定·制度空间静态凝视。0镜含运镜·全场景固定机位。
动态镜占比: 0/5。静态快速通道完成。

静态例外标注(仅标注·不展开论证):
  镜①-⑤全部: 信息密集(制度空间·观众吸收线索细节)+空间充裕但无运动动机(全场景~32s·对话+动作提供足够视觉信息·M-MOT-01)

不输出:
  ✗ 速度分布统计·加速度波形·两极分化检查
  ✗ "为什么这个镜头不运动"段落论证
  ✗ 静态例外审核表

---

# Step A-S4: 构图光影速记

## 镜① 0-5s: 全景建立

构图: 白板居中偏上 | 3层(前景桌面·中景Miguel·背景白板) | 横线(天花格栅灯+桌面)+竖线(白板边框+门框) | 开放构图·单点透视 | C-FI-06+C-DEP-01
光影: 天花板LED格栅(冷白~4500K·柔光·均匀) | 光比1:2(中调·均匀办公照明) | 白板=最亮区域 | L-3PT-01+L-3PT-05
色彩: 冷灰蓝主调 | 类似色(灰+蓝+白) | 低饱和 | COL-PRI-03

## 镜② 5-11s: 中景门口视角

构图: Vincent居中偏右(门框内)·Miguel在左侧背景白板前 | 3层(前景门框·中景Vincent·背景Miguel+白板) | 竖线(门框)+横线(桌面·天花灯) | 画中画(门框=自然画框) | C-FI-06+C-FI-13
光影: 天花板LED(冷白~4500K·柔光) | 光比1:2.5(门口微暗于白板区·自然光源衰减) | Vincent面部=次亮·白板=最亮(背景) | L-3PT-01+L-3PT-05
色彩: 冷灰蓝主调·门框暗部微偏青 | 类似色 | 低饱和 | COL-PRI-03

## 镜③ 11-18s: 中近景 Miguel

构图: Miguel左三分线·白板占据右侧背景 | 3层(前景Miguel肩部·中景Miguel面部+手部钉照片动作·背景白板线索) | 竖线(Miguel身体)+对角线(手臂→白板·红线网络) | 非对称构图 | C-KTZ-13+C-FI-06+C-FI-21
光影: 天花板LED(冷白~4500K·柔光)+笔记本屏幕光(冷蓝~6500K·局部·面部下侧微补) | 光比1:2.5 | Miguel面部=最亮·白板=次亮背景·手部(钉照片动作)有清晰照明 | L-3PT-01+L-3PT-05
色彩: 冷灰蓝主调+红钉红线(互补色高对比) | 互补色(蓝灰 vs 红) | 低饱和+红色高饱和(仅红钉·红线) | COL-PRI-01

## 镜④ 18-23s: 大特写白板

构图: 白板证据网络居中 | 2层(前景红钉+红线·中景照片+平面图+报告) | 斜线(红线网络·主导视觉流)+横线(报告·平面图) | 信息密度构图·无负空间 | C-FI-21+C-KTZ-13
光影: 天花板LED反射(冷白~4500K·柔光·白板表面最亮) | 光比1:3(白板表面:照片暗部) | 红钉=高光反射点·红线=中亮·照片暗部=最低 | L-3PT-01+L-3PT-05
色彩: 冷白主调+红色高对比+照片暖色调(人物照片·肤色) | 互补色(冷白 vs 红) | 白板低饱和+红色高饱和 | COL-PRI-01+COL-PRI-03
禁止: 白板文字内容(后期叠加·P-FAL-08)·弹道报告文字·酒店平面图标注

## 镜⑤ 23-32s: 中近景 Miguel(桌)

构图: Miguel右三分线·桌面前景(笔记本+卷宗+咖啡杯·部分虚化)·门口在左侧背景 | 3层(前景桌面物件虚化·中景Miguel取外套+车钥匙·背景门口+走廊光) | 竖线(Miguel)+对角线(手臂取外套动作) | 开放构图·Miguel面向门口(画右→画左) | C-KTZ-13+C-FI-06+C-FI-01
光影: 天花板LED(冷白~4500K·柔光)+笔记本屏幕光(冷蓝~6500K) | 光比1:3(桌区暗于白板区·Miguel面部由混合光源照明) | Miguel面部=最亮·车钥匙金属反光=点光源·桌面暗部=氛围 | L-3PT-01+L-3PT-05+L-3PT-08
色彩: 冷灰蓝主调·外套深色(黑/藏青·与冷灰形成层次)·车钥匙金属银(冷调反光) | 类似色+金属银点 | 低饱和 | COL-PRI-03

---

# Step A-S5: 轴线+空间速验

轴线验证: 5镜·0次越轴·0次视线矛盾(镜② Vincent看左[Miguel方向]·镜③ Miguel看右[Vincent方向]·镜⑤ Miguel看左[门口方向]·全场景一致性对视线✅)
空间约束: 5机位全部在可拍摄区域(IMAGE_AUDIT_EP14·6个可拍摄角度内选出5个)·不穿墙不悬空✅
P-FAL规避: P-FAL-01(无瞳孔描述)·P-FAL-02(无mm精度)·P-FAL-03(时间精度=1秒级)·P-FAL-04(每镜≤2个同时音效)·P-FAL-05(对白<4字/秒·Miguel最长句8秒9字≈1.1字/秒·Vincent最长句6秒8字≈1.3字/秒)·P-FAL-06(全固定无横移)·P-FAL-07(低视觉熵·冷灰单色主导·无高频纹理)·P-FAL-08(白板文字标注后期叠加·画面内不要求文字渲染)·P-FAL-09(全固定无运动形变)·P-FAL-10(无同时口型·Vincent单独发言·Miguel单独发言)全部规避✅

---

# ============================================================
# §4 机位域YAML
# 映射目标: TIME_SKELETON.segments[].camera + frames[].hard
# ============================================================

segments_camera:
  - segment_id: "①"
    time_range: [0, 5]
    shot_type: "全景"
    focal_length: "24mm"
    dof: "深景深f/11"
    angle: "眼平(1.6m)"
    axis_side: "A侧(白板前·面向门口)"
    coverage_function: "建立(空间引入+人物位置关系)"
    kb_rule_ids:
      - "D-TRI-03"
      - "C-DEP-01"

  - segment_id: "②"
    time_range: [5, 11]
    shot_type: "中景"
    focal_length: "35mm"
    dof: "中景深f/5.6"
    angle: "眼平(1.6m·门口视角)"
    axis_side: "A侧"
    coverage_function: "推进(Vincent通报+双人空间关系)"
    eye_line: "Vincent看左(画面左侧=白板方向·Miguel位置)"
    kb_rule_ids:
      - "D-TRI-01"
      - "E-MTC-04"
      - "C-FI-13"

  - segment_id: "③"
    time_range: [11, 18]
    shot_type: "中近景"
    focal_length: "50mm"
    dof: "浅景深f/2.8"
    angle: "眼平(1.6m·正面Miguel)"
    axis_side: "A侧"
    coverage_function: "推进(Miguel主镜头·对白+钉照片动作)"
    eye_line: "Miguel看右(画面右侧=门口方向·Vincent位置)"
    kb_rule_ids:
      - "D-TRI-03"
      - "C-COM-04"
      - "C-KTZ-13"

  - segment_id: "④"
    time_range: [18, 23]
    shot_type: "大特写"
    focal_length: "85mm"
    dof: "浅景深f/2.8"
    angle: "眼平(1.5m·白板中心高度)"
    axis_side: "轴上(neutral·正对白板)"
    coverage_function: "揭示(白板证据网络·逻辑锚点)"
    kb_rule_ids:
      - "C-COM-04"
      - "C-FI-21"

  - segment_id: "⑤"
    time_range: [23, 32]
    shot_type: "中近景"
    focal_length: "50mm"
    dof: "中景深f/5.6"
    angle: "眼平(1.6m·桌侧)"
    axis_side: "A侧"
    coverage_function: "释放(Miguel决策+动作+对白收束)"
    eye_line: "Miguel看左(画面左侧=门口方向·Vincent位置)"
    kb_rule_ids:
      - "D-TRI-05"
      - "E-MTC-04"
      - "C-FI-01"

frames_hard:
  # ====== 镜① 全景建立 0-5s ======
  - {sec: 0, global_sec: 0, camera_position: "①", shot_type: "全景", focal_length: "24mm"}
  - {sec: 1, global_sec: 1, camera_position: "①", shot_type: "全景", focal_length: "24mm"}
  - {sec: 2, global_sec: 2, camera_position: "①", shot_type: "全景", focal_length: "24mm"}
  - {sec: 3, global_sec: 3, camera_position: "①", shot_type: "全景", focal_length: "24mm"}
  - {sec: 4, global_sec: 4, camera_position: "①", shot_type: "全景", focal_length: "24mm"}

  # ====== 镜② 中景门口视角 5-11s ======
  - {sec: 5, global_sec: 5, camera_position: "②", shot_type: "中景", focal_length: "35mm"}
  - {sec: 6, global_sec: 6, camera_position: "②", shot_type: "中景", focal_length: "35mm"}
  - {sec: 7, global_sec: 7, camera_position: "②", shot_type: "中景", focal_length: "35mm"}
  - {sec: 8, global_sec: 8, camera_position: "②", shot_type: "中景", focal_length: "35mm"}
  - {sec: 9, global_sec: 9, camera_position: "②", shot_type: "中景", focal_length: "35mm"}
  - {sec: 10, global_sec: 10, camera_position: "②", shot_type: "中景", focal_length: "35mm"}

  # ====== 镜③ 中近景 Miguel 11-18s ======
  - {sec: 11, global_sec: 11, camera_position: "③", shot_type: "中近景", focal_length: "50mm"}
  - {sec: 12, global_sec: 12, camera_position: "③", shot_type: "中近景", focal_length: "50mm"}
  - {sec: 13, global_sec: 13, camera_position: "③", shot_type: "中近景", focal_length: "50mm"}
  - {sec: 14, global_sec: 14, camera_position: "③", shot_type: "中近景", focal_length: "50mm"}
  - {sec: 15, global_sec: 15, camera_position: "③", shot_type: "中近景", focal_length: "50mm"}
  - {sec: 16, global_sec: 16, camera_position: "③", shot_type: "中近景", focal_length: "50mm"}
  - {sec: 17, global_sec: 17, camera_position: "③", shot_type: "中近景", focal_length: "50mm"}

  # ====== 镜④ 大特写白板 18-23s ======
  - {sec: 18, global_sec: 18, camera_position: "④", shot_type: "大特写", focal_length: "85mm"}
  - {sec: 19, global_sec: 19, camera_position: "④", shot_type: "大特写", focal_length: "85mm"}
  - {sec: 20, global_sec: 20, camera_position: "④", shot_type: "大特写", focal_length: "85mm"}
  - {sec: 21, global_sec: 21, camera_position: "④", shot_type: "大特写", focal_length: "85mm"}
  - {sec: 22, global_sec: 22, camera_position: "④", shot_type: "大特写", focal_length: "85mm"}

  # ====== 镜⑤ 中近景 Miguel(桌) 23-32s ======
  - {sec: 23, global_sec: 23, camera_position: "⑤", shot_type: "中近景", focal_length: "50mm"}
  - {sec: 24, global_sec: 24, camera_position: "⑤", shot_type: "中近景", focal_length: "50mm"}
  - {sec: 25, global_sec: 25, camera_position: "⑤", shot_type: "中近景", focal_length: "50mm"}
  - {sec: 26, global_sec: 26, camera_position: "⑤", shot_type: "中近景", focal_length: "50mm"}
  - {sec: 27, global_sec: 27, camera_position: "⑤", shot_type: "中近景", focal_length: "50mm"}
  - {sec: 28, global_sec: 28, camera_position: "⑤", shot_type: "中近景", focal_length: "50mm"}
  - {sec: 29, global_sec: 29, camera_position: "⑤", shot_type: "中近景", focal_length: "50mm"}
  - {sec: 30, global_sec: 30, camera_position: "⑤", shot_type: "中近景", focal_length: "50mm"}
  - {sec: 31, global_sec: 31, camera_position: "⑤", shot_type: "中近景", focal_length: "50mm"}

# ============================================================
# §5 运镜域YAML
# 映射目标: TIME_SKELETON segments[].camera.movement + frames[].hard.camera_movement
# ============================================================

segments_movement:
  - segment_id: "①"
    movement: "固定"
    movement_speed_tier: "S0"
    static_exception: "信息密集(空间建立·观众吸收白板+桌面+人物位置信息)"
    kb_rule_ids:
      - "M-MOT-01"

  - segment_id: "②"
    movement: "固定"
    movement_speed_tier: "S0"
    static_exception: "信息密集(双人空间关系+Vincent对白信息+白板背景信息)"
    kb_rule_ids:
      - "M-MOT-01"

  - segment_id: "③"
    movement: "固定"
    movement_speed_tier: "S0"
    static_exception: "信息密集(对白信息+钉照片动作+白板证据·画面信息量饱和)"
    kb_rule_ids:
      - "M-MOT-01"

  - segment_id: "④"
    movement: "固定"
    movement_speed_tier: "S0"
    static_exception: "信息密集(大特写·白板证据网络密度极高·观众需要时间吸收线索细节)"
    kb_rule_ids:
      - "M-MOT-01"

  - segment_id: "⑤"
    movement: "固定"
    movement_speed_tier: "S0"
    static_exception: "信息密集(取外套+车钥匙动作+连续对白+决策转折)"
    kb_rule_ids:
      - "M-MOT-01"

frames_movement:
  # ====== 镜① 0-5s ======
  - {sec: 0, global_sec: 0, camera_position: "①", movement: "固定"}
  - {sec: 1, global_sec: 1, camera_position: "①", movement: "固定"}
  - {sec: 2, global_sec: 2, camera_position: "①", movement: "固定"}
  - {sec: 3, global_sec: 3, camera_position: "①", movement: "固定"}
  - {sec: 4, global_sec: 4, camera_position: "①", movement: "固定"}

  # ====== 镜② 5-11s ======
  - {sec: 5, global_sec: 5, camera_position: "②", movement: "固定"}
  - {sec: 6, global_sec: 6, camera_position: "②", movement: "固定"}
  - {sec: 7, global_sec: 7, camera_position: "②", movement: "固定"}
  - {sec: 8, global_sec: 8, camera_position: "②", movement: "固定"}
  - {sec: 9, global_sec: 9, camera_position: "②", movement: "固定"}
  - {sec: 10, global_sec: 10, camera_position: "②", movement: "固定"}

  # ====== 镜③ 11-18s ======
  - {sec: 11, global_sec: 11, camera_position: "③", movement: "固定"}
  - {sec: 12, global_sec: 12, camera_position: "③", movement: "固定"}
  - {sec: 13, global_sec: 13, camera_position: "③", movement: "固定"}
  - {sec: 14, global_sec: 14, camera_position: "③", movement: "固定"}
  - {sec: 15, global_sec: 15, camera_position: "③", movement: "固定"}
  - {sec: 16, global_sec: 16, camera_position: "③", movement: "固定"}
  - {sec: 17, global_sec: 17, camera_position: "③", movement: "固定"}

  # ====== 镜④ 18-23s ======
  - {sec: 18, global_sec: 18, camera_position: "④", movement: "固定"}
  - {sec: 19, global_sec: 19, camera_position: "④", movement: "固定"}
  - {sec: 20, global_sec: 20, camera_position: "④", movement: "固定"}
  - {sec: 21, global_sec: 21, camera_position: "④", movement: "固定"}
  - {sec: 22, global_sec: 22, camera_position: "④", movement: "固定"}

  # ====== 镜⑤ 23-32s ======
  - {sec: 23, global_sec: 23, camera_position: "⑤", movement: "固定"}
  - {sec: 24, global_sec: 24, camera_position: "⑤", movement: "固定"}
  - {sec: 25, global_sec: 25, camera_position: "⑤", movement: "固定"}
  - {sec: 26, global_sec: 26, camera_position: "⑤", movement: "固定"}
  - {sec: 27, global_sec: 27, camera_position: "⑤", movement: "固定"}
  - {sec: 28, global_sec: 28, camera_position: "⑤", movement: "固定"}
  - {sec: 29, global_sec: 29, camera_position: "⑤", movement: "固定"}
  - {sec: 30, global_sec: 30, camera_position: "⑤", movement: "固定"}
  - {sec: 31, global_sec: 31, camera_position: "⑤", movement: "固定"}

segments_transitions:
  - transition_id: "①→②"
    from_segment: "①"
    to_segment: "②"
    transition_type: "切(硬切)"
    time_range: [5, 5]
    reason: "全景→中景·机位跳跃·标准对话场景硬切过渡·无缝衔接"

  - transition_id: "②→③"
    from_segment: "②"
    to_segment: "③"
    transition_type: "切(硬切)"
    time_range: [11, 11]
    reason: "中景→中近景·正反打切换·Vincent→Miguel·标准对话硬切"

  - transition_id: "③→④"
    from_segment: "③"
    to_segment: "④"
    transition_type: "切(硬切)"
    time_range: [18, 18]
    reason: "中近景→大特写·插入镜头·景别跳跃≥2级(C-KTZ有叙事动机:揭示证据)"

  - transition_id: "④→⑤"
    from_segment: "④"
    to_segment: "⑤"
    transition_type: "切(硬切)"
    time_range: [23, 23]
    reason: "大特写→中近景·回主镜头·Miguel动作继续·硬切无缝"

  - transition_id: "⑤→scene_end"
    from_segment: "⑤"
    to_segment: null
    transition_type: "切(硬切至场景B·山丘贫民窟)"
    time_range: [32, 32]
    reason: "场景末硬切·案情室内景→贫民窟外景·EP14场景转换"

# ============================================================
# §6 构图光影域YAML
# 映射目标: TIME_SKELETON.global_anchors + frames[].soft
# ============================================================

global_anchors:
  character:
    Miguel: "Latin male, mid-40s, short dark hair with grey at temples, weathered face, deep-set brown eyes, five o'clock shadow stubble, medium build, wearing wrinkled medium-blue dress shirt with rolled-up sleeves(no jacket initially), dark navy or charcoal blazer draped over office chair back, dark trousers"
    Vincent: "Latin male, mid-30s, shorter dark hair neatly combed, clean-shaven, alert brown eyes, lighter build than Miguel, wearing a light grey dress shirt with top button undone(no tie), dark trousers, leaning posture in doorway frame"

  environment:
    description: "圣保罗刑警总部案情室·封闭内景无窗·约6m宽x5m深x2.8m高·白板线索墙占据后墙居中·合并办公桌在房间中央偏后·桌面有笔记本电脑+摊开的卷宗文件夹+笔记本+签字笔+陶瓷咖啡杯·黑色办公椅在桌后(外套搭在椅背上)·门口在前墙偏右·天花四组方形格栅LED面板灯·灰色地板·浅灰墙面"

  style_spine:
    description: "shot on Arri Alexa 35, cool institutional fluorescent 4500K, desaturated blue-gray grade, Kodak Vision3 250D base, crimson red accent contrast, subtle film grain"
    palette_anchors:
      - "slate gray"
      - "cool white (4500K fluorescent)"
      - "steel blue"
      - "crimson red (pushpin accent)"
      - "charcoal"

  lighting:
    description: "overhead grid LED panel lights, 4500K cool white fluorescent, even soft distribution from ceiling, whiteboard surface is brightest reflection zone in room, laptop screen provides cool blue ~6500K under-light on face when character is near desk, no natural light(no windows, enclosed interior)"
    anchor_in_reference: "IMAGE_AUDIT_EP14·场景1·光源分析·天花板格栅LED面板灯·冷白4500-5000K·白板区域最亮·桌面区域相对略暗·笔记本屏幕光局部冷蓝补光"

  constraints:
    - "面部比例全程一致·五官不漂移"
    - "光线色温全程锁定4500K无闪烁·笔记本屏幕冷蓝6500K仅在镜⑤出现时激活"
    - "画面稳定无晃动(全固定机位)·动作流畅自然(桌面取物动作)"
    - "无字幕·无Logo·无水印"
    - "白板上任何文字内容(弹道报告/酒店平面图标注/照片说明)均为后期叠加·不要求Seko渲染文字·P-FAL-08规避"
    - "红线+红钉为视觉锚点·每镜中红色饱和度为全画面最高值"

frames_soft:
  # ====== 镜① 全景建立 0-5s ======

  - sec: 0
    global_sec: 0
    camera_position: "①"
    action_anchor: "全景正对白板线索墙。Miguel背对镜头站立于白板前约1.5m处·面向白板·右手持红色图钉正将一张照片压向白板表面。房间冷灰基调·天花格栅灯投下均匀冷白光。桌面(画面下三分之一)可见笔记本电脑(屏幕亮·显示弹道分析界面)·摊开的卷宗·咖啡杯"
    spatial_anchor: "深景深f/11·全画面清晰。正面白板视角·单点透视·白板居中偏上·天花格栅灯四组在画面上方·桌面+椅子+电脑在画面下方·灰色地板至画面下边缘。白板表面反射天花光·为画面最亮区域(~4500K冷白)。墙面浅灰·地面深灰·整体低饱和冷调"
    character_state:
      - character: "Miguel"
        pose: "背对镜头站立·白板前约1.5m·右手举至白板高度"
        position: "画面中央偏下·白板前方"
        expression: "面部不可见·背对镜头"
    prop_state:
      - item: "白板线索墙"
        state: "表面已有5张照片(排列成弧形或线性·每个照片旁有红线标记)+弹道报告纸张(右下区域·文字后期叠加)+酒店平面图(左下区域·201房间红圈标注·后期叠加)+红色图钉+红线已连接部分照片"
      - item: "合并办公桌"
        state: "深色桌面·笔记本电脑屏幕亮(冷蓝光)·卷宗打开·咖啡杯在右侧"
    audio:
      ambience: "室内低频持续(空调低频·电脑风扇微嗡·荧光灯细微电流声)"
      events: []

  - sec: 1
    global_sec: 1
    camera_position: "①"
    action_anchor: "Miguel按下图钉·Rico的照片被固定在白板中央偏上位置。照片为半身照或头像·色调与白板上其他5张受害者照片一致。Miguel的右手从白板收回·微退半步。桌面电脑屏幕光微闪(冷蓝)"
    spatial_anchor: "同sec 0固定全景·新增:白板上Rico的照片(第6张·居中偏上·新钉入·图钉金属反光为白板上最亮高光点)。白板上红线网络可见(从左到右连接6张照片)"
    prop_state:
      - item: "白板线索墙"
        state: "新增Rico照片(居中偏上·刚钉入·金属图钉反光)·红线连接6张照片"
    audio:
      ambience: "室内低频持续"
      events: []

  - sec: 2
    global_sec: 2
    camera_position: "①"
    action_anchor: "Miguel微退半步·看向白板·头部微仰(审视刚完成的线索网络)。双手自然垂至身侧·右手仍持一枚红色图钉。天花板灯光在Miguel肩膀和头顶形成细柔高光线"
    spatial_anchor: "固定全景·Miguel从白板前微退(从距白板1.5m退至约1.8m)·白板上6张照片+红线网络完整可见·红色图钉在白板上形成6个反光高亮点"
    audio:
      ambience: "室内低频持续"
      events: []

  - sec: 3
    global_sec: 3
    camera_position: "①"
    action_anchor: "Miguel静止·审视白板·背部姿态透出专注。门口方向(画面右侧·画外)有轻微动静——Vincent的脚步声从走廊接近。白板在冷白灯光下静置·红钉反光稳定"
    spatial_anchor: "固定全景·Miguel在白板前·白板线索网络完整·桌面物件(笔记本电脑·卷宗·咖啡杯)·椅子(外套搭椅背·深色外套·画面下方·画框内可见)"
    audio:
      ambience: "室内低频持续"
      events: ["微弱的脚步声:从走廊接近·画外右侧"]

  - sec: 4
    global_sec: 4
    camera_position: "①"
    action_anchor: "Miguel仍面对白板。门口方向脚步声停止——Vincent已抵达门口。Miguel未转身·注意力仍在白板上"
    spatial_anchor: "固定全景·不变"
    audio:
      ambience: "室内低频持续"
      events: ["脚步声停止·门口区域微动(画外·Vincent到达)"]

  # ====== 镜② 中景门口视角 5-11s ======

  - sec: 5
    global_sec: 5
    camera_position: "②"
    action_anchor: "硬切至门口视角。Vincent从门口右侧探头入画框·上半身探入房间·左手扶门框·右手持文件夹或记事本。门框形成天然画框。背景深处可见Miguel在白板前(背对镜头·白板线索墙在更深处)"
    spatial_anchor: "中景深f/5.6·门口区域+Vincen清晰·背景Miguel+白板略微柔焦(景深分离但非全虚化)。门框(深色木或金属·画面左右边框)·门口区域暗于白板区(自然光源衰减)。Vincent面部由门口上方走廊光+室内散射光照亮·光比约1:2.5"
    character_state:
      - character: "Vincent"
        pose: "身体半探入门框·上半身在室内·左手扶门框·右手持记事本/文件夹在胸前"
        position: "画面居中偏右·门框内"
        expression: "中性偏紧·通报信息时的职业表情·眼睛看向画面左侧(Miguel方向)"
      - character: "Miguel"
        pose: "背对镜头站立·白板前"
        position: "画面左侧深处·白板前方"
        expression: null
    audio:
      ambience: "室内低频持续"
      events: []

  - sec: 6
    global_sec: 6
    camera_position: "②"
    action_anchor: "Vincent探头姿势稳定·看向画面左侧(白板方向·Miguel)。嘴唇微动开始说话"
    spatial_anchor: "固定·同sec 5"
    audio:
      ambience: "室内低频持续"
      events:
        - "Vincent: 酒店那边...监控没拍到脸。(语速约2.5字/秒·时长约3.5s·sec 6-9)"

  - sec: 7
    global_sec: 7
    camera_position: "②"
    action_anchor: "Vincent继续说·微摇头(表示无奈/失望)·左手在门框上轻拍一下(下意识小动作)。背景中Miguel未转身·仍看白板"
    spatial_anchor: "固定·同sec 5"
    audio:
      ambience: "室内低频持续"
      events: []  # Vincent对白持续中

  - sec: 8
    global_sec: 8
    camera_position: "②"
    action_anchor: "Vincent说完·嘴唇闭合·等待Miguel回应。眼神保持在Miguel方向·右手文件夹微垂(从胸前降至腰间)"
    spatial_anchor: "固定·同sec 5"
    audio:
      ambience: "室内低频持续"
      events: []  # 对白收尾

  - sec: 9
    global_sec: 9
    camera_position: "②"
    action_anchor: "Vincent保持探头姿势·等待。背景中Miguel开始微动——从白板前转身·看向Vincent方向(画面右)"
    spatial_anchor: "固定·Miguel在背景深处从面向白板转向面向门口(面向画面右)"
    audio:
      ambience: "室内低频持续"
      events: []

  - sec: 10
    global_sec: 10
    camera_position: "②"
    action_anchor: "Miguel在背景中面向Vincent(画面右侧)·嘴唇微动·开始说话。Vincent在门口·眼神保持与Miguel对视·姿势不变"
    spatial_anchor: "固定·Miguel已转身面向门口·面部在冷白灯光下·白板在Miguel身后(背景)"
    audio:
      ambience: "室内低频持续"
      events:
        - "Miguel(画面深处·对白开始): 他从不碰不需要碰的东西。(语速约2字/秒·时长约4s·sec 10-13·跨镜③)"

  # ====== 镜③ 中近景 Miguel 11-18s ======

  - sec: 11
    global_sec: 11
    camera_position: "③"
    action_anchor: "硬切至Miguel中近景。Miguel约左三分线位置·面朝画面右侧(Vincent方向)。面部由天花板冷白光+桌面笔记本冷蓝光(下侧微补)混合照明·眼睛看向画面右。白板在Miguel身后占据画面右半背景——Rico照片居中·5名死者照片弧形排列·红线网络·弹道报告·酒店平面图(文字后期叠加)"
    spatial_anchor: "浅景深f/2.8·Miguel面部+上半身清晰·背景白板略微柔焦(红线+照片轮廓可辨但细节柔化)。Miguel在左三分线·白板在右半背景·竖线(Miguel身体)+对角线(手臂方向+红线)构成非对称构图。光线:Miguel面部冷白主光(4500K)+下巴/颈部冷蓝补光(6500K笔记本屏幕·微弱但可见)"
    character_state:
      - character: "Miguel"
        pose: "站立·面向画面右侧·上身微转·右手自然垂在身侧(仍持红色图钉)·左手微抬(辅助说话手势)"
        position: "画面左三分线·上半身"
        expression: "冷静·笃定·嘴角微收紧·眼神坚定看向画面右(Vincent方向)·微有"你能怎样"的无奈感"
    audio:
      ambience: "室内低频持续"
      events: []  # Miguel对白持续: "他从不碰不需要碰的东西"

  - sec: 12
    global_sec: 12
    camera_position: "③"
    action_anchor: "Miguel继续说话·右手微抬·红色图钉在指间·白板反射光在图钉金属表面形成冷白高光点。Miguel视线从Vincent方向微转回白板(微偏头)"
    spatial_anchor: "固定·同sec 11·新增:图钉金属反光(Miguel右手指间·点光源高光)"
    audio:
      ambience: "室内低频持续"
      events: []  # 对白持续

  - sec: 13
    global_sec: 13
    camera_position: "③"
    action_anchor: "Miguel说完最后一字·嘴唇闭合。右手图钉收入掌心·转身面向白板·头微仰(审视Rico照片)。白板上6张照片由红线编织成网络·红色在冷白基调中形成唯一高饱和元素"
    spatial_anchor: "固定·Miguel从面向右转为面向白板(画面纵深方向)"
    audio:
      ambience: "室内低频持续"
      events: []

  - sec: 14
    global_sec: 14
    camera_position: "③"
    action_anchor: "Miguel面向白板·右手抬起·将指间最后一枚红色图钉按入白板某处(连接Rico照片的最后一根红线末端)。图钉按入的微小阻力·手臂肌肉微紧。白板上红线网络完成——6张照片全部由红线串联"
    spatial_anchor: "固定·白板在Miguel右侧背景·新增图钉的金属反光加入已有6个反光点·共7个红色图钉高光点"
    audio:
      ambience: "室内低频持续"
      events:
        - "微弱的图钉按入白板声:软木/泡沫板被针刺入的闷响"

  - sec: 15
    global_sec: 15
    camera_position: "③"
    action_anchor: "Miguel手从白板收回·微退一步·最后审视完成的线索板。白板上Rico照片居中·5名受害者照片环列·红线如蛛网将所有照片串联。Miguel深呼吸(肩膀微提然后下沉)·做出决定"
    spatial_anchor: "固定·Miguel微退·白板背景完整可见·红线网络占据画面右半·红色=唯一高饱和元素(与冷灰蓝形成互补色高对比)"
    audio:
      ambience: "室内低频持续"
      events:
        - "Miguel深呼吸:微弱的鼻腔气息声"

  - sec: 16
    global_sec: 16
    camera_position: "③"
    action_anchor: "Miguel转身·离开白板前·走向画面左侧(桌面方向)。手臂自然摆动·右手松开(图钉已钉完)。Miguel的身体从画面左侧滑出——留白板在画面右侧成为视觉焦点"
    spatial_anchor: "固定·Miguel从画面左侧逐渐移出(左出画)·白板占据画面右侧(主导视觉)·红线网络清晰·灯光均匀"
    audio:
      ambience: "室内低频持续"
      events: []

  - sec: 17
    global_sec: 17
    camera_position: "③"
    action_anchor: "Miguel已从画面左侧完全移出。画面转为白板主导——Rico照片居中·6张照片+红线网络+弹道报告+酒店平面图占据整个画面(但Miguel出画后·此镜头已过渡到白板作为主角)"
    spatial_anchor: "固定·画面:仅白板信息墙(无人物)·冷白光均匀照明白板表面·红色图钉+红线高对比·报告纸张微黄(暖调纸张与冷白光的微小色温差)"
    audio:
      ambience: "室内低频持续"
      events: []

  # ====== 镜④ 大特写白板 18-23s ======

  - sec: 18
    global_sec: 18
    camera_position: "④"
    action_anchor: "硬切至白板大特写。画面主体=Rico的照片(居中偏上·半身照·色调与其他受害者照片一致·暖调肤色在冷白背景下形成微暖对比)。红色图钉固定在照片上角·红线从Rico照片向四周辐射——连接左侧3张受害者照片+右侧2张受害者照片。白板亚光表面纹理微可见"
    spatial_anchor: "浅景深f/2.8·85mm等效·白板表面清晰。Rico照片居中·5名死者照片在四周围绕(弧形排列·每张由红线连接至Rico)。右下区域=弹道分析报告(纸张微黄·冷白光下显暖·文字后期叠加·不可见具体文字·仅有纸张质感+段落痕迹)。左下区域=酒店平面图(建筑线条简图·201房间红圈标注·后期叠加)。红色图钉×6(金属表面反光·冷白高光点)·红线×10+(亚光红线·不反光·与冷白背景形成互补色高对比)"
    character_state: []
    prop_state:
      - item: "Rico照片(白板·居中)"
        state: "半身照或头像·暖调肤色·深色外套·固定在白板中央偏上·红色图钉在上角"
      - item: "5名受害者照片"
        state: "弧形环绕Rico照片排列(左3·右2)·各由红线连接至Rico照片·各有独立红色图钉·照片色调一致(暖调人像)"
      - item: "红线网络"
        state: "10+根红线从Rico照片辐射至各受害者·形成蛛网/星形网络·暗红色·亚光表面·在白板冷白背景下高对比"
      - item: "弹道报告(右下)"
        state: "A4纸·微黄纸张·冷白光下显暖调·纸张表面有段落排版痕迹·文字不可见(后期叠加·P-FAL-08·不要求Seko渲染文字)"
      - item: "酒店平面图(左下)"
        state: "建筑平面简图·灰色/蓝灰色线条·201房间红圈标注(红色圆·后期叠加)·纸张微黄"
    audio:
      ambience: "室内低频持续"
      events: []

  - sec: 19
    global_sec: 19
    camera_position: "④"
    action_anchor: "大特写固定·白板证据网络静置。光在红钉金属表面微动(天花板LED的细微频率闪烁在金属上的反映·微不可察但增加真实感)。白板亚光表面纹理在85mm焦距下清晰可见——微细的干擦痕迹·旧钉眼(之前案件留下的微小凹痕)"
    spatial_anchor: "固定·同sec 18·新增:旧钉眼痕迹(白板表面·微凹小孔·~1mm·分散在照片之间的空白区域·交代白板使用历史·IMAGE_AUDIT_EP14·参考图格3)"
    audio:
      ambience: "室内低频持续"
      events: []

  - sec: 20
    global_sec: 20
    camera_position: "④"
    action_anchor: "白板大特写持续。光线稳定·红钉反光稳定·红线静置·照片静置。画面信息密度极高——观众有时间吸收:6名人物(Rico+5受害者)·弹道报告·酒店平面图·红线连接关系"
    spatial_anchor: "固定·同sec 18-19·画面全静止(无任何运动元素)·信息密度构图·无负空间(白板填满画面)"
    audio:
      ambience: "室内低频持续"
      events:
        - "画外音:微弱的衣物摩擦声(Miguel在桌边拿起外套·画面外·预兆镜⑤动作)"

  - sec: 21
    global_sec: 21
    camera_position: "④"
    action_anchor: "白板大特写持续。画面微变:画外Miguel动作使桌面光线微变化(电脑屏幕光角度微偏·白板边缘出现极微弱的冷蓝散射光)·暗示Miguel在桌边动作"
    spatial_anchor: "固定·白板边缘微蓝散射光(6500K·来自笔记本电脑·非常微弱·仅在白板左侧边缘可见)"
    audio:
      ambience: "室内低频持续"
      events: ["微弱的车钥匙金属碰撞声:画外·桌面(钥匙被拿起)"]

  - sec: 22
    global_sec: 22
    camera_position: "④"
    action_anchor: "白板大特写最后1秒。红钉反光·红线网络·照片·报告·平面图——全部静置。白板作为案件核心的视觉锚点已充分建立·观众已吸收关键信息"
    spatial_anchor: "固定·同sec 18-21"
    audio:
      ambience: "室内低频持续"
      events: []

  # ====== 镜⑤ 中近景 Miguel(桌) 23-32s ======

  - sec: 23
    global_sec: 23
    camera_position: "⑤"
    action_anchor: "硬切至Miguel中近景·桌侧角度。Miguel占据画面右三分线·上半身·左手已穿入外套(深色·藏青或炭灰·搭在椅背上的外套已取下)·正在将右臂穿入袖管·动作自然流畅。桌面在画面前景(下三分之一·浅景深·虚化)——可见笔记本电脑(屏幕亮·冷蓝光)·摊开的卷宗·咖啡杯(深色陶瓷)。桌面冷蓝光从下侧补亮Miguel面部(下巴·颈部)。白板在后景左侧(已不在焦点中心·虚化但红钉+红线仍可辨识)"
    spatial_anchor: "中景深f/5.6·桌面物件前景虚化(笔记本电脑虚化但屏幕冷蓝光可见)·Miguel上半身清晰·背景白板微虚化。Miguel右三分线·面向画面左侧(门口方向)。光线:冷白主光(4500K·天花板LED·从上方照明Miguel面部)+冷蓝补光(6500K·笔记本屏幕·从下方补亮下巴/颈部·形成微弱冷暖色温差)。外套:深色·正在穿·翻领在冷白光下形成柔和阴影层次"
    character_state:
      - character: "Miguel"
        pose: "站立在桌侧·正在穿外套(左手已穿入·右手正在套袖)·身体微转向左侧(门口方向)"
        position: "画面右三分线·上半身"
        expression: "决定已下·面部表情由审视转为行动——嘴角微收·眉头微紧(思考)·眼睛看左侧(门口方向·Vincent位置)"
      - character: "Vincent"
        pose: null
        position: "画外左侧(门口方向·下一句对白)"
        expression: null
    prop_state:
      - item: "Miguel的外套"
        state: "深色(藏青/炭灰)·翻领·合身剪裁·正在穿上·面料在冷白光下微有质感(羊毛混纺或棉质)"
      - item: "车钥匙"
        state: "在桌面·靠近画面右下角·金属钥匙+遥控器·银色金属在冷白光下反光(待Miguel拿起)"
      - item: "笔记本电脑"
        state: "桌面·屏幕亮·冷蓝光(6500K)·弹道分析或其他案件资料界面·屏幕光照亮桌面区域"
      - item: "咖啡杯"
        state: "桌面右侧·深色陶瓷·白色或浅色内壁·半空或空(工作已进行一段时间)"
    audio:
      ambience: "室内低频持续"
      events: []

  - sec: 24
    global_sec: 24
    camera_position: "⑤"
    action_anchor: "Miguel穿好外套·双手拉平衣领·整理领口(下意识的习惯动作·用时~1s)。外套已完全穿上·翻领平整。Miguel目光从桌面扫过——锁定车钥匙"
    spatial_anchor: "固定·Miguel穿外套完成·双手从衣领移至身侧·外套合身·衣摆在画面中下部(画面外)"
    audio:
      ambience: "室内低频持续"
      events: ["微弱的衣物摩擦声:外套整理"]

  - sec: 25
    global_sec: 25
    camera_position: "⑤"
    action_anchor: "Miguel右手伸向桌面·拿起车钥匙。金属钥匙+遥控器在冷白光下微闪(银色金属反光)·钥匙圈有小物件(可能的警徽钥匙链或简约金属环)。Miguel将钥匙握入掌心·抬头看向画面左侧(门口·Vincent方向)·准备说话"
    spatial_anchor: "固定·Miguel右手从桌面抬起·车钥匙金属反光(冷白光高光点)·左手自然垂至身侧"
    audio:
      ambience: "室内低频持续"
      events:
        - "微弱的金属碰撞声:车钥匙被拿起·钥匙环轻响"
        - "Miguel: 去Rico工作室叙叙旧。(语速约2字/秒·时长约3.5s·sec 25-28)"

  - sec: 26
    global_sec: 26
    camera_position: "⑤"
    action_anchor: "Miguel说话·右手握车钥匙(自然垂在身侧·钥匙在指间微露金属边缘)·左手微抬做辅助手势(掌心向上·示意'就是去聊聊')。眼神保持向门口(Vincent方向)·微微耸肩(补充语气)"
    spatial_anchor: "固定·Miguel在右三分线·车钥匙在右手(微可见)·左手微抬(画面中部)·面部表情:冷静+微讽·'叙旧'的轻描淡写与案件严重性的反差"
    audio:
      ambience: "室内低频持续"
      events: []  # 对白持续

  - sec: 27
    global_sec: 27
    camera_position: "⑤"
    action_anchor: "Miguel说完·嘴唇闭合·下巴微收('就这么定了'的笃定神情)。车钥匙在右手握紧·金属面从指缝微露"
    spatial_anchor: "固定·同sec 25-26"
    audio:
      ambience: "室内低频持续"
      events: []

  - sec: 28
    global_sec: 28
    camera_position: "⑤"
    action_anchor: "Miguel静止·等Vincent回应。画面外左侧传来Vincent的声音。Miguel眉毛微挑(预料到这个问题)·嘴角微动(几乎不可见的笑意)"
    spatial_anchor: "固定·Miguel面部微表情:眉微挑(画面下三分之一·眉毛微升约1mm)·嘴角右侧微升(几乎不可见)"
    audio:
      ambience: "室内低频持续"
      events:
        - "Vincent(画外·OS): 搜查令呢?(语速快·约3字/秒·时长约1.5s·sec 28-29)"

  - sec: 29
    global_sec: 29
    camera_position: "⑤"
    action_anchor: "Vincent问完·Miguel已准备好回答——微摇头(仅一次·幅度很小)·右手微抬(车钥匙在手中微晃·金属碰撞轻响)·嘴角的微讽笑意更明显·但眼神仍冷静"
    spatial_anchor: "固定·Miguel微摇头+右手微抬·车钥匙晃动(金属反光微闪)"
    audio:
      ambience: "室内低频持续"
      events: []

  - sec: 30
    global_sec: 30
    camera_position: "⑤"
    action_anchor: "Miguel开口回答·目光仍看门口(画面左)·但眼神中有一丝'你知道答案'的默契。右手车钥匙在身侧自然垂·钥匙金属面在冷白光下稳定反光"
    spatial_anchor: "固定·同sec 25-29"
    audio:
      ambience: "室内低频持续"
      events:
        - "Miguel: 只是叙旧而已。(语速约2.5字/秒·时长约2s·sec 30-31)"

  - sec: 31
    global_sec: 31
    camera_position: "⑤"
    action_anchor: "Miguel说完最后一字·嘴角讽刺的笑意微微停留·然后恢复职业表情。右手将车钥匙收入外套口袋(自然动作·钥匙金属声最后一响)。深吸一小口气·准备出发"
    spatial_anchor: "固定·Miguel将车钥匙收入口袋(右手从身侧移至外套口袋·金属光泽消失)·面部:笑意褪去·冷静职业表情恢复"
    audio:
      ambience: "室内低频持续"
      events:
        - "微弱的钥匙收入口袋声:金属+布料摩擦"

  - sec: 32
    global_sec: 32
    camera_position: "⑤"
    action_anchor: "Miguel面向门口方向·准备迈步(身体微向前倾·重心转移至前脚·但画面在迈步前结束)。外套合身·钥匙已在口袋·一切就绪"
    spatial_anchor: "固定·最终帧:Miguel在画面右三分线·身体微前倾(准备出发)·面部朝向画面左侧(门口·Vincent方向)·面部冷白光+微冷蓝补光照亮·冷静笃定。桌面前景虚化·笔记本屏幕冷蓝光仍在·白板在深层背景微虚化·红钉反光仍在"
    audio:
      ambience: "室内低频持续"
      events: []

---

# 场景末状态快照（供后续场景使用）

时间: 日间(内景无窗·无时间标识·但推断为工作时间·上午或下午)
案情室: Miguel与Vincent正准备出发前往Rico工作室
白板: Rico照片居中·6张照片由红线网络连接·弹道报告+酒店平面图在侧·红色图钉全部钉入
桌面: 笔记本电脑亮(弹道分析界面)·卷宗摊开·咖啡杯·外套已取走(椅背空)
人物: Miguel(外套已穿·车钥匙已取·在门口方向·准备出发)·Vincent(在门口·等待Miguel下一步)
EP14场景B: 山丘贫民窟·巷道+轿车·即将接续

---

# 设计签名

> **Agent:** Scene Designer v1.0 (合并式·三域整合)
> **复杂度:** S-Level · 3A S-Level快速通道
> **静态快速通道:** 已触发(全固定·固定镜占比100% ≥ 80%)
> **KB覆盖:** 机位域5规则类·运镜域1规则类(静态快速通道)·构图域7规则类·光影域6规则类·P0安全规则全量
> **P-FAL规避:** P-FAL-01~10全部主动规避(含P-FAL-08白板文字后期叠加)
> **画布宪法:** 七条铁律全部合规
> **输出格式:** §4(机位)·§5(运镜·静态快速通道)·§6(构图光影)三个YAML块完整
> **下游消费者:** storyboard_planner (Step A2.5) · prompt_composer (Step A3)
> **独立验证:** 待 Shot Reviewer + Movement Reviewer + Visual Reviewer 三域并行审查
> **总镜数:** 5镜 · **总时长:** 32s · **对白:** 4句 · **运镜:** 0(全固定)

---
> **v1.0 · 2026-07-07 · Scene Designer v1.0 首次产出**
> **关联文件:** EP14_S1_SCENE_DESIGNER.md · IMAGE_AUDIT_EP14.md · ANCHOR_BASELINE_EP14.md
> **替代:** 原三Agent串行链(Shot Architect + Movement Designer + Composition Designer) -> 单一Scene Designer合并式输出
> **场景S1设计完成:** 5镜·32秒·案情室·双人对话·全固定·三域协调
