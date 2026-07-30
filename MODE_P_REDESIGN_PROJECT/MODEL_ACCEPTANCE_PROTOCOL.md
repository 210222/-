# MODE:P 实模验收协议

> 本协议只由用户显式调用 /mode-p-accept 时执行。/mode-p-rebuild 和定时 /loop
> 不得自动进入本协议。验收不调用即梦、不渲染图片或视频。

## 1. 验收目的

本地测试能证明结构、哈希、边界、时长、恢复和同源派生，但不能证明模型真的具备：

- B1-B5：戏剧理解、镜头必要性、跨域统一、全片弧线和场面调度。
- D4：同一知识在不同场景中的迁移，而不是套用同一方案。
- J12：指定模型确实执行了 Director 与 DP。

因此，实模验收与工程重构分开运行。

## 2. 固定输入与模型

~~~text
FIXED_INPUT=MODE_P_REDESIGN_PROJECT/acceptance_cases/director_transfer_4scenes.md
FIXED_INPUT_SHA256=6cb709ad33294d0caf5aedb3ab6b528ab9cdcd0ff15e81240e8559bbf3b15073
DP_ADVERSARIAL_INPUT=MODE_P_REDESIGN_PROJECT/acceptance_cases/dp_adversarial_packet.md
DP_ADVERSARIAL_SHA256=ca8aeb2e8f2ee59485090e11258ed2fad97ad65684f700ba6503b299be718a14
EVIDENCE_ROOT=MODE_P_REDESIGN_PROJECT/model_acceptance_runs/<new-run-id>/
REQUIRED_DIRECTOR_MODEL=deepseek-v4-pro
REQUIRED_DP_MODEL=deepseek-v4-pro
~~~

不得使用 _MINI_SCRIPT、test_*.py 夹具、另一个样例或历史 run。每次验收必须分配
新的 run ID；无效 run 永久保留但不可恢复、重绑或晋升。
已归档的 run-001 是模型溯源错误的无效诊断运行，任何后续验收都不得复用。

## 3. 角色与写权限

- 主 Claude Code 任务只编排，不创作、不审查。
- 一次 mode-p-director Agent 调用负责四场的全片策略和全部 Master；修订继续使用
  同一个 Director Agent，不为每场新建 Director。
- 每一轮 mode-p-dp 都是新的 Agent，不得 resume 旧 DP。
- 本地程序只做脚手架、检索、编译、派生、预检、哈希、状态和原子提交。

验收父会话不得启动 Explore、Plan、general-purpose 或其他辅助 Agent。整次验收只允许
一个可恢复的 `mode-p-director` 身份与每轮全新的 `mode-p-dp`；流程理解由本协议和
`/mode-p-accept` 的确定性命令序列提供，不得另开 Agent 研究代码或历史运行。

第一个创作写入必须来自 Director Agent。主任务不得创作或修补：

- SCRIPT_FACTS.md
- EPISODE_VISUAL_BIBLE.md
- EPISODE_CONTINUITY_LEDGER.md
- DIRECTOR_MASTER.md

## 4. 模型溯源

Agent frontmatter、角色名、父模型名和主任务口头声明都不是模型证据。唯一模型证据是
Claude Code JSONL 中 Agent 工具结果的 resolvedModel。

Director 启动后、任何预检前，必须运行：

~~~powershell
python -m model_acceptance_guard bind-director --run-dir <run-dir> --agent-id <internal-agent-id>
~~~

校验器自动读取 Claude JSONL，不接受手填 --model。若真实 resolvedModel 不是
deepseek-v4-pro，必须立即 invalidate 当前 run，不得继续预检。
绑定成功时，校验器会把该 Agent 的工具调用记录和 `resolvedModel` 结果记录保存到
当前 run 的 `provenance/`。这是最小、可迁移的 JSONL 证据；原始电脑上的完整会话
路径只作为来源说明，后续换盘符、用户名或项目根目录时仍可重新核对记录哈希。

每个 fresh DP 返回后，必须逐字保存其最终消息，再运行：

~~~powershell
python -m model_acceptance_guard bind-dp --run-dir <run-dir> --review-id <round-id> --agent-id <internal-agent-id>
~~~

