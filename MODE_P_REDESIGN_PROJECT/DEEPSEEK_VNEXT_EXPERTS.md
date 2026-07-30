# MODE:P vNext DeepSeek 专家使用说明

## 定位

这五个专家是 Claude Code 中的只读工程审查角色，不是独立写入者。它们帮助
`deepseek-v4-pro` 父任务发现缺口、形成测试要求和复核实现；只有父任务可以修改
文件、运行命令、持有 rebuild-control token 和完成任务。

## 专家映射

| Claude Code Agent | 任务 |
|---|---|
| `mode-p-vnext-control-evidence-auditor` | R0.1、R0.2、R0.3、R3.2控制/证据侧 |
| `mode-p-vnext-golden-prompt-auditor` | R1.1-R1.4 |
| `mode-p-vnext-runtime-systems-auditor` | R2.1-R2.2 |
| `mode-p-vnext-knowledge-safety-auditor` | R2.3-R2.4 |
| `mode-p-vnext-release-auditor` | R3.1-R3.2发布侧 |

所有 Agent 都使用：

```yaml
tools: Read, Glob, Grep
model: inherit
permissionMode: plan
```

它们没有 `Write`、`Edit`、`Bash`、`Agent` 或 `Task`，因此不能修改项目、执行
测试、派生其他专家或推进控制状态。

## 使用步骤

1. 在 Claude Code 中选择父模型 `deepseek-v4-pro`。
2. 确认当前机器任务：R0.1、R0.2已完成时应为R0.3。
3. 运行只读审查：

   ```text
   /mode-p-vnext-expert-review R0.3
   ```

4. 父任务核验 Agent 调用结果中的实际 `resolvedModel` 必须等于
   `deepseek-v4-pro`；不匹配时丢弃审查结果。
5. 查看结构化 `EXPERT_REVIEW`。专家的 `READY` 只是建议，不是完成证据。
6. 另行运行正式施工命令：

   ```text
   /mode-p-vnext-rebuild R0.3
   ```

7. 施工仍由父 DeepSeek 会话完成，控制器负责 claim、固定测试和 complete。

## R0.3 语义证据专项修复

R0.3 曾出现“控制面完成但语义证据内部不一致”：逐项互斥分类为
`11/44/6/8/1`，而 Evidence 文本通过重复6项非法依赖、遗漏6项 NOT_STARTED
碰巧仍合计70；Progress 也只更新了顶部而保留 R0.1 正文。

这类已封存任务不能直接覆盖文件。请在 `deepseek-v4-pro` 父会话中运行：

```text
/mode-p-vnext-r03-semantic-repair
```

该命令会要求 DeepSeek 父任务先做只读预检，再通过控制器撤销和重新领取
R0.3；只有父任务能修改四个明确列出的 R0.3 文件。控制证据专家在修改前后
只读审计，不能持有 token 或替代控制器完成任务。

不要先运行 R1.1，也不要手工编辑机器状态、监督锁或已封存 Evidence。

注意：`MODE_P_VNEXT_PROGRESS.md` 是控制器明确列出的可变状态视图，不进入
`artifact_hashes`；不得宣称它已被R0.3哈希绑定。R0.3 Evidence 由状态记录中的
Evidence SHA-256单独绑定，不能自我哈希。

专项修复还必须执行R0.2入口回归并确认项目内不存在
`.claude/settings.local.json`。该文件即使未提交也会触发入口测试失败；需要的
Claude Code本机权限应放在项目工作区之外。

## R1.1 缺失媒体专项修复

如果R1.1的Golden媒体测试仍包含`if not exists: continue`，即使当前8个媒体
都存在且测试全绿，也不满足修复计划中的“不可用媒体明确标记missing，不允许
以skip代替冻结完成”。权威文本缺失会失败，不能替代该媒体检查。

在`deepseek-v4-pro`父会话中运行：

```text
/mode-p-vnext-r11-media-repair
```

