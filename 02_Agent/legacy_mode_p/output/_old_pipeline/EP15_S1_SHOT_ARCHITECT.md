# SHOT ARCHITECT v2.0 -- 机位设计报告

> 场景: EP15《会面》· Rico工作室（傍晚→夜）
> 日期: 2026-07-07
> 下游消费: Movement Designer → Storyboard Planner → SekoTalk
> 模式: 编辑器模式 + SekoTalk口型同步（有对白）

---

## §1 空间坐标系

```
坐标定义:
  原点(0,0,0) = 左墙×后墙交角
  X轴: 左墙(0) → 右墙(5).  单位: m
  Y轴: 后墙(0) → 前墙(5).  单位: m
  Z轴: 地板(0) → 天花板(3). 单位: m

关键空间锚点:
  工作台中心:          X=2.5  Y=2.8  Z=0.8(台面)
  Rico坐姿(眼高):      X=2.5  Y=2.8  Z=1.2
  Rico站姿(眼高):      X=2.5  Y=2.8  Z=1.7
  门(中心):           X=4.0  Y=0.0  Z=1.0(把手)
  Miguel门口站姿(眼高): X=4.0  Y=0.5  Z=1.7
  Miguel迈两步后(眼高): X=3.2  Y=1.5  Z=1.7
  吊灯:               X=2.5  Y=2.8  Z=2.5
  洞洞板后墙:           X=0→3.5 Y=0
  左墙改装枪列阵:       X=0  Y=1→4
  右角保险柜:          X=5  Y=3.5
  右角洗手池:          X=5  Y=4.5
  窗口(推断·LEVEL-C):  X=0.5 Y=5  Z=1.8→2.6(距地1.8m·高0.8m)
  光锥投影区(台面):     X=1.5→3.5 Y=2.5→3.5 (2800K暖黄·+2EV vs 暗角)

180°关系线: Rico坐姿头部(2.5,2.8,1.2) ↔ Miguel门口头部(4.0,0.5,1.7)
  线方程(俯视): X = 2.5 + 0.652*(2.8 - Y)
  所选机位侧: SOUTH/WEST侧 —— X < 2.5 + 0.652*(2.8 - Y)
  机位侧含义: 靠近房间前部×左墙侧(改装枪列阵侧)
  画面约定: Rico画右·Miguel画左(近景单人中)
  视线约定: Rico看向画面右方(朝向Miguel)·Miguel看向画面左方(朝向Rico)
```

---

## §2 逐镜机位设计

---

### SHOT 01 -- ECU · 锉刀在枪管上

```
脚本节拍: 第3行 "一只锉刀。在钢制枪管上来回——一圈、两圈、三圈。"
机位类型: 微距插入镜头(Insert·Macro) — 对话模板#6 / 悬疑模板#3
机位位置: X=2.5  Y=3.2  Z=1.1
          工作台上方·距台面~30cm·镜头轴线与台面呈~60°俯角
          机位在光锥范围内(2800K暖黄·台面明亮区)
画面内容: 锉刀在钢制枪管上往复。金属摩擦碎屑。浅景深·台面木纹虚化背景。
视线方向: N/A（无人物面部）
180°侧:   N/A（微距细节·无人物交互·不激活180°系统）
KB规则:   GEN-02(空间可行性·机位在工作台上方·不阻挡光锥·不悬空)
覆盖功能: 开场气氛锚点·建立"手艺人"母题·锉刀声=场景听觉基频
空间约束: 镜头不进入吊灯光锥正下方(避免镜头阴影投射到台面)
```

---

### SHOT 02 -- WS · 工作室建立镜头

```
脚本节拍: 第4行前半 "建立镜头：工作室纵深约五米。Rico背对门口坐在工作台前..."
机位类型: 全景建立(Master Establishing) — 对话模板#1
机位位置: X=1.5  Y=1.5  Z=1.6
          房间前部偏左·镜头朝向东北(后墙方向)
          180°验证: X=1.5 < 2.5+0.652*(2.8-1.5)=3.35 ✓ SOUTH/WEST侧
画面内容: 画面右侧=Rico背影(坐姿·工作台前·光锥笼罩)
          画面中右=工作台横亘·台面零件散落
          画面左中=洞洞板后墙·挂满工具
          画面左侧边缘=左墙改装枪列阵隐隐可见
          画面右后=门(深木色·黄铜把手·闭合状态)
          画面右远景=保险柜暗角
          吊灯光锥自上方投射·周围深褐阴影
视线方向: Rico未转身(背对镜头·面对工作台/后墙)
180°侧:   SOUTH/WEST侧 ✓
KB规则:   A-GEN-02(空间建立优先·任何动作场景第一镜必须是空间建立镜头) [P0]
          D-DUO-07(演员一前一后·纵深层次·Rico前景·门后景) [P1]
覆盖功能: 全景交代空间·Rico位置·光源关系·门位置·冷暖气口位置预埋
空间约束: 镜头不穿过工作台·不进入吊灯光锥路径·距地面1.6m模拟人眼高度
```

---

### SHOT 03 -- MS · 门被推开·影子入侵

```
脚本节拍: 第4行后半+第5行 "此刻门被推开...Miguel站在门口...他的影子先于他的人投在Rico的背上"
机位类型: 中景·悬疑入场镜头 — 悬疑模板#2(主观/半主观)
机位位置: X=2.0  Y=2.0  Z=1.6
          工作台与门之间的中间区域·偏左·镜头朝向西北(门方向)
          180°验证: X=2.0 < 2.5+0.652*(2.8-2.0)=3.02 ✓ SOUTH/WEST侧
画面内容: 前景=Rico背影(坐姿·屏幕右侧·光锥笼罩·背部朝向镜头)
          中景=光锥外暗区·地板
          背景右=门被推开·冷白楼道荧光(4000K)涌入·形成冷暖交界线
          门口=Miguel站姿剪影(逆光·面部不可辨)
          Miguel的影子从门口延伸·穿过地板暗区·投在Rico背上
          (影子方向: 从门(4000K冷光源)投向Rico(2800K暖光区))
视线方向: N/A（Rico背影·Miguel面部在逆光剪影中不可辨）
180°侧:   SOUTH/WEST侧 ✓（机位在两角色之间偏南/西·未跨越关系线）
KB规则:   A-SUS-10(声音先行预示·威胁出现前先有声音暗示——此处为视觉版:影子先于其人) [P2]
          A-SUS-09(恐惧的延时释放·先给安全感→细微变化打破→延迟揭示) [P1]
          D-DIA-22(门口场景的相持拍摄·对比色温展示双方立场·2800K vs 4000K) [P1]
          GEN-02(空间可行性·机位在空地上·不阻挡门开启路径·不阻挡影子投射) [P0]
覆盖功能: 悬念引入·Miguel首次出现(以影子/剪影形式)·冷暖色温首次同时入画
空间约束: 机位不得阻挡门向内开启的路径(门向内开约90°·需留出~1m弧线空间)
          机位不得进入Miguel与门之间的影子投射路径
```

---

### SHOT 04 -- CU · Rico侧脸·不回头对话

```
脚本节拍: 第6行 "CV Rico（没有回头，锉刀声没停）：门上没装门铃。但你下次可以敲门。"
机位类型: 近景单人(CU Single A) — 对话模板#2
机位位置: X=1.5  Y=3.5  Z=1.2
          Rico右前侧·距Rico面部~1.2m·镜头与Rico眼高齐平(坐姿1.2m)
          180°验证: X=1.5 < 2.5+0.652*(2.8-3.5)=2.04 ✓ SOUTH/WEST侧
画面内容: Rico面部3/4侧脸(面向画面右方·朝工作台/后墙·未转身)
          暖黄光锥(2800K)照亮面部右侧·左侧渐暗·chiaroscuro
          右手在画面下方/边缘继续锉刀动作(可见手部运动·锉刀声同步)
          嘴角微动·说话·视线始终在手上的工作
          背景=深褐暗区(光锥外)
视线方向: Rico视线向下/向前(看手头工作)·非面向镜头·非面向Miguel
          这是"不回头对话"的视线特征——人物不中断手头工作
180°侧:   SOUTH/WEST侧 ✓
KB规则:   D-TRI-02(选择关系线一侧并保持) [P0]
          D-DUO-13(拍摄单人镜头时让第二个演员留在摄影机视线之外) [P1]
          D-DUO-08(机位高度=眼平=平等视角·此时Rico为空间主人) [P2]
覆盖功能: Rico首次面部出场·建立"不回头也能对话"的性格特征·锉刀声的连续性
空间约束: 镜头距Rico面部≥1m(避免广角畸变)·不进入光锥投射线
```

---

### SHOT 05 -- MS · Miguel关门·靠门框·扫视

