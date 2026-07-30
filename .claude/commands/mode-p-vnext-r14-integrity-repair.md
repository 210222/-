# MODE:P vNext R1.4 完整性修复命令（DeepSeek 强边界）

本命令只修复已经被错误完成的 R1.4，不进入 R2.1。执行者是用户启动的
DeepSeek 父会话；Codex 负责外部门控和事后审计。

## 0. 模型与写入者

父会话实际 `resolvedModel` 必须为 `deepseek-v4-pro`。文本自称不算证明。
不满足时立即停止，不 claim、不写文件。

父会话是唯一写入者、唯一控制 token 持有者。只读 Golden 专家使用
`model: inherit`，实际 `resolvedModel` 也必须为 `deepseek-v4-pro`，且只允许
Read/Glob/Grep；专家不得写文件、运行控制器或持有 token。

一次只运行一个专家，不建立并行写入者。

## 1. Codex 审计事实：必须原样接受

当前 R1.4 虽被 controller 标记完成，官方套件也全部绿色，但生产 API 存在已独立
复现的假阳性：

1. Storyboard 末尾追加一个空格：
   `SB_HASH_MISMATCH` 存在，但 `all_valid=True`。
2. Video Prompt 末尾追加一个换行：
   `VP_HASH_MISMATCH` 存在，但 `all_valid=True`。
3. 交换 Storyboard 的 `[4s]` 与 `[5s]`：
   六个 category 全为 true，`all_valid=True`。
4. 删除 `@禁止` 的全部实际正文，仅保留 `- 【禁止】` 和 route：
   `forbidden_routes_valid=True`，`all_valid=True`。
5. 把“光区外不使用任何补光”改为相反语义：
   `forbidden_routes_valid=True`，`all_valid=True`。
6. 追加一个未知参考图和一条数量匹配的未知职责：
   `responsibilities_valid=True`，`all_valid=True`。
7. 只改 Storyboard 的关键画面语义：
   `homology_valid=True`，`all_valid=True`。
8. 调用者用 `dataclasses.replace` 同时替换 expected hash，可让篡改 artifact
   无诊断通过。

根因包括：

- hash mismatch 只追加 diagnostic，不参与 `all_valid`；
- 时间先排序再检查倒序，倒序分支不可达；
- worker 的 `reversed_times` 测试实际测试 99s 越界；
- SHA 测试只断言 diagnostic 存在，不断言交付被拒绝；
- prohibition parser 只拿到 bullet 首行 `【禁止】`，没有解析多行正文；
- responsibilities 只验证 expected 是 actual 的子集，没有 exact-set equality；
- homology 只比较排序后的时间子集和数量；
- expectation/manifest 没有独立 authority seal；
- Evidence 内 worker test 哈希仍写旧值
  `34f25c...`，实际/controller 绑定值为 `85d13c...`；
- Evidence 的 changed path/cwd 出现错误编码路径，不能作为可解析工件路径。

不得争论这些问题“已有 HASH_MISMATCH 所以算检测成功”。验收定义是失败关闭：
任何完整性、authority 或结构语义失败都必须导致 `all_valid=False`，并且对应语义
category 也必须失败。

## 2. 开始前控制面操作

从 `D:\tsc\导演系统_v5\01_调度器` 运行：

```powershell
python -m mode_p_vnext.rebuild_control audit
python -m mode_p_vnext.rebuild_control status
```

预期初始状态：

```text
audit issues = 0
completed_tasks contains R1.4
next_task = R2.1
current_task/current_owner/lock_token = null
production_entry = v4_unchanged
```

生成唯一 owner：

```text
ds-r14-integrity-<UTC timestamp or UUID>
```

用该 owner 失效 R1.4：

```powershell
python -m mode_p_vnext.rebuild_control invalidate R1.4 `
  --owner <owner> `
  --reason "Codex external audit reproduced fail-open integrity, timing, prohibition, responsibility, homology, expectation-authority, and Evidence inconsistencies"
```

再次 `audit/status/next`，必须看到 `next_task=R1.4`，然后：

```powershell
python -m mode_p_vnext.rebuild_control claim R1.4 --owner <owner>
```

