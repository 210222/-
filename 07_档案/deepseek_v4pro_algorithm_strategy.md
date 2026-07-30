# DeepSeek V4 Pro 算法设计最强策略 — MODE:P 管道专属

> **制定日期:** 2026-07-08
> **数据来源:** MODE:P全管道运行日志（EP13/EP14/EP15·15次Agent调用·1,806,420 tokens）
> **核心日志:** EP14_TOKEN_FORENSICS.md · EP14_ARCHITECTURE_WASTE.md · EP14_PERFORMANCE_ANALYSIS.md · REDTEAM_TWOSTAGE_ATTACK.md · ALGORITHM_ANALYSIS_TWOSTAGE.md · FEEDBACK_LOG.json
> **代码文件:** shot_classifier.py(305行) · intent_mapper.py(294行) · performance_matcher.py(~200行) · script_assembler.py(~350行) · intent_strategies.json(21策略)
> **策略原理:** 用MODE:P真实失败数据驱动V4 Pro深度推理·约束式提示词架构·五段强制推理链

---

# §0 策略核心原理

## 0.1 MODE:P管道真相（从日志中提炼）

MODE:P管道的本质是**两阶段设计**：意图先行 → 参数后填。管道中有两类组件：
- **确定性算法**（应零LLM·纯Python）：shot_classifier, intent_mapper, performance_matcher, script_assembler, Gate 0
- **LLM Agent**（应深度推理·非机械执行）：意图Agent, LLM参数设计, Scene Auditor

日志揭示的核心矛盾：

```
矛盾一 — "确定性算法精度不足·LLM补位":
  shot_classifier精度68%→分类错误→后续一切错误
  intent_mapper信息损失41%→默认参数不准→更多镜需要LLM
  → 确定性算法越弱·LLM工作量越大·成本越高

矛盾二 — "LLM做确定性工作":
  SSA用177K tokens检测了3项正则可发现的阻断
  SDA用144K tokens做了零阻断审计
  → LLM被当成正则引擎用·浪费率84.5%

矛盾三 — "Agent提示词驱动发散":
  Movement Designer收到"设计运镜"→978行·有效信息密度0.1%
  → 开放式提示词=V4 Pro发散推理=信号湮灭
```

**策略目标:** 强化确定性算法（精度68%→90%+）·把LLM从确定性工作中解放出来·让V4 Pro只在它真正擅长的创意推理上深度工作。

## 0.2 V4 Pro在MODE:P中的角色

```
MODE:P管道算法分层：

Layer 0: 确定性引擎（0 LLM）
  ├── shot_classifier.py     → 镜功能分类
  ├── intent_mapper.py       → 意图→策略+默认参数
  ├── performance_matcher.py → 心理状态→解剖学描述
  ├── script_assembler.py    → 台本组装·keyframe生成
  └── Gate 0 scanner         → 正则确定性检查(R01-R15)

Layer 1: 算法设计（V4 Pro·thinking=ON）
  → 改进Layer 0的算法本身
  → 分析失败模式·设计新算法

Layer 2: 创意生成（V4 Pro·thinking=ON）
  → 意图Agent: 剧本→意图卡
  → LLM参数设计: LOW置信度镜→定制参数
  → 这些不是"算法设计"任务·不在此策略范围内
```

## 0.3 核心原则：失败驱动·约束式推理

```
❌ 开放式: "设计更好的分类器" → V4 Pro发散 → 论证多·伪代码少
✅ 约束式: "分类器在4种失败模式(附真实案例)下精度68%。
          硬约束: 零LLM·<5ms/镜·纯Python。
          目标: 90%精度·5%容许UNCERTAIN率。
          按Step1→5推理。输出JSON+完整Python实现。"
          → V4 Pro锁定问题空间·深度推理·可部署输出
```

**约束式 = 失败案例 + 硬约束 + 输出格式 + 推理步骤。四者缺一不可。**

---

# §1 MODE:P 算法地图：8个节点

## 1.1 代码文件（真实存在的5个）

| # | 文件 | 行数 | 当前方法 | 当前精度 | 核心问题 |
|:--|------|:---:|---------|:------:|---------|
| **A1** | `shot_classifier.py` | ~305 | 正则关键词匹配+if-elif链 | 68% | 4类失败模式·词汇缺口+语义模糊 |
| **A2** | `intent_mapper.py` | 294 | strategy→查表+反馈回写 | 信息损失41% | 策略覆盖70.5%·时序维度缺失 |
| **A3** | `performance_matcher.py` | ~200 | 15状态关键词→解剖学描述 | 未量化 | 关键词vs语义理解·单状态输出 |
| **A4** | `script_assembler.py` | ~350 | keyframe驱动·ZONE_KEYWORDS | 未量化 | 镜头分配逻辑·MODEL选择规则 |
| **A5** | `intent_strategies.json` | 21策略 | 静态查表·default_params | 覆盖70.5% | 语义→参数损失41%·置信度误判 |

## 1.2 管道内嵌算法（尚未独立为代码文件·3个）

