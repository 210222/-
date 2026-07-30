# 调度器

MODE:P 的唯一默认入口是 `dispatcher_v5.0.md`。它运行导演与摄影指导的循环，目标模型为即梦 SD2.0 画布。

完整的旧文件迁移映射见项目根目录的 `MODE_P_MIGRATION.md`。

在 Claude Code 中，直接输入 `/mode-p <Scene Context 路径>` 即可自动运行完整循环。

从剧本设计先导篇或预告片段时，输入 `/mode-p-pilot <剧本路径> [场景名或范围]`。剧本决定事件，知识库决定镜头语言。

- 活动运行时：`mode_p/`
- 历史规范与旧工具：`legacy_mode_p/`
- 历史输出：`output/`

历史目录不参与新任务。不得从其中加载 Agent 指令、YAML 协议、TIME_SKELETON、Gate 0、复杂度路由或 Seko 包装规则。
