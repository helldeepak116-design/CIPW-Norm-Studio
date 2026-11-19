"""End-to-end diagnostic regression benchmark: Winter (2014) basalt.

Reference:
Winter, J. D. (2014), Principles of Igneous and Metamorphic Petrology,
2nd edition, Appendix B, Table 2: CIPW Norm Calculation for Tholeiitic
Basalt (Mid-Atlantic Ridge).

IMPORTANT METHOD QUALIFICATION
Winter's worked example is a simplified/modified CIPW procedure, not an
exact independent Kelsey (1965) norm. This test therefore protects the
current Studio result from regression against a published diagnostic
example; it does not certify exact Kelsey-method equivalence.

The published mineral molecular amounts are printed to approximately
four decimal places. An absolute tolerance of 1e-4 is used to cover
published rounding and the small method-convention differences observed
in the diagnostic comparison. This tolerance is not a universal
scientific acceptance criterion for other rocks or procedures.
"""

import pytest

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

# Winter (2014), Table 2: published normative mineral molecular amounts.
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

# Diagnostic tolerance: see module docstring. The maximum observed
# difference in the checked-in diagnostic run is about 8.8e-5 (quartz).
PUBLISHED_DIAGNOSTIC_ABS_TOLERANCE = 1.0e-4


@pytest.fixture(scope="module")
def winter_basalt_result():
    return calculate_cipw_norm(
        major_oxide_wt_percent=THOLEIITIC_BASALT_OXIDES,
        optional_measurements=OPTIONAL_MEASUREMENTS,
        sulfur_basis="S",
        carbonate_mode="none",
        volatile_free=False,
        assume_unmeasured_zero=False,
    )


def test_winter_tholeiitic_basalt_normative_molecular_amounts(
    winter_basalt_result,
):
    """Compare all ten published mineral amounts within stated tolerance."""

    actual = winter_basalt_result.final_minerals

    for mineral, expected in PUBLISHED_NORM_MOLECULAR_AMOUNTS.items():
        assert actual.get(mineral, 0.0) == pytest.approx(
            expected,
            abs=PUBLISHED_DIAGNOSTIC_ABS_TOLERANCE,
            rel=0.0,
        ), (
            f"{mineral} differs from Winter (2014) diagnostic reference: "
            f"actual={actual.get(mineral, 0.0):.10f}, "
            f"published={expected:.10f}"
        )


def test_winter_tholeiitic_basalt_calculation_completes_with_mass_balance(
    winter_basalt_result,
):
    """Require a completed calculation and internally balanced components."""

    assert winter_basalt_result.status == "COMPLETED"
    assert winter_basalt_result.mass_balance.balanced is True
    assert winter_basalt_result.mass_balance.max_non_silica_error <= 1e-8
    assert abs(winter_basalt_result.mass_balance.silica_error) <= 1e-8
    assert winter_basalt_result.redistribution_result.final_deficiency == pytest.approx(
        0.0,
        abs=1e-8,
    )
