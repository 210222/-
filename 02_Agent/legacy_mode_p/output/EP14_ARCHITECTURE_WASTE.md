# EP14 架构冗余审计报告 -- 结构性浪费深度分析

> **审计日期:** 2026-07-07
> **审计对象:** MODE:P管道 v6.1 全链路
> **数据来源:** dispatcher_v5.0.md · complexity_router_v1.0.md · scene_designer_v1.0.md · scene_auditor_v1.0.md · P-CONSTITUTION.md · EP14_REDTEAM_v2_REPORT.md · EP14_PERFORMANCE_ANALYSIS.md
> **审计方法:** 鱼骨图根因分析 + 信息生命周期追踪 + 最小可行管道设计 + 可立即消除浪费清单

---

# 1. 结构性浪费根因分析（鱼骨图）

```
算力浪费鱼骨图 ── 以EP14场景A (7镜·31秒·1室2人·86%固定·4句对白) 为解剖标本

┌─────────────────────────────────────────────────────────────────────────────┐
│                          算力浪费 (~875K tokens/场景)                         │
│                        根因: 管道复杂度与场景复杂度脱钩                          │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌─ 重复读取 ─────────────────────────────────────────────────────────────┐
  │                                                                         │
  │  ├── 宪法/P-STATE/canvas_runtime: 7+ Agent各自Read                       │
  │  │   ├─ Shot Architect: Read P-CONSTITUTION + P-STATE + canvas_rt       │
  │  │   ├─ Movement Designer: Read P-CONSTITUTION + P-STATE + canvas_rt    │
  │  │   ├─ Composition Designer: Read P-CONSTITUTION + P-STATE + canvas_rt │
  │  │   ├─ SDA: Read P-CONSTITUTION + P-STATE                              │
  │  │   ├─ Storyboard Planner: Read P-CONSTITUTION                          │
  │  │   ├─ Prompt Composer: Read P-CONSTITUTION + P-STATE + canvas_rt      │
  │  │   └─ SSA: Read P-CONSTITUTION + P-STATE                              │
  │  │   估算: 7次 x ~3K tokens/次 = ~21K tokens 纯重复                       │
  │  │                                                                       │
  │  ├── 参考图/空间地图: 5+ Agent各自Read                                    │
  │  │   ├─ Shot Architect: Read 全部参考图 + 空间地图                         │
  │  │   ├─ Movement Designer: Read 空间地图(已含在Shot输出中)                  │
  │  │   ├─ Composition Designer: Read 全部参考图 + ANCHOR_BASELINE §C         │
  │  │   ├─ SDA: Read 参考图 + 空间地图(作为审计参照)                           │
  │  │   └─ SSA: Read 空间地图(作为台本审计参照)                                │
  │  │   估算: 5次 x ~5-10K tokens/次(含图片描述) = ~25-50K tokens 重复        │
  │  │                                                                       │
  │  └── 上游输出: 审计Agent全量读取设计Agent输出(不只看YAML)                    │
  │      ├─ SDA读取Shot(857行) + Movement(978行) + Composition(1631行)        │
  │      │   = 3,466行自由文本 + 推理过程(虽声称隔离·实际仍需读完整报告)         │
  │      ├─ SSA读取prompt_composer台本(全部·含设计依据)                         │
  │      └── 估算: 审计Agent ~30-50%的输入token用于读取"不需要LLM判断"的部分     │
  │                                                                         │
  │  根因: 宪法第七条(独立验证)的实现方式是"每个Agent独立加载所有上下文"           │
  │       而非"预编译上下文包·一次加载·多Agent共享引用"                          │
  │       这是"独立验证=独立加载"的误用——独立指的是推理隔离，不是文件加载隔离       │
  └─────────────────────────────────────────────────────────────────────────┘

  ┌─ 过深度管道 ─────────────────────────────────────────────────────────┐
  │                                                                       │
  │  ├── S-Level场景触发了Movement+SDA+SSA(全零阻断)                        │
  │  │   ├─ EP14场景A: 7镜中6镜固定→Movement Designer产出978行论证           │
  │  │   │   "6个固定镜头是合理的"── 一行"全部固定·镜#A6推近0.05x"即可     │
  │  │   ├─ SDA产出1,040行·零阻断·10项警告(5-6项可正则检测)                 │
  │  │   └── SSA产出504行·3项阻断(全正则可检测: 过程动词+时间模糊词+工程符号) │
  │  │       → 如果先跑Gate 0正则扫描·SSA的177K token LLM调用完全不需要     │
  │  │                                                                     │
  │  ├── 复杂度路由未激活(新架构尚未部署)                                     │
  │  │   ├─ complexity_router将EP14A正确分类为S-Level(2 Agent)               │
  │  │   ├─ 但4个阻断项(BLOCK-1~4)未修复·S-Level不可用                       │
  │  │   ├─ 当前实际运行的是C-Level全管道(~18 Agent)                          │
  │  │   └── 根因解决停留在概念·实现未完成                                    │
  │  │                                                                     │
  │  └── 审计深度不随场景复杂度缩放                                           │
  │      ├─ SDA的五维审计(维度A-E)对S-Level场景发现率趋近于零                  │
  │      │   → 单室场景: 空间可行性自动满足·静态镜头: 无运镜越界风险           │
  │      ├─ SSA的五维审计在Gate 0覆盖后仅剩~20%增量价值                       │
  │      │   → 维度B(参数完整性)~30%是正则可检测的                             │
  │      └── 当前: 所有场景统一的审计深度·零自适应                             │
  │                                                                       │
  │  根因: 管道被设计为"对所有场景一视同仁"——但场景复杂度差异可达10x+           │
  │       complexity_router在纸面上解决了这个问题·但未部署                      │
  └───────────────────────────────────────────────────────────────────────┘

  ┌─ KB膨胀 ──────────────────────────────────────────────────────────────┐
  │                                                                       │
  │  ├── 03_导演知识库_v5.0.md ~720条规则·每次40-60K tokens                  │
  │  │   ├─ 完整文件~720条·约40-60K tokens(取决于编码密度)                    │
  │  │   ├─ EP14场景A实际需要: 双人对话场景·约52条机位+16条运镜+45条构图/光影 │
  │  │   │   = ~113条·约6-10K tokens                                        │
  │  │   └── 浪费因子: 6x-10x (加载720条·实际使用~113条)                     │
  │  │                                                                     │
  │  └── kb_index路由后仍加载完整章节·非仅规则摘要                            │
  │      ├─ kb_index_v2.0.md设计了场景类型路由(~5KB)                          │
  │      ├─ 路由结果: "加载§1.1-1.3双人对话·§5.2运动方式·§4.1+§6.1-6.4"    │
  │      ├─ 但实际加载方式: Agent Read KB文件 → 在上下文中"定位"到这些章节    │
  │      │   → 仍需加载完整文件(40-60K) → LLM在上下文中过滤                    │
  │      └── 理想方式: 预提取摘要(只含路由命中的规则文本·不加载整文件)          │
  │                                                                       │
  │  根因: KB物理结构是单一文件·即使"路由"也只是在已加载的60K中找10K            │
  │       真正的"路由"应该是预提取——调度器在Agent启动前提取10K摘要             │
  └───────────────────────────────────────────────────────────────────────┘

  ┌─ 形式主义产出 ─────────────────────────────────────────────────────────┐
  │                                                                         │
  │  ├── Movement Designer逐镜静态辩护                                        │
  │  │   ├─ 产出978行·其中~700行是"镜#N固定·因为角色静止·固定镜头有助于..."   │
  │  │   ├─ 运镜合理性论证段落: ~700行                                        │
  │  │   ├─ 实际信息增量: 1个运镜参数("镜#A6推近0.05x")                        │
  │  │   └── 有效信息密度: 1/978 = 0.1%                                       │
  │  │                                                                       │
  │  ├── SDA零阻断审计报告                                                    │
  │  │   ├─ 产出1,040行·零阻断·10项警告(其中5-6项正则可检测)                   │
  │  │   ├─ 真正需要LLM判断的发现: 4-5项·每项~50行                             │
  │  │   └── 有效信息密度: ~250/1,040 = 24%                                   │
  │  │                                                                       │
  │  └── OBJECT_TIMELINE(零O-ID台本引用)                                      │
  │      ├─ 定义了26个物品·O-01至O-26                                         │
  │      ├─ 但在台本【生成指令】中零O-ID引用                                    │
  │      ├─ 物品存在性只能通过人工关联 ANCHOR_BASELINE→设计报告→台本 跨文档追溯  │
  │      └── 产出价值: 设计意图存在·但在下游中无结构消费                         │
  │                                                                         │
  │  根因: Agent被指令要求"论证"而非"决策" —— "为什么这个镜头固定"需要论证       │
  │       但"什么都不做"不需要辩护。默认就是什么都不做。                          │
  └─────────────────────────────────────────────────────────────────────────┘

  ┌─ LLM做确定性工作 ───────────────────────────────────────────────────────┐
  │                                                                         │
  │  ├── SSA的3项阻断全正则可检测                                              │
  │  │   ├─ 阻断1: 过程动词"开始后退一步" → 正则 /^开始[^前]/                  │
  │  │   ├─ 阻断2: 时间模糊词"缓缓推近" → 正则 /缓缓/                           │
  │  │   ├─ 阻断3: 工程符号泄漏"v_dolly·w_pan" → 正则 /v_dolly|ω_pan/        │
  │  │   └── 如果先跑Gate 0: 3项阻断在~1K tokens内全部检出·零LLM               │
  │  │       SSA的177K tokens LLM调用完全不需要                                │
  │  │                                                                       │
  │  ├── Gate 0嵌入LLM审计而非前置                                             │
  │  │   ├─ 旧管道: Gate 0作为P-Verifier的第一步·在全部Agent调用之后            │
  │  │   ├─ 新架构: Gate 0前置到Scene Auditor Phase 0·在LLM审计之前             │
  │  │   ├─ 但新架构尚未部署·Gate 0前置策略仍未生效                              │
  │  │   └── 如果Gate 0在所有LLM审计之前执行: 节省SSA的177K + SDA中5-6项检查    │
  │  │                                                                       │
  │  └── "逐渐""推近落定"触发了177K token的LLM调用                              │
  │      ├─ 5个词("缓缓推近落定后，镜头固定")破坏了管道铁律#3(禁止时间模糊词)     │
  │      ├─ 修复成本: 5个词 → 删除·替换为精确参数                               │
  │      ├─ 但旧管道中引发了: SSA 177K tokens + 返工回环(~300K tokens)         │
  │      └── 浪费比: 5个词的错误 → ~477K tokens的LLM调用 → 95,400:1             │
  │                                                                         │
  │  根因: 确定性检查和概率性验证的执行顺序错误                                  │
  │       Gate 0(确定性·100%准确·零模型)应该在所有LLM审计之前执行               │
  │       而不是嵌入在LLM审计之中                                              │
  └─────────────────────────────────────────────────────────────────────────┘
```

