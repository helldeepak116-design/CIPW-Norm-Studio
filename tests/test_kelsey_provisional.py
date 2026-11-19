import pytest

from src.kelsey_provisional import (
    MAJOR_OXIDES,
    OPTIONAL_COMPONENTS,
    KelseyAllocationError,
    calculate_kelsey_provisional,
)


def major(**overrides):
    values = {name: 0.0 for name in MAJOR_OXIDES}
    values.update(overrides)
    return values


def optional(**overrides):
    values = {name: 0.0 for name in OPTIONAL_COMPONENTS}
    values.update(overrides)
    return values


def test_explicit_optional_components_are_required():
    with pytest.raises(KelseyAllocationError, match="Optional components"):
        calculate_kelsey_provisional(major(), {})


def test_rule_4_zircon_adds_silica_requirement():
    result = calculate_kelsey_provisional(
        major(SiO2=2.0),
        optional(ZrO2=0.1),
    )
    assert result.minerals["z"] == pytest.approx(0.1)
    assert result.silica_requirement == pytest.approx(0.1)


def test_rule_12_ilmenite_is_limited_by_feo():
    result = calculate_kelsey_provisional(
        major(SiO2=2.0, FeO=0.1, TiO2=0.2),
        optional(),
    )
    assert result.minerals["il"] == pytest.approx(0.1)
    assert next(s["residual"] for s in result.steps if s.get("rule") == 12 and s.get("component") == "TiO2") == pytest.approx(0.1)
def test_rule_12_ilmenite_is_limited_by_tio2():
    result = calculate_kelsey_provisional(
        major(SiO2=2.0, FeO=0.2, TiO2=0.1),
        optional(),
    )

    assert result.minerals["il"] == pytest.approx(0.1)

    feo_step = next(
        s for s in result.steps
        if s.get("rule") == 12 and s.get("component") == "FeO"
    )
    assert feo_step["residual"] == pytest.approx(0.1)


def test_rule_13_orthoclase():
    result = calculate_kelsey_provisional(
        major(SiO2=10.0, Al2O3=0.2, K2O=0.1),
        optional(),
    )
    assert result.minerals["or"] == pytest.approx(0.1)
    assert result.silica_requirement == pytest.approx(0.6)


def test_rule_13_excess_potassium_forms_metasilicate():
    result = calculate_kelsey_provisional(
        major(SiO2=10.0, Al2O3=0.1, K2O=0.2),
        optional(),
    )
    assert result.minerals["or"] == pytest.approx(0.1)
    assert result.minerals["ks"] == pytest.approx(0.1)
    assert result.silica_requirement == pytest.approx(0.7)


def test_rule_14_albite():
    result = calculate_kelsey_provisional(
        major(SiO2=10.0, Al2O3=0.2, Na2O=0.1),
        optional(),
    )
    assert result.minerals["ab"] == pytest.approx(0.1)
    assert result.silica_requirement == pytest.approx(0.6)


def test_rule_15_acmite():
    result = calculate_kelsey_provisional(
        major(SiO2=10.0, Na2O=0.1, Fe2O3=0.2),
        optional(),
    )
    assert result.minerals["ac"] == pytest.approx(0.1)
    assert result.silica_requirement == pytest.approx(0.4)


def test_rule_15_acmite_is_limited_by_ferric_iron():
    result = calculate_kelsey_provisional(
        major(SiO2=10.0, Na2O=0.2, Fe2O3=0.1),
        optional(),
    )

    assert result.minerals["ac"] == pytest.approx(0.1)
    assert result.minerals["ns"] == pytest.approx(0.1)
    assert result.silica_requirement == pytest.approx(0.5)


def test_rule_16_anorthite_and_corundum():
    result = calculate_kelsey_provisional(
        major(SiO2=10.0, Al2O3=0.3, CaO=0.1),
        optional(),
    )
    assert result.minerals["an"] == pytest.approx(0.1)
    assert result.minerals["c"] == pytest.approx(0.2)
    assert result.silica_requirement == pytest.approx(0.2)


