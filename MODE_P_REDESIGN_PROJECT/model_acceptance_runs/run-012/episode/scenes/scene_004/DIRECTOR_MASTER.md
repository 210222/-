# DIRECTOR_MASTER — scene_004（多层停车楼，雨夜，外景）

## 0. 版本

```text
Master 版本：scene_004/v1.0
```

## 1. 场景设计

```text
场景前状态：独立情境，无跨场继承。雨夜多层停车楼：阿泽抱文件袋在坡道上奔跑，两名追赶者自下一层出现，一辆货车停在中层转角车位，引擎熄灭。
戏剧变化：压力下的舍弃与失控的后果。阿泽把文件袋滑进货车底藏起、以自己的背影引开追赶者；到达顶层后，楼下传来货车发动声——藏匿点自己动了起来，处置权脱手。
信息策略：全片唯一一次观众多于场内一方：观众看见藏袋全过程，追赶者只看见背影并越过货车。结尾用纯声音完成反转：画面上无驾驶者、无文件袋去向确认，观众与阿泽一同跌回未知。
场景后状态：全片终止状态：阿泽两手空立于顶层边缘雨中，货车引擎声自下方持续。静帧收束后切黑场（后期），引擎与雨声延续一秒后收，全片结束。

场景空间：多层停车楼，外圈螺旋坡道逐层上行（P3 -> P4 -> 顶层露天层），钠灯沿坡道间隔布置，雨夜湿面反光。P4 转角前有横贯路面的排水沟，沟内雨水成流；转角车位停着一辆货车，车尾朝向坡道；顶层外缘设金属护栏，护栏外是城市黑夜。
关系线：追逐单向向上：阿泽恒定自左向右、自下向上运动；追赶者恒定在他身后更低处入画、同方向运动；全场无反向运动。顶层终点：阿泽面向护栏外黑夜，声源在画面外下方。
人物路径：阿泽：P3 坡道 → 跨排水沟 → P4 转角蹲滑藏袋 → 继续上行 → 顶层边缘停住。追赶者：P3 下层口 → 沿同一路线掠过货车 → 出画向上。文件袋：阿泽怀中 → 货车底部内侧车轮旁，此后画面上不再移动。
摄影可用区域：对侧楼板远机位（隔中庭空隙拍对面坡道）、坡道内侧手持跟随位（沿可通行路面横移）、货车旁地面低机位（静置）、货车后轮后方低位（借车尾遮挡）、顶层露天固定位。手持为主，藏袋插入镜与顶层收束镜稳定。

视觉策略：钠灯点状高光比，动作只在灯锥与湿面反光带内可读，雨丝只在灯位附近显形。三段节奏：建立——远机位交代人物、追兵与向右上的运动方向；升级——手持跟随跨沟与藏袋、低位看追兵过车；释放——顶层固定机位静止收束。藏袋低机位是全场唯一完全稳定的镜头，把决定从奔跑里单独拎出；顶层收束镜回归静止，让声音反转独占注意力。
镜头拆分理由：追兵入画、追逐线建立完成后切入跟随；蹲滑起始处切入地面低机位，让藏袋独立成镜；袋停定、人离开后切到货车后轮位接追兵通过，完成信息差；追兵背影没入上层后切顶层，让结果与声音反转落地。
场间关系：自上一场包厢静帧硬切进入，雨声由后期在切点前零点五秒入点；终镜静帧后切黑场（后期），引擎与雨声延续一秒后收束，全片结束。

场景蓝图：[D] 雨夜，多层停车楼外圈螺旋坡道。快递员阿泽（男，25岁上下，快递工作服湿透）抱文件袋向上狂奔；两名追赶者（男性，深色便装，全场无正面特写）自下一层追赶；P4 转角停着一辆车尾朝坡道的货车。钠灯橙光点状照明，湿地面反光，雨丝在灯锥中显形。本场变化：文件袋从怀中到货车底，最后随一声引擎发动脱离所有人视线。
声音基调：[D] 分层雨声底噪：开阔层的雨面沙声、坡道内的滴落回声；奔跑脚步与水花在混凝土上的硬回声；结尾顶层只剩雨声与喘息，货车引擎自下方点火并持续怠速——全场最重要的声音事件。
```

## 2. 共享 Boundary

