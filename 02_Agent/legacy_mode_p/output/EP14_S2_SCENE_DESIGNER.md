# Scene Designer v1.0 -- EP14 S2 机位+构图光影设计

> **Agent:** Scene Designer v1.0 (合并式·Shot+Comp)
> **剧本:** 枪王 EP14《调查》场景2: 贫民窟巷道+轿车 (午后)
> **complexity_level:** M
> **判定依据:** F1 N_spaces=2 · F2 N_speakers=1+VO · F3 N_dialogue=1+VO · F4 R_static=≈57% · F5 Has_motion=true · F6 N_subspaces=2
> **执行分支:** 3B M-Level流程 (Shot+Comp合并·运镜独立)
> **输出目标:** `D:\JianyingPro\tsc\导演系统_v5\02_Agent\output\EP14_S2_SCENE_DESIGNER.md`

---

# §0 场景类型判定 + 空间坐标系 (三域共享·只写一次)

## 场景类型判定

```
场景分析:
  [x] 有角色>=2 — Pedro(目击者·气息独白)+Rico+金丝眼镜男(车内二人)
  [x] 有躲藏/窥视/悬疑要素 — 追球→目击交易→躲藏→偷看→差点被发现→驶离
  [x] 环境叙事主导 — 贫民窟巷道+轿车内部·两个强视觉特征空间
  [x] 无传统对话 — Pedro独白式气息声·Rico无对白·VO可选

判定: 悬疑主导混合格式
核心场景类型: 悬疑/偷窥 (A-SUS系列规则主导)
KB章节路由: §2.3(悬疑)+§4(构图)+§6(光影)+§8(视觉结构)
```

场景类型=[悬疑/偷窥混合] · 角色数=[3:Pedro+Rico+金丝眼镜男] · complexity=[M]
KB章节=[§2.3悬疑+§4构图+§6光影+§8视觉结构]

## 空间坐标系 (一次性·三域共享)

### 空间A: 贫民窟窄巷 (外景·午后·阴天)

```
空间尺寸: 纵深~20m x 宽度<2m x 高度~6-8m(两侧墙面至一线天)
面积: ~40m² (狭长·不可横向调度)
地面: 碎石+干泥·微坡向巷内倾斜·积水洼散布

关键建筑元素:
  巷口入口(格1): 外部道路与巷内碎石交界·两侧砖墙夹道·入口上方电线
  巷内纵深(格2): 全深~20m·宽度<2m·两侧墙面透视收窄·一点透视强烈
  巷内回看巷口(格3): 从巷内看向巷口·逆光视角·人物/车辆以剪影呈现
  左侧墙面(格4): 红砖裸露·水泥补丁·渗水痕迹·小窗铁栅栏·褪色涂鸦
  巷中段核心(格5): 最窄处·铸铁排水管贴墙·墙根青苔·碎石地面微坡
  右侧墙面(格6): 灰泥剥落·底层红砖显露·电表箱(距地~1.5m)
  碎石地面(格7): 碎石子+干泥·积水洼反射天光·杂草墙根交界
  仰视天空(格8): 两侧墙面间一线天·电线+晾衣绳横跨·阴灰天空
  巷尾出口(格9): 通向外街·两侧墙面收束

人物可放置区域(巷道):
  ① 巷口入口(站姿·1人·外部道路与巷内交界)
  ② 巷中段车道(站姿·1人·宽度<2m限制·轿车停靠后两侧缝隙<0.3m禁入)
  ③ 巷中段垃圾桶后(蹲姿·Pedro躲藏·距地~0m·宽~1m·遮蔽物)
  ④ 巷尾出口(站姿·1人·备用路径)
  ⑤ 墙根/排水管旁(蹲姿·次要躲藏位·空间逼仄)

180度线设定(巷道):
  关系线: Pedro(观察者) <-> 轿车/Rico(被观察者)
  轴线方向: 沿巷道纵深(巷口<->巷尾)
  轴线侧选择: A侧(巷道右侧·电表箱侧) — 右侧墙面有可辨识视觉元素(电表箱+灰泥剥落)
  选取理由: 全部机位保持在轴线同侧·Pedro视线方向(看巷口)始终统一

光源物理锚点(巷道):
  光源1[巷口逆光]: 午后自然光·巷口方向·逆光·过曝1-2档·~4500K暖金
    锚点: 参考图格1(巷口入口)·格3(巷内回看巷口)
  光源2[阴天漫射天空光]: 头顶一线天·阴灰·漫射·~5500-6500K冷灰
    锚点: 参考图格8(仰视天空·一线天+电线)
  光源3[积水反射光]: 地面积水洼反射天光·微弱第二反射源
    锚点: 参考图格7(碎石地面微距)

空间约束速查:
  禁入区: 墙壁内部·排水管内部·电表箱内部·车辆引擎区域
  窄区: 巷道宽度<2m -> 禁止横移(P-FAL-06)·仅限推近/拉远/固定
  车辆停靠后两侧缝隙<0.3m -> 人物无法侧身通过
  推断空间: 垃圾桶(金属圆桶·高~1m·锈蚀·参考图未覆盖->推断属性·标注LEVEL-C)
```

### 空间B: 轿车内部 (午后·暖金侧逆光)

```
空间类型: 老旧黑色轿车前排(驾驶座+副驾驶座)
空间尺寸: ~1.5m宽(前排) x ~1.2m深 x ~1.1m高
面积: ~1.8m² (极度受限·不可站姿)

关键元素:
  挡风玻璃(左上/右上格): 沙尘覆盖·干涸水渍斑痕·天然滤镜+画框
  后视镜(右上格): 反射后排+车后街景·空间纵深叠加
  方向盘(左下格): 老化皮质·龟裂纹理·顶部积尘·驾驶座前方
  中控台+换挡杆(右中格): 灰尘覆盖·油光包浆·球头细微划痕
  皮质座椅(中下/右下格): 黑色皮革极度老化·龟裂褶皱·接缝积尘
  仪表台(右下格): 表面均匀灰尘·暖金光照下的光切面

人物可放置区域(轿车内):
  ⑥ 驾驶座(坐姿·1人·金丝眼镜男·方向盘后)
  ⑦ 副驾驶座(坐姿·1人·Rico)

180度线设定(轿车内):
  关系线: Rico <-> 金丝眼镜男(副驾驶<->驾驶座)
  轴线方向: 车宽方向(左右)
  轴线侧选择: 车外侧(从副驾驶窗外/挡风玻璃外向车内看)
  选取理由: 外部视角保持神秘感·挡风玻璃沙尘作为天然视觉滤镜·内反拍用于交换特写

光源物理锚点(轿车内):
  光源4[侧逆暖金]: 从驾驶座左侧/前方斜射入车内·侧逆光·~3200-4000K·高反差明暗切割
    锚点: 轿车内参考图(中上/右中格)·侧逆光与强对比+暖色基调描述
  光源5[挡风玻璃透射光]: 外部午后光透过挡风玻璃沙尘层·衰减为漫射暖金
    锚点: 轿车内参考图(左上格)·挡风玻璃POV

空间约束速查(轿车内):
  极度受限 -> 仅限固定/极慢推近/微摇
  人物间距约0.6-0.8m -> 中控区上方为交换动作核心区
  后排空置 -> 可用作虚拟摄影机位
```

---

# §1 场景级静态比例预判

```
逐镜预判(7镜):
  镜#1(追球入巷·6s): Pedro追球跑动 -> 动态主导
  镜#2(Pedro POV·发现轿车·6s): Pedro静止注视·车内人物微动 -> 静态主导
  镜#3(躲垃圾桶后·5s): Pedro蹲伏躲藏·探头 -> 静态主导
  镜#4(偷看POV·交易·6s): 隐匿视角·车内交换动作 -> 静态主导
  镜#5(Rico转头·6s): Rico转头·扫描视线 -> 静态主导
  镜#6(Pedro反应·5s): Pedro缩回·恐惧表情 -> 静态主导
  镜#7(轿车驶离·5s): 轿车驶离 -> 动态元素·固定机位

静态镜: #2+#3+#4+#5+#6 = 5/7镜 = 71.4%
动态镜: #1+#7 = 2/7镜 = 28.6%

判定: 静态占比 71.4% < 80% -> 静态快速通道不触发
但运镜域已委托Movement Designer独立设计·本报告不包含运镜决策
```

---

# §2 KB加载 (场景类型路由·Shot+Comp合并加载)

```
场景类型: 悬疑/偷窥 -> 加载以下KB子集:

机位域:
  §2.3 悬疑(10条) -> 加载: A-SUS-01(后退)·A-SUS-02(未知之惧)·A-SUS-03(紧张期待)·A-SUS-05(放大空间)·A-SUS-09(恐惧延时释放)

构图域:
  §4.1 Arijon构图 -> 加载: C-AJS-03(小窗口法)·C-AJS-05(黑暗压光法)
  §4.2 Framed Ink构图 -> 加载: C-FI-01(负空间)·C-FI-02(深度分层)·C-FI-06(剪影轮廓)·C-FI-14(嵌套构图)·C-FI-16(隐藏揭示)·C-FI-17(POV代入)
  §4.2b 负空间系统 -> 加载: C-FI2-NS-03(剪影负空间协同)·C-FI2-NS-07(明暗面积比)·C-FI2-NS-16(正负空间比例张力)·C-FI2-NS-21(负空间暗示画外威胁)·C-FI2-NS-27(前景遮挡+负空间多层深度)
  §4.4 深度透视 -> 加载: C-DEP-01(线性透视一点透视)

光影域:
  §6.1 布光核心 -> 加载: L-3PT-02(侧光立体)·L-3PT-04(阴影硬度)·L-3PT-05(阴影硬度与氛围匹配)
  §6.2 色温 -> 加载: L-CT-01(色温情绪)·L-CT-02(混合色温法则)
  §6.3 灯光场景 -> 加载: L-SCN-02(紧张/悬疑场景)
  §6.4 色彩法则 -> 加载: COL-PRI-01(互补色)·COL-PRI-02(冷暖深度)·COL-PRI-03(主色调统一)

视觉结构:
  §8.2 对比亲和 -> 加载: VS-CA-01~06(视觉对比=戏剧冲突·变化安全等级·波浪法则)
  §8.4 空间深度 -> 加载: VS-SPA-01(三层深度)·VS-SPA-04(色调对比分离前后景)

P0安全规则始终加载:
  GEN-01~05/09(通用铁律)·D-TRI-01~03(180度线)·M-MOT-03(空间可行性)
  画布宪法七条铁律·P-STATE §1(已验证模式)·P-STATE §2(P-FAL-01~10)

运镜域KB (M-MOT·M-MOV·M-LEN系列): 由Movement Designer独立加载·本报告不加载
```

---

# §B-S1 覆盖策略选择

```
场景类型: 悬疑/偷窥 -> 采用悬疑5机位关键模板 + POV偷窥专项机位:

选定机位(7镜·叙事流):
  镜#1 全景建立: 巷口入口·追球入巷·空间引入+动作主体
  镜#2 POV主观: Pedro第一人称视角·发现轿车·目击交易(透过车窗)
  镜#3 低角度躲藏: 垃圾桶侧方·Pedro蹲伏躲藏·儿童视角压迫感
  镜#4 偷窥遮蔽POV: 垃圾桶后方缝隙/桶沿上方·观众通过Pedro眼睛看·前景遮挡增强代入
  镜#5 车内外反打: 透过挡风玻璃/车窗·Rico转头扫描·威胁源主观化
  镜#6 极端特写反应: Pedro面部ECU·恐惧峰值·身体反应
  镜#7 远景收束: 巷内回看巷口·轿车驶离·Pedro前景锚点·空间释放

覆盖完整性: 7镜覆盖 建立(1)+POV(2)+躲藏(1)+偷窥(1)+威胁(1)+反应(1)+收束(1)
未使用机位: 不设再交代镜头(悬疑场景·Murch情感优先于空间重确认)
```

---

# §B-S2 逐镜机位设计 + §B-S4 逐镜构图设计 + §B-S5 逐镜光影设计

> 三域逐镜合并展开。§B-S3(运镜域)委托Movement Designer独立执行。
> 每镜: 机位参数 + 构图参数 + 光影参数 + 三域协调约束。

---

## 镜#1: 追球入巷·巷口猛停 [0-6s]

【叙事节拍】Pedro踢足球→球滚入窄巷→Pedro追球跑入巷道→足球停在巷中段碎石地上→Pedro抬头看见巷口外停着的黑色轿车→急停。

### 机位设计

| 参数 | 值 |
|------|-----|
| 机位类型 | 低角度建立+跟拍(空间引入·动作主体) |
| 景别 | 远景(起始) -> 中景(终点·Pedro停步后) |
| 焦距 | 24mm等效(广角·建立全纵深空间) |
| 景深 | 深景深f/8(全层清晰·巷道纵深需全焦) |
| 角度 | 超低角度(~30cm高·起始) -> 升高至~1.0m(Pedro眼高·终点) |
| 轴线侧 | A侧(巷道右侧) |
| 机位位置 | 巷口入口处(区域①)·面向巷内·初始距地~30cm·终点距地~1.0m |
| 视线方向 | Pedro看巷口方向(画面纵深)·轿车在远景巷口 |
| 覆盖功能 | 建立(空间引入)+推进(动作主体)+揭示(轿车出现——悬念钩子) |
| 空间约束 | 机位在巷口入口(区域①)·沿巷道中轴线行进·不穿墙不悬空 |
| KB规则ID | D-TRI-01 · A-SUS-02(未知之惧·轿车初现为暗色剪影) · C-DEP-01(一点透视) |

### 构图设计

