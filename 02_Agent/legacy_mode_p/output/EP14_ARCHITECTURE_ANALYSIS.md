# EP14 流程架构分析

> **分析日期:** 2026-07-07
> **分析范围:** MODE:P 全管道 (dispatcher_v5.0 + complexity_router_v1.0 + scene_designer_v1.0 + scene_auditor_v1.0)
> **参考基线:** P-CONSTITUTION.md / EP14剧本 / EP14_SUPERVISION_REPORT.md
> **分析方法:** 步骤必需性矩阵 + 依赖拓扑分析 + 上下文爆炸诊断 + 可扩展性评估 + 推理过程根因分析

---

## 1. 步骤必需性矩阵 (管道全部步骤·逐项判定)

### 判定符号
- **红色: 必须保留** — 删除后宪法违规或质量显著下降
- **黄色: 条件保留** — 对C-Level必要·对S/M-Level可跳过或精简
- **绿色: 可以删除** — 历史上零阻断·ROI约等于0·纯形式主义

### 1A. 全局前置步骤

| # | 步骤 | 旧执行者 | 新执行者 | 判定 | 理由 |
|---|------|---------|---------|:---:|------|
| 0 | IMAGE_AUDIT (图片资源盘点) | [O] | [O] | **红色** | 宪法第三条(空间锚定)的物理前提——所有设计必须基于可追溯的参考图。IMAG-01阻断(缺必备参考图)=管道终止。不可删除。 |
| 0.5 | OBJECT_TIMELINE (物体存在链提取) | [O] | [O]条件 | **黄色** | 宪法第六条(物体存在链可追溯)的执行前提。但对S-Level场景(N_objects<=3): 物品链简单·可由Scene Auditor维度抽查覆盖·独立提取ROI低。对M/C-Level(N_objects>3): 必须执行。complexity_router已条件化——正确。 |
| 0.6 | ANCHOR_BASELINE (全场景基线) | [O] | [O] | **红色** | 设计Agent的Character Anchor/Style Spine的唯一来源。删除后每个设计Agent需自行推断角色描述，导致跨场景角色外观不一致(已知P-STATE失败模式)。单场景(S-Level): 可精简(跳过跨场景连续性)但不可删除。 |

### 1B. 场景级设计步骤 (原三Agent串行链)

| # | 步骤 | 旧执行者 | 新执行者 | 判定 | 理由 |
|---|------|---------|---------|:---:|------|
| A1 | Scene Anchor Auditor P1 (快照格式检查) | [A] | [A]条件 | **黄色** | 仅≥2场景时触发。S-Level单场景: 跳过(无跨场景连续性需求)。M-Level多场景: 条件执行(场景数≥2)。单场景剧本: 可删除。 |
| A2.1 | Shot Architect (机位设计) | [A] | [A]合并 | **红色** | 机位是运镜和构图的硬性数据依赖。但独立Agent形式仅C-Level必需。S-Level: 合并入Scene Designer。M-Level: 路径M-B独立·路径M-A合并。不可完全删除——只是形式可合并。 |
| A2.2 | Movement Designer (运镜设计) | [A] | [A]合并 | **黄色** | EP14场景A证据: 978行论证"6个固定镜头合理"——净价值为负。对S-Level(>=80%固定): 静态快速通道一句话解决·独立Agent全冗余。对C-Level(动作/多空间/动态运镜): 独立Agent必要——运镜空间可行性验证无法被机位和构图替代。合并入Scene Designer后的静态快速通道机制(R-SFAST-01~03)已解决冗余问题。 |
| A2.3 | Composition Designer (构图光影) | [A] | [A]合并 | **红色** | 光影锚点验证(宪法第三条)和色彩策略是台本质量的核心。但独立Agent形式仅在C-Level必要。S/M-Level: 合并入Scene Designer·构图从空间地图直接引用(R-SFAST-04)。不可完全删除——但可合并。 |

### 1C. 审计与骨架步骤

| # | 步骤 | 旧执行者 | 新执行者 | 判定 | 理由 |
|---|------|---------|---------|:---:|------|
| A2-审计 | Scene Design Auditor (设计审计) | [A] | [A]合并 | **红色** | 宪法第七条(独立验证)的架构保证。EP14监督报告: SDA全措辞级零设计缺陷——但这不是"SDA无用"的证据，而是"设计Agent质量高"的证据。删除审计=违反宪法第七条。但可合并入Scene Auditor Phase 1(已实现)。 |
| A2.5 | Storyboard Planner (PLAN+TIME_SKELETON) | [A] | [A]条件 | **黄色** | TIME_SKELETON是prompt_composer和Scene Auditor Phase 2的硬性数据依赖。但对S-Level(<=5句对白·单场景): TIME_SKELETON trivial——音轨直接嵌入台本(R-SFAST-05)·Phase 2降级为仅2C+2G。C-Level: 必须执行。M-Level: 条件触发(complexity_router: F3>10或F1>1)。 |
| A3 | Prompt Composer (台本撰写) | [A] | [A]独立→合并 | **红色** | 导演台本是不可替代的最终交付物。但在S-Level中合并入Scene Designer(产出台本初稿)——不是删除PC，而是将台本撰写能力内嵌到设计Agent中。C/M-Level仍需要独立PC处理复杂时序+多角色调度。 |
| A3-审计1 | Scene Script Auditor (台本审计) | [A] | [A]合并 | **红色** | 台本质量门禁——宪法第一条(画面可见性)、第二条(渲染可行性)、第四条(运镜-画面分离)的验证执行者。合并入Scene Auditor Phase 3(已实现)。不可删除——但可合并。 |
| A3-审计2 | Scene Anchor Auditor P2 (锚点对比) | [A] | [A]条件 | **黄色** | 仅>=2场景时触发。跨场景锚点一致性验证。S-Level单场景: 跳过。监督报告建议: 对于S-Level场景，Scene Auditor Phase 2的2D(全局锚点逐字一致)已部分覆盖此功能。 |

