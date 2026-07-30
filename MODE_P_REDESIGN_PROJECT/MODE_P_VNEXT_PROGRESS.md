# MODE:P vNext Rebuild Progress

状态：`REPAIR_REQUIRED`

生产入口：`UNCHANGED — /mode-p-pilot remains v4`

最后更新：`2026-07-23`

> 当前任务与 owner 以 `rebuild_control status` 和 `MODE_P_VNEXT_REBUILD_STATE.json` 为准；此处不重复声明以避免漂移。

---

## 1. 当前结论

- vNext 最终目标、主运行 LOOP、遗漏审计和生产审计已经完成。
- vNext 已存在 127 个 Python 文件和 450 项 pytest + 235 个 subtests，但这些数量不能证明生产行为完成。
- 旧执行循环造成状态漂移：计划、Progress、Lock 和实际代码证据不一致。
- 迁移形态为“隔离重写 → 原子替换”，不是长期双系统并行。
- v4 只允许作为黑盒回归和回滚基线，不得进入 vNext 的知识、缓存、Session、编译或创作上下文。
- 审计时v4曾因项目内机器本地`.claude/settings.local.json`出现`685 passed + 1 failed`；该文件已清除，当前完整回归恢复为`686/686`。
- 旧 `/mode-p-rebuild` 继续服务旧 v4，不是 vNext 任务入口。
- 在 LOOP 修复队列完成前，禁止继续选择 V0-V10 任务，也禁止声称 `LOCAL_VNEXT_READY`。
- 当前唯一合法任务由 `rebuild_control next` 确定；始终以 `MODE_P_VNEXT_REBUILD_STATE.json` 为状态真源。

---

## 2. 权威入口

| 项目 | 路径/命令 |
|---|---|
| 最终运行约束 | `MODE_P_VNEXT_LOOP_SPEC.md` |
| 工程单轮协议 | `MODE_P_VNEXT_REBUILD_LOOP.md` |
| LOOP 修复计划 | `MODE_P_VNEXT_LOOP_REPAIR_PLAN.md` |
| 机器修复队列 | `MODE_P_VNEXT_REPAIR_TASKS.json` |
| 机器状态真源 | `MODE_P_VNEXT_REBUILD_STATE.json` |
| 实施任务队列 | `MODE_P_VNEXT_IMPLEMENTATION_PLAN.md` |
| 监督锁 | `MODE_P_VNEXT_SUPERVISION.lock` |
| 工程命令 | `/mode-p-vnext-rebuild [task_id]` |
| 连续执行 | `/loop 5m /mode-p-vnext-rebuild` |

---

## 3. 审计后基线证据

~~~text
2026-07-22
python -m unittest discover -q
cwd: D:\tsc\导演系统_v5\01_调度器\mode_p
result before vNext rebuild scaffold: Ran 685 tests — OK
result after uncontrolled loop execution: Ran 686 tests — 1 failure
failure: .claude/settings.local.json must not be packaged in project workspace
result after repair cleanup: Ran 686 tests — OK
hidden Windows decode thread errors: none on final rerun
~~~

该证据只证明当前 v4 基线绿色，不证明 vNext 已实现。

---

## 4. 当前状态权威来源

当前状态一律以 `rebuild_control status`、`rebuild_control next` 及 `MODE_P_VNEXT_REBUILD_STATE.json` 为准，本节不再重复声明可能漂移的当前任务/owner/目标。

---

## 5. 历史完成记录（待重验，不是当前状态真源）

以下记录由旧 Markdown 驱动 LOOP 产生。只有11项留下完整记录（V0.1–V1.6），而实施计划曾有65项被勾选；在机器控制面完成逐项迁移前，统一视为 `IMPLEMENTED_UNVERIFIED`。

### V1.6 Structured Handoff Contract

~~~text
task_id: V1.6
status: completed
changed_paths:
  - 01_调度器/mode_p_vnext/schema/handoff.py
  - 01_调度器/mode_p_vnext/tests/test_v1_6_handoff.py
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_PROGRESS.md
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_SUPERVISION.lock
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_IMPLEMENTATION_PLAN.md
spec_refs: LOOP §7.10a; Omission P0-10
focused_test_command: cd 01_调度器/mode_p_vnext && python -m pytest tests/test_v1_6_handoff.py -v
focused_test_result: 12 passed in 0.02s
regression_command: cd 01_调度器/mode_p_vnext && python -m pytest tests/ -q
regression_result: 216 passed, 150 subtests passed in 0.88s (V0.1–V1.6)
v4_isolation_result: no v4 imports
completed_at: 2026-07-22
next_task: V2.1
~~~

### V1.5 Fact Coverage Checker

~~~text
task_id: V1.5
status: completed
changed_paths:
  - 01_调度器/mode_p_vnext/fact_coverage.py
  - 01_调度器/mode_p_vnext/tests/test_v1_5_fact_coverage.py
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_PROGRESS.md
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_SUPERVISION.lock
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_IMPLEMENTATION_PLAN.md
spec_refs: LOOP §7.9, §12.8
focused_test_command: cd 01_调度器/mode_p_vnext && python -m pytest tests/test_v1_5_fact_coverage.py -v
focused_test_result: 11 passed in 0.02s
regression_command: cd 01_调度器/mode_p_vnext && python -m pytest tests/ -q
regression_result: 204 passed, 150 subtests passed in 0.84s (V0.1–V1.5)
v4_isolation_result: no v4 imports
completed_at: 2026-07-22
next_task: V1.6
~~~

