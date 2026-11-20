import pytest

from src.kelsey_silica_deficiency import redistribute_silica


TOLERANCE = 1e-10

# Independent elemental formula vectors.
# These deliberately do not import the application's mass-balance code.
def hypersthene_atoms(amount, mg_fraction, fe_fraction):
    return {
        "Mg": amount * mg_fraction,
        "Fe": amount * fe_fraction,
        "Si": amount,
        "O": amount * 3.0,
    }


def olivine_atoms(amount, mg_fraction, fe_fraction):
    return {
        "Mg": amount * 2.0 * mg_fraction,
        "Fe": amount * 2.0 * fe_fraction,
        "Si": amount,
        "O": amount * 4.0,
    }


def silica_atoms(amount):
    return {
        "Mg": 0.0,
        "Fe": 0.0,
        "Si": amount,
        "O": amount * 2.0,
    }


def add_atoms(*vectors):
    elements = {"Mg", "Fe", "Si", "O"}
    return {
        element: sum(vector[element] for vector in vectors)
        for element in elements
    }


@pytest.mark.parametrize(
    "mg_fraction",
    [0.0, 0.25, 0.75, 1.0],
)
@pytest.mark.parametrize(
    ("initial_deficiency", "expected_converted"),
    [
        (0.02, 0.04),  # Partial conversion.
        (0.08, 0.10),  # Complete conversion; deficiency remains.
    ],
)
def test_rule22_independent_elemental_conservation(
    mg_fraction,
    initial_deficiency,
    expected_converted,
):
    fe_fraction = 1.0 - mg_fraction
    initial_hy = 0.1

    result = redistribute_silica(
        {"hy": initial_hy},
        initial_deficiency,
    )

    rule22_steps = [
        step for step in result.steps
        if step["rule"] == 22
    ]

    assert len(rule22_steps) == 1

    converted = rule22_steps[0]["provisional_amount_converted"]
    olivine_formed = result.minerals["ol"]
    remaining_hy = result.minerals["hy"]

    assert converted == pytest.approx(
        expected_converted,
        abs=TOLERANCE,
    )
    assert olivine_formed == pytest.approx(
        converted / 2.0,
        abs=TOLERANCE,
    )
    assert remaining_hy == pytest.approx(
        initial_hy - converted,
        abs=TOLERANCE,
    )

    # Independently calculate elemental composition before conversion.
    initial_atoms = hypersthene_atoms(
        initial_hy,
        mg_fraction,
        fe_fraction,
    )

    # Independently calculate the remaining hypersthene,
    # newly formed olivine, and liberated silica.
    product_atoms = add_atoms(
        hypersthene_atoms(
            remaining_hy,
            mg_fraction,
            fe_fraction,
        ),
        olivine_atoms(
            olivine_formed,
            mg_fraction,
            fe_fraction,
        ),
        silica_atoms(converted / 2.0),
    )

    for element in ("Mg", "Fe", "Si", "O"):
        assert product_atoms[element] == pytest.approx(
            initial_atoms[element],
            abs=TOLERANCE,
        )

    # Silica release must equal the decrease in deficiency.
    silica_released = converted / 2.0

    assert (
        initial_deficiency - result.final_deficiency
    ) == pytest.approx(
        silica_released,
        abs=TOLERANCE,
    )
