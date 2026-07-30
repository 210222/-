# A1: shot_classifier 重新设计 → 发送给 DeepSeek V4 Pro

> **发送方式:** 复制本文全文 → 粘贴到 DeepSeek V4 Pro 对话
> **API参数:** `enable_thinking=True, temperature=0.1, max_tokens=16000`
> **预期输出:** 完整的 Python 类代码 + 伪代码 + 对比矩阵
> **验证方式:** 保存输出为 .py → 在 EP13/14/15 数据上回测

---

你是一个算法工程师。任务：重新设计 MODE:P 管道的 shot_classifier.py。

## §1 问题定义

**输入:** MODE:A 增强剧本中的单镜文本块（~150-300 字中文），例如：

```
### 分镜 4 (时长: 3.2s)
特写 | Miguel 的手指停在弹头底部批号上方
他什么都没说。呼吸声暂停。画面凝固在那一刻。
```

**输出要求:**
```python
@dataclass
class ClassificationResult:
    function_label: str   # 10 类之一
    confidence: float     # 0.0-1.0
    strategy_guess: str | None
    needs_llm: bool       # True = 需要 LLM 参数设计
    evidence: list[str]   # 分类依据
```

**10 类功能标签:** `开场建立 | 物件特写 | 人物建立 | 对话双人 | 单人反应 | 屏幕/证据 | 过渡/转场 | 退场/收起 | 动作/运动 | 情绪特写`

**目标精度:** ≥ 90%（当前 68%）
**正确性判据:** 在 EP13(17镜) + EP14(17镜) + EP15(17镜) = 51 镜上回测，与人类标注一致率 ≥ 90%

**硬约束:**
- 推理时零 LLM 调用
- 单镜延迟 < 5ms
- 纯 Python · 单文件 · 零 `pip install` 外部依赖（标准库 only）
- 新增类别 = 改一个 DICT 配置项，不改核心逻辑

**可牺牲:**
- 允许 ≤ 5% 镜标记为 UNCERTAIN（置信度 < 阈值）交给 LLM

---

## §2 当前算法基线

**当前方法:** 正则关键词匹配 + if-elif 优先级链
**代码:** `shot_classifier.py` FUNCTION_DEFAULTS 字典 + `extract_shots()` regex
**精度:** 68%（51 镜中 34 镜正确）

### 四种失败模式（附真实案例）

**模式 A — 同义词不匹配（35%·12 镜）:**
```
输入: "ECU 弹头底部批号·微距镜头"
当前输出: "单人反应" ❌
正确输出: "物件特写" ✅
根因: 关键词列表有"微距"但没有"ECU"·语义等价表达未覆盖
```

**模式 B — 边界模糊（25%·9 镜）:**
```
输入: "Miguel 听着·没有回应·眼神微动"
当前输出: "单人反应" ❌
正确输出: "情绪特写" ✅
根因: "反应"和"情绪"的边界在关键词层面无法区分
```

**模式 C — 多标签冲突（20%·7 镜）:**
```
输入: 分镜同时包含对话("你说什么") + 动作("猛地转身")
当前输出: 第一个匹配到的标签（不稳定）
根因: 单标签输出假设与多标签现实冲突
```

**模式 D — 新场景类型（20%·7 镜）:**
```
输入: POV 主观镜头·观众通过角色眼睛看
当前输出: "单人反应"(fallback) ❌
根因: 标签体系缺少"POV"类别
```

**误差累积链:**
```
分类器(68%) × 映射器(70%) × 策略匹配(75%) × 参数预测(70%) = 端到端 35.7%
```
分类器是误差链起点——这里错，后面全错。

---

## §3 设计空间

**可用信息源:**
- 镜文本全文（当前仅做关键词匹配·未利用语义结构）
- 相邻镜的功能标签（上下文·当前未用·可构建马尔可夫转移矩阵）
- 场景类型（室内对话/室外/动作·可从增强剧本元数据获取）
- 角色名列表

**不可用:**
- LLM（硬约束）
- 参考图/空间地图（分类阶段无此输入）

