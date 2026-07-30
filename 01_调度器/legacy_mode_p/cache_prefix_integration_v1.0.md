# Cache Prefix Integration v1.0 — 调度器集成规范

> **定位:** 定义调度器如何将缓存前缀注入Agent的system prompt·实现API级缓存命中
> **依赖:** cache_prefix_spec_v1.0.md · cache_prefix_builder.py · cache_prefixes/*.md
> **版本:** v1.0 · 建立日期: 2026-07-10

---

## §1 集成原理

### 1.1 当前Agent调用方式

```
调度器 → Agent工具调用:
  prompt = agent指令文件内容 + "请Read agent_quick_ref + CONTEXT_PACKAGE + KB_SUMMARY"

问题:
  - agent_quick_ref通过Read工具加载 → 在对话中间 → 不在prompt前缀
  - CONTEXT_PACKAGE通过Read工具加载 → 同上
  - 缓存只能匹配到第一个Read调用之前 → 仅指令文件开头匹配
  - V4 Flash缓存命中率: ~33%
```

### 1.2 缓存前缀注入方式

```
调度器 → Agent工具调用:
  system_prompt = 缓存前缀文件内容 (2-4K tokens·完全不变)
  user_message  = 场景数据 + "按需要可深读agent_quick_ref获取完整规则文本"

效果:
  - 缓存前缀在prompt最前面 → API级前缀匹配
  - 每次同类型Agent调用 → 前缀完全一致 → 缓存命中
  - 场景数据在user_message中 → 变化不影响前缀匹配
  - V4 Flash缓存命中率: ~33% → ~55-70%
```

---

## §2 调度器修改

### 2.1 新增 §-8: 缓存前缀注入协议

在 dispatcher_v5.0.md 的 §-7 之后新增以下章节：

```markdown
# 🆕 §-8 缓存前缀注入协议 (v1.0·API级缓存优化)

## §-8.1 协议定义

```
每个MODE:P Agent启动时·调度器执行以下注入:

  1. 按Agent类型选择缓存前缀文件:
     Agent类型          → 前缀文件
     ────────────────────────────────────────
     Scene Designer     → cache_prefixes/cache_prefix_scene_designer_v1.0.md
     Scene Auditor      → cache_prefixes/cache_prefix_scene_auditor_v1.0.md
     Shot Architect     → cache_prefixes/cache_prefix_shot_architect_v1.0.md
     Movement Designer  → cache_prefixes/cache_prefix_movement_designer_v1.0.md
     Composition Designer → cache_prefixes/cache_prefix_composition_designer_v1.0.md
     Prompt Composer    → cache_prefixes/cache_prefix_prompt_composer_v1.0.md

  2. 将前缀文件内容注入Agent的system prompt (第一条消息)

  3. 场景数据放入user message:
     - 场景描述 + 角色配置 + 空间地图摘要
     - 上游Agent输出文件路径 (Agent用Read工具按需加载)
     - CONTEXT_PACKAGE文件路径 (需要场景数据时Read)
     - KB_SUMMARY文件路径 (需要完整规则时Read)

  4. Agent在新上下文中启动·前缀已命中缓存
```

## §-8.2 注入格式

```
Agent调用时的prompt结构:

┌─ SYSTEM ────────────────────────────────────────────┐
│ [缓存前缀文件全文]                                     │
│   §0 角色与边界                                       │
│   §1 知识库规则 (1行摘要·约90条)                       │
│   §2 渲染约束 (P-FAL-01~10·硬上限·禁止词汇·模型选择)    │
│   §3 输出格式                                         │
│   §4 推理步骤                                         │
│   §5 禁止事项                                         │
│                                                       │
│ 💰 此段2-4K tokens·每次完全一致·缓存命中后零计算        │
├──────────────────────────────────────────────────────┤
│ USER                                                   │
│ [场景特定数据]                                          │
│   剧本段落 + 角色信息 + 空间摘要 + 上游输出文件路径      │
│                                                       │
│ 💰 此段1-5K tokens·每次不同·需要计算                    │
└──────────────────────────────────────────────────────┘
```

## §-8.3 回退机制

```
当缓存前缀文件不存在或损坏时:
  1. 调度器检测到前缀文件缺失 → ⚠️ 警告 "CACHE_PREFIX_MISSING"
  2. 回退到当前模式: Agent用Read工具加载agent_quick_ref
  3. 不影响管道正确性·仅缓存优化失效
  4. 下次管道启动时自动重试加载前缀文件

前缀版本不匹配时:
  1. 调度器比较前缀版本 vs agent_quick_ref版本
  2. 版本不匹配 → ⚠️ 警告 "CACHE_PREFIX_STALE"
  3. 使用旧前缀 (缓存仍部分有效)
  4. 建议运行: python cache_prefix_builder.py 重建前缀
```

## §-8.4 新Agent类型的前缀注册

```
新增Agent类型时:
  1. 在 cache_prefix_builder.py 的 AGENT_TYPES 字典中新增条目
  2. 定义: kb_domains / pfal_rules / canvas_sections / output_format
  3. 运行: python cache_prefix_builder.py --agent [new_type]
  4. 在 dispatcher 的 §-8.1 映射表中新增条目
```

## §-8.5 验证清单

```
每次MODE:P管道启动时验证:
  □ 所有需要的缓存前缀文件存在
  □ 前缀版本号与 agent_quick_ref 版本一致
  □ 前缀文件大小在预期范围内 (1.5K-5K tokens)
  □ 回退机制可用 (agent_quick_ref 路径有效)
```
```

### 2.2 修改Agent指令文件

每个Agent的指令文件 (02_Agent/*.md) 需要新增以下标注：

```markdown
## 🆕 缓存前缀声明

> **缓存前缀:** 调度器已将 `cache_prefix_[agent_type]_v1.0.md` 注入本Agent的system prompt。
> **前缀包含:** 角色定义·KB规则1行摘要·渲染约束·输出格式·推理步骤·禁止事项。
> **已覆盖:** agent_quick_ref §A-§F 的所有规则ID和1行摘要。
> **仍需Read:** CONTEXT_PACKAGE_[剧本名].md (场景数据)·上游Agent输出 (设计报告·台本)。
> **按需深读:** agent_quick_ref_v1.0.md (需要完整规则文本时)·03_导演知识库_v5.0.md (指定行号)。
> **不再Read:** agent_quick_ref_v1.0.md (除非按需深读)·P-CONSTITUTION.md·P-STATE.md·canvas_runtime.md·kb_index_v2.0.md。
```

### 2.3 更新Read清单

每个Agent指令文件的"输入要求"章节，将：

```markdown
🆕 必须加载的公共文件 (3个·调度器已预编译):
  ✅ agent_quick_ref_v1.0.md (~15K tokens)
  ✅ CONTEXT_PACKAGE_[剧本名].md (~8K tokens)
  ✅ KB_SUMMARY_[剧本名].md (~8-10K tokens)
```

改为：

```markdown
🆕 缓存前缀已注入 (调度器§-8·无需Agent主动Read):
  ✅ 缓存前缀已包含: 角色定义·KB规则摘要·渲染约束·输出格式·推理步骤
  → Agent启动时system prompt已包含全部不变内容

🆕 需要Read的文件 (仅场景变化数据):
  ✅ CONTEXT_PACKAGE_[剧本名].md (~5K tokens·场景数据·参考图索引)
  ✅ 上游Agent输出 (设计报告·台本·故事板·按需Read)
  
🆕 按需深读 (仅当缓存前缀中的1行摘要不够时):
  → agent_quick_ref_v1.0.md (需要查看完整KB规则速查时)
  → 03_导演知识库_v5.0.md (指定行号·需要完整规则条文时)

🆕 不再Read:
  ❌ agent_quick_ref_v1.0.md (规则摘要已在前缀中·除非按需深读)
  ❌ P-CONSTITUTION.md (已在缓存前缀 §2)
  ❌ P-STATE.md (P-FAL规则已在缓存前缀 §2.2)
  ❌ canvas_runtime.md (渲染约束已在缓存前缀 §2.1/2.3/2.4)
  ❌ kb_index_v2.0.md (路由结果已在缓存前缀 §1)
  ❌ KB_SUMMARY_[剧本名].md (规则摘要已在前缀中)
```

---

## §3 缓存效果预估

### 3.1 前缀大小实测

| Agent类型 | 前缀chars | 前缀tokens(估) | KB规则条数 | P-FAL | 禁止词汇 |
|-----------|---------:|:------------:|:--------:|:-----:|:------:|
| Scene Designer | 25,510 | ~7,300 | ~90 | ✅10条 | ✅ |
| Scene Auditor | 16,206 | ~4,600 | ~40 | ✅10条 | ✅ |
| Shot Architect | 16,047 | ~4,600 | ~45 | ✅精简 | ✅ |
| Movement Designer | 13,799 | ~3,900 | ~35 | ✅精简 | ✅ |
| Composition Designer | 14,570 | ~4,200 | ~35 | ✅精简 | ✅ |
| Prompt Composer | 12,675 | ~3,600 | ~10 | ✅10条 | ✅ |

> 注: tokens估算使用中英混合3.5 chars/token·实际API tokenizer可能略有差异

### 3.2 缓存命中率预估

```
场景: 3个场景·每个场景跑Scene Designer + Scene Auditor

当前 (无缓存前缀):
  Scene Designer ×3: 前缀=指令文件开头(~500 tokens)·命中率~30%
  Scene Auditor ×3:  前缀=指令文件开头(~500 tokens)·命中率~30%
  总计: ~6次调用·缓存命中token≈3×500×30% + 3×500×30% = 900 tokens

P0+P1后:
  Scene Designer ×3: 前缀=7.3K tokens·首次0%·后续2次100% → 7.3K×2=14.6K命中
  Scene Auditor ×3:  前缀=4.6K tokens·首次0%·后续2次100% → 4.6K×2=9.2K命中
  总计: ~23.8K tokens 缓存命中

  提升: 23.8K / 0.9K = 26× 缓存命中量
```

### 3.3 DeepSeek V4 Flash 专项提升

```
当前Flash缓存率: ~33% (仅指令文件开头匹配)
P0+P1后Flash缓存率: 
  首次调用: 0% (前缀首次加载)
  第2次同类型: 前缀完全匹配 → 7.3K tokens缓存命中
  缓存率 = 7.3K / (7.3K前缀 + 5K场景数据) = 59%
  第3+次同类型: 59-65%

Flash从33% → 55-65%: 提升22-32个百分点
V4 Pro保持90%+: thinking tokens继续提供额外锚点
```

### 3.4 Token成本节省

```
C-Level管道 (7 Agent × 3场景 = 21次调用):
  旧: 21 × 50K(公共上下文Read) = 1,050K tokens 公共上下文加载
  新: 7种Agent × 首次前缀加载(~4K avg) = 28K tokens
      后续14次调用: 前缀缓存命中 → 0 token计算
      场景数据: 21 × 5K = 105K (不可避免)
  总计公共上下文: 28K + 105K = 133K
  节省: 1,050K - 133K = 917K tokens → 87%减少

S-Level管道 (2 Agent × 1场景 = 2次调用):
  旧: 2 × 50K = 100K
  新: 2 × 4K(首次前缀) + 2 × 3K(场景数据) = 14K
  节省: 86K → 86%减少
```

---

## §4 实施步骤

```
Phase 1: 前缀文件就绪 ✅
  ☑ cache_prefix_builder.py (构建脚本)
  ☑ cache_prefix_scene_designer_v1.0.md
  ☑ cache_prefix_scene_auditor_v1.0.md
  ☑ cache_prefix_shot_architect_v1.0.md
  ☑ cache_prefix_movement_designer_v1.0.md
  ☑ cache_prefix_composition_designer_v1.0.md
  ☑ cache_prefix_prompt_composer_v1.0.md

Phase 2: 调度器集成 (需要手动执行)
  ☐ 在dispatcher_v5.0.md中新增 §-8 缓存前缀注入协议
  ☐ 更新dispatcher中每个Agent调用的system prompt注入逻辑
  ☐ 添加前缀文件缺失时的回退逻辑

Phase 3: Agent指令更新 (需要手动执行)
  ☐ 更新 scene_designer_v1.0.md: 新增缓存前缀声明·更新Read清单
  ☐ 更新 scene_auditor_v1.0.md: 同上
  ☐ 更新 shot_architect_v2.0.md: 同上
  ☐ 更新 movement_designer_v2.0.md: 同上
  ☐ 更新 composition_designer_v2.0.md: 同上
  ☐ 更新 prompt_composer_v2.0.md: 同上

Phase 4: 验证
  ☐ 单Agent同场景重跑3次 → 统计缓存命中率
  ☐ 跨场景不同Agent调用 → 验证前缀不互相污染
  ☐ Token消耗实测 → 对比优化前后
```

---

> **v1.0 · 2026-07-10 · 初始发布**
> **核心变更:** 调度器在Agent启动时将缓存前缀注入system prompt·替代Agent各自Read公共文件
> **关键效果:** Flash缓存命中率 33%→55-65% · Pro保持90%+ · 公共上下文token节省87%
> **回退安全:** 前缀文件缺失时自动回退到agent_quick_ref Read模式·不影响管道正确性
