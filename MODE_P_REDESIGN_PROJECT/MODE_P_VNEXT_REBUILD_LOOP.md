# MODE:P vNext 工程重构执行循环

> 用途：把 `MODE_P_VNEXT_LOOP_SPEC.md` 逐项落实为可执行代码、测试与证据。
>
> 本文件只约束工程重构，不创作分镜，不启动 Director/DP，不调用图像或视频模型，也不切换生产入口。

> **修复闸门（2026-07-22）**：当前状态为`REPAIR_REQUIRED`。必须先完成`MODE_P_VNEXT_LOOP_REPAIR_PLAN.md`和机器修复队列；在控制器输出`V_TASK_REVALIDATION_REQUIRED`前，禁止选择原V0-V10任务或报告`LOCAL_VNEXT_READY`。

---

## 1. 隔离重写，不是双系统共同创作

| 系统 | 入口 | 职责 | 当前状态 |
|---|---|---|---|
| v4 生产创作 | `/mode-p-pilot <script>` | 切换前的当前分集创作与双文件交付 | 只读黑盒基线 |
| vNext 工程重构 | `/mode-p-vnext-rebuild [task_id]` | 每轮实现一个 vNext 工程任务 | 本文件控制 |
| vNext 语义/真实运行验收 | 后续单独入口 | Golden、Shadow、Pilot、Canary | 未授权启动 |

施工期间允许两个目录暂时共存，只为回归、对照和回滚；禁止两个系统在同一次创作中共同工作。vNext 不得导入 v4 模块、知识索引、缓存、Session、delivery 或 fallback。工程重构通过不等于语义验收通过，更不等于允许替换 v4。

最终状态只能有一个活动 MODE:P：vNext 通过全部门并获用户批准后原子接管 `mode_p` 和 `/mode-p-pilot`，v4 转入只读归档包，不继续作为第二活动系统。

---

## 2. 权威文件优先级

发生冲突时按以下顺序裁决：

1. 用户在当前任务中的最新明确指令。
2. `MODE_P_VNEXT_LOOP_SPEC.md`。
3. `MODE_P_VNEXT_OMISSION_AUDIT.md`。
4. `MODE_P_VNEXT_PRODUCTION_AUDIT.md`。
5. `KNOWLEDGE_BASE_AUDIT.md` 与 `GOLDEN_SET_EVIDENCE_REPORT.md`。
6. `MODE_P_VNEXT_IMPLEMENTATION_PLAN.md`。
7. `MODE_P_VNEXT_PROGRESS.md`。
8. 当前 vNext 代码和测试证据。

旧 `CLAUDE_CODE_REBUILD_LOOP.md`、旧 `IMPLEMENTATION_PLAN.md`、旧 `PROGRESS.md` 只代表 v4 历史实施状态，不得作为 vNext 任务源。`legacy_mode_p/` 只能用于反例和兼容性检查。

### 2.1 SD2 专题源集合

下列四个文件共同构成 SD2 视频模型专题的只读权威包，必须作为一个有角色区分的来源家族登记，不能把其中任一文件或派生产物当成全部真相：

1. `03_知识库/sd2_model_capability.md`：模型失败模式与能力边界研究源。
2. `03_知识库/sd2_storyboard_prompt_quality_standard.md`：Storyboard/Video Prompt 写法、冲突和质量候选研究源。
3. `03_知识库/导演手册_视觉叙事决策框架.md`：运镜、构图、光影、切换及跨域裁决研究源。
4. `01_调度器/mode_p/knowledge/core/sd2.md`：由研究源压缩而来的运行时 Core 契约，不是新的独立研究证据。

`sd2_capability_profile.json` 是版本化的当前平台能力、项目限制和账户/画布事实源，不属于研究资料；当时长、分辨率、素材数量、模式或权限与研究文档中的固定数字冲突时，以当前 profile 与画布为准。`knowledge/capsules/` 是场景化派生材料，只能通过来源链复用，不能反向提升为专题研究源。

