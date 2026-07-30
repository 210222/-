# 独立监督报告 -- Phase 1 产出审查

> **审查日期:** 2026-07-07
> **审查范围:** complexity_router_v1.0.md / scene_designer_v1.0.md / scene_auditor_v1.0.md
> **参考基线:** dispatcher_v5.0.md / P-CONSTITUTION.md / TIME_SKELETON_spec.md
> **审查原则:** 只看最终产出，不看推理过程。批判性审查，找矛盾，找遗漏。

---

## 1. 跨文件一致性

### 1.1 complexity_router 分级定义 --> scene_designer 逐级对应

| 维度 | complexity_router 定义 | scene_designer 定义 | 一致性 |
|------|----------------------|-------------------|:---:|
| S-Level 角色数 | <=3 speakers | "单角色" (§1.2) | **矛盾** |
| S-Level 空间 | 单空间(1) | "单空间" | 一致 |
| S-Level 对白 | <=5句 | "情绪单一·3-5镜" (未显式约束对白数) | **模糊** |
| M-Level 角色数 | 4-6 speakers | "双人对话" (§1.2) | **矛盾** |
| M-Level 空间 | 2空间 | "单空间" (§1.2) | **矛盾** |
| M-Level 对白 | 6-15句 | "5-10镜" (未显式约束对白数) | **模糊** |
| C-Level 角色数 | >=7 speakers | "多人对话" | 大致一致 |
| C-Level 空间 | >=3空间 | "多空间" | 一致 |

**详细分析:**

**(A) S-Level 角色数矛盾:**
- complexity_router §1.3: "N_speakers <= 3" 是S-Level必要条件
- scene_designer §1.2 S-Level行: "单角色·单空间·情绪单一·3-5镜"
- "单角色" = 1人，但 complexity_router 允许多达3人
- 后果: 一个2人对话场景(满足S-Level其他条件)被分类器标为S-Level，但 scene_designer 的S-Level流程说"单角色"——Agent可能认为自己不该处理2人场景，导致输出不足或行为异常

**(B) M-Level 角色数与空间数矛盾:**
- complexity_router §1.4: M-Level触发条件包括 N_spaces=2、N_speakers in [4,6]
- scene_designer §1.2 M-Level行: "双人对话·单空间·5-10镜"
- "双人对话" = 2人，但M-Level触发阈值是4-6人
- "单空间" = 1空间，但M-Level触发条件之一是2空间
- 后果: 一个4人-双空间场景(complexity_router判定:M-Level)交给 scene_designer，其M-Level流程描述却暗示"双人单空间"，Agent可能低估场景复杂度

**(C) M-Level 对白数未显式约束:**
- complexity_router M-Level: N_dialogue in [6, 15]
- scene_designer M-Level: "5-10镜" (镜头数，非对白数)
- 虽然 "镜数" 与 "对白数" 非同一维度，但scene_designer未提及M-Level的对白范围，可能导致Agent对长对白场景准备不足

**裁决: scene_designer §1.2 的场景级别描述与 complexity_router 的判定规则在 S/M 两级存在事实性矛盾。需要统一。**

### 1.2 complexity_router 分级定义 --> scene_auditor 逐级对应

| 维度 | complexity_router 定义 | scene_auditor 定义 | 一致性 |
|------|----------------------|-------------------|:---:|
| 三级分类 | S / M / C | C-Level(三Agent) / S-Level(单Scene Designer) / 纯骨架 | **M-Level缺失** |
| M-Level输入 | 设计Agent 1-2个 | 输入矩阵中无M-Level列 | **遗漏** |
| M-Level审计 | 合并审计+Gate 0 | Phase 4.7降级策略仅提及S/C | **遗漏** |

**详细分析:**

**(A) M-Level 在 scene_auditor §1 输入矩阵中完全缺失:**
- scene_auditor §1 输入矩阵列: "C-Level (三Agent)" / "S-Level (单Scene Designer)" / "纯骨架(Skip PLAN)"
- M-Level 场景在 complexity_router 中有明确定义(§1.4): 4-6个Agent调用，设计Agent可拆分或合并
- M-Level 的设计侧有两种配置: (a) Shot独立 + Movement+Composition合并 (2个设计Agent); (b) Shot独立 + Movement独立 + Composition独立 (3个设计Agent，类似C-Level)
- scene_auditor 没有定义这两种M-Level配置下的审计行为

**(B) scene_auditor §4.7 "S-Level降级策略" 无M-Level:**
- 该节仅描述 S-Level(跳过三Agent内部一致性) 和 C-Level特有检查(追加三域矛盾检测)
- M-Level 的"Shot独立 + Movement+Composition合并"配置(2个设计Agent)不匹配S-Level(单Agent)也不匹配C-Level(三Agent独立)——存在一个未处理的中间配置

**(C) scene_auditor §5.9 Phase 2降级策略 无M-Level专属路径:**
- 降级策略表: 有PLAN+故事板 / 有PLAN无故事板 / 无PLAN(纯S-Level)
- M-Level 中 Storyboard Planner 是条件触发的(见 complexity_router §2.2: N_spaces=2 / Has_action / N_dialogue>=10 / R_static<0.50)
- M-Level场景可能触发Planner也可能不触发——scene_auditor 需处理"有PLAN"和"无PLAN"两种M-Level子情况，但未区分

**裁决: scene_auditor 对 M-Level 的支持存在系统性缺失。输入矩阵、降级策略、级别特定检查均未覆盖 M-Level。**

