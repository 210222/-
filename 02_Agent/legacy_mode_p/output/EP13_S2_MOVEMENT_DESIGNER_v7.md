# EP13_S2_MOVEMENT_DESIGNER_v7.1
## MODE:P Movement Designer · M-Level · 运镜设计
## 鉴证科实验室 · EP13《弹道学》第1幕

> **生成:** 2026-07-08 · Movement Designer v2.0
> **复杂度:** M-Level (M-A路径) · F1=1 F2=2 F3~15 F4~53% F6=false
> **被调用者:** dispatcher_v5.0.md MODE:P · Step A2 (串行第二位·读取Shot Architect报告)
> **下游消费者:** storyboard_planner (Step A2.5·§2G TIME_SKELETON组装) · Composition Designer (Step A2·串行第三位)
> **KB加载:** agent_quick_ref_v1.0.md §C.7(运镜与运动·~80条) · §C.0(通用铁律) · KB深读: 03_导演知识库_v5.0.md §5运镜与运动(M-MOT/M-MOV/M-20R/M-LEN 计78条规则)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎥 Movement Designer 运镜设计报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

---

## Step A: 情绪-运镜映射

### 场景情绪弧线: [0 → +2 → +3 → 0 → -1 → -3]

根据MODE:A增强剧本逐镜情绪推断:

| 镜号 | 秒段 | 情绪值 | 情绪描述 | 拟配运镜 | 强度 |
|:---:|:---:|:------:|---------|---------|:---:|
| #1 | 0-4 | 0 | 冷开场·纯视觉 | 极慢推近(0.1x) | S1 |
| #2 | 4-7 | 0 | 中立·专注工作 | 固定 | S0 |
| #3 | 7-10 | 0 | 中立·数据阅读 | 固定 | S0 |
| #4 | 10-14 | +2 | 兴奋·电话发现 | 慢推近(0.15x) | S1-S2 |
| #5 | 14-18 | +1 | 建立·Miguel入室 | 跟拍横移(0.2x) | S2 |
| #6 | 18-21 | 0 | 观察·消化证据 | 固定 | S0 |
| #7 | 21-26 | +2 | 揭示·专业骄傲 | 极慢推近(0.1x) | S1 |
| #7.5 | 26-28 | 0→-1 | 倾听·沉默 | 固定 | S0 |
| #8 | 28-32 | +3 | 冲击·档案摔桌 | 手持微晃(0.3x) | S2 |
| #9 | 32-36 | +1 | 认知·照片比对 | 固定 | S0 |
| #10 | 36-39 | +2 | 结论沉重 | 极慢推近(0.1x) | S1 |
| #11 | 39-45 | +1 | 释放·维度拓展 | 摇臂上升(0.2x) | S2 |
| #12 | 45-48 | +2 | 名字冲击 | 极慢推近(0.1x) | S1 |
| #12.5 | 48-50 | -1 | 凝固·沉默 | 固定 | S0 |
| #13 | 50-53 | -2 | 内化·身体认知 | 固定+呼吸位移 | S0-S1 |
| #14 | 53-56 | -2 | 终结·光的死亡 | 固定 | S0 |
| #15 | 56-58 | -3 | 余韵·悬念 | 固定 | S0 |

### 情绪-运镜强度对照检查

```
差值>1的镜头:
  #7  情绪+2 / 强度S1 · 差值≈1 ✅ 反差设计·慢速推近强化专业骄傲的分量
  #8  情绪+3 / 强度S2 · 差值≈1 ✅ 手持微晃=冲击的物理表达·不是速度是质感
  #10 情绪+2 / 强度S1 · 差值≈1 ✅ 反差设计·结论的重量用慢速而非快速
  #12 情绪+2 / 强度S1 · 差值≈1 ✅ 名字的压迫用慢速推进·非冲是压

全部镜情绪映射 ✅ 无≥2差值未标注
有意反差镜头已标注设计意图·非错位
```

---

## Step B: 空间可行性验证

### 空间地图速查 (§C ANCHOR_BASELINE)

```
空间尺寸: ~8m(纵深)×~5m(宽)×~3m(高) · 矩形长条形
禁入区: ❌ 实验台内部/上方 · 物证橱窗内部 · 墙壁内部 · 天花板
窄空间约束: 走廊宽度~2.5m > 1.5m → 横移可用 ✅
空间深度约束: >5m → 速度上限≤3.0x ✅ (全场景最大0.3x)
```

### 逐镜空间验证

| 镜号 | 运镜 | 空间检查 | 结果 |
|:---:|------|---------|:---:|
| #1 | 极慢推近(0.1x) | 推近路径<3cm·载物台空间深度<5cm·无障碍 | ✅ |
| #2 | 固定 | 无运动 | ✅ |
| #3 | 固定 | 无运动 | ✅ |
| #4 | 慢推近(0.15x) | 推近路径<6cm·工作台前空间充足 | ✅ |
| #5 | 横移跟拍(0.2x) | 横移路径沿走道·宽度~2.5m>1.5m·深度~8m>3m·M-MOT-03合规 | ✅ |
| #6 | 固定 | 无运动 | ✅ |
| #7 | 极慢推近(0.1x) | 推近路径<5cm·工作台前无障碍 | ✅ |
| #7.5 | 固定 | 无运动 | ✅ |
| #8 | 手持微晃(±2cm) | 固定位置微晃·无穿墙风险 | ✅ |
| #9 | 固定 | 无运动 | ✅ |
| #10 | 极慢推近(0.1x) | 推近路径<3cm·空间充足 | ✅ |
| #11 | 摇臂上升(0.2x·1.5m) | 上升路径沿走道·起点桌面~90cm→终点~240cm<天花板~300cm·路径无遮挡 | ✅ |
| #12 | 极慢推近(0.1x) | 推近路径<3cm·窗前区域空间充足 | ✅ |
| #12.5 | 固定 | 无运动 | ✅ |
| #13 | 呼吸位移(±0.5cm) | 微动范围<1cm·无风险 | ✅ |
| #14 | 固定 | 无运动 | ✅ |
| #15 | 固定 | 无运动 | ✅ |

**全部17镜空间验证: ✅ 17/17通过 · 无穿墙 · 无禁入区入侵**

---

## Step C: 逐镜运镜设计

### 镜#1 | 弹头ECU | 0-4s | 动态 | seq①

