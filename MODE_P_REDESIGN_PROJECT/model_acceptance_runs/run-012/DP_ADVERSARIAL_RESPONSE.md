ADV_S1-1: camera_path — Video Prompt [3.0s] 写明摄影机"travels in a straight line through the center of the desk"，运动路径直接穿越实体桌面，物理上不可执行，生成结果只能是穿模或桌体消失。
ADV_S1-1: light_source — Video Prompt [6.0s] 出现"a second main light shines through the solid right wall"，但 Script facts 明写房间仅有一盏实用顶灯；第二主光在场景中无依据，且实心墙不可透光，光源位置不可能成立。
ADV_S1-1: prompt_visibility — Video Prompt [6.0s] "or the camera may circle behind her if space permits" 以"或/如果允许"保留两案并存的未裁决机位分支，迫使生成模型自行猜测执行方案。
ADV_S1-1: view_sync — 同一时间点 6.0s，Storyboard 写 Mara "stands on the right side of the desk, facing the door"，Video Prompt 却写 "Mara remains seated"，两视图对本镜结束状态直接矛盾。
ADV_S1-1: action_continuity — Video Prompt 时间线到 [6.0s] 仍为"remains seated"，Exit 却声明她"stands on the right side of the desk facing the door"；起身动作在 6 秒时间线内没有任何节点，交出状态无法由镜内动作产生。
ADV_S1-1: story_fidelity — 剧本明写 Mara "rises from the chair"，但本镜 Video Prompt 时间线从 [0.0s] 坐姿到 [6.0s] "remains seated"，起身这一剧本事实在可生成的时间线中从未发生。
ADV_S1-2: story_fidelity — Storyboard Frame 0.0s 写 Mara "wearing a red coat"，剧本明写 "Her coat is blue"，画面服装事实违背剧本。
ADV_S1-2: view_sync — 同一时间点 0.0s，Storyboard 写红色外套，Video Prompt 写 "wearing a blue coat"，两视图对同一镜同一帧的服装颜色互相矛盾。
ADV_S1-2: boundary_continuity — 本镜入点 [0.0s] Mara "stands on the left side of the desk"，而 ADV_S1-1 以 continuous handoff 交出的状态是"站在桌右侧面向门"；连续边界两侧交出/接入位置不一致，剪切处人物瞬移。