### 1D. 故事板生成与审计步骤

| # | 步骤 | 旧执行者 | 新执行者 | 判定 | 理由 |
|---|------|---------|---------|:---:|------|
| A4A | 方式C故事板生成 | [A] | 跳过(S/M) | **黄色** | 方式C线稿故事板作为模型构图参考的功能——对C-Level(多空间/复杂运镜)有价值。对S-Level(单室·固定机位): 参考图本身即是构图参考·方式C冗余。complexity_router正确: S/M-Level跳过。 |
| A4B | Storyboard Auditor (故事板审计) | [A] | 跳过(S/M) | **黄色** | 随A4A跳过而跳过。C-Level保留。 |
| A4C | 人类审核门禁 | [H] | [H] | **红色** | 宪法外的流程保证——用户对最终交付物的确认权。不可删除。但对S-Level可精简审核展示(直接展示台本+参考图·无需线稿故事板)。 |

### 1E. 全场景后验证步骤

| # | 步骤 | 旧执行者 | 新执行者 | 判定 | 理由 |
|---|------|---------|---------|:---:|------|
| 9.0 | 加载全部TIME_SKELETON | [O] | [O] | **红色** | 跨场景验证的前提——Gate 0 Scanner需要所有场景的时间轴来检查跨场景连续性。但仅C-Level需要("全场景"意味着多场景)。S-Level单场景: 跳过(无跨场景验证需求)。 |
| 9.1 | Gate 0 Scanner (全局确定性扫描) | [A] | [O]前置 | **红色** | 宪法第五条(确定性>概率性)的核心执行者。但执行位置可优化: complexity_router已将其前置为每场景Scene Auditor的Phase 0——在LLM审计前·调度器自执行正则扫描。全场景后Gate 0 Scanner(Agent)仅C-Level需要——作为全局Gate 0。S/M-Level: 已并入Scene Auditor Phase 0。 |
| 9.2 | 5专家并行验证 | [A]x5 | 跳过(S/M) | **黄色** | 红队对抗·边界测验·假设驱动·模式匹配·结构同构。对C-Level(复杂多场景): 有价值——多维交叉验证捕获单场景审计遗漏的跨场景问题。对S-Level(单场景·简单): 论证密度不足·ROI低。EP14场景A: 5专家产出~2,500行论证简单场景——过度工程化。complexity_router正确跳过。 |
| 9.3 | 多方会诊 | [A] | 跳过(S/M) | **绿色** | 依赖5专家报告。S/M-Level跳过5专家→多方会诊自动跳过。即使C-Level: 5专家并行后·多方会诊交叉验证的价值取决于专家间发现的重叠度。如果5专家各自覆盖不同维度(设计目标)，交叉发现少→会诊产出低。需要实证数据。目前保留为C-Level专属。 |
| 9.5 | Render Packager (渲染打包) | [O] | [O] | **红色** | 将台本格式化为Seko可消费标准格式。R00确定性最终检查(格式完整性)。不可删除——但formatting部分可在S-Level中由Scene Designer直接产出符合格式的台本·跳过独立打包步骤。 |
| 9.6 | Object Existence Verifier (物体存在链) | [A] | [A]条件 | **黄色** | 宪法第六条(物体存在链)的专项独立验证。对M/C-Level(N_objects>3或有动作戏): 必须——物品链复杂·独立验证必要。对S-Level(N_objects<=3): 合并入Scene Auditor Phase 3抽查(监督报告WARN-4: 此合并尚未在scene_auditor中明确定义)。 |
| 10 | Render Verifier (渲染后验证) | [A] | 跳过(S/M) | **黄色** | 渲染后7维验证。需Seko实际渲染结果。对C-Level: 保留(复杂场景渲染失败风险高)。S/M-Level: 跳过——简单场景渲染失败率低·P-STATE模式匹配可提前规避。但需条件触发: 如果S-Level渲染结果用户反馈异常→可手动触发Render Verifier。 |

### 1F. 步骤必需性汇总

| 级别 | 原Agent数 | 红色(必须) | 黄色(条件) | 绿色(可删) | 优化后Agent数 | 节省 |
|:---:|:------:|:------:|:------:|:------:|:------:|:---:|
| C-Level | ~18 | 18 | 0 | 0 | ~18 | 0% (全管道) |
| M-Level(M-A) | ~18 | 4 | 3 | 11 | 4-7 | ~61-72% |
| M-Level(M-B) | ~18 | 6 | 2 | 10 | 6-8 | ~55-67% |
| S-Level | ~18 | 2 | 4 | 12 | 2 | ~89% |

