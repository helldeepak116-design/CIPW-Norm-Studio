
import pytest

from src.kelsey_silica_deficiency import redistribute_silica


TOLERANCE = 1e-10

INITIAL_MINERALS = {
    "hy": 0.1,
    "tn": 0.1,
    "ab": 0.1,
    "or": 0.1,
    "wo": 0.1,
    "di": 0.1,
}

INITIAL_DEFICIENCY = 2.0

ELEMENTS = ("Ca", "Mg", "Fe", "Al", "Na", "K", "Ti", "Si", "O")


# ---------------------------------------------------------------------
# Independent elemental formula vectors
#
# Important:
# Albite, orthoclase, nepheline, leucite and kaliophilite use
# oxide molecular-proportion units, consistent with the engine's
# normative mineral amounts.
#
# No application mass-balance or mineral-equivalent functions
# are imported or used here.
# ---------------------------------------------------------------------


def hypersthene_atoms(amount, mg_fraction, fe_fraction):
    # (Mg,Fe)SiO3
    return {
        "Ca": 0.0,
        "Mg": amount * mg_fraction,
        "Fe": amount * fe_fraction,
        "Al": 0.0,
        "Na": 0.0,
        "K": 0.0,
        "Ti": 0.0,
        "Si": amount,
        "O": amount * 3.0,
    }


def olivine_atoms(amount, mg_fraction, fe_fraction):
    # (Mg,Fe)2SiO4
    return {
        "Ca": 0.0,
        "Mg": amount * 2.0 * mg_fraction,
        "Fe": amount * 2.0 * fe_fraction,
        "Al": 0.0,
        "Na": 0.0,
        "K": 0.0,
        "Ti": 0.0,
        "Si": amount,
        "O": amount * 4.0,
    }


def sphene_atoms(amount):
    # CaTiSiO5
    return {
        "Ca": amount,
        "Mg": 0.0,
        "Fe": 0.0,
        "Al": 0.0,
        "Na": 0.0,
        "K": 0.0,
        "Ti": amount,
        "Si": amount,
        "O": amount * 5.0,
    }


def perovskite_atoms(amount):
    # CaTiO3
    return {
        "Ca": amount,
        "Mg": 0.0,
        "Fe": 0.0,
        "Al": 0.0,
        "Na": 0.0,
        "K": 0.0,
        "Ti": amount,
        "Si": 0.0,
        "O": amount * 3.0,
    }


def albite_atoms(amount):
    # Na2O . Al2O3 . 6SiO2
    # Na2Al2Si6O16
    return {
        "Ca": 0.0,
        "Mg": 0.0,
        "Fe": 0.0,
        "Al": amount * 2.0,
        "Na": amount * 2.0,
        "K": 0.0,
        "Ti": 0.0,
        "Si": amount * 6.0,
        "O": amount * 16.0,
    }


def nepheline_atoms(amount):
    # Na2O . Al2O3 . 2SiO2
    # Na2Al2Si2O8
    return {
        "Ca": 0.0,
        "Mg": 0.0,
        "Fe": 0.0,
        "Al": amount * 2.0,
        "Na": amount * 2.0,
        "K": 0.0,
        "Ti": 0.0,
        "Si": amount * 2.0,
        "O": amount * 8.0,
    }


def orthoclase_atoms(amount):
    # K2O . Al2O3 . 6SiO2
    # K2Al2Si6O16
    return {
        "Ca": 0.0,
        "Mg": 0.0,
        "Fe": 0.0,
        "Al": amount * 2.0,
        "Na": 0.0,
        "K": amount * 2.0,
        "Ti": 0.0,
        "Si": amount * 6.0,
        "O": amount * 16.0,
    }


def leucite_atoms(amount):
    # K2O . Al2O3 . 4SiO2
    # K2Al2Si4O12
    return {
        "Ca": 0.0,
        "Mg": 0.0,
        "Fe": 0.0,
        "Al": amount * 2.0,
        "Na": 0.0,
        "K": amount * 2.0,
        "Ti": 0.0,
        "Si": amount * 4.0,
        "O": amount * 12.0,
    }


def kaliophilite_atoms(amount):
    # K2O . Al2O3 . 2SiO2
    # K2Al2Si2O8
    return {
        "Ca": 0.0,
        "Mg": 0.0,
        "Fe": 0.0,
        "Al": amount * 2.0,
        "Na": 0.0,
        "K": amount * 2.0,
        "Ti": 0.0,
        "Si": amount * 2.0,
        "O": amount * 8.0,
    }


def wollastonite_atoms(amount):
    # CaSiO3
    return {
        "Ca": amount,
        "Mg": 0.0,
        "Fe": 0.0,
        "Al": 0.0,
        "Na": 0.0,
        "K": 0.0,
        "Ti": 0.0,
        "Si": amount,
        "O": amount * 3.0,
    }


def dicalcium_silicate_atoms(amount):
    # Ca2SiO4
    return {
        "Ca": amount * 2.0,
        "Mg": 0.0,
        "Fe": 0.0,
        "Al": 0.0,
        "Na": 0.0,
        "K": 0.0,
        "Ti": 0.0,
        "Si": amount,
        "O": amount * 4.0,
    }


def diopside_atoms(amount, mg_fraction, fe_fraction):
    # Ca(Mg,Fe)Si2O6
    return {
        "Ca": amount,
        "Mg": amount * mg_fraction,
        "Fe": amount * fe_fraction,
        "Al": 0.0,
        "Na": 0.0,
        "K": 0.0,
        "Ti": 0.0,
        "Si": amount * 2.0,
        "O": amount * 6.0,
    }


