# MODE:P vNext LOOP 修复计划

> 审计日期：2026-07-22
>
> 当前状态：`REPAIR_REQUIRED`
>
> 目标：先恢复可信的工程控制面，再重验现有实现；本计划完成前禁止继续 V0-V10、Shadow、Pilot、Canary 或生产切换。

---

## 1. 已确认的问题

1. 实施计划曾有65/70项勾选，但Progress只有10项完整证据。
2. V10.6在5项未完成、4项存在未完成前置依赖时被提前勾选。
3. Progress同时声明READY_TO_START、V10.6、V0.1 pending和“代码尚未开始”。
4. 文本锁和Markdown复选框由模型直接编辑，无法原子防并发或阻止跳过依赖。
5. vNext测试虽为450 passed + 235 subtests，但多个“完成”模块只是数据类或调用者传入布尔结果。
6. Storyboard/Video Renderer没有复现用户成功样本的完整格式。
7. Golden把备赛区错误描述为“丢失内部切镜”，与原设计的固定单镜头冲突。
8. V0.1仍有13个权威文件hash为null。
9. Shadow、Atomic Commit、Session Lock和Structural Runner没有真实文件系统/执行行为。
10. 项目内机器本地`.claude/settings.local.json`导致v4全量测试失败。

---

## 2. 修复原则

- 保留现有代码，不按勾选状态直接删除或重写。
- 所有原V任务先视为`IMPLEMENTED_UNVERIFIED`，逐项验真后才能迁入`VERIFIED`。
- 机器JSON是任务和状态真源；Markdown只作为人类视图。
- 大模型不得直接修改任务完成状态、锁或完成证据。
- 完成命令必须验证依赖、owner/token、允许路径、测试结果和Evidence hash。
- 修复队列完成前，原V0-V10计划保持暂停。
- v4只做黑盒回归；vNext不得导入v4知识、缓存、Session、delivery或fallback。

---

## 3. 修复阶段

### R0：控制面止血

- **R0.1 确定性控制面验收**：验证机器任务图、状态、原子claim、owner/token、证据门和恢复审计。
- **R0.2 执行入口接管**：`/mode-p-vnext-rebuild`和根`CLAUDE.md`只允许通过控制器选择、claim和complete任务。
- **R0.3 现有状态迁移**：把旧65项声称迁为`IMPLEMENTED_UNVERIFIED`；逐项绑定代码、测试和历史证据，撤销非法完成。

### R1：事实、Golden与输出契约

- **R1.1 基线Manifest修复**：补齐所有权威hash；不可用媒体明确标记missing，不允许以skip代替冻结完成。
- **R1.2 Golden事实修复**：保存四组完整故事板/视频提示词只读夹具，修正备赛区结论，区分用户评价与审计推断。
- **R1.3 双输出格式修复**：完整实现共享视觉锚、编号、阶段、时间节点、箭头、HOLD、音轨、禁止和转场格式。
- **R1.4 Structural Runner实装**：Runner自己读取和解析产物，不接受调用者预先计算的真假值。

### R2：真实运行行为

- **R2.1 文件事务与跨进程锁**：真实staging、manifest、`os.replace`、exclusive create、lease、崩溃和重复提交测试。
- **R2.2 CLI/Session/Shadow实装**：`python -m mode_p_vnext`可运行；Shadow实际生成隔离产物和Manifest，不只是数据类。
- **R2.3 知识与不可信文本链**：把Diagnosis→Query→Retrieval→Snapshot真正接入垂直集成；补Prompt Injection隔离。
- **R2.4 DP对抗与定向修订**：补手机背面泄漏、遮挡、画外、反射、否定词诱导和越权重导演测试。

### R3：发布安全与最终审计

- **R3.1 回滚、Kill Switch与操作文档**：实现封存包、唯一入口原子切换、恢复演练和人工批准边界。
- **R3.2 重新验证原70项与Local Completion Audit**：所有任务Evidence齐全、v4/vNext全绿、Golden格式通过后，控制器才可生成`LOCAL_VNEXT_READY`。

---

## 4. 单轮调用协议

每轮必须执行：

~~~text
python -m mode_p_vnext.rebuild_control audit
python -m mode_p_vnext.rebuild_control next
python -m mode_p_vnext.rebuild_control claim <task_id> --owner <run_id>
  -> 只读取该任务spec_refs和允许路径
  -> 实现与测试
python -m mode_p_vnext.rebuild_control complete <task_id> --owner <run_id> --token <token> --evidence <evidence.json>
~~~

失败时：

~~~text
python -m mode_p_vnext.rebuild_control fail <task_id> --owner <run_id> --token <token> --evidence <evidence.json>
~~~

禁止手工勾选任务或把Lock改成完成。

---

## 5. 修复完成门

只有以下全部成立，才能恢复原V0-V10队列：

- R0-R3全部由控制器标记完成。
- 任务图无重复、缺失、循环或未完成前置依赖。
- 每项修复任务有独立Evidence JSON和内容hash。
- 当前Progress由机器状态派生，不再包含互相矛盾的“当前任务”。
- 13个null authority hash全部处理。
- 四组Golden精确文本夹具存在，备赛区事实正确。
- vNext Renderer与用户成功格式的结构黄金测试通过。
- Structural Runner、Shadow、Atomic Commit和Lock具有真实行为测试。
- V3.7、V6.8、V7.6、V10.4、V10.5实际完成。
- v4完整测试为全绿。
- `LOCAL_VNEXT_READY`只能由控制器生成。

