# A2: intent_mapper 重新设计 → 发送给 DeepSeek V4 Pro

> **API参数:** `enable_thinking=True, temperature=0.1, max_tokens=20000`
> **预期输出:** 完整 Python 类 + 参数化函数 + 多策略合并逻辑

---

你是一个算法工程师+电影摄影指导。任务：重新设计 MODE:P 管道的 intent_mapper.py，补偿 41% 的语义信息损失。

## §1 问题定义

**输入:** 意图卡
```json
{
  "shot_id": "4",
  "visual_strategy": "[感官剥夺]",
  "narrative_function": "揭示",
  "character_psychology": "Miguel紧张·专注·怀疑",
  "emotion_note": "镜#4([感官剥夺]·极窄·与Miguel共享视角局限)",
  "scene_context": "鉴证科实验室·冷白光·全封闭无窗"
}
```

**输出:** 预填摄影参数
```json
{
  "shot_type": "大特写",
  "focal_length": "100mm",
  "dof": "f/1.4",
  "movement": "固定",
  "angle": "水平",
  "lighting": "侧光·单光源",
  "confidence": "HIGH",
  "llm_required": false,
  "source": "意图策略: [感官剥夺]",
  "param_certainty": 0.85
}
```

**当前信息损失率:** 41%（10 策略平均）
**目标:** < 15%

**硬约束:**
- 映射阶段零 LLM · O(1) 查表 · < 1ms/镜
- 策略新增 = 改 intent_strategies.json · 不改映射器代码
- 支持多策略组合: `[A]+[B]` → 合并参数 · 不是只取第一个

---

## §2 当前算法基线

**代码:** `intent_mapper.py` map_intent_to_params() 函数（第 17-145 行）
**策略库:** `intent_strategies.json`（21 策略 v2.0）

### 四个信息损失来源（按贡献排序）

**1. 时序维度缺失（30%）:**
"过渡""揭示""转折"有时间动态 · default_params 只有静态快照
例: "非人化→常化" — "过渡"是核心行为·但参数无 easing/时长/起止状态

**2. 空间关系未参数化（25%）:**
"交界位置""机位几何""POV 连接"未被表达
例: "冷暖色温交界" — "交界位置"是构图核心·但零坐标

**3. 情感意图丢失（25%）:**
"共享视角局限""替代表演""注意力转移"的视觉表达缺失
例: "感官剥夺" — "与角色共享视角局限"→无参数

**4. 选择规则缺失（20%）:**
二选一场景无决策规则
例: "屏幕 vs 实物""出场 vs 退场""外反拍 vs 内反拍"

### 当前反馈回写逻辑的缺陷

`intent_mapper.py` 第 162-193 行的 FEEDBACK_LOG 回写：
- 仅 4 条成功设计 · 匹配逻辑过于宽松（`fb_narrative in intent_narrative`）
- 无衰减模型 · 无聚类验证 · 无自动固化阈值

---

## §3 设计空间

**新增参数化维度:**
- `f(obj_size_cm, distance_m) → focal_length_mm` — 对象尺寸到焦距的连续函数
- `f(pov_level) → dof` — POV 等级到景深映射
- `f(emotion_intensity) → movement_speed` — 情绪强度到运镜速度
- 情感影响向量: 孤独→[+0.3 景别紧缩, +0.2 焦距拉长, +0.15 对比度]
- 场景类型偏移: 实验室→[+500K 色温, +0.3 景深收缩]

**多策略合并规则:**
- 当前 `intent_mapper.py` 第 28 行只取第一个策略标签
- 需要: `[A]+[B]` → 景别取 A · 光影取 B · 运镜取 A · 冲突时取优先级更高的

**反馈学习升级:**
- FSRS 衰减模型（λ=0.75/场景）
- CV < 15% → 自动固化到 default_params
- ≥ 3 次 LLM 成功设计 · 编辑距离 < 20% → 候选新策略

**硬约束:** 零 LLM · O(1) · 改 JSON 不改代码 · 支持多策略组合

---

## §4 强制推理步骤

Step 1 — 信息损失根因归类: 将 4 个损失来源映射到具体策略·计算可补偿比例
Step 2 — 参数化函数设计: 为每个损失维度设计补偿函数·定义输入/输出/参数范围
Step 3 — ≥ 3 候选: 不同原理的映射器架构
Step 4 — 对比矩阵
Step 5 — 推荐方案的完整 Python 实现（含参数化函数 + 多策略合并 + 反馈回写）

## §5 输出格式: JSON（同上格式）
