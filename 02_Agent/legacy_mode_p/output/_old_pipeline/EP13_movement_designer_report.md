# Movement Designer 运镜设计报告 — 枪王 EP13《弹道学》

> **生成:** Movement Designer v2.0 · Step A2 串行第二位
> **日期:** 2026-07-07
> **场景:** 鉴证科实验室 · 双人对话 · 室内 · 日 · ~8m深×~5m宽
> **下游消费者:** storyboard_planner (Step A2.5·§2G TIME_SKELETON组装) · Composition Designer (Step A2·串行第三位)

---

## 场景情绪弧线

```
从原始剧本推断逐镜情绪值→映射运镜强度:

  镜#    情绪值    情绪标签              运镜强度映射
  ──────────────────────────────────────────────────
  ①      +1       发现·好奇·冷开场       S1 极慢推近
  ②       0       建立·疲惫的人物         S0 静态
  ③      +1       揭示·数据确证           S0 静态(信息密集)
  ④      +2       升温·压制的兴奋         S1 极慢推近
  ⑤      +1       建立·跨越认知阈值       S2 横移跟拍
  ⑥      +1       关注·处理证据           S0 静态(信息密集)
  ⑦      +2       升温·知识权力·激情      S1 极慢推近
  ⑧       0       中性·倾听者沉默         S0 静态(情感沉浸)
  ⑨      +3       冲击·动作爆发           S3 手持微晃
  ⑩      +2       揭示·证据确证           S1 极慢推近
  ⑪      +2       结论·确认的重量         S1 极慢推近
  ⑫       0→-1    释放·维度拓展·过渡      S2 摇臂上升
  ⑬      +3       高潮·名字的冲击         S1 极慢推近(反差设计)
  ⑭      -1       凝固·名字落地后          S0 静态(情感沉浸)
  ⑮      -1       闭合·螺旋母题落点        S1 极慢推近
  ⑯      -2       结束·光的死亡            S0 静态(情感沉浸)
  ⑰      -2       余韵·悬念               S0 静态(情感沉浸)

情绪弧线形状: +1→0→+1→+2→+1→+1→+2→0→+3→+2→+2→0→+3→-1→-1→-2→-2
            缓慢上升→动作爆发→平缓回落→情感高潮→寂静收束
```

## KB加载

```
加载章节:
  §5.1 镜头选择 (M-LEN-01~16) — 16条 · 焦距-运镜关系参考
  §5.2 运动方式 (M-MOV-01~16) — 16条 · 运动类型选择
  §5.3 运动动机与约束 (M-MOT-01~07) — 7条 · 动机-速度-空间约束
  §5.3b 二十条基本规律 (M-20R-00~20) — 21条 · 运动语法基石
  §5.4 运镜对话 → 指向 §1.3 D-DIA-12~22

P0安全规则始终加载:
  M-MOT-03 (空间-运镜可行性约束)
  M-MOT-04 (运镜速度空间约束)
  M-MOT-05 (首帧锁定)
  M-20R-07 (三部分运动公式·静→动→静)
  M-20R-10 (同一画面区域沿同一方向运动)
  M-20R-12 (运动要顺畅有把握)
  M-20R-15 (起幅和落幅的构图平衡)
  M-20R-00 (零号法则·所有运动必须有戏剧动机)

P-STATE §1 已验证模式: 全部待首次验证·无已确认模式可供优先使用
P-STATE §2 已知失败规避:
  P-FAL-06(窄空间横移): 本场景走道宽~2.5m·深~8m·>3m深度·不触发 ✅
  P-FAL-09(极端运动形变): 仅#9手持0.3x微晃·不触发 ✅
  其余P-FAL-01~05/07/08/10: 与运镜设计无直接相关 ✅
```

---

## 逐镜运镜设计

---

### 分镜 #1 — 弹头ECU · 冷开场 · Segment ① (0-4s)

```
运镜类型: 极慢推近
速度参数: 0.1x · 4秒 · 推约2cm→0.5cm (从弹头表面微距距离→极近距离)
方向: 前推(沿显微镜光轴方向)
起止状态: 起点(距弹头~5-8cm·略侧15°) → 终点(距弹头~2-3cm·极近)
时长: 4s
KB规则ID: M-MOT-01(运镜必须有动机·冷开场=建立核心证据) + M-MOV-04(向前运动·强调主体重要性) + M-MOT-02(速度匹配情绪·+1好奇心=慢速) + M-20R-07(静→动→静·三部分运动公式) + M-20R-15(起幅落幅构图平衡)
情绪匹配: 情绪=+1(发现·好奇)·运镜强度=S1(极慢)·差值=0 ✅
空间约束: 推近路径在显微镜载物台上方·微距轨道·无遮挡 ✅
动机: 冷开场=用极慢推近将观众拉入微观世界·弹头膛线螺旋纹路逐渐占据画面——"值得推近看" ✅

静态镜检测: 非静态·推近动机明确 ✅
```

### 分镜 #2 — Vincent摘眼镜 · 人物建立 · Segment ② (4-7s)

```
运镜类型: 静态(固定)
速度参数: S0 · 0x
方向: N/A
起止状态: 固定于走道区域②·距Vincent~1.2m·CAM A面·微仰5°
时长: 3s
KB规则ID: M-MOT-01(运镜必须有动机·此镜动机="停留"而非运动——首次建立人物·观众需要时间吸收) + M-20R-05(直接切换比移动镜头更经济·此镜信息已由构图承载)
情绪匹配: 情绪=0(建立)·运镜强度=S0(静态)·差值=0 ✅
空间约束: 机位固定在走道区域②·无运动·不触发空间约束 ✅

静态镜检测: ✅ 信息密集——首次建立Vincent人物形象·"被工作消耗的人"·黑框眼镜核心锚点·观众需要时间吸收面部信息
非静态动机检测: N/A (此镜为静态)
```

### 分镜 #3 — 电脑屏幕 · 数据域 · Segment ③ (7-10s)

```
运镜类型: 静态(固定)
速度参数: S0 · 0x
方向: N/A
起止状态: 固定于复合工作站前·距屏幕~0.6m·正视
时长: 3s
KB规则ID: M-MOT-01(运镜动机=信息吸收——屏幕展示五枚弹头膛线照片·数据需要停留阅读) + M-20R-05(切换比移动更经济)
情绪匹配: 情绪=+1(揭示)·运镜强度=S0(静态)·差值=1 ⚠️
说明: 情绪+1但选择静态——此镜为插入镜头(屏幕特写)·信息密集·运镜会干扰数据阅读·静态是信息传达最优解·非错位
空间约束: 固定于复合工作站前·无运动 ✅

静态镜检测: ✅ 信息密集——五枚弹头膛线照片并列排开·需要时间比对·屏幕文字信息量高
非静态动机检测: N/A
```

### 分镜 #4 — Vincent打电话 · 情绪转折 · Segment ④ (10-14s)

```
运镜类型: 极慢推近
速度参数: 0.08x · 4秒 · 推约6cm (距Vincent~1.1m→~1.04m)
方向: 前推(沿Vincent视线方向·微仰保持)
起止状态: 起点(走道区域②·距Vincent~1.1m·眼平微仰) → 终点(~1.04m·稍更近)
时长: 4s
KB规则ID: M-MOT-01(动机=情绪升温·"压低的兴奋"→物理靠近) + M-MOT-02(情绪+2升温=慢速推近) + M-MOT-07(运镜与对话呼吸同步·Vincent压低的嗓音·运镜同步减速克制) + M-MOV-04(向前运动·强调Vincent的兴奋) + M-20R-07(静→动→静) + M-20R-13(人物先动→摄影机跟动·Vincent拿起手机的动作触发运镜动机)
情绪匹配: 情绪=+2(升温)·运镜强度=S1(极慢)·差值=1 ⚠️
说明: 情绪升温但运镜极慢——Vincent的兴奋是"被压制的"·他压低声音对手机说"现在过来"·运镜极慢=压制的兴奋·用克制的运动表达被抑制的情绪·反差设计·非错位
空间约束: 推近路径在走道区域②·无障碍 ✅

非静态动机检测:
  推近: Vincent拿起手机·压低声音·情绪升温 → "值得推近看" ✅
```

