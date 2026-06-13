# MODE: VIBECODABLE
# BRAAT BLOCK: Resource accounting model
# MISSION: Every feature must map lost -> measured -> recovered -> reported.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecoveryEstimate:
    name: str
    lost: float
    measured: float
    recovered: float
    unit: str
    explanation: str


def recovered_token_cost(duplicated_calls: int, avg_cost_per_call: float) -> float:
    return round(max(0, duplicated_calls) * max(0.0, avg_cost_per_call), 6)


def recovered_engineer_time(avoidable_context_reconstruction_minutes: float) -> float:
    return round(max(0.0, avoidable_context_reconstruction_minutes), 2)


def estimate_context_minutes(tokens_avoidable: int, tokens_per_minute: int = 700) -> float:
    if tokens_per_minute <= 0:
        raise ValueError("tokens_per_minute must be positive")
    return round(max(0, tokens_avoidable) / tokens_per_minute, 2)


def percent_recovered(total: float, avoidable: float) -> float:
    if total <= 0:
        return 0.0
    return round((avoidable / total) * 100, 2)
