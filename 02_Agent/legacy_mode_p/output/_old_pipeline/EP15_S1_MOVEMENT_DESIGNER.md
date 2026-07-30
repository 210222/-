# MOVEMENT DESIGNER v2.0 -- 运镜设计报告

> 场景: EP15《会面》· Rico工作室（傍晚→夜）
> 日期: 2026-07-07
> 上游: ANCHOR_BASELINE §B (运镜策略) + SHOT ARCHITECT §6 (机位YAML)
> 下游消费: Composition Designer → Storyboard Planner → SekoTalk
> 设计范围: 仅运镜类型·速度·方向·起止状态（不设计机位·构图·光影）

---

## 运镜策略总纲

```
主导风格: 静态固定 ~77% (17/22镜) —— 对峙的视觉化
次要风格: 极慢推近 ~23% (5/22镜) —— 对峙升温·0.03x-0.04x
特殊:     微距零运镜 (ECU细节·全部静态)
禁止:     快速运镜·摇摄(Pan)·大幅推拉·环绕(Orbit)·升降(Crane)

空间约束:
  · 空间深度~5m → 运镜速度≤1.0x (M-MOT-04)
  · 门口区域: 固定/缓推·禁快速横移 (M-MOT-03)
  · 工作台=不可穿越的物理障碍·运镜不跨工作台
  · 吊灯光锥=不可进入路径(避免镜头阴影投射到台面)
  · 小房间<10m²: 固定/手持/缓推·禁横移/升降 (M-MOT-03)

运镜速度与空间深度对照:
  · SHOT 03/18: 空间深度~4m → 0.03x ✓ (M-MOT-04: 2-5m→≤1.0x)
  · SHOT 10:   空间深度~3m → 0.04x ✓ 
  · SHOT 13/15: 空间深度~1.5m → 0.03x ✓ (M-MOT-04: <2m→≤0.5x·0.03x远低于上限)
```

---

# 第一部分：逐镜运镜设计

---

## SHOT 01 -- ECU · 锉刀开场

```
运镜类型: 静态固定 (Static Fixed)
速度:     0x (零运镜)
方向:     N/A
起幅:     静态·锉刀在枪管上·起始位（首帧=静态完成态 M-MOT-05）
落幅:     静态·同起幅位置（全程无位移）
运动段:   无

戏剧动机: 开场书挡(Opening Bookend)。零运镜让观众的全部注意力集中于——
          (1) 锉刀金属摩擦声(场景听觉基频)
          (2) 金属质感·碎屑·木纹(视觉质感)
          (3) 规律的往复节奏(建立"手艺人"母题)
          运镜在此没有叙事功能——锉刀声承担全部开场重量。

KB规则:
  M-MOT-01(P0):  运镜必须有动机——此处动机=静·让声音和质感叙事 ✓
  M-20R-07(P0):  静→动→静——全程静段·无动段 ✓
  M-MOT-05(P0):  首帧=静态清晰的冻结帧 ✓
  M-20R-12(P0):  完全静止·不犹豫 ✓
  M-20R-15(P0):  起幅=落幅=同一静态构图·完整平衡 ✓

空间约束: 微距·工作台上方·光锥范围内·无空间位移需求 ✓
过渡:     SHOT 01→02 = 硬切(Hard Cut)
         从ECU微距到WS全景·空间跳跃→被SHOT 02建立镜头解析
```

---

## SHOT 02 -- WS · 工作室建立镜头

```
运镜类型: 静态固定 (Static Fixed)
速度:     0x
方向:     N/A
起幅:     静态·Rico背对门口坐姿·工作台·洞洞板·门闭合·吊灯光锥
落幅:     静态·同起幅位置
运动段:   无

戏剧动机: 全景空间建立。A-GEN-02(P0): 任何动作场景第一镜必须是空间建立镜头。
          运镜=零——空间建立需要观众"扫描"画面信息：
          门的位置·工作台的纵深·洞洞板的工具·保险柜的暗角·吊灯光锥的范围。
          摄影机运动将干扰此空间认知过程。

KB规则:
  A-GEN-02(P0):  空间建立优先·第一镜=空间建立 ✓
  M-MOT-01(P0):  动机=空间信息传递·静态最有效 ✓
  M-MOT-05(P0):  首帧=静态完成态 ✓
  M-20R-07(P0):  全程静段 ✓
  M-20R-15(P0):  起幅落幅构图完整平衡 ✓

空间约束: 机位[1.5, 1.5, 1.6]·全景·不穿墙不悬空 ✓
过渡:     SHOT 02→03 = 硬切
         WS建立→MS门·景别收紧预告事件发生
```

---

## SHOT 03 -- MS · 门被推开·影子入侵

```
运镜类型: 极慢推近 (Slow Push-in · Dolly Forward)
速度:     0.03x
方向:     沿镜头轴线向前·朝向门口/Miguel方向
          位移向量: dir(+0.50mX, -0.33mY, 0mZ) · 约2.5s内位移~8cm
起幅:     静态·门闭合状态（3A 首帧锁定 M-MOT-05）
触发点:   门开始被推开 — 冷白光涌入 — 摄影机开始极慢推近
落幅:     静态·门完全打开·Miguel剪影确立·影子投在Rico背上（3B）
运动段:   3A(静) → [推近0.03x] → 3B(静)

三段式验证 (M-20R-07):
  静段1: 3A — 门闭合·静态冻结帧 ✓
  动段:  3A→3B — 推近0.03x ✓
  静段2: 3B — 门全开·落幅锁定 ✓

戏剧动机: "制度入侵私人领域"的视觉化。
          门被推开=冷白光(4000K·制度)涌入暖黄空间(2800K·Rico的私人领域)。
          Miguel的影子先于其人投在Rico背上=入侵的预兆。
          摄影机被此"入侵事件"吸引·不可察觉地向前探——
          观众和摄影机一起被拉向门口·见证两个世界的碰撞。
          
          M-20R-13: 门先动(Miguel推门)→摄影机跟动 ✓
          M-20R-14: 摄影机走最简单的路线——直线推近 ✓

KB规则:
  M-MOT-01(P0):  动机=制度入侵私人领域·摄影机被事件吸引 ✓
  M-20R-07(P0):  静→动→静三段式 ✓
  M-MOT-05(P0):  首帧=静态完成态 ✓
  M-MOT-03(P0):  门口区域·缓推(0.03x极慢·安全) ✓
  M-MOT-04(P0):  空间深度~4m·0.03x≤1.0x ✓
  M-20R-13(P1):  门/人先动→摄影机跟动 ✓
  M-20R-14(P1):  摄影机走最简单的直线 ✓
  M-20R-15(P0):  起幅落幅构图完整平衡 ✓

空间约束: 
  机位[2.0, 2.0, 1.6]·推近不进入门开启弧线(~1m半径) ✓
  推近不进入Miguel与门之间的影子投射路径 ✓
  位移量~8cm·远小于空间余量 ✓

过渡:     SHOT 03→04 = 硬切
         MS门→CU Rico面部·从"入侵"的外部事件切回Rico的"无视"反应
```

---

## SHOT 04 -- CU · Rico侧脸·不回头对话

```
运镜类型: 静态固定 (Static Fixed)
速度:     0x
方向:     N/A
起幅:     静态·Rico 3/4侧脸·视线向下(看手头工作)·锉刀声没停
落幅:     静态·同起幅（Rico全程未转身·未改变姿态）
运动段:   无

戏剧动机: Rico"不回头"=不承认Miguel的存在。摄影机与Rico的姿态同步——
          既然Rico选择无视门口的人，摄影机也不向门口移动。
          静态=Rico对自己空间的控制感·"这是我的地盘·我不用转身"。
          
          锉刀声持续·Rico说话但不停下手头工作——
          画面内的运动(手部锉刀往复)已经足够·摄影机运动将冗余。

KB规则:
  M-MOT-01(P0):  动机=与Rico的无视姿态同步·静止=控制 ✓
  M-20R-07(P0):  全程静段 ✓
  M-20R-12(P0):  完全静止·不犹豫 ✓
  M-20R-15(P0):  起幅落幅构图完整平衡 ✓
  D-DUO-08(P2):  眼平高度·平等视角——Rico为空间主人 ✓

空间约束: 机位[1.5, 3.5, 1.2]·CU·距Rico~1.2m·静态无位移 ✓
过渡:     SHOT 04→05 = 硬切
         CU Rico→MS Miguel·从无视者切到被无视者·视角倒转
```

---

## SHOT 05 -- MS · Miguel关门·靠门框·扫视

```
运镜类型: 静态固定 (Static Fixed)
速度:     0x
方向:     N/A
起幅:     静态·Miguel关门·靠门框（5A）
落幅:     静态·Miguel扫视结束·视线停在保险柜方向（5B）
运动段:   无

戏剧动机: Miguel的扫视动作(左→中→右:改装枪→零件→保险柜)是画面内的主体运动。
          摄影机静止——让观众跟随Miguel的视线路径"扫描"空间——
          就像SHOT 02中观众扫描全景一样。
          
          如果摄影机跟随Miguel的视线摇摄(Pan)，将打破"观众自主探索"的悬念感。
          M-PAN-01要求摇摄方向需有戏剧动机——此处无。
          
          门口区域: 固定是最优选择 (M-MOT-03)。

KB规则:
  M-MOT-01(P0):  动机=让观众自主跟随扫视路径·静态优于跟拍 ✓
  M-MOT-03(P0):  门口区域·固定 ✓
  M-20R-07(P0):  全程静段 ✓
  M-20R-15(P0):  起幅落幅构图完整平衡——门框构图始终稳定 ✓
  M-20R-05(P1):  直接切换比移动镜头更经济——扫视的三要素通过后续SHOT 06+07的POV插入完成 ✓

空间约束: 机位[2.5, 1.5, 1.7]·门口区域·固定·不进入门框平面 ✓
过渡:     SHOT 05→06 = 硬切
         MS Miguel→INSERT改装枪POV·扫视第一站·主观视角切换
```

---

## SHOT 06 -- INSERT · Miguel主观视角: 改装枪列阵

```
运镜类型: 静态固定 (Static Fixed)
速度:     0x
方向:     N/A
起幅:     静态·左墙改装枪列阵
落幅:     静态·同起幅
运动段:   无

戏剧动机: POV主观视角——摄影机=Miguel的眼睛。
          人眼不会"推轨"前进——运镜将打破POV幻觉。
          静态=让观众以Miguel的视角凝视这面墙·像刑警一样审视证据。
          
          改装枪列阵本身已携带足够信息量(手枪·步枪·消音器·瞄准镜——
          这是一个真正的枪械作坊)·运镜只会分散对证据的注意力。

KB规则:
  M-MOT-01(P0):  动机=POV主观视角·人眼不推轨·静止维护POV幻觉 ✓
  M-20R-07(P0):  全程静段 ✓
  M-20R-15(P0):  构图完整平衡 ✓

空间约束: 机位[1.5, 0.5, 1.7]·距左墙~0.5-0.8m·静态 ✓
过渡:     SHOT 06→07 = 硬切
         从左墙改装枪→右角保险柜·扫视第二站·POV连续切换
```

---

## SHOT 07 -- INSERT · Miguel主观视角: 保险柜·黑布