证据按问题维度裁决：

- 实际生成行为、故事板可预判性和提示词效果：用户明确评价与四组真实 Storyboard—Prompt—Video Golden 证据，高于专题研究中的社区建议或固定写法。
- 当前平台参数与可用模式：当前 `sd2_capability_profile.json` 和画布事实，高于研究文档中的历史数字。
- 导演判断：剧本事实与 Director 的情境判断优先；研究框架提供候选、反例和权衡，不能机械输出镜头答案。
- 来源内部冲突不得由模型静默合并。每条进入运行时的结论必须保留 `source_path`、`source_hash`、`claim_id`、`evidence_tier`、适用条件和不适用条件。

运行时实行按需检索：先由 Scene Diagnosis 形成查询，只加载当前戏剧问题需要的 Core 和少量相关 Claim；禁止整份加载上述研究文档，禁止把它们拼成单次大提示词。工程审计或索引重建可以读取原文，但产物必须是带来源的短记录。

提示词约束采用双域：`HUMAN_VIDEO_PROMPT` 保留完整【禁止】、审计理由与防错信息；`RENDER_PAYLOAD` 只接收目标模型方言允许的可执行描述。编译器依据能力档案和已验证 Golden 规则决定正向闭合、隔离或保留，既不得机械删除禁止事项，也不得把包含风险 token 的人类审核块原样盲目提交。

修复任务的责任边界：R1.1 冻结四文件角色与哈希；R1.2 用 Golden 事实裁决候选规则；R1.3 实现双输出格式和双域编译；R2.3 实现 Diagnosis→Query→Retrieval→Snapshot 的来源追溯与最小加载。四份原文在这些任务中保持只读。

---

## 3. 固定原则

每轮必须保持：

- 当前 v4 只作为黑盒输入/输出与回归基线；不得把其实现细节提升为 vNext 设计依据。
- 当前 v4 入口、Schema、知识索引、缓存、Session 和 delivery 不被 vNext 读取为运行输入或写入。
- 新代码只进入 `01_调度器/mode_p_vnext/`，除非任务明确属于共享只读适配层。
- 算法只处理确定性事实：ID、时间、状态、引用、版本、哈希、路由、覆盖、编码和证据。
- 大模型只负责创意或语义审查；工程 Rebuild 本身不得调用创意 Agent。
- Storyboard 与 Video Prompt 必须由同一 Director Master 派生。
- `HUMAN_VIDEO_PROMPT` 与实际 `RENDER_PAYLOAD` 分域。
- 不可信文本、知识、资产说明和用户纠正必须保留来源与路由，不能变成隐藏系统指令。
- 单次运行只读取当前任务需要的规范章节，禁止把完整知识库或 3000 行 LOOP 全量塞入模型上下文。
- 所有完成声明必须绑定当前代码、当前测试和可复验命令。

---

## 4. 监督锁

### 4.0 机器控制优先

Markdown锁只保留为只读历史摘要。任务选择、独占claim、owner/token、完成证据、恢复、失效回开和机器状态必须由以下命令控制：

~~~text
cd 01_调度器
python -m mode_p_vnext.rebuild_control audit
python -m mode_p_vnext.rebuild_control status
python -m mode_p_vnext.rebuild_control next
python -m mode_p_vnext.rebuild_control claim <task_id> --owner <run_id>
python -m mode_p_vnext.rebuild_control complete <task_id> --owner <run_id> --token <token> --evidence <path>
python -m mode_p_vnext.rebuild_control fail <task_id> --owner <run_id> --token <token> --evidence <path>
python -m mode_p_vnext.rebuild_control recover
python -m mode_p_vnext.rebuild_control invalidate <task_id> --owner <audit-run-id> --reason <reason>
~~~

禁止大模型直接把任务勾为完成、直接写`MODE_P_VNEXT_REBUILD_STATE.json`或创建/删除`MODE_P_VNEXT_REBUILD.lock.json`。修复队列的机器真源是`MODE_P_VNEXT_REPAIR_TASKS.json`和`MODE_P_VNEXT_REBUILD_STATE.json`。