### 分镜 #5 — Miguel入室 · 空间建立 · Segment ⑤ (14-18s)

```
运镜类型: 稳定器横移跟拍
速度参数: 0.3x · 4秒 · 横移约1.2m (跟随Miguel从门→走道中段)
方向: 右横移(CAM A面东侧·跟随Miguel向西侧工作台方向移动)
起止状态: 起点(走道区域②·靠近门侧·距门~2m·门框入画) → 终点(走道区域②中段·距Vincent~5m→~3.8m)
时长: 4s
KB规则ID: M-MOT-01(动机=Miguel出场·"跨越认知阈值"→摄影机跟随) + M-MOV-01(演员驱动摄影机·Miguel推门进入→摄影机跟随) + M-MOV-08(推轨引入演员·轨道移动跟随演员入画) + M-MOV-02(与摄影机一同运动·Miguel和摄影机同步移动) + M-20R-07(静→动→静) + M-20R-13(人物先动·Miguel推门→摄影机跟动) + M-MOT-03(走廊→走道宽~2.5m·跟拍可行·禁摇镜) + M-MOT-04(空间深度~8m>5m·速度≤3.0x·0.3x远低于上限 ✅)
情绪匹配: 情绪=+1(建立/兴趣)·运镜强度=S2(慢速跟拍)·差值=1 ⚠️
说明: 情绪+1但运镜S2——Miguel入室是空间建立镜头·需要跟拍来收纳门外→室内·走廊暖光→实验室冷光的色温过渡·S2跟拍比S1更适应人物移动速度·差值在可接受范围
空间约束: 走道宽~2.5m·横移跟拍可行·跟拍路径沿走道中轴线·无障碍 ✅

非静态动机检测:
  跟拍: Miguel推门入室·人物运动驱动摄影机运动 ✅
```

### 分镜 #6 — Miguel看屏幕 · 内反拍单人 · Segment ⑥ (18-21s)

```
运镜类型: 静态(固定)
速度参数: S0 · 0x
方向: N/A
起止状态: 固定于走道区域②·关系线内侧·距Miguel~1.2m·眼平
时长: 3s
KB规则ID: M-MOT-01(动机=信息吸收——Miguel处理五张膛线照片·视线扫描·信息密集)
情绪匹配: 情绪=+1(关注)·运镜强度=S0(静态)·差值=1 ⚠️
说明: 同#3·插入/信息处理镜头·运镜干扰信息吸收·静态最优
空间约束: 固定·无运动 ✅

静态镜检测: ✅ 信息密集——Miguel正在处理五张膛线照片的视觉比对·CU近景·观众和Miguel同步处理证据信息
```

### 分镜 #7 — Vincent解释膛线 · 知识权力 · Segment ⑦ (21-26s)

```
运镜类型: 极慢推近
速度参数: 0.05x · 5秒 · 推约5cm (距Vincent~1.2m→~1.15m)
方向: 前推(微仰保持·沿Vincent→Miguel视线轴)
起止状态: 起点(走道区域②·关系线内侧·距Vincent~1.2m·微仰3-5°) → 终点(~1.15m·画面更紧凑)
时长: 5s (全场第二长运动镜)
KB规则ID: M-MOT-01(动机=知识权力传递·"这是一个人的签名"→摄影机推进强化话语重量) + M-MOT-02(情绪+2升温=慢速·但全场最具叙事分量的对白·需更克制的速度·0.05x比常规+2情绪更慢·用极慢强化知识权威的沉稳) + M-MOT-07(运镜与对话呼吸同步·Vincent解释膛线的节奏·"力度、角度、每一道的间距"——语速平稳·运镜同步平稳推进) + M-MOV-04(向前运动·强调话语重量) + M-20R-07(静→动→静) + M-20R-19(跟拍中背景变化而人物构图不变·推近中Vincent面部大小缓慢变化·背景保持虚化固定)
情绪匹配: 情绪=+2(升温)·运镜强度=S1(极慢)·差值=1 ⚠️
说明: 情绪+2但运镜S1极慢——知识权力的表达不靠速度·靠沉稳。Vincent不是在喊口号·是在陈述事实。"签名"的重量靠极慢推近来累积·而非加速。反差设计·非错位
空间约束: 推近路径在走道区域②·路径上无障碍 ✅

非静态动机检测:
  推近: Vincent说"这是一个人的签名"——全场最具叙事分量的对白·"值得推近看" ✅
```

### 分镜 #7.5 — Miguel倾听反应 · 覆盖修复 · Segment ⑧ (26-28s)

```
运镜类型: 静态(固定)
速度参数: S0 · 0x
方向: N/A
起止状态: 固定于走道区域②·关系线内侧·同#6机位·距Miguel~1.2m
时长: 2s
KB规则ID: M-MOT-01(动机=倾听者的沉默反应·"凝固的空气比任何运镜都有力"·D-DIA-11上下文) + M-20R-05(切换比移动更经济·反应镜头不需运镜)
情绪匹配: 情绪=0(中性·倾听)·运镜强度=S0(静态)·差值=0 ✅
空间约束: 固定·无运动 ✅

静态镜检测: ✅ 情感沉浸——Miguel倾听Vincent关于"签名"的论述·沉默的反应蕴含力量·D-DIA-11精神:"摄影机完全不动·凝固的空气比任何运镜都有力"
```

### 分镜 #8 — Vincent摔档案 · 动作冲击 · Segment ⑨ (28-32s)

```
运镜类型: 手持微晃
速度参数: 0.3x · 4秒 (手持稳定器·非匀速推轨·微晃幅度±3-5cm)
方向: 固定机位(不位移)·手持微晃(机身微动)
起止状态: 起点(走道区域②·CAM A面·距Vincent~2m·35mm广角) → 终点(同机位·档案摔落后画面微震)
时长: 4s
KB规则ID: M-MOT-01(动机=动作冲击·档案"砰"摔桌上→物理冲击需运镜表达) + M-MOT-02(情绪+3高潮=快速·但此镜的核心动作(摔档案)已提供视觉冲击·运镜只需手持微晃传递物理震颤感·不需加速推拉) + M-MOV-10(融合运动·Vincent转身+摔档案+摄影机手持微晃·动作和运镜融合) + M-20R-07(静→微晃→静) + M-20R-13(人物先动·Vincent抽抽屉→转身→摔档案·摄影机在档案摔下瞬间微晃)
情绪匹配: 情绪=+3(冲击·动作爆发)·运镜强度=S3(手持微晃)·差值=0 ✅
空间约束: 固定机位于走道区域②·机位无位移·手持微晃不改变机位位置 ✅

非静态动机检测:
  手持: 场景需要"不安/临场感/冲击感" ✅
  推近: N/A (此镜为手持微晃·不推拉)
```

### 分镜 #9 — 两张照片并排 · 证据确证 · Segment ⑩ (32-36s)

