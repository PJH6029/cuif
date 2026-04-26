from __future__ import annotations

from pathlib import Path
from typing import Any

from .extract import extract_text_by_slide, find_shapes


def text_preservation_diff(candidate: str | Path, reference: str | Path, params: dict[str, Any]) -> dict[str, Any]:
    """Return a small structured diff for protected slide text/shape regions."""
    slides = params.get("slides")
    protected_texts = [str(x) for x in params.get("protected_texts", [])]
    selector = params.get("selector")
    candidate_text = extract_text_by_slide(candidate)
    reference_text = extract_text_by_slide(reference)
    mismatches: list[dict[str, Any]] = []

    if slides is None:
        slides = sorted(set(candidate_text) | set(reference_text))
    for slide in [int(s) for s in slides]:
        cand = candidate_text.get(slide, [])
        ref = reference_text.get(slide, [])
        if params.get("compare") == "exact_slide_text" and cand != ref:
            mismatches.append({"slide": slide, "candidate": cand, "reference": ref})

    for text in protected_texts:
        ref_has = any(text.lower() in " ".join(values).lower() for values in reference_text.values())
        cand_has = any(text.lower() in " ".join(values).lower() for values in candidate_text.values())
        if ref_has and not cand_has:
            mismatches.append({"protected_text_missing": text})

    if selector:
        ref_shapes = find_shapes(reference, selector)
        cand_shapes = find_shapes(candidate, selector)
        if len(ref_shapes) != len(cand_shapes):
            mismatches.append({"selector_count_mismatch": selector, "reference": len(ref_shapes), "candidate": len(cand_shapes)})
        else:
            tolerance = float(params.get("tolerance", 0.02))
            for ref_shape, cand_shape in zip(ref_shapes, cand_shapes, strict=True):
                deltas = {
                    "x": abs(ref_shape.x - cand_shape.x),
                    "y": abs(ref_shape.y - cand_shape.y),
                    "w": abs(ref_shape.w - cand_shape.w),
                    "h": abs(ref_shape.h - cand_shape.h),
                }
                if any(delta > tolerance for delta in deltas.values()):
                    mismatches.append({"selector": selector, "deltas": deltas, "tolerance": tolerance})

    return {"mismatches": mismatches, "match": not mismatches}