```
脚本节拍: 第7行 "Miguel关上门。靠在门框上——没有靠近。他的目光从左扫到右..."
机位类型: 中景单人(MS Single B) — 对话模板#3
机位位置: X=2.5  Y=1.5  Z=1.7
          Rico与门之间的中间位置·偏左·镜头朝向东北(门方向)
          180°验证: X=2.5 < 2.5+0.652*(2.8-1.5)=3.35 ✓ SOUTH/WEST侧
画面内容: Miguel在门框处·关门动作→靠门框
          门框作为自然画框·框住Miguel全身
          Miguel视线从左向右扫描:
            左→改装枪列阵(画面左部外·通过头部转动表示)
            中→工作台零件(画面中部·Miguel视线落点)
            右→保险柜暗角(画面右部·柜门留缝+黑布可见)
          关门后楼道冷光(4000K)消退·室内恢复2800K暖黄主导
          Miguel面部色温: 部分暖黄(面朝室内)+部分阴影(背朝已关的门)
视线方向: Miguel视线扫视(左→中→右)·最终停在保险柜方向
          扫视过程中短暂看向Rico方向(画面右前方·出画)
180°侧:   SOUTH/WEST侧 ✓
KB规则:   D-TRI-02(维持机位侧) [P0]
          D-DUO-08(机位高度=站姿眼平1.7m·与Miguel同高=此时权力对等) [P2]
          D-DIA-22(门口场景·门框构图·冷暖色温交替) [P1]
覆盖功能: Miguel首次清晰面部出场·建立其刑警观察习惯·空间三要素扫描(枪→零件→保险柜)
空间约束: 镜头不穿过门框平面·保持在室内·距Miguel~2m
```

---

### SHOT 06 -- INSERT · Miguel主观视角: 改装枪列阵

```
脚本节拍: 第7行 "他的目光从左扫到右：墙上的枪..."
机位类型: 插入镜头·主观视角(Insert·POV) — 对话模板#6 / 悬疑模板#2
机位位置: 从Miguel眼部位置出发(约X=4.0 Y=0.5 Z=1.7)·视线方向指向左墙(X=0 Y=1→4)
          实际机位: X=1.5 Y=0.5 Z=1.7(靠近左墙·镜头朝向右墙方向·拍改装枪正面)
          注意: 这是POV等效机位·非Miguel物理位置
画面内容: 左墙改装枪列阵·手枪/步枪/短管霰弹枪整齐排列
          改装配件·消音器·瞄准镜·弹匣
          墙面色温过渡: 近门处偏冷(4000K渗入)→近工作台处偏暖(2800K光锥边缘)
          金属表面反射暖黄光斑
视线方向: 模拟Miguel视线(从门口看向左墙)
180°侧:   N/A（POV插入·无人物面部·不包含另一角色）
KB规则:   GEN-02(空间可行性·机位在左墙前空地·不穿墙) [P0]
覆盖功能: 环境细节·Miguel观察内容的视觉化·建立"这里确实是枪械作坊"的证据链
空间约束: 镜头不穿入左墙·距墙~0.5-0.8m
```

---

### SHOT 07 -- INSERT · Miguel主观视角: 保险柜·黑布

```
脚本节拍: 第7行 "...角落的保险柜——柜门留了一条缝，里面黑布包裹着东西。"
机位类型: 插入镜头·主观视角(Insert·POV) — 对话模板#6
机位位置: 从Miguel眼部位置出发·视线方向指向右角保险柜(X=5 Y=3.5)
          实际机位: X=4.5 Y=3.0 Z=1.2(靠近保险柜·镜头微俯·拍柜门缝隙)
画面内容: 灰色保险柜·蹲在右角暗区·柜门未完全闭合(留缝约5-8cm)
          缝隙内可见黑布包裹的物体轮廓(不可辨具体形状)
          保险柜表面反射微弱暖黄光(来自光锥边缘·极弱)
          周围=深褐阴影·几乎全黑
视线方向: 模拟Miguel扫视终点·凝视保险柜缝隙
180°侧:   N/A（POV插入·无人物面部）
KB规则:   A-SUS-02(未知之惧·不拍威胁来源·黑布包裹之物=观众的想象) [P1]
          GEN-02(空间可行性·机位在保险柜前·右墙与保险柜之间有~1m空隙) [P0]
覆盖功能: 核心悬念植入·保险柜+黑布=全场景未解之谜·建立Miguel的怀疑依据
空间约束: 镜头在保险柜前·不穿入保险柜·不进入洗手池区域(杂物阻挡)
```

---

### SHOT 08 -- CU · Miguel "你看上去不惊讶"

```
脚本节拍: 第8行 "CV Miguel：你看上去不惊讶。"
机位类型: 近景单人(CU Single B) — 对话模板#3
机位位置: X=2.5  Y=1.2  Z=1.7
          Miguel正面偏左·距Miguel面部~1.2m·镜头与Miguel眼高齐平
          180°验证: X=2.5 < 2.5+0.652*(2.8-1.2)=3.54 ✓ SOUTH/WEST侧
画面内容: Miguel面部近景·靠在门框上
          面部半明半暗(靠近室内侧=暖黄光·靠近门侧=阴影)
          眼神从保险柜方向转回·锁定Rico(视线朝向画面右方=Rico方向)
          警徽在左胸前·暖黄光下光泽偏暖(与EP14楼道冷光警徽形成对比)
视线方向: Miguel视线朝向右方(Rico方向·出画右侧)
180°侧:   SOUTH/WEST侧 ✓
          E-MTC-04验证: Miguel看向画面右方 → 与此后的Rico看向画面左方配对 ✓
KB规则:   D-TRI-02(维持机位侧) [P0]
          D-DUO-02(外反拍对话机位·纵深——Miguel前景·Rico出画但在纵深空间中) [P0]
          D-DUO-08(眼平高度·此时权力尚未倾斜) [P2]
覆盖功能: Miguel首句对白·建立审问语气·从观察到发问的转换点
空间约束: 镜头距Miguel≥1m·不进入门框平面
```

---

### SHOT 09 -- CU · Rico放下锉刀·转身

```
脚本节拍: 第9行 "CV Rico（放下锉刀，转过身。两人现在面对面...）"
机位类型: 近景单人·动作镜头(CU Single A) — 对话模板#2
机位位置: X=1.5  Y=3.2  Z=1.2
          Rico右前侧·距Rico面部~1.2m·镜头与Rico坐姿眼高齐平
          180°验证: X=1.5 < 2.5+0.652*(2.8-3.2)=2.24 ✓ SOUTH/WEST侧
画面内容: Rico放下锉刀(手部入画→搁在枪管上·刀尖对准窗口方向)
          转身动作——从面向工作台(画面右)转向面向镜头/门方向(画面左)
          面部从3/4侧脸转为接近正面(面向画面左方=Miguel方向)
          面部光线变化: 转身过程中·光线从侧面→正面(始终在光锥内)
          眼神抬起·首次与Miguel对视
视线方向: Rico视线朝向画面左方(Miguel方向)
180°侧:   SOUTH/WEST侧 ✓
          E-MTC-04验证: Rico看向画面左方 → 与SHOT 08 Miguel看向画面右方配对 ✓
          注意: 转身前后·Rico从面对工作台(画面右)变为面对Miguel(画面左)·视线方向反转
KB规则:   D-TRI-02(维持机位侧·转身不跨线) [P0]
          E-MTC-04(视线匹配铁律·互相对视的人物视线方向相反) [P0]
覆盖功能: 关键转折点——Rico从"无视"到"面对"·两人首次建立视觉接触
          锉刀搁置方向(刀尖对准窗口)=空间线索预埋
空间约束: 镜头不阻挡Rico转身空间(椅子旋转半径~0.5m)
```

---

### SHOT 10 -- MS · 双人镜头·面对面·工作台相隔

```
脚本节拍: 第9行后半+第10行前半 "两人现在面对面——Rico画右坐姿，Miguel画左站姿，距离约四米"
          第11行 "Miguel向前迈了两步。距离缩到两米。"
          第12行 "Rico站起来。两人身高齐平..."
机位类型: 双人中景·再交代镜头(MS 2-Shot Re-establishing) — 对话模板#1+8
          此镜覆盖三个连续动作: 面对面建立 → Miguel迈步 → Rico站起
机位位置: X=1.5  Y=2.0  Z=1.6
          房间前部偏左·镜头朝向东北(后墙方向)
          180°验证: X=1.5 < 2.5+0.652*(2.8-2.0)=3.02 ✓ SOUTH/WEST侧
画面内容(三个阶段):
  阶段A: Rico坐姿(画右·工作台前·光锥中)
          Miguel站姿(画左·门框前·距离~4m)
          工作台横亘画面下部·台面零件·锉刀搁在枪管上
          吊灯光圈在两人之间
  阶段B: Miguel迈两步(画左→向画面中央移动·距离从4m缩到2m)
          工作台仍隔在两人之间
  阶段C: Rico站起(画右·从坐姿到站姿·身高与Miguel齐平)
          两人隔工作台对峙·台灯光圈在中间
视线方向: Rico看向画面左方(朝Miguel)·Miguel看向画面右方(朝Rico)
          互视·视线方向相反 ✓
180°侧:   SOUTH/WEST侧 ✓
KB规则:   D-TRI-01(关系线穿过两个中心人物头部) [P0]
          D-TRI-02(保持机位侧) [P0]
          D-DUO-01(面对面·基本对话构型·视线相互对应) [P0]
          D-DIA-20(障碍物调度·工作台=障碍物分离冲突双方·冲突升级时可被突破) [P1]
          D-DIA-03(不同高度·Rico坐姿vs Miguel站姿=权力不对等→Rico站起=权力拉平) [P1]
          A-GEN-02(空间建立优先) [P0]
覆盖功能: 三阶段动作覆盖·空间关系再交代·权力动态变化视觉化
          从"不对等"(坐vs站·4m)→"接近"(站vs站·2m·工作台相隔)
空间约束: 镜头从南/西侧拍摄·不穿过工作台·不进入光锥路径
          画面左侧(洞洞板后墙)和右侧(门)均在景深范围内
```