### 1.3 scene_designer 输出YAML --> scene_auditor 审计维度消费

| scene_designer YAML块 | scene_auditor 消费维度 | 能否消费 |
|----------------------|---------------------|:---:|
| §7.1 (§4 机位域): segments_camera + frames_hard | Phase 1: 维度1A(KB覆盖率) + 1B(帧间连续性) + 1D(空间可行性) | 可消费 |
| §7.2 (§5 运镜域): segments_movement + transitions | Phase 1: 维度1A + 1B + 1D + Phase 2: 2E(过渡对齐) | 可消费 |
| §7.3 (§6 构图光影域): global_anchors + frames_soft | Phase 1: 维度1A + 1C(锚定) + Phase 2: 2B/2D/2F | 可消费 |
| §6d 导演台本初稿(S-Level) | Phase 3: 台本域审计(维度3A-3E) | 可消费 |

YAML字段映射基本正确。scene_designer §7.4 明确标注了每个YAML块到TIME_SKELETON字段的映射和到下游消费者的路径，与 scene_auditor 的消费维度吻合。

**值得注意的问题:**
- S-Level管道中，scene_designer 直接产出§6d导演台本初稿(跳过PC)，但 scene_auditor Phase 3 假设输入是"prompt_composer从TIME_SKELETON展开的导演台本"。S-Level没有PC没有PLAN——scene_auditor Phase 3能否直接审计Scene Designer的台本初稿？文档未显式说明这一点。
- scene_auditor Phase 2 依赖 PLAN_[场景].md (含TIME_SKELETON)。S-Level跳过Planner时，Phase 2降级为仅2C+2G。但 scene_designer §7 仍然产出完整YAML——这些YAML与降级后的Phase 2之间没有消费关系。YAML产出在S-Level中可能成为"无人读取的产物"。

### 1.4 术语一致性检查

| 术语 | complexity_router | scene_designer | scene_auditor | 一致性 |
|------|:--:|:--:|:--:|:---:|
| 场景级别参数名 | (隐式) S/M/C-Level | `complexity_level: "S"/"M"/"C"` | "复杂度级别: C-Level/S-Level" | **S/M命名不一致** |
| Gate 0 规则编号 | R01-R15 (含R14画面外描述,R15光源锚定) | (不涉及) | R01-R15 (R14运镜语义,R15画面外声音源) | **R14/R15定义矛盾** |
| YAML块命名 | 不涉及 | §4机位域 / §5运镜域 / §6构图光影域 | 引用TIME_SKELETON字段名(segments/frames) | 需跨文档映射 |
| OBJECT_TIMELINE | "OBJECT_TIMELINE" | 引用"OBJECT_TIMELINE"(§8.2第六条) | "OBJECT_TIMELINE"(尚未直接引用) | 一致 |
| 复杂度声明格式 | §3.4定义固定格式 | (不涉及) | (不涉及) | N/A |

**关键矛盾详析:**

**(A) Gate 0 R14/R15 编号冲突:**
- **complexity_router §2.5 后置Gate 0:**
  - R14: "画面外描述: 含'画面外/镜头外/屏幕外/画框外' --> 🛑 (画布宪法第一条)"
  - R15: "光源锚定: 每个光源描述是否可追溯参考图 --> warning(正则辅助·LLM为主)"
- **scene_auditor §3.2:**
  - R14 (新增): "Action块含运镜语义" -- 检测运镜动词出现在画面描述中
  - R15 (新增): "Action块含画面外声音源" -- 检测"画框外/镜头外...传来/响起"
- **P-CONSTITUTION §5.1 仅定义 R01-R13**，没有R14/R15

这意味着同一编号(R14, R15)在两个文件中指代完全不同的检查项。当调度器或Agent引用"Gate 0 R14"时，无法确定指的是哪个定义。

此外，complexity_router的R14(画面外描述)在scene_auditor中被R15部分覆盖(画面外声音源)但没有被任何单一规则完整覆盖。complexity_router的R15(光源锚定)在scene_auditor中被归入Phase 1维度1C和Phase 3维度3C04(LLM为主的概率性检查)，而非Gate 0确定性扫描。

**(B) 级别参数命名不统一:**
- scene_designer 使用 `complexity_level: "S" | "M" | "C"` (字符串参数)
- scene_auditor 在 §1 输入矩阵中称 "C-Level(三Agent)"、"S-Level(单Scene Designer)" -- 无M-Level
- complexity_router 输出 "S-Level / M-Level / C-Level"
- dispatcher 传递参数时需确定使用哪种命名——三个文件未定义统一的参数契约

### 1.5 综合一致性裁决

| 检查项 | 裁决 |
|--------|:---:|
| complexity_router --> scene_designer S/M/C对应 | **矛盾 (角色数/空间数不一致)** |
| complexity_router --> scene_auditor S/M/C对应 | **M-Level缺失** |
| 输出YAML <--> 审计维度消费 | **大致一致 (S-Level台本消费路径存疑)** |
| 术语统一性 | **R14/R15编号冲突(阻断级)·级别命名不一致** |

---

## 2. 完整性

### 2.1 红队审计5项核心建议覆盖矩阵

