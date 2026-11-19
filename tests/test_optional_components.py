
import pytest

from src.optional_components import (
    OPTIONAL_COMPONENTS,
    OPTIONAL_COMPONENT_WEIGHTS,
    convert_optional_components,
)


def make_measurements(
    *,
    default_status="measured_zero",
    default_value=0.0,
):
    return {
        component: {
            "status": default_status,
            "value_wt_percent": default_value,
        }
        for component in OPTIONAL_COMPONENTS
    }


def test_all_measured_zero_components_are_calculation_ready():
    measurements = make_measurements()

    result = convert_optional_components(measurements)

    assert result.calculation_ready is True
    assert result.conditional is False
    assert result.unmeasured_components == ()
    assert all(
        value == 0.0
        for value in result.molecular_proportions.values()
    )


def test_measured_component_converts_wt_percent_to_moles():
    measurements = make_measurements()
    measurements["NiO"] = {
        "status": "measured",
        "value_wt_percent": 0.10,
    }

    result = convert_optional_components(measurements)

    expected = 0.10 / OPTIONAL_COMPONENT_WEIGHTS["NiO"]

    assert result.molecular_proportions["NiO"] == pytest.approx(
        expected
    )


def test_elemental_fluorine_uses_atomic_weight_basis():
    measurements = make_measurements()
    measurements["F"] = {
        "status": "measured",
        "value_wt_percent": 0.20,
    }

    result = convert_optional_components(measurements)

    expected = 0.20 / OPTIONAL_COMPONENT_WEIGHTS["F"]

    assert result.molecular_proportions["F"] == pytest.approx(
        expected
    )


def test_unmeasured_component_blocks_complete_calculation():
    measurements = make_measurements()
    measurements["BaO"] = {
        "status": "not_measured",
        "value_wt_percent": None,
    }

    result = convert_optional_components(measurements)

    assert result.calculation_ready is False
    assert result.conditional is False
    assert result.molecular_proportions["BaO"] is None
    assert result.unmeasured_components == ("BaO",)


def test_explicit_zero_assumption_produces_conditional_result():
    measurements = make_measurements()
    measurements["BaO"] = {
        "status": "not_measured",
        "value_wt_percent": None,
    }

    result = convert_optional_components(
        measurements,
        assume_unmeasured_zero=True,
    )

    assert result.calculation_ready is True
    assert result.conditional is True
    assert result.molecular_proportions["BaO"] == 0.0
    assert "BaO" in result.warnings[0]
    assert "CONDITIONAL RESULT" in result.warnings[0]


def test_measured_zero_is_distinct_from_not_measured():
    measurements = make_measurements()
    measurements["NiO"] = {
        "status": "measured_zero",
        "value_wt_percent": 0.0,
    }
    measurements["BaO"] = {
        "status": "not_measured",
        "value_wt_percent": None,
    }

    result = convert_optional_components(measurements)

    assert result.measurements["NiO"].status == "measured_zero"
    assert result.measurements["BaO"].status == "not_measured"
    assert result.molecular_proportions["NiO"] == 0.0
    assert result.molecular_proportions["BaO"] is None


def test_missing_component_record_is_rejected():
    measurements = make_measurements()
    del measurements["Cr2O3"]

    with pytest.raises(ValueError, match="Missing optional-component"):
        convert_optional_components(measurements)


def test_unknown_component_is_rejected():
    measurements = make_measurements()
    measurements["UnknownOxide"] = {
        "status": "measured_zero",
        "value_wt_percent": 0.0,
    }

    with pytest.raises(ValueError, match="Unsupported optional"):
        convert_optional_components(measurements)


@pytest.mark.parametrize(
    "status,value",
    [
        ("measured", 0.0),
        ("measured", -0.1),
        ("measured", float("nan")),
        ("measured", float("inf")),
        ("measured_zero", 0.1),
        ("not_measured", 0.0),
    ],
)
def test_invalid_measurement_combinations_are_rejected(status, value):
    measurements = make_measurements()
    measurements["NiO"] = {
        "status": status,
        "value_wt_percent": value,
    }

    with pytest.raises((ValueError, TypeError)):
        convert_optional_components(measurements)


def test_boolean_concentration_is_rejected():
    measurements = make_measurements()
    measurements["NiO"] = {
        "status": "measured",
        "value_wt_percent": True,
    }

    with pytest.raises(TypeError):
        convert_optional_components(measurements)


def test_input_measurements_are_not_modified():
    measurements = make_measurements()
    original = {
        key: value.copy()
        for key, value in measurements.items()
    }

    convert_optional_components(measurements)

    assert measurements == original


def test_all_optional_formula_weights_are_positive():
    assert set(OPTIONAL_COMPONENT_WEIGHTS) == set(OPTIONAL_COMPONENTS)

    assert all(
        value > 0
        for value in OPTIONAL_COMPONENT_WEIGHTS.values()
    )
