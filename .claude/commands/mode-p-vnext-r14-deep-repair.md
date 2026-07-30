---
description: Rebase the MODE:P vNext control authority and repair R1.4 against the complete Codex deep-audit gates without entering R2.1.
---

# MODE:P vNext R1.4 深审计修复（DeepSeek 强边界）

本命令处理两个不可拆分的阻断项：

1. R0 controller 没有锁定/执行 R1.4 外部验收，也不检测未申报改动；
2. R1.4 structural runner 主要依赖 artifact SHA，六类结构 category 不完整。

只在两层全部通过后恢复 R1.4 完成状态。不得进入 R2.1。

## 0. 唯一事实来源

先完整读取：

```text
MODE_P_REDESIGN_PROJECT/R1_4_DEEP_AUDIT_2026-07-26.md
.claude/commands/mode-p-vnext-r14-structural-runner.md
MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_REPAIR_TASKS.json
MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_REBUILD_STATE.json
MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/R1.4.json
01_调度器/mode_p_vnext/rebuild_control.py
01_调度器/mode_p_vnext/tests/test_rebuild_control.py
01_调度器/mode_p_vnext/structural_runner.py
01_调度器/mode_p_vnext/fixtures/r1_4/golden_expectations.py
01_调度器/mode_p_vnext/tests/test_v8_3_structural_runner.py
01_调度器/mode_p_vnext/fixtures/r1_3/golden_cases.py
01_调度器/mode_p_vnext/storyboard_projection.py
```

当前必须复现：

```text
worker R1.4: 47 passed
first R1.4 gate: 14 passed, 4 subtests passed
deep R1.4 gate: 23 failed
control binding gate: 5 failed, 1 passed, 2 subtests passed
R1.3 gate: 27 passed
V5: 70 passed
baseline: 120 passed, 325 subtests passed
controller audit: 0 issues
state next_task: R2.1
```

如果实际结果不同，停止，不 claim，不修改，输出 `R14_PREFLIGHT_DRIFT`。

## 1. DeepSeek 模型和五类只读专家

父会话实际 `resolvedModel` 必须为 `deepseek-v4-pro`。父会话是唯一写入者、唯一
controller owner/token 持有者。专家只能 Read/Glob/Grep 和运行只读检查；不得
Write/Edit、claim/complete/fail/invalidate、创建 Evidence、读取或输出 token。

依次激活五类专家：

### E1 Control Authority Expert

只读：

```text
rebuild_control.py
test_rebuild_control.py
MODE_P_VNEXT_REPAIR_TASKS.json
MODE_P_VNEXT_REBUILD_STATE.json
test_r1_4_control_binding_acceptance.py
```

必须审查：锁定输入、workspace delta、Evidence 信任边界、claim/complete/audit/
fail/recover、路径逃逸、符号链接/Windows reparse point、创建/删除/修改检测。

### E2 Golden Authority Expert

只读：

```text
golden_cases.py
source_spans.json
storyboard_projection.py
golden_expectations.py
R1.3 external gate
R1.4 two structural gates
```

必须审查：四组 contract fingerprint、semantic source SHA、ExpectedNode 权威、
不可自我重算、R1.3 不漂移。

### E3 Structural Parser/Topology Expert

只读：

```text
structural_runner.py
storyboard_renderer.py
video_renderer.py
R1.4 audit report
```

必须审查：strict section AST、timeline grammar、interval、Boundary/HOLD/audio/
transition、phase/shot/motion/description、正向/禁止区域。

### E4 Adversarial Test Expert

只读：

```text
test_v8_3_structural_runner.py
test_r1_4_external_acceptance.py
test_r1_4_adversarial_acceptance.py
test_r1_4_control_binding_acceptance.py
```

必须逐项说明每个 mutation 为什么由生产 API 的哪个 category 拒绝，不能用
artifact hash 代替。

### E5 Scope/Regression Expert

只读：

```text
R0.1-R1.4 machine evidence records
R1.3 bound artifact hashes
active entrypoint tests
production_entry state
```

必须审查：v4 不变、R1.3 不变、无 settings.local.json、无越界改动、fresh
Evidence 和历史 invalidation 轨迹。

五个专家修复前都必须给 `ISSUES` 或列出具体阻断；任何专家在 23/23 失败时给
READY，停止并输出 `EXPERT_FALSE_READY`。