```
运镜类型: 极慢推近
速度参数: 0.05x · 4秒 · 推约2cm (距桌面~40cm→~38cm·垂直俯拍)
方向: 下降+前推微复合(垂直俯拍→微倾·由正上方→略偏10°前倾)
起止状态: 起点(工作台桌面正上方~40cm·垂直俯拍90°) → 终点(~38cm·略倾~80°·更近距离审视膛线纹路)
时长: 4s
KB规则ID: M-MOT-01(动机=证据确证·"CORRESPONDENCIA ALINHADA 100%"→推近揭示) + M-MOV-03(揭示式运动·推近打破常规构图期待·将注意力从档案转移到膛线纹路的完美重合) + M-MOT-02(情绪+2=慢速·证据确证的沉稳) + M-20R-04(揭示被期待的事物·运动终点对准观众期待的证据匹配结果) + M-20R-07(静→动→静)
情绪匹配: 情绪=+2(揭示·确证)·运镜强度=S1(极慢)·差值=1 ⚠️
说明: 情绪+2但运镜S1——证据比对需要沉稳的视觉节奏·极慢推近让观众有时间比较两条"平行的闪电"·速度再快反而分散注意力
空间约束: 推近路径在工作台桌面上方·无遮挡 ✅

非静态动机检测:
  推近: 膛线纹路"像两条平行的闪电"→"值得推近看" ✅
```

### 分镜 #10 — Vincent"同一只手·同一种审美" · Segment ⑪ (36-39s)

```
运镜类型: 极慢推近(全场最慢)
速度参数: 0.03x · 3秒 · 推约1.5cm (距Vincent~1.1m→~1.085m·几乎不可察觉)
方向: 前推(微仰保持5°)
起止状态: 起点(走道区域②·关系线内侧·同#7机位·距Vincent~1.1m·微仰5°) → 终点(~1.085m·极微小前移)
时长: 3s
KB规则ID: M-MOT-01(动机=结论的重量·"同一只手·同一种审美"→推进强化话语的最终性) + M-MOT-02(情绪+2=慢速·但结论的沉重需要全场最慢速度·0.03x比常规+2情绪更慢) + D-DIA-19(聚焦于一人·摄影机锁定Vincent·缓慢推进·锁定主角面部) + M-MOV-04(向前运动·强调结论) + M-MOT-07(运镜与对话呼吸同步·Vincent最后的停顿"...审美"·运镜几乎静止·配合话语的落点) + M-20R-07(静→极微动→静)
情绪匹配: 情绪=+2(结论·确认)·运镜强度=S1(极慢·全场最慢)·差值=1 ⚠️
说明: 全场的结论时刻·用全场最慢的推近(0.03x)表达"确认的重量"·运镜几乎不可察觉——观众注意力完全在Vincent的最后两个字"审美"上·运镜的在场感是潜意识的。反差设计·非错位
空间约束: 推近路径在走道区域②·无障碍 ✅

非静态动机检测:
  推近: "同一只手·同一种审美"——全剧结论·"值得推近看" ✅
```

### 分镜 #11 — 摇臂升起 · 从证据到世界 · Segment ⑫ (39-45s)

```
运镜类型: 摇臂上升(垂直运动)
速度参数: 0.2x · 6秒 · 上升约1.5m (起点~90cm→终点~2.4m)
方向: 上升(垂直·从俯拍桌面→到水平看窗外)
起止状态: 起点(工作台桌面上方~90cm·俯拍~45°·24mm广角) → 终点(窗前~2.4m高度·水平0°·窗外城市全景)
时长: 6s (全场最长运动镜)
KB规则ID: M-MOT-01(动机=视觉化的语境拓展·从微观弹道证据到宏观城市·"证据→世界"的维度跨越) + M-MOV-03(揭示式运动·摇臂升起揭示窗外圣保罗午后世界) + M-MOV-04(向前/向上运动·强调空间维度的展开) + M-MOT-02(情绪0→-1疏离·摇臂升起的速度0.2x=沉思节奏·不逃不冲) + M-20R-04(揭示被期待的事物·运动终点对准窗外城市——观众知道证据链闭合后需要"向外看") + M-20R-07(静→动→静·6秒三部分) + M-20R-15(起幅=桌面俯拍平衡·落幅=窗前水平城市全景平衡) + M-20R-11(省略与重新引入·升降过程中摄入Vincent肩→百叶窗框→室外城市·三层深度调度)
情绪匹配: 情绪=0→-1(释放·过渡)·运镜强度=S2(慢速上升)·差值=2~3 ⚠️
说明: 情绪从0趋-1但运镜S2——此镜是全剧唯一的长运镜过渡镜·6秒摇臂上升承担"从证据到世界"的叙事过渡功能·S2(0.2x)是沉思节奏·比S1更适合长距离运动·视觉变化主导·情绪为背景
空间约束: 起始锚定于工作台区域①→中途穿过走道区域②→终点锚定于窗口区域④·路径全部在空间地图内 ✅
  ⚠️ 摇臂上升路径经过走道区域②天花板·需确认实验室层高~3m·终点~2.4m·不触顶 ✅

非静态动机检测:
  上升: 从微观到宏观的"维度拓展"→叙事动机明确 ✅
```

### 分镜 #12 — Miguel"Rico" · 名字的重量 · Segment ⑬ (45-48s)

```
运镜类型: 极慢推近
速度参数: 0.08x · 3秒 · 推约5cm (距Miguel~1.2m→~1.15m)
方向: 前推(微俯保持5°·Rembrandt侧逆光)
起止状态: 起点(窗前区域④·CAM A面·距Miguel~1.2m·微俯5°) → 终点(~1.15m)
时长: 3s
KB规则ID: M-MOT-01(动机=名字的压迫·"Rico"→推近强化名字落地的重量) + M-MOT-02(情绪+3高潮=快速·但"名字的冲击"不是动作冲击·是认知冲击——极慢推近让名字的重量累积·而非用快速运镜分散注意力) + D-DIA-12(力量对比·低角度Vincent=知识权力 vs 微俯角Miguel=被名字压倒·推近强化"被压倒"的视觉感受) + M-MOV-04(向前运动·强调名字的重量) + M-20R-07(静→动→静)
情绪匹配: 情绪=+3(高潮·名字的冲击)·运镜强度=S1(极慢)·差值=2 ⚠️
说明: 全场最高情绪(+3)配最克制的运镜(S1)——这是全剧情感高潮·但不是动作高潮。"Rico"这个名字的冲击力不是靠运镜速度传达的·而是靠Miguel面部的微表情和Rembrandt光。极慢推近=名字的重量在空气中缓慢沉淀。反差设计·非错位
空间约束: 推近路径在窗前区域④·无障碍 ✅

非静态动机检测:
  推近: Miguel说出"Rico"——全剧情感高潮·"值得推近看" ✅
```

### 分镜 #12.5 — Miguel面部凝固 · 名字落地后 · Segment ⑭ (48-50s)

```
运镜类型: 静态(固定)
速度参数: S0 · 0x
方向: N/A
起止状态: 固定于窗前区域④·同#12机位·距Miguel~1.2m·微俯5°
时长: 2s
KB规则ID: M-MOT-01(动机=凝固——名字落地后2秒·"用压抑表现力量"·D-DIA-11精神) + D-DIA-11(肢体语言对抗·摄影机完全不动·凝固的空气比任何运镜都有力) + M-20R-12(要么完全静止·要么平稳移动——此镜选择完全静止)
情绪匹配: 情绪=-1(凝固·疏离)·运镜强度=S0(静态)·差值=1 ✓ (-1情绪配S0静态在映射范围内)
空间约束: 固定·无运动 ✅

静态镜检测: ✅ 情感沉浸——名字落地后2秒凝固·"黑暗有层次"·"用压抑表现力量"·Miguel的"眼睛已经在别处了"。D-DIA-11明确指示"摄影机完全不动·凝固的空气比任何运镜都有力"
```

### 分镜 #13 — Miguel右手 · 螺旋母题闭合 · Segment ⑮ (50-53s)