该命令只允许DeepSeek父任务修改基线Manifest、基线测试和R1.1 Evidence。
它要求每个媒体显式标记`available|missing`：available必须存在且哈希/大小匹配；
missing必须保留预期路径和原因，并出现在结构化验证结果中。测试必须主动构造
缺失文件情形，证明不能静默`continue`。

## R1.2 精确提示词专项修复

R1.2中的“8个文件存在且每份超过100字”不等于“四组精确提示词对”。如果
fixture的`integrity_note`写着`Reconstructed`，或正文来自Evidence报告摘要，必须
撤销R1.2，不能让R1.3使用这些摘要学习输出格式。

完整八份用户原文已定位在本次Codex会话JSONL中，并分别固定了事件行号、字符数
和正文SHA-256。DeepSeek必须流式提取，不能把约266MB会话文件载入模型上下文，
也不能自行重构。

在`deepseek-v4-pro`父会话中运行：

```text
/mode-p-vnext-r12-exact-prompt-repair
```

该命令会受控回开R1.2，并通过八组独立常量验证逐字正文。任何字符改动、结尾
换行裁剪、空行归一化、摘要替换或`Reconstructed`声明都会使测试失败。修复完成
后才能进入R1.3双输出格式任务。

## R1.3 双输出格式专项修复

R1.3 的 Golden 预审已经确认：当前故事板和视频渲染器输出的是扁平通用
Markdown，与四组成功样本的分层格式不匹配。执行修复时使用：

```text
/mode-p-vnext-r13-dual-output-repair
```

该命令只修故事板/视频投影、渲染和对应 V5.1-V5.4、V5.8 测试。八份 R1.2
逐字提示词及其 manifest 是不可变输入，不能为了让 R1.3 测试通过而改写。

预审提到的 Master schema 扩展和负向能力路由不在 R1.3 写入边界内：
`generation_segment.py`、`capability_adapter.py`、`payload_compiler.py` 和
`payload_manifest.py` 禁止修改。R1.3 使用一个由两个投影共享、带来源字段 ID 的
只读双输出投影契约承载外部格式信息；故事板只选 `[SB]` 节点，视频读取完整节点。
它不能成为第二份导演创意，也不能让渲染器在运行时读取 Golden fixture。

V5.5-V5.7 在该轮仅作只读回归。若必须越界才能满足 R1.3 的四项检查，任务应以
`R13_SCOPE_BLOCKED` 停止，不能修改任务注册表、弱化测试或宣称能力路由已经修复。

### R1.3 完成后完整性回开

首轮 R1.3 虽然显示 80 项测试通过，但后续独立复核确认存在假阳性：共享合约和
节点实际可变；直接视频投影没有合约时间线；最小交付会静默缺段；默认文本会
虚构格式和视觉语义；四个 archetype 没有逐个投影渲染；篡改测试没有调用生产
检查路径；同步检查器会漏过合约 tick 篡改。

在 R1.4 开始前，使用：

```text
/mode-p-vnext-r13-integrity-repair
```

该命令会要求 DeepSeek 先用控制器撤销 R1.3，再修复不可变值对象、完整输出
fail-closed、来源追踪、精确时间、四组真实结构测试和生产合约指纹。不得直接运行
R1.4，也不得把 D3 或 D6-D7 错写成“延期至 R1.4”，因为 R1.4 没有这些实现文件的
写入权限。

### R1.3 Golden 事实落地二次回开

第一次完整性回开修复了主合约可变和默认视频无节点，但第二次审计发现测试中的
四个“Golden 原型”是模型重新编写的替代故事：观众席被缩成7秒、备赛区人物
提前到2秒入画、窄巷被改成Rico和追车，且视频只测试了枪管一例。空合约、缺少
来源、错误 shot ID、越界节点和重复职责仍能通过交付验证。

在 R1.4 之前再次执行：

```text
/mode-p-vnext-r13-golden-grounding-repair
```

该命令要求所有 Golden 测试值绑定八份逐字 fixture 的正文哈希和字符跨度，禁止
手写替代故事；同时修复主渲染入口 fail-closed、完整来源指纹、真实边界验证和
错误的节点计数尾注。完成并通过独立审查前不得开始 R1.4。

