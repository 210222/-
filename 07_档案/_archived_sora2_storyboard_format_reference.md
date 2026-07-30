# Sora 2.0 故事板模式 — 格式参考（已归档·非 MODE:P 格式）

> **来源:** OpenAI Cookbook (官方)
> **状态:** ⚠️ 已归档·MODE:P 当前故事板格式见 storyboard_previewer_v1.0.md §4
> **归档原因:** 目标模型已从 Sora 2.0 切换为 sd2.0 (Seedance 2.0)·此文件仅作历史参考

---

## 一、Sora 2.0 故事板核心概念

### Storyboard 模式是什么
- 多关键帧视频生成功能（Sora 2 Pro · $200/月）
- 用多个独立关键帧定义场景，Sora 自动插值帧间运动/转场/连续性
- 关键帧数: 2-5帧常用（建议从2帧开始验证稳定性，再扩展到3-4帧）
- 支持部分重新生成（单关键帧重渲，不重做全片）
- 时长: 每API调用4-20秒·Storyboard模式下最长25秒（Pro）·扩展拼接最长120秒

### 单Prompt模式 vs Storyboard模式

| | 单Prompt | Storyboard |
|------|------|------|
| 场景控制 | 一个全局描述 | 每关键帧独立描述 |
| 时长控制 | 固定 | 每段独立分配 |
| 跨镜一致性 | >8秒后容易漂移 | 锚点关键帧保持连贯 |
| 编辑 | 全部重做 | 单场景修改 |

---

## 二、四元素关键帧模板（每关键帧必须包含）

```
--- Character Anchor: 逐帧逐字复制的角色描述（不可改一字）
--- Scene Anchor:    逐帧逐字复制的场景描述（不可改一字）
--- Camera & Framing: 每帧可变（景别/角度/运镜）
--- Action Beat:      每帧一个具体动作（禁复合动词）
```

### Character Anchor 规则
- 每个关键帧中完全相同的角色描述·逐字复制·不改措辞
- 不同措辞 → 模型理解为不同人物 → 面部/服装漂移
- 包含: 年龄/性别/发型/发色/服装/身体特征/手持物
- 例: `Hong Kong woman, early 30s, shoulder-length black hair, tailored charcoal-gray blazer with white blouse`

### Scene Anchor 规则
- 每个关键帧中完全相同的场景描述·逐字复制
- 包含: 地点/时间/天气/光源/关键物体/空间关系
- 例: `Minimalist white studio, soft daylight from left, polished concrete floor, no props`

### Camera & Framing 规则
- **一镜仅一种运镜** — 不同时做dolly+升降
- 景别: wide / mid / medium close-up / close-up / extreme close-up
- 运镜: fixed / slow dolly-in / slow dolly-out / tracking L→R / slow orbit / handheld / crane rise / tilt
- 焦距: 24mm / 35mm / 50mm / 85mm / 100mm macro
- 景深: shallow DOF / deep focus / f/2.8 / f/8

### Action Beat 规则
- **一拍一动词** — 禁止"walk, pick up book, turn"在一个beat里
- 用精确动词+计数: "takes four steps" 而非 "walks across"
- 用beat+t时刻: "Beat 1 (0-2s): sets down chopsticks"

---

## 三、七段结构化提示词框架（官方Cookbook·单镜或Storyboard通用）

```
① Format & Look      — 时长·快门·媒介·颗粒·风格锚
② Style              — 视觉参考·胶片类型·调色风格·导演影响
③ Scene              — 地点·时间·天气·在场人物·背景活动
④ Photography        — 焦距·光圈·景深·运镜·对焦行为
⑤ Lighting           — 主光·补光·边缘光·色温·阴影质量·物理锚点
⑥ Action (Beats)     — 逐秒动作·一动词一拍·带时间戳
⑦ Sound              — 环境声·拟音·对白·无配乐·End Frame指令
```

### 完整模板