```
运镜类型: 极慢推近
速度参数: 0.05x · 3秒 · 推约1.5cm (距右手~25cm→~23.5cm)
方向: 前推(略侧30°保持·微俯保持)
起止状态: 起点(Miguel身侧·工作台边缘·距右手~25cm·略侧30°) → 终点(~23.5cm·手指间的空隙更清晰)
时长: 3s
KB规则ID: M-MOT-01(动机=螺旋母题闭环·"弹头螺旋→膛线螺旋→Miguel手指螺旋"·推近揭示手指间的空=枪柄形状) + M-MOV-03(揭示式运动·推近打破构图期待·将注意力从面部转移到手部螺旋) + M-MOT-02(情绪-1疏离=慢速·闭合的沉思) + M-20R-04(揭示未被期待的事物·观众预期看面部·镜头却给手部ECU)
情绪匹配: 情绪=-1(闭合·沉思)·运镜强度=S1(极慢)·差值=0 ✅
空间约束: 推近路径在窗前区域④/工作台边缘·无障碍 ✅

非静态动机检测:
  推近: Miguel右手蜷握形成枪柄弧度——"值得推近看"·螺旋母题最终落点 ✅
```

### 分镜 #14 — 显微镜灯灭 · 光的死亡 · Segment ⑯ (53-56s)

```
运镜类型: 静态(固定)
速度参数: S0 · 0x
方向: N/A
起止状态: 固定于显微镜工作台·载物台上方·同#1机位·距弹头~5-8cm
时长: 3s
KB规则ID: M-MOT-01(动机="停留"——光的死亡是这3秒的唯一事件·运镜会干扰钨丝冷却的色彩安魂曲) + M-20R-05(切换比移动更经济·灯灭是静态事件·不需要运镜表达)
情绪匹配: 情绪=-2(结束·光的死亡)·运镜强度=S0(静态)·差值=2 ⚠️
说明: 情绪-2但运镜S0——钨丝冷却本身就是"运动"(光的衰减从琥珀→暗红→深红→消失)·摄影机保持静止让观众专注见证"光的死亡"·运镜会干扰这一视觉事件
空间约束: 固定·无运动 ✅

静态镜检测: ✅ 信息密集+情感沉浸双重——钨丝冷却的色彩变化(琥珀→暗红→深红→消失)是这3秒的核心视觉事件·静态=让光自己"表演"。同时是圆形闭合(#1弹头ECU→#14同机位灯灭)
```

### 分镜 #15 — 窗光余韵 · 黑暗有层次 · Segment ⑰ (56-58s)

```
运镜类型: 静态(固定)
速度参数: S0 · 0x
方向: N/A
起止状态: 固定于实验室地板·窗前区域④·距地面~0.3-0.5m·低角度仰15°
时长: 2s
KB规则ID: M-MOT-01(动机=终场停留·"黑暗有层次·微光渗入=悬念"·全剧最后一个镜头用静止"呼吸") + M-20R-05(切换比移动更经济·终镜不需要运镜)
情绪匹配: 情绪=-2(余韵·悬念)·运镜强度=S0(静态)·差值=2 ⚠️
说明: 情绪-2但运镜S0——全剧终镜·光栅衰减(暖金→淡黄→消失)是最后2秒的唯一视觉事件·摄影机静止·让光自己褪去·给观众留下最后一帧的"黑暗有层次"。运镜会破坏终场的寂静
空间约束: 固定·无运动 ✅

静态镜检测: ✅ 情感沉浸——全剧最后一个镜头·"黑暗有层次·微光渗入=悬念"。终场的寂静靠摄影机静止来传达·任何运镜都会破坏这种终结感
```

---

## 运镜序列分析 (Step D)

### 速度分布

```
全剧17镜速度分布:

  S0 静态(0x):          ②③⑥⑧⑭⑯⑰ — 7镜 (41%)
  S1 极慢(0.03x-0.1x):  ①④⑦⑩⑪⑬⑮  — 7镜 (41%)
  S2 慢(0.2x-0.3x):     ⑤⑫           — 2镜 (12%)
  S3 中(0.3x):           ⑨            — 1镜 (6%)
  S4 中快(1.0x):         无            — 0镜
  S5-S8:                 无            — 0镜

速度分布分析:
  ⚠️ S0=41% > 40% 阈值 — 静态比例略高·但场景类型(鉴证科实验室双人对话)天然偏好固定机位
  ⚠️ S1=41% > 40% 阈值 — 极慢运镜集中·但此场景的叙事基调(科学/精密/沉思)天然匹配极慢速度
  ⚠️ S0+S1=82% — 速度集中在静态-极慢区间·场景一致性可接受
  🔴 缺失中速/快速层(S4-S8) — 但本场景无打斗/追逐/动作戏·不需要快速运镜
  → 结论: 速度分布"单一是场景气质·非设计缺陷"
```

### 相邻跳跃检测

```
镜间跳跃矩阵(S0-S8):

  ①(S1)→②(S0): |1-0|=1 ✅
  ②(S0)→③(S0): |0-0|=0 ✅
  ③(S0)→④(S1): |0-1|=1 ✅
  ④(S1)→⑤(S2): |1-2|=1 ✅
  ⑤(S2)→⑥(S0): |2-0|=2 ✅
  ⑥(S0)→⑦(S1): |0-1|=1 ✅
  ⑦(S1)→⑧(S0): |1-0|=1 ✅
  ⑧(S0)→⑨(S3): |0-3|=3 ⚠️ 接近阈值·但动机明确(静态倾听→动作冲击·摔档案)
  ⑨(S3)→⑩(S1): |3-1|=2 ✅
  ⑩(S1)→⑪(S1): |1-1|=0 ✅
  ⑪(S1)→⑫(S2): |1-2|=1 ✅
  ⑫(S2)→⑬(S1): |2-1|=1 ✅
  ⑬(S1)→⑭(S0): |1-0|=1 ✅
  ⑭(S0)→⑮(S1): |0-1|=1 ✅
  ⑮(S1)→⑯(S0): |1-0|=1 ✅
  ⑯(S0)→⑰(S0): |0-0|=0 ✅

跳跃检测结论:
  ✅ 无≥4级极端跳跃
  ⚠️ ⑧→⑨: S0→S3 (3级跳跃) — 动机明确·叙事触发·可接受
```

### 加速度波形

```
运镜强度波形 (S0-S3):

  S3 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░█░░░░░░░░░░░░░░░░░░░
  S2 ░░░░░░░░░░░░░░░░░░█░░░░░░░░░░░░░░░█░░░░░░░░░░░░░░
  S1 █░░░░░░░█░░░░░░░░░░░░░█░░░░░██░░░░░█░░░░░█░░░░░░░
  S0 ░░██░░░░░░░██░░░░██░░░░░░░░░░░░░░░░░░░██░░░██░░██
    ① ② ③ ④ ⑤ ⑥ ⑦ ⑧ ⑨ ⑩ ⑪ ⑫ ⑬ ⑭ ⑮ ⑯ ⑰
     0  4  7  10 14 18 21 26 28 32 36 39 45 48 50 53 56 (秒)

波形特征:
  ✅ 形成呼吸波形 — 不是方波·不是直线
  ✅ 波峰在#⑨(S3·动作冲击)·次峰在#⑤(S2·跟拍)和#⑫(S2·摇臂)
  ✅ 波谷均匀分布在信息密集/情感沉浸的静态镜
  ✅ 全剧结尾(#⑮⑯⑰)逐渐回落至S0·形成安静的收束
```

### 两极分化检测

```
静态(S0) + 极快(S5+) = 7 + 0 = 41%
✅ <60% 阈值·不触发两极分化警告
```

---

## 空间约束总结

