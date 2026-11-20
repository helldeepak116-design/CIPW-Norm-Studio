
import pytest

from src.kelsey_silica_deficiency import redistribute_silica


TOLERANCE = 1e-10


# Independent elemental formula vectors.
#
# Diopside:
# Ca(Mg,Fe)Si2O6
#
# Dicalcium silicate:
# Ca2SiO4
#
# Olivine:
# (Mg,Fe)2SiO4
#
# Liberated silica:
# SiO2
#
# These helpers deliberately do not import the application's
# mineral formula or mass-balance functions.


def diopside_atoms(amount, mg_fraction, fe_fraction):
    return {
        "Ca": amount,
        "Mg": amount * mg_fraction,
        "Fe": amount * fe_fraction,
        "Si": amount * 2.0,
        "O": amount * 6.0,
    }


def dicalcium_silicate_atoms(amount):
    return {
        "Ca": amount * 2.0,
        "Mg": 0.0,
        "Fe": 0.0,
        "Si": amount,
        "O": amount * 4.0,
    }


def olivine_atoms(amount, mg_fraction, fe_fraction):
    return {
        "Ca": 0.0,
        "Mg": amount * 2.0 * mg_fraction,
        "Fe": amount * 2.0 * fe_fraction,
        "Si": amount,
        "O": amount * 4.0,
    }


def silica_atoms(amount):
    return {
        "Ca": 0.0,
        "Mg": 0.0,
        "Fe": 0.0,
        "Si": amount,
        "O": amount * 2.0,
    }


def add_atoms(*vectors):
    elements = ("Ca", "Mg", "Fe", "Si", "O")

    return {
        element: sum(vector[element] for vector in vectors)
        for element in elements
    }


@pytest.mark.parametrize(
    ("mg_fraction", "fe_fraction"),
    [
        (1.00, 0.00),  # Forsterite end-member.
        (0.75, 0.25),  # Mg-rich olivine.
        (0.50, 0.50),  # Equal Mg-Fe partition.
        (0.25, 0.75),  # Fe-rich olivine.
        (0.00, 1.00),  # Fayalite end-member.
    ],
)
@pytest.mark.parametrize(
    ("initial_deficiency", "expected_converted"),
    [
        (0.04, 0.04),  # Partial diopside conversion.
        (0.10, 0.10),  # Complete conversion at exact capacity.
        (0.15, 0.10),  # Diopside exhausted; deficiency remains.
    ],
)
def test_rule27_independent_elemental_conservation(
    mg_fraction,
    fe_fraction,
    initial_deficiency,
    expected_converted,
):
    initial_diopside = 0.1

    assert mg_fraction + fe_fraction == pytest.approx(1.0)

    result = redistribute_silica(
        {"di": initial_diopside},
        initial_deficiency,
    )

    rule27_steps = [
        step for step in result.steps
        if step["rule"] == 27
    ]

    assert len(rule27_steps) == 1

    converted = rule27_steps[0]["provisional_amount_converted"]

    remaining_diopside = result.minerals["di"]
    dicalcium_silicate_formed = result.minerals["cs"]
    olivine_formed = result.minerals["ol"]

    assert converted == pytest.approx(
        expected_converted,
        abs=TOLERANCE,
    )

    # Rule 27 forms equal molecular amounts of Cs and Ol.
    assert dicalcium_silicate_formed == pytest.approx(
        converted / 2.0,
        abs=TOLERANCE,
    )

    assert olivine_formed == pytest.approx(
        converted / 2.0,
        abs=TOLERANCE,
    )

    assert remaining_diopside == pytest.approx(
        initial_diopside - converted,
        abs=TOLERANCE,
    )

    # Independently calculate the initial elemental inventory.
    initial_atoms = diopside_atoms(
        initial_diopside,
        mg_fraction,
        fe_fraction,
    )

    # Independently calculate the final elemental inventory:
    # remaining diopside + dicalcium silicate + olivine + silica.
    product_atoms = add_atoms(
        diopside_atoms(
            remaining_diopside,
            mg_fraction,
            fe_fraction,
        ),
        dicalcium_silicate_atoms(
            dicalcium_silicate_formed,
        ),
        olivine_atoms(
            olivine_formed,
            mg_fraction,
            fe_fraction,
        ),
        silica_atoms(converted),
    )

    for element in ("Ca", "Mg", "Fe", "Si", "O"):
        assert product_atoms[element] == pytest.approx(
            initial_atoms[element],
            abs=TOLERANCE,
        ), (
            f"{element} is not conserved: "
            f"initial={initial_atoms[element]}, "
            f"final={product_atoms[element]}"
        )

    # One mole-equivalent of diopside releases one SiO2.
    silica_released = converted

    assert (
        initial_deficiency - result.final_deficiency
    ) == pytest.approx(
        silica_released,
        abs=TOLERANCE,
    )

    assert result.final_deficiency == pytest.approx(
        max(0.0, initial_deficiency - converted),
        abs=TOLERANCE,
    )


def test_rule27_does_not_run_without_silica_deficiency():
    initial_diopside = 0.1

    result = redistribute_silica(
        {"di": initial_diopside},
        0.0,
    )

    rule27_steps = [
        step for step in result.steps
        if step["rule"] == 27
    ]

    assert rule27_steps == []

    assert result.minerals["di"] == pytest.approx(
        initial_diopside,
        abs=TOLERANCE,
    )

    assert result.minerals.get("cs", 0.0) == pytest.approx(
        0.0,
        abs=TOLERANCE,
    )

    assert result.minerals.get("ol", 0.0) == pytest.approx(
        0.0,
        abs=TOLERANCE,
    )

    assert result.final_deficiency == pytest.approx(
        0.0,
        abs=TOLERANCE,
    )
