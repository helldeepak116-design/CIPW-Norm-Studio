
$ErrorActionPreference = "Stop"

$ProjectRoot = "C:\GeologyProjects\CIPW-Norm-Studio"
Set-Location $ProjectRoot

Write-Host "Preparing CIPW Norm Studio engine..." -ForegroundColor Cyan

$directories = @(
    "src",
    "tests",
    "outputs\calculations"
)

foreach ($directory in $directories) {
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
}

@'
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
'@ | Set-Content -Encoding UTF8 ".\src\cipw_engine.py"

@'
import pytest

from src.cipw_engine import (
    allocate_stoichiometric_reaction,
    calculate_cipw_norm,
    molecular_proportions,
)


@pytest.fixture
def composition():
    return {
        "SiO2": 50.0,
        "TiO2": 1.0,
        "Al2O3": 15.0,
        "Fe2O3": 2.0,
        "FeO": 8.0,
        "MnO": 0.1,
        "MgO": 7.0,
        "CaO": 10.0,
        "Na2O": 3.0,
        "K2O": 2.0,
        "P2O5": 1.0,
    }


def test_molecular_proportions(composition):
    result = molecular_proportions(composition)
    assert result["SiO2"] == pytest.approx(50 / 60.0843)


def test_measured_iron_retained_separately(composition):
    result = molecular_proportions(composition)
    assert result["FeO"] == pytest.approx(8 / 71.8440)
    assert result["Fe2O3"] == pytest.approx(2 / 159.6882)


def test_reaction_allocation():
    available = {"CaO": 3.0, "P2O5": 1.0}
    coefficients = {"CaO": 3.0, "P2O5": 1.0}

    extent, remaining = allocate_stoichiometric_reaction(
        available, coefficients
    )

    assert extent == pytest.approx(1.0)
    assert remaining["CaO"] == pytest.approx(0.0)
    assert remaining["P2O5"] == pytest.approx(0.0)


def test_reaction_limiting_reactant():
    available = {"CaO": 3.0, "P2O5": 0.5}
    coefficients = {"CaO": 3.0, "P2O5": 1.0}

    extent, remaining = allocate_stoichiometric_reaction(
        available, coefficients
    )

    assert extent == pytest.approx(0.5)
    assert remaining["CaO"] == pytest.approx(1.5)


def test_reaction_rejects_missing_reactant():
    with pytest.raises(ValueError):
        allocate_stoichiometric_reaction(
            {"CaO": 1.0},
            {"P2O5": 1.0},
        )


def test_no_false_normative_output(composition):
    result = calculate_cipw_norm(composition)

    assert result.status == "FOUNDATION_ONLY"
    assert result.normative_minerals == {}
    assert result.warnings
'@ | Set-Content -Encoding UTF8 ".\tests\test_cipw_engine.py"

python -m py_compile .\src\cipw_engine.py .\tests\test_cipw_engine.py

if ($LASTEXITCODE -ne 0) {
    throw "Python compilation failed."
}

python -m pytest .\tests\test_cipw_engine.py -v

if ($LASTEXITCODE -ne 0) {
    throw "CIPW engine foundation tests failed."
}

Write-Host "CIPW engine foundation installed and tested." -ForegroundColor Green