| # | 红队建议 | 覆盖文件 | 覆盖状态 | 备注 |
|---|---------|---------|:---:|------|
| 1 | 三设计Agent合并 (Shot+Movement+Composition) | scene_designer_v1.0.md | 已覆盖 | S/M-Level合并为1个Agent。C-Level保留三Agent独立 |
| 2 | SDA+SSA合并 (设计审计+台本审计合并) | scene_auditor_v1.0.md | 已覆盖 | 合并为四阶段单一审计Agent。Gate 0也合并入内 |
| 3 | Gate 0前置 (正则先于LLM) | complexity_router §2.5 + scene_auditor §3 | 已覆盖 | 前置Gate 0(G0-PRE-01~06)+后置Gate 0(R01-R15)。Phase 0在LLM审计前执行 |
| 4 | 场景复杂度分级 (S/M/C) | complexity_router_v1.0.md §1 | 已覆盖 | 六项指标确定性分类。三级管道配置。边界情况9种 |
| 5 | OBJECT_TIMELINE条件触发 | complexity_router §2.4 | 已覆盖 | N_objects>=4或Has_action触发。S-Level不触发。C-Level始终触发 |

**红队建议覆盖总结: 5/5 已覆盖。但覆盖质量有差异(见下方)。**

### 2.2 TIME_SKELETON_spec.md §3.3 检查项覆盖 (2A-2G)

TIME_SKELETON_spec.md §3.3 定义了5个检查维度(以复选框列出)。scene_auditor 将其扩展为7个检查项(2A-2G):

| TIME_SKELETON §3.3 检查项 | scene_auditor 对应 | 实现状态 | 备注 |
|--------------------------|-------------------|:---:|------|
| 故事板格N构图 = frames[N].hard 景别+运镜 | §5.2 2A | 已实现 | 逐格比对景别/运镜/焦距/格号连续性 |
| 视频提示词第N秒 = frames[N].soft.action_anchor 展开 | §5.3 2B | 已实现 | 核心语义比对·区分"展开"vs"偏离" |
| 格N-->格N+1运镜过渡 = segments的transition | §5.6 2E | 已实现 | 转场类型+位置+过渡段检查 |
| 全局锚点逐字一致 | §5.5 2D | 已实现 | C1-C4+Constraints逐字比对 |
| 道具状态变化有中间帧 | §5.7 2F | 已实现 | 逐道具·逐状态变化·物理连续性 |

**scene_auditor 新增项(超出§3.3):**
| 新增检查项 | 位置 | 必要性 |
|-----------|------|:---:|
| 2C: 台本时长 <--> 骨架总时长 | §5.4 | 合理新增——时长溢出是常见缺陷 |
| 2G: 台本自创时间引用 | §5.8 | 合理新增——防止台本引用不存在的时间点 |

**TIME_SKELETON覆盖总结: 5/5原始项已实现 + 2项合理扩展。完整覆盖。**

### 2.3 Gate 0 R01-R15 正则精确度与可执行性

逐条检查 scene_auditor §3.2 中的正则表达式:

| 规则 | 检测方式 | 可执行? | 精确度评估 |
|------|---------|:---:|------|
| R01 时长 | 数值比较(提取秒数) | 可执行 | 100%·但提取正则依赖多种格式·可能漏检 |
| R02 过程动词 | 正则+排除模式 | 可执行 | 95%+·排除模式(刚(?!好)/已(?!经))基本覆盖常见误报 |
| R03 时间模糊词 | 正则+负向lookbehind | 可执行 | 95%+·lookbehind排除"第N秒""t=N"等合法上下文 |
| R04 跨镜引用 | 正则 | 可执行 | 100%·模式明确·排除规则清晰 |
| R05 参考图引用 | 模式匹配+清单比对 | 可执行 | 100%·模式匹配部分·存在性检查需调度器提供清单 |
| R06 禁止清单模糊 | 正则+上下文 | 可执行 | 95%+·排除"稳定/好像/自然光" |
| R07 工程符号 | 正则 | 可执行 | 100%·模式明确·双重保险(与R12交叉) |
| R08 段结构 | 关键块头匹配 | 可执行 | 100%·块头标记明确 |
| R09 负向词 | 正则+排除上下文 | 可执行 | 95%+·排除"不在画面中""文字为后期叠加"等合法使用 |
| R10 模型名 | 正则 | 可执行 | 100%·注意: "Seko"不算泄漏(已显式排除) |
| R11 @声明 | 模式匹配+汉字计数 | 可执行 | ~95%·汉字计数依赖分词·"用途:"标记为备选 |
| R12 KB泄漏 | 正则 | 可执行 | 100%·ID前缀明确·与R07部分重叠(双重保险) |
| R13 骨架顺序 | 关键词顺序匹配 | 可执行 | ~95%·缺Style段仅警告·有容错 |
| R14 运镜语义 | 正则 | 可执行 | 95%+·模式覆盖常见运镜动词·排除"推近落定后"等结束状态 |
| R15 画面外声 | 正则 | 可执行 | 100%·模式明确·仅触发声音动词+画面外词组合 |

**正则总体评价: 15条规则基本可执行。R01时长提取的正则依赖多种不同格式的文本标注，可能在格式不规范的台本中漏检。R03的lookbehind在某些正则引擎中可能不支持(需PCRE)。**

**一个值得关注的精确度问题:**
scene_auditor R01 提取时长的正则 `/t=\d+s至t=\d+s|\[\d+[-–]\d+\]\s*秒|段时长[:：]\s*(\d+)秒/` —— 这只覆盖了"段时长:N秒"格式。但台本中更常见的时长标注是 "0-5秒:" 或 "[0-5]秒" 或 "t=0s至t=5s" 等形式。R01需要确保覆盖台本实际使用的所有时长格式。

### 2.4 遗漏项 -- 边界情况