def test_rule_16_anorthite_is_limited_by_alumina():
    result = calculate_kelsey_provisional(
        major(SiO2=10.0, Al2O3=0.1, CaO=0.2),
        optional(),
    )

    assert result.minerals["an"] == pytest.approx(0.1)
    assert result.minerals.get("c", 0.0) == pytest.approx(0.0)
    assert result.minerals["wo"] == pytest.approx(0.1)
    assert result.silica_requirement == pytest.approx(0.3)


def test_rule_17_sphene_and_rutile():
    result = calculate_kelsey_provisional(
        major(SiO2=10.0, CaO=0.1, TiO2=0.2),
        optional(),
    )
    assert result.minerals["tn"] == pytest.approx(0.1)
    assert result.minerals["ru"] == pytest.approx(0.1)
    assert result.silica_requirement == pytest.approx(0.1)


def test_rule_17_sphene_is_limited_by_titanium():
    result = calculate_kelsey_provisional(
        major(SiO2=10.0, CaO=0.2, TiO2=0.1),
        optional(),
    )

    assert result.minerals["tn"] == pytest.approx(0.1)
    assert result.minerals.get("ru", 0.0) == pytest.approx(0.0)
    assert result.minerals["wo"] == pytest.approx(0.1)
    assert result.silica_requirement == pytest.approx(0.2)


def test_rule_18_magnetite_and_hematite():
    result = calculate_kelsey_provisional(
        major(SiO2=10.0, FeO=0.1, Fe2O3=0.2),
        optional(),
    )
    assert result.minerals["mt"] == pytest.approx(0.1)
    assert result.minerals["hm"] == pytest.approx(0.1)


def test_rule_18_magnetite_is_limited_by_ferric_iron():
    result = calculate_kelsey_provisional(
        major(SiO2=10.0, FeO=0.2, Fe2O3=0.1),
        optional(),
    )

    assert result.minerals["mt"] == pytest.approx(0.1)
    assert result.minerals.get("hm", 0.0) == pytest.approx(0.0)
    assert result.minerals["hy"] == pytest.approx(0.1)
    assert result.silica_requirement == pytest.approx(0.1)


def test_rule_19_mg_fe_ratios():
    result = calculate_kelsey_provisional(
        major(SiO2=10.0, MgO=0.3, FeO=0.1),
        optional(),
    )
    assert result.mg_fraction == pytest.approx(0.75)
    assert result.fe_fraction == pytest.approx(0.25)


def test_rule_20_diopside_and_hypersthene():
    result = calculate_kelsey_provisional(
        major(SiO2=10.0, CaO=0.2, MgO=0.3),
        optional(),
    )
    assert result.minerals["di"] == pytest.approx(0.2)
    assert result.minerals["hy"] == pytest.approx(0.1)
    assert result.silica_requirement == pytest.approx(0.5)


def test_rule_20_diopside_and_wollastonite():
    result = calculate_kelsey_provisional(
        major(SiO2=10.0, CaO=0.3, MgO=0.2),
        optional(),
    )
    assert result.minerals["di"] == pytest.approx(0.2)
    assert result.minerals["wo"] == pytest.approx(0.1)
    assert result.silica_requirement == pytest.approx(0.5)


def test_rule_21_silica_excess():
    result = calculate_kelsey_provisional(
        major(SiO2=10.0, K2O=0.1, Al2O3=0.1),
        optional(),
    )
    assert result.status == "SILICA_EXCESS"
    assert result.minerals["q"] == pytest.approx(9.4)


def test_rule_21_silica_deficiency():
    result = calculate_kelsey_provisional(
        major(SiO2=0.1, K2O=0.1, Al2O3=0.1),
        optional(),
    )
    assert result.status == "SILICA_DEFICIENCY"
    assert result.silica_deficiency == pytest.approx(0.5)


