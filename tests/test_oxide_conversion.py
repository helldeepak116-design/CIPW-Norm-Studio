
import pytest
import pandas as pd

from config.oxide_config import OXIDE_CONFIG
from config.settings import REQUIRED_OXIDES
from src.data_validation import (
    validate_oxide_composition,
    validate_geochemical_dataframe,
)
from src.oxide_conversion import convert_oxides_to_molecular_proportions


@pytest.fixture
def valid_composition():
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


def test_valid_composition(valid_composition):
    result = validate_oxide_composition(valid_composition)
    assert result["valid"] is True
    assert result["total_status"] == "within_range"
    assert result["analytical_total"] == pytest.approx(99.1)


def test_negative_oxide_rejected(valid_composition):
    valid_composition["FeO"] = -1
    result = validate_oxide_composition(valid_composition)
    assert result["valid"] is False


def test_missing_oxide_rejected(valid_composition):
    del valid_composition["FeO"]
    result = validate_oxide_composition(valid_composition)
    assert result["valid"] is False


def test_missing_is_not_zero(valid_composition):
    valid_composition["FeO"] = None
    result = validate_oxide_composition(valid_composition)
    assert result["valid"] is False


def test_measured_zero_is_accepted(valid_composition):
    valid_composition["FeO"] = 0.0
    result = validate_oxide_composition(valid_composition)
    assert result["valid"] is True


def test_nonfinite_value_rejected(valid_composition):
    valid_composition["MgO"] = float("nan")
    result = validate_oxide_composition(valid_composition)
    assert result["valid"] is False


def test_high_analytical_total_warns_not_rejects(valid_composition):
    valid_composition["SiO2"] = 60.0
    result = validate_oxide_composition(valid_composition)
    assert result["valid"] is True
    assert result["total_status"] == "high"
    assert len(result["warnings"]) > 0


def test_unknown_oxide_rejected(valid_composition):
    valid_composition["LOI"] = 2.0
    result = validate_oxide_composition(valid_composition)
    assert result["valid"] is False


def test_molecular_proportion(valid_composition):
    result = convert_oxides_to_molecular_proportions(valid_composition)
    table = result["oxide_table"]

    expected = 50.0 / OXIDE_CONFIG["SiO2"]["molecular_weight"]

    assert table.loc["SiO2", "molecular_proportion"] == pytest.approx(
        expected
    )


def test_cation_and_oxygen_proportions(valid_composition):
    result = convert_oxides_to_molecular_proportions(valid_composition)
    table = result["oxide_table"]

    molecular = 15.0 / OXIDE_CONFIG["Al2O3"]["molecular_weight"]

    assert table.loc["Al2O3", "cation_proportion"] == pytest.approx(
        molecular * 2
    )
    assert table.loc["Al2O3", "oxygen_proportion"] == pytest.approx(
        molecular * 3
    )


def test_volatile_free_conversion(valid_composition):
    result = convert_oxides_to_molecular_proportions(
        valid_composition,
        volatile_free=True,
    )

    assert result["volatile_free"] is True
    assert result["conversion_total"] == pytest.approx(100.0)


def test_original_composition_is_not_modified(valid_composition):
    original = valid_composition.copy()

    convert_oxides_to_molecular_proportions(valid_composition)

    assert valid_composition == original


def test_dataframe_validation(valid_composition):
    dataframe = pd.DataFrame([
        {"Sample_ID": "S01", **valid_composition}
    ])

    result = validate_geochemical_dataframe(dataframe)

    assert result["valid"] is True
    assert len(result["row_reports"]) == 1


def test_dataframe_duplicate_sample_ids(valid_composition):
    dataframe = pd.DataFrame([
        {"Sample_ID": "S01", **valid_composition},
        {"Sample_ID": "S01", **valid_composition},
    ])

    result = validate_geochemical_dataframe(dataframe)

    assert result["valid"] is False
    assert any("duplicate" in error.lower() for error in result["errors"])


def test_all_required_oxides_have_molecular_weights():
    assert set(REQUIRED_OXIDES) == set(OXIDE_CONFIG)


@pytest.mark.parametrize("boolean_value", [True, False])
def test_boolean_oxide_value_rejected(valid_composition, boolean_value):
    valid_composition["FeO"] = boolean_value

    result = validate_oxide_composition(valid_composition)

    assert result["valid"] is False
    assert any("boolean" in error.lower() for error in result["errors"])


@pytest.mark.parametrize("sample_id", ["", "   "])
def test_blank_sample_id_rejected(valid_composition, sample_id):
    dataframe = pd.DataFrame([
        {"Sample_ID": sample_id, **valid_composition}
    ])

    result = validate_geochemical_dataframe(dataframe)

    assert result["valid"] is False
    assert any("blank" in error.lower() for error in result["errors"])


def test_numeric_string_oxide_value_remains_accepted(valid_composition):
    valid_composition["FeO"] = "8.5"

    result = validate_oxide_composition(valid_composition)

    assert result["valid"] is True
    assert result["analytical_total"] == pytest.approx(99.6)


@pytest.mark.parametrize("nonfinite_value", [float("inf"), float("-inf"), float("nan")])
def test_nonfinite_oxide_values_rejected(valid_composition, nonfinite_value):
    valid_composition["FeO"] = nonfinite_value

    result = validate_oxide_composition(valid_composition)

    assert result["valid"] is False

def test_numeric_string_oxide_value_remains_accepted(valid_composition):
    valid_composition["FeO"] = "8.5"

    result = validate_oxide_composition(valid_composition)

    assert result["valid"] is True
    assert result["analytical_total"] == pytest.approx(99.6)