> 注: "必须"指该功能不可删除——但可通过合并Agent减少独立Agent调用次数。"可删"指该独立Agent调用可完全跳过·其功能或被合并·或不适用。

---

## 2. 依赖优化

### 2.1 当前依赖图 (C-Level·dispatcher §-2)

```
                    ┌─────────────┐
                    │ IMAGE_AUDIT │ (Step 0)
                    └──────┬──────┘
                           │ (软性·两者无相互依赖但当前串行)
                           ▼
                    ┌────────────────┐
                    │ OBJECT_TIMELINE │ (Step 0.5)
                    └──────┬─────────┘
                           │ (软性)
                           ▼
                    ┌─────────────────┐
                    │ ANCHOR_BASELINE  │ (Step 0.6)
                    └──────┬──────────┘
                           │ (硬性: 设计需要空间地图 §C)
                           ▼
              ┌─────────────────────────┐
              │ Shot Architect          │ (Wave 1·S1)
              └───────────┬─────────────┘
                          │ (硬性: 运镜需要机位 §6 YAML)
                          ▼
              ┌─────────────────────────┐
              │ Movement Designer       │ (Wave 1·S2)
              └───────────┬─────────────┘
                          │ (硬性: 构图需要机位+运镜 §6 YAML)
                          ▼
              ┌─────────────────────────┐
              │ Composition Designer    │ (Wave 1·S3)
              └───────────┬─────────────┘
                          │
               ┌──────────┴──────────┐
               ▼                     ▼
    ┌──────────────────┐  ┌──────────────────┐
    │ Scene Design      │  │ Storyboard       │ (Wave 2·并行)
    │ Auditor           │  │ Planner          │
    └────────┬─────────┘  └────────┬─────────┘
             │                     │ (硬性: PC需要PLAN §B)
             │                     ▼
             │          ┌──────────────────┐
             │          │ Prompt Composer  │ (Wave 3)
             │          └────────┬─────────┘
             │                   │
             └─────────┬─────────┘
                       ▼
              ┌──────────────────┐
              │ Scene Script     │
              │ Auditor + SAA P2 │ (Wave 4·并行)
              └──────────────────┘
```

### 2.2 硬性依赖 vs 软性依赖分析

| 依赖链 | 类型 | 分析 |
|-------|:---:|------|
| IMAGE_AUDIT → ANCHOR_BASELINE | **软性** | 两者都消费参考图+剧本·但IMAGE_AUDIT输出的是参考图覆盖度审计·ANCHOR_BASELINE输出的是角色锚点+风格基线。ANCHOR_BASELINE不需要IMAGE_AUDIT的结果来建立Character Anchor。正确依赖: 两者并行·然后设计Agent消费两者的输出。 |
| OBJECT_TIMELINE → [下游] | **软性** | OBJECT_TIMELINE只消费剧本+人物表·不依赖IMAGE_AUDIT或ANCHOR_BASELINE。可与前两者完全并行。设计Agent不直接消费OBJECT_TIMELINE——由Scene Auditor/Object Existence Verifier消费。 |
| ANCHOR_BASELINE → Shot Architect | **硬性** | 设计Agent需要空间地图(§C)和角色锚点(§A)。不可并行。 |
| Shot Architect → Movement Designer | **硬性** | 运镜设计需要知道机位位置·才可评估运镜空间可行性。不可并行。 |
| Movement Designer → Composition Designer | **硬性** | 构图需要知道运镜参数·才可评估景深随运镜的变化。不可并行。 |
| 三设计Agent → Scene Design Auditor | **硬性** | 审计Agent需要设计输出。不可并行(审计隔离原则)。 |
| 三设计Agent → Storyboard Planner | **软性(YAML)** | PLAN只消费设计Agent的§6 YAML结构化字段·不消费自由文本推理。如果设计Agent能先输出YAML块(而非等全部推理完成)·PLAN可提前启动。当前管道: 设计Agent输出单文件含推理+YAML→PLAN必须等设计Agent完全完成。优化潜力: 分阶段输出——但Agent调用是原子性的(一次调用=一个输出文件)。实际约束: 软性依赖但当前无法并行。 |
| Storyboard Planner → Prompt Composer | **硬性** | PC消费TIME_SKELETON(PLAN §B)作为逐秒时间轴。不可并行。 |
| Prompt Composer → Scene Script Auditor | **硬性** | 审计需要台本。不可并行。 |
| Scene Design Auditor ∥ Scene Script Auditor | **软性(可并行)** | 两者没有相互依赖——设计审计和台本审计独立。但当前管道将它们放在不同wave中(SDA在Wave 2·SSA在Wave 4)——因为SSA需要台本·台本需要PLAN·PLAN在Wave 2。如果设计产出和PLAN产出可用·SDA和SSA理论上可在同一wave并行(当前未实现这个优化)。 |

### 2.3 优化后依赖图