## 2. Codex 锁定工件

以下文件只读，禁止 DeepSeek 修改、复制替代、monkeypatch、skip、xfail：

```text
MODE_P_REDESIGN_PROJECT/vnext_acceptance/test_r1_4_external_acceptance.py
sha256=c4002cb806831f3688e8d2946a3715da653d72df804d0378712ce1e8d7099b42

MODE_P_REDESIGN_PROJECT/vnext_acceptance/test_r1_4_adversarial_acceptance.py
sha256=264c0138832a752d9e21d9baf61f8b56c0315b513adaabc33e397edc007854ed

MODE_P_REDESIGN_PROJECT/vnext_acceptance/test_r1_4_control_binding_acceptance.py
sha256=d1544611ad6bc83153e931170b8f7134b086679f28b74f3f81ea0bed0bd74679

MODE_P_REDESIGN_PROJECT/vnext_acceptance/test_r1_3_external_acceptance.py
sha256=de251e5dd97cc7b03b3ae27619f01e2587ce69efe23971a803e61d07fccc47cd

MODE_P_REDESIGN_PROJECT/R1_4_DEEP_AUDIT_2026-07-26.md
```

执行前后都重新计算前三个 Python gate 的 SHA。任一不符立即停止并输出
`LOCKED_GATE_DRIFT`。

## 3. 为什么不能只 invalidate R1.4

R1.4 task registry 只执行 worker-owned suite，且 registry/rebuild controller
本身已被 R0.1 Evidence 绑定。直接编辑 registry 会让 controller audit 报 R0.1
artifact drift；不编辑则外部门控仍不是 machine authority。

因此必须先正式反向失效已完成依赖链，再重建 R0.1 authority，最后顺序重验证。
禁止直接编辑 machine state JSON。

## 4. 阶段 A：控制面 authority rebase

### 4.1 反向失效

在 `D:\tsc\导演系统_v5\01_调度器`，使用一个新的、非空 owner。逐条运行并每步
检查 audit/status：

```powershell
python -m mode_p_vnext.rebuild_control invalidate R1.4 --owner <owner> --reason "Codex deep audit: 23 structural gate failures and unbound controller gates"
python -m mode_p_vnext.rebuild_control invalidate R1.3 --owner <owner> --reason "Dependency revalidation required by R0 authority rebase"
python -m mode_p_vnext.rebuild_control invalidate R1.2 --owner <owner> --reason "Dependency revalidation required by R0 authority rebase"
python -m mode_p_vnext.rebuild_control invalidate R1.1 --owner <owner> --reason "Dependency revalidation required by R0 authority rebase"
python -m mode_p_vnext.rebuild_control invalidate R0.3 --owner <owner> --reason "Dependency revalidation required by R0 authority rebase"
python -m mode_p_vnext.rebuild_control invalidate R0.2 --owner <owner> --reason "Dependency revalidation required by R0 authority rebase"
python -m mode_p_vnext.rebuild_control invalidate R0.1 --owner <owner> --reason "Controller must bind locked verification inputs and actual workspace delta"
```

必须看到：

```text
completed_tasks=[]
next_task=R0.1
current_owner=null
lock_token=null
audit=0 issues
```

任一步失败停止，不手改 state。

### 4.2 claim R0.1

```powershell
python -m mode_p_vnext.rebuild_control claim R0.1 --owner <owner>
```

token 只保留在父会话内存，不写文件、不发给专家、不出现在报告。

### 4.3 R0.1 允许修改

仅：

```text
01_调度器/mode_p_vnext/rebuild_control.py
01_调度器/mode_p_vnext/tests/test_rebuild_control.py
MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_REPAIR_TASKS.json
MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/<fresh-R0.1-evidence>.json
controller 自己原子更新的 state/lock
```

禁止修改 v4、R1.1-R1.4 生产文件、任何锁定 gate、R1.3、知识库、媒体、
`.claude/settings.local.json`。

### 4.4 控制器必须实现

#### A. locked verification inputs

Task schema 新增不可变、规范化的：

```json
"locked_verification_inputs": {
  "relative/path.py": "<lowercase sha256>"
}
```

要求：