实际独占锁是控制器原子创建的`MODE_P_REDESIGN_PROJECT/MODE_P_VNEXT_REBUILD.lock.json`。`MODE_P_VNEXT_SUPERVISION.lock`不得再由执行模型写入、接管或作为状态真源。一轮只有成功的`claim`可以进入`IN_PROGRESS`；成功、失败和崩溃恢复分别只能通过`complete`、`fail`和`recover`释放实际锁。完成后发现 Evidence 或绑定产物漂移时，只能用`invalidate`留下审计轨迹并回开任务。

---

## 5. 单轮状态机

~~~text
CONTROL_AUDIT
  -> CONTROL_STATUS
  -> CONTROL_NEXT
  -> CONTROL_CLAIM
  -> LOAD_MINIMUM_AUTHORITY
  -> INSPECT_ACTIVE_FILES
  -> IMPLEMENT_SMALLEST_COMPLETE_BEHAVIOR
  -> ADD_OR_UPDATE_TESTS
  -> RUN_FOCUSED_TESTS
  -> RUN_REQUIRED_REGRESSION
  -> VERIFY_V4_ISOLATION
  -> WRITE_EVIDENCE_SUMMARY
  -> CONTROL_COMPLETE_RUNS_VERIFICATION_COMMANDS
  -> POST_COMPLETE_AUDIT
  -> STOP
~~~

失败路径只能进入`rebuild_control fail`；锁状态不一致只能进入`recover`；已完成任务的 Evidence 或`artifact_hashes`失效只能进入`invalidate`。每轮只完成一个任务。`/loop`只负责重复调用单轮状态机，不允许一轮跨越多个任务、多个 Phase 或生产切换门。

---

## 6. 任务选择

任务选择只有一个来源：`rebuild_control next`。用户提供的 task_id 只能用于确认它与`next`返回的唯一 task_id 完全相同，不能覆盖依赖顺序。`status`用于观察，Markdown Progress 和复选框均无选任务权限。若`audit`报告已完成任务的 Evidence 或产物漂移，先用`invalidate`回开该任务，再重新执行`next`和`claim`。所有 R 任务完成后，控制器只进入`V_TASK_REVALIDATION_REQUIRED`，不得直接进入 Local Completion。

不得选择：

- 只改说明、没有行为或可执行证据的伪任务。
- 前置 Schema 尚未冻结的下游编译器任务。
- 需要用户产品决策但尚无明确答案的任务。
- 直接覆盖 v4 活动入口的任务。
- 自动执行 Golden 实模、外部视频生成或生产切换的任务。

---

## 7. 最小上下文加载

### 每轮固定读取

- 本文件。
- `rebuild_control status`与`next`返回的当前机器任务。
- 当前任务的`spec_refs`、`allowed_paths`、`verification_commands`及直接前置 Evidence。

### 按任务读取

- LOOP 中被任务 `spec_refs` 指向的章节。
- 相关 P0/P1 审计项。
- 当前实现文件和对应测试。
- 必要的 Golden 文本夹具、Schema 样例，或 SD2 专题源中按需检索的短段落。

### 禁止默认加载

- 整份知识库正文。
- 整份 SD2 专题研究文档；除非当前任务明确是离线来源审计或索引重建。
- 全部 Golden 图片和视频。
- 旧 v4 实施计划全文。
- 无关历史输出和 Session。
- Director/DP 的隐式推理或旧反馈。

若所需上下文无法在预算内完整加载，必须拆任务或阻断；不得静默截断。

---

## 8. 单任务执行契约

每个任务开始前必须确认：

- `task_id` 唯一。
- 所有 `depends_on` 已有有效证据。
- `allowed_paths` 与 `forbidden_paths` 明确。
- 验收命令可在本机运行。
- 不需要未获授权的外部服务。

实施时：

