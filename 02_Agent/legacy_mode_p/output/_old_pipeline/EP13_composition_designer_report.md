# Composition Designer v2.0 — EP13《弹道学》鉴证科实验室

> **独立上下文:** ✅ (未读取SA/MD推理·只读§6 YAML结构化块)
> **数据来源:** 原始剧本 + 场景参考图(鉴证科实验室+圣保罗城市景观) + ANCHOR_BASELINE §C(空间地图) + IMAGE_AUDIT
> **KB路由:** 对话/悬疑混合 → §4构图双人对话(~30条) + §6光影日间室内+色温

---

## 场景光源提取（从参考图·不依赖剧本）

| 光源 | 色温 | 位置 | 参考图锚点 |
|------|:---:|------|------|
| 天花板LED平板灯 | 5000K | 上方·嵌入式·4块一组·无影灯 | 图1+2 |
| 显微镜环形LED | 3200K | 载物台上方~3cm·侧光15° | 图5 |
| 电脑屏幕 | 6500K | 多连屏·面光方向 | 图3+6 |
| 蓝光键盘 | 470nm | 复合工作站·底部微光 | 图6 |
| 窗外午后阳光 | 3500K | 窗侧·百叶窗切为水平光栅·过曝1.5-2档 | 图9+圣保罗全景 |
| 走廊灯(推断) | 3500K | 门方向·逆光 | 推断·物理属性已标注 |

## 四色温系统

```
3200K 暖琥珀 — 显微镜·弹头近摄 — 发现·亲密·金属触感
5000K 冷白   — 天花板LED·环境 — 科学·客观·受控领域
6500K 冷蓝   — 屏幕·数据域 — 数字·证据·分析
3500K 暖金   — 窗外阳光·走廊 — 外部世界·人性·Rico的领域

色温节拍:
  #1 → 3200K 发现
  #2-#3 → 5000K+3200K底光+6500K蓝 消耗·数据
  #4 → 5000K+3000K暖黄(手机入侵) 人的温度
  #5-#6 → 5000K+3500K轮廓 跨越·进入
  #7-#8 → 5000K+6500K+3500K 揭示·冲击
  #9 → 5000K均匀 认知·确证
  #10 → 5000K单光源 结论
  #11 → 5000K→3500K 暖域入侵·维度拓展
  #12-#13 → 3500K主导 名字·内化
  #14 → 3200K→暗红→消失 光的死亡
  #15 → 3500K→淡黄→消失 悬念
```

## 构图母题

