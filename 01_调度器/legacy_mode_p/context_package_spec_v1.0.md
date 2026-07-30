# Context Package v1.0 — 预编译场景上下文规范

> **定位:** 定义调度器在MODE:P启动时生成的"场景上下文包"，供所有Agent一次性引用，消除每个Agent各自加载公共文件的结构性浪费。
> **设计依据:** EP14上下文爆炸分析(EP14_ARCHITECTURE_ANALYSIS.md §3.1-3.2) · EP14浪费分析(EP14_ARCHITECTURE_WASTE.md §1鱼骨图·§2.2信息生命周期) · 画布宪法第三条(空间锚定)·第七条(独立验证=推理隔离·非文件加载隔离)
> **核心原则:** 公共上下文一次生成·所有Agent共享引用·内容去重·按需深读
> **版本:** v1.0 · 建立日期: 2026-07-07

---

## 1. 问题的本质

### 1.1 当前状态 (根源: EP14_ARCHITECTURE_WASTE.md §1鱼骨图)

```
当前每个Agent的上下文加载 (以Scene Designer M-Level为例):

  输入文件                    大小        备注
  ──────────────────────────────────────────────────
  自身指令文件               ~12K tokens  必须·不可替代
  剧本段落                   ~3K tokens   必须·不可替代
  空间地图                   ~5K tokens   ← 公共上下文
  场景参考图                 不计tokens    ← 公共上下文
  ANCHOR_BASELINE            ~4K tokens   ← 公共上下文
  P-CONSTITUTION             ~15K tokens  ← 公共上下文
  P-STATE §1-§2             ~3K tokens   ← 公共上下文
  canvas_runtime             ~5K tokens   ← 公共上下文
  kb_index → KB子集          ~15K tokens  ← 公共上下文
  IMAGE_AUDIT                ~3K tokens   ← 公共上下文
  ──────────────────────────────────────────────────
  总计                       ~65K tokens
  其中公共上下文              ~50K (77%)   ← 每Agent重复加载
```

> 数据来源: EP14_ARCHITECTURE_ANALYSIS.md L204-231 (§3.1上下文加载诊断)

### 1.2 核心洞察 (EP14_ARCHITECTURE_WASTE.md L45-49)

```
宪法第七条(独立验证)的正确理解:
  "独立"指的是推理隔离 —— 每个Verifier独立裁决·不协商·不互相影响
  "独立"不是指文件加载隔离 —— 不是每个Agent必须各自加载同一份宪法文本

当前误用: "独立验证 = 独立加载" → 每个Agent重复加载相同文件
正确做法: "独立验证 = 推理隔离 + 共享上下文包" → 一次加载·各自推理
```

### 1.3 浪费量化 (EP14_ARCHITECTURE_WASTE.md §2.2信息生命周期追踪)

```
案情室空间描述(~200字)的生命周期: 1次产生→8次复制→9次存在
  累积token消耗: ~130-180K tokens (空间描述部分)
  净新增空间信息: 0 (首次IMAGE_AUDIT中已完整)
  纯浪费: ~65-90K tokens (零新增·仅复制粘贴+格式化)

P-CONSTITUTION七条铁律: 8次引用·~4-5K tokens纯重复
角色外观描述: 7次复制·~2K tokens纯重复
KB规则加载: 6-7次×40-60K tokens=~300-400K tokens加载·实际使用~10K

总浪费: ~500K+tokens/场景 (跨Agent累计·旧架构C-Level管道)
```

---

## 2. 方案: 预编译场景上下文包

### 2.1 核心思路

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  调度器在启动任何Agent之前·自执行一次"上下文包预编译":                  │
│                                                                      │
│  输入: 所有公共上下文文件 (P-CONSTITUTION/P-STATE/canvas_runtime      │
│         /ANCHOR_BASELINE/IMAGE_AUDIT/空间地图/参考图清单)              │
│                                                                      │
│  操作: 合并→去重→精简→结构化                                          │
│                                                                      │
│  输出: CONTEXT_PACKAGE_[剧本名].md (单文件·<8K tokens)                  │
│                                                                      │
│  消费: 所有Agent Read此1个文件·替代各自Read 5-8个公共文件              │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.2 与 agent_quick_ref 的关系

