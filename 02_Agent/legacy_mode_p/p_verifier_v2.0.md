# P-Verifier v2.0 — 方案二 · 独立专项专家验证架构

> **定位:** MODE:P管道统一验证层。7个独立专项专家各自验证一个维度，全部引用TIME_SKELETON作为单一真源。
> **核心变化 (v1.0→v2.0):** 13Agent→7专家 · 消除57%冗余 · Gate 0只运行一次 · 所有专家共享TIME_SKELETON
> **设计依据:** 验证层重叠矩阵分析 · TIME_SKELETON_spec.md · 画布宪法第七条(独立验证)
> **版本:** v2.0 · 2026-07-07
> **被调用者:** dispatcher_v5.0.md MODE:P · Step 9 (全场景完成后)

---

# §0 架构变化总览

```
v1.0 (当前)                        v2.0 (方案二)
════════════                        ════════════
13个Agent                           7个独立专项专家
├─ P-Verifier (编排)                ├─ Gate 0 Scanner (确定性规则·一次)
│  ├─ Gate 0 (13条)                 ├─ Spatial-Temporal Expert
│  ├─ Shot Reviewer                 ├─ Visual Anchor Expert
│  ├─ Movement Reviewer             ├─ Object Existence Expert
│  ├─ Visual Reviewer               ├─ Cross-Scene Continuity Expert
│  └─ Constraint Reviewer           ├─ Storyboard-Prompt Alignment Expert
├─ Scene Anchor Auditor             ├─ Render Packager (仅格式化·无R00)
├─ Scene Design Auditor             └─ Render Verifier (渲染后)
├─ Scene Script Auditor
├─ Storyboard Auditor
├─ Cross-Scene Continuity Auditor
├─ Object Existence Verifier
├─ Render Packager (含R00)
└─ Render Verifier

冗余率: ~57%                         冗余率: ~0%
确定性规则被检查4次                   确定性规则只检查1次
时间信息需要手动对照                   全部引用TIME_SKELETON自动对齐
```

---

# §1 七个独立专项专家

## Expert 1: Gate 0 Scanner (确定性规则扫描)

> **定位:** 所有可正则/数值检查的规则集中在此。零模型判断·100%准确率·只运行一次。
> **合并来源:** P-Verifier Gate 0 R01-R13 + Constraint Reviewer C01-C20 + Render Packager R00 + Scene Script Auditor B01-B05

```
输入:
  ├─ 全部场景 VIDEO_PROMPT_[场景].md
  ├─ 全部场景 TIME_SKELETON (从 PLAN_[场景].md §B)
  └─ P-CONSTITUTION.md §5

检查项 (一次扫描·全部场景):

R01 时长硬约束:    任一段>15.0秒 → 🛑 (数值比较)
R02 过程动词:      段首含"正在/刚/已/开始/持续" → 🛑 (正则)
R03 时间模糊词:    含"缓缓/渐渐/慢慢/逐渐/徐徐/冉冉" → 🛑 (正则)
R04 跨镜引用:      含"同上/参考上镜/如前/同镜#/与镜#" → 🛑 (正则)
R05 参考图引用:    @图片格式异常或引用不存在 → 🛑 (模式匹配)
R06 禁止清单模糊:  禁止项含模糊词 → 🛑 (正则)
R07 工程符号泄漏:  含v_dolly/ω_pan/f/数字/°/7-DOF/D-TRI-/M-MOT-/C-COM-/P-REN-/P-FAL- → 🛑 (正则)
R08 段结构完整:    缺@声明区/Subject/Action/Camera/Style/Constraints/【禁止】 → 🛑
R09 负向词:        【生成指令】正文含"不要/避免/禁止/不能/不应/勿/别" → 🛑 (正则)
R10 模型名泄漏:    含"即梦/海螺/Kling/Vidu/Seedance/可灵/万相/Runway/Pika" → 🛑 (正则)
R11 @引用声明:     @图片引用后无用途描述(≥5汉字) → 🛑 (模式匹配)
R12 骨架顺序:      不符Character→Action→Camera→Style→Constraints顺序 → 🛑
R13 骨架逐字一致性: Character Anchor/Style Spine/Lighting Anchor跨镜逐字对比 → 🛑

🆕 R14 TIME_SKELETON对齐:  视频提示词每秒描述是否存在对应的TIME_SKELETON.frames[N] → ⚠️
🆕 R15 逐秒格号完整性:      TIME_SKELETON.frames 是否有跳秒(sec序列不连续) → 🛑

输出: GATE0_REPORT.md (通过/阻断·逐项明细)
门禁: 任一🛑 → 阻断·打回prompt_composer修复·上限1轮
```