```
运镜类型: 静态固定 (Static Fixed)
速度:     0x
方向:     N/A
起幅:     静态·灰色保险柜·柜门留缝5-8cm·黑布包裹
落幅:     静态·同起幅
运动段:   无

戏剧动机: POV主观视角+核心悬念植入。
          保险柜留缝+黑布包裹物=全场景未解之谜——"那里面是什么？"
          摄影机静止=强迫观众和Miguel一起凝视那条缝隙·试图看穿黑布。
          
          A-SUS-02(P1): 未知之惧·不拍威胁来源·黑布=观众的想象。
          摄影机运动将"提示"观众应该感到什么·破坏悬念的开放性。
          静止——让观众自己决定该有多不安。

KB规则:
  M-MOT-01(P0):  动机=悬念凝视·静止=强迫观众面对未知 ✓
  M-20R-07(P0):  全程静段 ✓
  A-SUS-02(P1):  未知之惧·不拍威胁来源·观众想象填补黑布内容 ✓
  M-20R-15(P0):  构图完整平衡 ✓

空间约束: 机位[4.5, 3.0, 1.2]·保险柜前·不穿入保险柜·不进入洗手池杂物区 ✓
过渡:     SHOT 07→08 = 硬切
         从POV保险柜→CU Miguel面部·从"被凝视的物"回到"凝视者"
         观众和Miguel一起从保险柜缝隙收回视线
```

---

## SHOT 08 -- CU · Miguel "你看上去不惊讶"

```
运镜类型: 静态固定 (Static Fixed)
速度:     0x
方向:     N/A
起幅:     静态·Miguel面部近景·半明半暗·视线从保险柜方向转回锁定Rico
落幅:     静态·对白结束·视线锁定保持
运动段:   无

戏剧动机: Miguel首句对白·审问开启。
          静态=审问者的控制感——Miguel不需要靠运镜制造压力·他的话就是压力。
          "你看上去不惊讶"——这句本身就是对Rico的心理分析。
          
          面部半明半暗(靠近室内侧=暖黄·靠近门侧=阴影)=Miguel站在分界线上。
          摄影机不动——观众被锁在Miguel的审视中。

KB规则:
  M-MOT-01(P0):  动机=审问语气·静态=控制感 ✓
  M-MOT-03(P0):  门口区域·固定 ✓
  M-20R-07(P0):  全程静段 ✓
  M-20R-15(P0):  起幅落幅构图完整平衡 ✓

空间约束: 机位[2.5, 1.2, 1.7]·距Miguel~1.2m·不进入门框平面·静态 ✓
过渡:     SHOT 08→09 = 硬切
         CU Miguel→CU Rico·审问→回应·视线配对(E-MTC-04):Miguel看右→Rico看左
```

---

## SHOT 09 -- CU · Rico放下锉刀·转身

```
运镜类型: 静态固定 (Static Fixed)
速度:     0x
方向:     N/A
起幅:     静态·Rico放下锉刀·手在画面中（9A）
落幅:     静态·Rico转身完成·面对Miguel方向（9B）
运动段:   无（画面内有主体运动: 放下锉刀+转身·但摄影机不动）

戏剧动机: 放下锉刀+转身=全场景第一次关键转折——Rico从"无视"切换到"面对"。
          这个动作本身就是画面内最重要的运动事件。
          
          摄影机静止=让观众完整接收这个转折的每一个细节:
          · 锉刀搁在枪管上·刀尖对准窗口方向(空间线索预埋)
          · 转身过程中面部光线从侧面→正面(始终在光锥内)
          · 眼神首次抬起与Miguel对视
          
          M-20R-13: 人物先动(Rico转身)→摄影机跟动——
          但此处摄影机选择不跟动·让转身动作在固定画面中自行展开。
          "跟动"的前提是人物需要摄影机跟随才能保持在画面中——
          Rico在CU画面内转身·无需摄影机调整。

KB规则:
  M-MOT-01(P0):  动机=Rico的转身动作即运动事件·摄影机静止=不干扰 ✓
  M-20R-07(P0):  全程静段(画面内运动≠摄影机运动) ✓
  M-20R-15(P0):  起幅落幅构图——9B落幅中Rico面向镜头方向·构图平衡 ✓
  M-20R-13(P1):  人物先动·摄影机在需要跟动时才跟动——此处不需要 ✓

空间约束: 机位[1.5, 3.2, 1.2]·不阻挡Rico转身空间(椅子旋转半径~0.5m) ✓
过渡:     SHOT 09→10 = 硬切
         CU Rico→MS双人·从单人近景拉开到双人全景——
         视觉扩张=两人关系从"无视→面对"的空间化
```

---

## SHOT 10 -- MS · 双人镜头·三阶段（面对面→迈步→站起）

```
运镜类型: 静→极慢推近→静 (Static → Slow Push-in → Static)
速度:     0.04x (推近阶段)
方向:     沿镜头轴线向前·向两人之间的空间·压缩画面深度
          位移向量: dir(+0.73mX, 0mY, 0mZ)大致·约3s内位移~15cm
起幅:     静态·Rico坐姿画右·Miguel站姿画左·距离4m·工作台隔开（10A·首帧锁定）
触发点:   Miguel开始迈两步——摄影机开始极慢推近
落幅:     静态·Rico站起·两人身高齐平·隔工作台对峙（10C）
运动段:   10A(静) → [推近0.04x] → 10B(静·2m) → [静态保持] → 10C(静·齐平)

详细阶段分解:
  阶段A (10A):        静态·4m面对面·首帧锁定·工作台横亘画面底部
  阶段A→B (10A→10B): 极慢推近0.04x·Miguel迈两步·距离4m→2m
                      摄影机同步推近·M-20R-13: Miguel先动→摄影机跟动
                      推近=物理距离压缩=对峙升温的视觉化(D-DIA-01: 推近对话)
  阶段B (10B):        静态·落幅锁定·2m·工作台仍隔在两人之间
  阶段B→C (10B→10C): 静态保持·Rico站起——摄影机不动
                      Rico的站起动作是画面内主体运动·从坐姿到站姿·身高齐平
                      摄影机不动=让Rico的"生长"在固定画面中产生视觉冲击
                      (M-CRN-01: 不因人物高度变化而升降——动作适应镜头·非镜头适应动作)
  阶段C (10C):        静态·最终落幅·两人站姿·身高齐平·隔工作台对峙

三段式(M-20R-07):
  静段1: 10A — 4m面对面·静态冻结 ✓
  动段:  10A→10B — 推近0.04x ✓
  静段2: 10B — 2m·落幅锁定 ✓
  (10B→10C: 静段延伸·摄影机不参与Rico站起动作)

戏剧动机: 三阶段动作覆盖·权力动态变化的视觉化。
          · 推近0.04x沿最简路线(直线·M-20R-14)——Miguel在动·摄影机跟随
          · Rico站起时摄影机停止——因为站起动作的戏剧力量来自"从低位到高位"的对比
            如果摄影机此时升降·将消解这个对比(M-CRN-01)
          · 最终落幅:两人站立对峙·权力拉平——视觉化为画面内等高的两人

KB规则:
  M-MOT-01(P0):  动机=对峙升温·推近=心理距离压缩 ✓
  M-20R-07(P0):  静→动→静三段式 ✓
  M-MOT-05(P0):  首帧=静态完成态(10A) ✓
  M-MOT-04(P0):  深度~3m·0.04x≤1.0x ✓
  M-MOT-03(P0):  距门口>2m·非门区限制范围 ✓
  D-DIA-01(P1):  推近对话·对峙升温·0.04x极慢推近 ✓
  M-20R-13(P1):  Miguel先迈步→摄影机跟动 ✓
  M-20R-14(P1):  摄影机走最简单路线——直线推近 ✓
  M-CRN-01(P1):  Rico站起→摄影机不升降·动作适应镜头 ✓
  M-20R-15(P0):  起幅落幅构图完整平衡 ✓
  D-DIA-03(P1):  不同高度·坐vs站→站vs站·权力拉平 ✓
  D-DIA-20(P1):  工作台=障碍物·物理障碍=权力边界·镜头不穿越 ✓

空间约束: 
  机位[1.5, 2.0, 1.6]·推近方向沿镜头轴线·不穿越工作台 ✓
  不进入吊灯光锥路径 ✓
  位移量~15cm·安全余量充足 ✓

过渡:     SHOT 10→11 = 硬切
         MS双人→OTS Miguel肩·从建立镜头切到外反拍对话覆盖
```

---

## SHOT 11 -- OTS · 过Miguel肩拍Rico（外反拍A）

```
运镜类型: 静态固定 (Static Fixed)
速度:     0x
方向:     N/A
起幅:     静态·Miguel右肩前景(虚)·Rico正面后景(焦)
落幅:     静态·同起幅
运动段:   无

戏剧动机: 外反拍对话覆盖·Rico对白主镜。
          三角形底边机位(D-TRI-05)·标准对话模板。
          OTS机位中Rico为"开放形体"=对话主导方。
          静态=标准对话段的处置·运镜在此无增量叙事价值。
          
          M-20R-05: 直接切换比移动镜头更经济——
          OTS A→OTS B→CU的切换节奏已承载对话张力。

KB规则:
  M-MOT-01(P0):  动机=对话覆盖·静态=标准处置 ✓
  M-20R-07(P0):  全程静段 ✓
  M-20R-15(P0):  起幅落幅构图完整平衡 ✓
  M-20R-05(P1):  直接切换比移动镜头更经济 ✓

空间约束: 机位[3.2, 1.0, 1.7]·距Miguel~0.8m·不穿过Miguel身体·静态 ✓
过渡:     SHOT 11→12 = 硬切
         OTS A→OTS B·外反拍配对切换·视线方向反转
```

---

## SHOT 12 -- OTS · 过Rico肩拍Miguel（外反拍B）

```
运镜类型: 静态固定 (Static Fixed)
速度:     0x
方向:     N/A
起幅:     静态·Rico右肩前景(虚)·Miguel正面后景(焦)
落幅:     静态·同起幅
运动段:   无

戏剧动机: 外反拍对话覆盖·Miguel对白主镜。
          与SHOT 11配对构成三角形底边双机位(D-TRI-05)。
          静态=对话段标准处置。

KB规则:
  M-MOT-01(P0):  动机=对话覆盖·静态 ✓
  M-20R-07(P0):  全程静段 ✓
  M-20R-15(P0):  起幅落幅构图完整平衡 ✓

空间约束: 机位[1.8, 3.2, 1.6]·距Rico~0.8m·不穿过Rico身体·不进入光锥区 ✓
过渡:     SHOT 12→13 = 硬切
         OTS B→CU Rico内反拍·景别收紧——对话升温信号
         从外反拍(两人都在画面)到内反拍(单人CU)=心理聚焦收窄
```

---

## SHOT 13 -- CU · Rico "你有指控吗？"

