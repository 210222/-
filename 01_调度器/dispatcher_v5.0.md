# MODE:P — 导演循环调度器 v4.0

> 本文件是 MODE:P v4.0 重构后的调度入口。所有遗留 MODE（A/C/V/R/F/FP）已归档至
> `legacy_mode_p/`。当前唯一活动模式为 MODE:P。

## 唯一入口

```text
/mode-p-pilot <当前分集剧本路径>
```

当前分集可独立上传且是本集叙事真源。项目背景可选、自动绑定；无项目正常运行。
用户不填写项目名、集号、场景范围或会话目录，也不选择 Agent、运行脚本或转发反馈。

## 运行时角色

| 角色 | 载体 | 职责 |
|------|------|------|
| 调度宿主 | 当前 Claude Code 任务 | 状态、工具、Agent 路由；不创作 |
| Director | 每集一个持续 `mode-p-director` 子 Agent | 跨批次/修订/全片回看统一视觉设计，只写 `DIRECTOR_MASTER.md` |
| DP | 每轮全新 `mode-p-dp` 子 Agent | 独立审查空间/连续性/生成风险 |
| 本地程序 | `01_调度器/mode_p/` | 解析、编译、检查、缓存、锁、提交 |

Director 不输出推理过程或知识证明。DP 只审不设计。调度宿主和本地程序都不得接管
创作。生产流程继承 Claude Code 当前选择的模型并记录 Director 与 DP 的实际
`resolvedModel`；只有显式固定验收 `/mode-p-accept` 强制 `deepseek-v4-pro`。

## 唯一设计源

```text
DIRECTOR_MASTER.md (唯一设计源)
    ├── master_compiler.py → SHOT_MANIFEST.json (机械投影·无设计权)
    ├── view_deriver.py → STORYBOARD.md (同源派生)
    └── view_deriver.py → VIDEO_PROMPT.md (同源派生)
```

两个视图由本地派生器从同一 Master 生成，并按八类场景 Profile 调整关注顺序；禁止
Director 分别创作或事后修补。
每镜只写一条视觉时间线；Video 使用全部节点，Storyboard 只使用 `[SB]`
节点。N 个 Shot 共享 B0...BN 共 N+1 个 Boundary。

## 运行状态机

```text
BOOTSTRAP → SCRIPT_PARSE → DIRECTOR_BATCH
    → MASTER_COMPILE → VIEW_DERIVE → STRUCTURAL_PRECHECK
    → FRESH_DP_BATCH → DIRECTOR_REVISE (when needed)
    → FINAL_HASH_CHECK → ATOMIC_BATCH_COMMIT
    → EPISODE_REVIEW → ATOMIC_DELIVERY
```

完整规范见 `MODE_P_REDESIGN_PROJECT/LOOP_SPEC.md`；Claude Code 执行合约见
`.claude/commands/mode-p-pilot.md`。

## 核心文件

| 用途 | 路径 |
|------|------|
| 运行权威 | `MODE_P_REDESIGN_PROJECT/LOOP_SPEC.md` |
| Director 角色 | `02_Agent/director_agent.md` |
| DP 角色 | `02_Agent/dp_agent.md` |
| Director Agent 定义 | `.claude/agents/mode-p-director.md` |
| DP Agent 定义 | `.claude/agents/mode-p-dp.md` |
| 确定性运行时 | `01_调度器/mode_p/` |
| 核心知识 (4) | `01_调度器/mode_p/knowledge/core/` |
| 场景知识 (9) | `01_调度器/mode_p/knowledge/capsules/` |
| 能力配置 | `01_调度器/mode_p/sd2_capability_profile.json` |
| 资产索引 | `ASSET_INDEX.json` |
| 文字资产卡 | `ASSET_CARD_INDEX.json` |
| 重建进度 | `MODE_P_REDESIGN_PROJECT/PROGRESS.md` |

## 交付

仅两个文件：

```text
delivery/STORYBOARD.md
delivery/VIDEO_PROMPT.md
```

不交付 Master、Manifest、DP 反馈、遥测、审计报告、YAML、PLAN、TIME_SKELETON、
Gate 输出、Seko 语法或渲染打包。

## 不可违反的原则

1. 剧本唯一叙事真源
2. 导演唯一设计权
3. 单一设计母版 (`DIRECTOR_MASTER.md`)
4. 同源双视图（本地派生器生成）
5. DP 只审不设计
6. 每镜独立生成 (`0 < duration <= 15s`)
7. 参考模式是导演决策（纯提示词 / 首尾帧 / 全能参考）
8. 衔接由边界状态保证（不得"承接上一镜"）
9. 知识按需内化（Core + 1-3 胶囊 + 0-3 validated 经验）
10. 真实结果才可学习（Phase 5 渲染反馈）
11. Director/DP 不读取媒体二进制；无 verified 卡自动使用 text_only
12. DP 只读取剧本证据、双视图和实际使用摘要，不读取 Master/Manifest/知识/源码