### V1.4 Fact Registry Schema

~~~text
task_id: V1.4
status: completed
changed_paths:
  - 01_调度器/mode_p_vnext/schema/fact_registry.py
  - 01_调度器/mode_p_vnext/tests/test_v1_4_fact_registry.py
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_PROGRESS.md
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_SUPERVISION.lock
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_IMPLEMENTATION_PLAN.md
spec_refs: LOOP §7.9, §9 Step 1; Omission P0-10
focused_test_command: cd 01_调度器/mode_p_vnext && python -m pytest tests/test_v1_4_fact_registry.py -v
focused_test_result: 24 passed in 0.03s
regression_command: cd 01_调度器/mode_p_vnext && python -m pytest tests/ -q
regression_result: 193 passed, 150 subtests passed in 0.84s (V0.1–V1.4)
v4_isolation_result: no v4 imports
completed_at: 2026-07-22
next_task: V1.5
~~~

### V1.3 Boundary Ownership & HOLD

~~~text
task_id: V1.3
status: completed
changed_paths:
  - 01_调度器/mode_p_vnext/schema/boundary.py
  - 01_调度器/mode_p_vnext/tests/test_v1_3_boundary_hold.py
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_PROGRESS.md
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_SUPERVISION.lock
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_IMPLEMENTATION_PLAN.md
spec_refs: LOOP §7.4, §10.2
focused_test_command: cd 01_调度器/mode_p_vnext && python -m pytest tests/test_v1_3_boundary_hold.py -v
focused_test_result: 18 passed in 0.03s
regression_command: cd 01_调度器/mode_p_vnext && python -m pytest tests/ -q
regression_result: 169 passed, 150 subtests passed in 0.82s (V0.1–V1.3)
v4_isolation_result: no v4 imports
completed_at: 2026-07-22
next_task: V1.4
~~~

### V1.2 Timeline Validator/Compiler

~~~text
task_id: V1.2
status: completed
changed_paths:
  - 01_调度器/mode_p_vnext/timeline_validator.py
  - 01_调度器/mode_p_vnext/tests/test_v1_2_timeline_validator.py
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_PROGRESS.md
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_SUPERVISION.lock
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_IMPLEMENTATION_PLAN.md
spec_refs: LOOP §7.2a, §12.8
focused_test_command: cd 01_调度器/mode_p_vnext && python -m pytest tests/test_v1_2_timeline_validator.py -v
focused_test_result: 25 passed in 0.03s
regression_command: cd 01_调度器/mode_p_vnext && python -m pytest tests/ -q
regression_result: 151 passed, 150 subtests passed in 0.83s (V0.1–V1.2)
v4_isolation_result: no v4 imports
completed_at: 2026-07-22
next_task: V1.3
~~~

### V1.1 Canonical Timeline Schema

~~~text
task_id: V1.1
status: completed
changed_paths:
  - 01_调度器/mode_p_vnext/schema/canonical_timeline.py
  - 01_调度器/mode_p_vnext/tests/test_v1_1_timeline_schema.py
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_PROGRESS.md
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_SUPERVISION.lock
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_IMPLEMENTATION_PLAN.md
spec_refs: LOOP §7.2a, §10.2; Omission P0-08
focused_test_command: cd 01_调度器/mode_p_vnext && python -m pytest tests/test_v1_1_timeline_schema.py -v
focused_test_result: 33 passed in 0.04s
regression_command: cd 01_调度器/mode_p_vnext && python -m pytest tests/ -q
regression_result: 126 passed, 150 subtests passed in 0.82s (V0.1–V1.1)
v4_isolation_result: no v4 imports; schema uses only stdlib dataclasses
completed_at: 2026-07-22
next_task: V1.2
~~~


~~~text
task_id: V0.5
status: completed
changed_paths:
  - 01_调度器/mode_p_vnext/golden_fixture_registry.py
  - 01_调度器/mode_p_vnext/tests/test_v0_5_golden_fixtures.py
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_PROGRESS.md
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_SUPERVISION.lock
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_IMPLEMENTATION_PLAN.md
spec_refs: LOOP §5, §13; Golden Evidence Report
focused_test_command: cd 01_调度器/mode_p_vnext && python -m pytest tests/test_v0_5_golden_fixtures.py -v
focused_test_result: 22 passed, 40 subtests passed in 0.04s
regression_command: cd 01_调度器/mode_p_vnext && python -m pytest tests/ -v
regression_result: 93 passed, 150 subtests passed in 0.77s (V0.1–V0.5)
v4_isolation_result: registry is text-only — no media binary loading, no v4 imports
completed_at: 2026-07-22
next_task: V1.1
~~~

### V0.4 v4/vNext 污染扫描器

