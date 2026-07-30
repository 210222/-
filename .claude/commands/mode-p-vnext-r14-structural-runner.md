---
description: Implement exactly R1.4 real Golden structural runner under DeepSeek with source-bound artifact parsing, tamper tests, expert review, and controller completion.
argument-hint: []
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Agent
---

# R1.4 — Real Golden Structural Runner

在当前 Claude Code 父会话中执行且只执行 `R1.4`。这是一次受控制的
vNext 工程修复，不是创意生产、模型验收或生产切换。

## 0. 模型与角色硬门

父会话必须实际解析为：

```text
deepseek-v4-pro
```

文本自称不算证明。若当前父模型不是 `deepseek-v4-pro`，立即停止并返回：

```text
R14_MODEL_MISMATCH
EXPECTED: deepseek-v4-pro
ACTUAL: <resolved model>
NO_CLAIM
NO_WRITES
```

父 DeepSeek 会话是唯一写入者、唯一控制 token 持有者和唯一测试执行者。

只读专家固定为：

```text
mode-p-vnext-golden-prompt-auditor
```

专家必须使用 `model: inherit`，实际 `resolvedModel` 必须等于
`deepseek-v4-pro`。专家只允许 `Read/Glob/Grep`，不得使用 Write、Edit、Bash、
Agent、Task，不得 claim、complete、fail，不得写 Evidence。

一次只运行一个专家。不要并行运行多个写入者或多个专家。

## 1. 开始前确定性预检

在项目根目录 `D:\tsc\导演系统_v5` 工作。先从 `01_调度器` 执行：

```powershell
python -m mode_p_vnext.rebuild_control audit
python -m mode_p_vnext.rebuild_control status
python -m mode_p_vnext.rebuild_control next
```

必须同时满足：

```text
audit issues = 0
status = REPAIR_REQUIRED
completed_tasks contains R0.1-R1.3
next_task = R1.4
current_task = null
current_owner = null
lock_token = null
production_entry = v4_unchanged
```

还必须验证：

```text
MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/R1.3.json
sha256 = 2cd2fa03b03647c74e76b67389a8b51d32a61c99a3c9c7c96cf8f2336fc6fa4e

MODE_P_REDESIGN_PROJECT/vnext_acceptance/test_r1_3_external_acceptance.py
sha256 = de251e5dd97cc7b03b3ae27619f01e2587ce69efe23971a803e61d07fccc47cd

.claude/settings.local.json = ABSENT
```

任一条件不满足时停止，不 claim，不修改文件。不得通过修改旧 Evidence、机器状态、
任务注册表或外部门控来消除失败。

## 2. 只读 Golden 专家预审

在 claim 前调用一次
`mode-p-vnext-golden-prompt-auditor`，只给它下列最小任务包：

- `MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_REPAIR_TASKS.json` 的 R1.4 条目；
- `MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_LOOP_SPEC.md` §13、§29；
- `01_调度器/mode_p_vnext/structural_runner.py`；
- `01_调度器/mode_p_vnext/tests/test_v8_3_structural_runner.py`；
- `01_调度器/mode_p_vnext/fixtures/r1_3/golden_cases.py`；
- `01_调度器/mode_p_vnext/fixtures/r1_3/source_spans.json`；
- `MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/R1.3.json`；
- 本命令中的 R1.4 验收矩阵。

不要给专家完整知识库、媒体文件、旧 Session、v4 源码或控制 token。专家不得声称
观看过视频。

预审应把当前 placeholder 判为 `ISSUES`，至少识别：

1. runner 只有调用者传入的布尔值，没有 artifact parser；
2. 没有从真实 Storyboard/Video 输出计算结果；
3. 旧测试可由手工构造 `GoldenStructuralResult` 通过；
4. 没有真实篡改检测；
5. `skipIf` 会把模块缺失或实现缺失静默变成通过。

记录专家结果中的实际 `resolvedModel`。若不等于 `deepseek-v4-pro`，丢弃结果并停止。

## 3. Claim 和不可越界路径

生成唯一 owner，例如：

```text
ds-r14-structural-<UTC timestamp or UUID>
```

然后从 `01_调度器` claim：

```powershell
python -m mode_p_vnext.rebuild_control claim R1.4 --owner <owner>
```

token 只保留在当前父会话内，不输出给专家，不写入代码、测试、fixture、Evidence
或最终报告。