| # | 边界情况 | 是否覆盖 | 评估 |
|---|---------|:---:|------|
| 1 | 无参考图的场景 | 部分覆盖 | complexity_router G0-PRE-02 检查参考图引用。但如果场景确实无参考图(如纯CG环境)--> 阻断误报。无豁免机制 |
| 2 | 无PLAN的S-Level场景 | 已覆盖 | scene_auditor §5.9: 降级为仅2C+2G。但Phase 3仍假设有台本——S-Level的台本来源需明确(见兼容性) |
| 3 | 仅1镜的场景(总时长<=15s) | 未覆盖 | 单镜场景在 complexity_router 中无特殊处理——可能被归类为S-Level(单空间+少量对白)但运镜比例计算分母为1。单镜场景的帧间连续性检查(1B,3E)无意义但仍会执行 |
| 4 | 场景对白=0的纯视觉场景 | 未覆盖 | complexity_router N_dialogue=0 --> S-Level条件之一。但 scene_designer 的KB加载中"对话场景"路由可能不适用。纯视觉场景没有"双人对话""三人对话"等类型——scene_designer §3 Step 2 的场景类型路由缺少"无对白环境场景"的显式分支(虽有"环境/空镜"但描述偏景观类) |
| 5 | 场景跨越多个MODE:A场景头(子段) | 已覆盖 | complexity_router §1.6 情况1: N_spaces按空间名去重 |
| 6 | 同一个MODE:P运行中多个场景的不同级别 | 已覆盖 | complexity_router §1.6 情况7: 每场景独立分类 |
| 7 | N_objects预扫描不准确 | 已覆盖 | complexity_router §1.6 情况6: 复杂度升级信号机制 |
| 8 | 用户强制覆盖分类 | 已覆盖 | complexity_router §1.6 情况5: MODE:F强制覆盖机制 |
| 9 | 管道中途复杂度升级 | 已覆盖 | complexity_router §1.6 情况9: 暂停管道+已完步骤复用 |

### 2.5 遗漏项 -- 结构性遗漏

**(A) scene_auditor 缺失"仅台本·无设计报告"的审计模式:**
- M-Level 中当 Movement+Composition 合并时，输出的是统一的"运镜+构图报告"，而非两份独立的YAML
- scene_auditor Phase 1 假设输入是"场景设计报告(Scene Design Report)"，其中包含四域(机位/运镜/构图/光影)分别标注
- 合并报告能否被Phase 1的逐域检查正确解析？文档未说明

**(B) S-Level 管道中 scene_designer 产出导演台本初稿(§6d)后，谁做 Gate 0 前置?**
- complexity_router §2.1: S-Level管道中 Gate 0 前置(G0-PRE-01~06) 在 Agent 调用前执行——检查 MODE:A 源
- But S-Level管道中 Gate 0 后置(检查台本输出质量)由 scene_auditor 的 Phase 0 执行
- 然而 S-Level 管道跳过了 prompt_composer——台本由 scene_designer 直接产出
- scene_auditor Phase 0 假设输入是"导演台本全文(VIDEO_PROMPT_[场景].md)"——S-Level没有这个文件
- 结论: S-Level管道的台本格式可能与标准台本格式不同，scene_auditor 的 Gate 0 正则需要验证其兼容性

**(C) scene_designer 引用 TIME_SKELETON_spec.md §2 但输出 §7 YAML 并非 TIME_SKELETON 完整格式:**
- scene_designer §7 输出三个独立YAML块(§4/§5/§6)，声称"一次性产出--storyboard_planner读取全部四个块进行机械组装"
- 但 TIME_SKELETON_spec.md §2 定义的完整格式是单一的 TIME_SKELETON YAML 结构
- 这意味着中间多了一次"组装"步骤——如果 storyboard_planner 在 S/M-Level 中被跳过，YAML块将无法自动合成为 TIME_SKELETON
- scene_auditor Phase 2 期望输入是 PLAN_[场景].md (含TIME_SKELETON)，但S-Level没有PLAN

**裁决: S-Level管道中 TIME_SKELETON 的"生产者"角色缺失。scene_designer产出YAML片段但无组件将它们合成为TIME_SKELETON(因为Planner被跳过)。scene_auditor Phase 2降级为仅2C+2G，跳过了所有与TIME_SKELETON对齐的检查——这意味着S-Level场景完全没有骨架对齐验证。**

---

## 3. 兼容性

### 3.1 与 dispatcher_v5.0.md 的兼容性

#### 3.1.1 §-1 子代理强制执行协议

| R-AGENT规则 | complexity_router 声称 | 实际验证 | 裁决 |
|------------|---------------------|---------|:---:|
| R-AGENT-01 (Agent调用=独立进程) | S-Level合并Agent仍使用Agent工具发起独立调用(§3.3) | 合并的Scene Designer/Scene Auditor是可被Agent工具调用的独立指令文件 | 兼容 |
| R-AGENT-02 (审计Agent只读最终输出) | Scene Auditor只读Scene Designer最终报告(§2.1 S2) | scene_auditor §0 SW-C02明确"只读五样"·不含推理过程 | 兼容 |
| R-AGENT-03 (禁止自审) | Scene Auditor != Scene Designer·独立agentId(§2.1 S2) | 两个不同的Agent文件·不同的agentId | 兼容 |
| R-AGENT-04 (Agent调用声明) | §3.3定义了简化版声明格式 | 格式适配S-Level管道·保留了📤/📥标记 | 兼容 |
| R-AGENT-05 (调度器角色边界) | 复杂度分类为编排层决策·非Agent推理(§3.3) | 分类规则100%确定性·调度器自执行·属于编排层 | 兼容 |

