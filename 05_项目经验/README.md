# 05_项目经验 — MODE:P Experience Learning

> 本目录存放从外部真实渲染结果中提取的经验。MODE:P 本身不负责渲染；
> 所有证据来自即梦 SD2.0 实际生成结果和用户可观察反馈。

## 目录结构

| 目录 | 用途 | 晋升条件 |
|------|------|----------|
| `candidates/` | 新提交的待整理观察 | 有人工标记的渲染证据关联 |
| `repeated/` | 至少两次真实渲染中的可复现观察 | 至少 2 个独立 evidence_id + 2 条用户观察 |
| `validated/` | 已批准可进入知识检索的经验 | repeated + 至少 2 个不同场景 + 人工批准 + 回归通过 |
| `rejected/` | 已审查但不采纳的候选 | 明确拒绝理由记录 |
| `render_cases/` | 原始渲染案例归档 | Master + 渲染结果 + 用户反馈 |

## 晋升流程

```
外部渲染结果 + 用户观察
  → Knowledge Curator 提取 candidate
  → 修订并再次真实生成
  → repeated（至少两条真实 render case 与用户观察）
  → validated（至少两个不同场景 + 人工批准 + 回归通过）
```

## 规则

1. 无真实渲染证据不能创建有效经验。
2. 单次观察不能进入 repeated 或 validated。
3. validated 必须通过 `/mode-p-promote <candidate-id> validated --approved-by <name> --regression-command "<command>" --regression-passed`。
4. 知识更新可通过 promotion history 回退，且晋升前必须记录回归命令。
5. 全能参考或首尾帧的成功/失败经验必须记录：素材类型、素材职责、冲突关系、提示词、实际结果和修订结果。
6. 单次随机生成失败不得直接晋升为 SD2.0 通用规律。
7. 候选引用的 evidence_id 必须能在 `render_cases/` 中加载；observation_id 必须存在于对应案例。
8. 使用参考素材的渲染证据必须记录素材内容哈希或版本，不能只写 asset_id。