```
主体位置: 足球(画面下三分之一中央·0-3s·弹跳滚动) -> Pedro背影(画面中央·3-5s·全身·追球) -> Pedro静止+轿车远景剪影(画面中央·5-6s)

景别递进: 远景(0-3s·碎石地面占画面2/3) -> 中全景(3-5s·Pedro全身) -> 中景(5-6s·Pedro背影+远处轿车)

深度层次(3层·VS-SPA-01):
  前景层: 碎石地面(清晰·粒径纹理·积水洼·0-5s占据画面下1/2到1/3)
  中景层: 足球(清晰·0-3s) -> Pedro全身(清晰·3-6s·背对镜头·瘦小身形)
  背景层: 巷口暖亮逆光过曝区(6s时轿车暗色剪影出现在其中·制造悬念)

主导线条: 纵深汇聚线(巷道两侧墙面透视收窄·指向巷口·C-DEP-01) + 对角线(石阶斜线·0-2s·足球滚入路径)

负空间: 画面顶部一线天(窄条·灰白天空+电线横跨)·巷口暖亮过曝区(Pedro静止后·轿车出现前的"期待空间")

焦距: 24mm等效(广角·深景深·夸张纵深)
构图风格: 开放构图(巷口方向) -> 收敛式(Pedro停步·巷框围合)
KB规则ID: C-FI-02(深度分层) · C-FI-06(后期Pedro/轿车剪影) · C-DEP-01(线性透视) · VS-SPA-01(三层深度)
```

### 光影设计

```
主光源: 午后自然光·巷口方向·逆光·过曝1-2档·~4500K暖金·硬光
  锚点: 参考图格1(巷口入口)·格3(巷内回看巷口逆光)

辅助光: 阴天漫射天空光·头顶一线天·~5500K冷灰·柔光·巷内散射填充
  锚点: 参考图格8(仰视天空·一线天+电线)

光比: 中高1:5(0-3s·巷内暗部:巷口过曝) -> 极高1:10+(5-6s·轿车剪影:巷口过曝·Pedro边缘暖色轮廓光)

光影焦点:
  0-2s: 足球表面反光(微弱·漫射光照亮球面皮革纹理)
  3-5s: Pedro身体边缘逆光剪影(极细暖色轮廓光·头发+肩膀+手臂边缘)
  5-6s: 轿车暗色块在巷口暖亮背景中(最大明暗对比·悬念锚点)

视线引导路径: 碎石地面纹理 -> 足球 -> Pedro背影 -> 巷口暖亮区 -> 轿车暗色剪影

阴影处理: Pedro全身逆光剪影(3-6s·身体为中间调·无内部细节)·足球影子在碎石上拉长·闭塞阴影[需要·墙根+排水管缝隙]

边缘光: [需要] Pedro头发+肩膀极细暖色边缘光(~4500K)·与巷内冷灰暗部形成分离

色彩策略: 冷暖对冲 — 巷口暖金(4500K) vs 巷内冷灰(5500K)·Pedro剪影=中性暗色过渡
主色调: 冷暖对冲(巷内冷灰为主·巷口暖金为趣味点)
饱和度: 低饱和(阴天巷内·灰调) + 高饱和暖色(巷口过曝区·小面积·COL-PRI-02冷暖深度)
KB规则ID: L-3PT-05(阴影硬度匹配氛围·硬光巷口vs柔光巷内) · L-CT-02(混合色温法则) · COL-PRI-02(冷暖构建景深)
跨镜色温一致性: 4500K巷口+5500K巷内与场景锚点基线一致
```

### 三域协调

```
机位-构图: 低角度(30cm)起拍强化碎石地面为前景层·24mm广角夸张巷道纵深(一点透视)
机位-光影: 逆光机位(面向巷口) -> Pedro/轿车以剪影呈现·光源锚点在画面纵深方向
构图-光影: 冷暖对冲的色温分布天然形成前景(冷灰)-中景(暗色过渡)-背景(暖金)三层分离
```

---

## 镜#2: Pedro POV·发现轿车·目击交易 [6-12s]

【叙事节拍】硬切至Pedro主观视角。从他的眼高(~1.2m)看向巷口方向。黑色轿车停在巷口外道路。透过布满沙尘的挡风玻璃: Rico(副驾驶·侧脸)和金丝眼镜男(驾驶座)正在快速交换——信封换手机。

### 机位设计

| 参数 | 值 |
|------|-----|
| 机位类型 | POV主观视角(Pedro第一人称·透过挡风玻璃看车内) |
| 景别 | 中全景(Pedro所见·巷道纵深+轿车+挡风玻璃框) |
| 焦距 | 35mm等效(中焦·自然视野·略压缩空间) |
| 景深 | 中景深f/5.6(巷道中段至轿车均需可辨识) |
| 角度 | 眼平(~1.2m·Pedro身高) |
| 轴线侧 | A侧(巷道右侧·POV继承Pedro位置) |
| 机位位置 | 巷中段·Pedro站立位置(区域②·距轿车~12-15m)·虚拟POV |
| 视线方向 | Pedro看巷口方向·轿车在画面中央远景·挡风玻璃框定车内人物 |
| 覆盖功能 | 揭示(首次呈现车内交易·信息差制造——观众比Pedro看得更清楚) |
| 空间约束 | 虚拟POV·无物理机位约束·继承Pedro眼高位 |
| KB规则ID | C-FI-17(POV代入) · A-SUS-02(未知之惧·信息局部呈现) · C-FI-14(嵌套构图·挡风玻璃为画框) |

### 构图设计

```
主体位置: 轿车(画面中央远景·暗色块在巷口暖亮逆光中) -> 挡风玻璃框内(画面次级焦点·Rico侧脸右·司机左)

景别: 中全景(Pedro所见视野·巷道纵深压缩至轿车挡风玻璃框)

深度层次(4层·C-FI-02):
  前景层: 巷中段碎石地面(画面下方1/4·清晰)·头顶电线(画面顶部·细线横跨)
  中景前层: 巷道两侧墙面(渐进收窄·左侧红砖水泥补丁·右侧灰泥剥落·清晰→渐暗)
  中景后层: 轿车车体(暗色剪影·车身轮廓清晰·车窗反光)
  背景层: 巷口暖亮逆光过曝区(轿车后方)·挡风玻璃透出的车内暖金区域(画面中最温暖的色块)

主导线条: 纵深汇聚线(巷道墙面->轿车)·挡风玻璃水平+垂直框线(天然画框·C-FI-14)

负空间: 巷口暖亮过曝区(轿车周围·威胁存在的"光环")·挡风玻璃沙尘纹理(半透明遮挡·信息过滤器)

焦距: 35mm等效(中焦·Pedro自然视野)
构图风格: POV代入(前景无Pedro身体部位·纯主观) + 嵌套构图(巷道=外框·挡风玻璃=内框·C-FI-14)
KB规则ID: C-FI-17(POV代入) · C-FI-14(嵌套构图·景框中景框) · C-FI2-NS-21(负空间暗示画外威胁·Pedro在画外) · A-SUS-03(紧张期待·固定视角强迫等待)
```

### 光影设计

```
主光源(巷道): 巷口逆光(~4500K·过曝·轿车为暗色剪影·挡风玻璃边缘暖金)
  锚点: 参考图格1+格3

主光源(车内): 侧逆暖金(~3500K·从驾驶座左侧射入·照亮Rico侧脸和交换中的手)
  锚点: 轿车内参考图·侧逆光与强对比

辅助光: 阴天漫射天空光(~5500K·巷内散射·填充巷道地面+墙面+轿车外部)
  锚点: 参考图格8

光影结构(双色温系统·L-CT-02):
  巷内空间: 冷灰基调(5500K阴天漫射·中低调1:3)
  轿车外部: 暗色剪影(车体在巷口4500K逆光中)
  轿车内部: 暖金高反差(3500K侧逆光·1:10+光比·车内暗部深黑)

光影焦点:
  主焦点: 挡风玻璃内暖金光切面——Rico侧脸颧骨+司机金丝眼镜框反光(画面中最温暖·最亮的区域)
  次焦点: 信封/手机在交换瞬间被暖金光切面照亮(中控区上方)

视线引导路径: 碎石地面 -> 巷道墙面纵深 -> 轿车暗色剪影 -> 挡风玻璃 -> 暖金车内光区 -> 交换的手

色彩策略: 三重色温并置 — 巷内冷灰(5500K·大面积) + 巷口暖金(4500K·中面积) + 车内暖金(3500K·小面积·最高饱和)
  冷暖深度: 冷灰巷内(后退感) + 暖金车内(前进感) — 观众视线被"拉"入车内暖光区(COL-PRI-02)
主色调: 冷暖三重并置(冷灰为主色调·暖金为视觉焦点色)
饱和度: 低(巷内冷灰) + 中(巷口暖金) + 高(车内暖金·胶片质感)
KB规则ID: L-CT-02(混合色温法则·三重色温有叙事理由) · L-SCN-02(悬疑场景·高反差+暖金侧逆光) · COL-PRI-01(互补色对比·暖金vs冷灰) · COL-PRI-02(冷暖构建景深)
跨镜色温一致性: 延续镜#1三色温系统·巷口4500K+巷内5500K+新增车内3500K
```

### 三域协调

```
机位-构图: POV机位(Pedro眼高1.2m) -> 轿车处于微俯视角度·强化Pedro=观察者地位
机位-光影: POV虚拟机位位于巷内·天然处于冷灰(5500K)照度下·车内暖金(3500K)形成"暖色口袋"在冷色画框中
构图-光影: 嵌套构图(巷道框->挡风玻璃框)配合三重色温·每层画框有独立色温标识
```

---

## 镜#3: 躲藏·垃圾桶后探头 [12-17s]

【叙事节拍】Pedro看到车内交易后迅速躲到垃圾桶后方。蹲下·身体紧缩·手指扒住桶沿。极缓慢探头——半张脸从桶沿上方露出·一只眼窥视巷口方向。

### 机位设计

| 参数 | 值 |
|------|-----|
| 机位类型 | 低角度躲藏反应(垃圾桶侧方·OTS Pedro身后) |
| 景别 | 中景(Pedro蹲姿+垃圾桶关系) |
| 焦距 | 35mm等效(中焦·同时框入Pedro+垃圾桶+巷口背景) |
| 景深 | 中景深f/5.6(Pedro身体清晰·背景巷口可辨识) |
| 角度 | 低角度微仰(~0.6m高·Pedro蹲姿腰部高度·仰视他探头动作) |
| 轴线侧 | A侧(巷道右侧) |
| 机位位置 | 垃圾桶侧前方(区域③边界)·距Pedro~1.5m·距墙面>0.3m |
| 视线方向 | Pedro看巷口(画右上方·轿车方向)·视线方向一致 |
| 覆盖功能 | 反应(躲藏动作)+过渡(从目击到隐匿) |
| 空间约束 | 机位在垃圾桶侧前·不穿桶·距墙面>0.3m·宽度<2m限制OK |
| KB规则ID | A-SUS-01(后退躲藏=恐惧)·A-SUS-09(恐惧延时释放·先躲藏再缓慢探头) · C-FI-17(POV代入) |

### 构图设计

```
主体位置: Pedro蹲姿(画面中左·身体缩成团->探头后半张脸从桶沿上方露出) + 垃圾桶(画面右·大型暗色块·锈蚀金属质感)

景别: 中景(垃圾桶+Pedro关系完整呈现·巷口远景在背景)

深度层次(3层):
  前景层: 碎石地面(画面下方1/5·清晰·微坡)
  中景层: Pedro蹲姿(清晰·身体紧缩·手指扒桶沿·探头后半张脸露出) + 垃圾桶(清晰·金属圆桶·锈蚀纹理·画面右侧锚点)
  背景层: 巷口暖亮逆光(轿车暗色剪影仍在·提醒威胁未消除)·巷中段墙面冷灰渐变

主导线条: 竖线(垃圾桶圆柱形·Pedro垂直蹲姿) + 横线(桶沿水平线·遮挡基线·Pedro面部浮现的边界)

负空间: Pedro身体左侧巷内空间(暗部·向巷尾延伸·C-FI2-NS-21暗示后方还有退路)·巷口暖亮区(远景·威胁存在)

焦距: 35mm等效
构图风格: 低角度躲藏(仰拍增强压迫感·C-FI-15) + 遮挡渐进(桶沿从完全遮挡到半遮面·C-FI-16隐藏与揭示)
KB规则ID: C-FI-02(深度分层) · C-FI-16(隐藏与揭示·桶沿=信息控制界面) · C-FI-15(低角度仰拍·增强压迫) · A-SUS-03(紧张期待·缓慢探头)
```

### 光影设计

```
主光源: 阴天漫射天空光(~5500K·巷内·头顶一线天·柔光·均匀照明)
  锚点: 参考图格8

第二光源: 巷口逆光(~4500K·远景·在Pedro探头时面部边缘形成极微弱暖色轮廓)
  锚点: 参考图格3

光比: 中低1:3(巷内散射光均匀·无明显强对比·Pedro面部受光均匀但照度低)

光影焦点: Pedro探头后半张脸(从桶沿暗部浮现·面部在散射光中呈中间调)·手指扒桶沿的指关节(受力发白·局部高光)

视线引导路径: 垃圾桶(暗色块) -> Pedro手指(桶沿·指关节高光) -> Pedro面部(从桶沿后浮现) -> Pedro眼睛视线方向(巷口·轿车)

阴影处理: 垃圾桶内部(完全不可见·深黑)·Pedro蹲姿身体(桶后·暗部)·桶沿下方阴影(Pedro面部刚探头时在暗部·逐渐进入散射光区)
  闭塞阴影: [需要] 桶与墙之间的缝隙·排水管凹陷处

边缘光: [可选] Pedro探头后·面部边缘极微弱暖色轮廓光(~4500K·巷口远光·若有若无)

色彩策略: 巷内冷灰单色基调(5500K均匀散射·低饱和) + 远景巷口暖金(小面积·4500K·色彩对比点)
主色调: 冷灰单色(垃圾桶锈蚀橙棕色为次级色彩焦点)
饱和度: 低饱和(阴天散射光·色彩被削弱)
KB规则ID: L-3PT-04(阴天=大光源=柔阴影) · L-CT-02(混合色温·冷暖双色温有理) · COL-PRI-03(冷灰主色调统一)
跨镜色温一致性: 巷内5500K+巷口4500K一致
```

### 三域协调

```
机位-构图: 低角度(0.6m)仰拍 -> Pedro虽小但以仰角增强画面存在感·垃圾桶=大型前景锚点
机位-光影: 机位在垃圾桶侧前·天然处于巷内散射光(5500K)下·Pedro从桶后暗部探头进入散射光区=视觉揭示
构图-光影: 桶沿遮挡控制光影分区——桶沿下方=暗部(躲藏)·桶沿上方=散射光区(暴露·危险)
```

