# EP14 Phase 2 算力浪费修复文件 · 独立监督审查报告

> **审查日期:** 2026-07-07
> **审查身份:** 独立监督专家
> **审查对象:** 4个Phase 2产出修复文件
> **参考基线:** EP14_TOKEN_FORENSICS.md + EP14_ARCHITECTURE_WASTE.md + 5个被引用源文件
> **审查方法:** 四维度交叉验证（一致性·完整性·可操作性·节省估算）

---

## 综合裁决: ⚠️ 有条件通过 — 4项🛑阻断缺陷 + 7项⚠️警告

四个修复文件整体方向正确，核心设计逻辑自洽，但存在**4项必须在部署前修复的阻断级缺陷**（包括可导致Agent加载错误文件的跨文件正则不一致、过度宣称的节省数字、以及关键函数缺失的伪代码）。修复后可达✅通过。

---

# 维度一: 跨文件一致性

## 1.1 R01-R15正则表达式三源不一致 (🛑阻断)

**发现:** 同一套Gate 0规则在三个文件中存在三个版本的regex pattern。

| 规则 | P-CONSTITUTION §5.2 (原始) | agent_quick_ref §E.1 (速查) | gate0_context_aware §3.1 (实现) | scene_auditor §3.2 |
|------|---------------------------|----------------------------|-------------------------------|-------------------|
| R02 | `/正在\|刚(?!好)\|已(?!经)\|开始\|持续/` | 同左(简化) | 添加`^[^。\n]{0,20}?`前缀+`开始[^前]`+`持续[^时间]`+3个额外动词 | 同gate0 |
| R03 | `/缓缓\|渐渐\|慢慢\|逐渐\|徐徐\|冉冉/` | 同左(简化) | 添加负向后顾(排除`第\d+`/`t=`等合法上下文) | 同gate0 |
| R04 | `/同上\|参考上\|如前\|同镜\|与镜/` | 同左(简化) | 扩展为11种模式+`IGNORECASE`标志 | 同gate0 |
| R06 | `/稳(?!定)\|好(?!像)\|舒服/` | 同左(简化) | 额外添加`自然\|美感\|漂亮`+负向前瞻 | 同gate0 |
| R07 | `/v_dolly\|ω_pan\|7-DOF\|f\/\d\|°\/s/` | 同左(简化) | 额外添加`ω_tilt\|ω_roll` | 同gate0 |
| R09 | `/不要\|避免\|禁止\|不能\|不应\|勿\|别/` | 同左(简化) | 额外添加`切勿\|严禁\|不许\|不得`+负向前瞻豁免 | 同gate0 |
| R10 | `/即梦\|海螺\|Kling\|Vidu\|Seedance\|可灵\|万相\|Runway\|Pika/` | 同左(简化) | 额外添加`Sora\|Luma\|Dreamina\|Hailuo` | 同gate0 |
| R12 | `/D-TRI-\|M-MOT-\|C-COM-\|P-REN-\|P-FAL-/` | 同左(5个前缀) | 扩展为15个前缀(含C-KTZ-/C-FI-/L-3PT-/E-MTC-/GEN-/VS-LS-等) | 同gate0 |

**一致性链:**
- P-CONSTITUTION → agent_quick_ref: **一致**（agent_quick_ref忠实复制了原始简化版）
- P-CONSTITUTION → gate0_context_aware: **不一致**（gate0扩展了精确度，但P-CONSTITUTION未同步更新）
- agent_quick_ref → gate0_context_aware: **严重不一致**（速查卡标注"100%准确率"但regex与实现完全不同）
- gate0_context_aware → scene_auditor: **一致**（两者使用相同的扩展regex）

**影响:** 如果Agent以agent_quick_ref §E.1的regex为准进行合规判断，将漏检gate0实际实现的绝大部分违规（例如agent_quick_ref的R12仅5个KB前缀，gate0实现有15个）。同时，gate0_context_aware §3.1中的`RULES["R12"]["applicable_blocks"]`仅含`["BLOCK_ACTION"]`，但§2.1规则适用性表标注R12跳过HEADER和DESIGN_NOTES——这意味着R12也不会在PROHIBIT和CLOSING中扫描，与显式跳过逻辑略有差异。

**修复要求:** P-CONSTITUTION §5.2和agent_quick_ref §E.1必须同步到gate0_context_aware §3.1的v1.1扩展版regex。或明确声明agent_quick_ref §E.1仅为"概念速查·非可执行regex·完整regex见gate0_context_aware"。

### 1.1.1 R14/R15悬空 (⚠️警告)

agent_quick_ref §E.1标注R14和R15为"🆕 (待统一) — 见BLOCK-1修复"。gate0_context_aware和scene_auditor均已完整定义R14/R15的regex和适用区块。但P-CONSTITUTION §5.2仅到R13，且EP14_ARCHITECTURE_WASTE.md 附录B将BLOCK-1列为P0优先级修复项。四个修复文件未解决此阻断项——仅在被审查文件之间自洽，但与宪法原文脱节。

---

## 1.2 agent_quick_ref宪法摘要 ↔ gate0_context_aware R01-R15规则 ↔ P-CONSTITUTION原文 (⚠️警告)