```
运镜类型: 静→极慢推近→静 (Static → Slow Push-in → Static)
速度:     0.03x
方向:     沿镜头轴线向前·向Rico面部
          位移向量: dir(+0.82mX, 0mY, 0mZ)大致·约2s内位移~6cm
起幅:     静态·Rico近景·站姿·暖黄光·眼神锐利锁定（13A·首帧锁定）
触发点:   Rico开始说"你有指控吗？" → 摄影机开始极慢推近
落幅:     静态·对白结束·面部锁定（对白结束后·落幅静态保持）
运动段:   13A(静) → [推近0.03x·"你有指控吗？"] → 13A'(静·落幅)

三段式(M-20R-07):
  静段1: 13A — 首帧锁定 ✓
  动段:  对白期间·推近0.03x ✓
  静段2: 对白结束·落幅锁定 ✓

戏剧动机: Rico从防守转为进攻。"你有指控吗？"是Rico对刑警的直接挑战——
          潜台词="你没有证据·你什么都不能做"。
          
          极慢推近(0.03x)=Rico向Miguel施加心理压力的视觉化。
          摄影机被Rico的"进攻性"吸引·不可察觉地逼近他的面部——
          观众被拉进Rico的质询·和Miguel一起承受这个问题的重量。
          
          D-DIA-01(P1): 对峙升温·极慢推近 ✓
          M-MOT-02: 愤怒/紧张情绪→变速——Rico的平静表面下暗流=极慢但确实在逼近

KB规则:
  M-MOT-01(P0):  动机=心理进攻·推近=Rico施压 ✓
  M-20R-07(P0):  静→动→静三段式 ✓
  M-MOT-05(P0):  首帧=静态完成态 ✓
  M-MOT-04(P0):  空间深度~1.5m(<2m)·0.03x≤0.5x ✓ (远低于上限)
  D-DIA-01(P1):  对峙升温·极慢推近0.03x ✓
  M-20R-14(P1):  摄影机走最简单路线——直线 ✓
  M-20R-15(P0):  起幅落幅构图完整平衡 ✓
  M-MOT-02(P1):  速度匹配情绪·紧张=极慢但确定 ✓

空间约束: 机位[1.8, 2.8, 1.7]·距Rico~1.2m·光锥范围内·位移~6cm ✓
过渡:     SHOT 13→14 = 硬切
         CU Rico(推近结束·落幅锁定)→CU Miguel
         从进攻者切到被质询者——Miguel的回应
```

---

## SHOT 14 -- CU · Miguel "没有" + 两秒沉默

```
运镜类型: 静态固定 (Static Fixed) —— 绝对静止
速度:     0x
方向:     N/A
起幅:     静态·Miguel近景·沉默起始（14A）
落幅:     静态·"没有"·沉默2秒后（14B）
运动段:   无——全程绝对静止·包括两秒沉默期间

戏剧动机: 全场景最重要的静态时刻之一。
          D-DIA-11(P2): 肢体语言对抗——"摄影机完全不动·凝固的空气比任何运镜都有力"。
          
          Miguel的"没有"只有两个字·但它前后有两秒沉默。
          这两秒=观众预期"Miguel会指控他"的悬置——
          摄影机移动哪怕一毫米都会释放这个张力。
          
          A-SUS-03(P1): 紧张期待·固定镜头·不切不走·强迫观众等待。
          观众和Rico一起等待Miguel的下一句话——然后他说"没有"。
          反高潮(anti-climax)=比指控更有力的叙事选择。

KB规则:
  M-MOT-01(P0):  动机=沉默比语言有力·静止=不释放张力 ✓
  D-DIA-11(P2):  摄影机完全不动·凝固的空气 ✓
  A-SUS-03(P1):  紧张期待·固定·不切不走·强迫观众等待两秒 ✓
  M-20R-07(P0):  全程静段 ✓
  M-20R-15(P0):  起幅落幅构图完整平衡 ✓
  M-20R-12(P0):  完全静止·不犹豫 ✓

空间约束: 机位[2.8, 1.5, 1.7]·距Miguel~1.2m·静态 ✓
过渡:     SHOT 14→15 = 硬切
         CU Miguel(沉默结束)→CU Rico(反击)
         Miguel的"没有"打开了Rico的下一击
```

---

## SHOT 15 -- CU · Rico "那你来是——朋友的身份？"

```
运镜类型: 静→极慢推近→静 (Static → Slow Push-in → Static)
速度:     0.03x
方向:     沿镜头轴线向前·向Rico面部（同SHOT 13轴线）
          位移向量: 同SHOT 13方向·约2.5s内位移~7cm
起幅:     静态·Rico近景·嘴角微动(上一句残留·即将说话)（15A·首帧锁定）
触发点:   Rico说出"那你来是——" → 摄影机开始极慢推近
落幅:     静态·"朋友的身份？"结束·嘴角微动→收紧过渡（15B·落幅锁定）
运动段:   15A(静) → [推近0.03x] → 15B(静)

三段式(M-20R-07):
  静段1: 15A — 首帧锁定 ✓
  动段:  对白期间·推近0.03x ✓
  静段2: 15B — 落幅锁定 ✓

戏剧动机: Rico反客为主——用"朋友"一词将Miguel从制度身份中剥离。
          "那你来是——"后短暂停顿(故意留白)→"朋友的身份？"语气不升反降。
          
          极慢推近(0.03x)=Rico掌握对话主动权·向Miguel逼近。
          与SHOT 13形成运镜呼应——两次推近=两次心理进攻——
          SHOT 13=直接挑战("你有指控吗？")·SHOT 15=迂回包抄("朋友的身份？")。
          
          落幅锁定在"嘴角微动→收紧过渡"——为下面三连ECU序列(16a/b/c)做铺垫。

KB规则:
  M-MOT-01(P0):  动机=反客为主·推近=主动权转移 ✓
  M-20R-07(P0):  静→动→静三段式 ✓
  M-MOT-05(P0):  首帧=静态完成态 ✓
  M-MOT-04(P0):  空间深度~1.5m·0.03x≤0.5x ✓
  D-DIA-01(P1):  对峙升温·极慢推近 ✓
  M-20R-14(P1):  摄影机走最简单路线——直线 ✓
  M-20R-15(P0):  起幅落幅构图完整平衡 ✓

空间约束: 机位[1.8, 2.8, 1.7]·同SHOT 13·位移~7cm ✓
过渡:     SHOT 15→16a = 硬切
         CU Rico(推近落幅)→ECU Miguel右手
         从面部到手指·从宏观到微观·景别跳跃=叙事炸弹即将引爆
```

---

## SHOT 16a -- ECU · Miguel右手·手指后移1cm

```
运镜类型: 静态固定 (Static Fixed) —— 绝对静止
速度:     0x
方向:     N/A
起幅:     静态·ECU右手·手指初始自然垂放位置（16a_A）
落幅:     静态·ECU右手·手指后移1cm完成·靠近配枪皮套边缘（16a_B）
运动段:   无——画面内手指1cm位移是主体运动·摄影机绝对静止

戏剧动机: 全场景叙事高潮触发器。
          Miguel的手指只移动了1cm——画面中约2-3mm的位移。
          任何运镜——哪怕最轻微的呼吸晃动——都会淹没这个微动作。
          
          摄影机绝对静止=让1cm成为画面的全部事件。
          观众必须和Rico一样"捕捉"这个微动作——如果观众错过了·就错过了。
          摄影机不帮助观众——静止=观众的注意力考验。
          
          这与SHOT 14的两秒沉默形成呼应:
          SHOT 14=时间维度的沉默(两秒)·SHOT 16a=空间维度的静止(1cm)。

KB规则:
  M-MOT-01(P0):  动机=1cm位移是全部事件·运镜=破坏 ✓
  M-20R-07(P0):  全程静段 ✓
  M-20R-12(P0):  完全静止 ✓
  A-SUS-09(P1):  恐惧延时释放·细微变化(1cm)打破安全感 ✓
  M-20R-15(P0):  起幅落幅构图——落幅中手指位移完成·构图仍完整 ✓

空间约束: ECU·距右手~40cm·微距·静态无位移 ✓
过渡:     SHOT 16a→16b = 硬切
         ECU手指→ECU眼睛·三连切第二镜
         因果链:手指动→眼睛捕获——用剪切速度模拟Rico的扫视速度
```

---

## SHOT 16b -- ECU · Rico眼睛·视线下扫一帧

```
运镜类型: 静态固定 (Static Fixed) —— 绝对静止
速度:     0x
方向:     N/A
起幅:     静态·Rico双眼·平视Miguel（16b_A）
落幅:     静态·Rico双眼·下扫一帧后回到平视（16b_B）
运动段:   无——画面内1/24秒的视线扫动是主体运动·摄影机绝对静止

戏剧动机: 眼睛的扫动仅持续一帧(1/24秒)。
          摄影机绝对静止=观众必须"捕捉"这个瞬间——
          和Rico捕捉Miguel手指1cm位移一样·观众必须捕捉Rico的1/24秒扫视。
          
          如果摄影机有任何运动·1/24秒的微动作将完全不可见。
          零运镜=维护微动作的可读性。
          
          ANCHOR_BASELINE Rico锚点A2: "不动声色但什么都在看"——
          摄影机静止=与Rico的"不动声色"同步·但观众通过画面看到了他"在看"。

KB规则:
  M-MOT-01(P0):  动机=1/24秒微动作·零运镜=可读性 ✓
  M-20R-07(P0):  全程静段 ✓
  A-SUS-09(P1):  细微变化打破安全感·眼睛扫一帧=叙事炸弹 ✓
  M-20R-12(P0):  完全静止 ✓

空间约束: ECU·距眼睛~50cm·静态 ✓
过渡:     SHOT 16b→16c = 硬切
         ECU眼睛→ECU嘴角·三连切第三镜
        从"看到"(眼睛)→"反应"(嘴角)·反应链收束
```

---

## SHOT 16c -- ECU · Rico嘴角·收住

```
运镜类型: 静态固定 (Static Fixed) —— 绝对静止
速度:     0x
方向:     N/A
起幅:     静态·ECU嘴角·微松弛(上一句"朋友的身份？"残留)（16c_A）
落幅:     静态·ECU嘴角·收紧·绷直·完全闭合（16c_B）
运动段:   无——画面内嘴角收紧是主体运动·摄影机绝对静止

戏剧动机: 三连切序列收束。嘴角收紧=情绪内化=危险升级。
          从"对话"(15)到"微动作捕获"(16a→16b)→"情绪内化"(16c)——
          完整叙事弧线在4个静止镜头中完成。
          
          嘴角收紧是Rico情绪的唯一外泄口(ANCHOR_BASELINE锚点A3)——
          一旦这个口也闭合了·观众知道Rico已经把一切收进心里。
          "他知道了"——不需要对白·不需要运镜。
          
          A-SUS-03(P1): 紧张期待——最后一个ECU锁在嘴角·强迫观众消化这个信息。

KB规则:
  M-MOT-01(P0):  动机=情绪内化·静止=让观众消化 ✓
  M-20R-07(P0):  全程静段 ✓
  A-SUS-09(P1):  延时释放完结点·完整弧线收束 ✓
  A-SUS-03(P1):  紧张期待·锁在嘴角·强迫观众接收信息 ✓
  M-20R-12(P0):  完全静止 ✓
  M-20R-15(P0):  起幅落幅构图完整平衡 ✓

空间约束: ECU·距嘴角~40cm·静态 ✓
过渡:     SHOT 16c→17 = 硬切
         ECU嘴角→CU Miguel面部
         从Rico的情绪内化切回Miguel——Miguel不知道Rico已经"知道了"
         观众比Miguel多知道一个信息=戏剧反讽
```