## Expert 2: Spatial-Temporal Continuity Expert (空间-时间连续性)

> **定位:** 验证摄影机位置、180度线、视线、空间可行性在TIME_SKELETON时间轴上的一致性。
> **合并来源:** Shot Reviewer + Movement Reviewer(空间部分) + Scene Design Auditor(空间部分)

```
输入:
  ├─ TIME_SKELETON (全部场景)
  ├─ 空间地图文件
  ├─ 参考图
  └─ 三Agent设计报告

验证维度:

2A 180度轴线:
  逐segment检查: 摄影机位置是否跨越关系线?
  对照 TIME_SKELETON.segments[].camera.angle 验证

2B 视线匹配:
  逐帧检查: frames[N].soft.character_state.position 与 frames[N+1] 是否视线连贯?
  多角色同框时视线方向是否交汇?

2C 空间可达性:
  每个 segment 的 camera 位置在空间地图"可拍摄区域"内?
  transition.path 是否穿过禁入区/墙壁/家具?
  验证 TIME_SKELETON.segments[].transition.path 的空间可行性

2D 人物占位:
  逐帧检查: frames[N].soft.character_state.position 在空间地图"人物可放置区域"内?
  多角色同框时是否占位冲突(同一坐标)?
  人群场景: 标注人数 ≤ 空间容量?

2E 运镜空间可行性:
  窄空间(<3m深)横移 → ⚠️ P-FAL-06规避检查
  运镜路径物理约束: 摄影机不穿墙·不悬空

输出: SPATIAL_AUDIT.md (逐segment·逐帧违规清单)
裁决: P0违规→🛑 · P1违规→⚠️
```

## Expert 3: Visual Anchor Expert (视觉锚点)

> **定位:** 验证参考图锚定、光源锚点、色彩一致性——所有"画面中可见的视觉元素"是否可追溯。
> **合并来源:** Visual Reviewer + Constraint Reviewer(视觉部分) + Scene Design Auditor(锚定部分) + Storyboard Auditor(锚定维度)

```
输入:
  ├─ TIME_SKELETON (全部场景)
  ├─ IMAGE_AUDIT (参考图盘点)
  ├─ 参考图
  └─ P-CONSTITUTION.md §1(画面可见性) §3(空间锚定)

验证维度:

3A 参考图锚定:
  场景结构元素(墙/门/窗/固定家具/固定灯具)在参考图中存在?
  对照 TIME_SKELETON.global_anchors.environment 逐元素验证
  人物/动态道具不在参考图中 → ✅ (由剧本驱动·不要求参考图有人)

3B 光源锚点 (铁律#4):
  TIME_SKELETON.global_anchors.lighting 中的每个光源有物理锚点?
  自然光 → 窗户/门口可追溯参考图格位?
  人工光 → 灯具在参考图中可见?
  ❌ "感觉有一束光" → 🛑

3C 色彩一致性:
  色温K值跨镜一致? (对照 global_anchors.lighting)
  同一角色服装颜色跨镜一致? (对照 global_anchors.character)
  场景色调与参考图一致?

3D 画面可见性 (铁律#1):
  视频提示词每句主语是画面内可见物?
  画面外声音是否误入画面描述? (应在音轨中)
  文学修饰是否已转化为画面描述?

3E 构图参数:
  景别递进合理(广→中→近)?
  TIME_SKELETON.segments 间景别跳跃 ≥2档 → ⚠️

输出: VISUAL_AUDIT.md
裁决: P0违规→🛑 · P1-P2违规→⚠️
```