---

# 2. 信息生命周期分析

## 2.1 案情室空间描述的生命周期追踪

追踪"案情室空间描述(~6m x 4m x 3m·白板北墙·格栅灯5000K)"的完整生命周期：

```
┌────────────────────────────────────────────────────────────────────────────┐
│              信息生命周期 — 案情室空间描述 (~200字·零净新增信息)               │
│                                                                             │
│  产生: IMAGE_AUDIT Step 0A (调度器自执行·150行·一次)                          │
│    描述: "案情室·6m纵深×4m宽×3m高·白板居北墙·格栅灯天花·5000K·水泥地面"       │
│    信息状态: 完整·已包含所有空间事实                                           │
│    成本: 0 tokens (调度器自执行)                                              │
│                                                                             │
│  复制1: ANCHOR_BASELINE §C (结构化·404行)                                     │
│    形式: "空间尺寸: 6m×4m×3m | 北墙: 白板(2.4m×1.2m) | ..."                  │
│    新增信息: 结构化的格式开销(节标题·字段标签·前缀符号)                          │
│    成本: ~1-2K tokens                                                        │
│                                                                             │
│  复制2: Shot Architect §2 (机位化·857行)                                      │
│    形式: "案情室空间坐标系: 纵深6m·宽4m·高3m。白板位于北墙居中..."              │
│    新增信息: 机位坐标叠加(7个机位点·在空间坐标系中标注)                          │
│    合法新增: 机位坐标(不在IMAGE_AUDIT中)                                       │
│    空间描述部分: 重复·零新增                                                   │
│    成本: ~15-20K tokens(含空间描述重复+机位坐标)                                │
│                                                                             │
│  复制3: Movement Designer §1.2 (运镜化·978行)                                  │
│    形式: "场景空间: 单一案情室·纵深6m·宽4m·高3m。中央走廊宽约2.5m..."           │
│    新增信息: 运镜路径标注(在空间坐标系中标注推近路径)                             │
│    合法新增: 运镜路径(不在IMAGE_AUDIT中)                                        │
│    空间描述部分: 重复·零新增·且包含对固定镜的逐镜辩护                             │
│    成本: ~35-45K tokens(含空间描述重复+运镜路径+大量零价值论证)                   │
│                                                                             │
│  复制4: Composition Designer §1.1 (光影化·1631行)                              │
│    形式: "案情室空间: 6m×4m×3m单一矩形空间·北墙2.4m×1.2m白板..."               │
│    新增信息: 光源锚点+色彩参考·光影分区标记                                      │
│    合法新增: 光影分区(部分在IMAGE_AUDIT中已有·部分新增)                           │
│    空间描述部分: 重复·零新增                                                   │
│    成本: ~45-60K tokens(含空间描述重复+光影系统+色彩策略)                         │
│                                                                             │
│  复制5: SDA §A.1 (审计引用·1040行)                                             │
│    形式: 审计对象中引用三Agent的空间描述·逐行检查一致性                           │
│    新增信息: 审计结论·零新增空间事实                                            │
│    成本: ~20-30K tokens(含审计维度展开+空间描述引用)                              │
│                                                                             │
│  复制6: PLAN §A2 (逐字锁定·1516行)                                             │
│    形式: TIME_SKELETON.global_anchors.environment 逐字复制空间描述              │
│    新增信息: 格式锁定·零新增空间事实                                            │
│    成本: ~5-10K tokens(含global_anchors全块·环境仅占一小部分)                    │
│                                                                             │
│  复制7: 导演台本 C2 (台本锚定·984行)                                            │
│    形式: "C2 Environment Anchor: 凌晨4:30·案情室·6m×4m×3m..."                  │
│    新增信息: 时间上下文(凌晨4:30)·零新增空间事实                                 │
│    成本: ~3-5K tokens(含C1-C4全块·C2环境描述部分)                               │
│                                                                             │
│  复制8: SSA §C.4 (审计引用·504行)                                              │
│    形式: 审计维度中引用空间描述作为检查基准                                       │
│    新增信息: 审计结论·零新增空间事实                                            │
│    成本: ~5-8K tokens(含审计维度展开+空间描述引用)                                │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 汇总:                                                                 │   │
│  │   9次产生/复制(1次产生+8次复制)                                         │   │
│  │   累积token消耗: ~130-180K tokens (空间描述部分)                         │   │
│  │   净新增空间信息: 0 (首次IMAGE_AUDIT中就已完整)                           │   │
│  │   合法增量: 机位坐标+运镜路径+光影分区+时间上下文(~50%合法·50%纯重复)       │   │
│  │   纯浪费: ~65-90K tokens (零新增·仅复制粘贴+格式化的空间描述)               │   │
│  │                                                                       │   │
│  │   如果Scene Designer实现"空间描述只写一次":                               │   │
│  │     9次 → 3次(IMAGE_AUDIT + Scene Designer Step 0 + ANCHOR_BASELINE)  │   │
│  │     浪费: ~65-90K → ~0K                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────┘
```

