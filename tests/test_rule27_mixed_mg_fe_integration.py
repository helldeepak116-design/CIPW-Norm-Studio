import pytest

from src.kelsey_provisional import calculate_kelsey_provisional
from src.kelsey_silica_deficiency import redistribute_silica
from src.mass_balance import check_mass_balance, mineral_oxide_equivalents


OPTIONAL = {
    "NiO": 0.0,
    "BaO": 0.0,
    "SrO": 0.0,
    "ZrO2": 0.0,
    "F": 0.0,
    "Cl": 0.0,
    "SO3": 0.0,
    "S": 0.0,
    "CO2": 0.0,
    "Cr2O3": 0.0,
}

MAJOR = {
    "SiO2": 0.1,
    "TiO2": 0.0,
    "Al2O3": 0.0,
    "Fe2O3": 0.0,
    "FeO": 0.05,
    "MnO": 0.0,
    "MgO": 0.15,
    "CaO": 0.2,
    "Na2O": 0.0,
    "K2O": 0.0,
    "P2O5": 0.0,
}


def test_rule27_preserves_mg_fe_partition_and_component_balance():
    provisional = calculate_kelsey_provisional(MAJOR, OPTIONAL)

    assert provisional.mg_fraction == pytest.approx(0.75)
    assert provisional.fe_fraction == pytest.approx(0.25)

    final = redistribute_silica(
        provisional.minerals,
        provisional.silica_deficiency,
    )

    # Rule 27 reaction products.
    assert final.minerals["di"] == pytest.approx(0.0)
    assert final.minerals["cs"] == pytest.approx(0.1)
    assert final.minerals["ol"] == pytest.approx(0.1)

    # Verify the recorded reaction and silica release.
    rule27_steps = [
        step for step in final.steps
        if step["rule"] == 27
    ]

    assert len(rule27_steps) == 1
    assert rule27_steps[0]["provisional_amount_converted"] == pytest.approx(0.2)
    assert rule27_steps[0]["deficiency_before"] == pytest.approx(0.3)
    assert rule27_steps[0]["deficiency_after"] == pytest.approx(0.1)

    # Independently inspect the oxide-equivalent composition
    # assigned to the Rule 27 olivine product.
    olivine_components = mineral_oxide_equivalents(
        {"ol": final.minerals["ol"]},
        provisional.mg_fraction,
        provisional.fe_fraction,
    )

    assert olivine_components["MgO"] == pytest.approx(0.15)
    assert olivine_components["FeO"] == pytest.approx(0.05)
    assert olivine_components["SiO2"] == pytest.approx(0.1)

    # Integrated component mass-balance validation.
    balance = check_mass_balance(
        MAJOR,
        OPTIONAL,
        provisional,
        final,
    )

    assert balance.balanced is True
    assert balance.status == "BALANCED_WITH_UNRESOLVED_SILICA_DEFICIENCY"
    assert balance.max_non_silica_error == pytest.approx(0.0, abs=1e-10)
    assert balance.silica_error == pytest.approx(0.0, abs=1e-10)
    assert balance.expected_silica_deficit == pytest.approx(0.1)
    assert final.final_deficiency == pytest.approx(0.1)
