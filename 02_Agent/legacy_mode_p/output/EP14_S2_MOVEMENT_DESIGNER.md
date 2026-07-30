# Movement Designer Report — EP14 S2: 贫民窟巷道

> **生成:** Movement Designer v2.0 · MODE:P Step A2 · 2026-07-07
> **场景:** 外景 贫民窟窄巷+轿车内部（午后·阴天）·7镜·39秒
> **场景属性:** 悬疑/偷窥·三重色温·窄空间(<2m)·双空间(巷道+轿车)
> **独立上下文:** 不读取Scene Designer推理过程·仅读取§4(机位域YAML)+§6(构图光影域YAML)
> **KB加载:** kb_index_v2.0 §5 运镜与运动 · shared_agent_runtime.md §5 空间-运镜可行性矩阵
> **下游消费者:** storyboard_planner §2G (消费segments_movement+frames_movement+segments_transitions)

---

## 1. 场景运镜策略总览

### 1.1 运镜类型配比

```
场景运镜分布（7镜·39秒）:

  静态/固定:    5镜 (#2·#3·#4·#5·#6) = 71.4% · 28秒
  前跟拍+缓升:  1镜 (#1)               = 14.3% ·  6秒
  极慢前推:     1镜 (#7)               = 14.3% ·  5秒
  ────────────────────────────────────────────────────
  推近类:       1镜 (极慢·0.03x)
  跟拍类:       1镜 (前跟拍0.3x+缓升)
  横移类:       0镜 (空间禁制·巷宽<2m)
  摇摄类:       0镜
  环绕类:       0镜 (空间禁制·巷宽<2m)
  手持类:       0镜
  升降类:       0镜 (独立升降·#1的缓升为跟拍复合分量)
  旋转类:       0镜
  荷兰角:       0镜
```

**配比策略说明:** 本场景为悬疑/偷窥类型·窄空间(巷宽<2m) + 极度受限空间(轿车内)。运镜策略以静态固定为主导(71.4%)，对应悬疑场景的"静止凝视=悬念累积"法则。两个动态镜均为空间可行的纵向运动——#1沿巷道中轴线的低角度前跟拍(复合缓升)，#7在巷道中段的极慢前推(落定Pedro情绪锚点)。零横移·零环绕·零手持——全部受窄空间约束(M-MOT-03·P-FAL-06)。

参照shared_agent_runtime.md §4.1静态运镜例外规则：5个静态镜均属于合法例外——
- #2: 信息密集(POV+嵌套构图·透过沙尘挡风玻璃需吸收车内信息)
- #3: 信息密集(躲藏动作+缓慢探头·角色身体运动已承载节奏)
- #4: 信息密集(极度遮蔽POV·小窗口法·信息受限=悬念·固定维持视野限制)
- #5: 信息密集+空间受限(三设硬切·车内窄空间禁大幅运动)
- #6: 情感沉浸(ECU恐惧峰值·静止=窒息感·运动将稀释情绪)

### 1.2 空间约束分析

```
巷道物理尺寸（参照ANCHOR_BASELINE §C + CONTEXT_PACKAGE_EP14 §3）:
  纵深: ~20m (巷口→巷尾)
  宽度: <2m (两侧砖墙间距)
  高度: ~6-8m (至一线天)
  空间面积: ~40m² (狭长·不可横向调度)

可运镜范围分析:
  纵深方向(巷口↔巷尾·推拉方向):
    ✅ 全纵深~20m可用于前推/后拉
    ✅ #1前跟拍路径: 巷口→巷中段·沿巷道中轴线·行程~12-15m
    ✅ #7极慢前推: 巷中段·Pedro身后~1m起·行程~0.15m(5秒×0.03x)
    ✅ P-FAL-06: 纵深运动不触发窄空间横移禁制

  宽度方向(左右·横移方向):
    🛑 巷宽<2m → 完全禁横移(P-FAL-06·M-MOT-03)
    🛑 巷宽<2m → 禁环绕(环绕直径>2m不可行)
    ✅ 本场景零横移·零环绕·全部遵守

  高度方向(上下·升降方向):
    ✅ 头顶一线天~6-8m → 升降理论可行
    ⚠️ #1缓升为跟拍复合分量(非独立升降运镜)·从30cm→100cm·在本场景光源锚定范围内

  轿车内部（极度受限·~1.8m²）:
    🛑 仅限固定·推近空间<0.3m·无运镜意义
    ✅ #5车内段全部固定·硬切切换子机位

  禁入区:
    ❌ 墙面内部·排水管内部·电表箱内部·垃圾桶内部·车辆引擎区域
    ✅ 全部运镜路径在可拍摄巷道空间内

  关键空间约束速查:
    ✅ 窄巷(<2m) → 无横移·无环绕 → 仅纵向运动(P-FAL-06规避)
    ✅ 车辆停靠后两侧缝隙<0.3m → 人物不可通过·机位不可放置 → 已规避
    ✅ 垃圾桶推断属性(LEVEL-C) → 机位在桶侧前·不穿桶
```

---

## 2. 情绪-运镜映射