def silica_atoms(amount):
    # SiO2
    return {
        "Ca": 0.0,
        "Mg": 0.0,
        "Fe": 0.0,
        "Al": 0.0,
        "Na": 0.0,
        "K": 0.0,
        "Ti": 0.0,
        "Si": amount,
        "O": amount * 2.0,
    }


def add_atoms(*vectors):
    return {
        element: sum(vector[element] for vector in vectors)
        for element in ELEMENTS
    }


def mineral_inventory(minerals, mg_fraction, fe_fraction):
    """Calculate an independent elemental inventory of all minerals."""

    return add_atoms(
        hypersthene_atoms(
            minerals.get("hy", 0.0),
            mg_fraction,
            fe_fraction,
        ),
        olivine_atoms(
            minerals.get("ol", 0.0),
            mg_fraction,
            fe_fraction,
        ),
        sphene_atoms(minerals.get("tn", 0.0)),
        perovskite_atoms(minerals.get("pf", 0.0)),
        albite_atoms(minerals.get("ab", 0.0)),
        nepheline_atoms(minerals.get("ne", 0.0)),
        orthoclase_atoms(minerals.get("or", 0.0)),
        leucite_atoms(minerals.get("lc", 0.0)),
        kaliophilite_atoms(minerals.get("kp", 0.0)),
        wollastonite_atoms(minerals.get("wo", 0.0)),
        dicalcium_silicate_atoms(minerals.get("cs", 0.0)),
        diopside_atoms(
            minerals.get("di", 0.0),
            mg_fraction,
            fe_fraction,
        ),
    )


def independent_silica_release(result):
    """Calculate silica released using reaction-specific coefficients."""

    release_coefficients = {
        22: 0.5,
        23: 1.0,
        24: 4.0,
        25: 2.0,
        26: 0.5,
        27: 1.0,
        28: 2.0,
    }

    return sum(
        step["provisional_amount_converted"]
        * release_coefficients[step["rule"]]
        for step in result.steps
    )


# ---------------------------------------------------------------------
# Integrated Rules 22-28 validation
# ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("mg_fraction", "fe_fraction"),
    [
        (1.00, 0.00),
        (0.75, 0.25),
        (0.50, 0.50),
        (0.25, 0.75),
        (0.00, 1.00),
    ],
)
def test_rules22_to_28_independent_elemental_conservation(
    mg_fraction,
    fe_fraction,
):
    assert mg_fraction + fe_fraction == pytest.approx(1.0)

    result = redistribute_silica(
        INITIAL_MINERALS,
        INITIAL_DEFICIENCY,
    )

    # All seven rules must execute in their prescribed order.
    assert [step["rule"] for step in result.steps] == [
        22, 23, 24, 25, 26, 27, 28
    ]

    # Independently calculate the initial elemental inventory.
    initial_atoms = mineral_inventory(
        INITIAL_MINERALS,
        mg_fraction,
        fe_fraction,
    )

    # Independently calculate the final mineral inventory.
    final_atoms = mineral_inventory(
        result.minerals,
        mg_fraction,
        fe_fraction,
    )

    # Calculate silica released by each reaction independently.
    silica_released = independent_silica_release(result)

    # Add liberated silica to the final mineral inventory.
    final_with_liberated_silica = add_atoms(
        final_atoms,
        silica_atoms(silica_released),
    )

    # Every tracked element must be conserved.
    for element in ELEMENTS:
        assert final_with_liberated_silica[element] == pytest.approx(
            initial_atoms[element],
            abs=TOLERANCE,
        ), (
            f"{element} conservation failed: "
            f"initial={initial_atoms[element]}, "
            f"final={final_with_liberated_silica[element]}"
        )

    # Verify the independently calculated silica release.
    assert silica_released == pytest.approx(1.1, abs=TOLERANCE)

    assert result.initial_deficiency == pytest.approx(
        INITIAL_DEFICIENCY,
        abs=TOLERANCE,
    )

    assert result.final_deficiency == pytest.approx(
        0.9,
        abs=TOLERANCE,
    )

    assert (
        result.initial_deficiency - result.final_deficiency
    ) == pytest.approx(
        silica_released,
        abs=TOLERANCE,
    )

    # This input intentionally leaves residual silica deficiency.
    assert result.status == "UNRESOLVED_DEFICIENCY"


def test_rules22_to_28_independent_final_mineral_amounts():
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

    for mineral, expected_amount in expected.items():
        assert result.minerals[mineral] == pytest.approx(
            expected_amount,
            abs=TOLERANCE,
        )

    assert result.lc_prime_remaining == pytest.approx(
        0.0,
        abs=TOLERANCE,
    )


def test_rules22_to_28_independent_silica_release_accounting():
    result = redistribute_silica(
        INITIAL_MINERALS,
        INITIAL_DEFICIENCY,
    )

    expected_by_rule = {
        22: 0.05,
        23: 0.10,
        24: 0.40,
        25: 0.20,
        26: 0.05,
        27: 0.10,
        28: 0.20,
    }

    for step in result.steps:
        rule = step["rule"]
        converted = step["provisional_amount_converted"]

        expected_release = expected_by_rule[rule]

        coefficients = {
            22: 0.5,
            23: 1.0,
            24: 4.0,
            25: 2.0,
            26: 0.5,
            27: 1.0,
            28: 2.0,
        }

        assert converted * coefficients[rule] == pytest.approx(
            expected_release,
            abs=TOLERANCE,
        )

    assert independent_silica_release(result) == pytest.approx(
        1.1,
        abs=TOLERANCE,
    )
