import yaml

with open(r'C:\Users\21022\Desktop\导演系统\导演系统_v5\01_调度器\EP2_plan.yml', 'r', encoding='utf-8') as f:
    plan = yaml.safe_load(f)

plan['segment_frames'] = [
    {
        'segment_id': '①', 'shot_id': '#A1', 'characters_in_frame': ['伊莎贝拉'],
        'keyframes': [
            {'kf_id': '①-1', 'sec_offset': 0, 'global_sec': 0, 'type': 'hold', 'hold_until': 1,
             'action_anchor': '黄铜锁孔居中偏下。右手从上方伸入——拇指食指捏黄铜钥匙·红色标签垂下。钥匙尖对准锁孔·即将插入',
             'description': '深棕色木门板·木纹清晰。锁孔周围铜绿斑点·微磨损。冷白4000K均匀照明·木门冷色调',
             'lighting': 'L1吸顶荧光灯4000K冷白·均匀柔光·锁孔无阴影', 'spatial': '楼道·门外0.5m·锁孔同高1.2m·正面微俯'},
            {'kf_id': '①-2', 'sec_offset': 1, 'global_sec': 1, 'type': 'hold', 'hold_until': 2,
             'action_anchor': '钥匙完全插入锁孔。拇指向右扭动——顺时针方向·手腕外旋·红色标签微晃',
             'description': '锁芯内部机械咬合。手指稳定·动作熟练——她来过这里',
             'lighting': 'L1冷白4000K·黄铜钥匙表面微反光·标签红色饱和', 'spatial': '锁孔同高·钥匙在锁孔中旋转'},
            {'kf_id': '①-3', 'sec_offset': 2, 'global_sec': 2, 'type': 'event',
             'action_anchor': '锁芯弹开。左手握门把下压。右手拔钥匙。门缝从零变为细线——暖黄光涌入',
             'description': '门板绕右边缘门轴旋转·左边缘离开门框向深处移动。缝隙从细线变成一掌宽再变成一半门宽。暖黄三角形亮区投射地面。L形构图完成',
             'lighting': '冷暖双色温共存·4000K冷白左侧+2800K暖黄右侧·交界线锐利', 'spatial': '门半开·锁孔移至左侧·暖光矩形投射地面'}
        ]
    },
    {
        'segment_id': '②', 'shot_id': '#A2', 'characters_in_frame': [],
        'keyframes': [
            {'kf_id': '②-1', 'sec_offset': 0, 'global_sec': 3, 'type': 'hold', 'hold_until': 4,
             'action_anchor': 'POV全景·从门口看向室内。门框为暗色前景框。工业吊灯2800K暖黄·硬光·光锥向下·光锥外全黑',
             'description': '工作台居中·金属零件散落·工具架后墙。光和暗硬的分界线。前1秒完全静止',
             'lighting': 'L2工业吊灯2800K暖黄·光锥+2EV·光锥外-3EV全黑·chiaroscuro', 'spatial': '门口内0.3m·伊莎贝拉眼高1.55m·POV主观'},
            {'kf_id': '②-2', 'sec_offset': 1, 'global_sec': 4, 'type': 'hold', 'hold_until': 5,
             'action_anchor': '摄影机以极慢速度向右摇摄·每秒约1.5度。POV扫过工作台面——枪管哑光·弹簧暗银·螺丝散布。金属表面在暖黄下暖金反光',
             'description': '工具架——扳手·螺丝刀·油壶。摇摄速度匹配审视节奏',
             'lighting': 'L2光锥中心+2EV·金属反光微闪', 'spatial': '工作台左端→右端·视线虚线水平右移'},
            {'kf_id': '②-3', 'sec_offset': 2, 'global_sec': 5, 'type': 'event',
             'action_anchor': '摇摄短暂停住。视线落在手枪扳机一道细微划痕上——金属表面的浅线',
             'description': '弹匣退出·枪膛打开。机械美感——金属与机油·秩序与暴力',
             'lighting': 'L2暖黄光锥覆盖手枪·划痕边缘微细高光', 'spatial': '工作台右侧·手枪居中'},
            {'kf_id': '②-4', 'sec_offset': 3, 'global_sec': 6, 'type': 'hold', 'hold_until': 7,
             'action_anchor': '摄影机以慢速继续向右摇摄·每秒约2度。POV离开光锥最亮区域·画面变暗。白色织物进入视线边缘——灰色毛巾搭在洗手池边',
             'description': '半明半暗中·毛巾轮廓渐显',
             'lighting': '离开光锥中心·+2EV降至-1EV·毛巾在暗区呈浅灰', 'spatial': '洗手池右侧暗区·毛巾位置'},
            {'kf_id': '②-5', 'sec_offset': 4, 'global_sec': 7, 'type': 'hold', 'hold_until': 8,
             'action_anchor': '摇摄落定。特写。灰色毛巾搭在池边·中央暗红血迹·手掌大小·中心深红发黑·边缘浅红褐。棉质纹理清晰。背景全虚。2秒凝视',
             'description': '血迹中心深色发黑·向外扩散变浅。织物白色与血暗红对比在暖黄下偏深红褐',
             'lighting': '半暗区-1EV·血迹暗红在暖黄下偏深红褐·织物纹理侧光可见', 'spatial': '洗手池边缘·毛巾自然下垂·背景全虚'}
        ]
    },
    {
        'segment_id': '③', 'shot_id': '#A3', 'characters_in_frame': ['伊莎贝拉'],
        'keyframes': [
            {'kf_id': '③-1', 'sec_offset': 0, 'global_sec': 8, 'type': 'hold', 'hold_until': 9,
             'action_anchor': 'ECU·右手紧握门把——手掌包握·指关节发白。钥匙插在锁孔中·红色标签微晃。手在微微颤抖',
             'description': '不锈钢门把表面微细划痕。手背被冷白4000K照亮·手心在暗处',
             'lighting': 'L1冷白4000K·手背高光·手心暗部', 'spatial': '楼道·门外0.4m·门把同高1.1m'},
            {'kf_id': '③-2', 'sec_offset': 1, 'global_sec': 9, 'type': 'event',
             'action_anchor': '手指一根一根松开——指关节血色恢复。手掌从门把上离开·手指微屈悬停。VO低语Rico',
             'description': '门把上留下微细手汗痕迹。手指仍微颤',
             'lighting': 'L1冷白4000K·手背从微红到正常色', 'spatial': '门把同高·手悬停半空'},
            {'kf_id': '③-3', 'sec_offset': 2, 'global_sec': 10, 'type': 'event',
             'action_anchor': '身后脚步声——皮靴踩水磨石地面·由远及近。手突然弹开。甩镜——摄影机急速右转·0.5秒内所有东西变成水平模糊条纹',
             'description': '冷白4000K和暖黄2800K在甩镜中混合为暖冷光带。持续0.5秒——模拟听到脚步声后骤然转头',
             'lighting': '4000K冷白+2800K暖黄混合·水平拖尾光带', 'spatial': '甩镜过渡·画面全模糊'},
            {'kf_id': '③-4', 'sec_offset': 2.5, 'global_sec': 10, 'type': 'hold', 'hold_until': 12,
             'action_anchor': '甩镜落定。CU面部·第一次看到她的脸。左脸暖黄2800K边缘光+右脸冷白4000K正面光·分界线沿鼻梁。眼睛睁大·瞳孔定住·嘴唇微张·下巴微抖。头右后转·回看走廊',
             'description': '走廊空无一人。日光灯微闪。脚步声停了。她全程不出声',
             'lighting': '双色温同框·左暖右冷·分界鼻梁·瞳孔在暗处放大', 'spatial': '面部居中偏左·背景走廊纵深'}
        ]
    },
    {
        'segment_id': '④', 'shot_id': '#A4', 'characters_in_frame': ['伊莎贝拉'],
        'keyframes': [
            {'kf_id': '④-1', 'sec_offset': 0, 'global_sec': 12, 'type': 'hold', 'hold_until': 14,
             'action_anchor': '全景·空旷走廊。从近到远延伸·日光灯4000K微闪。空无一人。门框在前景底部·半开门·暖黄2800K矩形光柱投射地面。静止2秒',
             'description': '伊莎贝拉从门框中退出——深色背影从暖黄退入冷白。肤色从暖调回冷',
             'lighting': 'L1冷白4000K主导·门缝暖黄矩形在地面', 'spatial': '门口分界线·走廊全景·一点透视'},
            {'kf_id': '④-2', 'sec_offset': 2, 'global_sec': 14, 'type': 'transition', 'hold_until': 17,
             'action_anchor': '伊莎贝拉背影·右手拉门把向身体方向回收。门缝从半开变窄·暖黄矩形缩小。摄影机同时极慢后退·每秒约0.3米',
             'description': '门将合未合——缝隙只剩约5厘米。暖黄光只剩极细垂直线·如激光。面部最后一丝暖色边缘光消失——全脸进入4000K冷白。暖黄光彻底消失',
             'lighting': '暖黄矩形缩小→细线→消失·冷白4000K扩大·暖冷弧线闭环', 'spatial': '门前·dolly back沿走廊中轴·距门0~1.2m',
             'transition_target': {
                 'action_anchor': '门完全闭合——锁舌入位。暖黄光彻底消失。走廊回到纯冷4000K。伊莎贝拉静止1秒',
                 'lighting': '纯冷白4000K·均匀照明·暖光彻底消失',
                 'character_state': [{'character': '伊莎贝拉', 'pose': '静止·面对闭合的门', 'gaze': ''}],
                 'spatial': '距门1.2m·走廊中轴'
             },
             'transition_params': {
                 'color_temp_kelvin': {'start': 2800, 'end': 4000},
                 'position_in_frame': {'start': '近景·门前', 'end': '中景·退后'}
             }},
            {'kf_id': '④-3', 'sec_offset': 5, 'global_sec': 17, 'type': 'event',
             'action_anchor': '门完全闭合。ECU·右手掏钥匙·插入锁孔·手指一扭——锁芯弹响。手持续微抖。虎口微红痕',
             'description': '门已闭合。深棕色木门·冷白4000K下门板颜色偏灰',
             'lighting': '纯冷白4000K·手背均匀照明·黄铜表面微反光', 'spatial': '门把同高1.1m·锁孔居中'},
            {'kf_id': '④-4', 'sec_offset': 6, 'global_sec': 18, 'type': 'hold', 'hold_until': 20,
             'action_anchor': '钥匙拔出——水平滑出。手仍抖。虎口压红痕。红色标签在手心微晃。手悬停半空——最后1秒淡出全黑',
             'description': '冷暖弧线完整闭环——冷白→暖涌入→暖主导→暖收缩→冷闭合',
             'lighting': '纯冷白4000K→灰→黑·淡出', 'spatial': '手+钥匙居中悬停·锁孔在左'}
        ]
    }
]

with open(r'C:\Users\21022\Desktop\导演系统\导演系统_v5\01_调度器\EP2_plan_v2.yml', 'w', encoding='utf-8') as f:
    yaml.dump(plan, f, allow_unicode=True, default_flow_style=False, sort_keys=False, width=200)

print('OK')
for sf in plan['segment_frames']:
    print(f'{sf["shot_id"]}: {len(sf["keyframes"])} keyframes')