---

## 镜#4: 偷看POV·交易细节 [17-23s]

【叙事节拍】切换至Pedro偷看视角。前景:垃圾桶沿(极度虚化·深色块占据画面下方1/4)。中景:透过垃圾桶与墙壁之间的缝隙(或桶沿上方)看轿车挡风玻璃。车内:Rico和金丝眼镜男正在交换信封/手机——暖金侧逆光中的手部动作。

### 机位设计

| 参数 | 值 |
|------|-----|
| 机位类型 | 偷窥遮蔽POV(垃圾桶后方·通过缝隙/桶沿上方窥视) |
| 景别 | 中景(轿车挡风玻璃+车内人物·经前景遮挡裁切) |
| 焦距 | 50mm等效(中长焦·压缩空间·聚焦车内交换动作) |
| 景深 | 浅景深f/2.8(聚焦车内人物·前景桶沿+背景巷口虚化) |
| 角度 | 微仰(~0.8m·Pedro蹲姿眼高·从桶后向上窥视) |
| 轴线侧 | A侧(巷道右侧·继承Pedro位置) |
| 机位位置 | 垃圾桶后方(区域③)·紧贴桶身·虚拟POV |
| 视线方向 | Pedro看巷口方向·轿车在画面中景·通过桶与墙间隙/桶沿上方窥视 |
| 覆盖功能 | 揭示(交易细节)+代入(观众=Pedro·信息受限)+悬念(看得见但看不清) |
| 空间约束 | 虚拟POV在垃圾桶后·不穿桶·视线路径通过桶与墙间隙或桶沿上方 |
| KB规则ID | C-FI-17(POV代入·前景体现角色身体部位) · C-AJS-03(小窗口法·前景遮挡只留小画面) · C-FI-16(隐藏与揭示) · A-SUS-02(未知之惧·信息不完整) |

### 构图设计

```
主体位置: 轿车挡风玻璃框(画面中上部·通过缝隙/桶沿上方可见) + Rico侧脸+司机+交换的手(挡风玻璃框内)

景别: 中景(挡风玻璃框内人物·前景遮挡裁切视野)

深度层次(4层·VS-SPA-01):
  前景层(极近): 垃圾桶沿(极度虚化·深色块占据画面下方1/4-1/3·锈蚀纹理模糊成色块) or 墙壁边缘(画面左侧·深色竖条·虚化)
  前景层(近): 巷中段碎石地面(画面下方·虚化·空间过渡)
  中景层: 轿车挡风玻璃框(清晰·沙尘纹理可见·框内Rico侧脸+司机+交换的手)
  背景层: 巷口暖亮逆光(轿车后方·过曝·挡风玻璃框外)

主导线条: 桶沿水平弧线(画面底部·深色虚化)·挡风玻璃水平框线(中景·清晰画框)·Rico手臂斜线(指向中控区·动作线·C-FI-09对角线)

负空间: 前景遮挡形成的暗部(桶沿深色块=安全感/隐藏·C-FI2-NS-27前景遮挡+负空间多层深度)·缝隙/桶沿上方透出的画面(信息窗口·C-AJS-03小窗口法)

焦距: 50mm等效(中长焦·压缩空间·聚焦车内)
构图风格: 极度遮蔽POV(前景遮挡>画面30%·观众与Pedro共享视野限制) + 小窗口法(C-AJS-03·前景暗部包围小面积亮部)
KB规则ID: C-AJS-03(小窗口法·前景大面积暗部·小面积透出主体) · C-FI-17(POV代入) · C-FI-14(嵌套构图·桶沿+挡风玻璃=双重画框) · C-FI2-NS-27(前景遮挡+负空间创造多层深度)
```

### 光影设计

```
主光源(车内): 侧逆暖金(~3500K·从驾驶座左侧射入·照亮交换的手和Rico侧脸)
  锚点: 轿车内参考图·侧逆光与强对比

第二光源(巷口): 巷口逆光(~4500K·过曝·轿车后方·形成挡风玻璃框外的亮背景)
  锚点: 参考图格1+格3

第三光源(巷内): 阴天漫射天空光(~5500K·照亮前景垃圾桶沿+碎石地面·极弱)
  锚点: 参考图格8

光影结构:
  前景(桶沿/墙边): 深暗色块(在巷内散射光中呈深灰·照度极低)
  中景(挡风玻璃框内): 暖金高反差(3500K侧逆光·1:10+光比·交换的手为画面最亮区域)
  背景(巷口): 暖金过曝(~4500K·挡风玻璃框外)

光影焦点: 交换中的信封和手机在暖金光切面中——手部皮肤纹理·信封纸面质感·手机屏幕边缘反光(画面唯一暖色高亮区)

视线引导路径: 前景暗部(桶沿/墙边·"安全"的暗处) -> 挡风玻璃框(视觉窗口) -> 暖金车内光区 -> 交换的手(最亮焦点)

阴影处理: 前景遮挡形成大面积暗部(深黑·闭塞)·车内暗部(座椅缝隙·中控台凹陷·纯黑)·挡风玻璃沙尘散射暖光(柔化高光边缘)
  闭塞阴影: [需要] 桶与墙间隙·车内暗角

色彩策略: 三重色温嵌套 — 前景冷灰暗部(5500K·大面积·"隐藏") + 中景暖金焦点(3500K·小面积·"秘密") + 背景暖金过曝(4500K·最小面积·"外部世界")
主色调: 冷灰暗部包裹暖金核心(类似chiaroscuro的色温版本)
饱和度: 前=极低(暗部无色彩)·中=高(暖金·胶片质感)·后=中(巷口过曝·色彩被过曝冲淡)
KB规则ID: L-SCN-02(悬疑场景·硬光单侧+高光比) · COL-PRI-02(冷暖构建景深·冷退暖进) · C-AJS-05(黑暗压光法·暗部占2/3·突出亮部关键区) · COL-PRI-01(互补色对比)
跨镜色温一致性: 三重色温锚点一致
```

### 三域协调

```
机位-构图: 偷窥POV的极度遮蔽(>30%画面被遮挡) -> 观众信息受限=Pedro信息受限·悬念共享
机位-光影: 机位在桶后暗部(冷灰低照度) -> 中景车内暖金形成"视觉牵引"——观众眼睛自动跳向最亮的暖色区
构图-光影: 小窗口法(C-AJS-03)配合黑暗压光法(C-AJS-05) -> 前景暗部包围亮部窗口=自然视线引导
```

---

## 镜#5: Rico转头·差点发现 [23-29s]

【叙事节拍】车内。Rico完成交换后·突然转头看向车窗外(巷口/Pedro方向)。他的侧脸占画面左三分线——暖金侧逆光照亮颧骨和眼窝·另半脸在深黑阴影中·颈肌紧绷·视线扫描。POV切换:Rico透过挡风玻璃看到巷口碎石地面上的足球影子。他盯着影子看了几秒·然后转回头。差一点就发现Pedro。

### 机位设计

| 参数 | 值 |
|------|-----|
| 机位类型 | 车内近景(副驾驶侧·Rico侧脸)+POV主观(Rico所见巷口) |
| 景别 | 近景(0-3s·Rico侧脸) -> POV中全景(3-5s·挡风玻璃外巷口) -> 极端特写(5-6s·碎石地上足球影子) |
| 焦距 | 50mm(近景·压缩空间) -> 35mm(POV·自然视野) -> 85mm(影子ECU·极限特写) |
| 景深 | 浅f/2.8(Rico侧脸) -> 中f/5.6(POV巷口) -> 浅f/2.8(影子ECU) |
| 角度 | 眼平(0-3s·车内·Rico眼高) -> Rico第一人称视角(3-5s·透过挡风玻璃) -> 微俯(5-6s·影子在地面) |
| 轴线侧 | 车外侧(0-3s·Rico侧脸) -> 无(POV·主观不适用轴线) -> A侧(5-6s·影子在地面) |
| 机位位置 | 轿车内副驾驶侧(距Rico~0.5m·0-3s) -> 虚拟Rico视点(透过挡风玻璃·3-5s) -> 巷口碎石地面(ECU·5-6s) |
| 视线方向 | Rico看左(车窗外=巷口方向·0-3s) -> POV扫描巷口(3-5s) -> 定格足球影子(5-6s) |
| 覆盖功能 | 威胁识别(差点发现——全场景情绪峰值)+悬念升至最高 |
| 空间约束 | 车内CU不穿车体·POV为虚拟视点·影子ECU在地面·全部合规 |
| KB规则ID | A-SUS-09(恐惧延时释放·先给安全感再打破·交换刚完成->突然转头) · A-SUS-02(未知之惧·Rico在看什么?Pedro是否被发现?) · C-FI-17(POV代入) · C-FI-06(剪影·球的影子) |

### 构图设计

```
主体位置(按段):
  0-3s: Rico侧脸(画面左三分线·看画右=巷口方向·暖金半面光)
  3-5s: POV巷口全景(挡风玻璃沙尘纹理为前景滤镜·巷口暖亮在画面右上·垃圾桶暗色块靠右墙·碎石地面)
  5-6s: 足球影子ECU(画面下三分之一中央·深色椭圆·碎石间隙透光)

景别递进: 近景(1人) -> POV中全景(环境扫描) -> 极端特写(线索发现)

深度层次(按段):
  近景段(2层): FG=挡风玻璃边缘(虚化暗框) + BG=Rico侧脸(清晰·暖金半面·明暗交界线沿鼻梁)
  POV段(3层): FG=挡风玻璃沙尘(半透明柔焦纹理·不动) + MG=巷口碎石地面+垃圾桶+墙面(清晰·扫描经过) + BG=巷外道路暖亮过曝
  影子段(2层): FG=碎石(清晰·粒径纹理·干泥填隙) + 影子=深色椭圆(占据画面下1/3·半影边缘过渡柔和)

主导线条: 斜线(Rico下颌线·0-3s) -> 水平线(巷口碎石地面·3-5s) -> 曲线(足球影子椭圆·5-6s·C-FI-09引导线)

负空间: 近景段=画面右侧(车窗外出画方向·留白·暗示Pedro在画外·C-FI2-NS-21)·POV段=巷口上方天空(过曝·空白)

焦距: 50mm->35mm->85mm等效
构图风格: 画中画(车窗框->挡风玻璃框) + 扫描式POV(水平扫视) + 收敛定格(影子ECU·节奏骤停)
KB规则ID: C-FI-16(隐藏与揭示·扫描中发现影子) · C-FI-06(剪影·球的影子=Pedro的替身) · C-FI-02(深度分层·每段独立空间结构) · A-SUS-03(紧张期待·扫描过程=悬念累积)
```

### 光影设计

```
光源系统(多段·按角色/空间切换):

近景段(0-3s·车内·Rico):
  主光源: 侧逆暖金(~3500K·从驾驶座左侧射入·硬光)
    Rico面部半明半暗——暖金高光:颧骨+眼窝+下颌线 / 深黑阴影:另半脸
  光比: 极高1:10+(暖金高光面:暗面·chiaroscuro效果)
  光影焦点: Rico颧骨暖金高光区+眼眶暗部(扫描式视线在光影中更具威胁感)
  色彩: 暖金单色(3500K·高饱和)·暗部纯黑

POV段(3-5s·挡风玻璃外·巷口):
  主光源: 巷口逆光(~4500K·过曝1-2档·硬光)
  填充光: 阴天漫射(~5500K·巷内碎石+墙面散射·柔光)
  光影焦点: 视线扫过的路径——碎石(散射光均匀)·垃圾桶(暗色剪影在暖亮背景中)·墙面灰泥剥落纹理
  色彩: 冷暖混合(巷口暖金4500K+巷内冷灰5500K)

影子段(5-6s·碎石地面·ECU):
  主光源: 巷口逆光(~4500K·投射足球影子)
  填充光: 阴天漫射(~5500K·碎石间隙透光·形成影内亮斑)
  光影焦点: 足球影子——深色椭圆·边缘半影过渡带柔和(柔光散射)·影内非纯黑(碎石间隙透射光·细小亮斑镶嵌·影调丰富)
  光比: 中低1:2(碎石:影子·柔光散射·非高反差)
  色彩: 中性灰度(碎石暖灰+影子深灰·无主导色温)

色彩策略(全镜): 色温随视角切换 — 3500K暖金(车内/威胁源) -> 4500K+5500K混合(外部世界) -> 中性灰度(线索定格)
  色温作为空间标识: 暖金=轿车内(秘密空间)·冷暖混合=巷道(过渡空间)·灰度=碎石地面(证据/真相空间)
主色调: 暖金(0-3s) -> 冷暖对冲(3-5s) -> 灰度(5-6s)
饱和度: 高(车内暖金) -> 中(POV混合) -> 低(影子灰度)
KB规则ID: L-3PT-02(侧光立体·Rico面部) · L-SCN-02(悬疑场景·硬光单侧+高光比+冷色边缘) · L-CT-02(混合色温·逐段切换有叙事理由) · COL-PRI-03(每段有独立主色调)
跨镜色温一致性: 3500K+4500K+5500K三色温与锚点基线一致
```

### 三域协调

```
机位-构图: 车内近景->POV->ECU的三段式机位+景别递进=威胁扫描的完整视觉弧线
机位-光影: 车内近景段(3500K暖金) -> POV段(冷暖混合) -> 影子段(灰度)·机位切换伴随色温切换·强化空间转换感知
构图-光影: Rico面部明暗交界线(chiaroscuro) + POV扫描的水平引导线 + 影子椭圆的视觉停顿·光影分区引导了每段构图的视线方向
悬念设计: 镜#4=Pedro看Rico(偷看) -> 镜#5=Rico看向Pedro方向(差点发现)·正反打POV建立"差点对视"的悬念张力
```

---

## 镜#6: Pedro反应·缩回·恐惧 [29-34s]

【叙事节拍】硬切回垃圾桶后。Pedro看到Rico转头——眼睛瞬间瞪大·身体本能地向后缩·背部撞到墙壁。面部极端特写:右半脸+右眼从桶沿上方急速下沉消失。然后极缓慢地再次探头——确认Rico是否还在看。一只眼睛重新出现在桶沿上方。恐惧未消。

