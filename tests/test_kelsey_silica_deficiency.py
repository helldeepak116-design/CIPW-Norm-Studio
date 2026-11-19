import pytest

from src.kelsey_silica_deficiency import redistribute_silica


def test_rule_22_hypersthene_to_olivine():
    result = redistribute_silica({"hy": 1.0}, 0.2)
    assert result.minerals["hy"] == pytest.approx(0.6)
    assert result.minerals["ol"] == pytest.approx(0.2)
    assert result.final_deficiency == 0.0


def test_rule_23_sphene_to_perovskite():
    result = redistribute_silica({"tn": 1.0}, 0.3)
    assert result.minerals["tn"] == pytest.approx(0.7)
    assert result.minerals["pf"] == pytest.approx(0.3)


def test_rule_24_albite_to_nepheline():
    result = redistribute_silica({"ab": 1.0}, 2.0)
    assert result.minerals["ab"] == pytest.approx(0.5)
    assert result.minerals["ne"] == pytest.approx(0.5)


def test_rule_25_orthoclase_to_leucite_uses_half_mole_factor():
    result = redistribute_silica({"or": 1.0}, 1.0)
    assert result.minerals["or"] == pytest.approx(0.5)
    assert result.minerals["lc"] == pytest.approx(0.5)
    assert result.lc_prime_remaining == pytest.approx(0.5)


def test_rule_26_wollastonite_to_dicalcium_silicate():
    result = redistribute_silica({"wo": 1.0}, 0.2)
    assert result.minerals["wo"] == pytest.approx(0.6)
    assert result.minerals["cs"] == pytest.approx(0.2)


def test_rule_27_diopside_products():
    result = redistribute_silica({"di": 1.0}, 0.4)
    assert result.minerals["di"] == pytest.approx(0.6)
    assert result.minerals["cs"] == pytest.approx(0.2)
    assert result.minerals["ol"] == pytest.approx(0.2)


def test_rule_28_kaliophilite_uses_provisional_leucite_only():
    # Only 0.2 Or is available, so Rule 25 cannot consume all
    # the silica deficiency. It creates 0.1 provisional leucite.
    result = redistribute_silica({"or": 0.2, "lc": 0.4}, 2.0)

    assert result.minerals["or"] == pytest.approx(0.0)
    assert result.minerals["kp"] == pytest.approx(0.2)
    assert result.minerals["lc"] == pytest.approx(0.4)
    assert result.lc_prime_remaining == pytest.approx(0.0)
    assert result.final_deficiency > 0.0


def test_rule_order_is_preserved():
    result = redistribute_silica(
        {"hy": 0.2, "tn": 0.2, "ab": 0.2},
        1.0,
    )
    assert [step["rule"] for step in result.steps] == [22, 23, 24]


def test_unresolved_deficiency_is_reported():
    result = redistribute_silica({"hy": 0.1}, 1.0)
    assert result.status == "UNRESOLVED_DEFICIENCY"
    assert result.final_deficiency > 0


def test_zero_deficiency_does_not_change_minerals():
    result = redistribute_silica({"hy": 1.0, "ab": 0.5}, 0.0)
    assert result.minerals["hy"] == pytest.approx(1.0)
    assert result.minerals["ab"] == pytest.approx(0.5)
    assert result.steps == []


def test_negative_deficiency_rejected():
    with pytest.raises(ValueError):
        redistribute_silica({"hy": 1.0}, -0.1)


def test_negative_mineral_amount_rejected():
    with pytest.raises(ValueError):
        redistribute_silica({"hy": -1.0}, 0.1)


def test_non_finite_values_rejected():
    with pytest.raises(ValueError):
        redistribute_silica({"hy": float("nan")}, 0.1)

def test_rule_22_hypersthene_limited_conversion():
    result = redistribute_silica({"hy": 0.1}, 1.0)

    assert result.minerals["hy"] == pytest.approx(0.0)
    assert result.minerals["ol"] == pytest.approx(0.05)
    assert result.initial_deficiency == pytest.approx(1.0)
    assert result.final_deficiency == pytest.approx(0.95)
    assert result.status == "UNRESOLVED_DEFICIENCY"

    rule_22 = next(step for step in result.steps if step["rule"] == 22)

    assert rule_22["provisional_amount_converted"] == pytest.approx(0.1)
    assert rule_22["products_formed"]["ol"] == pytest.approx(0.05)
    assert rule_22["deficiency_before"] == pytest.approx(1.0)
    assert rule_22["deficiency_after"] == pytest.approx(0.95)

