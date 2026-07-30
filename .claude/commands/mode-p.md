---
description: Compatibility alias for the MODE:P current-episode pilot command.
argument-hint: <episode-script-path>
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
---

Treat `$ARGUMENTS` as the current independently uploaded episode script. Read
and execute `.claude/commands/mode-p-pilot.md` exactly. This alias must not use
the retired single-scene controller protocol, `dispatcher_v5.0.md`, legacy
Agents, direct Storyboard/Video authorship, or manual project/episode binding.