## Expert 4: Object Existence Expert (物体存在链)

> **定位:** 画面中每个物品必须有🅰🅱🅲来源。道具状态变化必须有中间帧。**这是唯一的道具权威检查点。**
> **合并来源:** Object Existence Verifier (保持·其他Agent的道具检查全部引用此处)
> **变化:** Constraint C12 / Scene Script E03 / Scene Anchor C / Cross-Scene D 的道具检查不再独立执行

```
输入:
  ├─ OBJECT_TIMELINE_[剧本名].md
  ├─ TIME_SKELETON (全部场景·逐帧prop_state)
  ├─ 全部 VIDEO_PROMPT_[场景].md
  ├─ 参考图 + 人物表
  └─ P-CONSTITUTION.md §6

验证维度:

V1 存在性验证:  TIME_SKELETON.frames[].soft.prop_state 中每物 ↔ OBJ_TIMELINE存在来源
V2 变化链验证:  物体状态变化的相邻帧之间是否有中间帧描述?
                用 TIME_SKELETON.frames[N].prop_state → frames[N+1].prop_state 逐帧追踪
V3 消失重现:    物体从 frames[N] 消失 → frames[M] 重现·中间帧无携带/拿取 → 🛑
V4 最终一致性:  frames[-1].prop_state 终态 ↔ OBJ_TIMELINE终态一致?
V5 凭空出现:    TIME_SKELETON 中的物品在 OBJ_TIMELINE 中不存在 → 🛑

输出: OBJECT_VERIFIER_REPORT.md (P0-P2分级)
裁决: P0/P1→🛑打回 · 上限2轮
```

## Expert 5: Cross-Scene Continuity Expert (跨场景连续性)

> **定位:** 场景A末帧 → 场景B首帧的锚点继承验证。全片级别。
> **合并来源:** Scene Anchor Auditor(阶段1+2) + Cross-Scene Continuity Auditor
> **变化:** 不再分"阶段1(逐对)"和"全片扫描"——在全部场景完成后一次性验证所有场景对。

```
输入:
  ├─ 全部 TIME_SKELETON (每场景末帧 + 首帧)
  ├─ 全部 VIDEO_PROMPT_[场景].md
  └─ 剧本全文

验证维度:

5A 角色状态锚点链:
  场景A TIME_SKELETON.frames[-1].character_state
  → 场景B TIME_SKELETON.frames[0].character_state
  角色外观/服装/姿态/位置是否连续?
  变化必须有跨场景事件锚点(换装/受伤/时间跳跃)

5B 时间线连续性:
  场景A→B的时间差(剧本标注或推断)
  TIME_SKELETON.scene_time_of_day 跨场景是否连贯?
  白天→黑夜 无过渡镜+时间差≤5秒 → 🛑

5C 道具全集追踪:
  场景A末帧 prop_state → 场景B首帧 prop_state
  道具是否延续? 消失/新增是否有依据?
  (基础检查·详细验证委托Expert 4)

5D 空间状态继承:
  场景A末帧 spatial_anchor
  → 场景B首帧 spatial_anchor
  同一场景重返时空间状态是否一致?
  (门/窗/灯的状态·家具位移)

5E 转场衔接:
  场景A末段 transition 终点状态
  → 场景B首段起点状态
  白→暗跳跃? 音频硬切→立即起? → ⚠️

输出: CROSS_SCENE_AUDIT.md
裁决: P0→🛑 · P1→⚠️
```

