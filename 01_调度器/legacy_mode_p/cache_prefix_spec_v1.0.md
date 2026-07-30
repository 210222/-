# Cache Prefix v1.0 — API级缓存前缀规范

> **定位:** 定义每个Agent类型的"缓存前缀块"——在API调用中放在prompt最前面的不变内容·利用DeepSeek prompt caching实现高命中率。
> **设计依据:** EP14_TOKEN_FORENSICS.md · deepseek_v4pro_algorithm_strategy.md · P0(重排序)+P1(预编译)方案
> **核心原理:** LLM API的prompt caching是前缀匹配——前缀一致→命中·后面内容变化不影响。将所有不变内容放在前缀·场景变化数据放在末尾。
> **版本:** v1.0 · 建立日期: 2026-07-10

---

## §0 问题的本质

### 0.1 当前缓存失败的原因

```
当前Agent调用流程:
  Step 1: 调度器发送Agent指令文件 (system prompt或首条消息)
  Step 2: Agent用Read工具加载 agent_quick_ref
  Step 3: Agent用Read工具加载 CONTEXT_PACKAGE
  Step 4: Agent用Read工具加载 KB_SUMMARY
  Step 5: Agent用Read工具加载 上游输出
  Step 6: Agent开始推理 + 输出

问题: 步骤2-5的Read调用在对话中间·每次Read触发一次LLM推理循环。
      Read返回的内容不在prompt前缀中·无法被缓存。
      只有步骤1的指令文件在prompt最前面——但指令文件本身只有角色定义·不包含KB规则。
```

### 0.2 缓存前缀方案

```
优化后的Agent调用流程:
  ┌─────────────────────────────────────────────┐
  │ SYSTEM PROMPT (缓存前缀·每次完全一致)          │
  │   §0 角色定义                                │
  │   §1 KB规则全文 (该Agent需要的子集)            │
  │   §2 渲染约束 (P-FAL·硬上限)                   │
  │   §3 输出格式 (YAML/JSON schema)              │
  │   §4 指令模板 (推理步骤+检查清单)              │
  │   §5 禁止事项                                │
  │   💰 此段约8-15K tokens·缓存命中后零计算       │
  ├─────────────────────────────────────────────┤
  │ USER MESSAGE (场景数据·每次不同)               │
  │   场景描述 + 角色配置 + 上游输出 + 参考图索引    │
  │   此段约3-8K tokens·每次都要计算               │
  │   💰 但只有这段需要计算·前缀已命中缓存           │
  └─────────────────────────────────────────────┘

缓存效果:
  DeepSeek V4 Pro:  前缀15K命中 + 数据5K计算 = 20K输入·75%缓存率
  DeepSeek V4 Flash: 前缀12K命中 + 数据5K计算 = 17K输入·71%缓存率
  (Flash前缀稍短·因不包含thinking token锚点·但远好于当前33%)
```

### 0.3 与现有文件的关系

```
cache_prefix (本规范)     → API级·注入到prompt最前面·用于缓存命中
agent_quick_ref           → 文件级·Agent需要时Read·向后兼容
CONTEXT_PACKAGE           → 文件级·场景数据包·User Message中引用
KB_SUMMARY                → 文件级·按需深读·不再作为主要KB来源

迁移路径:
  Phase 1: cache_prefix 替代 agent_quick_ref 的首轮Read
           → agent_quick_ref 保留为深读参考(当缓存前缀不够用时)
  Phase 2: cache_prefix 完全替代 agent_quick_ref
           → agent_quick_ref 降级为离线参考文档
```

---

## §1 缓存前缀结构规范

### 1.1 通用结构

