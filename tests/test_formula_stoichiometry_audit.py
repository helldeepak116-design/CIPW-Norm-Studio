
import math

import pytest

from src.mineral_formula_weights import (
    ATOMIC_WEIGHTS,
    MINERAL_FORMULAE,
    OXIDE_MASSES,
    get_formula_weight,
)


# Independent expected atom counts for every fixed-composition registry entry.
# Apatite is intentionally excluded: the selected Kelsey (1965) convention
# is represented on a P2O5-equivalent basis with variable allocated fluorine.
EXPECTED_ATOMS = {
    "q":  {"Si": 1, "O": 2},
    "c":  {"Al": 2, "O": 3},
    "z":  {"Zr": 1, "Si": 1, "O": 4},
    "or": {"K": 2, "Al": 2, "Si": 6, "O": 16},
    "ab": {"Na": 2, "Al": 2, "Si": 6, "O": 16},
    "an": {"Ca": 1, "Al": 2, "Si": 2, "O": 8},
    "lc": {"K": 2, "Al": 2, "Si": 4, "O": 12},
    "ne": {"Na": 2, "Al": 2, "Si": 2, "O": 8},
    "kp": {"K": 2, "Al": 2, "Si": 2, "O": 8},
    "hi": {"Na": 1, "Cl": 1},
    "th": {"Na": 2, "S": 1, "O": 4},
    "nc": {"Na": 2, "C": 1, "O": 3},
    "ac": {"Na": 2, "Fe": 2, "Si": 4, "O": 12},
    "ns": {"Na": 2, "Si": 1, "O": 3},
    "ks": {"K": 2, "Si": 1, "O": 3},
    "wo": {"Ca": 1, "Si": 1, "O": 3},
    "cs": {"Ca": 2, "Si": 1, "O": 4},
    "mt": {"Fe": 3, "O": 4},
    "cm": {"Fe": 1, "Cr": 2, "O": 4},
    "il": {"Fe": 1, "Ti": 1, "O": 3},
    "hm": {"Fe": 2, "O": 3},
    "tn": {"Ca": 1, "Ti": 1, "Si": 1, "O": 5},
    "pf": {"Ca": 1, "Ti": 1, "O": 3},
    "ru": {"Ti": 1, "O": 2},
    "fr": {"Ca": 1, "F": 2},
    "pr": {"Fe": 1, "S": 2},
    "cc": {"Ca": 1, "C": 1, "O": 3},
}


def test_registry_has_31_normative_minerals():
    assert len(MINERAL_FORMULAE) == 31


def test_all_fixed_formula_atom_counts_match_expected_stoichiometry():
    actual_fixed = {
        symbol: dict(entry.atoms)
        for symbol, entry in MINERAL_FORMULAE.items()
        if entry.atoms is not None
    }

    assert actual_fixed == EXPECTED_ATOMS


def test_all_variable_composition_entries_are_explicitly_variable():
    expected = {"ap", "di", "hy", "ol"}

    actual = {
        symbol
        for symbol, entry in MINERAL_FORMULAE.items()
        if entry.atoms is None
    }

    assert actual == expected


@pytest.mark.parametrize(
    "symbol, expected_factor",
    [
        (symbol, 1.0)
        for symbol in sorted(MINERAL_FORMULAE)
        if symbol not in {"hi"}
    ] + [("hi", 2.0)],
)
def test_internal_amount_conversion_factors(symbol, expected_factor):
    assert MINERAL_FORMULAE[
        symbol
    ].formula_units_per_internal_amount == pytest.approx(expected_factor)


@pytest.mark.parametrize("symbol", sorted(EXPECTED_ATOMS))
def test_fixed_formula_weights_are_finite_and_positive(symbol):
    weight = get_formula_weight(symbol)

    assert math.isfinite(weight)
    assert weight > 0


def test_kelsey_apatite_uses_p2o5_internal_amount_basis():
    entry = MINERAL_FORMULAE["ap"]

    assert entry.formula == "3CaO.P2O5.(1/3)CaF"
    assert entry.formula_units_per_internal_amount == pytest.approx(1.0)
    assert entry.fixed_oxide_mass == pytest.approx(
        (10.0 / 3.0) * OXIDE_MASSES["CaO"]
        + OXIDE_MASSES["P2O5"]
    )


def test_kelsey_apatite_fluorine_allocation_is_variable():
    entry = MINERAL_FORMULAE["ap"]

    assert entry.atoms is None

    phosphate_only = get_formula_weight(
        "ap",
        apatite_fluorine_fraction=0.0,
    )

    maximum_kelsey_fluorine = get_formula_weight(
        "ap",
        apatite_fluorine_fraction=1.0 / 3.0,
    )

    expected_difference = (1.0 / 3.0) * (
        ATOMIC_WEIGHTS["Ca"]
        + ATOMIC_WEIGHTS["F"]
        - OXIDE_MASSES["CaO"]
    )

    assert math.isfinite(phosphate_only)
    assert math.isfinite(maximum_kelsey_fluorine)
    assert phosphate_only > 0
    assert maximum_kelsey_fluorine > phosphate_only
    assert maximum_kelsey_fluorine - phosphate_only == pytest.approx(
        expected_difference
    )


@pytest.mark.parametrize(
    "fluorine_fraction",
    [-0.01, 0.34, math.inf, math.nan],
)
def test_kelsey_apatite_rejects_invalid_fluorine_fraction(
    fluorine_fraction,
):
    with pytest.raises(ValueError):
        get_formula_weight(
            "ap",
            apatite_fluorine_fraction=fluorine_fraction,
        )


def test_all_variable_mg_fe_entries_are_explicitly_variable():
    expected = {"di", "hy", "ol"}

    actual = {
        symbol
        for symbol, entry in MINERAL_FORMULAE.items()
        if entry.atoms is None and symbol != "ap"
    }

    assert actual == expected


@pytest.mark.parametrize(
    "symbol, expected_mg_fe_units",
    [
        ("di", 1.0),
        ("hy", 1.0),
        ("ol", 2.0),
    ],
)
def test_variable_mg_fe_oxide_component_counts(symbol, expected_mg_fe_units):
    entry = MINERAL_FORMULAE[symbol]

    assert entry.mg_fe_oxide_units == pytest.approx(expected_mg_fe_units)
    assert entry.fixed_oxide_mass > 0


def test_leucite_has_correct_oxide_equivalent_oxygen_count():
    # K2O + Al2O3 + 4SiO2 contains 1 + 3 + 8 = 12 oxygen atoms.
    assert MINERAL_FORMULAE["lc"].atoms["O"] == 12