```
═══════════ Wave 0: 全局前置 (3路并行·零相互依赖) ═══════════

  [O] IMAGE_AUDIT ─────┐
  [O] OBJECT_TIMELINE ─┼── 3路并行 → 总wall-clock = max(三者)
  [O] ANCHOR_BASELINE ─┘

  节省: 当前串行需3×(T_AUDIT+T_OBJ+T_ANCHOR) → 优化后需max(T_AUDIT,T_OBJ,T_ANCHOR)
        保守估计节省40-60%前置时间

═══════════ Wave 1-2: 场景级 (按复杂度路由·Adaptive) ═══════════

  S-Level (2 Waves·2 Agent):
    Wave 1: Scene Designer (三合一·含台本初稿)
    Wave 2: Scene Auditor (合并审计·4 Phase)

  M-Level (3-4 Waves·4-7 Agent):
    路径M-A (无动作戏):
      Wave 1: Scene Designer(Shot+Comp合并) → Movement Designer(独立)
      Wave 2: SDA ∥ Storyboard Planner(条件)
      Wave 3: Prompt Composer
      Wave 4: SSA ∥ Scene Anchor P2(条件)
    路径M-B (有动作戏):
      Wave 1: Shot → Movement → Comp (三独立)
      后续同M-A

  C-Level (原全管道·保持不变):
    dispatcher §-2 定义的4-wave拓扑·完整18 Agent

═══════════ Wave 3: 全场景后 (仅C-Level·S/M跳过) ═══════════

  [O] Gate 0 Scanner (前置·已在Scene Auditor Phase 0执行)
  [A] 5专家并行 → [A] 多方会诊
  [O] Render Packager
  [A] Object Existence Verifier (M-Level条件)
  [A] Render Verifier

  注: 全场景后步骤对C-Level保留·对S/M-Level跳过或合并入场景级审计。
```

### 2.4 关键依赖优化收益

| 优化 | 当前 | 优化后 | 收益类型 |
|------|------|-------|:---:|
| IMAGE_AUDIT ∥ ANCHOR_BASELINE | 串行 | 并行 | wall-clock: 节省~40%前置时间 |
| OBJECT_TIMELINE ∥ 上前两者 | 串行 | 并行 | wall-clock: 节省~33%前置时间 |
| 三Agent串行 → Scene Designer合并 | 3次Agent调用 | 1次Agent调用 | Agent调用: 节省67%·消除YAML合并冲突 |
| PLAN与设计"近并行" | 串行 | YAML-block优先传递 | 理论可行·实践受Agent原子性限制 |
| 审计Agent合并(SDA+SSA+Gate 0) | 2-3次Agent调用 | 1次Agent调用 | Agent调用: 节省50-67%·消除重复Gate 0 |

---

## 3. 上下文爆炸解决方案

### 3.1 当前每个Agent的上下文加载 (诊断)

```
典型设计Agent (以Scene Designer M-Level为例):

┌──────────────────────────────────────────────────────────────┐
│ 输入文件                    │ 估计大小    │ 累计          │
├─────────────────────────────┼────────────┼───────────────┤
│ 指令文件(自身)               │ ~12K tokens │ 12K           │
│ 剧本段落                     │ ~3K tokens  │ 15K           │
│ 空间地图                     │ ~5K tokens  │ 20K           │
│ 场景参考图(图像)             │ 不计tokens  │ -             │
│ ANCHOR_BASELINE              │ ~4K tokens  │ 24K           │
│ P-CONSTITUTION               │ ~15K tokens │ 39K           │
│ P-STATE §1-§2               │ ~3K tokens  │ 42K           │
│ canvas_runtime               │ ~5K tokens  │ 47K           │
│ shared_agent_runtime          │ ~8K tokens  │ 55K           │
│ kb_index → KB子集(~30条)     │ ~15K tokens │ 70K           │
│ TIME_SKELETON_spec            │ ~5K tokens  │ 75K           │
│ IMAGE_AUDIT                  │ ~3K tokens  │ 78K           │
│ 上游Agent输出(如果独立Agent)  │ ~10K tokens │ 88K           │
├─────────────────────────────┼────────────┼───────────────┤
│ 总计(Agent读取)              │            │ ~88K tokens   │
│ 其中"公共上下文"占比          │            │ ~50K (57%)    │
└──────────────────────────────────────────────────────────────┘

公共上下文 = P-CONSTITUTION + P-STATE + canvas_runtime + 
             shared_agent_runtime + ANCHOR_BASELINE + 空间地图 + IMAGE_AUDIT
           ≈ 50K tokens·每Agent重复加载
```

### 3.2 解决方案1: 预编译"场景上下文包"

**方案:** 调度器在启动Agent前·将公共上下文合并为单文件`SCENE_CONTEXT_BUNDLE.md`·Agent只需Read 1个文件替代8个。

```
SCENE_CONTEXT_BUNDLE.md 结构:
  §1 P-CONSTITUTION 精简版 (7条铁律·每条1-2句·~2K tokens)
  §2 场景空间坐标系 (一次写入·三域共享·~3K tokens)
  §3 ANCHOR_BASELINE 本场景节选 (§A+C·~2K tokens)
  §4 P-STATE 活跃条目 (§1已验证3条+§2已知失败6条·~2K tokens)
  §5 canvas_runtime 硬约束摘要 (~1K tokens)
  §6 IMAGE_AUDIT 本场景格位映射 (~1K tokens)
  §7 KB路由结果 (已路由的KB规则ID清单·非规则全文·~0.5K tokens)
  §8 复杂度级别 + 特殊指令 (~0.5K tokens)

总计: ~12K tokens (vs 当前50K·节省76%)
```

