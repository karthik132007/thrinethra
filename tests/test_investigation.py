import pytest
from packages.investigation.agent import ModelReasoning, validate_reasoning


def test_model_citations_must_point_to_retained_evidence():
    valid = ModelReasoning(
        answer="Review the cited measured occupancy.",
        evidence_references=["retained"],
        hypotheses=[
            {"text": "Possible congestion", "evidence_references": ["retained"]}
        ],
        review_steps=["Inspect the frame."],
    )
    assert validate_reasoning(valid, ["retained"]) is valid
    invalid = valid.model_copy(update={"evidence_references": ["invented"]})
    with pytest.raises(ValueError, match="unknown evidence"):
        validate_reasoning(invalid, ["retained"])


def test_model_cannot_introduce_autonomous_enforcement():
    reasoning = ModelReasoning(
        answer="Dispatch a response.",
        evidence_references=["retained"],
        hypotheses=[],
        review_steps=["Inspect source."],
    )
    with pytest.raises(ValueError, match="consequential"):
        validate_reasoning(reasoning, ["retained"])