本场 5 个 Shot，共 6 个共享 Boundary（B0-B5），与 Shot 交错书写于下方序列：B0 -> Shot 1 -> B1 -> Shot 2 -> B2 -> Shot 3 -> B3 -> Shot 4 -> B4 -> Shot 5 -> B5。

## 3. Shot Contract

## Boundary scene_004-B0 | SCENE_ENTRY -> scene_004-1

边界关系：[M] <scene_entry>
转场执行：[M] <post_production>
剪辑触发：[D] 自上一场包厢静帧硬切，雨声提前零点五秒入点（后期），第一帧落在奔跑中的阿泽身上。
交接描述：[D] 0 秒画面：雨夜停车楼对面坡道全景，阿泽已在全速上坡奔跑，文件袋横抱胸前；追赶者尚在画面外下层。声音自满幅雨声与奔跑水花直接进入，静转动。
接入状态键：[M]
  - character:a_ze position:carpark|ramp_p3_lower_section|running facing:upslope_north screen_direction:left_to_right posture:running_bag_clutched_to_chest wardrobe:courier_uniform_rain_soaked
  - character:chaser_a position:carpark|p3_level_mouth_below|running facing:upslope_north screen_direction:left_to_right posture:running_offscreen
  - character:chaser_b position:carpark|p3_level_mouth_below|running facing:upslope_north screen_direction:left_to_right posture:running_offscreen
  - prop:file_bag held_by:a_ze location:clutched_to_chest
  - prop:truck held_by:none location:p4_corner_bay_parked_engine_off
  - light_main direction:sodium_lamps_overhead_spaced color_temp:2200K ratio:1:16
  - action_phase:travel
  - story_time:night
  - weather:steady_rain
  - environment:multi_storey_carpark_wet_surfaces

## Shot scene_004-1 | 8s

叙事职责：[D] 建立：一个画面说清人物、追兵、空间层级与向右上的追逐方向；灯锥间的明暗交替确立本场视觉规则。
剧本事实：[D] L42——快递员阿泽抱着文件袋沿坡道向上跑；两名追赶者从下一层冲上来。
原文定位：[M] scene_004 L42-L42
生成单元：[M] 一个独立 SD2.0 视频段，时长从 0 秒到 8 秒。
场景表达：[M] <action_chase>
时间控制：[M] <second_nodes>

摄影设计：[D] 对侧楼板远机位，隔中庭空隙平拍对面坡道，28mm 广角；手持轻微呼吸晃动；机位固定于楼板边缘，无位移。
构图设计：[D] 坡道斜线自左下升向右上贯穿画面，三盏钠灯把湿面切成三段橙色光带；阿泽是光带中唯一的纵向运动体；下层坡道口在画面左下角，为追兵入画点；中庭黑负空间占画面下部。
光影设计：[D] 钠灯自上而下点状照明，色温2200K，光比1:16；灯锥内雨丝显形，灯间暗带只剩湿面反光；全镜光位恒定。
表演设计：[D] 阿泽全速冲刺，步频高、躯干前倾，文件袋横抱胸前双臂锁紧；中途一次快速回头即刻转回；追赶者两人步幅大、路线笔直，全程只见侧影与背影。

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无

视觉时间线：[D] [0.0s][SB] 雨夜多层停车楼，对面坡道自左下斜升至右上，三盏钠灯把湿面照成橙色光带，雨丝在灯锥中斜落；阿泽从画面左下灯锥进入，全速上坡奔跑，文件袋横抱胸前，工作服湿贴在背上。
  [1.0s] 阿泽穿出第一个灯锥进入暗带，湿面上只剩他晃动的倒影。
  [2.0s] 他冲入第二个灯锥，步幅未减，水花从鞋边溅开。
  [3.0s] 他快速回头一瞥身后下方，头随即转回，继续向右上冲。
  [4.0s] 阿泽接近画面右上第三个灯锥，背影在雨幕中缩小。
  [5.0s][SB] 画面左下坡道口，两名追赶者先后冲入第一个灯锥，同方向上坡猛追。
  [6.0s] 追赶者穿过灯锥进入暗带，脚步水花连成串响。
  [7.0s] 前后三人同向奔跑：阿泽在右上将出画，追赶者在左下持续加速。
  [8.0s][SB] 阿泽从画面右上出画，两名追赶者进入第二个灯锥，追逐线明确指向右上。