## 2.2 其他重复信息类别的生命周期分析

### 类别A: P-CONSTITUTION 七条铁律

```
产生: P-CONSTITUTION.md (一次写入·约10K tokens)

复制链:
  Shot Architect §8.2         — 画布七条铁律合规矩阵(~1K)
  Movement Designer            — 引用画布宪法·进行运镜合规检查(~0.5K)
  Composition Designer         — 引用画布宪法·进行构图合规检查(~0.5K)
  SDA                          — 引用画布宪法第三条(空间锚定)·第四条(运镜分离)(~0.3K)
  Storyboard Planner           — 引用画布宪法进行骨架合规(~0.2K)
  Prompt Composer              — 引用画布宪法全部七条进行台本合规(~0.5K)
  SSA                          — 引用画布宪法第一条·第二条·第四条(~0.5K)
  P-Verifier                   — 引用画布宪法第五条(Gate 0)·第七条(独立验证)(~0.5K)
  Object Existence Verifier    — 引用画布宪法第六条(物体存在链)(~0.5K)

8次引用·累积token: ~4-5K
纯浪费: ~3-4K (只需一次加载·所有Agent引用同一份)
根因: 宪法是"每个Agent独立加载的上下文"而非"预编译上下文包的组成部分"
```

### 类别B: 角色外观描述 (Character Anchor)