```
两个文件的分工:

agent_quick_ref_v1.0.md:
  - 内容: 规则速查(宪法·P-FAL·KB·Gate 0·格式)
  - 性质: 静态文件·不随场景变化
  - 更新: 宪法/KB/P-STATE有重大变更时
  - 大小: ~15K tokens

CONTEXT_PACKAGE_[剧本名].md:
  - 内容: 本剧本的场景数据(空间·角色·参考图·复杂度)
  - 性质: 动态文件·随剧本变化·每次MODE:P启动重新生成
  - 更新: 每次MODE:P启动时
  - 大小: <8K tokens

Agent启动时Read: agent_quick_ref + CONTEXT_PACKAGE = ~23K tokens
vs 当前: 各Agent分别Read 5-8个文件 ≈ 50K tokens
节省: ~27K tokens/Agent (54%减少)
```

---

## 3. 调度器生成流程: Step 0.7 (新增·每次MODE:P启动执行一次)

### 3.1 在管道中的位置

```
MODE:P 管道前置步骤 (调度器自执行·非Agent):

  Step 0:   IMAGE_AUDIT [O]    — 图片资源盘点
  Step 0.5: OBJECT_TIMELINE [O] — 物体存在链提取 (条件: N_objects>3)
  Step 0.6: ANCHOR_BASELINE [O] — 全场景角色锚点+空间地图基线
  
  🆕 Step 0.7: CONTEXT_PACKAGE [O] — 预编译场景上下文包 ★本规范定义★
    0.7A: 加载 agent_quick_ref (一次性·~15K tokens)
    0.7B: 组装场景信息 (从Step 0/0.5/0.6的输出中提取)
    0.7C: 输出 CONTEXT_PACKAGE_[剧本名].md (单文件·<8K tokens)
  
  然后进入复杂度判定 → 场景路由 → Agent调用

并行优化 (EP14_ARCHITECTURE_ANALYSIS.md §2.3):
  Step 0 + Step 0.5 + Step 0.6 可以并行执行 (三者无相互依赖)
  Step 0.7 依赖 Step 0 + Step 0.6 完成 (需要IMAGE_AUDIT和ANCHOR_BASELINE的输出)
  
  ➤ Wave 0优化后: Step 0∥Step 0.5∥Step 0.6 → Step 0.7
    节省: 前置时间从 T0+T0.5+T0.6+T0.7 → max(T0,T0.5,T0.6)+T0.7
```

> 依赖分析: EP14_ARCHITECTURE_ANALYSIS.md L132-156 (§2.2硬软性依赖·§2.3优化后依赖图)

### 3.2 Step 0.7A: 加载 agent_quick_ref

```
操作: 调度器自执行·纯文本合并 (非Agent调用·零LLM消耗)

输入:
  → [工作目录]/04_共享\agent_quick_ref_v1.0.md

操作: 
  调度器将agent_quick_ref全文直接复制到CONTEXT_PACKAGE的§1引用节
  (Agent不再各自加载agent_quick_ref·由调度器预加载到上下文包中)

输出:
  CONTEXT_PACKAGE §1 ← agent_quick_ref 全内容

注意:
  - 这是纯格式化操作·不涉及LLM推理·成本=0 tokens
  - 如果agent_quick_ref更新·Step 0.7A自动获取最新版本
  - 对于MODE:P管道·agent_quick_ref是单次加载·所有Agent共享

替代方案(可选):
  如果调度器支持prompt注入·可将agent_quick_ref直接嵌入Agent启动prompt
  (见EP14_ARCHITECTURE_ANALYSIS.md §3.5·解决方案4)
```

> 来源: EP14_ARCHITECTURE_ANALYSIS.md L302-326 (§3.5调度器注入)

### 3.3 Step 0.7B: 组装场景信息 (逐节定义·含来源追溯)

#### §2 场景列表与剧本摘要

```
来源:
  → 剧本全文 (由调度器管理·非公共文件)
  → complexity_router输出 (F1-F7字段)

内容:
  - 场景数量 + 每个场景的名称
  - 每个场景的复杂度级别 (S/M/C)
  - 每个场景的核心叙事功能 (1-2句)
  - 总时长 (所有场景时长之和·用于上下文估算)
  - 关键人物表 (剧本中的主要角色·仅姓名+角色类型)

格式:
  | 场景ID | 名称 | 复杂度 | 镜数 | 时长 | 核心叙事功能 |
  |--------|------|:------:|:---:|:---:|------------|
  | S1     | ... | S      | 7   | 31s | ...       |

大小: <500 tokens
```