token 只留在父会话内，不输出、不写入文件、不交给专家。

不要 claim R2.1。不要手改 machine state、lock、task registry 或历史 Evidence。

## 3. 允许与禁止路径

仅允许修改：

```text
01_调度器/mode_p_vnext/structural_runner.py
01_调度器/mode_p_vnext/tests/test_v8_3_structural_runner.py
01_调度器/mode_p_vnext/fixtures/r1_4/**
MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/R1.4.json
```

下列由 Codex 锁定，DeepSeek 只读：

```text
MODE_P_REDESIGN_PROJECT/vnext_acceptance/test_r1_4_external_acceptance.py
sha256 = c4002cb806831f3688e8d2946a3715da653d72df804d0378712ce1e8d7099b42

MODE_P_REDESIGN_PROJECT/vnext_acceptance/test_r1_3_external_acceptance.py
sha256 = de251e5dd97cc7b03b3ae27619f01e2587ce69efe23971a803e61d07fccc47cd

.claude/commands/mode-p-vnext-r14-integrity-repair.md
```

禁止修改：

- R1.3 或更早代码、fixture、Evidence；
- `storyboard_projection.py`、`storyboard_renderer.py`；
- `video_projection.py`、`video_renderer.py`；
- schema、capability adapter、payload compiler、payload manifest；
- v4、legacy、知识库、媒体、Session；
- `.claude/settings.local.json`；
- production entry。

不得复制外部门控为 worker 版本后只运行复制品；必须运行原路径。

## 4. 必须实现的生产语义

### 4.1 完整性必须参与批准结果

`SB_HASH_MISMATCH`、`VP_HASH_MISMATCH`、未知 case、被篡改 expectation/manifest
都必须令 `all_valid=False`。

可新增不可变 `integrity_valid`，或以另一个清晰、可审计的失败关闭机制实现；不得
仅依赖 diagnostics 文本。若保留六个结构 category，完整性仍必须是 `all_valid`
的硬门。

### 4.2 expectation authority 不由调用者自证

`run_structural_case` 不得信任调用者传入的任意 `CaseExpectation`。必须有独立固定
authority：

- 已知 case allowlist；
- expectation 的 canonical serialization/fingerprint；
- fingerprint 的独立固定值；
- 空、未知、修改过的 expectation 失败关闭；
- 修改 artifact hash 后再修改 expectation hash 不能重新授权 artifact。

expected 值不得在同一次断言中从被测对象计算。

### 4.3 时间验证使用原始序列

先在 artifact 原始出现顺序上检查，再为集合覆盖另行排序。必须检出：

- 缺秒；
- 重复秒；
- 真倒序；
- 越界；
- duration 不一致；
- HOLD 区间压缩、反向或丢失；
- boundary/cut 的时刻和 node kind 错误。

禁止“先 `sorted()` 再判断 `<`”。

### 4.4 section 顺序是完整序列

Storyboard 和 Video Prompt 都按 required section 的完整固定顺序比较，不是只检查
两三个局部先后关系。缺失、重复、未知、错序均失败关闭。

### 4.5 reference/duty 是 exact one-to-one

验证规范化后的 exact set/multiset equality：

- expected 缺失失败；
- unexpected 新增失败；
- 重复 ref/duty 失败；
- 一图多责、多图一责失败；
- 职责文本被改写失败。

数量相等不是充分条件。

### 4.6 禁止项解析完整正文

解析 `@禁止` 下的整个多行 prohibition block，route 独立解析。固定 expectation
至少包含禁止项的规范化正文 fingerprint 或精确 authority binding。

必须检出：

- 删除任意禁止项或全部正文；
- 把禁止语义改为相反/弱化语义；
- route 缺失、替换、移位；
- prohibition 被移入正向创意正文。

只解析 `- 【禁止】` 这个标题不算解析禁止项。

### 4.7 homology 比较共享契约，不只比较数量

至少比较：

- case/segment identity；
- phase ID 与原始顺序；
- node ID、temporal kind、start/end；
- cut/boundary/hold topology；
- Storyboard 到 Video 的投影关系；
- 关键语义锚或 source fingerprint；
- 起幅、过程、落幅、交接状态。

