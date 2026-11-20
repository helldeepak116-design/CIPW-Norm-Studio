
# CIPW Norm Studio — Scientific Validation Matrix

**Calculation method:** Classical Kelsey (1965)
**Iron basis:** Measured FeO and Fe2O3 separately
**Purpose:** Trace every implemented allocation rule to its equation, software tests, and independent scientific evidence.

## 1. Validation status definitions

| Status | Meaning |
|---|---|
| Published comparison | Compared with a published worked example using the relevant procedure |
| Synthetic regression | Tested using controlled numerical compositions |
| Mass-balance verified | Component conservation checked |
| Partial | Some behavior tested, but important branches remain unverified |
| Pending | Independent scientific evidence or required tests are missing |

A passing software test does not independently establish scientific validity.

## 2. Provisional allocation: Rules 1–21

| Rule | Allocation / calculation | Expected behavior to verify | Existing test coverage | Independent evidence | Status |
|---|---|---|---|---|---|
| 1 | Convert analytical oxide concentrations into molecular proportions | Correct molecular proportions and input validation | tests/test_oxide_conversion.py; tests/test_reference_benchmarks_extended.py | Idaho granite; Winter basalt oxide proportions | Published comparison for conversion only |
| 2 | Combine MnO and NiO with FeO on a molecular-proportion basis | Correct FeO-equivalent adjustment and conservation | tests/test_kelsey_provisional.py: test_rule_2_records_original_and_equivalent_iron_components; tests/test_mass_balance_integration.py | No independent whole-rock Kelsey benchmark | Synthetic regression |
| 3 | Combine BaO and SrO with CaO on a molecular-proportion basis | Correct CaO-equivalent adjustment and conservation | tests/test_kelsey_provisional.py: test_rule_3_records_original_and_equivalent_calcium_components; test_rule_4_zircon_records_allocation_and_residual | No independent whole-rock Kelsey benchmark | Synthetic regression |
| 4 | Allocate ZrO2 to zircon; account for associated silica | Zircon amount, silica requirement and residual ZrO2 | tests/test_kelsey_provisional.py: test_rule_3_records_original_and_equivalent_calcium_components; test_rule_4_zircon_records_allocation_and_residual | No independent Kelsey worked example identified | Synthetic regression |
| 5 | Allocate P2O5 to apatite using Kelsey's convention: 3CaO·P2O5·(1/3)CaF | Apatite amount, CaO consumption and limited F allocation | tests/test_kelsey_provisional.py: test_rule_5_zero_fluorine_still_allocates_all_p2o5_to_apatite; test_rule_5_fluorine_limited_apatite_retains_full_p2o5_allocation | Kelsey (1965), Rule 5 convention | Targeted synthetic rule audit |
| 6 | Allocate remaining F to fluorite | Fluorite amount, CaO consumption and residual F | tests/test_kelsey_provisional.py: test_rule_6_fluorite_without_apatite; test_rule_6_rejects_insufficient_calcium; apatite-fluorine audit | Kelsey (1965), Rule 6 | Targeted synthetic rule audit |
| 7 | Allocate Cl to halite using Na2O | Halite amount and residual Na2O/Cl | tests/test_kelsey_provisional.py: test_rule_7_halite; test_rule_7_rejects_insufficient_sodium | No independent whole-rock Kelsey benchmark | Synthetic regression |
| 8 | Allocate SO3 to thenardite using Na2O | Correct sulfur basis, allocation and residuals | tests/test_kelsey_provisional.py: test_rule_8_thenardite; tests/test_mass_balance_integration.py | No independent Kelsey worked example identified | Partial |
| 9 | Allocate elemental S to pyrite using FeO | Pyrite amount, FeO consumption and sulfur-basis handling | tests/test_kelsey_provisional.py: test_rule_9_pyrite; tests/test_mass_balance_integration.py | Kelsey (1965) procedure; independent whole-rock benchmark pending | Partial |
| 10a | Allocate CO2 to cancrinite using Na2O | Carbonate allocation and component conservation | tests/test_kelsey_provisional.py: test_rule_10_cancrinite_sodium_carbonate; test_rule_10_calcite | No independent whole-rock Kelsey benchmark | Synthetic regression |
| 10b | Allocate CO2 to calcite using CaO | Calcite allocation and component conservation | tests/test_kelsey_provisional.py: test_rule_10_cancrinite_sodium_carbonate; test_rule_10_calcite | No independent whole-rock Kelsey benchmark | Synthetic regression |
| 11 | Allocate Cr2O3 to chromite using FeO | Chromite amount and FeO consumption | tests/test_kelsey_provisional.py: test_rule_11_chromite | No independent Kelsey worked example identified | Synthetic regression |
| 12 | Allocate FeO and TiO2 to ilmenite | Limiting-component behavior and residual oxide | tests/test_kelsey_provisional.py: test_rule_12_ilmenite_is_limited_by_feo; test_rule_12_ilmenite_is_limited_by_tio2 | No independent whole-rock Kelsey benchmark | Synthetic regression |
| 13 | Allocate K2O and Al2O3 to orthoclase; excess K2O to potassium metasilicate | Limiting-component behavior and silica requirement | tests/test_kelsey_provisional.py: test_rule_13_orthoclase; test_rule_13_excess_potassium_forms_metasilicate | No independent Kelsey worked example identified | Synthetic regression |
| 14 | Allocate Na2O and Al2O3 to albite | Limiting-component behavior and silica requirement | tests/test_kelsey_provisional.py: test_rule_14_albite; test_rule_14_albite_is_limited_by_alumina | Bostonite end-to-end comparison; supportive evidence, not an isolated Rule 14 validation | Published comparison, rounded |
| 15 | Allocate Na2O and Fe2O3 to acmite; excess Na2O to sodium metasilicate | Limiting-component behavior and silica requirement | tests/test_kelsey_provisional.py: test_rule_15_acmite; test_rule_15_acmite_is_limited_by_ferric_iron | No independent Kelsey worked example identified | Synthetic regression |
| 16 | Allocate Al2O3 and CaO to anorthite; remaining Al2O3 to corundum | Limiting-component behavior and silica requirement | tests/test_kelsey_provisional.py: test_rule_16_anorthite_and_corundum; test_rule_16_anorthite_is_limited_by_alumina | Bostonite end-to-end comparison; supportive evidence, not isolated Rule 16 validation | Published comparison, rounded |
| 17 | Allocate CaO and TiO2 to sphene; excess TiO2 to rutile | Limiting-component behavior and silica requirement | tests/test_kelsey_provisional.py: test_rule_17_sphene_and_rutile; test_rule_17_sphene_is_limited_by_titanium | No independent Kelsey worked example identified | Synthetic regression |
| 18 | Allocate FeO and Fe2O3 to magnetite; remaining Fe2O3 to hematite | Limiting-component behavior and separate iron handling | tests/test_kelsey_provisional.py: test_rule_18_magnetite_and_hematite; test_rule_18_magnetite_is_limited_by_ferric_iron | Bostonite end-to-end comparison; supportive evidence, not isolated Rule 18 validation | Published comparison, rounded |
| 19 | Determine Mg/Fe proportions in the ferromagnesian component | Correct Mg and Fe fractions | tests/test_kelsey_provisional.py: test_rule_19_mg_fe_ratios; test_rule_19_uses_residual_iron_after_magnetite_allocation | No independent Kelsey worked example identified | Synthetic regression |
| 20 | Allocate Ca-bearing and Mg-Fe-bearing components to diopside, wollastonite and hypersthene | Correct mineral amounts and silica requirement | tests/test_kelsey_provisional.py: test_rule_20_diopside_and_hypersthene; test_rule_20_diopside_and_wollastonite | Bostonite end-to-end comparison; supportive evidence, not isolated Rule 20 validation | Published comparison, rounded |
| 21 | Compare available SiO2 with calculated silica requirement | Correct silica excess, deficiency or balance classification | tests/test_kelsey_provisional.py: test_rule_21_silica_excess; test_rule_21_silica_deficiency; test_rule_21_exact_silica_balance; test_rule_21_difference_within_tolerance_is_balanced | Bostonite intermediate deficiency; Winter diagnostic | Published comparison plus diagnostic |