## Expert 6: Storyboard-Prompt Alignment Expert (故事板-提示词对齐)

> **定位:** 验证故事板线稿和视频提示词是否都正确对齐TIME_SKELETON。
>   格N的构图 = 提示词第N秒的描述 = TIME_SKELETON.frames[N]。
> **合并来源:** Scene Script Auditor + Storyboard Auditor + storyboard_planner §2E.4f对照
> **变化:** 不再独立审计故事板或提示词——只验证二者与骨架的对齐。

```
输入:
  ├─ TIME_SKELETON (对齐基准)
  ├─ 全部 STORYBOARD_[场景].md
  └─ 全部 VIDEO_PROMPT_[场景].md

验证维度:

6A 格号→秒号对齐:
  故事板格N 标注的时间/景别/运镜 = TIME_SKELETON.frames[N].hard?
  视频提示词第N秒描述 = TIME_SKELETON.frames[N].soft 展开?
  三方逐秒对照·任一不一致 → ⚠️

6B 编号系统对齐:
  故事板中①②③④标注 = TIME_SKELETON.segments[].segment_id?
  运镜过渡标记 = TIME_SKELETON.segments[transition]?
  切镜标记 = transition_type:"切"?

6C 全局锚点对齐:
  故事板"共享视觉锚" = TIME_SKELETON.global_anchors?
  视频提示词 Subject/Style/Constraints = global_anchors 逐字复制?

6D 逐秒帧完整性:
  TIME_SKELETON.frames 的每秒 → 故事板有对应格? 视频提示词有对应描述?
  任一缺漏 → ⚠️

6E 信息分工合规:
  故事板不包含材质/光影/色彩? (这些应在提示词中)
  提示词不重复故事板已有的空间信息? (§5.1铁律)

输出: ALIGNMENT_AUDIT.md (逐秒对照表·差异清单)
裁决: 不对齐→⚠️打回·修正后重验证
```

## Expert 7: Render Verifier (渲染结果验证)

> **定位:** Seko渲染后验证。与v1.0相同——这是唯一的渲染后检查点。
> **变化:** 无。7维验证逻辑保持不变。新增与TIME_SKELETON的时序精度对照。

```
输入:
  ├─ RENDER_PACKAGE.md
  ├─ TIME_SKELETON (时序精度对照基准)
  ├─ Seko渲染结果 (用户描述)
  └─ P-STATE.md §1-§2

验证维度 (7维·保持不变):
  1. 镜头类型保真度
  2. 运镜执行
  3. 构图实现
  4. 光影锚点
  5. 角色放置
  🆕 6. 时序精度 (对照TIME_SKELETON.frames[].hard验证关键帧事件时刻)
  7. 物理自洽

输出: RENDER_VERIFIER_REPORT.md → Deep Repair Loop
```

---

# §2 执行流程

