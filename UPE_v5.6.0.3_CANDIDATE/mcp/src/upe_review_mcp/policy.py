"""Pure deterministic policy for the UPE review MCP adapter."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from hmac import compare_digest
from typing import Final


class QualityProfile(StrEnum):
    ECONOMY = "economy"
    BALANCED = "balanced"
    QUALITY = "quality"


@dataclass(frozen=True, slots=True)
class ModelRoute:
    reviewer_model: str
    rewriter_model: str


@dataclass(frozen=True, slots=True)
class TokenPrice:
    input_per_million_usd: float
    cached_input_per_million_usd: float
    output_per_million_usd: float


MODEL_ROUTES: Final[dict[QualityProfile, ModelRoute]] = {
    QualityProfile.ECONOMY: ModelRoute("gpt-5.6-luna", "gpt-5.6-terra"),
    QualityProfile.BALANCED: ModelRoute("gpt-5.6-terra", "gpt-5.6-terra"),
    QualityProfile.QUALITY: ModelRoute("gpt-5.6-sol", "gpt-5.6-sol"),
}

# Dated snapshot: 2026-07-26, standard processing, per 1M text tokens.
TOKEN_PRICES: Final[dict[str, TokenPrice]] = {
    "gpt-5.6-luna": TokenPrice(1.00, 0.10, 6.00),
    "gpt-5.6-terra": TokenPrice(2.50, 0.25, 15.00),
    "gpt-5.6-sol": TokenPrice(5.00, 0.50, 30.00),
}

MAX_FIELD_CHARS: Final[int] = 300_000
MAX_TOTAL_CHARS: Final[int] = 650_000
MIN_REVIEW_ROUNDS: Final[int] = 1
MAX_REVIEW_ROUNDS: Final[int] = 3


def text_sha256(text: str) -> str:
    """Return lowercase SHA-256 for the exact UTF-8 text."""
    return sha256(text.encode("utf-8")).hexdigest()


def verify_text_sha256(text: str, expected_sha256: str) -> bool:
    """Compare a supplied lowercase SHA-256 without timing-leaky equality."""
    normalized = expected_sha256.strip().lower()
    return len(normalized) == 64 and compare_digest(text_sha256(text), normalized)


def validate_request_limits(fields: dict[str, str], max_review_rounds: int) -> None:
    """Fail closed before a paid API call when size or round limits are invalid."""
    if not MIN_REVIEW_ROUNDS <= max_review_rounds <= MAX_REVIEW_ROUNDS:
        raise ValueError(
            f"max_review_rounds must be {MIN_REVIEW_ROUNDS}..{MAX_REVIEW_ROUNDS}"
        )
    empty = [name for name, value in fields.items() if not value.strip()]
    if empty:
        raise ValueError(f"required fields are empty: {', '.join(sorted(empty))}")
    oversized = [name for name, value in fields.items() if len(value) > MAX_FIELD_CHARS]
    if oversized:
        raise ValueError(
            f"fields exceed {MAX_FIELD_CHARS} characters: {', '.join(sorted(oversized))}"
        )
    total = sum(len(value) for value in fields.values())
    if total > MAX_TOTAL_CHARS:
        raise ValueError(f"total text exceeds {MAX_TOTAL_CHARS} characters")


def review_passes(
    *,
    blockers_remaining: bool,
    mandatory_dimensions_score: int,
    projected_median_next_gain: float,
    projected_upper_next_gain: float,
) -> bool:
    """Apply the exact UPE v5.6.0.3 terminal stop contract."""
    return (
        not blockers_remaining
        and mandatory_dimensions_score >= 4
        and projected_median_next_gain < 2.0
        and projected_upper_next_gain <= 3.0
    )


def estimate_standard_cost_usd(
    *,
    model: str,
    input_tokens: int,
    cached_input_tokens: int,
    output_tokens: int,
) -> float:
    """Estimate standard text-token cost from the dated price table."""
    if model not in TOKEN_PRICES:
        raise ValueError(f"unsupported price model: {model}")
    if min(input_tokens, cached_input_tokens, output_tokens) < 0:
        raise ValueError("token counts cannot be negative")
    if cached_input_tokens > input_tokens:
        raise ValueError("cached_input_tokens cannot exceed input_tokens")
    price = TOKEN_PRICES[model]
    uncached = input_tokens - cached_input_tokens
    cost = (
        uncached * price.input_per_million_usd
        + cached_input_tokens * price.cached_input_per_million_usd
        + output_tokens * price.output_per_million_usd
    ) / 1_000_000
    return round(cost, 8)
