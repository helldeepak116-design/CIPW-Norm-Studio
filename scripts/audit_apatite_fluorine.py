
"""Independent audit of Kelsey (1965) apatite-fluorine allocation.

Tests:
1. Fluorine below the Rule 5 apatite capacity.
2. Fluorine above the Rule 5 apatite capacity, requiring Rule 6 fluorite.

The expected allocations and apatite mass are calculated independently
from the application result.
"""

from __future__ import annotations

import math
import sys

from config.oxide_config import OXIDE_CONFIG
from src.mineral_formula_weights import ATOMIC_WEIGHTS
from src.norm_calculation import calculate_cipw_norm


ABS_TOL = 1e-9
MASS_BALANCE_TOL = 1e-8

MAJOR_OXIDES = {
    "SiO2": 89.0,
    "TiO2": 0.0,
    "Al2O3": 0.0,
    "Fe2O3": 0.0,
    "FeO": 0.0,
    "MnO": 0.0,
    "MgO": 0.0,
    "CaO": 10.0,
    "Na2O": 0.0,
    "K2O": 0.0,
    "P2O5": 1.0,
}

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


def close(actual: float, expected: float, label: str) -> None:
    """Raise an informative error if two values do not agree."""

    if not math.isclose(
        float(actual),
        float(expected),
        rel_tol=0.0,
        abs_tol=ABS_TOL,
    ):
        raise AssertionError(
            f"{label} FAILED: actual={actual:.12g}, "
            f"expected={expected:.12g}, "
            f"difference={actual - expected:.12g}"
        )

    print(f"PASS  {label}: {actual:.12g}")


def optional_measurements(fluorine_wt_percent: float) -> dict:
    """Create explicit records for all ten optional components."""

    measurements = {
        component: {
            "status": "measured_zero",
            "value_wt_percent": 0.0,
        }
        for component in OPTIONAL_COMPONENTS
    }

    measurements["F"] = {
        "status": "measured",
        "value_wt_percent": fluorine_wt_percent,
    }

    return measurements


