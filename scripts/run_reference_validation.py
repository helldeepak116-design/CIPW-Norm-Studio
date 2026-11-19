
"""Run the published Idaho Batholith granite benchmark.

Reference:
Mattioli, G. and Zachry, D. (2008).
GEOL 2313 - Homework Assignment 3.
University of Arkansas.

This is a diagnostic comparison because the published exercise
uses Hyndman's procedure rather than explicitly using Kelsey (1965).

The script does not declare scientific equivalence automatically.
It reports the differences for expert review.
"""

from __future__ import annotations

import sys
from pathlib import Path


# ---------------------------------------------------------
# Make the project root available for imports
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.norm_calculation import calculate_cipw_norm
from src.optional_components import OPTIONAL_COMPONENTS


# ---------------------------------------------------------
# Published Idaho Batholith granite composition
# Sample 134.15
# ---------------------------------------------------------

IDAHO_GRANITE_OXIDES = {
    "SiO2": 70.66,
    "TiO2": 0.24,
    "Al2O3": 15.99,
    "Fe2O3": 0.76,
    "FeO": 0.70,
    "MnO": 0.03,
    "MgO": 0.47,
    "CaO": 1.81,
    "Na2O": 4.76,
    "K2O": 3.55,
    "P2O5": 0.07,
}


# Published normative weight percentages.
# These sum to 99.02 wt.% in the original reference.
PUBLISHED_NORM_WT_PERCENT = {
    "q": 24.86,
    "c": 1.19,
    "or": 20.99,
    "ab": 40.28,
    "an": 8.51,
    "hy": 1.48,
    "mt": 1.09,
    "il": 0.46,
    "ap": 0.16,
}


PUBLISHED_NORM_TOTAL = 99.02


# ---------------------------------------------------------
# Optional components
#
# The published example does not provide measurements
# for these ten optional components.
#
# For this diagnostic run only, explicit measured-zero
# records are used. This is an assumption, not a claim
# that the original sample was analysed for these values.
# ---------------------------------------------------------

OPTIONAL_MEASUREMENTS = {
    component: {
        "status": "measured_zero",
        "value_wt_percent": 0.0,
    }
    for component in OPTIONAL_COMPONENTS
}


def print_section(title: str) -> None:
    print()
    print("=" * 76)
    print(title)
    print("=" * 76)


def run_validation() -> None:

    # -----------------------------------------------------
    # 1. Input information
    # -----------------------------------------------------

    analytical_total = sum(IDAHO_GRANITE_OXIDES.values())

    print_section("CIPW NORM STUDIO - SCIENTIFIC REFERENCE VALIDATION")

    print("Reference: Idaho Batholith granite, sample 134.15")
    print("Published source: University of Arkansas, GEOL 2313")
    print("Reference method: Hyndman procedure")
    print("Engine method: Classical Kelsey (1965)")
    print("Comparison type: Diagnostic, not exact equivalence")

    print(f"\nMajor oxide analytical total: {analytical_total:.4f} wt.%")

    # -----------------------------------------------------
    # 2. Execute the CIPW Norm calculation
    # -----------------------------------------------------

    result = calculate_cipw_norm(
        major_oxide_wt_percent=IDAHO_GRANITE_OXIDES,
        optional_measurements=OPTIONAL_MEASUREMENTS,
        sulfur_basis="none",
        carbonate_mode="none",
        volatile_free=False,
    )

    print_section("CALCULATION STATUS")

    print(f"Status: {result.status}")
    print(f"Method: {result.method}")
    print(f"Mass balance status: {result.mass_balance.status}")
    print(f"Mass balance passed: {result.mass_balance.balanced}")

    print(
        "Maximum non-silica component error: "
        f"{result.mass_balance.max_non_silica_error:.12g}"
    )

    print(
        "Silica error: "
        f"{result.mass_balance.silica_error:.12g}"
    )

    print(
        "Silica deficiency remaining: "
        f"{result.redistribution_result.final_deficiency:.12g}"
    )

    # -----------------------------------------------------
    # 3. Molecular proportions
    # -----------------------------------------------------

    print_section("MAJOR OXIDE MOLECULAR PROPORTIONS")

    print(
        f"{'Oxide':<12}"
        f"{'Input wt.%':>14}"
        f"{'Molecular proportion':>25}"
    )

    print("-" * 53)

    for oxide, wt_percent in IDAHO_GRANITE_OXIDES.items():

        molecular_proportion = result.major_oxide_moles[oxide]

        print(
            f"{oxide:<12}"
            f"{wt_percent:>14.4f}"
            f"{molecular_proportion:>25.8f}"
        )

    # -----------------------------------------------------
    # 4. Normative mineral comparison
    # -----------------------------------------------------

    print_section("PUBLISHED NORM VS CIPW NORM STUDIO")

    print(
        f"{'Mineral':<12}"
        f"{'Published wt.%':>17}"
        f"{'Studio wt.%':>17}"
        f"{'Difference':>17}"
    )

    print("-" * 63)

    all_symbols = sorted(
        set(PUBLISHED_NORM_WT_PERCENT)
        | set(result.mineral_wt_percent)
    )

    for symbol in all_symbols:

        published = PUBLISHED_NORM_WT_PERCENT.get(
            symbol,
            0.0,
        )

        calculated = result.mineral_wt_percent.get(
            symbol,
            0.0,
        )

        # Normalize the published reference to 100% for
        # comparison with the Studio's normalized mineral wt.%.
        published_normalized = (
            published / PUBLISHED_NORM_TOTAL * 100.0
        )

        difference = calculated - published_normalized

        print(
            f"{symbol:<12}"
            f"{published_normalized:>17.4f}"
            f"{calculated:>17.4f}"
            f"{difference:>17.4f}"
        )

    # -----------------------------------------------------
    # 5. Total normative mass
    # -----------------------------------------------------

    print_section("NORMATIVE MINERAL MASS SUMMARY")

    print(
        f"Total normative mineral mass: "
        f"{result.total_normative_mass:.8f}"
    )

    print(
        f"Sum of normalized mineral percentages: "
        f"{sum(result.mineral_wt_percent.values()):.8f}"
    )

    # -----------------------------------------------------
    # 6. Provisional and final mineral amounts
    # -----------------------------------------------------

    print_section("PROVISIONAL MINERAL MOLECULAR AMOUNTS")

    for symbol, amount in sorted(
        result.provisional_result.minerals.items()
    ):
        if abs(amount) > 1e-12:
            print(f"{symbol:<12} {amount:.10f}")

    print_section("FINAL MINERAL MOLECULAR AMOUNTS")

    for symbol, amount in sorted(
        result.final_minerals.items()
    ):
        print(f"{symbol:<12} {amount:.10f}")

    # -----------------------------------------------------
    # 7. Warnings and scientific interpretation
    # -----------------------------------------------------

    print_section("WARNINGS AND AUDIT NOTES")

    if result.warnings:
        for warning in result.warnings:
            print(f"- {warning}")
    else:
        print("No calculation warnings.")

    print()
    print(
        "IMPORTANT: The published exercise uses Hyndman's "
        "procedure, whereas this application uses Kelsey (1965)."
    )
    print(
        "Differences must be investigated before interpreting "
        "them as calculation errors."
    )
    print(
        "Optional components were assigned explicit measured-zero "
        "values for this diagnostic run because the published "
        "example does not provide their measurements."
    )

    print_section("VALIDATION RUN FINISHED")


if __name__ == "__main__":
    run_validation()
