
"""Published reference-data checks for CIPW Norm Studio.

References
----------
1. Mattioli, G. and Zachry, D. (2008).
   GEOL 2313 - Homework Assignment 3.
   University of Arkansas.

   Idaho Batholith granite, sample 134.15.

   The published exercise uses Hyndman's procedure, not explicitly
   Kelsey (1965). This test checks independently published oxide
   molecular proportions, not equivalence of final mineral norms.

2. Kelsey, C. H. (1965).
   Calculation of the C.I.P.W. norm.
   Mineralogical Magazine, 34(268), 276-282.
   DOI: 10.1180/minmag.1965.034.268.23

   Bostonite from Maros, Celebes.
   Washington (1917), p. 274, analysis no. 37.

   This test checks the published silica-deficiency intermediates
   and the Rules 22 and 24 redistribution results. It is not a
   complete end-to-end Bostonite norm benchmark because the full
   original oxide vector has not yet been independently transcribed.
"""

import pytest

from src.oxide_conversion import (
    convert_oxides_to_molecular_proportions,
)

from src.kelsey_silica_deficiency import (
    redistribute_silica,
)


# ---------------------------------------------------------------------
# Idaho Batholith granite: published oxide molecular proportions
# ---------------------------------------------------------------------

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


# Published molecular proportions rounded to four decimal places.
PUBLISHED_MOLECULAR_PROPORTIONS = {
    "SiO2": 1.1759,
    "TiO2": 0.0030,
    "Al2O3": 0.1568,
    "Fe2O3": 0.0048,
    "FeO": 0.0097,
    "MnO": 0.0004,
    "MgO": 0.0117,
    "CaO": 0.0323,
    "Na2O": 0.0768,
    "K2O": 0.0377,
    "P2O5": 0.0005,
}


def test_idaho_granite_analytical_total():
    total = sum(IDAHO_GRANITE_OXIDES.values())

    assert total == pytest.approx(99.04, abs=1e-8)


def test_idaho_granite_published_molecular_proportions():
    conversion = convert_oxides_to_molecular_proportions(
        IDAHO_GRANITE_OXIDES,
        volatile_free=False,
    )

    table = conversion["oxide_table"]

    for oxide, expected in PUBLISHED_MOLECULAR_PROPORTIONS.items():
        actual = float(
            table.loc[oxide, "molecular_proportion"]
        )

        # Published values are rounded to four decimal places.
        assert actual == pytest.approx(
            expected,
            abs=0.0002,
        ), f"Molecular proportion mismatch for {oxide}"


def test_idaho_granite_conversion_preserves_analytical_basis():
    conversion = convert_oxides_to_molecular_proportions(
        IDAHO_GRANITE_OXIDES,
        volatile_free=False,
    )

    assert conversion["volatile_free"] is False

    assert conversion["original_analytical_total"] == pytest.approx(
        99.04,
        abs=1e-8,
    )

    assert conversion["conversion_total"] == pytest.approx(
        99.04,
        abs=1e-8,
    )


# ---------------------------------------------------------------------
# Kelsey (1965): published Bostonite silica-deficiency example
# ---------------------------------------------------------------------

# Values transcribed from Kelsey's Table III:
#
# Initial silica deficiency D = 0.038
# Provisional hypersthene hy' = 0.015
# Provisional albite ab' = 0.095
#
# The paper prints intermediate and final molecular amounts to
# approximately three decimal places. The test therefore uses a
# tolerance appropriate to that published rounding.

BOSTONITE_INITIAL_DEFICIENCY = 0.038
BOSTONITE_PROVISIONAL_MINERALS = {
    "hy": 0.015,
    "ab": 0.095,
}


def test_kelsey_bostonite_rule_22_hypersthene_to_olivine():
    result = redistribute_silica(
        BOSTONITE_PROVISIONAL_MINERALS,
        BOSTONITE_INITIAL_DEFICIENCY,
    )

    # Rule 22 converts the available provisional hypersthene.
    assert result.minerals["hy"] == pytest.approx(
        0.0,
        abs=1e-10,
    )

    assert result.minerals["ol"] == pytest.approx(
        0.0075,
        abs=1e-10,
    )

    # D after Rule 22:
    # 0.038 - (0.015 / 2) = 0.0305.
    assert result.steps[0]["rule"] == 22

    assert result.steps[0]["provisional_amount_converted"] == pytest.approx(
        0.015,
        abs=1e-10,
    )

    assert result.steps[0]["deficiency_after"] == pytest.approx(
        0.0305,
        abs=1e-10,
    )

    # Kelsey's printed value is approximately 0.030.
    assert result.steps[0]["deficiency_after"] == pytest.approx(
        0.030,
        abs=0.0006,
    )


def test_kelsey_bostonite_rule_24_albite_to_nepheline():
    result = redistribute_silica(
        BOSTONITE_PROVISIONAL_MINERALS,
        BOSTONITE_INITIAL_DEFICIENCY,
    )

    # Rule 22 leaves D = 0.0305.
    # Rule 24 converts D / 4 = 0.007625 albite to nepheline.
    assert result.minerals["ne"] == pytest.approx(
        0.007625,
        abs=1e-10,
    )

    assert result.minerals["ab"] == pytest.approx(
        0.087375,
        abs=1e-10,
    )

    # Published rounded values: ne approximately 0.008 and
    # ab approximately 0.087.
    assert result.minerals["ne"] == pytest.approx(
        0.008,
        abs=0.0006,
    )

    assert result.minerals["ab"] == pytest.approx(
        0.087,
        abs=0.0006,
    )

    assert result.steps[-1]["rule"] == 24

    assert result.steps[-1]["deficiency_after"] == pytest.approx(
        0.0,
        abs=1e-10,
    )

    assert result.final_deficiency == pytest.approx(
        0.0,
        abs=1e-10,
    )


def test_kelsey_bostonite_applies_rules_in_published_order():
    result = redistribute_silica(
        BOSTONITE_PROVISIONAL_MINERALS,
        BOSTONITE_INITIAL_DEFICIENCY,
    )

    applied_rules = [
        step["rule"]
        for step in result.steps
    ]

    # The Bostonite example requires Rule 22 followed by Rule 24.
    # Rules 23 and 25-28 are not needed for this particular example.
    assert applied_rules == [22, 24]

    assert result.status == "COMPLETED"

    assert result.final_deficiency == pytest.approx(
        0.0,
        abs=1e-10,
    )