- 相对路径规范化且 resolve 后仍在 project root；
- 文件必须存在、必须是普通文件；
- 拒绝目录、symlink、junction/reparse point、路径逃逸；
- hash 必须是 64 位小写十六进制；
- locked input 不得匹配该 task 的 worker `allowed_paths`；
- claim、complete、audit 均验证 live hash；
- complete 将实际值写入 state record 的 `verification_input_hashes`；
- drift 后 `audit` 必须失败。

R1.4 固定：

```text
MODE_P_REDESIGN_PROJECT/vnext_acceptance/test_r1_4_external_acceptance.py
c4002cb806831f3688e8d2946a3715da653d72df804d0378712ce1e8d7099b42

MODE_P_REDESIGN_PROJECT/vnext_acceptance/test_r1_4_adversarial_acceptance.py
264c0138832a752d9e21d9baf61f8b56c0315b513adaabc33e397edc007854ed
```

#### B. authoritative R1.4 commands

R1.4 registry 必须由 controller 分别执行并记录：

```text
r1_4_structural_runner_suite
r1_4_external_gate
r1_4_adversarial_gate
```

不得通过 worker test 间接 import 冒充独立门控。

#### C. claim-time workspace manifest

由于当前 Git 没有 commit，不能依赖 `git diff`。controller 必须在 claim 时对
受监管根建立 canonical file manifest，并绑定到 lock/token：

```text
01_调度器/mode_p_vnext/**
01_调度器/mode_p/**
MODE_P_REDESIGN_PROJECT/**
.claude/commands/**
CLAUDE.md
```

确定性排除：

```text
.git/**
**/__pycache__/**
**/.pytest_cache/**
*.pyc
controller state
controller lock
本 claim 的 Evidence
受控 claim manifest 本身
```

complete 前重新扫描，计算 create/modify/delete。每个实际变化必须：

1. 出现在 Evidence declared `changed_paths`；
2. 匹配当前 task `allowed_paths`；
3. resolve 后仍在 root；
4. 不是 symlink/junction/reparse point。

Evidence 可以额外列出本轮未改变但需重新绑定的 task artifact；这些文件仍要
snapshot。Evidence 不得遗漏任何 actual delta。

fail/recover 必须保留可审计失败摘要并原子清理 claim manifest；异常中断不得留下
一个可被下一 claim 误用的 manifest。

#### D. Evidence 权威分层

- `checks` 仍只是完成请求字段，不能代替执行；
- controller 执行结果只存在 machine record；
- Evidence 的 `verification_results` 只能列 registry 中 controller 将执行的命令；
- 手工 R1.3/V5/baseline 结果放 `informational_results`，每项标记
  `authority=manual_untrusted_until_controller_or_supervisor_audit`；
- 不得把手工 exit_code 当 machine authority。

### 4.5 R0.1 行为测试

至少新增：

1. locked input 正确通过；
2. locked input 缺失、hash drift、路径逃逸、worker-writable 均失败；
3. controller 实际执行三个 R1.4 command；
4. state 记录 verification input hashes；
5. claim 后未申报 allowed-file 改动阻止 complete；
6. claim 后 out-of-scope 修改/创建/删除阻止 complete；
7. symlink/junction/reparse point 阻止 complete；
8. cache/state/lock 的受控变化不误报；
9. declared-but-unchanged artifact 可重新绑定；
10. fail/recover 清理 manifest；
11. audit 检出 locked gate post-completion drift；
12. Evidence 手写结果不能进入 controller machine record。

不允许 source-substring 测试代替行为测试。

### 4.6 完成 R0.1 后顺序重验证

R0.1 focused 和控制回归全绿、E1 post-review READY 后，用全新 Evidence complete
R0.1。随后依次：

```text
R0.2
R0.3
R1.1
R1.2
R1.3
```

每个任务都必须：

1. next/status 正确；
2. claim；
3. 不修改已绑定生产 artifact；
4. 运行该 task registry 的真实 verification；
5. 创建新的、唯一 Evidence 文件；
6. declared paths 列出需重新绑定的原 artifact；
7. controller complete；
8. audit 0 issues。

不得复用/覆盖旧 Evidence 内容。不得用批量脚本手改 state。

R1.3 完成后必须再次证明：

```text
R1.3 external: 27 passed
V5: 70 passed
source registry: reproducible
R1.3 bound hashes unchanged
next_task=R1.4
```

## 5. 阶段 B：R1.4 结构修复

### 5.1 claim 和写入边界