**R-AGENT 兼容性总体: 通过。合并Agent不违反R-AGENT协议的实质性要求。**

#### 3.1.2 §-2 并行/串行拓扑

| 管道级别 | complexity_router 拓扑 | dispatcher §-2 当前拓扑 | 冲突? |
|---------|----------------------|----------------------|:---:|
| S-Level | 2 waves全串行(S1-->S2) | §-2仅定义C-Level的4-wave拓扑 | 无冲突--S-Level是新拓扑·不覆盖C-Level |
| M-Level | 3-4 waves(含条件并行) | §-2无M-Level定义 | 无冲突--M-Level是新拓扑 |
| C-Level | 不变(当前完整管道) | §-2定义的4-wave拓扑 | 无冲突--完全一致 |

**并行拓扑总体: 兼容。S/M-Level是新增的简化拓扑，不修改C-Level的现有拓扑。**

#### 3.1.3 管道步骤插入位置

complexity_router §3.1 提议在 dispatcher 中插入 §-3 章节(§-2之后·§0之前)。这个位置与 §-1(子代理协议)和 §-2(并行拓扑)同级，属于"启动力"——在管道启动时执行。架构上合理。

complexity_router §3.4 提议的具体修改点(修改1~修改3)语法上可行:
- Step 0.5b 插入在 Step 0.5 和 Step 0.6 之间 -- 此时 MODE:A 已完成，所有复杂度数据可采集 -- 时机正确
- Gate 0 前置在 Agent 调用前执行 -- 避免浪费 Agent tokens -- 合理
- 加载清单新增 -- 不影响现有加载

### 3.2 S-Level 输出与 dispatcher 消费链的兼容性

**核心问题: S-Level管道跳过 Prompt Composer，但 dispatcher 的后续步骤假设有PC台本。**

```
dispatcher C-Level 输出链:
  Scene Designer --> storyboard_planner --> prompt_composer --> scene_auditor
                                                                    |
S-Level 输出链:                                                     |
  Scene Designer(含台本初稿) --------------------------------------> scene_auditor
  (跳过了 planner 和 PC)
```

**兼容性问题:**
1. Scene Designer 的 §6d 导演台本初稿 格式是否与 prompt_composer 产出的标准台本格式一致？如果不一致，scene_auditor 的 Gate 0 正则需要适配
2. scene_auditor Phase 3 检查项(3A-3E)假设输入是 prompt_composer 产出的台本(含【镜头参数卡】+【生成指令】+【禁止】+【段末转场】)。Scene Designer 的台本初稿是否包含这些结构块？
3. scene_auditor 的 R08 "段结构完整性" 检查【镜头参数卡】【生成指令】【段末转场设计】【禁止】——如果 Scene Designer 产出不使用这些块头，R08会全部误报

### 3.3 C-Level 管道向后兼容

complexity_router §4.2明确声明:
- 复杂度分类未执行 --> 默认C-Level --> 运行完整管道
- 数据采集失败 --> 保守策略(该指标触发升级)
- S-Level台本与C-Level台本使用相同段落格式

这些声明合理。但如果 M-Level 管道(使用合并Agent)被激活后发现问题，回退到C-Level需要确保所有三Agent的独立指令文件仍然可用且未被修改。

### 3.4 P-CONSTITUTION 合规

| 铁律 | S-Level合规 | M-Level合规 | 检查方式 |
|------|:---:|:---:|------|
| 第0条 KB>LLM | 合规 | 合规 | 每域每镜KB引用·P-STATE优先 |
| 第一条 画面可见性 | 合规 | 合规 | Scene Auditor维度D·Gate 0 R14(需注意R14定义不一致) |
| 第二条 渲染可行性 | 合规 | 合规 | P-FAL规避·P-STATE §2引用 |
| 第三条 空间锚定 | 合规 | 合规 | 空间地图+参考图·Scene Auditor维度B |
| 第四条 运镜-画面分离 | 合规 | 合规 | Scene Auditor维度E·Gate 0 R04/R07(但scene_auditor的R14才是运镜语义) |
| 第五条 确定性>概率性 | 合规 | 合规 | Gate 0前置+后置·先正则后LLM |
| 第六条 物体存在链 | **部分合规** | 合规 | S-Level N_objects<=3 --> 不触发OBJECT_TIMELINE --> 物品链验证降级为Scene Auditor维度D抽查 |
| 第七条 独立验证>自审 | 合规 | 合规 | Scene Designer != Scene Auditor·独立agentId |

**注意: 第六条在S-Level中降级为"Scene Auditor维度D抽查"。complexity_router §4.2 声称"S-Level的N_objects<=3-->物品链简单-->Scene Auditor维度D抽查"。然而，scene_auditor §6.3 维度3C04 关于物体存在链的描述是"Phase 1未执行时·3C04承担全部空间锚定检查"——这指的是空间锚定而非物体存在链。物体存在链的独立检查在 scene_auditor 中没有明确的"降级版"维度。这是一个覆盖缺口。**

### 3.5 与 TIME_SKELETON_spec.md 的兼容性

