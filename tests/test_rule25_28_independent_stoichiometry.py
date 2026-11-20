
import pytest

from src.kelsey_silica_deficiency import redistribute_silica


TOLERANCE = 1e-10


# Independent elemental formula vectors.
#
# Normative molecular-amount convention:
#
# Orthoclase (or):
#     K2O + Al2O3 + 6SiO2
#
# Leucite (lc):
#     K2O + Al2O3 + 4SiO2
#
# Kaliophilite (kp):
#     K2O + Al2O3 + 2SiO2
#
# Therefore:
#     1 or -> 1 lc + 2 SiO2
#     1 lc -> 1 kp + 2 SiO2
#
# These vectors are independently defined and do not import
# the application's mineral formula or mass-balance functions.


def orthoclase_atoms(amount):
    return {
        "K": amount * 2.0,
        "Al": amount * 2.0,
        "Si": amount * 6.0,
        "O": amount * 16.0,
    }


def leucite_atoms(amount):
    return {
        "K": amount * 2.0,
        "Al": amount * 2.0,
        "Si": amount * 4.0,
        "O": amount * 12.0,
    }


def kaliophilite_atoms(amount):
    return {
        "K": amount * 2.0,
        "Al": amount * 2.0,
        "Si": amount * 2.0,
        "O": amount * 8.0,
    }


def silica_atoms(amount):
    return {
        "K": 0.0,
        "Al": 0.0,
        "Si": amount,
        "O": amount * 2.0,
    }


def add_atoms(*vectors):
    elements = {"K", "Al", "Si", "O"}

    return {
        element: sum(vector[element] for vector in vectors)
        for element in elements
    }


@pytest.mark.parametrize(
    ("initial_deficiency", "expected_rule25", "expected_rule28"),
    [
        (0.10, 0.05, 0.0),
        (0.40, 0.10, 0.10),
        (0.60, 0.10, 0.10),
    ],
)
def test_rule25_rule28_independent_elemental_conservation(
    initial_deficiency,
    expected_rule25,
    expected_rule28,
):
    initial_orthoclase = 0.1

    result = redistribute_silica(
        {"or": initial_orthoclase},
        initial_deficiency,
    )

    rule25_steps = [
        step for step in result.steps
        if step["rule"] == 25
    ]

    rule28_steps = [
        step for step in result.steps
        if step["rule"] == 28
    ]

    assert len(rule25_steps) == 1

    converted_rule25 = (
        rule25_steps[0]["provisional_amount_converted"]
    )

    converted_rule28 = (
        rule28_steps[0]["provisional_amount_converted"]
        if rule28_steps else 0.0
    )

    assert converted_rule25 == pytest.approx(
        expected_rule25,
        abs=TOLERANCE,
    )

    assert converted_rule28 == pytest.approx(
        expected_rule28,
        abs=TOLERANCE,
    )

    remaining_orthoclase = result.minerals["or"]
    remaining_leucite = result.minerals["lc"]
    kaliophilite_formed = result.minerals.get("kp", 0.0)

    assert remaining_orthoclase == pytest.approx(
        initial_orthoclase - converted_rule25,
        abs=TOLERANCE,
    )

    assert kaliophilite_formed == pytest.approx(
        converted_rule28,
        abs=TOLERANCE,
    )

    assert remaining_leucite == pytest.approx(
        converted_rule25 - converted_rule28,
        abs=TOLERANCE,
    )

    # Independent initial elemental composition.
    initial_atoms = orthoclase_atoms(initial_orthoclase)

    # Rule 25 releases 2 SiO2 per orthoclase unit converted.
    # Rule 28 releases another 2 SiO2 per leucite unit converted.
    silica_released = (
        2.0 * converted_rule25
        + 2.0 * converted_rule28
    )

    product_atoms = add_atoms(
        orthoclase_atoms(remaining_orthoclase),
        leucite_atoms(remaining_leucite),
        kaliophilite_atoms(kaliophilite_formed),
        silica_atoms(silica_released),
    )

    for element in ("K", "Al", "Si", "O"):
        assert product_atoms[element] == pytest.approx(
            initial_atoms[element],
            abs=TOLERANCE,
        )

    # Both transformations must account for the complete
    # decrease in silica deficiency.
    assert (
        initial_deficiency - result.final_deficiency
    ) == pytest.approx(
        silica_released,
        abs=TOLERANCE,
    )


def test_rule28_does_not_consume_preexisting_leucite():
    initial_orthoclase = 0.1
    initial_leucite = 0.03

    result = redistribute_silica(
        {
            "or": initial_orthoclase,
            "lc": initial_leucite,
        },
        0.40,
    )

    rule25_steps = [
        step for step in result.steps
        if step["rule"] == 25
    ]

    rule28_steps = [
        step for step in result.steps
        if step["rule"] == 28
    ]

    assert len(rule25_steps) == 1
    assert len(rule28_steps) == 1

    assert rule25_steps[0]["provisional_amount_converted"] == pytest.approx(
        0.1,
        abs=TOLERANCE,
    )

    assert rule28_steps[0]["provisional_amount_converted"] == pytest.approx(
        0.1,
        abs=TOLERANCE,
    )

    # Original leucite must remain unchanged.
    assert result.minerals["lc"] == pytest.approx(
        initial_leucite,
        abs=TOLERANCE,
    )

    assert result.minerals.get("kp", 0.0) == pytest.approx(
        0.1,
        abs=TOLERANCE,
    )


def test_rule25_and_rule28_do_not_run_without_silica_deficiency():
    result = redistribute_silica(
        {"or": 0.1},
        0.0,
    )

    executed_rules = {
        step["rule"] for step in result.steps
    }

    assert 25 not in executed_rules
    assert 28 not in executed_rules

    assert result.minerals["or"] == pytest.approx(
        0.1,
        abs=TOLERANCE,
    )

    assert result.minerals["lc"] == pytest.approx(
        0.0,
        abs=TOLERANCE,
    )

    assert result.minerals.get("kp", 0.0) == pytest.approx(
        0.0,
        abs=TOLERANCE,
    )

    assert result.final_deficiency == pytest.approx(
        0.0,
        abs=TOLERANCE,
    )