```
运镜类型: 极慢推近(0.1x) / 线性运动-推近类
速度参数: 0.1x · 速度档S1
方向: 推近(~3cm)
起止状态: 静止(弹头全貌·2s) → 极慢推近(0.1x·2s) → 静止(弹头膛线细部)
时长: 4s (静止2s + 推近2s)
三段式: M-20R-07 静→动→静 ✅

KB规则ID: M-20R-07(三段运动公式) · M-MOT-04(速度上限·空间深度<5cm→≤0.5x·0.1x合规) · M-20R-15(起幅落幅平衡)

情绪匹配: 情绪值=0(冷开场) · 运镜强度=S1 · 差值=0 ✅ 完美匹配
空间约束: ✅ 推近路径<3cm·载物台空间深度<5cm·无障碍·无穿墙

动机检查: ✅ 画面有"值得推近看"的对象——弹头膛线纹路·揭示式运动(M-MOV-03)
首帧锁定: ✅ 第0秒静止·首帧为冻结帧·提供视觉锚点(M-MOT-05)
终点继承: ✅ 终点静止位置成为镜#2的视觉起点(弹头→Vincent工作) (M-MOT-06)
```

### 镜#2 | Vincent近景 | 4-7s | 静态 | seq②

```
运镜类型: 固定(S0) / 静态
静态例外: ✅ 信息密集——三层深度(前景显微镜虚化+中景面部+背景实验台纵深)
KB规则ID: M-MOT-01(无运镜动机·固定成立) · M-20R-05(直接切换比移动更经济)

情绪匹配: 情绪值=0(中立·专注) · 运镜强度=S0 · 差值=0 ✅
空间约束: ✅ 工作台前·无运动

无动机静态检测: 属于"信息密集"例外 → ✅ 观众需要时间吸收画面信息
```

### 镜#3 | 屏幕特写 | 7-10s | 静态 | seq③

```
运镜类型: 固定(S0) / 静态
静态例外: ✅ 信息密集——五张照片+绿色比对线+标题文字·屏幕数据密集
KB规则ID: M-20R-05(直接切换比移动镜头更经济·"事情已交代明白"→固定成立)

情绪匹配: 情绪值=0(中立·数据阅读) · 运镜强度=S0 · 差值=0 ✅
空间约束: ✅ 屏幕前固定位置

无动机静态检测: 属于"信息密集"例外 → ✅ 观众需要时间阅读屏幕数据
```

### 镜#4 | Vincent打电话 | 10-14s | 动态 | seq④

```
运镜类型: 慢推近(0.15x) / 线性运动-推近类
速度参数: 0.15x · 速度档S1-S2
方向: 推近(~6cm)
起止状态: 静止(胸部以上) → 慢推近(0.15x·3s) → 静止(双眼·双色温交汇)
时长: 4s (推近3s + 静止1s)
三段式: M-20R-07 静→动→静 ✅

KB规则ID: M-20R-07(三段公式) · M-MOT-02(速度匹配情绪·+2兴奋→0.15x适中) · M-MOV-04(向前运动强调主体重要性)

情绪匹配: 情绪值=+2(兴奋·新发现) · 运镜强度=S1-S2 · 差值≈1 ✅
空间约束: ✅ 推近路径<6cm·工作台前无遮挡

动机检查: ✅ "值得推近看"——Vincent面部兴奋细节+手机暖光入侵的瞬间
节奏-对白呼吸: 拿手机(推近)→等待音(推至双色温交汇)→对白(静止) ✅ (M-MOT-07)
```

### 镜#5 | Miguel入室 | 14-18s | 动态 | seq⑤

```
运镜类型: 跟镜头·稳定器横移(0.2x) / 线性运动-横移类
速度参数: 0.2x · 速度档S2
方向: 右横移~1.5m
起止状态: 静止(门内侧·Miguel剪影) → 跟拍横移(0.2x·4s) → 静止(工作台前·冷光浮现)
时长: 4s (横移4s·起止静止各~0.5s计入)
三段式: M-20R-07 静→动→静 ✅

KB规则ID: M-20R-13(人物先动→摄影机跟动) · M-MOT-01(运动动机=Miguel入室动作) · M-MOV-02(同步运动·摄影机与演员同速) · M-MOT-03(空间可行性·走廊宽~2.5m>1.5m)

情绪匹配: 情绪值=+1(建立·Miguel进入) · 运镜强度=S2 · 差值≈1 ✅
空间约束: ✅ 横移路径沿走道·宽度~2.5m>1.5m·深度~8m>3m·M-MOT-03走廊横移合规

动机检查: ✅ 演员驱动(M-MOV-01) · Miguel的"进入"动作=运镜动机
P-FAL-06检查: 空间深度~8m>3m·非窄空间横移 ✅
```

### 镜#6 | Miguel内反拍 | 18-21s | 静态 | seq⑥

```
运镜类型: 固定(S0) / 静态
静态例外: ✅ 情感沉浸——Miguel消化证据·需要静止让反应自己说话
KB规则ID: M-MOT-01(无运镜动机·固定成立)

情绪匹配: 情绪值=0(观察·消化) · 运镜强度=S0 · 差值=0 ✅
空间约束: ✅ 工作台前·无运动

无动机静态检测: 属于"情感沉浸"例外 → ✅ 沉默力量大于运镜
```

### 镜#7 | Vincent"签名" | 21-26s | 动态 | seq⑦

```
运镜类型: 极慢推近(0.1x) / 线性运动-推近类
速度参数: 0.1x · 速度档S1
方向: 推近(~5cm)
起止状态: 静止(胸部以上) → 极慢推近(0.1x·4s·配合对白呼吸) → 静止(眼镜+手指)
时长: 5s (推近4s·暂停+继续+静止1s)
三段式: M-20R-07 静→动→静 ✅

KB规则ID: M-20R-07(三段公式) · M-MOT-02(速度匹配情绪·0.1x=沉思节奏·情绪+2但有意反差) · M-MOT-07(运镜-对白呼吸同步·1-2s推近→暂停→3-4s继续→5s静止)

情绪匹配: 情绪值=+2(揭示·专业骄傲) · 运镜强度=S1 · 差值≈1 ⚠️ 反差设计
说明: 全场最具叙事分量的台词·极慢推近非情绪错位——用慢速强化"每一毫米都是判断"的沉重
空间约束: ✅ 推近路径<5cm·工作台前无遮挡

动机检查: ✅ "值得推近看"——眼镜反射屏幕蓝光+手指点向膛线纹路(M-MOV-03揭示式运动)
```

