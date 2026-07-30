ADV_S1-1: spatial_feasibility — Camera travels "through the center of the desk" at 3.0s; solid desk physically blocks the camera path.
ADV_S1-1: light_source — Second main light "shines through the solid right wall" at 6.0s; no window or opening exists, light cannot pass through solid wall.
ADV_S1-1: story_fidelity — Script requires Mara to rise from chair; Video [6.0s] says "Mara remains seated," contradicting core script action.
ADV_S1-1: view_sync — Storyboard 6.0s: "Mara stands"; Video [6.0s]: "Mara remains seated." Same timestamp, contradictory physical state between views.
ADV_S1-1: prompt_visibility — "[6.0s] ... or the camera may circle behind her if space permits" is unresolved branch; Director must pick one path, not defer to generation model.
ADV_S1-1: boundary_continuity — Exit handoff says "Mara stands" but Video [6.0s] says "remains seated"; internal state self-contradictory, next shot cannot receive reliably.
ADV_S1-2: boundary_continuity — ADV_S1-1 exit: Mara on right side of desk; ADV_S1-2 [0.0s]: Mara on left side. Continuous handoff broken by position teleport between shots.
ADV_S1-2: view_sync — Storyboard coat is RED; Video Prompt coat is BLUE. Categorical color mismatch between derived views at same timestamp.
ADV_S1-2: story_fidelity — Storyboard coat is red; script facts specify coat is blue. Script fact violated in Storyboard view.
