# A6: Gate 0 Scanner 剥离 → 发送给 DeepSeek V4 Pro

> **API参数:** `enable_thinking=False, temperature=0.0, max_tokens=8000`
> **预期输出:** 完整的 gate0_scanner.py · 约 100 行 · 可直接部署

---

你是一个算法工程师。任务：将 MODE:P 管道中的 Gate 0 检查从 LLM 审计中剥离，实现为纯 Python 正则扫描器。

## §1 问题定义

**现状:**
- Gate 0 R01-R15 共 15 项检查嵌入在 Scene Auditor Phase 0 中
- SSA 曾用 177,595 tokens LLM 调用检测了 3 项阻断——全部正则可检测
- Scene Auditor Phase 0 虽精简但仍需 Agent 调用（~3K tokens 开销）

**目标:**
- 调度器自执行 Gate 0 · 零 Agent 调用 · 零 LLM token
- 15 项规则 100% 正则/数值比较（确定性 = 100% 准确率）
- < 100ms 完成全场景扫描
- 输出 YAML 格式 `GATE0_PRE_REPORT.yml`

**已验证的正则可检测案例（EP14 S1 案情室）:**
```
阻断 1: "开始后退一步"     → 正则 /开始(?!前)/
阻断 2: "缓缓推近"         → 正则 /缓缓|渐渐|逐渐/
阻断 3: "v_dolly·ω_pan"   → 正则 /v_dolly|ω_pan|a_accel/
```

## §2 设计约束

**15 项 Gate 0 规则分为三类:**
- 纯正则（13 项）: R01-R09, R11-R13, R15 → 一行 `re.search()`
- 数值比较（1 项）: R14 台本锚点 vs PLAN 锚点 → `diff` 或字符串比对
- 白名单过滤（1 项）: R10 模型名假阳性 → 检查匹配位置是否在 header 元数据行

**硬约束:**
- 纯 Python · `re` 模块 only · 零外部依赖
- 输出 YAML 格式报告
- 假阳性需白名单过滤器（不是 LLM 裁决）
- 调度器在启动 Scene Auditor 前调用此脚本

## §3 输出要求

一个完整的 `gate0_scanner.py` 文件，包含:
- `RULES` 字典: 15 条规则的 pattern + description
- `is_header_line(text, match_pos) -> bool`: 白名单过滤器
- `scan(script_path, plan_path=None) -> Gate0Report`: 主扫描函数
- `Gate0Report`: 包含 total_rules, blocked_count, blocks[], results[]
- `__main__`: CLI 入口 `python gate0_scanner.py --script 台本.md [--plan PLAN.yml]`

## §4 推理步骤

Step 1 — 规则分类: 将 15 条规则分为纯正则/数值比较/白名单过滤
Step 2 — 假阳性分析: R10 模型名假阳性的触发条件·设计白名单逻辑
Step 3 — 输出格式: Gate0Report 的 YAML 结构设计
Step 4 — 完整实现（不需要多候选·这是确定性任务·直接给出最优实现）

## §5 输出格式: JSON · 包含 full_implementation 字段