def test_rule_23_sphene_limited_conversion():
    result = redistribute_silica({"tn": 0.1}, 0.5)

    assert result.minerals["tn"] == pytest.approx(0.0)
    assert result.minerals["pf"] == pytest.approx(0.1)
    assert result.initial_deficiency == pytest.approx(0.5)
    assert result.final_deficiency == pytest.approx(0.4)
    assert result.status == "UNRESOLVED_DEFICIENCY"

    rule_23 = next(step for step in result.steps if step["rule"] == 23)

    assert rule_23["provisional_amount_converted"] == pytest.approx(0.1)
    assert rule_23["products_formed"]["pf"] == pytest.approx(0.1)
    assert rule_23["deficiency_before"] == pytest.approx(0.5)
    assert rule_23["deficiency_after"] == pytest.approx(0.4)

def test_rule_24_albite_limited_conversion():
    result = redistribute_silica({"ab": 0.1}, 1.0)

    assert result.minerals["ab"] == pytest.approx(0.0)
    assert result.minerals["ne"] == pytest.approx(0.1)
    assert result.initial_deficiency == pytest.approx(1.0)
    assert result.final_deficiency == pytest.approx(0.6)
    assert result.status == "UNRESOLVED_DEFICIENCY"

    rule_24 = next(step for step in result.steps if step["rule"] == 24)

    assert rule_24["provisional_amount_converted"] == pytest.approx(0.1)
    assert rule_24["products_formed"]["ne"] == pytest.approx(0.1)
    assert rule_24["deficiency_before"] == pytest.approx(1.0)
    assert rule_24["deficiency_after"] == pytest.approx(0.6)

def test_rule_25_orthoclase_limited_conversion_and_diagnostics():
    result = redistribute_silica({"or": 0.2}, 0.7)

    assert result.minerals["or"] == pytest.approx(0.0)
    assert result.minerals["lc"] == pytest.approx(0.05)
    assert result.minerals["kp"] == pytest.approx(0.15)
    assert result.lc_prime_remaining == pytest.approx(0.05)
    assert result.final_deficiency == pytest.approx(0.0)
    assert result.status == "COMPLETED"

    rule_25 = next(step for step in result.steps if step["rule"] == 25)

    assert rule_25["provisional_amount_converted"] == pytest.approx(0.2)
    assert rule_25["products_formed"]["lc_prime"] == pytest.approx(0.2)
    assert rule_25["deficiency_before"] == pytest.approx(0.7)
    assert rule_25["deficiency_after"] == pytest.approx(0.3)

    rule_28 = next(step for step in result.steps if step["rule"] == 28)
    assert rule_28["provisional_amount_converted"] == pytest.approx(0.15)
    assert rule_28["products_formed"]["kp"] == pytest.approx(0.15)

def test_rule_26_wollastonite_limited_conversion_and_diagnostics():
    result = redistribute_silica({"wo": 0.1}, 0.5)

    assert result.minerals["wo"] == pytest.approx(0.0)
    assert result.minerals["cs"] == pytest.approx(0.05)
    assert result.initial_deficiency == pytest.approx(0.5)
    assert result.final_deficiency == pytest.approx(0.45)
    assert result.status == "UNRESOLVED_DEFICIENCY"

    rule_26 = next(step for step in result.steps if step["rule"] == 26)

    assert rule_26["provisional_amount_converted"] == pytest.approx(0.1)
    assert rule_26["products_formed"]["cs"] == pytest.approx(0.05)
    assert rule_26["deficiency_before"] == pytest.approx(0.5)
    assert rule_26["deficiency_after"] == pytest.approx(0.45)

def test_rule_27_diopside_limited_conversion_and_diagnostics():
    result = redistribute_silica({"di": 0.1}, 0.5)

    assert result.minerals["di"] == pytest.approx(0.0)
    assert result.minerals["cs"] == pytest.approx(0.05)
    assert result.minerals["ol"] == pytest.approx(0.05)
    assert result.initial_deficiency == pytest.approx(0.5)
    assert result.final_deficiency == pytest.approx(0.4)
    assert result.status == "UNRESOLVED_DEFICIENCY"

    rule_27 = next(step for step in result.steps if step["rule"] == 27)

    assert rule_27["provisional_amount_converted"] == pytest.approx(0.1)
    assert rule_27["products_formed"]["cs"] == pytest.approx(0.05)
    assert rule_27["products_formed"]["ol"] == pytest.approx(0.05)
    assert rule_27["deficiency_before"] == pytest.approx(0.5)
    assert rule_27["deficiency_after"] == pytest.approx(0.4)