def test_negative_input_rejected():
    with pytest.raises(KelseyAllocationError):
        calculate_kelsey_provisional(
            major(SiO2=-1.0),
            optional(),
        )


def test_non_finite_input_rejected():
    with pytest.raises(KelseyAllocationError):
        calculate_kelsey_provisional(
            major(SiO2=float("nan")),
            optional(),
        )


def test_rule_5_zero_fluorine_still_allocates_all_p2o5_to_apatite():
    result = calculate_kelsey_provisional(
        major(SiO2=10.0, P2O5=0.03, CaO=0.2),
        optional(),
    )

    assert result.minerals["ap"] == pytest.approx(0.03)
    assert result.residual_oxides["P2O5"] == pytest.approx(0.0)
    assert result.apatite_fluorine_amount == pytest.approx(0.0)

    rule5_cao = next(
        step for step in result.steps
        if step.get("rule") == 5 and step.get("component") == "CaO"
    )
    assert rule5_cao["amount_removed"] == pytest.approx(0.10)


def test_rule_5_fluorine_limited_apatite_retains_full_p2o5_allocation():
    result = calculate_kelsey_provisional(
        major(SiO2=10.0, P2O5=0.03, CaO=0.2),
        optional(F=0.005),
    )

    assert result.minerals["ap"] == pytest.approx(0.03)
    assert result.residual_oxides["P2O5"] == pytest.approx(0.0)
    assert result.apatite_fluorine_amount == pytest.approx(0.005)

    rule5_cao = next(
        step for step in result.steps
        if step.get("rule") == 5 and step.get("component") == "CaO"
    )
    assert rule5_cao["amount_removed"] == pytest.approx(0.10)

    apatite_step = next(
        step for step in result.steps
        if step.get("rule") == 5
        and step.get("description") == "Kelsey apatite allocation"
    )

    assert apatite_step["F_required"] == pytest.approx(0.01)
    assert apatite_step["F_used"] == pytest.approx(0.005)
    assert apatite_step["P2O5_unallocated"] == pytest.approx(0.0)


def test_rule_7_halite():
    result = calculate_kelsey_provisional(
        major(SiO2=10.0, Na2O=0.2),
        optional(Cl=0.1),
    )
    assert result.minerals["hi"] == pytest.approx(0.05)
    assert next(s["residual"] for s in result.steps if s.get("rule") == 7 and s.get("component") == "Na2O") == pytest.approx(0.15)


def test_rule_8_thenardite():
    result = calculate_kelsey_provisional(
        major(SiO2=10.0, Na2O=0.2),
        optional(SO3=0.1),
        sulfur_basis="SO3",
    )
    assert result.minerals["th"] == pytest.approx(0.1)
    assert next(s["residual"] for s in result.steps if s.get("rule") == 8 and s.get("component") == "Na2O") == pytest.approx(0.1)


def test_rule_9_pyrite():
    result = calculate_kelsey_provisional(
        major(SiO2=10.0, FeO=0.2),
        optional(S=0.1),
        sulfur_basis="S",
    )
    assert result.minerals["pr"] == pytest.approx(0.05)
    assert next(s["residual"] for s in result.steps if s.get("rule") == 9 and s.get("component") == "FeO") == pytest.approx(0.15)


def test_rule_10_calcite():
    result = calculate_kelsey_provisional(
        major(SiO2=10.0, CaO=0.2),
        optional(CO2=0.1),
        carbonate_mode="calcite",
    )
    assert result.minerals["cc"] == pytest.approx(0.1)
    assert next(s["residual"] for s in result.steps if s.get("rule") == 10 and s.get("component") == "CaO") == pytest.approx(0.1)


def test_rule_11_chromite():
    result = calculate_kelsey_provisional(
        major(SiO2=10.0, FeO=0.2),
        optional(Cr2O3=0.1),
    )
    assert result.minerals["cm"] == pytest.approx(0.1)
    assert next(s["residual"] for s in result.steps if s.get("rule") == 11 and s.get("component") == "FeO") == pytest.approx(0.1)