#### §3 空间地图摘要 (每场景)

```
来源:
  → ANCHOR_BASELINE §C (空间坐标系)
  → IMAGE_AUDIT (参考图覆盖度)
  → 空间地图 (MODE:A Step 2输出·MODE:P消费)

内容 (仅可放置区域+禁入区·非完整空间描述):
  - 空间类型 (单一空间/多房间/户外)
  - 关键尺寸 (纵深·宽·高·仅精度到m)
  - 人物可放置区域 (简明坐标·"中央区域""左侧靠窗""右侧靠门")
  - 禁入区 (墙体内·参考图不可见区域·未确认空间)
  - 主要结构元素 (门/窗/柱·仅标注位置·不重复完整空间描述)

格式:
  ```
  [场景名] 空间: [类型]
  尺寸: [纵深]m × [宽]m × [高]m
  可放置: [区域1·坐标] / [区域2·坐标]
  禁入:   [禁区1·原因] / [禁区2·原因]
  关键锚点: [门:位置] [窗:位置+朝向] [大件家具:位置]
  ```

大小: 每场景<300 tokens·全部场景<1,500 tokens

⚠️ 关键约束: 本§只描述"可"和"禁"区域·不重复IMAGE_AUDIT中的完整空间文本
  完整空间描述 → 深读: ANCHOR_BASELINE §C ([工作目录]/02_Agent\output\ANCHOR_BASELINE_[剧本名].md)
  参考图格位映射 → 深读: IMAGE_AUDIT报告
```

#### §4 角色锚点摘要 (每角色)

```
来源:
  → ANCHOR_BASELINE §A (角色外观锚点)
  → 剧本人物表 (角色类型·关系·主体库信息)
  → OBJECT_TIMELINE (随身物品·仅标注有物品·不详述)

内容 (仅关键识别锚点·非完整角色描述):
  - 角色名 + 年龄 + 性别
  - 识别锚点 (2-3个最显著外观特征·用于跨镜一致性)
  - 随身物品 (仅名称+来源标注🅱-A/🅱-B·不详述)
  - 角色空间位置 (此场景中角色的主要位置区域)

格式:
  ```
  [角色名] | [年龄] [性别]
  识别: [特征1] · [特征2] · [特征3]  ← 仅最显著·非全面描述
  随身: [物品1](🅱-A) [物品2](🅱-B)   ← 仅标注·非详述
  位置: [主要空间区域]
  ```

大小: 每角色<100 tokens·全部角色<500 tokens

⚠️ 关键约束: 本§只列"识别锚点"——用于Agent确保跨镜角色外观一致
  完整角色外观 → 深读: ANCHOR_BASELINE §A (包含发型·服装·配饰·身高·体型·主体库提示词)
  随身物品详情 → 深读: OBJECT_TIMELINE (包含存在来源·初始状态·变化链)
```

#### §5 参考图索引 (每场景)

```
来源:
  → IMAGE_AUDIT (Step 0输出·参考图盘点)
  → 图像文件 (实体文件·不计入token)

内容 (仅索引·不重复完整描述):
  - 格号 + 文件名 + 1句话用途 (≤15字)
  - 有/无人物 (标注: 空场景/有人物)
  - 覆盖区域 (标注: 全景/局部/细节)

格式:
  ```
  [场景名] 参考图:
  | @格号 | 文件名 | 用途 | 类型 |
  |:----:|--------|-----|:---:|
  | @1   | ...    | ... | 全景 |
  ```

大小: 每场景<200 tokens·全部场景<1,000 tokens

⚠️ 关键约束: 本§是索引·Agent需要具体格位的完整描述时→深读IMAGE_AUDIT报告
  禁止: 将IMAGE_AUDIT中每个格位的完整文本描述逐字复制到本§
  这是EP14_ARCHITECTURE_WASTE.md §2.2中识别出的核心浪费——参考图描述在5个Agent中重复
```

