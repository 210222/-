<!-- MODE_P_VNEXT_AUTHORITY: architecture-v3.1 -->

# MODE:P vNext v3.1 A10 media evidence operations protocol

> This is an A10 fail-closed operating protocol, not media Evidence, visual acceptance, owner approval, or production-switch authorization.

The protocol implements v3.1 sections 9–13, SHA256 `d5616edc209dcaba3d82a1defe5e11187145399c30143bad6e4e685eb5c4c903`.

## Required real-media package

Every preview candidate uses one immutable directory:

```text
MODE_P_REDESIGN_PROJECT/vnext_release_runs/A10/<immutable-run-id>/
  MEDIA_VISUAL_ACCEPTANCE.json
  v4/<actual media and frames>
  vnext/<actual media and frames>
  rollback/<rollback drill record>
```

`MEDIA_VISUAL_ACCEPTANCE.json` must enumerate non-empty real binary media and frame files. JSON claims, text fixtures, screenshots of text, mock/synthetic output, model descriptions, or default settings are not media evidence. It binds each run to its run ID, provider, same immutable `scene_digest`, source Artifact/capability references, real media path and SHA256, provider/run record and SHA256, frame path/index/timestamp/SHA256, observation, and failure attribution.

There must be independent `track=v4` and `track=vnext` real runs sharing the scene digest, a non-empty frame comparison, and a rollback record showing that production entry was and remains `v4_unchanged` with switch false. vNext proof must bind the real A8 run, VEC, ProjectionAST, and projection digest.

## Sequence and human boundary

1. A10 first verifies real media, frame, attribution, v4/vNext comparison, and rollback evidence using its registered tests.
2. Only after actual visual review accepts the media may the claimed A10 worker call `record-media-acceptance` with the evidence file.
3. The user independently reviews the same media. Only the user may create `OWNER_PREVIEW_APPROVAL` under `vnext_owner_approvals`, with the current media Evidence SHA256, `scope=OWNER_APPROVED_PREVIEW`, and `production_switch_authorized=false`.
4. The controller records the owner approval, re-runs verification, and can complete A10. It still cannot switch production.

Fail closed without real media, a real same-scene v4 comparison, frame hashes, failure attribution, rollback proof, vNext runtime binding, or user-submitted owner approval. Do not create a placeholder approval and do not invoke media acceptance merely because text tests pass.
