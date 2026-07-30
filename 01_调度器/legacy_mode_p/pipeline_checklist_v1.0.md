# MODE:P 管道强制执行清单 v1.0

> **定位:** 每次MODE:P场景运行前必须逐项勾选。调度器启动时Read本文件。任何未勾选项必须有显式跳过理由。
> **触发:** 调度器在复杂度分类后·Agent调用前·必须输出本清单。
> **版本:** v1.0 · 2026-07-09

---

## 前置步骤（调度器自执行·零Agent）

```
□ Step 0:   IMAGE_AUDIT
              ├─ 读取已有IMAGE_AUDIT报告 OR 从参考图清单生成
              ├─ 确认: 所有场景参考图已盘点·缺失项已标注·🛑阻断项已处理
              └─ 跳过条件: 无（强制执行）

□ Step 0.5: OBJECT_TIMELINE
              ├─ F7≤3 → ⚡跳过（标注"F7=N≤3·跳过"）
              ├─ F7>3 → 强制执行
              └─ 跳过时: Scene Auditor维度D抽查覆盖物体存在链

□ Step 0.6: ANCHOR_BASELINE
              ├─ S-Level: 保留Character Anchor+Style Spine·跳过跨场景连续性
              ├─ M/C-Level: 完整执行
              └─ 跳过条件: 无（至少执行S-Level精简版）

□ Step 0.7: CONTEXT_PACKAGE
              ├─ 组装: agent_quick_ref引用+场景列表+空间摘要+角色锚点
              │        +参考图索引+复杂度参数+P-STATE活跃条目+KB规则ID+深读索引
              ├─ 输出: CONTEXT_PACKAGE_[剧本名].md
              └─ 跳过条件: 无（强制·所有Agent共享·替代5-8个独立文件Read）
```

## 复杂度分类（调度器自执行·零模型）

```
□ F1-F7 字段提取
  F1=独立空间数 · F2=说话角色数 · F3=对白句数 · F4=静态镜头比例
  F5=空间复杂度标志 · F6=动作戏标志 · F7=跨镜追踪物品数

□ 判定: 🟢S / 🟡M / 🔴C
  S: F1=1 AND F2≤3 AND F3≤5 AND F4≥80% AND F5=false AND F6=false
  M: 不满足S也不满足C
  C: F2≥4 OR F3>15 OR F1≥4 OR F6=true

□ OBJECT_TIMELINE决策: F7>3→执行 / F7≤3→⚡跳过
```

## 设计层（Agent调用）

```
□ Scene Designer [Agent]
  ├─ 输入: 剧本+空间地图+参考图+ANCHOR_BASELINE+CONTEXT_PACKAGE+KB_SUMMARY
  ├─ S-Level: 三域合并·含台本初稿·≤600行·静态快速通道·无设计依据
  ├─ M-Level: 三域合并·含动作运镜展开·≤1200行
  ├─ C-Level: 三域合并·全维度展开·≤2000行
  └─ 输出: [场景]_SCENE_DESIGNER.md + §7 YAML块
```

## 确定性检查（调度器自执行·零LLM）

```
□ Gate 0 前置扫描 [Orchestrator]
  ├─ 输入: Scene Designer输出的台本初稿/导演台本
  ├─ 执行: R01-R15正则扫描（gate0_context_aware_v1.0.md）
  ├─ 输出: GATE0_PRE_REPORT.md
  ├─ ✅全部通过→进入Scene Auditor
  ├─ 🛑有阻断→返回Scene Designer修复·上限1轮
  └─ 成本: 0 tokens·纯正则·零LLM
```

## 审计层（Agent调用）

```
□ Scene Auditor [Agent]
  ├─ Phase 0: 读GATE0_PRE_REPORT.md·复审WARN项
  ├─ Phase 1: S-Level→跳过 / M-Level→精简 / C-Level→全量
  ├─ Phase 2: 有PLAN→全量 / 无PLAN→降级(仅2C+2G)
  ├─ Phase 3: 台本域审计（Gate 0已覆盖的不重复）
  └─ 裁决: 🛑→返回修复·上限2轮 / ⚠️→标注 / ✅→进入交付层
```

## 交付层 — 视频提示词（Agent调用·C/M-Level）

```
□ 格式对齐（生成前必做·不可跳过）
  ├─ 读取: prompt_composer_v2.0.md §3.3d（方式C模板）
  └─ 读取: 至少一个已有输出示例

□ Prompt Composer [Agent·C/M-Level]  /  Scene Designer台本格式对齐 [S-Level]
  ├─ 模板: @声明区 + Subject + Action(①②③④逐秒分段) + Camera + Style
  │        + Constraints + 时序描述 + 【禁止】 + 故事板对照
  ├─ 硬约束:
  │   · Action块零过程动词(正在/刚/已/开始)
  │   · Action块零时间模糊词(缓缓/渐渐/慢慢/逐渐)
  │   · Action块零工程符号(v_dolly/ω_pan/°/s/f/数字)
  │   · Action块零负向词(不要/避免/禁止——仅允许在【禁止】块)
  │   · 每段≤15秒
  │   · 光源必须有物理锚点
  │   · 跨镜零引用(同上/参考上镜)
  └─ 输出: [场景]_视频提示词_v2.0.md
```

## 交付层 — 故事板（Agent调用·与视频提示词可并行）

```
□ 格式对齐（生成前必做·不可跳过）
  ├─ 读取: storyboard_previewer_v1.5.md
  ├─ 读取: STORYBOARD_EP15_Rico工作室_方式C.md（锚点格式示例）
  └─ 确认: 逐格五维标注(🔴身体🔵相机🟢构图🟠光线⚫景别运镜)

□ Storyboard [Agent]
  ├─ 格式: 方式C锚点·N秒=N格·逐格·共享锚点·Seko线稿Prompt
  ├─ 每镜:
  │   · 共享锚点(全部N格)
  │   · 格N [Ns·景别·焦距·运镜]
  │   · 画面: [描述]
  │   · 🔴身体: / 🔵相机: / 🟢构图: / 🟠光线: / ⚫[景别·运镜·色温]
  │   · 【Seko线稿生成Prompt】在每镜末尾
  └─ 输出: STORYBOARD_[场景]_方式C_v2.md
```

## 交付层 — 最终打包（可与故事板并行）

```
□ Render Packager [Orchestrator·格式化]
  ├─ 输入: 视频提示词 + 故事板
  ├─ R00检查: 格式完整性·引用有效性·15秒硬约束
  ├─ 分段方案: 模型选择·参考图映射
  └─ 输出: RENDER_PACKAGE_[场景].md
```

---

## 三层交付物最终检查

```
□ 设计层: Scene Designer输出存在·YAML完整·台本初稿格式正确
□ 视觉层: 故事板存在·方式C锚点格式·逐格五维标注·Seko线稿Prompt
□ 执行层: 视频提示词存在·方式C分段格式·R02/R03/R07/R09全部通过
□ 格式验证: 视频提示词与prompt_composer模板逐字段对齐
□ 格式验证: 故事板与STORYBOARD_EP15示例逐字段对齐
```

---

> **v1.0 · 2026-07-09 · 管道强制执行清单**
> **原则:** 任何未勾选项必须有显式跳过理由。跳过交付层=管道未完成。
> **使用:** 调度器在复杂度分类后输出本清单·每完成一步回写勾选状态。