### R1.3 外部锁定验收三次回开

第二次回开后虽然 V5.1-V5.8 显示72项全绿，但独立复现确认这些测试仍在文件内
手写四组故事板和四组视频替代数据，没有读取R1.2八份原文，也没有任何来源字符
跨度文件。生产renderer模块仍可直接输出空合约；缺失顶层来源、未知shot、越界
节点、重复phase、非法node类型和重复参考图也没有专门错误。因此该轮Evidence
和Golden `READY`仍是假阳性。

在R1.4之前执行：

```text
/mode-p-vnext-r13-external-gate-repair
```

这一次以
`MODE_P_REDESIGN_PROJECT/vnext_acceptance/test_r1_3_external_acceptance.py`
作为DeepSeek无权修改的外部验收门。它固定八份正文哈希、来源跨度schema、八个
真实输出、canonical envelope、生产入口失败关闭和负向结构矩阵。DeepSeek只能
修改R1.3原有写入边界与`fixtures/r1_3/`，不能再通过自写测试和自写Evidence同时
定义“正确”。外部门未全绿或哈希变化时，禁止完成R1.3。

### R1.3 语义覆盖四次回开

上一版锁定门控的17/17已经复现，但它只验证了21个选定锚点，并不能证明完整
输出都来自八份逐字fixture。强化后的Codex外部门控又发现11类失败：故事板与
视频各自重建合约、时间线被压缩成阶段摘要、内部切点没有瞬时节点、大多数
输出语义没有来源跨度、必需章节集合为空、来源权威没有哈希、语义改写未被
拒绝、指纹存在分隔符碰撞，以及worker测试仍手写替代故事。

在R1.4之前执行：

```text
/mode-p-vnext-r13-semantic-coverage-repair
```

该命令锁定
`MODE_P_REDESIGN_PROJECT/vnext_acceptance/test_r1_3_external_acceptance.py`
的SHA-256为
`de251e5dd97cc7b03b3ae27619f01e2587ce69efe23971a803e61d07fccc47cd`。
修复前基线必须是16通过、11失败；完成条件是27项全部通过且门控文件未被修改
或绕过。修复还必须实现每个场景一份Canonical Director Contract、完整逐秒
Golden时间线、全部语义的SourceSpan或封闭确定性派生、抗碰撞Canonical JSON
指纹，以及直接使用八个真实Golden delivery的worker测试。只读Golden专家
复审为`READY`之前禁止启动R1.4。

如果DeepSeek因为单次回复范围而停在中间检查点，但控制器仍显示R1.3由原owner
持锁，不要重新撤销、认领或恢复。继续执行：

```text
/mode-p-vnext-r13-semantic-coverage-continue
```

续跑命令把剩余施工拆成生产权威与指纹、共享合约与完整Golden时间线、worker
测试与全回归三个阶段。阶段结束只能记录checkpoint，不能提前complete；单次
响应大小不是改路线、降低门控或把问题延期到R1.4的理由。

## 强边界

- 一次只运行一个与当前 task_id 匹配的专家。
- 专家仅接收任务包列出的路径和问题。
- 不给专家完整知识库、完整 LOOP、v4 源码、媒体二进制、Session 或无关历史。
- Golden 专家只读取精确提示词、结构化视频证据和用户评价，不声称观看媒体。
- 专家不接收控制 token，不写 Evidence，不调用任何生产、Shadow、Pilot 或
  外部生成服务。
- 专家输出必须引用 `path:line`，区分事实、用户评价、推断和建议。
- 多个专家不得并行写入；当前配置中所有专家本身均无写权限。

## 与正式 LOOP 的关系

这些文件提供独立的只读预审入口，不会改变已完成的 R0.1/R0.2，也不会自动被
`/mode-p-vnext-rebuild`调用。若以后要把专家审查设为每个任务的强制步骤，必须
通过控制器正式回开并重验对应入口任务，不能直接修改完成状态。
