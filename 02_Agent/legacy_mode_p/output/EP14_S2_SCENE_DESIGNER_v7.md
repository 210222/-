# S2 Scene Designer Report — EP14 案情室

> **MODE:P Step A2 · Scene Designer v1.0 · S-Level合并式三域设计**
> **场景:** 圣保罗刑警总部·案情室 | 7镜·31秒·1室2人·4句对白
> **复杂度:** 🟢 S-Level (F1=1 F2=2 F3=4 F4=86% F5=false F6=false)
> **继承:** EP14 pattern — 室内对话_单室_面对面 (已验证相机方案: 全景24mm→中景35mm→中近景50mm)
> **静态快速通道:** ✅ 激活 (86% ≥ 80%)

---

## §0 继承声明 — 来自历史模式

本场景匹配 `04_共享/decision_patterns/室内对话_单室_面对面/pattern.json` (EP14 案情室·7镜·31秒·2人)。

**继承已验证方案:**
- 机位结构: 全景24mm建立→中景35mm对话→中近景50mm单人（全继承不变）
- 光影方案: 天花板格栅灯5000K冷白均匀照明 + 走廊3500K暖黄（镜#A4/#A7）
- 运镜方案: 86%固定·仅镜#A2极慢前推0.05x（全继承不变）
- design_lesson: 50mm=对话场景甜区焦距·单室自动满足空间连续性·S-Level完全足够

**以下只列出差异:** 无差异·本场景同EP14案情室·全方案继承·唯角色锚点从ANCHOR_BASELINE逐字锁定。

---

## §1 场景类型判定 + 空间坐标系（三域共享·只写一次）

```
📐 场景类型 = [对话场景·双人·案情分析]
   角色数 = [2: Miguel(主导) + Vincent(门口探头)]
   complexity = [S]
   对白 = [4句: Vincent 2句 + Miguel 2句]

空间尺寸: 纵深~6m × 宽度~4m × 高度~3m·全封闭无窗·矩形
关键建筑元素:
  - 北墙: 巨大白色白板(2.4m×1.2m·占满墙面·视觉重心)
  - 南侧: 合并办公桌×2·距白板~1-2m·堆满文件/笔记本/咖啡杯
  - 西墙: 灰色金属门(宽~1m·高~2.1m·不锈钢把手)
  - 东墙: 素灰墙面·无窗
  - 天花板: 四个方形格栅发光顶灯(5000K冷白·无影灯设计)

人物可放置区域:
  ① 白板前0.5-2m (主表演区·Miguel站姿)
  ② 办公桌前/西侧 (Miguel取物区)
  ③ 办公桌后/电脑位 (次要人物区)
  ④ 门框区 (Vincent探头区)
  ⑤ 房间中央·距白板~3m (全景机位区)

180度线设定:
  关系线: Miguel ↔ 白板中心 (南北向·视线轴沿南北)
  轴线侧选择: A侧(西侧·门所在侧)
  选取理由: 门在西墙·西侧可同时覆盖白板前Miguel+门口Vincent

光源物理锚点:
  主光源: 天花板格栅灯×4·5000K冷白·锚定参考图上排
  第二光源a: 笔记本电脑屏幕·~6500K冷蓝·锚定参考图下排
  第二光源b: 门外走廊3500K暖黄(推断·已标注物理属性·仅镜#A4/#A7)

空间约束速查:
  禁入区: 白板至墙面(过窄·不可站人)·天花板以上
  窄区: 门框宽度~1m·禁横移运镜·禁大幅摇镜
  推断空间: 门外走廊(已标注物理属性·宽~1.5m·暖黄照明)
```

---

## §2 场景级静态比例预判

```
通读7镜头方向卡:
  镜#A1: 固定  | 镜#A2: 极慢前推(0.05x) | 镜#A3: 固定
  镜#A4: 固定  | 镜#A5: 固定              | 镜#A6: 固定
  镜#A7: 固定

静态占⽐ = 6/7 = 86% ≥ 80%
→ ✅ 静态快速通道激活（R-SFAST-01~06强制生效）
```

---

## §3 覆盖策略速选 (Step A-S1)

从8机位模板(双人对话)选出7个必要机位:

| 机位 | 类型 | 景别 | 焦距 | 叙事功能 |
|:----:|------|:----:|:----:|---------|
| A1 | 全景建立 | 全景 | 24mm | 建立空间·两人位置关系·全室信息 |
| A2 | 插入镜头 | 大特写 | 85mm | 揭示·情绪锚点·Rico照片+红线缠颈 |
| A3 | 单人Miguel | 中景 | 50mm | 推进·Miguel审视证据·面部表情叙事 |
| A4 | 单人Vincent | 中景 | 35mm | 引入·Vincent门口探头·冷暖交界 |
| A5 | 反应Miguel | 近景 | 85mm | 对话回应·Miguel面部微表情 |
| A6 | 插入·过渡 | 中景 | 50mm | 物理动作·Miguel拿外套+车钥匙 |
| A7 | 再交代 | 中全景 | 35mm | 场景出口·门框构图·冷暖分界 |

**未使用:** 过肩A/B — 单室面对白板非互视对话·无需OTS

KB规则ID: `D-TRI-04(三角形底边2机位+顶端1)`, `shared_agent_runtime.md §4·8机位模板-1/2/3/6/7/8`

---

## §4 逐镜机位速记 (Step A-S2)

```
#A1 | 全景     | 全景建立     | 24mm | 深景深f/8 | 眼平·1.6m·房间中央⑤ | 轴上·neutral | D-TRI-03
#A2 | 大特写   | 插入         | 85mm | 浅景深f/2.8 | 白板前①·距板0.4m→0.2m | 轴上·插入 | D-TRI-05
#A3 | 中景     | 单人Miguel  | 50mm | 中景深f/4 | 白板与桌间西侧①·距板1.8m | A侧 | D-TRI-02
#A4 | 中景     | 单人Vincent | 35mm | 中深f/5.6 | 门内侧④·距门1.5m | A侧 | D-TRI-02
#A5 | 近景     | 反应Miguel  | 85mm | 浅景深f/2.8 | 白板与桌交界①/②·距脸1.5m | A侧 | D-TRI-02·E-MTC-04
#A6 | 中景     | 插入·过渡  | 50mm | 中景深f/4 | 办公桌西侧②·距桌0.5m·1.3m低 | A侧 | D-TRI-02
#A7 | 中全景   | 再交代      | 35mm | 深景深f/8 | 门框外走廊·距门0.8m | A侧延伸 | D-TRI-02
```

**景别递进:** LS→ECU→MS→MS→CU→MS→MLS (V形曲线·相邻跳跃≤3级 ✅)

---

## §5 运镜处理 — 静态快速通道 (Step A-S3)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎥 运镜域: 静态快速通道激活 — 6/7镜固定
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

6/7镜固定·制度空间静态凝视。仅在以下镜头执行运动:
  · 镜#A2: 极慢前推(0.05x·S1)·沿光轴正向白板·行程~20cm·4秒匀速
    动机: Rico照片ECU推近·从"照片上的一个人名"到"被红线缠颈的人"·
          全场景唯一的运镜鼓起·制度空间的"心跳"