agent_quick_ref §A.1列出8条铁律（第〇条至第七条），与P-CONSTITUTION原文的条文编号一致。但存在两个层面问题：

1. **铁律对应关系偏移:** agent_quick_ref §A.1的铁律#5"确定性>概率性"引用"Gate 0正则扫描(100%)先于LLM概率验证(~73%)"。gate0_context_aware §5宣称"v1.0全局正则扫描产生假阳性"并升级到v1.1区块感知扫描。但agent_quick_ref §E.1仍使用v1.0的简化regex——与其自身引用的"100%准确率"存在内部矛盾（简化regex实际上会漏检gate0 v1.1扩展后的违规项）。

2. **知识来源层级:** agent_quick_ref §A.2的五层知识来源层级与P-CONSTITUTION §0.1的层级定义一致。但gate0_context_aware未显式引用此层级——其在§1开头仅引用了画布第五条，未引用第〇条的知识来源层级约束。

**裁决:** 概念层面一致，但具体regex实现存在版本漂移。不阻断部署但需修复。

---

## 1.3 context_package_spec加载策略 ↔ yaml_only_protocol文件拆分 (✅通过)

两个文件处理不同层面的问题，互补而非冲突：

| 维度 | context_package_spec | yaml_only_protocol |
|------|---------------------|-------------------|
| 解决什么问题 | 公共上下文在每个Agent间重复加载 | Agent间通信传递了不必要的推理文本 |
| 文件对象 | P-CONSTITUTION/P-STATE/canvas_runtime等共享静态文件 | 上游Agent的设计报告/PLAN等动态产出 |
| 拆分策略 | 合并→去重→单文件(CONTEXT_PACKAGE) | 拆分→双文件(.md人类 + .yml机器) |
| 加载者 | 所有Agent | 仅下游(审计/规划/合成)Agent |

context_package_spec §4.1的Agent加载清单中"条件Read"第4项明确引用"上游Agent §6 YAML块(结构化·非推理·见context_package_spec)"，与yaml_only_protocol的核心主张一致。两者在Agent启动序列中的位置: CONTEXT_PACKAGE先加载(公共上下文)，YAML后加载(Agent间通信)。

唯一轻微张力: context_package_spec §4.1说审计Agent"Read被审计Agent的完整报告(信息隔离·Verifier读完整输出但不读推理)"，而yaml_only_protocol说"审计Agent只读YAML"。这取决于"完整报告"的定义——如果完整报告=自由文本+设计依据，则与yaml_only冲突；如果完整报告=YAML+必要台本，则一致。resolution: context_package_spec说的"完整报告"在yaml_only_protocol实施后应理解为"YAML + 台本.md(去设计依据)"，需要在context_package_spec中明确此限定。

---

## 1.4 agent_quick_ref §B P-FAL列表 ↔ P-STATE §2 (✅通过)

P-STATE.md §2 (L45-54) 定义了完整的10条P-FAL: P-FAL-01至P-FAL-10，全部状态🟡。agent_quick_ref §B.2逐条对应，ID名称、触发条件、规避方案、状态标记完全一致。

agent_quick_ref §B.1中还提到了P-OPN-02(多人面部差异≥3人不可控)，此项在P-STATE中属于§3(未解决问题)而非§2(已知失败模式)。agent_quick_ref将其放在"硬上限速查表"而非"P-FAL速查卡"中是正确的分类，但表头未标明此项来自P-STATE §3而非§2，可能造成混淆。属轻微文档瑕疵。

---

## 1.5 四个文件对"调度器"职责定义 (⚠️警告)

| 文件 | 调度器职责描述 | 
|------|-------------|
| agent_quick_ref | (未显式定义调度器——Agent视角的速查卡) |
| context_package_spec | "调度器自执行·纯文本合并·零LLM" (Step 0.7) + "调度器预编译一次·所有Agent共享引用" |
| gate0_context_aware | "调度器自执行脚本·零LLM·零Agent调用·零模型判断" (§3.2) |
| yaml_only_protocol | "调度器负责传递.yml文件路径给下游Agent" (§1.2 YC-05) + "调度器检测逻辑"(§6.2兼容回退) |

共同主题: 调度器=确定性操作执行者·非LLM推理者。但存在边界模糊:
- context_package_spec §3.1中Step 0.7被描述为"管道前置步骤(调度器自执行·非Agent)"，但Step 0.7A说"调度器将agent_quick_ref全文直接复制到CONTEXT_PACKAGE的§1引用节"——这个"复制"是物理嵌入(~15K tokens)还是引用声明？如果是物理嵌入，则CONTEXT_PACKAGE的实际大小将超过声称的<8K限制。规范需要明确。
- yaml_only_protocol §6.2的"调度器检测逻辑"(IF .yml存在 THEN ... ELSE回退)暗示调度器需要文件系统感知能力，但这与gate0_context_aware中"调度器自执行正则扫描"的技术层级不同——前者需要调度器理解Agent输出格式，后者是纯文本处理。

**裁决:** 职责方向一致但边界定义不够精确。建议在dispatcher_v5.0.md中统一明确调度器的三个自执行能力(文本合并·正则扫描·文件路由)及其前提条件。

---

# 维度二: 完整性