**实施:** 调度器Step 0完成后·自执行`SCENE_CONTEXT_BUNDLE.md`合并。每个Agent调用时传递此文件路径。

**收益:** 节省(8-1)×(50K/8) = ~44K tokens/Agent × N个Agent。对C-Level(18 Agent): 节省~790K tokens。

### 3.3 解决方案2: KB规则"快速参考卡"格式

**方案:** KB规则从"详述格式"转为"快速参考卡"——规则ID+一句话+详述指针。Agent按需深读。

```
当前KB加载格式 (每条~300-800 tokens):
  ### D-TRI-01: 180度线基本原则
  > **来源:** Arijon Ch.4
  > **优先级:** P0
  > **规则:** 在关系线同一侧放置摄影机·以确保角色在画面中的视线方向一致...
  > **详细说明:** (展开3-5段·含示例·含例外·含冲突裁决)
  > **关联规则:** D-TRI-02, D-TRI-03
  > **代码引用:** ...
  [总计~400 tokens/条]

优化后快速参考卡 (每条~60-100 tokens):
  D-TRI-01 [P0] 180度线: 摄影机保持关系线同侧。例外: 中性过渡镜(插入/特写/空镜)。
  → 详述: 03_导演知识库_v5.0.md §1.1 [行号]

收益: 30条KB规则 × 300 tokens节省 = ~9K tokens/Agent
```

**实施:** 维护KB规则的双版本——详述版(03_导演知识库_v5.0.md·保持不变)和快速参考卡版(由kb_index路由后生成)。Agent加载快速参考卡版·仅在遇到陌生/冲突规则时Read详述版对应章节。

### 3.4 解决方案3: YAML-Only传递

**方案:** 设计Agent输出拆分为YAML块(结构化的·被下游消费)和自由文本(推理·仅供人类审核·不被下游Agent消费)。

```
当前:
  Scene Designer输出 = 推理(自由文本·~800行) + YAML块(§4+§5+§6·~200行)
  → 审计Agent Read完整输出(~1000行) → 其中80%是推理·不参与审计

优化后:
  Scene Designer输出:
    ├─ SCENE_DESIGN_REPORT.md (完整·含推理·供人类审核)
    └─ SCENE_DESIGN_YAML.yaml (仅§4+§5+§6 YAML块·供下游Agent消费)
  
  审计Agent只Read YAML文件(~200行 vs 1000行·节省80%)

  下游PLAN Agent也只Read YAML文件。
```

**实施:** Scene Designer指令中明确要求"同时输出两个文件: 完整报告(.md) + 结构化YAML(.yaml)"。下游Agent指令中明确要求"只Read YAML文件·不Read完整报告"。

**收益:** 审计Agent上下文从~88K tokens降至~48K tokens(节省40K)。PLAN Agent类似。

### 3.5 解决方案4: 调度器注入公共上下文

**方案:** 调度器将公共上下文直接注入Agent的prompt中·而非Agent自行Read。

```
当前:
  调度器: "📤 启动 Scene Designer · 输入: [8个文件路径]"
  Agent: Read 8个文件 → 开始推理

优化后:
  调度器: "📤 启动 Scene Designer"
    prompt中注入:
      - P-CONSTITUTION 精简版 (嵌入prompt)
      - 场景空间坐标系 (嵌入prompt)
      - P-STATE 活跃条目 (嵌入prompt)
      - canvas_runtime 硬约束 (嵌入prompt)
    文件路径(Agent需自行Read):
      - 剧本段落
      - 场景参考图
      - KB路由后的详述规则(按需)

  Agent收到prompt后不再需要Read公共文件。
```

**收益:** Agent启动时Read调用从8-12次降至2-3次。每次Read=1次LLM推理。节省5-9次推理×N个Agent。

### 3.6 上下文优化总收益估算

| 优化项 | 节省/Agent | ×18 Agent (C-Level) | ×2 Agent (S-Level) |
|--------|:--------:|:------------------:|:------------------:|
| 场景上下文包 | ~44K | ~790K | ~88K |
| KB快速参考卡 | ~9K | ~162K | ~18K |
| YAML-Only传递 | ~40K | ~360K (仅审计)+ | ~40K |
| 调度器注入 | 5-9次Read | ~90-162次Read | ~10-18次Read |
| **总节省** | | **~1,300K tokens** | **~146K tokens** |

> C-Level全管道(含5专家+多方会诊)当前估~3,500K tokens → 优化后~2,200K tokens (节省~37%)
> S-Level当前估~350K tokens → 优化后~200K tokens (节省~43%)

---

## 4. 多场景可扩展性

### 4.1 当前问题

```
2场景EP14:  2 × (Scene Designer + Scene Auditor) = 4 Agent
10场景剧本: 10 × 2 = 20 Agent (S-Level) → 不可线性扩展
10场景C-Level: 10 × 18 = 180 Agent → 完全不可扩展
```

