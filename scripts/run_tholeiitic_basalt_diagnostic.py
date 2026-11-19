"""Diagnostic end-to-end comparison with Winter's tholeiitic basalt.

Reference:
Winter, J. D. (2014), Principles of Igneous and Metamorphic Petrology,
2nd edition, Appendix B: The CIPW Norm, Table 2,
" C I P W Norm Calculation for Tholeiitic Basalt" (Mid-Atlantic Ridge).

Winter explicitly describes the presented procedure as a simplification
of the original CIPW norm, modified by later authors including Kelsey.
Consequently, this script reports differences; it does not fail merely
because the Kelsey (1965) engine differs from Winter's worked norm.

Run from the project root:
    python -m scripts.run_tholeiitic_basalt_diagnostic
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.norm_calculation import calculate_cipw_norm
from src.optional_components import OPTIONAL_COMPONENTS


THOLEIITIC_BASALT_OXIDES = {
    "SiO2": 49.20,
    "TiO2": 2.03,
    "Al2O3": 16.10,
    "Fe2O3": 2.72,
    "FeO": 7.77,
    "MnO": 0.18,
    "MgO": 6.44,
    "CaO": 10.50,
    "Na2O": 3.01,
    "K2O": 0.14,
    "P2O5": 0.23,
}

# Winter Table 2 reports 0.14 wt.% elemental S and 1.65 wt.% H2O.
# H2O is not an input to this anhydrous norm. S is entered explicitly.
OPTIONAL_MEASUREMENTS = {
    component: {
        "status": "measured_zero",
        "value_wt_percent": 0.0,
    }
    for component in OPTIONAL_COMPONENTS
}
OPTIONAL_MEASUREMENTS["S"] = {
    "status": "measured",
    "value_wt_percent": 0.14,
}

# Published molecular proportions of normative minerals from Winter
# Table 2. The "Remainder" column is an intermediate FeO+MgO pool,
# not a normative mineral, so it is deliberately excluded.
PUBLISHED_NORM_MOLECULAR_AMOUNTS = {
    "ap": 0.0016,
    "pr": 0.0022,
    "il": 0.0254,
    "or": 0.0015,
    "ab": 0.0486,
    "an": 0.1079,
    "mt": 0.0170,
    "di": 0.0740,
    "hy": 0.1519,
    "q": 0.0031,
}

PUBLISHED_NORM_WT_PERCENT = {
    "ap": 0.53,
    "pr": 0.26,
    "il": 3.86,
    "or": 0.83,
    "ab": 25.47,
    "an": 30.01,
    "mt": 3.94,
    "di": 16.70,
    "hy": 16.65,
    "q": 0.18,
}


def section(title: str) -> None:
    print()
    print("=" * 88)
    print(title)
    print("=" * 88)


def run_diagnostic() -> None:
    print("REFERENCE: Winter (2014), Appendix B, Table 2")
    print("ROCK: Mid-Atlantic Ridge tholeiitic basalt")
    print("REFERENCE PROCEDURE: simplified/modified CIPW")
    print("ENGINE PROCEDURE: classical Kelsey (1965)")
    print("COMPARISON: diagnostic only; not exact-method equivalence")

    print(f"Major-oxide total: {sum(THOLEIITIC_BASALT_OXIDES.values()):.4f} wt.%")
    print("Additional reported components: S = 0.14 wt.%; H2O = 1.65 wt.%")
    print("H2O is excluded from the anhydrous norm; S is included as elemental S.")

    result = calculate_cipw_norm(
        major_oxide_wt_percent=THOLEIITIC_BASALT_OXIDES,
        optional_measurements=OPTIONAL_MEASUREMENTS,
        sulfur_basis="S",
        carbonate_mode="none",
        volatile_free=False,
        assume_unmeasured_zero=False,
    )

    section("CALCULATION STATUS")
    print(f"Status: {result.status}")
    print(f"Method: {result.method}")
    print(f"Mass-balance status: {result.mass_balance.status}")
    print(f"Mass balance passed: {result.mass_balance.balanced}")
    print(
        "Maximum non-silica component error: "
        f"{result.mass_balance.max_non_silica_error:.12g}"
    )
    print(f"Silica error: {result.mass_balance.silica_error:.12g}")
    print(
        "Silica deficiency remaining: "
        f"{result.redistribution_result.final_deficiency:.12g}"
    )

    section("MAJOR OXIDE MOLECULAR PROPORTIONS")
    print(f"{'Oxide':<12}{'Input wt.%':>14}{'Studio moles':>18}")
    print("-" * 44)
    for oxide, wt_percent in THOLEIITIC_BASALT_OXIDES.items():
        print(
            f"{oxide:<12}{wt_percent:>14.4f}"
            f"{result.major_oxide_moles[oxide]:>18.8f}"
        )

    section("PUBLISHED NORM MOLECULAR AMOUNTS VS STUDIO")
    print(f"{'Mineral':<12}{'Winter':>16}{'Studio':>16}{'Difference':>16}")
    print("-" * 60)
    symbols = sorted(
        set(PUBLISHED_NORM_MOLECULAR_AMOUNTS)
        | set(result.final_minerals)
    )
    for symbol in symbols:
        published = PUBLISHED_NORM_MOLECULAR_AMOUNTS.get(symbol, 0.0)
        studio = float(result.final_minerals.get(symbol, 0.0))
        print(
            f"{symbol:<12}{published:>16.6f}"
            f"{studio:>16.6f}{studio - published:>16.6f}"
        )

    section("PUBLISHED NORM WT.% VS STUDIO")
    print(f"{'Mineral':<12}{'Winter wt.%':>16}{'Studio wt.%':>16}{'Difference':>16}")
    print("-" * 60)
    symbols = sorted(
        set(PUBLISHED_NORM_WT_PERCENT)
        | set(result.mineral_wt_percent)
    )
    # Winter's printed mineral weights are on the original-rock basis
    # and sum to approximately the anhydrous analytical mass, not 100%.
    # Normalize them before comparing with result.mineral_wt_percent,
    # which the Studio normalizes to 100% of its normative mineral mass.
    published_norm_total = sum(PUBLISHED_NORM_WT_PERCENT.values())
    print(
        "Winter printed norm-weight total before normalization: "
        f"{published_norm_total:.4f} wt.%"
    )
    for symbol in symbols:
        published_raw = PUBLISHED_NORM_WT_PERCENT.get(symbol, 0.0)
        published = (
            published_raw / published_norm_total * 100.0
            if published_norm_total > 0 else 0.0
        )
        studio = float(result.mineral_wt_percent.get(symbol, 0.0))
        print(
            f"{symbol:<12}{published:>16.4f}"
            f"{studio:>16.4f}{studio - published:>16.4f}"
        )

    section("INTERPRETATION")
    print(
        "This is a diagnostic comparison. Winter's table is a simplified/"
        "modified CIPW calculation, not a declared exact Kelsey (1965) "
        "reference result."
    )
    print(
        "Investigate differences in sulfur allocation, Fe-Mg distribution, "
        "mineral formula weights, and rounding before treating them as defects."
    )
    print(
        "The measured-zero optional-component entries are explicit assumptions "
        "for components not reported in this reference."
    )

    if not result.mass_balance.balanced:
        raise RuntimeError(
            "The Studio's internal component mass balance failed for this case."
        )

    print()
    print("DIAGNOSTIC RUN COMPLETED; REVIEW DIFFERENCES BEFORE ACCEPTANCE.")


if __name__ == "__main__":
    run_diagnostic()
