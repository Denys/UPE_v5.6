from __future__ import annotations

import pytest

from upe_review_mcp.policy import (
    MODEL_ROUTES,
    QualityProfile,
    estimate_standard_cost_usd,
    review_passes,
    text_sha256,
    validate_request_limits,
    verify_text_sha256,
)


def test_hash_binding_accepts_exact_text_and_rejects_change() -> None:
    candidate = "frozen candidate\n"
    digest = text_sha256(candidate)
    assert verify_text_sha256(candidate, digest)
    assert not verify_text_sha256(candidate + "x", digest)


def test_exit_contract_requires_every_gate() -> None:
    assert review_passes(
        blockers_remaining=False,
        mandatory_dimensions_score=4,
        projected_median_next_gain=1.99,
        projected_upper_next_gain=3.0,
    )
    assert not review_passes(
        blockers_remaining=True,
        mandatory_dimensions_score=5,
        projected_median_next_gain=0,
        projected_upper_next_gain=0,
    )
    assert not review_passes(
        blockers_remaining=False,
        mandatory_dimensions_score=3,
        projected_median_next_gain=0,
        projected_upper_next_gain=0,
    )
    assert not review_passes(
        blockers_remaining=False,
        mandatory_dimensions_score=5,
        projected_median_next_gain=2.0,
        projected_upper_next_gain=3.0,
    )
    assert not review_passes(
        blockers_remaining=False,
        mandatory_dimensions_score=5,
        projected_median_next_gain=1.0,
        projected_upper_next_gain=3.01,
    )


def test_model_routes_are_explicit() -> None:
    assert MODEL_ROUTES[QualityProfile.ECONOMY].reviewer_model == "gpt-5.6-luna"
    assert MODEL_ROUTES[QualityProfile.BALANCED].rewriter_model == "gpt-5.6-terra"
    assert MODEL_ROUTES[QualityProfile.QUALITY].reviewer_model == "gpt-5.6-sol"


def test_standard_cost_uses_cached_rate_without_double_counting() -> None:
    cost = estimate_standard_cost_usd(
        model="gpt-5.6-terra",
        input_tokens=100_000,
        cached_input_tokens=40_000,
        output_tokens=10_000,
    )
    # 60k*2.50/M + 40k*0.25/M + 10k*15/M = 0.31 USD
    assert cost == pytest.approx(0.31)


def test_request_limits_fail_before_api_work() -> None:
    fields = {"a": "x", "b": "y"}
    validate_request_limits(fields, 1)
    with pytest.raises(ValueError, match="1..3"):
        validate_request_limits(fields, 4)
    with pytest.raises(ValueError, match="required fields are empty"):
        validate_request_limits({"a": " "}, 1)