动态镜占比: 1/7 = 14%。静态快速通道完成。

禁止输出: 已跳过逐镜静态论证·速度分布统计·加速度波形·两极分化检查
```

---

## §6 构图光影速记 (Step A-S4)

### 6.1 构图速记

```
#A1 | 主体: 白板+Miguel背身   | 3层(前景桌面30%+中景Miguel25%+后景白板45%) | 单点透视·汇聚至白板中央 | 封闭构图·深空间 | C-KTZ-01·C-DEP-01
#A2 | 主体: Rico照片+手指    | 3层(前景手指25%+中景照片60%+后景白板15%) | 红线放射·指向画外201红圈 | 封闭·极浅空间 | C-AJS-01
#A3 | 主体: Miguel面部+背景红网 | 3层(前景领口5%+中景Miguel70%+后景红网虚化25%) | 垂直站姿+斜线红网 | 开放构图·中景空间 | C-FI-03
#A4 | 主体: Vincent门框探头  | 3层(前景门框15%+中景Vincent70%+后景白板15%) | 竖线门框+横线门上缘 | 框中框·制度画框 | C-FI-14
#A5 | 主体: Miguel面部       | 2层(前景面部85%+后景红网虚化15%) | 斜线视线+水平眉线+竖眉心纹 | 封闭·浅空间·极亲密度 | C-KTZ-02
#A6 | 主体: Miguel双手动作  | 3层(前景桌面15%+中景上身65%+后景白板20%) | 斜线双手X型交叉 | 开放·框取动作 | C-FI-02
#A7 | 主体: Miguel门框+全室 | 4层(前景门框10%+中景Miguel50%+走廊5%+后景白板35%) | 竖门框+透视汇聚 | 框中框·深空间 | C-FI-14·C-DEP-01·C-FI-16
```

### 6.2 光影速记

```
#A1 | 格栅灯5000K冷白·顶光均匀·无阴影·低光比1:1.5 | 白板最亮→桌面→Miguel背身 | 冷酷基色(灰/白·90%)+冲撞红(红线/图钉·10%)
#A2 | 格栅灯5000K+白板柔反光·从上方+后方 | 照片面部→手指→红线 | 红图钉+红线=唯一饱和色·Miguel手指冷白下偏灰偏蜡
#A3 | 格栅灯5000K顶光·面部扁平化 | 额骨颧骨→眼珠方向→红网背景 | Miguel棕褐偏灰偏蜡·背景红线'血管网'
#A4 | 双光源: 室内5000K冷白(右)+走廊3500K暖黄(左) | Vincent右眼→镜片反光变化 | 冷暖交界线贯穿面部·白大褂右冷白左暖黄
#A5 | 格栅灯5000K顶光·眼窝微暗·下颌微暗 | Miguel右眼→背景红网'光环' | 肤色偏灰蜡·背景红线=红色'光环'·与#A2缠颈红线视觉回响
#A6 | 格栅灯5000K+笔记本6500K冷蓝微光 | 车钥匙金属反光→腕表→伤疤 | 从'分析者'灰蜡到'行动者'深藏青·过渡
#A7 | 双光源: 室内5000K冷白(右/后)+走廊3500K暖黄(左/前) | 双重焦点: 警徽(冷白/制度)+车钥匙(暖黄/行动) | 四色状态: 右冷白+左暖黄+后白板+前暖光柱
```

KB规则ID: `L-3PT-01(伦勃朗光)`, `L-CT-01(色温情绪)`, `COL-PRI-02(冷暖深度)`, `COL-PRI-03(高光暖·阴影冷)`

### 6.3 色彩策略 — global_anchors.style_spine

```
style_spine: "冷白制度凝视·灰色理性基调·红色冲撞血管隐喻·框中框构图·单点透视线性秩序·静态主导运镜"
palette_anchors:
  - "cold-white-5000K"
  - "neutral-gray"
  - "pure-white-whiteboard"
  - "blood-red-accent"
  - "warm-yellow-3500K-corridor"
  - "dark-navy-jacket"
  - "gold-badge-gleam"
