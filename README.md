# 导演系统 v5 — MODE:P v4.0

> **最后更新**: 2026-07-18
> **状态**: v4.0 本地契约验收中 · run-005 仅为历史实模证据 · 当前契约待重验
> **重构**: 集级持续 Director · 统一视觉时间线 · 共享 Boundary · Fresh DP

---

## 快速开始

```text
/mode-p-pilot <当前分集剧本路径>
```

当前分集可独立上传，不要求从完整剧本拆出。一条命令完成从分集剧本到 SD2.0
提示词的流程，不需要项目名、集号、场景范围、Python 命令或手动转发 DP 反馈。

完整剧本只在用户用自然语言指定时登记为可选项目背景；单活动项目自动绑定，没有
项目时独立运行。分集与背景冲突时以当前分集为准。

调试/重建模式：

```text
/loop 5m /mode-p-rebuild
```

vNext 隔离重写（不调用创意 Agent、不替换当前生产入口）：

```text
/mode-p-vnext-rebuild V0.1
/loop 5m /mode-p-vnext-rebuild
```

当前vNext处于`REPAIR_REQUIRED`：上述命令会先执行`R0.1`开始的LOOP修复队列，不会继续原V0-V10，也不会接受手工勾选完成。机器状态由`mode_p_vnext.rebuild_control`控制；修复队列完成后才进入原任务逐项重验。

vNext 采用“隔离重写 → 原子替换”，不是长期双系统并行。施工期 v4 仅作为只读黑盒回归与回滚基线；vNext 禁止导入 v4 模块、知识索引、缓存、Session、delivery 或 fallback。只有完成本地工程、Shadow、Pilot、Canary 并获得用户明确批准后，vNext 才能接管唯一活动入口。

固定实模验收只可显式运行，不得放入 `/loop`：

```text
/mode-p-accept <新的 run ID>
```

---

## 架构

```
剧本 (唯一叙事真源)
    │
    ▼
Director (一个持续 mode-p-director 子 Agent·统一视觉设计)
    │
    ▼
DIRECTOR_MASTER.md (唯一设计母版)
    │
    ├── master_compiler.py → SHOT_MANIFEST.json (机械投影)
    ├── view_deriver.py → STORYBOARD.md (同源派生)
    └── view_deriver.py → VIDEO_PROMPT.md (同源派生)
    │
    ▼
DP (每轮全新 mode-p-dp 子 Agent·只审不设计)
    │
    ▼
episode_review → delivery/STORYBOARD.md + delivery/VIDEO_PROMPT.md
```

**只有两个 LLM 角色**：Director（创作）+ DP（审查）。本地程序负责解析、编译、
检查、缓存、锁和原子提交，不消耗模型调用，也不合成创意提示词正文。

## 项目结构

```
导演系统_v5/
├── CLAUDE.md                              ← Claude Code 项目指令
├── ASSET_INDEX.json                       ← 参考媒体索引
├── ASSET_CARD_INDEX.json                  ← 哈希绑定文字资产卡索引
├── MODE_P_REDESIGN_PROJECT/               ← 重构设计文档
│   ├── LOOP_SPEC.md                       ← 运行权威规范
│   ├── CLAUDE_CODE_REBUILD_LOOP.md        ← Claude Code 重构接力协议
│   ├── IMPLEMENTATION_PLAN.md             ← 实施状态；最终完成还需当前验收证据
│   ├── PROGRESS.md                        ← 进度与测试证据
│   └── ACCEPTANCE_MATRIX.md               ← 验收矩阵 A-K
├── .claude/
│   ├── commands/                          ← mode-p-pilot, mode-p-rebuild, mode-p-accept
│   ├── agents/                            ← mode-p-director, mode-p-dp
│   ├── settings.json                      ← Hook 配置
│   └── hooks/kb-guard.py                  ← KB 规则泄漏防护
├── 01_调度器/
│   ├── dispatcher_v5.0.md                 ← 调度入口（本架构摘要）
│   ├── mode_p/                            ← 确定性运行时（190+ 文件）
│   │   ├── knowledge/core/                ← 4 核心知识
│   │   ├── knowledge/capsules/            ← 9 场景知识胶囊
│   │   ├── knowledge/knowledge_index.json ← 版本化知识索引
│   │   └── sd2_capability_profile.json    ← SD2.0 能力配置
│   └── legacy_mode_p/                     ← 只读归档（v5.0-v7.0）
├── 02_Agent/
│   ├── director_agent.md                  ← Director 角色契约
│   └── dp_agent.md                        ← DP 角色契约
├── 05_项目经验/                            ← Phase 5 渲染反馈学习
│   ├── candidates/  repeated/  validated/
│   ├── rejected/  render_cases/
│   └── README.md                          ← 真实渲染经验晋升规则
└── delivery/                              ← 最终交付
    ├── STORYBOARD.md
    └── VIDEO_PROMPT.md
```