```
产生: ANCHOR_BASELINE §A (结构化·约200字/Rico + 150字/Marcus = ~0.5K tokens)

复制链:
  Shot Architect §2           — "Rico: mid-30s Latin male·short dark hair..."(~0.3K)
  Composition Designer §6     — global_anchors.character(~0.5K·逐字复制)
  PLAN §A                     — TIME_SKELETON.global_anchors.character(~0.5K·逐字复制)
  台本 C1                     — Character Anchor(~0.5K·逐字复制)
  SDA                         — 审计引用(~0.1K·片段)
  SSA                         — 审计引用(~0.1K·片段)
  storyboard_previewer        — 故事板生成引用(~0.3K·片段)

7次复制·累积token: ~2.5-3K
纯浪费: ~2K (C1锚点追字复制是合规的·但Shot Architect和Composition Designer中的重复是浪费)
```

### 类别C: KB规则ID引用链

```
产生: kb_index_v2.0.md路由 → 03_导演知识库_v5.0.md对应章节

复制链:
  Shot Architect             — 加载§1.1-1.3(~52条机位规则) + P0规则(~25条) = ~77条
  Movement Designer          — 加载§5.2-5.4(~34条) + P0规则(~25条) = ~59条
                               与Shot重叠: P0规则(~25条)全重复
  Composition Designer       — 加载§4.1-4.2+§6.1-6.4(~45条) + P0规则(~25条) = ~70条
                               与Shot重叠: P0规则(~25条)·与Movement重叠: 部分§5规则
  SDA                        — 加载场景路由KB子集 + P0规则(~25条)
  SSA                        — 加载管道铁律 + P-FAL + canvas_runtime
  P-Verifier                 — 加载P-CONSTITUTION §5(Gate 0规则)

KB加载总次数: 6-7次
每次加载: ~40-60K tokens(完整文件·非提取摘要)
累积: ~300-400K tokens
实际唯一需要: ~113条规则(双人对话场景)·约6-10K tokens
浪费因子: 30x-40x

根因: KB路由≠KB摘要提取。路由指明了"该读哪几章"，但Agent仍需加载完整KB文件(60K)
     然后在上下文中"定位"到那几章。真正的路由应是在Agent启动前提取6-10K的摘要。
```

### 类别D: 参考图描述

```
产生: IMAGE_AUDIT.md (Step 0A输出·含全部参考图格位的文本标注)

复制链:
  Shot Architect             — 读取参考图格位→机位选择(~2-3K)
  Composition Designer       — 读取参考图格位→光源锚定+色彩参考(~3-5K)
  SDA                        — 读取参考图→审计空间锚定(~2-3K)
  Prompt Composer            — 读取参考图→台本@图片引用(~1-2K)
  Storyboard Planner         — 读取参考图→故事板空间(~1-2K)

5次加载·累积token: ~10-15K
合法部分: 每个Agent基于参考图的不同决策(机位/光源/锚定/引用)——这不是纯重复
浪费部分: 参考图的"空间结构事实"部分(房间形状·家具位置·光源)——5次重复
         这些事实在IMAGE_AUDIT和空间地图中已完整·各Agent不应重新"分析"参考图
```

---

# 3. 最小可行管道(MVP)设计

## 3.1 设计目标

**用最少token产出合规台本。** 针对S-Level场景(单室·<=3说话角色·<=5句对白·>=80%静态)。

## 3.2 当前管道 vs MVP