| # | 算法 | 当前位置 | 当前状态 | 核心问题 |
|:--|------|---------|---------|---------|
| **A6** | Gate 0 Scanner | LLM审计Phase 0 | 嵌入Agent·浪费3-175K tokens | R01-R15全部正则可检测·需剥离 |
| **A7** | Confidence Calibration | intent_strategies.mapping_rules | 硬编码·6HIGH→应2HIGH | HIGH标签给了确定性0.45的策略 |
| **A8** | Strategy Coverage Model | ALGORITHM_ANALYSIS | 10→21策略推导·未实施 | 12类盲区·出现频率63% |

## 1.3 各节点设计难度与V4 Pro配置

| 节点 | 难度 | thinking | temp | max_tokens | 说明 |
|------|:----:|:--------:|:----:|:----------:|------|
| A1 分类器 | ⭐⭐⭐⭐ | ON | 0.1 | 16K | 4类失败模式·需完整Python类 |
| A2 映射器 | ⭐⭐⭐⭐⭐ | ON | 0.1 | 20K | 信息损失补偿·多维度参数化函数 |
| A3 表演匹配 | ⭐⭐⭐ | ON | 0.1 | 12K | 关键词→语义·多状态组合 |
| A4 脚本组装 | ⭐⭐ | OFF | 0.0 | 8K | 规则逻辑优化·纯确定性 |
| A5 策略规则库 | ⭐⭐⭐⭐ | ON | 0.1 | 16K | 策略定义重写·需领域知识 |
| A6 Gate 0 | ⭐⭐ | OFF | 0.0 | 5K | 纯正则·不需要推理 |
| A7 置信度 | ⭐⭐⭐ | ON | 0.1 | 10K | 统计校准·升级/降级条件 |
| A8 覆盖模型 | ⭐⭐⭐ | ON | 0.1 | 10K | 数学模型推导·策略排序 |

---

# §2 提示词架构：五段式强制推理

## 2.1 架构总览

这是从MODE:P运行日志中提炼的**唯一验证有效的提示词结构**。

```
┌──────────────────────────────────────────────────────────────────┐
│                五段式强制推理框架（MODE:P算法设计专用）              │
│                                                                    │
│  §1 问题定义（精确约束）                                             │
│     ├─ 输入数据类型+真实示例（贴项目中的真实数据·不编造）               │
│     ├─ 输出要求（Python class/func·不是自然语言描述）                  │
│     ├─ 正确性判据（量化指标+回测方法）                                │
│     └─ 硬约束+软约束（必须满足 vs 尽量满足）                           │
│                                                                    │
│  §2 当前算法基线                                                    │
│     ├─ 当前方法（引用具体代码文件:行号·不概括描述）                    │
│     ├─ 当前精度（精确数值·附回测场景名）                              │
│     ├─ 失败模式（分类·频次·真实输入输出对）                           │
│     └─ 失败根因（每类一句话·引导V4 Pro定位问题本质）                   │
│                                                                    │
│  §3 设计空间                                                       │
│     ├─ 可用信息源（穷举·标出哪些可用·哪些不可用）                      │
│     ├─ 可用技术手段（穷举·每种的技术约束）                             │
│     ├─ 硬约束（绝对不能突破的·如零LLM·<5ms·纯Python）                │
│     └─ 可牺牲维度（允许trade-off的·量化范围）                         │
│                                                                    │
│  §4 强制推理步骤（最重要——防止发散）                                   │
│     Step 1 — 错误根因归类: 将失败模式按根因分类                       │
│     Step 2 — 信息瓶颈分析: 当前方法丢失了输入的哪些维度？              │
│     Step 3 — ≥3算法候选: 每种不同原理·附伪代码                        │
│     Step 4 — 对比矩阵: 精度/延迟/新增依赖/维护成本                    │
│     Step 5 — 推荐方案: 完整Python实现·可直接保存为.py                │
│                                                                    │
│  §5 输出格式（JSON Schema·强制结构化）                                │
│     {                                                              │
│       "error_analysis": {...},                                      │
│       "information_bottleneck": "...",                              │
│       "candidates": [{"name","principle","pseudocode","metrics"}],  │
│       "recommendation": {"index","rationale","full_implementation"} │
│     }                                                              │
└──────────────────────────────────────────────────────────────────┘
```

## 2.2 四个设计原理（日志验证）

```
原理1 — "失败驱动·非目标驱动":
  日志证明: 告诉V4 Pro"目标90%精度"→它优化关键词权重（原地打转）
           告诉V4 Pro"35%失败来自同义词不匹配·这是真实案例"→它提出语义嵌入
  → 必须从失败案例出发·V4 Pro需要知道"哪里痛"

原理2 — "伪代码强制深度":
  日志证明: 只要求"描述算法"→产出论证散文（Movement Designer 978行·0.1%信号）
           要求"完整Python实现·可直接保存为.py"→V4 Pro被迫将推理转化为可执行逻辑
  → 伪代码是推理深度的强制函数·不是可选项

原理3 — "多候选对抗确认偏见":
  日志证明: 单方案→V4 Pro自我辩护（SDA:"零阻断证明设计质量高"）
          ≥3候选→V4 Pro被迫比较·自我发现缺陷
  → 每个候选必须列出≥1个已知缺陷

原理4 — "JSON消除叙事包装":
  日志证明: 自然语言输出→过渡句占30-50%（SDA·SSA的"首先""综上所述""值得注意的是"）
           JSON输出→信息密度90%+
  → 输出必须是合法JSON·不要Markdown包裹·不要解释性文字
```