def run_case(fluorine_wt_percent: float) -> None:
    """Run one independent apatite-fluorine audit case."""

    print("\n" + "=" * 72)
    print(f"APATITE-FLUORINE AUDIT: F = {fluorine_wt_percent:.4f} wt.%")
    print("=" * 72)

    result = calculate_cipw_norm(
        MAJOR_OXIDES,
        optional_measurements(fluorine_wt_percent),
        sulfur_basis="none",
        carbonate_mode="none",
        volatile_free=False,
        assume_unmeasured_zero=False,
        mass_balance_tolerance=MASS_BALANCE_TOL,
    )

    # ---------------------------------------------------------
    # A. Independent molecular-proportion calculations
    # ---------------------------------------------------------

    p2o5_molecular_weight = float(
        OXIDE_CONFIG["P2O5"]["molecular_weight"]
    )
    cao_molecular_weight = float(
        OXIDE_CONFIG["CaO"]["molecular_weight"]
    )
    fluorine_atomic_weight = float(ATOMIC_WEIGHTS["F"])
    calcium_atomic_weight = float(ATOMIC_WEIGHTS["Ca"])

    expected_ap = MAJOR_OXIDES["P2O5"] / p2o5_molecular_weight

    expected_total_f = (
        fluorine_wt_percent / fluorine_atomic_weight
    )

    # Kelsey (1965), Rule 5:
    # Maximum F allocation = 1/3 mole F per mole P2O5.
    expected_f_in_apatite = min(
        expected_total_f,
        expected_ap / 3.0,
    )

    # Kelsey (1965), Rule 6:
    # Remaining F forms fluorite, CaF2, at F/2.
    expected_remaining_f = max(
        0.0,
        expected_total_f - expected_f_in_apatite,
    )
    expected_fluorite = expected_remaining_f / 2.0

    # ---------------------------------------------------------
    # B. Compare normative mineral allocations
    # ---------------------------------------------------------

    actual_ap = float(result.final_minerals.get("ap", 0.0))
    actual_f_in_apatite = float(
        result.provisional_result.apatite_fluorine_amount
    )
    actual_fluorite = float(result.final_minerals.get("fr", 0.0))

    close(actual_ap, expected_ap, "Apatite molecular amount")
    close(
        actual_f_in_apatite,
        expected_f_in_apatite,
        "Fluorine allocated to apatite",
    )
    close(
        actual_fluorite,
        expected_fluorite,
        "Fluorite molecular amount",
    )

    # Check that the optional-component conversion uses the
    # independently calculated elemental-F molecular amount.
    close(
        result.optional_component_moles["F"],
        expected_total_f,
        "Elemental fluorine molecular proportion",
    )

    # ---------------------------------------------------------
    # C. Independently calculate Kelsey apatite mass
    # ---------------------------------------------------------

    if expected_ap <= 0:
        raise AssertionError("Expected apatite amount must be positive.")

    x = expected_f_in_apatite / expected_ap

    # Kelsey original convention:
    # 3CaO.P2O5.(1/3)CaF
    #
    # Generalized mass per mole P2O5:
    # (10/3)CaO + P2O5 + x(Ca + F - CaO)
    #
    # The CaO molecular weight is taken from the canonical oxide
    # configuration; the elemental Ca and F weights are explicit.
    independent_apatite_formula_mass = (
        (10.0 / 3.0) * cao_molecular_weight
        + p2o5_molecular_weight
        + x * (
            calcium_atomic_weight
            + fluorine_atomic_weight
            - cao_molecular_weight
        )
    )

    expected_apatite_mass = (
        expected_ap * independent_apatite_formula_mass
    )

    actual_apatite_mass = float(
        result.mineral_masses.get("ap", 0.0)
    )

    close(
        actual_apatite_mass,
        expected_apatite_mass,
        "Independent apatite mineral mass",
    )

    print(
        "Independent apatite formula mass: "
        f"{independent_apatite_formula_mass:.12f}"
    )
    print(f"Actual apatite mass:              {actual_apatite_mass:.12f}")
    print(f"Expected apatite mass:            {expected_apatite_mass:.12f}")

    # ---------------------------------------------------------
    # D. Verify Rule 5 fluorine capacity
    # ---------------------------------------------------------

    if actual_f_in_apatite > actual_ap / 3.0 + ABS_TOL:
        raise AssertionError(
            "Rule 5 fluorine allocation exceeds ap/3."
        )

    print("PASS  Rule 5 apatite fluorine capacity")

    # ---------------------------------------------------------
    # E. Verify component mass balance
    # ---------------------------------------------------------

    balance = result.mass_balance

    print(f"Mass balance status: {balance.balanced}")
    print(
        "Maximum non-silica component error: "
        f"{balance.max_non_silica_error:.12g}"
    )
    print(
        "Silica balance error: "
        f"{balance.silica_error:.12g}"
    )
    print(
        "Component differences: "
        f"{balance.component_differences}"
    )

    if not balance.balanced:
        raise AssertionError(
            "Engine component mass balance is not balanced."
        )

    if balance.max_non_silica_error > MASS_BALANCE_TOL:
        raise AssertionError(
            "Non-silica component error exceeds tolerance."
        )

    print("PASS  Engine component mass balance")

    print("\nCASE RESULT: PASS")


def main() -> int:
    """Execute both independent fluorine-allocation cases."""

    cases = (0.01, 0.10)

    try:
        for fluorine in cases:
            run_case(fluorine)

    except Exception as exc:
        print("\n" + "!" * 72)
        print("APATITE AUDIT FAILED")
        print(f"{type(exc).__name__}: {exc}")
        print("!" * 72)
        return 1

    print("\n" + "=" * 72)
    print("ALL INDEPENDENT APATITE-FLUORINE AUDITS PASSED")
    print("=" * 72)

    return 0


if __name__ == "__main__":
    sys.exit(main())
