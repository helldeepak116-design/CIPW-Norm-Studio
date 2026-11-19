"""Central calculation orchestrator for CIPW Norm Studio.

Coordinates:
    1. Major oxide wt.% conversion
    2. Optional-component measurement validation and conversion
    3. Kelsey (1965) provisional allocation, Rules 1-21
    4. Kelsey silica-deficiency redistribution, Rules 22-28
    5. Component mass-balance verification
    6. Normative mineral mass and normalized wt.% calculation

The scientific allocation rules remain in their existing modules.
This module coordinates them and retains their intermediate results.

Volatile-free normalization:
    When volatile_free=True, major oxides are normalized to 100 wt.%.
    Optional-component molecular proportions are multiplied by the
    same normalization factor to maintain a consistent analytical basis.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping

from src.oxide_conversion import (
    convert_oxides_to_molecular_proportions,
)

from src.optional_components import (
    OptionalComponentConversion,
    convert_optional_components,
)

from src.kelsey_provisional import (
    ProvisionalResult,
    calculate_kelsey_provisional,
)

from src.kelsey_silica_deficiency import (
    RedistributionResult,
    redistribute_silica,
)

from src.mass_balance import (
    MassBalanceResult,
    check_mass_balance,
)

from src.mineral_formula_weights import (
    calculate_mineral_masses,
)


MAJOR_OXIDES = (
    "SiO2",
    "TiO2",
    "Al2O3",
    "Fe2O3",
    "FeO",
    "MnO",
    "MgO",
    "CaO",
    "Na2O",
    "K2O",
    "P2O5",
)


@dataclass(frozen=True)
class NormCalculationResult:
    """Complete result and audit trail for one CIPW calculation."""

    method: str

    major_oxide_conversion: dict[str, Any]
    major_oxide_moles: dict[str, float]

    optional_component_conversion: OptionalComponentConversion
    optional_component_moles: dict[str, float]

    provisional_result: ProvisionalResult
    redistribution_result: RedistributionResult

    final_minerals: dict[str, float]
    mineral_masses: dict[str, float]
    total_normative_mass: float
    mineral_wt_percent: dict[str, float]

    mass_balance: MassBalanceResult

    sulfur_basis: str
    carbonate_mode: str
    volatile_free: bool

    optional_normalization_factor: float

    conditional: bool
    status: str
    warnings: tuple[str, ...]


class NormCalculationError(ValueError):
    """Raised when a complete normative calculation cannot proceed."""


class OptionalComponentsIncompleteError(NormCalculationError):
    """Raised when optional-component measurements are incomplete."""


def _extract_major_molecular_proportions(
    conversion: Mapping[str, Any],
) -> dict[str, float]:
    """Extract major oxide molecular proportions from conversion output."""

    if "oxide_table" not in conversion:
        raise NormCalculationError(
            "Major oxide conversion did not return an oxide_table."
        )

    table = conversion["oxide_table"]

    try:
        available_oxides = set(table.index)
    except AttributeError as exc:
        raise NormCalculationError(
            "The oxide_table must be a pandas DataFrame."
        ) from exc

    missing = set(MAJOR_OXIDES) - available_oxides

    if missing:
        raise NormCalculationError(
            f"Major oxide conversion is missing: {sorted(missing)}"
        )

    molecular_moles: dict[str, float] = {}

    for oxide in MAJOR_OXIDES:
        try:
            value = float(
                table.loc[oxide, "molecular_proportion"]
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise NormCalculationError(
                f"Could not extract molecular proportion for {oxide}."
            ) from exc

        if not math.isfinite(value) or value < 0:
            raise NormCalculationError(
                f"Invalid molecular proportion for {oxide}: {value}"
            )

        molecular_moles[oxide] = value

    return molecular_moles


def _validate_calculation_options(
    *,
    sulfur_basis: str,
    carbonate_mode: str,
    numerical_tolerance: float,
    mass_balance_tolerance: float,
) -> None:
    """Validate orchestration-level calculation options."""

    if sulfur_basis not in {"none", "S", "SO3"}:
        raise NormCalculationError(
            "sulfur_basis must be 'none', 'S', or 'SO3'."
        )

    if carbonate_mode not in {"none", "cancrinite", "calcite"}:
        raise NormCalculationError(
            "carbonate_mode must be 'none', 'cancrinite', or 'calcite'."
        )

    for name, value in (
        ("numerical_tolerance", numerical_tolerance),
        ("mass_balance_tolerance", mass_balance_tolerance),
    ):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be numeric.")

        if value <= 0:
            raise ValueError(f"{name} must be positive.")

        if not math.isfinite(float(value)):
            raise ValueError(f"{name} must be finite.")


def calculate_cipw_norm(
    major_oxide_wt_percent: Mapping[str, float],
    optional_measurements: Mapping[str, Any],
    *,
    sulfur_basis: str = "none",
    carbonate_mode: str = "none",
    volatile_free: bool = False,
    assume_unmeasured_zero: bool = False,
    numerical_tolerance: float = 1e-10,
    mass_balance_tolerance: float = 1e-8,
) -> NormCalculationResult:
    """Calculate a complete classical Kelsey (1965) CIPW norm.

    Parameters
    ----------
    major_oxide_wt_percent:
        Mapping of all eleven major oxides to analytical wt.%.

    optional_measurements:
        Mapping of all ten optional components. Each entry must specify
        measured, measured_zero, or not_measured status.

    sulfur_basis:
        "none", "S", or "SO3".

    carbonate_mode:
        "none", "cancrinite", or "calcite".

    volatile_free:
        If True, normalize the eleven major oxides to 100 wt.% before
        converting them to molecular proportions.

        The same normalization factor is applied to optional-component
        molecular proportions to maintain a consistent analytical basis.

    assume_unmeasured_zero:
        If True, explicitly permit an exploratory calculation with
        unmeasured optional components assumed absent. Such a result
        is marked conditional.

    numerical_tolerance:
        Tolerance passed to the Kelsey allocation and redistribution
        engines.

    mass_balance_tolerance:
        Independent component-conservation tolerance.

    Returns
    -------
    NormCalculationResult
        Complete calculation, intermediate results, mineral masses,
        normalized mineral wt.% and mass-balance audit.

    Raises
    ------
    OptionalComponentsIncompleteError
        If any optional component is unmeasured and the explicit
        zero-assumption option is disabled.
    """

    # ---------------------------------------------------------
    # 0. Validate calculation options and input mappings
    # ---------------------------------------------------------

    _validate_calculation_options(
        sulfur_basis=sulfur_basis,
        carbonate_mode=carbonate_mode,
        numerical_tolerance=numerical_tolerance,
        mass_balance_tolerance=mass_balance_tolerance,
    )

    if not isinstance(volatile_free, bool):
        raise TypeError("volatile_free must be boolean.")

    if not isinstance(assume_unmeasured_zero, bool):
        raise TypeError("assume_unmeasured_zero must be boolean.")

    if not isinstance(major_oxide_wt_percent, Mapping):
        raise TypeError("major_oxide_wt_percent must be a mapping.")

    if not isinstance(optional_measurements, Mapping):
        raise TypeError("optional_measurements must be a mapping.")

    # ---------------------------------------------------------
    # 1. Major oxide conversion: wt.% -> molecular proportions
    # ---------------------------------------------------------

    major_conversion = convert_oxides_to_molecular_proportions(
        dict(major_oxide_wt_percent),
        volatile_free=volatile_free,
    )

    major_moles = _extract_major_molecular_proportions(
        major_conversion
    )

    # ---------------------------------------------------------
    # 1A. Determine the analytical normalization factor
    # ---------------------------------------------------------

    original_analytical_total = float(
        major_conversion["original_analytical_total"]
    )

    if (
        not math.isfinite(original_analytical_total)
        or original_analytical_total <= 0
    ):
        raise NormCalculationError(
            "Original major-oxide analytical total must be "
            "finite and greater than zero."
        )

    if volatile_free:
        optional_normalization_factor = (
            100.0 / original_analytical_total
        )
    else:
        optional_normalization_factor = 1.0

    # ---------------------------------------------------------
    # 2. Optional component conversion and completeness check
    # ---------------------------------------------------------

    optional_conversion = convert_optional_components(
        optional_measurements,
        assume_unmeasured_zero=assume_unmeasured_zero,
    )

    if not optional_conversion.calculation_ready:
        raise OptionalComponentsIncompleteError(
            "Cannot calculate a complete CIPW norm because optional "
            "components are unmeasured: "
            + ", ".join(optional_conversion.unmeasured_components)
            + ". Explicitly enable assume_unmeasured_zero=True only "
            "for an exploratory conditional calculation."
        )

    optional_moles: dict[str, float] = {}

    for component, value in (
        optional_conversion.molecular_proportions.items()
    ):
        if value is None:
            raise NormCalculationError(
                f"{component} has no molecular proportion despite "
                "the calculation being marked ready."
            )

        raw_molecular_proportion = float(value)

        if (
            not math.isfinite(raw_molecular_proportion)
            or raw_molecular_proportion < 0
        ):
            raise NormCalculationError(
                f"Invalid molecular proportion for {component}."
            )

        # Apply the same analytical normalization factor used
        # for the major oxides.
        optional_moles[component] = (
            raw_molecular_proportion
            * optional_normalization_factor
        )

    # ---------------------------------------------------------
    # 3. Kelsey Rules 1-21: provisional allocation
    # ---------------------------------------------------------

    provisional = calculate_kelsey_provisional(
        major_moles,
        optional_moles,
        sulfur_basis=sulfur_basis,
        carbonate_mode=carbonate_mode,
        tolerance=numerical_tolerance,
    )

    # ---------------------------------------------------------
    # 4. Kelsey Rules 22-28: silica-deficiency redistribution
    #
    # This returns the COMPLETE final mineral dictionary.
    # Do not add it to provisional.minerals.
    # ---------------------------------------------------------

    redistribution = redistribute_silica(
        provisional.minerals,
        provisional.silica_deficiency,
        tolerance=numerical_tolerance,
    )

    final_minerals = {
        name: float(amount)
        for name, amount in redistribution.minerals.items()
        if float(amount) > numerical_tolerance
    }

    # ---------------------------------------------------------
    # 5. Independent component mass-balance verification
    # ---------------------------------------------------------

    balance = check_mass_balance(
        major_moles,
        optional_moles,
        provisional,
        redistribution,
        sulfur_basis=sulfur_basis,
        tolerance=mass_balance_tolerance,
    )

    # ---------------------------------------------------------
    # 6. Mineral masses and normalized normative wt.%
    # ---------------------------------------------------------

    mineral_masses = calculate_mineral_masses(
        final_minerals,
        mg_fraction=provisional.mg_fraction,
        fe_fraction=provisional.fe_fraction,
        apatite_fluorine_amount=provisional.apatite_fluorine_amount,
    )

    total_normative_mass = sum(mineral_masses.values())

    if total_normative_mass > 0:
        mineral_wt_percent = {
            symbol: mass / total_normative_mass * 100.0
            for symbol, mass in mineral_masses.items()
        }
    else:
        mineral_wt_percent = {}

    # ---------------------------------------------------------
    # 7. Overall status and warnings
    # ---------------------------------------------------------

    warnings: list[str] = list(optional_conversion.warnings)
    warnings.extend(balance.messages)

    if volatile_free:
        warnings.append(
            "Volatile-free normalization applied. "
            f"Normalization factor: "
            f"{optional_normalization_factor:.12g}. "
            "The same factor was applied to optional-component "
            "molecular proportions."
        )

    if redistribution.final_deficiency > numerical_tolerance:
        warnings.append(
            "Silica deficiency remains unresolved after Rules 22-28: "
            f"{redistribution.final_deficiency:.12g} molecular proportions."
        )

    if total_normative_mass <= numerical_tolerance:
        warnings.append(
            "No positive normative mineral mass was calculated."
        )

    if not balance.balanced:
        status = "MASS_BALANCE_FAILED"

    elif redistribution.final_deficiency > numerical_tolerance:
        status = "UNRESOLVED_SILICA_DEFICIENCY"

    elif optional_conversion.conditional:
        status = "CONDITIONAL"

    else:
        status = "COMPLETED"

    # ---------------------------------------------------------
    # 8. Return complete calculation and audit trail
    # ---------------------------------------------------------

    return NormCalculationResult(
        method="Classical CIPW Norm - Kelsey (1965)",

        major_oxide_conversion=major_conversion,
        major_oxide_moles=major_moles,

        optional_component_conversion=optional_conversion,
        optional_component_moles=optional_moles,

        provisional_result=provisional,
        redistribution_result=redistribution,

        final_minerals=final_minerals,
        mineral_masses=mineral_masses,
        total_normative_mass=total_normative_mass,
        mineral_wt_percent=mineral_wt_percent,

        mass_balance=balance,

        sulfur_basis=sulfur_basis,
        carbonate_mode=carbonate_mode,
        volatile_free=volatile_free,
        optional_normalization_factor=optional_normalization_factor,

        conditional=optional_conversion.conditional,
        status=status,
        warnings=tuple(warnings),
    )