```markdown
# [Agent名称] v[版本] — 缓存前缀

> **缓存ID:** `PREFIX_[AGENT_TYPE]_v[版本]`
> **目标大小:** [8-15]K tokens
> **适用管道:** MODE:P
> **消费方式:** 调度器在启动Agent时注入到system prompt

---

## §0 角色与边界

[角色定义·核心职责·与其他Agent的边界·1-2段]
[上下文隔离规则·信息可见性边界]

---

## §1 知识库规则

[该Agent需要的KB规则全文·按优先级排序]
[P0规则始终包含·P1/P2规则按Agent域筛选]
[格式: 规则ID + 一句话 + 详述(2-5句)]

### 1.1 通用铁律 (所有Agent共享·P0·~500 tokens)
### 1.2 [域1] 规则 ([Agent特有]·P0-P2·~2000 tokens)
### 1.3 [域2] 规则 ([Agent特有]·P0-P2·~1500 tokens)
...

---

## §2 渲染约束

[P-FAL-01~10 完整规避方案·每条2-3行]
[硬上限速查表·该Agent相关的约束项]
[模型选择速查·仅该Agent需要的镜头类型]

---

## §3 输出格式

[该Agent的输出Schema·JSON/YAML]
[字段定义·类型·必填/可选]
[示例输出块]

---

## §4 推理步骤

[强制推理链·Step 1→N]
[每步的输入·输出·检查点]

---

## §5 禁止事项

[Agent特有的禁止项·5-10条]
[每条: 禁止什么 + 为什么 + 替代方案]
```

### 1.2 大小控制

| Agent类型 | 目标前缀大小 | §1 KB占比 | §2约束占比 | §3格式占比 | §0+§4+§5占比 |
|-----------|:----------:|:--------:|:---------:|:--------:|:----------:|
| Scene Designer | 12-15K | 60% | 10% | 15% | 15% |
| Scene Auditor | 10-12K | 40% | 15% | 25% | 20% |
| Shot Architect | 8-10K | 55% | 10% | 15% | 20% |
| Movement Designer | 6-8K | 50% | 15% | 15% | 20% |
| Composition Designer | 8-10K | 55% | 10% | 15% | 20% |
| Prompt Composer | 10-12K | 30% | 25% | 25% | 20% |

### 1.3 版本管理

```
前缀版本号格式: PREFIX_[AGENT]_v[major].[minor]
  major: KB规则有新增/删除时递增
  minor: 措辞优化·格式调整时递增

前缀文件命名: cache_prefix_[agent_type]_v[major].[minor].md
存储位置: [工作目录]/01_调度器/cache_prefixes/

调度器在每次MODE:P启动时:
  1. 检查cache_prefixes/目录
  2. 按complexity_router的Agent选择·加载对应前缀
  3. 注入到Agent的system prompt
  4. 场景数据放入user message
```

---

## §2 各Agent类型的KB规则映射

### 2.1 Scene Designer (合并式·S/M/C-Level)

```
KB域 (从 agent_quick_ref §C 提取完整文本):
  ✅ §C.0 通用铁律 (GEN-01~05,09,10) — P0·始终包含
  ✅ §C.1 对话·双人·三角形原理 (D-TRI-01~09,13,14 + D-DUO-01,02,05,06) — 15条
  ✅ §C.2 对话·双人·调度模式 (D-DIA-01~03,05,07,08,10~13) — 11条
  ✅ §C.3 三人对话 (D-TRI-3-01~04,07~10) — 8条
  ✅ §C.4 动作场景 (A-FGT-01~04, A-CHS-01,02, A-SUS-01,02,05, A-ACT-01) — 10条
  ✅ §C.5 剪辑与节奏 (E-MUR-01~03, E-MTC-01~03, E-RHY-01,02) — 8条
  ✅ §C.6 构图与美学 (C-FI-01~03, C-KTZ-01~03, C-DEP-01,02) — 8条
  ✅ §C.7 运镜与运动 (M-MOT-01~06, M-MOV-01,02) — 8条
  ✅ §C.8 光影与色彩 (L-3PT-01~03, L-SCN-01, L-CT-01, COL-PRI-01~03) — 8条
  ✅ §C.9 视觉结构 (VS-COM-01, VS-CA-01,02, VS-INT-01, VS-SPA-01, VS-MOV-01) — 6条
  ✅ §F Performance KB (15心理状态速查表) — 全部

不含 (Scene Designer不需要的域):
  ❌ §D 输出格式 (在cache_prefix §3中独立定义·Scene Designer专用)
  ❌ §E 审计速查 (审计Agent专用)
  ❌ Gate 0正则 (调度器自执行·Agent不可见)

总规则数: ~90条 × 平均3行/条 = ~270行 ≈ ~3,500 tokens (规则文本)
          + 详述展开 → 约7,000 tokens
```

