# A5: intent_strategies 规则库重设计 → 发送给 DeepSeek V4 Pro

> **API参数:** `enable_thinking=True, temperature=0.1, max_tokens=16000`
> **预期输出:** 升级版 JSON 策略定义 · 情感向量 · 组合规则 · 置信度字段

---

你是一个算法工程师+电影摄影指导。任务：重新设计 MODE:P 的 intent_strategies.json 策略规则库。

## §1 问题定义

**当前状态:**
- `intent_strategies.json` v2.0 · 21 个策略
- 每个策略: desc + default_params + tuning_params（部分）+ llm_required 标签
- 覆盖率: 70.5% 实测 · 需 26 策略达 95%
- 6 个 HIGH 置信度标记 · 实测仅 2 个真正稳定（参数确定性 ≥ 0.7）

**三个核心问题:**

**问题 1 — 参数确定性缺失:**
default_params 是"最佳猜测"·但没有量化这个猜测的可靠程度
例: "感官剥夺" default="大特写/100mm/f1.4/侧光"
    但对象从 3cm 弹头→30cm 手机→参数完全不同·确定性仅 0.55

**问题 2 — 无策略间交互规则:**
`[空间建立]+[冷暖色温交界]` 同时在同一个镜头中出现
→ 当前只取第一个策略标签（intent_mapper.py 第 28 行）
→ 需要: 合并规则（取建立空间的全景+色温交界的光影）

**问题 3 — llm_required 标签不准确:**
7 个策略标记为 llm_required · 但某些在高确定性场景不需要 LLM
例: POV 主观在标准人眼视角的简单场景→可以直接用默认参数

## §2 设计目标

**新增字段（每个策略）:**
```json
{
  "策略名": {
    "desc": "...",
    "default_params": {...},
    "param_certainty": 0.55,           // 新增·参数确定性分数 0-1
    "emotion_vector": {                 // 新增·情感→参数偏移
      "孤独": {"shot_size": -0.3, "focal": +0.2, "contrast": +0.3},
      "恐惧": {"shot_size": -0.5, "focal": +0.3, "movement": +0.2}
    },
    "compatible_with": ["冷暖色温交界", "夜景/弱光"],
    "conflicts_with": ["空间建立"],
    "merge_rule": "取本策略的景别+焦距·取兼容策略的光影",
    "confidence_conditions": {
      "upgrade_to_high": "跨3+场景CV<15%·零LLM覆盖·无二选一参数",
      "downgrade_to_low": "LLM覆盖率>40%·参数CV>30%"
    }
  }
}
```

**新增 5 个策略填补 P0 盲区:**
1. OTS 过肩: 中近景/50-85mm/f2.8/肩后 30-45°/前景角色头部虚化
2. POV 主观: 近景/40-50mm/f4-5.6/手持呼吸感±2cm/眼平高度
3. 多人对话(3+): 全景主 24mm+中景插入 50mm/320°跳切规则
4. 梦境/主观现实: 自由/14-35mm/荷兰角 3-7°/不规则运镜
5. 变焦推拉: 中景/24-100mm/同步变焦+推拉/空间压缩效果

## §3-5 同上结构...