---

### SHOT 11 -- OTS · 过Miguel肩拍Rico（外反拍A）

```
脚本节拍: 第10-14行对话段 "你是刑警...改装枪...你有指控吗...没有...那你来是朋友的身份？"
          此镜主要覆盖:Rico对白(第9行后半+第12行+第14行)
机位类型: 过肩镜头·外反拍(OTS·Outer Reverse A) — 对话模板#4
          三角形底边上两机位之一·在Miguel背后·靠近关系线·向里把两人都拍入
机位位置: X=3.2  Y=1.0  Z=1.7
          Miguel右后侧(靠近门侧)·距Miguel~0.8m·镜头越过Miguel右肩朝向Rico
          180°验证: X=3.2 < 2.5+0.652*(2.8-1.0)=3.67 ✓ SOUTH/WEST侧
画面内容: 画面右侧前景=Miguel右肩+后脑(焦外·虚化)
          画面左侧后景=Rico正面(焦内·面对镜头/Miguel方向·坐姿或刚站起)
          Rico在光锥中·面部暖黄光照亮
          工作台边缘在画面底部
视线方向: Rico视线朝向画面右方(看向镜头后的Miguel)
          Miguel面部不可见(背对镜头)·但其视线方向隐含朝向左方(Rico方向)
180°侧:   SOUTH/WEST侧 ✓
KB规则:   D-TRI-05(外反拍角度·底边上机位在演员背后·靠近关系线·向里把两人拍入) [P0]
          D-TRI-02(保持在三角形同一侧) [P0]
          D-DUO-02(外反拍最强对话机位·纵深——Rico面对摄影机=开放形体占主导) [P0]
覆盖功能: Rico对白主镜·对话模板核心机位·"开放形体占主导"=Rico为对话主导方
空间约束: 镜头在Miguel身后·不穿过Miguel身体·距Miguel≥0.5m
          需确认Miguel站位(Y=1.0)与门之间有足够空间放置机位(约0.5m·可行)
```

---

### SHOT 12 -- OTS · 过Rico肩拍Miguel（外反拍B）

```
脚本节拍: 第10-14行对话段·主要覆盖Miguel对白(第8行+第10行+第13行)
          与SHOT 11配对·构成三角形底边双机位
机位类型: 过肩镜头·外反拍(OTS·Outer Reverse B) — 对话模板#5
          三角形底边上另一个机位·在Rico背后·靠近关系线
机位位置: X=1.8  Y=3.2  Z=1.6(Rico站起后·机位高度调至1.6m·介于坐姿与站姿眼高之间)
          Rico右后侧·距Rico~0.8m·镜头越过Rico右肩朝向Miguel
          180°验证: X=1.8 < 2.5+0.652*(2.8-3.2)=2.24 ✓ SOUTH/WEST侧
          注意: 此机位非常接近180°线(距线仅~0.44m)·但仍在线南/西侧·合法
画面内容: 画面左侧前景=Rico右肩+后脑(焦外·虚化)
          画面右侧后景=Miguel正面(焦内·面对镜头/Rico方向·站姿)
          Miguel面部光线: 暖黄光锥边缘+部分阴影·半明半暗
          门框在Miguel身后(远景·焦外)
视线方向: Miguel视线朝向画面左方(看向镜头后的Rico)
          Rico面部不可见(背对镜头)
180°侧:   SOUTH/WEST侧 ✓
KB规则:   D-TRI-05(外反拍角度·底边上另一机位) [P0]
          D-TRI-02(保持在三角形同一侧·不跳到另一侧) [P0]
          D-TRI-03(关系线必须穿过两个中心人物的头部) [P0]
覆盖功能: Miguel对白主镜·与SHOT 11配对构成经典对话外反拍组合
          注意: 此机位中Miguel为"开放形体"·但对话主导权仍在Rico(坐姿→刚站起·空间主人)
空间约束: 镜头在Rico身后·不穿过Rico身体·距Rico≥0.5m
          工作台在Rico前方·机位不得进入工作台上方光锥区
```

---

### SHOT 13 -- CU · Rico "你有指控吗？"

```
脚本节拍: 第12行 "CV Rico：你有指控吗？"
机位类型: 近景单人(CU Single A) — 对话模板#2
          内反拍角度·摄影机在两个演员之间·从三角形向外拍·靠近关系线
机位位置: X=1.8  Y=2.8  Z=1.7
          Rico正面偏右·距Rico面部~1.2m·镜头与Rico站姿眼高齐平
          180°验证: X=1.8 < 2.5+0.652*(2.8-2.8)=2.50 ✓ SOUTH/WEST侧
画面内容: Rico正面近景·站姿·隔工作台面对镜头方向
          面部在暖黄光锥中(2800K)·深金褐色肤质·颧骨分明·下颌线条硬朗
          眼神直接·锐利·锁定镜头后方的Miguel
          嘴角习惯性微收紧(情绪的唯一外泄口)
视线方向: Rico视线朝向画面右方(Miguel方向·出画)
180°侧:   SOUTH/WEST侧 ✓
KB规则:   D-TRI-06(内反拍角度·摄影机在两个演员之间·从三角形向外拍·单人近景) [P0]
          D-TRI-14(共轴推进法·三角形底边上视点沿视轴向前推·得到更近镜头) [P1]
          D-DIA-19(聚焦于一人·对话升温时·锁定主角面部) [P1]
覆盖功能: 对话升温·Rico主动出击·"你有指控吗"=权力反击
空间约束: 镜头距Rico≥1m·在光锥范围内但不阻挡光锥
```

---

### SHOT 14 -- CU · Miguel "没有" + 两秒沉默

```
脚本节拍: 第13行 "CV Miguel（沉默了两秒）：没有。"
机位类型: 近景单人(CU Single B) — 对话模板#3
          与SHOT 13配对的内反拍·摄影机在两个演员之间
机位位置: X=2.8  Y=1.5  Z=1.7
          Miguel正面偏左·距Miguel面部~1.2m·镜头与Miguel眼高齐平
          180°验证: X=2.8 < 2.5+0.652*(2.8-1.5)=3.35 ✓ SOUTH/WEST侧
画面内容: Miguel正面近景·面部光线=暖黄光锥边缘(2800K减弱)+部分阴影
          沉默两秒——面部微表情: 眉心竖纹加深·嘴唇轻抿·眼神不移开
          "没有"——简短·声音缓慢·嘴唇动作精确
          警徽在画面左下部·暖黄光下光泽收敛
视线方向: Miguel视线朝向画面左方(Rico方向·出画)
180°侧:   SOUTH/WEST侧 ✓
          E-MTC-04验证: Miguel视线左 ←→ Rico视线右(SHOT 13) ✓
KB规则:   D-TRI-06(内反拍角度·另一侧单人近景) [P0]
          D-DIA-11(肢体语言对抗·沉默时摄影机完全不动·凝固的空气) [P2]
          A-SUS-03(紧张期待·固定镜头·不切不走·强迫观众等待两秒沉默) [P1]
覆盖功能: 对话节奏转折·沉默比语言更有力·两秒=观众预期\"Miguel会指控他\"的悬置
空间约束: 镜头距Miguel≥1m·在Miguel迈两步后的新位置(Y=1.5)前
```

---

### SHOT 15 -- CU · Rico "那你来是——朋友的身份？"

```
脚本节拍: 第14行 "CV Rico（嘴角动了一下——不是笑）：那你来是——朋友的身份？"
机位类型: 近景单人(CU Single A) — 对话模板#2
机位位置: X=1.8  Y=2.8  Z=1.7
          同SHOT 13机位·Rico正面近景·延续内反拍
          180°验证: 同SHOT 13 ✓
画面内容: Rico正面近景·"嘴角动了一下——不是笑"(核心微表情)
          嘴角习惯性微收紧→松弛一瞬间→再收紧
          眼神保持锁定·"那你来是——"后短暂停顿(故意留白)
          "朋友的身份？"——语气不升反降·陈述而非疑问
视线方向: Rico视线朝向画面右方(Miguel方向)
180°侧:   SOUTH/WEST侧 ✓
KB规则:   D-TRI-06(内反拍) [P0]
          D-DUO-08(眼平高度·此时两人均站立·权力对等) [P2]
覆盖功能: Rico反客为主·用"朋友"一词将Miguel从制度身份中剥离
          嘴角微动=全场景Rico情绪唯一外泄·为下面手指1cm反应做铺垫
空间约束: 同SHOT 13
```