```
┌────────────────────────────────────────────────────────────────────────────┐
│  当前C-Level管道 (~18 Agent·~875K tokens)                                    │
│                                                                             │
│  Step 0: IMAGE_AUDIT [O]          Step 0.5: OBJECT_TIMELINE [O]             │
│  Step 0.6: ANCHOR_BASELINE [O]    Step A1: Scene Anchor Auditor [A]         │
│  Step A2.1: Shot Architect [A]    Step A2.2: Movement Designer [A]          │
│  Step A2.3: Composition Des. [A]  Step A2-审计: SDA [A]                     │
│  Step A2.5: Storyboard Planner[A] Step A3: Prompt Composer [A]              │
│  Step A3-审计1: SSA [A]           Step A3-审计2: Anchor Auditor P2 [A]      │
│  Step A4A: Storyboard Gen [A]     Step A4B: Storyboard Auditor [A]          │
│  Step A4C: Human Gate [H]         Step 9.1: Gate 0 Scanner [A]              │
│  Step 9.2: 5 Experts [A] x5       Step 9.3: Multi-Expert [A]                │
│  Step 9.5: Render Packager [O]    Step 9.6: Object Verifier [A]             │
│  Step 10: Render Verifier [A]                                               │
│                                                                             │
│  ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼               │
│                                                                             │
│  MVP管道 (S-Level·3 Agent·~60-80K tokens)                                    │
│                                                                             │
│  Wave 0: 预编译上下文包 [O] — 一次性·供所有Agent引用·零重复                     │
│    输入: IMAGE_AUDIT + ANCHOR_BASELINE + 空间地图 + 参考图清单                 │
│    操作: 合并→去重→生成上下文摘要包(含: 空间坐标系·角色锚点·光源锚点·             │
│           参考图格位清单·KB规则摘要·P-FAL规避清单)                              │
│    输出: CONTEXT_PACKAGE.md (~5K tokens·一次性)                                │
│    成本: 0 tokens (调度器自执行·纯格式化)                                       │
│                                                                             │
│  Wave 1 (串行·1步):                                                          │
│    S1: [Agent] Scene Designer (三域合并·独立Agent调用)                         │
│        ├─ 输入: CONTEXT_PACKAGE(非原始文件·是预编译摘要)                        │
│        │        + 原始剧本 + complexity_level:"S"                              │
│        ├─ 执行:                                                              │
│        │   1. 机位: 单室<=3个机位·景别+角度+焦段                                │
│        │   2. 运镜: 静态快速通道·一句话("7镜固定·仅镜#A6推近0.05x")            │
│        │   3. 构图光影: 从上下文包直接引用·补充未覆盖项                          │
│        │   4. 台本初稿: 直接输出【镜头参数卡】+【生成指令】+【禁止】+【段末转场】 │
│        ├─ 输出: 合并设计报告 + §7 YAML + 台本初稿 (单文件·<=1500行)            │
│        └─ 硬约束: 不写【设计依据】·不重复上下文包已有信息                        │
│    预估: ~40K tokens                                                         │
│                                                                             │
│  Wave 2 (串行·1步):                                                          │
│    S2: [Agent] Scene Auditor (S-Level精简·跳过Phase 1)                         │
│        ├─ Phase 0: Gate 0正则扫描 (R01-R15·调度器可自执行·零LLM)               │
│        │   → 有阻断: 返回S1修复·上限1轮                                         │
│        │   → 全部通过: 进入Phase 2-3                                           │
│        ├─ Phase 2: TIME_SKELETON降级验证 (台本内部时间自洽)                     │
│        │   (S-Level跳过PLAN·无完整TIME_SKELETON·仅做内部时间自洽)               │
│        ├─ Phase 3: 台本域审计 (精简版·Gate 0已覆盖的不重复)                      │
│        │   - 参数完整性·关键帧标注·音轨精度                                      │
│        │   - 画布宪法深度检查(画面可见性·P-FAL规避·空间锚定)                      │
│        │   - 禁止清单精确度·跨镜衔连                                             │
│        └─ 综合裁决: 🛑/⚠️/✅                                                   │
│    预估: ~20K tokens (Phase 1跳过节省~25K·Phase 0若调度器自执行节省~3K)         │
│                                                                             │
│  总Agent调用: 2次 (Scene Designer + Scene Auditor)                              │
│  预编译上下文: 1次 (调度器自执行·零token)                                        │
│  预估总token: ~60-80K                                                          │
│  对比旧管道875K: 节省 ~91%                                                      │
│  对比complexity_router理论S-Level(162K): 节省 ~51-63%                            │
│                                                                             │
│  关键差异 vs complexity_router S-Level:                                        │
│    1. 新增预编译上下文包——消除所有Agent对同一文件(宪法/P-STATE/canvas_rt/        │
│       参考图/空间地图)的重复加载                                                 │
│    2. Phase 0(Gate 0)移交调度器自执行——不消耗Agent调用和LLM token               │
│    3. Scene Auditor Phase 1明确跳过(S-Level·零价值)——节省~25K tokens            │
│    4. Phase 2降级(无PLAN→仅台本内部时间自洽)——节省~10K tokens                  │
└────────────────────────────────────────────────────────────────────────────┘
```

## 3.3 MVP到完整管道的降级路径

```
MVP (S-Level·~60-80K) ──→ 如果场景复杂度 > S-Level ──→ 自动升级

升级触发:
  任一F1-F7字段超过S-Level阈值 → 执行对应M/C-Level管道

M-Level (4-7 Agent):
  Wave 1: Shot Architect + Movement Designer(条件) + Composition Designer(条件)
  Wave 2: SDA + Storyboard Planner(条件)
  Wave 3: Prompt Composer
  Wave 4: SSA + Anchor Auditor P2(条件)

C-Level (~18 Agent):
  完整管道·dispatcher_v5.0.md §-2定义

关键原则:
  - 管道深度跟着场景复杂度走·不是反过来
  - 静态快速通道始终生效(>=80%固定→运镜域压缩)
  - 预编译上下文包在所有级别生效(消除重复加载)
  - Gate 0始终在调度器自执行·非Agent调用
```

---

# 4. 可立即消除的浪费清单

## 10项"今天就能删掉·零质量损失"的浪费

---

### 浪费项 #1: Movement Designer对静态场景的逐镜辩护段落

```
浪费类型: 🔴 纯浪费
场景: S/M-Level·>=80%固定镜
当前消耗: ~700行·~35-45K tokens/场景 (以EP14A为例)
删除内容: "镜#N固定·因为角色处于静止状态·固定镜头有助于..." 及所有静态例外论证段落
替代方案: 静态快速通道——运镜节一句 "本场景全部镜头固定。仅镜#X: 推近0.05x·S1。"
         已在scene_designer §5.4中定义·R-SFAST-01~03三条硬规则
风险评估: 零风险。固定镜头不需要辩护。默认就是什么都不做。
         管道铁律#6(运镜必须有动机)不应被误解为"必须写辩护段落"。
         动机可以用一个KB规则ID(M-MOT-01)标注·不需要700行论证。
估计节省: ~35K tokens/场景
适用级别: S-Level(全覆盖) · M-Level(静态快速通道触发时) · C-Level(静态快速通道仍压缩固定镜)
```

---

### 浪费项 #2: SDA Phase 1在S-Level场景上的完整执行