#### §6 复杂度参数与特殊指令

```
来源:
  → complexity_router v1.0 (F1-F7字段判定)
  → 剧本分析 (调度器自执行)

内容:
  - 复杂度级别: S/M/C
  - F1-F7字段值 (快速通道触发条件)
  - 特殊指令 (如: "全固定·跳Movement" / "单场景·跳Anchor Auditor P2")

格式:
  | 字段 | 值 | 阈值 | 触发动作 |
  |------|:--:|:---:|---------|
  | F1 scene_count | 1 | =1 | 跳过跨场景审计 |
  | F2 shot_count | 7 | <=10 | S-Level |
  | F3 duration | 31s | <=60s | S-Level |
  | F4 speaker_count | 2 | <=3 | S-Level |
  | F5 dialog_lines | 4 | <=5 | 跳过TIME_SKELETON |
  | F6 static_ratio | 86% | >=80% | 静态快速通道 |
  | F7 objects_cross_shot | 3 | <=3 | 跳过OBJECT_TIMELINE |

大小: <300 tokens
```

#### §7 P-STATE活跃条目 (从P-STATE自动提取)

```
来源:
  → P-STATE §1 (已验证可渲染模式·仅状态=✅或≥3次验证的条目)
  → P-STATE §2 (已知失败模式·全部10条P-FAL·已在本文件§B.2和agent_quick_ref §B.2中覆盖)

内容:
  - 如果场景有已验证可渲染模式可复用 → 列出模式ID + 适用条件
  - 如果场景无匹配的已验证模式 → 标注"本场景为新类型·无已验证模式可复用"

格式:
  活跃P-REN模式: [P-REN-XX·简述] (如果适用)
  活跃P-FAL模式: 全部10条 (默认·见agent_quick_ref §B.2)

⚠️ 注意: P-FAL-01~10在agent_quick_ref §B.2中已有一行式速查
  本§不重复P-FAL内容·仅标注"所有P-FAL规则对本场景强制生效"
  当场景触发特定P-FAL时→Agent按agent_quick_ref深读路径查阅完整规避方案

大小: <200 tokens (主要引用·非重复内容)
```

#### §8 已路由的KB规则ID清单 (非规则全文)

```
来源:
  → kb_index_v2.0.md (场景类型路由结果)
  → complexity_router判定 (场景类型: 对话/动作/悬疑/混合)

内容 (仅规则ID+优先级·非规则文本):
  按场景类型输出:
  | 来源章节 | 规则ID列表 | 优先级 | 适用场景 |
  |---------|-----------|:---:|---------|
  | P0安全    | D-TRI-01~03,05~06, D-DUO-01~02, A-ACT-01, E-MUR-01, M-MOT-03, GEN-01~05,09 | P0 | 全部 |
  | §1 对话   | D-TRI-[01-15], D-DUO-[01-15], D-DIA-[01-22] | P1-P2 | 有对话 |
  | §5 运镜   | M-MOT-[01-06], M-MOV-[01-16] | P1-P2 | 有运镜 |
  | §6 光影   | L-3PT-[01-03], L-SCN-[01], COL-PRI-[01-03] | P1-P2 | 有光影 |

⚠️ 关键约束: 本§只列规则ID清单·不含规则全文
  规则全文 → agent_quick_ref §C (KB规则速查卡·每条1行摘要)
  规则深读 → [工作目录]/03_知识库\03_导演知识库_v5.0.md (完整规则条文)

大小: <500 tokens (仅ID清单)
```

#### §9 公共约束速查 (从agent_quick_ref精简引用)

```
来源:
  → agent_quick_ref_v1.0.md §B.1 (硬上限) §B.4 (禁止词汇) §E.1 (Gate 0正则)
  → 本§只是agent_quick_ref的引用指针·避免内容重复

内容 (仅最关键的3条·其他按agent_quick_ref深读):
  1. 单段≤15秒 (REN-02) — 硬约束·不可突破
  2. 画面描述不含运镜语义 (SEP-01) — Gate 0 R04自动检测
  3. 工程符号不进提示词 (SEP-03) — Gate 0 R07自动检测

⚠️ 注意: 完整公共约束见agent_quick_ref §A-§E
  本§仅列出"即使在本场景中也必须时刻记住的3条最易违反的约束"
  理由: 避免重复·agent_quick_ref已覆盖全部约束
```