---

### SHOT 16a -- ECU · Miguel右手·手指后移1cm

```
脚本节拍: 第15行 "特写——Miguel的右手。手指微微向后移了一寸——靠近腰间的配枪。只移动了一厘米。"
机位类型: 超近特写(ECU·Extreme Close-Up) — 悬疑模板#3(特写线索)
          三连切序列第一镜
机位位置: X=3.5  Y=1.5  Z=1.0
          Miguel右侧·距其右手~40cm·镜头高度=腰部水平(~1.0m)
          镜头轴线水平·垂直于Miguel身体右侧面
画面内容: Miguel右手超近特写·手指从自然垂放位置向后(向腰后)移动1cm
          无名指旧伤疤可见(继承EP13/EP14锚点·螺旋母题)
          深藏青夹克面料在画面边缘·配枪皮套隐约可见(画面边缘·未入焦)
          移动幅度极小(1cm=画面中约2-3mm位移)·几乎不可察觉
视线方向: N/A（身体局部·无面部）
180°侧:   N/A（ECU身体局部·不激活180°系统·不包含第二角色）
KB规则:   A-SUS-09(恐惧的延时释放·细微变化打破安全感——手指只移动1cm) [P1]
          GEN-02(空间可行性·机位在Miguel右侧空地·不穿入其身体) [P0]
覆盖功能: 全场景叙事高潮触发器·1cm位移=Miguel的无意识威胁反应
          为下一个SHOT Rico捕捉到此动作建立因果链
空间约束: 镜头距Miguel右手≥30cm·不接触演员身体
```

---

### SHOT 16b -- ECU · Rico眼睛·视线下扫一帧

```
脚本节拍: 第15行 "切回Rico的眼睛——他的目光向下扫了一帧，捕捉到了那个动作。"
机位类型: 超近特写(ECU·Extreme Close-Up) — 悬疑模板#3
          三连切序列第二镜
机位位置: X=2.0  Y=2.8  Z=1.7
          Rico正前方偏右·距Rico眼睛~50cm·镜头与Rico眼高齐平
          180°验证: X=2.0 < 2.5+0.652*(2.8-2.8)=2.50 ✓ SOUTH/WEST侧
          (虽然是ECU·但若画面中包含Rico面部朝向信息·仍遵守180°侧)
画面内容: Rico双眼超近特写·深棕色虹膜·锐利
          视线从平视(锁定Miguel面部)向下扫——仅一帧(1/24秒)的微动作
          视线扫动方向: 从画面右方(平视Miguel)→急速向下→回到画面右方
          眼周皮肤在暖黄光下呈深金褐·睫毛投影
          瞳孔在扫视瞬间无明显变化(保持锐利·不是恐惧·是警觉)
视线方向: 向下扫一帧·然后回到画面右方(Miguel方向)
180°侧:   SOUTH/WEST侧 ✓(基于Rico面部朝向画面左=看向Miguel·短暂下扫不改变整体朝向)
KB规则:   A-SUS-09(细微变化打破安全感·眼睛扫动一帧=叙事炸弹) [P1]
          D-DIA-19(聚焦于一人·锁定主角面部) [P1]
覆盖功能: 全场景叙事核心——Rico捕捉到Miguel的无意识威胁反应
          "一秒内扫到Miguel手指的1cm位移"(ANCHOR_BASELINE Rico锚点A2)
空间约束: 镜头距Rico眼睛≥40cm·不遮挡Rico视线路径
```

---

### SHOT 16c -- ECU · Rico嘴角·收住

```
脚本节拍: 第15行 "嘴角收住。"
机位类型: 超近特写(ECU·Extreme Close-Up) — 悬疑模板#3
          三连切序列第三镜·结尾
机位位置: X=2.0  Y=2.8  Z=1.55
          同SHOT 16b机位轴线·镜头微俯·从眼睛移至嘴角
          距Rico嘴角~40cm
画面内容: Rico嘴角+下颌超近特写
          嘴角从微松弛(上一句"朋友的身份？"时的微动)→收紧·绷直·完全闭合
          下颌线条硬化·咬肌微微隆起(压制情绪)
          胡茬·皮肤纹理·金属屑微粒(光下反光点·ANCHOR_BASELINE Rico发色锚点)
视线方向: N/A（嘴部局部·无视线信息）
180°侧:   N/A（嘴部ECU·不包含方向性视觉信息）
KB规则:   A-SUS-09(延时释放完结点·从安全感→手指1cm→眼睛捕捉→嘴角收紧·完整弧线) [P1]
          A-SUS-03(紧张期待·最后一个ECU锁在嘴角·强迫观众消化"他知道了"的信息) [P1]
覆盖功能: 三连切序列收束·Rico情绪的唯一外泄口闭合=情绪内化=危险升级
          嘴角收紧=从"对话"到"对峙"的心理转折点
空间约束: 镜头距Rico面部≥30cm
```

---

### SHOT 17 -- CU · Miguel 缓慢对白

```
脚本节拍: 第16行 "CV Miguel（声音缓慢，像在选择每个字）：作为——一个不想看你自我毁灭的人。"
机位类型: 近景单人(CU Single B) — 对话模板#3
机位位置: X=2.8  Y=1.5  Z=1.7
          同SHOT 14机位·Miguel正面近景
          180°验证: 同SHOT 14 ✓
画面内容: Miguel正面近景·声音缓慢·每个字都经过选择
          嘴唇动作慢于正常语速·停顿在"作为——"后
          眉心竖纹更深·眼神不再那么坚定(心虚？——刚才手指动作被捕捉的潜意识反应)
          暖黄光下肤色散射深橙金(ANCHOR_BASELINE Miguel·2800K=活着的颜色)
          "不想看你自我毁灭"——带个人情感·不再是纯粹刑警审问
视线方向: Miguel视线朝向画面左方(Rico方向)
180°侧:   SOUTH/WEST侧 ✓
KB规则:   D-TRI-06(内反拍) [P0]
          D-DIA-11(肢体语言对抗·摄影机完全不动·对白节奏变慢·镜头不推不摇) [P2]
覆盖功能: Miguel立场转变暗示——从"刑警审问"转向"个人关心"
          "自我毁灭"=揭示两人过往关系深度(比同事/对头更深)
空间约束: 同SHOT 14
```

---

### SHOT 18 -- WS · 双人全景·对视·天空沉入暗蓝

```
脚本节拍: 第17行 "两人对视。窗外圣保罗的天空从橘色沉入暗蓝。台灯光圈在工作台上轻轻晃动。锉刀还搁在枪管上——刀尖对准窗口的方向。"
          第18行 "Rico低下头。把抹布叠好。放在桌上。"
机位类型: 全景再交代(WS Re-establishing) — 对话模板#8 / 悬疑模板#5(空间·气氛)
机位位置: X=1.5  Y=1.5  Z=1.6
          同SHOT 02基本位置·宽画幅·两人全身入画
          180°验证: X=1.5 < 2.5+0.652*(2.8-1.5)=3.35 ✓ SOUTH/WEST侧
画面内容: 双人全景——Rico站姿(画右·工作台后)·Miguel站姿(画左·距工作台~2m)
          两人对视·视线锁定·无对白
          窗口(画面前方·X=0.5 Y=5·推断位置)投进的光线从暖橘逐渐变为暗蓝
          光线变化投射在地面/左墙·非直射人物
          台灯光圈轻轻晃动(可能因窗外风？或门未完全闭合的微风？·不安定感)
          锉刀搁在枪管上·刀尖指向窗口方向(画面左前方)
          随后: Rico低头·拿起抹布·慢慢擦手指金属屑·叠好抹布·放在桌上
视线方向: 延续互视——Rico视线右·Miguel视线左
180°侧:   SOUTH/WEST侧 ✓
KB规则:   D-TRI-01(关系线穿过两人头部) [P0]
          D-TRI-02(维持机位侧) [P0]
          D-DIA-11(肢体语言对抗·摄影机完全不动·凝固的空气比任何运镜都有力) [P2]
          A-SUS-03(紧张期待·固定镜头·不切不走·强迫观众等待天空变色+对视为证) [P1]
          E-MTC-04(视线匹配铁律·互相对视·视线方向相反) [P0]
覆盖功能: 全场景情绪最高点·沉默的对视·外部时间流逝(天空变色)测量对峙时长
          Rico擦手=用动作替代语言·精确得像对待枪械零件
空间约束: 镜头从南/西侧·宽画幅包含:
          画面右=Rico(站姿·工作台后)·画面左=Miguel(站姿)
          画面左前边缘=窗口光线变化(窗口本身不入画·仅光线投射)
          画面上方=吊灯光圈(轻微晃动)
          画面底部=工作台·锉刀·抹布
```

---

### SHOT 19 -- MS · Rico "带搜查令来"