## 2.1 五类浪费根因覆盖度 (⚠️警告)

| 浪费根因 (EP14_ARCHITECTURE_WASTE §1鱼骨图) | agent_quick_ref | context_package | gate0_context_aware | yaml_only_protocol | 覆盖度 |
|:---|:---:|:---:|:---:|:---:|:---:|
| **#1 重复读取** (共享文件7+ Agent各自Read) | 部分(§A-§E压缩5文件→1) | **主要**(预编译一次·共享引用) | — | — | ✅ 充分 |
| **#2 KB膨胀** (720条→加载60K·使用10K) | **主要**(§C KB速查卡·每条1行) | 辅助(§8 KB规则ID清单) | — | — | ✅ 充分 |
| **#3 形式主义产出** (Movement 978行静态辩护) | — | — | 间接(通过集成complexity_router) | **主要**(审计不读推理·不传形式主义文本) | ⚠️ 部分 |
| **#4 LLM做确定性工作** (SSA 3项阻断全正则可检测) | — | — | **主要**(R01-R15调度器自执行) | — | ✅ 充分 |
| **#5 过深度管道** (S-Level触发18 Agent全管道) | — | 间接(§6引用complexity_router F1-F7) | 间接(集成点§3.2引用complexity_router) | — | ⚠️ 间接 |

**浪费#3(形式主义产出)覆盖不足:** yaml_only_protocol通过阻止下游Agent读取设计Agent的推理文本来阻断形式主义文本的传播，但它不能阻止设计Agent自身产生形式主义文本。agent_quick_ref和context_package_spec均未包含R-SFAST-01~06（静态快速通道硬规则）——这些规则定义在complexity_router_v1.0.md §3.3中，而非四个被审查文件中。这意味着如果仅部署四个修复文件而不部署complexity_router的S/M/C路由，浪费#3将持续存在。

**浪费#5(过深度管道)完全未直接覆盖:** 四个修复文件中无一直接解决管道深度问题。agent_quick_ref未提及复杂度级别；context_package_spec仅在§6中引用complexity_router输出；gate0_context_aware在§3.2集成点中假设complexity_router已部署；yaml_only_protocol §3.1的通信矩阵区分了C/M/S-Level但依赖外部路由。四个文件实际上**假设complexity_router已经部署并生效**——这是一个关键依赖未声明。EP14_ARCHITECTURE_WASTE.md 附录B列出4个阻断项(BLOCK-1~4)全部与complexity_router未部署相关，而这些阻断项在四个修复文件中未被解决。

---

## 2.2 context_package_spec八节场景信息覆盖度 (✅通过)

以scene_designer_v1.0.md §2的输入要求为基准检查覆盖:

| Scene Designer §2 输入项 | CONTEXT_PACKAGE 对应节 | 覆盖 |
|:---|:---|:---:|
| MODE:A增强剧本(镜头方向卡) | 未覆盖 — 这是每个设计目标的独立输入 | N/A(非公共上下文) |
| 空间地图文件 | §3 空间地图摘要 | ✅ |
| 场景参考图 | §5 参考图索引 | ✅ |
| 剧本段落(需要设计的场景) | §2 场景列表与剧本摘要 | ✅ |
| complexity_level参数 | §6 复杂度参数 | ✅ |
| P-STATE §1已验证模式 | §7 P-STATE活跃条目 | ✅ |
| P-CONSTITUTION铁律 | agent_quick_ref §A(嵌入CONTEXT_PACKAGE) | ✅ |
| canvas_runtime渲染边界 | agent_quick_ref §B(嵌入CONTEXT_PACKAGE) | ✅ |
| TIME_SKELETON_spec §2 | **未覆盖** — 格式规范·非场景数据 | ⚠️ 缺漏 |
| kb_index KB路由 | §8 KB规则ID清单 | ✅ |

以scene_auditor_v1.0.md §1的输入矩阵为基准:

| Scene Auditor §1 输入项 | CONTEXT_PACKAGE 对应节 | 覆盖 |
|:---|:---|:---:|
| P-CONSTITUTION.md | agent_quick_ref §A | ✅ |
| TIME_SKELETON_spec.md | **未覆盖** | ⚠️ 缺漏 |
| P-STATE.md §1-§3 | §7 P-STATE活跃条目 | 部分(仅§1-§2·§3未覆盖) |

**缺漏: TIME_SKELETON_spec.md未进入任何共享上下文。** Scene Auditor Phase 2(核心新增)明确需要TIME_SKELETON_spec.md §3.3审查报告diff视图。Scene Designer §2虽标注TIME_SKELETON_spec为"设计前必查"，但其中§2是了解目标格式——格式知识属于静态规则，应由agent_quick_ref或CONTEXT_PACKAGE覆盖。当前agent_quick_ref §D仅覆盖了TIME_SKELETON的字段定义(D.1)但未覆盖TIME_SKELETON_spec §3.3的diff验证规范。

---

## 2.3 agent_quick_ref遗漏的Agent必须规则 (⚠️警告)