1. 先写失败测试或可复验夹具。
2. 实现最小完整行为。
3. 不顺手重构无关模块。
4. 不用大模型生成确定性数据。
5. 不把规范文字复制成运行时大提示词。
6. 不为通过测试改变创意语义。

完成必须同时满足：

- 聚焦测试通过。
- 任务声明的回归通过。
- v4 隔离检查通过。
- 文档与实际入口一致。
- Evidence JSON记录变更路径和开发期检查结果。
- `complete`实际执行机器任务图中的`verification_commands`并记录`verification_results`、Evidence hash与`artifact_hashes`。
- 完成后的`audit`为全绿，实际锁已由控制器释放。

---

## 9. 测试分层

按受影响边界选择：

1. Schema 单元测试。
2. Canonical Serialization 字节黄金测试。
3. 编译器黄金文本测试。
4. 状态机与批准失效测试。
5. 安全、提示注入和项目隔离测试。
6. vNext 垂直集成测试。
7. v4 兼容与隔离回归。
8. Golden Set 结构验收。
9. Shadow/真实模型验收，仅在用户显式授权的独立入口运行。

任何任务修改共享依赖、根入口或通用资产索引时，必须运行完整 v4 回归。只修改 vNext 私有文件时，至少运行 vNext 聚焦测试和 v4 活动入口/隔离测试。

---

## 10. 允许的状态

机器状态文件的工程状态只能由控制器写入；Markdown Progress 只是派生视图。面向整个重构/发布流程允许的状态词为：

- `READY_TO_START`
- `IN_PROGRESS`
- `BLOCKED`
- `LOCAL_VNEXT_READY`
- `SHADOW_READY`
- `PILOT_READY`
- `CANARY_READY`
- `PRODUCTION_APPROVAL_REQUIRED`

Rebuild 最多推进到 `LOCAL_VNEXT_READY`。后续状态只能由独立验收流程和用户明确批准推进。

---

## 11. 阻断与失败

只有以下情况可以 `BLOCKED`：

- 缺少用户必须决定的产品语义。
- 权限、依赖或必需资产不可用。
- 同一锁冲突无法安全恢复。
- 规范存在会导致不同数据结构的真实矛盾。
- 外部模型/平台能力必须实测但尚未授权。

阻断记录必须包含：

~~~text
task_id
blocking_condition
evidence
attempted_safe_repairs
required_user_or_external_action
resume_from
~~~

测试失败、实现困难或文件较多不是阻断；保持任务 `IN_PROGRESS` 或记录失败后释放锁，下一轮继续同一任务。

---

## 12. Local Completion Audit

所有实施任务完成后，单独一轮执行：

1. 确认计划无未完成或证据失效任务。
2. 验证 vNext 活动入口只引用 vNext 模块。
3. 验证切换前 v4 活动入口未被替换，且 vNext 没有导入或回退到 v4。
4. 运行 vNext 全量测试。
5. 运行 v4 完整回归。
6. 运行 Legacy/V4/vNext 交叉污染扫描。
7. 验证所有 Schema、Manifest 和 Canonical JSON 版本。
8. 验证 Golden Set 结构夹具，但不调用真实模型。
9. 通过 Evidence 调用`complete`，由控制器更新状态并释放锁；不得手改 Progress 或锁。

通过后只报告：

~~~text
LOCAL_VNEXT_READY
NEXT_EXPLICIT_STEP: isolated vnext shadow acceptance
PRODUCTION_ENTRY_UNCHANGED
~~~

不得报告“生产完成”“真实视频质量通过”或自动启动 Shadow。

---

## 13. 调用

单轮：

~~~text
/mode-p-vnext-rebuild
~~~

指定任务：

~~~text
/mode-p-vnext-rebuild <exact-next-R-task>
~~~

连续工程循环：

~~~text
/loop 5m /mode-p-vnext-rebuild
~~~

出现 `BLOCKED`、`LOCAL_VNEXT_READY` 或用户要求暂停时停止循环。