### 机位设计

| 参数 | 值 |
|------|-----|
| 机位类型 | 极端特写反应(Pedro面部ECU+缩回避让动作) |
| 景别 | 极端特写(半张脸+一只眼) |
| 焦距 | 85mm等效(长焦·压缩空间·浅景深·聚焦眼部) |
| 景深 | 极浅f/2.0(聚焦眼睛·桶沿+背景完全虚化) |
| 角度 | 微仰拍(~0.6m·桶侧·Pedro蹲姿眼高) |
| 轴线侧 | A侧(巷道右侧) |
| 机位位置 | 垃圾桶侧前方(区域③边界)·距Pedro面部~0.5m |
| 视线方向 | Pedro看巷口(画右上方·轿车方向) -> 缩回(视线方向消失) -> 再次探出(看巷口·确认威胁) |
| 覆盖功能 | 情绪峰值反应(恐惧的视觉化·全场景Pedro首次完整面部ECU) |
| 空间约束 | 机位在垃圾桶侧前·距墙面>0.3m·不穿桶 |
| KB规则ID | A-SUS-01(后退缩回=恐惧) · A-SUS-09(恐惧延时释放·缩回后再次探头确认) · C-KTZ-02(特写亲密·观众与Pedro恐惧共鸣) |

### 构图设计

```
主体位置: Pedro右眼(画面左三分线上交点·视觉重心) -> 缩回时眼从画面下沉消失 -> 再次出现(同一位置·形成视觉回归)

景别: 极端特写

深度层次(2层·极简):
  前景层: 垃圾桶沿(极度虚化·深色模糊块占据画面下方1/3)
  中景层: Pedro面部(右半脸清晰·皮肤纹理+眼睫毛+瞳孔·左半脸在画面外/桶后)

主导线条: 垃圾桶沿水平弧线(画面底部·深色虚化)·Pedro颧骨斜线(指向眼睛)

负空间: 画面右侧暗部(巷内深处·Pedro视线方向·暗示轿车/威胁在画外·C-FI2-NS-21)·桶沿上方微光区(巷口远光渗透)

焦距: 85mm等效
构图风格: 极端遮挡(桶沿遮住75%面部+身体) + 极简(仅眼+半脸+桶沿虚化·C-FI2-NS-15环境简化凸显主体)
KB规则ID: C-FI-17(POV代入·前景体现角色身体部位) · C-FI2-NS-07(明暗面积比·暗部>70%) · C-FI2-NS-03(剪影负空间协同·桶沿深色块+眼睛亮部) · C-KTZ-02(特写亲密)
```

### 光影设计

```
主光源: 极弱巷内散射光(~5000K·头顶一线天经多重反射衰减·面部环境光极暗)
  锚点: 参考图格8

第二光源: 巷口远光(~4500K·在Pedro右眼瞳孔中形成针尖大小暖色高光点)
  锚点: 参考图格1+格3

光比: 极高1:8(面部环境光极暗:瞳孔高光点·绝大部分面部在阴影中)

光影焦点: Pedro右眼瞳孔中的针尖暖色高光点(画面中唯一的绝对亮部·~4500K暖色)

视线引导路径: 画面所有暗部 -> 瞳孔高光点(唯一亮部·观众视线被吸入瞳孔)

阴影处理: Pedro面部80%在阴影中·仅颧骨边缘+鼻梁侧翼有极微弱灰光(~5000K冷灰)·眼窝深黑·桶沿下方完全暗部
  闭塞阴影: [需要] 眼窝深处·桶与面部间隙

边缘光: [需要] Pedro颧骨+眼窝上沿极微弱冷灰边缘光(~5000K)·与暗部形成微弱分离·但远弱于瞳孔暖色高光点

色彩策略: 近乎单色(深灰+黑·去饱和)·唯一色彩=瞳孔暖色高光点(针尖大小·暖色在冷灰暗部中极其突出)
  -> 冷暖对比微型化: 整个画面只有针尖大的暖色(威胁的反射)+大面积冷灰暗部(Pedro的恐惧)
主色调: 极暗单色(冷灰·去饱和)
饱和度: 近零(阴影吞噬色彩·唯有瞳孔高光为高饱和暖色针尖)
KB规则ID: L-3PT-05(阴影硬度匹配氛围·柔光漫射=柔阴影·环境光极弱) · C-AJS-05(黑暗压光法·暗部>2/3·瞳孔高光为关键亮区) · COL-PRI-01(互补色对比·冷灰vs暖金针尖)
跨镜色温一致性: 5000K+4500K与锚点基线一致
```

### 三域协调

```
机位-构图: 85mm+极浅景深(f/2.0) -> 压缩空间·消除背景干扰·观众只能看眼睛
机位-光影: 机位在桶侧·桶沿遮挡大部分环境光 -> 面部在暗部·仅有远光在瞳孔中的反射
构图-光影: 黑暗压光(C-AJS-05)·明暗面积比>7:3(C-FI2-NS-07)·瞳孔高光=唯一视觉出口
情绪设计: 镜#5(Rico转头·威胁逼近) -> 镜#6(Pedro缩回·恐惧释放) = A-SUS-09恐惧延时释放的完整弧线
```

---

## 镜#7: 轿车驶离·Pedro前景锚点 [34-39s]

【叙事节拍】低角度·Pedro肩膀/头部在画面右前景(极度虚化/剪影)。中远景:黑色轿车发动·从巷口位置驶离——向巷尾方向(或侧向驶出画面)。轿车尾灯在巷口暖亮逆光中微微发光(红色点光源)。巷道恢复寂静。Pedro保持蹲姿·没有起身。最后一个画面停留在Pedro的背影和空荡的巷口。

### 机位设计

| 参数 | 值 |
|------|-----|
| 机位类型 | 远景收束+前景锚点(低角度·OTS Pedro·看巷口) |
| 景别 | 远景(巷道全纵深+Pedro前景剪影) |
| 焦距 | 24mm等效(广角·全纵深清晰·一点透视) |
| 景深 | 深景深f/8(全纵深·巷口至巷尾·前景Pedro至远景轿车) |
| 角度 | 低角度微仰(~0.5m·Pedro蹲姿肩高·仰视巷口) |
| 轴线侧 | A侧(巷道右侧) |
| 机位位置 | 巷中段·Pedro身后(区域②边界·垃圾桶后方~1m)·距地~0.5m |
| 视线方向 | Pedro看巷口(画面纵深)·轿车驶离方向 |
| 覆盖功能 | 收束(威胁离去)+情绪余韵(Pedro未起身=恐惧未消)+空间释放(轿车离开·巷道恢复日常) |
| 空间约束 | 机位在巷中段·在可站立区域内·低角度不穿墙·宽度<2m限制OK |
| KB规则ID | A-SUS-08(无路可逃的余韵·Pedro仍不敢动) · C-FI-06(Pedro前景剪影) · C-DEP-01(一点透视·巷道纵深) · C-FI2-NS-26(运动方向前方留白·轿车驶向巷口·前方暖亮空白) |

### 构图设计

```
主体位置: Pedro头部/肩膀(画面右下·前景剪影·极度虚化或暗色块) + 轿车(画面中央远景·暗色块·从巷口暖亮区驶向侧方·逐渐缩小)

景别: 远景(巷道全纵深·一点透视·C-DEP-01)

深度层次(4层·VS-SPA-01):
  前景层(极近): Pedro头部/肩膀剪影(画面右下·暗色块·略微虚化·锚定画面——观众知道Pedro仍在)
  前景层(近): 碎石地面(清晰·粒径纹理·从画面下方向巷口延伸)
  中景层: 巷中段墙面(清晰·冷灰·排水管·墙根青苔·垃圾桶靠右墙)
  背景层: 轿车(暗色块在巷口暖亮逆光中·驶离·缩小) -> 巷口暖亮过曝区(轿车离开后完整恢复)

主导线条: 纵深汇聚线(巷道两侧墙面·指向巷口·C-DEP-01线性透视) + 轿车顶部水平线(逐渐缩小·运动方向指示)

负空间: 巷口暖亮过曝区(轿车离开后留白·C-FI2-NS-26运动方向留白强化驶离感)·画面左侧巷内暗部(轿车离开后的空位)

焦距: 24mm等效(广角·夸张纵深)
构图风格: 前景锚点+深空收束(Pedro剪影=叙事锚点·提醒观众故事仍未结束) + 开放构图(巷口暖亮=出口/下一个场景的方向)
KB规则ID: C-FI-02(深度分层·4层) · C-DEP-01(线性透视) · C-FI2-NS-26(运动方向前方留白·轿车驶向巷口暖亮) · C-FI-06(剪影·Pedro前景剪影+轿车远景剪影·双重剪影) · VS-SPA-04(色调对比分离前后景·前景暗剪影+背景暖亮)
```

### 光影设计

```
主光源: 巷口逆光(~4500K·过曝1-2档·硬光·轿车驶向光源方向·逐渐融入暖亮·形成驶离剪影)
  锚点: 参考图格1+格3

辅助光: 阴天漫射天空光(~5500K·巷内散射·均匀照明前景碎石+墙面+Pedro剪影边缘)
  锚点: 参考图格8

光比: 极高1:10+(巷内暗部:巷口过曝·轿车在其中成为移动暗色块)
  Pedro前景: 暗色剪影(在巷内散射光中呈深灰·无内部细节)
  轿车远景: 暗色剪影(在巷口暖亮中·对比度最高)

光影焦点(按时间):
  0-2s: 轿车尾灯(红色点光源·如有亮起·在暖金背景中形成色彩对比)
  3-5s: 巷道空荡的巷口暖亮(轿车离去后的光区恢复·光线无遮挡)

视线引导路径: Pedro前景剪影(右下) -> 碎石地面纵深 -> 巷道墙面透视 -> 轿车暗色块(移动中·向巷口) -> 巷口暖亮过曝区

阴影处理: Pedro前景=暗色剪影(深灰·散射光边缘)·轿车=移动暗色剪影(边缘在暖亮中清晰)·两侧墙面=冷灰渐变(近暗->远受巷口光影响微亮)
  闭塞阴影: [需要] 墙根+排水管底部·垃圾桶后方暗部

色彩策略: 冷暖对冲(日常恢复态·与镜#1一致但无Pedro动作)——巷口暖金(4500K)+巷内冷灰(5500K)·Pedro+轿车=中性暗色块
  轿车尾灯红色: 暖金背景中的互补色点(红vs暖金=COL-PRI-01互补色·微小的视觉重音)
主色调: 冷暖对冲(日常恢复态·与镜#1形成闭环)
饱和度: 低(巷内冷灰·大面积) + 高(巷口暖金·小面积) + 点(尾灯红·极小面积)
KB规则ID: L-3PT-05(硬光巷口+柔光巷内·氛围匹配) · L-CT-02(混合色温·双色温有叙事理由) · COL-PRI-02(冷暖构建景深·暖进冷退) · COL-PRI-01(尾灯红vs暖金=互补色对比)
跨镜色温一致性: 4500K+5500K与全场景锚点基线一致
```

### 三域协调

```
机位-构图: 低角度(0.5m) + OTS Pedro -> 前景人物锚定画面·即使Pedro静止不动·他的存在"框住"了观众的视角
机位-光影: 低角度OTS -> Pedro剪影占据右下暗部·巷口暖亮在左上方·对角线明暗分布
构图-光影: 前景暗部(冷灰·Pedro)+背景亮部(暖金·巷口) = VS-SPA-04色调对比分离前后景 + 双重剪影(C-FI-06·Pedro+轿车)
场景闭环: 镜#1=Pedro跑入巷道·发现轿车 / 镜#7=Pedro蹲在原地·轿车离去 / 首尾呼应·情绪回路闭合
```

---

# §B-S6 验证汇总

## 跨镜轴线逐对验证

```
场景轴线: 巷道纵深方向(巷口<->巷尾)·A侧(巷道右侧)

镜#1->#2: #1(巷口跟拍·A侧)->#2(POV虚拟·继承Pedro位置·A侧) -> 同一空间·A侧一致 ✅
镜#2->#3: #2(POV虚拟)->#3(垃圾桶侧方·区域③·A侧) -> 同一空间·A侧一致 ✅
镜#3->#4: #3(垃圾桶侧方)->#4(垃圾桶后方POV·A侧) -> 同一空间·A侧一致 ✅
镜#4->#5: 不同空间(巷道->轿车内)·硬切·无轴线关系 ✅
镜#5->#6: 不同空间(轿车内->巷道)·硬切·无轴线关系 ✅
镜#6->#7: #6(垃圾桶侧方·ECU)->#7(垃圾桶后方1m·远景·A侧) -> 同一空间·A侧一致 ✅

跨镜轴线验证: 0次越轴·0次视线矛盾 ✅
```

## 视线匹配验证

```
Pedro视线方向: 始终看巷口(画面纵深·画右上方) ✅
  镜#1: Pedro看巷口(轿车方向) ✅
  镜#2: POV·Pedro所见即巷口 ✅
  镜#3: Pedro探头后看巷口 ✅
  镜#4: 偷窥POV·看巷口轿车 ✅
  镜#6: Pedro看巷口·缩回后再次确认 ✅
  镜#7: Pedro看巷口(轿车驶离方向) ✅

Rico视线方向(镜#5): 从车内看车窗外(巷口方向·看向Pedro方向) ✅
  与Pedro视线方向相对(正反打POV) ✅

视线匹配: 全部一致·Pedro视线方向全程未变 ✅
```

## 空间约束验证

```
镜#1: 机位在巷口入口(区域①)·沿巷道中轴线·不穿墙 ✅
镜#2: POV虚拟·无物理机位约束 ✅
镜#3: 机位在垃圾桶侧前(区域③边界)·距墙面>0.3m·不穿桶 ✅
镜#4: 虚拟POV在垃圾桶后·视线通过桶与墙间隙或桶沿上方 ✅
镜#5: 车内CU不穿车体·POV虚拟·影子ECU在地面(区域⑤) ✅
镜#6: 机位在垃圾桶侧前(区域③边界)·距墙面>0.3m ✅
镜#7: 机位在巷中段(区域②边界)·距地0.5m·在可站立区域 ✅

全部7镜机位在可放置区域内·不穿墙·不悬空 ✅
窄区约束: 巷道宽度<2m·无横移设计·仅固定/推近(P-FAL-06规避) ✅
```

