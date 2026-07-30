# MODE:P Rebuild Progress

状态：`LOCAL_REBUILD_READY`
版本：MODE:P v4.0
审计日期：2026-07-18
当前计划：63/65 项完成
历史实模证据：run-005（旧契约）
当前 v4.0 契约：原行为基线 `685 tests passed`；加入 vNext 重构入口隔离测试后仓库全量 `686 tests passed`；实模验收待全新 run 执行
真实即梦渲染：尚未验证

## 活动入口

| 入口 | 状态 | 边界 |
|---|---|---|
| `/mode-p-rebuild` | ready | 一轮工程任务或本地完成审计；不启动 Agent |
| `/mode-p-accept <new-run-id>` | ready for explicit rerun | 固定语义验收；不得放入 `/loop` |
| `/mode-p-pilot <episode-script>` | ready | 当前独立分集创作；一个持续 Director + 每轮 fresh DP |

## v4.0 当前已完成

1. 用户入口收敛为 `/mode-p-pilot <当前分集剧本>`；项目背景可选、自动绑定，冲突时当前分集优先。
2. 无项目、无图片、无资产卡均是正常路径；默认使用 `text_only`，运行时不调用视觉模型。
3. 整个分集只绑定一个 Director，跨批次、修订和 Episode Review 恢复同一 Agent。
4. 每镜只有一条视觉时间线；Video 使用全部节点，Storyboard 仅使用 `[SB]` 节点。
5. N 个 Shot 只有 N+1 个共享 Boundary，连续交接不再写两份。
6. 最终提示词全文预检与场景级 DP READY 证据契约已实现。
7. 每个 Shot 独立满足 `0 < duration <= 15s`，支持纯提示词、首尾帧和全能参考。
8. Director 只接收当前场景所需知识和文字资产卡；DP 只接收干净证据与两个派生视图。
9. 本地程序负责解析、哈希、边界、时长、引用、缓存、锁、恢复和原子提交。
10. Seko、旧领域 Agent 链、YAML Agent 协议、TIME_SKELETON、Gate、复杂度路由和规则 ID 证明链均退出活动路径。

## DeepSeek V4 Pro 审计

- Rebuild/Pilot 使用 Claude Code 当前选择的父模型；Pilot 子 Agent 使用 `model: inherit`。
- 当前约束详细度足够：职责、输入白名单、输出契约、轮次边界和失败条件均明确。
- 不要求输出完整思维链，不因大上下文窗口加载全仓库，不用模型名称白名单伪造能力保证。
- 更详细的通用规则会增加注意力成本；确定性约束继续由本地程序和测试承担。

## 当前验证证据

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

公司电脑迁移复验已通过：根目录 `requirements.txt` 声明运行时与测试依赖；Claude/Codex
KB Guard 使用向上发现项目 Hook 的通用路径，不依赖盘符、用户名或 `_v5` 目录名；活动
入口测试会真实执行 Hook 并拒绝重新引入机器绝对路径。

测试临时目录已改为每次 pytest 进程唯一，连续重复执行不会复用旧 Episode、DP batch 或 session 状态。

## 尚未声称完成

- run-005 是旧契约历史证据。run-011 使用当前模型完成四类场景并通过场景预检、对抗 DP
  与生产 DP，但因提交后的 Episode Review 解析不一致被正式标记为无效；该问题现已修复。
- 当前精确输出契约要获得正式实模结论，仍需显式运行新的
  `/mode-p-accept <new-run-id>`；不得恢复或晋升 run-011。
- 尚无即梦真实渲染结果、用户观察和 validated 经验记录，因此不声称渲染质量或持续
  学习闭环已经完成。
