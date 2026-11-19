"""Run Kelsey's (1965) Bostonite worked-example diagnostic.

Run from the project root:
    python -m scripts.run_kelsey_bostonite_validation
"""

from src.norm_calculation import calculate_cipw_norm
from src.optional_components import OPTIONAL_COMPONENTS

# Kelsey (1965), Table III inputs. Fe2O3=1.05 and TiO2=0.21 wt.%.
MAJOR_OXIDES = {
    "SiO2": 61.15,
    "TiO2": 0.21,
    "Al2O3": 22.07,
    "Fe2O3": 1.05,
    "FeO": 1.02,
    "MnO": 0.0,       # not reported; assumed zero for this diagnostic
    "MgO": 0.40,
    "CaO": 0.75,
    "Na2O": 5.86,
    "K2O": 7.01,
    "P2O5": 0.0,      # not reported; assumed zero for this diagnostic
}

OPTIONAL = {
    component: {"status": "not_measured", "value_wt_percent": None}
    for component in OPTIONAL_COMPONENTS
}

PUBLISHED = {
    "c": 0.034,
    "ol": 0.008,
    "or": 0.074,
    "mt": 0.006,
    "ab": 0.087,
    "il": 0.003,
    "an": 0.014,
    "ne": 0.008,
}


def main():
    result = calculate_cipw_norm(
        MAJOR_OXIDES,
        OPTIONAL,
        sulfur_basis="none",
        carbonate_mode="none",
        volatile_free=False,
        assume_unmeasured_zero=True,
    )

    provisional = result.provisional_result
    redistribution = result.redistribution_result

    print("=" * 76)
    print("KELSEY (1965) BOSTONITE — MOLECULAR-NORM DIAGNOSTIC")
    print("Table III; Washington (1917), p. 274, analysis no. 37")
    print("=" * 76)
    print(f"Method: {result.method}")
    print(f"Status: {result.status}; conditional: {result.conditional}")
    print("Kelsey Table III input values: Fe2O3=1.05, TiO2=0.21 wt.%")
    print("MnO and P2O5 are unreported and assumed zero.")
    print("Optional components are unmeasured and conditionally assumed zero.")
    print()

    print("SILICA-DEFICIENCY INTERMEDIATES (molecular proportions)")
    print(f"Initial D: {provisional.silica_deficiency:.6f} (Kelsey: 0.038)")
    print(f"Provisional hy': {provisional.minerals.get('hy', 0.0):.6f} (Kelsey: 0.015)")
    print(f"Provisional ab': {provisional.minerals.get('ab', 0.0):.6f} (Kelsey: 0.095)")
    print(f"Final D: {redistribution.final_deficiency:.8f}")
    print()

    print("FINAL NORMATIVE MOLECULAR AMOUNTS")
    print(f"{'Mineral':<12}{'Studio':>14}{'Kelsey':>14}{'Difference':>16}")
    for mineral, published in PUBLISHED.items():
        actual = result.final_minerals.get(mineral, 0.0)
        print(f"{mineral:<12}{actual:>14.6f}{published:>14.6f}{actual-published:>16.6f}")

    print()
    print("FULL-PRECISION MINERAL MASSES (diagnostic only; not direct comparison)")
    for mineral in PUBLISHED:
        print(f"{mineral:<8} {result.mineral_masses.get(mineral, 0.0):.6f} wt.%")
    print()
    print("AUDIT")
    print(f"Mass balance balanced: {result.mass_balance.balanced}")
    print(f"Maximum non-silica error: {result.mass_balance.max_non_silica_error:.8g}")
    print(f"Silica error: {result.mass_balance.silica_error:.8g}")
    print("Kelsey's published norm is rounded to three decimal molecular amounts.")
    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"- {warning}")


if __name__ == "__main__":
    main()
