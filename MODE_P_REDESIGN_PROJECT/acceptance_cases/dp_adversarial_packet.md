# MODE:P DP Adversarial Review Packet

This fixed packet is used only by explicit `/mode-p-accept`. It is not a
production scene and must never enter delivery or knowledge promotion.

## Script facts

ADV_S1: Mara rises from the chair, moves around the desk, picks up the key at
the door, and leaves. The room has one practical ceiling lamp. Her coat is blue.

## Shot whitelist

- ADV_S1-1
- ADV_S1-2

## Storyboard

### Shot ADV_S1-1 | 6s

Frame 0.0s: Mara sits on the right side of the desk under the ceiling lamp.
Frame 6.0s: Mara stands on the right side of the desk, facing the door.
Transition: continuous handoff to ADV_S1-2.

### Shot ADV_S1-2 | 5s

Frame 0.0s: Mara stands on the left side of the desk wearing a red coat.
Frame 5.0s: Mara reaches the door.
Transition: hard cut to scene exit.

## Video Prompt

### Shot ADV_S1-1 | 6s

Image:
[0.0s] Mara sits on the right side of the desk under the ceiling lamp.
[3.0s] The camera travels in a straight line through the center of the desk.
[6.0s] Mara remains seated while a second main light shines through the solid
right wall, or the camera may circle behind her if space permits.
Sound: room tone and chair movement.
Exit: continuous handoff; Mara stands on the right side of the desk facing the
door.

### Shot ADV_S1-2 | 5s

Image:
[0.0s] Mara stands on the left side of the desk wearing a blue coat.
[5.0s] Mara reaches the door and picks up the key.
Sound: footsteps and a key sound.
Exit: hard cut to scene exit.

## Required response contract

Return issue lines only. Use current Shot IDs and canonical DP fields. Do not
return READY. Review the packet as presented; do not repair it.
