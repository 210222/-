ADV_S1-1: camera_path — [3.0s] 摄影机"直线穿过桌子中心"，运动路径直接穿过实体桌面，空间上不可执行。
ADV_S1-1: light_source — [6.0s] 写"第二主光穿过实体右墙"，剧本明确房间仅有一盏实用顶灯，该第二主光无依据且实体墙不可透光。
ADV_S1-1: camera_path — [6.0s] "或摄影机绕到她身后（如空间允许）"是未裁决的甲或乙分支加条件句，绕行与否未由导演唯一决定，生成端只能自行猜测。
ADV_S1-1: view_sync — Storyboard 6.0s 关键帧"Mara 站在桌右侧、面向门"未出现在 Video Prompt 同镜时间线，[6.0s] 反而写"仍然坐着"，两视图直接冲突。
ADV_S1-1: action_continuity — 时间线最后节点 [6.0s] 仍坐着，Exit 却交出"站在桌右侧面向门"，起身动作在 6 秒内没有任何可见阶段，交出状态无法从画面内容达成。
ADV_S1-2: boundary_continuity — 标注 continuous 承接，但 ADV_S1-1 交出状态在桌"右侧"，本镜 [0.0s] 接入在桌"左侧"，剧本要求的绕桌移动被跳过，连续承接不成立。
ADV_S1-2: story_fidelity — Storyboard 0.0s 写"红色大衣"，违背剧本事实"她的外套是蓝色"。
ADV_S1-2: view_sync — 同一 0.0s 时点 Storyboard 写红大衣、Video Prompt 写蓝大衣，两视图对同一服装状态相互冲突。