## 核心原则

1. **剧本唯一真源** — 不新增剧本外事件、对白或动机
2. **导演唯一设计权** — 机位、运镜、构图、光影、表演统一决定
3. **单一设计母版** — 每场只有一个 `DIRECTOR_MASTER.md`
4. **同源双视图** — 两个视图从 Master 机械派生，禁止分别创作
5. **DP 只审不设计** — 只指出可观察问题，不接管风格选择
6. **每镜 `0 < duration <= 15s`** — 每镜独立；按情境使用事件/逐秒/半秒节点
7. **知识按需内化** — 当前知识架构冻结，本轮不扩建、不重排、不改选择策略
8. **真实结果才可学习** — 无即梦实际生成结果不进经验循环
9. **按情境派生** — 八类 Profile 改变双视图关注顺序，不复制八套模板
10. **无图片也正常** — 无 verified 资产卡即 `text_only`，不调用视觉模型
11. **只交付两个文件** — `STORYBOARD.md` + `VIDEO_PROMPT.md`

## Shot Contract 要点

- 稳定自然语言 Markdown 标签（不写 YAML/JSON/规则 ID）
- `story_fact` 可追溯至剧本原文行号
- 每镜只有一条 `视觉时间线`；视频使用全部节点，故事板只使用 Director 标记的 `[SB]` 节点
- N 个 Shot 只有 N+1 个共享 Boundary；连续切点只写一份交接状态，省略切点显式写出变化
- 生成模式：纯提示词 / 首尾帧 / 全能参考 + 参考职责绑定
- 声音设计：环境声、对白、动作声、声音桥
- 转场执行：SD2.0 镜内完成 / 后期剪辑完成

## 从旧版迁移

| 旧概念 | 新架构对应 |
|--------|-----------|
| MODE:A/C/V/R/F/FP | 已归档至 `legacy_mode_p/` |
| dispatcher_v5.0.md (旧版) | 本文件（重写）+ `LOOP_SPEC.md` |
| scene_context.md | `mode_p_pilot.py` 自动生成 Scene Context |
| loop_controller.md | `LOOP_SPEC.md` §6 状态机 |
| sd2_preflight.py | `structural_precheck.py`（预检） + `batch_dp.py`（DP 前检查） |
| run_mode_p.py init/submit | `mode_p_pilot.py`（全流程） + `run_mode_p.py`（确定性操作） |
| Shot/Movement/Composition 三 Agent | 单个 Director 统一设计 |
| P-Verifier v3.0 (6专家) | 每轮全新 mode-p-dp Agent |
| TIME_SKELETON | 每镜唯一 `视觉时间线`（事件节点/1s/0.5s）；`[SB]` 只是故事板投影标记 |
| Gate 0 / 规则 ID | `structural_precheck.py` + DP 自然语言审查 |
| Seko 平台语法 | SD2.0 生成模式 + 参考职责绑定 |
| STATE.md / P-STATE.md | `05_项目经验/` + `knowledge/capsules/` |
| kb_index_v2.0.md | `knowledge/knowledge_index.json` |
| PLAN_[场景].md | `DIRECTOR_MASTER.md`（场景蓝图 + 逐镜 Contract） |
| RENDER_PACKAGE.md | `VIDEO_PROMPT.md`（独立可生成） |
| OBJECT_TIMELINE / ANCHOR_BASELINE | `EPISODE_CONTINUITY_LEDGER.md` + 边界状态键 |
| 五段式+逐秒分段 | Shot Contract 的 `视觉时间线` + `声音设计` |

## 依赖

- Claude Code（主任务 = 调度器 · 子 Agent = 持续 Director + fresh DP）
- Python 3.10+（确定性运行时 · `01_调度器/mode_p/`）
- Python 包：`jsonschema`（运行时）和 `pytest`（本地验收）
- 即梦 SD2.0（外部画布 · MODE:P 不负责渲染）

迁移到新电脑后，在项目根目录先安装锁定范围内的依赖：

```powershell
python -m pip install -r requirements.txt
```

`.claude/settings.json` 中的 Hook 使用项目相对路径；项目目录移动后无需改写电脑用户名或盘符。
