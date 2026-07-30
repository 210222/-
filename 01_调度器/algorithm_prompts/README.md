# MODE:P 算法设计提示词集

> **用途:** 将以下提示词逐一发送给 DeepSeek V4 Pro，获取可部署的算法改进方案
> **策略文档:** `07_档案/deepseek_v4pro_algorithm_strategy.md`

---

## 发送顺序（按优先级）

| 顺序 | 文件 | 节点 | thinking | temp | 预计Token | 预期产出 |
|:--:|------|------|:--------:|:----:|:------:|---------|
| 1 | `A6_gate0_scanner.md` | Gate 0 | OFF | 0.0 | 8K | 100行·直接部署·立竿见影 |
| 2 | `A1_shot_classifier_redesign.md` | 分类器 | ON | 0.1 | 16K | 完整Python类·误差链起点 |
| 3 | `A2_intent_mapper_redesign.md` | 映射器 | ON | 0.1 | 20K | 参数化函数·信息损失补偿 |
| 4 | `A5_intent_strategies_redesign.md` | 策略库 | ON | 0.1 | 16K | 新JSON定义·5新策略 |
| 5 | `A7_confidence_calibration.md` | 置信度 | ON | 0.1 | 10K | ConfidenceEngine类 |
| 6 | `A3_performance_matcher_upgrade.md` | 表演匹配 | ON | 0.1 | 12K | 多状态组合匹配器 |
| 7 | `A4_script_assembler_review.md` | 脚本组装 | OFF | 0.0 | 8K | 审查发现+修正 |
| 8 | `A8_strategy_coverage_expansion.md` | 覆盖模型 | ON | 0.1 | 10K | 5新策略定义 |

## 发送方式

### 方式 1: Python API

```python
# 见同级目录的 runner.py
python runner.py A1
```

### 方式 2: 直接粘贴

1. 打开 DeepSeek V4 Pro 对话
2. 复制对应 `.md` 文件全文
3. 粘贴发送

## 使用后验证

每个算法设计完成后，对照 `deepseek_v4pro_algorithm_strategy.md` §6 的 6 个指标:

```
✅ signal_ratio > 70%（伪代码+实现/总输出）
✅ candidate_diversity > 0.5（≥3候选·原理不同）
✅ implementation_ready = True（可保存为.py·无语法错误）
✅ failure_coverage = 1.0（覆盖所有已知失败模式）
✅ novel_insight ≥ 1（至少1个日志中未记录的发现）
✅ token_efficiency > 50%
```

## 迭代

如果输出未达标 → 按 `deepseek_v4pro_algorithm_strategy.md` §6.2 迭代。