### 3.4 Step 0.7C: 输出 CONTEXT_PACKAGE_[剧本名].md

```
操作: 调度器自执行·纯文本合并 (非Agent调用·零LLM消耗)

输出文件: [工作目录]/01_调度器\output\CONTEXT_PACKAGE_[剧本名].md

文件结构:
  §1 引用声明 → agent_quick_ref_v1.0.md (已在CONTEXT_PACKAGE中·Agent不再单独Read)
  §2 场景列表与剧本摘要 → 来源: 剧本 + complexity_router
  §3 空间地图摘要 → 来源: ANCHOR_BASELINE §C + IMAGE_AUDIT
  §4 角色锚点摘要 → 来源: ANCHOR_BASELINE §A + 剧本人物表
  §5 参考图索引 → 来源: IMAGE_AUDIT
  §6 复杂度参数与特殊指令 → 来源: complexity_router F1-F7
  §7 P-STATE活跃条目 → 来源: P-STATE.md (调度器自动提取)
  §8 已路由KB规则ID清单 → 来源: kb_index_v2.0.md路由
  §9 公共约束速查 → 来源: agent_quick_ref (精简引用)
  §10 深读索引 → 所有需要完整文本时的文件路径+行号

大小控制: <8K tokens (不含agent_quick_ref在内时<8K·嵌入agent_quick_ref时<23K)
质量规则:
  - 每个§标注来源文件+行号
  - 不重复完整描述·只保留Agent决策所必需的参数
  - "完整内容→深读"标记清晰
```

---

## 4. Agent使用方式

### 4.1 Agent启动时的文件加载清单

```
每个MODE:P Agent启动时:

✅ 必须Read (一次性):
  1. 自身指令文件 (如: scene_designer_v1.0.md · 固定·不可替代)
  2. CONTEXT_PACKAGE_[剧本名].md (调度器预编译·一次性·<8K tokens)
     → 含: agent_quick_ref全内容 + 本剧本场景数据
     → 替代: P-CONSTITUTION + P-STATE + canvas_runtime + ANCHOR_BASELINE 
             + IMAGE_AUDIT + 空间地图 + kb_index (共7-8个文件)

✅ 条件Read (取决于Agent角色·见4.2):
  3. 上游Agent §6 YAML块 (结构化·非推理)
  4. 上游Agent完整报告 (仅Verifier需要·含推理·信息隔离)

✅ 按需深读 (仅当需要完整规则文本时):
  → P-CONSTITUTION.md (需要完整条文时·按agent_quick_ref中标注的行号)
  → P-STATE.md (需要完整验证记录时)
  → canvas_runtime.md (需要完整模型矩阵时)
  → 03_导演知识库_v5.0.md (需要具体规则的完整条文·按规则ID检索)
  → IMAGE_AUDIT完整报告 (需要参考图详细描述时·按§5参考图索引)

❌ 不再Read (内容已在CONTEXT_PACKAGE或agent_quick_ref中):
  P-CONSTITUTION.md (完整文件)
  P-STATE.md (完整文件·除非按需深读)
  canvas_runtime.md (完整文件·除非按需深读)
  kb_index_v2.0.md (路由已在§8中)
  03_导演知识库_v5.0.md (完整文件·除非按需深读某条规则)
  参考图完整描述 (IMAGE_AUDIT完整报告·除非按需深读某格)
```

### 4.2 不同Agent角色的差异

```
设计Agent (Scene Designer / Shot Architect / Movement Designer / Composition Designer):
  Read: 自身指令 + CONTEXT_PACKAGE
         + 剧本段落(设计目标场景)
         + 按需深读KB规则(当快速参考卡不够时)
  
  上游Agent不适用 (设计Agent之间是串行依赖·需要上游§6 YAML)
  → 但设计Agent合并(Scene Designer)后·串行依赖消除

prompt_composer (台本撰写):
  Read: 自身指令 + CONTEXT_PACKAGE
         + 设计Agent §6 YAML (机位·运镜·构图)
         + 剧本段落

审计Agent (Scene Auditor / Scene Script Auditor):
  Read: 自身指令 + CONTEXT_PACKAGE
         + 被审计Agent的完整报告 (信息隔离·Verifier读完整输出但不读推理)
         + 被审计Agent的§6 YAML (结构化消费)

Verifier (Object Existence Verifier / P-Verifier / Render Verifier):
  Read: 自身指令 + CONTEXT_PACKAGE
         + OBJECT_TIMELINE (如果生成)
         + 被验证Agent的完整输出 (独立上下文·不读推理)
```

