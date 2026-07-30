# MODE:P 完整重构迁移映射

本次重构的原则是：保留历史，切断默认调用。当前入口不再依赖旧管道的中间产物。

| 原职责 | 旧位置 | 当前替代 | 状态 |
|---|---|---|---|
| 主调度 | `01_调度器/dispatcher_v5.0.md` 的 v5-v8 内容 | 同路径的新导演循环 | 已替换 |
| 机位、运镜、构图、光影分域设计 | `02_Agent/legacy_mode_p/shot_*`、`movement_*`、`composition_*`、`scene_designer_*` | `02_Agent/director_agent.md` | 已合并 |
| 提示词组装 | `prompt_composer_*`、`storyboard_planner_*` | Director 直接输出两份提示词 | 已移除 |
| 多层审计和验证 | `scene_*auditor`、`p_verifier_*`、`render_verifier_*`、`object_existence_verifier_*` | `02_Agent/dp_agent.md` + `mode_p/sd2_preflight.py` | 已收缩 |
| YAML/PLAN/时间骨架 | `yaml_only_protocol`、`TIME_SKELETON_spec`、`PLAN_*` | Scene Context + 两份自然语言提示词 | 已移除 |
| 复杂度路由与 Gate 0 | `complexity_router`、`gate0_*` | 无；导演按场景直接工作，预检只保留 SD2.0 硬边界 | 已移除 |
| Seko 平台和打包 | `render_packager_*`、旧 `canvas_runtime` | `04_共享/canvas_runtime.md` 的即梦 SD2.0 边界 | 已替换 |
| 缓存前缀与旧脚本 | `01_调度器/legacy_mode_p/` | `mode_p/run_mode_p.py` | 已归档 |
| 历史输出 | 原 `02_Agent/output/`、`01_调度器/output/` | 各自 `legacy_mode_p/output/` | 已归档 |

## 当前有效文件

- `01_调度器/dispatcher_v5.0.md`
- `01_调度器/mode_p/`
- `02_Agent/director_agent.md`
- `02_Agent/dp_agent.md`
- `04_共享/CONSTITUTION.md`
- `04_共享/canvas_runtime.md`
- `04_共享/shared_agent_runtime.md`

## 运行不变量

1. Agent Host 只加载 Director 和 DP 两份指令。
2. 调度器只在 DP 通过后运行 SD2.0 最小预检。
3. 会话交付目录只包含 `STORYBOARD.md` 和 `VIDEO_PROMPT.md`。
4. `legacy_mode_p/` 下的文件、输出与协议不能作为新任务输入。