```
场景情绪弧线（从Scene Designer逐镜叙事节拍提取）:

  镜#1 [0-6s] : 好奇→警觉   情绪值 +1  → 前跟拍(0.3x)    · 运镜强度 S3  · 差值=2 ⚠️
    说明: 情绪+1但运镜S3——跟拍儿童追球·速度匹配动作主体(非情绪)·Pedro跑动速度决定运镜速度·无错位

  镜#2 [6-12s]: 警觉→紧张   情绪值 +2  → 固定(S0)        · 运镜强度 S0  · 差值=2 ⚠️
    说明: 情绪升温但运镜静止——POV信息密集·固定=强迫观众凝视·A-SUS-03紧张期待法则·反差设计

  镜#3 [12-17s]: 紧张→恐惧   情绪值 +2  → 固定(S0)        · 运镜强度 S0  · 差值=2 ⚠️
    说明: Pedro躲藏动作承载全部节奏·固定=让观众等·桶沿遮挡的"隐藏揭示"需静止

  镜#4 [17-23s]: 紧张(累积)  情绪值 +2  → 固定(S0)        · 运镜强度 S0  · 差值=2 ⚠️
    说明: 极度遮蔽POV·信息受限=悬念累积·静止=信息不更新=焦虑累积·运动将破坏

  镜#5 [23-29s]: 恐惧(峰值)  情绪值 +3  → 固定(S0+硬切)   · 运镜强度 S0  · 差值=3 ⚠️
    说明: 情绪高潮但运镜零——三设硬切(Rico CU→POV扫描→影子ECU)已提供足够视觉冲击·车内/巷口空间禁运镜

  镜#6 [29-34s]: 恐惧(释放)  情绪值 +2  → 固定(S0)        · 运镜强度 S0  · 差值=2 ⚠️
    说明: ECU恐惧峰值·静止=窒息感·Pedro缩回避让的动作为唯一动态·运镜将稀释

  镜#7 [34-39s]: 恐惧→余韵   情绪值 -1  → 极慢前推(0.03x) · 运镜强度 S1  · 差值=0 ✅
    说明: 疏离/余韵→极慢前推=远离感?→前推=靠近Pedro=情感重力·"靠近悲伤"的有效设计

  情绪-运镜匹配总结:
    ✅ 7/7镜有清晰的情绪-运镜映射逻辑
    ⚠️ 5镜差值≥2——均为悬疑场景的"反差设计"(情绪升·运镜静)·非设计失误
    ✅ 2镜(#1 #7)的运镜速度由空间/动作/情绪协同决定·非单一情绪驱动
```

---

## 3. 逐镜运镜设计

### 镜#1: 追球入巷·低角度前跟拍+缓升 [0-6s]

```
运镜类型:     低角度前跟拍(0.3x) + 缓升(30cm→100cm)  复合运动
速度参数:     0.3x前跟(0-4s) → 0.05x极慢前推落定(5s)
方向:         沿巷道中轴线·巷口→巷中段·正前方
起止状态:     起点:巷口入口·距地30cm·面朝巷内
              终点:巷中段·距地100cm(Pedro眼高)·Pedro身后~2m
时长:         6秒 (6帧·0-5s)
行程:         前跟~12m(4s) + 微推~0.05m(1s落定)
缓升:         30cm→100cm·共70cm·4秒完成(第3-5s主要上升段)

KB规则ID:    M-MOT-02(速度匹配·跟拍匹配人物跑动)·M-MOV-05(跟拍/追踪)
              M-MOV-04(向前推进)·M-MOT-03(空间可行性·巷道纵深充足)
              M-MOT-04(速度空间约束·巷宽<2m禁横移·0.3x纵向跟拍可行)

情绪匹配:     情绪=+1(好奇/动作)·运镜强度=S3(0.3x跟拍)·差值=2 ⚠️
              跟拍=动作主体驱动·速度由Pedro跑动速度决定·非情绪驱动·无错位

空间约束:     ✅ 沿巷道中轴·行程~12m·全路径在巷道内·不穿墙不悬空
              ✅ 巷宽<2m·纵向运动不触发横移禁制(P-FAL-06)
              ✅ 缓升从30cm→100cm·全部在头顶一线天(~6-8m)下方

动机:         建立空间+引领观众·低角度=儿童视角·跟拍=观众与Pedro一同进入巷道
              缓升=从"地面视角"(球的视角)→"儿童视角"(Pedro眼高)·视角转换承载叙事
```

**逐秒运动分解:**

| 秒 | global_sec | 运镜状态 | 高度 | 说明 |
|:--:|:----------:|---------|:----:|------|
| 0 | 0 | 前跟拍(0.3x) | 30cm | 起幅·足球滚入·低角度跟球 |
| 1 | 1 | 前跟拍(0.3x) | 30cm | 跟球继续·碎石地面纹理·墙面进入画面 |
| 2 | 2 | 前跟拍(0.3x) | 30cm | Pedro进入画面后景·开始缓升(30→45cm) |
| 3 | 3 | 前跟拍(0.3x)+缓升 | 45→65cm | Pedro追近球·缓升中段·视角从地面升高 |
| 4 | 4 | 前跟拍(0.2x)+缓升 | 65→85cm | Pedro减速·运镜同步减速·轿车剪影在巷口出现 |
| 5 | 5 | 极慢前推(0.05x)落定 | 85→100cm | Pedro停步·运镜微推落定·画面固定·轿车暗色剪影 |