```
全场景完成后 (Step 9):

┌──────────────────────────────────────────────────────────────────┐
│                    P-Verifier v2.0 执行流程                        │
│                                                                  │
│  Step 9.0: 加载所有 TIME_SKELETON (每场景 PLAN_[场景].md §B)      │
│                                                                  │
│  Step 9.1: Gate 0 Scanner (确定性规则·阻塞)                       │
│    R01-R15 一次扫描 → 🛑阻断或✅通过                              │
│    🛑 → 打回prompt_composer·上限1轮                               │
│                                                                  │
│  Step 9.2: 5个专项专家并行验证 (独立上下文·各自加载TIME_SKELETON)  │
│    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│    │ Expert 2    │  │ Expert 3    │  │ Expert 4    │            │
│    │ Spatial-    │  │ Visual      │  │ Object      │            │
│    │ Temporal    │  │ Anchor      │  │ Existence   │            │
│    └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
│           │                │                │                    │
│    ┌──────┴──────┐  ┌──────┴──────┐                                │
│    │ Expert 5    │  │ Expert 6    │  ← 并行·独立上下文             │
│    │ Cross-Scene │  │ Alignment   │                                │
│    └──────┬──────┘  └──────┬──────┘                                │
│           │                │                                       │
│           └───────┬────────┘                                       │
│                   ▼                                                │
│  Step 9.3: Judge 综合裁决                                          │
│    汇集5份报告 → 去重(同一违规被多个专家标记→合并)                   │
│    P0违规 → 🛑 打回                                                │
│    P1违规 → ⚠️ 标注                                                │
│    P2违规 → 💡 建议                                                │
│                                                                  │
│  Step 9.4: Render Packager (仅格式化·无R00)                       │
│    R00规则已在Gate 0检查 → 不重复                                  │
│    去冗余 · @声明标准化 · 输出RENDER_PACKAGE.md                     │
│                                                                  │
│  Step 9.5: 提交Seko渲染                                           │
│                                                                  │
│  Step 9.6: Render Verifier (Expert 7·渲染后)                      │
│    7维验证 → Deep Repair Loop                                     │
│    更新P-STATE.md §2(失败模式) §4(会话日志)                        │
└──────────────────────────────────────────────────────────────────┘
```

---

# §3 与v1.0的关键差异

| 维度 | v1.0 | v2.0 (方案二) |
|------|------|------|
| Agent数量 | 13 | 7 |
| 冗余率 | ~57% | ~0% |
| 确定性规则检查 | 4次(Gate 0 + Constraint + R00 + Script Auditor) | 1次(Gate 0 Scanner) |
| 时间对齐方式 | 手动对照编号系统 | 自动引用TIME_SKELETON |
| 道具跟踪权威 | 5个Agent各自检查 | Expert 4 唯一权威 |
| 跨场景连续性 | 2个Agent(Anchor Auditor + Cross-Scene) | 1个Expert(Cross-Scene) |
| 故事板-提示词对齐 | 3个Agent各自审计 | 1个Expert(Alignment) |
| 审查报告格式 | 各自独立格式 | 统一diff格式(对TIME_SKELETON的偏移量) |
| 信息隔离 | 部分Agent共享上下文 | 每个Expert完全独立上下文 |
| P-Verifier角色 | 编排4个Agent+Judge | Gate 0 启动 + 调度5个Expert + Judge汇总 |

---

# §4 被替代的旧Agent文件

以下文件被v2.0替代·保留在`02_Agent/`作为历史参考·不再被dispatcher加载:

```
替代映射:
  shot_reviewer_v1.0.md          → Expert 2 (Spatial-Temporal)
  movement_reviewer_v1.0.md      → Expert 2 (空间可行性部分)
  visual_reviewer_v1.0.md        → Expert 3 (Visual Anchor)
  constraint_reviewer_v1.0.md    → Expert 1 (Gate 0) + Expert 3 (视觉约束)
  scene_anchor_auditor_v1.0.md   → Expert 5 (Cross-Scene)
  scene_design_auditor_v1.0.md   → Expert 2 + Expert 3
  scene_script_auditor_v1.0.md   → Expert 1 (Gate 0) + Expert 6 (Alignment)
  storyboard_auditor_v2.3.md     → Expert 6 (Alignment)
  cross_scene_continuity_auditor_v1.0.md → Expert 5 (Cross-Scene)
  
保留不变:
  object_existence_verifier_v1.0.md → Expert 4 (Object Existence)
  render_verifier_v1.0.md           → Expert 7 (Render Verifier)
  render_packager_v1.0.md           → Render Packager (仅格式化·无R00)
```

---

> **v2.0 · 2026-07-07**
> **创建:** 方案二架构 · 独立专项专家验证
> **关联:** TIME_SKELETON_spec.md · P-CONSTITUTION.md §7 · storyboard_planner_v2.0.md
> **下一步:** 更新dispatcher MODE:P流程 · 更新README验证Agent矩阵