声音设计：[D] 满幅分层雨声贯穿；阿泽的脚步水花回声自左下移向右上；5.0 秒起第二组更重的双人脚步进入并渐强；无对白。

## Boundary scene_004-B1 | scene_004-1 -> scene_004-2

边界关系：[M] <continuous>
转场执行：[M] <post_production>
剪辑触发：[D] 阿泽右上出画、追赶者进入第二灯锥的瞬间切出，动作方向不断。
交接描述：[D] 同一时刻的空间交接：阿泽刚越过 P3 坡道顶进入 P4 段，追赶者在 P3 坡道中段；文件袋仍在怀中。后镜以侧跟视角在 P4 段接住他的奔跑。
交出状态键：[M]
  - character:a_ze position:carpark|ramp_p3_to_p4_transition|running facing:upslope_north screen_direction:left_to_right posture:running_bag_clutched_to_chest
  - character:chaser_a position:carpark|ramp_p3_mid|running facing:upslope_north screen_direction:left_to_right posture:running
  - character:chaser_b position:carpark|ramp_p3_mid|running facing:upslope_north screen_direction:left_to_right posture:running
  - prop:file_bag held_by:a_ze location:clutched_to_chest
  - prop:truck held_by:none location:p4_corner_bay_parked_engine_off
  - light_main direction:sodium_lamps_overhead_spaced color_temp:2200K ratio:1:16
  - action_phase:travel
接入状态键：[M] <same>

## Shot scene_004-2 | 8s

叙事职责：[D] 升级：贴身跟随让速度可触，跨排水沟是第一个障碍峰值；镜末的急变线与下蹲把叙事引向藏袋决定。
剧本事实：[D] L44——阿泽跨过排水沟，在转角处滑向货车（藏袋动作于下一镜完成）。
原文定位：[M] scene_004 L44-L44
生成单元：[M] 一个独立 SD2.0 视频段，时长从 0 秒到 8 秒。
场景表达：[M] <action_chase>
时间控制：[M] <second_nodes>

摄影设计：[D] 坡道内侧手持侧跟位，24mm 广角近距，与阿泽同速沿可通行路面向右横移；跟随晃动保留，镜末随他减速。
构图设计：[D] 阿泽持续占画面中带偏左，奔跑方向向右；钠灯一盏接一盏从画面上缘掠过，立柱作背景速度参照；排水沟自画面右侧进入作前景障碍；货车尾部在镜末进入画面右前。
光影设计：[D] 钠灯顶光间歇掠过，色温2200K，光比1:16；暗带里以湿面反光维持轮廓；跨沟瞬间水面反光碎裂；全镜光位恒定。
表演设计：[D] 步幅节奏清晰：调整步—蹬地起跳—腾空—落地连步；急变线时肩膀先倾、重心下沉；进入货车侧阴影带时膝盖弯曲入蹲，文件袋从胸前转到右手。

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无

视觉时间线：[D] [0.0s][SB] 手持侧跟中景：阿泽在 P4 坡道段全速向右奔跑，文件袋抱在左臂与胸口之间，右臂摆动，钠灯一盏接一盏从画面上缘掠过，背景立柱连续后退，雨丝斜穿灯光。
  [1.0s] 前方路面出现横贯的排水沟，沟内雨水成流，反着橙光。
  [2.0s] 阿泽步幅调整，右脚蹬地起跳。
  [3.0s][SB] 跨越排水沟的腾空瞬间：水面倒影被落点砸碎，扇形水花溅起。
  [4.0s] 落地连步，身体前倾冲向转角，画面右前方进入停着的货车尾部。
  [5.0s] 阿泽向货车一侧急变线，肩膀先倾，重心下沉开始减速。
  [6.0s] 他滑入货车旁的阴影带，膝盖弯曲进入蹲姿，文件袋从胸前转到右手。
  [7.0s] 蹲姿压低到位，右手携袋探向车底黑暗边缘。
  [8.0s][SB] 结束帧：阿泽蹲在货车侧面阴影里，右手与文件袋抵在车底空隙边缘，头转向来路方向一瞥。
声音设计：[D] 近距雨声与同步奔跑喘息贴耳；3.0 秒落地水花重响；5.0 秒鞋底急刹摩擦；7.0 秒布料贴地的窸窣；无对白。

## Boundary scene_004-B2 | scene_004-2 -> scene_004-3

