"""Extended published-reference checks for CIPW Norm Studio.

Reference:
Winter, J. D. (2014), Principles of Igneous and Metamorphic Petrology,
2nd edition, Appendix B: The CIPW Norm, Table 2
("CIPW Norm Calculation for Tholeiitic Basalt", Mid-Atlantic Ridge).

This test checks the published major-oxide molecular proportions only.
Winter's worked norm is a simplified/modified CIPW procedure and is
therefore not used here as an exact Kelsey (1965) mineral-norm oracle.
The end-to-end comparison is reported separately by
scripts/run_tholeiitic_basalt_diagnostic.py.
"""

import pytest

from src.oxide_conversion import convert_oxides_to_molecular_proportions


# The 11 major oxides transcribed from Winter (2014), Table 2.
# The reported analytical total of 100.11 wt.% also includes
# 0.14 wt.% elemental S and 1.65 wt.% H2O; those are not major oxides.
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

# Molecular proportions calculated from the published wt.% and
# the corresponding formula weights in Winter's table, rounded to
# four decimal places. FeO is kept separate from MnO here; Winter's
# later allocation step combines MnO with FeO.
PUBLISHED_MAJOR_MOLECULAR_PROPORTIONS = {
    "SiO2": 0.8189,
    "TiO2": 0.0254,
    "Al2O3": 0.1579,
    "Fe2O3": 0.0170,
    "FeO": 0.1081,
    "MnO": 0.0025,
    "MgO": 0.1598,
    "CaO": 0.1872,
    "Na2O": 0.0486,
    "K2O": 0.0015,
    "P2O5": 0.0016,
}


def test_winter_tholeiitic_basalt_major_oxide_total():
    assert sum(THOLEIITIC_BASALT_OXIDES.values()) == pytest.approx(
        98.32,
        abs=1e-8,
    )


def test_winter_tholeiitic_basalt_published_molecular_proportions():
    conversion = convert_oxides_to_molecular_proportions(
        THOLEIITIC_BASALT_OXIDES,
        volatile_free=False,
    )

    table = conversion["oxide_table"]

    for oxide, expected in PUBLISHED_MAJOR_MOLECULAR_PROPORTIONS.items():
        actual = float(table.loc[oxide, "molecular_proportion"])

        # The published molecular proportions are rounded to 4 decimals.
        assert actual == pytest.approx(
            expected,
            abs=0.0002,
        ), f"Winter tholeiitic basalt molecular proportion mismatch: {oxide}"

    assert conversion["volatile_free"] is False
    assert conversion["original_analytical_total"] == pytest.approx(
        98.32,
        abs=1e-8,
    )
    assert conversion["conversion_total"] == pytest.approx(
        98.32,
        abs=1e-8,
    )