## 光源锚点验证

```
光源1(巷口逆光·~4500K):
  镜#1: 锚点[格1+格3·巷口方向逆光] ✅
  镜#2: 锚点[格1+格3·轿车上方的巷口逆光] ✅
  镜#3: 锚点[格3·巷口远光间接填充] ✅
  镜#4: 锚点[格1+格3·挡风玻璃框外亮背景] ✅
  镜#5: 锚点[格1+格3·POV巷口·影子投射源] ✅
  镜#6: 锚点[格1+格3·瞳孔暖色高光点] ✅
  镜#7: 锚点[格1+格3·巷口暖亮恢复·轿车驶离] ✅

光源2(阴天漫射天空光·~5500K):
  镜#1: 锚点[格8·头顶一线天散射] ✅
  镜#2: 锚点[格8·巷内散射·地面+墙面+轿车外部] ✅
  镜#3: 锚点[格8·巷内主照明] ✅
  镜#4: 锚点[格8·前景桶沿+碎石地面弱光] ✅
  镜#5: 锚点[格8·POV扫描中巷内照明·影子段碎石散射] ✅
  镜#6: 锚点[格8·面部极弱环境光] ✅
  镜#7: 锚点[格8·前景碎石+墙面散射] ✅

光源4(轿车内侧逆暖金·~3500K):
  镜#2: 锚点[轿车内参考图·侧逆光与强对比·车内交换] ✅
  镜#4: 锚点[轿车内参考图·侧逆光与强对比·偷窥视角中的车内] ✅
  镜#5: 锚点[轿车内参考图·侧逆光与强对比·Rico侧脸] ✅

光源3(积水反射·格7): 镜#1地面闪烁微光 [微弱·非主导] ✅

全部光源可追溯参考图·无无锚点光源·无凭空编造 ✅
三重色温系统(3500K/4500K/5500K)全场景锚点一致 ✅
```

## P-FAL规避验证

```
P-FAL-01(瞳孔变化): 未描述瞳孔收缩/扩张过程·固定瞳孔状态(瞳孔中暖色高光点固定) ✅
P-FAL-02(mm级精度): 全部用相对描述(微仰/极近/极度虚化)·无mm级精确间距 ✅
P-FAL-03(亚秒级时序): 全部以秒为最小单位·VO约2字/秒可控 ✅
P-FAL-04(3+同时音效): 各镜最多2个同时音效(环境+事件) ✅
P-FAL-05(VO语速): VO≤4字/秒 ✅
P-FAL-06(窄空间横移): 巷道宽度<2m·全固定设计·无横移 ✅
P-FAL-07(高频视觉噪声): 无闪烁/条纹/噪点描述·背景为巷道自然纹理 ✅
P-FAL-08(画面文字): 无画面内文字要求 ✅
P-FAL-09(极端运动形变): 运镜域已委托Movement Designer·本报告无运镜描述 ✅
P-FAL-10(多人同时口型): Pedro气息声单独出现·Rico无对白·不冲突 ✅

全部P-FAL-01~10已主动规避 ✅
```

## 画布七条铁律合规声明

```
第〇条 KB>LLM: 全部决策标注KB规则ID·优先使用P-STATE已验证模式 ✅
第一条 画面可见性>文学: 光影/构图描述仅涉及画面内可见元素·无抽象情绪词 ✅
第二条 渲染可行性>美学: P-FAL-01~10全部规避·Seko硬上限遵守 ✅
第三条 空间锚定>创意: 全部机位可追溯空间地图·全部光源有物理锚点·人物在可放置区域内 ✅
第四条 运镜-画面分离: 本报告不含运镜语义·运镜域委托Movement Designer独立执行 ✅
第五条 确定性>概率性: 全部坐标/参数可量化·静态比例判定为确定性规则 ✅
第六条 物体存在链: 关键道具(O-032足球/O-033轿车/O-034信封/O-035手机/O-037垃圾桶)均有来源标注·与OBJECT_TIMELINE对齐 ✅
第七条 独立验证: 本Agent不自检·交付独立Reviewer验证 ✅
```

---

# §B-S7 YAML输出

> §4(机位域) + §6(构图光影域)两个YAML块。
> §5(运镜域)委托Movement Designer独立执行·不在本报告中输出。

---

# ═══════════════════════════════════════
# §4 机位域YAML
# 映射目标: TIME_SKELETON.segments[].camera + frames[].hard
# ═══════════════════════════════════════

segments_camera:
  - segment_id: "1"
    time_range: [0, 6]
    shot_type: "远景->中景"
    focal_length: "24mm"
    dof: "深景深f/8"
    angle: "超低角度(30cm)->眼平(1.0m)"
    axis_side: "A侧(巷道右侧)"
    coverage_function: "建立+推进+揭示"
    kb_rule_ids:
      - "D-TRI-01"
      - "A-SUS-02"
      - "C-DEP-01"

  - segment_id: "2"
    time_range: [6, 12]
    shot_type: "中全景"
    focal_length: "35mm"
    dof: "中景深f/5.6"
    angle: "眼平(1.2m·Pedro眼高·POV)"
    axis_side: "A侧(继承Pedro位置)"
    coverage_function: "揭示+人物引入·信息差制造"
    kb_rule_ids:
      - "C-FI-17"
      - "A-SUS-02"
      - "C-FI-14"

  - segment_id: "3"
    time_range: [12, 17]
    shot_type: "中景"
    focal_length: "35mm"
    dof: "中景深f/5.6"
    angle: "低角度微仰(0.6m·桶侧)"
    axis_side: "A侧"
    coverage_function: "反应+过渡·躲藏动作"
    kb_rule_ids:
      - "A-SUS-01"
      - "A-SUS-09"
      - "C-FI-17"

  - segment_id: "4"
    time_range: [17, 23]
    shot_type: "中景(前景遮蔽POV)"
    focal_length: "50mm"
    dof: "浅景深f/2.8"
    angle: "微仰(0.8m·桶后POV)"
    axis_side: "A侧"
    coverage_function: "揭示+代入·交易细节"
    kb_rule_ids:
      - "C-FI-17"
      - "C-AJS-03"
      - "C-FI-16"
      - "A-SUS-02"

  - segment_id: "5"
    time_range: [23, 29]
    shot_type: "近景->POV中全景->极端特写"
    focal_length: "50mm->35mm->85mm"
    dof: "浅f/2.8->中f/5.6->浅f/2.8"
    angle: "眼平(车内)->第一人称(POV)->微俯(影子)"
    axis_side: "车外侧->无(POV)->A侧"
    coverage_function: "威胁识别·全场景情绪峰值"
    kb_rule_ids:
      - "A-SUS-09"
      - "A-SUS-02"
      - "C-FI-17"
      - "C-FI-06"

  - segment_id: "6"
    time_range: [29, 34]
    shot_type: "极端特写"
    focal_length: "85mm"
    dof: "极浅景深f/2.0"
    angle: "微仰拍(0.6m·桶侧)"
    axis_side: "A侧"
    coverage_function: "情绪峰值反应·恐惧视觉化"
    kb_rule_ids:
      - "A-SUS-01"
      - "A-SUS-09"
      - "C-KTZ-02"

  - segment_id: "7"
    time_range: [34, 39]
    shot_type: "远景"
    focal_length: "24mm"
    dof: "深景深f/8"
    angle: "低角度微仰(0.5m·OTS Pedro)"
    axis_side: "A侧"
    coverage_function: "收束+情绪余韵+空间释放"
    kb_rule_ids:
      - "A-SUS-08"
      - "C-FI-06"
      - "C-DEP-01"
      - "C-FI2-NS-26"

frames_hard:
  - sec: 0
    global_sec: 0
    camera_position: "1"
    shot_type: "远景"
    focal_length: "24mm"
  - sec: 1
    global_sec: 1
    camera_position: "1"
    shot_type: "远景"
    focal_length: "24mm"
  - sec: 2
    global_sec: 2
    camera_position: "1"
    shot_type: "远景"
    focal_length: "24mm"
  - sec: 3
    global_sec: 3
    camera_position: "1"
    shot_type: "中全景"
    focal_length: "24mm"
  - sec: 4
    global_sec: 4
    camera_position: "1"
    shot_type: "中全景"
    focal_length: "24mm"
  - sec: 5
    global_sec: 5
    camera_position: "1"
    shot_type: "中景"
    focal_length: "24mm"
  - sec: 6
    global_sec: 6
    camera_position: "2"
    shot_type: "中全景"
    focal_length: "35mm"
  - sec: 7
    global_sec: 7
    camera_position: "2"
    shot_type: "中全景"
    focal_length: "35mm"
  - sec: 8
    global_sec: 8
    camera_position: "2"
    shot_type: "中全景"
    focal_length: "35mm"
  - sec: 9
    global_sec: 9
    camera_position: "2"
    shot_type: "中全景"
    focal_length: "35mm"
  - sec: 10
    global_sec: 10
    camera_position: "2"
    shot_type: "中全景"
    focal_length: "35mm"
  - sec: 11
    global_sec: 11
    camera_position: "2"
    shot_type: "中全景"
    focal_length: "35mm"
  - sec: 12
    global_sec: 12
    camera_position: "3"
    shot_type: "中景"
    focal_length: "35mm"
  - sec: 13
    global_sec: 13
    camera_position: "3"
    shot_type: "中景"
    focal_length: "35mm"
  - sec: 14
    global_sec: 14
    camera_position: "3"
    shot_type: "中景"
    focal_length: "35mm"
  - sec: 15
    global_sec: 15
    camera_position: "3"
    shot_type: "中景"
    focal_length: "35mm"
  - sec: 16
    global_sec: 16
    camera_position: "3"
    shot_type: "中景"
    focal_length: "35mm"
  - sec: 17
    global_sec: 17
    camera_position: "4"
    shot_type: "中景(遮蔽POV)"
    focal_length: "50mm"
  - sec: 18
    global_sec: 18
    camera_position: "4"
    shot_type: "中景(遮蔽POV)"
    focal_length: "50mm"
  - sec: 19
    global_sec: 19
    camera_position: "4"
    shot_type: "中景(遮蔽POV)"
    focal_length: "50mm"
  - sec: 20
    global_sec: 20
    camera_position: "4"
    shot_type: "中景(遮蔽POV)"
    focal_length: "50mm"
  - sec: 21
    global_sec: 21
    camera_position: "4"
    shot_type: "中景(遮蔽POV)"
    focal_length: "50mm"
  - sec: 22
    global_sec: 22
    camera_position: "4"
    shot_type: "中景(遮蔽POV)"
    focal_length: "50mm"
  - sec: 23
    global_sec: 23
    camera_position: "5"
    shot_type: "近景"
    focal_length: "50mm"
  - sec: 24
    global_sec: 24
    camera_position: "5"
    shot_type: "近景"
    focal_length: "50mm"
  - sec: 25
    global_sec: 25
    camera_position: "5"
    shot_type: "中全景"
    focal_length: "35mm"
  - sec: 26
    global_sec: 26
    camera_position: "5"
    shot_type: "中全景"
    focal_length: "35mm"
  - sec: 27
    global_sec: 27
    camera_position: "5"
    shot_type: "极端特写"
    focal_length: "85mm"
  - sec: 28
    global_sec: 28
    camera_position: "5"
    shot_type: "极端特写"
    focal_length: "85mm"
  - sec: 29
    global_sec: 29
    camera_position: "6"
    shot_type: "极端特写"
    focal_length: "85mm"
  - sec: 30
    global_sec: 30
    camera_position: "6"
    shot_type: "极端特写"
    focal_length: "85mm"
  - sec: 31
    global_sec: 31
    camera_position: "6"
    shot_type: "极端特写"
    focal_length: "85mm"
  - sec: 32
    global_sec: 32
    camera_position: "6"
    shot_type: "极端特写"
    focal_length: "85mm"
  - sec: 33
    global_sec: 33
    camera_position: "6"
    shot_type: "极端特写"
    focal_length: "85mm"
  - sec: 34
    global_sec: 34
    camera_position: "7"
    shot_type: "远景"
    focal_length: "24mm"
  - sec: 35
    global_sec: 35
    camera_position: "7"
    shot_type: "远景"
    focal_length: "24mm"
  - sec: 36
    global_sec: 36
    camera_position: "7"
    shot_type: "远景"
    focal_length: "24mm"
  - sec: 37
    global_sec: 37
    camera_position: "7"
    shot_type: "远景"
    focal_length: "24mm"
  - sec: 38
    global_sec: 38
    camera_position: "7"
    shot_type: "远景"
    focal_length: "24mm"

# ═══════════════════════════════════════
# §5 运镜域YAML — 委托Movement Designer
# ═══════════════════════════════════════

# 运镜域已委托独立的Movement Designer Agent执行。
# 本报告不包含segments_movement / frames_movement / segments_transitions。
# Movement Designer将基于本报告的机位+构图+光影设计进行运镜决策。
# 交接参数:
#   - 静态镜: #2+#3+#4+#5+#6 (5/7=71.4%)
#   - 动态镜: #1(跟拍追球)+#7(固定但含轿车运动)
#   - 窄空间约束: 巷道<2m禁横移(P-FAL-06)
#   - 车内极度受限: 仅限固定/极慢推近/微摇

# ═══════════════════════════════════════
# §6 构图光影域YAML
# 映射目标: TIME_SKELETON.global_anchors + frames[].soft
# ═══════════════════════════════════════