```
浪费类型: 🔴 纯浪费
场景: S-Level (单室·<=3说话角色·简单对话)
当前消耗: ~25K tokens (Scene Auditor Phase 1·EP14实测)
        旧SDA: ~144K tokens (独立Agent·含指令加载和完整审计输出)
删除内容: Phase 1全部五个维度(1A-KB覆盖率·1B-帧间连续性·1C-参考图锚定·1D-空间可行性·1E-覆盖完整性)
替代方案: S-Level场景的设计审计发现率趋近于零(EP14A: 零阻断·零新发现)
         单室→空间可行性自动满足
         静态镜头→无运镜越界风险
         KB覆盖率在Scene Designer指令中被R6硬约束强制要求
         → S-Level Scene Auditor直接跳过Phase 1·从Phase 0→Phase 2
风险评估: 极低。红队审计v2已确认"Phase 1在S级场景上发现率趋近于零"(维度四裁决)。
         如果Scene Designer未遵守KB引用约束→Phase 3的宪法第零条检查仍能捕获。
估计节省: ~25K tokens/场景 (新架构) · ~144K tokens/场景 (旧架构)
适用级别: S-Level · M-Level可降级为精简版(仅检查1C+1D·跳过1A+1B+1E)
```

---

### 浪费项 #3: Gate 0确定性检查嵌入LLM审计而非调度器自执行

```
浪费类型: 🔴 纯浪费
场景: 所有级别·所有场景
当前消耗: SSA用177K tokens LLM调用检测了3项正则可检测的阻断
         Scene Auditor Phase 0用~3K tokens(含Agent调用开销·非纯正则成本)
删除内容: Gate 0从Agent调用中移除·改为调度器自执行
替代方案: 调度器在Scene Designer完成台本初稿后·立即自执行R01-R15正则扫描
         纯正则·零LLM·零Agent调用·~0.5K tokens(正则引擎执行成本)
         仅在全部✅后才启动Scene Auditor Agent
         阻塞: 调度器读取台本文件→逐条R01-R15→输出GATE0_PRE_REPORT.md
         成本: 0 tokens (调度器自执行·正则无模型判断)
风险评估: 零风险。所有R01-R15均为100%准确率的正则/数值/模式匹配检查。
         画布宪法第五条:"确定性优先于概率性·Gate 0(100%) > LLM验证(~73%)"
         这是宪法本身的要求——当前违反了自己的宪法。
估计节省: ~175K tokens/场景 (旧SSA全部) · ~3K tokens/场景 (新Scene Auditor Phase 0)
         注意: SSA仍然需要(台本域的深度宪法检查·Phase 3)·但Gate 0部分移除
适用级别: 所有级别·全管道
```

---

### 浪费项 #4: KB完整文件加载·路由后仍加载60K而非提取10K摘要

```
浪费类型: 🟡 低效
场景: 所有需要KB的Agent
当前消耗: 每个Agent加载完整KB文件~40-60K tokens·实际使用~10-15K(路由命中的章节)
         6个Agent × 60K = ~360K tokens加载·实际需要: 6 × 10K = ~60K
         纯浪费: ~300K tokens
删除内容: Agent的"Read 03_导演知识库_v5.0.md 完整文件"调用
替代方案: 调度器在管道启动时·根据场景类型预提取KB摘要
         操作: kb_index_v2.0.md路由 → 从KB文件中提取对应章节的规则文本
         → 保存为 KB_SUMMARY_[场景名].md (~10K tokens)
         → 各Agent Read KB_SUMMARY 替代 Read KB完整文件
         这可以在调度器层实现·不改变任何Agent指令文件
风险评估: 低。kb_index_v2.0的路由逻辑已完整·场景类型判定已定义。
         唯一风险: 路由遗漏了某条关键规则·导致Agent在摘要中找不到。
         缓解: KB_SUMMARY尾部保留"完整KB文件路径·如需查阅非路由规则请Read"
         但禁止Agent默认加载完整KB。
估计节省: ~150-300K tokens/场景 (取决于Agent数量·含6-7个Agent的KB加载)
         注意: 这是"跨Agent累计"节省·非单Agent节省
适用级别: 所有级别·所有场景类型
```

---

### 浪费项 #5: OBJECT_TIMELINE在S-Level场景(F7<=3)的预生成

```
浪费类型: 🟡 低效
场景: S-Level·跨镜追踪物品数<=3
当前消耗: Step 0.5 调度器自执行→生成OBJECT_TIMELINE.md·但在S-Level台本中零O-ID引用
         26个物品定义·零消费
删除内容: S-Level·F7<=3时跳过Step 0.5 OBJECT_TIMELINE生成
替代方案: complexity_router §6已设计此跳过逻辑·但需要实际部署
         物品存在性由Scene Auditor设计审计维度覆盖(空间锚定检查捕获凭空出现)
         对于只有<=3个跨镜物品的简单场景·正则级存在性检查足够
风险评估: 低。红队审计v2已确认WARN-4(S-Level物品存在性验证执行真空)
         但该警告的核心是"跳过OBJECT_TIMELINE后·谁负责验证物品存在性"
         解决方案: Scene Auditor Phase 3追加一条正则检查——扫描台本物品清单
         vs 参考图物品清单·检测凭空出现物品
         对于S-Level场景(<=3跨镜物品)·正则检查完全足够
估计节省: 跳过Step 0.5调度器自执行时间 + 避免26个未被引用的O-ID占用文件空间
         直接token节省: 有限(调度器自执行·非LLM)
         间接节省: 减少管道步骤·减少文件数量·减少认知负担
适用级别: S-Level(F7<=3)·M-Level(F7<=3)
```

---

### 浪费项 #6: Storyboard Planner在S-Level场景的全量TIME_SKELETON生成

