ADV_S1-1: camera_path — Video Prompt [3.0s]"the camera travels in a straight line through the center of the desk"，摄影机路径直线穿越实体桌子中心，该路径在空间中不可存在。
ADV_S1-1: light_source — Video Prompt [6.0s]"a second main light shines through the solid right wall"，光线穿透实心右墙且剧本设定房间仅有一盏实用吸顶灯，该第二主光无任何物理锚点。
ADV_S1-1: prompt_visibility — Video Prompt [6.0s]含未裁决分支"or the camera may circle behind her if space permits"，机位方案在两选项间未定，生成模型将被迫自行猜测。
ADV_S1-1: view_sync — 6.0s 处 Storyboard 为"Mara stands on the right side of the desk, facing the door"，Video Prompt 同刻却写"Mara remains seated"，同镜同时刻两视图直接冲突。
ADV_S1-1: action_continuity — 剧本要求 Mara 起身，但 Video 时间线 0.0s 坐、6.0s 仍坐，起身动作阶段在 6 秒内全程不可见，Exit 交出的"站立面向门"状态无法由画面达成。
ADV_S1-2: boundary_continuity — ADV_S1-1 以 continuous handoff 交出"Mara 站在桌右侧面向门"，本镜 0.0s 却从"left side of the desk"接入，共享边界两侧位置状态断裂。
ADV_S1-2: view_sync — 0.0s 处 Storyboard 写"wearing a red coat"，Video Prompt 同刻写"wearing a blue coat"，同镜同时刻服装颜色相互冲突。
ADV_S1-2: story_fidelity — Storyboard 0.0s 让 Mara 穿红色外套，违背剧本事实"Her coat is blue"。