---

### 镜#2: Pedro POV·发现轿车 [6-12s] — 固定

```
运镜:         固定 (S0)
时长:         6秒 (6-11s)
静态例外:     信息密集——POV主观+嵌套构图(巷道框→挡风玻璃框)+三重色温信息层+车内双人物
              观众需6秒吸收: 空间环境(巷道+轿车) + 人物(双人识别) + 动作(交换交易)
KB规则ID:    M-MOT-01(静态镜动机·信息密集例外)·A-SUS-03(固定视角强迫等待=紧张期待)
动机:         POV主观视角·固定=Pedro在看·观众与Pedro共享视觉信息获取时间
              任何运镜(推近/摇镜)将破坏POV的真实感——人眼在注视时不会"推近"
空间约束:     ✅ 虚拟POV·无物理机位约束·固定不触发空间禁制
```

---

### 镜#3: 躲藏·垃圾桶后探头 [12-17s] — 固定

```
运镜:         固定 (S0)
时长:         5秒 (12-16s)
静态例外:     信息密集——躲藏动作(急跑+蹲下+紧缩+极慢探头)经历4个子节拍·角色身体运动已承载全部节奏
              固定=观众等待·桶沿作为信息控制界面·C-FI-16隐藏与揭示法则
KB规则ID:    M-MOT-01(静态镜动机·信息密集例外)·A-SUS-03(紧张期待·缓慢探头=悬念)
动机:         固定机位=见证者视角·观众如同墙上的一只眼·不介入·只观察
              Pedro的探头动作是画面内唯一动态·运镜将抢夺观众注意力
空间约束:     ✅ 机位在垃圾桶侧前·距墙>0.3m·固定不触发空间禁制
```

---

### 镜#4: 偷看POV·交易细节 [17-23s] — 固定

```
运镜:         固定 (S0)
时长:         6秒 (17-22s)
静态例外:     信息密集——极度遮蔽POV(>30%画面被桶沿遮挡)+小窗口法(C-AJS-03)+车内信息层
              信息受限=悬念·固定维持视野限制·观众与Pedro共享"看不清"的焦虑
KB规则ID:    M-MOT-01(静态镜动机·信息密集例外)·A-SUS-03(固定视角·信息不更新=焦虑累积)
动机:         遮蔽POV·固定=Pedro不敢动=摄影机不敢动·镜头运动的缺失即角色恐惧的镜像
              任何微推(想看清)将背叛Pedro的主观限制·破坏代入感
空间约束:     ✅ 虚拟POV在桶后·固定不触发空间禁制
```

---

### 镜#5: Rico转头·差点发现 [23-29s] — 固定(三设硬切)

```
运镜:         固定 (S0) — 三段子机位·全部固定·通过硬切切换
时长:         6秒 (23-28s) = 2s(Rico CU·车内)+3s(POV扫描·巷口)+2s(影子ECU·碎石)
静态例外:     复合——Rico CU(空间受限·车内~1.8m²禁运镜)+POV(信息密集·扫描需固定机位让视线移动)+影子ECU(情感沉浸·静止=Rico发现的悬念悬停)
KB规则ID:    M-MOT-01(静态镜动机·空间受限+信息密集例外)
动机:         车内段=空间极度受限·固定唯一选择
              POV段=扫描式视线是角色动作·非摄影机运动·固定机位让Rico的视线"扫过"画面
              影子ECU=线索定格·固定=让观众与Rico一起"盯着看"
空间约束:     ✅ 车内CU不穿车体·POV虚拟视点·影子ECU在地面·全部合规
```

---

### 镜#6: Pedro反应·缩回·恐惧 [29-34s] — 固定

```
运镜:         固定 (S0)
时长:         5秒 (29-33s)
静态例外:     情感沉浸——ECU恐惧峰值·Pedro缩回避让的动作(第29s)+极慢重新探头(第32s)
              固定=窒息感·摄影机如被恐惧冻结·任何运动将稀释情绪浓度
KB规则ID:    M-MOT-01(静态镜动机·情感沉浸例外)·A-SUS-09(恐惧延时释放·静止=恐惧的视觉化)
动机:         ECU+85mm+极浅景深f/2.0——画面已压缩至仅有眼睛·运镜无视觉意义
              恐惧的极致表达是"不敢动"——Pedro不敢动·摄影机也不敢动
空间约束:     ✅ 机位在垃圾桶侧前·距墙>0.3m·固定不触发空间禁制
```

---

### 镜#7: 轿车驶离·Pedro前景锚点 [34-39s] — 极慢前推