### 2.2 Scene Auditor (合并式·审计专用)

```
KB域 (从 agent_quick_ref §C + §E 提取):
  ✅ §C.0 通用铁律 — P0
  ✅ §C.5 剪辑与节奏 (全部·8条) — TIME_SKELETON验证需要
  ✅ §C.7 运镜与运动 (M-MOT-01~06) — 运镜合规审计需要
  ✅ §E.1 Gate 0规则索引 (R01-R15·完整regex) — 审计基准
  ✅ §E.2 违规代码速查 (全部violation codes)
  ✅ §E.3 裁决矩阵 (🛑/⚠️/💡判定标准)

不含:
  ❌ §C.1-4 对话/动作场景规则 (设计Agent域·审计不判定设计质量)
  ❌ §C.6 构图美学规则 (审计不替代Visual Reviewer)
  ❌ §C.8-9 光影/视觉结构 (同上)
  ❌ §F Performance KB (Scene Auditor不判定表演质量)

总规则数: ~40条 ≈ ~2,000 tokens + 详述 → ~4,000 tokens
```

### 2.3 Shot Architect (C-Level·机位设计)

```
KB域:
  ✅ §C.0 通用铁律
  ✅ §C.1 对话·双人·三角形原理 (全部·15条) — 核心域
  ✅ §C.2 对话·双人·调度模式 (全部·11条) — 核心域
  ✅ §C.3 三人对话 (全部·8条) — 核心域
  ✅ §C.4 动作场景·通用 (A-ACT-01) — 空间建立
  ✅ §C.6 构图·景别单位 (C-KTZ-01) — 景别选择

不含:
  ❌ §C.5 剪辑 (下游Agent域)
  ❌ §C.7 运镜 (Movement Designer域)
  ❌ §C.8-9 光影/视觉结构 (Composition Designer域)
```

### 2.4 Movement Designer (C-Level·运镜设计)

```
KB域:
  ✅ §C.0 通用铁律
  ✅ §C.7 运镜与运动 (全部·8条 + M-MOV-01~16完整)
  ✅ §C.1 对话·调度模式中的运镜规则 (D-DIA-01推近·D-DIA-07绕圈·D-DIA-11跨越界线)
  ✅ §C.4 动作场景中的运动规则 (A-FGT-03紧跟演员·A-CHS-01,02追逐)

不含:
  ❌ §C.1-3 机位三角形 (Shot Architect域)
  ❌ §C.6,8 构图/光影 (Composition Designer域)
```

### 2.5 Composition Designer (C-Level·构图+光影)

```
KB域:
  ✅ §C.0 通用铁律
  ✅ §C.6 构图与美学 (全部·8条 + C-FI-01~25完整)
  ✅ §C.8 光影与色彩 (全部·8条 + L-3PT-01~15完整)
  ✅ §C.9 视觉结构 (全部·6条)

不含:
  ❌ §C.1-4 对话/动作 (Shot Architect + Movement Designer域)
  ❌ §C.5 剪辑 (下游Agent域)
```

### 2.6 Prompt Composer (台本撰写)

```
KB域:
  ✅ §C.0 通用铁律
  ✅ §D.2 台本格式模板 (完整)
  ✅ §D.3 禁止清单模板 (完整)
  ✅ §B.1 硬上限速查 (全部·14项·P-FAL-01~10)
  ✅ §B.4 禁止词汇清单 (完整·7类)
  ✅ §B.3 模型选择速查 (完整·按镜头类型)
  ✅ §B.2 P-FAL速查卡 (10条·触发+规避)

不含:
  ❌ §C.1-9 KB规则全文 (设计Agent域·台本撰写不判定设计质量)
```

---

## §3 缓存效果预估

### 3.1 单Agent缓存率