agent_quick_ref的附录来源索引明确列出其压缩自9个源文件，但**shared_agent_runtime.md未列入此表**。shared_agent_runtime.md包含:
- §1 MODE:P模式定义和Agent通用行为规范
- §2 通用电影知识(8/6/5机位模板·Katz简约法则·Arijon轴线理论)
- §3 画布vs编辑器模式选择逻辑
- §4 覆盖策略模板
- §5 景别递进规则
- §6 禁止清单生成规范

检查覆盖:
- shared_agent_runtime §4(8/6/5机位模板): 在scene_designer §4.1中引用为"shared_agent_runtime.md §4 (8/6/5机位模板)"，但agent_quick_ref中无对应速查。Agent需要此知识来执行覆盖策略选择。
- shared_agent_runtime §1(Agent通用行为规范): 未在agent_quick_ref中覆盖。这包含R-AGENT-01~05硬约束——如果Agent不Read shared_agent_runtime，可能违反子代理协议。

agent_quick_ref §C (KB规则速查)仅覆盖了03_导演知识库_v5.0.md的导演规则，未覆盖shared_agent_runtime.md的Agent行为规则。如果按照context_package_spec §4.1中"❌不再Read"清单执行，Agent将失去对shared_agent_runtime的访问。

**但**: agent_quick_ref的总览图(第15-38行)并未将shared_agent_runtime列入"❌不再Read"清单。这意味着Agent仍需单独Read shared_agent_runtime——这符合设计意图。问题在于: context_package_spec §4.1的"❌不再Read"清单也未包含shared_agent_runtime，但该清单声称"替代7-8个文件"——实际列出的替代文件为6个(P-CONSTITUTION/P-STATE/canvas_runtime/kb_index/KB完整/参考图完整描述)，加上shared_agent_runtime理论上仍需加载，共7个。数字上一致但表述不够清晰。

---

## 2.4 yaml_only_protocol YAML Schema ↔ scene_designer §7输出格式 (🛑阻断)

**严重不一致:**

yaml_only_protocol §4.1定义了"Scene Designer合并输出YAML Schema"，其结构为:
```yaml
scene: {id, name, type, total_shots, total_duration_sec, complexity_level}
global_anchors: {character, environment, lighting, style_spine}
shots: [{shot_id, label, function, duration_sec, camera: {position, shot_type, focal_length, movement, ...}, ...}]
cross_shot_continuity: {transitions, axis_continuity, prop_chain}
```

scene_designer_v1.0.md §7实际输出**三个独立YAML块**:
- §7.1 (§4 机位域YAML): `segments_camera` + `frames_hard`
- §7.2 (§5 运镜域YAML): `segments_movement` + `frames_movement` + `segments_transitions`
- §7.3 (§6 构图光影域YAML): `global_anchors` + `frames_soft`

**关键差异:**
1. **结构不同:** yaml_only定义了一个扁平的`shots`数组(每个shot包含所有camera/movement/composition数据内联)，而scene_designer使用三个独立的segment/frame结构(`segments_camera`, `segments_movement`, `frames_hard/soft/movement`)。
2. **字段名不同:** yaml_only使用`shot_id: "A1"`, scene_designer使用`segment_id: "①"`。
3. **粒度不同:** yaml_only的schema是shot级别的(`shots[].camera.position`)，scene_designer是segment级别的(`segments_camera[].time_range`)加上逐秒frames。
4. **枚举值不同:** yaml_only §4.1的`camera.shot_type`注释说"标准术语: 大特写|特写|中近景|近景|中景|中全景|全景|远景"，而scene_designer §4.2的`shot_type`枚举值不完全一致。
5. **全局锚点位置不同:** yaml_only将`global_anchors`放在顶层，scene_designer将其放在§7.3(frames_soft和global_anchors段)。

**实际后果:** 如果yaml_only_protocol §3.1的通信矩阵指示"Scene Auditor Read [场景]_DESIGN.yml"，但scene_designer实际输出的是三个独立YAML块(可能需要storyboard_planner组装)，则Scene Auditor将无法找到预期格式的数据。

yaml_only_protocol §3.1自己也承认了这一点——它将Scene Designer(合并)的输出标注为`[场景]_DESIGN.yml`含"§4+§5+§6三个YAML块"，这与"一个.yml文件"的前提矛盾。

**修复要求:** 
- 方案A: 更新yaml_only_protocol §4.1的schema以匹配scene_designer §7的实际三段式输出结构。
- 方案B: 在scene_designer输出中添加一个符合yaml_only_protocol §4.1 schema的合并YAML块(作为storyboard_planner的前置消费或作为Scene Auditor的便捷接口)。
- 方案C: 明确yaml_only_protocol §4.1为"远期目标schema"，当前阶段使用scene_designer §7的三段式结构，并在通信矩阵中标注"当前: 3个独立.yml·目标: 1个合并.yml"。

---

# 维度三: 可操作性

## 3.1 gate0_context_aware Python伪代码可运行性 (🛑阻断)

gate0_context_aware §3.1提供了Python伪代码(约190行)。以下为关键缺陷:

**A. 未定义的函数引用 (4个·阻断)**
```python
# 第576行: execute_numeric_check(rule_id, block_text, start_line)   — 未定义
# 第584行: execute_pattern_check(rule_id, block_text, start_line)   — 未定义
# 第592行: execute_structure_check(rule_id, blocks, filepath)       — 未定义
# 第608行: summarize_blocks(blocks)                                  — 未定义
```
这4个函数是核心检查逻辑(run_numeric/pattern/structure checks)，缺失导致代码不可运行。其中`execute_numeric_check`需要实现R01的时长提取+数值比较逻辑；`execute_pattern_check`需要实现R05/R11的@引用格式检查；`execute_structure_check`需要实现R08的段结构完整性检查和R13的骨架顺序检查。

**B. 死标记 (1个·警告)**
```python
# 第454行: (r'^###\s*【镜头参数卡】', 'BLOCK_PARAM_CARD', True)
```
`BLOCK_PARAM_CARD`在BLOCK_MARKERS中定义但规则适用性矩阵(§2.1)中没有任何规则适用于此区块类型。`get_applicable_rules()`会对其返回空列表，block被跳过。该标记既不被消费也不产生任何效果。

**C. 假阳性过滤器冗余 (6个·效率问题)**
`is_false_positive()`函数(第488-520行)中的6个检查与§2.1规则适用性矩阵重复:
```python
# 第494行: R10 in BLOCK_HEADER         — R10的applicable_blocks已排除HEADER
# 第498行: R10 in BLOCK_DESIGN_NOTES   — R10的applicable_blocks已排除DESIGN_NOTES
# 第502行: R09 in BLOCK_PROHIBIT       — R09的applicable_blocks已排除PROHIBIT
# 第506行: R12 in BLOCK_DESIGN_NOTES   — R12的applicable_blocks已排除DESIGN_NOTES
# 第510行: R14 in BLOCK_TRANSITION     — R14的applicable_blocks已排除TRANSITION
# 第514行: R07 f-stop值假阳性          — 仅在applicable_blocks中未排除Camera参数块时需要
```
其中前5项是死代码——适用性矩阵已经排除了这些规则在这些区块中的扫描，`is_false_positive`永远不会被调用到这些分支。第6项(R07 f-stop)是唯一真正需要的假阳性检查（因为f/8在Camera参数中是合法的但R07的regex会匹配到它）。

**D. 边界条件处理不完整**
- §3.3.1无标记台本回退: `parse_blocks()`返回仅含BLOCK_HEADER一个块时触发回退，但伪代码中未实现此逻辑(未在`gate0_scan()`中检查回退条件)。
- §3.3.5多镜场景区块交错: 伪代码中`parse_blocks()`按`###`标记头区分区块，但多个镜#的ACTION块会被当作同一个BLOCK_ACTION(如果它们之间没有其他类型的标记头)。violation报告中的"镜#A3"标注仅通过行号向上查找，这依赖于台本格式的特定约定——不是通用的。

**E. 正则表达式的Python兼容性**
R02的负向预测 `刚(?!好)` 在Python `re`模块中工作正常。R03的变长负向后顾 `(?<!(?:第\d+|t=|...))` 在Python 3.x中可能触发 `re.error: look-behind requires fixed-width pattern`——`(?:第\d+|t=|...)`包含变长分支`第\d+`。需要使用regex库(`import regex`)替代标准`re`，或拆分为多个固定宽度的后顾断言。

---

## 3.2 context_package_spec Step 0.7A "零LLM"判定 (⚠️警告)

Step 0.7A描述为"调度器自执行·纯文本合并·零LLM消耗"。这在技术上是成立的——如果"合并"是指将agent_quick_ref文件内容物理复制到CONTEXT_PACKAGE中。但存在两个问题:

**A. 物理嵌入 vs 引用声明的歧义:** §3.2说"调度器将agent_quick_ref全文直接复制到CONTEXT_PACKAGE的§1引用节"，但§3.4的输出结构说"§1 引用声明 → agent_quick_ref_v1.0.md (已在CONTEXT_PACKAGE中·Agent不再单独Read)"。"已在CONTEXT_PACKAGE中"如果仅是一个引用声明(文件路径)，则Agent仍需执行一次Read来加载agent_quick_ref——这时CONTEXT_PACKAGE大小<8K但不包含15K的agent_quick_ref内容，Agent总加载=8K+15K=23K。如果是物理嵌入，CONTEXT_PACKAGE大小=8K+15K=23K，Agent一次Read即可完成。这两种方案对应不同的实施路径，但规范未明确选择。

**B. 零LLM的限定:** 如果采用物理嵌入方案，调度器执行的是文件读取+字符串拼接——确实是零LLM。但如果采用引用声明方案，"Agent不再单独Read agent_quick_ref"的前提是Agent启动prompt中已注入——这需要调度器支持prompt注入(§3.2末尾提到的"替代方案(可选)")。在无prompt注入能力的调度器上，Agent必须自行Read agent_quick_ref，此时"零LLM"仅指Step 0.7操作本身，但Agent的上下文加载仍然消耗~15K tokens。

---

## 3.3 yaml_only_protocol向后兼容实现 (✅通过·有实施细节缺失)

yaml_only_protocol §6.2描述的兼容逻辑清晰可实施:
```
IF [场景]_SHOT.yml 存在 THEN
  传递 .yml 路径给下游Agent
ELSE
  回退: 传递 .md 路径给下游Agent
  并在日志中标记 "⚠️ YAML-only回退·旧Agent仍在产生MD-only输出"
```