边界关系：[M] <continuous>
转场执行：[M] <post_production>
剪辑触发：[D] 蹲滑到位、文件袋触及车底空隙边缘的瞬间切出，进入决定的静止视角。
交接描述：[D] 阿泽蹲在货车侧面，右手携文件袋抵在车底边缘；追赶者仍在下层坡道逼近（画外脚步）。该状态为前镜结束帧与后镜 0 秒地面低机位画面共用。
交出状态键：[M]
  - character:a_ze position:carpark|p4_corner_truck_side|crouched facing:upslope_north screen_direction:static posture:crouch_right_hand_extending_bag_to_truck_underside
  - character:chaser_a position:carpark|ramp_p3_upper|running facing:upslope_north screen_direction:left_to_right posture:running_offscreen
  - character:chaser_b position:carpark|ramp_p3_upper|running facing:upslope_north screen_direction:left_to_right posture:running_offscreen
  - prop:file_bag held_by:a_ze location:at_truck_underside_edge
  - prop:truck held_by:none location:p4_corner_bay_parked_engine_off
  - light_main direction:sodium_lamps_overhead_spaced color_temp:2200K ratio:1:16
  - action_phase:prepare
接入状态键：[M] <same>

## Shot scene_004-3 | 5s

叙事职责：[D] 决定独立成镜：全场唯一稳定机位看文件袋滑入车底黑暗——观众独享藏匿点信息，与阿泽结成同谋视角。
剧本事实：[D] L44——把文件袋滑进一辆停着的货车底部，自己继续向顶层跑。
原文定位：[M] scene_004 L44-L44
生成单元：[M] 一个独立 SD2.0 视频段，时长从 0 秒到 5 秒。
场景表达：[M] <action_chase>
时间控制：[M] <half_second_nodes>

摄影设计：[D] 货车旁地面低机位，镜头贴湿地面静置，视轴平视车底空隙；35mm；完全稳定，无晃动——全场唯一静置镜头。
构图设计：[D] 车底空隙横贯画面中带，上缘是车厢底沿的雨滴串，下缘是映着钠灯橙光的湿地面；画面右侧入画阿泽的蹲姿双腿与持袋右手；车底深处的内侧车轮是滑行终点的黑色锚点。
光影设计：[D] 钠灯光从画面外上方打在湿地面上形成橙色反光带，色温2200K，光比1:16；车底空隙近全黑，文件袋入内后只余轮廓；全镜光位恒定。
表演设计：[D] 手部与腿部表演：右手一次发力平推，随即抽回；双腿蹬地起身离画，动作连贯无回望；袋的滑行、撞停、静止是本镜的全部主角。

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无

视觉时间线：[D] [0.0s][SB] 地面低机位：货车底部空隙横贯画面，湿地面映着钠灯橙光，雨滴沿车厢底沿成串下落；画面右侧是阿泽的蹲姿双腿，右手把文件袋抵在车底空隙边缘。
  [0.5s] 右手发力，文件袋贴地滑入车底空隙。
  [1.0s] 袋底擦过湿地面，拖出一道水痕滑向车底深处。
  [1.5s][SB] 文件袋撞上内侧车轮停住，陷进车底黑暗，只余轮廓。
  [2.0s] 阿泽的手抽回出画，双腿蹬地发力。
  [2.5s] 双腿离画，画面只剩车底空隙与串落的雨滴。
  [3.0s] 画外右侧奔跑脚步声远去，地面水洼晃动一次。
  [3.5s] 车底黑暗静止，袋的轮廓与内侧车轮融成一团暗影。
  [4.0s] 雨滴连续打在车底边沿，溅起细小水点。
  [4.5s] 橙色反光在湿面上轻微颤动，画面再无新运动。
  [5.0s][SB] 定格：车底空隙的黑暗收着文件袋的轮廓，地面水洼恢复平静。
声音设计：[D] 贴地声场：0.5-1.5 秒袋底刮地与撞轮胎的闷响；2.0 秒蹬地发力；3.0 秒起脚步声向右远去；滴水声特写级放大；无对白。

## Boundary scene_004-B3 | scene_004-3 -> scene_004-4

