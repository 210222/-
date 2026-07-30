# A7: Confidence Calibration 动态分级 → 发送给 DeepSeek V4 Pro

> **API参数:** `enable_thinking=True, temperature=0.1, max_tokens=10000`
> **预期输出:** ConfidenceEngine Python 类 · CV 计算 · 升级/降级条件

---

你是一个算法工程师。任务：将 MODE:P 的置信度分级从硬编码改为基于运行数据的动态校准。

## §1 问题定义

**输入:** 策略运行历史
```python
history = [
    {"strategy": "感官剥夺", "scene": "EP13", "params_used": {...},
     "params_default": {...}, "llm_overridden": False, "edit_distance": 0.0},
    {"strategy": "感官剥夺", "scene": "EP15", "params_used": {...},
     "params_default": {...}, "llm_overridden": False, "edit_distance": 0.05},
    # ... 更多记录
]
```

**输出:**
```python
{
  "strategy": "感官剥夺",
  "confidence": "MEDIUM",  # HIGH | MEDIUM | LOW
  "certainty_score": 0.55,
  "can_upgrade": True,     # 如果满足升级条件
  "upgrade_blockers": ["跨场景数不足(2/3)", "参数CV=18%>15%"],
  "recommendation": "再运行1个场景·若参数CV降至15%以下·可升级为HIGH"
}
```

**当前问题:**
- 置信度硬编码在 `intent_strategies.json` 的 `mapping_rules` 中
- 6 个 HIGH → 实测仅 2 个真正稳定
- 升级/降级条件写在文档里·未实现为代码

**升级/降级条件（来自 ALGORITHM_ANALYSIS_TWOSTAGE.md §4.2-4.3）:**
- MEDIUM → HIGH: 跨 3+ 场景 CV < 15% + 零 LLM 覆盖 + 无二选一参数
- LOW → MEDIUM: 3+ 次 LLM 输出编辑距离 < 20% + 可提取 tuning 规则 + 审查通过率 > 80%
- LOW 衰减: λ = 0.75/场景 · 4-5 场景后 LOW < 10%

## §2 设计空间

**动态校准引擎核心逻辑:**
```python
class ConfidenceEngine:
    def __init__(self, history_path="confidence_history.json"):
        self.history = self._load(history_path)
    
    def calibrate(self, strategy_key: str) -> ConfidenceResult:
        records = [r for r in self.history if r["strategy"] == strategy_key]
        
        if len(records) < 3:
            return ConfidenceResult("MEDIUM", reason="数据不足(<3场景)")
        
        cv = self._compute_param_cv(records)       # 跨场景参数变异系数
        override_rate = self._compute_override_rate(records)  # LLM覆盖比例
        has_bifurcation = self._check_bifurcation(strategy_key)  # 是否有二选一参数
        
        if cv < 0.15 and override_rate == 0 and not has_bifurcation:
            return ConfidenceResult("HIGH", certainty=1.0 - cv)
        elif cv < 0.30 or override_rate < 0.2:
            return ConfidenceResult("MEDIUM", certainty=0.7 - cv)
        else:
            return ConfidenceResult("LOW", certainty=0.4 - cv)
    
    def record(self, strategy_key, params_used, params_default, llm_overridden):
        """每次管道运行后调用·记录本次参数使用情况"""
        edit_dist = self._compute_edit_distance(params_used, params_default)
        self.history.append({...})
        self._save()
```

## §3-5 同上...