global_anchors:
  character:
    Pedro: "Boy, 10 years old, male, thin small malnourished build, ~1.2m height, dark black unkempt hair, deep-set brown eyes large and alert, sun-tanned skin from outdoor favela life, narrow face with slightly protruding cheekbones, small hands with dirt under fingernails. Costume: faded old light-colored T-shirt (may have small holes), dark shorts or old trousers (knees worn), barefoot or old flip-flops. Core visual signatures: (P1) half-face one-eye peeking from behind trash can rim — only right half of face visible, left half obscured by can; (P2) fingers gripping rusty can rim with whitened knuckles from tension; (P3) crouched low posture at approximately 0.8m eye height when squatting behind trash can."
    Rico: "Latin male, 30-35 years old, lean build with controlled precise presence, short dark brown hair neatly kept (not favela style), tan-brown skin, angular face with calm expressionless default look, deep-set dark eyes with slow scanning gaze, no unnecessary movements. Costume: dark casual jacket or coat (not police style), dark shirt or t-shirt, dark trousers (inside car, shadowy interior obscures details). Core visual signatures: (R1) side profile silhouette through dusty windshield — half face lit by warm gold side-light, other half in deep shadow; (R2) quick mechanical hand movements for envelope/phone exchange — no wasted motion; (R3) sudden head turn with visible neck muscle tension — the moment of near-discovery."
    GoldRimmedGlassesDriver: "Male, 40-50 years old, medium build, seated in driver seat behind steering wheel. Gold-rimmed glasses (thin gold metal frame, round or oval lenses) are PRIMARY visual identifier — rest of facial features obscured by glasses reflection and dark car interior shadow. Costume: dark top (shirt or jacket, details indistinct in deep shadow). Core visual signatures: (G1) gold-rim glasses reflecting warm side-backlight as tiny bright points in dark car interior; (G2) hands moving from steering wheel to center console for exchange; (G3) side face partially lit by warm gold light on cheekbone and glasses frame edge only — maintain mysterious aura through visual concealment."

  environment:
    description: "Favela narrow alleyway in Sao Paulo hills, afternoon, overcast sky. Alley dimensions: approximately 20m deep, less than 2m wide, open-air corridor between two brick walls. Left wall: exposed red brick, cement patches, water seepage dark stains, small iron-barred window, faded graffiti remnants. Right wall: peeling gray plaster revealing underlying red brick, electric meter box at approximately 1.5m height. Floor: gravel and dry mud with slight slope inward, scattered puddles reflecting sky light, weeds at wall-gravel junction. Overhead: narrow strip of gray overcast sky with crisscrossing electrical wires and clothesline. Two exits: alley entrance (connects to external road via stone steps, bright afternoon backlight overexposed 1-2 stops, approximately 4500K warm gold) and alley rear exit (connects to another street, darker). Mid-alley: rusted cast iron drainpipe along left wall, moss at wall base, metal trash can (approximately 1m tall, rusted surface, inferred physical property — reference image does not directly cover, marked LEVEL-C) positioned against right wall. Secondary space: dark sedan interior (front seats only) — old black sedan, dusty windshield with dried water stain patterns, aged cracked black leather seats with deep creases and seam dust, dust-covered dashboard and center console, gear shift knob with oily patina and fine scratches, rearview mirror reflecting backseat and street behind, warm gold side-backlight (approximately 3500K) entering from driver side window creating high-contrast chiaroscuro light slices on leather, hands, and dashboard surfaces."

  style_spine:
    description: "shot on Arri Alexa 35, Kodak Vision3 250D, desaturated cool slate gray alley interior with warm amber gold overexposed entrance, vintage warm gold high-contrast car interior like 1970s crime cinema, subtle film grain, 2.35:1 widescreen aspect ratio for lateral compression of narrow alley depth"
    palette_anchors:
      - "cool slate gray (alley interior, 5500K overcast)"
      - "warm amber gold (alley entrance backlight, 4500K)"
      - "vintage warm gold/amber (car interior side-backlight, 3500K)"
      - "deep black (car interior shadows, chiaroscuro voids)"
      - "rust orange-brown (trash can, drainpipe, iron oxidation details)"

  lighting:
    description: "Triple light source system spanning two interconnected spaces. ALLEY: Source1 — alley entrance afternoon backlight, 4500K, hard light, overexposed 1-2 stops, anchored in reference Grid1 (alley entrance looking in) and Grid3 (looking back at entrance from inside alley). Source2 — overcast diffused sky light, 5500-6500K, soft light, from narrow sky strip above alley between walls, anchored in reference Grid8 (looking up at sky strip with wires). Source3 — weak puddle reflection light from gravel floor water puddles, anchored in reference Grid7 (gravel micro-detail). CAR INTERIOR: Source4 — warm gold side-backlight, 3200-4000K, hard light, entering from driver side left/front window, creating sharp chiaroscuro contrast with light slices on leather seats, steering wheel top, dashboard surfaces, and hands during exchange, anchored in car interior reference images (center-top and right-center grid positions showing side-backlight and strong contrast). KEY COLOR TEMPERATURE SYSTEM: alley entrance warm-bright (4500K) versus alley interior cool-gray (5500K) versus car interior warm-gold intimate (3500K). Each space has a distinct color temperature identity — the warm car interior (3500K) reads as a 'warm pocket of secrecy' embedded within the cold gray alley environment. Earthy texture tones throughout: red brick warm brown, gray plaster mid-gray, gravel neutral gray, rusted iron orange-brown."
    anchor_in_reference: "Alley: Grid1 (entrance backlight) + Grid3 (looking back at entrance) + Grid5 (alley mid-section core) + Grid7 (gravel micro-detail with puddle reflection) + Grid8 (looking up at sky strip with wires). Car interior: side-backlight and strong contrast descriptions + warm color tone base + external view through windshield."

  constraints:
    - "Pedro half-face one-eye visual signature consistent across shots #3, #4, #6 — same angle, same trash can rim position, same eye-to-rim relationship"
    - "Rico expressionless angular face matches EP14 Scene A award photo of Rico for cross-scene anchor continuity"
    - "Gold-rimmed glasses reflection is car interior only highlight point — maintain consistent reflection angle and brightness in shots #2 and #5"
    - "Alley triple color temperature contrast ratio consistent: warm 4500K entrance vs cool 5500K interior vs warm 3500K car interior"
    - "Football shadow on gravel floor: semi-penumbra edge transition, not pure black — gravel gaps transmit both alley entrance light (4500K) and sky light (5500K) creating subtle bright speckles within shadow"
    - "Trash can: metal cylinder approximately 1m tall, rusted surface, positioned against right wall in alley mid-section — inferred physical property (reference image does not directly cover), marked as LEVEL-C for Object Existence Verifier"
    - "All characters maintain consistent facial proportions across shots — no facial feature drift"
    - "No flickering in light color temperature across shots within same light source"
    - "No subtitles, no logos, no watermarks"
    - "No on-screen text — any required text marked as 'post-production overlay' (P-FAL-08)"

