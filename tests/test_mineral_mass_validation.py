import math
import pytest

from src.mineral_formula_weights import (
    ATOMIC_WEIGHTS,
    OXIDE_MASSES,
    calculate_mineral_masses,
    get_formula_weight,
    mineral_mass_from_amount,
)


# Independent reference values calculated from the registry's stated
# atomic weights and the project's configured oxide molecular weights.
FIXED_FORMULA_WEIGHTS = {
    "ac": 461.99753856,
    "mt": 231.531,
    "cm": 223.8332,
    "il": 151.709,
    "fr": 78.074806326,
    "pr": 119.965,
    "cc": 100.086,
    "nc": 105.98753856,
}


@pytest.mark.parametrize(
    "symbol, expected",
    FIXED_FORMULA_WEIGHTS.items(),
)
def test_representative_fixed_mineral_formula_weights(symbol, expected):
    assert get_formula_weight(symbol) == pytest.approx(
        expected, abs=1e-8
    )


@pytest.mark.parametrize(
    "symbol, mg_expected, fe_expected",
    [
        ("di", 216.5504, 248.09),
        ("hy", 100.3887, 131.9283),
        ("ol", 140.6931, 203.7723),
    ],
)
def test_mg_fe_mineral_endmember_formula_weights(
    symbol, mg_expected, fe_expected
):
    mg_weight = get_formula_weight(
        symbol, mg_fraction=1.0, fe_fraction=0.0
    )
    fe_weight = get_formula_weight(
        symbol, mg_fraction=0.0, fe_fraction=1.0
    )

    assert mg_weight == pytest.approx(mg_expected, abs=1e-8)
    assert fe_weight == pytest.approx(fe_expected, abs=1e-8)


@pytest.mark.parametrize(
    "symbol, mg_expected, fe_expected",
    [
        ("di", 216.5504, 248.09),
        ("hy", 100.3887, 131.9283),
        ("ol", 140.6931, 203.7723),
    ],
)
def test_mg_fe_mineral_intermediate_composition_is_linear(
    symbol, mg_expected, fe_expected
):
    mg_fraction = 0.60
    fe_fraction = 0.40

    expected = mg_fraction * mg_expected + fe_fraction * fe_expected
    actual = get_formula_weight(
        symbol,
        mg_fraction=mg_fraction,
        fe_fraction=fe_fraction,
    )

    assert actual == pytest.approx(expected, abs=1e-8)


def test_fluorite_formula_weight_uses_exact_registry_atomic_weights():
    assert get_formula_weight("fr") == pytest.approx(
        78.074806326, abs=1e-10
    )


def test_apatite_uses_kelsey_p2o5_basis_and_fluorine_correction():
    amount = 1.0
    base_mass = (
        (10.0 / 3.0) * OXIDE_MASSES["CaO"]
        + OXIDE_MASSES["P2O5"]
    )
    full_fluorine_mass = base_mass + (1.0 / 3.0) * (
        ATOMIC_WEIGHTS["Ca"]
        + ATOMIC_WEIGHTS["F"]
        - OXIDE_MASSES["CaO"]
    )

    assert get_formula_weight("ap") == pytest.approx(base_mass, abs=1e-8)
    assert get_formula_weight(
        "ap", apatite_fluorine_fraction=1.0 / 3.0
    ) == pytest.approx(full_fluorine_mass, abs=1e-8)
    assert mineral_mass_from_amount(
        "ap", amount, apatite_fluorine_fraction=1.0 / 3.0
    ) == pytest.approx(full_fluorine_mass, abs=1e-8)


def test_halite_mass_uses_two_formula_units_per_internal_amount():
    amount = 0.5
    expected = get_formula_weight("hi")

    assert mineral_mass_from_amount("hi", amount) == pytest.approx(
        expected, abs=1e-8
    )


@pytest.mark.parametrize(
    "symbol",
    ["ac", "mt", "cm", "il", "ap", "fr", "pr", "cc", "nc"],
)
def test_fixed_mineral_mass_scales_linearly_with_amount(symbol):
    formula_weight = get_formula_weight(symbol)
    amount = 2.5

    actual = mineral_mass_from_amount(symbol, amount)

    expected = amount * formula_weight

    assert actual == pytest.approx(expected, abs=1e-8)


@pytest.mark.parametrize("symbol", ["q", "ac", "mt", "ap", "hi", "di", "hy", "ol"])
def test_zero_mineral_amount_returns_zero_mass(symbol):
    kwargs = (
        {"mg_fraction": 0.6, "fe_fraction": 0.4}
        if symbol in {"di", "hy", "ol"}
        else {}
    )

    assert mineral_mass_from_amount(symbol, 0.0, **kwargs) == 0.0


def test_calculate_mineral_masses_preserves_input_amounts_and_keys():
    minerals = {
        "ac": 0.25,
        "mt": 0.10,
        "fr": 0.05,
        "ap": 0.03,
        "hy": 0.20,
        "ol": 0.15,
    }
    original = minerals.copy()

    result = calculate_mineral_masses(
        minerals,
        mg_fraction=0.7,
        fe_fraction=0.3,
    )

    assert set(result) == set(minerals)
    assert minerals == original
    assert all(value >= 0 for value in result.values())


@pytest.mark.parametrize(
    "amount",
    [-1.0, math.inf, -math.inf, math.nan],
)
def test_negative_or_nonfinite_amounts_are_rejected(amount):
    with pytest.raises(ValueError):
        mineral_mass_from_amount("q", amount)


def test_boolean_amount_is_rejected():
    with pytest.raises(TypeError):
        mineral_mass_from_amount("q", True)


@pytest.mark.parametrize(
    "mg_fraction, fe_fraction",
    [
        (0.5, 0.4),
        (-0.1, 1.1),
        (math.nan, 0.0),
        (math.inf, 0.0),
    ],
)
def test_invalid_mg_fe_compositions_are_rejected(
    mg_fraction, fe_fraction
):
    with pytest.raises(ValueError):
        get_formula_weight(
            "di",
            mg_fraction=mg_fraction,
            fe_fraction=fe_fraction,
        )