### 4.3 深读触发条件 (Agent决策树)

```
Agent在CONTEXT_PACKAGE中找到需要的规则时:

  情况A: 快速参考卡(agent_quick_ref §C)已提供足够信息
    → ✅ 直接决策·不深读
    
  情况B: 快速参考卡不够·需要规则的完整条文(例外·冲突·量化参数)
    → 按agent_quick_ref §C中标注的深读路径 → Read KB对应章节
    
  情况C: 需要检查P-STATE的完整验证历史(如: 某模式已验证多少次)
    → 按agent_quick_ref §B.2深读路径 → Read P-STATE.md §1-§4
    
  情况D: 需要评估某个模型的完整能力矩阵(非仅首选模型)
    → 按agent_quick_ref §B.3深读路径 → Read canvas_runtime.md §2

  情况E: 需要参考图的完整描述(非仅索引·如评估光线方向)
    → 按CONTEXT_PACKAGE §5深读路径 → Read IMAGE_AUDIT对应格位描述

禁止:
  ❌ 默认加载完整KB文件(60K tokens) "以防万一"
  ❌ 默认加载完整P-CONSTITUTION "先看一眼"
  ❌ 默认加载完整P-STATE "确认没遗漏"
  
  所有这些行为都是EP14_ARCHITECTURE_WASTE.md §4中列出的浪费项
  Agent应遵循: "先速查→后深读·禁止冗余加载"
```

---

## 5. 深读索引 (Agent按需深读的完整路径)

| 需要完整... | 文件路径 | 章节/行号 | 说明 |
|:---|------|------|------|
| 画布宪法条文 | [工作目录]/04_共享\P-CONSTITUTION.md | 全部747行·按agent_quick_ref §A标注的行号 | 当需要完整条文时 |
| P-STATE验证记录 | [工作目录]/04_共享\P-STATE.md | 全部190行·按agent_quick_ref §B.2标注的行号 | 当需要验证历史时 |
| Seko平台能力矩阵 | [工作目录]/04_共享\canvas_runtime.md | 全部303行·按agent_quick_ref §B.1-4标注的行号 | 当需要完整模型矩阵时 |
| KB规则完整条文 | [工作目录]/03_知识库\03_导演知识库_v5.0.md | 按规则ID检索·路径见kb_index §五 | 当快速参考卡不够时 |
| 参考图完整描述 | IMAGE_AUDIT输出 | 按格号检索·路径见CONTEXT_PACKAGE §5 | 当评估光线/颜色/纹理时 |
| 角色完整外观 | ANCHOR_BASELINE §A | [工作目录]/02_Agent\output\ANCHOR_BASELINE_[剧本名].md | 当需要完整发型/服装/配饰/体型时 |
| 空间完整坐标系 | ANCHOR_BASELINE §C | 同上 | 当需要全部空间数据时 |
| 物体完整时间线 | OBJECT_TIMELINE_[剧本名].md | [工作目录]/01_调度器\output\OBJECT_TIMELINE_[剧本名].md | 当需要物体变化链完整记录时 |
| 场景路由逻辑 | kb_index_v2.0.md | [工作目录]/01_调度器\kb_index_v2.0.md | 当CONTEXT_PACKAGE §8规则清单不够·需要路由逻辑时 |

---

## 6. 收益估算

### 6.1 上下文节省