frames_soft:

  # ====== 镜#1: 追球入巷·巷口猛停 [0-6s] ======

  - sec: 0
    global_sec: 0
    camera_position: "1"
    action_anchor: "旧足球从石阶上方向画面滚入·球体占画面下三分之一中央·足球表面旧皮革磨损纹理可见·球在碎石地面上弹跳·碎石飞溅微尘"
    spatial_anchor: "超低角度贴近地面·碎石占据前景2/3·石阶从画面外延伸入画·巷内纵深空间向远处收窄·巷口方向暖亮逆光过曝"
    prop_state:
      - item: "旧足球(O-032)"
        state: "沿石阶滚下·刚进入画面·弹跳中"
      - item: "碎石地面(O-021)"
        state: "碎石子+干泥·微坡向巷内·画面主体"
    character_state: []
    audio:
      ambience: "贫民窟远底噪(远处人声·狗吠·电视声从窗内传出)"
      events:
        - "足球在碎石上弹跳: 喀嗒-喀嗒 节奏"

  - sec: 1
    global_sec: 1
    camera_position: "1"
    action_anchor: "足球继续沿碎石地面滚落·速度微减·球体影子在前方碎石上拉长·狭窄巷内足球撞击左侧墙根碎石后方向微偏"
    spatial_anchor: "两侧砖墙进入画面边缘·左侧墙面红砖水泥补丁纹理渐显·头顶一线天窄条开始可见·巷口暖亮过曝区在远景中央"
    prop_state:
      - item: "旧足球(O-032)"
        state: "滚动中·速度微减·方向微偏"
    character_state: []
    audio:
      ambience: "贫民窟远底噪持续"
      events:
        - "足球滚动声: 咕噜噜持续·节奏放缓"

  - sec: 2
    global_sec: 2
    camera_position: "1"
    action_anchor: "足球继续向巷内滚落·Pedro的赤脚从石阶上方进入画面后景·小跑追逐球·瘦小身形剪影在巷口暖亮逆光中"
    spatial_anchor: "两侧砖墙更清晰·墙面渗水痕迹深灰蔓延可见·头顶电线进入画面顶部·巷口暖亮过曝在画面远景中央"
    prop_state:
      - item: "旧足球(O-032)"
        state: "继续滚动·速度进一步减慢"
    character_state:
      - character: "Pedro"
        pose: "小跑追逐·手臂摆动·身体前倾"
        position: "画面后景上方·石阶中段·距球约2m"
        expression: "未可见(逆光剪影)"
    audio:
      ambience: "贫民窟远底噪持续"
      events:
        - "足球滚动声继续·伴随Pedro小跑脚步声"

  - sec: 3
    global_sec: 3
    camera_position: "1"
    action_anchor: "Pedro追近足球·距离缩短至约1m·右手前伸准备捡球·足球即将停止滚动"
    spatial_anchor: "两侧墙面压迫感增强·墙根青苔沿墙角可见·铸铁排水管贴左侧墙面进入画面·巷口暖亮逆光中隐约可见外部道路"
    prop_state:
      - item: "旧足球(O-032)"
        state: "即将停止·在碎石地上最后滚动"
    character_state:
      - character: "Pedro"
        pose: "追近至球旁·右手前伸·身体仍然前倾"
        position: "画面中景·距球约1m"
        expression: "未可见(身体朝向球·背向镜头侧)"
    audio:
      ambience: "贫民窟远底噪"
      events:
        - "足球滚动声即将停止·最后几下碎石摩擦声"

  - sec: 4
    global_sec: 4
    camera_position: "1"
    action_anchor: "Pedro突然猛停·双脚钉在碎石上·身体惯性前倾后急刹·右腿在前左腿在后形成支撑·足球在前方约1m处静止"
    spatial_anchor: "相机升至Pedro眼高约1.0m·巷口全景展开:暖亮过曝逆光中一辆黑色轿车暗色剪影停在巷口外部道路·车身挡住部分巷口暖光·形成不祥的暗色块"
    prop_state:
      - item: "旧足球(O-032)"
        state: "静止在碎石地上·球体影子在地上"
      - item: "黑色轿车(O-033)"
        state: "停在巷口外部道路·暗色剪影·全新出现在画面中"
    character_state:
      - character: "Pedro"
        pose: "猛停·双脚钉地·身体前倾后急刹·重心后移"
        position: "画面中景中央偏右·背对镜头"
        expression: "不可见(背对)·但身体语言传达震惊"
    audio:
      ambience: "贫民窟远底噪"
      events:
        - "足球静止:碎石摩擦声停止"
        - "Pedro急停:碎石上急促摩擦声"

  - sec: 5
    global_sec: 5
    camera_position: "1"
    action_anchor: "Pedro身体完全静止·手臂垂放·背部僵硬·面向巷口方向凝视轿车·瘦小背影在巷道中央形成中间调剪影·边缘被巷口暖逆光勾勒极细暖色轮廓光"
    spatial_anchor: "固定画面:两侧墙面收窄至巷口·碎石地面向前延伸至外部道路交界·轿车暗色剪影在巷口暖亮逆光中占据中心远景·天空一线天在上方窄条可见"
    prop_state:
      - item: "旧足球(O-032)"
        state: "静止在碎石地上·球的影子在地上·距Pedro约1m"
      - item: "黑色轿车(O-033)"
        state: "静止停在巷口外部道路·暗色剪影·引擎怠速"
    character_state:
      - character: "Pedro"
        pose: "完全静止站立·背对镜头·凝视巷口轿车"
        position: "画面中景中央·距轿车远景约15m"
        expression: "不可见(背影)"
    audio:
      ambience: "贫民窟远底噪持续"
      events:
        - "轿车引擎声:低沉怠速声从巷口方向传来·持续"

  # ====== 镜#2: Pedro POV·发现轿车·目击交易 [6-12s] ======

  - sec: 6
    global_sec: 6
    camera_position: "2"
    action_anchor: "硬切至Pedro主观视角。从他眼高(~1.2m)看巷口方向。黑色轿车停在巷口外道路。透过布满沙尘和干涸水渍的挡风玻璃看入车内前排。Rico(右·副驾驶)和金丝眼镜司机(左·驾驶座)坐姿·两人上半身可见·挡风玻璃沙尘层在暖金逆光中散射形成柔和空气质感"
    spatial_anchor: "挡风玻璃作为天然画框·沙尘纹理和水渍斑痕在前景半透明·后视镜反射后排空间和车后街景·中控台灰尘均匀覆盖·方向盘老化皮质龟裂纹理在司机手中隐约可见·车内暖金侧逆光与巷内冷灰形成冷暖视觉分离"
    prop_state:
      - item: "挡风玻璃(O-030)"
        state: "沙尘覆盖·干涸水渍斑痕·散射暖金光"
      - item: "皮质座椅(O-029)"
        state: "黑色皮革极度老化·龟裂褶皱"
      - item: "方向盘(O-026)"
        state: "老化皮质龟裂·司机双手握持"
    character_state:
      - character: "Rico"
        pose: "坐姿·副驾驶·身体微微转向司机侧"
        position: "挡风玻璃框内·画面右侧"
        expression: "棱角分明·面无表情·冷静"
      - character: "GoldRimmedGlassesDriver"
        pose: "坐姿·驾驶座·双手在方向盘上"
        position: "挡风玻璃框内·画面左侧"
        expression: "不可辨(车内暗部+眼镜反光模糊)"
    audio:
      ambience: "轿车引擎低沉怠速声(从巷口方向传来·略远)"
      events: []

  - sec: 7
    global_sec: 7
    camera_position: "2"
    action_anchor: "Rico右手从身侧取出信封(深色/牛皮纸色)·动作快而精准·无多余手指动作。司机左手从方向盘移至中控区上方"
    spatial_anchor: "挡风玻璃沙尘纹理持续在前景·车内空间焦点收至两人之间的中控区上方·暖金侧逆光在仪表台边缘形成清晰光切面"
    prop_state:
      - item: "信封(O-034)"
        state: "Rico右手握持·刚从身侧取出·出现在画面中"
    character_state:
      - character: "Rico"
        pose: "右手持信封向司机方向递出·动作快而精准"
        position: "挡风玻璃框内右侧"
        expression: "面无表情·眼神锁定交换物"
      - character: "GoldRimmedGlassesDriver"
        pose: "左手从方向盘移向中控区·准备交换"
        position: "挡风玻璃框内左侧"
    audio:
      ambience: "引擎怠速声持续"
      events:
        - "信封轻微摩擦声"

  - sec: 8
    global_sec: 8
    camera_position: "2"
    action_anchor: "Rico将信封递至中控区上方中央。司机右手从身侧取出一部深色手机·动作同样快而机械。两只手在中控区上方交汇·信封和手机在暖金侧逆光的光切面中"
    spatial_anchor: "画面焦点收至中控区上方·暖金侧逆光在信封表面和手机屏幕边缘形成清晰光切面·仪表台灰尘在暖光下可见颗粒"
    prop_state:
      - item: "信封(O-034)"
        state: "Rico递至中控区上方中央·暖金光切面照亮"
      - item: "手机(O-035)"
        state: "司机右手取出·深色·即将递出"
    character_state:
      - character: "Rico"
        pose: "右手持信封在中控区上方·等待交换"
        expression: "面无表情"
      - character: "GoldRimmedGlassesDriver"
        pose: "右手持手机递出·左手从方向盘移至中控区"
    audio:
      ambience: "引擎怠速声持续"
      events: []

  - sec: 9
    global_sec: 9
    camera_position: "2"
    action_anchor: "交换完成。Rico接过手机收入身侧口袋·司机接过信封放在中控台或身侧。手指接触即分离·无多余停留"
    spatial_anchor: "画面紧致:中控区上方·两只手占据画面中央·交换后的静止·仪表台灰尘和换挡杆球头油光包浆清晰·暖金光照亮手部皮肤纹理"
    prop_state:
      - item: "信封(O-034)"
        state: "司机已接收·放置中控台或身侧"
      - item: "手机(O-035)"
        state: "Rico已接收·收入身侧"
    character_state:
      - character: "Rico"
        pose: "交换完成·手收回身侧"
      - character: "GoldRimmedGlassesDriver"
        pose: "交换完成·左手回到方向盘"
    audio:
      ambience: "引擎怠速声持续"
      events:
        - "手机轻放声"

  - sec: 10
    global_sec: 10
    camera_position: "2"
    action_anchor: "交换后静止片刻。Rico手放在腿上·司机双手回到方向盘。车内恢复到交换前的静态·但信封和手机已交换位置。Rico侧脸在暖金侧逆光中半明半暗"
    spatial_anchor: "中控区+两只手(静止)+两人下半面部(暗部)·暖金光照亮方向盘顶部老化龟裂·司机金丝眼镜框边缘微光反射·车内暗部深邃黑色"
    prop_state:
      - item: "信封(O-034)"
        state: "在司机侧·已放置"
      - item: "手机(O-035)"
        state: "在Rico侧·已放置"
      - item: "金丝眼镜(O-036)"
        state: "司机佩戴·金色细框·镜片在侧逆光下反光"
    character_state:
      - character: "Rico"
        pose: "坐姿静止·手在腿上·侧脸半明半暗"
      - character: "GoldRimmedGlassesDriver"
        pose: "坐姿静止·双手在方向盘"
    audio:
      ambience: "引擎怠速声持续·车内安静"
      events: []

  - sec: 11
    global_sec: 11
    camera_position: "2"
    action_anchor: "静止延续。车内暗部深邃·暖金光照区域稳定·交换已完成的静止瞬间——暴风雨前的平静"
    spatial_anchor: "挡风玻璃沙尘纹理静止·仪表台暖金光切面稳定·后视镜反射后排暗部空间"
    audio:
      ambience: "引擎怠速声持续"
      events: []

  # ====== 镜#3: 躲藏·垃圾桶后探头 [12-17s] ======

  - sec: 12
    global_sec: 12
    camera_position: "3"
    action_anchor: "硬切回巷道。Pedro在巷口中央猛停位置·身体快速转向后跑向巷中段靠墙的垃圾桶·动作急促·手臂摆动·身体前倾跑步姿态"
    spatial_anchor: "低角度微仰视角从Pedro身侧~1.5m处·巷口暖亮逆光在远景(轿车暗色剪影仍在)·巷中段墙面在散射光中呈冷灰色调·垃圾桶(金属圆桶·锈蚀)靠右侧墙面"
    prop_state:
      - item: "垃圾桶(O-037)"
        state: "靠右侧墙面·金属圆桶·高约1m·表面锈蚀·静止"
      - item: "黑色轿车(O-033)"
        state: "远景巷口·暗色剪影·仍在"
    character_state:
      - character: "Pedro"
        pose: "从巷口快速跑向垃圾桶方向·身体前倾"
        position: "画面中景·向画面右侧移动"
        expression: "不可见(侧身+运动模糊)"
    audio:
      ambience: "贫民窟远底噪+引擎怠速声从巷口传来"
      events:
        - "Pedro急促跑步声在碎石上"

  - sec: 13
    global_sec: 13
    camera_position: "3"
    action_anchor: "Pedro到达垃圾桶后方·快速蹲下·膝盖抵胸·全身缩成一团·身体完全被垃圾桶遮挡·仅头顶和部分肩膀从桶沿上方微露"
    spatial_anchor: "巷中段·垃圾桶占据画面右侧·Pedro缩入桶后过程可见其身体从右侧边缘消失·巷中段墙面冷灰散射光均匀·左侧排水管锈蚀纹理可见"
    prop_state:
      - item: "垃圾桶(O-037)"
        state: "原位·遮挡Pedro·桶沿在画面中右区域"
    character_state:
      - character: "Pedro"
        pose: "快速蹲下·膝盖抵胸·缩成一团"
        position: "垃圾桶后方·身体被桶遮挡·仅头顶微露"
    audio:
      ambience: "引擎怠速声持续"
      events:
        - "Pedro蹲下:碎石上急促摩擦+身体撞击桶壁闷响"

  - sec: 14
    global_sec: 14
    camera_position: "3"
    action_anchor: "Pedro完全静止在垃圾桶后·身体紧缩·双手扶桶·头顶在桶沿下方·从外看不到面部。垃圾桶在散射光下呈冷灰锈蚀质感"
    spatial_anchor: "静止画面:巷中段全貌·排水管·墙根青苔·碎石地面·垃圾桶靠右墙·巷口方向暖亮逆光中轿车剪影仍在·形成静态的威胁存在"
    prop_state:
      - item: "垃圾桶(O-037)"
        state: "静止靠墙·遮挡Pedro"
    character_state:
      - character: "Pedro"
        pose: "完全静止蹲姿·身体紧缩·被垃圾桶遮挡"
        position: "垃圾桶后方·不可见"
    audio:
      ambience: "引擎怠速声持续·贫民窟远底噪"
      events: []

  - sec: 15
    global_sec: 15
    camera_position: "3"
    action_anchor: "Pedro极缓慢地从桶沿上方探出头·动作极其谨慎·先露出发际线·再额头·最后停在半张脸——右半脸和右眼从桶沿上方露出·手指扒着桶沿·指关节紧抓"
    spatial_anchor: "画面焦点转移至垃圾桶上方·Pedro半张脸从桶沿后浮现·巷口暖亮逆光在远景提供微弱轮廓照明"
    prop_state:
      - item: "垃圾桶(O-037)"
        state: "桶沿被Pedro手指扒住·指关节紧抓桶沿金属边"
    character_state:
      - character: "Pedro"
        pose: "极缓慢探头·手指扒桶沿·右半脸+右眼露出"
        position: "垃圾桶后方·桶沿上方"
        expression: "右眼大睁·警觉·瞳孔在暗处"
    audio:
      ambience: "引擎怠速声持续"
      events:
        - "Pedro气息声:微弱·几乎只在嘴唇间流动"

  - sec: 16
    global_sec: 16
    camera_position: "3"
    action_anchor: "Pedro保持探头姿势·右半脸+右眼静止在桶沿上方·眼睛不眨·锁定巷口方向(轿车)·身体其余部分完全被桶遮挡"
    spatial_anchor: "静止·桶沿水平线分割画面·上方=Pedro半脸(冷灰散射光)·下方=桶身暗部·远景巷口暖亮+轿车剪影"
    character_state:
      - character: "Pedro"
        pose: "探头静止·手指扒桶沿·半脸露出"
        position: "垃圾桶后方·桶沿上方"
        expression: "右眼大睁·警觉注视·嘴唇紧闭"
    audio:
      ambience: "引擎怠速声·贫民窟远底噪"
      events: []

  # ====== 镜#4: 偷看POV·交易细节 [17-23s] ======

  - sec: 17
    global_sec: 17
    camera_position: "4"
    action_anchor: "切换至偷窥POV。前景:垃圾桶沿(极度虚化·深色块占据画面下方1/4)。中景:透过桶与墙壁间隙/桶沿上方看轿车挡风玻璃。车内:Rico和金丝眼镜男·暖金侧逆光中·交换刚完成后的静止"
    spatial_anchor: "极度遮蔽POV:桶沿深色虚化块在下方·桶与墙间隙形成狭窄视窗·巷中段碎石地面虚化过渡·轿车挡风玻璃框在画面中上部·沙尘纹理过滤车内画面·巷口暖亮在挡风玻璃框外过曝"
    prop_state:
      - item: "垃圾桶(O-037)"
        state: "桶沿在画面下1/4·极度虚化深色块·遮挡视野"
      - item: "挡风玻璃(O-030)"
        state: "沙尘+水渍纹理·天然画框·散射暖金光"
    character_state:
      - character: "Rico"
        pose: "坐姿静止·副驾驶·侧脸在暖金半面光中"
        position: "挡风玻璃框内右侧"
        expression: "棱角分明·面无表情"
      - character: "GoldRimmedGlassesDriver"
        pose: "坐姿静止·驾驶座·双手在方向盘"
        position: "挡风玻璃框内左侧·暗部"
    audio:
      ambience: "引擎怠速声(从巷口方向·略远)"
      events: []

  - sec: 18
    global_sec: 18
    camera_position: "4"
    action_anchor: "偷窥视角延续。车内两人保持静止·交换已完成·暖金侧逆光照亮中控区上方·方向盘顶部皮质龟裂在暖光中纹理清晰"
    spatial_anchor: "桶沿深色虚化块静止·视觉窗口(间隙/桶沿上方)窄小·观众与Pedro共享视野限制·信息受限制造悬念"
    audio:
      ambience: "引擎怠速声持续"
      events: []

  - sec: 19
    global_sec: 19
    camera_position: "4"
    action_anchor: "车内·Rico右手微动——检查手机(翻看屏幕或放入口袋)·动作细微但可见。金丝眼镜男转头微瞥Rico方向·然后回正"
    spatial_anchor: "挡风玻璃框内·暖金侧逆光中Rico手部微动是画面唯一动态·眼镜反光微闪(司机转头时)"
    character_state:
      - character: "Rico"
        pose: "右手微动·检查手机·动作细微"
        expression: "面无表情·视线在手机上"
      - character: "GoldRimmedGlassesDriver"
        pose: "微转头瞥Rico·回正"
    audio:
      ambience: "引擎怠速声·车内极静"
      events: []

  - sec: 20
    global_sec: 20
    camera_position: "4"
    action_anchor: "车内恢复静止。Rico手机已收好·司机双手在方向盘·暖金侧逆光在仪表台灰尘上形成稳定光切面·车内暗部深邃"
    spatial_anchor: "偷窥视角静止·桶沿深色块不变·挡风玻璃沙尘纹理不变·巷口暖亮过曝不变——时间在静止中累积紧张"
    audio:
      ambience: "引擎怠速声持续"
      events: []

  - sec: 21
    global_sec: 21
    camera_position: "4"
    action_anchor: "静止延续。车内暖金光切面无变化·暗部深黑·挡风玻璃沙尘纹理过滤使画面呈现胶片颗粒质感"
    spatial_anchor: "偷窥视角静止·观众等待·Pedro在等待·悬念在累积"
    audio:
      ambience: "引擎怠速声·此刻格外清晰(视觉静默强化听觉)"
      events: []

  - sec: 22
    global_sec: 22
    camera_position: "4"
    action_anchor: "静止延续。最后一秒的平静。车内一切如常——但观众知道Pedro在看·信息差制造双重悬念:Rico会发现Pedro吗?"
    spatial_anchor: "桶沿深色块·间隙视窗·挡风玻璃框·车内暖金+暗部·巷口暖亮——全部静止·等待打破"
    audio:
      ambience: "引擎怠速声持续"
      events: []

  # ====== 镜#5: Rico转头·差点发现 [23-29s] ======

  - sec: 23
    global_sec: 23
    camera_position: "5"
    action_anchor: "硬切至轿车内近景。Rico侧脸·副驾驶位。他突然转头——颈肌紧绷·头部快速转向左侧车窗外(巷口方向)·动作果断无犹豫·暖金侧逆光照亮他左半脸(颧骨·眼窝·下颌线)·右半脸在深黑阴影中"
    spatial_anchor: "车内空间紧致·Rico面部占画面左三分线·暖金侧逆光(~3500K)形成清晰明暗交界线沿鼻梁和下颌·挡风玻璃边缘在前景右侧虚化暗框·车内暗部深邃黑色"
    prop_state:
      - item: "挡风玻璃(O-030)"
        state: "前挡边缘在画面右侧虚化暗框"
    character_state:
      - character: "Rico"
        pose: "突然转头向左(巷口方向)·颈肌紧绷·动作果断"
        position: "副驾驶·画面左三分线"
        expression: "棱角分明·面无表情但眼中有警觉·扫描式视线"
    audio:
      ambience: "引擎怠速声(车内·近)"
      events: []

  - sec: 24
    global_sec: 24
    camera_position: "5"
    action_anchor: "Rico侧脸静止·目光穿过挡风玻璃看向巷口方向·扫描式视线从左向右缓慢移动。暖金光照亮颧骨和眼窝·另半脸在深黑阴影中"
    spatial_anchor: "画面紧致:挡风玻璃在前景右上方形成暗框·透过玻璃隐约可见巷口暖亮区·Rico面部暖金+深黑chiaroscuro效果"
    character_state:
      - character: "Rico"
        pose: "转头后静止·目光锁定巷口方向·视线扫描"
        expression: "扫描式视线·警觉·面无表情"
    audio:
      ambience: "引擎怠速声持续"
      events: []

  - sec: 25
    global_sec: 25
    camera_position: "5"
    action_anchor: "POV开始:画面过渡至Rico第一人称视角·透过挡风玻璃看巷口。沙尘+水渍纹理成为前景滤镜。巷口暖亮逆光(~4500K过曝)从画面右方入画·碎石地面占据画面下方·巷口两侧墙面收束·垃圾桶暗色块靠右墙"
    spatial_anchor: "POV视角:挡风玻璃沙尘层在前景形成柔焦纹理过滤·巷口暖亮过曝区在画面右上·碎石地面向巷外延伸·垃圾桶+墙面在中景左方·Pedro身体被桶完全遮挡·只有桶的暗色轮廓"
    prop_state:
      - item: "挡风玻璃(O-030)"
        state: "POV前景·沙尘+水渍纹理过滤视线"
      - item: "垃圾桶(O-037)"
        state: "靠右墙·暗色剪影在巷口暖亮背景中·Pedro在其后不可见"
    character_state: []
    audio:
      ambience: "引擎怠速声(车内)"
      events: []

  - sec: 26
    global_sec: 26
    camera_position: "5"
    action_anchor: "POV扫描继续:视线从左向右水平扫过巷口。扫过碎石地面纹理·积水洼反射天光·墙面灰泥剥落处·垃圾桶轮廓——在Pedro躲藏位置没有停留·Rico没有发现Pedro"
    spatial_anchor: "POV扫描中·挡风玻璃沙尘纹理在前景静态·巷口全景在背景缓慢右移——碎石→墙面→垃圾桶依次入画·扫描经过垃圾桶区域"
    audio:
      ambience: "引擎怠速声持续"
      events: []

  - sec: 27
    global_sec: 27
    camera_position: "5"
    action_anchor: "POV扫描结束·视线停在碎石地面上。足球的影子——一个深色椭圆在碎石上·边缘有半影过渡带·影子内部非纯黑(碎石间隙透射巷口暖光和天空光形成细小亮斑镶嵌)"
    spatial_anchor: "画面定格:碎石地面近景·球的影子深色椭圆占据画面下三分之一·碎石粒径不一·干泥填隙·球的影子是画面中唯一的不规则元素"
    prop_state:
      - item: "旧足球(O-032)"
        state: "球体在画面外(上方或侧方)·仅影子可见在碎石上"
    character_state: []
    audio:
      ambience: "引擎怠速声持续"
      events: []

  - sec: 28
    global_sec: 28
    camera_position: "5"
    action_anchor: "球的影子静止在碎石上。Rico的目光在此停留——一段静默。碎石地面微坡·球的影子在散射光中呈深灰·半影边缘过渡柔和·碎石间隙透光形成亮斑镶嵌"
    spatial_anchor: "固定ECU画面:碎石微距·球的影子深色椭圆占据画面下三分之一·碎石间隙中的细小亮斑散布在影子内部和外部·自然光影纹理"
    audio:
      ambience: "引擎怠速声·格外清晰(视觉静默强化听觉)"
      events: []

  # ====== 镜#6: Pedro反应·缩回·恐惧 [29-34s] ======

  - sec: 29
    global_sec: 29
    camera_position: "6"
    action_anchor: "硬切回垃圾桶后。Pedro右半脸+右眼ECU·桶沿在画面下1/3(极度虚化深色块)。Pedro眼睛瞬间瞪大——看到Rico转头·瞳孔中暖色高光点如针尖·眼白可见血丝。然后面部急速向下沉——缩回避让·右眼从桶沿上方消失·画面只剩桶沿深色虚化块和暗部背景"
    spatial_anchor: "画面紧缩:桶沿深色块占据下方·Pedro面部从存在到消失·背景巷内墙面在极浅景深下完全虚化为冷灰色调"
    prop_state:
      - item: "垃圾桶(O-037)"
        state: "桶沿在画面下1/3·极度虚化·Pedro缩回后桶沿上方无面部"
    character_state:
      - character: "Pedro"
        pose: "眼睛瞪大->身体后缩·面部急速下沉消失·背部撞墙"
        position: "垃圾桶后方·缩回避让·不可见"
        expression: "恐惧·眼睛瞪大·瞳孔暖色高光点(缩回前瞬间)"
    audio:
      ambience: "引擎怠速声持续(从巷口方向·略远)"
      events:
        - "Pedro气息声:急促·几乎听清的 CV:又是他——"

  - sec: 30
    global_sec: 30
    camera_position: "6"
    action_anchor: "桶沿上方为空——Pedro已完全缩回桶后。画面仅剩桶沿深色虚化块+背景冷灰虚化·巷口暖色远光在背景微渗透·Pedro呼吸声可闻"
    spatial_anchor: "ECU固定:桶沿虚化深色块占据画面下1/3·背景为巷内墙面(完全虚化冷灰)·巷口方向微弱的暖色渗透在画面右上角"
    character_state:
      - character: "Pedro"
        pose: "缩在桶后·背部贴墙·完全不可见"
        position: "垃圾桶后方·完全遮蔽"
        expression: "不可见"
    audio:
      ambience: "引擎怠速声"
      events:
        - "Pedro急促呼吸声(桶后·微弱)"

  - sec: 31
    global_sec: 31
    camera_position: "6"
    action_anchor: "桶沿上方仍为空。静止。Pedro在桶后的呼吸声渐缓。巷口引擎声仍在·Rico还在扫描——悬念未解"
    spatial_anchor: "固定ECU:桶沿虚化+背景冷灰·画面几乎静止·仅有微弱的光线微动(巷口暖光在墙面上的微偏移)"
    audio:
      ambience: "引擎怠速声"
      events:
        - "Pedro呼吸声:渐缓·但仍有紧张"

  - sec: 32
    global_sec: 32
    camera_position: "6"
    action_anchor: "极缓慢地·Pedro右眼重新从桶沿上方浮现——先睫毛·再眼睑·最后眼睛完全露出。右眼大睁·瞳孔中暖色高光点(巷口远光反射)重新出现·他还在确认:Rico是否还在看?"
    spatial_anchor: "桶沿上方·Pedro右眼重新出现·眼睫毛清晰·瞳孔暖色高光点如针尖·桶沿深色虚化块不变·背景冷灰虚化不变·Pedro面部其余部分仍在桶后暗部"
    character_state:
      - character: "Pedro"
        pose: "极缓慢重新探头·右眼从桶沿上方浮现"
        position: "垃圾桶后方·桶沿上方·仅右眼露出"
        expression: "恐惧未消·右眼大睁·确认威胁是否仍在"
    audio:
      ambience: "引擎怠速声·然后引擎声微变——Rico转回头·轿车准备驶离"
      events:
        - "Pedro气息声:极微弱·近乎无声"

  - sec: 33
    global_sec: 33
    camera_position: "6"
    action_anchor: "Pedro右眼保持静止在桶沿上方·瞳孔中暖色高光点稳定·恐惧未消但未再缩回——他确认了:轿车还在·但Rico已转回头"
    spatial_anchor: "ECU:右眼+桶沿虚化+冷灰背景·画面结构与29秒相似但情绪不同——从恐惧峰值过渡到恐惧余波·Pedro的身体仍紧绷但不再逃离"
    character_state:
      - character: "Pedro"
        pose: "探头静止·右眼锁定巷口"
        expression: "恐惧未消·瞳孔暖色高光点·嘴唇紧闭"
    audio:
      ambience: "引擎声从怠速转为启动驶离的低沉轰鸣·音调变化"
      events: []

  # ====== 镜#7: 轿车驶离·Pedro前景锚点 [34-39s] ======

  - sec: 34
    global_sec: 34
    camera_position: "7"
    action_anchor: "硬切至巷道远景。低角度·OTS Pedro。Pedro头部/肩膀剪影(暗色块·画面右下·略微虚化)。中远景:轿车从巷口位置发动·车身暗色块在暖亮逆光中开始移动·向巷尾方向驶离"
    spatial_anchor: "低角度远景(~0.5m·Pedro蹲姿肩高):两侧砖墙向巷口收窄·碎石地面从画面下方向巷口延伸·Pedro前景剪影在右下锚定画面·轿车在巷口暖亮区中央·开始横向移动"
    prop_state:
      - item: "黑色轿车(O-033)"
        state: "发动·开始从巷口驶离·暗色块在暖亮中移动"
      - item: "旧足球(O-032)"
        state: "球体在碎石地面某处(画面外)·球的影子仍可见"
    character_state:
      - character: "Pedro"
        pose: "蹲姿静止·头部/肩膀在画面右下·剪影/暗色块"
        position: "垃圾桶后方·画面右下前景锚点"
        expression: "不可见(背对镜头·剪影)"
    audio:
      ambience: "轿车引擎加速声·由近渐远"
      events: []

  - sec: 35
    global_sec: 35
    camera_position: "7"
    action_anchor: "轿车继续驶离·暗色块在画面中向巷口侧方缩小·车身在暖亮逆光中从完整剪影变为渐小暗块·尾灯红色点光源在暖金背景中微亮"
    spatial_anchor: "固定远景:Pedro前景剪影不变·碎石地面纵深·巷道墙面透视·轿车从巷口中央移至侧方·体积缩小·巷口暖亮开始恢复完整(不再被轿车遮挡)"
    audio:
      ambience: "轿车引擎声渐远"
      events: []

  - sec: 36
    global_sec: 36
    camera_position: "7"
    action_anchor: "轿车逐渐消失在巷口侧方·暖亮过曝区恢复完整——午后的日常光线重新填满巷口。Pedro前景剪影保持不变·没有起身"
    spatial_anchor: "空巷远景:无车辆·暖亮巷口完整恢复·碎石地面·两侧墙面·头顶一线天·Pedro前景剪影右下——故事未结束·Pedro仍未动"
    prop_state:
      - item: "黑色轿车(O-033)"
        state: "驶离·消失在巷口侧方/巷尾方向·不再可见"
    audio:
      ambience: "轿车引擎声远去至消失·贫民窟远底噪恢复"
      events: []

  - sec: 37
    global_sec: 37
    camera_position: "7"
    action_anchor: "巷口空荡·暖亮逆光完整。碎石地面上球的影子仍在。Pedro前景剪影静止。巷道恢复日常——但紧张感残留在画面中·Pedro的身体语言传递着恐惧未消"
    spatial_anchor: "固定远景:低角度·Pedro剪影右下·碎石地面纵深·箱口暖亮·头顶一线天·排水管·垃圾桶·全部静止·日常恢复但记忆残留"
    character_state:
      - character: "Pedro"
        pose: "蹲姿静止·未起身·身体仍紧缩"
        position: "垃圾桶后方·画面右下前景剪影"
    audio:
      ambience: "贫民窟远底噪(远处人声·狗吠·电视声恢复)"
      events: []

  - sec: 38
    global_sec: 38
    camera_position: "7"
    action_anchor: "最后一个画面静持。Pedro前景剪影·空巷口暖亮·球的影子·冷灰墙面。Pedro没有起身——刚才看到的一切已经改变了他。贫民窟午后的日常恢复了·但在这个男孩的眼睛里·世界已经不同"
    spatial_anchor: "固定远景:全纵深清晰·无运动元素·仅有光影——巷口暖亮渐变至巷内冷灰·Pedro剪影=叙事锚点·静止的时间·等待下一场景"
    audio:
      ambience: "贫民窟远底噪持续·渐渐过渡至下一场景环境声"
      events: []