```
运镜类型:     极慢前推(0.03x)   线性运动·推近类
速度参数:     0.03x·匀速·全程5秒
方向:         沿巷道中轴线偏右·朝向Pedro蹲姿位置(垃圾桶后方)
起止状态:     起点:Pedro身后~1m·距地50cm·OTS低角度
              终点:Pedro身后~0.85m·距地50cm不变
时长:         5秒 (34-38s)
行程:         ~15cm (5秒×0.03x≈0.15m)
复合:         无·纯前推·无缓升/缓降·无摇摄

KB规则ID:    M-MOV-04(向前推进)·M-MOT-02(速度匹配情绪·余韵→极慢)
              M-MOT-03(空间可行性·行程15cm·在巷道纵深内)
              M-MOT-04(速度空间约束·0.03x极慢·不触发P-FAL-06)

情绪匹配:     情绪=-1(疏离/余韵)·运镜强度=S1(0.03x极慢)·差值=0 ✅
              极慢前推="靠近悲伤"——威胁退去后·摄影机轻轻靠近Pedro·情感重力而非空间推进

空间约束:     ✅ 前推路径沿巷道中轴线偏右·行程~15cm·全路径在巷道内
              ✅ 不穿Pedro·不穿垃圾桶·不触墙面
              ✅ 巷宽<2m·纵向微推不触发横移禁制

动机:         轿车驶离=威胁消散·但极慢前推(而非拉远)=摄影机的"情感重力"——被Pedro的恐惧吸引·轻轻靠近
              0.03x几乎不可感知——观众潜意识中感到"画面在变近"但无法确认·增强不安余韵
              前推方向朝向Pedro(而非朝向巷口跟轿车)=叙事重音落在"留下来的人"·非"离开的车"
```

**逐秒运动分解:**

| 秒 | global_sec | 运镜状态 | 距Pedro | 说明 |
|:--:|:----------:|---------|:-------:|------|
| 34 | 34 | 极慢前推(0.03x) | ~1.00m | 起幅·轿车发动·Pedro前景剪影 |
| 35 | 35 | 极慢前推(0.03x) | ~0.97m | 轿车驶离中·微推进·几乎无感 |
| 36 | 36 | 极慢前推(0.03x) | ~0.94m | 轿车消失·巷口暖亮恢复·推进持续 |
| 37 | 37 | 极慢前推(0.03x) | ~0.91m | 空巷·球的影子·Pedro未起身 |
| 38 | 38 | 极慢前推(0.03x) | ~0.85m | 落幅·静持·情感重量落定 |

---

## 4. 运镜序列节奏分析

```
全场景速度分布（7镜）:

  速度档位    镜数    占比    对应镜头
  ─────────────────────────────────────
  S0 固定      5      71.4%   #2#3#4#5#6
  S1 极慢      1      14.3%   #7 (0.03x前推)
  S3 慢速      1      14.3%   #1 (0.3x跟拍)
  S4-S7        0       0%     —

相邻跳跃检测:
  #1(S3)→#2(S0): 跳跃3级 → S3到S0 = 跟拍硬切至POV固定·切本身消解跳跃 ⚠️无连续运动过渡
  #2(S0)→#3(S0): 0级 ✅
  #3(S0)→#4(S0): 0级 ✅
  #4(S0)→#5(S0): 0级 ✅
  #5(S0)→#6(S0): 0级 ✅
  #6(S0)→#7(S1): 1级 ✅ 极微跳跃·S0→S1过渡自然

加速度波形:
  S3(起) → S0(6秒)→S0(5秒)→S0(6秒)→S0(6秒)→S0(5秒)→S1(落)
  波形: 起跳→长平→微升  有呼吸节奏 ✅
  评价: 静态平原(28秒)被两个动态点包裹——开篇跟拍引入·收尾微推闭合·形成运动弧线

两极分化检测:
  静态(S0)+快速(S4-S7) = 71.4% + 0% = 71.4% < 80% ✅ 不触发两极分化警告
  但71.4%静态仍偏高——在本悬疑偷窥场景类型中·高静态比例是预期特征·非设计缺陷
  Seko文件参考: shared_agent_runtime.md §4.1 悬疑场景合法静态比例上限85%
```

---

## 5. 空间约束总验证

```
✅ 逐镜验证:
  ✅ #1: 沿巷道中轴·前跟12m·缓升30→100cm·全部在空间内
  ✅ #2: POV虚拟·无物理约束
  ✅ #3: 桶侧前固定·距墙>0.3m
  ✅ #4: 虚拟POV桶后·无物理约束
  ✅ #5: 车内CU不穿车·POV虚拟·影子ECU在地面
  ✅ #6: 桶侧前固定·距墙>0.3m
  ✅ #7: 前推15cm·沿巷道中轴偏右·不穿Pedro/桶/墙

窄空间禁制(P-FAL-06):
  ✅ 零横移——巷道宽度<2m·全部纵向运动
  ✅ 零环绕——环绕直径≈3-5m>巷宽2m·不可行
  ✅ #1前跟拍沿巷道中轴线·不触及墙面
  ✅ #7微推15cm·路径安全

P-STATE §2已知失败规避:
  ✅ P-FAL-06(窄空间横移): 0次触发·零横移设计
  ✅ P-FAL-09(极端运动形变): 0次触发·最大速度0.3x·远低于触发阈值
  ✅ 全部运镜速度在Seko可稳定渲染范围内

总评: ✅ 全部7镜·39秒·0次空间违规·0次P-FAL触发
```