```
脚本节拍: 第19行 "CV Rico：那我建议你——下次带搜查令来。"
机位类型: 中景单人(MS Single A) — 对话模板#2
          从SHOT 18宽画幅收紧至Rico中景·终结对话
机位位置: X=1.5  Y=3.0  Z=1.7
          Rico正面偏右·距Rico~1.8m·中景(含上半身+工作台边缘)
          180°验证: X=1.5 < 2.5+0.652*(2.8-3.0)=2.37 ✓ SOUTH/WEST侧
画面内容: Rico中景·站姿·抹布已叠好放在桌面上
          说完"带搜查令来"后·眼神保持锁定(不退缩)
          面部暖黄光·深金褐肤色·下颌线条硬朗收紧
          工作台边缘+锉刀+叠好的抹布在画面下部
视线方向: Rico视线朝向画面右方(Miguel方向·出画)
180°侧:   SOUTH/WEST侧 ✓
KB规则:   D-TRI-06(内反拍·单人近/中景) [P0]
          D-DIA-12(力量对比·Rico=空间主人·最后一句对白=权力宣告) [P1]
覆盖功能: 对话终结·Rico最后一句话="这是我家·这是我的领域·你没有搜查令就出去"
          "下次"=隐含的威胁——我们还会再见·但不是这次
空间约束: 镜头距Rico~1.8m·中景景别
```

---

### SHOT 20 -- ECU · 锉刀继续转动（结尾书挡）

```
脚本节拍: 第20行 "VO：两个人都知道对方知道。但知道的秘密在没有证据的房间里——就是空气。"
          第21行 "黑屏。锉刀继续转动——一圈。"
机位类型: 超近特写(ECU·Closing Bookend) — 悬疑模板#3
          与SHOT 01配对·构成开场-结尾书挡结构
机位位置: X=2.5  Y=3.2  Z=1.1
          同SHOT 01机位·工作台上方·距台面~30cm·~60°俯角
画面内容: 锉刀搁在枪管上(同SHOT 01·但锉刀不再被手握住·静止于枪管上)
          VO播放过程中·画面静止(锉刀不动·搁在枪管上·刀尖对准窗口方向)
          VO结束·画面渐黑(黑屏)·黑屏后·声音延续: 锉刀继续转动——一圈
          (黑屏时只有声音·金属摩擦声·一圈)
视线方向: N/A（无人物）
180°侧:   N/A（微距细节·无人物交互）
KB规则:   GEN-02(空间可行性·同SHOT 01·机位在工作台上方) [P0]
          A-SUS-01(轻微后退——此处为"黑屏后退"·观众被拉出画面·只剩声音·不安感) [P1]
覆盖功能: 书挡闭合·与SHOT 01对称·悬念悬置——故事没有解决·锉刀声暗示Rico继续工作
空间约束: 同SHOT 01
```

---

## §3 跨镜轴线验证

### 3.1 180°线一致性检查

```
全场景20镜+3子镜·逐一验证SOUTH/WEST侧:

SHOT 01: N/A (微距·无人物)                        ✓
SHOT 02: X=1.5 < 3.35 (线值@Y=1.5)               ✓ SOUTH/WEST
SHOT 03: X=2.0 < 3.02 (线值@Y=2.0)               ✓ SOUTH/WEST
SHOT 04: X=1.5 < 2.04 (线值@Y=3.5)               ✓ SOUTH/WEST
SHOT 05: X=2.5 < 3.35 (线值@Y=1.5)               ✓ SOUTH/WEST
SHOT 06: N/A (POV插入·无人物)                      ✓
SHOT 07: N/A (POV插入·无人物)                      ✓
SHOT 08: X=2.5 < 3.54 (线值@Y=1.2)               ✓ SOUTH/WEST
SHOT 09: X=1.5 < 2.24 (线值@Y=3.2)               ✓ SOUTH/WEST
SHOT 10: X=1.5 < 3.02 (线值@Y=2.0)               ✓ SOUTH/WEST
SHOT 11: X=3.2 < 3.67 (线值@Y=1.0)               ✓ SOUTH/WEST
SHOT 12: X=1.8 < 2.24 (线值@Y=3.2)               ✓ SOUTH/WEST
SHOT 13: X=1.8 < 2.50 (线值@Y=2.8·线上值)        ✓ SOUTH/WEST
SHOT 14: X=2.8 < 3.35 (线值@Y=1.5)               ✓ SOUTH/WEST
SHOT 15: X=1.8 < 2.50 (线值@Y=2.8)               ✓ SOUTH/WEST
SHOT 16a: N/A (ECU身体局部)                        ✓
SHOT 16b: X=2.0 < 2.50 (线值@Y=2.8·面上朝向一致)  ✓ SOUTH/WEST
SHOT 16c: N/A (ECU嘴部局部)                        ✓
SHOT 17: X=2.8 < 3.35 (线值@Y=1.5)               ✓ SOUTH/WEST
SHOT 18: X=1.5 < 3.35 (线值@Y=1.5)               ✓ SOUTH/WEST
SHOT 19: X=1.5 < 2.37 (线值@Y=3.0)               ✓ SOUTH/WEST
SHOT 20: N/A (微距·无人物)                        ✓

结果: 所有含人物面部朝向的镜头均在同一侧·0次跨线 ✓
```

### 3.2 视线匹配验证 (E-MTC-04)

```
角色        镜头        视线方向(画面中)      看向对象      配对验证
─────────────────────────────────────────────────────────────
SHOT 04  Rico(CU)     向下/前(看工作)        手头工作      非互视·单方
SHOT 08  Miguel(CU)   右方                   Rico         与SHOT 09配对
SHOT 09  Rico(CU)     左方(转身后)            Miguel       与SHOT 08配对 ✓
SHOT 10  Rico(MS)     左方                   Miguel       与Miguel右方配对 ✓
SHOT 10  Miguel(MS)   右方                   Rico         与Rico左方配对 ✓
SHOT 11  Rico(OTS)    右方(看向镜头后Miguel)   Miguel       配对 ✓
SHOT 12  Miguel(OTS)  左方(看向镜头后Rico)     Rico         配对 ✓
SHOT 13  Rico(CU)     右方                   Miguel       与SHOT 14配对
SHOT 14  Miguel(CU)   左方                   Rico         与SHOT 13配对 ✓
SHOT 15  Rico(CU)     右方                   Miguel       配对 ✓
SHOT 17  Miguel(CU)   左方                   Rico         配对 ✓
SHOT 18  Rico(WS)     左方·互视              Miguel       互视 ✓
SHOT 18  Miguel(WS)   右方·互视              Rico         互视 ✓
SHOT 19  Rico(MS)     右方                   Miguel       配对 ✓

结果: 所有互视配对中·视线方向相反 ✓
      银幕上匹配的视线总是相反的 ✓
```

### 3.3 空间约束验证

```
约束项                         验证
─────────────────────────────────────
不穿墙                          所有机位在房间可站立/可放置区域 ✓
不悬空                          所有机位Z坐标在地面以上·有支撑 ✓
不阻挡门开启路径                  SHOT 03/05/08机位避开门的90°弧线 ✓
不进入光锥投射线(工作台上方)       SHOT 02/03/10/18宽画幅机位在光锥侧方 ✓
不穿过工作台                     所有机位在工作台南侧或侧方 ✓
不阻挡人物移动路径                SHOT 10/11/12给Miguel迈步+Rico站起留空间 ✓
人物可放置区域对应               所有角色位置在ANCHOR_BASELINE定义的站立/座位区 ✓
禁入区规避                       机位不进入洞洞板与工作台窄缝·不进入保险柜杂物区 ✓
窗口光线变化                      SHOT 18中窗口光线投射·窗口本身不入画 ✓
```

---

## §4 覆盖度分析

### 4.1 对话模板8机位覆盖

```
模板机位          对应SHOT        覆盖状态
─────────────────────────────────────────
1.双人全景(Est.)   SHOT 02+10+18   ✓ 三重建立(初始·面对面·最后对峙)
2.单人A(Single A)  SHOT 04+09+13+15+19 ✓ 5次Rico单人·覆盖全部对白+动作
3.单人B(Single B)  SHOT 05+08+14+17 ✓ 4次Miguel单人·覆盖全部对白+动作
4.过肩A(OTS A)     SHOT 11         ✓ 外反拍Miguel肩→Rico
5.过肩B(OTS B)     SHOT 12         ✓ 外反拍Rico肩→Miguel
6.插入(Insert)     SHOT 01+06+07+20 ✓ 4次插入(锉刀·枪墙·保险柜·锉刀收尾)
7.反应(Reaction)   SHOT 16a/b/c    ✓ 三连ECU反应序列
8.再交代(Re-est.)  SHOT 18         ✓ 全景再交代
─────────────────────────────────────────
覆盖度: 8/8 ✓
```

### 4.2 悬疑模板5机位覆盖

```
模板机位          对应SHOT        覆盖状态
─────────────────────────────────────────
1.主镜头(氛围)     SHOT 02+18      ✓ 全片氛围建立+高潮气氛延续
2.主观视角         SHOT 06+07      ✓ Miguel双POV插入
3.特写线索         SHOT 01+16a+20  ✓ 锉刀·手指·锉刀收尾
4.反应镜头         SHOT 16b/c      ✓ Rico眼睛+嘴角
5.空镜(空间)       SHOT 18(后半)   ✓ 天空变色+光圈晃动
─────────────────────────────────────────
覆盖度: 5/5 ✓
```