## 3. Silica-deficiency redistribution: Rules 22–28

| Rule | Redistribution | Expected behavior to verify | Existing test coverage | Independent evidence | Status |
|---|---|---|---|---|---|
| 22 | Hypersthene → olivine | One mole of hypersthene converted produces 0.5 mole olivine and releases 0.5 mole silica | tests/test_kelsey_silica_deficiency.py: test_rule_22_hypersthene_to_olivine; test_rule_22_hypersthene_limited_conversion | Bostonite intermediate/final comparison | Published comparison, rounded |
| 23 | Sphene → perovskite | Correct conversion and silica-deficiency reduction | tests/test_kelsey_silica_deficiency.py: test_rule_23_sphene_to_perovskite; test_rule_23_sphene_limited_conversion | No independent worked example identified | Synthetic regression |
| 24 | Albite → nepheline | Correct conversion and silica-deficiency reduction | tests/test_kelsey_silica_deficiency.py: test_rule_24_albite_to_nepheline; test_rule_24_albite_limited_conversion | Bostonite end-to-end comparison; supportive evidence, not isolated Rule 24 validation | Published comparison, rounded |
| 25 | Orthoclase → provisional leucite | Correct provisional leucite amount and silica-deficiency reduction | tests/test_kelsey_silica_deficiency.py: test_rule_25_orthoclase_to_leucite_uses_half_mole_factor; test_rule_25_orthoclase_limited_conversion_and_diagnostics | No independent worked example identified | Synthetic regression |
| 26 | Wollastonite → dicalcium silicate | Correct conversion and residual deficiency | tests/test_kelsey_silica_deficiency.py: test_rule_26_wollastonite_to_dicalcium_silicate; test_rule_26_wollastonite_limited_conversion_and_diagnostics | No independent worked example identified | Synthetic regression |
| 27 | Diopside → dicalcium silicate and olivine | Correct product proportions and residual deficiency | tests/test_kelsey_silica_deficiency.py: test_rule_27_diopside_products; test_rule_27_diopside_limited_conversion_and_diagnostics | No independent worked example identified | Synthetic regression |
| 28 | Provisional leucite → kaliophilite | Only leucite generated by Rule 25 may be consumed | tests/test_kelsey_silica_deficiency.py: test_rule_28_kaliophilite_uses_provisional_leucite_only | No independent worked example identified | Synthetic regression |

