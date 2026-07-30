# A4: script_assembler 审查优化 → 发送给 DeepSeek V4 Pro

> **API参数:** `enable_thinking=False, temperature=0.0, max_tokens=8000`
> **预期输出:** 优化建议 + 修正代码 · 纯确定性审查

---

你是一个算法工程师。任务：审查 MODE:P 管道的 script_assembler.py 并优化其确定性逻辑。

## §1 问题定义

**代码:** `script_assembler.py` (~350行)
**核心逻辑:**
- MODEL 字典: (shot_type, has_motion) → 渲染模型选择（第 23-28 行）
- ZONE_KEYWORDS: 空间区 → 机位关键词（第 31-34 行）
- PFAL 规则: 按模型的已知失败模式规避列表（第 15-21 行）
- HOLD_PATTERNS: 帧间保持模板文本（第 37-40 行）

**需要审查的问题:**
1. MODEL 字典是否覆盖了所有 (shot_type, has_motion) 组合？有无 fallback 路径？
2. ZONE_KEYWORDS 映射是否完整？新场景类型（室外·车内·走廊）是否覆盖？
3. PFAL 列表是否遗漏已知失败模式？从 REDTEAM 报告中有无新发现？
4. HOLD_PATTERNS 模板文本是否自然·有无语法问题？
5. 边界条件：PLAN 缺失时的降级逻辑是否健壮？

**硬约束:** 零 LLM · 纯 Python · 所有规则显式可查·无隐式 fallback

## §2-5 精简·确定性审查·直接输出发现+修正