### 镜#7.5 | Miguel倾听 | 26-28s | 静态 | seq⑧

```
运镜类型: 固定(S0) / 静态
静态例外: ✅ 情感沉浸——沉默力量大于运镜·倾听者的表情变化需要静止
KB规则ID: M-MOT-01(固定成立·倾听者的沉默不需要运镜干扰)

情绪匹配: 情绪值=0→-1(倾听·微沉) · 运镜强度=S0 · 差值≤1 ✅
空间约束: ✅ 实验台间通道·无运动

无动机静态检测: 属于"情感沉浸"例外 → ✅ 沉默反应镜头
```

### 镜#8 | 档案摔桌 | 28-32s | 动态 | seq⑨

```
运镜类型: 手持轻微晃动(0.3x·±2cm) / 手持类-微晃
速度参数: 0.3x · 速度档S2
方向: 固定位置·呼吸式位移(-2cm~+2cm)
起止状态: 微晃(摔倒前的静默紧张) → 手持微晃持续(0.3x·档案摔落) → 微晃(冲击余韵)
时长: 4s (微晃4s)

KB规则ID: M-MOT-01(运动动机="砰"的冲击·手持=秩序被打破) · M-MOT-02(速度匹配冲击·+3→S2·冲击的物理表达) · M-MOV-12(运动增强张力·固定位微晃创造不稳定感)

情绪匹配: 情绪值=+3(冲击·爆发) · 运镜强度=S2 · 差值≈1 ✅
说明: 全剧第一次脱离三脚架固定——科学实验室的"秩序"被旧档案暴力打破·手持微晃=冲击的物理表达
空间约束: ✅ 固定位置微晃·±2cm范围·无穿墙风险

动机检查: ✅ 场景需要"不安/临场感"→手持成立 ✅
```

### 镜#9 | 照片并排 | 32-36s | 静态 | seq⑩

```
运镜类型: 固定(S0) / 静态
静态例外: ✅ 信息密集——两张照片+红连接线+绿文字·观众需要自行完成比对
KB规则ID: M-20R-05(直接切换比移动镜头更经济·"让观众自己发现"=默奇准则)

情绪匹配: 情绪值=+1(认知·确证) · 运镜强度=S0 · 差值≈1 ✅
空间约束: ✅ 工作台上方·无运动

无动机静态检测: 属于"信息密集"例外 → ✅ 观众需要自行完成视觉比对
```

### 镜#10 | Vincent"同一只手" | 36-39s | 动态 | seq⑪

```
运镜类型: 极慢推近(0.1x) / 线性运动-推近类
速度参数: 0.1x · 速度档S1
方向: 推近(~3cm)
起止状态: 静止(胸部以上·直视) → 极慢推近(0.1x·2s) → 静止(双眼·结论落地)
时长: 3s (推近2s + 静止1s)
三段式: M-20R-07 静→动→静 ✅

KB规则ID: M-20R-07(三段公式) · M-MOT-02(速度=情感落地速度·结论的重量→0.1x) · M-MOV-04(向前运动强调主体重要性·结论句=全场最重要台词之一)

情绪匹配: 情绪值=+2(结论的沉重) · 运镜强度=S1 · 差值≈1 ✅
说明: 情绪高潮但运镜极慢——反差设计·用慢速强化"同一只手"的确认分量·非错位
空间约束: ✅ 推近路径<3cm·工作台前无遮挡

动机检查: ✅ 情绪高潮·结论值得推近 ✅
```

### 镜#11 | 摇臂升起·窗外 | 39-45s | 动态 | seq⑫

```
运镜类型: 缓慢升起·摇臂上升(0.2x匀速) / 复合运动-升降类
速度参数: 0.2x匀速 · 速度档S2
方向: 上升~1.5m (起点桌面~90cm→终点窗高~240cm)
起止状态: 静止(照片·1s) → 匀速上升(0.2x·4s·肩→百叶窗→窗外) → 静止(城市全景·1s)
时长: 6s (静止1s + 上升4s + 静止1s)
三段式: M-20R-07 静→动→静 ✅
三层空间过渡: 微距(<0.5m·照片) → 中景(~1.5m·Vincent肩剪影) → 远景(>500m·城市)

KB规则ID: M-20R-07(三段公式) · M-CRN-05(升降机·反向应用·从个别到宏观) · M-MOT-04(速度约束·空间深度>5m→≤3.0x·0.2x合规) · M-20R-15(起幅照片构图平衡+落幅城市全景平衡)

情绪匹配: 情绪值=+1(释放·维度拓展) · 运镜强度=S2 · 差值≈1 ✅
空间约束: ✅ 上升路径沿走道·起点~90cm→终点~240cm<天花板~300cm·路径无遮挡·不穿墙

动机检查: ✅ 默奇"情感51%"——从微观证据到宏观世界的维度拓展·情绪释放
全剧最长单镜(6s)·唯一长镜头·唯一升降运动
```

### 镜#12 | Miguel"Rico" | 45-48s | 动态 | seq⑬

```
运镜类型: 极慢推近(0.1x) / 线性运动-推近类
速度参数: 0.1x · 速度档S1
方向: 推近(~3cm)
起止状态: 静止(胸部以上·盯照片) → 极慢推近(0.1x·2s) → 静止(眼睛·名字出口)
时长: 3s (推近2s + 静止1s)
三段式: M-20R-07 静→动→静 ✅

KB规则ID: M-20R-07(三段公式) · M-MOT-02(速度=名字的压迫不是冲是压·0.1x) · M-MOV-04(向前运动强调"Rico"这个名字的重量)

情绪匹配: 情绪值=+2(名字的冲击·突然拉近) · 运镜强度=S1 · 差值≈1 ⚠️ 反差设计
说明: 情绪冲击但运镜极慢——"Rico"名字的压迫感用慢速推进而非冲刺·慢=逃不开的重量
空间约束: ✅ 推近路径<3cm·窗前区域空间充足

动机检查: ✅ 名字的冲击值得推近·揭示Miguel面部表情变化(M-MOV-03)
```

### 镜#12.5 | Miguel凝固 | 48-50s | 静态 | seq⑭

```
运镜类型: 固定(S0) · 绝对静止 / 静态
静态例外: ✅ 情感沉浸——"名字落地后的凝固"·绝对静止强化冲击余韵
KB规则ID: M-MOT-01(固定成立·凝固不需要运镜)

情绪匹配: 情绪值=-1(凝固·沉默中的沉重) · 运镜强度=S0 · 差值≈1 ✅
空间约束: ✅ 实验台间通道·无运动

无动机静态检测: 属于"情感沉浸"例外 → ✅ 表情凝固瞬间·运镜会破坏张力
```