R1.4 只允许修改：

```text
01_调度器/mode_p_vnext/structural_runner.py
01_调度器/mode_p_vnext/tests/test_v8_3_structural_runner.py
01_调度器/mode_p_vnext/fixtures/**
MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/**
```

虽然 `fixtures/**` 是控制器允许的 glob，但以下已被前置任务哈希绑定，视为只读：

```text
01_调度器/mode_p_vnext/fixtures/*_prompt.json
01_调度器/mode_p_vnext/fixtures/prompt_fixture_manifest.json
01_调度器/mode_p_vnext/fixtures/r1_3/**
```

如需 R1.4 新 fixture，只能新增在：

```text
01_调度器/mode_p_vnext/fixtures/r1_4/
```

禁止修改：

- `storyboard_projection.py`、`storyboard_renderer.py`；
- `video_projection.py`、`video_renderer.py`；
- schema、capability adapter、payload compiler、payload manifest；
- R0.1-R1.3 Evidence 和已绑定 artifact；
- repair task registry、machine state、lock JSON、Progress checkbox；
- v4、legacy、知识库、媒体、Session、Shadow、Pilot、Canary、Production；
- `.claude/settings.local.json`；
- 本命令文件。

若完成要求确实需要越界，调用控制器 `fail` 并报告
`R14_SCOPE_BLOCKED`，不得自行扩大任务。

## 4. Real Runner 的定义

`structural_runner.py` 必须成为无模型、确定性、失败关闭的 artifact 检查器。

### 4.1 输入必须是真实 artifact

runner 必须解析生产渲染器实际输出的 Storyboard 和 Video Prompt 文本或文件。
测试中的八个 artifact 必须来自：

```python
build_golden_deliveries()
render_storyboard(...)
render_video_prompt(...)
```

四组场景全部覆盖：

```text
gun_barrel
audience
prep_area
alley
```

禁止在测试中重新手写四组替代故事。禁止只用一个枪管案例冒充四组覆盖。

### 4.2 结果必须由 runner 计算

保留或重构 `GoldenStructuralResult` 均可，但六个结果不得由调用者作为可信布尔值
传入。至少提供公开的实际运行 API，例如：

```python
run_structural_case(...)
run_structural_suite(...)
```

API 名称可以不同，但必须满足：

- 输入是 artifact、不可变 case expectation/manifest 和必要 authority；
- 输出是不可变结果及结构化 diagnostics；
- `all_valid` 由各计算结果派生；
- 调用者不能通过传六个 `True` 获得通过；
- 缺文件、空文本、解析失败、未知 case、重复 section、缺 section 均失败关闭；
- 相同输入产生字节级或值级相同结果；
- 不调用任何 LLM、网络、媒体解析或外部生成服务。

### 4.3 必须实际计算的六类结果

`format_valid`

- Storyboard 和 Video 的必填 section 存在且顺序正确；
- 不接受重复、伪造、空 section；
- 区分 Storyboard 与 Video 的格式职责；
- 不能只做 `substring in text` 的单一哨兵检查。

`timing_valid`

- 从 artifact 中解析显示时间、区间与保持状态；
- 与 canonical segment bounds 和每秒状态数量一致；
- 检出缺秒、重复秒、倒序、越界、错误持续时间和被压缩的 HOLD；
- 12 秒片段最后状态为 11s 时仍必须确认总时长为 12s。

`cuts_valid`

- 解析并验证内部 Boundary；
- 枪管、备赛区无内部切镜；
- 观众席切点为 3s、8s；
- 窄巷切点为 5s、9s；
- 检出缺切、增切、切点移动和把连续运镜误判为切镜。

`responsibilities_valid`

- 上传参考与职责一对一；
- 无重复 reference ID、无孤立职责、无缺失职责；
- 检出角色参考被当成场景、故事板职责被改写或 reference 被替换。

`forbidden_routes_valid`

- `@禁止` 内容存在并可追溯；
- 路由标记与 contract/expectation 一致；
- 检出删除禁止项、修改禁止语义、路由缺失、路由被替换；
- 禁止项不能因模型 token 风险进入正向创意正文。

`homology_valid`

- Storyboard 与 Video 属于同一 case 和同一 canonical contract；
- Storyboard 状态是 Video 完整时间线的合法投影，而不是另一份创意；
- phase 顺序、关键状态、起幅/过程/落幅、边界和共享锚一致；
- 检出跨场景错配、节点顺序变化、语义锚替换和 topology 分叉。