```
Format: [类型], [时长]s, [镜头特征].

Style: shot on [胶片/媒介], [颗粒/质感], [调色板] in [主色] and [辅色],
[halation/光晕效果]. Influenced by [参考导演/电影].

Scene: [精确地点], [时间], [天气/环境].
[在场人物]. [背景活动].

Photography: [焦距] [镜头类型], [光圈/景深],
[运镜 — 仅一种].

Lighting: [主光来源], [色温], [阴影质量].
[补光/边缘光/实用灯].

Action:
--- Beat 1, 0 to N seconds: [主体动作], [摄影机行为].
--- Beat 2, N to M seconds: [主体动作], [摄影机行为].
--- Beat N, M to Z seconds: [主体动作], [摄影机行为].

Dialogue: [脚本带说话者标签, 或 "no dialogue, ambient only"].

Sound:
--- Ambient: [背景声].
--- Foley: [特定动作声].
--- Music: [类型和情绪, 或 "none"].

End frame: [最终画面描述].
```

---

## 四、多镜Storyboard模板（Shot-List格式）

```
Shot 1:
  duration: 4.0 sec
  Scene: [景别·角度·运镜·地点]
  Character: [在场人物]
  Action: [动作·用beats描述]
  Emotion: [情绪/氛围]
  Details: [视觉细节·灯光·调色板]
  Audio: [环境声·拟音·对白]
  Transition: [转场方式 或 "none"]

Shot 2:
  duration: 6.0 sec
  Scene: ...
```

### 多镜一致性规则
- **Style spine** — 15-25字的风格锚短语，逐镜重复
- **Palette anchors** — 3-5个颜色锚点词贯穿全片（如 `amber, cream, walnut brown, slate, olive`）
- **Character anchor** — 每镜逐字复制角色描述
- **Scene anchor** — 每镜逐字复制场景描述（同场景时）
- **一镜一运镜** — 不复合运镜
- **一镜一拍一主体动作** — 不在同一block内切换景别/运镜类型
- **转场明确标注或标注"none"** — 否则模型可能随机过渡

---

## 五、API参数（不在Prompt文本中）

| 参数 | 值 | 说明 |
|------|------|------|
| `model` | `sora-2` 或 `sora-2-pro` | 模型选择 |
| `size` | `1280x720` / `1920x1080` / `1080x1920` 等 | 分辨率 |
| `seconds` | `4` / `8` / `12` / `16` / `20` | 时长（API参数控制·写prompt里无效） |
| `characters` | 最多2个角色ID | 通过Characters API上传参考视频创建 |
| `storyboard` | `true` / `false` | 启用多场景模式 |
| `input_reference` | 图像文件(JPEG/PNG/WebP) | 首帧锚定·必须匹配目标分辨率 |

---

## 六、禁止事项（prompt文本中的排除项）

- 用描述性否定: "no Dutch angles" / "no on-screen text"
- 2-4条排除项最有效
- 不要:"make it longer" "HD resolution" — 这些是API参数不是prompt

---

## 七、常见失败模式

| 错误 | 后果 | 修复 |
|------|------|------|
| 每帧字符描述不同 | 角色变形漂移 | 逐字复制anchor |
| 一拍多个复合动作 | 急促/机器人式运动 | 一拍仅一动词 |
| 未指定灯光 | 帧间光线随机漂移 | 固定灯光+色温·逐帧重复 |
| 直接跳到5+关键帧 | 更长的生成时间·更多断裂 | 从2帧开始·验证稳定后扩展 |
| 运镜复合 | 运动混乱 | 一镜仅一种运镜 |

---

> **v1.0 · 2026-07-04**
> **对MODE:P的影响:** STORYBOARD.md格式应从当前"每镜独立描述"重构为"全局Anchor + 逐镜差异化字段"。
> Character Anchor和Scene Anchor从MODE:A增强剧本提取·全片统一·逐镜逐字复制。
> Camera & Framing每镜独立（已有参数卡）。
> Action Beat格式从连续叙述改为Beat分节。
> 增加Style Spine和Palette Anchors作为全片级锁定。