---

## SHOT 17 -- CU · Miguel 缓慢对白

```
运镜类型: 静态固定 (Static Fixed)
速度:     0x
方向:     N/A
起幅:     静态·Miguel近景·缓慢对白开始（17A）
落幅:     静态·"不想看你自我毁灭"结束（17A持续）
运动段:   无

戏剧动机: Miguel声音缓慢·像在选择每个字。
          D-DIA-11(P2): "摄影机完全不动"——对白节奏由演员控制而非摄影机。
          
          Miguel的缓慢=不确定·在选字=在犹豫。
          摄影机静止=让Miguel的犹豫暴露在观众面前——
          如果此时摄影机推近·将"催促"Miguel·破坏选字的节奏。
          
          "不想看你自我毁灭"=揭示两人过往关系深度——
          不是纯粹的刑警vs嫌犯·有私人历史。
          静态镜头让这句话的重量自行落地。

KB规则:
  M-MOT-01(P0):  动机=缓慢对白·静止=节奏由演员控制 ✓
  D-DIA-11(P2):  摄影机完全不动 ✓
  M-20R-07(P0):  全程静段 ✓
  M-20R-15(P0):  起幅落幅构图完整平衡 ✓

空间约束: 机位[2.8, 1.5, 1.7]·距Miguel~1.2m·静态 ✓
过渡:     SHOT 17→18 = 硬切
         CU Miguel→WS双人全景
         从单人近景到双人全景·视觉扩张=沉默的空间化
         广角=两人之间的整个房间进入画面·沉默填满空间
```

---

## SHOT 18 -- WS · 双人全景·对视·天空变色·Rico擦手

```
运镜类型: 静→极慢推近→静 (Static → Slow Push-in → Static)
          推近仅在对视/天空变色阶段·擦手阶段恢复绝对静止
速度:     0.03x (推近阶段)
方向:     沿镜头轴线向前·向两人对峙空间
          位移向量: dir(+0.73mX, 0mY, 0mZ)大致·约8-12s内位移~30cm
起幅:     静态·双人全景·对视·天空暖橘·台灯光圈稳定（18A·首帧锁定）
触发点:   天空开始从暖橘向暗蓝过渡 → 摄影机开始极慢推近
落幅:     静态·Rico擦手·叠抹布·天空暗蓝·光圈稳定（18D·最终落幅）
运动段:   18A(静) → [推近0.03x·天空变色期间] → 18B(静·推近停止) → 
          18B→18C(静·Rico低头拿抹布) → 18C→18D(静·擦手叠抹布) → 18D(静·落幅)

详细阶段分解:
  阶段1 (18A):      静态·首帧锁定·两人对视·天空暖橘(~3000K)
  阶段1→2 (18A→18B): 极慢推近0.03x·天空橘→暗蓝(~8000K)过渡
                      推近=对峙在沉默中持续升温·心理空间被压缩到极限
                      天空变色=外部时间流逝·测量对峙时长
                      台灯光圈轻轻晃动=不安定感
                      M-MOT-01: 对峙升温=运镜动机
  阶段2 (18B):      静态·落幅锁定·推近停止·天空过渡中
                      ★ 推近在此停止——因为下面进入Rico的擦手动作
  阶段2→3 (18B→18C): 静态保持·Rico低头·拿起抹布
                      摄影机不动——D-DIA-11生效
  阶段3 (18C):      静态·Rico擦手指金属屑·动作缓慢精确
  阶段3→4 (18C→18D): 静态保持·Rico叠抹布·像对待枪械零件一样精确
  阶段4 (18D):      静态·最终落幅·抹布叠好放在桌上·天空暗蓝

★ 为什么推近在擦手前停止？
  D-DIA-11(P2): "Rico擦手·叠抹布·沉默对峙——摄影机完全不动"
  擦手动作的戏剧力量来自其精确·缓慢·控制感——和对待枪械零件一样。
  摄影机运动将带入"外部动力"·破坏Rico对动作的绝对控制。
  静止=Rico控制一切·包括摄影机。

三段式(M-20R-07):
  静段1: 18A — 首帧锁定 ✓
  动段:  18A→18B — 推近0.03x ✓
  静段2: 18B→18D — 落幅+延伸静段 ✓

戏剧动机: 全场景情绪最高点。
          对视+天空变色+光圈晃动=三个层次的"运动"在固定画面中展开——
          运镜在此是画龙点睛而非画蛇添足:
          · 极慢推近(0.03x)几乎不可察觉·但观众潜意识感到"空间在缩小"
          · 推近在擦手前停止=运镜知道自己何时该退出

KB规则:
  M-MOT-01(P0):  动机=对峙升温·推近=心理压缩 ✓
  M-20R-07(P0):  静→动→静 ✓
  M-MOT-05(P0):  首帧=静态完成态 ✓
  M-MOT-04(P0):  深度~4m·0.03x≤1.0x ✓
  D-DIA-11(P2):  Rico擦手·叠抹布→摄影机完全不动 ✓
  A-SUS-03(P1):  紧张期待·固定·不切不走·天空变色+对视为证 ✓
  D-DIA-01(P1):  对峙升温·极慢推近0.03x ✓
  M-20R-14(P1):  摄影机走最简单路线——直线 ✓
  M-20R-15(P0):  起幅落幅构图完整平衡 ✓
  M-MOT-02(P1):  速度匹配情绪·紧张=极慢但确定 ✓
  M-20R-04(P1):  运动结束时·画面应对准观众期待的东西——
                  落幅对准Rico叠好的抹布=对峙的"结果" ✓

空间约束: 
  机位[1.5, 1.5, 1.6]·推近沿镜头轴线·不穿越工作台 ✓
  不进入吊灯光锥路径 ✓
  位移~30cm(最长推近·因天空变色历时8-12s) ✓

过渡:     SHOT 18→19 = 硬切
         WS双人全景→MS Rico单人
         从分享的沉默空间收紧到Rico个人——他即将说最后一句
```

---

## SHOT 19 -- MS · Rico "带搜查令来"

```
运镜类型: 静态固定 (Static Fixed)
速度:     0x
方向:     N/A
起幅:     静态·Rico中景·站姿·抹布已叠好放在桌面上（19A）
落幅:     静态·"带搜查令来"对白结束·眼神锁定保持
运动段:   无

戏剧动机: 权力宣告·对话终结。
          "带搜查令来"=这是我家·这是我的领域·你没有搜查令就出去。
          "下次"=隐含的威胁——我们还会再见·但不是这次。
          
          静态=权威·不容置疑。
          Rico不需要运镜来增强这句话——话本身就是力量。
          摄影机静止=让这句话在空气中停留。
          
          D-DIA-12(P1): 力量对比·Rico=空间主人·最后一句=权力宣告。

KB规则:
  M-MOT-01(P0):  动机=权力宣告·静止=权威 ✓
  M-20R-07(P0):  全程静段 ✓
  D-DIA-12(P1):  力量对比·Rico空间主人·权力宣告 ✓
  M-20R-15(P0):  起幅落幅构图完整平衡 ✓
  M-20R-05(P1):  直接切换——对白结束后切到结尾书挡·不需要运镜过渡 ✓

空间约束: 机位[1.5, 3.0, 1.7]·距Rico~1.8m·静态 ✓
过渡:     SHOT 19→20 = 硬切
         MS Rico→ECU锉刀·回到开场书挡
         从人物的最后一句切回锉刀——人退场·物(锉刀)留到最后
```

---

## SHOT 20 -- ECU · 锉刀·结尾书挡

```
运镜类型: 静态固定 → 黑屏 (Static → Black Screen)
速度:     0x (画面阶段)
方向:     N/A
起幅:     静态·锉刀搁在枪管上·刀尖对准窗口·VO播放（20A）
落幅:     黑屏·锉刀声持续(金属摩擦·一圈)（20B）
运动段:   无——摄影机全程静止·画面最终消失(黑屏)·声音延续

戏剧动机: 书挡闭合(Closing Bookend)·与SHOT 01对称。
          · 画面阶段: 静态——与SHOT 01完全一致的位置和角度
          · VO阶段: 画面静止·锉刀无声地搁在枪管上
          · 黑屏: 画面消失·声音悬置——"锉刀继续转动·一圈"
          
          A-SUS-01(P1): "轻微后退"的变体——此处是"黑屏后退"。
          观众被"拉出"画面·但锉刀声不让离开。
          悬念不解决——Rico继续工作·Miguel没有搜查令·一切悬置。
          
          摄影机在画面阶段保持静止——让VO+锉刀的画面构成最后的视觉记忆。
          黑屏不是摄影机运动·是画面的消失——但声音证明故事没有结束。

KB规则:
  M-MOT-01(P0):  动机=书挡闭合·静止对称SHOT 01 ✓
  M-20R-07(P0):  画面阶段全程静段·黑屏=画面结束·非运镜 ✓
  A-SUS-01(P1):  黑屏后退·观众被拉出画面·不安感 ✓
  M-20R-15(P0):  起幅构图与SHOT 01完全对称·完整平衡 ✓

空间约束: ECU·工作台上方·同SHOT 01·静态 ✓
过渡:     无（场景结束·黑屏+锉刀声·悬念悬置）
```

---

## 段间过渡(Transitions)总览

```
全部转换: 硬切 (Straight Cut / Hard Cut)
无叠化·无淡入淡出(SHOT 20黑屏除外·黑屏=画面结束·非过渡效果)

过渡节奏设计:
  
  A段·开场 (01→02→03): 
    01微距→02全景→03中景·三级跳建立空间·节奏: 稳
    
  B段·对话建立 (03→04→05→06→07→08→09):
    03入侵→04无视→05观察→06/07POV→08审问→09转身
    景别在MS/CU/INSERT间跳切·节奏: 切分·累积
    
  C段·对峙升温 (09→10→11→12→13→14→15):
    09转身→10双人三阶段→11/12OTS对话→13进攻→14沉默→15反击
    10为最长镜头(三阶段·~10-15s)·其余为对话性快切
    节奏: 紧张递进
    
  D段·微动作高潮 (15→16a→16b→16c→17):
    15CU→16aECU→16bECU→16cECU→17CU
    三连ECU=全场景最快剪切节奏·模拟Rico扫视速度
    节奏: 急速·三连击
    
  E段·沉默对峙 (17→18→19→20):
    17CU→18WS(最长镜头·~15-20s)→19MS→20ECU
    从快切(ECU三连)到长镜头(18)=节奏释放
    18为全场景最长镜头·让观众在沉默中消化一切
    节奏: 释放·沉降

过渡KB规则:
  M-20R-05(P1): 所有过渡均为直切——对话已交代明白·精心设计的移动镜头不如经济切换 ✓
  M-MOT-06(P1): 运镜终点继承——推近镜头的落幅=下一镜的视觉起点(非运动继承·是空间/景别关系的继承)
                 例如: SHOT 10落幅(双人·2m·齐平)→SHOT 11/12的OTS景别基于此空间关系 ✓
```

---

# 第二部分：§6 YAML结构化块

## segments_movement