### 镜#13 | Miguel右手ECU | 50-53s | 准静态 | seq⑮

```
运镜类型: 固定+呼吸式位移(±0.5cm·0.1x) / 手持/特殊-伪静态(呼吸微动)
速度参数: 0.1x · 速度档S0-S1
方向: 无方向·随机微位移
起止状态: 微颤(手的紧张→0.5s) → 持续微颤(2s·身体内化"Rico") → 静止(最终静止·0.5s)

KB规则ID: M-MOT-01(运动动机=身体本能反应·紧张微颤) · M-MOT-02(速度匹配情绪·-2沉重→微颤0.1x·不是大幅晃动是压抑的微) · M-MOV-12(运动增强张力·微动比静止更紧张)

情绪匹配: 情绪值=-2(内化·身体认知) · 运镜强度=S0-S1 · 差值≈1 ✅
空间约束: ✅ 微动范围<1cm·窗前区域无风险

动机检查: ✅ 身体的紧张→微颤0.1x·不是无动机晃动
P-FAL-09检查: 微动范围极小(±0.5cm)·非极端运动形变 ✅
```

### 镜#14 | 弹头灯灭 | 53-56s | 静态 | seq⑯

```
运镜类型: 固定(S0) · 绝对静止 / 静态
静态例外: ✅ 信息密集——光消失过程(3200K→暗红→深红→消失)是叙事本身
KB规则ID: M-MOT-01(固定成立·见证光的死亡需要绝对静止) · M-20R-05(直截了当的固定比运动更有效)

情绪匹配: 情绪值=-2(终结·光的死亡) · 运镜强度=S0 · 差值=0 ✅
空间约束: ✅ 载物台前·无运动

无动机静态检测: 属于"信息密集"例外 → ✅ 光消失过程本身即叙事·非信息密集=情感沉浸
叙事闭环: 镜#1弹头ECU起于固定→极慢推近·镜#14弹头ECU以固定·绝对静止终结
```

### 镜#15 | 光残余·悬念 | 56-58s | 静态 | seq⑰

```
运镜类型: 固定(S0) · 绝对静止 / 静态
静态例外: ✅ 情感沉浸——光的余韵·悬念·黑暗有层次
KB规则ID: M-MOT-01(固定成立·余韵不需要运镜)

情绪匹配: 情绪值=-3(余韵·虚无) · 运镜强度=S0 · 差值=0 ✅
空间约束: ✅ 窗前地板·无运动

无动机静态检测: 属于"情感沉浸"例外 → ✅ 悬念收束·绝对静止是最好的余韵
```

---

## Step D: 运镜序列节奏检查

### 速度分布统计

```
速度档统计(17镜):
  S0(固定·绝对静止): 镜#2·#3·#6·#7.5·#9·#12.5·#14·#15 = 8镜 → 47%
  S0-S1(近静止·呼吸微动): 镜#13 = 1镜 → 6%
  S1(极慢·0.1x): 镜#1·#7·#10·#12 = 4镜 → 24%
  S1-S2(中慢·0.15x): 镜#4 = 1镜 → 6%
  S2(慢·0.2x-0.3x): 镜#5·#8·#11 = 3镜 → 18%
  S3+(中+) : 0镜 → 0%

判定: S0主导(47%) · S1+S2合计约47% · 无S3+快速运动
  ✅ 任何一档未超过40%上限? 47% > 40% ⚠️
  说明: 鉴证科实验室是对话/调查场景·大比例固定符合叙事需求·非速度单一问题
  鉴证场景特征: 近景主导(53%)·固定+极慢推近占71%·全场景无快速运动
  → 场景一致性可接受·不触发阻断
```

### 相邻跳跃检测

```
速度档序列: S1→S0→S0→S1-S2→S2→S0→S1→S0→S2→S0→S1→S2→S1→S0→S0-S1→S0→S0

相邻差:
  ①(S1)→②(S0): 1级 ✅
  ②(S0)→③(S0): 0级 ✅
  ③(S0)→④(S1-S2): 1.5级 ✅
  ④(S1-S2)→⑤(S2): 0.5级 ✅
  ⑤(S2)→⑥(S0): 2级 ✅
  ⑥(S0)→⑦(S1): 1级 ✅
  ⑦(S1)→⑧(S0): 1级 ✅   (7.5 S0是Miguel反应镜·中性插入)
  ⑧(S0)→⑨(S2): 2级 ✅   (从反应→冲击·合理提升)
  ⑨(S2)→⑩(S0): 2级 ✅   (冲击→暂停比对·2级跳跃可接受)
  ⑩(S0)→⑪(S1): 1级 ✅
  ⑪(S1)→⑫(S2): 1级 ✅
  ⑫(S2)→⑬(S1): 1级 ✅
  ⑬(S1)→⑭(S0): 1级 ✅
  ⑭(S0)→⑮(S0-S1): 0.5级 ✅
  ⑮(S0-S1)→⑯(S0): 0.5级 ✅
  ⑯(S0)→⑰(S0): 0级 ✅

结论: 无≥4级跳跃 ✅·最大跳跃2级(⑤→⑥·⑧→⑨·⑨→⑩)·均在安全范围内
```

### 呼吸波形分析

```
全场景速度波形(17镜·58秒):

S2   ─     ┌─┐         ┌─┐
     │     │ │         │ │
S1   ┌─┐   │ │ ┌─┐   ┌─┘ └─┐
     │ │   │ │ │ │   │       │
S0  ─┘ └───┘ └─┘ └───┘       └─────────

波形特征:
  三段呼吸节奏:
    第1波(0-14s·#1→#4): S1→S0→S0→S1-S2 — 慢起·拾升·冷开场
    第2波(14-39s·#5→#11): S2→S0→S1→S0→S2→S0→S1 — 起伏·主对话波浪
    第3波(39-58s·#12→#17): S2→S1→S0→S1-S0→S0→S0 — 衰减·收束

判定: ✅ 形成清晰的呼吸波形·非方波/直线
  - 上升沿: 渐变(非骤升·最大单步=2级)
  - 衰减: 平缓(末段5镜从S1→S0-S1→S0·非骤降)
  - 两极分化检查: S0(静态)47% + S3+无(极快)0% = 47% < 60% ✅ 不缺中间节奏层
```

