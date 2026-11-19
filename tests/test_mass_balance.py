from types import SimpleNamespace

import pytest

from src.mass_balance import (
    check_mass_balance,
    mineral_oxide_equivalents,
)


def zero_inputs():
    major = {
        "SiO2": 0.0, "TiO2": 0.0, "Al2O3": 0.0,
        "Fe2O3": 0.0, "FeO": 0.0, "MnO": 0.0,
        "MgO": 0.0, "CaO": 0.0, "Na2O": 0.0,
        "K2O": 0.0, "P2O5": 0.0,
    }
    optional = {
        "NiO": 0.0, "BaO": 0.0, "SrO": 0.0,
        "ZrO2": 0.0, "F": 0.0, "Cl": 0.0,
        "SO3": 0.0, "S": 0.0, "CO2": 0.0,
        "Cr2O3": 0.0,
    }
    return major, optional


def test_empty_assemblage_is_balanced():
    major, optional = zero_inputs()
    provisional = SimpleNamespace(
        minerals={},
        residual_oxides={},
        silica_deficiency=0.0,
        mg_fraction=0.0,
        fe_fraction=0.0,
    )

    result = check_mass_balance(major, optional, provisional)

    assert result.balanced
    assert result.status == "BALANCED"
    assert result.max_non_silica_error == 0.0
    assert result.silica_error == 0.0


def test_quartz_accounts_for_silica_excess():
    major, optional = zero_inputs()
    major["SiO2"] = 2.5

    provisional = SimpleNamespace(
        minerals={"q": 2.5},
        residual_oxides={"SiO2": 2.5},
        silica_deficiency=0.0,
        mg_fraction=0.0,
        fe_fraction=0.0,
    )

    result = check_mass_balance(major, optional, provisional)

    assert result.balanced
    assert result.component_differences["SiO2"] == pytest.approx(0.0)


def test_expected_silica_deficiency_is_reported_separately():
    major, optional = zero_inputs()
    major["SiO2"] = 1.0
    major["Al2O3"] = 1.0
    major["K2O"] = 1.0

    provisional = SimpleNamespace(
        minerals={"or": 1.0},
        residual_oxides={"SiO2": 1.0},
        silica_deficiency=5.0,
        mg_fraction=0.0,
        fe_fraction=0.0,
    )

    result = check_mass_balance(major, optional, provisional)

    assert result.balanced
    assert result.status == "BALANCED_WITH_UNRESOLVED_SILICA_DEFICIENCY"
    assert result.expected_silica_deficit == pytest.approx(5.0)


def test_detects_non_silica_component_imbalance():
    major, optional = zero_inputs()
    major["Al2O3"] = 1.0

    provisional = SimpleNamespace(
        minerals={},
        residual_oxides={},
        silica_deficiency=0.0,
        mg_fraction=0.0,
        fe_fraction=0.0,
    )

    result = check_mass_balance(major, optional, provisional)

    assert not result.balanced
    assert result.status == "IMBALANCE"
    assert result.component_differences["Al2O3"] == pytest.approx(1.0)


def test_mg_fe_partition_is_conserved_in_diopside():
    equivalents = mineral_oxide_equivalents(
        {"di": 2.0},
        mg_fraction=0.75,
        fe_fraction=0.25,
    )

    assert equivalents["CaO"] == pytest.approx(2.0)
    assert equivalents["MgO"] == pytest.approx(1.5)
    assert equivalents["FeO"] == pytest.approx(0.5)
    assert equivalents["SiO2"] == pytest.approx(4.0)


def test_rejects_invalid_mg_fe_fractions():
    with pytest.raises(ValueError):
        mineral_oxide_equivalents(
            {"di": 1.0},
            mg_fraction=0.8,
            fe_fraction=0.8,
        )


def test_pyrite_uses_selected_sulfur_component():
    equivalents = mineral_oxide_equivalents(
        {"pr": 0.5},
        mg_fraction=0.0,
        fe_fraction=0.0,
        sulfur_component="SO3",
    )

    assert equivalents["FeO"] == pytest.approx(0.5)
    assert equivalents["SO3"] == pytest.approx(1.0)
    assert "S" not in equivalents


def test_rejects_non_finite_mineral_amount():
    with pytest.raises(ValueError):
        mineral_oxide_equivalents(
            {"q": float("nan")},
            mg_fraction=0.0,
            fe_fraction=0.0,
        )



