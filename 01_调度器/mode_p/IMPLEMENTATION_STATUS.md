# MODE:P 实现状态

更新时间：2026-07-18
版本：v4.0
状态：`LOCAL_REBUILD_READY`；run-011 为无效诊断证据；当前契约已通过本地回归，待全新实模重验

## 完成总览

| Phase | 内容 | 任务数 | 状态 |
|---|---|---:|:---:|
| 0 | 活动基线修复 | 5 | 完成 |
| 1 | 数据契约与单场垂直切片 | 10 | 完成 |
| 2 | 完整剧本与导演批次 | 8 | 完成 |
| 3 | 知识、能力与参考资产 | 7 | 完成 |
| 4 | 状态机、缓存与 Claude Code Loop | 12 | 完成 |
| 5 | 真实渲染反馈学习框架 | 4 | 完成 |
| 6 | 迁移与收口 | 4 | 完成 |
| 7 | 注意力收敛与独立分集 | 7 | 完成 |
| 8 | 视觉真源与有效审查 | 8 | 6 完成，2 待实模/外部证据 |
| **合计** | | **65** | **63 完成** |

## 本地证据

```text
python -m pytest . -q
685 tests passed in 179.37s (`python -m unittest discover`)

python -m unittest test_active_entrypoints.py
14 tests passed in 1.30s

python -m unittest test_script_facts_tool.py test_master_compiler.py test_dp_contract.py test_dp_adversarial_check.py test_episode_review.py test_model_acceptance_guard.py
108 tests passed in 9.86s

python -m legacy_residue_check
No legacy residue found.
```

这些结果证明当前本地实现与结构契约。run-011 证明真实 Director 能完成四类场景设计，
也暴露并促成了事实阶段、DP 契约和 Episode Review 解析修复；但该 run 已正式失效，
2026-07-19 的当前输出契约仍需新 run 的显式实模验收，不得把诊断证据写成通过结论。

## 活动入口

```text
/mode-p-pilot <当前分集剧本路径>
/mode-p-rebuild
/mode-p-accept <new-run-id>
```

`/mode-p-rebuild` 不启动 Agent；`/mode-p-accept` 不得放入 `/loop`。工程参数仅供测试和恢复使用，不属于用户创作入口。

## 当前架构

- 当前独立分集是本集叙事真源；完整项目剧本只是可选背景，不要求分集是其子串。
- 每集一个持续 Director，跨批次、修订和 Episode Review 统一设计镜头、运镜、构图、光影、表演和切换。
- 每轮使用 fresh DP，只读取干净场景证据、Storyboard、Video Prompt、实际能力摘要和已使用资产卡。
- Master 是唯一设计源；Storyboard 与 Video Prompt 只复制 Director 源文本，并按 Director
  选择的场景 Profile 改变关注顺序。脚本不得补写画面、动作、光影、声音或转场文案。
- 每镜只有一条视觉时间线；Video 使用全部节点，Storyboard 仅使用 `[SB]` 节点。
- N 个 Shot 只有 N+1 个共享 Boundary。
- 无图片和无资产卡均正常；运行时不调用视觉模型，默认 `text_only`。
- 文字资产卡以媒体哈希绑定，媒体变化后自动 stale，并受模型上下文预算限制。
- 每个 Shot 独立满足 `0 < duration <= 15s`；支持纯提示词、首尾帧、全能参考。
- 最终只交付 `STORYBOARD.md` 与 `VIDEO_PROMPT.md`。

## 不得回归

- 不恢复 Seko、旧领域 Agent 链、YAML Agent 协议、TIME_SKELETON、Gate、复杂度路由或规则 ID 证明链。
- 不让 DP 读取 Master、Manifest、知识库、源码、哈希或 Director 推理过程。
- 不把完整项目剧本、全知识库或全资产卡无差别塞入模型上下文。
- 不将 pytest 通过表述为导演语义能力已经验收。
- 不把哈希、边界 ID、Profile、时间模式、审计标签或程序合成的控制文案写进最终提示词。