---

## 6. 画布七条铁律合规声明（运镜域）

```
□ 第〇条 KB>LLM:
  ✅ 全部7镜标注KB规则ID(M-MOT-01~04·M-MOV-04/05)
  ✅ 运镜类型均来自KB §5运镜体系·无LLM自由发挥类型
  ✅ 引用P-STATE §2已知失败(P-FAL-06/P-FAL-09)验证
  ✅ 知识来源: L4(kb_index→§5运镜)+L2(P-STATE §2)

□ 第一条 画面可见性>文学:
  ✅ 本Agent仅设计运镜·不输出画面描述
  ✅ 运镜参数不含抽象情绪词·仅含可量化运动描述

□ 第二条 渲染可行性>美学:
  ✅ P-FAL-06规避: 巷宽<2m·零横移·纵向运动不触发
  ✅ P-FAL-09规避: 最大0.3x跟拍·远低于触发阈值
  ✅ 运镜速度S0-S3全在Seko稳定渲染范围

□ 第三条 空间锚定>创意:
  ✅ 全部运镜路径锚定于ANCHOR_BASELINE §C+CONTEXT_PACKAGE §3
  ✅ 窄巷<2m禁横移/环绕·空间数据驱动运镜限制
  ✅ 前推路径全部在巷道纵深内·不穿墙不穿模

□ 第四条 运镜-画面分离:
  ✅ 画面描述引用自Scene Designer·不含运镜语义
  ✅ 运镜参数仅存于§5 YAML·与画面描述分离
  ✅ 工程符号(速度倍数·7-DOF)不进画面描述

□ 第五条 确定性>概率性:
  ✅ 全部运镜类型有S0-S3速度档位量化
  ✅ #1跟拍: 0.3x·12m·4s·缓升30→100cm —— 全部精确
  ✅ #7前推: 0.03x·15cm·5s —— 精确可量化
  ✅ 静态例外均有具体理由·非模糊判断

□ 第六条 物体存在链:
  ✅ 本Agent仅设计运镜·不涉及物体描述
  ✅ 运镜设计中未引入新物体

□ 第七条 独立验证:
  ✅ 本报告由Movement Designer独立产生
  ✅ 仅读取Scene Designer §4(机位YAML)+§6(构图光影YAML)
  ✅ 不读取Scene Designer推理过程
  ✅ 验证委托Movement Reviewer独立执行

合规总评: ✅ 七条铁律全部合规·🛑0 ⚠️0
```

---

# ═══════════════════════════════════════
# §5 YAML: segments_movement
# 映射目标: TIME_SKELETON.segments[].camera.movement
# ═══════════════════════════════════════