---

# §3 逐节点提示词模板（MODE:P专属）

以下每个模板已预填入**从MODE:P运行日志和实际代码中提取的真实数据**。

---

## A1: shot_classifier — 从规则引擎升级为语义感知引擎

```markdown
你是一个算法工程师。任务：重新设计 MODE:P 管道的 shot_classifier.py。

## §1 问题定义

**输入:** MODE:A增强剧本中的单镜文本块（~150-300字中文）
**真实输入示例:**
"""
### 分镜 4 (时长: 3.2s)
特写 | Miguel的手指停在弹头底部批号上方
他什么都没说。呼吸声暂停。画面凝固在那一刻。
"""

**输出类型:**
{
  "function_label": "情绪特写" | "开场建立" | "物件特写" | "人物建立" |
                    "对话双人" | "单人反应" | "屏幕/证据" | "过渡/转场" |
                    "退场/收起" | "动作/运动",
  "confidence": 0.0-1.0,
  "needs_llm": true | false,
  "strategy_guess": "策略标签" | null
}

**目标精度:** ≥ 90%（当前实测68%·EP13/14/15回测51镜）
**正确性判据:** 在EP13(17镜)+EP14(17镜)+EP15(17镜)上回测·与人类标注一致率≥90%

**硬约束:**
- 推理时零LLM调用
- 单镜延迟<5ms
- 纯Python·单文件·零外部pip依赖
- 新增类别=改一个DICT配置项·不改核心逻辑

**可牺牲:**
- 允许≤5%镜标记为UNCERTAIN（交给LLM Agent设计）换90%高置信分类

---

## §2 当前算法基线

**当前方法:** 正则关键词匹配+按优先级的if-elif链
**代码位置:** `01_调度器/shot_classifier.py` 第97-124行
**当前精度:** 68%（EP13/14/15三场景51镜·34镜正确）

**四种失败模式（附真实案例）:**

### 模式A: 同义词不匹配（35%·12镜）
  例1: "微距拍摄的弹头"→正确分类为"物件特写"
       "ECU弹头底部批号"→关键词列表没有"ECU"→误分类为"单人反应"
  例2: "全景展示实验室"→正确分类"空间建立"
       "整个房间尽收眼底"→未匹配→误分类
  根因: 关键词词典有限·无法覆盖语义等价表达

### 模式B: 边界模糊（25%·9镜）
  例1: "Miguel听着·没有回应·眼神微动"→"单人反应"vs"情绪特写"？边界不明确
  例2: "Rico低头继续工作"→是"人物建立"还是"过渡/转场"？
  根因: 功能标签间有模糊带·纯关键词无法做语义判断

### 模式C: 多标签冲突（20%·7镜）
  例: 分镜同时含对话("你说什么")+动作("猛地转身")→关键词同时匹配两类
  根因: 单标签输出假设与多标签现实不匹配

### 模式D: 新场景类型（20%·7镜）
  例: POV主观镜头→分类器无对应标签→fallback到"单人反应"（错误）
  根因: 功能标签体系不完整

**误差累积链（分类器是误差链起点）:**
分类器(68%) × 映射器(70%) × 策略匹配(75%) × 参数预测(70%) = 端到端35.7%

---

## §3 设计空间

**可用信息源:**
- 镜文本全文（当前仅做关键词匹配·未利用语义结构）
- 相邻镜功能标签（上下文·当前完全未用）
- 角色名列表（scene_designer已提取）
- 场景类型元数据（室内对话/室外动作/夜景）

**不可用信息源:**
- LLM（硬约束·推理时零LLM）
- 参考图/空间地图（分类阶段无此输入）

**可用技术手段:**
- 规则树重构：排除式而非匹配式（先排除不可能类别·缩小候选集）
- TF-IDF+余弦相似度：每类维护一组典型镜文本·新镜→最近邻
- 轻量嵌入：bge-small-zh（132MB·pip install sentence-transformers后可用）
- 混合路由：规则粗筛→嵌入精排→阈值以下标记UNCERTAIN
- 上下文规则：前镜标签→当前镜先验概率（马尔可夫转移矩阵）

**硬约束:** 零LLM·<5ms·纯Python·新增类别=改字典

**可牺牲维度:** 允许5%UNCERTAIN率换精度·可以用50MB模型文件

---

## §4 强制推理步骤

你必须按以下步骤逐步推理，每步输出中间结果：

**Step 1 — 错误根因归类:**
将4类失败模式归类为根因：
- 词汇缺口（模式A）
- 语义模糊（模式B+C·本质都是语义而非词汇问题）
- 覆盖率不足（模式D）
计算每类根因占比和解决后的精度上限。

**Step 2 — 信息瓶颈分析:**
当前正则匹配丢失了镜文本的哪些维度？
- 句法结构（"微距拍摄的弹头"→"微距"修饰的是"弹头"·当前是词袋模型）
- 修饰关系（副词→动词·形容词→名词的语义绑定）
- 情感语义（"他什么都没说"→情绪负荷高·非中性描述）
- 上下文（前镜是"空间建立"→当前镜大概率不是另一个"空间建立"）
量化每个丢失维度的精度贡献。

**Step 3 — ≥3算法候选（不同原理·非参数变体）:**
候选A: 规则树重构（排除式·关键词→快速排除5-7类→剩余2-3类精细判断）
候选B: 嵌入相似度（TF-IDF或bge-small-zh·每类维护原型向量集）
候选C: 混合路由（规则粗筛→嵌入精排→置信度<0.7→UNCERTAIN）
候选D: [你自己提出·必须与A/B/C原理不同]

每个候选需给出：原理（为什么有效）、伪代码、覆盖的失败模式、精度估计、延迟估计

**Step 4 — 对比矩阵:**
| 维度 | A规则树 | B嵌入 | C混合 | D(你的) |
|------|:-----:|:----:|:----:|:-----:|
| 精度估计 | | | | |
| 延迟(ms/镜) | | | | |
| 新增依赖 | | | | |
| UNCERTAIN率 | | | | |
| 维护成本 | | | | |
| 主要缺陷 | | | | |

**Step 5 — 推荐方案:**
选最优候选·给出：
- 完整的Python类实现（class ShotClassifier: ...）
- __init__（加载什么数据·做什么预处理）
- classify(shot_text, context=None) -> ClassificationResult
- 配置字典（LABEL_CONFIG·如何添加新类别）
- 回测方法（如何验证精度）

---

## §5 输出格式

严格输出以下JSON（不要额外文字·不要Markdown代码块包裹·直接JSON）:

{
  "error_analysis": {
    "lexical_gap": {"pct": 35, "count": 12, "root": "关键词词典有限"},
    "semantic_ambiguity": {"pct": 45, "count": 16, "root": "词袋模型丢失语义"},
    "coverage_gap": {"pct": 20, "count": 7, "root": "标签体系不完整"}
  },
  "information_bottleneck": {
    "lost_dimensions": [...],
    "dimension_contribution": {...},
    "max_theoretical_precision": 0.XX
  },
  "candidates": [
    {
      "name": "...",
      "principle": "...",
      "pseudocode": "...",
      "precision_estimate": 0.XX,
      "latency_ms": N,
      "dependencies": [...],
      "uncertain_rate": 0.XX,
      "known_weakness": "..."
    }
  ],
  "recommendation": {
    "candidate_index": N,
    "rationale": "...",
    "full_implementation": "完整Python类代码..."
  }
}
```