```
假设: 前缀大小 P, 场景数据大小 D, 均用同一Agent类型N次

缓存命中率 = (N-1)/N × P/(P+D)
           (首次调用无缓存·后续调用前缀全命中)

Scene Designer (P=14K, D=6K, N=3场景):
  命中率 = 2/3 × 14/20 = 0.67 × 0.70 = 47%
  但连续同场景重跑: N=3 × 同一场景 → P+D完全一致 → 命中率接近100%

Scene Designer (P=14K, D=6K, N=5次同Agent调用含重试):
  命中率 = 4/5 × 14/20 = 0.80 × 0.70 = 56%

Scene Auditor (P=11K, D=8K, N=3场景):
  命中率 = 2/3 × 11/19 = 0.67 × 0.58 = 39%
  (审计的D较大·因为需要读设计报告+台本+故事板)

对于有thinking=ON的V4 Pro:
  前缀中增加reasoning tokens (~5-8K) → P变大 → P/(P+D)提升
  Scene Designer: P=14+6=20K, 命中率 = 2/3 × 20/26 = 51%
  (thinking tokens自身也是前缀的一部分·进一步提升了缓存率)
```

### 3.2 与当前对比

```
当前 (无缓存前缀):
  Scene Designer V4 Flash: 缓存率 ~33% (仅agent_quick_ref的Read前前缀匹配)
  Scene Designer V4 Pro:   缓存率 ~90% (多轮对话历史+thinking形成长前缀)

P0+P1后:
  Scene Designer V4 Flash: 缓存率 ~55-70% (前缀12-15K + 场景数据变化)
  Scene Designer V4 Pro:   缓存率 ~92-95% (前缀更长·多轮对话历史仍起作用)
  
  → Flash提升20-40个百分点·Pro保持高位并略提升
```

### 3.3 Token节省估算

```
C-Level管道 (7 Agent × 3场景):
  当前总token: ~875K/场景
  每个Agent的公共上下文: 50K × 7 = 350K
  缓存前缀覆盖: 10K × 7 = 70K 首次·后续 0 (缓存命中)
  
  假设50%的Agent调用是同一类型重复:
    旧: 350K × 3场景 = 1,050K
    新: 70K × 3(首次) + 0 × 其他 = 210K
    节省: 840K tokens → 80%

S-Level管道 (2 Agent × 1场景):
  缓存前缀首次加载: 25K
  vs 旧架构各Agent独立加载: 100K
  节省: 75K tokens → 75%
```

---

## §4 实施清单

```
Phase 1: 创建缓存前缀文件
  ☐ cache_prefix_scene_designer_v1.0.md  (~14K tokens)
  ☐ cache_prefix_scene_auditor_v1.0.md   (~11K tokens)
  ☐ cache_prefix_shot_architect_v1.0.md  (~9K tokens)
  ☐ cache_prefix_movement_designer_v1.0.md (~7K tokens)
  ☐ cache_prefix_composition_designer_v1.0.md (~9K tokens)
  ☐ cache_prefix_prompt_composer_v1.0.md (~11K tokens)

Phase 2: 构建脚本
  ☐ cache_prefix_builder.py (自动从agent_quick_ref + KB提取规则·组装前缀)

Phase 3: 调度器集成
  ☐ 更新dispatcher_v5.0.md: 新增 §-8 缓存前缀注入协议
  ☐ 更新Agent指令文件: 标记当前文件为"深读参考"·缓存前缀为"主要prompt"

Phase 4: 验证
  ☐ 单Agent缓存率测试 (同场景重跑3次·统计缓存命中)
  ☐ 跨场景缓存率测试 (不同场景·验证前缀匹配)
  ☐ Token节省量实测
```

---

> **v1.0 · 2026-07-10 · 初始发布**
> **设计原理:** P0(Prompt重排序) + P1(预编译上下文块) → API级缓存前缀
> **核心贡献:** 将agent_quick_ref/CONTEXT_PACKAGE/KB_SUMMARY的文件级优化升级为API级缓存优化
> **关键指标:** V4 Flash缓存命中率 33%→55-70% · V4 Pro 90%→92-95%
> **下一步:** 创建各Agent类型的缓存前缀文件 → 构建自动生成脚本 → 调度器集成
