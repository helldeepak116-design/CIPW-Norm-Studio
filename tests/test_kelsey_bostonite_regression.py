"""Kelsey (1965) Bostonite molecular-norm regression benchmark.

Sources:
- Kelsey (1965), Mineralogical Magazine 34(268), Table III, pp. 281-282.
- Washington (1917), Professional Paper 99, p. 274, analysis no. 37.

Kelsey's Table III uses Fe2O3 = 1.05 wt.% and TiO2 = 0.21 wt.%.
These differ slightly from the Washington analysis transcription
(1.06 and 0.20 respectively); this test uses Kelsey's printed inputs.

Kelsey publishes normative mineral molecular amounts to three decimal
places and normative weight percentages calculated from those rounded
amounts. This test therefore compares final molecular amounts, not
full-precision mineral masses calculated from modern formula weights.

MnO and P2O5 are not reported in the original analysis. They are
explicitly set to zero for this conditional historical reproduction.
All optional components are marked not_measured and conditionally
assumed zero; this is not equivalent to measured zero.
"""

import pytest

from src.norm_calculation import calculate_cipw_norm
from src.optional_components import OPTIONAL_COMPONENTS


# Kelsey (1965), Table III; source analysis Washington (1917), p. 274, No. 37.
# H2O+ is excluded from the anhydrous CIPW calculation.
KELSEY_BOSTONITE_MAJOR_OXIDES = {
    "SiO2": 61.15,
    "TiO2": 0.21,      # Kelsey Table III value
    "Al2O3": 22.07,
    "Fe2O3": 1.05,     # Kelsey Table III value
    "FeO": 1.02,
    "MnO": 0.0,        # not reported; explicit zero assumption
    "MgO": 0.40,
    "CaO": 0.75,
    "Na2O": 5.86,
    "K2O": 7.01,
    "P2O5": 0.0,       # not reported; explicit zero assumption
}

OPTIONAL_MEASUREMENTS = {
    component: {"status": "not_measured", "value_wt_percent": None}
    for component in OPTIONAL_COMPONENTS
}

# Kelsey (1965), Table III: normative mineral molecular amounts,
# printed to three decimal places.
PUBLISHED_NORM_MOLECULAR_AMOUNTS = {
    "c": 0.034,
    "ol": 0.008,
    "or": 0.074,
    "mt": 0.006,
    "ab": 0.087,
    "il": 0.003,
    "an": 0.014,
    "ne": 0.008,
}

# Historical source values are rounded to 0.001 molecular proportions.
# This tolerance allows for rounding and modern formula-weight conventions.
PUBLISHED_MOLECULAR_ABS_TOLERANCE = 0.0010
INTERMEDIATE_ABS_TOLERANCE = 0.0015


@pytest.fixture(scope="module")
def bostonite_result():
    return calculate_cipw_norm(
        KELSEY_BOSTONITE_MAJOR_OXIDES,
        OPTIONAL_MEASUREMENTS,
        sulfur_basis="none",
        carbonate_mode="none",
        volatile_free=False,
        assume_unmeasured_zero=True,
    )


def test_bostonite_result_is_explicitly_conditional(bostonite_result):
    result = bostonite_result

    assert result.conditional is True
    assert result.status == "CONDITIONAL"
    assert set(result.optional_component_conversion.unmeasured_components) == set(
        OPTIONAL_COMPONENTS
    )
    assert result.mass_balance.balanced is True


def test_bostonite_kelsey_silica_deficiency_intermediates(bostonite_result):
    provisional = bostonite_result.provisional_result

    assert provisional.silica_deficiency == pytest.approx(
        0.038, abs=INTERMEDIATE_ABS_TOLERANCE, rel=0.0
    )
    assert provisional.minerals["hy"] == pytest.approx(
        0.015, abs=INTERMEDIATE_ABS_TOLERANCE, rel=0.0
    )
    assert provisional.minerals["ab"] == pytest.approx(
        0.095, abs=INTERMEDIATE_ABS_TOLERANCE, rel=0.0
    )

    final = bostonite_result.final_minerals
    for mineral, expected in {
        "ol": 0.008,
        "hy": 0.0,
        "ab": 0.087,
        "ne": 0.008,
    }.items():
        assert final.get(mineral, 0.0) == pytest.approx(
            expected, abs=INTERMEDIATE_ABS_TOLERANCE, rel=0.0
        )


def test_bostonite_published_final_norm_molecular_amounts(bostonite_result):
    result = bostonite_result

    for mineral, published_amount in PUBLISHED_NORM_MOLECULAR_AMOUNTS.items():
        assert result.final_minerals.get(mineral, 0.0) == pytest.approx(
            published_amount,
            abs=PUBLISHED_MOLECULAR_ABS_TOLERANCE,
            rel=0.0,
        )

    assert result.redistribution_result.final_deficiency == pytest.approx(
        0.0, abs=1e-10
    )