```

---

## §7 轴线+空间速验 (Step A-S5)

```
轴线验证: 7镜·0次越轴·0次视线矛盾
  - 镜#A1-A2: 轴上·neutral ✅
  - 镜#A3-A7: A侧(西侧) ✅
  - A侧自然延伸至走廊(镜#A7)·空间连续·不越轴 ✅

空间约束: 7机位全部在人物可放置区域①-⑤内·不穿墙不悬空 ✅
  - 镜#A1: 区域⑤   | 镜#A2: 区域①  | 镜#A3: 区域①
  - 镜#A4: 区域④   | 镜#A5: 区域①/②| 镜#A6: 区域②
  - 镜#A7: 区域④走廊侧(推断·已标注物理属性) ✅

P-FAL规避: 全部规避 ✅
  - P-FAL-01: 瞳孔状态固定·不描述变化过程 ✅
  - P-FAL-02: 无mm级精确间距 ✅
  - P-FAL-03: 无亚秒级时序描述 ✅
  - P-FAL-04: 同时音效≤2层(环境声+SFX/CV) ✅
  - P-FAL-05: VO语速≤4字/秒 ✅
  - P-FAL-06: 宽~4m·不禁横移·但全部静态 ✅
  - P-FAL-07: 无高频视觉噪声·冷白均匀·制度空间 ✅
  - P-FAL-08: 白板文字=后期叠加 ✅
  - P-FAL-09: 无快速运动·极慢前推0.05x ✅
  - P-FAL-10: 交替单人口型·听者不在画面 ✅
```

---

## §8 五段式导演台本

---

### 【场景级共享锚点】(画布模式·场景头部一次性声明)

```
@参考图: 案情室.txt(上排+中排+下排) — 用途: 案情室全空间·白板线索墙·桌面工作区

C1 Character Anchor (逐字锁定·全7镜不可改一字):
  Miguel: "Latin male, 30-40s, short black curly hair with greying temples, wide cheekbones, square jaw, vertical crease between brows, deep brown eyes with detective scrutiny, solid build"
  Costume: "浅灰衬衫(纽扣领) + 深藏青警探夹克(哑光面料·拉链立领·前半段未穿搭椅背·后半段穿上)"
  Vincent: "Male, 30-40s, dark brown short hair slightly disheveled, thin build, cold white skin tone from indoor lab work"
  Costume: "白色实验室外套(长款·及膝) + 内搭深色衬衫 + 黑框眼镜(黑色板材·矩形框·核心视觉识别物)"

C2 Environment Anchor:
  "圣保罗刑警总部案情室·日间·全封闭室内(~6m深×~4m宽×~3m高)·无窗·纯人工照明·素灰色墙面·强烈单点透视。北墙: 巨大白色白板(~3-4m宽·占满墙面)·人物照片+红线网络+建筑平面图(201红圈)+弹道分析报告。南侧: 合并办公桌×2·距白板~1-2m·堆满文件/笔记本/咖啡杯/签字笔/笔记本电脑。西墙: 灰色金属门(宽~1m·高~2.1m·不锈钢把手)·外连走廊(3500K暖黄光·推断·已标注物理属性)。东墙: 素灰墙面·无窗。天花板: 四个方形格栅发光顶灯(5000K冷白·均匀·无影灯设计)。"

C3 Lighting Anchor:
  "主光源: 天花板方形格栅发光顶灯×4·5000K冷白·柔光·大面积均匀扩散·无影灯设计·全室(~6m×4m)覆盖·低光比约1:1至1:2。第二光源a: 笔记本电脑屏幕~6500K冷蓝微光·桌面局部半径~0.3m。第二光源b: 门外走廊暖黄光(推断·已标注物理属性)·3500K暖黄·从门外走廊漫射·经门框切割为矩形光柱·仅镜#A4/#A7出现·叙事功能: 打破冷白制度的均匀性。"

C4 Style Spine & Palette:
  "shot on Arri Alexa 35, cold-white institutional 5000K, neutral-gray palette, blood-red accent as vascular metaphor, frame-within-frame composition motif, single-point perspective linear order, static-dominant camera language"
  Palette: cold-white-5000K · neutral-gray · pure-white-whiteboard · blood-red-accent · warm-yellow-3500K-corridor · dark-navy-jacket · gold-badge-gleam
```

---

### 镜#A1: 全景 · 5s (global_sec 0-4)

【镜头参数卡】
- 景别: 全景 | 焦距: 24mm | 景深: f/8深景深
- 角度: 眼平·1.6m·正北朝向
- 机位: 房间中央·距白板~3m·区域⑤
- 轴线: 轴上·neutral
- 运镜: 固定(S0)
- KB: D-TRI-03·C-KTZ-01·C-DEP-01

【传入参考图】案情室.txt·上排空间布局 — 全室建立透视

【生成指令】
t=0: Miguel背对镜头站在白板前·深藏青夹克搭在椅背上未穿·站姿距白板~0.5m·面向白板线索墙。前景合并办公桌(文件堆叠·笔记本·咖啡杯·笔记本电脑屏幕亮着)→中景Miguel背影→后景巨大白色白板(人物照片·红线网络·建筑平面图201红圈·弹道分析报告)。天花板四个方形格栅发光顶灯·5000K冷白·全室均匀·无可见阴影。冷酷基色(灰/白/黑白)~90%+冲撞红(红线/红图钉)~5-10%。
t=1-3: Miguel背身站位稳定·建立镜头持续·全室透视不变·观众吸收空间信息。
t=4: 建立镜头最后时刻·Miguel位置不变·轻微布料摩擦声(Miguel抬手准备钉照片)。

音轨: 低音量空调运行声·办公室底噪·t=4 SFX布料摩擦声0.5s

【段末转场】硬切→镜#A2·从全室全景→Rico照片ECU·空间跳跃~2.6m

【禁止】
1. 白板文字/名字/日期/弹道报告=后期叠加·不在prompt中要求渲染文字(P-FAL-08)
2. 无负向词(不要/避免/禁止/不能)
3. 画面描述不含运镜语义(运镜在参数卡中已标明"固定")
4. 首帧零过程动词("刚/正在/开始")—用完成态"站在""搭在"
5. 无跨镜引用("同上"等)—每镜独立完整

---

### 镜#A2: 大特写 · 4s (global_sec 5-8)

【镜头参数卡】
- 景别: 大特写 | 焦距: 85mm | 景深: f/2.8浅景深
- 角度: 眼平·1.5m·与照片平齐·正北
- 机位: 白板前偏左·距板0.4m→0.2m·区域①
- 轴线: 轴上·插入镜头·天然中性
- 运镜: 极慢前推0.05x(S1)·直线光轴·总行程~20cm·匀速4秒
- KB: D-TRI-05·M-MOT-02·C-AJS-01

【传入参考图】案情室.txt·中排白板线索墙 — 照片+红线构图

【生成指令】
t=5: Miguel右手拇指指腹压紧红图钉·食指稳定照片边角·拇指将红色图钉按入Rico照片上边缘。Rico照片占据画面中心~60%面积·三年前颁奖台举奖杯·面无表情。红线从照片颈部穿过·向四周放射连接·指向201红圈方向。手指+红图钉=前景层·照片面部=中景层·白板表面+红线=后景层。红图钉+红线=唯一饱和色·Miguel手指棕褐色在5000K冷白下偏灰偏蜡。SFX: 图钉入白板"咔"声0.2s。
t=6: 图钉已按入·Miguel手指开始从照片边缘移开·极慢推近中·照片面部缓慢扩大·红线缠颈视觉强化。
t=7: 推近继续·Miguel手指完全退出画框·照片面部占~70%·红线从颈侧穿过细节清晰可见。SFX: 手指离开照片摩擦声0.3s。
t=8: 推近落定·距白板~0.2m·Rico照片面部占~80%面积·成为画面绝对主体·"面无表情"在极度逼近下变为冷峻·红线从颈侧穿过形成"缠颈"视觉·旧钉眼凹陷在边缘清晰可见·全场景情绪锚点顶峰。

音轨: 室内低频持续·t=5 SFX图钉"咔"声·t=7 SFX手指摩擦声

【段末转场】硬切→镜#A3·从Rico照片ECU→Miguel中景

【禁止】
1. 不描述瞳孔变化过程(P-FAL-01)—瞳孔状态固定
2. 红线缠颈视觉通过构图呈现·不写"窒息感/压迫感"等抽象情绪词
3. 无"仿佛/如同/似乎"等文学修饰词
4. 运镜"极慢前推"仅在参数卡中描述·不在【生成指令】中混入运镜语义
5. 首帧零过程动词("正在按入"改为完成态)

---

### 镜#A3: 中景 · 5s (global_sec 9-13)

【镜头参数卡】
- 景别: 中景 | 焦距: 50mm | 景深: f/4中等景深
- 角度: 眼平·1.6m·东偏南朝向
- 机位: 白板与桌之间西侧(A侧)·距白板~1.8m·区域①
- 轴线: A侧(西侧)
- 运镜: 固定(S0)
- KB: D-TRI-02·C-FI-03·L-3PT-01

【传入参考图】案情室.txt·中排白板线索墙 — Miguel审视角度

【生成指令】
t=9: Miguel身体刚完成后移动作·重心后移·双臂垂放或微交叉·后退一步——从"钉照片"切换到"审视证据网"。上身位于画面左三分线·视线方向(画右上方·看向白板线索网)留白。前景衬衫领口+金色警徽(5%)→中景Miguel上半身·面部核心(70%)→后景白板红线网络虚化为色块和线条·形成红色"血管网"在Miguel肩后(25%)。50mm f/4中等景深·后景虚化但可辨识。Miguel棕褐色在5000K冷白下偏灰偏蜡——"分析者"状态。
t=10-12: 审视继续·眼珠从左向右移动·追踪红线逻辑路径·眉心竖纹持续·t=11眼珠追踪至201红圈方向·短暂停顿·大脑连接线索。
t=13: 审视结束·身体微倾向门口方向·即将切换至对话状态。SFX: 轻微脚步声从走廊方向传来(画左·门外·0.5s)。

音轨: 低音量空调运行声·办公室底噪·t=13 SFX脚步声0.5s

【段末转场】硬切→镜#A4·从白板侧Miguel→门口Vincent·空间跳跃~3m

【禁止】
1. 不写"仿佛在思考/似乎在回忆"等模糊表述——只写可见的面部/眼球动作
2. 画面描述不含运镜语义
3. 禁止跨镜引用("同上镜色温"等)
4. 无负向词

---

### 镜#A4: 中景 · 4s (global_sec 14-17)

【镜头参数卡】
- 景别: 中景 | 焦距: 35mm | 景深: f/5.6中等景深
- 角度: 眼平·1.6m·正西朝向·面向门框
- 机位: 室内门框内侧偏南·距门~1.5m·区域④
- 轴线: A侧(西侧)
- 运镜: 固定(S0)
- KB: D-TRI-02·C-FI-14(框中框)·L-CT-01(冷暖交界)

【传入参考图】案情室.txt·上排空间布局 — 门框+走廊方向

【生成指令】
t=14: Vincent从走廊探头进入门框——身体在走廊·头微倾探入案情室·一半脸在门框后·露出右半脸和黑框眼镜(V1锚点)。门框作为天然画框占据画面边缘(框中框构图母题第一次出现)。前景门框灰色金属边缘(15%)→中景Vincent上半身·核心信息层(70%)→后景室内白板模糊轮廓+办公桌边缘·f/5.6虚化(15%)。双光源冷暖交界——右半脸(室内侧)=5000K冷白·左半身(走廊侧)=3500K暖黄·冷暖交界线从门框垂直中线贯穿Vincent面部中央偏左。白色实验室外套右半冷白纯白vs左半暖黄微暖。黑框眼镜冷白侧镜片反射格栅灯光斑·暖黄侧反射减少·深棕色眼睛可见(V2锚点)。CV: "酒店监控没有拍到脸。没有指纹。没有DNA。他清理过。"(语速中等·陈述语调·3s)
t=15-16: 探头姿势稳定·门框构图维持框中框几何张力·冷暖交界线持续。
t=17: 对白完毕·等待Miguel回应·视线方向看画右(东=看向Miguel方向)。

音轨: 低音量空调运行声·t=14 CV Vincent 3s(语速中等)

【段末转场】硬切→镜#A5·从Vincent门区→Miguel白板区·正反打

【禁止】
1. 冷暖交界通过双光源色温参数呈现·不写"矛盾/撕裂"等抽象词
2. 门框=物理门框·不写"制度的界限/秩序的隐喻"等文学修饰
3. 画面描述不含运镜语义
4. 禁止跨镜引用

---

### 镜#A5: 近景 · 5s (global_sec 18-22)

【镜头参数卡】
- 景别: 近景 | 焦距: 85mm | 景深: f/2.8浅景深
- 角度: 眼平·1.65m·微高于Miguel眼平·东偏北朝向
- 机位: 白板与桌交界西侧·距脸~1.5m·区域①/②
- 轴线: A侧(西侧)
- 运镜: 固定(S0)
- KB: D-TRI-02·E-MTC-04(视线匹配)·C-KTZ-02(特写亲密)

【传入参考图】案情室.txt·中排白板线索墙 — Miguel面部+背景红线

【生成指令】
t=18: Miguel身体微转向门口一侧(西)·头微倾·目光投向画左(Vincent方向)——与#A4 Vincent看画右(东)形成对视匹配。面部占据画面~60%·中央偏左·眼睛在画面上三分线·视线方向(画左下方·看向Vincent)留白。前景面部(85%)+后景红线网络极度虚化→红色"光环"(15%)·f/2.8·85mm浅景深。天花格栅灯5000K冷白顶光·额骨颧骨最亮·眼窝微暗·下颌微暗·低光比1:1.5。Miguel棕褐色偏灰偏蜡·"我早就知道"的表情在冷灰肤色下=知情者的冷淡。后景红线极度虚化·在Miguel头后方形成模糊红色"光环"——与#A2缠颈红线视觉回响·暗示Miguel也在"线的网络"中。CV: "他从来不需要清理——"(语速缓慢·2s)
t=19: 持续对白。CV: "——他从不碰不需要碰的东西。"(2.5s)
t=20: 对白完毕静默瞬间·表情从"陈述"过渡到"判断完成"。
t=21: 眼珠从画左移回中央偏下(桌面方向)·身体开始从"对话"转向"行动"·审视感转化为决心。
t=22: 回应完成·身体转向办公桌方向·"分析者"→"行动者"切换开始(M3锚点·在下一镜)。

音轨: 室内低频持续·t=18 CV Miguel 2s·t=19 CV Miguel 2.5s

【段末转场】硬切→镜#A6·从面部CU→手部动作MS·节奏推进

【禁止】
1. 不写"似乎知道些什么/好像早已预料"等模糊表述——只写可见微表情
2. 背景红线"光环"通过浅景深构图呈现·不写"宿命/注定"等抽象词
3. 视线匹配是对视方向相反(Vincent看右↔Miguel看左)·不加文字解释
4. 禁止跨镜引用

---

### 镜#A6: 中景 · 3s (global_sec 23-25)

【镜头参数卡】
- 景别: 中景 | 焦距: 50mm | 景深: f/4中等景深
- 角度: 微俯·1.3m·略低于眼平·东偏北朝向
- 机位: 办公桌西侧(A侧)·距桌~0.5m·区域②
- 轴线: A侧(西侧)
- 运镜: 固定(S0)
- KB: D-TRI-02·C-FI-02(深度分层)·L-3PT-01

【传入参考图】案情室.txt·下排桌面微观细节 — 办公桌+笔记本电脑

【生成指令】
t=23: Miguel右手从椅背拿起深藏青警探夹克(哑光面料·拉链立领)——动作果断·无犹豫(M3锚点)·左手同时从桌面抓起车钥匙——双手双轨并行。上身位于画面右三分线·手部动作在画面中央偏下——"行动"在画面几何中心。前景桌面(笔记本电脑+咖啡杯+笔记本+签字笔·15%)→中景Miguel上半身+手部动作(65%)→后景白板线索墙·适度虚化(20%)。双手斜线形成"X"型交叉=分析到行动的交叉点。车钥匙金属反光在冷白光下短暂闪烁(画面最亮)→深色腕表同框→右手无名指旧伤疤形成枪柄弧度(A49锚点)。笔记本电脑屏幕~6500K冷蓝微光·桌面局部。SFX: 车钥匙金属碰撞叮声0.3s。
t=24: 夹克从手部传递到肩部·左手握钥匙·哑光面料冷白光下=蓝黑色·"行动者"颜色。SFX: 夹克面料摩擦声0.5s。
t=25: 穿衣完成·深藏青夹克已穿上·拉链未拉·立领竖立·左手持车钥匙·右手自然垂放·准备离开。从"分析"到"行动"的物理切换完成。

音轨: 室内低频持续·t=23 SFX金属碰撞0.3s·t=24 SFX布料摩擦0.5s

【段末转场】硬切→镜#A7·从室内桌侧→门外走廊·场景出口

【禁止】
1. 手部动作只写可见物理动作·不写"决心/果断/毅然"等情绪词
2. 旧伤疤=A49锚点·只描述可见物理形态(淡色凹痕·枪柄弧度)
3. 无负向词
4. 禁止跨镜引用

---

### 镜#A7: 中全景 · 5s (global_sec 26-30)

【镜头参数卡】
- 景别: 中全景 | 焦距: 35mm | 景深: f/8深景深
- 角度: 眼平·1.6m·正东朝向·从走廊穿过门框看向室内
- 机位: 门框外侧走廊内·距门~0.8m·区域④走廊侧(推断·已标注物理属性)
- 轴线: A侧延伸至走廊·空间连续·不越轴
- 运镜: 固定(S0)
- KB: D-TRI-02·C-FI-14(框中框)·C-DEP-01(单点透视)·C-FI-16(隐藏/揭示)

【传入参考图】案情室.txt·上排空间布局 — 门框透视+走廊光

【生成指令】
t=26: Miguel站在门框中·身体大部分在室内·面朝走廊方向(画面前方)·停了一下——门框恰好挡住他的脸(M4锚点)。观众只能看到: 深藏青夹克的肩膀和衣领·金色警徽在冷白光一侧闪烁·左手持车钥匙·右手自然垂放。全场景构图顶峰——框中框(门框构图·C-FI-14)+冷暖分界(门框垂直中线贯穿身体)+脸部遮挡(C-FI-16)+全纵深透视(门框→Miguel→白板~6m纵深·C-DEP-01)。四层最深纵深: 前景门框边缘(10%)+中景前Miguel在门框中(50%)+中景后走廊(5%)+后景白板线索墙(35%)。深景深f/8·35mm·全室纵深清晰。双光源冷暖交界——右侧(室内·5000K冷白)·左侧(走廊·3500K暖黄)。双重视觉焦点——右: 金色警徽(冷白侧·制度锚点)+左: 车钥匙(暖黄侧·暖金反光·行动锚点)。一个画面四种色彩状态: 右冷白·左暖黄·后白板·前暖光柱。CV: "我只是去——"(轻微停顿·门框挡脸的时刻·2s)
t=27: 门框中停留·冷暖交界线稳定贯穿身体·脸上门框遮挡保持。CV: "——'叙旧'。"("叙旧"在挡脸时刻说出·潜台词与遮挡共振·1.5s)
t=28: 对白完毕·静默呼吸时刻·门的构图中Miguel停顿·冷暖分界·脸部遮挡·"叙旧"余韵在画面中凝固。
t=29: Miguel开始从门框中移动——身体走入走廊·左半身暖黄占比增大·右半身冷白减小·"分界线上的人"开始向外部世界倾斜。
t=30: Miguel从门框中走出·身体完全进入走廊·全被3500K暖黄包裹——肤色全暖金·"行动者"肤色弧线终点。走进走廊深处·最终消失在暖黄光中·门框画面留空·后景白板在6m纵深中静止·案情室空无一人。SFX: 脚步声渐远·门框处空无一人(1s)。

音轨: 室内低频持续+走廊室外底噪上升·t=26 CV Miguel 2s·t=27 CV Miguel 1.5s·t=30 SFX脚步声渐远1s

【段末转场】场景封闭·Miguel走入走廊→延续至下场景(贫民窟巷道)

【禁止】
1. 脸部遮挡通过门框物理位置实现·不写"隐藏的意图/不可见的表情"等
2. "叙旧"的潜台词通过对白+遮挡呈现·不在画面描述中写"不可信/讽刺"
3. 冷暖交界=双光源物理现象·不写"制度与自由的界限"等文学比喻
4. 禁止跨镜引用
5. 首帧零过程动词

---

## §9 YAML输出 (Step A-S6)

### §9.1 机位域YAML (segments_camera + frames_hard)

```yaml
# ═══════════════════════════════════════
# §4 机位域YAML
# 映射: TIME_SKELETON.segments[].camera + frames[].hard
# ═══════════════════════════════════════

segments_camera:
  - segment_id: "A1"
    time_range: [0, 4]
    shot_type: "全景"
    focal_length: "24mm"
    dof: "深景深f/8"
    angle: "眼平·1.6m·正北朝向"
    camera_position: "房间中央·区域⑤·距白板~3m"
    axis_side: "轴上·neutral"
    coverage_function: "建立·全室空间+白板视觉重心"
    kb_rule_ids:
      - "D-TRI-03"
      - "C-KTZ-01"

  - segment_id: "A2"
    time_range: [5, 8]
    shot_type: "大特写"
    focal_length: "85mm"
    dof: "浅景深f/2.8"
    angle: "眼平·1.5m·正北·与照片平齐"
    camera_position: "白板前偏左·区域①·0.4m→0.2m"
    axis_side: "轴上·neutral·插入镜头"
    coverage_function: "揭示·情绪锚点·Rico照片红线缠颈"
    kb_rule_ids:
      - "D-TRI-05"
      - "C-AJS-01"

  - segment_id: "A3"
    time_range: [9, 13]
    shot_type: "中景"
    focal_length: "50mm"
    dof: "中景深f/4"
    angle: "眼平·1.6m·东偏南朝向"
    camera_position: "白板与桌间西侧·区域①·距白板~1.8m"
    axis_side: "A侧·西侧"
    coverage_function: "推进·Miguel审视·面部表情叙事"
    kb_rule_ids:
      - "D-TRI-02"
      - "C-FI-03"

  - segment_id: "A4"
    time_range: [14, 17]
    shot_type: "中景"
    focal_length: "35mm"
    dof: "中景深f/5.6"
    angle: "眼平·1.6m·正西朝向"
    camera_position: "门内侧偏南·区域④·距门~1.5m"
    axis_side: "A侧·西侧"
    coverage_function: "引入·Vincent门口探头·冷暖交界"
    kb_rule_ids:
      - "D-TRI-02"
      - "C-FI-14"

  - segment_id: "A5"
    time_range: [18, 22]
    shot_type: "近景"
    focal_length: "85mm"
    dof: "浅景深f/2.8"
    angle: "眼平·1.65m·微高于Miguel眼平·东偏北"
    camera_position: "白板与桌交界西侧·区域①/②·距脸~1.5m"
    axis_side: "A侧·西侧"
    coverage_function: "反应·Miguel回应Vincent·面部微表情"
    kb_rule_ids:
      - "D-TRI-02"
      - "E-MTC-04"
      - "C-KTZ-02"

  - segment_id: "A6"
    time_range: [23, 25]
    shot_type: "中景"
    focal_length: "50mm"
    dof: "中景深f/4"
    angle: "微俯·1.3m·略低于眼平·东偏北"
    camera_position: "办公桌西侧·区域②·距桌~0.5m"
    axis_side: "A侧·西侧"
    coverage_function: "过渡·物理动作·分析者→行动者"
    kb_rule_ids:
      - "D-TRI-02"
      - "C-FI-02"

  - segment_id: "A7"
    time_range: [26, 30]
    shot_type: "中全景"
    focal_length: "35mm"
    dof: "深景深f/8"
    angle: "眼平·1.6m·正东朝向·走廊→室内"
    camera_position: "门框外走廊·区域④走廊侧·距门~0.8m"
    axis_side: "A侧延伸至走廊·空间连续"
    coverage_function: "再交代+过渡·门框构图·场景封闭"
    kb_rule_ids:
      - "D-TRI-02"
      - "C-FI-14"
      - "C-DEP-01"
      - "C-FI-16"
```

### §9.2 运镜域YAML (segments_movement + frames_movement + segments_transitions)

```yaml
# ═══════════════════════════════════════
# §5 运镜域YAML
# 映射: TIME_SKELETON.segments[].camera.movement + transition + frames[].hard.camera_movement
# ═══════════════════════════════════════

segments_movement:
  - segment_id: "A1"
    movement: "固定"
    movement_speed_tier: "S0"
    kb_rule_ids: ["M-MOT-01"]

  - segment_id: "A2"
    movement: "极慢前推(0.05x)"
    movement_speed_tier: "S1"
    direction: "正北·沿光轴·垂直白板"
    path: "直线·行程~20cm·匀速"
    duration_sec: 4
    kb_rule_ids: ["M-MOT-02", "M-MOT-04"]

  - segment_id: "A3"
    movement: "固定"
    movement_speed_tier: "S0"
    kb_rule_ids: ["M-MOT-01"]

  - segment_id: "A4"
    movement: "固定"
    movement_speed_tier: "S0"
    kb_rule_ids: ["M-MOT-01"]

  - segment_id: "A5"
    movement: "固定"
    movement_speed_tier: "S0"
    kb_rule_ids: ["M-MOT-01"]

  - segment_id: "A6"
    movement: "固定"
    movement_speed_tier: "S0"
    kb_rule_ids: ["M-MOT-01"]

  - segment_id: "A7"
    movement: "固定"
    movement_speed_tier: "S0"
    kb_rule_ids: ["M-MOT-01"]

segments_transitions:
  - transition_id: "A1→A2"
    from_segment: "A1"
    to_segment: "A2"
    transition_type: "硬切"
    at_global_sec: 5
    visual_change: "从全室全景→Rico照片ECU·空间跳跃~2.6m·建立→情绪锚点"
    kb_rule_ids: ["E-MUR-01"]

  - transition_id: "A2→A3"
    from_segment: "A2"
    to_segment: "A3"
    transition_type: "硬切"
    at_global_sec: 9
    visual_change: "从Rico照片ECU→Miguel MS·轴上→A侧·从物件到人物"

  - transition_id: "A3→A4"
    from_segment: "A3"
    to_segment: "A4"
    transition_type: "硬切"
    at_global_sec: 14
    visual_change: "从白板侧Miguel→门口Vincent·空间跳跃~3m·切换拍摄对象"

  - transition_id: "A4→A5"
    from_segment: "A4"
    to_segment: "A5"
    transition_type: "硬切"
    at_global_sec: 18
    visual_change: "正反打·Vincent看右↔Miguel看左对视匹配"
    kb_rule_ids: ["E-MTC-04"]

  - transition_id: "A5→A6"
    from_segment: "A5"
    to_segment: "A6"
    transition_type: "硬切"
    at_global_sec: 23
    visual_change: "从面部CU→手部动作MS·回应→行动的节奏推进"

  - transition_id: "A6→A7"
    from_segment: "A6"
    to_segment: "A7"
    transition_type: "硬切"
    at_global_sec: 26
    visual_change: "从室内桌侧→门外走廊·空间出口·场景封闭"
```

### §9.3 构图光影域YAML (global_anchors + frames_soft)

```yaml
# ═══════════════════════════════════════
# §6 构图光影域YAML
# 映射: TIME_SKELETON.global_anchors + frames[].soft
# ═══════════════════════════════════════

global_anchors:
  character:
    Miguel: "Latin male, 30-40s, short black curly hair with greying temples, wide cheekbones, square jaw, vertical crease between brows, deep brown eyes with detective scrutiny, solid build, 浅灰衬衫(纽扣领) + 深藏青警探夹克(哑光面料·拉链立领·前半段未穿搭椅背·后半段穿上), A19-金色警徽(左胸前·盾形·金属反光), A29-深色金属腕表(黑色表盘·秒针在走), A49-右手无名指旧伤疤(握物时形成枪柄弧度)"
    Vincent: "Male, 30-40s, dark brown short hair slightly disheveled, thin build, cold white skin tone from indoor lab work, 白色实验室外套(长款·及膝) + 内搭深色衬衫, V1-黑框眼镜(黑色板材·矩形框), V2-深棕色眼睛"
    presence_note: "Vincent仅在镜#A4出现·不入室·其余6镜不可见"

  environment:
    description: "圣保罗刑警总部案情室·日间·全封闭室内(~6m深×~4m宽×~3m高)·无窗·纯人工照明·素灰色墙面·强烈单点透视"
    key_elements:
      - "北墙: 巨大白色白板(~3-4m宽·占满墙面)·人物照片+红线网络+建筑平面图(201红圈)+弹道分析报告"
      - "南侧: 合并办公桌×2·距白板~1-2m·堆满文件/笔记本/咖啡杯/签字笔/笔记本电脑"
      - "西墙: 灰色金属门(宽~1m·高~2.1m·不锈钢把手)·外连走廊(3500K暖黄光·推断·已标注物理属性)"
      - "东墙: 素灰墙面·无窗"
      - "天花板: 四个方形格栅发光顶灯(5000K冷白·均匀·无影灯设计)"

  style_spine:
    description: "cold-white institutional 5000K, neutral-gray palette, blood-red accent as vascular metaphor, frame-within-frame composition motif, single-point perspective linear order, static-dominant camera language"
    palette_anchors:
      - "cold-white-5000K"
      - "neutral-gray"
      - "pure-white-whiteboard"
      - "blood-red-accent"
      - "warm-yellow-3500K-corridor"
      - "dark-navy-jacket"
      - "gold-badge-gleam"

  lighting:
    primary:
      source: "天花板方形格栅发光顶灯×4"
      color_temp: "5000K·冷白"
      quality: "柔光·大面积均匀扩散·无影灯设计"
      coverage: "全室(~6m×4m)·低光比约1:1至1:2"
    secondary:
      - source: "笔记本电脑屏幕"
        color_temp: "~6500K·冷蓝微光"
        quality: "弱光·柔和扩散·桌面局部"
      - source: "门外走廊暖黄光(推断·已标注物理属性)"
        color_temp: "3500K·暖黄"
        quality: "软光·从门外走廊漫射·经门框切割为矩形光柱"
        narrative_function: "仅镜#A4/#A7出现·打破冷白制度的均匀性"

  constraints:
    - "所有光源描述基于物理锚点·无凭空编造光源"
    - "所有人物位置锚定空间地图人物可放置区域①-⑤"
    - "白板文字=后期叠加·P-FAL-08规避"
    - "画面描述不含运镜语义·参照画布宪法第四条"
    - "Miguel肤色作为'色温计'——冷白下偏灰偏蜡→暖黄下回暖"
    - "面部比例全程一致·五官不漂移·光线色温全程锁定"
    - "画面稳定无晃动·动作流畅自然"
    - "无字幕·无Logo·无水印"

frames_soft:
  - sec: 0
    global_sec: 0
    camera_position: "A1"
    action_anchor: "Miguel背对镜头站在白板前·深藏青夹克搭在椅背上未穿·站姿距白板~0.5m·面向白板线索墙"
    spatial_anchor: "前景合并办公桌→中景Miguel背影→后景白板(人物照片·红线网络·201红圈·弹道分析报告)"
    character_state:
      - character: "Miguel"
        pose: "背对镜头·站姿·面向白板·距板~0.5m"
        expression: "面部不可见·背身"
        costume: "浅灰衬衫·深藏青夹克搭在椅背上(未穿)"
    audio:
      ambience: "低音量空调运行声·办公室底噪"
      events: []

  - sec: 1
    global_sec: 1
    camera_position: "A1"
    action_anchor: "画面同t=0·Miguel背身站位稳定·观察白板线索墙"
    spatial_anchor: "同t=0·全室透视不变·观众吸收空间信息"
    character_state:
      - character: "Miguel"
        pose: "同t=0·背对镜头·站姿"
    audio:
      ambience: "低音量空调运行声·办公室底噪"

  - sec: 2
    global_sec: 2
    camera_position: "A1"
    action_anchor: "建立镜头持续·观众建立对案情室空间的完整认知"
    spatial_anchor: "同t=0"
    character_state:
      - character: "Miguel"
        pose: "同t=0"
    audio:
      ambience: "低音量空调运行声·办公室底噪"

  - sec: 3
    global_sec: 3
    camera_position: "A1"
    action_anchor: "建立镜头的倒数第二秒"
    spatial_anchor: "同t=0"
    audio:
      ambience: "低音量空调运行声·办公室底噪"

  - sec: 4
    global_sec: 4
    camera_position: "A1"
    action_anchor: "建立镜头结束·Miguel位置不变·即将切至ECU"
    spatial_anchor: "同t=0·全室全景的最终凝视"
    audio:
      ambience: "低音量空调运行声·办公室底噪"
      events:
        - second: 4
          type: "SFX"
          description: "轻微布料摩擦声(Miguel抬手准备钉照片)"
          duration: 0.5

  - sec: 5
    global_sec: 5
    camera_position: "A2"
    action_anchor: "Miguel右手拇指指腹压紧红图钉·食指稳定照片边角·拇指将红色图钉按入Rico照片上边缘"
    spatial_anchor: "Rico照片占据画面中心~60%·手指+图钉=前景·照片面部=中景·白板表面+红线=后景"
    prop_state:
      - item: "红图钉"
        state: "Miguel右手拇指正在按入照片上边缘"
      - item: "Rico照片"
        state: "三年前·颁奖台·举奖杯·面无表情·红线从照片颈部穿过"
    audio:
      ambience: "室内低频持续"
      events:
        - second: 5
          type: "SFX"
          description: "图钉入白板的细微'咔'声"
          duration: 0.2

  - sec: 6
    global_sec: 6
    camera_position: "A2"
    action_anchor: "图钉已按入·Miguel手指开始从照片边缘移开"
    spatial_anchor: "极慢推近中·Rico照片面部缓慢扩大·红线缠颈视觉强化"
    prop_state:
      - item: "红图钉"
        state: "已按入·稳固"
      - item: "Rico照片"
        state: "面部在推近中缓慢扩大"
    audio:
      ambience: "室内低频持续"

  - sec: 7
    global_sec: 7
    camera_position: "A2"
    action_anchor: "推近继续·Miguel手指完全退出画框·视觉转移至照片面部+红线缠颈"
    spatial_anchor: "推近中·Rico照片面部占~70%·红线从颈侧穿过细节清晰可见"
    audio:
      ambience: "室内低频持续"
      events:
        - second: 7
          type: "SFX"
          description: "手指离开照片·轻微摩擦声"
          duration: 0.3

  - sec: 8
    global_sec: 8
    camera_position: "A2"
    action_anchor: "推近落定·Rico照片面部成为画面绝对主体·占据~80%面积·红线缠颈视觉"
    spatial_anchor: "推近落定距白板~0.2m·Rico面部绝对焦点·紧凑无剩余空间·视觉压迫极致"
    prop_state:
      - item: "Rico照片"
        state: "面部占~80%·红线下穿颈侧·冷峻·红线缠颈清晰"
    audio:
      ambience: "室内低频持续·极静"

  - sec: 9
    global_sec: 9
    camera_position: "A3"
    action_anchor: "Miguel身体刚完成后移动作·重心后移·双臂垂放或微交叉·后退一步——从'钉照片'切换到'审视证据网'"
    spatial_anchor: "Miguel上身位于画面左三分线·视线方向(画右上方·看向白板)留白·前景衬衫领口+警徽·中景面部·后景白板红线网络虚化"
    character_state:
      - character: "Miguel"
        pose: "身体刚完成后移·重心后移·双臂垂放或微交叉"
        expression: "眉心竖纹·深棕色眼珠从左向右移动·追踪红线逻辑路径"
    audio:
      ambience: "低音量空调运行声·办公室底噪"

  - sec: 10
    global_sec: 10
    camera_position: "A3"
    action_anchor: "审视继续·眼珠进一步移动·眉心竖纹持续"
    character_state:
      - character: "Miguel"
        expression: "眼珠继续扫描"
    audio:
      ambience: "低音量空调运行声·办公室底噪"

  - sec: 11
    global_sec: 11
    camera_position: "A3"
    action_anchor: "眼珠追踪到201红圈方向·短暂停顿·'抓住关键'表情"
    audio:
      ambience: "低音量空调运行声·办公室底噪"

  - sec: 12
    global_sec: 12
    camera_position: "A3"
    action_anchor: "审视接近尾声·眉心竖纹微微加深——'分析'转向'判断'"
    audio:
      ambience: "低音量空调运行声·办公室底噪"

  - sec: 13
    global_sec: 13
    camera_position: "A3"
    action_anchor: "审视结束·身体微倾向门口方向·即将切换至对话状态"
    audio:
      ambience: "低音量空调运行声·办公室底噪"
      events:
        - second: 13
          type: "SFX"
          description: "轻微脚步声从走廊方向(画左·门外)"
          duration: 0.5

  - sec: 14
    global_sec: 14
    camera_position: "A4"
    action_anchor: "Vincent从走廊探头进入门框——身体在走廊·头微倾探入·一半脸在门框后·露出右半脸和黑框眼镜"
    spatial_anchor: "门框作为天然画框(框中框)·前景门框边缘(15%)·中景Vincent(70%)·后景室内白板模糊(15%)·冷暖交界线贯穿面部"
    character_state:
      - character: "Vincent"
        pose: "身体在走廊·头微倾探入案情室·露出右半脸"
        expression: "信息传递者·深棕色眼睛可见"
    audio:
      ambience: "低音量空调运行声·办公室底噪"
      events:
        - second: 14
          type: "CV"
          description: "Vincent: '酒店监控没有拍到脸。没有指纹。没有DNA。他清理过。'"
          duration: 3.0

  - sec: 15
    global_sec: 15
    camera_position: "A4"
    action_anchor: "探头姿势稳定·黑框眼镜冷暖光下镜片反射变化"
    audio:
      ambience: "低音量空调运行声·办公室底噪"

  - sec: 16
    global_sec: 16
    camera_position: "A4"
    action_anchor: "Vincent继续陈述·探头姿势不变·冷暖交界在服装上同样明显"
    audio:
      ambience: "低音量空调运行声·办公室底噪"

  - sec: 17
    global_sec: 17
    camera_position: "A4"
    action_anchor: "对白完毕·等待Miguel回应·视线方向看画右(东=看向Miguel)"
    audio:
      ambience: "低音量空调运行声·办公室底噪"

  - sec: 18
    global_sec: 18
    camera_position: "A5"
    action_anchor: "Miguel身体微转向门口·头微倾·目光投向画左(Vincent方向)——与#A4 Vincent看画右形成对视匹配"
    spatial_anchor: "Miguel面部占~60%·中央偏左·前景面部(85%)+后景红线极度虚化→红色'光环'(15%)"
    character_state:
      - character: "Miguel"
        pose: "身体微转向门口一侧(西)·头微倾"
        expression: "眉心竖纹微加深·嘴角微抿·'我早就知道'表情"
    audio:
      ambience: "室内低频持续"
      events:
        - second: 18
          type: "CV"
          description: "Miguel: '他从来不需要清理——'"
          duration: 2.0

  - sec: 19
    global_sec: 19
    camera_position: "A5"
    action_anchor: "Miguel持续对白·视线保持在画左·嘴角微抿在CU下极为清晰"
    audio:
      ambience: "室内低频持续"
      events:
        - second: 19
          type: "CV"
          description: "Miguel: '——他从不碰不需要碰的东西。'"
          duration: 2.5

  - sec: 20
    global_sec: 20
    camera_position: "A5"
    action_anchor: "对白完毕静默瞬间·表情从'陈述'过渡到'判断完成'"
    audio:
      ambience: "室内低频持续"

  - sec: 21
    global_sec: 21
    camera_position: "A5"
    action_anchor: "眼珠从画左移回中央偏下(桌面方向)·审视感转化为决心"
    audio:
      ambience: "室内低频持续"

  - sec: 22
    global_sec: 22
    camera_position: "A5"
    action_anchor: "回应完成·身体转向办公桌方向·'分析者'→'行动者'切换开始"
    audio:
      ambience: "室内低频持续"

  - sec: 23
    global_sec: 23
    camera_position: "A6"
    action_anchor: "Miguel右手从椅背拿起深藏青夹克(哑光面料·拉链立领)·左手从桌面抓起车钥匙·双手双轨并行"
    spatial_anchor: "上身画面右三分线·手部动作画面中央偏下·前景桌面(15%)·中景Miguel(65%)·后景白板虚化(20%)"
    character_state:
      - character: "Miguel"
        pose: "右手拿起夹克·左手抓起车钥匙"
        expression: "面部被手臂微遮挡·短暂暗化"
        costume: "浅灰衬衫·正在穿上深藏青夹克"
    prop_state:
      - item: "深藏青夹克"
        state: "从椅背拿起·正在穿上"
      - item: "车钥匙"
        state: "左手从桌面抓起·金属反光"
    audio:
      ambience: "室内低频持续"
      events:
        - second: 23
          type: "SFX"
          description: "车钥匙被拿起·金属碰撞叮声"
          duration: 0.3

  - sec: 24
    global_sec: 24
    camera_position: "A6"
    action_anchor: "夹克从手部传递到肩部·左手握钥匙"
    prop_state:
      - item: "深藏青夹克"
        state: "从手部传递到肩部·正在穿上"
    audio:
      ambience: "室内低频持续"
      events:
        - second: 24
          type: "SFX"
          description: "夹克面料摩擦声"
          duration: 0.5

  - sec: 25
    global_sec: 25
    camera_position: "A6"
    action_anchor: "穿衣完成·深藏青夹克已穿上·拉链未拉·立领竖立·左手持车钥匙·准备离开"
    character_state:
      - character: "Miguel"
        pose: "夹克已穿上·左手车钥匙·准备离开"
        costume: "深藏青夹克已穿上(哑光面料·拉链立领·未拉)"
    audio:
      ambience: "室内低频持续"

  - sec: 26
    global_sec: 26
    camera_position: "A7"
    action_anchor: "Miguel站在门框中·身体大部分在室内·面朝走廊方向·停了一下——门框恰好挡住他的脸(M4锚点)"
    spatial_anchor: "框中框+冷暖分界+脸部遮挡+全纵深(门框→Miguel→白板~6m)·4层纵深·深景深f/8·35mm"
    character_state:
      - character: "Miguel"
        pose: "站在门框中·面朝走廊"
        visible_part: "肩膀·衣领·金色警徽(冷白侧)·左手车钥匙·右手垂放·脸被门框遮挡"
        costume: "深藏青夹克已穿上·浅灰衬衫内搭·金色警徽·车钥匙"
    audio:
      ambience: "室内低频持续·走廊脚步声余韵"
      events:
        - second: 26
          type: "CV"
          description: "Miguel: '我只是去——'"
          duration: 2.0

  - sec: 27
    global_sec: 27
    camera_position: "A7"
    action_anchor: "Miguel在门框中停留·冷暖交界线稳定贯穿身体·脸部遮挡保持"
    audio:
      ambience: "室内低频持续"
      events:
        - second: 27
          type: "CV"
          description: "Miguel: '——'叙旧'。'"
          duration: 1.5

  - sec: 28
    global_sec: 28
    camera_position: "A7"
    action_anchor: "对白完毕·静默呼吸时刻·门框中停顿·'叙旧'余韵凝固"
    audio:
      ambience: "室内低频持续·走廊微室外底噪"

  - sec: 29
    global_sec: 29
    camera_position: "A7"
    action_anchor: "Miguel开始从门框中移动——身体走入走廊·左半身暖黄占比增大·右半身冷白减小"
    audio:
      ambience: "走廊暖黄光中微弱室外底噪上升·室内低频渐退"

  - sec: 30
    global_sec: 30
    camera_position: "A7"
    action_anchor: "Miguel从门框中走出·完全进入走廊·全3500K暖黄包裹·消失在暖黄光中·门框留空"
    spatial_anchor: "空门框——制度的框架还在·人已走了·后景白板6m纵深静止·案情室空无一人"
    character_state:
      - character: "Miguel"
        pose: "从门框走出·进入走廊·消失在暖黄光中"
        visible_part: "身体渐被走廊暖黄光完全包裹·最终消失在光中"
    audio:
      ambience: "走廊脚步声远去·室外底噪"
      events:
        - second: 30
          type: "SFX"
          description: "脚步声渐远·门框处空无一人·场景结束"
          duration: 1.0
```

---

> **Scene Designer 签名:** v1.0 · S-Level三域合并设计 · 2026-07-07
> **复杂度:** 🟢 S-Level · 输出规模: ~750行 (含YAML 450行+台本300行)
> **继承:** EP14 pattern (室内对话_单室_面对面) · 全方案继承无差异
> **静态快速通道:** ✅ 激活 · 6/7镜固定 · 仅镜#A2含运镜(极慢前推0.05x·S1)
> **KB引用覆盖:** ✅ 每镜每域≥1条KB规则ID · 机位/运镜/构图/光影各域覆盖完整
> **P-FAL规避:** ✅ 全部10项通过
> **下游交付:** storyboard_planner (消费§9 YAML三块) · prompt_composer (消费§8台本)
> **替代:** 原三Agent串行链(Shot Architect+Movement Designer+Composition Designer)
