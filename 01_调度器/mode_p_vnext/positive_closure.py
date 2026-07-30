"""MODE:P vNext — Positive Closure & Negative Route Validator (V2.3).

High-risk surfaces must be expressed as positive physical closure, not only as
negation. Negative routes control how forbidden items reach the model.

Spec references: LOOP §11.4-§11.7.
"""

from __future__ import annotations

from typing import List

from mode_p_vnext.schema.visibility_contract import VisibilityContract


def check_positive_closure(contract: VisibilityContract) -> List[str]:
    """Return violations where high-risk surfaces lack positive closure.

    Rule: every item in ``forbidden_qa`` or ``leakage_risks`` should have a
    corresponding entry in ``positive_closure`` that states what the surface
    SHOULD look like (positive physical description), not just what it
    shouldn't be.
    """
    violations: List[str] = []
    risks = set(contract.leakage_risks) | set(contract.forbidden_qa)
    closures = set(contract.positive_closure)

    if risks and not closures:
        violations.append(
            "forbidden_qa/leakage_risks present but positive_closure is empty "
            "— negation alone is a known production risk"
        )

    # Check for shared keywords between risk items and closure items
    for risk in risks:
        # Find any character-level overlap between risk and closure texts
        # (Chinese text doesn't have spaces between words)
        covered = any(
            _texts_share_keywords(risk, closure)
            for closure in closures
        )
        if not covered:
            violations.append(
                f"No positive_closure found for risk item: '{risk}'"
            )

    return violations


# 2-char tokens that are descriptive/property words, not object identifiers.
# These can cause false-positive matches between unrelated risk/closure pairs.
_DESCRIPTOR_TOKENS: frozenset = frozenset({
    "透明", "可见", "不可", "保持", "完整", "表面", "实体",
    "出现", "未经", "错误", "当前", "镜头",
})


def _texts_share_keywords(risk: str, closure: str) -> bool:
    """Return True if *risk* and *closure* share a non-descriptor 2-char token.

    Chinese text doesn't use spaces — we slide a 2-char window over both
    texts and look for matching noun/subject tokens, skipping common
    descriptive words.
    """
    # Collect non-descriptor 2-char tokens from risk
    risk_tokens = set()
    for i in range(len(risk) - 1):
        tok = risk[i:i + 2]
        if tok not in _DESCRIPTOR_TOKENS:
            risk_tokens.add(tok)

    # Check if any risk token appears in closure
    for tok in risk_tokens:
        if tok in closure:
            return True
    return False


def check_negative_route(contract: VisibilityContract) -> List[str]:
    """Return warnings about negative route configuration.

    - ``inline``: warns that negation tokens may leak into generative output
    - ``token_leakage_risk``: warns this needs human QA review
    - ``human_qa_only``: warns forbidden_qa should be documented
    - ``separate_channel``: no warning (ideal case)
    """
    warnings: List[str] = []
    route = contract.negative_route

    if route == "inline":
        if contract.forbidden_qa:
            warnings.append(
                "negative_route='inline' with forbidden_qa: negation tokens "
                "may be interpreted as generation targets"
            )
    elif route == "token_leakage_risk":
        warnings.append(
            "negative_route='token_leakage_risk': requires human QA review "
            "before model submission"
        )
    elif route == "human_qa_only":
        warnings.append(
            "negative_route='human_qa_only': forbidden_qa must be "
            "documented in QA checklist, not sent to model"
        )
    elif route == "separate_channel":
        # Ideal case — no warning needed
        pass

    return warnings
