import pytest

from src.norm_calculation import (
    calculate_cipw_norm,
    OptionalComponentsIncompleteError,
)
from src.optional_components import OPTIONAL_COMPONENTS


def make_optional_measurements():
    """Return explicit measured-zero records for all optional components."""

    return {
        component: {
            "status": "measured_zero",
            "value_wt_percent": 0.0,
        }
        for component in OPTIONAL_COMPONENTS
    }


def make_pure_silica_composition():
    """Return a pure silica composition."""

    return {
        "SiO2": 100.0,
        "TiO2": 0.0,
        "Al2O3": 0.0,
        "Fe2O3": 0.0,
        "FeO": 0.0,
        "MnO": 0.0,
        "MgO": 0.0,
        "CaO": 0.0,
        "Na2O": 0.0,
        "K2O": 0.0,
        "P2O5": 0.0,
    }


def test_pure_silica_calculation_completes():
    result = calculate_cipw_norm(
        make_pure_silica_composition(),
        make_optional_measurements(),
    )

    assert result.status == "COMPLETED"
    assert result.mass_balance.balanced is True
    assert result.final_minerals["q"] > 0


def test_pure_silica_norm_contains_quartz():
    result = calculate_cipw_norm(
        make_pure_silica_composition(),
        make_optional_measurements(),
    )

    assert "q" in result.mineral_masses
    assert "q" in result.mineral_wt_percent
    assert result.mineral_wt_percent["q"] == pytest.approx(100.0)


def test_normalized_mineral_percentages_sum_to_100():
    result = calculate_cipw_norm(
        make_pure_silica_composition(),
        make_optional_measurements(),
    )

    assert sum(result.mineral_wt_percent.values()) == pytest.approx(
        100.0
    )


def test_unmeasured_optional_component_blocks_calculation():
    optional = make_optional_measurements()

    optional["NiO"] = {
        "status": "not_measured",
        "value_wt_percent": None,
    }

    with pytest.raises(OptionalComponentsIncompleteError):
        calculate_cipw_norm(
            make_pure_silica_composition(),
            optional,
        )


def test_explicit_zero_assumption_produces_conditional_result():
    optional = make_optional_measurements()

    optional["NiO"] = {
        "status": "not_measured",
        "value_wt_percent": None,
    }

    result = calculate_cipw_norm(
        make_pure_silica_composition(),
        optional,
        assume_unmeasured_zero=True,
    )

    assert result.conditional is True
    assert result.status == "CONDITIONAL"
    assert result.optional_component_moles["NiO"] == 0.0


def test_provisional_and_redistributed_results_are_retained():
    result = calculate_cipw_norm(
        make_pure_silica_composition(),
        make_optional_measurements(),
    )

    assert result.provisional_result is not None
    assert result.redistribution_result is not None
    assert result.provisional_result.minerals["q"] > 0
    assert result.redistribution_result.minerals["q"] > 0


def test_mass_balance_result_is_retained():
    result = calculate_cipw_norm(
        make_pure_silica_composition(),
        make_optional_measurements(),
    )

    assert result.mass_balance.status == "BALANCED"
    assert result.mass_balance.max_non_silica_error <= 1e-8
    assert abs(result.mass_balance.silica_error) <= 1e-8


def test_invalid_sulfur_basis_is_rejected():
    with pytest.raises(ValueError, match="sulfur_basis"):
        calculate_cipw_norm(
            make_pure_silica_composition(),
            make_optional_measurements(),
            sulfur_basis="invalid",
        )


def test_invalid_carbonate_mode_is_rejected():
    with pytest.raises(ValueError, match="carbonate_mode"):
        calculate_cipw_norm(
            make_pure_silica_composition(),
            make_optional_measurements(),
            carbonate_mode="invalid",
        )


def test_volatile_free_normalization_scales_optional_components():
    composition = make_pure_silica_composition()
    composition["SiO2"] = 95.0

    optional = make_optional_measurements()

    optional["NiO"] = {
        "status": "measured",
        "value_wt_percent": 0.1,
    }

    result = calculate_cipw_norm(
        composition,
        optional,
        volatile_free=True,
    )

    expected_factor = 100.0 / 95.0

    raw_ni_moles = (
        result.optional_component_conversion
        .molecular_proportions["NiO"]
    )

    assert result.optional_normalization_factor == pytest.approx(
        expected_factor
    )

    assert result.optional_component_moles["NiO"] == pytest.approx(
        raw_ni_moles * expected_factor
    )


def test_normal_calculation_does_not_scale_optional_components():
    optional = make_optional_measurements()

    optional["NiO"] = {
        "status": "measured",
        "value_wt_percent": 0.1,
    }

    result = calculate_cipw_norm(
        make_pure_silica_composition(),
        optional,
        volatile_free=False,
    )

    raw_ni_moles = (
        result.optional_component_conversion
        .molecular_proportions["NiO"]
    )

    assert result.optional_normalization_factor == pytest.approx(1.0)

    assert result.optional_component_moles["NiO"] == pytest.approx(
        raw_ni_moles
    )


def test_kelsey_apatite_fluorine_is_carried_into_final_mineral_mass():
    composition = make_pure_silica_composition()
    composition.update({
        "SiO2": 90.0,
        "CaO": 10.0,
        "P2O5": 1.0,
    })

    optional = make_optional_measurements()
    optional["F"] = {
        "status": "measured",
        "value_wt_percent": 0.01,
    }

    result = calculate_cipw_norm(composition, optional)

    apatite = result.final_minerals["ap"]
    fluorine_in_apatite = result.provisional_result.apatite_fluorine_amount
    fluorine_limit = apatite / 3.0

    assert apatite > 0
    assert 0 < fluorine_in_apatite < fluorine_limit
    assert result.mass_balance.balanced

    from config.oxide_config import OXIDE_CONFIG
    from src.mineral_formula_weights import ATOMIC_WEIGHTS

    base_formula_mass = (
        (10.0 / 3.0) * OXIDE_CONFIG["CaO"]["molecular_weight"]
        + OXIDE_CONFIG["P2O5"]["molecular_weight"]
    )
    fluorine_fraction = fluorine_in_apatite / apatite
    expected_mass = apatite * (
        base_formula_mass
        + fluorine_fraction
        * (ATOMIC_WEIGHTS["F"] - ATOMIC_WEIGHTS["O"])
    )

    assert result.mineral_masses["ap"] == pytest.approx(expected_mass)
