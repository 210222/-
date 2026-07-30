# 架构审查报告：两阶段 MODE:P 设计 v1

> **审查日期:** 2026-07-08
> **审查对象:** `_two_stage_design_v1.md` · `intent_strategies.json` · `intent_mapper.py` · `EP13_INTENT_CARDS.json`
> **审查范围:** 数据流完整性 · 失败路径 · 系统接口 · 性能估算
> **优先级定义:** P0=阻断级(Pipeline无法运行) · P1=重要(需设计修复) · P2=优化(可迭代改进)

---

## 目录

1. [P0 — 阻断级问题](#p0--阻断级问题)
2. [P1 — 重要问题](#p1--重要问题)
3. [P2 — 优化建议](#p2--优化建议)
4. [性能估算对比](#性能估算对比)
5. [总结: 改进路线图](#总结-改进路线图)

---

## P0 — 阻断级问题

---

### P0-1: LLM 微调编排器缺失 (最关键阻断)

**问题描述:**
映射器返回 LOW/MEDIUM 置信度后，没有任何代码负责启动 LLM。`intent_mapper.py` 仅输出 `llm_required: true` 标志，但：
- 谁读取这个标志并触发 LLM 调用？
- LLM 的输入是什么？（仅策略名？全部意图卡？空间地图？剧本原文？）
- LLM 输出的格式是什么？如何合并回映射器默认参数？
- 如果 LLM 调用失败（超时/拒绝/输出格式错误），重试策略是什么？
- 多个 LOW 镜头的 LLM 调用是串行还是并行？

**影响:** Stage 2 管道无法完整运行。`llm_required` 策略（沉默中的情绪转折、运动/动作中的揭示）的镜头永远得不到参数。

**建议修复:**
1. 新建 `intent_llm_tuner.py` — 接收映射器输出 + 完整意图卡 + 空间数据 → 输出 LLM 设计的参数字段
2. 定义明确的 "LLM 输入包" 格式：包含 `full_intent_card` + `default_params` + `spatial_context` + `script_excerpt`
3. 明确合并策略：LLM 只覆盖 `default_params` 中标记为 `tunable` 的字段，其他字段保留映射器默认
4. 为多镜并行 LLM 调用设计并发管理器

```python
# 伪代码 — 缺失的编排逻辑
def stage2_orchestrator(intent_cards, strategies, space_data):
    mapper_results = map_all(intent_cards, strategies)  # 现行映射器
    
    for shot in mapper_results['shots']:
        if shot['llm_required'] or shot['confidence'] == 'LOW':
            # 🔴 这段代码不存在
            llm_params = launch_llm_tuner(
                intent_card=shot['intent'],
                default_params=extract_defaults(shot),
                spatial_context=space_data
            )
            shot = merge_params(shot, llm_params)
    
    return assemble_yaml(mapper_results['shots'])
```

---

### P0-2: 参数模型与 YAML 格式不匹配

**问题描述:**
映射器输出 6 个字段（`shot_type`·`focal_length`·`dof`·`movement`·`angle`·`lighting`），但实际的 `segments_camera` YAML 需要更多字段。对比：

| 字段 | 映射器输出 | YAML 需要 | 来源 |
|:---|:---:|:---:|:---:|
| segment_id | 无 | 必须 | 实际 YAML |
| time_range | 无 | 必须 | 实际 YAML |
| shot_type | 有 | 必须 | 一致 |
| focal_length | 有 | 必须 | 一致 |
| dof | 有 | 必须 | 一致 |
| angle | 有 | 必须 | 一致 |
| axis_side | **无** | 必须 | spatial_check.S01 依赖 |
| movement | 有 | 必须 | 一致 |
| coverage | 无 | 建议 | YAML 常见字段 |
| kb_rule_ids | 无 | 建议 | YAML 常见字段 |
| lighting | 有 | 建议 | 策略默认 |
| movement_speed | 无 | 建议 | spatial_check.S04 依赖 |

**关键缺失:**
- **`axis_side`**: 这是 `spatial_check.S01`（180度线检查）的必需输入。映射器不输出它意味着 spatial_check 对自动生成的参数无法运行。
- **`time_range`**: 意图卡不包含镜头时长信息。没有 `time_range=[start, end]` ，YAML 块无法组装为完整镜头序列。
- **`kb_rule_ids`**: 现有 Scene Auditor 依赖 KB 规则 ID 进行设计域审计（维度1A）。映射器输出 `source` 字符串而非规则 ID，破坏了审计链。

**建议修复:**
1. 在 `intent_strategies.json` 中为每个策略添加 `axis_side` 默认值
2. 为映射器添加 `time_range` 估算逻辑（从节奏位置和叙事功能推导）
3. 在策略默认值中添加 `kb_rule_refs` 字段

---

### P0-3: 复合策略被静默丢弃

**问题描述:**
`EP13_INTENT_CARDS.json` 中有 8/8 组使用单一策略标签，但其中 3 组包含复合策略信息：

| 组 | `visual_strategy` | 提取的标签 | 被丢弃的部分 |
|:---|:---|:---:|:---|
| G1 | `[空间建立] + 感官压缩` | 空间建立 | "感官压缩" — 对参数有重大影响 |
| G3 | `[标准对话三角形] + 屏幕冷蓝光作为对话第三角色` | 标准对话三角形 | 非标准光照要求 |
| G6 | `[运动/动作中的揭示] + 匀速升起` | 运动/动作中的揭示 | "匀速升起" |

映射器只匹配第一个 `[tag]`。第二个策略中可能包含关键的参数调整信息。**更危险的是**：G1 被标记为 HIGH 置信度（"空间建立"在 high_confidence 列表中），但实际需要的参数包含"感官压缩"的元素（极窄景别、浅景深等），与标准"空间建立"（大景深、24mm）完全矛盾。

**这是置信度模型的核心缺陷:** 策略标签匹配 ≠ 参数正确。一个 HIGH 置信度的映射可能给出完全错误的参数。

**建议修复:**
1. 支持复合策略：解析 `[tag1] + [tag2]` 或 `[tag1] + 文字描述` 格式
2. 对于复合策略，以第二个策略的 `llm_required` 属性为准（更保守）
3. 或：发现复合策略时自动降级为 MEDIUM 置信度，强制 LLM 介入调节
4. 或：在 `intent_strategies.json` 中定义策略组合的覆盖规则

---

### P0-4: Stage2 → 现有检查管道的集成未定义

**问题描述:**
当前管道顺序：`Agent输出YAML → Gate 0 → spatial_check → Scene Auditor → P-Verifier`

两个阶段设计下，管道变为：`Stage1(意图Agent) → 人审 → Stage2(映射器+LLM) → ???`

具体集成问题：
1. **Gate 0 输入是台本（markdown格式），不是意图卡或映射器输出格式**。Gate 0 扫描 R01-R15 全部针对 prompt_composer 的台本格式设计。映射器的 dict 输出无法通过 Gate 0。
2. **spatial_check 输入是 YAML（segments_camera 块）**，需要结构化的 segment_id、time_range、axis_side 等。映射器 dict 没有这些字段。
3. **时序问题**：Gate 0 和 spatial_check 需要完整台本才能运行，但两阶段设计中 Stage 2 的"组装"步骤（dict→YAML→台本）缺失。

**本质问题：Stage 2 没有"YAML 组装器"。** 映射器 + LLM 微调只产出参数 dict，但没有人将这些 dict 组装为符合现有检查工具输入格式的 YAML + 台本。

**建议修复:**
1. 新建 `yaml_assembler.py` — 将映射器输出 + LLM 微调结果 + 时间/空间数据 → 完整的 segments_camera YAML
2. 新建 `script_generator.py` — 从 YAML + 意图卡 → 导演台本（prompt_composer 格式）
3. 明确新管道顺序：`Stage1 → 人审 → Map → LLM调 → YAML组装 → 台本生成 → Gate0 → spatial → Auditor`

---

## P1 — 重要问题

---

### P1-1: 组级字段丢失到镜级粒度

**问题描述:**
`flatten_groups()` 将组级字段（character_psychology、audience_feeling、rhythm_position）复制到组内每个镜头，但 `key_differences` 中描述的镜级差异被映射为同一个 `emotion_note`。

以 G1 为例：`key_differences` 描述了三个镜头完全不同的视觉需求：
- 镜#1: 纯物(弹头·95%黑负空间·感官剥夺)
- 镜#2: 人物出场(底光3200K非人化→摘眼镜露脸)
- 镜#3: 数据域(屏幕·五照片并列·冷蓝6500K)

但 `flatten_groups` 将所有三个镜头的 `emotion_note` 都设为相同的 `key_differences` 全文，映射器无法区分哪个镜头需要哪种参数调整。

**影响:**
- 同组内不同镜头的情绪微调无法实现
- 如果 G1 镜头#1 需要"感官剥夺"参数（ECU·浅景深）但镜头#3 需要"数据域"参数（屏幕展示·深景深），映射器无法区分

**建议修复:**
1. 将 `key_differences` 从自由文本改为结构化数据：
```json
"shot_differences": {
  "镜#1": {"visual_focus": "纯物", "lighting": "黑负空间95%", "strategy_hint": "感官剥夺"},
  "镜#2": {"visual_focus": "人物出场", "lighting": "底光3200K→眼平", "strategy_hint": "非人化→常化"},
  "镜#3": {"visual_focus": "数据域", "lighting": "冷蓝6500K", "strategy_hint": "证据展示"}
}
```
2. 或降低组内多镜头的置信度，强制 LLM 逐镜微调

---

### P1-2: 三个意图字段被映射器完全忽略

**问题描述:**
意图卡有 5 个核心字段，映射器只用了 2 个：

| 字段 | 意图 Agent 产出 | 映射器使用 | 浪费程度 |
|:---|:---:|:---:|:---:|
| `narrative_function` | 是 | 是（策略匹配+回退推导） | 0% |
| `visual_strategy` | 是 | 是（标签提取+策略匹配） | 0% |
| `character_psychology` | 是 | **否** | 100% |
| `audience_feeling` | 是 | **否** | 100% |
| `rhythm_position` | 是 | **否** | 100% |
| `emotion_note`(key_differences) | 是 | 是（情绪微调提示） | ~30% |

`character_psychology`、`audience_feeling`、`rhythm_position` 占意图卡内容量的约 60%（按文本量计算）。映射器既不读取也不传递它们到下游。

**缓解条件（但不充分）:**
- 如果 LLM 微调阶段读取这些字段，则它们对 LOW/MEDIUM 镜头有用 → 但对 HIGH 镜头的 60% 内容仍然浪费
- 如果人类审查时需要这些字段做判断依据，则它们有存在价值

**建议修复:**
1. **映射器使用 `rhythm_position`**：从中推导 `time_range`（节奏位置暗示时长区间，如"上升"可能对应 2-4 秒，"高潮"可能对应 4-6 秒）
2. **映射器使用 `audience_feeling`**：从中提取情绪关键词，影响焦距和景深选择（"不安"→较长焦·"释放"→较宽景别）
3. 或将这 3 个字段透传到映射器输出中，供 LLM 微调阶段使用（至少保证它们不被丢弃）

---

### P1-3: 人审修改意图 → 自动重映射覆盖 LLM 修改

**问题描述:**
设计文档说："改意图=改几行文字·参数自动更新"。但当：
1. 意图 Agent 产出意图卡
2. 映射器为镜#10 生成 HIGH 参数
3. LLM 微调（因复合策略或情绪要求）覆盖了部分参数
4. 人审修改镜#10 的意图文本
5. 映射器重新运行 → 原始映射器输出覆盖 LLM 修改的参数

**问题: 没有"LLM 覆盖标记"。** 映射器无法区分"这个参数是默认值"和"这个参数被 LLM 特意调整过"。

**建议修复:**
1. 为每个参数添加来源标记：`source: mapper | llm | human`
2. 设计合并策略：`human > llm > mapper`
3. 当意图文本改变时，只重新生成未标记为 `human` 和 `llm` 的参数，或提供差异对比

---

### P1-4: 置信度模型给出虚假安全感

**问题描述:**
当前置信度判断 = 策略标签匹配程度。但策略标签匹配 ≠ 参数正确。

具体风险案例：
| 组 | 策略 | 置信度 | 实际风险 |
|:---|:---|:---:|:---|
| G1 | [空间建立] + 感官压缩 | HIGH | 参数实际需要感官剥夺特征，与空间建立默认矛盾 |
| G3 | [标准对话三角形] + 屏幕冷蓝光 | HIGH | 标准对话参数不含屏幕光照，实际需要组合 |
| G6 | [运动/动作中的揭示] + 匀速升起 | LOW | 正确识别为 LOW |
| G7 | [冷暖色温交界] | MEDIUM | 正确识别为 MEDIUM |

HIGH 置信度在 G1 和 G3 中给出了错误的确定性。当人审看到"✅ HIGH"时，会信任映射结果而不检查，但参数实际上需要调整。

**建议修复:**
1. 在映射器输出中增加 `strategy_purity` 字段：标记是否为纯策略
2. 复合策略或策略+修饰语的映射自动降级为 MEDIUM
3. 为每种策略定义"检查清单"，人审时对照检查

---

### P1-5: `axis_side` 缺失导致 spatial_check S01 无法运行

**问题描述:**
spatial_check 的 S01 检查（180度线一致性）需要每个 segment 的 `axis_side` 字段。但：
- `intent_strategies.json` 中的 10 个策略全部**没有定义** `axis_side`
- 映射器输出不包含 `axis_side`
- 自动生成的 YAML 缺少此字段 → spatial_check 无法验证跳轴

**影响:** 两阶段设计无法保证 180 度线合规，这是 P0 铁律违规。

**建议修复:**
1. 在 `intent_strategies.json` 中为对话类策略添加 `axis_side` 默认值
2. 在映射器中为单人/物体镜头添加 `axis_side: "中性"` 默认
3. 在 yaml_assembler 中根据角色对话方向推导 `axis_side`

---

## P2 — 优化建议

---

### P2-1: 策略标签解析健壮性

`visual_strategy` 的正则提取 `[([^\]]+)]` 要求严格的中括号格式。如果策略标签写作 `【空间建立】` 或 `空间建立`，映射器会回退到 `narrative_function` 推导（MEDIUM）。建议：
- 支持多种括号格式 `[...]` `【...】`
- 支持无括号的"开头匹配"
- 添加标签提取失败时的日志警告

---

### P2-2: 情绪微调从字符串到参数化

映射器的 `emotion_hint` 目前是单行字符串（如 `"焦距可能偏长·景别可能偏紧"`），不是可计算的结构化调整。建议改为：

```json
"emotion_tuning": {
  "focal_length_delta": "+35mm",
  "shot_type_tighten": 1,
  "movement_speed_adjust": -0.5,
  "lighting_contrast_adjust": "+2 stops"
}
```

这样 yaml_assembler 可以直接在默认参数上应用数值调整，而不需要 LLM 介入。

---

### P2-3: 多镜 LLM 微调的并行化

当 N 个 LOW 镜头的 LLM 微调相互独立时，应该并行执行。目前设计是隐式串行。建议设计并发管理器：
- 估算每个 LOW 镜头的 LLM token 消耗
- 限制最大并行度（如 3-5 镜同时）
- 按置信度顺序处理（先 MEDIUM 后 LOW）
- 超时/重试策略

以 EP13 为例：17 镜中有 4 镜需要 LLM（~23.5%），并行化可将 Stage 2 延迟从 4×LLM延迟 降至 1×LLM延迟。

---

### P2-4: `time_range` 推导

意图卡目前没有任何镜头时长信息。建议添加推导逻辑：
- 从 `rhythm_position` 映射：
  - `"曲线起点"` → 2-4 秒
  - `"上升"` → 3-5 秒
  - `"第一次转折"` → 3-6 秒
  - `"高潮"` → 4-8 秒
  - `"下降"` → 3-5 秒
  - `"曲线终点"` → 3-6 秒
- 从 `narrative_function` 微调：
  - `收尾` → 偏长（消化时间）
  - `揭示` → 适中
  - `反应` → 偏短

---

### P2-5: 意图卡格式版本化

`EP13_INTENT_CARDS.json` 使用 `intent_groups` 格式（组级聚合）。建议在新版本中改为或增加 `per_shot` 格式：

```json
"per_shot_intents": [
  {
    "shot_id": "镜#1",
    "strategy": "感官剥夺",
    "narrative_function": "建立·物锚定",
    "character_psychology": "— (无角色·纯物)",
    "audience_feeling": "好奇·冷感·被压缩在细节世界",
    "rhythm_position": "曲线起点·低·静",
    "emotion_tuning": {"focus": "极窄", "contrast": "高反差", "movement": "极慢"}
  },
  ...
]
```

这解决了 P1-1（组级字段丢失）的大部分问题，且每镜意图可直接输入映射器，无需 `flatten_groups`。

---

## 性能估算对比

### 各阶段 Token 和耗时

| 阶段 | 组件 | Token 消耗 | 耗时 | LLM 调用 | 说明 |
|:---|:---|---:|:---:|:---:|:---|
| **第一阶段** | 意图 Agent | ~3K-6K | 3-8 秒 | 1 次 | 简化输出（无参数），比当前 Agent 减少约 40% |
| **第二阶段** | 确定性映射器 | 0 tokens | <1 秒 | 0 | 纯正则+查表 |
| **第二阶段** | LLM 微调（LOW镜） | 5K-15K/镜 | 2-5 秒/镜 | N 次(串行) | EP13需4镜=~40K·~15秒(串行) |
| **第二阶段** | YAML 组装器 | 0 tokens | <1 秒 | 0 | 纯拼接 |
| **第二阶段** | 台本生成器 | 2K-5K | 1-3 秒 | 1 次 | 从 YAML+意图卡→台本 |
| **审查层** | Gate 0 | 0 tokens | <1 秒 | 0 | 纯正则 |
| **审查层** | spatial_check | 0 tokens | <1 秒 | 0 | 纯几何 |
| **审查层** | Scene Auditor | ~14K-25K | 5-15 秒 | 1 次 | 比当前减少约 30% |
| | **总计（典型场景）** | **~24K-50K** | **~15-35 秒** | **~3-7 次** | |

### 新旧管道对比

| 维度 | 当前管道 | 两阶段管道 | 差值 |
|:---|---:|---:|:---:|
| LLM 调用次数 | 2 次（Agent+Auditor） | 3-7 次（意图+微调×N+台本+审计） | +50%~+250% |
| LLM 总 Token | ~30K-50K | ~24K-50K | ~持平或略降 |
| 确定性处理 Token | 0 | 0 | 持平 |
| 端到端耗时 | ~15-25 秒 | ~15-35 秒 | +0~+10 秒 |
| 人审精确度 | 审参数（复杂·易漏） | 审意图（简单·准确） | 人审质量提升 |
| 参数修改成本 | 改→重跑 Agent（全量） | 改意图→自动重映射（零成本） | 大幅降低 |
| 新增基础设施 | 无 | LLM编排器+YAML组装器+台本生成器 | 新增 3 组件 |

### 并行化潜力

两阶段设计的最大优势在并行化未被利用：

```
当前隐式串行: 意图Agent → 映射器 → LLM#1 → LLM#2 → ... → YAML组装 → 台本生成
                              ↓串行↓
最优并行:     意图Agent → 映射器 ─┬─ LLM#1 ─┐
                                  ├─ LLM#2 ─┤
                                  ├─ LLM#3 ─┤── 合并 → YAML组装 → 台本生成
                                  └─ LLM#N ─┘
```

串行总耗时: `T_意图 + N × T_LLM + T_组装`
并行总耗时: `T_意图 + 1 × T_LLM + T_组装`

如果 EP13 的 4 个 LOW 镜头并行，Stage 2 LLM 时间从 ~15 秒压缩到 ~4 秒，节省 ~70%。

---

## 总结: 改进路线图

### 必须完成（P0）— 管道能跑

```
1. 新建 intent_llm_tuner.py    ← 缺失的核心编排器
2. 新建 yaml_assembler.py      ← 从dict到完整YAML的转换
3. 新建 script_generator.py    ← 从YAML到导演台本的转换
4. 修复策略提取: 支持复合策略  ← 修改 map_intent_to_params()
5. 明确管道顺序:               ← 修改 dispatcher 配置
   Stage1 → 人审 → Map → LLM调 → YAML组装 → 台本生成 → Gate0 → spatial → Auditor
```

### 应该修复（P1）— 跑得正确

```
6. 意图卡增加 per_shot 粒度    ← 修改 INTENT_CARDS 格式
7. 映射器读取 rhythm/audience ← 利用已产出的 ~60% 信息
8. LLM覆盖标记系统             ← 避免重映射丢失修改
9. 置信度模型加入"纯度"因子   ← 复合策略降级
10. 策略添加 axis_side 默认值  ← 保证 spatial_check 可运行
```

### 可以优化（P2）— 跑得更好

```
11. 情绪微调参数化             ← 从字符串到数值调整
12. 并行 LLM 微调              ← 并发管理器
13. time_range 推导逻辑        ← 从节奏位置映射时长
14. 标签解析健壮性提升         ← 支持多种括号格式
15. 意图格式版本化             ← 向下兼容的 v2 格式
```

### 核心结论

两阶段设计的方向是正确的 — **分离"为什么拍"和"怎么拍"降低了认知复杂度**。但当前实现跳过了一个关键的中间层：**从意图卡到可检查产出的"组装"步骤**。性能优势（人审更快、改意图代价更低）是真实的，但不能以"新增三个缺失组件 + 一个过度简化的参数模型"为代价实现。

**一句话**: 设计思路正确，但实现完成度约 40%。需要补全 LLM 编排器、YAML 组装器、台本生成器三个组件，并修复参数模型缺失字段，才能验证设计文档中承诺的质量改进。
