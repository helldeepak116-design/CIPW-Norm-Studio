"""CIPW Norm Studio: calculation-engine foundation.

This module provides molecular input validation and auditable
stoichiometric allocation primitives.

It is NOT yet a complete Kelsey (1965) implementation.
Unsupported allocation rules fail explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from config.oxide_config import OXIDE_CONFIG, OXIDE_ORDER
from src.data_validation import validate_oxide_composition


@dataclass
class CalculationStep:
    rule: str
    description: str
    reactants: dict[str, float]
    products: dict[str, float]
    remaining: dict[str, float]


@dataclass
class CIPWResult:
    status: str
    molecular_proportions: dict[str, float]
    normative_minerals: dict[str, float]
    intermediates: dict[str, Any]
    audit_trail: list[CalculationStep] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def molecular_proportions(composition: dict[str, float]) -> dict[str, float]:
    """Convert oxide weight percentages to molecular proportions."""
    validation = validate_oxide_composition(composition)

    if not validation["valid"]:
        raise ValueError("; ".join(validation["errors"]))

    return {
        oxide: float(composition[oxide]) / OXIDE_CONFIG[oxide]["molecular_weight"]
        for oxide in OXIDE_ORDER
    }


def allocate_stoichiometric_reaction(
    available: dict[str, float],
    coefficients: dict[str, float],
) -> tuple[float, dict[str, float]]:
    """Calculate the maximum reaction extent for supplied reactants.

    Coefficients are positive reactant requirements per reaction extent.
    This is a generic auditable allocation primitive, not a mineral rule.
    """
    if not coefficients:
        raise ValueError("At least one reaction coefficient is required.")

    for oxide, coefficient in coefficients.items():
        if oxide not in available:
            raise ValueError(f"Missing reactant: {oxide}")
        if coefficient <= 0:
            raise ValueError("Reaction coefficients must be positive.")
        if available[oxide] < 0:
            raise ValueError("Available molecular amounts cannot be negative.")

    extent = min(
        available[oxide] / coefficient
        for oxide, coefficient in coefficients.items()
    )

    consumed = {
        oxide: extent * coefficient
        for oxide, coefficient in coefficients.items()
    }

    remaining = available.copy()

    for oxide, amount in consumed.items():
        remaining[oxide] -= amount
        if abs(remaining[oxide]) < 1e-12:
            remaining[oxide] = 0.0

    return extent, remaining


def calculate_cipw_norm(composition: dict[str, float]) -> CIPWResult:
    """Validate composition and return the current engine status.

    Mineral allocation is deliberately disabled until the complete
    Kelsey rules and coefficients have been transcribed and tested.
    """
    validation = validate_oxide_composition(composition)

    if not validation["valid"]:
        raise ValueError("; ".join(validation["errors"]))

    molecular = molecular_proportions(composition)

    return CIPWResult(
        status="FOUNDATION_ONLY",
        molecular_proportions=molecular,
        normative_minerals={},
        intermediates={
            "analytical_total": validation["analytical_total"],
            "molecular_proportions": molecular.copy(),
        },
        warnings=[
            "Full Kelsey (1965) normative allocation is not yet implemented.",
            "No normative mineral percentages have been calculated.",
        ],
    )