**可用技术:**
- 规则树重构：排除式而非匹配式（先排除不可能的 5-7 类→缩小候选集→精细判断）
- TF-IDF + 余弦相似度（每类维护一组典型镜文本·scikit-learn 标准库可实现）
- 上下文马尔可夫模型（前镜→当前镜的标签转移概率）
- 混合路由：规则粗筛→嵌入/相似度精排→置信度 < 阈值→UNCERTAIN

**硬约束:** 零 LLM · < 5ms · 纯标准库

**可牺牲:** ≤ 5% UNCERTAIN 率 · 可以用 pickle 文件存储预计算的向量

---

## §4 强制推理步骤

按以下步骤逐步推理，每步输出中间结果：

**Step 1 — 错误根因归类:**
- 将 4 类失败模式归类为根因：词汇缺口(A) / 语义模糊(B+C) / 覆盖率不足(D)
- 计算每类根因占比
- 估算每类根因被解决后的精度上限

**Step 2 — 信息瓶颈:**
当前正则匹配丢失了镜文本的哪些信息维度？
- 句法结构（修饰关系·"微距拍摄的弹头"→微距修饰弹头）
- 情感语义（"什么都没说"→高情绪负荷）
- 上下文（前镜标签→当前镜先验）
量化每个维度的精度贡献

**Step 3 — ≥3 算法候选（不同原理·非参数变体）:**
每个候选必须包含：原理·伪代码·覆盖的失败模式·精度估计·延迟估计·至少 1 个已知缺陷

**候选 A:** 规则树重构 — 排除式·关键词快速排除 5-7 类→剩余 2-3 类精细规则判断
**候选 B:** TF-IDF 相似度 — 每类维护原型文本集·余弦相似度最近邻
**候选 C:** 混合路由 — 规则粗筛→相似度精排→置信度 < 0.7→UNCERTAIN
**候选 D:** 你自己提出·必须与 A/B/C 原理不同

**Step 4 — 对比矩阵:**
| 维度 | A | B | C | D |
|------|:--:|:--:|:--:|:--:|
| 精度估计 | | | | |
| 延迟(ms/镜) | | | | |
| 新增依赖 | | | | |
| UNCERTAIN 率 | | | | |
| 主要缺陷 | | | | |

**Step 5 — 推荐方案:**
选最优候选。给出：
- 完整的 Python 类实现（`class ShotClassifier`）
- `__init__` — 加载配置·预处理
- `classify(shot_text, prev_label=None) -> ClassificationResult`
- `LABELS` 配置字典 — 如何添加新类别
- `evaluate(test_cases) -> float` — 回测精度方法

---

## §5 输出格式

严格输出以下 JSON（不要 Markdown 代码块包裹·不要解释性文字·直接 JSON）:

```json
{
  "error_analysis": {
    "lexical_gap": {"pct": 35, "count": 12, "root_cause": "关键词词典有限·无法覆盖语义等价表达"},
    "semantic_ambiguity": {"pct": 45, "count": 16, "root_cause": "词袋模型丢失语义·单标签假设与多标签现实冲突"},
    "coverage_gap": {"pct": 20, "count": 7, "root_cause": "功能标签体系不完整·缺少POV等类型"}
  },
  "information_bottleneck": {
    "lost_dimensions": ["句法结构", "情感语义", "上下文"],
    "dimension_contribution": {"句法结构": 0.15, "情感语义": 0.10, "上下文": 0.05},
    "max_theoretical_precision": 0.94
  },
  "candidates": [
    {
      "name": "规则树重构",
      "principle": "排除式而非匹配式——先排除不可能类别缩小候选集",
      "pseudocode": "def classify(text): candidates = all_labels; for rule in exclusion_rules: candidates -= rule.exclude(text); ...",
      "precision_estimate": 0.82,
      "latency_ms": 1,
      "dependencies": ["无"],
      "uncertain_rate": 0.10,
      "known_weakness": "仍依赖关键词·对全新表达方式敏感"
    }
  ],
  "recommendation": {
    "candidate_index": 2,
    "rationale": "混合路由在精度和复杂度之间取得最佳平衡·规则的确定性+相似度的语义覆盖+UNCERTAIN兜底",
    "full_implementation": "class ShotClassifier:\n    def __init__(self):\n        ...\n    def classify(self, shot_text, prev_label=None):\n        ..."
  }
}
```