## 4. Cross-cutting validation

| Area | Required verification | Existing evidence | Remaining work |
|---|---|---|---|
| Oxide conversion | Formula weights, molecular proportions and analytical basis | Published Idaho and Winter oxide-proportion comparisons | Additional independent analytical datasets |
| Iron handling | FeO and Fe2O3 remain separately measured | Rule 18 tests and Bostonite comparison | Additional iron-rich reference compositions |
| Optional components | Measurement status, conversion and allocation | Optional-component tests and integration tests | Independent validation of each chemical branch |
| Apatite fluorine | Kelsey Rule 5 allocation and Rule 6 excess F | Synthetic low-F and high-F audits | Published whole-rock fluorine-bearing benchmark |
| Sulfur | SO3 and elemental S handling | Existing rule and integration coverage | Independent sulfur-bearing benchmark |
| Carbonate | Cancrinite and calcite modes | Synthetic integration tests | Independent carbonate-bearing benchmark |
| Silica excess | Quartz production and mass consistency | Pure-silica regression and mass-balance tests | Published quartz-norm benchmark |
| Silica deficiency | Rule order, mineral conversion and unresolved deficiency | Rules 22–28 regression tests | Independent examples for each pathway |
| Mass balance | Component conservation and silica accounting | Internal mass-balance tests | Independent external comparison |
| Mineral masses | Formula weights and conversion to normalized wt.% | Formula-weight and mass-validation tests | Additional independently calculated reference norms |
| PDF reporting | Correct presentation of inputs, outputs, assumptions and audit trail | Report-generation tests and inspected report | Automated PDF content regression |
| Streamlit interface | Input validation, state retention and exports | Existing application-level checks | Full user-workflow testing |

## 5. Published benchmark registry

| Benchmark | Source | Permitted validation claim |
|---|---|---|
| Bostonite | Kelsey (1965), Table III; Washington (1917), p. 274, analysis 37 | Rounded Kelsey worked-example comparison |
| Mid-Atlantic Ridge tholeiitic basalt | Winter (2014), Appendix B, Table 2 | Modified-CIPW diagnostic comparison |
| Idaho Batholith granite, sample 134.15 | Mattioli and Zachry (2008) | Oxide molecular-proportion and different-procedure diagnostic comparison |
| Apatite-fluorine cases | Synthetic audit based on Kelsey Rules 5–6 | Targeted arithmetic and formula-mass verification |

## 6. Scientific acceptance criteria

A rule should not be marked independently validated until the following evidence is recorded:

1. Primary reference, edition and page/table.
2. Original analytical inputs and units.
3. Explicit assumptions for unreported components.
4. Molecular allocation equations and stoichiometric coefficients.
5. Expected mineral molecular amounts or intermediate values.
6. Comparison with the application output.
7. Tolerance justified by source precision and numerical method.
8. Component mass-balance result.
9. A reproducible automated test.

Synthetic tests and internal conservation checks must remain separately identified from published-reference validation.

## 7. Current limitations

- The Bostonite benchmark is rounded and conditional because some analytical components are unreported.
- Winter's basalt is a modified-procedure diagnostic, not an exact independent Kelsey implementation.
- The Idaho granite exercise uses a different normative procedure.
- Synthetic tests establish expected behavior for selected inputs, not universal equivalence with the published method.
- Independent end-to-end published benchmarks are not yet available for every allocation and redistribution rule.

## 8. Reproducibility

Run from the project root:

```powershell
python -m pytest -q
python -m pytest -q tests/test_kelsey_provisional.py
python -m pytest -q tests/test_kelsey_silica_deficiency.py
python -m pytest -q tests/test_mass_balance_integration.py
python -m scripts.run_kelsey_bostonite_validation
python -m scripts.audit_apatite_fluorine
```

Update this matrix whenever a scientific rule, reference benchmark, test, or numerical tolerance changes.
