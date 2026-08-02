<!-- MODE_P_VNEXT_AUTHORITY: architecture-v3.1 -->

> Active v3.1 governance (which overrides every legacy descriptive note below):
> `vnext_repair_evidence/MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V3.1.md`,
> `MODE_P_VNEXT_CONSTRUCTION_V3_1.md`,
> `MODE_P_VNEXT_RELEASE_TASKS.json`, and `MODE_P_VNEXT_RELEASE_STATE.json`.
> v3.0 is historical under the recorded Projection/Gate-0/DP conflict repair;
> it cannot be used as active authority or completion evidence.

# MODE:P Director Intelligence - 重构项目章程

> vNext 重构入口：`/mode-p-vnext-rebuild [task_id]`
>
> vNext v3.1 唯一权威架构：
> `vnext_repair_evidence/MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V3.1.md`
>
> vNext v3.1 工程协议：`MODE_P_VNEXT_CONSTRUCTION_V3_1.md`
>
> vNext v3 任务与状态：`MODE_P_VNEXT_RELEASE_TASKS.json`、
> `MODE_P_VNEXT_RELEASE_STATE.json`
>
> 唯一控制命令：`python -m mode_p_vnext.release_control`
>
> 迁移方式：模块化单体内隔离迁移，验证后再提出独立生产切换方案。v2.0-v2.3
> 架构文档、R、DDO、CPL、V0–V10 任务均只作历史证据；v2.3 已被全项目审查否决。
> 生产 v4 仍是只读产品行为基线和唯一生产入口，不是 vNext 施工任务源。

> 状态：v3.1 活动管道按 ReleaseLedger 顺序施工、验证和回归中。
> 实施入口：`IMPLEMENTATION_PLAN.md`
> 运行规范：`LOOP_SPEC.md`
> Claude Code 重构接力协议：`CLAUDE_CODE_REBUILD_LOOP.md`
> 知识系统：`KNOWLEDGE_SYSTEM.md`
> 验收标准：`ACCEPTANCE_MATRIX.md`

## 1. 项目使命

MODE:P 必须成为一个以剧本为叙事真源、以导演判断为统一设计权、以即梦 SD2.0 为生成边界的视觉导演系统。

系统读取当前独立上传的分集剧本后，应能：

1. 理解本集的戏剧结构、人物关系变化和信息释放顺序。
2. 建立本集视觉策略，并在存在项目背景时继承非冲突的长期设定。
3. 统一设计机位、运镜、构图、光影、表演可见化和画面切换。
4. 从同一份导演母版派生故事板提示词和视频提示词。
5. 为每个独立镜头选择纯提示词、首尾帧或全能参考，并为参考素材分配明确职责。
6. 用镜间边界契约保证独立生成的视频可以连续剪辑。
7. 由独立 DP 只检查空间、连续性和执行风险，再由导演修订。
8. 通过真实即梦生成结果积累经过验证的项目经验，使知识系统逐步完善。

## 2. 核心定义

### 2.1 真正的导演

导演不是 Prompt Composer，也不是规则检查员。导演负责回答：

- 这场戏真正改变了什么？
- 观众何时应该看到、忽略或误解什么？
- 人物关系如何通过距离、角度、占比、光线和镜头时长呈现？
- 摄影机为何在此刻运动或保持静止？
- 一个镜头如何把视觉和情绪交给下一镜？
- 当前镜头为何使用首尾帧、全能参考或纯提示词，各参考分别控制什么？
- 在 SD2.0 能力范围内，哪个方案最接近导演意图？

### 2.2 知识内化

知识内化不是把整个知识库放入上下文，也不是在输出中引用规则编号。它是：

```text
识别剧本信号
  -> 检索相关知识胶囊与已验证经验
  -> 将知识转化为统一视觉决策
  -> 用真实生成结果验证
  -> 将重复有效的经验晋升回知识系统
```

### 2.3 单一设计源

每个场景只有一个 `DIRECTOR_MASTER.md`。它是导演设计真源，不是交付物。

- 故事板提示词是 Master 的空间与关键画面视图。
- 视频提示词是 Master 的时间、运动、表演和声音视图。
- 任何修订先改 Master，再重新生成受影响的两个视图。

## 3. 目标架构

```text
当前分集剧本 + 可选项目背景
  -> BOOTSTRAP（预加载索引、版本和素材元数据，不调用模型）
  -> 缓存恢复与依赖失效
  -> Script Ingest（提取事实，不创作）
  -> Director 批次会话
      -> 全片视觉策略
      -> 场景队列
          -> 知识上下文组装
          -> Director Master
          -> 内部 Shot Manifest
          -> Storyboard + Video Prompt
  -> 结构预检
  -> 全新 DP 批量审查
      -> 有问题：Director 局部修订后重新结构预检
  -> 最终哈希检查与批次提交
  -> 全片交付
  -> 可选：真实渲染观察与知识学习循环
```

## 4. Agent 边界

### 4.1 运行时只有两个创作角色

| 角色 | 职责 | 禁止事项 |
|---|---|---|
| Director | 本集视觉策略、场面调度、镜头、运镜、构图、光影、表演、切换和唯一 Master | 规则证明、审计报告、分别创作双视图、把设计分给领域 Agent |
| DP | 独立复核空间、轴线、连续性、摄影路径、光源和 SD2.0 风险 | 重做导演方案、添加风格偏好、生成评分表 |

### 4.2 非运行时维护角色

Knowledge Curator 只在真实即梦结果和明确用户反馈出现后运行。它不参与正常创作，不直接修改核心知识，只产生经验候选与晋升建议。

## 5. 产物边界

### 5.1 内部设计文件

- `SCRIPT_FACTS.md`：剧本事实与场景边界。
- `EPISODE_VISUAL_BIBLE.md`：全片视觉弧线和连续性策略。
- `KNOWLEDGE_CONTEXT.md`：本场实际加载的知识文件清单，不包含推理。
- `DIRECTOR_MASTER.md`：场景唯一设计源。
- `SHOT_MANIFEST.json`：由 Master 机械生成的内部规范字段投影，不拥有设计权。
- `DP_FEEDBACK.md`：当前轮简短反馈。

这些文件只服务运行与学习，不交付即梦。

### 5.2 最终交付

每个场景只交付：

1. `STORYBOARD.md`
2. `VIDEO_PROMPT.md`

不交付 YAML、PLAN、TIME_SKELETON、规则 ID、审计报告、Seko 包装或 Agent 推理。

## 6. 非目标

- 不训练或修改 Claude 模型参数。
- 不让历史模式自动替代导演判断。
- 不以关键词命中直接决定镜头。
- 不在无真实渲染证据时自动修改知识库。
- 不恢复旧多 Agent 设计链或多层验证链。
- 不保证即梦每次随机生成都完全一致；系统目标是提高可控性和可修正性。
- 不把“预加载”理解为提前塞入完整知识库；预加载只建立索引、版本指纹和最小上下文缓存。

## 7. 成功定义

项目完成时，用户在 Claude Code 中只需：

```text
/mode-p-pilot <当前分集剧本路径>
```

默认处理当前分集的全部场景。完整剧本只在用户自然语言指定后登记为可选背景；分集
无需从它拆分。系统自动完成本集视觉策略、逐场设计、DP 修订、同步检查和 SD2.0
预检。无图片时直接使用 `text_only`；Director/DP 不读取媒体二进制。

真实渲染后，用户可以单独触发学习命令；学习不阻塞日常创作。
