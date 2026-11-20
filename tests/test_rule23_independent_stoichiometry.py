
import pytest

from src.kelsey_silica_deficiency import redistribute_silica


TOLERANCE = 1e-10


# Independent elemental formula vectors.
# Sphene:     CaTiSiO5
# Perovskite: CaTiO3
# Silica:     SiO2
#
# These deliberately do not import the application's
# mineral formula or mass-balance functions.

def sphene_atoms(amount):
    return {
        "Ca": amount,
        "Ti": amount,
        "Si": amount,
        "O": amount * 5.0,
    }


def perovskite_atoms(amount):
    return {
        "Ca": amount,
        "Ti": amount,
        "Si": 0.0,
        "O": amount * 3.0,
    }


def silica_atoms(amount):
    return {
        "Ca": 0.0,
        "Ti": 0.0,
        "Si": amount,
        "O": amount * 2.0,
    }


def add_atoms(*vectors):
    elements = {"Ca", "Ti", "Si", "O"}
    return {
        element: sum(vector[element] for vector in vectors)
        for element in elements
    }


@pytest.mark.parametrize(
    ("initial_deficiency", "expected_converted"),
    [
        (0.04, 0.04),  # Partial sphene conversion.
        (0.10, 0.10),  # Complete conversion at exact capacity.
        (0.15, 0.10),  # Sphene exhausted; deficiency remains.
    ],
)
def test_rule23_independent_elemental_conservation(
    initial_deficiency,
    expected_converted,
):
    initial_sphene = 0.1

    result = redistribute_silica(
        {"tn": initial_sphene},
        initial_deficiency,
    )

    rule23_steps = [
        step for step in result.steps
        if step["rule"] == 23
    ]

    assert len(rule23_steps) == 1

    converted = rule23_steps[0]["provisional_amount_converted"]
    perovskite_formed = result.minerals["pf"]
    remaining_sphene = result.minerals["tn"]

    assert converted == pytest.approx(
        expected_converted,
        abs=TOLERANCE,
    )

    assert perovskite_formed == pytest.approx(
        converted,
        abs=TOLERANCE,
    )

    assert remaining_sphene == pytest.approx(
        initial_sphene - converted,
        abs=TOLERANCE,
    )

    # Independently calculate elemental composition before conversion.
    initial_atoms = sphene_atoms(initial_sphene)

    # Account for remaining sphene, formed perovskite,
    # and liberated silica.
    product_atoms = add_atoms(
        sphene_atoms(remaining_sphene),
        perovskite_atoms(perovskite_formed),
        silica_atoms(converted),
    )

    for element in ("Ca", "Ti", "Si", "O"):
        assert product_atoms[element] == pytest.approx(
            initial_atoms[element],
            abs=TOLERANCE,
        )

    # One mole-equivalent of sphene releases one SiO2
    # and therefore reduces deficiency by one.
    silica_released = converted

    assert (
        initial_deficiency - result.final_deficiency
    ) == pytest.approx(
        silica_released,
        abs=TOLERANCE,
    )


def test_rule23_does_not_run_without_silica_deficiency():
    result = redistribute_silica(
        {"tn": 0.1},
        0.0,
    )

    rule23_steps = [
        step for step in result.steps
        if step["rule"] == 23
    ]

    assert rule23_steps == []
    assert result.minerals["tn"] == pytest.approx(0.1)
    assert result.minerals.get("pf", 0.0) == pytest.approx(0.0)
    assert result.final_deficiency == pytest.approx(0.0)