---

# 场景末状态快照 (供后续场景使用)

```
时间: 午后·阴天·场景结束
巷道: 空无一人·碎石地面·球的影子仍在·垃圾桶靠右墙·巷口暖光完整
Pedro: 蹲在垃圾桶后·未起身·恐惧未消·刚目睹了一场秘密交易
旧足球: 在巷口碎石地上·球的影子在碎石上
黑色轿车: 已驶离·去向不明·车内Rico+金丝眼镜男
Rico: 在驶离的轿车内·已接收手机·信封已交给司机
金丝眼镜男: 驾驶轿车离开·已接收信封

关键未解悬念:
  - Rico是否看到了足球影子? 他停留的几秒意味着什么?
  - Pedro看到了什么? 他理解了多少?
  - 轿车驶向何处? Rico的下一个目的地?
```

---

# 设计签名

> **Agent:** Scene Designer v1.0 (合并式·Shot+Comp)
> **复杂度:** M-Level · 3B标准流程
> **运镜域:** 委托Movement Designer独立执行·本报告不含运镜设计
> **KB覆盖:** 机位域5规则类·构图域12规则类·光影域13规则类·视觉结构4规则类·P0安全全量
> **P-FAL规避:** P-FAL-01~10全部主动规避
> **画布宪法:** 七条铁律全部合规
> **输出格式:** §4(机位域YAML)+§6(构图光影域YAML)·§5(运镜域)委托独立
> **下游消费者:** Movement Designer(§4+§6作为运镜设计输入) · storyboard_planner(Step A2.5·组装TIME_SKELETON) · prompt_composer(Step A3·global_anchors+frames_soft消费)
> **独立验证:** 待 Shot Reviewer + Visual Reviewer 双域并行审查·Movement Reviewer审查Movement Designer独立输出
>
> **v1.0 · 2026-07-07 · Scene Designer v1.0 Shot+Comp合并产出**
> **关联文件:** EP14_S2_SCENE_DESIGNER.md · CONTEXT_PACKAGE_EP14.md · ANCHOR_BASELINE_EP14.md · IMAGE_AUDIT_EP14.md · OBJECT_TIMELINE_EP14.md
> **替代:** 原三Agent串行链(Shot Architect + Composition Designer) -> 单一Scene Designer Shot+Comp合并式输出
> **场景设计完成:** 7镜·39秒·巷道+轿车内·悬疑/偷窥主导·双空间·三重色温系统