def test_insufficient_apatite_calcium_is_rejected():
    with pytest.raises(KelseyAllocationError, match="Rule 5"):
        calculate_kelsey_provisional(
            major(SiO2=10.0, P2O5=0.1, CaO=0.1),
            optional(F=0.1),
        )





def test_rule_10_cancrinite_sodium_carbonate():
    result = calculate_kelsey_provisional(
        major(SiO2=10.0, Na2O=0.2),
        optional(CO2=0.1),
        carbonate_mode="cancrinite",
    )

    assert result.minerals["nc"] == pytest.approx(0.1)
    assert next(
        s["residual"]
        for s in result.steps
        if s.get("rule") == 10 and s.get("component") == "Na2O"
    ) == pytest.approx(0.1)

    assert result.residual_oxides["CO2"] == pytest.approx(0.0)


def test_rule_2_records_original_and_equivalent_iron_components():
    result = calculate_kelsey_provisional(
        major(FeO=0.5, MnO=0.1),
        optional(NiO=0.2),
    )

    step = next(s for s in result.steps if s.get("rule") == 2)

    assert step["FeO_original"] == pytest.approx(0.5)
    assert step["MnO_added"] == pytest.approx(0.1)
    assert step["NiO_added"] == pytest.approx(0.2)
    assert step["FeO_equivalent_added"] == pytest.approx(0.3)
    assert step["FeO_after_adjustment"] == pytest.approx(0.8)


def test_rule_3_records_original_and_equivalent_calcium_components():
    result = calculate_kelsey_provisional(
        major(CaO=0.5),
        optional(BaO=0.1, SrO=0.2),
    )

    step = next(s for s in result.steps if s.get("rule") == 3)

    assert step["CaO_original"] == pytest.approx(0.5)
    assert step["BaO_added"] == pytest.approx(0.1)
    assert step["SrO_added"] == pytest.approx(0.2)
    assert step["CaO_equivalent_added"] == pytest.approx(0.3)
    assert step["CaO_after_adjustment"] == pytest.approx(0.8)

def test_rule_4_zircon_records_allocation_and_residual():
    result = calculate_kelsey_provisional(
        major(SiO2=2.0),
        optional(ZrO2=0.1),
    )

    step = next(
        s for s in result.steps
        if s.get("rule") == 4
    )

    assert result.minerals["z"] == pytest.approx(0.1)
    assert result.residual_oxides["ZrO2"] == pytest.approx(0.0)
    assert step["silica_added_to_Y"] == pytest.approx(0.1)
    assert step["Y"] == pytest.approx(0.1)
    assert result.silica_requirement == pytest.approx(0.1)

def test_rule_6_fluorite_without_apatite():
    result = calculate_kelsey_provisional(
        major(SiO2=10.0, CaO=0.01),
        optional(F=0.02),
    )

    assert result.minerals["fr"] == pytest.approx(0.01)
    assert result.residual_oxides["F"] == pytest.approx(0.0)
    assert result.residual_oxides["CaO"] == pytest.approx(0.0)

    fluorite_f = next(
        s for s in result.steps
        if s.get("rule") == 6 and s.get("component") == "F"
    )
    fluorite_cao = next(
        s for s in result.steps
        if s.get("rule") == 6 and s.get("component") == "CaO"
    )

    assert fluorite_f["amount_removed"] == pytest.approx(0.02)
    assert fluorite_cao["amount_removed"] == pytest.approx(0.01)


def test_rule_6_rejects_insufficient_calcium():
    with pytest.raises(KelseyAllocationError, match="Rule 6"):
        calculate_kelsey_provisional(
            major(SiO2=10.0, CaO=0.009),
            optional(F=0.02),
        )

def test_rule_7_rejects_insufficient_sodium():
    with pytest.raises(KelseyAllocationError, match="Rule 7"):
        calculate_kelsey_provisional(
            major(SiO2=10.0, Na2O=0.049),
            optional(Cl=0.1),
        )

