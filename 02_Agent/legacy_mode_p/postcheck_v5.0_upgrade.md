# Postcheck v5.0 升级补丁

> **适用于**: postcheck_v3.0.md → v5.0

---

## 变更1: 新增5M Verifier验证
```
旧: 5A-5K闭环质检
新: 5A-5K + 5M Verifier验证

5M: Verifier裁决验证
  - 读取 Verifier v2.0 报告的"需返工项"
  - 验证这些项在第二轮修复后是否被解决
  - 验证"标注已知缺陷"的项是否有清晰的人工修复方向
```

## 变更2: Verifier冲突处理
```
Verifier与Postcheck裁决冲突:
  Verifier✅ + Postcheck🛑 → Postcheck优先(最终质检)
  Verifier🛑 + Postcheck✅ → Verifier优先(发现漏检)
  同时🛑 → 🛑双重阻断
```

## 变更3: 知识库版本
```
引用 KB: 03_导演知识库_v4.0.md
     kb_index_v2.0.md（场景路由）
```

## 不变项
```
- 5A-5K原有质检项不变
- 2轮返工上限不变
- 超限降级交付逻辑不变
```
