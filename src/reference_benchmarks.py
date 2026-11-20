
"""Published reference benchmarks for CIPW Norm Studio.

Reference values are kept separate from the calculation engine.
The Bostonite values are transcribed from Kelsey (1965), Table III.

Comparison uses absolute differences in molecular proportions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Any


BOSTONITE_KELSEY_1965 = {
    "name": "Bostonite, Maros, Celebes",
    "reference": (
        "Kelsey, C.H. (1965), Table III; "
        "Washington (1917), p. 274, Analysis No. 37"
    ),
    "tolerance": 0.001,
    "oxide_composition": {
        "SiO2": 61.15,
        "TiO2": 0.21,
        "Al2O3": 22.07,
        "Fe2O3": 1.05,
        "FeO": 1.02,
        "MnO": 0.0,
        "MgO": 0.40,
        "CaO": 0.75,
        "Na2O": 5.86,
        "K2O": 7.01,
        "P2O5": 0.0,
    },
    "published_molecular_amounts": {
        "c": 0.034,
        "ol": 0.008,
        "or": 0.074,
        "mt": 0.006,
        "ab": 0.087,
        "il": 0.003,
        "an": 0.014,
        "ne": 0.008,
    },
    "assumptions": (
        "MnO and P2O5 were unreported and assumed zero. "
        "Optional components were unmeasured and conditionally "
        "assumed absent."
    ),
}


@dataclass(frozen=True)
class BenchmarkRow:
    mineral: str
    published: float
    calculated: float
    absolute_difference: float
    tolerance: float
    passed: bool


def matches_bostonite_composition(
    oxide_input: Mapping[str, Any],
    *,
    composition_tolerance: float = 1e-6,
) -> bool:
    """Return True only when all benchmark major oxides match."""

    if not isinstance(oxide_input, Mapping):
        return False

    expected = BOSTONITE_KELSEY_1965["oxide_composition"]

    for oxide, expected_value in expected.items():
        try:
            actual_value = float(oxide_input[oxide])
        except (KeyError, TypeError, ValueError, OverflowError):
            return False

        if abs(actual_value - expected_value) > composition_tolerance:
            return False

    return True


def compare_bostonite_reference(
    calculated_minerals: Mapping[str, Any],
    oxide_input: Mapping[str, Any],
) -> list[BenchmarkRow] | None:
    """Compare Studio molecular amounts with Kelsey Table III.

    Returns None when the input composition does not match the
    Bostonite benchmark. Missing calculated minerals are treated
    as zero because the benchmark comparison includes only the
    eight published minerals.
    """

    if not matches_bostonite_composition(oxide_input):
        return None

    if not isinstance(calculated_minerals, Mapping):
        raise TypeError("calculated_minerals must be a mapping")

    reference = BOSTONITE_KELSEY_1965
    tolerance = float(reference["tolerance"])

    rows = []

    for mineral, published_value in (
        reference["published_molecular_amounts"].items()
    ):
        try:
            calculated_value = float(
                calculated_minerals.get(mineral, 0.0)
            )
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(
                f"Invalid calculated molecular amount for {mineral}"
            ) from exc

        published_value = float(published_value)
        difference = abs(calculated_value - published_value)

        rows.append(
            BenchmarkRow(
                mineral=mineral,
                published=published_value,
                calculated=calculated_value,
                absolute_difference=difference,
                tolerance=tolerance,
                passed=difference <= tolerance,
            )
        )

    return rows