---

## A2: intent_mapper — 补偿41%语义信息损失

```markdown
你是一个算法工程师。任务：重新设计 MODE:P 管道的 intent_mapper.py。

## §1 问题定义

**输入:** 意图卡（来自意图Agent的输出·EP13_INTENT_CARDS.json格式）
{
  "shot_id": "4",
  "visual_strategy": "[感官剥夺]",
  "narrative_function": "揭示",
  "character_psychology": "Miguel紧张·专注·怀疑",
  "emotion_note": "镜#4([感官剥夺]·极窄·与Miguel共享视角局限)",
  "scene_context": "鉴证科实验室·冷白光·全封闭无窗"
}

**输出:** 预填的摄影参数
{
  "shot_type": "大特写",
  "focal_length": "100mm",
  "dof": "f/1.4",
  "movement": "固定",
  "angle": "水平·侧光方向",
  "lighting": "侧光·单光源",
  "confidence": "HIGH"|"MEDIUM"|"LOW",
  "llm_required": true|false,
  "source": "意图策略: [感官剥夺]"
}

**当前信息损失率:** 41%（10策略平均·数据来源ALGORITHM_ANALYSIS_TWOSTAGE.md §1.1）
**目标信息损失率:** <15%

**硬约束:**
- 映射阶段零LLM
- 查表O(1)·延迟<1ms
- 策略新增=改intent_strategies.json·不改映射器代码
- 策略组合（多标签）→按优先级合并·不是取第一个

---

## §2 当前算法基线

**当前方法:** strategy→default_params查表 + tuning_params微调 + 反馈回写
**代码位置:** `01_调度器/intent_mapper.py` 第17-145行（map_intent_to_params函数）
**策略规则:** `04_共享/intent_strategies.json`（21策略·当前版本v2.0）

**10策略信息损失分解（ALGORITHM_ANALYSIS_TWOSTAGE.md §1.1实测）:**

| 策略 | 损失率 | 核心丢失 |
|------|:-----:|---------|
| 感官剥夺 | 25% | "与角色共享视角局限"→无参数表达 |
| 标准对话三角形 | 35% | 外反拍/内反拍选择规则·OTS规格缺失 |
| 冷暖色温交界 | 50% | 交界位置无坐标·色温差值未参数化 |
| 非人化→常化 | 40% | 过渡easing/时长未定义 |
| 空间建立 | 15% | 较高一致 |
| 证据/屏幕展示 | 45% | 屏幕vs实物二选一模糊 |
| 沉默中的情绪转折 | 55% | "沉默"≠"极慢推近"·推近时机才是关键 |
| 运动/动作中的揭示 | 60% | 运动路径和揭示时机完全空白 |
| 人物出场/退场 | 50% | 出场和退场参数相同·注意力转移缺失 |
| 空镜收尾 | 35% | "替代表演"意图未参数化 |

**四个信息损失来源（按贡献排序）:**
1. 时序维度缺失(30%): "过渡""揭示""转折"有时间动态·default_params只有静态快照
2. 空间关系未参数化(25%): "交界位置""机位几何""POV连接"未被表达
3. 情感意图丢失(25%): "共享视角局限""替代表演""注意力转移"
4. 选择规则缺失(20%): 二选一场景无决策规则

**当前反馈回写逻辑（intent_mapper.py第162-193行）:**
- 从FEEDBACK_LOG.json读取4条成功设计
- 同策略·同叙事功能→置信度LOW→MEDIUM
- 问题: 仅4条数据·匹配逻辑简单·无衰减模型

---

## §3 设计空间

**新增参数化维度:**
- 对象尺寸→焦距函数: f(obj_size_cm, distance_m) → focal_length_mm
- 角色POV→景深函数: f(pov_level) → dof
- 情绪强度→运镜速度: f(emotion_intensity) → movement_speed
- 情感影响向量: 孤独→[+1景别紧缩, +0.5焦距拉长, +0.3对比度]
- 场景类型偏移: 实验室→[+500K色温, +0.5景深收缩]

**策略组合处理:**
- 当前只取第一个策略标签（intent_mapper.py第28-39行·re.findall取第一个匹配）
- 需要支持多策略合并：[A]+[B]→取A的景别·B的光影·C的运镜
- 冲突解决规则：景别取最紧的·焦距取最长的·光影取主导策略的

**反馈学习升级:**
- 当前宽松匹配（fb_narrative in intent_narrative）
- 需要：FSRS衰减模型·CV<15%自动固化·≥3次成功→候选新策略

**硬约束:** 零LLM·O(1)·改JSON不改代码·支持多策略组合

---

## §4 强制推理步骤（同上Step 1-5）

## §5 输出格式（JSON）
```