~~~text
task_id: V0.4
status: completed
changed_paths:
  - 01_调度器/mode_p_vnext/contamination_scanner.py
  - 01_调度器/mode_p_vnext/tests/test_v0_4_contamination.py
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_PROGRESS.md
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_SUPERVISION.lock
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_IMPLEMENTATION_PLAN.md
spec_refs: LOOP §15.1, §24, §27
focused_test_command: cd 01_调度器/mode_p_vnext && python -m pytest tests/test_v0_4_contamination.py -v
focused_test_result: 19 passed in 0.07s
regression_command: cd 01_调度器/mode_p_vnext && python -m pytest tests/ -v
regression_result: 71 passed, 110 subtests passed in 0.75s (V0.1–V0.4)
v4_isolation_result: scan_v4_for_vnext_imports() returns 0 violations; no v4 files import vNext
completed_at: 2026-07-22
next_task: V0.5
~~~

### V0.3 Canonical Serialization 基础层

~~~text
task_id: V0.3
status: completed
changed_paths:
  - 01_调度器/mode_p_vnext/canonical_serialization.py
  - 01_调度器/mode_p_vnext/tests/test_v0_3_canonical.py
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_PROGRESS.md
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_SUPERVISION.lock
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_IMPLEMENTATION_PLAN.md
spec_refs: LOOP §21.2; Omission P1-15
focused_test_command: cd 01_调度器/mode_p_vnext && python -m pytest tests/test_v0_3_canonical.py -v
focused_test_result: 24 passed in 0.03s
regression_command: cd 01_调度器/mode_p_vnext && python -m pytest tests/ -v
regression_result: 52 passed, 110 subtests passed in 0.69s (V0.1–V0.3)
v4_isolation_result: no v4 imports in canonical_serialization.py; v4 isolation guard unaffected
completed_at: 2026-07-22
next_task: V0.4
~~~

### V0.2 建立 vNext 包骨架

~~~text
task_id: V0.2
status: completed
changed_paths:
  - 01_调度器/mode_p_vnext/__init__.py
  - 01_调度器/mode_p_vnext/version.py
  - 01_调度器/mode_p_vnext/schema/__init__.py
  - 01_调度器/mode_p_vnext/fixtures/__init__.py
  - 01_调度器/mode_p_vnext/tests/test_v0_2_skeleton.py
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_PROGRESS.md
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_SUPERVISION.lock
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_IMPLEMENTATION_PLAN.md
spec_refs: LOOP §15.1, §21
focused_test_command: cd 01_调度器/mode_p_vnext && python -m pytest tests/test_v0_2_skeleton.py -v
focused_test_result: 15 passed in 0.03s
regression_command: cd 01_调度器/mode_p_vnext && python -m pytest tests/ -v
regression_result: 28 passed, 110 subtests passed in 0.68s (V0.1 + V0.2)
v4_isolation_result: V4IsolationTests all passed — no mode_p creative imports detected; __init__.py guard active
completed_at: 2026-07-22
next_task: V0.3
~~~

### V0.1 冻结基线清单

~~~text
task_id: V0.1
status: completed
changed_paths:
  - MODE_P_REDESIGN_PROJECT/vnext_baseline/V0.1_FREEZE_MANIFEST.json
  - 01_调度器/mode_p_vnext/tests/test_v0_1_baseline.py
  - 01_调度器/mode_p_vnext/tests/__init__.py
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_PROGRESS.md
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_SUPERVISION.lock
  - MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_IMPLEMENTATION_PLAN.md
spec_refs: LOOP §4, §15.1; Audit P0-12/P1-14
focused_test_command: cd 01_调度器/mode_p_vnext && python -m pytest tests/test_v0_1_baseline.py -v
focused_test_result: 13 passed, 110 subtests passed in 0.66s
regression_command: cd 01_调度器/mode_p && python -m pytest -q
regression_result: 685 passed, 1 failed (pre-existing environment: settings.local.json exists; untracked)
v4_isolation_result: no v4 imports or fallback in vNext baseline. Manifest records v4 as read-only black-box only.
completed_at: 2026-07-22
next_task: V0.2
~~~

工程执行桥接层已通过以下非任务初始化验证：

~~~text
plan graph: 70 unique task IDs; no missing or forward dependencies
entry/residue focused tests: 26 passed
legacy residue scan: no findings
full repository regression: 686 passed
v4/vNext Python import scan: no v4 import or fallback in mode_p_vnext
~~~

---

## 6. 阻断

当前无阻断。

---

## 7. 下一轮选择规则

1. 如果当前任务为 `IN_PROGRESS` 且 owner 合法，继续当前任务。
2. 否则选择实施计划中第一个前置条件全部完成的 `[ ]` 任务。
3. 不得读取旧 `IMPLEMENTATION_PLAN.md` 推断 vNext 任务。
4. 不得自动开始 Shadow、Pilot、Canary 或真实模型验收。

---

## 8. 完成状态模板

每个任务完成后追加：

~~~text
task_id:
status: completed
changed_paths:
spec_refs:
focused_test_command:
focused_test_result:
regression_command:
regression_result:
v4_isolation_result:
completed_at:
next_task:
~~~