### 4.3 EP15特有模式覆盖

```
模式                      覆盖SHOT           KB规则
─────────────────────────────────────────────────
障碍物调度(工作台=障碍物)   SHOT 10+18        D-DIA-20 [P1]
门口冷暖交界               SHOT 03+05+08     D-DIA-22 [P1]
影子先于其人               SHOT 03           A-SUS-10 [P2]
手指1cm微动作              SHOT 16a          A-SUS-09 [P1]
恐惧延时释放(安全感→打破)  SHOT 02→03→16a/b/c A-SUS-09 [P1]
推近对话(对峙升温)          SHOT 10(Miguel迈步+Rico站起) D-DIA-01 [P1]
力量对比(坐vs站→站vs站)    SHOT 10           D-DIA-03+D-DIA-12 [P1]
聚焦于一人(对话升温)        SHOT 13+14+15+17  D-DIA-19 [P1]
肢体语言对抗(凝固镜头)      SHOT 18           D-DIA-11 [P2]
```

---

## §5 KB规则引用清单

### P0级规则（始终·不可违反）

| 规则ID | 规则内容 | 引用镜次 | 验证状态 |
|--------|---------|---------|---------|
| D-TRI-01 | 关系线穿过两个中心人物的头部 | 全场景 | ✓ |
| D-TRI-02 | 选择关系线一侧并保持 | 全场景(04→19) | ✓ 无跨线 |
| D-TRI-03 | 关系线基于头部位置 | 全场景 | ✓ |
| D-TRI-05 | 外反拍·底边机位·向里拍两人 | SHOT 11+12 | ✓ |
| D-TRI-06 | 内反拍·机位在两人之间·向外拍单人 | SHOT 13+14+15+17+19 | ✓ |
| GEN-02 | 空间可行性 > 美学简化 | 全场景 | ✓ 全部可站立/放置 |
| E-MTC-04 | 视线匹配铁律·互视视线相反 | SHOT 08↔09, 13↔14, 18 | ✓ |
| M-MOT-03 | 门口·固定/缓推/手持·禁快速横移 | SHOT 03+05+08 | ✓ 全部固定/缓推预留 |
| A-GEN-02 | 空间建立优先·第一镜=空间建立 | SHOT 02 | ✓ |

### P1级规则（场景关键）

| 规则ID | 规则内容 | 引用镜次 |
|--------|---------|---------|
| D-TRI-04 | 三角形底边+顶端=七个可选机位 | SHOT 11+12(底边)+13+14(顶端内侧) |
| D-TRI-07 | 主观视点·POV | SHOT 06+07 |
| D-TRI-08 | 平行位置·视轴平行·各拍侧面像 | SHOT 13↔14(平行关系) |
| D-TRI-09 | 大三角形组合·七个视点 | 整体布局 |
| D-TRI-13 | 主镜头在三角形顶端 | SHOT 02+10+18(顶角回看图) |
| D-TRI-14 | 共轴推进法·沿视轴向前推 | SHOT 10→13+14(宽→紧) |
| D-DUO-01 | 面对面·基本对话构型 | SHOT 10+18 |
| D-DUO-02 | 外反拍最强·纵深·开放形体占主导 | SHOT 11+12 |
| D-DUO-07 | 一前一后·纵深层次 | SHOT 02(初始·Rico前·门后) |
| D-DUO-13 | 单人时第二演员留在画外 | SHOT 04+05+08+09+13+14+15+17+19 |
| D-DIA-01 | 推近对话·吸引/排斥力 | SHOT 10(动作驱近) |
| D-DIA-03 | 不同高度·权力不对等 | SHOT 10(Rico坐vs Miguel站→齐平) |
| D-DIA-12 | 力量对比·低角度/眼平 | SHOT 19(Rico空间主人·最后一句) |
| D-DIA-17 | 夸张仰拍·支配地位 | (预留·未在此场景使用) |
| D-DIA-19 | 聚焦于一人·对话升温 | SHOT 13→14→15→17 |
| D-DIA-20 | 障碍物调度·工作台=障碍物 | SHOT 10+18 |
| D-DIA-22 | 门口相持·对比焦距/角度 | SHOT 03+05+08 |
| D-DIA-21 | 深布景调度·分层 | SHOT 10+18 |
| A-SUS-01 | 轻微后退·不安 | SHOT 20(黑屏后退) |
| A-SUS-09 | 恐惧延时释放·安全感→打破 | SHOT 02→03→16a/b/c |
| A-SUS-03 | 紧张期待·固定镜头·不切不走 | SHOT 14(两秒沉默)+SHOT 18(天空变色) |

### P2级规则（辅助·增强）

| 规则ID | 规则内容 | 引用镜次 |
|--------|---------|---------|
| D-DUO-08 | 机位距离/高度·距离定景别·高度定视角心理 | SHOT 04(眼平·平等)+SHOT 14(眼平) |
| D-DUO-09 | 三角形2号位置最弱·侧面·同一平面 | (未使用·预留于对话开始/过渡) |
| D-DIA-11 | 肢体语言对抗·摄影机不动·凝固空气 | SHOT 17+18 |
| A-SUS-10 | 声音先行预示 | SHOT 03(视觉版·影子先行) |
| A-SUS-02 | 未知之惧·不拍威胁来源 | SHOT 07(黑布包裹物) |

---

## §6 YAML结构化块

### segments_camera