### 4.2 优化方向1: 多场景批量设计

**方案:** Scene Designer一次处理所有相同复杂度的场景。

```
当前: 
  for scene in scenes:
    [Agent] Scene Designer(scene_i)  # N次Agent调用

优化后:
  [Agent] Scene Designer(scenes=[scene_1, scene_2, ... scene_k])
    → 批量输出 k 份设计报告
    → 同类型场景的KB规则只加载一次
    → 跨场景一致性在同一上下文中保证

适用条件:
  ✅ 同为S-Level的场景
  ✅ 同一场景类型(如均为双人对话)
  ❌ 不同复杂度级别(→分别调用)
  ❌ 场景数过多导致上下文爆炸(→分批·每批≤3场景)
```

**收益:** 5个S-Level场景: 5次调用→1次调用(节省4次Agent启动开销)。KB加载从5次降至1次。

### 4.3 优化方向2: 分场景台本独立生成

**方案:** 批量设计后·每场景独立生成台本(保持上下文隔离)。

```
Wave 1: [Agent] Scene Designer 批量设计(S-Level场景1-3)
Wave 2: 3个Scene Designer并行·各自为1个场景的台本初稿精炼
         (共享Wave 1的设计YAML·但各自独立上下文)

理由: 台本生成需要逐秒展开描述·上下文密集。合并会导致上下文爆炸。
```

### 4.4 优化方向3: 跨场景审计延迟批处理

**方案:** 场景级审计(Scene Auditor)在每场景完成后立即执行(保证修复回环)。跨场景审计(5专家·多方会诊·Object Existence Verifier·Render Verifier)延迟到全场景完成后批量执行。

```
当前:
  每场景: Scene Auditor → 全场景后: 5专家+多方会诊+OBJ_Verifier+Render_Verifier

优化后:
  每场景: Scene Auditor (立即执行·保证修复回环)
  全场景后(仅多场景·C-Level):
    [A] 跨场景连续性检查 (替代原Anchor Auditor P2)
    [A] Object Existence Verifier (全场景批量·一次调用处理所有物体链)
    [A] Gate 0 Scanner (全场景批量·一次扫描)
    [A] 5专家并行 (仅C-Level保留)
    跳过: 多方会诊(待实证·可能并入Judge裁决)
```

**收益:** 去重——Object Existence Verifier从每场景调用1次→全场景调用1次。5专家从每场景一组→全场景一组。

### 4.5 场景打包策略

```
S-Level场景打包 (单室·简单对话):
  批量设计: 3-5场景/批 → 1次Scene Designer调用
  独立台本: 每场景1次(并行·独立上下文)
  独立审计: 每场景1次(并行·独立上下文)
  全场景后: 跳过

M-Level场景打包 (多空间·动态运镜):
  批量设计: 2-3场景/批 → 1次Scene Designer调用(Shot+Comp合并)
  独立运镜: 每场景1次Movement Designer(并行)
  独立台本: 每场景1次Prompt Composer(并行)
  独立审计: 每场景1次Scene Auditor(并行)

C-Level场景打包 (复杂动作·多人对话):
  不打包·每场景独立全管道(保证质量)
  全场景后: 批量跨场景验证(1组5专家+1次多方会诊)
```

### 4.6 可扩展性汇总

| 场景数 | 复杂度 | 当前Agent数 | 优化后Agent数 | 节省 |
|:-----:|:-----:|:--------:|:---------:|:---:|
| 2 | S+S | 4 | 3 (1批量设计+2审计) | 25% |
| 5 | 5×S | 10 | 4 (1批量设计+3审计并行) | 60% |
| 5 | 5×M | 25-35 | 10-15 | ~55% |
| 10 | 10×S | 20 | 7 (2批设计+5审计并行) | 65% |
| 10 | 5×S+3×M+2×C | ~100 | ~40 | ~60% |

> 注: 优化后Agent数含批量设计和跨场景批量审计的折减。

---

## 5. 推理过程过长根因 + 解决方案

### 5.1 根因鱼骨图

```
                    ┌─────────────────────────────────────────────┐
                    │         Agent推理时间过长 (3,476s/场景)        │
                    └─────────────────────────────────────────────┘
                                      │
        ┌─────────┬─────────┬─────────┼─────────┬─────────┬─────────┐
        ▼         ▼         ▼         ▼         ▼         ▼         ▼
   ┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐
   │文件读取  ││大KB加载 ││上游输出 ││形式主义  ││串行链   ││过度验证 ││重复检查 │
   │开销     ││        ││膨胀     ││论证     ││累积延迟 ││        ││        │
   └────┬────┘└────┬────┘└────┬────┘└────┬────┘└────┬────┘└────┬────┘└────┬────┘
        │         │         │         │         │         │         │
        ▼         ▼         ▼         ▼         ▼         ▼         ▼
  每Agent启动  KB v5.0  审计Agent   Movement   三Agent   SDA对     Gate 0+
  时Read 8-12  ~720条   读取设计    Designer   串行:     简单场景  SSA对同
  个文件·每   ·即使路由  Agent完整   978行论证   Shot等   零设计缺  一台本:
  次Read=1   后仍~30条  输出(含    "6个固定   Movement  陷仍全    正则可检
  次LLM推理   ·每条含   推理·非仅  镜头合理"  等Comp   维度审计   测项+LLM
  ·Comp:33   详述~400   YAML)      ·静态快   ·每个等   ·Gate 0  重复检测
  次调用!     tokens               速通道前   待上游    前置前     ·Gate 0
                                   的旧行为   ·1,457s  无意义    前置前
                                             comp!               的SSA
```