```
浪费类型: 🔴 纯浪费
场景: S-Level·<=5句对白·全硬切·无复杂时序
当前消耗: Storyboard Planner ~136K tokens·产出31帧TIME_SKELETON+PLAN
         但S-Level场景: 对白直接嵌入台本音轨(<=5句·无复杂时序)
         TIME_SKELETON的价值: 在S-Level场景上→对白时序对齐(但<=5句·手动对齐即可)
删除内容: S-Level管道的Step A2.5 Storyboard Planner
替代方案: Scene Designer直接输出台本·对白嵌入【生成指令】音轨段
         复杂度路由R-SFAST-05: "<=5句对白→直接写入音轨·不通过PLAN中转"
         时间轴由Scene Designer在台本初稿中直接管理
         场景级共享锚点(C1-C4)由Scene Designer从ANCHOR_BASELINE提取
风险评估: 低-中。TIME_SKELETON的核心价值=多段运镜过渡+多道具状态变化+多角色协同
         S-Level场景(单室·静态·<=5句对白)没有TIME_SKELETON的核心应用场景
         失去: 结构化的逐秒时间轴(对S-Level场景·导演台本自身就提供了逐秒描述)
         保留: 台本内部时间自洽检查(Scene Auditor Phase 2降级模式)
估计节省: ~136K tokens/场景 + 1个Agent调用
适用级别: S-Level全场景·M-Level条件(F3<=5 AND F1=1时跳过)
```

---

### 浪费项 #7: 多Agent对P-CONSTITUTION的重复加载·改为预编译上下文包

```
浪费类型: 🔴 纯浪费
场景: 所有管道·所有Agent
当前消耗: 7+ Agent各自Read P-CONSTITUTION.md + canvas_runtime.md + P-STATE.md
         每次~3-5K tokens × 7 = ~21-35K tokens纯重复
         文件内容完全不变——每次Read的结果完全一致
删除内容: Agent指令中的"Read P-CONSTITUTION.md"行(针对引用型文件)
替代方案: 预编译上下文包——调度器一次性合并宪法关键条款·P-STATE规避清单·平台约束
         输出: CONTEXT_PACKAGE.md
         Agent读取CONTEXT_PACKAGE替代读取三个独立文件
         引用格式不变: "参照画布宪法第X条" —— 文本已在上下文包中
风险评估: 零风险。这是"加载方式"的改变·不是"内容"的改变。
         宪法文本、P-STATE数据、平台约束完全不变。
         唯一变更: 从"每个Agent Read三个文件"改为"每个Agent Read一个合并文件"
         合并文件内容 = 三个文件内容的去重并集
估计节省: ~15-25K tokens/场景(跨Agent累计)
适用级别: 所有级别·全管道
```

---

### 浪费项 #8: 禁止清单中的纯模糊词(已被Gate 0 R06覆盖·Agent不再需要LLM检测)

```
浪费类型: 🟡 低效
场景: 所有台本产出
当前消耗: Scene Script Auditor在Phase 3维度3D中·用LLM检测"禁止清单精确度"
         但Gate 0 R06已用正则扫描了"纯模糊词"("稳""舒服""自然""好看")
         Phase 3 LLM检测是对同一条正则规则的概率性再确认——浪费
删除内容: Phase 3维度3D中与Gate 0 R06重叠的"禁止清单模糊词"检查
替代方案: Phase 3维度3D仅保留Gate 0无法检测的部分:
         3D02(禁止与生成指令矛盾——需要语义理解)
         3D03(禁止重叠与冗余——需要语义理解)
         3D01(可逐项检查性——可改为正则: 检查每条禁止是否有具体量化描述)
风险评估: 极低。Gate 0 R06的正则准确率100%。
         Phase 3保留的3D02和3D03是真正需要LLM的语义检查。
估计节省: ~3-5K tokens/场景 (Phase 3维度3D的精简)
适用级别: 所有级别
```

---

### 浪费项 #9: Scene Designer中S-Level场景的"设计依据"块

```
浪费类型: 🔴 纯浪费
场景: S-Level·Scene Designer输出
当前消耗: [设计依据]块在台本中占~15-20%篇幅·仅供人类审核
         但Scene Auditor的SW-C03明确声明"不读【设计依据】块"
         P-Verifier不读·Render Packager去冗余时移除
         → 设计依据的唯一消费者是人类·但在S-Level的流水线中人类只审最终交付物
删除内容: Scene Designer S-Level输出中的【设计依据】块
替代方案: KB规则ID直接在【镜头参数卡】中标注(作为元数据·不进入Seko可执行块)
         审计Agent通过KB规则ID检查合规性(SW-C05: 两个规则来源)
         人类审核时查看【镜头参数卡】中的KB标记即可理解设计意图
风险评估: 零风险。设计依据块是"人类审核辅助"·不是"管道消费结构"
         S-Level场景的设计决策如此简单(<=3个机位·全固定·<=5句对白)
         KB规则ID标注已充分说明设计依据
估计节省: ~5-8K tokens/场景
适用级别: S-Level全场景·M-Level可选
```

---

### 浪费项 #10: Scene Anchor Auditor在单场景(S-Level)的跨场景锚点检查

```
浪费类型: 🔴 纯浪费
场景: S-Level·单场景剧本(无跨场景锚点需求)
当前消耗: Step A1快照格式检查 + Step A3后阶段2锚点对比验证
         单场景剧本: 没有"上一场景的快照"可读取
         "首场景跳过"逻辑已定义·但调度器仍然需要检查→判定跳过→消耗调度步骤
删除内容: 单场景剧本的Step A1和Step A3后Anchor Auditor P2
替代方案: complexity_router预检查: 场景数==1 → 自动跳过所有锚点审计
         R-SFAST-06已定义"跳过Step A1, Step A3后Anchor Auditor, A4A, A4B"
风险评估: 零风险。单场景无跨场景锚点·无快照·无阶段2对比对象。
         检查对象不存在→审计无意义。
估计节省: 1-2个Agent调用 + ~137K tokens (Anchor Auditor P1实测·EP14)
适用级别: 场景数==1的所有级别
```

---

## 4.1 浪费汇总

