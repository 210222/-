# MODE:P vNext R1.4 第二轮对抗修复（DeepSeek 强边界）

> **已废止。** 2026-07-26 深审计发现 23 个结构失败和控制面未绑定问题。
> 不得再执行本文件。唯一替代命令：
> `.claude/commands/mode-p-vnext-r14-deep-repair.md`。

本命令修复 R1.4 第一轮 integrity repair 后仍存在的分类器缺口。只完成 R1.4，
不进入或 claim R2.1。

## 1. 固定执行角色

父会话与 pre/post Golden 专家的实际 `resolvedModel` 必须都是
`deepseek-v4-pro`。父会话是唯一写入者和 token 持有者；专家只读，不能运行
controller、写 Evidence 或持有 token。

## 2. 必须接受的 Codex 复现事实

第一轮锁定门控 14/14 通过，所有 artifact 篡改也已经能通过
`integrity_valid=False` 令 `all_valid=False`。但以下变异仍让负责该问题的
结构 category 返回 true：

1. VP panel `6s→5s`，造成重复 5s 和缺失 6s：
   `timing_valid=True`。
2. HOLD `13s–13s→13s–99s`：
   `timing_valid=True`。
3. HOLD node kind `[保持]→[@音轨]`：
   `homology_valid=True`。
4. audience boundary ID `[cut_3s]→[forged_boundary_id]`：
   `cuts_valid=True` 且 `homology_valid=True`。
5. 删除 VP 0s panel description：
   `homology_valid=True`。
6. upload mapping `@图片2 @rico→@图片2 @evil`，职责行保持不变：
   `responsibilities_valid=True`。
7. 插入 `### @UNKNOWN_INJECT`：
   `format_valid=True`。
8. VP 0s camera motion `前推→横移`：
   `homology_valid=True`。

全局 hash 拒绝不能替代分类器。R1.4 的结构 runner 将来需要诊断非 Golden
artifact；因此必须由对应 category 识别结构语义错误。

## 3. 控制面

从 `D:\tsc\导演系统_v5\01_调度器`：

```powershell
python -m mode_p_vnext.rebuild_control audit
python -m mode_p_vnext.rebuild_control status
```

确认 audit 0 issues、R1.4 已完成、next_task=R2.1、无 owner/token。生成唯一
owner 后失效 R1.4：

```powershell
python -m mode_p_vnext.rebuild_control invalidate R1.4 `
  --owner <owner> `
  --reason "Codex second external audit reproduced VP timing, interval, node-kind, boundary-ID, semantic-anchor, reference-mapping, unknown-section, and camera-motion category gaps"

python -m mode_p_vnext.rebuild_control audit
python -m mode_p_vnext.rebuild_control status
python -m mode_p_vnext.rebuild_control next
```

必须看到 `next_task=R1.4` 后再 claim：

```powershell
python -m mode_p_vnext.rebuild_control claim R1.4 --owner <owner>
```

token 不得写入任何文件或交给专家。

## 4. 路径边界

只允许修改：

```text
01_调度器/mode_p_vnext/structural_runner.py
01_调度器/mode_p_vnext/tests/test_v8_3_structural_runner.py
01_调度器/mode_p_vnext/fixtures/r1_4/**
MODE_P_REDESIGN_PROJECT/vnext_repair_evidence/R1.4.json
```

Codex 锁定、只读：

```text
MODE_P_REDESIGN_PROJECT/vnext_acceptance/test_r1_4_external_acceptance.py
sha256 = c4002cb806831f3688e8d2946a3715da653d72df804d0378712ce1e8d7099b42

MODE_P_REDESIGN_PROJECT/vnext_acceptance/test_r1_4_adversarial_acceptance.py
sha256 = db91f7d0f4152ec60a0de97dd55fdf7adbe17296a3ca210977d372a722d97e5b

MODE_P_REDESIGN_PROJECT/vnext_acceptance/test_r1_3_external_acceptance.py
sha256 = de251e5dd97cc7b03b3ae27619f01e2587ce69efe23971a803e61d07fccc47cd

.claude/commands/mode-p-vnext-r14-adversarial-repair.md
```