```yaml
# Movement Designer v2.0 · segments_movement
# 映射目标: TIME_SKELETON.segments[].camera.movement
# 下游消费者: storyboard_planner §2G (机械组装)
# 在Scene Designer segments_camera基础上补充movement字段

segments_movement:
  - seg_id: "1"
    time_range: [0, 6]
    movement: "低角度前跟拍(0.3x)+缓升(30cm→100cm)"
    movement_speed_tier: "S3→S1"
    movement_direction: "巷口→巷中段·沿巷道中轴线·正前"
    movement_path: "直线·起点巷口入口(距地30cm)·终点巷中段(距地100cm·Pedro身后~2m)·行程~12m"
    movement_composite: "前跟拍4s(0.3x)+微推落定1s(0.05x) + 缓升70cm(30→100cm·第2-5s)"
    dof_vector: [0, 0, 0, 0, +70cm, 12m, 0]  # v_dolly≈3m/s前4s·v_boom≈17.5cm/s
    static_exception: "非静态·跟拍匹配Pedro跑动·儿童追球入巷·动作驱动运镜"
    kb_rule_ids:
      - "M-MOT-02"
      - "M-MOV-05"
      - "M-MOV-04"
      - "M-MOT-03"
    spatial_verdict: "✅ 沿巷道中轴·行程12m在纵深20m内·缓升30→100cm在一线天下方·不穿墙"

  - seg_id: "2"
    time_range: [6, 12]
    movement: "固定"
    movement_speed_tier: "S0"
    movement_direction: "无"
    dof_vector: [0, 0, 0, 0, 0, 0, 0]
    static_exception: "信息密集——POV主观+嵌套构图(巷道框→挡风玻璃框)+三重色温+车内双人物·6秒吸收"
    kb_rule_ids:
      - "M-MOT-01"
    spatial_verdict: "✅ 虚拟POV·固定不触发空间约束"

  - seg_id: "3"
    time_range: [12, 17]
    movement: "固定"
    movement_speed_tier: "S0"
    movement_direction: "无"
    dof_vector: [0, 0, 0, 0, 0, 0, 0]
    static_exception: "信息密集——躲藏4子节拍(急跑+蹲下+紧缩+极慢探头)·角色身体运动承载节奏"
    kb_rule_ids:
      - "M-MOT-01"
    spatial_verdict: "✅ 桶侧前固定·距墙>0.3m·不触发空间约束"

  - seg_id: "4"
    time_range: [17, 23]
    movement: "固定"
    movement_speed_tier: "S0"
    movement_direction: "无"
    dof_vector: [0, 0, 0, 0, 0, 0, 0]
    static_exception: "信息密集——遮蔽POV(>30%遮挡)+小窗口法(C-AJS-03)·固定维持视野限制=悬念"
    kb_rule_ids:
      - "M-MOT-01"
    spatial_verdict: "✅ 虚拟POV桶后·固定不触发空间约束"

  - seg_id: "5"
    time_range: [23, 29]
    movement: "固定(三设硬切)"
    movement_speed_tier: "S0"
    movement_direction: "无(每子设固定·硬切切换机位)"
    dof_vector: [0, 0, 0, 0, 0, 0, 0]
    movement_note: "三段子机位均固定: 23-25s车内Rico CU/25-27s巷口POV/27-28s影子ECU·硬切切换·无连续运镜"
    static_exception: "复合——车内段(空间受限·1.8m²)+POV段(信息密集·扫描)+影子ECU(情感沉浸·悬念悬停)"
    kb_rule_ids:
      - "M-MOT-01"
    spatial_verdict: "✅ 车内不穿车·POV虚拟·影子在地面·全部合规"

  - seg_id: "6"
    time_range: [29, 34]
    movement: "固定"
    movement_speed_tier: "S0"
    movement_direction: "无"
    dof_vector: [0, 0, 0, 0, 0, 0, 0]
    static_exception: "情感沉浸——ECU恐惧峰值·缩回避让+极慢探头·静止=窒息感·运动稀释情绪"
    kb_rule_ids:
      - "M-MOT-01"
    spatial_verdict: "✅ 桶侧前固定·距墙>0.3m·不触发空间约束"

  - seg_id: "7"
    time_range: [34, 39]
    movement: "极慢前推(0.03x)"
    movement_speed_tier: "S1"
    movement_direction: "巷中段→Pedro方向·沿巷道中轴偏右·微朝垃圾桶"
    movement_path: "直线·起点Pedro身后~1m(距地50cm)·终点~0.85m·行程~15cm·匀速5s"
    dof_vector: [0, 0, 0, 0, 0, 0.03, 0]  # v_dolly=0.03m/s·纯前推无复合
    push_distance_cm: 15
    push_duration_s: 5
    static_exception: "非静态·极慢前推=情感重力·威胁退去后摄影机轻轻靠近Pedro·0.03x几乎不可感知"
    kb_rule_ids:
      - "M-MOV-04"
      - "M-MOT-02"
      - "M-MOT-03"
    spatial_verdict: "✅ 前推15cm在巷道纵深内·不穿Pedro/桶/墙·巷宽<2m纵向运动不触发横移禁制"

# ═══════════════════════════════════
# segments_transitions (全部硬切·无连续运镜过渡)
# ═══════════════════════════════════
segments_transitions:
  - {transition_id: "1→2", from_segment: "1", to_segment: "2", transition_type: "硬切", time_range: [6, 6], path: "N/A·硬切", visual_change: "从Pedro背影停步+巷口轿车剪影→硬切至Pedro POV看轿车·观察者→所见·经典POV切", kb_rule_ids: []}

  - {transition_id: "2→3", from_segment: "2", to_segment: "3", transition_type: "硬切", time_range: [12, 12], path: "N/A·硬切", visual_change: "从POV看车内交易→硬切回巷道Pedro跑向垃圾桶·所见→反应·信息差闭合", kb_rule_ids: []}

  - {transition_id: "3→4", from_segment: "3", to_segment: "4", transition_type: "硬切", time_range: [17, 17], path: "N/A·硬切", visual_change: "从桶侧看Pedro探头→硬切至桶后偷窥POV·观察者→所见(更受限视角)·嵌套信息差", kb_rule_ids: []}

  - {transition_id: "4→5", from_segment: "4", to_segment: "5", transition_type: "硬切", time_range: [23, 23], path: "N/A·硬切", visual_change: "从偷窥POV看车内→硬切至车内Rico近景·空间跳跃(巷道→轿车内)·威胁源突然拉近·悬念引爆", kb_rule_ids: []}

  - {transition_id: "5→6", from_segment: "5", to_segment: "6", transition_type: "硬切", time_range: [29, 29], path: "N/A·硬切", visual_change: "从Rico视角影子ECU→硬切至Pedro恐惧ECU·威胁扫描→恐惧反应·正反打恐惧释放", kb_rule_ids: []}

  - {transition_id: "6→7", from_segment: "6", to_segment: "7", transition_type: "硬切", time_range: [34, 34], path: "N/A·硬切", visual_change: "从Pedro右眼ECU→硬切至巷道远景OTS·极度压缩→全纵深展开·空间释放·恐惧余韵落地", kb_rule_ids: []}

# ═══════════════════════════════════
# frames_movement (逐秒运镜状态·39帧)
# ═══════════════════════════════════
frames_movement:
  # ===== 镜#1: 追球入巷·前跟拍+缓升 (0-5s, global 0-5) =====
  - {frame_id: "S2_1_start", seg_ref: "1", sec: 0, global_sec: 0, camera_position: "1", movement: "前跟拍(0.3x)·起幅·距地30cm", is_transition_frame: false}
  - {frame_id: "S2_1_01",  seg_ref: "1", sec: 1, global_sec: 1, camera_position: "1", movement: "前跟拍(0.3x)·匀速·距地30cm", is_transition_frame: false}
  - {frame_id: "S2_1_02",  seg_ref: "1", sec: 2, global_sec: 2, camera_position: "1", movement: "前跟拍(0.3x)+缓升始·距地30→45cm", is_transition_frame: false}
  - {frame_id: "S2_1_03",  seg_ref: "1", sec: 3, global_sec: 3, camera_position: "1", movement: "前跟拍(0.3x)+缓升·距地45→65cm", is_transition_frame: false}
  - {frame_id: "S2_1_04",  seg_ref: "1", sec: 4, global_sec: 4, camera_position: "1", movement: "前跟拍(0.2x)+缓升·距地65→85cm", is_transition_frame: false}
  - {frame_id: "S2_1_end", seg_ref: "1", sec: 5, global_sec: 5, camera_position: "1", movement: "极慢前推(0.05x)落定·距地100cm", is_transition_frame: false}

  # ===== 镜#2: Pedro POV·固定 (6-11s, global 6-11) =====
  - {frame_id: "S2_2_00", seg_ref: "2", sec: 6,  global_sec: 6,  camera_position: "2", movement: "固定", is_transition_frame: false}
  - {frame_id: "S2_2_01", seg_ref: "2", sec: 7,  global_sec: 7,  camera_position: "2", movement: "固定", is_transition_frame: false}
  - {frame_id: "S2_2_02", seg_ref: "2", sec: 8,  global_sec: 8,  camera_position: "2", movement: "固定", is_transition_frame: false}
  - {frame_id: "S2_2_03", seg_ref: "2", sec: 9,  global_sec: 9,  camera_position: "2", movement: "固定", is_transition_frame: false}
  - {frame_id: "S2_2_04", seg_ref: "2", sec: 10, global_sec: 10, camera_position: "2", movement: "固定", is_transition_frame: false}
  - {frame_id: "S2_2_05", seg_ref: "2", sec: 11, global_sec: 11, camera_position: "2", movement: "固定", is_transition_frame: false}

  # ===== 镜#3: 躲藏·垃圾桶后探头·固定 (12-16s, global 12-16) =====
  - {frame_id: "S2_3_00", seg_ref: "3", sec: 12, global_sec: 12, camera_position: "3", movement: "固定", is_transition_frame: false}
  - {frame_id: "S2_3_01", seg_ref: "3", sec: 13, global_sec: 13, camera_position: "3", movement: "固定", is_transition_frame: false}
  - {frame_id: "S2_3_02", seg_ref: "3", sec: 14, global_sec: 14, camera_position: "3", movement: "固定", is_transition_frame: false}
  - {frame_id: "S2_3_03", seg_ref: "3", sec: 15, global_sec: 15, camera_position: "3", movement: "固定", is_transition_frame: false}
  - {frame_id: "S2_3_04", seg_ref: "3", sec: 16, global_sec: 16, camera_position: "3", movement: "固定", is_transition_frame: false}

  # ===== 镜#4: 偷看POV·固定 (17-22s, global 17-22) =====
  - {frame_id: "S2_4_00", seg_ref: "4", sec: 17, global_sec: 17, camera_position: "4", movement: "固定", is_transition_frame: false}
  - {frame_id: "S2_4_01", seg_ref: "4", sec: 18, global_sec: 18, camera_position: "4", movement: "固定", is_transition_frame: false}
  - {frame_id: "S2_4_02", seg_ref: "4", sec: 19, global_sec: 19, camera_position: "4", movement: "固定", is_transition_frame: false}
  - {frame_id: "S2_4_03", seg_ref: "4", sec: 20, global_sec: 20, camera_position: "4", movement: "固定", is_transition_frame: false}
  - {frame_id: "S2_4_04", seg_ref: "4", sec: 21, global_sec: 21, camera_position: "4", movement: "固定", is_transition_frame: false}
  - {frame_id: "S2_4_05", seg_ref: "4", sec: 22, global_sec: 22, camera_position: "4", movement: "固定", is_transition_frame: false}

  # ===== 镜#5: Rico转头·固定三设硬切 (23-28s, global 23-28) =====
  - {frame_id: "S2_5_00", seg_ref: "5", sec: 23, global_sec: 23, camera_position: "5", movement: "固定(Rico CU·车内)", is_transition_frame: false}
  - {frame_id: "S2_5_01", seg_ref: "5", sec: 24, global_sec: 24, camera_position: "5", movement: "固定(Rico CU·车内)", is_transition_frame: false}
  - {frame_id: "S2_5_02", seg_ref: "5", sec: 25, global_sec: 25, camera_position: "5", movement: "固定(POV扫描·巷口)", is_transition_frame: false}
  - {frame_id: "S2_5_03", seg_ref: "5", sec: 26, global_sec: 26, camera_position: "5", movement: "固定(POV扫描·巷口)", is_transition_frame: false}
  - {frame_id: "S2_5_04", seg_ref: "5", sec: 27, global_sec: 27, camera_position: "5", movement: "固定(影子ECU·碎石)", is_transition_frame: false}
  - {frame_id: "S2_5_05", seg_ref: "5", sec: 28, global_sec: 28, camera_position: "5", movement: "固定(影子ECU·碎石)", is_transition_frame: false}

  # ===== 镜#6: Pedro反应·固定 (29-33s, global 29-33) =====
  - {frame_id: "S2_6_00", seg_ref: "6", sec: 29, global_sec: 29, camera_position: "6", movement: "固定", is_transition_frame: false}
  - {frame_id: "S2_6_01", seg_ref: "6", sec: 30, global_sec: 30, camera_position: "6", movement: "固定", is_transition_frame: false}
  - {frame_id: "S2_6_02", seg_ref: "6", sec: 31, global_sec: 31, camera_position: "6", movement: "固定", is_transition_frame: false}
  - {frame_id: "S2_6_03", seg_ref: "6", sec: 32, global_sec: 32, camera_position: "6", movement: "固定", is_transition_frame: false}
  - {frame_id: "S2_6_04", seg_ref: "6", sec: 33, global_sec: 33, camera_position: "6", movement: "固定", is_transition_frame: false}

  # ===== 镜#7: 轿车驶离·极慢前推 (34-38s, global 34-38) =====
  - {frame_id: "S2_7_start", seg_ref: "7", sec: 34, global_sec: 34, camera_position: "7", movement: "极慢前推(0.03x)·起幅·距Pedro~1.00m", is_transition_frame: false}
  - {frame_id: "S2_7_01",   seg_ref: "7", sec: 35, global_sec: 35, camera_position: "7", movement: "极慢前推(0.03x)·匀速·距Pedro~0.97m", is_transition_frame: false}
  - {frame_id: "S2_7_02",   seg_ref: "7", sec: 36, global_sec: 36, camera_position: "7", movement: "极慢前推(0.03x)·匀速·距Pedro~0.94m", is_transition_frame: false}
  - {frame_id: "S2_7_03",   seg_ref: "7", sec: 37, global_sec: 37, camera_position: "7", movement: "极慢前推(0.03x)·匀速·距Pedro~0.91m", is_transition_frame: false}
  - {frame_id: "S2_7_end",  seg_ref: "7", sec: 38, global_sec: 38, camera_position: "7", movement: "极慢前推(0.03x)·落幅·距Pedro~0.85m", is_transition_frame: false}
```