### 5.2 根因量化分析

| 根因类别 | 贡献占比 | 旧管道证据 | 量化影响 |
|---------|:------:|-----------|---------|
| **文件读取开销** | ~25% | Comp: 33次工具调用(1,457s)·其中~20次为Read文件 | 每Read≈3-5s·33次≈100-165s。占Comp总时间~10%。但所有Agent累计Read约100+次。 |
| **大KB加载** | ~20% | Comp加载KB v5.0(~50K字)后仍需阅读·30条规则详述≈12K tokens推理开销 | KB推理开销≈200-300s/Agent(含规则匹配+引用验证) |
| **上游输出膨胀** | ~15% | SSA读全部上游输出(177K tokens)·80%为推理(不参与审计) | 浪费≈250s(读推理+过滤非YAML信息) |
| **形式主义论证** | ~15% | Movement Designer: 978行中~700行为"固定镜头合理"辩护 | 浪费≈500s(Movement + 部分Comp) |
| **串行链累积** | ~15% | Shot(857s) + Movement(?s) + Comp(1,457s) = 串行等待 | 总wall-clock = sum·无并行增益 |
| **过度验证** | ~7% | SDA零阻断·SSA三项阻断全正则可检测·但都完整执行LLM调用 | 浪费≈200s(LLM推理做正则可做的事) |
| **重复检查** | ~3% | Gate 0正则扫描 + SSA的LLM重复检查同一条目 | 浪费≈50s(重复推理) |

### 5.3 三阶段改进方案

#### Phase A: 短期 (立即实施·0代码改动)

| # | 措施 | 根因 | 预期收益 |
|---|------|------|:------:|
| A1 | 启用complexity_router·S-Level场景使用2 Agent管道 | 形式主义论证+过度验证+串行链 | S-Level: 3,476s→估~400s (节省88%) |
| A2 | 启用Scene Designer静态快速通道(>=80%固定) | 形式主义论证 | 每S-Level场景节省~500s(Movement论证消除) |
| A3 | 将Gate 0前置到Scene Auditor Phase 0(正则先于LLM) | 重复检查(SSA的LLM做正则可做的事) | SSA从333s→估~100s (节省70%) |
| A4 | IMAGE_AUDIT ∥ OBJECT_TIMELINE ∥ ANCHOR_BASELINE 并行启动 | 串行链(前置步骤) | 前置时间从T1+T2+T3→max(T1,T2,T3)·节省~40% |

**短期总收益:** S-Level: ~3,476s → ~400s (88% wall-clock节省) · C-Level: ~3,476s → ~2,500s (28%节省)

#### Phase B: 中期 (1-2周·需轻量实现)

| # | 措施 | 根因 | 预期收益 |
|---|------|------|:------:|
| B1 | 实现SCENE_CONTEXT_BUNDLE.md预编译 | 文件读取开销 | 每Agent节省~7次Read·C-Level全管道节省~126次Read |
| B2 | KB规则快速参考卡(one-liner + 详述指针) | 大KB加载 | 每Agent KB推理从~200s→~50s |
| B3 | YAML-Only传递(设计Agent输出双文件) | 上游输出膨胀 | 审计Agent上下文从88K→48K·推理时间减半 |
| B4 | S-Level批量设计(最多3场景/批) | 多场景扩展性 | 5场景从10 Agent→4 Agent |

**中期总收益:** C-Level: ~2,500s → ~1,500s (在此基础上再省40%) · S-Level: ~400s → ~250s

#### Phase C: 长期 (管道重设计·需架构变更)

| # | 措施 | 根因 | 预期收益 |
|---|------|------|:------:|
| C1 | 调度器注入公共上下文(Agent prompt预填充) | 文件读取开销(彻底消除) | Agent启动时0次Read(仅Read剧本+参考图) |
| C2 | KB规则编译为向量索引(语义检索替代文本路由) | 大KB加载 | KB加载从Read文件→向量检索·~10s |
| C3 | 分阶段Agent输出(先YAML·后推理)·下游提前启动 | 串行链累积 | PLAN可与设计"近并行"·wall-clock节省~20% |
| C4 | 多场景Pipeline-as-DAG(有向无环图调度) | 全管道架构 | 全局最优并行调度·最大化资源利用 |

**长期总收益:** C-Level: ~3,476s → ~800s (77%节省) · S-Level: ~3,476s → ~150s (96%节省)

### 5.4 具体长推理Agent的根因与修复

#### Composition Designer (1,457s → 33工具调用)