claim R1.4 后只允许：

```text
01_调度器/mode_p_vnext/structural_runner.py
01_调度器/mode_p_vnext/tests/test_v8_3_structural_runner.py
01_调度器/mode_p_vnext/fixtures/r1_4/**
MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/<fresh-R1.4-evidence>.json
```

不得修改：

```text
R1.3 golden_cases/source_spans/projection/renderers
三个 Codex R1.4 gate
R1.3 gate
rebuild_control/task registry（阶段 A 完成后已锁定）
v4/legacy/knowledge/media
machine state/lock（controller 除外）
```

### 5.2 expectation authority

`CaseExpectation` 必须固定并纳入 authority fingerprint：

```text
case_id / segment_id
segment bounds / ticks_per_second
canonical SB/VP SHA
R1.3 contract fingerprint
semantic_sources_sha256
required sections + nonempty policy
Storyboard references
upload image ID→target
target→duty
ExpectedNode topology
prohibition body/route/positive-leak policy
handoff/transition
```

`ExpectedNode` 至少：

```text
node_id
node_type
temporal_kind
start/end
phase_id
sb_node
shot_id
shot_size
camera_motion
description/source fingerprint
relative order
```

权威常量必须来自已锁定 R1.3 contract/source，不得从被测 artifact 动态重算。

公开 `expectation_fingerprint` 必须满足：

```text
public field == recomputed fingerprint == independent authority
```

任一不等令 `integrity_valid=False`。

### 5.3 strict parser

构建 section-aware AST，不得有 silent unmatched：

- 未知 `### @...`；
- 不可解析 bold node；
- 已知 section 空内容；
- duration 存在但不可解析；
- duplicate/forged/out-of-order section；
- timeline node 缺字段；
- 非法 interval/kind；

均产生确定性 format diagnostic。

### 5.4 category 责任

`format_valid`：

- strict allowlist、顺序、唯一、非空、grammar。

`timing_valid`：

- VP panel 精确覆盖 `0..segment_end-1`；
- 缺秒、重复、倒序、负值、`start>=segment_end`；
- interval 有限、`start<=end`、end 不越界；
- HOLD/audio 预期数量、kind、区间；
- boundary/hold/audio/transition 不冒充 panel 秒。

`cuts_valid`：

- Boundary node ID/kind/time/order exact；
- no-cut case 禁止 Boundary；
- 检出连续运镜→切镜和切镜→连续运镜。

`responsibilities_valid`：

- Storyboard refs；
- upload ID→target exact；
- target→duty exact；
- 无 duplicate/orphan/replacement/type rewrite。

`forbidden_routes_valid`：

- canonical prohibition body/source/route；
- 删除、改写、增补、route 替换；
- 对正向 section 做结构化泄漏检测；
- 不得全局 substring 造成禁止 section 自命中。

`homology_valid`：

- 同 segment/case/contract/source；
- SB 是 VP node topology 的合法投影；
- 每节点 phase/shot/motion/description；
- Boundary/HOLD/audio/transition/handoff；
- 起幅/过程/落幅；
- 缺 VP description 直接失败；
- 禁止空文本、过短包含或单向 weak containment 通过。

artifact hash 仍可作为 `integrity_valid`，但不能替代上述 category。

### 5.5 worker 测试必须修复

删除替代性测试模式：

- 字符串长度冒充 parser；
- OOB 冒充 reversal；
- canonical success 导致空 diagnostics 循环；
- 只检查 hash diagnostic；
- 只钉 gun barrel hash。

worker tests 必须包含外部门控等价或更强的生产 API mutation，但不得复制一套生产
parser。

## 6. 完整测试顺序

从 `01_调度器`：

