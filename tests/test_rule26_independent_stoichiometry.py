
import pytest

from src.kelsey_silica_deficiency import redistribute_silica


TOLERANCE = 1e-10


# Independent elemental formula vectors.
#
# Wollastonite (wo): CaSiO3
# Dicalcium silicate (cs): Ca2SiO4
# Silica: SiO2
#
# Rule 26:
#     CaSiO3 -> 0.5 Ca2SiO4 + 0.5 SiO2
#
# One normative wollastonite unit produces:
#     0.5 normative dicalcium silicate
#     0.5 silica equivalents
#
# These vectors are independently defined and do not import
# the application's mineral formula or mass-balance functions.


def wollastonite_atoms(amount):
    return {
        "Ca": amount,
        "Si": amount,
        "O": amount * 3.0,
    }


def dicalcium_silicate_atoms(amount):
    return {
        "Ca": amount * 2.0,
        "Si": amount,
        "O": amount * 4.0,
    }


def silica_atoms(amount):
    return {
        "Ca": 0.0,
        "Si": amount,
        "O": amount * 2.0,
    }


def add_atoms(*vectors):
    elements = {"Ca", "Si", "O"}

    return {
        element: sum(vector[element] for vector in vectors)
        for element in elements
    }


@pytest.mark.parametrize(
    ("initial_deficiency", "expected_converted"),
    [
        (0.025, 0.05),  # Partial wollastonite conversion.
        (0.05, 0.10),   # Complete conversion at exact capacity.
        (0.08, 0.10),   # Wollastonite exhausted; deficiency remains.
    ],
)
def test_rule26_independent_elemental_conservation(
    initial_deficiency,
    expected_converted,
):
    initial_wollastonite = 0.1

    result = redistribute_silica(
        {"wo": initial_wollastonite},
        initial_deficiency,
    )

    rule26_steps = [
        step for step in result.steps
        if step["rule"] == 26
    ]

    assert len(rule26_steps) == 1

    converted = (
        rule26_steps[0]["provisional_amount_converted"]
    )

    dicalcium_silicate_formed = result.minerals["cs"]
    remaining_wollastonite = result.minerals["wo"]

    # Verify the amount converted.
    assert converted == pytest.approx(
        expected_converted,
        abs=TOLERANCE,
    )

    # One wollastonite unit produces half a dicalcium
    # silicate unit.
    assert dicalcium_silicate_formed == pytest.approx(
        converted / 2.0,
        abs=TOLERANCE,
    )

    assert remaining_wollastonite == pytest.approx(
        initial_wollastonite - converted,
        abs=TOLERANCE,
    )

    # Independently calculate the initial elemental composition.
    initial_atoms = wollastonite_atoms(initial_wollastonite)

    # Account for remaining wollastonite, formed dicalcium
    # silicate, and liberated silica.
    silica_released = converted / 2.0

    product_atoms = add_atoms(
        wollastonite_atoms(remaining_wollastonite),
        dicalcium_silicate_atoms(dicalcium_silicate_formed),
        silica_atoms(silica_released),
    )

    # Verify conservation of Ca, Si and O.
    for element in ("Ca", "Si", "O"):
        assert product_atoms[element] == pytest.approx(
            initial_atoms[element],
            abs=TOLERANCE,
        )

    # Verify silica release against the reduction in deficiency.
    assert (
        initial_deficiency - result.final_deficiency
    ) == pytest.approx(
        silica_released,
        abs=TOLERANCE,
    )


def test_rule26_does_not_run_without_silica_deficiency():
    result = redistribute_silica(
        {"wo": 0.1},
        0.0,
    )

    rule26_steps = [
        step for step in result.steps
        if step["rule"] == 26
    ]

    assert rule26_steps == []

    assert result.minerals["wo"] == pytest.approx(
        0.1,
        abs=TOLERANCE,
    )

    assert result.minerals.get("cs", 0.0) == pytest.approx(
        0.0,
        abs=TOLERANCE,
    )

    assert result.final_deficiency == pytest.approx(
        0.0,
        abs=TOLERANCE,
    )