def test_rule_8_rejects_insufficient_sodium():
    with pytest.raises(KelseyAllocationError, match="Rule 8"):
        calculate_kelsey_provisional(
            major(SiO2=10.0, Na2O=0.099),
            optional(SO3=0.1),
            sulfur_basis="SO3",
        )

def test_rule_9_rejects_insufficient_iron():
    with pytest.raises(KelseyAllocationError, match="Rule 9"):
        calculate_kelsey_provisional(
            major(SiO2=10.0, FeO=0.049),
            optional(S=0.1),
            sulfur_basis="S",
        )

def test_rule_10_cancrinite_rejects_insufficient_sodium():
    with pytest.raises(KelseyAllocationError, match="Rule 10a"):
        calculate_kelsey_provisional(
            major(SiO2=10.0, Na2O=0.099),
            optional(CO2=0.1),
            carbonate_mode="cancrinite",
        )


def test_rule_10_calcite_rejects_insufficient_calcium():
    with pytest.raises(KelseyAllocationError, match="Rule 10b"):
        calculate_kelsey_provisional(
            major(SiO2=10.0, CaO=0.099),
            optional(CO2=0.1),
            carbonate_mode="calcite",
        )

def test_rule_11_rejects_insufficient_iron():
    with pytest.raises(KelseyAllocationError, match="Rule 11"):
        calculate_kelsey_provisional(
            major(SiO2=10.0, FeO=0.099),
            optional(Cr2O3=0.1),
        )

def test_rule_14_albite_is_limited_by_alumina():
    result = calculate_kelsey_provisional(
        major(SiO2=10.0, Al2O3=0.1, Na2O=0.2),
        optional(),
    )

    assert result.minerals["ab"] == pytest.approx(0.1)
    assert result.minerals.get("ns", 0.0) == pytest.approx(0.1)
    assert result.silica_requirement == pytest.approx(0.7)

def test_rule_19_uses_residual_iron_after_magnetite_allocation():
    result = calculate_kelsey_provisional(
        major(
            SiO2=10.0,
            MgO=0.3,
            FeO=0.2,
            Fe2O3=0.1,
        ),
        optional(),
    )

    assert result.minerals["mt"] == pytest.approx(0.1)
    assert result.mg_fraction == pytest.approx(0.75)
    assert result.fe_fraction == pytest.approx(0.25)

    rule_19 = next(step for step in result.steps if step["rule"] == 19)

    assert rule_19["MgO"] == pytest.approx(0.3)
    assert rule_19["FeO"] == pytest.approx(0.1)
    assert rule_19["MgFe_total"] == pytest.approx(0.4)
    assert rule_19["Mg_fraction"] == pytest.approx(0.75)
    assert rule_19["Fe_fraction"] == pytest.approx(0.25)

def test_rule_21_exact_silica_balance():
    result = calculate_kelsey_provisional(
        major(SiO2=0.6, K2O=0.1, Al2O3=0.1),
        optional(),
    )

    assert result.status == "SILICA_BALANCED"
    assert result.silica_requirement == pytest.approx(0.6)
    assert result.silica_excess == pytest.approx(0.0)
    assert result.silica_deficiency == pytest.approx(0.0)
    assert result.minerals.get("q", 0.0) == pytest.approx(0.0)

    rule_21 = next(step for step in result.steps if step["rule"] == 21)
    assert rule_21["status"] == "SILICA_BALANCED"


def test_rule_21_difference_within_tolerance_is_balanced():
    result = calculate_kelsey_provisional(
        major(SiO2=0.6 + 5e-11, K2O=0.1, Al2O3=0.1),
        optional(),
        tolerance=1e-10,
    )

    assert result.status == "SILICA_BALANCED"
    assert result.silica_excess == pytest.approx(0.0)
    assert result.silica_deficiency == pytest.approx(0.0)
    assert result.minerals.get("q", 0.0) == pytest.approx(0.0)