```powershell
python -m pytest mode_p_vnext/tests/test_rebuild_control.py -q
python -m pytest mode_p_vnext/tests/test_v8_3_structural_runner.py -q

python -m pytest `
  ..\MODE_P_REDESIGN_PROJECT\vnext_acceptance\test_r1_4_external_acceptance.py `
  -q

python -m pytest `
  ..\MODE_P_REDESIGN_PROJECT\vnext_acceptance\test_r1_4_adversarial_acceptance.py `
  -q

python -m pytest `
  ..\MODE_P_REDESIGN_PROJECT\vnext_acceptance\test_r1_3_external_acceptance.py `
  -q

python -m pytest -q `
  mode_p_vnext/tests/test_v5_1_storyboard_projection.py `
  mode_p_vnext/tests/test_v5_2_storyboard_renderer.py `
  mode_p_vnext/tests/test_v5_3_video_projection.py `
  mode_p_vnext/tests/test_v5_4_video_renderer.py `
  mode_p_vnext/tests/test_v5_5_capability_adapter.py `
  mode_p_vnext/tests/test_v5_6_payload_compiler.py `
  mode_p_vnext/tests/test_v5_7_payload_manifest.py `
  mode_p_vnext/tests/test_v5_8_dual_output_sync.py

python -m pytest -q `
  mode_p_vnext/tests/test_v0_1_baseline.py `
  mode_p_vnext/tests/test_rebuild_control.py `
  mode_p/test_active_entrypoints.py `
  mode_p_vnext/tests/test_v0_5_golden_fixtures.py `
  mode_p_vnext/tests/test_v8_1_golden_registration.py

python -m mode_p_vnext.fixtures.r1_3.generate_registry
python -m compileall -q mode_p_vnext
python -m mode_p_vnext.rebuild_control audit
```

期望：

```text
first R1.4 gate: 14 passed, 4 subtests passed
deep R1.4 gate: 23 passed
R1.3 gate: 27 passed
V5: 70 passed
baseline: 120 passed, 325 subtests passed
registry: reproducible
audit: 0 issues
```

## 7. post experts、Evidence、controller complete

E1–E5 必须分别重新审查并全部 `READY`。任何一个 `ISSUES` 都继续当前 R1.4 claim，
不得写完成 Evidence。

fresh R1.4 Evidence：

- `changed_paths` 包含所有实际 delta 和需绑定 artifact；
- `checks` 三个 required check；
- `verification_results` 只列 controller registry 三个 R1.4 command；
- R1.3/V5/baseline/registry 放 `informational_results` 并标记手工权威等级；
- 记录三个锁定 gate SHA；
- 记录四组 contract/source SHA；
- mutation matrix 逐项是 category 通过，不是 hash 通过；
- pre/post 五专家 model/verdict；
- production entry、settings.local、R1.3 hashes。

然后 controller `complete R1.4`。完成后运行：

```powershell
python -m pytest `
  ..\MODE_P_REDESIGN_PROJECT\vnext_acceptance\test_r1_4_control_binding_acceptance.py `
  -q

python -m mode_p_vnext.rebuild_control audit
python -m mode_p_vnext.rebuild_control status
python -m mode_p_vnext.rebuild_control next
```

必须：

```text
control binding gate: 6 passed, 2 subtests passed
audit: 0 issues
completed_tasks: R0.1-R1.4
current_owner: null
lock_token: null
next_task: R2.1
production_entry: v4_unchanged
```

停止。不得 claim R2.1。

## 8. 禁止捷径

- 不接受 22/23、5/6 或任何 partial pass；
- 不修改锁定 gate 或审计报告；
- 不用 artifact SHA 代替 category；
- 不用测试内 parser/monkeypatch；
- 不删除测试、skip、xfail、expectedFailure；
- 不重算 authority 后同步更新 expected；
- 不修改 R1.3 适配 R1.4；
- 不手改 state、token、lock；
- 不复用旧 Evidence 冒充 fresh run；
- 不把手工 verification 写成 controller 权威；
- 不启用 vNext feature gate；
- 不改 production entry；
- 不进入 Shadow/Pilot/Canary/Production。

## 9. 最终输出

```text
R1.4 DEEP REPAIR COMPLETE
parent_resolved_model: deepseek-v4-pro
E1_control: READY
E2_golden: READY
E3_parser_topology: READY
E4_adversarial: READY
E5_scope_regression: READY
control_tests: <count> passed
worker_tests: <count> passed
r1_4_external_gate: 14 passed, 4 subtests passed
r1_4_deep_gate: 23 passed
r1_4_control_binding_gate: 6 passed, 2 subtests passed
r1_3_external_gate: 27 passed
r1_3_v5_regression: 70 passed
full_regression: 120 passed, 325 subtests passed
source_registry: reproducible
controller_audit: 0 issues
locked_inputs: verified
actual_delta: reconciled
evidence_sha256: <sha256>
next_task: R2.1
production_entry: v4_unchanged
```