| TIME_SKELETON规范 | 遵守情况 | 备注 |
|-------------------|:---:|------|
| §1 原则2: 骨架是源·产出物是视图 | 遵守 | scene_auditor Phase 2 对骨架做diff而非重新描述 |
| §4 生产者-消费者契约 | **部分遵守** | S-Level跳过了storyboard_planner(生产者)但scene_designer产出YAML片段——TIME_SKELETON的完整生产者缺失 |
| §5 编号系统兼容 | 遵守 | scene_designer §7 YAML的frame_label字段兼容格号系统 |
| §6 文件产出规范 | **部分遵守** | S-Level跳过了PLAN_[场景].md 和 STORYBOARD_[场景].md 的生成 -->

---

## 4. 可操作性

### 4.1 complexity_router 六项指标采集可操作性

| 指标 | 采集方法 | 是否存在歧义? | 5秒内可行性 |
|------|---------|:---:|:---:|
| N_spaces | 场景头正则+去重 | **存在** | 可行 |
| N_speakers | CV角色名正则+去重 | 低歧义 | 可行 |
| N_dialogue | 对话行正则+计数 | 低歧义 | 可行 |
| R_static | 运镜动词正则/总镜数 | **存在** | 可行 |
| Has_action | 动作关键词3级正则 | **存在** | 可行 |
| N_objects | 物品名词正则+跨镜去重 | **高歧义** | **存疑** |

**详细分析:**

**(A) N_spaces 歧义:**
"同一空间·不同区域"的判断依赖空间地图——"如果区域名称共享同一空间前缀...且在空间地图中标注为同一建筑内相邻区域 --> 计为1个空间"。这要求调度器在采集N_spaces时已经能读取和解析空间地图——增加了采集复杂度。如果空间地图尚未生成(MODE:A Step 2输出空间地图)，此判断无法完成。

但在 complexity_router 的设计中，复杂度分类发生在Step 0.5b，此时MODE:A已完成，空间地图已生成。所以时序上可行。

**(B) R_static 歧义:**
运镜动词正则中的排除模式非常复杂(如"推(?!荐|测|算|论|断...)")——这是一个很长的负向lookahead。正则的长度和复杂度可能导致在某些正则引擎中性能问题或匹配错误。

此外，"含'固定机位'/'静止'/'锁定'字样 --> 静态镜"的规则优先于运镜动词检测——这个优先级规则需要在代码中显式实现，而非正则直接表达。

**(C) Has_action 歧义:**
Level 3 悬疑/惊惧类的正则匹配容易产生误报——"紧张"可能在非动作上下文中出现("气氛紧张"是描述而非动作)。规则声称"仅当剧本动作描述含此关键词时命中"，这要求区分"动作描述行"和"对白行"——需要额外的上下文解析。

**(D) N_objects 高歧义:**
这是六项指标中歧义最高的:
- 物品名词正则 `物品类: /照片|文件|档案|证件|手机|...` 会匹配到对白中的物品提及(如角色说"把那份文件给我")——但对白中提及不等于场景中实际存在
- "同义词合并"需要同义词表——复杂度高
- "人物随身物品自动排除"需要人物表——但人物表可能不完整
- "例外: 如果剧本中特殊使用了随身物品(如'掏出证件'·'手机放到桌上') --> 该物品离开角色身体 --> 计入N_objects"——这需要对"掏出""放到桌上"等动作进行语义理解，正则难以精确实现
- complexity_router 承认这是"轻量预扫描"，并设计了"复杂度升级信号"机制作为补救(§1.6情况6)——这间接承认了预扫描可能不准确

**(E) 5秒可行性:**
这六项指标的采集涉及: 读取MODE:A增强剧本全文 + 读取人物表 + 读取空间地图 + 运行多个复杂正则 + 去重计数 + 同义词合并。对于一个有30+镜的场景，仅N_objects的逐镜扫描和跨镜去重就可能需要数秒。5秒是一个乐观估计。

### 4.2 scene_designer 输入文件清单完整性

scene_designer §2 列出:

**必须输入:**
- MODE:A 增强剧本 (已列出)
- 空间地图文件 (已列出)
- 场景参考图 (已列出)
- 剧本段落 (已列出)
- complexity_level参数 (已列出)

**设计前必查:**
- P-STATE.md §1-§2 (已列出)
- P-CONSTITUTION.md (已列出)
- canvas_runtime.md §1-§2 (已列出)
- TIME_SKELETON_spec.md §2 (已列出)

**缺失项:**
| 缺失输入 | 用途 | 严重度 |
|---------|------|:---:|
| IMAGE_AUDIT.md | 参考图格位对应·哪些格位有可用参考图 | **高** |
| OBJECT_TIMELINE (M/C-Level) | 物体存在链·道具状态·M/C-Level必需 | **高** |
| ANCHOR_BASELINE.md | 全场景Character Anchor基线·§2输入清单虽在必查列表中提到了P-STATE和ANCHOR_BASELINE，但ANCHOR_BASELINE未出现在"必须输入"或"设计前必查"的显式列表中 | **中** |
| kb_index_v2.0.md | KB路由索引·在KB加载中提到但未在输入清单中列出 | **低** |

scene_designer §2 底部提到KB加载时引用 kb_index_v2.0.md，但输入清单中未显式列出。ANCHOR_BASELINE 在 §2 设计前必查中未出现，但在复杂度路由 S-Level 管道中被列为输入。

OBJECT_TIMELINE 的缺失比较严重——M-Level(当N_objects>=4时)和C-Level场景都需要OBJECT_TIMELINE来验证物体存在链。scene_designer §8.2第六条声明"与OBJECT_TIMELINE对齐"，但没有将OBJECT_TIMELINE列入输入清单。