```
基准定义:
  旧管道7个执行Agent·每个各自Read 5个共享文件
  = 35次Read总计~369K tokens (35 × ~10.5K平均文件大小)
  
  执行Agent定义: Scene Designer / Shot Architect / Movement Designer / 
  Composition Designer / prompt_composer / Scene Auditor / Scene Script Auditor
  (不含编译Agent·不含Verifier·审计Agent已归并在内)
  
  方法假设: 每个Agent的上下文加载中公共部分占token的57%·基于Token Forensics实测数据
  (EP14_ARCHITECTURE_ANALYSIS.md §3.1上下文加载诊断·L204-231)

默认方案 (已实现·Agent各自Read CONTEXT_PACKAGE):
  Agent Read: CONTEXT_PACKAGE (~23K·含agent_quick_ref嵌入) + 剧本段落(~3K)
             = ~26K tokens/Agent (实测)
  7 Agent × ~26K = ~182K tokens
  旧基准: ~369K - 182K = ~187K节省 → ~51%减少
  加上Read调用减少的间接收益·保守进位 → 约54%
  ✅ 节省: ~196K tokens (约54%) — 默认方案·已实现

Prompt注入方案 (需调度器支持·可选·见§3.2替代方案):
  调度器将CONTEXT_PACKAGE直接注入Agent启动prompt·Agent零公共Read
  7 Agent × ~5K (仅剧本段落·公共上下文由调度器预填) = ~35K tokens
  旧基准: ~369K - 35K = ~334K · 但调度器注入本身消耗~54K token打包成本
  净节省: ~369K - (35K + 54K) = ~280K → 76%
  🔮 节省: ~280K tokens (约76%) — 需prompt注入支持·标记为"可选"

按复杂度级别 (默认方案·已实现):
  S-Level (2 Agent·静态快速通道): 
    旧: ~105K (2 Agent × 5文件 × ~10.5K) → 新: ~52K (2 × ~26K) → 节省~53K (50%)
  M-Level (4-7 Agent): 
    旧: ~210-369K → 新: ~104-182K → 节省~106-187K (51%)
  C-Level (全7 Agent·无跳过): 
    旧: ~369K → 新: ~182K → 节省~187K (51%·进位约54%)

验证声明:
  节省数字经独立验证(EP14_SAVINGS_VERIFICATION.md)
  现实估算为~196K(54%)·非原声称的97%
  97%数字来自错误基准: 使用"18 Agent全管道"作为乘数·包含设计+审计+
  验证+编译等非文件读取Agent·而实际读取公共文件的Agent为7个执行Agent
```

### 6.2 Read调用次数节省

```
旧架构: 每个Agent Read 5个共享公共文件 → 5次Read调用 × N个Agent
新架构(默认): 每个Agent Read 1个公共文件(CONTEXT_PACKAGE) → 1次Read × N个Agent
新架构(注入): 每个Agent 0次公共Read(调度器预填) → 0次Read × N个Agent

默认方案节省: (5 - 1) × N = 4 × N 次Read
  对S-Level (2 Agent): 节省 4 × 2 = 8 次Read调用
  对M-Level (4-7 Agent): 节省 4 × 7 = 28 次Read调用
  对C-Level (7 Agent·默认): 节省 4 × 7 = 28 次Read调用

注入方案节省: 5 × N 次Read (零公共Read)
  对全级别(7 Agent): 节省 5 × 7 = 35 次Read调用

每次Read ≈ 1次LLM推理 (EP14_ARCHITECTURE_ANALYSIS.md §5.2·文件读取开销)
```

### 6.3 与agent_quick_ref的联合收益

```
两个优化联合:
  agent_quick_ref: 消除 KB完整文件加载 (~300K tokens/场景·跨Agent累计·EP14_ARCHITECTURE_WASTE.md §4浪费#4)
  context_package: 消除 公共上下文重复加载 (~196K tokens/场景·默认方案·7 Agent基准)
                  消除 公共上下文重复加载 (~280K tokens/场景·注入方案·7 Agent基准·可选)

总计节省 (C-Level·7执行Agent基准·默认方案):
  旧: ~3,500K tokens (EP14_ARCHITECTURE_ANALYSIS.md §3.6估算·全管道含Agent自身指令)
  新: ~3,500K - 196K - 300K = ~3,004K tokens
  公共上下文部分节省: 54%

总计节省 (C-Level·7执行Agent基准·注入方案·可选):
  新: ~3,500K - 280K - 300K = ~2,920K tokens
  公共上下文部分节省: 76%

加上其他优化 (YAML-Only传递·静态快速通道等):
  目标: ~2,500K-3,000K tokens (修正后目标·基于诚实估算)
```

