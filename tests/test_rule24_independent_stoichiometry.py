
import pytest

from src.kelsey_silica_deficiency import redistribute_silica


TOLERANCE = 1e-10


# Independent elemental formula vectors.
#
# CIPW normative molecular-amount convention:
# One normative albite (ab) unit represents:
#     Na2O + Al2O3 + 6SiO2
#     equivalent to 2 NaAlSi3O8 formula units.
#
# One normative nepheline (ne) unit represents:
#     Na2O + Al2O3 + 2SiO2
#     equivalent to 2 NaAlSiO4 formula units.
#
# Therefore, the Rule 24 transformation is:
#
#     2 NaAlSi3O8 -> 2 NaAlSiO4 + 4 SiO2
#
# In normative molecular-amount units:
#
#     1 ab -> 1 ne + 4 SiO2
#
# These vectors are independently defined and do not import
# the application's mineral formula or mass-balance functions.


def albite_atoms(amount):
    """Elemental composition of normative albite."""
    return {
        "Na": amount * 2.0,
        "Al": amount * 2.0,
        "Si": amount * 6.0,
        "O": amount * 16.0,
    }


def nepheline_atoms(amount):
    """Elemental composition of normative nepheline."""
    return {
        "Na": amount * 2.0,
        "Al": amount * 2.0,
        "Si": amount * 2.0,
        "O": amount * 8.0,
    }


def silica_atoms(amount):
    """Elemental composition of silica."""
    return {
        "Na": 0.0,
        "Al": 0.0,
        "Si": amount,
        "O": amount * 2.0,
    }


def add_atoms(*vectors):
    """Sum independent elemental composition vectors."""
    elements = {"Na", "Al", "Si", "O"}

    return {
        element: sum(vector[element] for vector in vectors)
        for element in elements
    }


@pytest.mark.parametrize(
    ("initial_deficiency", "expected_converted"),
    [
        (0.20, 0.05),  # Partial albite conversion.
        (0.40, 0.10),  # Complete conversion at exact capacity.
        (0.60, 0.10),  # Albite exhausted; deficiency remains.
    ],
)
def test_rule24_independent_elemental_conservation(
    initial_deficiency,
    expected_converted,
):
    initial_albite = 0.1

    result = redistribute_silica(
        {"ab": initial_albite},
        initial_deficiency,
    )

    # Verify that Rule 24 was executed exactly once.
    rule24_steps = [
        step for step in result.steps
        if step["rule"] == 24
    ]

    assert len(rule24_steps) == 1

    converted = rule24_steps[0]["provisional_amount_converted"]

    nepheline_formed = result.minerals["ne"]
    remaining_albite = result.minerals["ab"]

    # Verify the amount converted.
    assert converted == pytest.approx(
        expected_converted,
        abs=TOLERANCE,
    )

    # One normative albite unit produces one normative nepheline unit.
    assert nepheline_formed == pytest.approx(
        converted,
        abs=TOLERANCE,
    )

    # Verify the remaining albite.
    assert remaining_albite == pytest.approx(
        initial_albite - converted,
        abs=TOLERANCE,
    )

    # Independently calculate the initial elemental composition.
    initial_atoms = albite_atoms(initial_albite)

    # Independently calculate the final elemental composition:
    # remaining albite + formed nepheline + liberated silica.
    product_atoms = add_atoms(
        albite_atoms(remaining_albite),
        nepheline_atoms(nepheline_formed),
        silica_atoms(4.0 * converted),
    )

    # Verify conservation of Na, Al, Si and O.
    for element in ("Na", "Al", "Si", "O"):
        assert product_atoms[element] == pytest.approx(
            initial_atoms[element],
            abs=TOLERANCE,
        )

    # Rule 24 releases four silica equivalents per normative
    # albite unit converted.
    silica_released = 4.0 * converted

    assert (
        initial_deficiency - result.final_deficiency
    ) == pytest.approx(
        silica_released,
        abs=TOLERANCE,
    )


def test_rule24_does_not_run_without_silica_deficiency():
    result = redistribute_silica(
        {"ab": 0.1},
        0.0,
    )

    rule24_steps = [
        step for step in result.steps
        if step["rule"] == 24
    ]

    assert rule24_steps == []

    assert result.minerals["ab"] == pytest.approx(
        0.1,
        abs=TOLERANCE,
    )

    assert result.minerals.get("ne", 0.0) == pytest.approx(
        0.0,
        abs=TOLERANCE,
    )

    assert result.final_deficiency == pytest.approx(
        0.0,
        abs=TOLERANCE,
    )