- **螺旋母题:** 弹头膛线(#1金属) → 屏幕膛线(#7数字) → Miguel手指(#13肉体) — 三段闭合
- **双联画母题:** 旧照片↔新证据(#9) · 冷白室内↔暖金窗外(#11)
- **三层嵌套:** Vincent肩(暗前景) + 百叶窗框(画中画) + 城市(远景) — #11
- **负空间叙事:** 手指间空=枪柄形状 — #13

## §6 global_anchors YAML

```yaml
global_anchors:
  character:
    Vincent: "30-40岁男性·深棕色短发微凌乱·黑框眼镜(黑色板材·矩形框·可摘戴)·白色实验室长外套·领口微敞·内搭深色衬衫·肤色冷白·偏瘦体态·鉴定师的手(指甲修剪整齐·指关节细微皱纹)"
    Miguel: "30-40岁男性·黑色短卷发·两鬓和发际微花白·棕褐色皮肤(色温敏感:冷光偏灰蜡·暖光皮下散射深橙金)·宽颧骨·方下颌·眉心间竖纹·深棕色眼睛·宽阔肩膀·深藏青色警探夹克(哑光面料·拉链立领)·浅灰衬衫纽扣领内搭·左胸前金色警徽(盾形·浮雕鹰+星环)·深色金属腕表(黑色表盘)·无名指旧伤疤(细长·缝合痕)"
  environment:
    scene: "圣保罗刑警总部·鉴证科实验室·日·室内·午后"
    description: "矩形实验室(~8m深×~5m宽×~3m高)·双排不锈钢实验台·地板黑色金属轨道·尽头巨幅LED屏幕·左侧玻璃物证橱窗·复合工作站(多连屏·蓝光键盘)·微距比对操作台(显微镜+游标卡尺+镊子+黑色防静电垫+五证据袋)·百叶窗(金属叶片·半开半合)·灰色金属消防门(不锈钢把手·外连走廊)·窗外圣保罗城市全景"
  style_spine:
    description: "冷峻科学实验室视觉·四色温精密控制·高低反差光影·微观证据与宏观城市的视觉辩证法·螺旋母题(金属→数字→肉体)·双联画·三层嵌套·负空间叙事·Arri Alexa 35·中等对比度·微颗粒感·窗外过曝1.5-2档(有意的视觉修辞)"
  lighting:
    primary: [天花板LED平板灯5000K·显微镜环形LED3200K·电脑屏幕6500K·蓝光键盘470nm·窗外午后阳光3500K]
    strategy: "冷白=科学客观受控·暖琥珀=发现亲密·冷蓝=数据证据·暖金=外部真实生命世界·色温过渡是入侵而非渐变"
    light_events: [手机暖光入侵(#4)·门槛光门槛(#5)·档案摔下高光反射(#8)·窗光过曝(#11)·钨丝冷却(#14)·光栅衰减(#15)]
  constraints:
    - "面部比例全程一致·五官不漂移·角色跨镜Identity保持"
    - "四色温系统全程锁定·无额外杂色光·所有光源有参考图锚点"
    - "百叶窗光栅方向+密度全程一致·窗光过曝维持"
    - "画面稳定无晃动(#8手持微晃0.3x除外·设计性冲击表达)"
    - "无字幕·无Logo·无水印·画面内文字标注'后期叠加'(#3/#9)"
    - "物体存在链完整·弹头/显微镜/旧档案/证据袋桌面位置全程一致"
```

## §6 frames_soft YAML（逐秒·58s）

```yaml
frames_soft:
  # #1 弹头ECU (0-4s) — 3200K主导
  - {sec:0, action:"弹头固定·静止2s·整体~2cm", spatial:"载物台水平线下1/3·弹头居中·纯黑负空间95%", props:"O-01弹头(垂直固定·蘑菇状·膛线纹路)·O-02环形LED(亮·3200K)", color_temp:3200}
  - {sec:1, action:"静止", spatial:"同sec0", props:"同sec0", color_temp:3200}
  - {sec:2, action:"推近·膛线放大", spatial:"载物台线下移", props:"O-01弹头(推至~0.5cm)", color_temp:3200}
  - {sec:3, action:"推近终点·膛线山脊峡谷清晰", spatial:"弹头~0.5cm·95%纯黑", props:"O-01弹头(膛线特写)", color_temp:3200}
  # #2 Vincent摘眼镜 (4-7s) — 三光源系统
  - {sec:4, action:"直起腰·摘黑框眼镜·揉鼻梁", spatial:"Vincent画右2/3·前景左显微镜虚化·背景实验台纵深·三层深度", props:"O-08眼镜(摘下·手持)·O-02显微镜(亮·底光反弹)·O-10五证据袋·O-11游标卡尺·O-12镊子·O-04键盘(470nm)", character:"Vincent:摘眼镜·疲惫·被消耗的人", color_temp:5000}
  - {sec:5, action:"揉鼻梁·眼镜在手中", spatial:"同sec4", props:"同sec4", character:"Vincent:四小时·裸眼浮现", color_temp:5000}
  - {sec:6, action:"揉鼻梁结束·裸眼·固定静止", spatial:"同sec4", props:"O-08眼镜(手中/桌面)", character:"Vincent:人浮现", color_temp:5000}
  # #3 屏幕比对 (7-10s) — 6500K数据域
  - {sec:7, action:"五张膛线照片静止·绿色比对线贯穿", spatial:"屏幕80%·五照片水平排列", props:"O-03屏幕(五膛线照片·绿线·冷蓝6500K)·O-04键盘(470nm)", color_temp:6500}
  - {sec:8, action:"静止·五膛线完美重合", spatial:"同sec7", color_temp:6500}
  - {sec:9, action:"静止·绿线确认100%匹配", spatial:"同sec7", color_temp:6500}
  # #4 Vincent打电话 (10-14s) — 手机暖光入侵
  - {sec:10, action:"左手拿手机·划开拨号界面", spatial:"Vincent画左·右留白(视线空间)·手机画面下方", props:"O-13手机(OLED屏亮·3000K暖黄)·O-08眼镜(摘下·手中/桌面)", character:"Vincent:兴奋·嘴唇微张·喉结动", color_temp:5000, light_event:"手机暖光入侵冷白空间"}
  - {sec:11, action:"拨号·举手机到耳边·等待音一声", spatial:"推近·胸部以上→眼睛", character:"Vincent:想说但未组织好", color_temp:5000, light_event:"双色温颧骨交汇·冷白上·暖黄下"}
  - {sec:12, action:"等待音二声·喉结动·咽口水·兴奋", spatial:"推至颧骨双色温处", character:"Vincent:面部微血管扩张·皮下透暖色", color_temp:5000}
  - {sec:13, action:"对白'Miguel。现在过来。'·静止·推至眼部", spatial:"眼部特写·颧骨双色温·背景全虚", character:"Vincent:声音压低但压不住兴奋·等了四小时", color_temp:5000}
  # #5 Miguel入室 (14-18s) — 光门槛
  - {sec:14, action:"Miguel推门·走廊暖光涌入(逆光剪影)", spatial:"MLS·门画右·Miguel剪影·Vincent画左工作台前", props:"O-18灰色金属门(推开)·O-15夹克·O-16警徽·O-17衬衫·O-29腕表", character:"Miguel:剪影·宽阔肩膀·逆光轮廓", color_temp:3500, light_event:"门槛作为光门槛"}
  - {sec:15, action:"向前迈步·跨越门框·面孔从剪影浮现", spatial:"跟拍横移·Miguel从左→右移动", props:"O-23影子(斜长·打破轨道平行线)", character:"Miguel:棕褐肤色·宽颧骨·方下颌·眼睛锁定Vincent", color_temp:5000}
  - {sec:16, action:"继续走向工作台·影子拉长", spatial:"跟拍·轨道线从脚下延伸", character:"Miguel:刑警审视感", color_temp:5000}
  - {sec:17, action:"Vincent未回头·把屏幕转向Miguel·屏幕光扫过脸", spatial:"跟拍终点", props:"O-03屏幕(转向·6500K照亮Miguel)", color_temp:5000, light_event:"光先于信息抵达"}
  # #6 Miguel看屏幕 (18-21s) — 冷/暖同时对比
  - {sec:18, action:"看屏幕·眉头收紧·眉心竖纹", spatial:"CU·Miguel中央偏右·屏幕蓝光左侧·背景全虚", props:"O-16警徽(反射顶灯白光)·O-26左手搭金属台面(无名指微敲)", character:"Miguel:大脑已翻译成结论·嘴巴等眼睛确认", color_temp:5000}
  - {sec:19, action:"眼睛扫过五张照片·嘴唇微抿", character:"Miguel:棕褐肤色冷光下偏灰偏蜡", color_temp:5000}
  - {sec:20, action:"对白'同一把枪？'", character:"Miguel:声音低沉·不是疑问是确认", color_temp:5000}
  # #7 Vincent解释膛线 (21-26s) — 知识权力
  - {sec:21, action:"手指点在第三枚弹头膛线上·对白'比那更糟。看这个膛线切割——'", spatial:"CU·微仰3-5°·Vincent画左·手指画中央偏右", props:"O-08眼镜(戴上·镜片反射屏幕蓝光·两个蓝色方块)·O-14手指(指腹压膛线)", character:"Vincent:知识权力·声音低但精准", color_temp:5000}
  - {sec:22, action:"'不是工厂加工。'·推近暂停", spatial:"推近暂停", character:"Vincent:鉴定师职业骄傲", color_temp:5000}
  - {sec:23, action:"'是手工锉出来的。锉刀的力度、角度、每一道的间距——'·推近继续", spatial:"推向眼镜·脸几乎贴屏幕", color_temp:5000}
  - {sec:24, action:"推近继续·眼镜反射屏幕光清晰", spatial:"眼镜反射两个蓝色方块", props:"O-08眼镜(镜片反射·遮住眼睛)", character:"Vincent:镜片后面眼睛在燃烧", color_temp:5000}
  - {sec:25, action:"'这是一个人的签名。'·推近停止·静止", spatial:"终点·让'签名'落地", props:"O-14手指(在膛线终点·弹头变形漩涡处)", character:"Vincent:看到了对手的签名", color_temp:5000}
  # #7.5 Miguel倾听 (26-28s)
  - {sec:26, action:"听着·面部在暗区·嘴唇微动·忍住未说", spatial:"CU·Miguel中央·低照度~30%·背景全虚", character:"Miguel:听到'签名'·身体已准备那个名字", color_temp:5000}
  - {sec:27, action:"右眼微眯·嘴唇合上·大脑归档'签名'→'Rico'抽屉", character:"Miguel:沉默=力量", color_temp:5000}
  # #8 Vincent摔档案 (28-32s) — 冲击的光学表达
  - {sec:28, action:"拉开金属抽屉·抽出旧档案(泛黄牛皮纸·红色标签)", spatial:"MS·广角35mm·Vincent画右抽屉转身→左", props:"O-20抽屉(拉开·金属轨道声)·O-19旧档案(抽出·泛黄封面·红色标签·三年前日期)", character:"Vincent:能量释放", color_temp:5000}
  - {sec:29, action:"转身~120°·档案举起·对角线动作·Block亲和被打破", spatial:"对角线右下→左上", color_temp:5000}
  - {sec:30, action:"档案'砰'摔桌上·高光反射闪入(光事件)·微尘扬起在5000K光池中飘浮", spatial:"档案画中央偏左·桌面下1/3", props:"O-19旧档案(封面弹开)·O-23微尘(扬起)·O-21 Rico备案照(露出·卷草雕花·红点镜·金色扳机)·O-22膛线特写照片", character:"Vincent:冲击释放", color_temp:5000, light_event:"档案摔下高光反射·光事件·冲击的光学表达"}
  - {sec:31, action:"档案摊开·Rico照片完全露出·微尘沉降·旧纸乳白偏黄vs数字屏幕冷白偏蓝=视觉年代学", props:"O-21 Rico照片(老式闪光灯·乳白偏黄)·O-03屏幕(冷白偏蓝)", color_temp:5000, light_event:"视觉年代学(Gurney)"}
  # #9 两张照片并排 (32-36s) — 光的平等
  - {sec:32, action:"两张照片静止并排·左旧(泛黄·乳白偏黄)·右新(冷白偏蓝)", spatial:"ECU·对称构图·各占一半·黑色防静电垫背景", props:"O-21旧照片(乳白偏黄)·O-37新照片(冷白偏蓝)·O-25防静电垫(网格纹理)", color_temp:5000}
  - {sec:33, action:"红笔在垫子上画连接线·从左边第三条纹路连到右边", props:"O-24红笔(画线)·O-38红线(垂直贯穿)", color_temp:5000}
  - {sec:34, action:"连接线完成·膛线像两条平行闪电·旧照片允许1-2°倾斜(人类不完美vs科学必然)", props:"O-39绿色'100%'文字(白字绿底·画面下方)", color_temp:5000}
  - {sec:35, action:"静止·绿字100%可见·观众自己完成比对", color_temp:5000}
  # #10 Vincent结论 (36-39s) — 结论让光更冷
  - {sec:36, action:"抬头·穿过照片和工作台看Miguel·对白'同一只手。'·右手敲左边旧照片", spatial:"CU·Vincent中央·直视镜头(Miguel方向)·背景全虚", props:"O-08眼镜(戴上)·O-14右手(敲照片·画下方虚化)", character:"Vincent:声音很轻·怕打破什么", color_temp:5000}
  - {sec:37, action:"'同一种……'·嘴唇停顿·选词'审美'", spatial:"推近·胸部以上→眼睛", character:"Vincent:眼光从照片移向Miguel眼睛", color_temp:5000}
  - {sec:38, action:"'审美。'·推近静止·直视Miguel·单光源高反差·伦勃朗三角·冷光更冷", spatial:"终点·眼窝深影·伦勃朗三角·苍白面部", character:"Vincent:结论落地·在结论面前连光都变得更冷", color_temp:5000}
  # #11 摇臂升起 (39-45s) — 从证据到世界
  - {sec:39, action:"起点:两张照片画面下2/3·Vincent肩进入(黑色剪影)", spatial:"MS·桌面~90cm·俯角~45°", props:"O-44 Vincent肩(剪影·软焦)", color_temp:5000}
  - {sec:40, action:"上升·照片缩小·Vincent肩全影·VO进入'每一个枪匠都在子弹上签名。'", spatial:"~110cm·俯角~35°", props:"O-45百叶窗(进入画面·金属叶片·半开半合)", color_temp:5000}
  - {sec:41, action:"升至百叶窗叶片高度·三层嵌套显现", spatial:"~140cm·俯角~20°·百叶窗光栅·画中画", props:"O-47地板轨道(引导线延伸至窗边)·O-46窗外城市(暖金3500K·过曝·进入画框)", color_temp:5000, light_event:"双联画·冷白vs暖金"}
  - {sec:42, action:"VO'只是大多数人看不懂。'·升至百叶窗上方·城市过半画面", spatial:"~180cm·俯角~10°·左暗(室内)/右亮(窗外)", props:"O-46窗外城市(土黄水泥墙·蓝玻璃幕墙·高架桥·远山)", color_temp:5000}
  - {sec:43, action:"VO'Vincent能。'·升至窗高(~240cm)·窗外城市全景", spatial:"LS·~240cm·水平0°·三层嵌套完整", props:"O-46窗外城市全景(过曝1.5-2档·高架桥+远山+建筑群+屋顶天线+绿树+信号塔)", color_temp:5000, light_event:"窗外世界是过度的·视觉修辞"}
  - {sec:44, action:"静止·窗外全景·观众眼睛从近景重聚焦到远景", spatial:"LS·终点·水平0°", color_temp:5000}
  # #12 Miguel"Rico" (45-48s) — 名字的重击
  - {sec:45, action:"盯照片上名字·Rembrandt侧逆光·半暖半冷·'站在分界线上'", spatial:"CU·Miguel中央·微俯5°·百叶窗光栅横跨·照片虚化前景", props:"O-16警徽(在一条阳光中闪耀)·O-21 Rico备案照(红色圈名)", character:"Miguel:半暖(棕褐橙金·活着的颜色)/半冷(灰蜡·认知外)", color_temp:3500}
  - {sec:46, action:"嘴唇微动·分开→合上→再次分开·深吸气·确认准备好了", spatial:"推近·胸部以上→眼睛", character:"Miguel:刑警的确认", color_temp:3500}
  - {sec:47, action:"'Rico。'·一个词·眼睛没离开照片·深棕色眼·燃烧·静止1s", spatial:"终点·眼部·半暖半冷", character:"Miguel:名字出口·身体已内化·棕褐肤色暖光下深橙金='活着的颜色'", color_temp:3500}
  # #12.5 Miguel凝固 (48-50s)
  - {sec:48, action:"名字落地后1s·无任何动作·眼睛盯照片但焦点在照片后方(三年前的射击场或下一个犯罪现场)", spatial:"同#12位·焦平面在眼睛", character:"Miguel:凝固·嘴唇微张·名字挂在唇边·已无声", color_temp:3500}
  - {sec:49, action:"2s绝对静止·连姿态都没有·只有静止·Katz'用压抑表现力量'", character:"Miguel:眼睛在别处", color_temp:3500}
  # #13 Miguel右手 (50-53s) — 螺旋母题闭合
  - {sec:50, action:"右手自然垂身侧·开始变化·无名指向内弯曲·指尖触掌心", spatial:"ECU·右手画中央·工作台金属边缘下方虚化·背景全黑", props:"O-27右手(关节褶皱·指甲弧度·血管)·O-29腕表(秒针在走)", character:"Miguel:身体先于意识·手已开始回应'Rico'", color_temp:3500}
  - {sec:51, action:"拇指向内弯·手指间负空间=枪柄形状浮现·C-FI2-NS-01负空间主体", spatial:"手指弧度对角线·无名指+拇指圆形负空间画中央", props:"O-27右手(关节发白·血液压走)·O-28旧伤疤(皮肤微凸·缝合痕)·O-53负空间(枪柄形状)", character:"Miguel:本能·螺旋母题闭合(弹头→屏幕膛线→手指)", color_temp:3500}
  - {sec:52, action:"手指静止·弧度完整·枪柄稳定·手背青血管隆起(地图)·腕表秒针继续走", spatial:"终点·负空间·C-FI2-NS-15纯黑虚化", props:"O-27右手(静止·握紧)·O-28伤疤·O-29腕表·O-53负空间(枪柄=签名=Rico=下一个受害者)", character:"Miguel:肌肉记忆", color_temp:3500}
  # #14 显微镜灯灭 (53-56s) — 光的死亡
  - {sec:53, action:"环形LED亮·3200K暖琥珀光圈·弹头清晰·画面其余纯黑·与#1圆形闭合", spatial:"ECU·同#1位·光圈~5cm·弹头中央", props:"O-02显微镜(亮·3200K)·O-01弹头(膛线纹路·全剧起点=终点)", color_temp:3200}
  - {sec:54, action:"'啪'·灯灭·磷光体余辉:3200K→暗红·色彩安魂曲开始", props:"O-02显微镜(灯灭)·O-01弹头(暗红微光中)", color_temp:3200, light_event:"钨丝冷却=热力学的可见化(Gurney)"}
  - {sec:55, action:"暗红→深红→消失·0.5s全黑·不是'结束'·是'之后'", spatial:"全黑", color_temp:0}
  # #15 窗光余韵 (56-58s) — 悬念
  - {sec:56, action:"全黑中·百叶窗光栅残留·暖金平行条纹在地板和轨道上微光·城市声继续(遥远车流·模糊警笛)", spatial:"CU→全黑·地板·光栅水平条纹·轨道最后反光", props:"O-06地板轨道(最后反光)·O-45光栅(暖金微光)", color_temp:3500, light_event:"Alton黑暗有层次·微光渗入=悬念·外面还有东西在发生·Rico还在"}
  - {sec:57, action:"光栅暖金→淡黄→消失·渐暗→全黑·城市声音继续", spatial:"全黑", color_temp:0}
```

## P-STATE检查

```
P-FAL-01~10: 全部规避 ✅
P-CONSTITUTION第一条(画面可见性): 全部描述为画面内可见物 ✅
P-CONSTITUTION第三条(空间锚定): 全部光源有参考图锚点 ✅
```

---
**Composition Designer v2.0 · 独立上下文 ✅ · 2026-07-07**
