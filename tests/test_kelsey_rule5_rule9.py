import pytest

from src.kelsey_provisional import (
    MAJOR_OXIDES,
    OPTIONAL_COMPONENTS,
    KelseyAllocationError,
    calculate_kelsey_provisional,
)


def make_major(**overrides):
    values = {name: 0.0 for name in MAJOR_OXIDES}
    values["SiO2"] = 10.0
    values.update(overrides)
    return values


def make_optional(**overrides):
    values = {name: 0.0 for name in OPTIONAL_COMPONENTS}
    values.update(overrides)
    return values


def rule_component(result, rule, component):
    matches = [
        step for step in result.steps
        if step.get("rule") == rule
        and step.get("component") == component
    ]
    return matches


def test_rule5_apatite_uses_original_kelsey_one_third_fluorine_limit():
    result = calculate_kelsey_provisional(
        make_major(P2O5=0.03, CaO=0.20),
        make_optional(F=0.03),
    )

    apatite_steps = [
        step for step in result.steps
        if step.get("rule") == 5
        and step.get("description") == "Kelsey apatite allocation"
    ]

    assert len(apatite_steps) == 1
    assert apatite_steps[0]["apatite"] == pytest.approx(0.03)
    assert apatite_steps[0]["CaO_used"] == pytest.approx(0.10)
    assert apatite_steps[0]["F_required"] == pytest.approx(0.01)
    assert apatite_steps[0]["F_used"] == pytest.approx(0.01)
    assert result.apatite_fluorine_amount == pytest.approx(0.01)


def test_rule6_fluorite_uses_remaining_fluorine():
    result = calculate_kelsey_provisional(
        make_major(P2O5=0.03, CaO=0.20),
        make_optional(F=0.03),
    )

    fluorine_consumption = rule_component(result, 6, "F")
    calcium_consumption = rule_component(result, 6, "CaO")

    assert len(fluorine_consumption) == 1
    assert len(calcium_consumption) == 1

    assert fluorine_consumption[0]["amount_removed"] == pytest.approx(0.02)
    assert calcium_consumption[0]["amount_removed"] == pytest.approx(0.01)
    assert result.minerals["fr"] == pytest.approx(0.01)


def test_rule5_and_rule6_fluorine_mass_balance():
    result = calculate_kelsey_provisional(
        make_major(P2O5=0.03, CaO=0.20),
        make_optional(F=0.03),
    )

    apatite = next(
        step for step in result.steps
        if step.get("rule") == 5
        and step.get("description") == "Kelsey apatite allocation"
    )

    fluorite_f = sum(
        step["amount_removed"]
        for step in rule_component(result, 6, "F")
    )

    assert apatite["F_used"] + fluorite_f == pytest.approx(0.03)


def test_rule9_pyrite_from_elemental_sulfur():
    result = calculate_kelsey_provisional(
        make_major(FeO=0.20),
        make_optional(S=0.10),
        sulfur_basis="S",
    )

    assert result.minerals["pr"] == pytest.approx(0.05)

    sulfur_steps = rule_component(result, 9, "S")
    iron_steps = rule_component(result, 9, "FeO")

    assert len(sulfur_steps) == 1
    assert len(iron_steps) == 1
    assert sulfur_steps[0]["amount_removed"] == pytest.approx(0.10)
    assert iron_steps[0]["amount_removed"] == pytest.approx(0.05)


def test_rule9_pyrite_from_so3_as_sulfur_source():
    result = calculate_kelsey_provisional(
        make_major(FeO=0.20),
        make_optional(SO3=0.10),
        sulfur_basis="S",
    )

    assert result.minerals["pr"] == pytest.approx(0.05)

    sulfur_steps = rule_component(result, 9, "SO3")
    iron_steps = rule_component(result, 9, "FeO")

    assert len(sulfur_steps) == 1
    assert len(iron_steps) == 1
    assert sulfur_steps[0]["amount_removed"] == pytest.approx(0.10)
    assert iron_steps[0]["amount_removed"] == pytest.approx(0.05)


def test_rule9_rejects_simultaneous_s_and_so3():
    with pytest.raises(
        KelseyAllocationError,
        match="either S or SO3",
    ):
        calculate_kelsey_provisional(
            make_major(FeO=0.20),
            make_optional(S=0.10, SO3=0.10),
            sulfur_basis="S",
        )


def test_rule9_pyrite_iron_and_sulfur_consumption_balance():
    result = calculate_kelsey_provisional(
        make_major(FeO=0.20),
        make_optional(S=0.10),
        sulfur_basis="S",
    )

    sulfur_consumed = sum(
        step["amount_removed"]
        for step in rule_component(result, 9, "S")
    )

    iron_consumed = sum(
        step["amount_removed"]
        for step in rule_component(result, 9, "FeO")
    )

    pyrite = result.minerals["pr"]

    assert sulfur_consumed == pytest.approx(2.0 * pyrite)
    assert iron_consumed == pytest.approx(pyrite)