同一 DP Agent ID 重用、模型不符、角色不符、输入/run 路径不符都必须失败。校验器还会从
Claude transcript 绑定 DP 最终消息的哈希；父任务改写、缩短、合并或重新格式化后的反馈
不得提交。格式不合格时保留原响应，使用新的 review ID 启动另一个 fresh DP。

内部 Agent ID 只用于校验器和证据文件，不显示给用户。

## 5. 唯一执行顺序

~~~text
EXPLICIT_START
  -> LOCAL_PREFLIGHT
  -> PREPARE_NEW_RUN
  -> OFFICIAL_PILOT_SCAFFOLD
  -> ONE_PRO_DIRECTOR
  -> BIND_DIRECTOR_PROVENANCE
  -> MASTER_COMPILE_AND_DERIVE
  -> STRUCTURAL_PRECHECK
  -> FRESH_ADVERSARIAL_PRO_DP
  -> ADVERSARIAL_DP_CHECK
  -> FRESH_PRO_DP
  -> BIND_DP_PROVENANCE
  -> DIRECTOR_REVISE when needed
  -> FINAL_HASH_CHECK
  -> ATOMIC_BATCH_COMMIT
  -> EPISODE_REVIEW
  -> ATOMIC_TWO_FILE_DELIVERY
  -> EVIDENCE_AUDIT
~~~

### 5.1 Local preflight

确认：

- SUPERVISION.lock 已 released。
- IMPLEMENTATION_PLAN 的本地实现 P8.1-P8.6 全部勾选；P8.7 正是本次验收，
  P8.8 是不阻塞启动的外部即梦证据。
- 当前聚焦测试、全量测试和 legacy residue 证据有效。
- 固定输入哈希匹配。
- 没有另一个 acceptance run 处于 in_progress。

### 5.2 Prepare and scaffold

从 01_调度器/mode_p 运行：

~~~powershell
python -m model_acceptance_guard prepare --run-id <new-run-id> --owner claude-code
python -m mode_p_pilot <fixed-input> --session-dir <run-dir>/episode
~~~

mode_p_pilot 只创建确定性 session、场景、状态和占位文件。不得手写 RUN_STATE，
不得用临时 Python 片段调用 init_state/transition 绕过正式入口。

### 5.3 Director

启动一个 mode-p-director Agent。Assignment 必须包含：

- 固定输入绝对路径和 SHA-256。
- 新 run 与 episode session 的绝对路径。
- 02_Agent/director_agent.md。
- director_master_template.md。
- PILOT_PREP_STATUS.json、BATCH_MANIFEST.json 和 SCENE_SESSIONS.json。
- 每场选择的最小知识上下文。

四场共用同一个 Director。Director 只能写被授权的 episode 文档与 Master。

Director 必须按 `PILOT_PREP_STATUS.json` 分阶段工作，不得跨过确定性骨架生成：

1. `awaiting_script_facts`：首次调用只填写已生成的 `SCRIPT_FACTS.md`，完成后重新运行
   `mode_p_pilot` 验证来源并生成分集文档骨架。
2. `awaiting_episode_documents`：恢复同一个 Director，只填写程序生成的
   `EPISODE_VISUAL_BIBLE.md` 与 `EPISODE_CONTINUITY_LEDGER.md`，完成后再次运行
   `mode_p_pilot`。
3. `ready_for_scene_design`：恢复同一个 Director，开始四场 Master 设计。

这种分段只增加确定性校验，不增加 Director 身份或知识加载；不得为省一次恢复调用而让模型
提前自建骨架，随后再进行大段格式返工。

### 5.4 Deterministic gate and DP loop

Director provenance 绑定成功后，才可通过活动 runtime：

1. 编译 Master。
2. 从 Master 唯一视觉时间线派生 Storyboard 与 Video Prompt。
3. 运行结构预检，包括 N+1 共享 Boundary 和最终提示词全文扫描。
4. 先通过 5.5 的验收专用对抗 DP Gate。
5. 为当前批次生成哈希绑定的 DP_PACKET。
6. 启动一个 fresh mode-p-dp Agent，并在接受响应前绑定其 Pro provenance。
7. 每场恰好一条 READY，不是每 Shot 一条；冒号后的依据为 18-240 字符，必须引用当前
   Shot 并附一条可观察审查理由。不得有前言、标题、摘要或结语；通用 READY 失败。
8. 生产反馈必须由 `batch_dp submit` 对整个 packet 提交一次；禁止拆成逐场
   `run_mode_p submit` 绕过批次状态。