---

## A3: performance_matcher — 从关键词到语义匹配

```markdown
你是一个算法工程师。任务：升级 MODE:P 管道的 performance_matcher.py。

## §1 问题定义

**输入:** 角色心理状态描述
例: "Miguel在说谎·回避直接回答·但内心紧张·手指微颤"

**输出:** 匹配的表演状态+完整解剖学描述
{
  "primary_state": "lying",
  "secondary_state": "avoidance",   // 当前不支持双状态
  "anatomical": {
    "eyes": "眨眼频率先抑制(0-2秒)后激增(3-5秒)·注视对方时间增加监控反应",
    "brow": "短暂眉间纵纹(<500ms微表情)·随后被抑制",
    "mouth": "代偿性过度控制·微笑启动延迟约200ms·嘴角不对称",
    "hands": "自我安抚动作增加·触碰面部/颈部/衣物",
    "voice": "基频微升10-15Hz·回答前潜伏期延长"
  },
  "match_confidence": 0.85
}

**当前状态:**
- 15个心理状态×5个解剖维度（代码中内嵌·第17-40行可见4个状态）
- 纯关键词匹配（"没有""不是""骗""假"→lying）
- 单状态输出·不支持状态组合
- 精度未量化·无回测数据

**目标:**
- 支持多状态组合（主状态+次状态·如lying+avoidance·lying+anger）
- 精度可量化（需定义回测方案）
- 新增状态=改字典·不改逻辑

**硬约束:** 零LLM·<2ms/匹配·纯Python·零外部依赖

---

## §2 当前算法基线

**当前方法:** 15状态关键词列表→第一个匹配的状态→输出该状态解剖学描述
**代码位置:** `01_调度器/performance_matcher.py` 第17-40行（STATES字典+keywords字段）
**问题:** 关键词匹配丢失了心理状态的微妙组合（人说谎时常同时回避·两者解剖学表现叠加）

## §3 设计空间

**改进方向:**
- 语义匹配：用轻量嵌入替代关键词（同bge-small-zh·与A1共享依赖）
- 多状态组合：加权叠加（主状态×0.7+次状态×0.3→合并解剖学描述）
- 置信度输出：match_confidence基于关键词命中密度和相邻镜状态一致性

## §4-5 同上...
```

---

## A4: script_assembler — 优化确定性组装逻辑

```markdown
你是一个算法工程师。任务：审查并优化 MODE:P 管道的 script_assembler.py。

## §1 问题定义

**当前状态（代码位置: `01_调度器/script_assembler.py`）:**
- keyframe驱动的帧生成（line 1注释·实际实现待确认）
- MODEL字典: (shot_type, has_motion)→渲染模型（line 23-28）
- ZONE_KEYWORDS: 空间区→机位关键词（line 31-34）
- PFAL规则列表: 按渲染模型的已知失败模式（line 15-21）
- HOLD_PATTERNS: 模板化的帧间保持文本（line 37-40）

**需要验证/优化的问题:**
1. MODEL选择规则是否完整？是否有未覆盖的(shot_type, has_motion)组合？
2. ZONE_KEYWORDS映射是否覆盖所有空间区类型？
3. PFAL列表是否缺少已知失败模式？
4. HOLD_PATTERNS的文本质量是否足够自然？

**硬约束:** 零LLM·纯Python·所有规则显式可查

## §2-5 同上·由于任务为审查优化·可简化推理步骤
```

---

## A5: intent_strategies.json → 策略规则库重设计