### 运镜类型多样性分析

```
推近类(极慢+慢): #1·#4·#7·#10·#12 = 5镜 → 29%
横移类(跟拍): #5 = 1镜 → 6%
升降类(摇臂): #11 = 1镜 → 6%
手持类(微晃): #8·#13 = 2镜 → 12%
固定/静态: #2·#3·#6·#7.5·#9·#12.5·#14·#15 = 8镜 → 47%

多样性判定:
  ✅ 使用了4种主要运镜类型(推近·横移·升降·手持)+静态
  ❌ 无旋转运动(摇镜/环绕/荷兰角)——鉴证场景不需要·叙事合理
  ❌ 无复合运动(变速/变焦/甩入甩出)——鉴证场景不需要·叙事合理

推近类占比29%·全部为极慢(0.1x)或慢(0.15x)·速度一致性好
```

---

## 空间约束总表

```
空间可行性: ✅ 全部17镜运镜路径在可拍摄空间内·无穿墙·无禁入区入侵
P-FAL-06(窄空间横移): ✅ 镜#5横移空间宽度~2.5m>1.5m·深度~8m>3m·合规
速度约束(M-MOT-04): ✅ 最大速度0.3x(镜#8)·远低于空间深度>5m对应的上限3.0x
推近深度: ✅ 最大推近路径<6cm(镜#4)·远小于空间可支撑范围
上升高度: ✅ 镜#11上升~1.5m·终点~240cm<天花板~300cm·安全余量~60cm
手持微晃: ✅ 镜#8(±2cm)·镜#13(±0.5cm)·均为安全幅度
```

---

## §6 结构化TIME_SKELETON输出

> **必填:** 以下YAML块直接映射到 TIME_SKELETON。在Shot Architect的segments_camera基础上补充movement和transition字段。

### §6.1 segments_movement 映射

```yaml
segments_movement:
  - segment_id: "①"
    time_range: [0, 4]
    movement: "极慢推近(0.1x)"
    movement_speed_tier: "S1"
    direction: "推近~3cm"
    duration_sec: 2
    three_part: "静(2s)→动(2s)→静(0s)"  # 终点静止即段结束
    start_state: "静止·弹头全貌"
    end_state: "静止·弹头膛线纹路"
    kb_rule_ids:
      - "M-20R-07"
      - "M-MOT-04"
      - "M-20R-15"

  - segment_id: "②"
    time_range: [4, 7]
    movement: "固定"
    movement_speed_tier: "S0"
    static_exception: "信息密集(三层深度)"
    kb_rule_ids:
      - "M-MOT-01"
      - "M-20R-05"

  - segment_id: "③"
    time_range: [7, 10]
    movement: "固定"
    movement_speed_tier: "S0"
    static_exception: "信息密集(屏幕数据·五张照片+比对线)"
    kb_rule_ids:
      - "M-20R-05"

  - segment_id: "④"
    time_range: [10, 14]
    movement: "慢推近(0.15x)"
    movement_speed_tier: "S1-S2"
    direction: "推近~6cm"
    duration_sec: 3
    three_part: "静(0s)→动(3s)→静(1s)"
    start_state: "静止·胸部以上"
    end_state: "静止·双眼·双色温交汇"
    kb_rule_ids:
      - "M-20R-07"
      - "M-MOT-02"
      - "M-MOV-04"

  - segment_id: "⑤"
    time_range: [14, 18]
    movement: "稳定器横移跟拍(0.2x)"
    movement_speed_tier: "S2"
    direction: "右横移~1.5m"
    duration_sec: 4
    three_part: "静(0s)→动(4s)→静(0s)"  # 起止计入相邻段
    start_state: "门内侧·Miguel剪影+走廊暖光"
    end_state: "工作台前·冷白顶光浮现"
    path: "沿实验台间通道直线横移"
    kb_rule_ids:
      - "M-20R-13"
      - "M-MOT-01"
      - "M-MOV-02"
      - "M-MOT-03"

  - segment_id: "⑥"
    time_range: [18, 21]
    movement: "固定"
    movement_speed_tier: "S0"
    static_exception: "情感沉浸(Miguel消化证据)"
    kb_rule_ids:
      - "M-MOT-01"

  - segment_id: "⑦"
    time_range: [21, 26]
    movement: "极慢推近(0.1x)·对白呼吸节奏"
    movement_speed_tier: "S1"
    direction: "推近~5cm"
    duration_sec: 4
    three_part: "静(0s)→动(1-2s推近→暂停→3-4s继续推近)→静(5s静止落地)"
    start_state: "静止·胸部以上"
    end_state: "静止·眼镜反射蓝光+手指点膛线"
    rhythm: "配合对白呼吸·M-MOT-07"
    kb_rule_ids:
      - "M-20R-07"
      - "M-MOT-02"
      - "M-MOT-07"
      - "M-MOV-03"

  - segment_id: "⑧"
    time_range: [26, 28]
    movement: "固定"
    movement_speed_tier: "S0"
    static_exception: "情感沉浸(Miguel倾听·沉默力量)"
    kb_rule_ids:
      - "M-MOT-01"

  - segment_id: "⑨"
    time_range: [28, 32]
    movement: "手持微晃(0.3x·±2cm)"
    movement_speed_tier: "S2"
    direction: "固定位置·呼吸式位移"
    duration_sec: 4
    start_state: "微晃持续"
    end_state: "微晃→静止过渡"
    kb_rule_ids:
      - "M-MOT-01"
      - "M-MOT-02"
      - "M-MOV-12"

  - segment_id: "⑩"
    time_range: [32, 36]
    movement: "固定"
    movement_speed_tier: "S0"
    static_exception: "信息密集(照片并排·观众自行比对)"
    kb_rule_ids:
      - "M-20R-05"

  - segment_id: "⑪"
    time_range: [36, 39]
    movement: "极慢推近(0.1x)"
    movement_speed_tier: "S1"
    direction: "推近~3cm"
    duration_sec: 2
    three_part: "静(0s)→动(2s)→静(1s)"
    start_state: "静止·胸部以上·直视"
    end_state: "静止·双眼·结论落地"
    kb_rule_ids:
      - "M-20R-07"
      - "M-MOT-02"
      - "M-MOV-04"

  - segment_id: "⑫"
    time_range: [39, 45]
    movement: "摇臂缓慢升起(0.2x匀速)"
    movement_speed_tier: "S2"
    direction: "上升~1.5m(90cm→240cm)"
    duration_sec: 5
    three_part: "静(1s·照片)→动(4s·匀速上升)→静(1s·窗外城市)"
    start_state: "静止·桌面俯角~45°·照片"
    end_state: "静止·眼平水平0°·窗外城市全景"
    path: "沿走道垂直上升·三层空间(微距→中景→远景)"
    kb_rule_ids:
      - "M-20R-07"
      - "M-CRN-05"
      - "M-MOT-04"
      - "M-20R-15"

  - segment_id: "⑬"
    time_range: [45, 48]
    movement: "极慢推近(0.1x)"
    movement_speed_tier: "S1"
    direction: "推近~3cm"
    duration_sec: 2
    three_part: "静(0s)→动(2s)→静(1s)"
    start_state: "静止·胸部以上·盯照片"
    end_state: "静止·眼睛·名字出口"
    kb_rule_ids:
      - "M-20R-07"
      - "M-MOT-02"
      - "M-MOV-04"

  - segment_id: "⑭"
    time_range: [48, 50]
    movement: "固定"
    movement_speed_tier: "S0"
    static_exception: "情感沉浸(名字落地后的凝固·绝对静止)"
    kb_rule_ids:
      - "M-MOT-01"

  - segment_id: "⑮"
    time_range: [50, 53]
    movement: "固定+呼吸式位移(±0.5cm·0.1x)"
    movement_speed_tier: "S0-S1"
    direction: "无方向·随机微位移"
    duration_sec: 3
    start_state: "微颤(手的紧张)"
    end_state: "静止(内化完成)"
    kb_rule_ids:
      - "M-MOT-01"
      - "M-MOT-02"

  - segment_id: "⑯"
    time_range: [53, 56]
    movement: "固定"
    movement_speed_tier: "S0"
    static_exception: "信息密集(光消失过程本身就是叙事)"
    kb_rule_ids:
      - "M-MOT-01"

  - segment_id: "⑰"
    time_range: [56, 58]
    movement: "固定"
    movement_speed_tier: "S0"
    static_exception: "情感沉浸(光的余韵·悬念)"
    kb_rule_ids:
      - "M-MOT-01"
```

