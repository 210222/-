# Claude Code Loop 使用说明

详细执行协议见：

```text
MODE_P_REDESIGN_PROJECT/CLAUDE_CODE_REBUILD_LOOP.md
```

`CLAUDE_CODE_REBUILD_LOOP.md` 是 Claude Code 接力执行重构工程的权威文件；
`LOOP_SPEC.md` 是重构后 MODE:P 创作运行时的架构规范。

## 1. 开始重构

在项目根目录启动 Claude Code 后，运行一次：

```text
/mode-p-rebuild
```

有未完成项时，它每次只完成一个有测试证据的实施任务；全部勾选后，它执行一轮
Local Completion Audit，而不是报告“需要新任务”。本地审计完成时输出
`LOCAL_REBUILD_READY`，不会自动启动实模。

## 2. 使用 Claude Code Loop

如果当前 Claude Code 版本提供 `/loop`，让它周期性调用单步命令：

```text
/loop 5m /mode-p-rebuild
```

每轮从 `PROGRESS.md` 继续。Loop 不应无故重复已经 `passed` 的实施任务，也不能跨过
`blocked` 任务；但测试失败、活动文件变化或验收证据过期时，必须重新审计受影响的
已完成项。
仅在本机 `/loop` 会等待上一轮结束时使用周期调用；若可能并发启动，改为每轮完成后手动再次执行 `/mode-p-rebuild`。

每轮都必须以 `LOOP_SPEC.md` v3.0 为运行权威。重点验收独立分集入口、可选项目背景、最小 Director/DP 上下文、无多模态文字资产卡、Profile 双视图、规范化 Manifest、结构预检、缓存事务、镜间边界和动作时间轴。
工程实施本身必须按 `CLAUDE_CODE_REBUILD_LOOP.md` 的任务选择、锁、测试和状态同步规则执行。

`/mode-p-rebuild` 不允许启动 Director/DP。需要固定实模验收时，先停止
`/loop`，再由用户显式运行一次：

```text
/mode-p-accept <新的 run ID>
```

不得把 `/mode-p-accept` 放进定时 Loop。

如果 `/loop` 语法与本机版本不同，先在 Claude Code 内执行 `/help loop`，然后把 `/mode-p-rebuild` 作为重复执行的命令。不要改写单步命令为一次完成全部阶段。

## 3. 观察进度

随时查看：

```text
MODE_P_REDESIGN_PROJECT/PROGRESS.md
```

可信进度必须包含修改文件和测试证据。仅有“已分析”“已设计”或“应该可行”不算完成。

## 4. 暂停与恢复

- 可以在任意任务完成后停止 Claude Code。
- 下次重新运行 `/mode-p-rebuild` 会从第一个未完成任务继续；若全部完成，则进入
  Local Completion Audit。
- 遇到 `blocked` 时先解决记录的阻断条件，再继续 Loop。
- 不删除或手工跳过失败测试。

## 5. 项目完成后运行 MODE:P

最终用户入口仍为：

```text
/mode-p-pilot <当前分集剧本路径>
```

当前分集默认处理全部场景；生产入口不接受场景范围或项目绑定参数。局部重算由内部
失效器根据内容变化自动决定。

运行时由主任务编排一个持续 `mode-p-director` 子 Agent 和每轮全新的
`mode-p-dp`，自动完成：剧本分场与事实追溯、全片视觉策略、批次 Master、内部
Manifest、双视图派生、DP 前结构预检、修订、最终哈希检查、批次提交和全片回看闭环。
用户不需要手动选择生成模式或转发反馈；Director 必须在每个 Shot 中给出纯提示词、
首尾帧或全能参考的选择与 asset_id 职责。
