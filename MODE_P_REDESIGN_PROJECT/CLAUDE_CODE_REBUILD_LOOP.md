# MODE:P v3.0 Claude Code Rebuild Loop

> 本文件只定义工程重构循环。它不创作剧本提示词，不启动 Director/DP，也不执行实模验收。

## 1. 三种 Loop 的边界

| 入口 | 职责 | 是否调用 LLM 子 Agent | 结束状态 |
|---|---|---:|---|
| /mode-p-rebuild | 修改代码、规范、测试和入口 | 否 | LOCAL_REBUILD_READY 或具体失败 |
| /mode-p-accept | 固定四场真实语义验收 | 是，显式调用 Pro Director/DP | MODEL_ACCEPTANCE_PASSED 或真实阻塞 |
| /mode-p-pilot script | 用户剧本的正式创作 | 是，一个持续 Director + fresh DP | 原子双文件交付或真实阻塞 |

三个入口不得互相偷偷升级：

- Rebuild 不得因为当前计划全部勾选完成而自动启动实模。
- Accept 不得修改活动实现来帮助样例通过。
- Pilot 不得写重构进度或把用户作品当回归夹具。

## 2. Rebuild 的唯一目标

把 IMPLEMENTATION_PLAN.md 中的任务落实为当前代码和可执行证据，并保证：

- 剧本是唯一叙事真源。
- 一个 Director 统一设计镜头、运镜、构图、光影、表演和切换。
- Storyboard 与 Video Prompt 从同一 Master 派生。
- 当前独立分集是本集真源；完整剧本只是可选、非冲突项目背景。
- Director 与 DP 使用最小模型上下文，不读取媒体二进制或无关工程证据。
- 八类场景 Profile 真正改变双视图组织；无素材自动使用 text_only。
- 每个 Shot 独立满足 0 < duration <= 15s。
- 支持纯提示词、首尾帧和全能参考。
- 运行时没有 Seko、旧领域 Agent 链、YAML Agent 协议、TIME_SKELETON、
  Gate、复杂度路由或规则 ID 证明链。

## 3. 权威文件

每轮只按以下优先级判断：

1. 当前活动代码与当前测试结果。
2. IMPLEMENTATION_PLAN.md 与 PROGRESS.md。
3. ACCEPTANCE_MATRIX.md。
4. LOOP_SPEC.md。
5. 本文件与活动入口文档。

legacy_mode_p/、旧输出报告和历史 Agent 指令只可作为迁移反例。

## 4. 并发与锁

开始前必须读取 MODE_P_REDESIGN_PROJECT/SUPERVISION.lock。

- status: active 且 owner 不是当前任务：立即停止，不编辑、不测试。
- status: released：可以继续。
- 发现另一个 Claude/pytest 正在写同一范围：立即停止。
- 每轮只允许一个写入者；锁状态必须在结束时同步。

## 5. 单轮状态机

~~~text
READ_STATE
  -> SELECT_ONE_TASK
  -> MARK_IN_PROGRESS
  -> INSPECT_ACTIVE_FILES
  -> IMPLEMENT_MINIMAL_COMPLETE_CHANGE
  -> FOCUSED_TESTS
  -> REQUIRED_REGRESSION
  -> SYNC_PLAN_PROGRESS_STATUS
  -> STOP
~~~

每轮只执行一个任务或一个确定性完成审计。/loop 只是重复调用该单轮状态机，
不能改变单轮边界。

## 6. 任务选择

顺序固定：

1. 用户最新明确指定的任务。
2. PROGRESS.md 中真实 in_progress 且没有其他 owner 的任务。
3. 第一项未勾选且前置条件完成的任务。
4. 已勾选但当前测试失败或证据失效的任务。
5. 全部勾选时执行一次本地完成审计。

禁止选择：

- 只改说明、不改变可执行行为的伪任务。
- 恢复旧 Agent、Seko 或规则证明链。
- 创建另一套原型目录绕开活动入口。
- 自动执行 MODEL_ACCEPTANCE_PROTOCOL.md。

## 7. 本地完成审计

全部任务勾选后执行：

~~~text
CHECK_LOCK_AND_WRITERS
  -> VERIFY_PLAN_AND_PROGRESS
  -> TEST_ACTIVE_ENTRYPOINTS
  -> SCAN_LEGACY_RESIDUE
  -> RUN_FULL_SUITE_IF_EVIDENCE_IS_STALE
  -> SYNC_DOCUMENTS
~~~

必须运行或复核当前有效结果：

~~~powershell
cd 01_调度器/mode_p
python -m pytest test_active_entrypoints.py test_legacy_residue_check.py -q
python -m legacy_residue_check
python -m pytest . -q
~~~

通过后只报告：

~~~text
LOCAL_REBUILD_READY
NEXT_EXPLICIT_STEP: /mode-p-accept
~~~

不得报告 MODEL_ACCEPTANCE_PASSED、A-K 全部通过或最终项目完成。
实模状态由 MODEL_ACCEPTANCE_STATUS.md 单独记录。

若活动文件在最近全量测试后未变化，后续定时轮次只做轻量入口/残留检查并报告
NO_LOCAL_DRIFT；不得重复全量测试，更不得启动模型。

本工作区不是 Git 仓库。不得调用 `git status`、`git diff` 等命令判断漂移；使用
监督锁、活动文件时间/哈希、轻量入口测试和已记录的全量证据。

## 8. 实现原则

- 本地程序处理解析、ID、哈希、时长、边界、引用、缓存、恢复和原子提交。
- LLM 的创作与审查能力只在显式 Accept/Pilot 入口中使用。
- 所有设计先写 Master，再机械派生两个视图。
- 检查器不得替 Director 选择机位、构图、光影、运镜、表演或切换。
- 真实即梦渲染学习不属于重构关键路径。
- 项目登记、场景解析、资产卡绑定、Profile 派生和 DP 证据裁剪都由本地算法完成，
  不新增领域 Agent 或视觉模型调用。

### DeepSeek V4 Pro / 强推理父模型

- 在 Claude Code 中先选择目标父模型；Rebuild 与 Pilot 都不得在文件内伪造模型名。
- Rebuild 仍是一轮一个工程任务，不因模型能力强而一次改完整仓库。
- Pilot 子 Agent 使用 `model: inherit`；记录 Agent 工具实际 `resolvedModel`。
- 不追加“输出完整思维链”要求。模型应读取当前任务所需文件、私下推理、直接完成文件。
- 更大上下文窗口不是加载全库的理由；Director/DP 白名单和资产卡预算始终有效。

## 9. 阻塞

仅在凭据、权限、素材、真实剧本歧义或产品决策缺失时标记 blocked。记录：

~~~text
task_id
failed_command_or_evidence
attempted_repairs
required_external_change
next_step_after_unblock
~~~

任务困难、测试较慢或文件较多不是阻塞。

## 10. 调用

单轮：

~~~text
/mode-p-rebuild
~~~

指定任务：

~~~text
/mode-p-rebuild P4.12
~~~

连续工程循环：

~~~text
/loop 5m /mode-p-rebuild
~~~

当出现 LOCAL_REBUILD_READY 后停止 /loop。实模验收必须由用户另行显式执行
/mode-p-accept。