### 4.3 scene_auditor 四阶段架构的顺序合理性

```
Phase 0: Gate 0 确定性预扫描 --> 仅需台本·零外部依赖 --> 先执行·合理
Phase 1: 设计域审计 --> 需设计报告 --> 条件执行·合理
Phase 2: TIME_SKELETON 同构验证 --> 需PLAN+台本+故事板 --> 在Phase 1后·合理
Phase 3: 台本域审计 --> 需台本(含Phase 0已扫内容) --> 在最后·合理
```

**阶段间依赖分析:**
- Phase 0 不依赖任何Agent输出——仅检查台本格式——先执行正确
- Phase 1 依赖设计报告——在Phase 0后执行——如果Phase 0阻断则Phase 1-3都不执行——正确
- Phase 2 依赖 PLAN+台本+故事板——需要Phase 0通过后才有有效台本——在Phase 1后执行——合理。Phase 2不依赖Phase 1的结果——但Phase 1如果发现了设计问题并打回修复，Phase 2的结果是否会过时？文档未明确这个交互
- Phase 3 依赖台本——在Phase 2后执行——合理。Phase 3中的Gate 0已覆盖项不再重复检查——正确

**潜在的阶段间问题:**
1. Phase 1 发现设计问题并打回修复 --> 设计报告更新 --> 可能影响 PLAN (如果 storyboard_planner 已经基于旧设计生成了 PLAN) --> Phase 2 的骨架对齐可能基于过时的骨架
2. S-Level 场景中 Phase 1 条件执行("仅当设计报告存在时")——但 S-Level 的 Scene Designer 确实会产出设计报告(统一设计报告+台本初稿)。Phase 1应该正常执行而非跳过

### 4.4 其他可操作性问题

**(A) S-Level 管道中台本初稿的格式未定义:**
- scene_designer §3A-S6 说"仍然输出完整§7 YAML"
- 但 complexity_router §2.1 S1 说产出"统一设计报告(含台本初稿)"
- "台本初稿"的格式未在任何文件中定义——它是否包含【镜头参数卡】【生成指令】【禁止】【段末转场】？是否满足 scene_auditor Phase 0 的结构要求(R08)?
- 这是S-Level管道最关键的可操作性缺口

**(B) M-Level 管道的 Agent 拆分决策是运行时判定:**
- complexity_router §2.2: "如果 R_static >= 0.60 AND N_speakers <= 5 --> 运镜+构图合并为1个Agent; 否则 --> 拆分为2个Agent"
- 这个判定影响管道拓扑(更多Agent调用、不同的输出格式、不同的审计需求)
- 但 scene_auditor 没有适配这两种M-Level配置

**(C) 复杂度升级信号的检测与响应未定义在 scene_designer/scene_auditor 中:**
- complexity_router §1.6 情况6: Scene Designer发现>3个跨镜物品 --> 输出"warning 复杂度升级信号"
- complexity_router 附录A 给出了升级信号的正则: `/warning\s*复杂度升级信号/gm`
- 但 scene_designer 的指令中没有指示Agent应该何时输出此信号——§8.2第六条只说"与OBJECT_TIMELINE对齐"但没有给出"发现额外跨镜物品时标注升级信号"的具体指令

---

## 综合裁决

### 阻断项 (必须修)

| # | 问题 | 涉及文件 | 修复建议 |
|---|------|---------|---------|
| BLOCK-1 | **Gate 0 R14/R15编号冲突**: complexity_router 定义 R14=画面外描述/R15=光源锚定; scene_auditor 定义 R14=Action运镜语义/R15=画面外声音源。同一编号指代不同检查项 | complexity_router §2.5 + scene_auditor §3.2 | 统一编号: 将 scene_auditor 的新增规则编号为 R14/R15，将 complexity_router 的画面外描述并入R14(与scene_auditor合并)或将 complexity_router 的R14/R15重新编号为 R16/R17。建议以 scene_auditor 为准(R14运镜/R15画面外声)，因这两项可100%正则检测 |
| BLOCK-2 | **scene_auditor 缺失M-Level支持**: 输入矩阵无M-Level列; §4.7降级策略无M-Level; Phase 2降级策略无M-Level专属路径。M-Level场景(占复杂度路由的中间层)将无审计规范可依 | scene_auditor §1, §4.7, §5.9 | 在输入矩阵中新增M-Level列; 补充M-Level的设计Agent配置(1设计 vs 2设计 vs 3设计)的审计适配; Phase 2降级策略中新增M-Level路径(条件PLAN) |
| BLOCK-3 | **scene_designer S/M-Level场景描述与complexity_router判定规则矛盾**: S-Level "单角色" vs "<=3 speakers"; M-Level "双人对话" vs "4-6 speakers"; M-Level "单空间" vs "2空间" | scene_designer §1.2 | 将 scene_designer 的场景描述改为引用 complexity_router 的判定规则而非自创约束。建议改为: S-Level="<=3说话角色·单空间·<=5句对白·>=80%固定"; M-Level="中等复杂度(详见complexity_router §1.4)" |
| BLOCK-4 | **S-Level管道中台本初稿格式未定义**: Scene Designer产出"台本初稿"但格式未在任何文件中规范。scene_auditor Phase 0 的 R08 检查期望【镜头参数卡】【生成指令】【禁止】【段末转场】——如果台本初稿不使用这些块头，Gate 0 会全部误报 | scene_designer §3A + complexity_router §2.1 | 在 scene_designer 中明确定义 §6d 导演台本初稿的格式规范——至少需要与标准台本兼容的结构块。或在 scene_auditor 中新增"S-Level台本格式变体"的检查项 |