实施要点已覆盖:
- 检测条件明确(文件存在性检查)
- 回退行为明确(传递.md路径)
- 日志记录明确

**缺失的实施细节:**
1. 未指定调度器如何"知道"哪些下游Agent期望.yml输入——是通过Agent指令文件中的声明，还是通过调度器配置文件？
2. 未指定过渡期的Agent指令文件如何同时支持两种输入格式——如果Agent指令写"Read EP14_S1_SHOT.yml"，但调度器传递了.md路径，Agent会出错。
3. 未指定多Agent输出共存时的冲突处理——如果Shot Architect已迁移(输出.yml)但Movement Designer未迁移(仍输出.md)，下游Scene Auditor的输入矩阵需要混合读取。

**建议:** 在§6.2中增加一个过渡期Agent输入格式声明模板，例如:
```
# 在Agent指令文件中
# YAML-ONLY: true  ← 调度器解析此行决定传递.yml还是.md
```
这样调度器可以根据Agent的声明而非文件存在性来决定传递格式。

---

## 3.4 agent_quick_ref来源标注可验证性 (✅通过)

agent_quick_ref的附录"文件来源索引"为每个章节标注了:
- 源文件名
- 绝对文件路径
- 原始行数/大小
- 具体行号范围(深读标注中)

抽查验证:
- §C.1 标注"深读: 03_导演知识库_v5.0.md §1.1-1.2 (三角形原理L58-75 + 双人九变体L78-94)" — 路径和行号格式可用于验证
- §E.2 标注"深读: P-CONSTITUTION.md L539-546 (§6.5违规代码·物体存在链)" — 需源文件中存在对应行号
- §B.1 标注"深读: canvas_runtime.md L67-82 (§1.3渲染硬上限速查) · P-STATE.md L43-55 (§2已知失败模式)" — P-STATE.md L43-55经grep验证：P-FAL-01至P-FAL-10定义在L45-54，与标注一致(误差-2行，可接受)

所有来源标注格式规范、路径使用绝对路径、行号可追溯。满足可验证性要求。

---

# 维度四: 节省估算验证

## 4.1 "97%减少公共上下文重复" — 宣称不可实现 (🛑阻断)

context_package_spec §6.1宣称:
```
新架构: 公共文件加载: 1次(Step 0.7·调度器自执行·零LLM) + ~23K tokens(Agent Read)
节省: ~900K - 23K = ~877K tokens (97%减少)
```

**计算基础审查:**

旧架构(18 Agent × 50K = 900K)的来源:
- Token Forensics §2.1表: 旧管道7 Agent共享文件重复读取=~368,900 tokens
- 全管道15 Agent(含新架构)共享文件重复读取=~575,920 tokens
- context_package_spec使用的是18 Agent(C-Level全管道)，但Token Forensics中旧管道为7 Agent，全管道(旧+新)为15 Agent
- context_package_spec的900K(18×50K)计算基础与Token Forensics的575,920(15 Agent)不匹配

新架构(23K)的计算:
- 如果物理嵌入: CONTEXT_PACKAGE=23K(8K+15K agent_quick_ref)，每个Agent Read一次=18×23K=414K，节省=900K-414K=486K(54%)，非97%
- 如果prompt注入: 0次Agent Read，节省=900K(100%)，但宣称的23K暗示仍有读取成本
- 如果引用声明(Agent仍需Read agent_quick_ref): 8K+15K=23K/Agent，同上414K总计

**实际可实现的范围:**
- 方案A(物理嵌入): 54%节省 — 达不到97%
- 方案B(prompt注入+物理嵌入): 需要调度器支持prompt注入 — §3.2标注为"可选"方案
- 方案C(引用声明+Agent各自Read): 54% — 同方案A

**结论:** "97%减少"的宣称只有在调度器实现prompt注入(将所有公共上下文嵌入Agent启动prompt·零Agent Read)时才成立。当前方案默认路径(Agent Read CONTEXT_PACKAGE)的实际节省为约54%。过度宣称达43个百分点。

---

## 4.2 "Agent间通信从678K降至220K(68%)" — 计算基础部分可靠 (⚠️警告)

yaml_only_protocol §5.2宣称:
```
累计Agent间传输: ~678K → ~220K (节省 ~458K · -68%)
```

**678K的来源验证(Token Forensics数据):**

| Agent | Token Forensics 总token | yaml_only 归类为"通信" | 匹配? |
|:---|:---|:---|:---:|
| SDA | 143,787 | 144K | ✅ 接近 |
| SSA | 177,595 | 177K | ✅ 接近 |
| Storyboard Planner | 135,535 | 95K(仅设计报告读取部分·非全部) | ⚠️ 不一致 |
| Prompt Composer | 118,471 | 120K | ✅ 接近 |
| Scene Auditor(new) | 173,360 | 已在SDA+SSA中计数 | ⚠️ 重复? |