```markdown
你是一个算法工程师+电影摄影指导。任务：重新设计 MODE:P 的 intent_strategies.json。

## §1 问题定义

**当前状态:**
- 21个策略·每个有desc+default_params+tuning_params（v2.0·2026-07-08）
- 策略覆盖率: 70.5%实测（ALGORITHM_ANALYSIS_TWOSTAGE.md §2.1）
- 需要21策略达95%覆盖率（渐近覆盖模型·log(0.05/0.30)/log(0.85)≈11新增）
- 当前6个HIGH·实际应2个HIGH+4个MEDIUM（置信度误判）

**已知盲区（含出现频率·见REDTEAM_TWOSTAGE_ATTACK.md+ALGORITHM_ANALYSIS）:**
- OTS过肩(12%) | 单人对白(10%) | POV主观(8%) | 双人同框(6%)
- 多人对话(6%) | 低角度(5%) | 手持纪实(3%) | 跳切蒙太奇(3%)
- 反射镜像(2%) | 叠化时间过渡(2%) | 梦境/主观现实(2%) | 变焦推拉(4%)

**目标:**
- 新增策略填补高优先级盲区（OTS·POV·多人对话·梦境）
- 重校准置信度: 每个策略给出参数确定性分数(0-1)
- 每个策略增加: 情感影响向量·环境覆盖规则·策略组合兼容性

## §2 当前算法基线

**当前文件:** `04_共享/intent_strategies.json`（21策略·v2.0）

**问题1: 默认参数·但缺少参数确定性量化**
例: 感官剥夺 default_params="大特写/100mm/f/1.4/侧光"
    但确定性仅0.55——对象不同·焦距150-400mm都有可能

**问题2: llm_required标签不准确**
7个策略标记为llm_required·但某些在高确定性场景(如简单POV)可能不需要LLM

**问题3: 缺少策略间交互规则**
[空间建立]+[冷暖色温交界]→24mm广角+双色温→需要参数合并规则

## §3 设计空间

**新增字段建议:**
```json
{
  "strategies": {
    "感官剥夺": {
      "desc": "...",
      "default_params": {...},
      "param_certainty": 0.55,        // 新增·参数确定性分数
      "emotion_vector": {              // 新增·情感影响向量
        "孤独": {"shot_size": -0.3, "focal": +0.2, "contrast": +0.3},
        "恐惧": {"shot_size": -0.5, "focal": +0.3, "movement": +0.2}
      },
      "compatible_with": ["冷暖色温交界", "夜景/弱光"],  // 新增·策略组合
      "conflicts_with": ["空间建立"],                     // 新增·互斥策略
      "confidence_conditions": {       // 新增·置信度升级条件
        "upgrade_to_high": "跨3+场景·CV<15%·零LLM覆盖"
      }
    }
  }
}
```

## §4-5 同上...
```

---

## A6: Gate 0 Scanner — 零token正则引擎

```markdown
你是一个算法工程师。任务：将Gate 0从LLM审计中剥离·实现调度器自执行的零token正则扫描。

## §1 问题定义

**当前状态（数据来源EP14_TOKEN_FORENSICS.md §1.7·§3.2）:**
- SSA用177,595 tokens检测了3项阻断——全部正则可检测
- Scene Auditor Phase 0用~3K tokens(含Agent调用开销)执行15项Gate 0规则
- R01-R15共15项：13项100%正则·1项数值比较(diff)·1项需白名单过滤

**三个真实案例（来自EP14 S1·案情室场景）:**
阻断1: "开始后退一步"→正则 /开始(?!前)/
阻断2: "缓缓推近"→正则 /缓缓|渐渐|逐渐/
阻断3: "v_dolly·ω_pan"→正则 /v_dolly|ω_pan|a_accel/

**目标:**
- 调度器自执行Gate 0（Python脚本·非Agent调用·非LLM token）
- 15项规则·全部100%准确（正则保证）
- <100ms完成扫描
- 输出YAML格式GATE0_PRE_REPORT.yml

**硬约束:** 纯Python·re模块·零外部依赖·零LLM token

---

## §2 设计空间

**15项Gate 0规则分类:**
- 纯正则(13项): R01-R09, R11-R13, R15 → 一行re.search()
- 数值比较(1项): R14台本锚点vs PLAN锚点→diff或字符串比对
- 白名单过滤(1项): R10模型名假阳性→检查匹配位置是否在header元数据行

**实现方案（~100行Python）:**
```python
# gate0_scanner.py
import re
import sys

RULES = {
    "R01": {"pattern": r"开始(?!前)", "desc": "过程动词"},
    "R02": {"pattern": r"缓缓|渐渐|逐渐", "desc": "时间模糊词"},
    # ... R03-R15
}

def scan(script_path: str, plan_path: str = None) -> dict:
    """扫描台本文件·返回Gate 0报告"""
    with open(script_path, 'r', encoding='utf-8') as f:
        text = f.read()

    results = []
    for rule_id, rule in RULES.items():
        matches = list(re.finditer(rule["pattern"], text))
        # 白名单过滤: 排除header行
        real_matches = [m for m in matches
                       if not is_header_line(text, m.start())]
        results.append({
            "rule": rule_id,
            "desc": rule["desc"],
            "status": "🛑" if real_matches else "✅",
            "matches": [text[m.start()-20:m.end()+20] for m in real_matches]
        })

    return {"total_rules": len(RULES), "blocks": [...], "results": results}