### 警告项 (建议修)

| # | 问题 | 涉及文件 | 修复建议 |
|---|------|---------|---------|
| WARN-1 | **S-Level管道中TIME_SKELETON生产者缺失**: scene_designer产出YAML片段但storyboard_planner被跳过-->无人组装TIME_SKELETON。scene_auditor Phase 2降级为仅2C+2G，丢失了2A/2B/2D/2E/2F——S-Level场景完全没有骨架对齐验证 | complexity_router §2.1 + scene_designer §7 + scene_auditor §5.9 | 选项A: S-Level的Scene Designer同时产出简化版TIME_SKELETON(合并YAML块)。选项B: S-Level跳过Phase 2审计是设计意图(简单场景不需要骨架验证)——但需显式文档化并评估风险 |
| WARN-2 | **N_objects轻量预扫描歧义高**: 正则匹配物品名词无法区分"对白中提及"和"场景中实际存在"; 同义词合并依赖不存在的同义词表; 随身物品排除需语义理解"掏出/放到桌上" | complexity_router §1.2.6 | 接受不完美预扫描作为设计约束，但需在复杂度声明中标注"预扫描置信度"; 调低异常物品数阈值(<=2而非<=3触发S-Level); 强化复杂度升级信号机制 |
| WARN-3 | **scene_designer 输入清单缺失 OBJECT_TIMELINE**: M/C-Level场景需要OBJECT_TIMELINE来验证物体存在链(宪法第六条)，但scene_designer §2输入清单未列出 | scene_designer §2 | 在"必须输入"(M/C-Level)或"设计前必查"中新增OBJECT_TIMELINE |
| WARN-4 | **S-Level宪法第六条覆盖不足**: complexity_router声称"Scene Auditor维度D抽查"覆盖物体存在链，但scene_auditor §6.3维度3C04是空间锚定检查而非物体存在链检查。S-Level场景的物体存在链验证无明确执行者 | complexity_router §4.2 + scene_auditor §6.3 | 在scene_auditor Phase 3中新增S-Level专属的物体存在链简化检查维度(如3F) |
| WARN-5 | **级别参数命名不一致**: scene_designer使用 `complexity_level: "S"/"M"/"C"`(字符串参数); scene_auditor使用"C-Level/S-Level/纯骨架"分类; complexity_router输出"S-Level/M-Level/C-Level" | 三个文件 | 建立统一的参数契约: 建议使用 `complexity_level: "S" | "M" | "C"`(单字母字符串)作为dispatcher传递给Agent的标准参数 |
| WARN-6 | **M-Level Agent拆分决策与scene_auditor审计配置的脱节**: complexity_router §2.2的运行时判定(合并vs拆分)影响设计Agent数量和输出格式，但scene_auditor未适配这两种M-Level配置 | complexity_router §2.2 + scene_auditor §1 | 在scene_auditor中新增M-Level的两种配置路径: "M-2Agent模式"(Shot+合并MovementComposition)和"M-3Agent模式"(三Agent独立) |

### 通过项

| # | 检查项 | 裁决 |
|---|--------|:---:|
| PASS-1 | 红队5项核心建议全部覆盖 | 通过 |
| PASS-2 | TIME_SKELETON §3.3的5项检查在scene_auditor 2A-2G中全部实现 | 通过 |
| PASS-3 | 15条Gate 0规则均有可执行的正则表达式 | 通过 |
| PASS-4 | R-AGENT-01~05五条硬约束在合并Agent后仍合规 | 通过 |
| PASS-5 | C-Level管道完全向后兼容(默认行为=当前完整管道) | 通过 |
| PASS-6 | complexity_router 9种边界情况覆盖较全面 | 通过 |
| PASS-7 | P-CONSTITUTION七条铁律在三级管道中均有对应的检查机制 | 通过 |
| PASS-8 | scene_auditor四阶段执行顺序合理·无循环依赖 | 通过 |
| PASS-9 | 渐进迁移策略(四阶段影子模式)设计保守安全 | 通过 |
| PASS-10 | OBJECT_TIMELINE条件触发逻辑清晰·三级决策表正确 | 通过 |

---

## 总结

**整体评价:** Phase 1三个文件构成了一个概念完整的三级管道体系。红队建议被全面覆盖，TIME_SKELETON规范被正确引用，P-CONSTITUTION合规矩阵完整。但存在4个阻断级问题和6个警告级问题，主要集中在三个方面:

1. **M-Level的系统性缺失** — scene_auditor没有为M-Level(中间层)提供输入矩阵和审计适配，使得三级体系实际上只有两极(S/C)的审计支持
2. **S/M-Level描述与判定规则的矛盾** — scene_designer的场景级别描述与complexity_router的判定规则在角色数/空间数上存在事实性不一致
3. **S-Level管道的"最后一公里"未定义** — 台本初稿格式规范缺失、TIME_SKELETON生产者缺失、物体存在链验证降级未实现

建议在进入Phase 2(Agent指令文件详细编写)之前优先修复4个阻断项。警告项可在Phase 2中并行修复。

---

**独立监督专家签名:** EP14_SUPERVISION_REPORT.md
**审查依据:** 画布宪法·TIME_SKELETON规范·dispatcher v5.0·三个Phase 1产出文件
**审查独立性:** 本监督Agent未读取任何设计Agent的推理过程·仅审查最终产出文件