**问题1: Storyboard Planner的数字不一致。** yaml_only §5.2将Storyboard Planner的"通信"计为95K，但Token Forensics显示其总token为135,535。yaml_only §3.3解释为Storyboard Planner加载三份设计报告(3,466行)约95K——但这95K是"设计报告读取"子集，不包括其自身的KB加载(7,700)、其余上下文加载(41,700)、净推理(56,935)。所以95K作为"通信"token是合理的(仅跨Agent传输的部分)，但678K总数混用了全量token和通信子集——这是不一致的计算口径。

**问题2: 新Scene Auditor既已整合SDA+SSA，其token应已包含在二者之中，不应再额外累加。** yaml_only的Agent列表中有"SDA(如独立)"和"SSA(如独立)"——这些标注"如独立"说明它们可能已合并。但在新架构中SDA+SSA已被Scene Auditor替代(173,360 tokens)，不再独立存在。总和678K的正确分解应为旧管道数据，不含新Scene Auditor。

**220K新消耗的计算基础:**
yaml_only §3.2-3.4提供了新模式下的逐Agent加载行数估算(如Scene Auditor: ~1,784行→~45K tokens)。这些估算基于YAML文件大小和台本去设计依据后的缩减，计算逻辑清晰。但存在以下假设:
- 假设所有设计Agent已完全迁移至YAML+MD双输出 — 过渡期内可能不成立
- 假设台本去除【设计依据】块后从984行降至700行 — 需要实际测量验证
- 假设YAML解析零额外token开销 — 实际YAML的key-value结构仍消耗token

**结论:** "678K→220K"的方向和数量级正确，但678K的计算口径不一致(混合了全量token和通信子集)，且220K是基于全量迁移的理想状态，过渡期实际节省低于宣称值。建议降级宣称至"Agent间通信token预计节省55-65%"，并在全量迁移后实测验证。

---

## 4.3 其他节省宣称的验证

**agent_quick_ref 声称 "~50K tokens/Agent (当前57%浪费→0%)":**
- Token Forensics §1(逐Agent分析)确认每个Agent的上下文加载约36-84K(占各自总量的47-67%)
- 压缩后：agent_quick_ref(15K) + CONTEXT_PACKAGE(8K) = 23K/Agent
- 节省：以Shot Architect为例，旧上下文加载36.3K，新23K = 节省37%。不是"从57%浪费→0%"
- 措辞"57%浪费→0%"指的是公共上下文重复加载的浪费被消除——是正确的(公共上下文不再重复加载)，但总上下文仍包含23K的非浪费部分

**总结:** 四个文件的节省估算在方向上都正确，但context_package_spec的"97%减少"存在严重过度宣称(实际约54%)，yaml_only_protocol的"678K→220K(68%)"需要统一计算口径。

---

# 综合裁决与修复优先级

## 裁决矩阵

| 维度 | 裁决 | 关键发现 |
|:---|:---:|:---|
| 1. 跨文件一致性 | ⚠️ | R01-R15 regex三版本不一致(速查≠实现≠宪法)；P-CONSTITUTION未同步v1.1扩展；yaml_only schema与scene_designer §7输出格式冲突 |
| 2. 完整性 | ⚠️ | 五类浪费中#3(形式主义)和#5(过深度管道)未直接覆盖；TIME_SKELETON_spec未纳入共享上下文；shared_agent_runtime覆盖边界模糊 |
| 3. 可操作性 | ⚠️ | gate0伪代码缺4个核心函数+变长后顾Python兼容性问题；CONTEXT_PACKAGE物理嵌入vs引用声明歧义；yaml_only过渡期Agent输入格式未定义 |
| 4. 节省估算 | ⚠️ | "97%减少"宣称过度(实际约54%)；"678K→220K"计算口径不一致 |

## 🛑 阻断缺陷 (部署前必须修复·4项)

### 🛑-1: R01-R15正则三源同步
**文件:** P-CONSTITUTION.md §5.2 + agent_quick_ref §E.1 + gate0_context_aware §3.1
**问题:** 三组regex在6条规则(R02/R03/R04/R06/R09/R12)上存在差异，速查卡与实际实现不一致。
**修复:** (a) agent_quick_ref §E.1明确标注"概念速查·完整可执行regex见gate0_context_aware §3.1"；(b) P-CONSTITUTION §5.2更新R02-R13为v1.1扩展版regex并新增R14/R15。

### 🛑-2: yaml_only_protocol Schema与scene_designer §7格式冲突
**文件:** yaml_only_protocol_v1.0.md §4.1 + scene_designer_v1.0.md §7
**问题:** yaml_only定义单一flat shots数组，scene_designer实际输出三段式segment+frame结构。
**修复:** 采用方案C——在yaml_only_protocol §4.1标注"远期目标schema"。新增§4.3"当前阶段三段式YAML规范"直接引用scene_designer §7.1-7.3的结构定义。更新通信矩阵§3.1中的"消费方式"说明实际读取的是3个独立.yml块。

### 🛑-3: gate0伪代码缺失核心函数实现
**文件:** gate0_context_aware_v1.0.md §3.1
**问题:** `execute_numeric_check()`, `execute_pattern_check()`, `execute_structure_check()`, `summarize_blocks()`未定义。
**修复:** 补充4个函数的伪代码实现。至少提供R01时长检查、R05参考图引用检查、R08段结构完整性检查、R13骨架顺序检查的具体逻辑。