| # | 浪费项 | 类型 | 单场景节省(token) | 节省来源 |
|:-:|--------|:---:|--------:|---------|
| 1 | Movement Designer静态辩护段落 | 🔴 | ~35K | 运镜域·静态快速通道 |
| 2 | SDA Phase 1在S-Level的执行 | 🔴 | ~25K(新)/~144K(旧) | 审计域·S-Level降级 |
| 3 | Gate 0嵌入LLM而非调度器自执行 | 🔴 | ~175K(旧SSA)/~3K(新) | 审计域·确定性前置 |
| 4 | KB完整文件加载·非提取摘要 | 🟡 | ~150-300K(跨Agent) | 知识域·预提取摘要 |
| 5 | OBJECT_TIMELINE在S-Level的预生成 | 🟡 | 间接(步骤+文件) | 调度域·条件跳过 |
| 6 | Storyboard Planner S-Level全量TIME_SKELETON | 🔴 | ~136K | 骨架域·S-Level跳过 |
| 7 | P-CONSTITUTION多Agent重复加载 | 🔴 | ~15-25K(跨Agent) | 上下文域·预编译包 |
| 8 | 禁止清单LLM重复检测已正则覆盖项 | 🟡 | ~3-5K | 审计域·去冗余 |
| 9 | S-Level设计依据块 | 🔴 | ~5-8K | 输出域·精简格式 |
| 10 | 单场景跨场景锚点审计 | 🔴 | ~137K + 2 Agent | 审计域·条件跳过 |

**10项合计节省: ~680-850K tokens/场景 (含跨Agent累计·全管道·旧架构基线)**

**如果只计算新架构(S-Level·2 Agent): ~65-85K tokens/场景节省·MVP从162K降至60-80K**

---

# 5. 架构改进路线图

## 5.1 优先级矩阵

```
                    高影响
                      │
         Gate 0前置   │   KB摘要提取
         浪费#3       │   浪费#4
                      │
   Movement静态辩护   │   SDA S-Level跳过
   浪费#1             │   浪费#2
                      │
   ──────────────────┼──────────────────
                      │
   设计依据块         │   OBJECT_TIMELINE
   浪费#9            │   浪费#5
                      │
   Storyboard跳过     │
   浪费#6             │
                      │
                    低影响
   
   左: 易实施(指令修改)          右: 需要新基础设施(预编译器)
```

## 5.2 实施顺序

```
第一优先级 (本周可完成·零新代码):
  浪费#1: Movement Designer静态辩护删除 → 在scene_designer §5.4中强制执行R-SFAST-01~03
  浪费#3: Gate 0调度器自执行 → 在dispatcher中定义调度器自执行Gate 0的正则清单
  浪费#9: S-Level设计依据块删除 → scene_designer S-Level输出模板中移除该块

第二优先级 (需场景路由部署):
  浪费#2: SDA Phase 1 S-Level跳过 → scene_auditor S-Level降级策略
  浪费#6: Storyboard Planner S-Level跳过 → complexity_router R-SFAST-05
  浪费#10: 单场景锚点审计跳过 → complexity_router R-SFAST-06

第三优先级 (需新基础设施):
  浪费#4: KB摘要提取 → 新建kb_extractor(调度器自执行·从KB文件中提取路由命中的规则文本)
  浪费#7: 预编译上下文包 → 新建context_compiler(合并宪法+P-STATE+canvas_rt为单一文件)
  浪费#8: Phase 3与Gate 0重叠项移除 → scene_auditor Phase 3去冗余

条件跳过(依赖复杂度路由F7判定):
  浪费#5: OBJECT_TIMELINE条件跳过
```

---

## 附录A: 关键数字速查

| 指标 | 旧管道(C-Level) | 新架构理论S-Level | MVP | MVP vs 旧 |
|------|:---:|:---:|:---:|:---:|
| Agent调用 | ~18 | 2 | 2 | -88.9% |
| Tokens | ~875K | ~162K(估) | ~60-80K | -91.4% |
| Wall-Clock | ~58分钟 | ~15分钟(估) | ~8分钟(估) | -86.2% |
| 设计:审计比 | 0.93:1(倒挂) | ~1:1 | ~2:1(设计主导) | 正常化 |
| 零价值Agent | 5+(Mov/SDA/SSA Gate0/Anchor单场景/Storyboard S-Level) | 0(理论·未实现) | 0 | 消除 |
| Gate 0执行者 | P-Verifier(Agent·LLM) | Scene Auditor Phase 0(Agent·LLM) | 调度器(自执行·零LLM) | 架构修正 |

## 附录B: 红队审计v2四个阻断项的修复状态

| 阻断项 | 问题 | 本报告对应浪费项 | 修复优先级 |
|--------|------|:---:|:---:|
| BLOCK-1 | Gate 0 R14/R15编号冲突 | 浪费#3(Gate 0前置) | P0 |
| BLOCK-2 | scene_auditor M-Level缺失 | 架构补全·非浪费 | P1 |
| BLOCK-3 | scene_designer S/M级描述矛盾 | 浪费#1(静态快速通道) | P0 |
| BLOCK-4 | S-Level台本初稿格式未定义 | 浪费#9(设计依据)+MVP §7.5 | P0 |

---

> **架构冗余审计签名:** EP14_ARCHITECTURE_WASTE.md
> **审计范围:** MODE:P管道 v6.1 全链路·以EP14场景A为解剖标本
> **核心发现:** 管道中存在4类结构性浪费(重复读取·过深度管道·KB膨胀·形式主义产出)·10项可立即消除·零质量损失
> **最小可行管道:** 2 Agent·~60-80K tokens·节省91% vs 当前C-Level管道
> **最严重浪费:** Movement Designer的978行静态辩护(有效信息密度0.1%)·SDA的1,040行零阻断审计·SSA用177K tokens检测了3项正则可发现的阻断
> **架构悖论:** 宪法第五条要求"确定性优先于概率性"·但Gate 0确定性检查却嵌入在LLM审计之后执行