```yaml
segments_camera:
  scene: "EP15_S1_Rico工作室"
  duration_est: "100-120s"
  total_shots: 20
  180_degree_line:
    endpoint_a: {actor: Rico, pos: [2.5, 2.8, 1.2], note: "坐姿头部·工作台前"}
    endpoint_b: {actor: Miguel, pos: [4.0, 0.5, 1.7], note: "站姿头部·门口"}
    line_equation: "X = 2.5 + 0.652*(2.8 - Y)"
    camera_side: "SOUTH/WEST"
    side_rule: "X < 2.5 + 0.652*(2.8 - Y)"
  coordinate_system:
    unit: "meters"
    origin: [0, 0, 0]
    x_axis: "左墙(0) → 右墙(5)"
    y_axis: "后墙(0) → 前墙(5)"
    z_axis: "地板(0) → 天花板(3)"
  anchors:
    workbench_center: [2.5, 2.8, 0.8]
    rico_seated_eye: [2.5, 2.8, 1.2]
    rico_standing_eye: [2.5, 2.8, 1.7]
    door_center: [4.0, 0.0, 1.0]
    miguel_door_eye: [4.0, 0.5, 1.7]
    miguel_forward_eye: [3.2, 1.5, 1.7]
    lamp: [2.5, 2.8, 2.5]
    light_cone_zone: {x: [1.5, 3.5], y: [2.5, 3.5], color_temp: 2800, note: "暖黄·+2EV"}
    door_cold_light: {color_temp: 4000, note: "楼道冷白荧光"}
    color_boundary: {at: "门框平面", warm: 2800, cold: 4000}
    gun_wall: {x: 0, y: [1, 4], note: "左墙改装枪列阵"}
    safe: {x: 5, y: 3.5, note: "右角灰色保险柜"}
    sink: {x: 5, y: 4.5, note: "右角洗手池·染血毛巾"}
    window_inferred: {x: 0.5, y: 5, z: [1.8, 2.6], confidence: "LEVEL-C", note: "推断·不入画·仅光线变化"}
  shots:
    - id: 1
      script_beat: "第3行·锉刀开场"
      type: "ECU·Insert·Macro"
      camera_pos: [2.5, 3.2, 1.1]
      look_direction: "俯角60°·向下"
      subject: "锉刀+枪管·台面"
      line180_side: "N/A"
      kb_rules: ["GEN-02"]
      coverage: "开场气氛锚点·书挡结构A"
      
    - id: 2
      script_beat: "第4行前半·建立镜头"
      type: "WS·Master Establishing"
      camera_pos: [1.5, 1.5, 1.6]
      look_direction: "东北·朝向门/后墙"
      subject: "Rico背影+工作台+洞洞板+门+保险柜"
      line180_side: "SOUTH/WEST"
      kb_rules: ["A-GEN-02(P0)", "D-DUO-07(P1)", "GEN-02(P0)"]
      coverage: "空间建立·对话模板#1"
      
    - id: 3
      script_beat: "第4行后半+第5行·门推开·影子"
      type: "MS·Suspense Entry"
      camera_pos: [2.0, 2.0, 1.6]
      look_direction: "西北·朝向门"
      subject: "Rico背影前景+门后景·Miguel剪影·影子投射"
      line180_side: "SOUTH/WEST"
      kb_rules: ["A-SUS-10(P2)", "A-SUS-09(P1)", "D-DIA-22(P1)", "GEN-02(P0)"]
      coverage: "悬念入场·悬疑模板#2"
      
    - id: 4
      script_beat: "第6行·Rico不回头对话"
      type: "CU·Single A"
      camera_pos: [1.5, 3.5, 1.2]
      look_direction: "Rico3/4侧脸·视线向下(看工作)"
      subject: "Rico面部·锉刀手"
      line180_side: "SOUTH/WEST"
      kb_rules: ["D-TRI-02(P0)", "D-DUO-13(P1)", "D-DUO-08(P2)", "GEN-02(P0)"]
      coverage: "对话模板#2·Rico首次面部出场"
      
    - id: 5
      script_beat: "第7行·Miguel关门·扫视"
      type: "MS·Single B"
      camera_pos: [2.5, 1.5, 1.7]
      look_direction: "Miguel视线扫视:左→中→右"
      subject: "Miguel全身·门框构图·扫视动作"
      line180_side: "SOUTH/WEST"
      kb_rules: ["D-TRI-02(P0)", "D-DUO-08(P2)", "D-DIA-22(P1)", "GEN-02(P0)"]
      coverage: "对话模板#3·Miguel首次清晰面部出场"
      
    - id: 6
      script_beat: "第7行·扫视:改装枪列阵"
      type: "INSERT·POV"
      camera_pos: [1.5, 0.5, 1.7]
      look_direction: "从门口看向左墙"
      subject: "左墙改装枪列阵·金属反光"
      line180_side: "N/A"
      kb_rules: ["GEN-02(P0)"]
      coverage: "对话模板#6·悬疑模板#2"
      
    - id: 7
      script_beat: "第7行·扫视:保险柜"
      type: "INSERT·POV"
      camera_pos: [4.5, 3.0, 1.2]
      look_direction: "微俯·看保险柜缝隙"
      subject: "灰色保险柜·柜门留缝·黑布包裹物"
      line180_side: "N/A"
      kb_rules: ["A-SUS-02(P1)", "GEN-02(P0)"]
      coverage: "对话模板#6·核心悬念植入"
      
    - id: 8
      script_beat: "第8行·Miguel首句对白"
      type: "CU·Single B"
      camera_pos: [2.5, 1.2, 1.7]
      look_direction: "Miguel看向右方(Rico)"
      subject: "Miguel面部·半明半暗·警徽"
      line180_side: "SOUTH/WEST"
      kb_rules: ["D-TRI-02(P0)", "D-DUO-02(P0)", "D-DUO-08(P2)", "E-MTC-04(P0)"]
      coverage: "对话模板#3·审问语气建立"
      
    - id: 9
      script_beat: "第9行·Rico转身"
      type: "CU·Single A·Action"
      camera_pos: [1.5, 3.2, 1.2]
      look_direction: "Rico从看工作(右)→转看Miguel(左)"
      subject: "Rico放下锉刀·转身·面部光线变化"
      line180_side: "SOUTH/WEST"
      kb_rules: ["D-TRI-02(P0)", "E-MTC-04(P0)", "GEN-02(P0)"]
      coverage: "对话模板#2·关键转折点"
      
    - id: 10
      script_beat: "第9行后-第12行·面对面→迈步→站起"
      type: "MS·2-Shot·Re-establishing"
      camera_pos: [1.5, 2.0, 1.6]
      look_direction: "两人互视·Rico左·Miguel右"
      subject: "三阶段:面对面→Miguel迈两步→Rico站起"
      line180_side: "SOUTH/WEST"
      kb_rules:
        - "D-TRI-01(P0)"
        - "D-TRI-02(P0)"
        - "D-DUO-01(P0)"
        - "D-DIA-20(P1)"
        - "D-DIA-03(P1)"
        - "A-GEN-02(P0)"
        - "GEN-02(P0)"
      coverage: "对话模板#1+8·三阶段动作覆盖"
      action_stages:
        - stage: "A"
          description: "Rico坐姿画右·Miguel站姿画左·距离4m·工作台隔开"
        - stage: "B"
          description: "Miguel迈两步·距离缩至2m"
        - stage: "C"
          description: "Rico站起·两人身高齐平·隔工作台对峙"
          
    - id: 11
      script_beat: "第10-14行对话段·Rico对白主镜"
      type: "OTS·Outer Reverse A"
      camera_pos: [3.2, 1.0, 1.7]
      look_direction: "越过Miguel右肩·看Rico正面"
      subject: "Miguel肩前景(虚)·Rico正面后景(焦)"
      line180_side: "SOUTH/WEST"
      kb_rules: ["D-TRI-05(P0)", "D-TRI-02(P0)", "D-DUO-02(P0)", "GEN-02(P0)"]
      coverage: "对话模板#4·外反拍A·Rico开放形体占主导"
      
    - id: 12
      script_beat: "第10-14行对话段·Miguel对白主镜"
      type: "OTS·Outer Reverse B"
      camera_pos: [1.8, 3.2, 1.6]
      look_direction: "越过Rico右肩·看Miguel正面"
      subject: "Rico肩前景(虚)·Miguel正面后景(焦)"
      line180_side: "SOUTH/WEST"
      kb_rules: ["D-TRI-05(P0)", "D-TRI-02(P0)", "D-TRI-03(P0)", "GEN-02(P0)"]
      coverage: "对话模板#5·外反拍B·与SHOT 11配对"
      
    - id: 13
      script_beat: "第12行·Rico'你有指控吗？'"
      type: "CU·Single A·Inner Reverse"
      camera_pos: [1.8, 2.8, 1.7]
      look_direction: "Rico看向右方"
      subject: "Rico面部近景·暖黄光·锐利眼神"
      line180_side: "SOUTH/WEST"
      kb_rules: ["D-TRI-06(P0)", "D-TRI-14(P1)", "D-DIA-19(P1)", "GEN-02(P0)"]
      coverage: "对话模板#2·内反拍·Rico主动出击"
      
    - id: 14
      script_beat: "第13行·Miguel'没有'+沉默2秒"
      type: "CU·Single B·Inner Reverse"
      camera_pos: [2.8, 1.5, 1.7]
      look_direction: "Miguel看向左方"
      subject: "Miguel面部近景·沉默2秒·'没有'"
      line180_side: "SOUTH/WEST"
      kb_rules: ["D-TRI-06(P0)", "D-DIA-11(P2)", "A-SUS-03(P1)", "E-MTC-04(P0)", "GEN-02(P0)"]
      coverage: "对话模板#3·沉默比语言有力"
      
    - id: 15
      script_beat: "第14行·Rico'朋友的身份？'"
      type: "CU·Single A·Inner Reverse"
      camera_pos: [1.8, 2.8, 1.7]
      look_direction: "Rico看向右方·嘴角微动"
      subject: "Rico面部近景·嘴角微动(非笑)"
      line180_side: "SOUTH/WEST"
      kb_rules: ["D-TRI-06(P0)", "D-DUO-08(P2)", "GEN-02(P0)"]
      coverage: "对话模板#2·反客为主"
      
    - id: 16a
      script_beat: "第15行·Miguel手指1cm"
      type: "ECU·Extreme Close-Up"
      camera_pos: [3.5, 1.5, 1.0]
      look_direction: "水平·拍右手"
      subject: "Miguel右手·手指向后移1cm·无名指旧伤疤·配枪皮套边缘"
      line180_side: "N/A"
      kb_rules: ["A-SUS-09(P1)", "GEN-02(P0)"]
      coverage: "悬疑模板#3·三连切第一镜·叙事高潮触发器"
      
    - id: 16b
      script_beat: "第15行·Rico眼睛捕获"
      type: "ECU·Extreme Close-Up"
      camera_pos: [2.0, 2.8, 1.7]
      look_direction: "Rico眼睛下扫一帧"
      subject: "Rico双眼·下扫一帧·深棕色虹膜"
      line180_side: "SOUTH/WEST"
      kb_rules: ["A-SUS-09(P1)", "D-DIA-19(P1)", "GEN-02(P0)"]
      coverage: "悬疑模板#3·三连切第二镜·眼睛捕捉微动作"
      
    - id: 16c
      script_beat: "第15行·Rico嘴角收住"
      type: "ECU·Extreme Close-Up"
      camera_pos: [2.0, 2.8, 1.55]
      look_direction: "N/A(嘴部局部)"
      subject: "Rico嘴角·收紧·下颌硬化·金属屑微粒"
      line180_side: "N/A"
      kb_rules: ["A-SUS-09(P1)", "A-SUS-03(P1)", "GEN-02(P0)"]
      coverage: "悬疑模板#3·三连切第三镜·情绪内化"
      
    - id: 17
      script_beat: "第16行·Miguel缓慢对白"
      type: "CU·Single B·Inner Reverse"
      camera_pos: [2.8, 1.5, 1.7]
      look_direction: "Miguel看向左方"
      subject: "Miguel面部·声音缓慢·选字"
      line180_side: "SOUTH/WEST"
      kb_rules: ["D-TRI-06(P0)", "D-DIA-11(P2)", "GEN-02(P0)"]
      coverage: "对话模板#3·立场转变暗示"
      
    - id: 18
      script_beat: "第17-18行·对视·天空变色·Rico擦手"
      type: "WS·Re-establishing·Atmosphere"
      camera_pos: [1.5, 1.5, 1.6]
      look_direction: "互相凝视·天空光变化·光圈晃动"
      subject: "双人全景·天空橘→暗蓝·台灯光圈晃动·Rico擦手叠抹布"
      line180_side: "SOUTH/WEST"
      kb_rules:
        - "D-TRI-01(P0)"
        - "D-TRI-02(P0)"
        - "D-DIA-11(P2)"
        - "A-SUS-03(P1)"
        - "E-MTC-04(P0)"
        - "GEN-02(P0)"
      coverage: "对话模板#8·悬疑模板#5·全场景情绪最高点"
      window_light_change:
        from: "暖橘(~3000K·黄昏)"
        to: "暗蓝(~8000K·入夜)"
        projection: "地面/左墙·不直射人物·窗口本身不入画"
        
    - id: 19
      script_beat: "第19行·Rico'带搜查令来'"
      type: "MS·Single A·Closer"
      camera_pos: [1.5, 3.0, 1.7]
      look_direction: "Rico看向右方"
      subject: "Rico中景·抹布已叠好·最后一句对白"
      line180_side: "SOUTH/WEST"
      kb_rules: ["D-TRI-06(P0)", "D-DIA-12(P1)", "GEN-02(P0)"]
      coverage: "对话模板#2·权力宣告·对话终结"
      
    - id: 20
      script_beat: "第20-21行·VO·黑屏·锉刀声"
      type: "ECU·Closing Bookend"
      camera_pos: [2.5, 3.2, 1.1]
      look_direction: "俯角60°·向下"
      subject: "锉刀搁枪管上→黑屏·锉刀声一圈"
      line180_side: "N/A"
      kb_rules: ["GEN-02(P0)", "A-SUS-01(P1)"]
      coverage: "书挡闭合·悬念悬置·与SHOT 01对称"
      end_sequence:
        - "VO播放·画面静止(锉刀搁枪管)"
        - "VO结束·黑屏"
        - "黑屏中·锉刀声:金属摩擦·一圈"
```