### 🛑-4: "97%减少公共上下文重复"宣称过度
**文件:** context_package_spec_v1.0.md §6.1
**问题:** 宣称97%节省仅在prompt注入方案下成立，默认路径(Agent Read)实际约54%。与Token Forensics量化数据不匹配。
**修复:** 差异化表述——"prompt注入方案(远期): ≤100%节省 / Agent Read方案(当前): ~54%节省"。提供两种方案的计算路径。将摘要行(第510行)从"97%减少"改为分场景标注。

## ⚠️ 警告缺陷 (可后续修复·7项)

### ⚠️-1: 浪费#3(形式主义)和#5(过深度管道)覆盖不足
四个修复文件未直接包含静态快速通道硬规则(R-SFAST-01~06)和复杂度路由逻辑。当前设计将这些依赖推给complexity_router——但complexity_router的4个阻断项(BLOCK-1~4)未修复。建议: 在context_package_spec §9中嵌入静态快速通道的3条最核心规则。

### ⚠️-2: CONTEXT_PACKAGE物理嵌入 vs 引用声明歧义
context_package_spec §3.2和§3.4对agent_quick_ref在CONTEXT_PACKAGE中的存在形式给出矛盾信号。建议: 明确选择方案并统一术语——物理嵌入时用"§1 公共规则速查(嵌入式)"，引用声明时用"§1 引用声明(需Agent自行Read)"。

### ⚠️-3: TIME_SKELETON_spec未纳入共享上下文
Scene Auditor Phase 2(TIME_SKELETON结构同构验证)明确需要TIME_SKELETON_spec §3.3。建议: 在agent_quick_ref §D中新增D.5 "TIME_SKELETON diff验证规范速查"，或在context_package_spec §9中引用。

### ⚠️-4: P-CONSTITUTION R14/R15缺失
宪法原文仅到R13，但三个文件(gate0/scene_auditor/agent_quick_ref)都已使用R14/R15。建议: 在P-CONSTITUTION §5.2中新增R14(运镜语义)和R15(画面外声音源)的正式定义。

### ⚠️-5: yaml_only过渡期Agent输入格式未定义
yaml_only §6.2描述了调度器回退逻辑，但未定义Agent指令文件如何同时支持.yml和.md输入。建议: 新增Agent输入声明模板(见本报告§3.3建议)。

### ⚠️-6: agent_quick_ref §E.1 regex与§E.1自身宣称的"100%准确率"矛盾
简化版regex的准确率低于gate0 v1.1扩展版。建议: §E.1标题改为"Gate 0检查项概念速查(非可执行regex·完整regex见gate0_context_aware §3.1)"。

### ⚠️-7: gate0伪代码中变长后顾断言Python兼容性
R03 regex中`(?<!(?:第\d+|t=|...))`使用变长分支，标准`re`模块不支持。建议: 改为`import regex`或拆分为多个固定宽度后顾。

---

## 修复建议优先级排序

| 优先级 | 缺陷编号 | 修复文件 | 工作量 |
|:---:|:---|:---|:---:|
| P0 | 🛑-1 | P-CONSTITUTION.md + agent_quick_ref §E.1 | 中(需同步3文件) |
| P0 | 🛑-2 | yaml_only_protocol §4.1 + §3.1 | 中(需新增schema节) |
| P0 | 🛑-3 | gate0_context_aware §3.1 | 中(需补充4函数逻辑) |
| P0 | 🛑-4 | context_package_spec §6.1 | 低(改数字+加注释) |
| P1 | ⚠️-2 | context_package_spec §3.2/3.4 | 低(消除歧义) |
| P1 | ⚠️-6 | agent_quick_ref §E.1 | 低(改标题+加声明) |
| P1 | ⚠️-4 | P-CONSTITUTION §5.2 | 低(新增R14/R15) |
| P2 | ⚠️-1 | context_package_spec §9 | 低(嵌入3条规则) |
| P2 | ⚠️-3 | agent_quick_ref §D | 低(新增D.5) |
| P2 | ⚠️-5 | yaml_only_protocol §6.2 | 低(新增模板) |
| P3 | ⚠️-7 | gate0_context_aware §3.1 | 低(改import) |

---

## 最终声明

四个修复文件构成了一套逻辑自洽的减浪费方案，核心机制(公共上下文预编译·KB规则速查化·Gate 0确定性前置·Agent间YAML-only通信)方向正确。部署前需解决4项阻断缺陷——其中regex三源不一致和yaml_only schema冲突是最紧迫的，因为它们会直接导致Agent在运行时加载错误文件或使用错误的检查规则。7项警告可在部署后迭代修复。

**综合裁决: ⚠️ 有条件通过 — 修复4项🛑阻断后可达✅通过。**

---

> **监督审查专家签名:** EP14_WASTE_FIX_SUPERVISION.md
> **审查范围:** 4个Phase 2产出文件 × 5个参考文件 × 4个审查维度
> **核心发现:** 4项阻断(正则三版不一致·schema冲突·伪代码缺函数·97%过度宣称) + 7项警告
> **修复后预期:** 四个文件可安全部署·实际token节省约50-55%(非宣称的68-97%)·过渡期需Agent指令文件同步更新