```yaml
segments_movement:
  scene: "EP15_S1_Rico工作室"
  source: "MOVEMENT_DESIGNER v2.0"
  date: "2026-07-07"
  
  global_constraints:
    space_depth_m: "~5"
    speed_limit: "≤1.0x"
    speed_limit_rule: "M-MOT-04(P0)"
    doorway_speed_rule: "固定/缓推/手持·禁快速横移"
    doorway_rule_id: "M-MOT-03(P0)"
    forbidden_movements:
      - "快速运镜"
      - "摇摄(Pan)"
      - "大幅推拉"
      - "环绕(Orbit)"
      - "升降(Crane)"
    impassable_barrier: "工作台(X=1.5→3.5, Y=2.8, Z=0.8)·运镜不可穿越"
    light_cone_no_fly: "吊灯光锥投影区(台面: X=1.5→3.5, Y=2.5→3.5)·镜头不入"
  
  movement_distribution:
    static:
      count: 17
      percentage: "77%"
      shot_ids: [1, 2, 4, 5, 6, 7, 8, 9, 11, 12, 14, 16a, 16b, 16c, 17, 19, 20]
    slow_push_in:
      count: 5
      percentage: "23%"
      speed_range: "0.03x - 0.04x"
      shot_ids: [3, 10, 13, 15, 18]
  
  transitions:
    type: "全部硬切(Hard Cut)"
    exception: "SHOT 20结尾黑屏=画面结束·非过渡效果"
    total_cuts: 19
  
  shots:
    - id: 1
      script_beat: "第3行·锉刀开场"
      movement_type: "静态固定(Static)"
      speed: 0
      speed_unit: "x (multiplier)"
      direction: "N/A"
      direction_vector: [0, 0, 0]
      displacement_cm: 0
      start_state: "static"
      trigger: "N/A"
      end_state: "static"
      dramatic_motive: "开场书挡·零运镜让观众专注于锉刀声和金属质感·建立手艺人节奏"
      kb_rules:
        - "M-MOT-01(P0): 动机=声音和质感叙事·静止"
        - "M-20R-07(P0): 全程静段"
        - "M-MOT-05(P0): 首帧=静态冻结帧"
        - "M-20R-12(P0): 完全静止·不犹豫"
        - "M-20R-15(P0): 起幅落幅构图完整平衡"
      space_constraint: "微距·工作台上方30cm·光锥内·无位移"

    - id: 2
      script_beat: "第4行前半·建立镜头"
      movement_type: "静态固定(Static)"
      speed: 0
      direction: "N/A"
      direction_vector: [0, 0, 0]
      displacement_cm: 0
      start_state: "static"
      trigger: "N/A"
      end_state: "static"
      dramatic_motive: "全景空间建立·静态让观众扫描空间信息(门·工作台·洞洞板·保险柜·光锥)"
      kb_rules:
        - "A-GEN-02(P0): 空间建立优先"
        - "M-MOT-01(P0): 动机=空间信息传递"
        - "M-MOT-05(P0): 首帧=静态完成态"
        - "M-20R-07(P0): 全程静段"
        - "M-20R-15(P0): 起幅落幅构图完整平衡"
      space_constraint: "全景·机位[1.5,1.5,1.6]·不穿墙不悬空"

    - id: 3
      script_beat: "第4行后半+第5行·门推开·影子"
      movement_type: "极慢推近(Slow Push-in)"
      speed: 0.03
      speed_unit: "x"
      direction: "沿镜头轴线向前·朝向门口/Miguel"
      direction_vector: [0.50, -0.33, 0.00]
      displacement_cm: "~8"
      duration_est_s: "~2.5"
      phases:
        - phase: "3A_static_start"
          state: "static"
          description: "门闭合·首帧锁定(M-MOT-05)"
        - phase: "3A_to_3B_push"
          state: "moving"
          speed: 0.03
          trigger: "门开始被推开·冷白光涌入"
          description: "摄影机被入侵事件吸引·不可察觉地向前探"
        - phase: "3B_static_end"
          state: "static"
          description: "门完全打开·Miguel剪影确立·影子投在Rico背上·落幅锁定"
      dramatic_motive: "制度入侵私人领域·冷白光(4000K)涌入暖黄空间(2800K)·摄影机被事件吸引·M-20R-13:门先动→摄影机跟动"
      kb_rules:
        - "M-MOT-01(P0): 动机=制度入侵·摄影机被事件吸引"
        - "M-20R-07(P0): 静→动→静三段式"
        - "M-MOT-05(P0): 首帧=静态完成态"
        - "M-MOT-03(P0): 门口区域·缓推0.03x安全"
        - "M-MOT-04(P0): 深度~4m·0.03x≤1.0x"
        - "M-20R-13(P1): 门先动→摄影机跟动"
        - "M-20R-14(P1): 摄影机走最简单的直线"
        - "M-20R-15(P0): 起幅落幅构图完整平衡"
      space_constraint: "机位[2.0,2.0,1.6]·推近不入开门弧线(~1m半径)·不入影子投射路径"

    - id: 4
      script_beat: "第6行·Rico不回头对话"
      movement_type: "静态固定(Static)"
      speed: 0
      direction: "N/A"
      direction_vector: [0, 0, 0]
      displacement_cm: 0
      start_state: "static"
      trigger: "N/A"
      end_state: "static"
      dramatic_motive: "与Rico的'无视'姿态同步——不回头=不承认Miguel的存在·摄影机静止=控制"
      kb_rules:
        - "M-MOT-01(P0): 动机=与Rico无视姿态同步"
        - "M-20R-07(P0): 全程静段"
        - "M-20R-12(P0): 完全静止"
        - "M-20R-15(P0): 起幅落幅构图完整平衡"
        - "D-DUO-08(P2): 眼平=平等视角·Rico空间主人"
      space_constraint: "机位[1.5,3.5,1.2]·距Rico~1.2m·CU·静态"

    - id: 5
      script_beat: "第7行·Miguel关门·扫视"
      movement_type: "静态固定(Static)"
      speed: 0
      direction: "N/A"
      direction_vector: [0, 0, 0]
      displacement_cm: 0
      start_state: "static"
      trigger: "N/A"
      end_state: "static"
      dramatic_motive: "Miguel扫视=画面内主体运动·摄影机静止让观众自主跟随扫视路径·M-20R-05:后续POV插入完成三要素"
      kb_rules:
        - "M-MOT-01(P0): 动机=让观众自主跟随扫视"
        - "M-MOT-03(P0): 门口区域·固定"
        - "M-20R-07(P0): 全程静段"
        - "M-20R-15(P0): 起幅落幅构图完整平衡·门框构图始终稳定"
        - "M-20R-05(P1): 三要素由后续POV插入完成·无需摇摄"
      space_constraint: "机位[2.5,1.5,1.7]·门口区域·固定·不入门框平面"

    - id: 6
      script_beat: "第7行·扫视:改装枪列阵"
      movement_type: "静态固定(Static)"
      speed: 0
      direction: "N/A"
      direction_vector: [0, 0, 0]
      displacement_cm: 0
      start_state: "static"
      trigger: "N/A"
      end_state: "static"
      dramatic_motive: "POV主观视角·摄影机=Miguel的眼睛·人眼不推轨·静止维护POV幻觉"
      kb_rules:
        - "M-MOT-01(P0): 动机=POV幻觉维护·人眼不推轨"
        - "M-20R-07(P0): 全程静段"
        - "M-20R-15(P0): 构图完整平衡"
      space_constraint: "机位[1.5,0.5,1.7]·距左墙~0.5-0.8m·静态"

    - id: 7
      script_beat: "第7行·扫视:保险柜"
      movement_type: "静态固定(Static)"
      speed: 0
      direction: "N/A"
      direction_vector: [0, 0, 0]
      displacement_cm: 0
      start_state: "static"
      trigger: "N/A"
      end_state: "static"
      dramatic_motive: "POV主观视角+悬念凝视·静止强迫观众面对保险柜缝隙·A-SUS-02:黑布=观众想象"
      kb_rules:
        - "M-MOT-01(P0): 动机=悬念凝视·静止=强迫观众面对未知"
        - "M-20R-07(P0): 全程静段"
        - "A-SUS-02(P1): 未知之惧·不拍威胁来源"
        - "M-20R-15(P0): 构图完整平衡"
      space_constraint: "机位[4.5,3.0,1.2]·保险柜前·不入保险柜·不入洗手池杂物区"

    - id: 8
      script_beat: "第8行·Miguel首句对白"
      movement_type: "静态固定(Static)"
      speed: 0
      direction: "N/A"
      direction_vector: [0, 0, 0]
      displacement_cm: 0
      start_state: "static"
      trigger: "N/A"
      end_state: "static"
      dramatic_motive: "审问开启·静态=审问者的控制感·Miguel不需要运镜制造压力·话本身就是压力"
      kb_rules:
        - "M-MOT-01(P0): 动机=审问语气·静态=控制"
        - "M-MOT-03(P0): 门口区域·固定"
        - "M-20R-07(P0): 全程静段"
        - "M-20R-15(P0): 起幅落幅构图完整平衡"
      space_constraint: "机位[2.5,1.2,1.7]·距Miguel~1.2m·不入门框平面"

    - id: 9
      script_beat: "第9行·Rico转身"
      movement_type: "静态固定(Static)"
      speed: 0
      direction: "N/A"
      direction_vector: [0, 0, 0]
      displacement_cm: 0
      start_state: "static"
      trigger: "N/A"
      end_state: "static"
      dramatic_motive: "Rico放下锉刀+转身=全场景第一次关键转折·摄影机静止让观众完整接收每个细节·M-20R-13:人物先动但不需跟动(Rico在画面内转身)"
      kb_rules:
        - "M-MOT-01(P0): 动机=Rico转身即运动事件·摄影机不干扰"
        - "M-20R-07(P0): 全程静段(画面内运动≠摄影机运动)"
        - "M-20R-15(P0): 起幅落幅构图·落幅中Rico面向镜头方向·平衡"
        - "M-20R-13(P1): 人物先动·摄影机需要时才跟动·此处不需要"
      space_constraint: "机位[1.5,3.2,1.2]·不阻挡Rico转身空间(旋转半径~0.5m)"

    - id: 10
      script_beat: "第9行后-第12行·面对面→迈步→站起"
      movement_type: "静→极慢推近→静(Static→Push-in→Static)"
      speed: 0.04
      speed_unit: "x"
      direction: "沿镜头轴线向前·向两人对峙空间·压缩画面深度"
      direction_vector: [0.73, 0.00, 0.00]
      displacement_cm: "~15"
      duration_est_s: "~3 (推近阶段)"
      phases:
        - phase: "10A_static"
          state: "static"
          description: "首帧锁定·Rico坐姿画右·Miguel站姿画左·距离4m·工作台隔开"
        - phase: "10A_to_10B_push"
          state: "moving"
          speed: 0.04
          trigger: "Miguel开始迈两步"
          description: "摄影机跟动推近·M-20R-13:Miguel先动→摄影机跟动·距离4m→2m·对峙升温"
        - phase: "10B_static"
          state: "static"
          description: "落幅锁定·距离2m·工作台仍隔在两人之间"
        - phase: "10B_to_10C_static_hold"
          state: "static"
          description: "摄影机保持静止·Rico站起(画面内主体运动)·M-CRN-01:不升降·动作适应镜头"
        - phase: "10C_static"
          state: "static"
          description: "最终落幅·两人站姿·身高齐平·隔工作台对峙·权力拉平"
      dramatic_motive: "物理距离4m→2m=对峙升温·推近=心理距离压缩视觉化·Rico站起时摄影机停止=站起的戏剧力量来自高度对比"
      kb_rules:
        - "M-MOT-01(P0): 动机=对峙升温·推近=心理压缩"
        - "M-20R-07(P0): 静→动→静三段式"
        - "M-MOT-05(P0): 首帧=静态完成态(10A)"
        - "M-MOT-04(P0): 深度~3m·0.04x≤1.0x"
        - "M-MOT-03(P0): 距门口>2m·非门区限制"
        - "D-DIA-01(P1): 对峙升温·极慢推近0.04x"
        - "M-20R-13(P1): Miguel先迈步→摄影机跟动"
        - "M-20R-14(P1): 摄影机走最简单路线——直线"
        - "M-CRN-01(P1): Rico站起→不升降"
        - "M-20R-15(P0): 起幅落幅构图完整平衡"
        - "D-DIA-03(P1): 坐vs站→站vs站·权力拉平"
        - "D-DIA-20(P1): 工作台=障碍物·运镜不穿越"
      space_constraint: "机位[1.5,2.0,1.6]·推近不入光锥路径·不入工作台·位移~15cm"

    - id: 11
      script_beat: "第10-14行对话段·Rico对白主镜"
      movement_type: "静态固定(Static)"
      speed: 0
      direction: "N/A"
      direction_vector: [0, 0, 0]
      displacement_cm: 0
      start_state: "static"
      trigger: "N/A"
      end_state: "static"
      dramatic_motive: "外反拍对话覆盖·OTS标准处置·M-20R-05:对话切换节奏已承载张力·运镜无增量价值"
      kb_rules:
        - "M-MOT-01(P0): 动机=对话覆盖·静态=标准处置"
        - "M-20R-07(P0): 全程静段"
        - "M-20R-15(P0): 起幅落幅构图完整平衡"
        - "M-20R-05(P1): 直接切换比移动镜头更经济"
      space_constraint: "机位[3.2,1.0,1.7]·距Miguel~0.8m·不穿过Miguel身体"

    - id: 12
      script_beat: "第10-14行对话段·Miguel对白主镜"
      movement_type: "静态固定(Static)"
      speed: 0
      direction: "N/A"
      direction_vector: [0, 0, 0]
      displacement_cm: 0
      start_state: "static"
      trigger: "N/A"
      end_state: "static"
      dramatic_motive: "外反拍对话覆盖·与SHOT 11配对·静态=标准处置"
      kb_rules:
        - "M-MOT-01(P0): 动机=对话覆盖·静态"
        - "M-20R-07(P0): 全程静段"
        - "M-20R-15(P0): 起幅落幅构图完整平衡"
      space_constraint: "机位[1.8,3.2,1.6]·距Rico~0.8m·不穿过Rico身体·不入光锥区"

    - id: 13
      script_beat: "第12行·Rico'你有指控吗？'"
      movement_type: "静→极慢推近→静(Static→Push-in→Static)"
      speed: 0.03
      speed_unit: "x"
      direction: "沿镜头轴线向前·向Rico面部·压缩心理距离"
      direction_vector: [0.82, 0.00, 0.00]
      displacement_cm: "~6"
      duration_est_s: "~2"
      phases:
        - phase: "13A_static_start"
          state: "static"
          description: "首帧锁定·Rico近景·暖黄光·眼神锐利"
        - phase: "13A_push"
          state: "moving"
          speed: 0.03
          trigger: "Rico开始说'你有指控吗？'"
          description: "极慢推近·Rico心理进攻的视觉化·向Miguel施压"
        - phase: "13A_prime_static_end"
          state: "static"
          description: "落幅锁定·对白结束·面部锁定保持"
      dramatic_motive: "Rico从防守转进攻·直接挑战刑警·推近=施压·观众和Miguel一起承受质询的重量"
      kb_rules:
        - "M-MOT-01(P0): 动机=心理进攻·推近=施压"
        - "M-20R-07(P0): 静→动→静三段式"
        - "M-MOT-05(P0): 首帧=静态完成态"
        - "M-MOT-04(P0): 深度~1.5m(<2m)·0.03x≤0.5x"
        - "D-DIA-01(P1): 对峙升温·极慢推近"
        - "M-20R-14(P1): 摄影机走直线"
        - "M-20R-15(P0): 起幅落幅构图完整平衡"
        - "M-MOT-02(P1): 速度匹配情绪·紧张=极慢但确定"
      space_constraint: "机位[1.8,2.8,1.7]·光锥范围内·位移~6cm"

    - id: 14
      script_beat: "第13行·Miguel'没有'+沉默2秒"
      movement_type: "静态固定(Static)——绝对静止"
      speed: 0
      direction: "N/A"
      direction_vector: [0, 0, 0]
      displacement_cm: 0
      phases:
        - phase: "14A_static_start"
          state: "static"
          description: "沉默起始·Miguel近景·面部微表情"
        - phase: "14A_silence"
          state: "static"
          description: "两秒沉默·摄影机绝对不动·D-DIA-11:凝固的空气"
        - phase: "14A_response"
          state: "static"
          description: "'没有'·简短·沉默后开口"
        - phase: "14B_static_end"
          state: "static"
          description: "落幅·沉默后·视线锁定保持"
      dramatic_motive: "D-DIA-11:摄影机完全不动·凝固的空气比任何运镜都有力·两秒沉默=观众预期悬置·反高潮比指控更有力"
      kb_rules:
        - "M-MOT-01(P0): 动机=沉默比语言有力·静止=不释放张力"
        - "D-DIA-11(P2): 摄影机完全不动·凝固的空气"
        - "A-SUS-03(P1): 紧张期待·固定·不切不走·强迫观众等待"
        - "M-20R-07(P0): 全程静段"
        - "M-20R-15(P0): 起幅落幅构图完整平衡"
        - "M-20R-12(P0): 完全静止·不犹豫"
      space_constraint: "机位[2.8,1.5,1.7]·距Miguel~1.2m·静态"

    - id: 15
      script_beat: "第14行·Rico'朋友的身份？'"
      movement_type: "静→极慢推近→静(Static→Push-in→Static)"
      speed: 0.03
      speed_unit: "x"
      direction: "沿镜头轴线向前·向Rico面部(同SHOT 13轴线)"
      direction_vector: [0.82, 0.00, 0.00]
      displacement_cm: "~7"
      duration_est_s: "~2.5"
      phases:
        - phase: "15A_static_start"
          state: "static"
          description: "首帧锁定·嘴角微动(上一句残留)·即将说话"
        - phase: "15A_push"
          state: "moving"
          speed: 0.03
          trigger: "Rico说出'那你来是——'"
          description: "极慢推近·Rico反客为主·用'朋友'剥离Miguel制度身份"
        - phase: "15B_static_end"
          state: "static"
          description: "落幅锁定·'朋友的身份？'结束·嘴角微动→收紧过渡·为16a/b/c铺垫"
      dramatic_motive: "Rico反客为主·推近=主动权转移·与SHOT 13形成运镜呼应(双进攻)·落幅锁定在嘴角收紧前"
      kb_rules:
        - "M-MOT-01(P0): 动机=反客为主·推近=主动权转移"
        - "M-20R-07(P0): 静→动→静三段式"
        - "M-MOT-05(P0): 首帧=静态完成态"
        - "M-MOT-04(P0): 深度~1.5m·0.03x≤0.5x"
        - "D-DIA-01(P1): 对峙升温·极慢推近"
        - "M-20R-14(P1): 摄影机走直线"
        - "M-20R-15(P0): 起幅落幅构图完整平衡"
      space_constraint: "机位[1.8,2.8,1.7]·同SHOT 13·位移~7cm"

    - id: "16a"
      script_beat: "第15行·Miguel手指1cm"
      movement_type: "静态固定(Static)——绝对静止"
      speed: 0
      direction: "N/A"
      direction_vector: [0, 0, 0]
      displacement_cm: 0
      phases:
        - phase: "16a_A_static"
          state: "static"
          description: "ECU右手·手指初始自然垂放·无名指旧伤疤可见"
        - phase: "16a_finger_move"
          state: "static"
          description: "画面内主体运动:手指向后移1cm·摄影机绝对静止·1cm=画面全部事件"
        - phase: "16a_B_static"
          state: "static"
          description: "手指位移完成·靠近配枪皮套边缘"
      dramatic_motive: "全场景叙事高潮触发器·1cm位移=全部事件·零运镜=让1cm成为画面唯一焦点·观众必须自己捕捉"
      kb_rules:
        - "M-MOT-01(P0): 动机=1cm是全部事件·运镜=破坏"
        - "M-20R-07(P0): 全程静段"
        - "M-20R-12(P0): 完全静止"
        - "A-SUS-09(P1): 恐惧延时释放·细微变化打破安全感"
        - "M-20R-15(P0): 起幅落幅构图完整平衡"
      space_constraint: "ECU·距右手~40cm·微距·静态"

    - id: "16b"
      script_beat: "第15行·Rico眼睛捕获"
      movement_type: "静态固定(Static)——绝对静止"
      speed: 0
      direction: "N/A"
      direction_vector: [0, 0, 0]
      displacement_cm: 0
      phases:
        - phase: "16b_A_static"
          state: "static"
          description: "ECU双眼·平视Miguel方向·深棕色虹膜"
        - phase: "16b_eye_flick"
          state: "static"
          description: "画面内主体运动:视线下扫一帧(1/24s)·摄影机绝对静止·Rico捕捉微动作"
        - phase: "16b_B_static"
          state: "static"
          description: "视线回到平视·锁定·瞳孔保持锐利(非恐惧·是警觉)"
      dramatic_motive: "1/24秒微动作·零运镜=维护可读性·观众必须和Rico一样'捕捉'瞬间·ANCHOR_BASELINE锚点A2:不动声色但什么都在看"
      kb_rules:
        - "M-MOT-01(P0): 动机=1/24s微动作·零运镜=可读性"
        - "M-20R-07(P0): 全程静段"
        - "A-SUS-09(P1): 细微变化打破安全感·眼睛扫一帧=叙事炸弹"
        - "M-20R-12(P0): 完全静止"
      space_constraint: "ECU·距眼睛~50cm·静态"

    - id: "16c"
      script_beat: "第15行·Rico嘴角收住"
      movement_type: "静态固定(Static)——绝对静止"
      speed: 0
      direction: "N/A"
      direction_vector: [0, 0, 0]
      displacement_cm: 0
      phases:
        - phase: "16c_A_static"
          state: "static"
          description: "ECU嘴角·微松弛(上一句残留)·胡茬·金属屑微粒反光"
        - phase: "16c_tighten"
          state: "static"
          description: "画面内主体运动:嘴角收紧·绷直·完全闭合·下颌硬化·咬肌微隆"
        - phase: "16c_B_static"
          state: "static"
          description: "嘴角完全收紧·情绪内化完成·锚点A3:情绪唯一外泄口闭合=危险升级"
      dramatic_motive: "三连切序列收束·嘴角收紧=情绪内化=危险升级·从对话到对峙的心理转折点·静止=让观众消化'他知道了'"
      kb_rules:
        - "M-MOT-01(P0): 动机=情绪内化·静止=让观众消化"
        - "M-20R-07(P0): 全程静段"
        - "A-SUS-09(P1): 延时释放完结点·完整弧线收束"
        - "A-SUS-03(P1): 紧张期待·锁在嘴角·强迫观众接收信息"
        - "M-20R-12(P0): 完全静止"
        - "M-20R-15(P0): 起幅落幅构图完整平衡"
      space_constraint: "ECU·距嘴角~40cm·静态"

    - id: 17
      script_beat: "第16行·Miguel缓慢对白"
      movement_type: "静态固定(Static)"
      speed: 0
      direction: "N/A"
      direction_vector: [0, 0, 0]
      displacement_cm: 0
      start_state: "static"
      trigger: "N/A"
      end_state: "static"
      dramatic_motive: "D-DIA-11:摄影机完全不动·对白节奏由演员控制·Miguel缓慢选字=犹豫·静止让犹豫暴露"
      kb_rules:
        - "M-MOT-01(P0): 动机=缓慢对白·静止=节奏由演员控制"
        - "D-DIA-11(P2): 摄影机完全不动"
        - "M-20R-07(P0): 全程静段"
        - "M-20R-15(P0): 起幅落幅构图完整平衡"
      space_constraint: "机位[2.8,1.5,1.7]·距Miguel~1.2m·静态"

    - id: 18
      script_beat: "第17-18行·对视·天空变色·Rico擦手"
      movement_type: "静→极慢推近→静(Static→Push-in→Static)·推近仅在对视/天空变色阶段"
      speed: 0.03
      speed_unit: "x"
      direction: "沿镜头轴线向前·向两人对峙空间"
      direction_vector: [0.73, 0.00, 0.00]
      displacement_cm: "~30"
      duration_est_s: "~8-12 (推近阶段·因天空变色历时较长)"
      phases:
        - phase: "18A_static_start"
          state: "static"
          description: "首帧锁定·双人全景·对视·天空暖橘(~3000K)·台灯光圈稳定"
        - phase: "18A_to_18B_push"
          state: "moving"
          speed: 0.03
          trigger: "天空开始从暖橘向暗蓝过渡"
          description: "极慢推近·对峙在沉默中升温·天空变色测量对峙时长·光圈微晃·心理空间被压缩到极限"
        - phase: "18B_static_push_stop"
          state: "static"
          description: "推近停止·落幅锁定·天空过渡中·D-DIA-11:擦手前运镜必须停止"
        - phase: "18B_to_18C_static"
          state: "static"
          description: "摄影机保持静止·Rico低头·拿起抹布"
        - phase: "18C_static_wipe"
          state: "static"
          description: "Rico擦手指金属屑·动作缓慢精确·像对待枪械零件"
        - phase: "18C_to_18D_static"
          state: "static"
          description: "摄影机保持静止·Rico叠抹布·放在桌上·动作精确"
        - phase: "18D_static_end"
          state: "static"
          description: "最终落幅·抹布叠好·天空暗蓝(~8000K)·光圈稳定·M-20R-04:落幅对准叠好的抹布=对峙的'结果'"
      dramatic_motive: "全场景情绪最高点·推近=心理空间被压缩到极限·推近在擦手前停止(D-DIA-11)=运镜知道何时退出·擦手的精确控制由静止承载"
      kb_rules:
        - "M-MOT-01(P0): 动机=对峙升温·推近=心理压缩"
        - "M-20R-07(P0): 静→动→静"
        - "M-MOT-05(P0): 首帧=静态完成态"
        - "M-MOT-04(P0): 深度~4m·0.03x≤1.0x"
        - "D-DIA-11(P2): Rico擦手·叠抹布→摄影机完全不动"
        - "A-SUS-03(P1): 紧张期待·固定·天空变色+对视为证"
        - "D-DIA-01(P1): 对峙升温·极慢推近"
        - "M-20R-14(P1): 摄影机走直线"
        - "M-20R-15(P0): 起幅落幅构图完整平衡"
        - "M-MOT-02(P1): 速度匹配情绪·紧张=极慢"
        - "M-20R-04(P1): 落幅对准叠好的抹布·观众期待对峙'结果'"
      space_constraint: "机位[1.5,1.5,1.6]·推近不入光锥·不入工作台·位移~30cm(最长推近)"

    - id: 19
      script_beat: "第19行·Rico'带搜查令来'"
      movement_type: "静态固定(Static)"
      speed: 0
      direction: "N/A"
      direction_vector: [0, 0, 0]
      displacement_cm: 0
      start_state: "static"
      trigger: "N/A"
      end_state: "static"
      dramatic_motive: "权力宣告·对话终结·静态=权威·Rico不需要运镜·话本身就是力量·D-DIA-12:空间主人·最后一句=权力"
      kb_rules:
        - "M-MOT-01(P0): 动机=权力宣告·静止=权威"
        - "M-20R-07(P0): 全程静段"
        - "D-DIA-12(P1): 力量对比·空间主人·权力宣告"
        - "M-20R-15(P0): 起幅落幅构图完整平衡"
        - "M-20R-05(P1): 直接切换·运镜过渡不必要"
      space_constraint: "机位[1.5,3.0,1.7]·距Rico~1.8m·静态"

    - id: 20
      script_beat: "第20-21行·VO·黑屏·锉刀声"
      movement_type: "静态固定→黑屏(Static→Black Screen)"
      speed: 0
      speed_unit: "x"
      direction: "N/A"
      direction_vector: [0, 0, 0]
      displacement_cm: 0
      phases:
        - phase: "20A_static"
          state: "static"
          description: "锉刀搁枪管上·刀尖对准窗口·VO播放·画面静止(同SHOT 01对称)"
        - phase: "20A_to_20B_blackout"
          state: "static→black"
          description: "VO结束·画面渐黑·摄影机位置不变·黑屏=画面消失·非运镜"
        - phase: "20B_black_sound"
          state: "black_screen"
          description: "黑屏·锉刀声:金属摩擦·一圈·声画分离·悬念悬置"
      dramatic_motive: "书挡闭合·与SHOT 01完全对称·A-SUS-01:黑屏后退·观众被拉出画面·锉刀声不让离开·悬念不解决"
      kb_rules:
        - "M-MOT-01(P0): 动机=书挡闭合·静止对称SHOT 01"
        - "M-20R-07(P0): 画面阶段全程静段·黑屏=画面结束·非运镜"
        - "A-SUS-01(P1): 黑屏后退·不安感"
        - "M-20R-15(P0): 起幅与SHOT 01完全对称·构图完整"
      space_constraint: "ECU·工作台上方·同SHOT 01·静态"
```

