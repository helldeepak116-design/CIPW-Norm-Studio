import pytest

from config.oxide_config import OXIDE_CONFIG
from src.mineral_formula_weights import (
    OXIDE_MASSES,
    get_formula_weight,
)


@pytest.mark.parametrize("oxide", ["SiO2", "MgO", "FeO", "CaO"])
def test_registry_oxide_masses_match_project_configuration(oxide):
    assert OXIDE_MASSES[oxide] == pytest.approx(
        OXIDE_CONFIG[oxide]["molecular_weight"],
        abs=0.0,
    )


def test_hypersthene_endmember_weights_use_configured_oxide_masses():
    mg_weight = get_formula_weight(
        "hy", mg_fraction=1.0, fe_fraction=0.0
    )
    fe_weight = get_formula_weight(
        "hy", mg_fraction=0.0, fe_fraction=1.0
    )

    expected_mg = (
        OXIDE_CONFIG["SiO2"]["molecular_weight"]
        + OXIDE_CONFIG["MgO"]["molecular_weight"]
    )
    expected_fe = (
        OXIDE_CONFIG["SiO2"]["molecular_weight"]
        + OXIDE_CONFIG["FeO"]["molecular_weight"]
    )

    assert mg_weight == pytest.approx(expected_mg, abs=1e-12)
    assert fe_weight == pytest.approx(expected_fe, abs=1e-12)