```

## §3-5 精简·可直接输出完整实现
```

---

## A7: Confidence Calibration — 动态置信度分级

```markdown
你是一个算法工程师。任务：将 MODE:P 的置信度分级从硬编码改为动态校准。

## §1 问题定义

**当前状态:**
- 置信度分界硬编码在intent_strategies.json的mapping_rules中
- 6个HIGH·实测仅2个真正稳定（参数确定性≥0.7）
- 需要降级4个: 感官剥夺(0.55)/证据展示(0.45)/出场退场(0.50)/空镜收尾(0.75→边界)

**升级/降级条件（来自ALGORITHM_ANALYSIS_TWOSTAGE.md §4.2-4.3）:**
- MEDIUM→HIGH: 跨3+场景CV<15% + 零LLM覆盖记录 + 无二选一参数
- LOW→MEDIUM: 3+次LLM输出编辑距离<20% + 可提取tuning规则 + 审查通过率>80%
- LOW收敛: λ=0.75/场景·4-5场景后LOW<10%

**目标:**
- 置信度不再硬编码·基于实际运行数据动态计算
- 每次管道运行后自动更新（类似FEEDBACK_LOG的回写机制）

## §2 设计空间

**动态置信度引擎:**
```python
class ConfidenceEngine:
    def __init__(self):
        self.history = []  # 每次运行的(param_determinacy, llm_overrides)

    def calibrate(self, strategy_key: str) -> str:
        """返回 HIGH | MEDIUM | LOW"""
        records = [r for r in self.history if r["strategy"] == strategy_key]
        if len(records) < 3:
            return "MEDIUM"  # 数据不足·保守

        cv = compute_cv(records)  # 参数变异系数
        override_rate = sum(1 for r in records if r["llm_overridden"]) / len(records)

        if cv < 0.15 and override_rate == 0:
            return "HIGH"
        elif cv < 0.30 or override_rate < 0.2:
            return "MEDIUM"
        else:
            return "LOW"
```

## §3-5 同上...
```

---

## A8: Strategy Coverage Model — 策略扩展路线图

```markdown
你是一个算法工程师。任务：定义 MODE:P 策略从21→26策略的精确扩展路线图。

## §1 问题定义

**当前覆盖率:** 70.5%（21策略·实测·ALGORITHM_ANALYSIS_TWOSTAGE.md §2.1）
**目标覆盖率:** 95%
**边际覆盖模型:** 每新策略→覆盖15%×剩余盲区
**推导:** 当前盲区=29.5%·需覆盖24.5%→log(0.05/0.295)/log(0.85)≈5个新策略

**12个盲区按ROI排序:**
P0(>8%): OTS过肩(12%)·单人对白(10%)·POV主观(8%)
P1(4-8%): 双人同框(6%)·多人对话(6%)·低角度(5%)
P2(<4%): 手持纪实(3%)·跳切蒙太奇(3%)·反射镜像(2%)·叠化(2%)·梦境(2%)·变焦推拉(4%)

## §2 设计空间

**新增5策略的default_params定义:**
1. OTS过肩: 中近景/50-85mm/f2.8/肩后30-45°/角色头部虚化前景
2. POV主观: 近景/40-50mm/f4-5.6/手持呼吸感±2cm/眼平高度
3. 多人对话(3+): 全景主24mm+中景插入50mm/多轴·320°跳切
4. 梦境/主观现实: 自由/14-35mm广角/可变光圈/荷兰角3-7°/不规则运镜
5. 变焦推拉(Dolly Zoom): 中景/24-100mm/同步变焦+推拉/空间压缩

## §3-5 同上...
```

---

# §4 V4 Pro参数矩阵（MODE:P专用）

```python
V4PRO_MODEP_CONFIG = {
    # ═══════════════════════════════════════════════
    # 算法设计（A1-A3, A5, A7-A8）
    # ═══════════════════════════════════════════════
    "algorithm_design": {
        "model": "deepseek-v4-pro",
        "temperature": 0.1,
        "top_p": 0.9,
        "max_tokens": 16000,
        "extra_body": {"enable_thinking": True},
    },

    # ═══════════════════════════════════════════════
    # 确定性优化（A4, A6）
    # ═══════════════════════════════════════════════
    "deterministic": {
        "model": "deepseek-v4-pro",
        "temperature": 0.0,
        "top_p": 1.0,
        "max_tokens": 8000,
        "extra_body": {"enable_thinking": False},
    },

    # ═══════════════════════════════════════════════
    # 意图Agent（MODE:P Phase 1·非算法设计）
    # ═══════════════════════════════════════════════
    "intent_agent": {
        "model": "deepseek-v4-pro",
        "temperature": 0.3,
        "top_p": 0.9,
        "max_tokens": 8000,
        "extra_body": {"enable_thinking": True},
    },

    # ═══════════════════════════════════════════════
    # LLM参数设计（MODE:P Phase 3·LOW置信度镜）
    # ═══════════════════════════════════════════════
    "param_design": {
        "model": "deepseek-v4-pro",
        "temperature": 0.5,
        "top_p": 0.92,
        "max_tokens": 4000,
        "extra_body": {"enable_thinking": True},
    },
}
```