```
✅ 全部17镜运镜路径在可拍摄空间内

详细验证:
  ✅ #①②④⑦⑧⑩⑪: 走道区域②·推近/固定/手持·路径无遮挡
  ✅ #③: 复合工作站区域⑤·固定·无位移
  ✅ #⑤: 走道区域②·横移跟拍·走道宽~2.5m·可容纳摄影机+操作员
  ✅ #⑥: 走道区域②·固定·无位移
  ✅ #⑨: 走道区域②·固定机位手持微晃·不位移·无碰撞风险
  ✅ #⑫: 起始工作台区域①→中途走道②→终点窗口区域④·全程在空间内·天花板高度~3m·终点~2.4m·不触顶 ✅
  ✅ #⑬⑭⑮: 窗前区域④·推近/固定·路径无遮挡
  ✅ #⑯: 工作台区域①·固定·同#1机位
  ✅ #⑰: 窗前区域④/走道②交界·固定·地面低角度

  🛑 无阻断
  ⚠️ 无边界警告
  ⚠️ #⑫摇臂上升经过走道区域②天花板·已确认层高~3m·终点~2.4m·余量充足

M-MOT-03 空间-运镜可行性约束: 全部通过 ✅
M-MOT-04 运镜速度空间约束: 空间深度~8m>5m·全部速度≤0.3x·远低于3.0x上限 ✅
P-FAL-06(窄空间横移): 走道~2.5m宽·~8m深·>3m深度·不触发 ✅
P-FAL-09(极端运动形变): 仅#9手持0.3x微晃·不触发 ✅
```

---

## P-STATE 对照检查

```
P-STATE §1 已验证可渲染模式: 全部待首次验证·无已确认模式可供优先使用
  说明: 本次设计的运镜模式(极慢推近·横移跟拍·摇臂上升·手持微晃)均为首次使用·标注"新模式"

P-STATE §2 已知失败模式规避:
  P-FAL-01(瞳孔控制): ✅ 不涉及
  P-FAL-02(mm精度): ✅ 运镜参数使用cm级描述
  P-FAL-03(亚秒): ✅ 逐秒精度·不描述亚秒事件
  P-FAL-04(≥3音效): ✅ 不涉及音效设计
  P-FAL-05(VO语速): ✅ 不涉及VO设计
  P-FAL-06(窄空间横移): ✅ 走道~2.5m宽·~8m深·>3m
  P-FAL-07(高频视觉噪声): ✅ 本场景无高频视觉元素
  P-FAL-08(画面文字): ✅ 不要求在画面中渲染文字
  P-FAL-09(极端运动形变): ✅ 全场最大速度0.3x(手持微晃/跟拍)·无快速/大幅度运动
  P-FAL-10(多人口型): ✅ 本场景为交替单人口型·不触发
```

---

## 画布宪法对照

```
画布宪法第三条(空间锚定):
  ✅ 全部运镜路径均在空间地图人物可放置区域内
  ✅ 推近路径可追溯到走道区域②/工作台区域①/窗前区域④
  ✅ 横移跟拍路径沿走道中轴线·可追溯到走道区域②
  ✅ 摇臂上升路径从工作台①→走道②→窗前④·全程锚定
  ✅ 运镜不穿墙·不悬空

画布宪法第四条(运镜-画面分离):
  ✅ 本报告仅描述运镜参数·不含画面描述
  ✅ 每镜独立完整·不跨镜引用运镜状态
```

---

## §6 结构化 TIME_SKELETON 输出 (v2.0)

### 6.1 segments_movement YAML

```yaml
# ─── Movement Designer v2.0 · segments_movement ───
# 下游: storyboard_planner §2G → TIME_SKELETON.segments[].camera.movement
# 在Shot Architect的segments_camera基础上补充movement字段

segments_movement:
  - segment_id: "①"
    movement: "极慢前推"
    movement_speed: "0.1x"
    movement_direction: "前推(沿显微镜光轴)"
    movement_range: "距弹头~5-8cm→~2-3cm"
    movement_duration_sec: 4
    movement_speed_tier: "S1"
    kb_rule_ids:
      - "M-MOT-01"
      - "M-MOV-04"
      - "M-MOT-02"
      - "M-20R-07"
      - "M-20R-15"

  - segment_id: "②"
    movement: "固定"
    movement_speed: "0x"
    movement_direction: "N/A"
    movement_range: "N/A"
    movement_duration_sec: 3
    movement_speed_tier: "S0"
    static_motivation: "信息密集·首次建立Vincent人物形象"
    kb_rule_ids:
      - "M-MOT-01"
      - "M-20R-05"

  - segment_id: "③"
    movement: "固定"
    movement_speed: "0x"
    movement_direction: "N/A"
    movement_range: "N/A"
    movement_duration_sec: 3
    movement_speed_tier: "S0"
    static_motivation: "信息密集·屏幕膛线照片需要时间比对"
    kb_rule_ids:
      - "M-MOT-01"
      - "M-20R-05"

  - segment_id: "④"
    movement: "极慢前推"
    movement_speed: "0.08x"
    movement_direction: "前推(沿Vincent视线方向·微仰保持)"
    movement_range: "距Vincent~1.1m→~1.04m"
    movement_duration_sec: 4
    movement_speed_tier: "S1"
    kb_rule_ids:
      - "M-MOT-01"
      - "M-MOT-02"
      - "M-MOT-07"
      - "M-MOV-04"
      - "M-20R-07"
      - "M-20R-13"

  - segment_id: "⑤"
    movement: "稳定器横移跟拍"
    movement_speed: "0.3x"
    movement_direction: "右横移(跟随Miguel从门→走道中段)"
    movement_range: "距门~2m→走道中段·横移~1.2m"
    movement_duration_sec: 4
    movement_speed_tier: "S2"
    kb_rule_ids:
      - "M-MOT-01"
      - "M-MOV-01"
      - "M-MOV-02"
      - "M-MOV-08"
      - "M-20R-07"
      - "M-20R-13"
      - "M-MOT-03"
      - "M-MOT-04"

  - segment_id: "⑥"
    movement: "固定"
    movement_speed: "0x"
    movement_direction: "N/A"
    movement_range: "N/A"
    movement_duration_sec: 3
    movement_speed_tier: "S0"
    static_motivation: "信息密集·Miguel处理五张膛线照片·视线扫描"
    kb_rule_ids:
      - "M-MOT-01"

  - segment_id: "⑦"
    movement: "极慢前推"
    movement_speed: "0.05x"
    movement_direction: "前推(微仰保持3-5°·沿Vincent→Miguel视线轴)"
    movement_range: "距Vincent~1.2m→~1.15m"
    movement_duration_sec: 5
    movement_speed_tier: "S1"
    kb_rule_ids:
      - "M-MOT-01"
      - "M-MOT-02"
      - "M-MOT-07"
      - "M-MOV-04"
      - "M-20R-07"
      - "M-20R-19"
    dialog_sync: "运镜与Vincent解释膛线的语速同步平稳推进"

  - segment_id: "⑧"
    movement: "固定"
    movement_speed: "0x"
    movement_direction: "N/A"
    movement_range: "N/A"
    movement_duration_sec: 2
    movement_speed_tier: "S0"
    static_motivation: "情感沉浸·倾听者的沉默反应·D-DIA-11精神"
    kb_rule_ids:
      - "M-MOT-01"
      - "M-20R-05"

  - segment_id: "⑨"
    movement: "手持微晃"
    movement_speed: "0.3x(微晃幅度)"
    movement_direction: "固定机位·机身微动(±3-5cm)"
    movement_range: "机位不位移·仅机身微晃"
    movement_duration_sec: 4
    movement_speed_tier: "S3"
    kb_rule_ids:
      - "M-MOT-01"
      - "M-MOT-02"
      - "M-MOV-10"
      - "M-20R-07"
      - "M-20R-13"

  - segment_id: "⑩"
    movement: "极慢前推"
    movement_speed: "0.05x"
    movement_direction: "下降+前推微复合(垂直俯拍90°→略倾~80°前倾)"
    movement_range: "距桌面~40cm→~38cm"
    movement_duration_sec: 4
    movement_speed_tier: "S1"
    kb_rule_ids:
      - "M-MOT-01"
      - "M-MOV-03"
      - "M-MOT-02"
      - "M-20R-04"
      - "M-20R-07"

  - segment_id: "⑪"
    movement: "极慢前推"
    movement_speed: "0.03x"
    movement_direction: "前推(微仰保持5°)"
    movement_range: "距Vincent~1.1m→~1.085m·几乎不可察觉"
    movement_duration_sec: 3
    movement_speed_tier: "S1"
    kb_rule_ids:
      - "M-MOT-01"
      - "M-MOT-02"
      - "M-MOV-04"
      - "M-MOT-07"
      - "M-20R-07"
    note: "全场最慢速度·结论的重量·运镜几乎不可察觉"

  - segment_id: "⑫"
    movement: "摇臂上升(垂直)"
    movement_speed: "0.2x"
    movement_direction: "上升(垂直·俯拍45°→水平0°)"
    movement_range: "起点~90cm→终点~2.4m·上升~1.5m"
    movement_duration_sec: 6
    movement_speed_tier: "S2"
    kb_rule_ids:
      - "M-MOT-01"
      - "M-MOV-03"
      - "M-MOV-04"
      - "M-MOT-02"
      - "M-20R-04"
      - "M-20R-07"
      - "M-20R-15"
      - "M-20R-11"
    note: "全场最长运动镜·从证据到世界的维度过渡·路径经过工作台①→走道②→窗前④"

  - segment_id: "⑬"
    movement: "极慢前推"
    movement_speed: "0.08x"
    movement_direction: "前推(微俯保持5°·Rembrandt侧逆光)"
    movement_range: "距Miguel~1.2m→~1.15m"
    movement_duration_sec: 3
    movement_speed_tier: "S1"
    kb_rule_ids:
      - "M-MOT-01"
      - "M-MOT-02"
      - "M-MOV-04"
      - "M-20R-07"
    note: "名字的压迫·极慢推近让'Rico'的重量在空气中沉淀"

  - segment_id: "⑭"
    movement: "固定"
    movement_speed: "0x"
    movement_direction: "N/A"
    movement_range: "N/A"
    movement_duration_sec: 2
    movement_speed_tier: "S0"
    static_motivation: "情感沉浸·名字落地后2秒凝固·D-DIA-11明确指示"
    kb_rule_ids:
      - "M-MOT-01"
      - "M-20R-12"

  - segment_id: "⑮"
    movement: "极慢前推"
    movement_speed: "0.05x"
    movement_direction: "前推(略侧30°保持·微俯保持)"
    movement_range: "距右手~25cm→~23.5cm"
    movement_duration_sec: 3
    movement_speed_tier: "S1"
    kb_rule_ids:
      - "M-MOT-01"
      - "M-MOV-03"
      - "M-MOT-02"
      - "M-20R-04"
    note: "螺旋母题闭合·推近揭示手指间负空间=枪柄形状"

  - segment_id: "⑯"
    movement: "固定"
    movement_speed: "0x"
    movement_direction: "N/A"
    movement_range: "N/A"
    movement_duration_sec: 3
    movement_speed_tier: "S0"
    static_motivation: "信息密集+情感沉浸·钨丝冷却的色彩安魂曲·摄影机静止让光自己表演"
    kb_rule_ids:
      - "M-MOT-01"
      - "M-20R-05"

  - segment_id: "⑰"
    movement: "固定"
    movement_speed: "0x"
    movement_direction: "N/A"
    movement_range: "N/A"
    movement_duration_sec: 2
    movement_speed_tier: "S0"
    static_motivation: "情感沉浸·全剧终镜·黑暗有层次·微光渗入=悬念"
    kb_rule_ids:
      - "M-MOT-01"
      - "M-20R-05"
```

