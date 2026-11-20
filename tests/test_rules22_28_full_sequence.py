import pytest

from src.kelsey_silica_deficiency import redistribute_silica
from src.mass_balance import mineral_oxide_equivalents


INITIAL_MINERALS = {
    "hy": 0.1,
    "tn": 0.1,
    "ab": 0.1,
    "or": 0.1,
    "wo": 0.1,
    "di": 0.1,
}

INITIAL_DEFICIENCY = 2.0
MG_FRACTION = 0.75
FE_FRACTION = 0.25
TOLERANCE = 1e-10


def test_rules22_to_28_execute_in_correct_order():
    result = redistribute_silica(
        INITIAL_MINERALS,
        INITIAL_DEFICIENCY,
    )

    assert [step["rule"] for step in result.steps] == [
        22, 23, 24, 25, 26, 27, 28
    ]

    expected_deficiencies = [
        1.95, 1.85, 1.45, 1.25, 1.20, 1.10, 0.90
    ]

    for step, expected in zip(result.steps, expected_deficiencies):
        assert step["deficiency_after"] == pytest.approx(expected)


def test_rules22_to_28_produce_expected_final_minerals():
    result = redistribute_silica(
        INITIAL_MINERALS,
        INITIAL_DEFICIENCY,
    )

    expected = {
        "hy": 0.0,
        "tn": 0.0,
        "ab": 0.0,
        "or": 0.0,
        "wo": 0.0,
        "di": 0.0,
        "lc": 0.0,
        "ol": 0.1,
        "pf": 0.1,
        "ne": 0.1,
        "cs": 0.1,
        "kp": 0.1,
    }

    for mineral, amount in expected.items():
        assert result.minerals[mineral] == pytest.approx(amount)

    assert result.lc_prime_remaining == pytest.approx(0.0)


def test_rules22_to_28_conserve_non_silica_components():
    result = redistribute_silica(
        INITIAL_MINERALS,
        INITIAL_DEFICIENCY,
    )

    before = mineral_oxide_equivalents(
        INITIAL_MINERALS,
        MG_FRACTION,
        FE_FRACTION,
    )

    after = mineral_oxide_equivalents(
        result.minerals,
        MG_FRACTION,
        FE_FRACTION,
    )

    components = set(before) | set(after)

    for component in components - {"SiO2"}:
        assert after.get(component, 0.0) == pytest.approx(
            before.get(component, 0.0),
            abs=TOLERANCE,
        )


def test_rules22_to_28_release_expected_silica():
    result = redistribute_silica(
        INITIAL_MINERALS,
        INITIAL_DEFICIENCY,
    )

    before = mineral_oxide_equivalents(
        INITIAL_MINERALS,
        MG_FRACTION,
        FE_FRACTION,
    )

    after = mineral_oxide_equivalents(
        result.minerals,
        MG_FRACTION,
        FE_FRACTION,
    )

    silica_released = (
        before.get("SiO2", 0.0)
        - after.get("SiO2", 0.0)
    )

    assert silica_released == pytest.approx(1.1)
    assert result.initial_deficiency == pytest.approx(2.0)
    assert result.final_deficiency == pytest.approx(0.9)
    assert (
        result.initial_deficiency - result.final_deficiency
    ) == pytest.approx(silica_released)


def test_rules22_to_28_report_unresolved_deficiency():
    result = redistribute_silica(
        INITIAL_MINERALS,
        INITIAL_DEFICIENCY,
    )

    assert result.status == "UNRESOLVED_DEFICIENCY"
    assert result.final_deficiency == pytest.approx(0.9)