9. READY 时做 final hash check 和 batch commit。
10. 有问题时只把引用到的 Shot 问题发送给同一 Director 修订，再重新派生和 fresh DP。

Visual Bible 与 Continuity Ledger 必须在生产 DP packet 前完成。packet 创建后两者均为
哈希绑定输入；如 Episode Review 暴露出必须修改的缺陷，当前 run 失效，不得在旧 DP
反馈后修改共享文档并继续交付。

没有固定轮数。相同 Master 哈希下重复同一问题时停止为空转阻塞。

### 5.5 Adversarial DP gate

生产 DP 之前另启动一个 fresh `mode-p-dp`，只给它固定
`dp_adversarial_packet.md` 和活动 DP 输出契约。以独立 review ID 绑定真实模型后，
保存响应并运行：

~~~powershell
python -m dp_adversarial_check <run-dir>/DP_ADVERSARIAL_RESPONSE.md
~~~

必须同时识别机位路径、无锚点光源、未裁决提示词分支、共享 Boundary 断裂和
Storyboard/Video 不同步五类问题。这是验收专用额外一次 DP 调用，不进入
生产 Pilot、交付、缓存或知识/经验系统。

### 5.6 Episode and delivery

所有场景提交后，由同一 Director 对最小 Episode Review packet 做全片一致性复核。
若需要修订，只回到受影响场景；修订后仍必须通过 fresh DP。

Episode Review PASS 后只能由 episode_delivery 原子生成：

~~~text
delivery/STORYBOARD.md
delivery/VIDEO_PROMPT.md
~~~

不得交付 Master、Manifest、DP 报告、YAML、审计表、Seko 包装或渲染文件。

交付后必须再次运行 `mode_p_pilot` 刷新分集根 `RUN_STATE.json`，随后只能通过：

~~~powershell
python -m model_acceptance_guard complete --run-dir <run-dir>
~~~

晋升验收状态。`complete` 必须同时看到批次 `DP_STATE=committed`、四场景
`batch_commit`、分集根状态 `delivery`、当前 Episode Review、恰好两份交付及全部
模型/语义证据。不得直接手写 bootstrap 或 MODEL_ACCEPTANCE_STATUS。

## 6. 必需证据

新 run 必须包含：

- ACCEPTANCE_BOOTSTRAP.json：固定输入、真实 Director/DP provenance。
- provenance/*.jsonl：每个 Director/DP 的最小可迁移工具调用与 resolvedModel 原始记录。
- RUN_EVIDENCE.json：指令、模型、调用、耗时、知识、输入输出和测试哈希。
- DIRECTOR_QUALITY_REVIEW.md：B1-B5 的具体 Scene/Shot 证据。
- TRANSFER_REVIEW.md：D4 的三场对话迁移对比。
- DP_ADVERSARIAL_RESPONSE.md 及检查结果：五类故意问题全部被 fresh DP 识别。
- 完整 episode session。
- 最终两份 delivery 的 SHA-256。

隐藏推理、规则 ID 证明和历史报告不属于证据。

## 7. 通过、失败和阻塞

只有以下全部成立才能写 MODEL_ACCEPTANCE_PASSED：

- Director 和每个 DP 的真实 resolvedModel 都是 deepseek-v4-pro。
- 每条模型 provenance 都有 run 内可复核的最小 JSONL 快照，且记录哈希匹配。
- 四场全部完成 Master -> 派生 -> 预检 -> fresh DP -> commit。
- 批次 DP_STATE 为 committed，分集根 RUN_STATE 为 delivery，且状态哈希有效。
- 验收专用 fresh DP 通过五类问题对抗检查。
- Episode Review 与原子双文件交付通过。
- B1-B5、D4 有可观察证据。
- 所有证据文件和哈希可复核。

以下情况立即把当前 run 标记 invalid：

- 实际模型不是 deepseek-v4-pro。
- 伪造、手填或无法找到 Agent provenance。
- 父任务修改 fresh DP 的最终消息后提交。
- 主任务创作/修补 Director 文件。
- 绕过正式状态机、预检或 fresh DP。
- 恢复历史无效 run。

只有认证、权限、Agent 工具不可用或真实剧本歧义才标记 blocked，并记录原始错误与
恢复动作。测试通过不能替代实模验收。
