import pytest

from src.cipw_engine import (
    allocate_stoichiometric_reaction,
    calculate_cipw_norm,
    molecular_proportions,
)


@pytest.fixture
def composition():
    return {
        "SiO2": 50.0,
        "TiO2": 1.0,
        "Al2O3": 15.0,
        "Fe2O3": 2.0,
        "FeO": 8.0,
        "MnO": 0.1,
        "MgO": 7.0,
        "CaO": 10.0,
        "Na2O": 3.0,
        "K2O": 2.0,
        "P2O5": 1.0,
    }


def test_molecular_proportions(composition):
    result = molecular_proportions(composition)
    assert result["SiO2"] == pytest.approx(50 / 60.0843)


def test_measured_iron_retained_separately(composition):
    result = molecular_proportions(composition)
    assert result["FeO"] == pytest.approx(8 / 71.8440)
    assert result["Fe2O3"] == pytest.approx(2 / 159.6882)


def test_reaction_allocation():
    available = {"CaO": 3.0, "P2O5": 1.0}
    coefficients = {"CaO": 3.0, "P2O5": 1.0}

    extent, remaining = allocate_stoichiometric_reaction(
        available, coefficients
    )

    assert extent == pytest.approx(1.0)
    assert remaining["CaO"] == pytest.approx(0.0)
    assert remaining["P2O5"] == pytest.approx(0.0)


def test_reaction_limiting_reactant():
    available = {"CaO": 3.0, "P2O5": 0.5}
    coefficients = {"CaO": 3.0, "P2O5": 1.0}

    extent, remaining = allocate_stoichiometric_reaction(
        available, coefficients
    )

    assert extent == pytest.approx(0.5)
    assert remaining["CaO"] == pytest.approx(1.5)


def test_reaction_rejects_missing_reactant():
    with pytest.raises(ValueError):
        allocate_stoichiometric_reaction(
            {"CaO": 1.0},
            {"P2O5": 1.0},
        )


def test_no_false_normative_output(composition):
    result = calculate_cipw_norm(composition)

    assert result.status == "FOUNDATION_ONLY"
    assert result.normative_minerals == {}
    assert result.warnings