---

## frames_movement

```yaml
frames_movement:
  scene: "EP15_S1_Rico工作室"
  source: "MOVEMENT_DESIGNER v2.0"
  date: "2026-07-07"
  note: "每关键帧指定摄影机运动状态·供Composition Designer+Storyboard Planner机械消费"
  total_keyframes: 42
  
  keyframes:
    # ---- SHOT 01 ----
    - shot_id: 1
      kf_id: "1A"
      movement_state: "static"
      speed: 0
      is_start_frame: true
      is_end_frame: true
      description: "锉刀在枪管上·起始位·静态冻结·零运镜"
      
    # ---- SHOT 02 ----
    - shot_id: 2
      kf_id: "2A"
      movement_state: "static"
      speed: 0
      is_start_frame: true
      is_end_frame: true
      description: "建立全景·Rico背影·工作台·洞洞板·门闭合·静态冻结"
      
    # ---- SHOT 03 ----
    - shot_id: 3
      kf_id: "3A"
      movement_state: "static_start"
      speed: 0
      is_start_frame: true
      is_end_frame: false
      next_transition: "push_in"
      description: "门闭合·首帧冻结(M-MOT-05)·静段起始"
      
    - shot_id: 3
      kf_id: "3B"
      movement_state: "static_end"
      speed: 0
      is_start_frame: false
      is_end_frame: true
      prev_transition: "push_in"
      description: "门全开·Miguel剪影·落幅锁定·推近终点·0.03x推近~2.5s位移~8cm"
      push_in_detail:
        from_kf: "3A"
        speed: 0.03
        direction: "沿镜头轴线向前→门口/Miguel"
        trigger: "门开始被推开·冷白光涌入"
        displacement_cm: "~8"
        rule_m20r07: "静(3A)→动(推近0.03x)→静(3B)"
        rule_m20r13: "门先动→摄影机跟动"
      
    # ---- SHOT 04 ----
    - shot_id: 4
      kf_id: "4A"
      movement_state: "static"
      speed: 0
      is_start_frame: true
      is_end_frame: true
      description: "Rico 3/4侧脸·视线向下·锉刀声·静态冻结"
      
    # ---- SHOT 05 ----
    - shot_id: 5
      kf_id: "5A"
      movement_state: "static"
      speed: 0
      is_start_frame: true
      is_end_frame: false
      description: "Miguel关门·靠门框·静态"
      
    - shot_id: 5
      kf_id: "5B"
      movement_state: "static"
      speed: 0
      is_start_frame: false
      is_end_frame: true
      description: "Miguel扫视结束·视线停在保险柜方向·静态·画面内扫视为主体运动"
      
    # ---- SHOT 06 ----
    - shot_id: 6
      kf_id: "6A"
      movement_state: "static"
      speed: 0
      is_start_frame: true
      is_end_frame: true
      description: "左墙改装枪列阵·POV静态·摄影机=Miguel眼睛"
      
    # ---- SHOT 07 ----
    - shot_id: 7
      kf_id: "7A"
      movement_state: "static"
      speed: 0
      is_start_frame: true
      is_end_frame: true
      description: "保险柜留缝·黑布包裹·POV静态·悬念凝视"
      
    # ---- SHOT 08 ----
    - shot_id: 8
      kf_id: "8A"
      movement_state: "static"
      speed: 0
      is_start_frame: true
      is_end_frame: true
      description: "Miguel面部·'你看上去不惊讶'·半明半暗·静态冻结"
      
    # ---- SHOT 09 ----
    - shot_id: 9
      kf_id: "9A"
      movement_state: "static"
      speed: 0
      is_start_frame: true
      is_end_frame: false
      description: "Rico放下锉刀·手在画面中·静态·画面内主体运动(放下锉刀+转身)但摄影机不动"
      
    - shot_id: 9
      kf_id: "9B"
      movement_state: "static"
      speed: 0
      is_start_frame: false
      is_end_frame: true
      description: "Rico转身完成·面对Miguel方向·面部光线从侧→正·静态落幅"
      
    # ---- SHOT 10 ----
    - shot_id: 10
      kf_id: "10A"
      movement_state: "static_start"
      speed: 0
      is_start_frame: true
      is_end_frame: false
      next_transition: "push_in"
      description: "双人·Rico坐姿画右·Miguel站姿画左·距离4m·首帧冻结·静段1"
      
    - shot_id: 10
      kf_id: "10B"
      movement_state: "static_mid"
      speed: 0
      is_start_frame: false
      is_end_frame: false
      prev_transition: "push_in"
      description: "Miguel迈两步完成·距离2m·推近落幅·静段2·0.04x推近~3s位移~15cm"
      push_in_detail:
        from_kf: "10A"
        speed: 0.04
        direction: "沿镜头轴线向前→两人对峙空间"
        trigger: "Miguel开始迈两步"
        displacement_cm: "~15"
        rule_m20r07: "静(10A)→动(推近0.04x)→静(10B)"
        rule_m20r13: "Miguel先动→摄影机跟动"
      
    - shot_id: 10
      kf_id: "10C"
      movement_state: "static_end"
      speed: 0
      is_start_frame: false
      is_end_frame: true
      description: "Rico站起·两人身高齐平·隔工作台·最终落幅·摄影机在10B→10C全程静止·Rico站起=画面内主体运动·M-CRN-01:不升降"
      
    # ---- SHOT 11 ----
    - shot_id: 11
      kf_id: "11A"
      movement_state: "static"
      speed: 0
      is_start_frame: true
      is_end_frame: true
      description: "OTS Miguel肩→Rico正面·静态·外反拍A"
      
    # ---- SHOT 12 ----
    - shot_id: 12
      kf_id: "12A"
      movement_state: "static"
      speed: 0
      is_start_frame: true
      is_end_frame: true
      description: "OTS Rico肩→Miguel正面·静态·外反拍B"
      
    # ---- SHOT 13 ----
    - shot_id: 13
      kf_id: "13A"
      movement_state: "static_start"
      speed: 0
      is_start_frame: true
      is_end_frame: false
      next_transition: "push_in"
      description: "Rico近景·'你有指控吗？'·首帧冻结·静段1"
      note: "SHOT 13的起幅和落幅是同一关键帧位置(13A)·推近在单帧内完成·落幅=13A'(在YAML中表示为13A的end状态)"
      
    # ---- SHOT 14 ----
    - shot_id: 14
      kf_id: "14A"
      movement_state: "static"
      speed: 0
      is_start_frame: true
      is_end_frame: false
      description: "Miguel近景·沉默起始·绝对静止·D-DIA-11激活"
      
    - shot_id: 14
      kf_id: "14B"
      movement_state: "static"
      speed: 0
      is_start_frame: false
      is_end_frame: true
      description: "Miguel近景·'没有'·沉默2秒后·绝对静止·A-SUS-03:固定·不切不走"
      
    # ---- SHOT 15 ----
    - shot_id: 15
      kf_id: "15A"
      movement_state: "static_start"
      speed: 0
      is_start_frame: true
      is_end_frame: false
      next_transition: "push_in"
      description: "Rico近景·嘴角微动(上一句残留)·首帧冻结·静段1"
      note: "SHOT 15的推近在单帧内完成·落幅=15A'(end状态)·与SHOT 13形成运镜呼应"
      
    # ---- SHOT 16a ----
    - shot_id: "16a"
      kf_id: "16a_A"
      movement_state: "static"
      speed: 0
      is_start_frame: true
      is_end_frame: false
      description: "ECU Miguel右手·手指初始位置·绝对静止·三连切第一镜"
      
    - shot_id: "16a"
      kf_id: "16a_B"
      movement_state: "static"
      speed: 0
      is_start_frame: false
      is_end_frame: true
      description: "ECU Miguel右手·手指后移1cm完成·靠近配枪皮套·摄影机绝对静止·1cm=画面内主体运动"
      
    # ---- SHOT 16b ----
    - shot_id: "16b"
      kf_id: "16b_A"
      movement_state: "static"
      speed: 0
      is_start_frame: true
      is_end_frame: false
      description: "ECU Rico眼睛·平视Miguel·绝对静止·三连切第二镜"
      
    - shot_id: "16b"
      kf_id: "16b_B"
      movement_state: "static"
      speed: 0
      is_start_frame: false
      is_end_frame: true
      description: "ECU Rico眼睛·下扫一帧(1/24s)→回到平视·摄影机绝对静止·1/24s=画面内主体运动"
      
    # ---- SHOT 16c ----
    - shot_id: "16c"
      kf_id: "16c_A"
      movement_state: "static"
      speed: 0
      is_start_frame: true
      is_end_frame: false
      description: "ECU Rico嘴角·微松弛·绝对静止·三连切第三镜"
      
    - shot_id: "16c"
      kf_id: "16c_B"
      movement_state: "static"
      speed: 0
      is_start_frame: false
      is_end_frame: true
      description: "ECU Rico嘴角·收紧·绷直·完全闭合·绝对静止·情绪内化完成·三连切收束"
      
    # ---- SHOT 17 ----
    - shot_id: 17
      kf_id: "17A"
      movement_state: "static"
      speed: 0
      is_start_frame: true
      is_end_frame: true
      description: "Miguel近景·缓慢对白·'不想看你自我毁灭'·绝对静止·D-DIA-11"
      
    # ---- SHOT 18 ----
    - shot_id: 18
      kf_id: "18A"
      movement_state: "static_start"
      speed: 0
      is_start_frame: true
      is_end_frame: false
      next_transition: "push_in"
      description: "双人全景·对视·天空暖橘(~3000K)·光圈稳定·首帧冻结·静段1"
      
    - shot_id: 18
      kf_id: "18B"
      movement_state: "static_mid"
      speed: 0
      is_start_frame: false
      is_end_frame: false
      prev_transition: "push_in"
      description: "双人全景·对视·天空过渡中(~4000K)·光圈微晃·推近停止·落幅锁定"
      push_in_detail:
        from_kf: "18A"
        speed: 0.03
        direction: "沿镜头轴线向前→两人对峙空间"
        trigger: "天空开始从暖橘向暗蓝过渡"
        displacement_cm: "~30"
        rule_m20r07: "静(18A)→动(推近0.03x)→静(18B)"
        rule_ddia11: "推近在18B停止→Rico擦手阶段(18B→18D)摄影机完全不动"
      
    - shot_id: 18
      kf_id: "18C"
      movement_state: "static"
      speed: 0
      is_start_frame: false
      is_end_frame: false
      description: "Rico低头·拿抹布·擦金属屑·摄影机绝对静止·D-DIA-11激活:擦手动作=摄影机不动"
      
    - shot_id: 18
      kf_id: "18D"
      movement_state: "static_end"
      speed: 0
      is_start_frame: false
      is_end_frame: true
      description: "抹布叠好·放在桌上·天空暗蓝(~8000K)·光圈稳定·最终落幅·M-20R-04:落幅对准叠好的抹布=对峙的'结果'"
      
    # ---- SHOT 19 ----
    - shot_id: 19
      kf_id: "19A"
      movement_state: "static"
      speed: 0
      is_start_frame: true
      is_end_frame: true
      description: "Rico中景·站姿·抹布已叠好·'带搜查令来'·静态冻结·权力宣告"
      
    # ---- SHOT 20 ----
    - shot_id: 20
      kf_id: "20A"
      movement_state: "static"
      speed: 0
      is_start_frame: true
      is_end_frame: false
      description: "锉刀搁枪管上·VO播放·画面静止·与SHOT 01完全对称·书挡结构B"
      
    - shot_id: 20
      kf_id: "20B"
      movement_state: "black_screen"
      speed: 0
      is_start_frame: false
      is_end_frame: true
      description: "黑屏·锉刀声持续(金属摩擦·一圈)·画面消失·声画分离·悬念悬置·A-SUS-01:黑屏后退"
```