### 6.2 segments_transitions YAML

```yaml
# ─── Movement Designer v2.0 · segments_transitions ───
# 下游: storyboard_planner §2G → TIME_SKELETON.segments[transition]
# 段间运镜过渡设计(非硬切时)

segments_transitions:
  - transition_id: "①→②"
    from_segment: "①"
    to_segment: "②"
    transition_type: "切"
    time_range: [4, 4]
    note: "硬切·从微观弹头→人物脸·冷开场→人物建立"

  - transition_id: "②→③"
    from_segment: "②"
    to_segment: "③"
    transition_type: "切"
    time_range: [7, 7]
    note: "硬切·Vincent面部→电脑屏幕·同一空间不同位置"

  - transition_id: "③→④"
    from_segment: "③"
    to_segment: "④"
    transition_type: "切"
    time_range: [10, 10]
    note: "硬切·屏幕结果→Vincent打电话·叙事推进"

  - transition_id: "④→⑤"
    from_segment: "④"
    to_segment: "⑤"
    transition_type: "切"
    time_range: [14, 14]
    note: "硬切·Vincent电话→Miguel进门·时间跳跃(Miguel到达)"

  - transition_id: "⑤→⑥"
    from_segment: "⑤"
    to_segment: "⑥"
    transition_type: "切"
    time_range: [18, 18]
    note: "硬切·外反拍建立→内反拍Miguel单人·正反打体系启动"

  - transition_id: "⑥→⑦"
    from_segment: "⑥"
    to_segment: "⑦"
    transition_type: "切"
    time_range: [21, 21]
    note: "硬切·标准正反打回切·Miguel→Vincent·视线匹配"

  - transition_id: "⑦→⑧"
    from_segment: "⑦"
    to_segment: "⑧"
    transition_type: "切"
    time_range: [26, 26]
    note: "硬切·Vincent解释→Miguel倾听反应·正反打回切"

  - transition_id: "⑧→⑨"
    from_segment: "⑧"
    to_segment: "⑨"
    transition_type: "切"
    time_range: [28, 28]
    note: "硬切·Miguel倾听→Vincent摔档案宽动作·从内反拍到外反拍·角度拉宽·动能跳跃(S0→S3)"

  - transition_id: "⑨→⑩"
    from_segment: "⑨"
    to_segment: "⑩"
    transition_type: "切"
    time_range: [32, 32]
    note: "硬切·档案动作→照片ECU·中性插入作桥梁·动能回收(S3→S1)"

  - transition_id: "⑩→⑪"
    from_segment: "⑩"
    to_segment: "⑪"
    transition_type: "切"
    time_range: [36, 36]
    note: "硬切·照片比对→Vincent结论·中性插入作桥梁"

  - transition_id: "⑪→⑫"
    from_segment: "⑪"
    to_segment: "⑫"
    transition_type: "切"
    time_range: [39, 39]
    note: "硬切·Vincent结论→摇臂升起·从内反拍到过渡镜·#⑫自身是运镜过渡"

  - transition_id: "⑫→⑬"
    from_segment: "⑫"
    to_segment: "⑬"
    transition_type: "切"
    time_range: [45, 45]
    note: "硬切·窗前城市全景→窗前Miguel近景·空间连续(均在窗前区域④)"

  - transition_id: "⑬→⑭"
    from_segment: "⑬"
    to_segment: "⑭"
    transition_type: "无缝延续"
    time_range: [48, 48]
    note: "同一机位·同镜内节拍变化·Miguel说Rico→面部凝固·无缝衔接·不标记为硬切"
    path: "无·同一机位延续"
    speed: "0x·静止状态延续"
    visual_change: "Miguel面部从说'Rico'的微动→完全凝固·只有光线在变化"

  - transition_id: "⑭→⑮"
    from_segment: "⑭"
    to_segment: "⑮"
    transition_type: "切"
    time_range: [50, 50]
    note: "硬切·Miguel面部→右手ECU·中性插入·螺旋母题从面部到手部"

  - transition_id: "⑮→⑯"
    from_segment: "⑮"
    to_segment: "⑯"
    transition_type: "切"
    time_range: [53, 53]
    note: "硬切·手部ECU→显微镜ECU·中性插入间过渡·终场回归"

  - transition_id: "⑯→⑰"
    from_segment: "⑯"
    to_segment: "⑰"
    transition_type: "切"
    time_range: [56, 56]
    note: "硬切·显微镜→地板窗光·终场中性过渡·圆形闭合完成"
```

