import pytest

from src.kelsey_provisional import calculate_kelsey_provisional
from src.kelsey_silica_deficiency import redistribute_silica
from src.mass_balance import check_mass_balance


def empty_optional():
    return {
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


def base_major():
    return {
        "SiO2": 0.0,
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


def test_real_provisional_calculation_with_silica_excess():
    major = base_major()
    major.update({
        "SiO2": 10.0,
        "Al2O3": 1.0,
        "K2O": 1.0,
        "FeO": 1.0,
        "MnO": 0.1,
        "MgO": 1.0,
    })

    optional = empty_optional()
    optional["NiO"] = 0.2

    provisional = calculate_kelsey_provisional(major, optional)

    result = check_mass_balance(
        major,
        optional,
        provisional,
    )

    assert provisional.status == "SILICA_EXCESS"
    assert result.balanced
    assert result.status == "BALANCED"
    assert result.max_non_silica_error < 1e-8
    assert abs(result.silica_error) < 1e-8


def test_real_orthoclase_to_leucite_redistribution():
    major = base_major()
    major.update({
        "SiO2": 4.0,
        "Al2O3": 1.0,
        "K2O": 1.0,
    })
    optional = empty_optional()

    provisional = calculate_kelsey_provisional(major, optional)

    assert provisional.status == "SILICA_DEFICIENCY"
    assert provisional.silica_deficiency == pytest.approx(2.0)

    redistributed = redistribute_silica(
        provisional.minerals,
        provisional.silica_deficiency,
    )

    result = check_mass_balance(
        major,
        optional,
        provisional,
        redistributed,
    )

    assert redistributed.status == "COMPLETED"
    assert redistributed.minerals["or"] == pytest.approx(0.0)
    assert redistributed.minerals["lc"] == pytest.approx(1.0)
    assert result.balanced
    assert result.status == "BALANCED"


def test_real_hypersthene_to_olivine_redistribution():
    major = base_major()
    major.update({
        "SiO2": 1.0,
        "MgO": 2.0,
    })
    optional = empty_optional()

    provisional = calculate_kelsey_provisional(major, optional)

    assert provisional.status == "SILICA_DEFICIENCY"
    assert provisional.silica_deficiency == pytest.approx(1.0)

    redistributed = redistribute_silica(
        provisional.minerals,
        provisional.silica_deficiency,
    )

    result = check_mass_balance(
        major,
        optional,
        provisional,
        redistributed,
    )

    assert redistributed.status == "COMPLETED"
    assert redistributed.minerals["hy"] == pytest.approx(0.0)
    assert redistributed.minerals["ol"] == pytest.approx(1.0)
    assert result.balanced
    assert result.status == "BALANCED"


def test_pyrite_elemental_sulfur_end_to_end():
    major = base_major()
    major.update({
        "SiO2": 10.0,
        "FeO": 0.20,
    })
    optional = empty_optional()
    optional["S"] = 0.10

    provisional = calculate_kelsey_provisional(
        major,
        optional,
        sulfur_basis="S",
    )

    result = check_mass_balance(
        major,
        optional,
        provisional,
        sulfur_basis="S",
    )

    assert provisional.minerals["pr"] == pytest.approx(0.05)
    assert result.balanced
    assert result.max_non_silica_error < 1e-8
    assert result.component_differences["S"] == pytest.approx(0.0)
    assert result.component_differences["FeO"] == pytest.approx(0.0)


def test_pyrite_so3_reporting_basis_end_to_end():
    major = base_major()
    major.update({
        "SiO2": 10.0,
        "FeO": 0.20,
    })
    optional = empty_optional()
    optional["SO3"] = 0.10

    provisional = calculate_kelsey_provisional(
        major,
        optional,
        sulfur_basis="S",
    )

    result = check_mass_balance(
        major,
        optional,
        provisional,
        sulfur_basis="S",
    )

    assert provisional.minerals["pr"] == pytest.approx(0.05)
    assert result.balanced
    assert result.max_non_silica_error < 1e-8
    assert result.component_differences["SO3"] == pytest.approx(0.0)
    assert result.component_differences["FeO"] == pytest.approx(0.0)


def test_thenardite_so3_end_to_end():
    major = base_major()
    major.update({
        "SiO2": 10.0,
        "Na2O": 0.20,
    })
    optional = empty_optional()
    optional["SO3"] = 0.10

    provisional = calculate_kelsey_provisional(
        major,
        optional,
        sulfur_basis="SO3",
    )

    result = check_mass_balance(
        major,
        optional,
        provisional,
        sulfur_basis="SO3",
    )

    assert provisional.minerals["th"] == pytest.approx(0.10)
    assert result.balanced
    assert result.max_non_silica_error < 1e-8
    assert result.component_differences["SO3"] == pytest.approx(0.0)
    assert result.component_differences["Na2O"] == pytest.approx(0.0)


def test_cancrinite_sodium_carbonate_mass_balance_end_to_end():
    major = base_major()
    major.update({
        "SiO2": 10.0,
        "Na2O": 0.20,
    })
    optional = empty_optional()
    optional["CO2"] = 0.10

    provisional = calculate_kelsey_provisional(
        major,
        optional,
        carbonate_mode="cancrinite",
    )

    result = check_mass_balance(
        major,
        optional,
        provisional,
    )

    assert provisional.minerals["nc"] == pytest.approx(0.10)
    assert result.balanced
    assert result.max_non_silica_error < 1e-8
    assert result.component_differences["CO2"] == pytest.approx(0.0)
    assert result.component_differences["Na2O"] == pytest.approx(0.0)


def test_rule_2_mn_ni_equivalent_mass_balance():
    major = base_major()
    major.update({
        "SiO2": 10.0,
        "FeO": 0.5,
        "MnO": 0.1,
    })

    optional = empty_optional()
    optional["NiO"] = 0.2

    provisional = calculate_kelsey_provisional(major, optional)
    result = check_mass_balance(major, optional, provisional)

    step = next(s for s in provisional.steps if s.get("rule") == 2)

    assert step["FeO_equivalent_added"] == pytest.approx(0.3)
    assert step["FeO_after_adjustment"] == pytest.approx(0.8)
    assert result.balanced
    assert result.max_non_silica_error < 1e-8


def test_rule_3_ba_sr_equivalent_mass_balance():
    major = base_major()
    major.update({
        "SiO2": 10.0,
        "CaO": 0.5,
    })

    optional = empty_optional()
    optional.update({
        "BaO": 0.1,
        "SrO": 0.2,
    })

    provisional = calculate_kelsey_provisional(major, optional)
    result = check_mass_balance(major, optional, provisional)

    step = next(s for s in provisional.steps if s.get("rule") == 3)

    assert step["CaO_equivalent_added"] == pytest.approx(0.3)
    assert step["CaO_after_adjustment"] == pytest.approx(0.8)
    assert result.balanced
    assert result.max_non_silica_error < 1e-8

def test_zircon_end_to_end_mass_balance_with_silica_excess():
    major = base_major()
    major["SiO2"] = 2.0

    optional = empty_optional()
    optional["ZrO2"] = 0.1

    provisional = calculate_kelsey_provisional(major, optional)
    result = check_mass_balance(major, optional, provisional)

    assert provisional.minerals["z"] == pytest.approx(0.1)
    assert provisional.minerals["q"] == pytest.approx(1.9)
    assert provisional.residual_oxides["ZrO2"] == pytest.approx(0.0)

    assert result.balanced
    assert result.status == "BALANCED"
    assert result.max_non_silica_error < 1e-8
    assert result.component_differences["ZrO2"] == pytest.approx(0.0)
    assert result.component_differences["SiO2"] == pytest.approx(0.0)


def test_zircon_end_to_end_mass_balance_with_silica_deficiency():
    major = base_major()
    major["SiO2"] = 0.05

    optional = empty_optional()
    optional["ZrO2"] = 0.1

    provisional = calculate_kelsey_provisional(major, optional)
    result = check_mass_balance(major, optional, provisional)

    assert provisional.minerals["z"] == pytest.approx(0.1)
    assert provisional.residual_oxides["ZrO2"] == pytest.approx(0.0)
    assert provisional.silica_requirement == pytest.approx(0.1)
    assert provisional.silica_deficiency == pytest.approx(0.05)
    assert provisional.status == "SILICA_DEFICIENCY"

    assert result.balanced
    assert result.status == "BALANCED_WITH_UNRESOLVED_SILICA_DEFICIENCY"
    assert result.expected_silica_deficit == pytest.approx(0.05)
    assert result.max_non_silica_error < 1e-8
    assert abs(result.silica_error) < 1e-8

def test_kelsey_apatite_and_remaining_fluorine_mass_balance():
    major = base_major()
    major.update({
        "SiO2": 10.0,
        "P2O5": 0.03,
        "CaO": 0.20,
    })

    optional = empty_optional()
    optional["F"] = 0.03

    provisional = calculate_kelsey_provisional(major, optional)
    result = check_mass_balance(major, optional, provisional)

    assert provisional.minerals["ap"] == pytest.approx(0.03)
    assert provisional.apatite_fluorine_amount == pytest.approx(0.01)
    assert provisional.minerals["fr"] == pytest.approx(0.01)
    assert provisional.residual_oxides["P2O5"] == pytest.approx(0.0)
    assert provisional.residual_oxides["F"] == pytest.approx(0.0)

    assert result.balanced
    assert result.max_non_silica_error < 1e-8
    assert result.component_differences["P2O5"] == pytest.approx(0.0)
    assert result.component_differences["F"] == pytest.approx(0.0)
    assert result.component_differences["CaO"] == pytest.approx(0.0)


def test_fluorine_limited_kelsey_apatite_mass_balance():
    major = base_major()
    major.update({
        "SiO2": 10.0,
        "P2O5": 0.03,
        "CaO": 0.20,
    })

    optional = empty_optional()
    optional["F"] = 0.005

    provisional = calculate_kelsey_provisional(major, optional)
    result = check_mass_balance(major, optional, provisional)

    assert provisional.minerals["ap"] == pytest.approx(0.03)
    assert provisional.apatite_fluorine_amount == pytest.approx(0.005)
    assert provisional.residual_oxides["P2O5"] == pytest.approx(0.0)
    assert provisional.residual_oxides["F"] == pytest.approx(0.0)

    assert result.balanced
    assert result.max_non_silica_error < 1e-8
    assert result.component_differences["P2O5"] == pytest.approx(0.0)
    assert result.component_differences["F"] == pytest.approx(0.0)
    assert result.component_differences["CaO"] == pytest.approx(0.0)


def test_pure_fluorite_end_to_end_mass_balance():
    major = base_major()
    major.update({
        "SiO2": 10.0,
        "CaO": 0.01,
    })

    optional = empty_optional()
    optional["F"] = 0.02

    provisional = calculate_kelsey_provisional(major, optional)
    result = check_mass_balance(major, optional, provisional)

    assert provisional.minerals["ap"] == pytest.approx(0.0)
    assert provisional.minerals["fr"] == pytest.approx(0.01)
    assert provisional.residual_oxides["F"] == pytest.approx(0.0)
    assert provisional.residual_oxides["CaO"] == pytest.approx(0.0)

    assert result.balanced
    assert result.max_non_silica_error < 1e-8
    assert result.component_differences["F"] == pytest.approx(0.0)
    assert result.component_differences["CaO"] == pytest.approx(0.0)

def test_pure_halite_end_to_end_mass_balance():
    major = base_major()
    major.update({
        "SiO2": 10.0,
        "Na2O": 0.05,
    })

    optional = empty_optional()
    optional["Cl"] = 0.1

    provisional = calculate_kelsey_provisional(major, optional)
    result = check_mass_balance(major, optional, provisional)

    assert provisional.minerals["hi"] == pytest.approx(0.05)
    assert provisional.residual_oxides["Cl"] == pytest.approx(0.0)
    assert provisional.residual_oxides["Na2O"] == pytest.approx(0.0)

    assert result.balanced
    assert result.max_non_silica_error < 1e-8
    assert result.component_differences["Cl"] == pytest.approx(0.0)
    assert result.component_differences["Na2O"] == pytest.approx(0.0)

def test_calcite_end_to_end_mass_balance():
    major = base_major()
    major.update({
        "SiO2": 10.0,
        "CaO": 0.10,
    })

    optional = empty_optional()
    optional["CO2"] = 0.10

    provisional = calculate_kelsey_provisional(
        major,
        optional,
        carbonate_mode="calcite",
    )

    result = check_mass_balance(
        major,
        optional,
        provisional,
    )

    assert provisional.minerals["cc"] == pytest.approx(0.10)
    assert provisional.residual_oxides["CO2"] == pytest.approx(0.0)
    assert provisional.residual_oxides["CaO"] == pytest.approx(0.0)

    assert result.balanced
    assert result.max_non_silica_error < 1e-8
    assert result.component_differences["CO2"] == pytest.approx(0.0)
    assert result.component_differences["CaO"] == pytest.approx(0.0)

def test_chromite_end_to_end_mass_balance():
    major = base_major()
    major.update({
        "SiO2": 10.0,
        "FeO": 0.10,
    })

    optional = empty_optional()
    optional["Cr2O3"] = 0.10

    provisional = calculate_kelsey_provisional(major, optional)
    result = check_mass_balance(major, optional, provisional)

    assert provisional.minerals["cm"] == pytest.approx(0.10)
    assert provisional.residual_oxides["Cr2O3"] == pytest.approx(0.0)
    assert provisional.residual_oxides["FeO"] == pytest.approx(0.0)

    assert result.balanced
    assert result.max_non_silica_error < 1e-8
    assert result.component_differences["Cr2O3"] == pytest.approx(0.0)
    assert result.component_differences["FeO"] == pytest.approx(0.0)
@pytest.mark.parametrize(
    ("feo", "tio2", "expected_residual_component", "expected_residual"),
    [
        (0.10, 0.20, "TiO2", 0.10),
        (0.20, 0.10, "FeO", 0.10),
    ],
    ids=["feo-limited", "tio2-limited"],
)
def test_ilmenite_limiting_cases_end_to_end_mass_balance(
    feo, tio2, expected_residual_component, expected_residual
):
    major = base_major()
    major.update({
        "SiO2": 10.0,
        "FeO": feo,
        "TiO2": tio2,
    })

    optional = empty_optional()
    provisional = calculate_kelsey_provisional(major, optional)

    result = check_mass_balance(major, optional, provisional)

    assert provisional.minerals["il"] == pytest.approx(min(feo, tio2))

    rule12_step = next(
        step for step in provisional.steps
        if step.get("rule") == 12
        and step.get("component") == expected_residual_component
    )
    assert rule12_step["residual"] == pytest.approx(expected_residual)

    assert result.balanced
    assert result.max_non_silica_error < 1e-8

@pytest.mark.parametrize(
    ("al2o3", "k2o", "expected_or", "expected_ks"),
    [
        (0.20, 0.10, 0.10, 0.00),
        (0.10, 0.20, 0.10, 0.10),
    ],
    ids=["k2o-limited", "al2o3-limited"],
)
def test_rule_13_orthoclase_and_potassium_metasilicate_mass_balance(
    al2o3, k2o, expected_or, expected_ks
):
    major = base_major()
    major.update({
        "SiO2": 20.0,
        "Al2O3": al2o3,
        "K2O": k2o,
    })

    optional = empty_optional()

    provisional = calculate_kelsey_provisional(major, optional)
    result = check_mass_balance(major, optional, provisional)

    assert provisional.minerals["or"] == pytest.approx(expected_or)
    assert provisional.minerals.get("ks", 0.0) == pytest.approx(expected_ks)

    assert result.balanced
    assert result.max_non_silica_error < 1e-8
    assert abs(result.silica_error) < 1e-8


@pytest.mark.parametrize(
    ("al2o3", "na2o", "expected_ab", "expected_ns"),
    [
        (0.20, 0.10, 0.10, 0.00),
        (0.10, 0.20, 0.10, 0.10),
    ],
    ids=["na2o-limited", "al2o3-limited"],
)
def test_rule_14_albite_limiting_cases_end_to_end_mass_balance(
    al2o3, na2o, expected_ab, expected_ns
):
    major = base_major()
    major.update({
        "SiO2": 20.0,
        "Al2O3": al2o3,
        "Na2O": na2o,
        "Fe2O3": 0.0,
    })

    optional = empty_optional()

    provisional = calculate_kelsey_provisional(major, optional)
    result = check_mass_balance(major, optional, provisional)

    assert provisional.minerals["ab"] == pytest.approx(expected_ab)
    assert provisional.minerals.get("ns", 0.0) == pytest.approx(expected_ns)

    assert result.balanced
    assert result.max_non_silica_error < 1e-8
    assert abs(result.silica_error) < 1e-8

@pytest.mark.parametrize(
    ("na2o", "fe2o3", "expected_ac", "expected_ns", "expected_silica"),
    [
        (0.1, 0.2, 0.1, 0.0, 0.4),
        (0.2, 0.1, 0.1, 0.1, 0.5),
    ],
)
def test_rule_15_acmite_and_sodium_metasilicate_end_to_end(
    na2o,
    fe2o3,
    expected_ac,
    expected_ns,
    expected_silica,
):
    major = base_major()
    major.update({
        "SiO2": 10.0,
        "Na2O": na2o,
        "Fe2O3": fe2o3,
    })
    optional = empty_optional()

    provisional = calculate_kelsey_provisional(major, optional)

    assert provisional.minerals.get("ac", 0.0) == pytest.approx(expected_ac)
    assert provisional.minerals.get("ns", 0.0) == pytest.approx(expected_ns)
    assert provisional.silica_requirement == pytest.approx(expected_silica)

    result = check_mass_balance(major, optional, provisional)

    assert result.balanced
    assert result.status == "BALANCED"
    assert result.max_non_silica_error < 1e-8
    assert abs(result.silica_error) < 1e-8

@pytest.mark.parametrize(
    ("al2o3", "cao", "expected_an", "expected_c", "expected_wo",
     "expected_silica"),
    [
        (0.3, 0.1, 0.1, 0.2, 0.0, 0.2),
        (0.1, 0.2, 0.1, 0.0, 0.1, 0.3),
    ],
    ids=["cao-limited", "alumina-limited"],
)
def test_rule_16_anorthite_and_corundum_end_to_end(
    al2o3, cao, expected_an, expected_c, expected_wo, expected_silica
):
    major = base_major()
    major.update({
        "SiO2": 20.0,
        "Al2O3": al2o3,
        "CaO": cao,
    })
    optional = empty_optional()

    provisional = calculate_kelsey_provisional(major, optional)

    assert provisional.minerals.get("an", 0.0) == pytest.approx(expected_an)
    assert provisional.minerals.get("c", 0.0) == pytest.approx(expected_c)
    assert provisional.minerals.get("wo", 0.0) == pytest.approx(expected_wo)
    assert provisional.silica_requirement == pytest.approx(expected_silica)

    result = check_mass_balance(major, optional, provisional)

    assert result.balanced
    assert result.status == "BALANCED"
    assert result.max_non_silica_error < 1e-8
    assert abs(result.silica_error) < 1e-8

@pytest.mark.parametrize(
    ("cao", "tio2", "expected_tn", "expected_ru", "expected_wo",
     "expected_silica"),
    [
        (0.1, 0.2, 0.1, 0.1, 0.0, 0.1),
        (0.2, 0.1, 0.1, 0.0, 0.1, 0.2),
    ],
    ids=["tio2-excess", "cao-excess"],
)
def test_rule_17_sphene_and_rutile_end_to_end(
    cao, tio2, expected_tn, expected_ru, expected_wo, expected_silica
):
    major = base_major()
    major.update({
        "SiO2": 20.0,
        "CaO": cao,
        "TiO2": tio2,
    })
    optional = empty_optional()

    provisional = calculate_kelsey_provisional(major, optional)

    assert provisional.minerals.get("tn", 0.0) == pytest.approx(expected_tn)
    assert provisional.minerals.get("ru", 0.0) == pytest.approx(expected_ru)
    assert provisional.minerals.get("wo", 0.0) == pytest.approx(expected_wo)
    assert provisional.silica_requirement == pytest.approx(expected_silica)

    result = check_mass_balance(major, optional, provisional)

    assert result.balanced
    assert result.status == "BALANCED"
    assert result.max_non_silica_error < 1e-8
    assert abs(result.silica_error) < 1e-8

@pytest.mark.parametrize(
    ("feo", "fe2o3", "expected_mt", "expected_hm", "expected_hy",
     "expected_silica"),
    [
        (0.1, 0.2, 0.1, 0.1, 0.0, 0.0),
        (0.2, 0.1, 0.1, 0.0, 0.1, 0.1),
    ],
    ids=["feo-limited", "fe2o3-limited"],
)
def test_rule_18_magnetite_and_hematite_end_to_end(
    feo, fe2o3, expected_mt, expected_hm, expected_hy, expected_silica
):
    major = base_major()
    major.update({
        "SiO2": 20.0,
        "FeO": feo,
        "Fe2O3": fe2o3,
    })
    optional = empty_optional()

    provisional = calculate_kelsey_provisional(major, optional)

    assert provisional.minerals.get("mt", 0.0) == pytest.approx(expected_mt)
    assert provisional.minerals.get("hm", 0.0) == pytest.approx(expected_hm)
    assert provisional.minerals.get("hy", 0.0) == pytest.approx(expected_hy)
    assert provisional.silica_requirement == pytest.approx(expected_silica)

    result = check_mass_balance(major, optional, provisional)

    assert result.balanced
    assert result.status == "BALANCED"
    assert result.max_non_silica_error < 1e-8
    assert abs(result.silica_error) < 1e-8

def test_rule_19_mixed_mg_fe_ratio_mass_balance_after_magnetite():
    major = base_major()
    major.update({
        "SiO2": 20.0,
        "CaO": 0.2,
        "MgO": 0.3,
        "FeO": 0.2,
        "Fe2O3": 0.1,
    })
    optional = empty_optional()

    provisional = calculate_kelsey_provisional(major, optional)

    assert provisional.minerals["mt"] == pytest.approx(0.1)
    assert provisional.mg_fraction == pytest.approx(0.75)
    assert provisional.fe_fraction == pytest.approx(0.25)
    assert provisional.minerals["di"] == pytest.approx(0.2)
    assert provisional.minerals["hy"] == pytest.approx(0.2)

    result = check_mass_balance(major, optional, provisional)

    assert result.balanced
    assert result.status == "BALANCED"
    assert result.max_non_silica_error < 1e-8
    assert abs(result.silica_error) < 1e-8

@pytest.mark.parametrize(
    (
        "cao", "mgo", "feo",
        "expected_di", "expected_wo", "expected_hy",
        "expected_silica",
    ),
    [
        (0.2, 0.3, 0.1, 0.2, 0.0, 0.2, 0.6),
        (0.3, 0.1, 0.1, 0.2, 0.1, 0.0, 0.5),
    ],
    ids=["cao-limited", "mgfe-limited"],
)
def test_rule_20_diopside_wollastonite_hypersthene_end_to_end(
    cao, mgo, feo,
    expected_di, expected_wo, expected_hy,
    expected_silica,
):
    major = base_major()
    major.update({
        "SiO2": 20.0,
        "CaO": cao,
        "MgO": mgo,
        "FeO": feo,
    })
    optional = empty_optional()

    provisional = calculate_kelsey_provisional(major, optional)

    assert provisional.minerals.get("di", 0.0) == pytest.approx(expected_di)
    assert provisional.minerals.get("wo", 0.0) == pytest.approx(expected_wo)
    assert provisional.minerals.get("hy", 0.0) == pytest.approx(expected_hy)
    assert provisional.silica_requirement == pytest.approx(expected_silica)

    assert provisional.mg_fraction == pytest.approx(mgo / (mgo + feo))
    assert provisional.fe_fraction == pytest.approx(feo / (mgo + feo))

    result = check_mass_balance(major, optional, provisional)

    assert result.balanced
    assert result.status == "BALANCED"
    assert result.max_non_silica_error < 1e-8
    assert abs(result.silica_error) < 1e-8

def test_rule_21_exact_silica_balance_end_to_end():
    major = base_major()
    major.update({
        "SiO2": 0.6,
        "Al2O3": 0.1,
        "K2O": 0.1,
    })
    optional = empty_optional()

    provisional = calculate_kelsey_provisional(major, optional)

    assert provisional.status == "SILICA_BALANCED"
    assert provisional.silica_requirement == pytest.approx(0.6)
    assert provisional.silica_excess == pytest.approx(0.0)
    assert provisional.silica_deficiency == pytest.approx(0.0)

    result = check_mass_balance(major, optional, provisional)

    assert result.balanced
    assert result.status == "BALANCED"
    assert result.max_non_silica_error < 1e-8
    assert abs(result.silica_error) < 1e-8

def test_rule_22_mixed_mg_fe_hypersthene_to_olivine_mass_balance():
    major = base_major()
    major.update({
        "SiO2": 1.0,
        "MgO": 1.5,
        "FeO": 0.5,
    })
    optional = empty_optional()

    provisional = calculate_kelsey_provisional(major, optional)

    assert provisional.status == "SILICA_DEFICIENCY"
    assert provisional.mg_fraction == pytest.approx(0.75)
    assert provisional.fe_fraction == pytest.approx(0.25)
    assert provisional.minerals["hy"] == pytest.approx(2.0)
    assert provisional.silica_deficiency == pytest.approx(1.0)

    redistributed = redistribute_silica(
        provisional.minerals,
        provisional.silica_deficiency,
    )

    assert redistributed.minerals["hy"] == pytest.approx(0.0)
    assert redistributed.minerals["ol"] == pytest.approx(1.0)
    assert redistributed.final_deficiency == pytest.approx(0.0)
    assert redistributed.status == "COMPLETED"

    result = check_mass_balance(
        major,
        optional,
        provisional,
        redistributed,
    )

    assert result.balanced
    assert result.status == "BALANCED"
    assert result.max_non_silica_error < 1e-8
    assert abs(result.silica_error) < 1e-8

def test_rule_23_sphene_to_perovskite_mass_balance():
    major = base_major()
    major.update({
        "SiO2": 0.0,
        "CaO": 0.1,
        "TiO2": 0.1,
    })
    optional = empty_optional()

    provisional = calculate_kelsey_provisional(major, optional)

    assert provisional.status == "SILICA_DEFICIENCY"
    assert provisional.minerals.get("tn", 0.0) == pytest.approx(0.1)
    assert provisional.silica_deficiency == pytest.approx(0.1)

    redistributed = redistribute_silica(
        provisional.minerals,
        provisional.silica_deficiency,
    )

    assert redistributed.minerals["tn"] == pytest.approx(0.0)
    assert redistributed.minerals["pf"] == pytest.approx(0.1)
    assert redistributed.final_deficiency == pytest.approx(0.0)
    assert redistributed.status == "COMPLETED"

    result = check_mass_balance(
        major,
        optional,
        provisional,
        redistributed,
    )

    assert result.balanced
    assert result.status == "BALANCED"
    assert result.max_non_silica_error < 1e-8
    assert abs(result.silica_error) < 1e-8

def test_rule_24_albite_to_nepheline_mass_balance():
    major = base_major()
    major.update({
        "SiO2": 0.2,
        "Al2O3": 0.1,
        "Na2O": 0.1,
    })
    optional = empty_optional()

    provisional = calculate_kelsey_provisional(major, optional)

    assert provisional.status == "SILICA_DEFICIENCY"
    assert provisional.minerals.get("ab", 0.0) == pytest.approx(0.1)
    assert provisional.silica_deficiency == pytest.approx(0.4)

    redistributed = redistribute_silica(
        provisional.minerals,
        provisional.silica_deficiency,
    )

    assert redistributed.minerals["ab"] == pytest.approx(0.0)
    assert redistributed.minerals["ne"] == pytest.approx(0.1)
    assert redistributed.final_deficiency == pytest.approx(0.0)
    assert redistributed.status == "COMPLETED"

    result = check_mass_balance(
        major,
        optional,
        provisional,
        redistributed,
    )

    assert result.balanced
    assert result.status == "BALANCED"
    assert result.max_non_silica_error < 1e-8
    assert abs(result.silica_error) < 1e-8

def test_rule_26_wollastonite_to_dicalcium_silicate_mass_balance():
    major = base_major()
    major.update({
        "SiO2": 0.0,
        "CaO": 0.1,
    })
    optional = empty_optional()

    provisional = calculate_kelsey_provisional(major, optional)

    assert provisional.status == "SILICA_DEFICIENCY"
    assert provisional.minerals.get("wo", 0.0) == pytest.approx(0.1)
    assert provisional.silica_deficiency == pytest.approx(0.1)

    redistributed = redistribute_silica(
        provisional.minerals,
        provisional.silica_deficiency,
    )

    assert redistributed.minerals["wo"] == pytest.approx(0.0)
    assert redistributed.minerals["cs"] == pytest.approx(0.05)
    assert redistributed.final_deficiency == pytest.approx(0.05)
    assert redistributed.status == "UNRESOLVED_DEFICIENCY"

    result = check_mass_balance(
        major,
        optional,
        provisional,
        redistributed,
    )

    assert result.balanced
    assert result.status == "BALANCED_WITH_UNRESOLVED_SILICA_DEFICIENCY"
    assert result.max_non_silica_error < 1e-8
    assert abs(result.silica_error) < 1e-8

def test_rule_27_mixed_mg_fe_diopside_redistribution_mass_balance():
    major = base_major()
    major.update({
        "SiO2": 0.0,
        "CaO": 0.2,
        "MgO": 0.15,
        "FeO": 0.05,
    })
    optional = empty_optional()

    provisional = calculate_kelsey_provisional(major, optional)

    assert provisional.status == "SILICA_DEFICIENCY"
    assert provisional.minerals.get("di", 0.0) == pytest.approx(0.2)
    assert provisional.minerals.get("hy", 0.0) == pytest.approx(0.0)
    assert provisional.mg_fraction == pytest.approx(0.75)
    assert provisional.fe_fraction == pytest.approx(0.25)
    assert provisional.silica_deficiency == pytest.approx(0.4)

    redistributed = redistribute_silica(
        provisional.minerals,
        provisional.silica_deficiency,
    )

    assert redistributed.minerals["di"] == pytest.approx(0.0)
    assert redistributed.minerals["cs"] == pytest.approx(0.1)
    assert redistributed.minerals["ol"] == pytest.approx(0.1)
    assert redistributed.final_deficiency == pytest.approx(0.2)
    assert redistributed.status == "UNRESOLVED_DEFICIENCY"

    result = check_mass_balance(
        major,
        optional,
        provisional,
        redistributed,
    )

    assert result.balanced
    assert result.status == "BALANCED_WITH_UNRESOLVED_SILICA_DEFICIENCY"
    assert result.max_non_silica_error < 1e-8
    assert abs(result.silica_error) < 1e-8

def test_rule_28_orthoclase_to_kaliophilite_mass_balance():
    major = base_major()
    major.update({
        "SiO2": 2.0,
        "Al2O3": 1.0,
        "K2O": 1.0,
    })
    optional = empty_optional()

    provisional = calculate_kelsey_provisional(major, optional)

    assert provisional.status == "SILICA_DEFICIENCY"
    assert provisional.minerals["or"] == pytest.approx(1.0)
    assert provisional.silica_deficiency == pytest.approx(4.0)

    redistributed = redistribute_silica(
        provisional.minerals,
        provisional.silica_deficiency,
    )

    assert redistributed.status == "COMPLETED"
    assert redistributed.minerals["or"] == pytest.approx(0.0)
    assert redistributed.minerals["lc"] == pytest.approx(0.0)
    assert redistributed.minerals["kp"] == pytest.approx(1.0)
    assert redistributed.final_deficiency == pytest.approx(0.0)

    rule_25 = next(step for step in redistributed.steps if step["rule"] == 25)
    rule_28 = next(step for step in redistributed.steps if step["rule"] == 28)

    assert rule_25["provisional_amount_converted"] == pytest.approx(1.0)
    assert rule_28["provisional_amount_converted"] == pytest.approx(1.0)
    assert rule_28["products_formed"]["kp"] == pytest.approx(1.0)

    result = check_mass_balance(
        major,
        optional,
        provisional,
        redistributed,
    )

    assert result.balanced
    assert result.status == "BALANCED"
    assert result.max_non_silica_error < 1e-8
    assert abs(result.silica_error) < 1e-8