边界关系：[M] <continuous>
转场执行：[M] <post_production>
剪辑触发：[D] 脚步声远去、水洼平复的静止瞬间切出，把画面交给即将到来的追赶者。
交接描述：[D] 文件袋已停在车底内侧车轮旁；阿泽在货车上方坡道继续奔跑（画外）；追赶者逼近 P4 转角。后镜自货车后轮低位接同一时刻。
交出状态键：[M]
  - character:a_ze position:carpark|p4_beyond_truck_upslope|running facing:upslope_north screen_direction:left_to_right posture:running_offscreen_hands_empty
  - character:chaser_a position:carpark|p4_corner_approach|running facing:upslope_north screen_direction:left_to_right posture:running_offscreen
  - character:chaser_b position:carpark|p4_corner_approach|running facing:upslope_north screen_direction:left_to_right posture:running_offscreen
  - prop:file_bag held_by:none location:under_truck_against_inner_wheel
  - prop:truck held_by:none location:p4_corner_bay_parked_engine_off
  - light_main direction:sodium_lamps_overhead_spaced color_temp:2200K ratio:1:16
  - action_phase:travel
接入状态键：[M] <same>

## Shot scene_004-4 | 8s

叙事职责：[D] 信息差落地：追赶者紧贴藏匿点跑过、视线锁着高处背影——观众知道的比他们多；前景车底阴影是无声的赌注。
剧本事实：[D] L45——追赶者只看见他的背影，越过货车追了上去。
原文定位：[M] scene_004 L45-L45
生成单元：[M] 一个独立 SD2.0 视频段，时长从 0 秒到 8 秒。
场景表达：[M] <action_chase>
时间控制：[M] <second_nodes>

摄影设计：[D] 货车后轮后方低位机位，借车尾遮挡，视轴朝右上坡道方向；32mm；轻微手持呼吸，无位移。
构图设计：[D] 前景左下：货车后轮与车底阴影一角压住画面；中景：转角路面与排水沟延伸的湿面反光；远景右上：上层坡道灯锥里阿泽缩小的背影；追赶者的通过路线横穿中景。
光影设计：[D] 钠灯自画面外上方照亮转角路面，色温2200K，光比1:16；车底阴影保持全黑；远景灯锥雨幕显形；全镜光位恒定。
表演设计：[D] 两名追赶者一前一后、步幅全开，视线始终锁定右上方背影，头部无一次下垂；掠过车尾时肩膀擦近前景边缘，带起水花。

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无

视觉时间线：[D] [0.0s][SB] 车尾低位构图：前景左下是货车后轮与车底阴影一角，中景转角路面空置反着橙光，远景右上灯锥里阿泽的背影正向更高层缩小，雨丝在灯下斜落。
  [1.0s] 画面左侧外传来两组逼近的脚步水花声，由弱转强。
  [2.0s][SB] 两名追赶者一前一后冲入画面左缘，紧贴货车侧面跑过，视线锁着右上方的背影。
  [3.0s] 前一名追赶者掠过车尾，肩膀擦近前景边缘，带起一片水花。
  [4.0s] 后一名追赶者跟进通过，两人的头始终朝向右上高处。
  [5.0s] 两名追赶者在转角向右上加速，先后进入上一层灯锥。
  [6.0s] 两个背影在雨幕中缩小，脚步声开始衰减。
  [7.0s] 转角路面重新空置，雨点连续敲击货车顶棚。
  [8.0s][SB] 定格：前景车底阴影纹丝未动，远景右上两名追赶者的背影没入更高一层，转角只剩雨声。
声音设计：[D] 雨声与车顶金属敲击贯穿；1.0-6.0 秒双人脚步由逼近、通过到远去的完整声像移动；无对白。

## Boundary scene_004-B4 | scene_004-4 -> scene_004-5

边界关系：[M] <continuous>
转场执行：[M] <post_production>
剪辑触发：[D] 追赶者背影没入上层、转角完全空置的瞬间切出，跳到顶层接结果。
交接描述：[D] 追赶者已上行出画，文件袋静止于车底；阿泽正冲上顶层露天层。后镜以顶层固定机位接他跑入画面的同一时刻。
交出状态键：[M]
  - character:a_ze position:carpark|rooftop_entry|running facing:upslope_north screen_direction:left_to_right posture:running_hands_empty
  - character:chaser_a position:carpark|upper_ramp_offscreen|running facing:upslope_north screen_direction:left_to_right posture:running_offscreen
  - character:chaser_b position:carpark|upper_ramp_offscreen|running facing:upslope_north screen_direction:left_to_right posture:running_offscreen
  - prop:file_bag held_by:none location:under_truck_against_inner_wheel
  - prop:truck held_by:none location:p4_corner_bay_parked_engine_off
  - light_main direction:sodium_lamps_overhead_spaced color_temp:2200K ratio:1:16
  - action_phase:travel
