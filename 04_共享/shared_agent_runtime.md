# MODE:P 共享运行时

所有 MODE:P 调用共享以下最小上下文：

- `Scene Context` 中的剧本、空间事实、人物连续性、参考材料与用户意图。
- `CONSTITUTION.md` 的空间、连续性与 SD2.0 边界。
- `01_调度器/mode_p/knowledge/` 中按需选择的知识胶囊。

Director 读取完整设计上下文。DP 读取场景上下文与导演的两份提示词。两者都不读取旧流程报告、规则编号、YAML、PLAN 或历史审计文件。
