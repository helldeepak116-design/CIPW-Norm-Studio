import math
import pytest

from src.mineral_formula_weights import (
    ATOMIC_WEIGHTS,
    MINERAL_FORMULAE,
    OXIDE_MASSES,
    calculate_mineral_masses,
    get_formula_weight,
    mineral_mass_from_amount,
)


def test_registry_contains_all_mass_balance_minerals():
    expected = {
        "z", "ap", "fr", "hi", "th", "pr", "nc", "cc", "cm",
        "il", "or", "ks", "ab", "ac", "ns", "an", "c", "tn",
        "ru", "mt", "hm", "di", "wo", "hy", "q", "ol", "pf",
        "ne", "lc", "cs", "kp",
    }
    assert set(MINERAL_FORMULAE) == expected


@pytest.mark.parametrize(
    "symbol, expected",
    [
        ("q", 60.083),
        ("c", 101.960077),
        ("hi", 58.43976928),
        ("pr", 119.965),
        ("fr", 78.073806326),
        ("cc", 100.086),
        ("wo", 116.161),
        ("hm", 159.687),
    ],
)
def test_selected_formula_weights(symbol, expected):
    assert get_formula_weight(symbol) == pytest.approx(expected, abs=0.01)


def test_apatite_uses_original_kelsey_formula_and_p2o5_internal_basis():
    formula_weight = get_formula_weight("ap")
    amount = 1.0

    assert MINERAL_FORMULAE["ap"].formula == "3CaO.P2O5.(1/3)CaF"
    assert MINERAL_FORMULAE["ap"].formula_units_per_internal_amount == pytest.approx(1.0)
    assert mineral_mass_from_amount("ap", amount) == pytest.approx(
        formula_weight
    )


def test_apatite_formula_weight_increases_with_allocated_fluorine():
    phosphate_only = get_formula_weight("ap", apatite_fluorine_fraction=0.0)
    kelsey_full_fluorine = get_formula_weight(
        "ap", apatite_fluorine_fraction=1.0 / 3.0
    )

    assert kelsey_full_fluorine > phosphate_only
    expected_difference = (1.0 / 3.0) * (
        ATOMIC_WEIGHTS["Ca"]
        + ATOMIC_WEIGHTS["F"]
        - OXIDE_MASSES["CaO"]
    )
    assert kelsey_full_fluorine - phosphate_only == pytest.approx(
        expected_difference
    )


def test_halite_internal_amount_is_converted_to_two_nacl_formula_units():
    assert MINERAL_FORMULAE["hi"].formula_units_per_internal_amount == 2.0
    assert mineral_mass_from_amount("hi", 0.5) == pytest.approx(
        get_formula_weight("hi")
    )


def test_mixed_mg_fe_formula_weights_are_composition_dependent():
    mg_endmember = get_formula_weight("hy", mg_fraction=1.0, fe_fraction=0.0)
    fe_endmember = get_formula_weight("hy", mg_fraction=0.0, fe_fraction=1.0)
    mixed = get_formula_weight("hy", mg_fraction=0.75, fe_fraction=0.25)

    assert mg_endmember < mixed < fe_endmember
    assert mixed == pytest.approx(
        0.75 * mg_endmember + 0.25 * fe_endmember
    )


@pytest.mark.parametrize("symbol", ["di", "hy", "ol"])
def test_mg_fe_formula_weights_require_rule_19_fractions(symbol):
    with pytest.raises(ValueError, match="requires Rule 19"):
        get_formula_weight(symbol)


def test_diopside_and_olivine_have_expected_mg_fe_dependence():
    mg_di = get_formula_weight("di", mg_fraction=1.0, fe_fraction=0.0)
    fe_di = get_formula_weight("di", mg_fraction=0.0, fe_fraction=1.0)
    mg_ol = get_formula_weight("ol", mg_fraction=1.0, fe_fraction=0.0)
    fe_ol = get_formula_weight("ol", mg_fraction=0.0, fe_fraction=1.0)

    assert mg_di < fe_di
    assert mg_ol < fe_ol


def test_calculate_mineral_masses_uses_internal_amount_factors():
    masses = calculate_mineral_masses(
        {"q": 1.0, "ap": 1.0, "hi": 0.5, "hy": 1.0},
        mg_fraction=0.75,
        fe_fraction=0.25,
    )

    assert masses["q"] == pytest.approx(get_formula_weight("q"))
    assert masses["ap"] == pytest.approx(get_formula_weight("ap"))
    assert masses["hi"] == pytest.approx(get_formula_weight("hi"))
    assert masses["hy"] == pytest.approx(
        get_formula_weight("hy", mg_fraction=0.75, fe_fraction=0.25)
    )


@pytest.mark.parametrize("amount", [-1.0, math.inf, math.nan])
def test_mineral_mass_rejects_invalid_amounts(amount):
    with pytest.raises(ValueError):
        mineral_mass_from_amount("q", amount)


def test_registry_rejects_unknown_mineral():
    with pytest.raises(ValueError, match="Unsupported"):
        get_formula_weight("unknown")


def test_mass_calculation_rejects_unknown_mineral():
    with pytest.raises(ValueError, match="Unsupported"):
        calculate_mineral_masses(
            {"unknown": 1.0},
            mg_fraction=0.5,
            fe_fraction=0.5,
        )


@pytest.mark.parametrize(
    "mg_fraction, fe_fraction",
    [(0.7, 0.2), (-0.1, 1.1), (math.nan, 0.0)],
)
def test_invalid_mg_fe_fractions_are_rejected(mg_fraction, fe_fraction):
    with pytest.raises(ValueError):
        get_formula_weight(
            "di",
            mg_fraction=mg_fraction,
            fe_fraction=fe_fraction,
        )