### 4.4 固定 expectation 与哈希

若使用 manifest，manifest 不得存储预计算的通过布尔值，只能存储：

- case ID；
- canonical artifact SHA-256；
- segment bounds；
- 期望状态数；
- 期望内部切点；
- reference/职责集合；
- prohibition route；
- 必填 section；
- 与 R1.3 contract/source fingerprint 的绑定。

expected hash 必须作为稳定 fixture 常量存在，不能在断言时从被测 artifact
重新计算并同时当成 expected 值。不得让篡改后的输入重新生成自己的正确答案。

### 4.5 诊断

失败结果必须指出：

```text
case_id
artifact_kind
check/category
machine-readable code
human-readable detail
```

diagnostics 必须不可变、确定性排序，不得用异常信息偶然顺序作为 API。

## 5. 测试矩阵

彻底重写 placeholder 测试。禁止：

- `skipIf`、`skip`、`expectedFailure`；
- 仅检查 dataclass；
- 手工传入六个布尔值；
- 测试内复制生产解析算法；
- monkeypatch runner 直接返回成功；
- 只检查文件存在或字符串长度；
- 在测试运行时重写权威 fixture；
- 捕获所有异常后仍判通过。

至少覆盖：

1. 八个真实 artifact 都被 parser 读取；
2. 四组真实 case 全部有效；
3. 四组各自的时长、状态数和切点被实际计算；
4. reference 与 duty 一对一；
5. prohibition 和 route 被实际解析；
6. Storyboard/Video 同源关系被实际计算；
7. 空 artifact、缺 artifact、未知 case、错误配对失败；
8. section 删除、重复、乱序失败；
9. 时间删除、重复、倒序、越界、时长修改失败；
10. 观众席 3s/8s 和窄巷 5s/9s 任一切点篡改失败；
11. 无切镜案例被注入切镜后失败；
12. duty 删除、重复、错配失败；
13. 禁止项删除或 route 改写失败；
14. Storyboard 与其他场景 Video 交叉配对失败；
15. 任意已绑定 artifact 单字节篡改触发 SHA 或语义失败；
16. expectation/manifest 自身篡改被检测；
17. 相同输入重复运行结果完全一致；
18. runner 源码不导入或调用 Anthropic、OpenAI、Claude、DeepSeek、
    图像/视频解析器或网络库。

测试必须证明每个失败是由生产 runner API 检出，而不是测试自己的辅助断言检出。

## 6. 实施顺序

1. 记录 claim 后基线测试，确认旧测试是假阳性。
2. 先写会失败的新测试/fixture。
3. 实现最小完整 parser、validator、result/diagnostic。
4. 运行 focused test，逐项关闭失败。
5. 检查所有改动都在 R1.4 allowed paths。
6. 运行完整回归。
7. 运行只读 Golden 专家后审。
8. 全部通过后才写 Evidence。
9. 只通过 controller complete 完成。
10. 完成 R1.4 后停止，不 claim R2.1。

## 7. 必跑验证

从 `01_调度器` 运行：

```powershell
python -m pytest mode_p_vnext/tests/test_v8_3_structural_runner.py -q
```

然后运行 R1.3 不漂移门：

```powershell
python -m pytest ..\MODE_P_REDESIGN_PROJECT\vnext_acceptance\test_r1_3_external_acceptance.py -q

python -m pytest -q `
  mode_p_vnext/tests/test_v5_1_storyboard_projection.py `
  mode_p_vnext/tests/test_v5_2_storyboard_renderer.py `
  mode_p_vnext/tests/test_v5_3_video_projection.py `
  mode_p_vnext/tests/test_v5_4_video_renderer.py `
  mode_p_vnext/tests/test_v5_5_capability_adapter.py `
  mode_p_vnext/tests/test_v5_6_payload_compiler.py `
  mode_p_vnext/tests/test_v5_7_payload_manifest.py `
  mode_p_vnext/tests/test_v5_8_dual_output_sync.py

python -m mode_p_vnext.fixtures.r1_3.generate_registry
```

运行前置完整回归：