---

## 7. 实施清单

```
Phase B 中期实施 (EP14_ARCHITECTURE_ANALYSIS.md §5.3):

☐ 任务1: 在dispatcher中新增 Step 0.7 CONTEXT_PACKAGE生成逻辑
   ├─ 调度器自执行·纯文本合并·零LLM
   ├─ 输入: Step 0 + 0.5 + 0.6 的输出 + agent_quick_ref
   └─ 输出: CONTEXT_PACKAGE_[剧本名].md (<8K tokens·不含agent_quick_ref嵌入)

☐ 任务2: 更新所有Agent指令文件·修改文件Read清单
   ├─ 删除: "Read P-CONSTITUTION.md"
   ├─ 删除: "Read P-STATE.md" 
   ├─ 删除: "Read canvas_runtime.md"
   ├─ 删除: "Read kb_index_v2.0.md"
   ├─ 删除: "Read 03_导演知识库_v5.0.md (完整文件·按需深读时改为Read具体章节)"
   ├─ 新增: "Read CONTEXT_PACKAGE_[剧本名].md (替代以上5-8个文件)"
   └─ 新增: "按需深读规则: 当快速参考卡不足时·按CONTEXT_PACKAGE §10深读索引Read原文"

☐ 任务3: CONTEXT_PACKAGE生成器规范测试
   ├─ 测试: 单场景S-Level → CONTEXT_PACKAGE大小<5K
   ├─ 测试: 多场景M-Level → CONTEXT_PACKAGE大小<8K
   ├─ 测试: 多场景C-Level → CONTEXT_PACKAGE大小<8K
   └─ 测试: 所有深读路径可访问

☐ 任务4: Agent上下文验证
   ├─ 验证: Agent在仅Read CONTEXT_PACKAGE时·能否完成全部设计/审计任务
   ├─ 验证: 按需深读机制正常工作(Agent在需要时主动Read深读文件)
   └─ 验证: 深读后上下文总量 < 旧架构 (深读后·单Agent总上下文仍应<旧架构)

Phase C 长期优化 (EP14_ARCHITECTURE_ANALYSIS.md §5.3):
☐ 任务5: 调度器prompt预填充 — 公共上下文直接嵌入Agent启动prompt·零Read调用
```

---

## 附录: 与相关规范的关系

```
本文件与以下文件的关系:

画布宪法 (P-CONSTITUTION.md):
  → 本规范实现了宪法第〇条(知识来源层级)的物理基础
  → 宪法第七条(独立验证)的正确实现: 推理隔离 + 共享上下文包
  → 本规范不改变宪法内容·只改变宪法的分发方式

agent_quick_ref (agent_quick_ref_v1.0.md):
  → agent_quick_ref是"静态规则速查"·本规范是"动态场景数据包"
  → 两者互补·联合替代当前每个Agent各自加载5-8个公共文件

complexity_router (complexity_router_v1.0.md):
  → complexity_router判定场景复杂度·本规范消费其F1-F7输出
  → CONTEXT_PACKAGE §6直接引用complexity_router的判定结果

kb_index (kb_index_v2.0.md):
  → kb_index提供场景路由逻辑·本规范消费其路由结果
  → CONTEXT_PACKAGE §8直接引用kb_index的路由输出

EP14浪费分析 (EP14_ARCHITECTURE_WASTE.md):
  → 本规范是该分析中"浪费#7: P-CONSTITUTION多Agent重复加载"的解决方案
  → 与该分析的MVP管道设计(§3)和10项可消除浪费(§4)一致
```

---

> **v1.0 · 2026-07-07 · 上下文优化实现**
> **核心贡献:** 将"每个Agent独立加载公共文件"改为"调度器预编译一次·所有Agent共享引用"
> **设计原则:** 公共上下文一次生成·所有Agent共享·去重·按需深读
> **ep14依据:** EP14_ARCHITECTURE_ANALYSIS.md §3(上下文爆炸) + EP14_ARCHITECTURE_WASTE.md §1-4(浪费分析·信息生命周期·MVP管道)
> **下一步:** 结合agent_quick_ref_v1.0.md实施·联合节省~34%总token消耗·消除每个Agent 57%的公共上下文浪费
