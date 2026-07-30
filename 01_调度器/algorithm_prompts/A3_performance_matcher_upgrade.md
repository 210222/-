# A3: performance_matcher 升级 → 发送给 DeepSeek V4 Pro

> **API参数:** `enable_thinking=True, temperature=0.1, max_tokens=12000`
> **预期输出:** 升级版 Python 代码 · 支持多状态组合 · 轻量语义匹配

---

你是一个算法工程师。任务：升级 MODE:P 管道的 performance_matcher.py，从纯关键词匹配升级为语义感知的多状态组合匹配器。

## §1 问题定义

**输入:** 角色心理状态描述文本
```
"Miguel在说谎·回避直接回答·但内心紧张·手指微颤·不敢直视Rico"
```

**输出:**
```json
{
  "primary_state": "lying",
  "secondary_state": "avoidance",
  "tertiary_state": "tension",
  "state_weights": {"lying": 0.6, "avoidance": 0.3, "tension": 0.1},
  "anatomical": {
    "eyes": "眨眼频率先抑制后激增·注视对方时间增加·但视线频繁漂移",
    "brow": "短暂眉间纵纹(<500ms)·随后被抑制",
    "mouth": "代偿性过度控制·微笑启动延迟·嘴角不对称",
    "hands": "自我安抚动作增加·触碰面部·手指微颤",
    "voice": "基频微升10-15Hz·回答前潜伏期延长"
  },
  "match_confidence": 0.85
}
```

**当前状态:**
- 15 个心理状态 · 每个含 keywords 列表 + 5 维解剖学描述（STATES 字典·第 17 行起）
- 纯关键词匹配 · 单状态输出
- 不支持多状态组合（人说谎时常同时回避·两者解剖学表现叠加）

**硬约束:** 零 LLM · < 2ms/匹配 · 纯 Python · 零外部依赖

## §2 当前算法基线

**代码:** `performance_matcher.py` STATES 字典（第 17-40 行可见 lying/avoidance 等状态）
**方法:** 遍历 STATES → 第一个 keywords 命中 → 输出该状态
**缺陷:** 无法表达复合心理状态（lying+avoidance+tension 是常见组合·当前只输出 lying）

## §3 设计空间

**改进方向:**
- 多状态组合: 所有命中的状态按关键词密度加权→合并解剖学描述
- 语义关联: 状态间有共现模式（lying 常与 avoidance 共现·可在字典中定义共现权重）
- 置信度输出: match_confidence 基于关键词密度+状态数+相邻镜状态一致性

**状态共现矩阵（从 PERFORMANCE_KB 中可归纳）:**
- lying + avoidance: 高频共现·人在说谎时回避
- lying + tension: 中频·说谎伴随紧张
- anger + dominance: 中频·愤怒伴随控制欲

## §4 强制推理步骤（Step 1-5）
## §5 输出格式: JSON · 包含 full_implementation