---

## 输出摘要

```
┌──────────────────────────────────────────────────────────────────┐
│           EP15 S1 MOVEMENT DESIGNER · 运镜设计摘要                │
│                                                                  │
│  场景: Rico工作室（傍晚→夜）· 单场景                               │
│  总镜数: 20镜 (含16a/b/c三子镜·实际22个运镜单元)                    │
│                                                                  │
│  运镜分布:                                                        │
│    静态固定 (0x):      17镜 — 01,02,04,05,06,07,08,09,11,       │
│                                  12,14,16a,16b,16c,17,19,20      │
│    极慢推近 (0.03-0.04x): 5镜 — 03(0.03x),10(0.04x),13(0.03x),  │
│                                  15(0.03x),18(0.03x)              │
│                                                                  │
│  运镜比例: 静态 77% / 推近 23%                                    │
│  (符合ANCHOR_BASELINE §B: 静态~70%·推近~20%·微距~10%)            │
│                                                                  │
│  禁用类型: 快速运镜·摇摄(Pan)·大幅推拉·环绕(Orbit)·升降(Crane)    │
│  全部满足 ✓                                                       │
│                                                                  │
│  空间约束验证:                                                    │
│    速度≤1.0x (M-MOT-04):  最快0.04x·远低于上限 ✓                  │
│    门口区域禁快速横移 (M-MOT-03): 门口区域仅固定/缓推 ✓            │
│    不穿越工作台:           所有推近方向沿镜头轴线·不跨工作台 ✓      │
│    不入光锥路径:           所有推近不入吊灯光锥投影区 ✓            │
│    不进入禁入区:           位移量极小(6-30cm)·安全余量充足 ✓       │
│                                                                  │
│  三段式验证 (M-20R-07):                                          │
│    5个推近镜头均静→动→静·起幅落幅均为静态冻结帧 ✓                │
│    17个静态镜头全程静段 ✓                                        │
│                                                                  │
│  运动动机验证 (M-MOT-01):                                        │
│    5个推近均基于明确的戏剧动机(入侵·对峙升温·心理进攻·压缩) ✓    │
│    17个静态均基于明确的戏剧动机(声音叙事·空间建立·节奏控制等) ✓  │
│                                                                  │
│  关键设计决策:                                                    │
│    1. SHOT 18: 推近在对视阶段·擦手前停止——D-DIA-11优先于推近     │
│    2. SHOT 10: 推近在Miguel迈步阶段·Rico站起时摄影机不升降       │
│       ——M-CRN-01: 动作适应镜头·非镜头适应动作                     │
│    3. SHOT 03: 唯一在门口区域的推近——速度0.03x极慢·方向沿轴      │
│       ——M-MOT-03: 门口缓推安全·非横移                            │
│    4. SHOT 13+15: 两次推近形成运镜呼应——双进攻节奏                │
│    5. SHOT 14+16a/b/c+17: 绝对静止序列——微动作叙事               │
│                                                                  │
│  KB规则引用:                                                      │
│    P0级: M-MOT-01, M-MOT-03, M-MOT-04, M-MOT-05,                 │
│           M-20R-00, M-20R-07, M-20R-10, M-20R-12, M-20R-15       │
│    P1级: M-MOT-02, M-MOT-06, D-DIA-01, M-20R-04, M-20R-05,       │
│           M-20R-13, M-20R-14, M-20R-16, M-CRN-01, A-SUS-01,      │
│           A-SUS-03, A-SUS-09, D-DIA-03, D-DIA-12, D-DIA-20       │
│    P2级: D-DIA-11, A-SUS-02, D-DUO-08                            │
│                                                                  │
│  下游消费:                                                        │
│    → Composition Designer: segments_movement中22个运镜单元        │
│    → Storyboard Planner: frames_movement中42个关键帧·运动状态     │
│      每个关键帧标注: movement_state·speed·is_start/end_frame     │
│      推近关键帧含: push_in_detail(speed·direction·trigger·disp)  │
│                                                                  │
│  输出文件: EP15_S1_MOVEMENT_DESIGNER.md                           │
│  写入时间: 2026-07-07                                              │
└──────────────────────────────────────────────────────────────────┘
```