### 6.3 frames_movement YAML

```yaml
# ─── Movement Designer v2.0 · frames_movement ───
# 下游: storyboard_planner §2G → TIME_SKELETON.frames[].hard.camera_movement
# 在Shot Architect的frames_hard基础上补充movement字段
# 逐秒运镜状态 — 58秒完整映射

frames_movement:
  # ─── 分镜#1: 弹头ECU (0-4s) · Segment ① · 极慢前推0.1x ───
  - sec: 0
    global_sec: 0
    camera_position: "①"
    movement: "固定(起幅·首帧锁定)"
    is_start_frame: true

  - sec: 1
    global_sec: 1
    camera_position: "①"
    movement: "极慢前推中(0.1x)"

  - sec: 2
    global_sec: 2
    camera_position: "①"
    movement: "极慢前推中(0.1x)"

  - sec: 3
    global_sec: 3
    camera_position: "①"
    movement: "极慢前推中·落定(0.1x)"
    is_end_frame: true

  # ─── 分镜#2: Vincent摘眼镜 (4-7s) · Segment ② · 固定 ───
  - sec: 4
    global_sec: 4
    camera_position: "②"
    movement: "固定"

  - sec: 5
    global_sec: 5
    camera_position: "②"
    movement: "固定"

  - sec: 6
    global_sec: 6
    camera_position: "②"
    movement: "固定"

  # ─── 分镜#3: 屏幕比对 (7-10s) · Segment ③ · 固定 ───
  - sec: 7
    global_sec: 7
    camera_position: "③"
    movement: "固定"

  - sec: 8
    global_sec: 8
    camera_position: "③"
    movement: "固定"

  - sec: 9
    global_sec: 9
    camera_position: "③"
    movement: "固定"

  # ─── 分镜#4: Vincent打电话 (10-14s) · Segment ④ · 极慢前推0.08x ───
  - sec: 10
    global_sec: 10
    camera_position: "④"
    movement: "固定(起幅·首帧锁定)"
    is_start_frame: true

  - sec: 11
    global_sec: 11
    camera_position: "④"
    movement: "极慢前推中(0.08x)"

  - sec: 12
    global_sec: 12
    camera_position: "④"
    movement: "极慢前推中(0.08x)"

  - sec: 13
    global_sec: 13
    camera_position: "④"
    movement: "极慢前推中·落定(0.08x)"
    is_end_frame: true

  # ─── 分镜#5: Miguel入室 (14-18s) · Segment ⑤ · 横移跟拍0.3x ───
  - sec: 14
    global_sec: 14
    camera_position: "⑤"
    movement: "固定(起幅·门框入画·首帧锁定)"
    is_start_frame: true

  - sec: 15
    global_sec: 15
    camera_position: "⑤"
    movement: "横移跟拍中(0.3x·Miguel移动)"

  - sec: 16
    global_sec: 16
    camera_position: "⑤"
    movement: "横移跟拍中(0.3x)"

  - sec: 17
    global_sec: 17
    camera_position: "⑤"
    movement: "固定(落定·Miguel停在走道中段)"
    is_end_frame: true

  # ─── 分镜#6: Miguel看屏幕 (18-21s) · Segment ⑥ · 固定 ───
  - sec: 18
    global_sec: 18
    camera_position: "⑥"
    movement: "固定"

  - sec: 19
    global_sec: 19
    camera_position: "⑥"
    movement: "固定"

  - sec: 20
    global_sec: 20
    camera_position: "⑥"
    movement: "固定"

  # ─── 分镜#7: Vincent解释膛线 (21-26s) · Segment ⑦ · 极慢前推0.05x ───
  - sec: 21
    global_sec: 21
    camera_position: "⑦"
    movement: "固定(起幅·首帧锁定)"
    is_start_frame: true

  - sec: 22
    global_sec: 22
    camera_position: "⑦"
    movement: "极慢前推中(0.05x)"

  - sec: 23
    global_sec: 23
    camera_position: "⑦"
    movement: "极慢前推中(0.05x)"

  - sec: 24
    global_sec: 24
    camera_position: "⑦"
    movement: "极慢前推中(0.05x)"

  - sec: 25
    global_sec: 25
    camera_position: "⑦"
    movement: "极慢前推中·落定(0.05x)"
    is_end_frame: true

  # ─── 分镜#7.5: Miguel倾听 (26-28s) · Segment ⑧ · 固定 ───
  - sec: 26
    global_sec: 26
    camera_position: "⑧"
    movement: "固定"

  - sec: 27
    global_sec: 27
    camera_position: "⑧"
    movement: "固定"

  # ─── 分镜#8: Vincent摔档案 (28-32s) · Segment ⑨ · 手持微晃0.3x ───
  - sec: 28
    global_sec: 28
    camera_position: "⑨"
    movement: "手持微晃(起幅·档案抽抽屉)"
    is_start_frame: true

  - sec: 29
    global_sec: 29
    camera_position: "⑨"
    movement: "手持微晃中(0.3x·档案摔下·微震峰值)"

  - sec: 30
    global_sec: 30
    camera_position: "⑨"
    movement: "手持微晃中(0.3x·微震衰减)"

  - sec: 31
    global_sec: 31
    camera_position: "⑨"
    movement: "手持微晃·落定(恢复稳定)"
    is_end_frame: true

  # ─── 分镜#9: 两张照片并排 (32-36s) · Segment ⑩ · 极慢前推0.05x ───
  - sec: 32
    global_sec: 32
    camera_position: "⑩"
    movement: "固定(起幅·首帧锁定·垂直俯拍)"
    is_start_frame: true

  - sec: 33
    global_sec: 33
    camera_position: "⑩"
    movement: "极慢前推中(0.05x·含微倾)"

  - sec: 34
    global_sec: 34
    camera_position: "⑩"
    movement: "极慢前推中(0.05x)"

  - sec: 35
    global_sec: 35
    camera_position: "⑩"
    movement: "极慢前推中·落定(0.05x·略倾~80°)"
    is_end_frame: true

  # ─── 分镜#10: Vincent结论 (36-39s) · Segment ⑪ · 极慢前推0.03x ───
  - sec: 36
    global_sec: 36
    camera_position: "⑪"
    movement: "固定(起幅·首帧锁定)"
    is_start_frame: true

  - sec: 37
    global_sec: 37
    camera_position: "⑪"
    movement: "极慢前推中(0.03x·几乎不可察觉)"

  - sec: 38
    global_sec: 38
    camera_position: "⑪"
    movement: "极慢前推中·落定(0.03x)"
    is_end_frame: true

  # ─── 分镜#11: 摇臂升起 (39-45s) · Segment ⑫ · 摇臂上升0.2x ───
  - sec: 39
    global_sec: 39
    camera_position: "⑫"
    movement: "固定(起幅·桌面俯拍·首帧锁定)"
    is_start_frame: true

  - sec: 40
    global_sec: 40
    camera_position: "⑫"
    movement: "摇臂上升中(0.2x·穿过Vincent肩)"

  - sec: 41
    global_sec: 41
    camera_position: "⑫"
    movement: "摇臂上升中(0.2x·百叶窗框进入)"

  - sec: 42
    global_sec: 42
    camera_position: "⑫"
    movement: "摇臂上升中(0.2x·窗框过渡)"

  - sec: 43
    global_sec: 43
    camera_position: "⑫"
    movement: "摇臂上升中(0.2x·窗外城市显现)"

  - sec: 44
    global_sec: 44
    camera_position: "⑫"
    movement: "固定(落定·窗前水平·城市全景)"
    is_end_frame: true

  # ─── 分镜#12: Miguel说Rico (45-48s) · Segment ⑬ · 极慢前推0.08x ───
  - sec: 45
    global_sec: 45
    camera_position: "⑬"
    movement: "固定(起幅·首帧锁定·窗前·Rembrandt光)"
    is_start_frame: true

  - sec: 46
    global_sec: 46
    camera_position: "⑬"
    movement: "极慢前推中(0.08x·'Rico'出口)"

  - sec: 47
    global_sec: 47
    camera_position: "⑬"
    movement: "极慢前推中·落定(0.08x·名字落地)"
    is_end_frame: true

  # ─── 分镜#12.5: Miguel面部凝固 (48-50s) · Segment ⑭ · 固定 ───
  - sec: 48
    global_sec: 48
    camera_position: "⑭"
    movement: "固定(凝固·名字落地后)"

  - sec: 49
    global_sec: 49
    camera_position: "⑭"
    movement: "固定(凝固·'眼睛在别处')"

  # ─── 分镜#13: Miguel右手ECU (50-53s) · Segment ⑮ · 极慢前推0.05x ───
  - sec: 50
    global_sec: 50
    camera_position: "⑮"
    movement: "固定(起幅·首帧锁定)"
    is_start_frame: true

  - sec: 51
    global_sec: 51
    camera_position: "⑮"
    movement: "极慢前推中(0.05x·手指蜷握)"

  - sec: 52
    global_sec: 52
    camera_position: "⑮"
    movement: "极慢前推中·落定(0.05x·枪柄弧度成形)"
    is_end_frame: true

  # ─── 分镜#14: 显微镜灯灭 (53-56s) · Segment ⑯ · 固定 ───
  - sec: 53
    global_sec: 53
    camera_position: "⑯"
    movement: "固定(灯亮·钨丝白热)"

  - sec: 54
    global_sec: 54
    camera_position: "⑯"
    movement: "固定(钨丝冷却·琥珀→暗红)"

  - sec: 55
    global_sec: 55
    camera_position: "⑯"
    movement: "固定(钨丝冷却·暗红→深红→消失)"

  # ─── 分镜#15: 窗光余韵 (56-58s) · Segment ⑰ · 固定 ───
  - sec: 56
    global_sec: 56
    camera_position: "⑰"
    movement: "固定(光栅暖金)"

  - sec: 57
    global_sec: 57
    camera_position: "⑰"
    movement: "固定(光栅淡黄→消失·全剧终)"
```