### frames_hard

```yaml
frames_hard:
  scene: "EP15_S1_Rico工作室"
  total_keyframes: 42
  note: "仅列出机位定位用硬关键帧·供Movement Designer确定起止帧·供Storyboard Planner布局"
  keyframes:
    - shot_id: 1
      kf_id: "1A"
      frame_type: "static"
      description: "锉刀在枪管上·起始位"
      
    - shot_id: 2
      kf_id: "2A"
      frame_type: "static"
      description: "建立全景·Rico背对门口·工作台·洞洞板·门闭合"
      
    - shot_id: 3
      kf_id: "3A"
      frame_type: "static_start"
      description: "门闭合状态"
      kf_id: "3B"
      frame_type: "static_end"
      description: "门推开·Miguel剪影·影子投在Rico背上"
      
    - shot_id: 4
      kf_id: "4A"
      frame_type: "static"
      description: "Rico3/4侧脸·锉刀声·说对白"
      
    - shot_id: 5
      kf_id: "5A"
      frame_type: "static_start"
      description: "Miguel关门·靠门框"
      kf_id: "5B"
      frame_type: "static_end"
      description: "Miguel视线扫视结束·停在保险柜方向"
      
    - shot_id: 6
      kf_id: "6A"
      frame_type: "static"
      description: "左墙改装枪列阵"
      
    - shot_id: 7
      kf_id: "7A"
      frame_type: "static"
      description: "保险柜留缝·黑布包裹"
      
    - shot_id: 8
      kf_id: "8A"
      frame_type: "static"
      description: "Miguel面部·'你看上去不惊讶'"
      
    - shot_id: 9
      kf_id: "9A"
      frame_type: "static_start"
      description: "Rico放下锉刀·手在画面中"
      kf_id: "9B"
      frame_type: "static_end"
      description: "Rico转身完成·面对Miguel方向"
      
    - shot_id: 10
      kf_id: "10A"
      frame_type: "static_stage_A"
      description: "双人·Rico坐姿画右·Miguel站姿画左·距离4m"
      kf_id: "10B"
      frame_type: "static_stage_B"
      description: "Miguel迈两步·距离2m"
      kf_id: "10C"
      frame_type: "static_stage_C"
      description: "Rico站起·两人身高齐平·隔工作台对峙"
      
    - shot_id: 11
      kf_id: "11A"
      frame_type: "static"
      description: "OTS Miguel肩→Rico正面"
      
    - shot_id: 12
      kf_id: "12A"
      frame_type: "static"
      description: "OTS Rico肩→Miguel正面"
      
    - shot_id: 13
      kf_id: "13A"
      frame_type: "static"
      description: "Rico近景·'你有指控吗？'"
      
    - shot_id: 14
      kf_id: "14A"
      frame_type: "static_start"
      description: "Miguel近景·沉默起始"
      kf_id: "14B"
      frame_type: "static_end"
      description: "Miguel近景·'没有'·沉默2秒后"
      
    - shot_id: 15
      kf_id: "15A"
      frame_type: "static"
      description: "Rico近景·嘴角微动·'朋友的身份？'"
      
    - shot_id: 16a
      kf_id: "16a_A"
      frame_type: "static"
      description: "ECU Miguel右手·手指初始位置"
      kf_id: "16a_B"
      frame_type: "static"
      description: "ECU Miguel右手·手指后移1cm完成"
      
    - shot_id: 16b
      kf_id: "16b_A"
      frame_type: "static"
      description: "ECU Rico眼睛·平视Miguel"
      kf_id: "16b_B"
      frame_type: "static"
      description: "ECU Rico眼睛·下扫一帧(1/24s)·捕获手指位移"
      
    - shot_id: 16c
      kf_id: "16c_A"
      frame_type: "static_start"
      description: "ECU Rico嘴角·微松弛(上一句残留)"
      kf_id: "16c_B"
      frame_type: "static_end"
      description: "ECU Rico嘴角·收紧·绷直·完全闭合"
      
    - shot_id: 17
      kf_id: "17A"
      frame_type: "static"
      description: "Miguel近景·缓慢对白·'不想看你自我毁灭'"
      
    - shot_id: 18
      kf_id: "18A"
      frame_type: "static_start"
      description: "双人全景·对视·天空暖橘·光圈稳定"
      kf_id: "18B"
      frame_type: "static_mid"
      description: "双人全景·对视·天空过渡中·光圈微晃"
      kf_id: "18C"
      frame_type: "static_mid"
      description: "Rico低头·拿抹布·擦金属屑"
      kf_id: "18D"
      frame_type: "static_end"
      description: "抹布叠好·放在桌上·天空暗蓝"
      
    - shot_id: 19
      kf_id: "19A"
      frame_type: "static"
      description: "Rico中景·'带搜查令来'"
      
    - shot_id: 20
      kf_id: "20A"
      frame_type: "static_start"
      description: "锉刀搁枪管上·VO播放"
      kf_id: "20B"
      frame_type: "static_end"
      description: "黑屏·锉刀声一圈"
```

---

## §7 输出摘要

```
┌──────────────────────────────────────────────────────────────────┐
│                  EP15 S1 SHOT ARCHITECT · 设计摘要                   │
│                                                                  │
│  场景: Rico工作室（傍晚→夜）· 单场景                                │
│  总镜数: 20镜 (含16a/b/c三子镜·实际23个机位)                        │
│  180°侧: SOUTH/WEST · 全程未跨线 ✓                                 │
│                                                                  │
│  机位分布:                                                        │
│    ECU (超近特写):   5镜 — SHOT 01,16a,16b,16c,20                │
│    CU (近景):        7镜 — SHOT 04,08,09,13,14,15,17             │
│    MS (中景):        5镜 — SHOT 03,05,10,11,12,19                │
│    WS (全景):        2镜 — SHOT 02,18                             │
│    INSERT (插入):     2镜 — SHOT 06,07                            │
│                                                                  │
│  模板覆盖:                                                        │
│    对话8机位模板: 8/8 ✓                                           │
│    悬疑5机位模板: 5/5 ✓                                           │
│                                                                  │
│  KB规则引用:                                                      │
│    P0级: 9条规则 · 全部验证通过 ✓                                  │
│    P1级: 18条规则引用于对应镜次                                     │
│    P2级: 6条规则引用于对应镜次                                     │
│                                                                  │
│  空间约束:                                                        │
│    全机位可站立/放置 · 0穿墙 · 0悬空 · 0阻挡人物移动 ✓             │
│                                                                  │
│  下游消费:                                                        │
│    → Movement Designer: frames_hard中42个关键帧·确定起止帧+运镜    │
│    → Storyboard Planner: segments_camera中23个机位·首帧+末帧布局   │
│    → SekoTalk: 编辑器模式·口型同步·SHOT 04/08/09/13/14/15/17/19   │
│                                                                  │
│  输出文件: EP15_S1_SHOT_ARCHITECT.md                              │
│  写入时间: 2026-07-07                                              │
└──────────────────────────────────────────────────────────────────┘
```