### §6.2 segments_transitions 映射

```yaml
segments_transitions:
  # --- 第1波:冷开场 ---
  - transition_id: "①→②"
    from_segment: "①"
    to_segment: "②"
    transition_type: "硬切"
    time_range: [4, 4]
    path: "直接切换·弹头→Vincent面部"
    speed: "瞬时"
    visual_change: "全黑背景的弹头ECU→三层深度的工作台CU"
    kb_rule_ids: []

  - transition_id: "②→③"
    from_segment: "②"
    to_segment: "③"
    transition_type: "硬切"
    time_range: [7, 7]
    path: "直接切换"
    speed: "瞬时"
    visual_change: "Vincent面部→屏幕数据特写"
    kb_rule_ids: []

  - transition_id: "③→④"
    from_segment: "③"
    to_segment: "④"
    transition_type: "硬切"
    time_range: [10, 10]
    path: "直接切换"
    speed: "瞬时"
    visual_change: "屏幕数据→Vincent接电话"
    kb_rule_ids: []

  - transition_id: "④→⑤"
    from_segment: "④"
    to_segment: "⑤"
    transition_type: "硬切"
    time_range: [14, 14]
    path: "直接切换"
    speed: "瞬时"
    visual_change: "Vincent近景→门侧MLS·Miguel入室"
    kb_rule_ids: []

  # --- 第2波:主对话 ---
  - transition_id: "⑤→⑥"
    from_segment: "⑤"
    to_segment: "⑥"
    transition_type: "硬切"
    time_range: [18, 18]
    path: "直接切换"
    speed: "瞬时"
    visual_change: "MLS横移终点→Miguel CU·内反拍"
    kb_rule_ids: []

  - transition_id: "⑥→⑦"
    from_segment: "⑥"
    to_segment: "⑦"
    transition_type: "硬切"
    time_range: [21, 21]
    path: "直接切换·正反打"
    speed: "瞬时"
    visual_change: "Miguel CU→Vincent CU·微仰拍"
    kb_rule_ids:
      - "E-MTC-03"   # 视线匹配

  - transition_id: "⑦→⑧"
    from_segment: "⑦"
    to_segment: "⑧"
    transition_type: "硬切"
    time_range: [26, 26]
    path: "直接切换·正反打"
    speed: "瞬时"
    visual_change: "Vincent揭示→Miguel沉默反应"
    kb_rule_ids:
      - "E-MTC-03"

  - transition_id: "⑧→⑨"
    from_segment: "⑧"
    to_segment: "⑨"
    transition_type: "硬切"
    time_range: [28, 28]
    path: "直接切换"
    speed: "瞬时"
    visual_change: "Miguel沉默→Vincent摔档案·广角MS"
    kb_rule_ids: []

  - transition_id: "⑨→⑩"
    from_segment: "⑨"
    to_segment: "⑩"
    transition_type: "硬切"
    time_range: [32, 32]
    path: "直接切换"
    speed: "瞬时"
    visual_change: "广角MS→桌面ECU·照片比对"
    kb_rule_ids: []

  - transition_id: "⑩→⑪"
    from_segment: "⑩"
    to_segment: "⑪"
    transition_type: "硬切"
    time_range: [36, 36]
    path: "直接切换"
    speed: "瞬时"
    visual_change: "照片ECU→Vincent直视CU"
    kb_rule_ids: []

  - transition_id: "⑪→⑫"
    from_segment: "⑪"
    to_segment: "⑫"
    transition_type: "硬切"
    time_range: [39, 39]
    path: "直接切换·位置匹配"
    speed: "瞬时"
    visual_change: "Vincent CU→桌上照片(摇臂起点)·位置匹配过渡"
    kb_rule_ids:
      - "E-MTC-01"   # 位置匹配

  # --- 第3波:衰减收束 ---
  - transition_id: "⑫→⑬"
    from_segment: "⑫"
    to_segment: "⑬"
    transition_type: "硬切"
    time_range: [45, 45]
    path: "直接切换·空中→地面"
    speed: "瞬时"
    visual_change: "窗外城市全景→Miguel面部CU"
    kb_rule_ids: []

  - transition_id: "⑬→⑭"
    from_segment: "⑬"
    to_segment: "⑭"
    transition_type: "硬切"
    time_range: [48, 48]
    path: "直接切换"
    speed: "瞬时"
    visual_change: "Miguel CU→Miguel凝固(同机位·时间跳跃)"
    kb_rule_ids:
      - "E-MTC-02"   # 动作匹配(凝固前→凝固后)

  - transition_id: "⑭→⑮"
    from_segment: "⑭"
    to_segment: "⑮"
    transition_type: "硬切"
    time_range: [50, 50]
    path: "直接切换"
    speed: "瞬时"
    visual_change: "Miguel凝固→右手ECU·插入"
    kb_rule_ids: []

  - transition_id: "⑮→⑯"
    from_segment: "⑮"
    to_segment: "⑯"
    transition_type: "硬切"
    time_range: [53, 53]
    path: "直接切换"
    speed: "瞬时"
    visual_change: "Miguel手ECU→弹头ECU(叙事闭环)"
    kb_rule_ids: []

  - transition_id: "⑯→⑰"
    from_segment: "⑯"
    to_segment: "⑰"
    transition_type: "硬切"
    time_range: [56, 56]
    path: "直接切换"
    speed: "瞬时"
    visual_change: "弹头灯灭全黑→地板光栅残余"
    kb_rule_ids: []
```

