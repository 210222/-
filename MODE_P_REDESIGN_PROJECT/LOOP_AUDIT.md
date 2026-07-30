# MODE:P v3.0 Loop 审计

审计日期：2026-07-17
结论：`LOCAL_REBUILD_READY`
适用环境：Claude Code + 当前父模型（包括 DeepSeek V4 Pro）

## 1. 审计范围

本轮检查了以下活动边界：

- `LOOP_SPEC.md`、`CLAUDE_CODE_REBUILD_LOOP.md`、`IMPLEMENTATION_PLAN.md`、`ACCEPTANCE_MATRIX.md`
- `.claude/commands/mode-p-rebuild.md`、`mode-p-pilot.md`、`mode-p.md`
- `.claude/agents/mode-p-director.md`、`mode-p-dp.md`
- Director/DP 运行契约、Master 编译器、双视图派生器、Batch DP、项目背景和资产卡注册表
- 活动入口测试、遗留协议扫描、全量回归和重复执行隔离

## 2. 已修复问题

1. DP 描述曾暗示读取 Master，并承担本地哈希职责；现已限定为最小干净证据和自然语言技术审查。
2. Pilot 文档中的 Batch DP 参数示例与真实 CLI 不一致；现已与可执行参数对齐。
3. Master 要求模型手写可机械推导的镜头边界 ID；现由编译器按镜头顺序生成，遗留显式值仅用于一致性校验。
4. 完整项目剧本可能无差别进入上下文；现只做本地词法检索，分集冲突时当前分集绝对优先。
5. 场景模型上下文包含源码路径和哈希等工程噪声；现只保留精确剧本摘录和必要连续性。
6. 测试用 PID 固定目录会在 Windows PID 复用后读取旧 session；现改为每次 pytest 进程唯一的临时根目录。
7. 后续轮次曾尝试在非 Git 工作区运行 `git status`；现明确使用锁、活动文件证据和轻量测试判断漂移。
8. 项目迁移到另一台 Windows 电脑后，Hook 曾保留旧用户目录绝对路径；现改为项目相对路径并由活动入口测试实际执行验证。
9. 运行时依赖曾只存在于原电脑环境；现由根目录 `requirements.txt` 声明 `jsonschema` 与 `pytest`，并在 README 中记录迁移安装命令。

## 3. DeepSeek V4 Pro 适配结论

现有描述和约束已经足够，不应继续堆叠通用提示词。

- **职责足够清楚**：Rebuild 只做工程；Pilot 才创作；Accept 只做显式语义验收。
- **上下文足够明确**：Director/DP 各有白名单和预算，不以大上下文窗口为由加载全仓库。
- **输出足够明确**：Director 写一个 Master；本地程序派生两个视图；DP 只给问题定位和通过结论。
- **强约束放置正确**：时长、边界、哈希、引用、状态、缓存、锁和提交由程序检查，不依赖模型记忆。
- **推理要求适当**：允许模型内部充分推理，但不要求展示完整思维链、规则引用或审计证明。
- **模型选择不过度绑定**：生产 Pilot 继承 Claude Code 当前父模型并记录实际 resolved model；不拒绝合理的模型名称变体。

DeepSeek V4 Pro 可能倾向长分析或扩大任务范围，当前“一轮一个任务”“精确停止状态”“禁止自动升级到 Accept/Pilot”已直接约束这些风险。再增加知识库全文、旧架构说明、规则枚举或固定审计模板，会占用设计注意力而不提高导演质量。

## 4. Loop 安全边界

`/mode-p-rebuild` 的 allowed tools 不包含 Agent，且文档明确禁止 Director、DP、即梦、渲染和实模验收。当前计划全部完成后，它只能：

1. 检查锁和活动入口。
2. 运行遗留扫描。
3. 在证据失效时运行全量测试。
4. 同步状态文档。
5. 返回 `LOCAL_REBUILD_READY`；后续无漂移轮次返回 `NO_LOCAL_DRIFT`。

它不会因为在无人值守模式运行而生成创作内容或消耗 Director/DP 子 Agent 调用。

## 5. 验证证据

```text
全量回归：655 passed, 8 subtests passed in 83.95s
活动入口与遗留测试：23 passed in 0.16s
遗留扫描：No legacy residue found.
重复执行：episode_review + mode_p_pilot + structural_precheck 连续两轮均为 30 passed
```

## 6. 交给 Claude Code 的命令

先在 Claude Code 中选择 DeepSeek V4 Pro，然后从项目根目录运行：

```text
/loop 5m /mode-p-rebuild
```

首轮应返回：

```text
LOCAL_REBUILD_READY
NEXT_EXPLICIT_STEP: /mode-p-accept
```

若继续保持 Loop 且文件未变化，后续应返回 `NO_LOCAL_DRIFT`。看到 `LOCAL_REBUILD_READY` 后可以停止 Loop；不要让 Rebuild 自动调用 `/mode-p-accept`。

正式创作某个独立分集时另行运行：

```text
/mode-p-pilot "<当前分集剧本路径>"
```

## 7. 剩余边界

本轮没有启动真实 Director/DP。因此只能确认工程 Loop、上下文控制和输出同源机制已就绪，不能宣称 B1-B5、D4 导演语义质量已经通过。该结论必须来自用户显式执行的新 `/mode-p-accept <new-run-id>`。
