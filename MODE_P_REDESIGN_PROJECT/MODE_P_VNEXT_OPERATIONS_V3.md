<!-- MODE_P_VNEXT_AUTHORITY: architecture-v3.0 -->

# MODE:P vNext v3.0 A10 媒体证据操作协议

> 此文件是 A10 的 fail-closed 操作协议，不是媒体证据，也不构成视觉验收、用户批准或生产切换授权。

## 1. 不可替代的边界

本协议只落实 `MODE_P_VNEXT_ARCHITECTURE_REDESIGN_V3.0.md`（SHA256
`a8d58de8d9865d989f567b78d49c1c7de2251e061c7887b6fe2d8018797a830a`）第 13、15 A10、18 节：

- A10 必须有非空的、可在本地复核的真实媒体文件和帧文件；JSON 字段、测试夹具、截图文本、模型陈述或默认配置都不是媒体。
- v4 与 vNext 必须从同一个不可变 `scene_digest` 生成独立媒体运行；不得把一方的文件或提示词复制给另一方冒充对照。
- 每一帧必须关联实际媒体文件、内容 SHA256、运行 ID，以及产生失败/发现的 Artifact 或 capability 归因。
- 回滚演练只证明 v4 保持生产入口；A10 不得修改 v4、FeatureGate、生产状态或 `production_switch_authorized=false`。
- `OWNER_PREVIEW_APPROVAL` 是用户本人在独立目录提交的决定，必须绑定最终媒体证据文件的 SHA256。执行器、模型、测试、worker 和此文件都不能代填或代签。

## 2. A10 运行目录和证据包

每次候选预览使用唯一目录：

```text
MODE_P_REDESIGN_PROJECT/vnext_release_runs/A10/<immutable-run-id>/
  MEDIA_VISUAL_ACCEPTANCE.json
  v4/<actual-rendered-media-and-frames>
  vnext/<actual-rendered-media-and-frames>
  rollback/<rollback-drill-record>
```

`MEDIA_VISUAL_ACCEPTANCE.json` 必须是实际媒体的清单，而不是模板占位符。其最小可验证内容如下；所有相对路径必须留在上述 A10 目录内。

| 字段 | 必须满足的条件 |
|---|---|
| `kind` | 精确为 `MEDIA_VISUAL_ACCEPTANCE` |
| `accepted` | 仅在独立媒体审阅已接受后为 `true` |
| `evidence_mode` | 精确为 `EXTERNAL_REAL_MEDIA`，不得为 fixture、mock、sample 或 synthetic |
| `architecture_authority_sha256` | 精确为冻结的 v3.0 SHA256 |
| `media_runs` | 至少各一个 `track=v4` 与 `track=vnext` 的真实运行；每项含运行 ID、provider、同一 `scene_digest`、开始/结束时间、实际媒体路径及其 SHA256、输入 Artifact/capability 引用、provider/运行记录文件及其 SHA256、以及归因 |
| `frame_evidence` | 非空；每帧含运行 ID、帧索引、毫秒时间戳、实际帧路径及 SHA256、审阅检查项和归因 |
| `v4_vnext_comparison` | 精确绑定两个不同轨道的运行、共同 `scene_digest`、非空帧对和审阅观察 |
| `vnext_runtime_binding` | vNext VEC/Projection ID，以及在 A10 目录中可复核的 VEC/Projection/A8 `RUN.json`/`RESULT.json` 记录文件和内容哈希 |
| `rollback_drill` | 非空的演练记录文件及其 SHA256；前后 production entry 均为 `v4_unchanged`，且 switch 始终为 `false` |
| `production_switch_authorized` | 精确为 `false` |

媒体与帧文件必须是可识别的图片或视频二进制，长度非零，并与清单 SHA256 一致。证据验证只检查可复核性和归因完整性；它**不**替代人的视觉判断。

## 3. 执行顺序

1. 记录 v4 与 vNext 的同场输入摘要，确认二者独立运行且 production entry 仍是 `v4_unchanged`。
2. 在受控的外部渲染/验证环境中生成实际媒体和可查看帧，将原始文件与 provider/运行记录复制到唯一 A10 目录；不得用本地测试输出替代。
3. 填写 `MEDIA_VISUAL_ACCEPTANCE.json` 的真实路径、二进制 SHA256、输入引用、失败归因、对照和回滚演练。运行 A10 注册测试；无证据包时测试必须审计式 skip，发现伪造/缺失物理文件时必须失败。
4. 仅在该测试通过、媒体可复查且人工媒体审阅接受后，使用已领取 A10 锁的执行器运行：

   ```text
   python -m mode_p_vnext.release_control record-media-acceptance \
     --owner <a10-lock-owner> --token <a10-lock-token> \
     --evidence <A10/MEDIA_VISUAL_ACCEPTANCE.json>
   ```

5. 用户本人独立查看同一份媒体。若本人明确批准，**用户本人**在独立的
   `MODE_P_REDESIGN_PROJECT/vnext_owner_approvals/<approval-id>/` 中创建
   `OWNER_PREVIEW_APPROVAL`，其中 `media_evidence_sha256` 必须等于控制器刚记录的媒体证据 SHA256，`scope=OWNER_APPROVED_PREVIEW`，并保持
   `production_switch_authorized=false`。任何非本人创建、模型生成或默认批准一律无效。
6. 仅由用户本人提交后，记录批准、复跑注册验证、执行 audit，并由 ReleaseLedger 判定 A10 是否可 complete。即使完成，也只会得到切换提案资格，绝不切换生产。

## 4. 失败关闭条件

以下任一情况不得调用媒体接受或用户批准命令：没有真实渲染器/验证器、没有可复核媒体二进制、没有同场 v4/vNext 对照、没有回滚演练、媒体或帧哈希不一致、任何归因缺失、vNext 不能绑定到真实文本运行，或用户本人尚未提交批准。应使用 ReleaseLedger `fail` 记录该 A10 失败，并保持两个手工门均为 `false`。