```
根因诊断:
  1. KB v5.0是单一巨型文件(~720条·~50K字) → 即使路由后仍加载大量文本
  2. 33次工具调用中~20次为Read操作(文件加载·KB查询)
  3. 每次Read操作=LLM需要处理整个文件上下文·累积巨大推理开销
  4. 三域中最复杂的域(构图+光影+色彩+景深+光源锚点) → 本身推理密集

修复:
  短期: KB路由后只加载快速参考卡·需要详述时Read具体章节(而非全文)
  中期: 场景上下文包预编译·构图域直接从包中取空间坐标系+光源信息
  长期: KB矢量检索替代文本路由

预期: 1,457s → 400-600s (节省59-73%)
```

#### Scene Script Auditor (333s · 177K tokens · 15工具调用)

```
根因诊断:
  1. 读取prompt_composer完整台本(含推理·含设计依据块) → 80%不参与审计
  2. 15次工具调用中~10次为Read上游Agent输出文件(含推理)
  3. Gate 0可正则检测的3项阻断(B01/B02/R14) → SSA也做了LLM推理(浪费)
  4. 上下文巨大(177K tokens) → LLM需要在大量文本中找到审计目标

修复:
  短期: Gate 0前置到Phase 0(正则先于LLM) → SSA不再检查Gate 0已覆盖项
  中期: YAML-Only传递 → SSA只读台本YAML块(非完整prompt_composer推理)
  长期: SSA作为Scene Auditor Phase 3的一部分·上下文复用

预期: 333s → 100-150s (节省55-70%)
```

---

## 综合: 三级优化路线图

### 短期 (立即·本周)

```
优先级 P0:
  ☐ 修复4个阻断项(BLOCK-1 ~ BLOCK-4·见监督报告)
     ├─ Gate 0 R14/R15编号统一
     ├─ scene_auditor M-Level支持补充
     ├─ scene_designer S/M描述与complexity_router对齐
     └─ S-Level台本初稿格式定义
  ☐ 启用complexity_router·S-Level走2 Agent管道
  ☐ 启用Scene Designer静态快速通道(R-SFAST-01~03)
  ☐ IMAGE_AUDIT + OBJECT_TIMELINE + ANCHOR_BASELINE 并行启动

预期效果:
  EP14场景A(S-Level): 875K tokens·3,476s → 估~120K tokens·~400s (wall-clock节省88%)
  EP14场景B(M-Level): 估~250K tokens·~1,200s (vs 当前同场景A的3,476s)
  总Agent调用: ~18次 → 2次(S-Level) + 4-7次(M-Level)
```

### 中期 (1-2周)

```
优先级 P1:
  ☐ 实现SCENE_CONTEXT_BUNDLE.md预编译脚本
  ☐ 建立KB快速参考卡格式(kb_index_v2.0输出双版本)
  ☐ Scene Designer实现双文件输出(.md推理 + .yaml结构化)
  ☐ S-Level批量设计(2-3场景/批)
  ☐ 修复6个警告项(WARN-1 ~ WARN-6·见监督报告)

预期效果:
  上下文节省: 每Agent从~88K → ~45K (节省49%)
  Agent调用: S-Level批量: 5场景·10 Agent → 4 Agent
  wall-clock: C-Level ~2,500s → ~1,500s
```

### 长期 (管道重设计)

```
优先级 P2:
  ☐ 调度器prompt预填充能力(公共上下文直接注入)
  ☐ KB矢量索引替代文本读取检索
  ☐ 分阶段Agent输出(先YAML·后推理)·启用"近并行"
  ☐ Pipeline-as-DAG调度器(全局最优并行拓扑)
  ☐ 自动复杂度路由+动态管道深度调整

预期效果:
  wall-clock: C-Level ~800s · S-Level ~150s
  上下文爆炸: 彻底消除(Agent启动时0-2次Read)
  多场景: 10场景C-Level从180 Agent → ~30 Agent
```

---

### 附录: 关键发现总结

1. **最大单一收益:** complexity_router S-Level管道——EP14场景A从3,476s降至估~400s·节省88%。这是ROI最高的单项改进。

2. **最危险的架构缺陷:** scene_auditor M-Level支持缺失(BLOCK-2)——M-Level占复杂度分类的中间层·但没有审计规范可依。如果不修复·M-Level场景的台本质量失去保证。

3. **最常见的浪费模式:** "什么都不做的论证"——Movement Designer为静态镜头写978行辩护。静态快速通道(R-SFAST-01~03)是此问题的直接解药。

4. **最被低估的优化:** 公共上下文预编译——当前每个Agent浪费~50K tokens重复加载相同文件。一次性修复·对所有Agent生效。

5. **管道深度的反直觉规律:** EP14数据表明——管道步骤越多·每个步骤的边际价值越低。S-Level 2 Agent管道的质量并不比C-Level 18 Agent管道低(对简单场景而言)——因为18 Agent中的12个步骤在做"橡皮图章"工作。

---

> **分析完成日期:** 2026-07-07
> **分析依据:** dispatcher_v5.0 · complexity_router_v1.0 · scene_designer_v1.0 · scene_auditor_v1.0 · P-CONSTITUTION · EP14剧本 · EP14_SUPERVISION_REPORT
> **方法论:** 步骤必需性矩阵 + 依赖拓扑分析 + 上下文爆炸诊断 + 可扩展性评估 + 根因鱼骨图
