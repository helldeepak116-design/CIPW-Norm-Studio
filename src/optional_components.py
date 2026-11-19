
"""Optional-component measurement validation and conversion.

All reported concentrations are interpreted as wt.% on the same
analytical basis as the major oxides.

Elemental F, Cl and S are converted using atomic weights.
Oxide components are converted using their formula weights.

Unmeasured components remain unknown unless the caller explicitly
opts into an exploratory zero-assumption calculation.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping

from src.mineral_formula_weights import ATOMIC_WEIGHTS


OPTIONAL_COMPONENTS = (
    "NiO",
    "BaO",
    "SrO",
    "ZrO2",
    "F",
    "Cl",
    "SO3",
    "S",
    "CO2",
    "Cr2O3",
)

VALID_STATUSES = {
    "measured",
    "measured_zero",
    "not_measured",
}


def _formula_weight(*parts: tuple[str, float]) -> float:
    """Calculate a formula weight from the canonical atomic weights."""
    total = 0.0

    for element, count in parts:
        if element not in ATOMIC_WEIGHTS:
            raise ValueError(
                f"Atomic weight for {element!r} is not registered."
            )

        total += ATOMIC_WEIGHTS[element] * count

    if not math.isfinite(total) or total <= 0:
        raise ValueError("Invalid optional-component formula weight.")

    return total


OPTIONAL_COMPONENT_WEIGHTS = {
    "NiO": _formula_weight(("Ni", 1), ("O", 1)),
    "BaO": _formula_weight(("Ba", 1), ("O", 1)),
    "SrO": _formula_weight(("Sr", 1), ("O", 1)),
    "ZrO2": _formula_weight(("Zr", 1), ("O", 2)),
    "F": ATOMIC_WEIGHTS["F"],
    "Cl": ATOMIC_WEIGHTS["Cl"],
    "SO3": _formula_weight(("S", 1), ("O", 3)),
    "S": ATOMIC_WEIGHTS["S"],
    "CO2": _formula_weight(("C", 1), ("O", 2)),
    "Cr2O3": _formula_weight(("Cr", 2), ("O", 3)),
}


@dataclass(frozen=True)
class OptionalComponentMeasurement:
    """One optional component's analytical measurement."""

    status: str
    value_wt_percent: float | None


@dataclass(frozen=True)
class OptionalComponentConversion:
    """Validated optional-component conversion result."""

    molecular_proportions: dict[str, float | None]
    measurements: dict[str, OptionalComponentMeasurement]
    unmeasured_components: tuple[str, ...]
    calculation_ready: bool
    conditional: bool
    warnings: tuple[str, ...]


def _parse_measurement(
    component: str,
    raw: OptionalComponentMeasurement | Mapping,
) -> OptionalComponentMeasurement:
    """Validate and normalize one measurement record."""

    if isinstance(raw, OptionalComponentMeasurement):
        status = raw.status
        value = raw.value_wt_percent

    elif isinstance(raw, Mapping):
        status = raw.get("status")
        value = raw.get("value_wt_percent")

    else:
        raise TypeError(
            f"{component}: measurement must be a mapping or "
            "OptionalComponentMeasurement."
        )

    if status not in VALID_STATUSES:
        raise ValueError(
            f"{component}: status must be one of "
            f"{sorted(VALID_STATUSES)}."
        )

    if status == "not_measured":
        if value is not None:
            raise ValueError(
                f"{component}: not_measured must have "
                "value_wt_percent=None."
            )

        return OptionalComponentMeasurement(
            status="not_measured",
            value_wt_percent=None,
        )

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(
            f"{component}: measured concentration must be numeric."
        )

    value = float(value)

    if not math.isfinite(value):
        raise ValueError(
            f"{component}: concentration must be finite."
        )

    if value < 0:
        raise ValueError(
            f"{component}: concentration cannot be negative."
        )

    if status == "measured_zero" and value != 0:
        raise ValueError(
            f"{component}: measured_zero requires exactly 0 wt.%."
        )

    if status == "measured" and value <= 0:
        raise ValueError(
            f"{component}: measured requires a value greater than "
            "zero. Use measured_zero for an analysed zero."
        )

    return OptionalComponentMeasurement(
        status=status,
        value_wt_percent=value,
    )


def convert_optional_components(
    measurements: Mapping[str, OptionalComponentMeasurement | Mapping],
    *,
    assume_unmeasured_zero: bool = False,
) -> OptionalComponentConversion:
    """Validate and convert all ten optional components.

    Parameters
    ----------
    measurements:
        Mapping containing every key in OPTIONAL_COMPONENTS.

        Each value must contain:
            status: measured | measured_zero | not_measured
            value_wt_percent: numeric value or None

    assume_unmeasured_zero:
        False (default):
            Unmeasured components remain None and the result is not
            ready for Kelsey calculation.

        True:
            Unmeasured components are assigned zero only for the
            explicitly requested exploratory calculation. The result
            is marked conditional and includes warnings.

    Returns
    -------
    OptionalComponentConversion
        Validated measurements, molecular proportions and completeness
        information.
    """

    if not isinstance(measurements, Mapping):
        raise TypeError("measurements must be a mapping.")

    if not isinstance(assume_unmeasured_zero, bool):
        raise TypeError("assume_unmeasured_zero must be boolean.")

    supplied = set(measurements)
    expected = set(OPTIONAL_COMPONENTS)

    missing_keys = sorted(expected - supplied)
    unknown_keys = sorted(supplied - expected)

    if missing_keys:
        raise ValueError(
            f"Missing optional-component records: {missing_keys}"
        )

    if unknown_keys:
        raise ValueError(
            f"Unsupported optional components: {unknown_keys}"
        )

    normalized: dict[str, OptionalComponentMeasurement] = {}
    molecular_proportions: dict[str, float | None] = {}
    unmeasured: list[str] = []
    warnings: list[str] = []

    for component in OPTIONAL_COMPONENTS:
        record = _parse_measurement(
            component,
            measurements[component],
        )
        normalized[component] = record

        if record.status == "not_measured":
            unmeasured.append(component)

            if assume_unmeasured_zero:
                molecular_proportions[component] = 0.0
            else:
                molecular_proportions[component] = None

            continue

        assert record.value_wt_percent is not None

        molecular_proportions[component] = (
            record.value_wt_percent
            / OPTIONAL_COMPONENT_WEIGHTS[component]
        )

    if unmeasured:
        if assume_unmeasured_zero:
            warnings.append(
                "CONDITIONAL RESULT: unmeasured optional components "
                "were assumed absent (0 molecular proportion): "
                + ", ".join(unmeasured)
                + ". This is not equivalent to measured zero."
            )
        else:
            warnings.append(
                "Calculation blocked: optional components have not "
                "been measured: "
                + ", ".join(unmeasured)
                + ". Supply measurements or explicitly request an "
                "exploratory zero-assumption calculation."
            )

    conditional = bool(unmeasured and assume_unmeasured_zero)
    calculation_ready = not unmeasured or assume_unmeasured_zero

    return OptionalComponentConversion(
        molecular_proportions=molecular_proportions,
        measurements=normalized,
        unmeasured_components=tuple(unmeasured),
        calculation_ready=calculation_ready,
        conditional=conditional,
        warnings=tuple(warnings),
    )
