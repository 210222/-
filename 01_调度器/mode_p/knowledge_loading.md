# Knowledge Loading Policy

MODE:P uses the existing knowledge base as decision ability, not as an
evidence system. No final prompt or DP feedback may expose a rule ID.

## Always-loaded director kernel

Load `knowledge/director_core.md`, `knowledge/sd2.md`, and
`knowledge/performance.md` into the Director system prompt. These are
the active distilled form of the following source material:

- `03_知识库/导演手册_视觉叙事决策框架.md`
- `03_知识库/运镜思维_导演可用运动思维.md`
- `03_知识库/04_构图思维_导演用.md`
- `03_知识库/sd2_model_capability.md`
- `03_知识库/PERFORMANCE_KB.md`

The kernel must teach these linked decisions:

- story beat -> shot distance, angle, and cut rhythm
- camera movement -> motive, spatial path, opening and ending composition
- composition -> visual center, depth, power, negative space, and eye line
- lighting -> physical source, direction, color temperature, ratio, and continuity
- transition -> movement, screen direction, graphic match, or emotional contrast
- subtext -> visible anatomy, gesture, pace, and posture

The DP loads only its governing instruction, factual scene context, canvas
runtime boundaries, `knowledge/sd2.md`, Master/current views when available,
and the actual reference plan. It does not load creative scene capsules or
historical patterns, which would turn technical review into a second design pass.

## Scene capsules

Load one or two capsules according to the script, never the entire legacy KB:

| Scene signal | Capsule focus |
|---|---|
| Two-person dialogue | `knowledge/dialogue.md` |
| Action or pursuit | `knowledge/action.md` |
| Suspense or discovery | `knowledge/suspense.md` |
| Intimate or reflective | `knowledge/reflective.md` |
| Multi-space transition | director kernel only; add the dominant scene capsule |

## SD2.0 capsule

Always apply these model facts:

- Each generated segment is at most 15 seconds.
- Prefer one core action per shot.
- Show at most two clearly readable faces per shot.
- Use physical, positive, visible language in the image description.
- Avoid literal text rendering requests.
- Keep identity anchors ahead of scene/action language when identity stability matters.
- Reduce motion or split the shot when identity, dense action, and multiple faces compete.

## Render memory

Do not load `P-STATE.md` by default. Consult a concise, curated render-failure
note only after a real rendered result repeats a known failure.