### §6.3 frames_movement 映射

```yaml
frames_movement:
  # ═══ seq① : 镜#1 弹头ECU 极慢推近 ═══
  - sec: 0
    global_sec: 0
    camera_position: "①"
    movement: "静止(首帧锁定·弹头全貌)"

  - sec: 1
    global_sec: 1
    camera_position: "①"
    movement: "静止(蓄力)"

  - sec: 2
    global_sec: 2
    camera_position: "①"
    movement: "极慢推近中(0.1x·膛线纹路渐显)"

  - sec: 3
    global_sec: 3
    camera_position: "①"
    movement: "极慢推近→静止(弹头弧面占画面~15%)"

  # ═══ seq② : 镜#2 Vincent近景 固定 ═══
  - sec: 4
    global_sec: 4
    camera_position: "②"
    movement: "固定(三层深度信息密集)"

  - sec: 5
    global_sec: 5
    camera_position: "②"
    movement: "固定"

  - sec: 6
    global_sec: 6
    camera_position: "②"
    movement: "固定"

  # ═══ seq③ : 镜#3 屏幕特写 固定 ═══
  - sec: 7
    global_sec: 7
    camera_position: "③"
    movement: "固定(屏幕数据密集)"

  - sec: 8
    global_sec: 8
    camera_position: "③"
    movement: "固定"

  - sec: 9
    global_sec: 9
    camera_position: "③"
    movement: "固定"

  # ═══ seq④ : 镜#4 Vincent打电话 慢推近 ═══
  - sec: 10
    global_sec: 10
    camera_position: "④"
    movement: "慢推近开始(0.15x·拿手机)"

  - sec: 11
    global_sec: 11
    camera_position: "④"
    movement: "慢推近中(0.15x·等待音·推至双色温交汇)"

  - sec: 12
    global_sec: 12
    camera_position: "④"
    movement: "推近至颧骨(0.15x→静止过渡)"

  - sec: 13
    global_sec: 13
    camera_position: "④"
    movement: "静止(对白·双眼双色温)"

  # ═══ seq⑤ : 镜#5 Miguel入室 横移跟拍 ═══
  - sec: 14
    global_sec: 14
    camera_position: "⑤"
    movement: "跟拍横移开始(0.2x·Miguel推门)"

  - sec: 15
    global_sec: 15
    camera_position: "⑤"
    movement: "跟拍横移(0.2x·Miguel沿走道进入)"

  - sec: 16
    global_sec: 16
    camera_position: "⑤"
    movement: "跟拍横移(0.2x·暖光→冷光过渡)"

  - sec: 17
    global_sec: 17
    camera_position: "⑤"
    movement: "跟拍横移→静止(Miguel走到工作台前)"

  # ═══ seq⑥ : 镜#6 Miguel内反拍 固定 ═══
  - sec: 18
    global_sec: 18
    camera_position: "⑥"
    movement: "固定(Miguel消化证据·情感沉浸)"

  - sec: 19
    global_sec: 19
    camera_position: "⑥"
    movement: "固定"

  - sec: 20
    global_sec: 20
    camera_position: "⑥"
    movement: "固定"

  # ═══ seq⑦ : 镜#7 Vincent"签名" 极慢推近·对白呼吸 ═══
  - sec: 21
    global_sec: 21
    camera_position: "⑦"
    movement: "极慢推近开始(0.1x·胸部以上→上移)"

  - sec: 22
    global_sec: 22
    camera_position: "⑦"
    movement: "极慢推近中(0.1x·推向眼镜和手指)"

  - sec: 23
    global_sec: 23
    camera_position: "⑦"
    movement: "推近暂停(配合对白停顿)"

  - sec: 24
    global_sec: 24
    camera_position: "⑦"
    movement: "极慢推近继续(0.1x·继续上推)"

  - sec: 25
    global_sec: 25
    camera_position: "⑦"
    movement: "静止(落地·眼镜反射蓝光+手指点膛线)"

  # ═══ seq⑧ : 镜#7.5 Miguel倾听 固定 ═══
  - sec: 26
    global_sec: 26
    camera_position: "⑧"
    movement: "固定(沉默倾听·低照度)"

  - sec: 27
    global_sec: 27
    camera_position: "⑧"
    movement: "固定"

  # ═══ seq⑨ : 镜#8 档案摔桌 手持微晃 ═══
  - sec: 28
    global_sec: 28
    camera_position: "⑨"
    movement: "手持微晃(0.3x·±2cm·秩序被打破)"

  - sec: 29
    global_sec: 29
    camera_position: "⑨"
    movement: "手持微晃(0.3x·档案摔落冲击)"

  - sec: 30
    global_sec: 30
    camera_position: "⑨"
    movement: "手持微晃(0.3x·冲击余韵)"

  - sec: 31
    global_sec: 31
    camera_position: "⑨"
    movement: "手持微晃→静止过渡"

  # ═══ seq⑩ : 镜#9 照片并排 固定 ═══
  - sec: 32
    global_sec: 32
    camera_position: "⑩"
    movement: "固定(绝对静止·信息密集)"
  - sec: 33
    global_sec: 33
    camera_position: "⑩"
    movement: "固定"
  - sec: 34
    global_sec: 34
    camera_position: "⑩"
    movement: "固定"
  - sec: 35
    global_sec: 35
    camera_position: "⑩"
    movement: "固定"

  # ═══ seq⑪ : 镜#10 Vincent"同一只手" 极慢推近 ═══
  - sec: 36
    global_sec: 36
    camera_position: "⑪"
    movement: "极慢推近开始(0.1x·"同一只手")"

  - sec: 37
    global_sec: 37
    camera_position: "⑪"
    movement: "推近至眼睛(0.1x→静止过渡·"同一种……")"

  - sec: 38
    global_sec: 38
    camera_position: "⑪"
    movement: "静止(结论落地·"审美")"

  # ═══ seq⑫ : 镜#11 摇臂升起 ═══
  - sec: 39
    global_sec: 39
    camera_position: "⑫"
    movement: "静止(起点·照片·摇臂预备)"

  - sec: 40
    global_sec: 40
    camera_position: "⑫"
    movement: "匀速上升(0.2x·过Vincent肩剪影)"

  - sec: 41
    global_sec: 41
    camera_position: "⑫"
    movement: "匀速上升(0.2x·过百叶窗框)"

  - sec: 42
    global_sec: 42
    camera_position: "⑫"
    movement: "匀速上升(0.2x·窗外城市浮现)"

  - sec: 43
    global_sec: 43
    camera_position: "⑫"
    movement: "匀速上升(0.2x→减速过渡)"

  - sec: 44
    global_sec: 44
    camera_position: "⑫"
    movement: "静止(终点·窗外城市全景·落幅平衡)"

  # ═══ seq⑬ : 镜#12 Miguel"Rico" 极慢推近 ═══
  - sec: 45
    global_sec: 45
    camera_position: "⑬"
    movement: "极慢推近开始(0.1x·盯照片)"

  - sec: 46
    global_sec: 46
    camera_position: "⑬"
    movement: "推近至眼睛(0.1x→减速·"Rico")"

  - sec: 47
    global_sec: 47
    camera_position: "⑬"
    movement: "静止(名字出口·半明半暗)"

  # ═══ seq⑭ : 镜#12.5 Miguel凝固 固定 ═══
  - sec: 48
    global_sec: 48
    camera_position: "⑭"
    movement: "固定(绝对静止·凝固)"

  - sec: 49
    global_sec: 49
    camera_position: "⑭"
    movement: "固定"

  # ═══ seq⑮ : 镜#13 Miguel右手 固定+呼吸位移 ═══
  - sec: 50
    global_sec: 50
    camera_position: "⑮"
    movement: "固定+微呼吸(±0.5cm·手部紧张微颤)"

  - sec: 51
    global_sec: 51
    camera_position: "⑮"
    movement: "固定+微呼吸(±0.5cm·内化"Rico")"

  - sec: 52
    global_sec: 52
    camera_position: "⑮"
    movement: "静止(内化完成·手部静止)"

  # ═══ seq⑯ : 镜#14 弹头灯灭 固定 ═══
  - sec: 53
    global_sec: 53
    camera_position: "⑯"
    movement: "固定(见证·弹头·琥珀光)"

  - sec: 54
    global_sec: 54
    camera_position: "⑯"
    movement: "固定(丝灯冷却·暗红)"

  - sec: 55
    global_sec: 55
    camera_position: "⑯"
    movement: "固定(深红→消失·全黑)"

  # ═══ seq⑰ : 镜#15 光残余·悬念 固定 ═══
  - sec: 56
    global_sec: 56
    camera_position: "⑰"
    movement: "固定(地板光栅·暖金)"

  - sec: 57
    global_sec: 57
    camera_position: "⑰"
    movement: "固定(光栅衰减·淡黄→消失)"
```