接入状态键：[M] <same>

## Shot scene_004-5 | 12s

叙事职责：[D] 释放与反转：奔跑在顶层边缘耗尽，静止里楼下引擎点火——舍弃换来的安全瞬间失控，全片在未知中收束。
剧本事实：[D] L47——阿泽到达顶层边缘后停下，听见下方传来货车发动的声音。
原文定位：[M] scene_004 L47-L47
生成单元：[M] 一个独立 SD2.0 视频段，时长从 0 秒到 12 秒。
场景表达：[M] <suspense_reveal>
时间控制：[M] <event_nodes>

摄影设计：[D] 顶层露天固定位，三脚架完全稳定，视轴朝护栏与城市黑夜方向；35mm 中远景；无运动——释放段回归静止。
构图设计：[D] 空旷露天顶层占画面下半，右侧边缘护栏切出城市黑夜的负空间；一盏灯杆在画面左上把雨幕照成锥形；阿泽的奔跑终点设在护栏前偏右的视觉重心；画面外下方是声源方向。
光影设计：[D] 顶层灯杆钠光为主，色温2200K，光比1:16；雨幕只在灯锥内显形；护栏外城市黑夜留少量远处光点；全镜光位恒定。
表演设计：[D] 冲入画面时速度已散、步幅踉跄；停住后双手空垂，肩背随喘息大幅起伏，雨水顺下颌成线；引擎声起时头部猛转向右下方声源，随后半步抵住护栏、上身探出边缘向下看，定住。

生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无

视觉时间线：[D] [0.0s][SB] 顶层露天固定中远景：空旷雨夜楼顶，右侧边缘护栏外是城市黑夜，左上灯杆把雨幕照成锥形；阿泽从画面左侧跑入，速度已散，步幅踉跄，双手空空。
  [2.5s] 他减速踉跄两步，在护栏前停住，双手垂在身侧，肩背随喘息大幅起伏，雨水顺下颌成线。
  [5.0s][SB] 楼下一声引擎点火轰响穿过楼板；阿泽的头猛地转向画面右下方声源。
  [7.5s] 他上前半步抵住护栏，上身探出边缘向下看，背影绷直。
  [10.0s] 引擎声转入持续怠速，混进雨声；阿泽保持凭栏下望的姿势，静止。
  [12.0s][SB] 定格：顶层边缘的阿泽背影凭栏静止，雨幕在灯锥中连续落下，画面外下方引擎声持续。
声音设计：[D] 开阔雨面沙声与近距喘息贯穿；5.0 秒楼下货车引擎点火轰响——全场核心声音事件，随后转入持续怠速并与雨声混合直到镜末；无对白。

## Boundary scene_004-B5 | scene_004-5 -> SCENE_EXIT

边界关系：[M] <scene_exit>
转场执行：[M] <post_production>
剪辑触发：[D] 凭栏静帧保持两秒后切黑场，全片结束。
交接描述：[D] 全片终止状态：阿泽两手空、凭栏立于顶层边缘雨中；文件袋最后可见位置为车底内侧车轮旁；货车引擎在画面外下方持续怠速。黑场后引擎与雨声延续一秒收束（后期），无下一场。
交出状态键：[M]
  - character:a_ze position:carpark|rooftop_edge_railing|standing facing:downward_over_railing screen_direction:static posture:leaning_on_railing_looking_down_hands_empty
  - character:chaser_a position:carpark|upper_ramp_offscreen|unseen facing:upslope_north screen_direction:static posture:offscreen
  - character:chaser_b position:carpark|upper_ramp_offscreen|unseen facing:upslope_north screen_direction:static posture:offscreen
  - prop:file_bag held_by:none location:under_truck_last_seen_position
  - prop:truck held_by:none location:p4_corner_bay_engine_running
  - light_main direction:sodium_lamps_overhead_spaced color_temp:2200K ratio:1:16
  - action_phase:static
  - environment:truck_engine_idling_below_rain_continuous