| 任务类型 | thinking | temp | max_tokens | 原因 |
|---------|:--------:|:----:|:----------:|------|
| 算法设计 A1-A3,A5,A7-A8 | ON | 0.1 | 16-20K | 需要深度推理·低温度保确定性 |
| 确定性优化 A4,A6 | OFF | 0.0 | 5-8K | 纯逻辑·不需要推理链 |
| 意图Agent | ON | 0.3 | 8K | 需要理解剧本·中等温度 |
| LLM参数设计 | ON | 0.5 | 4K | 创意需要一定随机性 |

---

# §5 反模式目录（MODE:P日志验证）

## 5.1 五个致命反模式

### 🔴 AP-1: "设计更好的X"（开放式）
```
日志证据: Movement Designer提示词含"为每个镜头设计运镜方案"
→ 产出978行·有效信息密度0.1%
修正: "当前运镜节978行·700行为零信息辩护。S-Level场景(6/7镜固定)只需1行：
      '全固定·仅镜#A6推近0.05x·S1。' 输出≤50行·只写非固定镜参数。"
```

### 🔴 AP-2: "逐条检查规则"（LLM替代正则）
```
日志证据: SSA 177K tokens检测3项阻断·全部正则可检测
修正: "Gate 0已用正则扫描了R01-R15。你只检查Gate 0无法覆盖的主观质量维度。
      如果某项检查可以用正则表达→它不属于你的审计范围。"
```

### 🔴 AP-3: "分析当前系统"（分析≠设计）
```
日志证据: 分析报告产出描述+建议·未转化为可执行算法
修正: "基于附件的失败数据·提出≥3种不同原理的算法方案。
      每种必须有伪代码。选最优给出完整Python实现。不要只描述问题。"
```

### 🔴 AP-4: 自然语言输出（叙事格式）
```
日志证据: SDA·SSA审计报告过渡句占30%+·"首先""综上""值得注意的是"
修正: "输出必须为合法JSON。不要Markdown包裹。不要解释性文字。纯JSON。"
```

### 🔴 AP-5: 单候选方案（确认偏误）
```
日志证据: 单方案→V4 Pro自我辩护
修正: "必须≥3候选·不同原理·每个列出≥1缺陷。选最优并解释为什么优于其他。"
```

## 5.2 反模式速查

| 反模式 | 症状 | 诊断 | 修正 |
|--------|------|------|------|
| AP-1 开放式 | 输出含大量"合理性论证" | 检查辩护段落占比 | 给出精确基线+失败案例 |
| AP-2 LLM做正则 | 输出=逐条✅/❌列表 | ✅占比>80% | Gate 0前置·LLM只做语义判断 |
| AP-3 分析≠设计 | 输出=描述+建议·无代码 | 搜索"class ""def ""算法" | 强制要求完整Python实现 |
| AP-4 叙事格式 | 含"首先""综上""值得注意的是" | 过渡词密度>5% | 强制JSON schema |
| AP-5 单候选 | 只有1个方案 | 搜索"候选""方案""替代" | 强制≥3候选·每候选≥1缺陷 |

---

# §6 测量与迭代

## 6.1 六个效果指标

```python
ALGORITHM_DESIGN_METRICS = {
    "signal_ratio": "伪代码+实现行数 / 总输出行数",           # 目标>70%
    "candidate_diversity": "候选方案原理差异度(0-1)",         # 目标>0.5
    "implementation_ready": "可直接保存为.py·无语法错误",     # 目标=True
    "failure_coverage": "覆盖的已知失败模式占比",              # 目标=1.0
    "novel_insight": "提出日志中未记录的发现",                 # 目标≥1
    "token_efficiency": "净推理Token/总Token",                # 目标>50%
}
```

## 6.2 迭代协议

```
第1轮: 复制§3模板→V4 Pro algorithm_design参数→获取输出
    ↓ 评估6指标
第2轮: signal_ratio<50%→加强§5输出格式约束
       candidate_diversity<0.3→增加"不同原理"约束
       failure_coverage<0.8→补充遗漏案例到§2
    ↓
第N轮: 直到signal_ratio>70% AND implementation_ready=True
```

## 6.3 成功判据

```
✅ 伪代码+实现≥70%输出行数
✅ ≥3候选·原理不同·非参数变体
✅ 推荐方案完整Python类·可直接保存为.py
✅ 每个已知失败模式有对应解决逻辑
✅ Token消耗<50K（算法设计任务）
✅ ≥1洞察非直接从日志读出
```

---

> **策略版本:** v2.0 — MODE:P专属
> **数据基线:** EP13/EP14/EP15 MODE:P管道·15次Agent调用·1,806,420 tokens
> **代码基线:** shot_classifier.py(305行)·intent_mapper.py(294行)·performance_matcher.py(~200行)·script_assembler.py(~350行)·intent_strategies.json(21策略)
> **核心原则:** 约束式推理=失败案例+硬约束+输出格式+推理步骤
> **与v1.0差异:** 移除复杂度路由器和KB路由器·新增表演匹配器和脚本组装器·全部模板基于实际代码文件重写