---

## 下游消费契约清单

```
Movement Designer v2.0 输出结构:
  ┌─ 运镜设计报告 (自由文本·人类审核) — 以上全部
  └─ §6 结构化块 (YAML·storyboard_planner §2G机械组装)
        ├─ §6.1 segments_movement    → TIME_SKELETON.segments[].camera.movement (17段·全部覆盖)
        ├─ §6.2 segments_transitions → TIME_SKELETON.segments[transition]       (15个段间过渡·全部硬切)
        └─ §6.3 frames_movement      → TIME_SKELETON.frames[].hard.camera_movement (58帧·逐秒覆盖)

必填字段检查:
  ✅ shot_id (segment_id) — 全部覆盖
  ✅ movement_type — 全部标注
  ✅ speed_tier (movement_speed_tier) — 全部量化(S0-S2)
  ✅ transition_type — 全部标注(硬切)
  ✅ 无缺失必填字段 → 调度器§-5.3检查通过
```

---

## 文件引用索引

| 来源 | 文件 |
|------|------|
| Movement Designer 指令 | 02_Agent/movement_designer_v2.0.md |
| Agent Quick Reference | 04_共享/agent_quick_ref_v1.0.md |
| Context Package EP13 | 02_Agent/output/CONTEXT_PACKAGE_EP13.md |
| Shot Architect 场景设计(上游) | 02_Agent/output/EP13_S2_SCENE_DESIGNER_v7.1.md |
| 空间地图(§C) | 02_Agent/output/EP13_ANCHOR_BASELINE.md |
| 图片审计 | 02_Agent/output/EP13_IMAGE_AUDIT.md |
| KB深度检索(运镜域) | 03_知识库/03_导演知识库_v5.0.md §5 (M-MOT/M-MOV/M-20R/M-LEN) |
| TIME_SKELETON规范 | 04_共享/TIME_SKELETON_spec.md §2 |

---

> **Movement Designer v2.0 · 2026-07-08 · 独立上下文·仅运镜决策**
> **不包含:** 机位类型/覆盖策略(Shot Architect负责) · 构图/光影/色彩(Composition Designer负责)
> **KB域:** §5 运镜与运动 (M-MOT/M-MOV/M-20R/M-LEN) · 引用规则数: 15条
> **运镜覆盖率:** 17/17镜全部设计 · 动态8镜(展开全参数) · 静态9镜(标注例外类别)
> **静态例外分布:** 信息密集(4镜:#2·#3·#9·#14) · 情感沉浸(4镜:#6·#7.5·#12.5·#15) · 准静态呼吸(1镜:#13)
> **速度范围:** S0-S2 · 无S3+运动 · 场景特征匹配(鉴证/对话·近景主导·71%固定+极慢推近)