```powershell
python -m pytest -q `
  mode_p_vnext/tests/test_v0_1_baseline.py `
  mode_p_vnext/tests/test_rebuild_control.py `
  mode_p/test_active_entrypoints.py `
  mode_p_vnext/tests/test_v0_5_golden_fixtures.py `
  mode_p_vnext/tests/test_v8_1_golden_registration.py
```

预期前置基线：

```text
R1.3 external gate: 27 passed
R1.3 V5 suite: 70 passed
regression: 120 passed, 325 subtests passed
source_spans.json is reproducible
control audit: 0 issues
production_entry: v4_unchanged
```

测试数量可以因 R1.4 新增真实测试而增加，但不得减少现有计数或通过删除测试获得
绿色。

## 8. Golden 专家后审

测试全绿后，再调用同一个只读
`mode-p-vnext-golden-prompt-auditor`。仍只给最小任务包，并额外提供：

- 修改后的 `structural_runner.py`；
- 修改后的 `test_v8_3_structural_runner.py`；
- 新增的 `fixtures/r1_4/**`；
- focused test 和全部回归的完整结果；
- changed path 列表；
- R1.3 外部门控当前 SHA-256；
- 当前 controller audit/status。

后审必须逐项回答：

- 是否解析了真实 artifact；
- 是否由 runner 计算结果；
- 是否存在调用者提供布尔值的捷径；
- 是否存在 vacuous/tautological test；
- 是否覆盖四组 case 和八个 artifact；
- 篡改测试是否经过生产 API；
- 是否修改了 R1.3 或更早的哈希绑定文件；
- 是否越过 R1.4 scope；
- 是否可以裁定 `READY`。

只有实际 `resolvedModel=deepseek-v4-pro` 且结论为 `READY` 才可继续。

## 9. Evidence 与 controller complete

仅在上述全部通过后写：

```text
MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/R1.4.json
```

Evidence 必须至少包含：

- `task_id: R1.4`；
- 唯一 changed paths；
- 三个 required check：
  - `runner_parses_artifacts`
  - `runner_computes_results`
  - `tamper_detection`
- 每个 check 的 `exit_code: 0` 和具体测试证据；
- 四组/八 artifact 覆盖统计；
- mutation matrix 统计；
- focused、R1.3、完整回归结果；
- pre/post expert 实际 resolvedModel 与裁定；
- R1.3 Evidence 和锁定外部门控哈希未变；
- `production_entry=v4_unchanged`；
- `.claude/settings.local.json=ABSENT`。

Evidence 不是完成权威。使用当前 claim 的 owner/token 调用：

```powershell
python -m mode_p_vnext.rebuild_control complete R1.4 `
  --owner <owner> `
  --token <private-token> `
  --evidence ..\MODE_P_REDESIGN_PROJECT\vnext_repair_evidence\R1.4.json
```

控制器必须亲自重新执行注册表中的
`r1_4_structural_runner_suite`。不要伪造 verification result。

完成后再次运行：

```powershell
python -m mode_p_vnext.rebuild_control audit
python -m mode_p_vnext.rebuild_control status
```

必须满足：

```text
audit issues = 0
completed_tasks contains R1.4
current_task = null
current_owner = null
lock_token = null
next_task = R2.1
production_entry = v4_unchanged
```

不要启动 R2.1。

## 10. 中断与失败

如果只是单次回复容量不足，但 claim 仍由当前 owner 有效持有：

- 不重新 claim；
- 不 recover；
- 不 invalidate；
- 不写完成 Evidence；
- 不 complete；
- 返回精确 checkpoint，并要求在同一父会话继续。

如果出现真实 scope blocker、不可满足前置或无法安全继续：

- 写失败证据；
- 通过 `rebuild_control fail` 释放；
- 返回明确 blocker；
- 不手改 lock/state。

## 11. 最终回复格式

成功时只报告可验证事实：

```text
R1.4 COMPLETE
parent_resolved_model: deepseek-v4-pro
pre_expert_resolved_model: deepseek-v4-pro
pre_expert_verdict: ISSUES
post_expert_resolved_model: deepseek-v4-pro
post_expert_verdict: READY
focused_tests: <count> passed
r1_3_external_gate: 27 passed
r1_3_v5_regression: 70 passed
full_regression: 120 passed, 325 subtests passed
controller_audit: 0 issues
evidence_sha256: <hash>
next_task: R2.1
production_entry: v4_unchanged
```

不得输出 token。不得声称已进入 Shadow、Pilot、Canary、Production。