排序后的时间子集和 panel count 只能是辅助条件，不能单独证明同源。

## 5. 锁定外部门控

先运行当前实现，必须看到外部门控失败；若全绿，停止并报告
`R14_GATE_NOT_EXERCISING_DEFECT`。

```powershell
python -m pytest `
  ..\MODE_P_REDESIGN_PROJECT\vnext_acceptance\test_r1_4_external_acceptance.py `
  -q
```

DeepSeek 不得修改外部门控。修复后必须全部通过。门控覆盖：

- 四组 canonical pair；
- 单字节 SB/VP 篡改；
- forged expectation 和 unknown case；
- 真倒序、重复秒、缺秒；
- section 错序；
- 禁止正文删除和语义反转；
- unexpected reference+duty；
- Storyboard 关键语义和时间 topology 分叉。

worker test 也必须新增等价或更强的生产 API 测试，但外部门控是独立权威。

## 6. 必跑回归

从 `01_调度器` 顺序执行：

```powershell
python -m pytest mode_p_vnext/tests/test_v8_3_structural_runner.py -q

python -m pytest `
  ..\MODE_P_REDESIGN_PROJECT\vnext_acceptance\test_r1_4_external_acceptance.py `
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
python -m mode_p_vnext.rebuild_control audit
```

最低不漂移结果：

```text
R1.3 external gate: 27 passed
R1.3 V5 regression: 70 passed
full regression: 120 passed, 325 subtests passed
source_spans.json is reproducible
controller audit: 0 issues
production_entry: v4_unchanged
```

R1.4 worker 和外部门控必须 100% 通过；不能接受 xfail、skip、删测试或降低断言。

## 7. Golden 专家

修复前和修复后各调用同一个只读 Golden 专家。后审必须逐项回答：

1. hash mismatch 是否令交付失败；
2. expectation 是否有独立 authority；
3. 真倒序/缺秒/重复秒是否由生产 API 检出；
4. section 是否全序验证；
5. responsibility 是否 exact equality；
6. prohibition 是否解析并验证完整正文；
7. homology 是否验证共享契约和语义锚；
8. 外部门控是否原文件、未修改、全绿；
9. R1.3 和 v4 是否未漂移；
10. Evidence 路径和哈希是否与磁盘一致。

任何一项未证明，裁定必须为 `ISSUES`，不得写完成 Evidence。

## 8. Evidence 与 complete

旧 R1.4 Evidence 已失效。新 Evidence 必须使用 UTF-8 正确路径，逐个重新计算并记录
当前真实 artifact SHA-256；不得复制旧的 `34f25c...` test hash。

Evidence 至少记录：

- pre/post expert 实际 resolvedModel 与 verdict；
- changed paths；
- production/worker/external gate 哈希；
- 每条 verification command 的 argv、cwd、exit code、stdout；
- mutation matrix；
- R1.3 Evidence 与外部门控哈希未变；
- `.claude/settings.local.json=ABSENT`；
- `production_entry=v4_unchanged`。

仅当全部门禁通过且 post expert 为 READY 后：

```powershell
python -m mode_p_vnext.rebuild_control complete R1.4 `
  --owner <owner> `
  --token <private-token> `
  --evidence ..\MODE_P_REDESIGN_PROJECT\vnext_repair_evidence\R1.4.json
```

随后再运行 `audit/status`。必须得到 `next_task=R2.1`，但停止，不 claim R2.1。

## 9. 最终回复格式

```text
R1.4 INTEGRITY REPAIR COMPLETE
parent_resolved_model: deepseek-v4-pro
pre_expert_verdict: ISSUES
post_expert_verdict: READY
worker_tests: <count> passed
r1_4_external_gate: <count> passed
r1_3_external_gate: 27 passed
r1_3_v5_regression: 70 passed
full_regression: 120 passed, 325 subtests passed
source_registry: reproducible
controller_audit: 0 issues
evidence_sha256: <hash>
next_task: R2.1
production_entry: v4_unchanged
```

如果失败，保留当前 claim 并返回精确 checkpoint；只有真实不可恢复 blocker 才通过
controller `fail` 释放。不得以回复长度、测试较多或需要机械录入为 blocker。