禁止修改 R1.3、renderer/projection、schema、v4、legacy、知识库、媒体、task
registry、machine state、旧 Evidence、`.claude/settings.local.json`。

## 5. 必须实现的结构语义

### 5.1 VP 时间与区间

- 对 VP panel 原始序列执行倒序、重复、缺秒和范围验证。
- boundary/hold/audio/transition 不得冒充每秒 panel 覆盖。
- 验证每个 interval 的 start/end：有限数值、`start<=end`、在 segment bounds
  内、符合 expected node kind。
- HOLD 缺失、压缩、扩张或反向必须由 timing/homology 拒绝。

### 5.2 拓扑与 node identity

Golden expectation 必须固定需要比较的 boundary/hold/audio/transition
结构，包括 node ID、temporal kind、start/end 和相对顺序。只比较 cut time 不够。

HOLD 改成 AUDIO、boundary ID 改写、node 类型丢失必须令
`homology_valid=False`；cut boundary ID/类型错误也应令 `cuts_valid=False`
或提供同等明确的 topology category 诊断。

### 5.3 语义锚与运镜

- VP 同时间没有 description 时不能静默跳过。
- 比较共享契约中的关键 description/source fingerprint。
- 比较 phase、shot size、camera motion、起幅/过程/落幅和交接节点。
- 不得仅用包含关系让空文本或过短片段通过。

### 5.4 参考图映射与职责

Expectation 需要固定 upload reference ID→target 和 target→duty 的完整映射。
同时验证：

- reference mapping exact equality；
- duty exact equality；
- ID 唯一；
- target 唯一性策略；
- 一图一责；
- 不允许只改 upload target 而沿用旧 duty。

### 5.5 section allowlist

Parser 必须识别所有 section header，包括未知 `### @...`。format 验证使用
required full order 加 allowlist：

- 缺失、重复、错序失败；
- 未知 section 失败；
- 未知内容不得被并入前后合法 section。

## 6. 两个锁定门控

修复前运行：

```powershell
python -m pytest `
  ..\MODE_P_REDESIGN_PROJECT\vnext_acceptance\test_r1_4_external_acceptance.py `
  -q

python -m pytest `
  ..\MODE_P_REDESIGN_PROJECT\vnext_acceptance\test_r1_4_adversarial_acceptance.py `
  -q
```

预期：第一门 14 通过；第二门当前失败。若第二门修复前全绿，停止并报告门控未
触发已知缺陷。

修复后两个门控必须全部通过，且原文件哈希不变。worker test 必须新增等价或更强
的分类器测试，不能只依赖外部门控。

## 7. 全部回归

```powershell
python -m pytest mode_p_vnext/tests/test_v8_3_structural_runner.py -q

python -m pytest `
  ..\MODE_P_REDESIGN_PROJECT\vnext_acceptance\test_r1_4_external_acceptance.py `
  ..\MODE_P_REDESIGN_PROJECT\vnext_acceptance\test_r1_4_adversarial_acceptance.py `
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

R1.3 external 必须 27，V5 必须 70，baseline 必须 120+325，registry 必须
reproducible，production entry 必须 `v4_unchanged`。

## 8. Evidence 与完成

post Golden 专家必须逐项审查八个新变异，全部证明后才能给 READY。新 Evidence
重新记录所有实际工件哈希、两个 R1.4 外部门控哈希、命令、cwd、输出和 mutation
matrix。不要复制旧 verification text。

只在全部门禁绿色后 controller `complete R1.4`。完成后 audit/status 必须无锁且
next_task=R2.1；停止，不 claim R2.1。

最终报告：

```text
R1.4 ADVERSARIAL REPAIR COMPLETE
parent_resolved_model: deepseek-v4-pro
pre_expert_verdict: ISSUES
post_expert_verdict: READY
worker_tests: <count> passed
r1_4_external_gate: 14 passed
r1_4_adversarial_gate: 8 passed
r1_3_external_gate: 27 passed
r1_3_v5_regression: 70 passed
full_regression: 120 passed, 325 subtests passed
source_registry: reproducible
controller_audit: 0 issues
evidence_sha256: <hash>
next_task: R2.1
production_entry: v4_unchanged
```
