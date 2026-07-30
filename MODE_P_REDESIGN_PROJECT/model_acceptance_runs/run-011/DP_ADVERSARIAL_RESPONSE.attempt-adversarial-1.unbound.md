ADV_S1-1: spatial_feasibility — [3.0s] 摄影机"直线穿过桌子中央"，运动路径直接穿透实体桌面道具，机位路径与桌子无法在该房间内共存。
ADV_S1-1: light_source — [6.0s] 出现"第二主光穿过实心右墙"，剧本设定房间仅有一盏实用吸顶灯，该光源既无剧本依据也无法穿透实墙成立。
ADV_S1-1: camera_path — [6.0s] "or the camera may circle behind her if space permits" 把是否环绕机移留成未裁决的甲或乙条件分支，生成模型将被迫自行猜测执行方案。
ADV_S1-1: view_sync — Storyboard Frame 6.0s 为 Mara 站在桌右侧面向门，而 Video Prompt [6.0s] 写"remains seated"，该故事板关键帧未出现在同镜视频时间线上。
ADV_S1-1: action_continuity — Video Prompt 时间线到 [6.0s] 仍"remains seated"，Exit 却交出"站在桌右侧面向门"；起身动作在 6 秒内任何节点都不可见，出口状态无法从时间线到达。
ADV_S1-2: boundary_continuity — 入场 [0.0s] Mara 站在桌左侧，但 ADV_S1-1 的 continuous handoff 交出的是站在桌右侧；共享边界两侧位置左右互换且无任何覆盖该位移的动作。
ADV_S1-2: story_fidelity — Storyboard Frame 0.0s 让 Mara 穿红色外套，剧本明确"Her coat is blue"，外套颜色与剧本事实冲突。
ADV_S1-2: view_sync — 同一 0.0s 关键帧 Storyboard 写红色外套而 Video Prompt 写蓝色外套，两个派生视图对同镜同时刻状态相互冲突。