---

## 设计签名

```
┌──────────────────────────────────────────────────────────────────┐
│  Movement Designer 签名                                           │
│                                                                   │
│  版本: v2.0                                                       │
│  上下文: 独立上下文·仅运镜决策·不读Scene Designer推理             │
│  KB覆盖率: 100% (7/7镜含KB规则ID)                                │
│  运镜类型: 固定5镜 + 前跟拍+缓升1镜 + 极慢前推1镜              │
│  速度分布: S0=71.4% · S1=14.3% · S3=14.3%                       │
│  渲染可行性: ✅ 全部运镜路径在Seko稳定渲染范围内                  │
│  P-FAL规避: ✅ P-FAL-06(窄空间横移) 0触发·P-FAL-09 0触发         │
│  窄空间合规: ✅ 巷宽<2m·零横移·零环绕·全部纵向运动               │
│  空间合规: ✅ 全部运镜路径在巷道纵深内·不穿墙不悬空                │
│  画布宪法合规: ✅ 七条铁律全部合规                               │
│  过渡类型: 硬切 × 6·无连续运镜过渡                               │
│  静态例外: ✅ 5/5静态镜均有有效例外理由·无惰性静态               │
│                                                                   │
│  下游交付: storyboard_planner §2G (消费segments_movement +        │
│              frames_movement + segments_transitions)              │
│  关联文件: EP14_S2_SCENE_DESIGNER.md · CONTEXT_PACKAGE_EP14.md    │
│           ANCHOR_BASELINE_EP14.md · IMAGE_AUDIT_EP14.md           │
└──────────────────────────────────────────────────────────────────┘
```

> **v2.0 · 2026-07-07 · Movement Designer v2.0 独立产出**
> **关联文件:** EP14_S2_SCENE_DESIGNER.md · CONTEXT_PACKAGE_EP14.md · ANCHOR_BASELINE_EP14.md
> **替代:** 原运镜域委托——本报告为EP14 S2运镜域独立完成
> **运镜设计完成:** 7镜·39秒·窄巷·悬疑/偷窥·静态主导(71.4%)·复合跟拍(镜#1)+极慢前推(镜#7)