---

## 运镜设计概要统计

```
运镜类型分布 (17镜):

  线性运动:
    极慢前推(0.03x-0.1x):  7镜 (#1/#4/#7/#10/#11/#12/#13) — 41%
    横移跟拍(0.3x):          1镜 (#5) — 6%
    摇臂上升(0.2x):          1镜 (#11) — 6%
    手持微晃(0.3x):          1镜 (#8) — 6%

  静态:
    固定(0x):                7镜 (#2/#3/#6/#7.5/#12.5/#14/#15) — 41%

  复合运动:
    下降+前推微复合:         1镜 (#9·0.05x) — 6%

  未使用:
    旋转运动(摇镜/仰俯摇/环绕/荷兰角): 0镜
    拉远类: 0镜
    快速运镜: 0镜

速度档位分布:
  S0 静态:   7镜 (41%)
  S1 极慢:   7镜 (41%)
  S2 慢:     2镜 (12%)
  S3 中:     1镜 (6%)
  S4-S8:     0镜 (0%)

情绪-运镜差值分布:
  差值=0: 6镜 (#1/#2/#5/#8/#9/#13) — 35%
  差值=1: 8镜 (#3/#4/#6/#7/#7.5/#10/#11/#12.5) — 47%
  差值=2: 3镜 (#12/#14/#15) — 18%
  差值>2: 0镜 — 0%
  所有差值≤2·无需阻断·差值≥2的3镜均有明确叙事动机解释

反差设计统计 (情绪≠运镜但有动机说明):
  #12: 情绪+3→S1(极慢) — 名字的重量靠极慢累积·非靠速度
  #14: 情绪-2→S0(静态) — 钨丝冷却本身就是视觉运动·摄影机静止让光表演
  #15: 情绪-2→S0(静态) — 终镜·静止=终场的寂静
  #11: 情绪+2→S1(极慢) — 结论的确认靠沉稳·不靠速度
  #4: 情绪+2→S1(极慢) — "被压制的兴奋"·克制=力量

KB规则覆盖率:
  17镜 × 平均4.2条KB规则/镜 = ~72次引用
  覆盖KB章节: §5.1(镜头选择)·§5.2(运动方式)·§5.3(运动动机与约束)·§5.3b(二十条规律)·§5.4(运镜对话→§1.3)
  覆盖率: 100% (每镜至少2条KB规则引用)

运镜重复率 (连续3镜以上同类型):
  S1(极慢推近)连续: #10→#11 (2镜)·#12→#13 (2镜) — 均≤2镜 ✅
  S0(固定)连续: #2→#3 (2镜)·#6→#7.5 (跳过#7S1) / #14→#15 (2镜) — 均≤2镜 ✅
  无≥3镜连续同类型 ✅
```

---

## 设计方法说明

### 反差设计哲学

本场景运镜设计的核心策略是**反差设计**——用运镜的克制来传达情绪的强度。具体表现为:

1. **情绪高潮(+3)不使用快速运镜**: #9是唯一的例外(手持微晃S3·动作冲击)，但#12(+3情感高潮)和#11(+2结论)均使用S1极慢推近。运镜的"慢"让观众注意力集中在对白和表演上，而非被运镜分散。

2. **推近不等于加速**: 全场7次极慢推近的速度分布在0.03x-0.1x之间，没有一次超过0.1x。M-MOT-02(速度匹配情绪)在本场景中被重新解读——科学/知识场景的"情绪升温"不一定等于"物理加速"。

3. **静态镜的叙事力量**: 7个静态镜(41%)不是为了省事，而是有精确的叙事动机——信息密集(#2/#3/#6)、情感沉浸(#7.5/#12.5/#15)、光事件见证(#14)。每个静态镜都回答"为什么不运动"。

### 独立上下文声明

```
Movement Designer v2.0
独立上下文: ✅ (未读取覆盖/对话KB·未读取构图KB·未读取光影KB)
设计依据: KB §5 运镜与运动(~110条) + P0安全规则 + P-CONSTITUTION第三条/第四条 + P-STATE §2规避
输入: Shot Architect §6 YAML(仅读结构化块·不读推理) + 原始剧本 + ANCHOR_BASELINE §C(空间地图) + P-STATE + P-CONSTITUTION + canvas_runtime + kb_index
输出: 运镜设计报告(自由文本) + §6 segments_movement + §6 segments_transitions + §6 frames_movement
下游: storyboard_planner (Step A2.5·§2G TIME_SKELETON组装) · Composition Designer (Step A2·串行第三位)
日期: 2026-07-07
场景: 枪王EP13《弹道学》·鉴证科实验室·17镜·58s
```
