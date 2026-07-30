ADV_S1-1: spatial_feasibility — Video Prompt [3.0s] 摄影机"直线穿过桌子中心"，运动路径穿透实体桌面，机位路径与道具无法共存，画面必然穿物。
ADV_S1-1: camera_path — [6.0s] "or the camera may circle behind her if space permits" 是带条件假设的未裁决分支，生成模型须在维持机位与环绕到人物身后两个方案间自行猜测，关键运镜未被唯一决定。
ADV_S1-1: light_source — [6.0s] 出现"第二主光穿过实心右墙"，剧本明确房间仅有一盏天花板实用灯，该第二主光无任何来源依据，且光线穿透实体墙面不可成立。
ADV_S1-1: view_sync — Storyboard 6.0s 关键帧为"站在桌右侧面向门"，Video Prompt 同镜 [6.0s] 却写"remains seated"，故事板关键状态未出现在视频时间线上，两视图同一时间点直接冲突。
ADV_S1-1: boundary_continuity — Exit 声明 continuous handoff 且 Mara"站在桌右侧面向门"，但视频时间线终点 6.0s 仍是坐姿，起身动作在 6 秒内无任何可见阶段，交出状态在本镜内无法达成。
ADV_S1-2: boundary_continuity — 入场 [0.0s] Mara 站在"桌左侧"，与 ADV_S1-1 声明的 continuous 交出状态"桌右侧"矛盾，人物在连续交接中瞬移过桌，剧本要求的绕桌移动在两镜时间线中均不可见。
ADV_S1-2: view_sync — Storyboard 0.0s 写"红色外套"，Video Prompt 同点写"蓝色外套"，剧本事实为蓝色外套；同一时间节点两视图对同一属性给出矛盾值，故事板关键帧偏离视频时间线与剧本。
